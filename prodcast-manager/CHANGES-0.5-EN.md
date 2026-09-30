# ProdCast Manager 0.5

Local build for App, Agent, Worker and AI from tag v0.5.0-rc.2. Nothing is published automatically.

## Installation files

Select the complete ZIP and enter the SHA256 of release-manifest.json. The complete archive includes Ollama and offline system dependencies for the platforms listed in its manifest. Archives larger than 2 GB are supported. If AI is selected, choose the Qwen3 4B Instruct model file in the third field. The second field accepts a separate Ollama archive when the release manifest declares one. Leave it empty for complete ZIPs with embedded Ollama.

## Domain login

Open Site → LDAP / Active Directory and select Enable domain login in App. Enter the controller's LDAPS URL, user domain, search base DN and allowed group DN. Import the controller's public CA chain when using an internal CA. This is separate from the App website PFX. Without an imported CA, App uses its container's trust store; trusting a certificate on the Windows PC does not configure App trust.

The service account is used for Manager diagnostics. App checks the password and group using the signing-in user's connection. Test passwords are not saved; the service account password is not sent to App. Run the connection and user checks, save, then select Install or Update. Saving alone does not change servers. Settings are stored in the App database and are also visible in its admin interface. A later Manager update reapplies its saved directory settings.

Use userPrincipalName for the AD lookup attribute when UPN is populated. Select sAMAccountName for accounts without a UPN. Both App VM and its containers must resolve the controller's name through internal DNS. Manager does not change DNS automatically.

Nested AD groups are supported. Primary-group membership is not included; use a dedicated ProdCast group. App v0.5.0-rc.2 does not recheck directory access for existing sessions after group changes or account disablement. This Manager build does not add session revalidation.

## Export and restore data

Export backup saves one .pcbackup file to a folder of your choice. Set a password of at least 12 characters and keep it separately. The file is encrypted and cannot be recovered without its password.

The backup contains the main PostgreSQL database dump, App user files, App configuration and the site identity/encryption keys. User attachments are included even when large. Ollama models, Docker images, installers, AI caches, Worker binaries and SSH passwords are excluded. Integration data stored outside the managed database and App media volume needs a separate backup.

For a consistent export, Manager pauses the site and scheduler, drains work queues, then stops App and Workers. It restarts previously running containers and services after export.

Restore backup replaces an existing installation's data. Use the original site and the exact complete release recorded in the backup. Password, integrity, Installation ID, encryption keys and version are checked before changes. Manager creates safety copies on the VMs before restoring. If restore fails, App and Workers remain stopped. Fix the cause and retry the same backup. There is no automatic database rollback.

If the Manager folder is lost, use Import backup profile, enter the backup password and provide SSH credentials again. Import creates a new local profile without changing VMs. For clean VMs, first install the original complete release, then restore the backup. Original addresses, Installation ID and activation are retained. Migration to different addresses or directly into a different release is not supported by this restore workflow. Upgrade separately after recovery.

## Reset VMs

Reset stops running jobs. If a Worker service cannot stop gracefully, Manager verifies that its process belongs to the selected installation and terminates only that process tree. Automatic service restart is disabled during reset. Retry the same reset mode after a failure.

- **Recreate components, keep data:** removes managed containers and Worker service registrations while keeping the database, App files and models. Use Repair with the exact installed release afterwards. For an interrupted first install, resume the original installation.
- **Full reset:** removes managed containers and active ProdCast data, including the database, App files and AI models. Type the site name to confirm. Then use Install again. The local Manager profile and activation are retained.

Reset affects ProdCast, not the operating system. OS, network, SSH, Docker/Python, system settings and existing server-side backups remain. Full reset does not erase backup history. Unrelated containers/services are not removed. All selected VMs are checked for installation ownership before reset starts.

You can copy .pcbackup to another PC. Store the file and its password separately and never distribute a private backup with the public installation bundle.
