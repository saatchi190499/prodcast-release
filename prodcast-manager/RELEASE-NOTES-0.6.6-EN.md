# Manager 0.6.6

During a core update using an external AI payload release, leave BOTH AI models
and Ollama components fields empty to skip the optional AI update. Existing AI
services are left unchanged; the core report explicitly says AI was skipped.
Manager does not connect to AI or create a pending AI journal for this choice.
This does not verify that the existing AI installation is healthy or compatible.

Selecting either AI package still requests AI work and normal validation applies.
Fresh installation and explicit Retry AI do not silently skip missing packages.

Old failed/running AI journals with no steps and no inflight action are archived
in profile/history and marked skipped when the packages are omitted. This clears
false pending states created before any AI action started. Journals for genuinely
started operations are preserved, including inflight claim failures; stop or retry
them separately. Manager 0.6.5's separate AI-stop fix is retained.

Standalone one-file EXE; data/logs remain inside prodcast-data. Existing EN/RU v0.6
PDF manuals are included unchanged and supplemented by these notes. Combined AI
model ZIP and current Worker execution-policy support are retained. No AD prototype.
