from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"Scripts"))
from evidence_identity import scene_identity, pacing_defaults, assert_clean_editor


class EvidenceIdentityTests(unittest.TestCase):
    def editor_fixture(self,dirty=(),map_path="/Game/Platform/Maps/HiddenPlatform.HiddenPlatform",playing=False):
        levels=SimpleNamespace(is_in_play_in_editor=lambda:playing)
        editor=SimpleNamespace(get_editor_world=lambda:SimpleNamespace(get_path_name=lambda:map_path))
        api=SimpleNamespace(LevelEditorSubsystem="level",UnrealEditorSubsystem="editor")
        api.get_editor_subsystem=lambda kind:levels if kind=="level" else editor
        api.EditorLoadingAndSavingUtils=SimpleNamespace(
            get_dirty_content_packages=lambda:[SimpleNamespace(get_path_name=lambda name=name:name) for name in dirty],
            get_dirty_map_packages=lambda:[])
        return api

    def test_dirty_platform_assets_and_wrong_world_are_rejected(self):
        assert_clean_editor(self.editor_fixture(dirty=["/Game/Unrelated/Asset"]))
        for api in (self.editor_fixture(dirty=["/Game/Platform/Materials/M_Test"]),
                    self.editor_fixture(map_path="/Temp/Unsaved.World"),
                    self.editor_fixture(playing=True)):
            with self.assertRaises(RuntimeError):
                assert_clean_editor(api)

    def test_project_pacing_is_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"Config").mkdir()
            path=root/"Config/DefaultEngine.ini"
            path.write_text("[SystemSettings]\nt.MaxFPS=32\nr.OneFrameThreadLag=0\n")
            self.assertEqual(pacing_defaults(root),(32,False))
            path.write_text("[SystemSettings]\nt.MaxFPS=-1\nr.OneFrameThreadLag=0\n")
            with self.assertRaises(ValueError):
                pacing_defaults(root)
    def test_material_changes_invalidate_scene_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ("Content/Platform/Maps/HiddenPlatform.umap","Content/Platform/Materials/M_Test.uasset",
                         "PlatformNine.uproject","Config/DefaultEngine.ini","Config/DefaultInput.ini"):
                path=root/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b"fixture")
            first=scene_identity(root)
            self.assertEqual(first,scene_identity(root))
            (root/"Content/Platform/Materials/M_Test.uasset").write_bytes(b"changed")
            self.assertNotEqual(first["sha256"],scene_identity(root)["sha256"])

    def test_missing_map_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                scene_identity(Path(folder))
