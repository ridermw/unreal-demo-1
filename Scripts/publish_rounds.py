"""Build the static GitHub Pages review gallery from actual Unreal evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def validate_component_audit(verdict, checklist):
    expected = {item.split(":", 1)[0] for group in checklist["groups"] for item in group["components"]}
    audit = verdict.get("component_audit", [])
    observed = [entry["id"] for entry in audit]
    if len(observed) != len(set(observed)) or set(observed) != expected:
        raise ValueError(f"Incomplete/duplicate component audit; missing={sorted(expected-set(observed))}")
    for entry in audit:
        if entry["status"] not in ("matches", "partial", "wrong", "missing", "not_visible"):
            raise ValueError(f"Invalid audit status: {entry['id']}")
        if not entry.get("target_observation") or not entry.get("actual_observation"):
            raise ValueError(f"Missing visual observations: {entry['id']}")
        if entry["status"] in ("wrong", "missing", "partial") and not entry.get("correction"):
            raise ValueError(f"Missing corrective action: {entry['id']}")


def build(root=ROOT):
    site = root / "docs"
    evidence = root / "Evidence/rounds"
    evidence.mkdir(parents=True, exist_ok=True)
    records = []
    for folder in sorted((root / ".dream-loop").glob("round-[0-9][0-9]")):
        verdict_file, image = folder / "verdict.json", folder / "unreal.png"
        if not verdict_file.is_file() or not image.is_file():
            continue
        saved = evidence / folder.name
        saved.mkdir(exist_ok=True)
        for name in ("verdict.json", "unreal.png", "performance.json"):
            if (folder / name).exists():
                shutil.copy2(folder / name, saved / name)
    for folder in sorted(evidence.glob("round-[0-9][0-9]")):
        verdict = json.loads((folder / "verdict.json").read_text())
        if int(folder.name[-2:]) >= 4:
            validate_component_audit(verdict, json.loads(
                (root / "Art/Reference/visual-checklist.json").read_text()))
        image = folder / "unreal.png"
        scores = verdict["scores"]
        total = verdict["total"]
        if abs(sum(scores.values()) - total) > .001:
            raise ValueError(f"Invalid score sum in {folder.name}")
        for key, maximum in (("composition", 3), ("lighting", 3), ("materials", 3), ("details", 1)):
            if not 0 <= scores[key] <= maximum:
                raise ValueError(f"Invalid {key} score in {folder.name}")
        destination = site / "rounds" / folder.name
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image, destination / "unreal.png")
        performance_file = folder / "performance.json"
        performance = json.loads(performance_file.read_text()) if performance_file.exists() else None
        record = {"id": folder.name, "image": f"rounds/{folder.name}/unreal.png",
                  "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                  "scores": scores, "total": total, "assessment": verdict["assessment"],
                  "fixes": verdict.get("prioritized_fixes", []),
                  "component_audit": verdict.get("component_audit", []),
                  "performance": performance,
                  "accepted": total >= 8 and bool(performance and performance.get("status") == "success"
                                                 and performance.get("meets_target"))}
        records.append(record)
    if not records:
        raise RuntimeError("No independently judged Unreal round is available")
    shutil.copy2(root / "Art/Reference/target.png", site / "target.png")
    (site / "rounds.json").write_text(json.dumps(records, indent=2) + "\n")
    (site / ".nojekyll").touch()
    print(f"Published {len(records)} round records; latest {records[-1]['total']}/10.")


if __name__ == "__main__":
    build()
