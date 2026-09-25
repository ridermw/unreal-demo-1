"""Assemble and verify the saved Platform Nine level using existing imported assets."""

import math

import unreal
from scene_contract import verify_camera, verify_inventory, verify_material_slots


MAP = "/Game/Platform/Maps/HiddenPlatform"
PREFIX = "PN_"


def world_position(point):
    return unreal.Vector(point[0] * 100, -point[1] * 100, point[2] * 100)


def camera_rotation(position, target):
    delta = world_position(target) - world_position(position)
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(delta.z, math.hypot(delta.x, delta.y))),
        yaw=math.degrees(math.atan2(delta.y, delta.x)), roll=0)


def assemble(manifest):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        if not levels.load_level(MAP):
            raise RuntimeError("Unable to load existing station map")
    elif not levels.new_level(MAP):
        raise RuntimeError("Unable to create station map")
    existing = {}
    for actor in actors.get_all_level_actors():
        label = actor.get_actor_label()
        if label in existing:
            raise RuntimeError(f"Duplicate actor label: {label}")
        existing[label] = actor

    def upsert(name, cls, position=(0, 0, 0), rotation=None):
        label = PREFIX + name
        actor = existing.get(label)
        if actor is not None and not isinstance(actor, cls):
            raise RuntimeError(f"Actor class conflict: {label}")
        if actor is None:
            actor = actors.spawn_actor_from_class(cls, world_position(position))
            if actor is None:
                raise RuntimeError(f"Cannot spawn actor: {label}")
            actor.set_actor_label(label)
            existing[label] = actor
        actor.set_actor_location(world_position(position), False, False)
        if rotation is not None:
            actor.set_actor_rotation(rotation, False)
        actor.set_folder_path("PlatformNine")
        return actor

    for spec in manifest["meshes"]:
        mesh = unreal.EditorAssetLibrary.load_asset("/Game/Platform/Meshes/SM_" + spec["name"])
        if mesh is None:
            raise RuntimeError(f"Missing imported mesh: {spec['name']}")
        actor = upsert(spec["name"], unreal.StaticMeshActor)
        component = actor.static_mesh_component
        component.set_static_mesh(mesh)
        component.set_mobility(unreal.ComponentMobility.STATIC)
        component.set_collision_profile_name("BlockAll")
        component.set_editor_property("cast_shadow", spec["name"] not in ("Puddles", "Windows"))

    sun = upsert("Sun", unreal.DirectionalLight, (0, 0, 15),
                 unreal.Rotator(pitch=-32, yaw=60, roll=0))
    light = sun.get_component_by_class(unreal.DirectionalLightComponent)
    light.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.set_intensity(7000)
    light.set_editor_property("atmosphere_sun_light", True)
    light.set_editor_property("light_source_angle", 2.0)
    light.set_light_color(unreal.LinearColor(1.0, 0.91, 0.78, 1))

    upsert("SkyAtmosphere", unreal.SkyAtmosphere)
    sky = upsert("SkyLight", unreal.SkyLight)
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    sky_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky_component.set_intensity(1.3)
    sky_component.set_editor_property("real_time_capture", True)
    sky_component.set_editor_property("lower_hemisphere_is_black", False)

    fog = upsert("Haze", unreal.ExponentialHeightFog, (0, 0, 0))
    fog_component = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    fog_component.set_editor_property("fog_density", 0.008)
    fog_component.set_editor_property("fog_height_falloff", 0.2)
    fog_component.set_fog_inscattering_color(unreal.LinearColor(0.30, 0.39, 0.46, 1))
    fog_component.set_volumetric_fog(True)
    fog_component.set_editor_property("volumetric_fog_scattering_distribution", 0.4)
    fog_component.set_volumetric_fog_distance(10000)

    post = upsert("Exposure", unreal.PostProcessVolume)
    post.set_editor_property("unbound", True)
    settings = post.get_editor_property("settings")
    for key, value in {
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
        "override_auto_exposure_apply_physical_camera_exposure": True,
        "auto_exposure_apply_physical_camera_exposure": False,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -7.0,
        "override_bloom_intensity": True,
        "bloom_intensity": 0.25,
        "override_vignette_intensity": True,
        "vignette_intensity": 0.15,
        "override_motion_blur_amount": True,
        "motion_blur_amount": 0.0,
    }.items():
        settings.set_editor_property(key, value)
    post.set_editor_property("settings", settings)

    for index, position in enumerate(manifest["lamps"]):
        lamp = upsert(f"LampLight_{index:02}", unreal.PointLight, position)
        component = lamp.get_component_by_class(unreal.PointLightComponent)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
        component.set_intensity(1800)
        component.set_light_color(unreal.LinearColor(1.0, 0.49, 0.19, 1))
        component.set_attenuation_radius(650)
        component.set_editor_property("source_radius", 14)
        component.set_editor_property("cast_shadows", index < 3)
        component.set_editor_property("volumetric_scattering_intensity", 0.25)

    config = manifest["camera"]
    rotation = camera_rotation(config["position"], config["target"])
    camera = upsert("TargetCamera", unreal.CameraActor, config["position"], rotation)
    camera.camera_component.set_field_of_view(config["fov"])
    camera.camera_component.set_aspect_ratio(16 / 9)
    camera.camera_component.set_editor_property("constrain_aspect_ratio", True)
    camera.camera_component.set_editor_property("post_process_blend_weight", 0)
    camera.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    upsert("ExploreStart", unreal.PlayerStart, config["position"], rotation)
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(world_position(config["position"]), rotation)
    if not levels.save_current_level():
        raise RuntimeError("Station map save failed")
    if not levels.load_level(MAP):
        raise RuntimeError("Station map reload failed")
    return verify(manifest)


def verify(manifest):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world is None or world.get_path_name().split(".")[0] != MAP:
        raise RuntimeError(f"Wrong loaded world: {world}")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    by_label = {}
    for actor in actors:
        label = actor.get_actor_label()
        if label.startswith(PREFIX):
            if label in by_label:
                raise RuntimeError(f"Duplicated generated actor: {label}")
            by_label[label] = actor
    meshes = []
    for spec in manifest["meshes"]:
        actor = by_label.get(PREFIX + spec["name"])
        if not isinstance(actor, unreal.StaticMeshActor):
            raise RuntimeError(f"Missing mesh actor: {spec['name']}")
        component = actor.static_mesh_component
        mesh = component.static_mesh
        if mesh is None or mesh.get_name() != "SM_" + spec["name"]:
            raise RuntimeError(f"Wrong mesh assignment: {spec['name']}")
        materials = [component.get_material(i).get_path_name()
                     for i in range(component.get_num_materials())]
        slots = [str(slot.get_editor_property("imported_material_slot_name"))
                 for slot in mesh.static_materials]
        verify_material_slots(slots, materials)
        meshes.append({"actor": actor.get_path_name(), "mesh": mesh.get_path_name(),
                       "materials": materials})
    verify_inventory(manifest, by_label)
    for index in range(len(manifest["lamps"])):
        if not isinstance(by_label[f"PN_LampLight_{index:02}"], unreal.PointLight):
            raise RuntimeError(f"Incorrect lamp actor class: {index}")
    camera = by_label[PREFIX + "TargetCamera"]
    position, rotation = camera.get_actor_location(), camera.get_actor_rotation()
    verify_camera(manifest["camera"], [position.x, position.y, position.z],
                  [rotation.pitch, rotation.yaw, rotation.roll], camera.camera_component.field_of_view)
    return {
        "status": "success", "map": MAP, "generated_actor_count": len(by_label),
        "total_actor_count": len(actors), "meshes": meshes,
        "camera": {"position_cm": [position.x, position.y, position.z],
                   "rotation_degrees": [rotation.pitch, rotation.yaw, rotation.roll],
                   "fov": camera.camera_component.field_of_view},
        "engine": unreal.SystemLibrary.get_engine_version(),
        "rendered": False,
    }
