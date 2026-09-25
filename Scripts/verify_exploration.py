"""Verify real collision surfaces and an unobstructed platform corridor in the live editor."""

import importlib
import json
from pathlib import Path
import sys
import traceback
from datetime import datetime,timezone

import unreal

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"Scripts"))
import evidence_identity
importlib.reload(evidence_identity)
report={"status":"running","utc":datetime.now(timezone.utc).isoformat(),"traces":[]}
destination=ROOT/"Evidence/exploration-report.json"


def trace(name,start,end):
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    hit=unreal.SystemLibrary.line_trace_single(
        world,unreal.Vector(*start),unreal.Vector(*end),unreal.TraceTypeQuery.ECC_VISIBILITY,
        True,[],unreal.DrawDebugTrace.NONE,True)
    result={"name":name,"start_cm":start,"end_cm":end,"hit":hit is not None}
    if hit is not None:
        values=hit.to_tuple()
        if len(values)<11 or not values[0]:
            raise RuntimeError("Unsupported or nonblocking HitResult layout")
        # UE5.8's reflected BreakHitResult order: impact point5, normal7, actor9.
        point,normal,actor,component=values[5],values[7],values[9],values[10]
        body=component.static_mesh.get_editor_property("body_setup")
        mode=body.get_editor_property("collision_trace_flag") if body else None
        blocks_pawn=component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)==unreal.CollisionResponseType.ECR_BLOCK
        if not blocks_pawn or mode!=unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
            raise RuntimeError(f"Hit surface does not support expected pawn collision: {actor.get_actor_label()}")
        result.update(impact_cm=[point.x,point.y,point.z],normal=[normal.x,normal.y,normal.z],
                      actor_label=actor.get_actor_label(),blocks_pawn=blocks_pawn,collision_mode=str(mode))
    report["traces"].append(result)
    return result


try:
    evidence_identity.assert_clean_editor(unreal)
    identity=evidence_identity.scene_identity(ROOT)
    for y in (0,1000,3500,8000,10700):
        result=trace(f"platform-floor-{y}",[150,-y,250],[150,-y,-100])
        if (not result["hit"] or result["actor_label"]!="PN_Architecture"
                or not 67<=result["impact_cm"][2]<=74 or result["normal"][2]<.9):
            raise RuntimeError(f"Platform collision failed at y={y}: {result}")
    result=trace("opposite-floor",[-800,-1100,250],[-800,-1100,-100])
    if not result["hit"] or not 58<=result["impact_cm"][2]<=64:
        raise RuntimeError("Opposing platform collision failed")
    result=trace("locomotive-body",[100,-700,300],[-500,-700,300])
    if not result["hit"] or result["actor_label"]!="PN_Locomotive":
        raise RuntimeError("Locomotive body collision failed")
    result=trace("right-wall",[150,-600,300],[600,-600,300])
    if not result["hit"] or result["actor_label"] not in ("PN_Architecture","PN_Windows"):
        raise RuntimeError("Station wall collision failed")
    result=trace("clear-platform-corridor",[150,300,180],[150,-9500,180])
    if result["hit"]:
        raise RuntimeError("The platform walking corridor is unexpectedly blocked")
    evidence_identity.assert_clean_editor(unreal)
    if evidence_identity.scene_identity(ROOT)!=identity:
        raise RuntimeError("Saved scene changed during exploration verification")
    report.update(status="success",scene_identity=identity,
                  limitations=["Static collision probes; not a full walking-controller or packaged-game test"])
    destination.write_text(json.dumps(report,indent=2)+"\n")
    print("EXPLORATION_COLLISION_OK",len(report["traces"]))
except Exception:
    report.update(status="failed",traceback=traceback.format_exc())
    destination.write_text(json.dumps(report,indent=2)+"\n")
    raise
