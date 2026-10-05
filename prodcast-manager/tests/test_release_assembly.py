import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "release"))
from assemble import build, pack, record, sha256, write_json


COMMIT = "a" * 40
RC = "v0.6.0-rc.1"


def payload(root, component, names):
    folder = root / component
    folder.mkdir()
    for name in names:
        (folder / name).write_bytes((component + name).encode())
    write_json(folder / "release-manifest.json", {"repository": f"saatchi190499/prodcast-{component}", "version": RC, "source_commit": COMMIT, "artifacts": [record(path) for path in sorted(folder.iterdir())]})
    (folder / "SHA256SUMS").write_text("checksums")
    archive = root / f"prodcast-{component}-{RC}-component.zip"
    pack(folder, archive, [path.name for path in folder.iterdir()])
    descriptor = root / f"prodcast-{component}-{RC}-component.json"
    write_json(descriptor, {"component": component, "repository": f"saatchi190499/prodcast-{component}", "version": RC, "source_commit": COMMIT, "archive": record(archive), "build_manifest_sha256": sha256(folder / "release-manifest.json")})
    return descriptor, archive


def base(root):
    folder = root / "base"
    folder.mkdir()
    for name in ("prodcast-backend-v0.5.0-linux-amd64.tar.gz", "prodcast-worker-v0.5.0-windows-amd64.zip", "ProdCastAgent-Setup-v0.5.0.exe", "ProdCast-Manager-0.5.zip", "offline-database-images.tar"):
        (folder / name).write_bytes(name.encode())
    external = {"name": "offline-ollama.tar.xz", "bytes": 123, "sha256": "c" * 64}
    manifest = {"version": "v0.5.0", "management": {"schema": 3, "recommended_manager": "0.5", "offline": {"external_ollama": {"name": "ollama-components.zip"}, "ollama_runtime": external["name"], "model_archive": "ollama-model-metadata.tar"}}, "components": [{"component": name, "source_commit": "b" * 40, "binary_version": "v0.5.0"} for name in ("app", "agent", "worker", "ai", "license")], "artifacts": [record(path, location="complete") for path in sorted(folder.iterdir())] + [external]}
    write_json(folder / "release-manifest.json", manifest)
    archive = root / "base.zip"
    pack(folder, archive, [path.name for path in folder.iterdir()])
    return archive


def test_complete_excludes_agent_and_manager_executables(tmp_path):
    descriptors = {}
    archives = {}
    descriptors["app"], archives["app"] = payload(tmp_path, "app", [f"prodcast-backend-{RC}-linux-amd64.tar.gz"])
    descriptors["worker"], archives["worker"] = payload(tmp_path, "worker", [f"prodcast-worker-{RC}-windows-amd64.zip"])
    descriptors["agent"], archives["agent"] = payload(tmp_path, "agent", [f"ProdCastAgent-Setup-{RC}.exe", "workflow-agent-sbom.cdx.json"])
    manager = tmp_path / "ProdCast-Manager.exe"
    manager.write_bytes(b"manager")
    assets = build(
        "v0.6.0", base(tmp_path), descriptors, archives, manager, tmp_path / "out",
        ["v0.5.0-rc.2", "v0.5.0"],
    )
    with zipfile.ZipFile(assets["complete"]) as archive:
        names = archive.namelist()
        assert not any(name.lower().endswith(".exe") for name in names)
        assert not any(name.startswith("ProdCastAgent-") for name in names)
        assert not any(name.lower().startswith("prodcast-manager-") for name in names)
        assert "prodcast-worker-v0.6.0-windows-amd64.zip" in names
        manifest = json.loads(archive.read("release-manifest.json"))
    external = {item["name"] for item in manifest["artifacts"] if item.get("location") == "release-asset"}
    assert external == {"ProdCastAgent-Setup-v0.6.0.exe", "ProdCast-Manager-v0.6.0.exe"}
    assert any(item["name"] == "offline-ollama.tar.xz" for item in manifest["artifacts"])
    assert {"v0.5.0-rc.2", "v0.5.0"} <= set(manifest["management"]["upgrade_from"])
    worker = next(item for item in manifest["components"] if item["component"] == "worker")
    assert worker["binary_version"] == RC
    assert assets["manager"].read_bytes() == b"manager"
