"""Verified public Ollama model ZIPs; never import account keys or execute files."""
import base64
import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path

EMBEDDING_NAME = 'qwen3-embedding:0.6b'
EMBEDDING_DIGEST = 'ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d'
EMBEDDING_MANIFEST = 'manifests/registry.ollama.ai/library/qwen3-embedding/0.6b'
EMBEDDING_MANIFEST_BYTES = base64.b64decode('eyJzY2hlbWFWZXJzaW9uIjoyLCJtZWRpYVR5cGUiOiJhcHBsaWNhdGlvbi92bmQuZG9ja2VyLmRpc3RyaWJ1dGlvbi5tYW5pZmVzdC52Mitqc29uIiwiY29uZmlnIjp7Im1lZGlhVHlwZSI6ImFwcGxpY2F0aW9uL3ZuZC5kb2NrZXIuY29udGFpbmVyLmltYWdlLnYxK2pzb24iLCJkaWdlc3QiOiJzaGEyNTY6OTIwMmZlYmVkOWUyZGFkYWMxNGJjYTA4OWJlOTA4NjQ1NzEzMzZmYTlmNDM3NWI2OTBhMjZlZDU0ODk1N2ZkZSIsInNpemUiOjI2Nn0sImxheWVycyI6W3sibWVkaWFUeXBlIjoiYXBwbGljYXRpb24vdm5kLm9sbGFtYS5pbWFnZS5tb2RlbCIsImRpZ2VzdCI6InNoYTI1NjowNjUwN2M3YjQyNjg4NDY5YzRlNzI5OGIwYTFlMTZkZWZmMDZjYWYyOTFjZjBhNWIyNzhjMzA4MjQ5YzNlNDM5Iiwic2l6ZSI6NjM5MTUwNTkyLCJmcm9tIjoiL1VzZXJzL29sbGFtYS8ub2xsYW1hL21vZGVscy9ibG9icy9zaGEyNTYtMDY1MDdjN2I0MjY4ODQ2OWM0ZTcyOThiMGExZTE2ZGVmZjA2Y2FmMjkxY2YwYTViMjc4YzMwODI0OWMzZTQzOSJ9XX0=')
EMBEDDING_CONFIG_BYTES = base64.b64decode('eyJtb2RlbF9mb3JtYXQiOiJnZ3VmIiwibW9kZWxfZmFtaWx5IjoicXdlbjMiLCJtb2RlbF9mYW1pbGllcyI6WyJxd2VuMyJdLCJtb2RlbF90eXBlIjoiNTk1Ljc4TSIsImZpbGVfdHlwZSI6IlE4XzAiLCJhcmNoaXRlY3R1cmUiOiJhbWQ2NCIsIm9zIjoibGludXgiLCJyb290ZnMiOnsidHlwZSI6ImxheWVycyIsImRpZmZfaWRzIjpbInNoYTI1NjowNjUwN2M3YjQyNjg4NDY5YzRlNzI5OGIwYTFlMTZkZWZmMDZjYWYyOTFjZjBhNWIyNzhjMzA4MjQ5YzNlNDM5Il19fQo=')


def expand_gguf_pair(root, files, external):
    """Supply pinned metadata internally; public ZIP needs only the two GGUFs."""
    from .release import sha
    manifest=json.loads(EMBEDDING_MANIFEST_BYTES)
    if hashlib.sha256(EMBEDDING_MANIFEST_BYTES).hexdigest()!=EMBEDDING_DIGEST:
        raise ValueError('Bundled embedding metadata checksum mismatch')
    config=manifest['config'];embedding=manifest['layers'][0]
    if (len(manifest['layers'])!=1 or len(EMBEDDING_CONFIG_BYTES)!=config['size'] or
            hashlib.sha256(EMBEDDING_CONFIG_BYTES).hexdigest()!=config['digest'][7:]):
        raise ValueError('Bundled embedding configuration checksum mismatch')
    if not external or len(files)!=2:raise ValueError('AI models ZIP must contain exactly two GGUF files: chat and embedding')
    identities={p:(p.stat().st_size,sha(p)) for p in files}
    chat=[p for p,v in identities.items() if v==(external['bytes'],external['sha256'])]
    embed=[p for p,v in identities.items() if v==(embedding['size'],embedding['digest'][7:])]
    if len(chat)!=1 or len(embed)!=1 or chat[0]==embed[0]:
        raise ValueError('AI model checksum mismatch: use the release-verified Qwen3 4B Instruct Q4_K_M and official Qwen3 Embedding 0.6B Q8_0 GGUF files')
    metadata=root/'models'/EMBEDDING_MANIFEST;metadata.parent.mkdir(parents=True);metadata.write_bytes(EMBEDDING_MANIFEST_BYTES)
    blobs=root/'models/blobs';blobs.mkdir()
    (blobs/config['digest'].replace(':','-')).write_bytes(EMBEDDING_CONFIG_BYTES)
    embed[0].rename(blobs/embedding['digest'].replace(':','-'))


def prepare_bundle(source, cache, external, chat_digest):
    from .release import safe_zip, sha
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    # Revalidate on every use, including cached ZIPs. Only public model files
    # enter the generated transfer archive; ZIP names/compression are not trust.
    with tempfile.TemporaryDirectory(prefix='ai-models-',dir=cache) as temporary:
        root=Path(temporary);safe_zip(source,root)
        files=[p for p in root.rglob('*') if p.is_file()]
        if files and all(p.parent==root and p.suffix.lower()=='.gguf' for p in files):
            expand_gguf_pair(root,files,external)
            files=[p for p in root.rglob('*') if p.is_file()]
        if any(not (p.suffix.lower()=='.gguf' and p.parent==root or
                    re.fullmatch(r'(?:models/)?blobs/sha256-[0-9a-f]{64}',p.relative_to(root).as_posix()) or
                    re.fullmatch(r'(?:models/)?manifests/registry\.ollama\.ai/library/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+',p.relative_to(root).as_posix())) for p in files):
            raise ValueError('AI models ZIP must contain only public Ollama manifests/blobs and optional top-level GGUF files; do not include account keys')
        selected={};models=[]
        # Chat remains authenticated by the selected stack release. The current
        # embedding manifest is pinned here to the official Ollama registry.
        for name,digest in [('qwen3:4b-instruct',chat_digest.removeprefix('sha256:')),(EMBEDDING_NAME,EMBEDDING_DIGEST)]:
            family,tag=name.split(':');relative=f'manifests/registry.ollama.ai/library/{family}/{tag}'
            matches=[p for p in files if p.relative_to(root).as_posix() in (relative,'models/'+relative)]
            if not matches:
                if name=='qwen3:4b-instruct':continue  # Chat manifest is also in Ollama components.
                raise ValueError('AI models ZIP is missing '+name+' manifest and blobs. Export the Ollama models directory after pulling both models.')
            if len(matches)!=1 or sha(matches[0])!=digest:raise ValueError('AI model manifest checksum mismatch: '+name)
            manifest=json.loads(matches[0].read_text('utf-8'))
            selected[relative]=matches[0];models.append(name)
            for item in [manifest['config'],*manifest['layers']]:
                value=item['digest']
                if not re.fullmatch(r'sha256:[0-9a-f]{64}',value) or type(item['size']) is not int or item['size']<0:raise ValueError('Invalid AI model blob contract')
                blob='blobs/'+value.replace(':','-')
                candidates=[p for p in files if p.relative_to(root).as_posix() in (blob,'models/'+blob)]
                if len(candidates)!=1 or candidates[0].stat().st_size!=item['size'] or sha(candidates[0])!=value[7:]:raise ValueError('Missing/corrupt AI model blob: '+name)
                selected[blob]=candidates[0]
        if external:
            matches=[p for p in files if p.stat().st_size==external['bytes'] and sha(p)==external['sha256']]
            if not matches:raise ValueError('AI models ZIP is missing the release-verified Qwen3 4B Instruct Q4_K_M model')
            selected['blobs/sha256-'+external['sha256']]=matches[0]
        destination=cache/('ai-models-'+sha(source)[:20]+'-'+chat_digest[-12:]+'.tar')
        partial=destination.with_suffix('.partial')
        try:
            with tarfile.open(partial,'w') as archive:
                for name,path in sorted(selected.items()):archive.add(path,arcname=name,recursive=False)
            partial.replace(destination)
        finally:partial.unlink(missing_ok=True)
        return destination
