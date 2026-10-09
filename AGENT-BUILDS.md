# Agent installer builds

Run **Build Prodcast Agent installer** from Actions and enter one internal version, such as `0.6.5`.

The workflow checks out `prodcast-agent` main, uses the same Windows build and smoke tests as **Build and assemble ProdCast release**, and uploads `Prodcast-Agent-0.6.5` for 30 days. The artifact includes `ProdcastAgentSetup-v0.6.5.exe`, installation instructions, the dependency inventory, a source commit manifest, and checksums. Windows displays the product as **Prodcast Agent** with version `0.6.5.0`.

This workflow creates no Git tags, drafts, or GitHub releases. Rebuilding an internal version does not require or reserve a platform release version. It uses the existing `PRODCAST_RELEASE_APP_ID` / `PRODCAST_RELEASE_APP_PRIVATE_KEY` credentials, or the existing `PRODCAST_RELEASE_TOKEN` fallback, to read the Agent repository.
