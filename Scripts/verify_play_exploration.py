"""Check that the possessed native fly pawn actually moves and can drive the play camera."""

import json
from pathlib import Path
from datetime import datetime,timezone
import unreal

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"Evidence/play-exploration-report.json"
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None:
    raise RuntimeError("Start native PIE before running the movement check")
controller=unreal.GameplayStatics.get_player_controller(world,0)
pawn=unreal.GameplayStatics.get_player_pawn(world,0) if controller else None
if pawn is None:
    raise RuntimeError("No possessed exploration pawn")
controller.set_view_target_with_blend(pawn,0)
start=pawn.get_actor_location()
state={"handle":None,"start_time":unreal.SystemLibrary.get_game_time_in_seconds(world)}
report={"status":"running","utc":datetime.now(timezone.utc).isoformat(),
        "method":"Native DefaultPawn movement input in live PIE; not hardware-key simulation",
        "pawn_class":pawn.get_class().get_name(),"start_cm":[start.x,start.y,start.z]}
REPORT.write_text(json.dumps(report,indent=2)+"\n")


def tick(delta):
    try:
        current=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if current is None:
            raise RuntimeError("PIE ended before the movement test completed")
        elapsed=unreal.SystemLibrary.get_game_time_in_seconds(current)-state["start_time"]
        if elapsed<.5:
            pawn.add_movement_input(unreal.Vector(0,-1,0),1,True)
            return
        end=pawn.get_actor_location()
        distance=((end.x-start.x)**2+(end.y-start.y)**2+(end.z-start.z)**2)**.5
        if distance<20 or controller.get_view_target()!=pawn:
            raise RuntimeError(f"Pawn/camera exploration failed; displacement={distance}")
        report.update(status="success",end_cm=[end.x,end.y,end.z],distance_cm=distance,
                      elapsed_game_seconds=elapsed,camera_follows_possessed_pawn=True)
        REPORT.write_text(json.dumps(report,indent=2)+"\n")
        unreal.unregister_slate_post_tick_callback(state["handle"])
        unreal.log("PLAY_EXPLORATION_OK")
    except Exception as error:
        report.update(status="failed",error=str(error))
        REPORT.write_text(json.dumps(report,indent=2)+"\n")
        unreal.unregister_slate_post_tick_callback(state["handle"])
        unreal.log_error("PLAY_EXPLORATION_FAILED "+str(error))
        raise


state["handle"]=unreal.register_slate_post_tick_callback(tick)
unreal._platform_exploration_test=(state,tick)
print("PLAY_EXPLORATION_SCHEDULED")
