# Agent installer builds

Run **Build Prodcast Agent installer** from Actions and enter one internal version, such as `v0.6.5`, matching the complete-release version format.

The workflow checks out `prodcast-agent` main, uses the same Windows build and smoke tests as **Build and assemble ProdCast release**, and uploads `Prodcast-Agent-v0.6.5` for 30 days. The artifact contains only `ProdcastAgentSetup-v0.6.5.exe`. Windows displays the product as **Prodcast Agent** with version `0.6.5.0`.

The complete-release workflow's `agent-payload` artifact also contains only the installer EXE. Its assembly metadata travels separately in the one-day `agent-assembly-metadata` artifact and is recombined with the EXE for provenance and checksum validation.

This workflow creates no Git tags, drafts, or GitHub releases. Rebuilding an internal version does not require or reserve a platform release version. It uses the existing `PRODCAST_RELEASE_APP_ID` / `PRODCAST_RELEASE_APP_PRIVATE_KEY` credentials, or the existing `PRODCAST_RELEASE_TOKEN` fallback, to read the Agent repository.
