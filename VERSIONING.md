# ProdCast release versioning

This file is the required versioning policy for every future ProdCast release.
Use the exact strings described here in Git tags, workflow inputs, filenames, and
`release-manifest.json`.

## Version formats

- Stable Complete release: `vMAJOR.MINOR.PATCH` (example: `v0.6.1`).
- App and Agent candidate: `vMAJOR.MINOR.PATCH-rc.N` (example:
  `v0.6.1-rc.1`). They normally use the same candidate version.
- Worker: use the exact version of the tested Worker package. It may differ from
  App and Agent only when the release record explicitly selects that version.
  For ProdCast `v0.6.1`, Worker is `v0.6.0-rc.2`.
- Manager: its executable filename uses the stable Complete version, for example
  `ProdCast-Manager-v0.6.1.exe`.
- Every version stored in a manifest or workflow input includes the leading `v`.
  Do not write `0.6.1`, `0.6.0 rc2`, or `0.5.0rc2`.

Tags are immutable release records. After a normal release, never move, reuse,
or overwrite a tag. If a candidate is rejected, increment `N` and create a new
candidate tag.

## Main branches and release commits

Before tagging, fetch every repository and confirm that its remote `main` contains
the intended release commit. Fast-forward `main` when an approved release commit
is ahead of it. Do not include uncommitted local files.

Record the exact source commit and binary version for App, Agent, Worker, and AI
in `release-manifest.json`. A component version describes the bytes actually
built; do not relabel an older package to match the Complete version.

## Upgrade versions

The release workflow's `upgrade_from` input is a comma-separated list of exact
versions, with no spaces required. Example:

```text
v0.5.0-rc.2,v0.5.0
```

Each value is validated as `vMAJOR.MINOR.PATCH` or
`vMAJOR.MINOR.PATCH-rc.N` and is merged into
`management.upgrade_from` in the generated manifest. Only list versions for
which the upgrade path is supported and tested.

## Workflow inputs

For ProdCast `v0.6.1`, use:

| Input | Value |
|---|---|
| `version` | `v0.6.1` |
| `component_tag` | `v0.6.1-rc.1` |
| `worker_tag` | `v0.6.0-rc.2` |
| `upgrade_from` | `v0.5.0-rc.2,v0.5.0` |
| `base_tag` | `v0.6.0` |
| `base_archive` | `ProdCast-v0.6.0-complete.zip` |

`component_tag` selects App and Agent. `worker_tag` independently selects the
tested Worker contribution. The generated manifest must retain Worker binary
version `v0.6.0-rc.2`.

## Publication checks

Before publishing, verify that:

1. All component source commits match the intended remote `main` history.
2. `management.upgrade_from` contains every approved source version.
3. Worker `binary_version` is the exact selected Worker tag.
4. Complete contains Worker but no top-level Agent or Manager executable.
5. Agent and Manager are separate release assets.
6. Checksums match every published asset and temporary component assets are gone.

