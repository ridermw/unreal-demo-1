"""Apply generated, aligned surface maps to the station's existing material assets."""

from pathlib import Path

import unreal


def upgrade(root, manifest):
    library = unreal.EditorAssetLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    editing = unreal.MaterialEditingLibrary
    texture_cache = {}

    def load_texture(name, kind):
        key = name + ("" if kind == "albedo" else "_" + kind)
        if key in texture_cache:
            return texture_cache[key]
        source = root / "Art/Textures" / (key + ".png")
        if not source.is_file():
            raise FileNotFoundError(f"Required generated PBR map missing: {source}")
        path = "/Game/Platform/Textures/T_" + key
        if not library.does_asset_exist(path):
            task = unreal.AssetImportTask()
            task.filename = str(source)
            task.destination_path = "/Game/Platform/Textures"
            task.destination_name = "T_" + key
            task.automated = True
            task.save = True
            tools.import_asset_tasks([task])
            if not task.imported_object_paths:
                raise RuntimeError(f"Texture import failed: {source}")
        texture = library.load_asset(path)
        if texture is None:
            raise RuntimeError(f"Cannot load imported map {path}")
        texture.set_editor_property("srgb", kind == "albedo")
        if kind == "normal":
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif kind == "roughness":
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        if not library.save_loaded_asset(texture):
            raise RuntimeError(f"Texture save failed: {key}")
        texture_cache[key] = texture
        return texture

    reports = []
    for name, spec in manifest["materials"].items():
        surface = spec["texture"]
        if not surface:
            if name == "Lamp":
                lamp = library.load_asset("/Game/Platform/Materials/M_Lamp")
                emission = editing.get_material_property_input_node(lamp, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
                inputs = editing.get_inputs_for_material_expression(lamp, emission)
                constants = [node for node in inputs if isinstance(node, unreal.MaterialExpressionConstant)]
                if len(constants) != 1:
                    raise RuntimeError("Unexpected lamp emission graph")
                constants[0].r = 650
                editing.recompile_material(lamp)
                if not library.save_loaded_asset(lamp):
                    raise RuntimeError("Cannot save lamp emission")
            continue
        material = library.load_asset("/Game/Platform/Materials/M_" + name)
        if material is None:
            raise RuntimeError(f"Material missing: {name}")
        original_base_input = editing.get_material_property_input_node(
            material, unreal.MaterialProperty.MP_BASE_COLOR)
        by_parameter = {str(node.get_editor_property("parameter_name")): node
                        for node in editing.get_material_expressions(material)
                        if isinstance(node, unreal.MaterialExpressionTextureSampleParameter2D)}
        maps = {}
        for index, kind in enumerate(("albedo", "normal", "roughness")):
            texture = load_texture(surface, kind)
            node = by_parameter.get("Surface_" + kind)
            if node is None:
                node = editing.create_material_expression(
                    material, unreal.MaterialExpressionTextureSampleParameter2D, -900, 600 + index * 300)
                node.set_editor_property("parameter_name", "Surface_" + kind)
                node.set_editor_property("group", "Generated Surface")
            node.texture = texture
            node.set_editor_property("sampler_type",
                unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if kind == "normal"
                else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS if kind == "roughness"
                else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
            maps[kind] = node
        for kind, prop in (("albedo", unreal.MaterialProperty.MP_BASE_COLOR),
                           ("normal", unreal.MaterialProperty.MP_NORMAL),
                           ("roughness", unreal.MaterialProperty.MP_ROUGHNESS)):
            if not editing.connect_material_property(maps[kind], "R" if kind == "roughness" else "", prop):
                raise RuntimeError(f"Cannot wire {kind} on {name}")
        tint_value = {
            "DarkLeather": (0.45, 0.40, 0.35), "RoofPanel": (0.25, 0.25, 0.25),
            "AmberGlass": (0.14, 0.15, 0.12), "Glass": (0.35, 0.43, 0.45),
            "Scarlet": (1.0, 0.62, 0.56),
        }.get(name, (1.0, 1.0, 1.0))
        expressions = editing.get_material_expressions(material)
        tint = next((node for node in expressions
                     if isinstance(node, unreal.MaterialExpressionVectorParameter)
                     and str(node.get_editor_property("parameter_name")) == "SurfaceTint"), None)
        if tint is None:
            tint = editing.create_material_expression(
                material, unreal.MaterialExpressionVectorParameter, -850, 1500)
            tint.set_editor_property("parameter_name", "SurfaceTint")
        tint.set_editor_property("default_value", unreal.LinearColor(*tint_value, 1))
        multiply = original_base_input
        if not isinstance(multiply, unreal.MaterialExpressionMultiply):
            multiply = editing.create_material_expression(material, unreal.MaterialExpressionMultiply, -300, 650)
        for source, input_ in ((maps["albedo"], "A"), (tint, "B")):
            if not editing.connect_material_expressions(source, "", multiply, input_):
                raise RuntimeError(f"Cannot connect tint on {name}")
        if not editing.connect_material_property(multiply, "", unreal.MaterialProperty.MP_BASE_COLOR):
            raise RuntimeError(f"Cannot apply tint on {name}")
        metallic = editing.get_material_property_input_node(material, unreal.MaterialProperty.MP_METALLIC)
        if not isinstance(metallic, unreal.MaterialExpressionConstant):
            raise RuntimeError(f"Unexpected metallic input type on {name}")
        metallic.r = spec["metallic"]
        if name in ("Glass", "AmberGlass", "RoofPanel"):
            material.set_editor_property("two_sided", True)
        if name == "AmberGlass":
            material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
            emission = editing.get_material_property_input_node(material, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
            if emission is None:
                emission = editing.create_material_expression(
                    material, unreal.MaterialExpressionConstant3Vector, -300, 1400)
            emission.constant = unreal.LinearColor(0.16, 0.075, 0.018, 1)
            if not editing.connect_material_property(emission, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
                raise RuntimeError("Cannot wire window interior glow")
        if name == "Glass":
            opacity = editing.get_material_property_input_node(material, unreal.MaterialProperty.MP_OPACITY)
            opacity.r = 0.5
        editing.recompile_material(material)
        if not library.save_loaded_asset(material):
            raise RuntimeError(f"PBR material save failed: {name}")
        reports.append({"material": material.get_path_name(),
                        "maps": {kind: maps[kind].texture.get_path_name() for kind in maps}})
    return reports
