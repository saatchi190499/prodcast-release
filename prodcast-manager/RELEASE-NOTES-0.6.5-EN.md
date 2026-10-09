# Manager 0.6.5

Fix: Stop previous operation now handles a pending ai-journal.json independently
of the core deployment journal. A completed core upgrade no longer produces a
misleading idle result while AI blocks Worker removal or addition.

Open the original installation profile/vault, click Stop previous operation, then
retry Worker removal. This also works when optional AI has been disabled in the
profile after an interrupted upgrade. No complete release ZIP is required to stop.

The AI VM is checked against the saved address, installation identity and operation
owner before releasing it. Connection errors or a different owner leave the AI
journal pending. The original journal is archived in profile/history and marked
stopped, not deleted. Installed AI, DB data, core deployment and vault are preserved;
stopping does not roll back the database or undo an interrupted AI deployment.

Based on current non-AD Manager code, retaining combined AI-model ZIP support and
declared Worker execution-policy support. Includes existing EN/RU v0.6 PDF manuals;
these notes supplement them. No AD service-account prototype changes are included.
