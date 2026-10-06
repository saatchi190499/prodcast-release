# ProdCast Manager 0.6 — user guide

## Start and release contents

Extract the ZIP into a writable directory and run `ProdCast-Manager.exe`. It is a standalone onefile executable; no `_internal` folder or Python installation is required. Manager stores profiles, settings, and logs in the adjacent `prodcast-data` folder. Use `prodcast-manager-cli.exe` for command-line operations.

The package includes `source.zip`, RU/EN documentation, `site.example.json`, `SHA256SUMS`, and validation reports `VALIDATION.json` and `TEST-RESULTS.xml`. Replace the example's documentation-only addresses before connecting.

Manager and ProdCast have separate version numbers. Manager 0.6 does not require selecting a ProdCast 0.6 release.

## Profiles and credentials

For an existing installation, open its original `site.json` with its original credential store. Transfer the entire profile directory, including `secrets.json`, `secrets.key`, SSH keys and journals. Do not create a replacement profile for an existing installation. Back up the profile before making changes.

Profiles and their backups contain secrets. Do not share them with logs or place them in public directories. Verify SSH fingerprints through a trusted VM console.

## Choose the correct action

| Task | Action |
| --- | --- |
| First installation on prepared VMs without an existing ProdCast installation | Install |
| Update an installed site | Update, during an agreed maintenance window |
| Add a new Windows VM as a Worker | Add Workers… |
| Save entered settings | Save configuration; this does not install anything |

## Add a Worker

1. Open the installed profile and select the complete package for the **exact installed ProdCast release**, with its trusted manifest SHA-256.
2. Increase the Worker count on the Servers tab. Up to 16 total Workers are supported when the selected Worker package permits that count.
3. Enter the new VM's IP, SSH credentials and verified host fingerprint. Preserve existing VM addresses and other site settings.
4. Click Add Workers… and confirm the new servers. Do not also click Install: `worker3: install` in the log is an internal expansion step.
5. Wait for `Workers added: worker3` or the equivalent list of added roles. Then verify a real job and operation after a reboot at an agreed time.

Expansion does not restart App, existing Workers or DB containers. It adds database access for the new Workers and preserves site identity and existing secrets. Worker removal and renumbering are unsupported. Use the updated profile and Manager 0.6 or later afterward.

If an operation fails after changes begin, retry Add Workers… with the same release and addresses. Preserve journals and credentials. A preflight-only failure permits correcting new VM settings. Do not move the profile during an unfinished operation.

## A VM cloned from another Worker

Changing the IP and Windows hostname does not remove the old ProdCast role, service or credentials. A clone with `role=worker2` and service `ProdCastWorker02` is not a clean Worker3 VM; Manager refuses automatic adoption.

Check the hostname, IP, services and recorded role through the clone's own console. Use a clean VM or a separately approved clone-cleanup procedure that verifies its address and installation ownership. Do not edit the role in JSON or reset the whole site to clean a single clone. A running cloned service can connect to the shared queue using the original Worker's credentials.

## Temporary staging cleanup warning

If `Could not clean a temporary staging directory` appears after successful `verify`, `commit`, `db: workers-commit` and `Workers added`, expansion has already completed. Do not reinstall or reset the installed Worker.

This is a known diagnostic limitation in 0.6: the warning omits the VM and underlying exception. One possible cause is root-owned temporary files on Linux followed by cleanup as the ordinary SSH user. Additional inspection is required to confirm the cause for a particular run.

Staging directories are under `C:\ProgramData\ProdCastManager\inbox` on Windows and `/var/tmp/prodcast-manager-<identifier>` on Linux. They may contain secrets. Remove only the positively identified directory of a completed operation, after checking the VM, paths and absence of active operations. Never remove the entire `ProdCastManager`, `Managed` or profile directory to address this warning. This documentation refresh does not include a cleanup implementation fix.

## Ollama components compatibility

An older Ollama ZIP is accepted when both inner files match the SHA-256 hashes and sizes in the selected trusted ProdCast manifest. The ZIP name, timestamps, ZIP compression and inner filenames may differ. Changed content and unsafe archives remain rejected. The AI model is validated separately. The real Ollama 0.4 ZIP was checked against the ProdCast 0.5.0 manifest.

## Further documentation

- `CHANGES-0.6-EN.md`: changes and Worker expansion CLI.
- `OFFLINE-EN.md`: offline packages and installation.
- `LDAP-EN.md`: LDAP / Active Directory.
- `RECOVERY-EN.md`: backup, recovery and limitations.
- `README-EN.md`: documentation entry point.

The source test run passed 387 tests, with 7 skipped because external fixtures were unavailable. Portable GUI/CLI self-tests passed. A user-provided log confirms successful Worker3 expansion; actual job execution and reboot resilience are not established by that log.
