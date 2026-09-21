# ProdCast releases

Download packaged ProdCast App releases from the [Releases page](https://github.com/saatchi190499/prodcast-release/releases).

This repository contains customer distribution information. Application source
code and build history are maintained separately in private repositories.

## Installation

Choose a release and download its `prodcast-app-<VERSION>-deployment.tar.gz`
package. Extract it and follow `runtime/INSTALL-RU.md` for installation,
configuration, upgrade and rollback instructions.

- Online installation uses the exact Docker image digests recorded in
  `packages.env` and `images.json`.
- Offline installation additionally requires the matching Docker image archives
  attached to that release; follow its installation instructions.
- Use `SHA256SUMS` to verify the downloaded release files before installation.
- Create your own runtime secrets and TLS configuration. Example settings are
  templates, not customer credentials.

GitHub Container Registry access is configured separately from this repository.
If an image requires authentication, obtain read access from your distributor.
Never use a release-publishing token on a customer deployment.

## Release automation

The private App build workflow tests and packages a version, publishes its
Docker images, and uploads the finished release assets here. No application
source branch or source Git history is copied into this repository.

Versions ending in `-rc.N` are release candidates. Read each release's
installation notes and acceptance status before deployment. Other ProdCast
components may require separate compatible packages.

GitHub's automatic **Source code (zip)** and **Source code (tar.gz)** downloads
contain only the files committed to this distribution repository. Use the
deployment packages under release assets to install ProdCast.

The distributed backend includes compiled Python bytecode, which can be
reverse-engineered. Browser JavaScript and open-source integration plugins are
inspectable; this distribution is not an encryption mechanism.
