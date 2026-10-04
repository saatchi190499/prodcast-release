"""Assemble a ProdCast release with Agent and Manager as standalone EXE assets."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile


REPOSITORY = "saatchi190499/prodcast-release"
COMPONENTS = {"app", "agent", "worker"}


def sha256(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_name(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
        raise ValueError(f"Unsafe artifact name: {value!r}")
    return value


def validate_version(value: str) -> str:
    if not re.fullmatch(r"v\d+\.\d+\.\d+", value):
        raise ValueError("Release version must use vX.Y.Z")
    return value


def record(path: Path, **extra: object) -> dict[str, object]:
    path = Path(path)
    return {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path), **extra}


def write_json(path: Path, value: object) -> None:
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def verify(folder: Path, item: dict[str, object]) -> Path:
    path = Path(folder) / validate_name(str(item["name"]))
    if path.is_symlink() or not path.is_file() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
        raise ValueError(f"Artifact integrity failed: {path.name}")
    return path


def unpack(archive: Path, destination: Path) -> None:
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as source:
        names: set[str] = set()
        for item in source.infolist():
            name = validate_name(item.filename)
            mode = item.external_attr >> 16
            if name in names or item.is_dir() or stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise ValueError(f"Unsafe ZIP member: {name}")
            names.add(name)
        for item in source.infolist():
            with source.open(item) as src, (destination / item.filename).open("wb") as dst:
                shutil.copyfileobj(src, dst)


def pack(folder: Path, output: Path, names: list[str]) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for name in sorted(names):
            path = Path(folder) / validate_name(name)
            if path.is_symlink() or not path.is_file():
                raise ValueError("Only regular files can be packaged")
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            with path.open("rb") as src, archive.open(info, "w", force_zip64=True) as dst:
                shutil.copyfileobj(src, dst)


def component_file(component: str, name: str) -> bool:
    prefixes = {
        "app": ("prodcast-app-", "prodcast-backend-", "prodcast-frontend-", "prodcast-gateway-"),
        "agent": ("prodcast-agent-", "ProdCastAgent-", "workflow-agent-"),
        "worker": ("prodcast-worker-",),
    }
    return name.startswith(prefixes[component])


def manager_file(name: str) -> bool:
    return name.lower().startswith("prodcast-manager-")


def declared_external_payloads(manifest: dict) -> set[str]:
    """Return only payload names whose bytes are explicitly stored outside Complete."""
    offline = manifest.get("management", {}).get("offline", {})
    names: set[str] = set()
    if offline.get("external_ollama"):
        for key in ("ollama_runtime", "model_archive"):
            value = offline.get(key)
            if isinstance(value, str):
                names.add(value)
    external_model = offline.get("external_model")
    if isinstance(external_model, dict) and isinstance(external_model.get("name"), str):
        names.add(external_model["name"])
    return names


def contribution(descriptor_path: Path, archive_path: Path, component: str) -> tuple[dict, Path]:
    descriptor = json.loads(Path(descriptor_path).read_text(encoding="utf-8"))
    if descriptor.get("component") != component or descriptor.get("repository") != f"saatchi190499/prodcast-{component}":
        raise ValueError(f"Wrong {component} descriptor")
    if Path(archive_path).name != descriptor["archive"]["name"]:
        raise ValueError(f"Wrong {component} contribution archive")
    verify(Path(archive_path).parent, descriptor["archive"])
    return descriptor, Path(archive_path)


def load_payload(root: Path, component: str, descriptor: dict, archive: Path) -> tuple[Path, dict]:
    payload = root / f"input-{component}"
    unpack(archive, payload)
    manifest_path = payload / "release-manifest.json"
    if sha256(manifest_path) != descriptor["build_manifest_sha256"]:
        raise ValueError(f"{component} source manifest checksum mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if any(manifest.get(key) != descriptor.get(key) for key in ("repository", "version", "source_commit")):
        raise ValueError(f"{component} provenance mismatch")
    names = [item["name"] for item in manifest["artifacts"]]
    if len(names) != len(set(names)) or {"release-manifest.json", "SHA256SUMS"} & set(names):
        raise ValueError(f"Invalid {component} artifact list")
    for item in manifest["artifacts"]:
        verify(payload, item)
    if {p.name for p in payload.iterdir()} != set(names) | {"release-manifest.json", "SHA256SUMS"}:
        raise ValueError(f"Unexpected files in {component} contribution")
    return payload, manifest


def mapped_name(component: str, name: str, source_tag: str, target: str) -> str:
    validate_name(name)
    if name == "release-manifest.json":
        return f"prodcast-{component}-source-manifest.json"
    if name in {"images.json", "packages.env", "INSTALL-RU.md", "INSTALL-EN.md"}:
        return f"prodcast-{component}-{name}"
    if not component_file(component, name):
        raise ValueError(f"Unexpected {component} artifact: {name}")
    return name.replace(source_tag, target)


def build(version: str, base_archive: Path, descriptors: dict[str, Path], archives: dict[str, Path], manager_exe: Path, output: Path) -> dict[str, Path]:
    """Build and verify release assets without contacting GitHub."""
    target = validate_version(version)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    contents = output / "contents"
    unpack(Path(base_archive), contents)
    manifest_path = contents / "release-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_version = manifest.get("version")

    controls = {"release-manifest.json", "release-manifest.json.sha256", "SHA256SUMS"}
    declared_external = declared_external_payloads(manifest)
    for item in manifest["artifacts"]:
        path = contents / validate_name(str(item["name"]))
        if item["name"] in declared_external or item.get("location", "complete") != "complete":
            continue
        if not path.is_file():
            raise ValueError(f"Required Complete artifact is missing: {path.name}")
        else:
            verify(contents, item)

    components = {item["component"]: copy.deepcopy(item) for item in manifest["components"]}
    if not {"app", "agent", "worker"} <= components.keys():
        raise ValueError("Base release is missing a required component")
    external = [copy.deepcopy(item) for item in manifest["artifacts"] if (item.get("location", "complete") != "complete" or item["name"] in declared_external) and not component_file("agent", str(item["name"])) and not manager_file(str(item["name"]))]

    for old in list(contents.iterdir()):
        if component_file("agent", old.name) or manager_file(old.name):
            old.unlink()

    for component in ("app", "worker", "agent"):
        descriptor, archive = contribution(descriptors[component], archives[component], component)
        payload, build_manifest = load_payload(output, component, descriptor, archive)
        artifact_names = [item["name"] for item in build_manifest["artifacts"]]
        mapping: dict[str, str] = {}
        if component == "agent":
            installers = [name for name in artifact_names if name.startswith("ProdCastAgent-Setup-") and name.endswith(".exe")]
            if len(installers) != 1:
                raise ValueError("Agent contribution must contain exactly one setup EXE")
            destination = output / f"ProdCastAgent-Setup-{target}.exe"
            shutil.copyfile(payload / installers[0], destination)
            mapping[installers[0]] = destination.name
        else:
            for old in list(contents.iterdir()):
                if component_file(component, old.name):
                    old.unlink()
            for name in artifact_names + ["release-manifest.json"]:
                destination_name = mapped_name(component, name, descriptor["version"], target)
                if (contents / destination_name).exists():
                    raise ValueError(f"Artifact collision: {destination_name}")
                shutil.copyfile(payload / name, contents / destination_name)
                mapping[name] = destination_name
        components[component] = {
            "component": component,
            "repository": descriptor["repository"],
            "source_commit": descriptor["source_commit"],
            "binary_version": descriptor["version"],
            "images": json.loads((payload / "images.json").read_text()) if (payload / "images.json").exists() else [],
            "source_release": f"https://github.com/{REPOSITORY}/releases/tag/{target}",
            "artifact_mapping": mapping,
        }

    manager_output = output / f"ProdCast-Manager-{target}.exe"
    if Path(manager_exe).suffix.lower() != ".exe" or not Path(manager_exe).is_file():
        raise ValueError("Manager build did not produce an EXE")
    shutil.copyfile(manager_exe, manager_output)
    if any(path.suffix.lower() == ".exe" for path in contents.iterdir()):
        raise ValueError("Complete ZIP may not contain top-level EXE files")

    manifest["version"] = target
    manifest["status"] = "complete"
    manifest["publication_status"] = "draft"
    manifest["production_accepted"] = False
    manifest["created_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["components"] = list(components.values())
    manifest["assembly_source"] = {
        "base_version": base_version,
        "changed_components": ["app", "agent", "worker"],
        "standalone_executables": [f"ProdCastAgent-Setup-{target}.exe", f"ProdCast-Manager-{target}.exe"],
    }
    manifest.setdefault("management", {})["recommended_manager"] = target.removeprefix("v")
    manifest["management"]["distribution"] = "standalone-exe"
    external += [record(output / f"ProdCastAgent-Setup-{target}.exe", location="release-asset"), record(manager_output, location="release-asset")]
    manifest["artifacts"] = external + [record(path, location="complete") for path in sorted(contents.iterdir()) if path.name not in controls]
    write_json(manifest_path, manifest)
    (contents / "release-manifest.json.sha256").write_text(f"{sha256(manifest_path)}  release-manifest.json\n", encoding="utf-8")
    (contents / "SHA256SUMS").write_text("".join(f"{sha256(path)}  {path.name}\n" for path in sorted(contents.iterdir()) if path.name != "SHA256SUMS"), encoding="utf-8")

    complete = output / f"ProdCast-{target}-complete.zip"
    pack(contents, complete, [path.name for path in contents.iterdir()])
    shutil.copyfile(manifest_path, output / "release-manifest.json")
    (output / "SHA256SUMS").write_text("".join(f"{sha256(path)}  {path.name}\n" for path in (complete, output / f"ProdCastAgent-Setup-{target}.exe", manager_output, output / "release-manifest.json")), encoding="utf-8")
    notes = output / "RELEASE-NOTES.md"
    notes.write_text(
        f"# ProdCast {target}\n\n"
        "The Complete archive contains the container/deployment payload and the Windows Worker package. Agent and Manager are separate standalone executables and are not stored inside Complete.\n\n"
        f"- `ProdCast-{target}-complete.zip` — containers, deployment files, and Worker\n"
        f"- `ProdCastAgent-Setup-{target}.exe` — Windows Agent installer\n"
        f"- `ProdCast-Manager-{target}.exe` — standalone Windows Manager\n\n"
        f"Manager manifest SHA256: `{sha256(manifest_path)}`\n",
        encoding="utf-8",
    )
    return {"complete": complete, "agent": output / f"ProdCastAgent-Setup-{target}.exe", "manager": manager_output, "manifest": output / "release-manifest.json", "checksums": output / "SHA256SUMS", "notes": notes}


def gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "GitHub CLI failed")
    return result.stdout


def download(tag: str, name: str, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    gh("release", "download", tag, "--repo", REPOSITORY, "--pattern", validate_name(name), "--dir", str(destination))
    path = destination / name
    if not path.is_file():
        raise ValueError(f"Missing release asset: {name}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--base-tag", required=True)
    parser.add_argument("--base-archive", required=True)
    parser.add_argument("--component-tag", required=True)
    parser.add_argument("--manager-exe", required=True)
    parser.add_argument("--output", default="dist/assembled")
    args = parser.parse_args()
    target = validate_version(args.version)
    output = Path(args.output).resolve()
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        base = download(args.base_tag, args.base_archive, temp / "base")
        descriptors: dict[str, Path] = {}
        archives: dict[str, Path] = {}
        for component in sorted(COMPONENTS):
            stem = f"prodcast-{component}-{args.component_tag}-component"
            descriptors[component] = download(target, stem + ".json", temp / component)
            archives[component] = download(target, stem + ".zip", temp / component)
        assets = build(target, base, descriptors, archives, Path(args.manager_exe), output)
        paths = [assets[key] for key in ("complete", "agent", "manager", "manifest", "checksums", "notes")]
        gh("release", "upload", target, *map(str, paths), "--repo", REPOSITORY)
        gh("release", "edit", target, "--repo", REPOSITORY, "--title", f"ProdCast {target}", "--notes-file", str(assets["notes"]))
        for component in sorted(COMPONENTS):
            stem = f"prodcast-{component}-{args.component_tag}-component"
            gh("release", "delete-asset", target, stem + ".json", "--repo", REPOSITORY, "--yes")
            gh("release", "delete-asset", target, stem + ".zip", "--repo", REPOSITORY, "--yes")
        print(json.dumps({key: {"name": path.name, "sha256": sha256(path)} for key, path in assets.items()}, indent=2))


if __name__ == "__main__":
    main()
