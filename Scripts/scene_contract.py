"""Engine-independent saved-scene evidence checks."""

import math


def verify_inventory(manifest, labels):
    expected = {"PN_" + mesh["name"] for mesh in manifest["meshes"]}
    expected.update("PN_" + name for name in
                    ("TargetCamera", "ExploreStart", "Sun", "SkyAtmosphere", "SkyLight", "Haze", "Exposure"))
    expected.update(f"PN_LampLight_{i:02}" for i in range(len(manifest["lamps"])))
    missing = expected - set(labels)
    if missing:
        raise ValueError(f"Missing generated actors: {sorted(missing)}")


def verify_camera(config, position, rotation, fov):
    expected_position = [config["position"][0] * 100, -config["position"][1] * 100,
                         config["position"][2] * 100]
    target = [config["target"][0] * 100, -config["target"][1] * 100, config["target"][2] * 100]
    delta = [b - a for a, b in zip(expected_position, target)]
    expected_rotation = [math.degrees(math.atan2(delta[2], math.hypot(delta[0], delta[1]))),
                         math.degrees(math.atan2(delta[1], delta[0])), 0]
    if any(abs(a - b) > 0.1 for a, b in zip(position, expected_position)):
        raise ValueError("Saved camera position differs from source")
    if any(abs(a - b) > 0.01 for a, b in zip(rotation, expected_rotation)) or abs(fov - config["fov"]) > 0.01:
        raise ValueError("Saved camera orientation or field of view differs from source")


def verify_material_slots(slots, materials):
    expected = ["/Game/Platform/Materials/M_" + name + ".M_" + name for name in slots]
    if materials != expected:
        raise ValueError("Material assignments differ from mesh slot order")
