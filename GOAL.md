# Platform Nine: Recovery and Completion Goal

Resume and complete the Platform 9 3/4-inspired Unreal scene in:

```text
/Users/mattheww/git/unreal-demo-1
```

First reconcile and clean up the interrupted work, then continue implementation using **Dream Loop PRO**. This is an execution goal, not another planning-only exercise. Inspect current state before acting. The status below records what was verified after the device restart on September 24, 2026, during the late-evening EDT session; it is not a substitute for checking the current filesystem and editor.

## Goal

Deliver a detailed, saved, explorable Unreal environment matching the existing target image: scarlet steam locomotive, Victorian brick platform, vaulted iron/glass roof, hanging 9 3/4 sign, luggage trolley, trunks, lanterns, and atmospheric steam. Open the completed level in Unreal and demonstrate it with actual Unreal screenshots.

Preserve the existing composition and reuse the generated assets where they serve the target. Improve inadequate geometry or materials rather than treating a successful export as proof of visual quality. Do not expand the scope into unrelated gameplay systems.

## Known State at Handoff

- `PlatformNine.uproject` exists in this repository and was open in Unreal Engine 5.8.3.
- The active level was `/Temp/Untitled_0`. `Content/` was empty.
- The original `/Users/mattheww/Documents/Unreal Projects/UEIntroProject` was intentionally deleted after explicit user approval. Do not recreate it or describe it as preserved.
- `.dream-loop/target.png` is the generated visual target, **not an Unreal render**.
- `Art/Textures/` contains generated brick, stone, scarlet, and leather PNGs plus generation metadata.
- `Art/Models/` contains 14 FBX groups, `HiddenPlatform.blend`, and `manifest.json`. Blender export succeeded; the models have not been visually validated in Unreal.
- `Scripts/build_station.py` generated those assets.
- `Scripts/probe_unreal.py` confirmed scripting API availability only. It did not import assets or build the scene.
- `Scripts/build_unreal.py` was planned but never created.
- A steam-image generation request was launched, but `Art/Textures/steam.png` was absent and its request outcome was unresolved.
- Branch `feat/platform-nine` had no commits, project files were untracked, and no git remote was configured. An internal Copilot checkpoint existed, but it was not a normal project commit or a substitute for versioning the deliverables.
- Unreal MCP responded at `http://127.0.0.1:8000/mcp` with 19 toolsets. Native tools were unavailable in the resumed session, but direct HTTP MCP calls worked, including a read of the current level.
- No actual railway-scene Unreal render, independent visual score, performance result, or saved scene-reopen verification had been produced.

## Asset and Evidence References

Inspect and preserve these existing repository-relative files:

| Path | Purpose and limits |
| --- | --- |
| `.dream-loop/target.png` | Locked visual target; not evidence of implementation. |
| `.dream-loop/target-prompt.txt` | Target generation instructions. |
| `.dream-loop/target.png.metadata.json` | Target generation provenance. |
| `.dream-loop/engine-probe.json` | Historical engine/API readiness result. |
| `.dream-loop/probe.log` | Historical toolchain probe log, not a scene-build result. |
| `.dream-loop/model-build.log` | Historical Blender export evidence. |
| `Art/Textures/` | Generated surface images and associated metadata. |
| `Art/Models/manifest.json` | Exported groups, material definitions, camera, and lamp placement. |
| `Art/Models/HiddenPlatform.blend` | Existing authored Blender source geometry. |
| `Art/Models/*.fbx` | The 14 exported geometry groups. |
| `Scripts/build_station.py` | Reproducible Blender scene/model generation. |
| `Scripts/probe_unreal.py` | Unreal scripting readiness check. |
| `PlatformNine.uproject` and `Config/` | New project descriptor and engine/editor configuration. |

Inventory any additional files before assuming this list is complete.

`.dream-loop/` is gitignored. Preserve it locally, and copy the locked target, prompt, and sanitized provenance into a tracked `Art/Reference/` directory. Verify that copied images match the originals. Do not move or delete the originals, or regenerate existing assets merely to simplify recovery. Preserve valuable deliverables in version control rather than leaving their only copies in ignored working directories.

Historical machine-local plans are under:

```text
/Users/mattheww/.copilot/session-state/a12c7184-450b-4017-927e-abb95361d6c5/files/platform-design.md
/Users/mattheww/.copilot/session-state/a12c7184-450b-4017-927e-abb95361d6c5/files/platform-plan.md
```

Those plans contain outdated intro-project preservation language and unimplemented steps. Use them as historical context only. Make the repository's progress documentation sufficient for another restart without depending on those machine-local files.

## Cleanup and Recovery

1. Recheck the filesystem, git state, running project, current level, and MCP connectivity. Preserve any changes made since this handoff.
2. Reconcile the task ledger and stale plans. Planning tasks marked done do not mean the scene exists. Record actual progress in `README.md`.
3. Preserve the target, generated textures, Blender source, exports, and reproducibility metadata. Do not broadly delete caches or directories. Ask before deleting files; approval to delete the old intro project is not approval for further deletion.
4. Inspect generated configuration and metadata for credentials or tokens before staging. Never print or commit secrets.
5. Establish a reviewed baseline git checkpoint. Do not invent a remote, claim a push, or silently discard existing work.
6. Reconcile interrupted generation jobs. A missing output or timed-out command does not prove a request was rejected or never accepted.

## Implementation Constraints

- Load the relevant skills, including Dream Loop **PRO**, and follow its asset-sourcing, judging, and stall rules. Do not restart design discovery or regenerate the target without a concrete need.
- Use the installed **`mockui` CLI for all image generation**, always with explicit output paths inside this repository. Do not substitute another image service.
- Reconcile the uncertain steam request if possible before submitting a replacement. Do not blindly duplicate potentially accepted generation jobs.
- Use existing Blender assets as the starting point. Inspect and improve them where the target requires it.
- Implement a repeatable Unreal import/build workflow: import meshes and textures, construct materials, assemble the scene, add lighting, atmosphere, and camera, and save `/Game/Platform/Maps/HiddenPlatform`.
- Resolve scale, axes, material assignments, collisions, and camera framing in the actual engine.
- Prefer native Unreal MCP tools when available. Otherwise use the verified HTTP endpoint or installed Unreal scripting facilities. An open port or successful handshake alone does not establish that an editor operation succeeded.
- For direct application UI interaction, use Computer Use. Do not bypass its safety controls with shell-based UI automation.
- Do not download external assets, provision services, or install new plugins without authorization.
- Surface failures explicitly. Treat missing completion reports, logged scripting errors, and missing outputs as failures even when a process exits successfully.

## Milestones

Execute these milestones in order. Each milestone has an explicit evidence gate. Make smaller commits within a milestone when independently working units are complete.

### M0: Recover and Checkpoint the Existing Work

- Reconcile repository, editor, MCP, task ledger, and stale plans.
- Inventory generated assets, historical evidence, and unresolved jobs.
- Review configuration and metadata for secrets before staging.
- Preserve the locked target and sanitized provenance in `Art/Reference/`.
- Establish a reviewed baseline commit containing the recoverable project, source assets, scripts, reference image, and accurate `README.md`.

**Exit evidence:** asset inventory, current-state summary, and baseline commit SHA. Clearly label the baseline as source assets and project setup, not a completed scene.

### M1: Import Assets Successfully

- Implement the repeatable Unreal import/material workflow.
- Import existing meshes and textures.
- Verify scale, orientation, material slots, references, and missing-file handling.
- Ensure re-running the workflow does not silently duplicate assets or actors.
- Save imported Unreal packages.

**Exit evidence:** saved Unreal assets, import report, relevant checks, and a reviewed commit.

### M2: Assemble and Save the First Complete Scene

- Place architecture, train, track, signs, furniture, and luggage.
- Set the target camera, initial lighting, and startup map.
- Save `/Game/Platform/Maps/HiddenPlatform`.
- Reload the saved map and verify its contents rather than relying on unsaved editor state.
- Capture the first actual Unreal screenshot.

**Exit evidence:** actual Unreal screenshot, saved-map verification, and a reviewed commit.

### M3: Complete the Visual Treatment

- Refine materials, lighting, steam, atmosphere, and fine details against the locked target.
- Reconcile the uncertain steam generation before replacing it.
- Inspect the scene from the target camera and other useful viewpoints to confirm it is real, explorable geometry.
- Establish and record a numeric acceptable-performance target appropriate to this device before declaring performance acceptable.
- Measure frame rate and frame time at the documented capture resolution and quality settings, after warmup.

**Exit evidence:** live screenshot, measurement conditions and performance results, and a reviewed commit.

### M4: Run the Dream Loop PRO Improvement Cycle

- Give an independent judge the target and actual Unreal screenshot, plus the previous screenshot and verdict when available.
- Use the Pro rubric: composition 0-3, lighting 0-3, materials 0-3, and details 0-1.
- Save each round's screenshot, verdict, category scores, and next fixes under `.dream-loop/`.
- Apply actionable feedback, validate changes, and capture the next live result.
- Follow the skill's stall/rethink rules instead of repeating small tweaks without progress.
- Commit each validated improvement round; do not batch the whole loop into one final commit.

**Exit evidence:** score at least 8/10 and acceptable measured performance, or an explicitly reported stall requiring user input. A stall is a blocked outcome, not scene completion. If performance requires optimization, re-judge afterward to detect visual regressions.

### M5: Verify and Hand Off

- Reopen the saved scene and confirm persistent assets and material assignments.
- Leave Unreal displaying the final saved level.
- Preserve selected final screenshots and the final verdict in a tracked repository location; working captures may remain in `.dream-loop/`.
- Update `README.md` with launch/rebuild instructions, results, and limitations.
- Review and commit the final coherent changes.

**Exit evidence:** final actual Unreal screenshot, visual score, frame rate and capture resolution, project/map paths, final commit, and an accurate git-status report.

## Checkpoint and Commit Discipline

- Make small, reviewed commits throughout each milestone whenever an independently working unit is complete. Milestones are not permission to defer all commits until their end.
- Commit after every completed milestone and validated visual improvement round when there are relevant changes. Do not create empty commits merely to satisfy a cadence.
- Before each commit, run the relevant checks, inspect the staged diff, exclude secrets, caches, and unrelated edits, and update progress documentation.
- Stage deliberately rather than blindly staging the entire worktree. Follow the current session's commit-trailer requirements.
- Maintain a restart-safe checkpoint in repository files, with a concise tracked summary in `README.md`. Record:
  - Current milestone and whether it is pending, active, blocked, or verified.
  - Last known-good commit and the saved map path.
  - Evidence paths and commands that established the current state.
  - Known failures, limitations, and the next exact action.
  - Outstanding generation request IDs, recorded status, and output paths, without credentials.
- Update that checkpoint after each milestone, after each visual round, before an editor restart, and before stopping. Do not depend only on chat, the session task database, or temporary files.
- Do not label failed or unverified work complete. Preserve failure details and distinguish a work-in-progress checkpoint from a validated milestone.
- Never assume a timed-out generation failed; reconcile its existing request. If the request cannot be reconciled, state the uncertainty before deciding whether to replace it.
- Push only if an authorized remote exists. Otherwise report: "Committed locally; no remote configured."

## Validation and Completion Standard

- Verify saved assets and the map reopen correctly.
- Capture real Unreal screenshots. Never present the target image or a Blender render as the finished Unreal scene.
- Completion requires the Dream Loop Pro visual threshold, acceptable measured performance, and a persistent saved scene. Report measured FPS, resolution, quality settings, and relevant limitations.
- Keep `README.md`, checkpoints, and commits synchronized with meaningful progress.
- Report concrete blockers honestly. Distinguish generated, imported, saved, rendered, and visually validated work.
- Finish with the actual screenshot, project/map paths, measured results, git status, and remaining limitations.

Proceed autonomously with local reversible work. Ask only for genuine blockers, destructive cleanup approval, external costs/access, or consequential scope decisions.
