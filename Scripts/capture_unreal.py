"""Capture the live saved target camera; run through editor_python.py, not NullRHI."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import struct

import unreal


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--name", default="m2-unreal-camera")
args = parser.parse_args()
if not args.name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.name):
    raise ValueError("Capture name must contain only letters, digits, hyphens and underscores")
output = ROOT / "Evidence" / (args.name + ".png")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
cameras = [actor for actor in actors if actor.get_actor_label() == "PN_TargetCamera"]
if len(cameras) != 1 or not isinstance(cameras[0], unreal.CameraActor):
    raise RuntimeError("Expected one saved target camera")
camera = cameras[0]
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).pilot_level_actor(camera)
unreal.get_editor_subsystem(unreal.EditorActorSubsystem).clear_actor_selection_set()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for command in ("sg.ViewDistanceQuality 2", "sg.AntiAliasingQuality 2", "sg.ShadowQuality 2",
                "sg.GlobalIlluminationQuality 2", "sg.ReflectionQuality 2", "sg.PostProcessQuality 2",
                "sg.TextureQuality 2", "sg.EffectsQuality 2", "sg.FoliageQuality 2",
                "sg.ShadingQuality 2", "r.ScreenPercentage 100", "r.VSync 0", "t.MaxFPS 0"):
    unreal.SystemLibrary.execute_console_command(world, command)
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1536, 864, str(output), camera=camera, delay=0.0, force_game_view=True)
if task is None or not task.is_valid_task():
    raise RuntimeError("Unreal did not create a screenshot task")
unreal._platform_capture_task = task
unreal.EditorLevelLibrary.editor_invalidate_viewports()
print("CAPTURE_SCHEDULED", str(output))
