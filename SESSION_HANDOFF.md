# FreeCAD-Az — recovery handoff

**Updated:** 2026-11-05
**Repository:** https://github.com/Mr-Azrack/FreeCAD-Az
**Active implementation branch:** codex/az-design-workbench
**HEAD examined before this continuity commit:** dac67fee9cebb9cb7e342a45098fd913510f10f6
**Draft PR:** https://github.com/Mr-Azrack/FreeCAD-Az/pull/1
**Important:** The HEAD value above records the starting snapshot, not an eternal current HEAD. Always query git / GitHub again after reconnecting.

## Last completed state observed

- Version 0.1 of the Az Design workbench is present on the implementation branch, two commits ahead of main before this documentation commit.
- The implementation includes a standalone installer/release ZIP, FreeCAD-native sketch-to-solid modeling and UI changes. Full details: addons/AzDesign/README.md.
- Previous results: Linux FreeCAD 1.0.0 / Qt5 integration JSON records 30 passing checks; PR description reports more installer and packaging validation.
- This continuity/checkpoint documentation is being installed as the next separate commit; it does not modify the CAD code or provide fresh test results.
- Work branch PR #1 is draft, not merged into main.

## Immediate next safe actions

1. Fetch current branch status, changed paths, HEAD, open PR, CI, and any local uncommitted changes. Avoid resets and force pushes.
2. Review AGENTS.md, PROJECT_STATE.md, DECISIONS.md, and ROADMAP.md. Compare them to current code; correct any stale claims.
3. Verify AzDesign installation and first-part modeling on the actual Windows shop machine. Capture FreeCAD version, OS, failure logs/screenshots, and regression evidence.
4. Prioritize Stage 1 profile-region selection and the real sketch-to-solid interaction gaps; make an acceptance benchmark and implement on a dedicated reviewable feature branch or the current feature branch as appropriate.
5. For each completed milestone: run meaningful tests, commit code and affected docs, and refresh this handoff with exact tested commit and remaining work.

## Required resume protocol after Work timeout, crash, or lost context

- **Do not rely on recovered conversational memory.** Re-read repository state.
- Inspect: git remote -v; git branch --show-current; git rev-parse HEAD; git status --short; git log -5 --oneline; git diff; git diff --cached.
- If git is not available, use GitHub branch HEAD, file history, PR and workflow results; do not claim a clean working tree.
- Resolve disagreements between chat and repository in favor of verified files and commits.
- Identify work in progress, last committed checkpoint, completed tests and unresolved failures. Do not duplicate, clobber, or silently discard edits.
- Resume from the first uncompleted acceptance item, not from an imagined previous step.
- After substantive progress write: timestamp, branch and commit, files changed, tests actually run and their results, blockers, immediate next action, and any non-reproducible local state.

## Session end checklist

- [ ] Current branch and HEAD recorded.
- [ ] Code committed in reviewable increments; uncommitted changes explicitly itemized.
- [ ] Tests/evidence recorded without exaggeration.
- [ ] State/decisions/roadmap updated as needed.
- [ ] Exact next action and blockers stated.
- [ ] No secrets, local credentials, or transient machine-specific data committed.

**Operating principle:** Git is memory; the handoff is an index to that memory, not a replacement for verification.
