"""Build the static GitHub Pages review gallery from actual Unreal evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def matching_runtime_evidence(capture,performance):
    if not capture or not performance:
        return False
    keys=("frame_cap","one_frame_thread_lag","resolution","screen_percentage","runtime_settings")
    return bool(capture.get("status")=="success" and performance.get("status")=="success"
                and capture.get("view")=="target" and performance.get("view")=="target"
                and capture.get("camera_label")==performance.get("camera_label")=="PN_TargetCamera"
                and capture.get("clean_editor_verified") and performance.get("provenance_finalized")
                and all(capture.get(key) is not None and capture.get(key)==performance.get(key) for key in keys)
                and capture.get("scene_identity") and capture["scene_identity"]==performance.get("scene_identity"))


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
        for name in ("verdict.json", "unreal.png", "performance.json", "capture.json"):
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
        capture_file=folder/"capture.json"
        capture=json.loads(capture_file.read_text()) if capture_file.exists() else None
        image_hash=hashlib.sha256(image.read_bytes()).hexdigest()
        capture_valid=bool(capture and capture.get("status")=="success"
                           and capture.get("sha256")==image_hash and capture.get("scene_identity"))
        if int(folder.name[-2:])>=9 and not capture_valid:
            raise ValueError(f"Round {folder.name} lacks a successful matching capture receipt")
        matching_evidence=bool(capture_valid and matching_runtime_evidence(capture,performance))
        record = {"id": folder.name, "image": f"rounds/{folder.name}/unreal.png",
                  "sha256": image_hash,
                  "scores": scores, "total": total, "assessment": verdict["assessment"],
                  "fixes": verdict.get("prioritized_fixes", []),
                  "component_audit": verdict.get("component_audit", []),
                  "performance": performance,
                  "capture": capture, "matching_capture_and_performance": matching_evidence,
                  "accepted": total >= 8 and bool(performance and performance.get("status") == "success"
                                                 and performance.get("meets_target") and matching_evidence)}
        records.append(record)
    if not records:
        raise RuntimeError("No independently judged Unreal round is available")
    shutil.copy2(root / "Art/Reference/target.png", site / "target.png")
    (site / "rounds.json").write_text(json.dumps(records, indent=2) + "\n")
    inspections=[]
    for receipt in sorted((root/"Evidence").glob("inspection-final-*.json")):
        metadata=json.loads(receipt.read_text())
        image=receipt.with_suffix(".png")
        if metadata.get("status")!="success" or not metadata.get("clean_editor_verified"):
            raise ValueError(f"Inspection capture is not verified: {receipt.name}")
        if hashlib.sha256(image.read_bytes()).hexdigest()!=metadata.get("sha256"):
            raise ValueError(f"Inspection image changed after capture: {image.name}")
        folder=site/"inspections"
        folder.mkdir(exist_ok=True)
        shutil.copy2(image,folder/image.name)
        inspections.append({"view":metadata["view"],"image":"inspections/"+image.name,
                            "fov":metadata["fov"],"scene_identity":metadata["scene_identity"],
                            "sha256":metadata["sha256"]})
    (site/"inspections.json").write_text(json.dumps(inspections,indent=2)+"\n")
    (site / ".nojekyll").touch()
    print(f"Published {len(records)} round records; latest {records[-1]['total']}/10.")


if __name__ == "__main__":
    build()
