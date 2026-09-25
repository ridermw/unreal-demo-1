"""Request native in-viewport PIE for exploration and game-clock diagnostics."""

import unreal

performance = unreal.load_object(None, "/Script/UnrealEd.Default__EditorPerformanceSettings")
performance.set_editor_property("bThrottleCPUWhenNotForeground", False)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if levels.is_in_play_in_editor():
    raise RuntimeError("End the existing PIE session before starting a measurement session")
levels.editor_request_begin_play()
print("NATIVE_PIE_REQUESTED")
