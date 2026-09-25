"""Run in Unreal's Python console: py ".../Scripts/build_unreal.py" --stage import"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
import sys


ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/Platform"
MAP = BASE + "/Maps/HiddenPlatform"


def source_manifest(root=ROOT):
    manifest = json.loads((root / "Art/Models/manifest.json").read_text())
    names = [mesh["name"] for mesh in manifest["meshes"]]
    if len(names) != len(set(names)) or len(names) != 14:
        raise ValueError("Expected fourteen uniquely named mesh groups")
    for mesh in manifest["meshes"]:
        path = (root / mesh["file"]).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise FileNotFoundError(f"Required mesh source missing or outside project: {mesh['file']}")
    for material in manifest["materials"].values():
        if material["texture"]:
            path = root / "Art/Textures" / (material["texture"] + ".png")
            if not path.is_file():
                raise FileNotFoundError(f"Required generated texture missing: {path}")
    return manifest


def save_report(stage, report):
    report["stage"] = stage
    report["utc"] = datetime.now(timezone.utc).isoformat()
    directory = ROOT / "Evidence"
    directory.mkdir(exist_ok=True)
    (directory / f"{stage}-report.json").write_text(json.dumps(report, indent=2) + "\n")


def validate_mesh_record(source, record):
    if record["lod0_triangles"] <= 0:
        raise ValueError(f"Empty mesh: {source['name']}")
    if sorted(slot["slot"] for slot in record["slots"]) != source["material_slots"]:
        raise ValueError(f"Material slot mismatch: {source['name']}")
    bounds = source["source_bounds_m"]
    center = [(lo + hi) * 50 for lo, hi in zip(bounds["minimum"], bounds["maximum"])]
    center[1] *= -1
    extent = [(hi - lo) * 50 for lo, hi in zip(bounds["minimum"], bounds["maximum"])]
    for expected, actual in ((center, record["center_cm"]), (extent, record["extent_cm"])):
        if any(abs(a - b) > 5 for a, b in zip(expected, actual)):
            raise ValueError(f"Scale/orientation mismatch on {source['name']}: {actual} vs {expected}")


def import_assets(unreal, manifest):
    library = unreal.EditorAssetLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    editing = unreal.MaterialEditingLibrary

    def asset(path):
        result = library.load_asset(path)
        if result is None:
            raise RuntimeError(f"Cannot load required Unreal asset: {path}")
        return result

    textures = {}
    for name in sorted({m["texture"] for m in manifest["materials"].values()} - {None}):
        path = f"{BASE}/Textures/T_{name}"
        if not library.does_asset_exist(path):
            task = unreal.AssetImportTask()
            task.filename = str(ROOT / "Art/Textures" / (name + ".png"))
            task.destination_path = BASE + "/Textures"
            task.destination_name = "T_" + name
            task.automated = True
            task.save = True
            tools.import_asset_tasks([task])
            if not task.imported_object_paths:
                raise RuntimeError(f"Texture import returned no objects: {name}")
        textures[name] = asset(path)

    materials = {}
    for name, spec in manifest["materials"].items():
        path = f"{BASE}/Materials/M_{name}"
        if library.does_asset_exist(path):
            materials[name] = asset(path)
            continue
        material = tools.create_asset("M_" + name, BASE + "/Materials",
                                      unreal.Material, unreal.MaterialFactoryNew())
        if material is None:
            raise RuntimeError(f"Cannot create material {name}")

        def scalar(value, x, y):
            expression = editing.create_material_expression(
                material, unreal.MaterialExpressionConstant, x, y)
            expression.r = value
            return expression

        color = editing.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -600, 0)
        color.constant = unreal.LinearColor(*spec["color"], 1.0)
        base = color
        if spec["texture"]:
            texture = editing.create_material_expression(
                material, unreal.MaterialExpressionTextureSample, -850, -200)
            texture.texture = textures[spec["texture"]]
            if name in ("Brick", "Stone", "Scarlet", "Leather", "DarkLeather", "Wood"):
                base = texture
            else:
                grayscale = editing.create_material_expression(
                    material, unreal.MaterialExpressionDesaturation, -600, -200)
                if not editing.connect_material_expressions(texture, "", grayscale, ""):
                    raise RuntimeError(f"Cannot wire texture into {name} desaturation")
                multiply = editing.create_material_expression(
                    material, unreal.MaterialExpressionMultiply, -350, 0)
                editing.connect_material_expressions(grayscale, "", multiply, "A")
                editing.connect_material_expressions(color, "", multiply, "B")
                base = multiply
        editing.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
        editing.connect_material_property(scalar(spec["metallic"], -300, 200), "",
                                           unreal.MaterialProperty.MP_METALLIC)
        editing.connect_material_property(scalar(spec["roughness"], -300, 300), "",
                                           unreal.MaterialProperty.MP_ROUGHNESS)
        if name in ("Glass", "AmberGlass"):
            material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            material.set_editor_property("two_sided", True)
            editing.connect_material_property(scalar(0.20 if name == "Glass" else 0.48, -300, 400),
                                               "", unreal.MaterialProperty.MP_OPACITY)
        if name == "Lamp":
            emission = editing.create_material_expression(
                material, unreal.MaterialExpressionMultiply, -300, 500)
            editing.connect_material_expressions(color, "", emission, "A")
            editing.connect_material_expressions(scalar(12.0, -600, 600), "", emission, "B")
            editing.connect_material_property(emission, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        editing.recompile_material(material)
        if not library.save_loaded_asset(material):
            raise RuntimeError(f"Material save failed: {path}")
        materials[name] = material

    material_checks = []
    for name, material in materials.items():
        spec = manifest["materials"][name]
        required = [unreal.MaterialProperty.MP_BASE_COLOR, unreal.MaterialProperty.MP_METALLIC,
                    unreal.MaterialProperty.MP_ROUGHNESS]
        if name in ("Glass", "AmberGlass"):
            required.append(unreal.MaterialProperty.MP_OPACITY)
        if name == "Lamp":
            required.append(unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        for property_ in required:
            if editing.get_material_property_input_node(material, property_) is None:
                raise RuntimeError(f"Missing graph input {property_} on {name}")
        expressions = editing.get_material_expressions(material)
        for node in expressions:
            if isinstance(node, unreal.MaterialExpressionDesaturation):
                texture_nodes = [n for n in expressions if isinstance(n, unreal.MaterialExpressionTextureSample)]
                if len(texture_nodes) != 1 or not editing.connect_material_expressions(texture_nodes[0], "", node, ""):
                    raise RuntimeError(f"Cannot wire generated texture into {name}")
                editing.recompile_material(material)
                if not library.save_loaded_asset(material):
                    raise RuntimeError(f"Cannot save corrected {name} material")
        referenced_textures = [node.texture.get_path_name() for node in expressions
                               if isinstance(node, unreal.MaterialExpressionTextureSample)
                               and node.texture is not None]
        if spec["texture"] and textures[spec["texture"]].get_path_name() not in referenced_textures:
            raise RuntimeError(f"Missing generated texture reference on {name}")
        material_checks.append({"name": name, "texture_references": referenced_textures,
                                "required_graph_inputs": [str(p) for p in required]})

    report = {"status": "success", "meshes": [], "textures": sorted(textures),
              "materials": sorted(materials), "material_checks": material_checks,
              "policy": "Reuse and validate existing named packages; no deletions"}
    for mesh in manifest["meshes"]:
        name = mesh["name"]
        path = f"{BASE}/Meshes/SM_{name}"
        if not library.does_asset_exist(path):
            options = unreal.InterchangeGenericAssetsPipeline()
            options.set_editor_property("asset_name", "SM_" + name)
            data = options.get_editor_property("mesh_pipeline")
            data.set_editor_property("combine_static_meshes_behavior",
                                     unreal.InterchangeCombineStaticMeshesBehavior.ALL)
            data.generate_lightmap_u_vs = False
            data.set_editor_property("collision", False)
            material_pipeline = options.get_editor_property("material_pipeline")
            material_pipeline.set_editor_property("import_materials", False)
            material_pipeline.get_editor_property("texture_pipeline").set_editor_property(
                "import_textures", False)
            parameters = unreal.ImportAssetParameters()
            parameters.is_automated = True
            parameters.destination_name = "SM_" + name
            parameters.override_pipelines = [unreal.SoftObjectPath(options.get_path_name())]
            manager = unreal.InterchangeManager.get_interchange_manager_scripted()
            source = unreal.InterchangeManager.create_source_data(str(ROOT / mesh["file"]))
            imported = manager.import_asset(BASE + "/Meshes", source, parameters)
            if not imported or len(imported) != 1:
                raise RuntimeError(f"Expected one combined mesh for {name}; got {imported}")
        static_mesh = asset(path)
        slots = []
        for index, slot in enumerate(static_mesh.static_materials):
            slot_name = str(slot.get_editor_property("imported_material_slot_name"))
            if slot_name not in materials:
                raise RuntimeError(f"Unknown material slot {slot_name!r} on {name}")
            static_mesh.set_material(index, materials[slot_name])
            slots.append({"slot": slot_name, "material": materials[slot_name].get_path_name()})
        if not slots:
            raise RuntimeError(f"Mesh has no material slots: {name}")
        if {"Glass", "AmberGlass"} & {slot["slot"] for slot in slots}:
            nanite = static_mesh.get_editor_property("nanite_settings")
            nanite.enabled = False
            static_mesh.set_editor_property("nanite_settings", nanite)
        body = static_mesh.get_editor_property("body_setup")
        if body:
            body.set_editor_property("collision_trace_flag",
                                    unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        if not library.save_loaded_asset(static_mesh):
            raise RuntimeError(f"Mesh save failed: {path}")
        bounds = static_mesh.get_bounds()
        record = {
            "name": name, "path": path, "slots": slots,
            "center_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
            "extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
            "lod0_triangles": static_mesh.get_num_triangles(0),
            "nanite_enabled": static_mesh.get_editor_property("nanite_settings").enabled,
        }
        validate_mesh_record(mesh, record)
        report["meshes"].append(record)
    report["engine"] = unreal.SystemLibrary.get_engine_version()
    report["asset_count"] = len(library.list_assets(BASE, recursive=True, include_folder=False))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["import", "scene", "verify"], default="import")
    args = parser.parse_args()
    save_report(args.stage, {"status": "running"})
    try:
        manifest = source_manifest()
        import unreal
        if args.stage == "import":
            report = import_assets(unreal, manifest)
        else:
            sys.path.insert(0, str(ROOT / "Scripts"))
            import station_scene
            if args.stage == "scene":
                report = station_scene.assemble(manifest)
            else:
                if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP):
                    raise RuntimeError("Cannot reopen station map")
                report = station_scene.verify(manifest)
        save_report(args.stage, report)
        unreal.log("PLATFORM_" + args.stage.upper() + "_OK " + json.dumps(report))
    except Exception:
        save_report(args.stage, {"status": "failed", "traceback": traceback.format_exc()})
        raise


if __name__ == "__main__":
    main()
