"""Capture the live saved target camera; run through editor_python.py, not NullRHI."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import hashlib
import sys
import time
import importlib

import unreal


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"Scripts"))
import evidence_identity
importlib.reload(evidence_identity)
from evidence_identity import scene_identity, pacing_defaults, assert_clean_editor, QUALITY_SETTINGS
parser = argparse.ArgumentParser()
parser.add_argument("--name", default="m2-unreal-camera")
parser.add_argument("--view",choices=["target","reverse","locomotive","luggage","opposite"],default="target")
args = parser.parse_args()
if not args.name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.name):
    raise ValueError("Capture name must contain only letters, digits, hyphens and underscores")
output = ROOT / "Evidence" / (args.name + ".png")
if output.exists():
    raise RuntimeError("Capture already exists; use a fresh --name so stale pixels cannot count as success")
previous_task=getattr(unreal,"_platform_capture_task",None)
if previous_task is not None and previous_task.is_valid_task() and not previous_task.is_task_done():
    raise RuntimeError("A previous Unreal screenshot task is still pending; do not overlap captures")
assert_clean_editor(unreal)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
cameras = [actor for actor in actors if actor.get_actor_label() == "PN_TargetCamera"]
if len(cameras) != 1 or not isinstance(cameras[0], unreal.CameraActor):
    raise RuntimeError("Expected one saved target camera")
camera = cameras[0]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.editor_set_viewport_realtime(True)
capture_camera=camera
fov=camera.camera_component.field_of_view
location=camera.get_actor_location()
rotation=camera.get_actor_rotation()
if args.view=="target":
    levels.pilot_level_actor(camera)
else:
    from station_scene import world_position,camera_rotation
    viewpoints={
        "reverse":((1.7,25,2.35),(1.5,0,2.2),70),
        "locomotive":((.25,5.8,1.95),(-2.3,5.3,1.35),60),
        "luggage":((2.7,-3.4,2.2),(4.0,-1.2,1.55),55),
        "opposite":((-5.9,5.0,2.35),(-9.7,11.0,4.0),65),
    }
    position,target,fov=viewpoints[args.view]
    location=world_position(position)
    rotation=camera_rotation(position,target)
    levels.eject_pilot_level_actor()
    key=levels.get_active_viewport_config_key()
    levels.set_level_viewport_camera_info(location,rotation,key)
    levels.set_level_viewport_fov(fov,key)
    capture_camera=None
identity=scene_identity(ROOT)
frame_cap,frame_lag=pacing_defaults(ROOT)
report={"status":"pending","source":"Actual Unreal AutomationLibrary screenshot",
        "scene_identity":identity,"image":str(output.relative_to(ROOT)),
        "utc":datetime.now(timezone.utc).isoformat(),"resolution":[1536,864],
        "camera_label":camera.get_actor_label() if args.view=="target" else "EditorInspection:"+args.view,
        "view":args.view,"fov":fov,
        "position_cm":[location.x,location.y,location.z],
        "rotation_degrees":[rotation.pitch,rotation.yaw,rotation.roll],
        "quality":"High","screen_percentage":100,"frame_cap":frame_cap,"one_frame_thread_lag":frame_lag}
report_file=output.with_suffix(".json")
report_file.write_text(json.dumps(report,indent=2)+"\n")
unreal.get_editor_subsystem(unreal.EditorActorSubsystem).clear_actor_selection_set()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for command in ("sg.ViewDistanceQuality 2", "sg.AntiAliasingQuality 2", "sg.ShadowQuality 2",
                "sg.GlobalIlluminationQuality 2", "sg.ReflectionQuality 2", "sg.PostProcessQuality 2",
                "sg.TextureQuality 2", "sg.EffectsQuality 2", "sg.FoliageQuality 2",
                "sg.ShadingQuality 2", "r.ScreenPercentage 100", "r.VSync 0",
                f"t.MaxFPS {frame_cap:g}",f"r.OneFrameThreadLag {1 if frame_lag else 0}",
                "r.HighResScreenshotDelay 32"):
    unreal.SystemLibrary.execute_console_command(world, command)
expected=dict(QUALITY_SETTINGS,**{"t.MaxFPS":frame_cap,"r.OneFrameThreadLag":int(frame_lag),"r.ScreenPercentage":100})
actual={name:unreal.SystemLibrary.get_console_variable_float_value(name) for name in expected}
if any(abs(actual[name]-value)>.001 for name,value in expected.items()):
    report.update(status="failed",error="Live render settings differ from requested values",runtime_settings=actual)
    report_file.write_text(json.dumps(report,indent=2)+"\n")
    raise RuntimeError("Unreal did not apply requested capture settings")
report["runtime_settings"]=actual
report_file.write_text(json.dumps(report,indent=2)+"\n")
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1536, 864, str(output), camera=capture_camera, delay=0.0, force_game_view=True)
if task is None or not task.is_valid_task():
    raise RuntimeError("Unreal did not create a screenshot task")
unreal._platform_capture_task = task
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_invalidate_viewports()


def watch_capture(capture_task,image_file,metadata_file,metadata,root,restore_camera,performance,old_throttle):
    state={"handle":None,"start":time.monotonic(),"active":True}

    def finished(delta):
        try:
            current={name:unreal.SystemLibrary.get_console_variable_float_value(name)
                     for name in metadata["runtime_settings"]}
            if any(abs(current[name]-value)>.001 for name,value in metadata["runtime_settings"].items()):
                raise RuntimeError("Runtime render settings changed during deferred screenshot capture")
            if not capture_task.is_task_done():
                if time.monotonic()-state["start"]>90:
                    raise RuntimeError("Unreal screenshot task exceeded90seconds without completion")
                return
            data=image_file.read_bytes()
            if data[:8]!=b"\x89PNG\r\n\x1a\n" or struct.unpack(">II",data[16:24])!=(1536,864):
                raise RuntimeError("Screenshot pixel output does not match requested1536x864")
            if scene_identity(root)!=metadata["scene_identity"]:
                raise RuntimeError("Saved scene changed during screenshot capture")
            assert_clean_editor(unreal)
            metadata.update(status="success",sha256=hashlib.sha256(data).hexdigest(),
                            completed_utc=datetime.now(timezone.utc).isoformat(),
                            clean_editor_verified=True)
            metadata_file.write_text(json.dumps(metadata,indent=2)+"\n")
            unreal.unregister_slate_post_tick_callback(state["handle"])
            state["active"]=False
            performance.set_editor_property("bThrottleCPUWhenNotForeground",old_throttle)
            if restore_camera:
                unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).pilot_level_actor(restore_camera)
            unreal.log("PLATFORM_CAPTURE_COMPLETE "+str(image_file))
        except Exception as error:
            metadata.update(status="failed",error=str(error))
            metadata_file.write_text(json.dumps(metadata,indent=2)+"\n")
            unreal.unregister_slate_post_tick_callback(state["handle"])
            state["active"]=False
            performance.set_editor_property("bThrottleCPUWhenNotForeground",old_throttle)
            unreal.log_error("PLATFORM_CAPTURE_FAILED "+str(error))
            raise

    state["handle"]=unreal.register_slate_post_tick_callback(finished)
    return state,finished


performance=unreal.load_object(None,"/Script/UnrealEd.Default__EditorPerformanceSettings")
old_throttle=performance.get_editor_property("bThrottleCPUWhenNotForeground")
unreal._platform_capture_watch=watch_capture(task,output,report_file,report,ROOT,
    camera if args.view!="target" else None,performance,old_throttle)
performance.set_editor_property("bThrottleCPUWhenNotForeground",False)
print("CAPTURE_SCHEDULED", str(output))
