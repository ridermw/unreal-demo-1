"""Inspect the saved Blender source without changing it; enrich the FBX manifest."""

import json
from pathlib import Path
import bpy


ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / "Art/Models/manifest.json"
manifest = json.loads(manifest_path.read_text())
for group in manifest["meshes"]:
    objects = [obj for obj in bpy.data.objects if obj.type == "MESH"
               and obj.name.startswith(group["name"] + "_")]
    if not objects:
        raise RuntimeError(f"Source group missing: {group['name']}")
    coordinates = [obj.matrix_world @ vertex.co for obj in objects for vertex in obj.data.vertices]
    minimum = [min(p[i] for p in coordinates) for i in range(3)]
    maximum = [max(p[i] for p in coordinates) for i in range(3)]
    group["material_slots"] = sorted({slot.name for obj in objects for slot in obj.data.materials})
    group["source_bounds_m"] = {"minimum": minimum, "maximum": maximum}
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
print("SOURCE_CONTRACTS_OK", len(manifest["meshes"]))
