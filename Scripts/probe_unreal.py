import json
from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir()).resolve()
required = [
    "EditorActorSubsystem",
    "LevelEditorSubsystem",
    "EditorAssetLibrary",
    "AssetImportTask",
    "FbxImportUI",
    "MaterialEditingLibrary",
    "AutomationLibrary",
]
missing = [name for name in required if not hasattr(unreal, name)]
if missing:
    raise RuntimeError(f"Required Unreal scripting APIs unavailable: {missing}")
report = {
    "engine": unreal.SystemLibrary.get_engine_version(),
    "project": str(root),
    "required_apis": required,
    "ready": True,
}
destination = root / ".dream-loop" / "engine-probe.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(report, indent=2))
unreal.log("PLATFORM_PROBE_OK " + json.dumps(report))
