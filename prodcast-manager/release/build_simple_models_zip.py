"""Build the two-readable-GGUF model ZIP without model metadata or keys."""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prodcast_manager.ai_models import EMBEDDING_MANIFEST_BYTES
from prodcast_manager.release import sha


def main():
    parser=argparse.ArgumentParser()
    for name in ('release','chat-model','embedding-model','output'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args();output=Path(args.output)
    if output.exists():raise ValueError('Output already exists; do not overwrite a released ZIP')
    with zipfile.ZipFile(args.release) as archive:
        names=[n for n in archive.namelist() if n.endswith('release-manifest.json')]
        if len(names)!=1:raise ValueError('Ambiguous release manifest')
        external=json.loads(archive.read(names[0]))['management']['offline']['external_model']
    embedding=json.loads(EMBEDDING_MANIFEST_BYTES)['layers'][0]
    sources=[(Path(args.chat_model),'Qwen3-4B-Instruct-Q4_K_M.gguf',external['bytes'],external['sha256']),
             (Path(args.embedding_model),'Qwen3-Embedding-0.6B-Q8_0.gguf',embedding['size'],embedding['digest'][7:])]
    for path,name,size,digest in sources:
        if path.stat().st_size!=size or sha(path)!=digest:raise ValueError('Model checksum mismatch: '+name)
    output.parent.mkdir(parents=True,exist_ok=True);partial=output.with_suffix('.partial')
    with zipfile.ZipFile(partial,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as archive:
        for path,name,size,digest in sources:archive.write(path,name)
    partial.replace(output)
    print('ZIP_SHA256 '+sha(output),flush=True)


if __name__=='__main__':main()
