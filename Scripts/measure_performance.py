"""Collect warmed-up PIE frame intervals without blocking Unreal's game thread."""

from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import time

import unreal


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Evidence/performance-report.json"
if getattr(unreal, "_platform_perf_running", False):
    raise RuntimeError("A performance measurement is already running")
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if world is None:
    raise RuntimeError("Start Play In Editor before measuring")
controller = unreal.GameplayStatics.get_player_controller(world, 0)
if controller is None:
    raise RuntimeError("No PIE player controller")
resolution = tuple(controller.get_viewport_size())
if resolution != (1536, 864):
    raise RuntimeError(f"PIE resolution must be 1536x864, got {resolution}")
for command in ("r.ScreenPercentage 100", "r.VSync 0", "t.MaxFPS 0"):
    unreal.SystemLibrary.execute_console_command(world, command)
settings = {}
for name in ("sg.ViewDistanceQuality", "sg.AntiAliasingQuality", "sg.ShadowQuality",
             "sg.GlobalIlluminationQuality", "sg.ReflectionQuality", "sg.PostProcessQuality",
             "sg.TextureQuality", "sg.EffectsQuality", "sg.ShadingQuality"):
    settings[name] = unreal.SystemLibrary.get_console_variable_int_value(name)
    if settings[name] != 2:
        raise RuntimeError(f"Expected High quality (2), got {name}={settings[name]}")
data = {"status": "warming-up", "warmup_frames": 120, "measurement_frames": 360,
        "resolution": resolution, "screen_percentage": 100, "quality": settings,
        "frame_source": "PIE game-world delta seconds and independent Slate wall-clock intervals",
        "device": "Apple M4 Pro, 20 GPU cores, 48 GB",
        "target": {"median_fps_minimum": 30, "p95_frame_ms_maximum": 50},
        "utc": datetime.now(timezone.utc).isoformat()}
REPORT.write_text(json.dumps(data, indent=2) + "\n")
state = {"frames": 0, "previous": time.perf_counter(), "wall_ms": [], "game_ms": [], "handle": None}
unreal._platform_perf_running = True


def tick(delta_seconds):
    try:
        now = time.perf_counter()
        wall_ms = (now - state["previous"]) * 1000
        state["previous"] = now
        state["frames"] += 1
        if state["frames"] <= 120:
            return
        current = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if current is None:
            raise RuntimeError("PIE ended during measurement")
        state["wall_ms"].append(wall_ms)
        state["game_ms"].append(unreal.GameplayStatics.get_world_delta_seconds(current) * 1000)
        if len(state["wall_ms"]) < 360:
            return
        ordered = sorted(state["wall_ms"])
        if min(state["game_ms"]) <= 0:
            raise RuntimeError("Game world did not advance on every sampled frame; UI intervals are not valid FPS")
        median_ms = statistics.median(ordered)
        p95 = ordered[int((len(ordered)-1)*0.95)]
        data.update({
            "status": "success", "median_fps": 1000 / median_ms,
            "average_fps": 1000 / statistics.mean(ordered), "median_frame_ms": median_ms,
            "p95_frame_ms": p95, "game_median_frame_ms": statistics.median(state["game_ms"]),
            "wall_frame_intervals_ms": state["wall_ms"], "game_frame_intervals_ms": state["game_ms"],
            "meets_target": 1000 / median_ms >= 30 and p95 <= 50,
        })
        REPORT.write_text(json.dumps(data, indent=2) + "\n")
        unreal.unregister_slate_post_tick_callback(state["handle"])
        unreal._platform_perf_running = False
        unreal.log("PLATFORM_PERFORMANCE_COMPLETE " + str(REPORT))
    except Exception as error:
        data.update({"status": "failed", "error": str(error)})
        REPORT.write_text(json.dumps(data, indent=2) + "\n")
        unreal.unregister_slate_post_tick_callback(state["handle"])
        unreal._platform_perf_running = False
        unreal.log_error("PLATFORM_PERFORMANCE_FAILED " + str(error))
        raise


state["handle"] = unreal.register_slate_post_tick_callback(tick)
unreal._platform_perf_state = state
print("PERFORMANCE_SCHEDULED", str(REPORT))
