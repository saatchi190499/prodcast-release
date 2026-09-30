# ProdCast Manager 0.3.4

- New bilingual LDAP / Active Directory settings window on the Site tab.
- Encrypted service account and CA storage per site, without changing installation identity.
- Read-only LDAPS tests from the App VM: certificate/hostname verification, service bind, base DN, group, test login and nested AD group membership.
- Probe dependencies bundled for offline use; no package installation or sudo required for these tests.
- Test passwords are cleared from the form and excluded from saved settings and logs.
- Scope: preparation and diagnostics only. App code, containers, authentication, user synchronization and session revocation are unchanged. Separate App integration is required.
