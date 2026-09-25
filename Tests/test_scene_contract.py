import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))
from scene_contract import verify_camera, verify_inventory, verify_material_slots


class SceneContractTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / "Art/Models/manifest.json").read_text())

    def test_missing_lamp_rejected(self):
        labels = {"PN_" + mesh["name"] for mesh in self.manifest["meshes"]}
        labels.update("PN_" + name for name in
                      ("TargetCamera", "ExploreStart", "Sun", "SkyAtmosphere", "SkyLight", "Haze", "Exposure"))
        with self.assertRaises(ValueError):
            verify_inventory(self.manifest, labels)
        labels.update(f"PN_LampLight_{i:02}" for i in range(len(self.manifest["lamps"])))
        verify_inventory(self.manifest, labels)

    def test_camera_pose_and_fov(self):
        config = {"position": [1, -5, 2], "target": [1, 20, 2], "fov": 70}
        verify_camera(config, [100, 500, 200], [0, -90, 0], 70)
        for position, rotation, fov in [
            ([100, 500, 200], [0, -90, 0], 1),
            ([100, 500000, 200], [0, -90, 0], 70),
            ([100, 500, 200], [-90, 0, 0], 70),
        ]:
            with self.assertRaises(ValueError):
                verify_camera(config, position, rotation, fov)

    def test_swapped_materials_rejected(self):
        materials = ["/Game/Platform/Materials/M_Brick.M_Brick", "/Game/Platform/Materials/M_Stone.M_Stone"]
        verify_material_slots(["Brick", "Stone"], materials)
        with self.assertRaises(ValueError):
            verify_material_slots(["Brick", "Stone"], list(reversed(materials)))


if __name__ == "__main__":
    unittest.main()
