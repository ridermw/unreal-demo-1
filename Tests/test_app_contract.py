import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class WalkthroughAppContractTests(unittest.TestCase):
    def test_runtime_module_and_editor_only_tools(self):
        project=json.loads((ROOT/"PlatformNine.uproject").read_text())
        self.assertTrue(any(module["Name"]=="PlatformNine" and module["Type"]=="Runtime"
                            for module in project.get("Modules",[])))
        plugins={plugin["Name"]:plugin for plugin in project["Plugins"]}
        for name in ("PythonScriptPlugin","EditorScriptingUtilities","ModelContextProtocol","EditorToolset"):
            self.assertEqual(plugins[name]["TargetAllowList"],["Editor"])

    def test_viewer_is_the_default_game_mode(self):
        config=(ROOT/"Config/DefaultEngine.ini").read_text()
        self.assertIn("GlobalDefaultGameMode=/Script/PlatformNine.ViewerGameMode",config)
        self.assertIn("GameDefaultMap=/Game/Platform/Maps/HiddenPlatform",config)

    def test_only_saved_platform_map_is_required_for_cook(self):
        config=(ROOT/"Config/DefaultGame.ini").read_text()
        self.assertIn('/Game/Platform/Maps/HiddenPlatform',config)
        self.assertIn("bCookAll=False",config)
        self.assertIn("bUseZenStore=False",config)

    def test_fullscreen_key_reaches_viewer_input(self):
        self.assertIn("bF11TogglesFullscreen=False",(ROOT/"Config/DefaultInput.ini").read_text())

    def test_build_outputs_are_not_source_assets(self):
        self.assertIn("Builds/",(ROOT/".gitignore").read_text())


if __name__=="__main__":
    unittest.main()
