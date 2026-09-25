"""Generated vapor sprite material and spatially layered chimney/wheel steam."""

import unreal


def load_density(root, name):
    library = unreal.EditorAssetLibrary
    image = root / "Art/Textures" / (name + ".png")
    if not image.is_file():
        raise FileNotFoundError(f"Required generated vapor image missing: {image}")
    path = "/Game/Platform/Textures/T_" + name
    if not library.does_asset_exist(path):
        task=unreal.AssetImportTask()
        task.filename=str(image)
        task.destination_path="/Game/Platform/Textures"
        task.destination_name="T_"+name
        task.automated=True
        task.save=True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        if not task.imported_object_paths:
            raise RuntimeError(f"Vapor image import failed: {name}")
    texture=library.load_asset(path)
    if texture is None:
        raise RuntimeError(f"Cannot load vapor texture: {path}")
    texture.set_editor_property("srgb",False)
    texture.set_editor_property("compression_settings",unreal.TextureCompressionSettings.TC_MASKS)
    texture.set_editor_property("address_x",unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property("address_y",unreal.TextureAddress.TA_CLAMP)
    if not library.save_loaded_asset(texture):
        raise RuntimeError(f"Cannot save vapor texture: {name}")
    return texture


def material(root):
    library = unreal.EditorAssetLibrary
    path = "/Game/Platform/Materials/M_SteamCloud"
    existing = library.load_asset(path) if library.does_asset_exist(path) else None
    if existing and library.get_metadata_tag(existing, "PlatformSteamVersion") == "3":
        return existing
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    texture=load_density(root,"steam_chimney_wide")
    result = existing or tools.create_asset("M_SteamCloud", "/Game/Platform/Materials",
                                            unreal.Material, unreal.MaterialFactoryNew())
    result.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    result.set_editor_property("two_sided", True)
    result.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    editing = unreal.MaterialEditingLibrary
    density = editing.create_material_expression(result, unreal.MaterialExpressionTextureSampleParameter2D, -600, 200)
    density.set_editor_property("parameter_name","SteamDensity")
    density.texture = texture
    density.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    opacity = editing.create_material_expression(result, unreal.MaterialExpressionMultiply, -300, 200)
    scale = editing.create_material_expression(result, unreal.MaterialExpressionScalarParameter, -600, 400)
    scale.set_editor_property("parameter_name", "Density")
    scale.set_editor_property("default_value", 0.22)
    color = editing.create_material_expression(result, unreal.MaterialExpressionVectorParameter, -300, 0)
    color.set_editor_property("parameter_name", "SteamLuminance")
    color.set_editor_property("default_value", unreal.LinearColor(65, 72, 80, 1))
    fade = editing.create_material_expression(result, unreal.MaterialExpressionDepthFade, -50, 200)
    fade.set_editor_property("fade_distance_default", 80)
    for source, output, target, input_ in ((density, "R", opacity, "A"), (scale, "", opacity, "B"),
                                          (opacity, "", fade, "")):
        if not editing.connect_material_expressions(source, output, target, input_):
            raise RuntimeError(f"Cannot connect steam graph input {input_}")
    if not editing.connect_material_property(fade, "", unreal.MaterialProperty.MP_OPACITY):
        raise RuntimeError("Cannot connect steam opacity")
    if not editing.connect_material_property(color, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError("Cannot connect steam color")
    editing.recompile_material(result)
    library.set_metadata_tag(result, "PlatformSteamVersion", "3")
    if not library.save_loaded_asset(result):
        raise RuntimeError("Cannot save steam material")
    return result


def assemble(root, upsert, manifest):
    vapor = material(root)
    library = unreal.EditorAssetLibrary
    low_path = "/Game/Platform/Materials/MI_WheelSteam"
    if library.does_asset_exist(low_path):
        low_vapor = library.load_asset(low_path)
    else:
        low_vapor = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "MI_WheelSteam", "/Game/Platform/Materials", unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    editing = unreal.MaterialEditingLibrary
    editing.set_material_instance_parent(low_vapor, vapor)
    editing.set_material_instance_scalar_parameter_value(low_vapor, "Density", .18)
    editing.set_material_instance_texture_parameter_value(low_vapor,"SteamDensity",load_density(root,"steam_wheels"))
    editing.set_material_instance_vector_parameter_value(
        low_vapor, "SteamLuminance", unreal.LinearColor(65, 72, 78, 1))
    editing.update_material_instance(low_vapor)
    if not library.save_loaded_asset(low_vapor):
        raise RuntimeError("Cannot save wheel steam instance")
    plane = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    if plane is None:
        raise RuntimeError("Engine plane unavailable for steam cards")
    chimney = manifest["chimney"]
    specs = []
    for index, angle in enumerate((-30, 0, 30)):
        specs.append((f"ChimneySteam_{index}", (chimney[0]+index*0.12, chimney[1]+index*0.25, 7.1+index*0.2),
                      3.2, 4.8, angle))
    for index, y in enumerate((4.7, 6.6, 8.8, 11.4, 15.0)):
        specs.append((f"WheelSteam_{index}", (-1.3, y, 1.10), 4.0, 1.7, 30))
    for name, position, width, height, angle in specs:
        actor = upsert(name, unreal.StaticMeshActor, position,
                       unreal.Rotator(pitch=-12 if name.startswith("Chimney") else 0, yaw=angle, roll=90))
        actor.set_actor_scale3d(unreal.Vector(width, height, 1))
        component = actor.static_mesh_component
        component.set_static_mesh(plane)
        component.set_material(0, low_vapor if name.startswith("Wheel") else vapor)
        component.set_collision_profile_name("NoCollision")
        component.set_editor_property("cast_shadow", False)
