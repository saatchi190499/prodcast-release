# ProdCast Manager 0.6.2

- First-tab Worker selector with individual Repair/Reinstall and Remove actions.
- Re-add removed Workers on the retired or fresh VM using the original site's vault and verified DB retirement receipt.
- Stable Worker IDs after removal, resumable journals, retained runtime files and logs.
- App administrator access stays available during operations and reads saved credentials without preparing or saving the profile.
- Linux staging cleanup uses the same privilege level as the agents, removes only generated staging directories and handles root-owned Python caches from previous operations. New agent runs disable bytecode cache generation.
- Worker cleanup warnings identify the affected VM and directory, with local redacted diagnostics when available.
- Onefile executables; local profiles and session logs remain under prodcast-data.

Manager 0.6.2 is separate from the ProdCast stack version. Repair and Add Workers require the stack's exact installed release. Individual Worker actions pause App scheduling and ingress while tasks drain; they do not discard jobs. Remove retains Worker files and logs rather than wiping the VM.
