# Manager 0.3.3 — RHEL offline installation fix

- Preserve installed RHEL prerequisite versions instead of requesting an OS package upgrade from the offline UBI repository.
- Include Red Hat signed Python audit bindings matching the RHEL 9.0 DVD audit libraries. Verify the package hash and signature before installation.
- Keep existing complete-release archives, manifest hashes, installation IDs, profiles and interrupted-operation journals compatible.
- Resume an interrupted first installation with **Install**, using the original site and release. Do not create a new site or change the operation to Update.

Validated on RHEL 9.0: offline Docker installation and repeated bootstrap, SELinux Enforcing, auditd active, existing audit/curl/iproute versions and installation state preserved. The original interrupted deployment then completed through the packaged Manager: App, DB, two Windows Server 2019 Workers, and AI including model generation and the App-to-AI check. Other RHEL minor-version combinations are not covered by this VM check. Offline files were used; external network access was not firewall-blocked for this run.
