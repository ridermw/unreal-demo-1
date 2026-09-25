import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
import hashlib

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_unreal", ROOT / "Scripts/build_unreal.py")
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class SourceContractTests(unittest.TestCase):
    def mesh_fixture(self):
        source = BUILD.source_manifest()["meshes"][0]
        bounds = source["source_bounds_m"]
        center = [(lo + hi) * 50 for lo, hi in zip(bounds["minimum"], bounds["maximum"])]
        center[1] *= -1
        return source, {"lod0_triangles": 10, "slots": [{"slot": n} for n in source["material_slots"]],
                        "center_cm": center,
                        "extent_cm": [(hi - lo) * 50 for lo, hi in zip(bounds["minimum"], bounds["maximum"])]}

    def test_correct_mesh_contract(self):
        BUILD.validate_mesh_record(*self.mesh_fixture())

    def test_swapped_axes_fail(self):
        source, record = self.mesh_fixture()
        record["extent_cm"][1], record["extent_cm"][2] = record["extent_cm"][2], record["extent_cm"][1]
        with self.assertRaises(ValueError):
            BUILD.validate_mesh_record(source, record)

    def test_empty_geometry_fails(self):
        source, record = self.mesh_fixture()
        record["lod0_triangles"] = 0
        with self.assertRaises(ValueError):
            BUILD.validate_mesh_record(source, record)

    def test_missing_material_slot_fails(self):
        source, record = self.mesh_fixture()
        record["slots"].pop()
        with self.assertRaises(ValueError):
            BUILD.validate_mesh_record(source, record)

    def test_full_detail_mesh_cannot_silently_use_reduced_fallback(self):
        source, record = self.mesh_fixture()
        source["exported_triangles"] = 35000
        record["nanite_enabled"] = False
        record["lod0_triangles"] = 940
        with self.assertRaises(ValueError):
            BUILD.validate_mesh_record(source, record)

    def test_real_sources_are_complete(self):
        manifest = BUILD.source_manifest()
        self.assertEqual(len(manifest["meshes"]), 14)
        self.assertGreaterEqual(len(manifest["materials"]), 17)

    def test_missing_mesh_fails_before_engine_work(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "Art/Models").mkdir(parents=True)
            manifest = json.loads((ROOT / "Art/Models/manifest.json").read_text())
            (root / "Art/Models/manifest.json").write_text(json.dumps(manifest))
            with self.assertRaises(FileNotFoundError):
                BUILD.source_manifest(root)

    def test_duplicate_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "Art/Models").mkdir(parents=True)
            manifest = {"meshes": [{"name": "Same", "file": "Same.fbx"}] * 14}
            (root / "Art/Models/manifest.json").write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                BUILD.source_manifest(root)

    def test_reference_is_exact_copy(self):
        inventory = json.loads((ROOT / "Evidence/source-inventory.json").read_text())
        target = next(f for f in inventory["files"] if f["path"] == "Art/Reference/target.png")
        self.assertEqual(hashlib.sha256((ROOT / target["path"]).read_bytes()).hexdigest(),
                         target["sha256"])


if __name__ == "__main__":
    unittest.main()
