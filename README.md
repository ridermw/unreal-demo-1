# Platform Nine

An original Victorian hidden-platform environment. `GOAL.md` is the authoritative
objective and evidence standard. The generated target is a reference, **not an
Unreal screenshot**.

## Restart checkpoint

- **M0 verified:** recovered source baseline; M1 active; M2-M5 pending.
- Starting commit: `cebd39e` on `main`; authorized remote:
  `https://github.com/ridermw/unreal-demo-1.git`.
- Project: `PlatformNine.uproject`, Unreal Engine 5.8.3.
- Required map: `/Game/Platform/Maps/HiddenPlatform` (**not created yet**).
- Fresh editor inspection: `/Temp/Untitled_0`, zero actors, empty `Content/`.
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
- **Next exact action:** implement `Scripts/build_unreal.py` with import-only,
  scene-assembly, and reopen-verification stages. Import the existing assets and
  inspect saved bounds/material slots before assembling the level.

## Execution and evidence gates

| Milestone | Gate | Status |
| --- | --- | --- |
| M0 | Reviewed source inventory, sanitized reference/configuration, pushed baseline | Verified in recovery commit |
| M1 | Idempotent import, saved assets, slot/scale/reference report | Active |
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
