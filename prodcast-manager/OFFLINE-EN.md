# Offline installation: ProdCast v0.5.0-rc.2

1. Bring the complete ZIP (Ollama included) and, if AI is required, the Qwen3 4B Instruct model file into the offline network. No separate Ollama ZIP is needed.
2. Extract the entire Manager folder to a writable location and run ProdCast-Manager.exe. For an existing installation, import its original site.json with its data folder or transfer the complete data folder to the new Manager. Do not create a new identity over an existing deployment.
3. Configure App, DB, 1–16 Workers and optional AI. Verify SSH fingerprints. Linux needs root or sudo; Workers need a Windows administrator.
4. Import the issued offline license and public signature PEM. For a new site, request a license for the Installation ID shown by Manager. Import the website PFX and its DNS name. Client PCs must already trust its public CA.
5. For domain login, configure LDAP / Active Directory and select Enable domain login in App. See CHANGES-0.5-EN.md.
6. Select the complete ZIP in the first field and enter the SHA256 of release-manifest.json. If AI is enabled, select the model file in the third field. ZIP files larger than 2 GB are supported.
7. Check access. Choose Install for clean VMs or Update for an existing site. After fixing an error, retry the same operation with its original profile and release.
8. Wait for the App/DB/Workers result and the separate AI result. AI failure does not invalidate a successful core deployment. AI uses an available supported GPU driver or CPU; Manager does not install GPU drivers.

This bundle contains offline dependencies for Ubuntu 22.04, Ubuntu 26.04 and RHEL 9, plus Windows Server 2019/2022/2025 x64. Debian and Ubuntu 24.04 packages are not included in this particular bundle. Prepare OS, OS updates, SSH, GPU drivers and external engineering applications in advance.

See CHANGES-0.5-EN.md for backup/restore and reset. Models and installers are excluded from backups. Profiles are stored in data and logs in logs next to Manager. Keep the original complete ZIP for backup recovery.
