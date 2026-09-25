# Platform Nine

An original Victorian hidden-platform environment. `GOAL.md` is the authoritative
objective and evidence standard. The generated target is a reference, **not an
Unreal screenshot**.

## Restart checkpoint

- **PAUSED at user request for another session restart. M0-M2 verified.**
  Source baseline: `ba06f5c`. Last known-good import checkpoint: **`b924990`**,
  reviewed and pushed to `origin/main`. Last verified milestone commit:
  **`1647362` (M2)**. The subsequent pause commit preserves partial M3 work;
  **M3-M5 are not complete**.
- Starting commit: `cebd39e` on `main`; authorized remote:
  `https://github.com/ridermw/unreal-demo-1.git`.
- Project: `PlatformNine.uproject`, Unreal Engine 5.8.3.
- Saved map: **`/Game/Platform/Maps/HiddenPlatform`**.
- Fresh-process reopen verification now confirms **39 generated actors**,
  fourteen mesh assignments, material-slot order and the revised camera.
- **Partial M3:** 37 source texture PNGs: twelve albedo/normal/roughness sets plus
  a steam density sprite. All 33 new `mockui` requests completed; original four
  color textures were retained. Flare generated new color/steam images; Sunburst
  generated aligned normal and roughness maps. Verified receipts and hashes:
  `Evidence/texture-generation.json`. No generation job remains running.
- Refined masonry bays/arches, covered roof/skylights, paving and ballast are
  saved in `Art/Models/Refined/`; original FBX and `.blend` files remain in place.
  `Art/Models/manifest.json` now selects the refined sources.
  `Art/Models/source-baseline-manifest.json` preserves the original mapping.
- Dedicated PBR materials, revised light/camera setup and layered steam cards
  are imported and saved. `Evidence/materials-report.json` lists texture bindings.
  `Evidence/m3-unreal-treatment.png` is the actual 1536x864 Unreal result,
  **not visually accepted**; the scene still differs substantially from the target.
  Native MCP responds at `http://127.0.0.1:8000/mcp` with 19 toolsets.
- Recovered: 14 FBX groups, Blender source, four generated surface textures.
  `Evidence/source-inventory.json` records sizes and SHA-256 checksums.
- Locked reference: `Art/Reference/target.png`, copied byte-for-byte from
  `.dream-loop/target.png`; original working evidence remains untouched.
- The initial commit included an automatically generated Android file-server
  token. Recovery disables that unused service and removes the token from current
  configuration; historical commits have not been rewritten. Metadata is
  allowlisted to omit cloud account/deployment identifiers.
- Historical steam generation remains **unresolved**, with no recoverable request
  ID. One explicitly tracked replacement completed as `Art/Textures/steam.png`;
  do not submit another merely to reconcile the historical request.
- **Next exact action:** load the newly installed Unreal skills and Dream Loop
  PRO, recheck editor/MCP/git, then diagnose the non-advancing PIE world before
  claiming performance. Continue visual refinement and M4 judging afterward.
- **Performance is NOT verified.** `Evidence/performance-report.json` is
  explicitly `invalid`; its values are isolated under `rejected_ui_only_sample`.
  Slate ticked, but PIE world time and delta stayed zero with gameplay pause false
  and time dilation 1.0. Those UI intervals are not game FPS.
  Native `StartPIE` twice reported "PIE ended before warmup completed" while
  `IsPIERunning` remained true. Investigate that lifecycle problem, not a new
  performance target. PIE was stopped before this pause.
- The live background-throttle preference was unexpectedly true despite project
  defaults. It was set false through MCP. On this Mac, a floating PIE window
  setting of 1536x844 produced a measured client viewport of 1536x864.
  Verify actual client dimensions rather than assuming window settings match.
- `python3 Scripts/run_unreal.py scene` assembles/upserts the level; `verify`
  reopens it in a fresh process. Both stages are implemented.
- On resume, load the newly installed Unreal skills and Dream Loop **PRO**;
  recheck git, the current editor/project/map, MCP, and saved assets before acting.
  Do not regenerate the locked target or redo M0/M1 without evidence of a problem.
- Native MCP inspection works. Computer Use console input did not reliably
  execute Python. `Scripts/editor_python.py` now connects to the live editor via
  the installed SDK: loopback-unicast discovery with a wildcard multicast-response
  listener resolves this Mac's discovery issue. The editor endpoint remains bound
  to `127.0.0.1`, TTL 0. Remote execution was **disabled again before this pause**.
  No new plugin or external service was installed.
- **First actual Unreal screenshot:** `Evidence/m2-unreal-first.png`, native
  MCP viewport capture, 1535x1818, FOV 90 (not yet target framing).
  `Evidence/m2-capture.json` records provenance. It shows a rough scene with
  overbright light, overly open windows/roof and material fallbacks, not completion.
  Six fallback shaders were traced to a disconnected desaturation input; the
  importer now repairs and checks that connection; live native material
  compilation passed. `Evidence/m2-unreal-camera.png` is the corrected-material
  1536x864 actual Unreal target-camera capture at FOV 70. Its visual quality is
  still inadequate: bright/open architecture, basic surface detail and no steam.
- **No Dream Loop score or valid FPS measurement exists yet.**
  Saved/imported does not mean visually accepted.

## Execution and evidence gates

| Milestone | Gate | Status |
| --- | --- | --- |
| M0 | Reviewed source inventory, sanitized reference/configuration, pushed baseline | Verified in recovery commit |
| M1 | Idempotent import, saved assets, slot/scale/reference report | Verified in import checkpoint |
| M2 | Saved and reopened map, first actual Unreal image | Verified; rough baseline |
| M3 | Materials/atmosphere/detail pass and measured performance | Paused; partial, performance invalid |
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
- `python3 Scripts/editor_python.py Scripts/capture_unreal.py --name <capture>`:
  schedule a live 1536x864 target-camera capture under `Evidence/`.
  Verify the output file and dimensions after the task completes. This script
  must run in the live editor, never the NullRHI commandlet.
  It retains the screenshot task and requests 32 settling frames. If a background
  capture does not complete, native `CaptureViewport` triggered the pending
  high-resolution draw in this session; verify the output rather than resubmit.
- To reapply refined source assets in the live editor, enable loopback Python
  remote execution through MCP, then run:
  `python3 Scripts/editor_python.py Scripts/build_unreal.py --stage import --reimport`,
  followed by the `--stage materials` and `--stage scene` calls.
  This sequence is important: material upgrading replaces baseline graph inputs
  with the dedicated generated maps. Save first and inspect the results.
- `Scripts/measure_performance.py` is unfinished diagnostic tooling. It now rejects
  zero game-delta samples but has not yet produced a valid measurement.
- **Pause review findings to fix before M3 completion:** reused meshes must not
  receive a new source hash without importing it; existing generated outputs must
  reconcile interrupted job bookkeeping before reporting completion; performance
  must track newly advanced game frames rather than Slate intervals; intermediate
  roof arches are currently duplicated fourfold by their placement loop.
  See `Evidence/review-m3-pause.json`. This is a reviewed **WIP checkpoint with
  known issues**, not an approved final visual/performance milestone.
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
loads the saved HiddenPlatform map. Native MCP is
preferred for inspection; project Python scripts can be run from Unreal's Cmd
console as `py "/absolute/path/to/script.py"`.
