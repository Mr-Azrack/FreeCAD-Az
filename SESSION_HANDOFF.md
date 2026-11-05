# FreeCAD-Az — recovery handoff

**Updated:** 2026-11-05
**Repository:** https://github.com/Mr-Azrack/FreeCAD-Az
**Development branch:** codex/az-design-workbench
**Reviewed implementation commit:** dac67fee9cebb9cb7e342a45098fd913510f10f6 (Az Design 0.2)
**Draft PR:** https://github.com/Mr-Azrack/FreeCAD-Az/pull/1

This is a checkpoint, **not a pinned current HEAD**. Always fetch branch HEAD and inspect new commits before work. Other sessions may be pushing code simultaneously.

## Verified from repository inspection

- Az Design 0.2 extends the earlier workbench with exact selectable sketch regions, live solid workflows, viewport handles, user parameters, supported Press/Pull, rollback and suppression, and native/parametric feature compatibility. Read addons/AzDesign/README.md for details.
- v0.2 package is addons/releases/AzDesign-0.2.0.zip; installer macro is addons/Install_AzDesign.FCMacro.
- addons/AzDesign/tests/validation-v02-linux.json records 26 passing modeling tests, four installer tests, passed v0.2 GUI and previous native/navigation checks, and manual viewport-drag observations. These are **recorded prior results**, not tests rerun by this handoff session.
- Environment of recorded validation: Linux, FreeCAD 1.0.0, Qt5/PySide2. Windows/macOS/Qt6/FreeCAD 1.1 not verified.
- While preparing this protocol, the active branch advanced from ab4a2ab3 to dac67fee. The continuity files were committed on top of that newer implementation rather than clobbering it.
- This checkpoint only adds documentation. CAD code functionality was not modified by the continuity commits.

## Immediate actions

1. Fetch current branch and verify HEAD, PR status, check runs, changed paths, and any uncommitted edits. Inspect new changes since the baseline above.
2. Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md, and the latest addons/AzDesign/README.md.
3. Run Windows shop-machine installation and a representative fabrication workflow; log exact versions and results. Be mindful v0.2 custom features require Az installed to recompute.
4. Select next Stage 1 usability gap based on actual Windows modeling experience; define an acceptance test, implement in small commits, test, and advance the draft PR.
5. Update the continuity docs with actual results and a specific next action before leaving the session.

## Timeout/crash/compaction recovery checklist

- **Never trust a recovered Work session's recollection as authoritative.**
- When local git exists: inspect git remote -v; git branch --show-current; git rev-parse HEAD; git status --short; git log -5 --oneline; git diff; git diff --cached.
- If only GitHub tools are available, inspect branch HEAD, PR, commits and files. You cannot claim a clean worktree without checking the local environment.
- Reconcile discrepancies with verified repository evidence. Preserve uncommitted changes, avoid blind resets, and do not retry a possibly completed operation without inspecting outcomes.
- Resume from the first genuinely uncompleted work item and update this handoff at the next checkpoint.

## Required end-of-session entry

Record: date/time; actual branch and HEAD; exact files/commits; tests run and results; CI/PR status; uncommitted changes; open risks; next reproducible action; any local-only artifacts or tool/environment limits.

**Rule:** Git is the authoritative memory, and this handoff points to it.
