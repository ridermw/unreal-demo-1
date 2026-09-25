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
        elif kind in ("roughness", "wetness"):
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
            "Scarlet": (0.65, 0.30, 0.25), "Stone": (.19,.20,.21),
            "Brick": (.7,.62,.53), "BlackSteel": (.85,.85,.85),
            "Cream": (.62,.49,.32), "Brass": (.72,.60,.43),
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
        multiply = next((node for node in expressions
                         if isinstance(node, unreal.MaterialExpressionMultiply)
                         and str(node.get_editor_property("desc")) == "SurfaceBaseTint"), original_base_input)
        if not isinstance(multiply, unreal.MaterialExpressionMultiply):
            multiply = editing.create_material_expression(material, unreal.MaterialExpressionMultiply, -300, 650)
        multiply.set_editor_property("desc", "SurfaceBaseTint")
        for source, input_ in ((maps["albedo"], "A"), (tint, "B")):
            if not editing.connect_material_expressions(source, "", multiply, input_):
                raise RuntimeError(f"Cannot connect tint on {name}")
        if not editing.connect_material_property(multiply, "", unreal.MaterialProperty.MP_BASE_COLOR):
            raise RuntimeError(f"Cannot apply tint on {name}")
        metallic = editing.get_material_property_input_node(material, unreal.MaterialProperty.MP_METALLIC)
        if not isinstance(metallic, unreal.MaterialExpressionConstant):
            raise RuntimeError(f"Unexpected metallic input type on {name}")
        metallic.r = spec["metallic"]
        modifiers = {"Stone": .60, "Scarlet": .9, "BlackSteel": 1.1, "Brass": .9,
                     "Iron": 1.0, "Leather": 1.0, "DarkLeather": 1.0, "Wood": 1.0}
        if name in modifiers:
            rough_scale = next((node for node in expressions
                if isinstance(node, unreal.MaterialExpressionScalarParameter)
                and str(node.get_editor_property("parameter_name")) == "RoughnessScale"), None)
            if rough_scale is None:
                rough_scale = editing.create_material_expression(
                    material, unreal.MaterialExpressionScalarParameter, -650, 1900)
                rough_scale.set_editor_property("parameter_name", "RoughnessScale")
            rough_scale.set_editor_property("default_value", modifiers[name])
            rough_product = next((node for node in expressions
                if isinstance(node, unreal.MaterialExpressionMultiply)
                and str(node.get_editor_property("desc")) == "SurfaceRoughness"), None)
            if rough_product is None:
                rough_product = editing.create_material_expression(
                    material, unreal.MaterialExpressionMultiply, -300, 1800)
                rough_product.set_editor_property("desc", "SurfaceRoughness")
            if not editing.connect_material_expressions(maps["roughness"], "R", rough_product, "A"):
                raise RuntimeError("Cannot wire roughness sample")
            if not editing.connect_material_expressions(rough_scale, "", rough_product, "B"):
                raise RuntimeError("Cannot wire roughness scale")
            if not editing.connect_material_property(rough_product, "", unreal.MaterialProperty.MP_ROUGHNESS):
                raise RuntimeError("Cannot wire varied roughness")
        normal_strength = next((node for node in expressions
            if isinstance(node, unreal.MaterialExpressionScalarParameter)
            and str(node.get_editor_property("parameter_name")) == "NormalStrength"), None)
        if normal_strength is None:
            normal_strength = editing.create_material_expression(
                material, unreal.MaterialExpressionScalarParameter, -800, 2150)
            normal_strength.set_editor_property("parameter_name", "NormalStrength")
        normal_strength.set_editor_property("default_value", .45 if name in ("Brick","Stone","Gravel") else .14)
        flatten = next((node for node in expressions
            if isinstance(node, unreal.MaterialExpressionLinearInterpolate)
            and str(node.get_editor_property("desc")) == "SurfaceNormal"), None)
        if flatten is None:
            flatten = editing.create_material_expression(
                material, unreal.MaterialExpressionLinearInterpolate, -300, 2100)
            flatten.set_editor_property("desc", "SurfaceNormal")
            neutral = editing.create_material_expression(
                material, unreal.MaterialExpressionConstant3Vector, -600, 2300)
            neutral.constant = unreal.LinearColor(0, 0, 1, 1)
            if not editing.connect_material_expressions(neutral, "", flatten, "A"):
                raise RuntimeError("Cannot wire neutral surface normal")
        if not editing.connect_material_expressions(maps["normal"], "", flatten, "B"):
            raise RuntimeError("Cannot wire generated normal")
        if not editing.connect_material_expressions(normal_strength, "", flatten, "Alpha"):
            raise RuntimeError("Cannot wire normal strength")
        if not editing.connect_material_property(flatten, "", unreal.MaterialProperty.MP_NORMAL):
            raise RuntimeError("Cannot wire softened surface normal")
        if name == "Stone":
            def node_with_label(cls, label, x, y):
                found = next((node for node in editing.get_material_expressions(material)
                              if isinstance(node, cls) and str(node.get_editor_property("desc")) == label), None)
                if found is None:
                    found = editing.create_material_expression(material, cls, x, y)
                    found.set_editor_property("desc", label)
                return found

            mask = node_with_label(unreal.MaterialExpressionTextureSample, "GeneratedWetness", -900, 2600)
            mask.texture = load_texture("stone", "wetness")
            mask.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
            darken = node_with_label(unreal.MaterialExpressionLinearInterpolate, "WetDarken", -550, 2600)
            darken.set_editor_property("const_a", 1)
            darken.set_editor_property("const_b", .36)
            wet_color = node_with_label(unreal.MaterialExpressionMultiply, "WetBaseColor", -250, 2600)
            wet_roughness = node_with_label(unreal.MaterialExpressionLinearInterpolate, "WetRoughness", -250, 2900)
            wet_roughness.set_editor_property("const_b", .07)
            for source_node, output, target_node, input_ in (
                (mask, "R", darken, "Alpha"), (multiply, "", wet_color, "A"), (darken, "", wet_color, "B"),
                (rough_product, "", wet_roughness, "A"), (mask, "R", wet_roughness, "Alpha")):
                if not editing.connect_material_expressions(source_node, output, target_node, input_):
                    raise RuntimeError(f"Cannot wire wet paving: {input_}")
            if not editing.connect_material_property(wet_color, "", unreal.MaterialProperty.MP_BASE_COLOR):
                raise RuntimeError("Cannot wire wet paving color")
            if not editing.connect_material_property(wet_roughness, "", unreal.MaterialProperty.MP_ROUGHNESS):
                raise RuntimeError("Cannot wire wet paving roughness")
        if name in ("Glass", "AmberGlass", "RoofPanel"):
            material.set_editor_property("two_sided", True)
        if name == "AmberGlass":
            material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            opacity = editing.get_material_property_input_node(material, unreal.MaterialProperty.MP_OPACITY)
            opacity.r = .22
            emission = editing.get_material_property_input_node(material, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
            if emission is None:
                emission = editing.create_material_expression(
                    material, unreal.MaterialExpressionConstant3Vector, -300, 1400)
            emission.constant = unreal.LinearColor(.06, .025, .008, 1)
            if not editing.connect_material_property(emission, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
                raise RuntimeError("Cannot wire window interior glow")
        if name == "Glass":
            opacity = editing.get_material_property_input_node(material, unreal.MaterialProperty.MP_OPACITY)
            opacity.r = 0.28
        editing.recompile_material(material)
        if not library.save_loaded_asset(material):
            raise RuntimeError(f"PBR material save failed: {name}")
        reports.append({"material": material.get_path_name(),
                        "maps": {kind: maps[kind].texture.get_path_name() for kind in maps}})
    return reports
