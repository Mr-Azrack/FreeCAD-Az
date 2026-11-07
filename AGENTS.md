# FreeCAD-Az: mandatory continuity and recovery protocol

Applies to AI assistants and human contributors working in this repository. Read this file at the beginning of every new session, after context compaction, or after a Work interruption.

## Startup and recovery (before editing code)

1. Confirm the repository URL, current branch, HEAD SHA, working-tree status, and any uncommitted changes. Run git fetch when supported; do not discard local changes.
2. Read PROJECT_STATE.md, DECISIONS.md, ROADMAP.md, and SESSION_HANDOFF.md on the **actual checked-out branch**.
3. Read relevant implementation files, test results, the latest commits, and any linked pull request. Check whether documentation is stale compared with HEAD.
4. Build a verified summary: what is implemented, what was merely proposed, what tests really ran, what is uncommitted, and the next safe action.
5. After a timeout or reconnect, do not continue a remembered command blindly. Recheck branch/HEAD, diff, files, running jobs, and generated artifacts first.

## Execution rules

- Git and inspected files are the source of truth. Chat, Work, and SESSION_HANDOFF.md are helpful but can be stale.
- Never overwrite, reset, force-push, or abandon unknown changes while recovering.
- Keep substantive changes on a task/feature branch and under review. Do not silently merge to main.
- Work in independently testable increments. Commit small, coherent changes after validation, not one giant session-ending commit.
- At each meaningful milestone, update PROJECT_STATE.md (verified facts), DECISIONS.md (new accepted decisions), ROADMAP.md (scope/progress), and SESSION_HANDOFF.md (resume point) as applicable, and commit those updates.
- Before risky commands or ending a session, write a handoff containing exact branch, commit, files changed, tests/results, known problems, and the next commands/actions.
- Distinguish tests personally executed from test results recorded by an earlier session. Never claim a Windows/macOS test from Linux evidence.
- Record blockers plainly, including tools and environment that were unavailable; never fabricate completion.
- Respect repository licenses, FreeCAD's AI_POLICY.md, and human review of AI-assisted contributions. Use the appropriate Assisted-by trailer on AI-assisted commits.

## Product guardrails

FreeCAD-Az aims for a Fusion 360-like **CAD workflow and usability**, implemented independently on FreeCAD. Do not copy Autodesk code or branded assets. Preserve parametric modeling, native FreeCAD object semantics, and editable FCStd files. Feature parity is a destination, not an unverified current claim.

**Recovery invariant:** after any Work session dies, a fresh agent must be able to recover the current state from Git history and the four continuity files without relying on the old conversation.
