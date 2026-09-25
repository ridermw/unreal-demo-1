# Platform Nine

An original Victorian hidden-platform environment. `GOAL.md` is the authoritative
objective and evidence standard. The generated target is a reference, **not an
Unreal screenshot**.

## Mac walkthrough app - built

Open the self-contained Apple Silicon Shipping application:

```text
Builds/PlatformNine-Mac-Shipping-20260925T142016/Mac/PlatformNine-Mac-Shipping.app
```

The approximately 842 MB bundle includes the runtime and cooked scene; Unreal Editor
is not required. It is ad-hoc signed for local running, **not Apple-notarized**.
The actual packaged executable loaded `HiddenPlatform` and passed fresh checks
for five views, preset keys, keyboard movement, mouse-look input and the Escape
menu at 1536x864. See `Evidence/app-package-report.json` and
`Evidence/App/packaged-20260925T143421/report.json`.

Controls: **Tab** explore/menu; **WASD** move; **mouse** look; **Q/E** or
**Ctrl/Space** vertical; **Shift** faster; **1-5** preset views; **Esc** menu;
**H** hide controls; **F11** fullscreen. Menu buttons include Explore, Next view,
Fullscreen and Quit. Physical mouse hit boxes, fullscreen and the Quit button
still have a manual UI check outstanding; work stopped after the build as requested.

Rebuild with `python3 Scripts/package_mac.py`; verify with
`python3 Scripts/verify_mac_app.py`. Mac packaging requires `-package` and
`-createappbundle` in addition to cook/stage/archive. `bUseZenStore=False` avoids
the stale Zen cook-store problem. The verifier writes inside the app sandbox and
copies evidence back to the repository. Failed earlier app outputs and identical
staging/binary copies were deleted with permission; only the successful app and
its distribution ZIP remain. Diagnostic logs remain local under `.dream-loop/`.

Native code is under `Source/PlatformNine/`. The saved, resource-packed Blender
inspection snapshot is
`Art/Models/SessionSnapshots/BlenderSession-20260925T142950.blend` (Git LFS);
it is not the authoritative full station source. Blender and Unreal Editor were
saved and closed. The app bundle and ZIP are ignored build outputs, not Git files.

## Current checkpoint

**Not complete.** The latest independent visual score is **5.4/10** (round 12,
58/58 components audited); the required threshold remains 8/10. The original
visual objective is paused. The user subsequently prioritized the standalone app
and requested stopping after it was built, followed by preservation and cleanup.
Do not interpret a working app or local improvements as visual acceptance.

- Project: `PlatformNine.uproject`, Unreal 5.8.3 on Apple M4 Pro / 48 GB.
- Saved map: `/Game/Platform/Maps/HiddenPlatform`. Current scene report: 99 generated
  actors, 14 authored mesh groups, 29 material packages and 44 imported texture images.
- Current actual target capture: `Evidence/final-candidate-target.png`. Its complete
  58-component verdict is `Evidence/rounds/round-12/verdict.json`. Best historical
  score was 5.5/10; the unchanged required score is 8/10.
- Runtime defaults are **High quality, 1536x864, 100% screen percentage, 32 FPS cap,
  one-frame thread lag disabled**. The last pre-app matched-state timing was
  **31.99 median FPS / 31.67 ms p95**, passing median >=30 FPS and p95 <=50 ms.
  This is not a fresh packaged-app performance measurement.
- Captures now reject unsaved platform changes and record the saved-scene hash,
  actual runtime settings, camera, PNG hash and completion status in sibling JSON.
  Profiles require finalized provenance bound to both log and CSV. Gallery
  acceptance requires matching capture/profile state and runtime conditions.
- `Evidence/exploration-report.json` verifies both platform floors, train and wall
  collision, Pawn blocking/complex-as-simple settings, and the open central route.
  These are actual engine probes, not a full packaged-player traversal test.
- `Evidence/play-exploration-report.json` verifies native DefaultPawn displacement
  and camera control in advancing PIE. No hardware-key simulation is claimed.
- `Evidence/inspection-opposite-platform.png` and other `inspection-*.png` files
  are actual Unreal alternate views; each has a capture receipt. Blender inspection
  renders stay under `.dream-loop/` and are never presented as Unreal evidence.
- The corrected source/assets are preserved on `main`; the LFS checkpoint
  `d702b9a` was pushed successfully. The separate **`checkpoint/platform-nine`**
  branch is an older recovery snapshot, not the current app.
  The seven unpublished commits after `ae13c86` were migrated to Git LFS.
  The original checkpoint `9ce49ef` is preserved under
  `backup/pre-lfs-20260925`; the migrated checkpoint is `15ffadd`.
  All 393 protected working-file hashes are unchanged, and published history plus
  Pages/recovery refs were preserved. See `Evidence/lfs-migration.json` and
  `Evidence/lfs-commit-map.csv` for verification and old/new commit IDs.
- Public review gallery: **https://ridermw.github.io/unreal-demo-1/**, deployed from
  `gh-pages`. It is a screenshot/audit gallery, not a playable browser Unreal build.
- **Paused:** no further app or art work is authorized by this checkpoint.
  The deployed gallery branch is still at `fab3616` (through round 07); newer
  evidence through round 12 is preserved on `main`, not yet redeployed.
  A new session should orient from the handoff and wait for the user's direction.

## Historical recovery notes (superseded by the checkpoint above)

- **Five-hour best-effort window active until September 25, 2026, 07:21 EDT
  (11:21 UTC). M4 and final completion are not accepted.**
  Source baseline: `ba06f5c`. Last known-good import checkpoint: **`b924990`**,
  reviewed and pushed to `origin/main`. Last verified milestone commit:
  **`53f4a8a` (partial M3 source/scene)**. This checkpoint fixes the recorded
  review issues and establishes real rendered-frame performance.
  **Visual acceptance and M4-M5 are not complete.**
- **Latest full-scene audit:** round05 **5.0/10**, all **58/58 components**
  checked. Judge reports **stalled** after structural rethinking. The user then
  requested best effort during a five-hour absence; this does not lower the
  acceptance standard or grant permission to rewrite unpublished history.
- **Round06 audit:** **5.3/10** (composition2.2, lighting1.4, materials1.3,
  details0.4), 58/58 components. Improved steam, window warmth, buffer assembly
  and station/train depth; still below acceptance. Running gear is the next
  targeted component. Round06 evidence is published independently while that
  next source/asset revision is in progress.
- **Round07 audit:** **5.3/10**, unchanged,58/58 components. Connected running
  gear is more substantial but still does not match the reference. A lossless
  pacing experiment (40FPS cap, one-frame thread lag disabled) measured
  33.47medianFPS and56.10ms p95, still failing. These are experimental conditions,
  not an accepted default or proof of completion. Foreground trolley/trunk/cloth
  proportions are the next isolated component pass.
- A complete reviewed recovery snapshot is pushed on
  `checkpoint/platform-nine` (`317efe7` initially); this does not alter local
  blocked history or advance `origin/main`.
- **Latest valid performance:** **34.47 median FPS, 58.05 ms p95** at 1536x864,
  High, 100% screen percentage, standalone Metal rendering. P95 still fails the
  50 ms target. Actual gameplay uses `PN_TargetCamera`, FOV70, verified during
  advancing native PIE in `Evidence/play-camera-verification.json`.
- **Important fidelity fix:** hero geometry must disable automatic Nanite building
  before reimport, not only after import. The sign's rendered triangle count went
  from940 to35,154; locomotive from5,164 to650,658; luggage from4,247 to268,922.
  Source counts are recorded as `exported_triangles`; non-Nanite imports now fail
  if they retain less than98% of the evaluated source triangles.
- **Sign-focused work:** `Scripts/extract_sign_reference.py` crops the target's
  face with explicit provenance, then maps it to real sign geometry. Scrollwork
  is traced into an angled3D support, not pasted scenery. Latest actual image:
  `Evidence/hero-fullgeometry-unreal.png`. Earlier focused review rated face8/10,
  bracket2.5/10; that review predates full-detail scrollwork restoration and is
  not proof of acceptance. The sign is not yet claimed picture-perfect.
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
- **Next exact action:** independent Dream Loop PRO comparison of
  `.dream-loop/round-00/unreal.png` with the locked target, then substantial
  geometry/material/lighting correction and performance optimization.
- **Dream Loop round 03:** score **4.8/10** (composition 2.1, lighting 1.2,
  materials 1.2, details 0.3). Another small gain, not acceptance. Judge flags
  "stall approaching"; next pass must address substantial roof depth, connected
  locomotive machinery, and warm reflected lighting. The gallery has all four
  judged frames (00-03). Round03 performance has not been remeasured.
- **Judge coverage correction:** earlier verdicts did not adequately inventory the
  scenery behind the train. Subsequent rounds must use
  `Art/Reference/visual-checklist.json` and `Scripts/judge_round.txt`: explicit
  train-front-to-back and full-scene component observations precede the unchanged
  PRO category score. Unmentioned regions must not be treated as correct.
  The gallery now displays the expandable58-item audits for rounds04and05.
- **Dream Loop round 02:** score **4.7/10** (composition 2.1, lighting 1.2,
  materials 1.1, details 0.3). Smaller cage and wetness improve the image, but
  locomotive proportions, material fidelity, roof depth and warm reflections
  remain below the target. The judge says continue, not stalled.
  Current measured performance: **45.99 median FPS / 53.68 ms p95**, still failing
  the <=50 ms p95 gate. The editor's realtime rendering was disabled during the
  standalone profile to avoid competing GPU work.
- **Dream Loop round 01:** score **4.5/10** (composition 2.0, lighting 1.2,
  materials 1.0, details 0.3), up from 3.4. Actual image:
  `Evidence/rounds/round-01/unreal.png`. The judge repeated structural gaps;
  the next pass must rethink proportions and architectural depth, not merely
  add small details. Performance must be remeasured after visual changes.
- **Human review gallery:** `https://ridermw.github.io/unreal-demo-1/`.
  GitHub Pages publishes `gh-pages:/`. Run `python3 Scripts/publish_rounds.py`
  after every independently judged round, then `python3 Scripts/deploy_pages.py`.
  Gallery images are actual Unreal captures, with a labeled generated-target
  comparison. It is not a playable browser port or a Pixel Streaming service.
- **Main push blocker:** local commit `142a732` contains an oversized historical
  roof FBX/package and GitHub rejected it. Corrected current roof files are below
  10 MiB, but the unpublished history still includes the oversized blobs.
  Permission was requested to preserve a backup ref and replace the unpublished
  commit; no response was available. **Do not amend/rewrite it without approval.**
  Last pushed main is `ae13c86`; later work is committed locally. The review
  gallery uses its own branch and is live independently.
- **Valid performance, target not met:** median **30.05 FPS**, median **33.27 ms**,
  p95 **86.35 ms** at 1536x864, High, 100% screen percentage. Native Unreal CSV
  `FrameTime`, 720 actual standalone Metal frames, first 360 discarded for warmup.
  `Evidence/performance-frames.csv` preserves 360 measured frames.
  `python3 Scripts/profile_unreal.py` repeats this offscreen rendered game profile
  (not NullRHI). It verifies actual resolution from engine metadata and excludes
  personal metadata from tracked frame evidence.
- The old Slate-only sample is invalid and not the current result. Native
  `LevelEditorSubsystem.editor_request_begin_play()` advances game time correctly
  in the editor viewport; MCP floating `StartPIE` did not. Use native scripted
  in-viewport play for exploration and standalone CSV for performance.
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
  to `127.0.0.1`, TTL 0. Remote execution is enabled in the current working session.
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
- These historical entries document earlier evidence and failures. They do not
  override the current checkpoint or certify visual acceptance.

## Execution and evidence gates

| Milestone | Gate | Status |
| --- | --- | --- |
| M0 | Reviewed source inventory, sanitized reference/configuration, pushed baseline | Verified in recovery commit |
| M1 | Idempotent import, saved assets, slot/scale/reference report | Verified in import checkpoint |
| M2 | Saved and reopened map, first actual Unreal image | Verified; rough baseline |
| M3 | Materials/atmosphere/detail pass and measured performance | First treatment and valid measurement recorded |
| M4 | Independent Dream Loop PRO score >=8/10 and performance pass | Active; not accepted |
| M5 | Final reopen, tracked screenshots/verdict, reviewed pushed handoff | Pending |

Performance acceptance is set **before measurement**: at 1536x864, 100% screen
percentage, High scalability, software Lumen, no hardware ray tracing, after at
least 120 warmup frames, target median >=30 FPS and 95th-percentile frame time
<=50 ms over >=300 frames. Device: Apple M4 Pro, 20 GPU cores, 48 GB memory.
Report editor/PIE conditions, frame caps and any deviation rather than silently
changing the target. Only matching, finalized evidence may satisfy the gate.

## Source and rebuild

### Git LFS

Install Git LFS before cloning or checking out the Unreal assets, then run
`git lfs install --local` and `git lfs pull` in this repository. `.gitattributes`
tracks Unreal packages (`.uasset`, `.umap`, `.ubulk`, `.uexp`), FBX and Blender
models, and PNG source textures under `Art/Textures/`.

Images under `Art/Reference/`, `Evidence/` and `docs/` remain ordinary Git files
so the review gallery can serve them. Enabling these rules does not itself convert
oversized blobs in existing commits. Any history migration must preserve the
current work and explicitly limit rewriting to the approved unpublished range;
do not rewrite `origin/main`, `gh-pages` or recovery refs implicitly.

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
- Repeated imports reuse and validate named packages without actor creation.
  All authored meshes now preserve full source geometry; imported triangle counts
  must retain at least 98% of the evaluated source rather than a simplified fallback.
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
  Use a fresh capture name: existing outputs are rejected to prevent stale pixels
  from being reported as success. `--view reverse|locomotive|luggage|opposite`
  captures genuine alternate viewpoints without editing saved camera actors.
- `python3 Scripts/profile_unreal.py`: current project pacing defaults, 360 warmup
  frames plus 360 measured frames. `--frame-cap 0 --frame-lag` requests an uncapped
  diagnostic variant; `--gpu-stats` adds detailed GPU instrumentation. Reports use
  confirmed engine readbacks, not requested settings. `--existing-log` requires
  finalized, untampered provenance; pending/failed/legacy captures cannot replay
  into successful evidence.
- `blender --background --python-exit-code 1 -P Tests/blender_geometry_contract.py`:
  checks continuous tube closure, outward winding and saved blanket edge winding.
- `python3 Scripts/editor_python.py Scripts/verify_exploration.py`: actual collision
  probes in the saved live map. `Scripts/explore_unreal.py` releases the piloted
  camera for normal editor navigation; `--play-camera` uses the possessed fly pawn
  after native PIE is started with `Scripts/start_performance_pie.py`.
- To reapply refined source assets in the live editor, enable loopback Python
  remote execution through MCP, then run:
  `python3 Scripts/editor_python.py Scripts/build_unreal.py --stage import --reimport`,
  followed by the `--stage materials` and `--stage scene` calls.
  This sequence is important: material upgrading replaces baseline graph inputs
  with the dedicated generated maps. Save first and inspect the results.
- `Scripts/measure_performance.py` is unfinished diagnostic tooling. It now rejects
  zero game-delta samples but has not yet produced a valid measurement.
- Pause review findings resolved: reused meshes now reject source-hash mismatches;
  existing generated outputs reconcile and sanitize receipts without resubmission;
  performance uses native game/render CSV frame timing; redundant intermediate
  roof arches removed (source vertices reduced from 1,090,710 to 758,934).
  `Evidence/review-m3-pause.json` remains the historical review receipt.
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
