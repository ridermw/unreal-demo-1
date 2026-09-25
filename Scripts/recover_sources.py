"""Preserve reference provenance and inventory recovered sources without deleting files."""

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
PROVENANCE_KEYS = (
    "rendered_at", "size", "quality", "model_name", "model_version",
    "prompt_char_count", "prompt",
)


def main():
    reference = ROOT / "Art/Reference"
    reference.mkdir(parents=True, exist_ok=True)
    for name in ("target.png", "target-prompt.txt"):
        source, destination = ROOT / ".dream-loop" / name, reference / name
        if destination.exists() and destination.read_bytes() != source.read_bytes():
            raise RuntimeError(f"Refusing to overwrite different reference: {destination}")
        shutil.copy2(source, destination)
        assert source.read_bytes() == destination.read_bytes()
    provenance = json.loads((ROOT / ".dream-loop/target.png.metadata.json").read_text())
    (reference / "target.png.metadata.json").write_text(
        json.dumps({key: provenance[key] for key in PROVENANCE_KEYS}, indent=2) + "\n"
    )
    config = ROOT / "Config/DefaultEngine.ini"
    lines = config.read_text().splitlines()
    in_file_server = False
    sanitized = []
    for line in lines:
        if line.startswith("["):
            in_file_server = "AndroidFileServer" in line
        if in_file_server and line.startswith("SecurityToken="):
            continue
        if in_file_server and line.startswith(("bEnablePlugin=", "bAllowNetworkConnection=")):
            line = line.split("=")[0] + "=False"
        sanitized.append(line)
    config.write_text("\n".join(sanitized) + "\n")
    for path in sorted((ROOT / "Art/Textures").glob("*.metadata.json")):
        data = json.loads(path.read_text())
        path.write_text(json.dumps({key: data[key] for key in PROVENANCE_KEYS}, indent=2) + "\n")
    files = sorted(p for p in (ROOT / "Art").rglob("*") if p.is_file())
    report = {
        "kind": "source-assets-only-not-an-Unreal-render",
        "files": [
            {"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size,
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in files
        ],
        "mesh_groups": len(json.loads((ROOT / "Art/Models/manifest.json").read_text())["meshes"]),
        "steam_request": {
            "status": "unresolved; no output, process, request ID, or completion receipt recovered",
            "output": "Art/Textures/steam.png",
            "replacement_submitted": False,
        },
    }
    output = ROOT / "Evidence"
    output.mkdir(exist_ok=True)
    (output / "source-inventory.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Recovered {len(files)} source files; reference bytes verified; configuration sanitized.")


if __name__ == "__main__":
    main()
