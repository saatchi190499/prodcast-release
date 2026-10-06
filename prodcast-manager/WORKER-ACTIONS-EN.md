# Individual Worker actions (preview)

Open the installed profile. On **1. Servers**, select an installed Worker and choose **Repair / reinstall worker** or **Remove worker**.

Repair requires the exact complete release installed on that Worker, not the intended upgrade release. For a Worker still on ProdCast 0.6.1 after an interrupted 0.6.2 update, select the original 0.6.1 release. Complete or stop the previous deployment operation first.

Manager pauses App scheduling and ingress, then checks that jobs have drained. It only stops/reinstalls the selected Worker. Other Worker services and App/DB containers are not reinstalled. The selected runtime is replaced while previous files, logs, credentials and Worker ID are retained.

Remove unregisters the selected service, disables its PostgreSQL login, terminates its DB connections and removes its PostgreSQL/Redis access entries. SQL roles and historical application records are retained. The profile and encrypted vault are committed together with a recoverable transaction. Worker files and logs remain on the VM for inspection. This is not a VM wipe.

At least one Worker must remain. Worker IDs are stable: removing worker2 from worker1/worker2/worker3 leaves worker1/worker3. Use Add Workers to reinstall a removed Worker on its retired VM or on a fresh VM, with the same installed-site vault. Manager verifies its database retirement receipt before restoring access. A clone with active installation state is not treated as a retired or fresh VM.

Interrupted actions are resumed with the same selected Worker and action. Keep the profile, vault and worker-action-journal.json. App scheduling may remain paused after a failure until the action is successfully resumed.

The drain check requires responses from configured consumers and empty pending work. A missing/broken consumer can block the operation. This preview does not discard jobs or bypass that check. Live VM acceptance testing is required before publishing.
