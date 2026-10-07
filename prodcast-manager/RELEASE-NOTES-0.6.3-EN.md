# ProdCast Manager 0.6.3

Standalone Windows executable; the previous released Manager was 0.6.2. Profiles and logs remain in `prodcast-data`. No source archive is included. Existing EN/RU v0.6 PDF manuals are reused; these notes describe the updated model input.

## AI Documents deployment fix

Manager provisions the complete, additive document-library schema in `prodcast_ai`, transactionally and with tables owned by its non-superuser application role. It enables RAG, installs `qwen3-embedding:0.6b`, verifies 1024-dimensional embeddings, and mounts persistent writable document storage at `/opt/prodcast-manager/ai-data/documents`. Document listing is checked directly and from App. Older cached AI installation receipts cannot skip the corrected provisioning.

## Simple AI models ZIP

The supplied ZIP contains exactly two files:

```
Qwen3-4B-Instruct-Q4_K_M.gguf
Qwen3-Embedding-0.6B-Q8_0.gguf
```

Select this ZIP in the AI model picker. The Ollama components ZIP is still selected separately and supplies the release-authenticated chat template/configuration. Manager supplies the pinned embedding configuration internally. No public-cache manifests or hash-named files are needed inside the model ZIP. Both GGUFs are checked by content SHA256 and size; changing filenames does not bypass verification. ZIP64 is supported. Installation creates Ollama's internal hash-named blobs automatically and does not download models in the offline network.

The prior Ollama-cache model ZIP format remains compatible. Legacy standalone chat GGUF input remains supported only when the required embedding cache is already installed; missing embedding fails clearly instead of disabling document search.

## Apply to an installed site

Keep the existing `prodcast-data` profile and vault. Select the same installed complete stack package and its trusted manifest hash, the compatible Ollama components ZIP, and the new two-GGUF model ZIP. Click **Retry AI** to apply the document schema on DB and recreate AI without restarting or upgrading App/Workers. A full Update also applies the fix, but performs the usual core-stack update first. DB and AI must not be owned by an unrelated pending operation.

Server-local AI backups include the document directory. This does not implement automatic rollback or add AI documents to the existing App/DB-only `.pcbackup` export format.

Manager and stack versions are independent. No live VMs are changed merely by unpacking or launching Manager.
