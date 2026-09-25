"""Release the target camera for editor navigation, or use the existing fly pawn in PIE."""

import argparse
import unreal

parser=argparse.ArgumentParser()
parser.add_argument("--play-camera",action="store_true")
args=parser.parse_args()
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if args.play_camera:
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if world is None:
        raise RuntimeError("Start native PIE first with start_performance_pie.py")
    controller=unreal.GameplayStatics.get_player_controller(world,0)
    pawn=unreal.GameplayStatics.get_player_pawn(world,0) if controller else None
    if pawn is None:
        raise RuntimeError("The play session has no possessed exploration pawn")
    controller.set_view_target_with_blend(pawn,0)
    if controller.get_view_target()!=pawn:
        raise RuntimeError("Failed to activate the possessed exploration pawn camera")
    print("EXPLORATION_PAWN_CAMERA",pawn.get_class().get_name())
else:
    if levels.is_in_play_in_editor():
        raise RuntimeError("End PIE before enabling editor free-camera navigation")
    levels.eject_pilot_level_actor()
    levels.editor_set_viewport_realtime(True)
    print("EDITOR_FREE_CAMERA_READY; use the viewport's normal right-mouse navigation")
