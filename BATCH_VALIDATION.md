# Design Native — Batched Development and Validation Policy

**Effective November 10, 2026.** Owner preference: fix several related issues together, not one commit/build per bug and not an enormous untestable backlog.

## Batch size and finish line

- Keep one active modeling batch containing **3–6 related issues** or **one integrated user workflow** (e.g. select face → sketch → hole → edit feature). Pick the finish line from the actual owner part and screenshots.
- Make small, reversible Git commits *within* the batch. Individual commits are checkpoints, **not release triggers**.
- No unrelated functionality while the batch is being validated. Preserve stock FreeCAD, the current installed release, and original FCStd files.
- Before calling a batch complete, update PROJECT_STATE.md, ROADMAP.md and SESSION_HANDOFF.md with exact working/tested evidence, failures, owners' observable acceptance steps, and precise next actions.

## Three gates, with no unnecessary Windows rebuilds

1. **Fast and automatic on each feature-branch push:** `.github/workflows/az-design.yml` runs headless safety/UI contract tests, native FreeCAD geometry checks and packaging. Investigate *all* failing tests in a run together, rather than fixing just the first visible failure. Update outdated stubs and implementation contracts in the same pass.
2. **Batch candidate only:** when the related changes are ready and fast CI is green, update `.github/validation-requests/native-0.5.7.txt` on the trusted branch to the **exact candidate SHA** and brief scope. That marker triggers `.github/workflows/az-native-patch.yml` **once per candidate**. The Windows job first runs the add-on headless contract suite locally and only then downloads the pinned large installed baseline; it creates a 0.5.5→0.5.6 patch, tests actual apply, bundled Qt launch, rollback, and uninstall. A failing candidate is not released. Repair a group of issues and submit a *new* candidate marker, not a rebuild per micro-fix.
3. **Owner acceptance and official release:** on green add-on + Windows candidate checks at the same SHA, check relevant native GUI behavior with the owner's real part, then use separate controlled publisher on main with verified SHA256 artifact. Never silently promote a draft feature branch or claim installed behavior is confirmed by headless CI alone.

## Severity override

- Critical file corruption, unsafe machine-control behavior, security issues, or updater/rollback breakages get a separate urgent fix and appropriate tests. Routine GUI polish, missing buttons, or harmless label glitches wait for the current batch.
- The native full Windows installer remains manual for C++/runtime/major version changes; routine UI changes use incremental patches.

## Versioned candidate discipline

- Owner has installed the validated v0.5.6 test candidate; current correction target is **v0.5.7**, installed over 0.5.6.
- The v0.5.7 candidate marker is a guarded request to run the release validation jobs; its presence is not publication and does not change the installed app.
- Artifacts from prior SHAs (including successful Windows patch #17/#18) do not validate later source changes.
- A marker payload must identify the desired SHA and scope, so its commit is auditable. The push changes only that marker file, avoiding accidental expensive tests on every ordinary source commit.

## Current correction: 0.5.6→0.5.7

Batch includes fixing the actual native Home first-launch callback crash (InitGui loader namespace), suppressing the stock splash on subsequent native Design launches, and adding real 2×2 Sketcher circle patterns for one native four-hole operation. The Windows patch job is now preceded by the native FreeCAD geometry solver job. The installed 0.5.6 baseline is reconstructed from pinned 0.5.4 installer + 0.5.5 patch + checksum-verified successful 0.5.6 Build #20 patch, and rollback must return exactly to 0.5.6. Do not call the new version tested, installed or published until those jobs and owner acceptance have actually succeeded.
