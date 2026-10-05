# Creating a new ProdCast release

This guide describes the release process introduced with ProdCast v0.6.0.
The authoritative tag and manifest spelling rules are in
[`VERSIONING.md`](../VERSIONING.md) and must be applied to every release.

The final release has this layout:

- `ProdCast-vX.Y.Z-complete.zip` — containers, deployment/runtime files, and the Windows Worker package.
- `ProdCastAgent-Setup-vX.Y.Z.exe` — standalone Windows Agent installer.
- `ProdCast-Manager-vX.Y.Z.exe` — standalone single-file Windows Manager.
- `release-manifest.json`, `SHA256SUMS`, and `RELEASE-NOTES.md` — release metadata and integrity records.

Agent and Manager must never be placed inside the Complete ZIP. The Worker package remains inside Complete.

## 1. Choose the versions

Use one stable release version, one matching App/Agent candidate tag, and the
exact tested Worker tag. Worker may differ when that choice is explicitly
recorded in the release.

Example for the release after v0.6.0:

```text
Stable release:       v0.7.0
Component candidate: v0.7.0-rc.1
Worker candidate:    v0.7.0-rc.1
Upgrade from:        v0.6.0
Base release tag:    v0.6.0
Base archive:        ProdCast-v0.6.0-complete.zip
```

App and Agent normally use the same candidate tag. The `worker_tag` workflow
input records the Worker version independently; never relabel Worker bytes.

If a candidate build fails after it has uploaded different bytes, fix the source and use the next candidate number, for example `v0.7.0-rc.2`. Do not move or replace an existing candidate tag.

## 2. Prepare the source repositories

Confirm that the required changes are committed and pushed in:

- `saatchi190499/prodcast-app`
- `saatchi190499/prodcast-worker`
- `saatchi190499/prodcast-agent`
- `saatchi190499/prodcast-release` for Manager or release-workflow changes

Run each repository's tests before creating tags. The App and Worker commits should match the versions already validated in DEV.

Do not release from a working tree with uncommitted changes.

## 3. Create the central draft first

Open:

```text
https://github.com/saatchi190499/prodcast-release/releases/new
```

Create a draft with:

- Tag: the stable version, for example `v0.7.0`
- Target: `main`
- Title: `ProdCast v0.7.0`
- Draft: enabled
- Pre-release: disabled

Save it as a draft. Do not publish it yet.

The draft must exist before component tags are pushed. Component workflows intentionally refuse to create the central release themselves.

## 4. Tag App, Worker, and Agent

In each component repository, create the same annotated candidate tag on the exact commit being released.

Example:

```bash
git status --short
git fetch origin --tags
git tag -a v0.7.0-rc.1 -m "ProdCast v0.7.0 release candidate 1"
git push origin refs/tags/v0.7.0-rc.1
```

Run those commands separately in:

- `prodcast-app`
- `prodcast-worker`
- `prodcast-agent`

Even when Agent has no functional changes, create its matching candidate tag. This produces an Agent installer whose filename and embedded version match the new release.

Never reuse or force-move a published candidate tag. Use `rc.2`, `rc.3`, and so on after a source fix.

## 5. Wait for component workflows

Open the Actions page in each repository and wait for these workflows:

- App: `Release packages`
- Worker: `Release Windows package`
- Agent: `Release Windows package`

All three workflows must finish successfully.

They build and validate the component packages, then upload six temporary assets to the central draft:

```text
prodcast-app-v0.7.0-rc.1-component.json
prodcast-app-v0.7.0-rc.1-component.zip
prodcast-worker-v0.7.0-rc.1-component.json
prodcast-worker-v0.7.0-rc.1-component.zip
prodcast-agent-v0.7.0-rc.1-component.json
prodcast-agent-v0.7.0-rc.1-component.zip
```

Do not start final assembly until all six assets exist.

## 6. Run final assembly

Open the Actions page in `prodcast-release`:

```text
https://github.com/saatchi190499/prodcast-release/actions/workflows/release.yml
```

Choose **Run workflow**, select `main`, and enter:

| Input | Example |
|---|---|
| `version` | `v0.7.0` |
| `component_tag` | `v0.7.0-rc.1` |
| `worker_tag` | `v0.7.0-rc.1` |
| `upgrade_from` | `v0.6.0` |
| `base_tag` | `v0.6.0` |
| `base_archive` | `ProdCast-v0.6.0-complete.zip` |

Start the workflow named **Build and assemble ProdCast release**.

The workflow performs these operations:

1. Runs the complete Manager test suite on Windows.
2. Builds GUI and CLI Manager binaries with Python 3.11.
3. Runs the packaged Manager GUI/resource smoke test.
4. Produces a single-file `ProdCast-Manager.exe`.
5. Downloads and verifies the previous Complete archive.
6. Downloads and verifies the App, Worker, and Agent component candidates.
7. Replaces App and Worker in Complete.
8. Keeps Worker inside Complete.
9. Moves Agent and Manager to separate EXE assets.
10. Rejects the build if any top-level EXE remains inside Complete.
11. Generates the manifest, release notes, and SHA-256 checksums.
12. Uploads the final assets and removes the six temporary component assets.

## 7. Verify the draft

The draft must contain exactly these six assets:

```text
ProdCast-v0.7.0-complete.zip
ProdCastAgent-Setup-v0.7.0.exe
ProdCast-Manager-v0.7.0.exe
release-manifest.json
RELEASE-NOTES.md
SHA256SUMS
```

Check the following before publication:

- The assembly workflow completed successfully.
- Complete has a SHA-256 digest and a plausible size.
- Agent and Manager are separate `.exe` assets.
- `release-manifest.json` contains the intended App, Worker, and Agent source commits.
- The manifest lists the Worker ZIP with `location: complete`.
- The manifest lists Agent and Manager with `location: release-asset`.
- The manifest does not list a top-level `.exe` with `location: complete`.
- No temporary `*-component.json` or `*-component.zip` assets remain.

Keep the draft unpublished if any check is wrong.

## 8. Publish the release

On the draft release page:

1. Review the release title and notes.
2. Confirm **Set as the latest release**.
3. Confirm **Pre-release** is disabled for a stable version.
4. Select **Publish release**.

After publication, verify:

```text
https://github.com/saatchi190499/prodcast-release/releases/latest
```

The page must resolve to the new version and show all six assets.

## 9. Failure handling

If a component workflow fails before uploading its candidate, fix the component and push a new candidate tag such as `v0.7.0-rc.2`.

If final assembly fails, leave the stable release as a draft. Fix `prodcast-release/main`, then run **Build and assemble ProdCast release** again with the same inputs. The final assets are uploaded only after integrity checks pass.

If final assets were partially uploaded, inspect the draft before retrying. Do not publish a draft containing duplicate, stale, or incomplete assets.

Published releases are immutable release records. Do not replace their binaries. Create the next version instead.

## Current limitation

The v0.6 release assembler updates App, Worker, and Agent and reuses AI and offline infrastructure from the selected base release. If AI or offline infrastructure changes, extend and test the assembler before creating component tags.
