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
    triangles = 0
    for obj in objects:
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        triangles += len(mesh.loop_triangles)
        evaluated.to_mesh_clear()
    group["exported_triangles"] = triangles
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
source_manifest_path = Path(bpy.data.filepath).parent / "manifest.json"
if source_manifest_path != manifest_path:
    source_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
print("SOURCE_CONTRACTS_OK", len(manifest["meshes"]))
