# Manager 0.6

## Add Workers after installation

Back up the entire site profile, then open the installed profile and its original credentials in Manager 0.6. Select the exact installed ProdCast release. Increase the Worker count (up to 16), enter the new VM addresses and SSH credentials, verify their host fingerprints, and click **Add Workers…**. Each new Worker needs a separate prepared Windows Server VM. Ordinary Save or Update is not the expansion action.

Expansion checks the installed core, generates independent credentials for new Workers, adds PostgreSQL/Redis grants and firewall access, installs only the new Windows services and checks readiness. It does not restart App, existing Workers or DB containers. AI is untouched. Installation identity, certificates, activation and existing secrets are preserved.

After a failure, retry with the same release and addresses; preserve the profile and journal. Once server changes begin, only the original transaction can resume. A failed preflight with no attempted changes permits correcting new addresses or the selected release. Partially created accounts are retained for recovery, not automatically deleted. Do not move the profile or perform other operations until expansion completes.

Use the complete updated profile afterward, never an older snapshot. Expanded profiles require Manager 0.6 or later; downgrading Manager is unsupported. Only consecutive Worker additions are supported, not removal, renumbering or changing existing VM addresses. The selected Worker package must support the resulting count. Service readiness is not a substitute for a real acceptance job. DB capacity limits are not increased automatically.

CLI: `prodcast-manager-cli.exe add-workers --site <original-site.json> --workers-site <proposed-site.json> --release <complete-release> --manifest-sha256 <trusted-hash> --yes`. The proposed file retains existing site settings and adds Worker entries. New SSH credentials are prompted separately.

## Older Ollama components

Old ZIP names, timestamps, compression and inner filenames may differ. Both inner payloads must match the SHA-256 hashes and sizes in the selected trusted release manifest; matching files are mapped to current names. Changed content, extra entries, duplicates, symlinks and unsafe paths remain rejected. The AI model is still checked independently.
