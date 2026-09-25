"""Measure unique advancing PIE frames, never Slate-only refresh intervals."""

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
        "frame_source": "Unique advancing PIE game times, game delta and wall-clock cross-check",
        "device": "Apple M4 Pro, 20 GPU cores, 48 GB",
        "target": {"median_fps_minimum": 30, "p95_frame_ms_maximum": 50},
        "utc": datetime.now(timezone.utc).isoformat()}
REPORT.write_text(json.dumps(data, indent=2) + "\n")
state = {"frames": 0, "previous": time.perf_counter(), "wall_ms": [], "game_ms": [], "handle": None,
         "game_time": unreal.SystemLibrary.get_game_time_in_seconds(world),
         "started": time.perf_counter(), "skipped_ui_ticks": 0}
unreal._platform_perf_running = True


def tick(delta_seconds):
    try:
        now = time.perf_counter()
        if now - state["started"] > 120:
            raise RuntimeError("Game-frame measurement exceeded 120-second deadline")
        current = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if current is None:
            raise RuntimeError("PIE ended during measurement")
        game_time = unreal.SystemLibrary.get_game_time_in_seconds(current)
        if game_time <= state["game_time"]:
            state["skipped_ui_ticks"] += 1
            return
        game_ms = unreal.GameplayStatics.get_world_delta_seconds(current) * 1000
        elapsed_game_ms = (game_time - state["game_time"]) * 1000
        wall_ms = (now - state["previous"]) * 1000
        state["previous"] = now
        state["game_time"] = game_time
        state["frames"] += 1
        if abs(game_ms - elapsed_game_ms) > max(0.5, game_ms * 0.10):
            raise RuntimeError("Sampler missed game frames or game clock is dilated")
        if state["frames"] <= 120:
            return
        state["wall_ms"].append(wall_ms)
        state["game_ms"].append(game_ms)
        if len(state["wall_ms"]) < 360:
            return
        ordered = sorted(state["game_ms"])
        if min(state["game_ms"]) <= 0:
            raise RuntimeError("Game world did not advance on every sampled frame; UI intervals are not valid FPS")
        median_ms = statistics.median(ordered)
        p95 = ordered[int((len(ordered)-1)*0.95)]
        discrepancy = abs(sum(state["wall_ms"]) / sum(state["game_ms"]) - 1)
        if discrepancy > 0.10:
            raise RuntimeError(f"Wall/game duration mismatch: {discrepancy:.1%}")
        data.update({
            "status": "success", "median_fps": 1000 / median_ms,
            "average_fps": 1000 / statistics.mean(ordered), "median_frame_ms": median_ms,
            "p95_frame_ms": p95, "game_median_frame_ms": statistics.median(state["game_ms"]),
            "wall_frame_intervals_ms": state["wall_ms"], "game_frame_intervals_ms": state["game_ms"],
            "skipped_ui_ticks": state["skipped_ui_ticks"], "wall_game_duration_error": discrepancy,
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
