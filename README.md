# Platform Nine

An original Victorian hidden-platform environment. `GOAL.md` is the authoritative
objective and evidence standard. The generated target is a reference, **not an
Unreal screenshot**.

## Restart checkpoint

- **M0-M1 verified:** source baseline `ba06f5c`; M2 next; M3-M5 pending.
- Starting commit: `cebd39e` on `main`; authorized remote:
  `https://github.com/ridermw/unreal-demo-1.git`.
- Project: `PlatformNine.uproject`, Unreal Engine 5.8.3.
- Required map: `/Game/Platform/Maps/HiddenPlatform` (**not created yet**).
- Last map inspection: `/Temp/Untitled_0`, zero scene actors. M1 now has 35 saved
  packages: fourteen combined meshes, seventeen materials, four textures.
  Native MCP responds at `http://127.0.0.1:8000/mcp` with 19 toolsets.
- Recovered: 14 FBX groups, Blender source, four generated surface textures.
  `Evidence/source-inventory.json` records sizes and SHA-256 checksums.
- Locked reference: `Art/Reference/target.png`, copied byte-for-byte from
  `.dream-loop/target.png`; original working evidence remains untouched.
- The initial commit included an automatically generated Android file-server
  token. Recovery disables that unused service and removes the token from current
  configuration; historical commits have not been rewritten. Metadata is
  allowlisted to omit cloud account/deployment identifiers.
- Historical steam generation remains **unresolved**: no output, running process,
  request ID, or completion receipt recovered from local/cloud session history
  and `mockui history`. No replacement has yet been submitted.
- **Next exact action:** add scene assembly and reopen verification to
  `Scripts/build_unreal.py`, run `python3 Scripts/run_unreal.py scene`, then load
  the saved map through native MCP and capture its actual viewport.

## Execution and evidence gates

| Milestone | Gate | Status |
| --- | --- | --- |
| M0 | Reviewed source inventory, sanitized reference/configuration, pushed baseline | Verified in recovery commit |
| M1 | Idempotent import, saved assets, slot/scale/reference report | Verified in import checkpoint |
| M2 | Saved and reopened map, first actual Unreal image | Pending |
| M3 | Materials/atmosphere/detail pass and measured performance | Pending |
| M4 | Independent Dream Loop PRO score >=8/10 and performance pass | Pending |
| M5 | Final reopen, tracked screenshots/verdict, reviewed pushed handoff | Pending |

Performance acceptance is set **before measurement**: at 1536x864, 100% screen
percentage, High scalability, software Lumen, no hardware ray tracing, after at
least 120 warmup frames, target median >=30 FPS and 95th-percentile frame time
<=50 ms over >=300 frames. Device: Apple M4 Pro, 20 GPU cores, 48 GB memory.
Report editor/PIE conditions and any deviation rather than silently changing the
target. No performance result or visual score exists yet.

## Source and rebuild

- `Scripts/build_station.py`: existing Blender generation/export source.
  Do not rerun it in an unsaved Blender session: it clears that session's scene.
  Existing source and exports are preserved and are the starting point.
- `Scripts/probe_unreal.py`: API readiness only, not scene-build evidence.
- `python3 Scripts/run_unreal.py import`: checked Unreal commandlet import.
  It requires a fresh success report and no logged Python failures, not just exit
  code zero. Override `UNREAL_EDITOR_CMD` for another engine install.
- `python3 -m unittest discover -s Tests -v`: source and mesh-contract tests.
- `Evidence/import-report.json`: engine version, exact material graph/texture
  references, per-group slots, axis-specific centimeter bounds, triangles, Nanite.
  Blender `(x,y,z)` meters maps to Unreal `(100*x,-100*y,100*z)` centimeters.
  Mesh collision uses complex-as-simple for exploration; not simulated bodies.
- Repeated imports reuse and validate the same packages (35 total), without
  actor creation. Groups with translucent glass do not use Nanite.
- Legacy FBX crashed in headless mode while opening a message-log window.
  Use the explicit Interchange pipeline, not `AssetImportTask.options` for FBX:
  that field did not apply Interchange options. Ten unintended test-import
  packages were **moved, not deleted**, to
  `.dream-loop/failed-import-preserved/`. They are not part of the scene.
- `Scripts/inspect_blender_sources.py` enriches the manifest using saved Blender
  geometry without re-exporting it. Source bounds and exact slot sets are checked
  on every Unreal import. Detailed source vertices differ from Nanite fallback
  triangle counts; the report labels the latter as engine LOD0 triangles.
- `Scripts/recover_sources.py`: reference preservation, sanitized provenance,
  credential removal from unused file-server settings, source inventory.
- All image generation uses `mockui` and explicit repository output paths.
  No external asset downloads or new plugins/services are authorized.
- `.dream-loop/`, `Saved/`, engine caches and intermediate data are not deliverables.
  Selected final Unreal evidence will be tracked under `Evidence/`.

Open `PlatformNine.uproject` with the installed 5.8 editor. The startup map setting
already names the intended map, but that map does not yet exist. Native MCP is
preferred for inspection; project Python scripts can be run from Unreal's Cmd
console as `py "/absolute/path/to/script.py"`.
