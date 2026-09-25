# Platform Nine

An original Victorian hidden-platform environment. `GOAL.md` is the authoritative
objective and evidence standard. The generated target is a reference, **not an
Unreal screenshot**.

## Restart checkpoint

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
- **No Dream Loop score exists yet; frame pacing fails the acceptance target.**
  Saved/imported does not mean visually accepted.

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
