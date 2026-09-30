# Resume and recovery — Manager 0.2.5

## A dependency installation or VM connection failed

Correct SSH/sudo/administrator permissions, network access, free space or VM resources. Reopen the **same site**, select the **same release** and repeat the original action: **Install** or **Update**. Manager retains the operation identity and retries unfinished steps. Do not create a new profile or delete the journal.

Recorded success is checked against runtime state. Docker/Compose checks run again; if a partial Docker installation left Compose missing, Manager installs the required packages. Failed dependency downloads or installations are not recorded as successful. An OS or installer problem requiring manual intervention or a reboot must still be resolved by the administrator.

## Installation completed, but containers were removed or stopped

1. Open the original site, retaining its credentials and Installation ID.
2. Select the **exact complete release currently installed** and its manifest checksum.
3. Click **Repair** and confirm the VM list.
4. Wait for App, DB and Worker verification. Enabled AI is handled separately at the end.

Manager recreates missing, stopped and unhealthy containers using saved configuration. Healthy containers are retained; the App gateway also restarts when its upstream services are recovered. Existing PostgreSQL/Redis directories and the App media volume are reused. This mode does not run migrations or change the release version. Existing images, configuration and data disks must remain on the VMs.

A missing or stopped Worker service is reinstalled into a new directory while retaining the previous directory. If a damaged Worker's service is still running, finish its jobs and stop the service first: Manager does not forcibly interrupt active jobs. Final checks verify Worker connectivity.

For an unfinished operation, repeat its original action with the original release. **Repair** is for an installed stack; it does not cancel an interrupted update. Use **Update** for version or configuration changes after recovery completes.

## What must be preserved

PostgreSQL alone is not enough: preserve Redis queues, App files, configuration, certificates and Manager's `data` folder. Missing PostgreSQL/Redis data or a missing App media volume stops recovery. Reattach the original disk or restore a backup first. Manager does not remove volumes or silently replace a known installation with an empty database.

Recreating a container does not fix network, certificate, activation or configuration errors. Manager verifies readiness afterwards; an unresolved cause leaves diagnostics and allows retrying the same operation.

A remote process may continue after SSH disconnects. Another operation remains blocked until that process finishes. A lost original profile, replaced VM or release change during an operation requires separate investigation; deleting journals is not a recovery procedure.

This version was checked locally, including simulated failures and retries. Full recovery on real VMs was not performed in this validation run.
