---
artifact_contract: "ce-handoff/v1"
created_at: "2026-09-25T14:57:20Z"
title: "Platform Nine: Mac app delivered, original visual objective paused"
summary: "A working Mac walkthrough is preserved in a GitHub release; scene acceptance remains incomplete and the user ended the session."
keywords: ["platform-nine", "unreal", "mac-app", "git-lfs", "paused"]
cwd: "/Users/mattheww/git/unreal-demo-1"
repository: "ridermw/unreal-demo-1"
repo_root_sha: "cebd39ed61fc7e7b1610c4f8fc10ca4934fd13fe"
branch: "main"
head: "222100a59a833dac683c92ee38637b15d184b4e4"
resume_focus: "Orient from the delivered app and unfinished visual goal, then wait for the user's direction."
---

# Current intent and stopping point

The user selected a **standalone Mac walkthrough app**, then explicitly said
**"stop after the app has been built."** After delivery, the user requested saving
and closing Blender and Unreal, a durable restart handoff, committing/pushing
everything useful, and retaining only the successful app while deleting failed
attempts. This document preserves that stopping point, not authorization to
resume autonomous art work.

The runtime/app checkpoint is `222100a` on `main`, pushed and verified against
`origin/main`. This handoff, release receipt and final README are preserved in a
subsequent documentation commit; the frontmatter `head` names the app checkpoint,
not that later commit. Blender, Unreal Editor and the walkthrough executable
were all closed at handoff. No build, generation or review job remains pending.

## Start with these authoritative pointers

| Reference | What matters |
| --- | --- |
| `README.md`, first two sections | App location, controls, release link, paused objective and current limitations; later historical notes are superseded. |
| `Evidence/app-distribution.json` | Exact app/ZIP identity, verified remote digest, release commit and approved cleanup scope. |
| `Evidence/app-package-report.json` | Successful Shipping archive and packaged-runtime result, not an editor-only smoke test. |
| `Evidence/App/packaged-20260925T143421/report.json` and three PNGs | Actual packaged map, five views, input checks and 1536x864 screenshots. |
| `GOAL.md` | Original M0-M5 objective and unchanged visual/performance acceptance thresholds. |
| `Evidence/rounds/round-12/verdict.json` | Latest 5.4/10 verdict with all 58 components audited; required score remains 8/10. |

## Delivered app and remote preservation

The sole retained local app, relative to this repository, is:

```text
Builds/PlatformNine-Mac-Shipping-20260925T142016/Mac/PlatformNine-Mac-Shipping.app
```

It is an Apple Silicon `arm64` Shipping build, self-contained with cooked content,
approximately 883 MB / 842 MiB. Unreal Editor is not required. It is **ad-hoc
signed, not Apple-notarized**; Gatekeeper may block downloaded copies. The bundle
identifier remains `com.YourCompany.PlatformNine`. It is not a Windows, Intel Mac,
browser or Pixel Streaming deliverable.

The app binary is **not in Git or LFS**. Its ZIP and checksum are uploaded to the
GitHub prerelease `mac-walkthrough-20260925` in `ridermw/unreal-demo-1`, targeting
`222100a59a833dac683c92ee38637b15d184b4e4`.
The local ZIP is `Builds/PlatformNine-Mac-arm64-20260925.zip` (521,979,534 bytes).
GitHub reports the same SHA-256 as the locally verified ZIP:

```text
12a16045de6db4553d9388b15905a410ba1c9b7c5f20dde92b3cfce2ba678449
```

All 30 app files match the ZIP contents; executable permissions are retained.
The release is the remote binary backup. Local `Builds/` remains ignored.
On a fresh checkout, the app comes from the release rather than `git lfs pull`;
LFS restores the source assets separately.

Controls: **Tab** explore/menu; **WASD** move; **mouse** look; **Q/E** or
**Ctrl/Space** vertical; **Shift** faster; **1-5** presets; **Esc** menu;
**H** hide controls; **F11** fullscreen. HUD buttons: Explore, Next view,
Fullscreen, Quit.

## Evidence and remaining limitations

- The packaged app loaded `HiddenPlatform`, verified all five views, preset-key
  input, keyboard movement (167.41 cm), mouse-look and Escape/menu input.
  Screenshots are 1536x864 at 100% screen percentage. These are simulated engine
  input events, not physical hardware-input claims.
- Physical mouse hit boxes, fullscreen and the Quit button remain **manually
  unverified**. The smoke run exits programmatically. Signed-bundle verification
  passed, but installation on another Mac was not tested.
- The final Python discovery run passed **34 tests**. The existing final
  read-only app review returned **no significant issues**. No review result is
  still outstanding.
- `Evidence/App/uncooked-20260925T120522/` is earlier Editor-Cmd evidence.
  Editor-only Python plugin errors made that run insufficient as packaged proof;
  it is retained for provenance, not used instead of the successful packaged run.
- Initial M0-M3 work is preserved; M4 visual acceptance is stalled and M5 final
  original-objective acceptance remains incomplete. Latest score is **5.4/10**;
  best historical score was **5.5/10**, not the required **8/10**.
- Last **pre-app** matched-state scene profile: **31.99 median FPS / 31.67 ms
  p95**, High quality, 1536x864, 100%, 32 FPS cap, one-frame thread lag disabled.
  It passed the original timing thresholds but is **not a new packaged-app
  performance profile**. Fullscreen adjusts rendering scale to preserve a
  roughly 1536x864 render budget; it does not promise full-Retina rendering.
- The static Pages gallery is not playable. `gh-pages` was verified at
  `fab361698ffd5801601ccb7ede1c08cb203aac17` (through round 07); newer rounds
  through 12 are preserved on `main` but were not redeployed during handoff.

## Rebuild entry points and abandoned approaches

`Scripts/package_mac.py` owns Shipping packaging; `Scripts/verify_mac_app.py`
owns sandbox-safe packaged verification. Their default commands are:

```bash
python3 Scripts/package_mac.py
python3 Scripts/verify_mac_app.py
python3 -m unittest discover -s Tests -v
```

These are reproduction references, not a request to run another build on resume.
The last toolchain was Unreal 5.8.3, Xcode 27.0 / Mac SDK 27.0, and Blender 5.2.1
LTS. The engine is machine-local at `/Users/Shared/Epic Games/UE_5.8`.
`Source/PlatformNine.Target.cs` and `PlatformNineEditor.Target.cs` use
BuildSettingsVersion.V7 and Unreal5_8 include ordering.

- **Cook-store trap:** stale `Saved/Cooked/Mac/ue.projectstore` metadata caused
  connection retries and a stalled cook. `Config/DefaultGame.ini` now sets
  `bUseZenStore=False`. The stale descriptor was preserved locally under
  `.dream-loop/preserved-zen-cook-*/`; it is not required to rebuild.
- **Incomplete archive trap:** cook/stage/archive alone returned success with a
  roughly 267 MB executable-only bundle. Packaging requires both `-package` and
  `-createappbundle`, in addition to build/cook/stage/Pak/IoStore/compression.
  The script rejects an archive missing cooked containers.
- **Sandbox trap:** exit code 0 without a smoke report is not success. The
  sandbox cannot write directly to repository evidence. The verifier writes
  into the machine-local app container under
  `~/Library/Containers/com.YourCompany.PlatformNine/Data/Library/Caches/PlatformNineVerification/`,
  then copies evidence unchanged. Each run requires a fresh directory.
- `ViewerPlayerControllerSmoke.cpp` initializes smoke handling before camera
  validation so startup failures are explicit; stale evidence cannot be reused.
- `Config/DefaultInput.ini` disables the engine's F11 interception. The viewer
  handles that key itself so the keyboard and HUD button share behavior.
- `PlatformNine.uproject` restricts Python/MCP/editor plugins to Editor targets.
  EnhancedInput is a runtime dependency. The game mode, fly pawn, controller
  and HUD are in `Source/PlatformNine/`; Mac plist/entitlement templates are
  preserved under `Build/Mac/Resources/`.

Successful packaging diagnostics remain machine-local at
`.dream-loop/package-mac-20260925T142016.log`. Earlier logs ending
`121303` (stalled cook) and `123125` (incomplete archive), plus
`.dream-loop/handoff-tests.log`, remain local/ignored. These bulky diagnostics
are not remotely backed up; the essential conclusions and runtime evidence are.

## Scene/source recovery

- Saved map: `/Game/Platform/Maps/HiddenPlatform`. Latest scene report records
  99 generated actors, 14 authored mesh groups, 29 material packages, 44 textures.
- `Art/Models/Refined/HiddenPlatform.blend` and
  `Art/Models/manifest.json` identify authoritative refined geometry and exports.
  `Scripts/build_station.py`, `build_unreal.py`, `station_scene.py`,
  `station_materials.py` and `station_steam.py` are the procedural pipeline.
- `Art/Models/SessionSnapshots/BlenderSession-20260925T142950.blend` is the
  separately saved, resource-packed inspection session (11,598,004 bytes).
  It includes inspected luggage/default objects, **not the complete station**.
  It was committed and uploaded through LFS during final preservation.
- Automatic Nanite building must be disabled **before reimport** to retain the
  modeled detail. Disabling it after import did not restore source geometry.
  Imported non-Nanite triangles must retain at least 98% of evaluated exports.
- Blender `(x,y,z)` meters maps to Unreal `(100*x,-100*y,100*z)` centimeters.
  Continuous swept tubes replaced capped per-segment cylinders; cloth winding
  was corrected. `Tests/blender_geometry_contract.py` captures geometry checks.
- The sign uses a user-authorized crop of the locked target on actual 3D sign
  geometry, with separately modeled ornament. `Scripts/extract_sign_reference.py`
  records provenance. The overall sign was not claimed picture-perfect.
- `Art/Reference/visual-checklist.json` and `Scripts/judge_round.txt` enforce
  all 58 components, including the opposing facade behind the train.
  `Scripts/capture_unreal.py`, `profile_unreal.py` and `evidence_identity.py`
  bind actual Unreal captures/profiles to saved-scene identity and runtime
  conditions; target images and Blender renders are not Unreal evidence.
- The user explicitly requested reading the `unreal-mcp` skill before using
  Unreal MCP. The newer Blender and Unreal technical-art skills are available,
  but neither application needs to be reopened just to read this handoff.

## Git/LFS and approved cleanup

Git LFS is configured and working. The seven formerly unpublished commits after
`ae13c86` were migrated; published history was not rewritten. The LFS checkpoint
`d702b9a` and app commit `222100a` were pushed to `main`.
`Evidence/lfs-migration.json` and `Evidence/lfs-commit-map.csv` record the verified
393 unchanged protected working files and old/new commit IDs. Do not repeat
the migration.

The local `backup/pre-lfs-20260925` ref preserves the old raw-blob history;
`checkpoint/platform-nine` is an older remote recovery branch, not the app.
Those refs and `gh-pages` were intentionally left unchanged. An indiscriminate
push of all refs would include the oversized pre-LFS history.

LFS covers Unreal packages, FBX, Blender files and source texture PNGs.
Reference/evidence/docs images stay in ordinary Git for the gallery.
Repository-local credentials use `gh auth git-credential`; no token is stored
in source. The new Blender snapshot's LFS upload was confirmed during app push.

With the user's explicit approval to remove failed/duplicate apps, these exact
generated outputs were removed:

```text
Builds/PlatformNine-Mac-Shipping-20260925T121303/
Builds/PlatformNine-Mac-Shipping-20260925T123125/
Saved/StagedBuilds/Mac/PlatformNine-Mac-Shipping.app/
Binaries/Mac/PlatformNine-Mac-Shipping.app/
```

The last two bundles were hash-identical to the retained successful app.
No authoritative models, textures, source or runtime evidence were deleted.
Generated counters, file-order logs, `.DS_Store`, caches and build outputs remain
ignored. One successful `.app` plus one distribution ZIP remains locally.

## Continuity boundary

The durable recovery set is the repository (including LFS) **plus the release
asset**. Local ignored diagnostics are supplementary. The handoff itself is
committed, not dependent on temporary session storage.

The appropriate next-session action is orientation and confirmation of the
user's new direction. Manual app UI checks, notarized distribution, gallery
deployment and further art improvements are possible future work, **not active
tasks or implied authorization**. The original 8/10 visual objective remains
explicitly incomplete.
