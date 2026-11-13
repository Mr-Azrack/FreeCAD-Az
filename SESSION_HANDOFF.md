# FreeCAD-Az — recovery handoff

**Updated:** 2026-11-06
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

## Implementation-session completion update — 2026-11-05

**Tested code:** `dac67fee9cebb9cb7e342a45098fd913510f10f6`. **Inspected docs parent:**
`f500e7271468a21ff3e7b9d3ad8a8fe1c9c400d2`. This update preserves the concurrent
continuity edits and adds fresh implementation/CI facts; query Git for the new tip.

The implementation session ran and passed 26 native tests, 27 desktop workflow
checks, 30 original modeling/navigation checks and 4 installer tests on FreeCAD
1.0/Linux/Qt5. Manual mouse dragging and cross-call Cancel passed. Native Fillet
survives upstream Az dimension edits; mixed native/Az history reopens. The checked-in
`validation-v02-linux.json` contains the evidence. Windows remains untested.

[CI run 42100114683](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42100114683)
passed package and native modeling jobs. Inherited Dependency Review is blocked by
this fork's disabled/unsupported Dependency graph; repository-wide CI is not all green.
PR #1 remains draft. No merge to main or repository setting change was performed.

Source, installer and evidence are committed; no CAD implementation changes remain
uncommitted. Local launchers, fault probes and generated example FCStd files were
transient diagnostics outside the checkout and are not needed for recovery. Next:
perform the Windows shop-part acceptance workflow listed above, record actual
versions/results, then choose the next measured usability gap. Do not duplicate the
already implemented profile selection, parameters, Q or rollback from stale notes.

## Startup failure follow-up — 0.2.1

Parent inspected before this fix: `8b27bb09993a40d4c52b64f210951cb17aee5c40`.
Owner's Windows FreeCAD v1-1 installation failed while executing InitGui.py because
`__file__` was absent. Init.py had the same bug. It was hidden by earlier manual
GUI launchers that injected a file value. Startup workbench code moved into
`azdesign/workbench.py`; both entry scripts now import normally. Added five loader
regressions to package CI. All five fail against 0.2.0 and pass against 0.2.1; the
four installer tests also pass. A full installed FreeCAD 1.0/Linux restart
automatically registered the workbench and activated its ribbon. Evidence and
platform limits are recorded in
`addons/AzDesign/tests/validation-startup-0.2.1.json`.

New installer: `addons/releases/AzDesign-0.2.1.zip`. The owner should extract it,
rerun Install_AzDesign.FCMacro and restart FreeCAD, then confirm startup and run the
Windows shop-part workflow. Do not reuse the known-broken 0.2.0 startup entry files.
The modeling engine is unchanged by this hotfix. Full Windows/1.1 modeling support
must not be inferred from the startup fix or earlier Linux results. Read current
branch HEAD and PR #1 before resuming; keep the branch under review.

### Published 0.2.1 verification checkpoint

Startup fix/source commit: `0242b3a6f7b23026a2b33e63ad6e04ac5c5763e0`.
[Add-on CI run 42162682276](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42162682276)
passed for that commit, including the new startup regressions and native modeling/
installer/package jobs. The ZIP is `addons/releases/AzDesign-0.2.1.zip`, SHA256
`c65900d15c337f619e34a8d2fb719bdd75426ad4a68b8b39f8ec9e0e2ee0bd8d`.
PR #1 remains draft and main is unchanged. The inherited Dependency Review setting
issue persists. The remaining immediate action is the owner's Windows/1.1 reinstall
and startup/modeling retest; Linux startup validation does not close that gate.

## First-document failure follow-up — 0.2.2, 2026-11-05

Inspected parent: `788e74da80a86f30a0b48747f9d2bbe52da06bd7`, branch
`codex/az-design-workbench`. The owner reported the Create Sketch None.activeView
traceback and confirmed New was a workaround. The hidden AzGeometry calculator
was incorrectly accepted as a modeling document. Updated modeling.py, features.py,
commands.py, tasks.py and parameters.py to use visible design context and preserve
the calculator lifecycle. Added test_document_context.py to package CI; bumped
package and guide/download links to 0.2.2. Init entry scripts retain the 0.2.1 fix.

Personally executed: initial 10 regressions against old code reproduced 6 failures,
3 errors and 1 pass; current 13 context tests, 5 startup, 4 installer, 26 modeling
tests and 27 installed-module desktop workflow checks pass. Cold installed startup
and manual Create Sketch through Extrude succeeded without New. Calculator uses
the native activeDocument() getter because clearing it can leave the Python
ActiveDocument attribute stale. Final code was installed/reloaded for the last
GUI suite. Platform: Linux FreeCAD 1.0/Qt5; owner Windows/1.1 retest still pending.
See validation-document-context-0.2.2.json. The 30 older v0.1 GUI checks were not
rerun for this hotfix; do not count them as fresh evidence.

At this source checkpoint, build/package integrity and publishing are next. Publish
the corrected ZIP and source on the existing feature branch with a head lease;
update PR #1 and inspect add-on CI. Do not merge main or claim repository-wide
CI success. Preserve any concurrent changes if the branch advances. Local desktop
helpers and FCStd models outside the checkout are transient test artifacts.

### Published 0.2.2 verification checkpoint

First-document fix/source commit: `b9b1c52fcaed354035fb88079df09e9caa156ff0`.
[Add-on CI run 42165160134](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42165160134)
passed both package and native modeling jobs, including all 13 context, 5 startup,
4 installer and 26 modeling regressions. The separate local GUI suite passed
27 checks; a manual first sketch/extrusion without New also passed.
The published package is `addons/releases/AzDesign-0.2.2.zip` (95,924 bytes), SHA256
`803a684579bd9dcf5aeba1081784d43a256c8948b22b1ba8017cad3796442a66`; its
remote Git blob matches the verified local artifact. The releases folder guide
now points to this package. PR #1 is updated and remains draft; main is unchanged.
The inherited Dependency Review setting issue persists. No CAD implementation
changes remain uncommitted at this checkpoint.

Next owner action: install 0.2.2 with Install_AzDesign.FCMacro, restart the Windows
FreeCAD 1.1 workstation, and try Create Sketch from the Start page without New.
Then complete the representative shop-part acceptance workflow. The New-document
workaround remains valid for an installation that has not yet been updated.
Linux evidence does not establish the Windows/1.1 acceptance gate.

## Workspace redesign checkpoint — 0.3.0, 2026-11-06

Inspected source parent: `5d9cc1056615878e320fcee107d8008ff0d1e698` on
`codex/az-design-workbench`. The owner says the existing installation works and
wants the workspace's layout/visual behavior comparable to Fusion; they expressly
permit full-fork/core work. No installed version was stated in that confirmation.

Changed ui.py/session.py for application tabs/ribbon, grouped Browser dock, compact
timeline and reversible layout. Added workspace.py (Browser, native document tabs,
canvas navigation and idle Solid radial menu), appearance.py (scoped preferences
and scene-only grid), original SVG icon sources/generator, and
tests/integration_workspace.py. commands.py routes Az Home/Fit around the grid.
Package version and download guides now target 0.3.0. No C++ core patch is needed
for this increment; the frontend remains entirely in our repo.

Personally executed and passing: 28 new workspace GUI checks, 27 existing v0.2 GUI
checks, 30 original GUI/navigation checks, 26 native modeling tests, 13 document
context tests, 5 startup tests and 4 installer tests. Installed in the native test
profile, fully quit/relaunched, observed automatic registration and a visible empty
Design. Visual QA then caught white sketch edges on the light canvas; final
edit-mode colors and light task headers were installed/reloaded and all 85 desktop
checks passed again. Manual Browser sketch edit and Finish Sketch returned to the
Solid layout correctly. Evidence: tests/validation-workspace-0.3.0.json.

Environment: Linux FreeCAD 1.0/Qt5/PySide2. Do not infer Windows/1.1/Qt6 sign-off.
Native advanced dialogs, click-to-activate idle Solid radial tools and Body-Tip
stepping are the supported behavior; full history reordering and complete Fusion
parity remain future scope. At this checkpoint, package integrity/publication/CI
are next. Keep PR #1 draft; do not merge main. Publish with a head lease and
preserve concurrent edits. Native test helpers/FCStd files outside the repo are
transient diagnostics. Next owner task after publication: install 0.3.0, review
the work area at their Windows display scale, and run a representative shop part.

Final restoration hardening: Sketcher can use its current cached edit color as
the default after a preference is removed. The cleanup now primes native sketch
color defaults before removing keys that were originally absent. Two focused
Python lifecycle regressions pass for absent/default and existing custom colors;
package CI includes them. The 85 GUI suites above preceded this deactivation-only
hardening; do not relabel it as a separate native GUI rerun.

### Published 0.3.0 verification checkpoint

Workspace source/package commit: `1d35f35398c57e89ba0c7464447c36e3f04caa2d`.
[Add-on CI run 42231553398](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42231553398)
passed package and native modeling jobs, including the new two cached-color
restoration regressions. Local desktop evidence remains the 28+27+30 checks and
installed startup/visual observations in validation-workspace-0.3.0.json; those
GUI checks are not CI checks. The report explicitly records the later Python-only
cleanup hardening. ZIP: `addons/releases/AzDesign-0.3.0.zip`, 142,854 bytes, SHA256
`ea6870ebc16d51d22a0fffde9d7be2cb4573efb6adff4e4ca58de9755e9a34b5`.
Remote blob `50e5d4564e3761253ab056087b2de53ec0b60a1d` matches the verified local
artifact. PR #1 title/body and installation guides point to 0.3.0; it remains
draft and main is unchanged. The inherited Dependency Review setting failure
remains unrelated and unresolved. Source, assets, package and evidence are
committed; no CAD implementation changes remain uncommitted.

Next: owner installs 0.3.0 through Install_AzDesign.FCMacro, restarts, selects Az
Design and reviews the workspace on Windows/1.1 at their actual display scaling.
Verify sketch readability, Browser/selection, document tabs, native task behavior,
undo/save/reopen and Native CAD restoration on a representative shop part. Use
that feedback to choose the next visual/ergonomic gap; do not mark complete Fusion
parity or Windows/Qt6 acceptance from this Linux checkpoint.

## Compatibility and grid follow-up — 0.3.1, 2026-11-06

Parent inspected: `d6d9611917a9e47745659c87fedda456cab4c5dc` on
`codex/az-design-workbench`. Owner likes the new layout, then reported Midplane
deprecation messages and `('Boolean',)`, and requested a visible Fusion-like grid.
The visual feedback is positive, not full Windows platform acceptance.

Added compat.py to use native SideType/Type2 on modern Pad/Pocket and reserve
Midplane/TwoLengths for older features. Updated both extrusion paths and native
Press/Pull classification. Reproduced the Boolean failure as KeyError in preference
restoration; native GetContents returns Boolean/Integer, not only the aliases
assumed by our stub. Also reproduced empty-group GetContents returning None.
Both are fixed, and CI covers preference and modern/legacy API contracts.

Grid now defaults on and remembers the Az setting; modeling draws 10 mm major /
2 mm minor lines, while native sketch grid follows its editing plane. Native
sketch ShowGrid is restored after edit/exit. A Coin bounds reset excludes floor
decoration from native scene bounds, including animated fitting; it creates no
saved model object. Updated sketch entry/Finish Sketch fitting accordingly.

Fresh passing checks: 3 modern/legacy property contracts, 4 appearance lifecycles,
13 document-context, 5 startup, 4 installer, 26 native modeling tests; final installed
fresh-app grid suite passed 16 checks and a 20×20×6 solid smoke check (2400 mm³).
The real native saved preference kind was Boolean and its restoration passed.
Manual inspection confirmed readable aligned sketch grid and properly framed
modeling floor. Earlier candidate passed 27+30 GUI checks, but a workspace run
stopped after 21 and the long-lived test desktop later required recovery. Do not
count it as a passing 28-check run. Final bounds correction was verified in a fresh
app using the focused native grid suite and manual checks. See
`tests/validation-compat-grid-0.3.1.json` for exact provenance.

Native evidence: Linux FreeCAD 1.0/Qt5/PySide2. FreeCAD 1.1 API checked from source
and sentinel contracts only; Windows/1.1 runtime retest remains pending. At this
checkpoint, package integrity/publication/CI are next. Keep PR #1 draft, lease the
branch head and preserve concurrent work. No merge to main is authorized here.

### Published 0.3.1 verification checkpoint

Source/package commit: `f08150dd6f1b2d13770d0d387050eef12f9b19fa`.
[Add-on CI run 42237616994](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42237616994)
passed native modeling and package jobs, including modern/legacy extrusion
contracts and native preference type regressions. ZIP: AzDesign-0.3.1.zip,
149,792 bytes, SHA256
`33d44a9fd3515506292e62ed836024232a12518511dc606e68c89966ce8f74fd`.
Remote blob `d6f4774dca28518818884935be59702799d641ea` matches local verification.
PR #1 and guides target 0.3.1; PR remains draft and main is unchanged. Inherited
Dependency Review remains a separate fork-setting failure. No implementation
changes remain uncommitted.

Next: owner updates with Install_AzDesign.FCMacro and fully restarts Windows
FreeCAD 1.1, tests a fresh extrusion in One side/Symmetric/Two sides, confirms
workspace exit without Boolean errors, and reviews default grids in modeling and
sketching. Record any remaining full traceback. Linux native checks plus modern
API contracts do not establish Windows/1.1 kernel acceptance.

## 2026-11-06 — Az Design 0.3.2 Hole stabilization handoff

Source parent inspected when starting: b481b386212c5d69521e5ed8f6c4cc7305925b9d;
work continues on codex/az-design-workbench, draft PR #1. The next agent MUST
retrieve its actual HEAD, latest Git history, tests, PR and local status instead
of treating this paragraph as current HEAD. No reset, merge or force push.

Implementation committed on branch:
- azdesign/hole_spec.py: validates dimensions/thread standard/size and forbids
  ModelThread=True; version-tolerant optional CosmeticThread property.
- azdesign/hole_operation.py: new/edit tip Hole transaction, valid shape checks,
  base-solid fallback, cancellation, accept with native objects.
- azdesign/hole.py: Az Qt Hole task for a sketch, diameter, depth/Through all,
  native cosmetic thread standard and explicit size, Show result/Show original,
  Cancel/Accept. No actual geometric helix generation.
- catalog.py, commands.py, workspace.py, ui.py, session.py: route Hole command
  and supported edit paths through Az without a native workbench jump.
- tests/test_hole_spec.py and test_hole_operation.py (7 offline tests);
  tests/test_workflow.py (two native Hole tests); CI workflow runs both.
- package.xml and __init__.py updated to 0.3.2. README and release guide
  distinguish the Actions review artifact from checked-in 0.3.1 ZIP.

Evidence: run 42248055124, on pre-version-bump Hole code, passed package and
native modeling (28 tests) on Linux FreeCAD 1.0. The earlier run 42247401143
caught FreeCAD 1.0 missing CosmeticThread; source fixed and revalidated. Build
0.3.2's own CI artifact from the newest successful Az Design workflow; do not
claim this documentation-only update reexecuted CAD tests.

Next owner Windows/FreeCAD 1.1 checklist:
1. Download AzDesign-installer 0.3.2 CI artifact from PR #1's latest passing
   Az Design add-on run; extract nested AzDesign-0.3.2.zip and run
   Install_AzDesign.FCMacro. Restart FreeCAD fully.
2. Model a block; sketch at least one circle center on its top face; finish
   sketch, invoke Hole (H), set a blind or Through all depth, Show result.
   Verify canvas and Az ribbon remain intact, model is visible and valid.
3. Show original solid then Show result; Cancel and confirm original geometry,
   history, visibility and undo. Repeat and Accept; reopen Hole from Browser
   and timeline and verify changes without switching workbenches.
4. On a fresh test body create cosmetic ISO thread with an explicit size;
   verify native Threaded=True, ModelThread=False. Do not attempt actual
   modeled threads through Az; test only with disposable documents and
   independently validated native geometry workflows.
5. Test save/reopen, Native CAD return/restoration, STEP export and reopening,
   feature-history edits, and different UI scaling. Note the exact version,
   traceback, screenshot and steps for failures.

Limitations: no Windows/1.1 or live Qt GUI acceptance was personally executed.
The geometric thread crash root cause is still unknown. Advanced Hole settings
and editing a Hole with downstream features are intentionally delegated to
Native CAD. Package CI creates an Actions artifact; as of source checkpoint,
no checked-in addons/releases/AzDesign-0.3.2.zip exists.

### Verified packaged review build — 0.3.2

[CI run 42248286120](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42248286120)
passed native modeling and installer/package jobs. Artifact
[AzDesign-installer 13519427193](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42248286120/artifacts/13519427193)
contains `AzDesign-0.3.2.zip`. Extracted inner ZIP: **160,781 bytes**,
SHA256 `23a308cbf2dc0d50396b95156851fbde115d7e15b3c25a9b792b337208130e11`.
The downloaded ZIP's CRC check passed and its packaged offline HoleSpec
(4) and HoleOperation (3) tests all passed separately on Python 3.13.
These package checks do not substitute for a Windows/FreeCAD 1.1 GUI retest.

Last document source commit before this note: a452478c2a3d19edc6f6931047be51aae684dafe.
The user's chat has also been provided the exact tested package bytes. The
conversation-file link is not a durable GitHub release; CI artifacts can expire.
The checked-in ZIP under addons/releases remains version 0.3.1.

## 2026-11-06 — 0.3.3 modeled-thread crash-lab handoff

User tested the 0.3.2 Hole UI and says it works, though still not as polished as
Fusion. User requested real modeled threads enabled so the native crash can be
reproduced and debugged. Existing 0.3.2 automated Linux success does not
establish safe native threads on Windows.

This session inspected PR #1 and all four continuity docs on branch
`codex/az-design-workbench` (starting HEAD `561aa6d3227742dc0ea6afff14cb7d4d02cb7b1c`).
Committed implementation changes in several small commits: explicit opt-in
HoleSpec, fsynced checkpoint/fault logger, instrumented HoleOperation, UI
experimental checkbox with warning, thread-size-first workflow, and disposable
M4 test macro. Installer packing now includes a top-level copy of the macro.
Added test_hole_diagnostics.py and updated spec/operation offline regressions;
package CI runs all three. package.xml/__init__.py mark 0.3.3 and documentation
includes THREAD_CRASH_LAB.md. Exact latest HEAD must be fetched before editing.

The first full 0.3.3 CI review was run
[42253489192](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42253489192).
The package job was observed successful while native modeling was still running
at this checkpoint. Verify completion and latest run before claiming success.
Do not execute a live modeled thread in CI. The last checked-in release ZIP is
0.3.1; the 0.3.3 ZIP is an Actions review artifact, not a local app rebuild.

Next reproducible owner step: install the 0.3.3 review artifact; launch a
SECOND, isolated Windows FreeCAD 1.1 process with no unsaved work, run the
root-level `Probe_Modeled_Thread.FCMacro`, and capture the last JSONL stage,
Python fault text and Windows Event Viewer exception. The input FCStd is saved
before native recomputation. To identify an OCCT C++ crash frame, follow
`THREAD_CRASH_LAB.md` for an optional ProcDump capture, avoiding public
sharing of dumps containing process memory. Only after evidence exists should
we patch FreeCAD C++ or mark geometric threads production-safe. No main merge.

### Verified 0.3.3 experimental crash-lab review artifact

[Az Design CI 42253489192](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42253489192)
passed both **package** and **native modeling** jobs on the source commit
`0d251aa10eba7ea64f16f74964e6dbbb8516668b`. The native FreeCAD 1.0
suite passed 28 modeling tests (cosmetic-thread and preview only); packaging
passed six HoleSpec, four HoleOperation and one durable-diagnostic offline test,
plus prior baseline checks. Running a real ModelThread helix is **not** part of
CI because it may crash the worker.

Download the [AzDesign-installer artifact 13521627224](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42253489192/artifacts/13521627224).
It contains `AzDesign-0.3.3.zip`: **172,372 bytes**,
SHA256 `b4a126826650fb6d9555266c1a6618406e1613f418191ce6ff1332f56b5f7fe0`.
The outer/inner ZIP CRC checks passed, and the extracted 11 dedicated offline
Hole tests passed again. `Probe_Modeled_Thread.FCMacro` is at the ZIP root
and under `AzDesign/Tools`; it was syntax-checked but **not run**.
Its SHA256 is
`af658bc61f1d3ac36a09f5dfd2fbfd4f96bea9ed0119bf30a8a29a4f8ab22e79`.

Important: Windows FreeCAD 1.1 GUI acceptance and modeled-thread crash
reproduction remain outstanding. The first real crash should be reproduced
in a separate disposable FreeCAD process, followed by log analysis.

## 2026-11-06 — 0.3.4 edit-mode bugfix handoff

Reported by owner: Az 0.3.3 interactive Hole panel successfully created real
spiral-thread geometry with no crash; no macro was run. Editing those threads
then showed many errors (error text not captured yet). Actual inspected source
confirmed two deliberate outdated rejections: `HoleTask.__init__` and
`HoleOperation.__init__` both blocked `editing.ModelThread`; UI also defaulted
experimental checkbox False and could strip modeled state on subsequent edit.

Changed in source on `codex/az-design-workbench` (draft PR #1):
- Removed outdated rejections, retained pre-existing Body Tip and source constraints.
- `HoleTask` reads `editing.ModelThread` and snapshots native input settings.
  Opening/accepting an unchanged modeled Hole does not enter a native transaction
  or recompute. Clicking Show result on unchanged settings also skips recompute.
  A modified modeled thread still prompts and goes through fsynced diagnostics.
- `HoleOperation` labels edit diagnostic scenarios separately.
- Stub tests check existing modeled Hole can enter the editor unchanged and
  that a changed preview logs before native recompute. Added FreeCAD 1.0 native
  geometry test for safe, cosmetic threaded-hole edit and cancellation rollback.
- Incremented package/add-on to 0.3.4 and documented remaining risks in READMEs.

Next: inspect latest branch SHA and new CI run. Download and verify actual
0.3.4 package from successful Actions run before releasing. Owner should back
up their FCStd, install 0.3.4, and test opening/editing modeled Hole. If errors
recur request exact first traceback or screenshot and latest experimental log.
The original 0.3.3 creation success does not prove that modeled-thread edit
itself is safe or that save/reopen works. No fork merge.

### Verified 0.3.4 editable native Hole package — 2026-11-06

**Verified CI:** [Az Design run 42271403820](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42271403820) passed both jobs. The native FreeCAD 1.0 modeling suite passed **29 tests**, including a real native threaded Hole edit, modified-depth preview and Cancel rollback test. The packaged offline HoleSpec tests (**6**), HoleOperation tests (**7**, including existing modeled-hole edit and native LinkSub Profile inputs), and durable logger test (**1**) passed, along with earlier install/workspace checks. This does **not** run helical `ModelThread=True` in FreeCAD 1.1 Windows; only the owner can validate that.

**Verified installer:** [AzDesign-installer artifact 13528953274](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42271403820/artifacts/13528953274) includes `AzDesign-0.3.4.zip`, **174,669 bytes**, SHA256 `8f7bba2e56f94446ffa427913a4951a8e92006eac49cfe84d03423e59746e6d1`.
Outer and inner ZIP CRC checks passed; both macro files and edited code were verified; the three packaged offline Hole test scripts passed when separately extracted and run.

**Specific reproduced native bug:** The first 0.3.4 CI [run 42271071660](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42271071660) failed in the newly added threaded-Hole edit test: `features.DesignError: Choose a native Hole associated with this sketch.` The native `Hole.Profile` is not always directly equal to a Sketch object. Fixed both `HoleOperation` comparison and `HoleTask` sketch selection with `hole_profile_sketch()` to resolve FreeCAD's `Profile` LinkSub representation, then reran CI successfully.

**Still pending:** User's actual Windows GUI/FreeCAD 1.1 trial of edit existing *modeled helical* threads, changing standard/size, save/reopen. If any errors persist capture first traceback, FreeCAD version and newest `AzDesign-Diagnostics` log. Do not conflate cosmetic native regression with a real modeled-helix edit stress test. PR remains draft/unmerged, checked-in release ZIP remains 0.3.1.

## 2026-11-06 — Owner confirmation: 0.3.4 modeled Hole editing

The owner installed/tested Az Design 0.3.4 after the modeled-thread editing fixes and reported **"ok that works great"**. Earlier owner testing confirmed that the Az Hole panel generated visible real helical threads on Windows without crashing. This is owner-reported GUI acceptance of the updated editing workflow, not a claim that every thread standard, size, save/reopen, downstream dependency, or native crash scenario has been tested. The 0.3.4 package/native CI checks previously passed; PR #1 remains a draft. Continue collecting exact repro cases for any remaining UX or geometry bugs.

## 2026-11-06 — 0.3.5 Hole UX iteration

Owner said no need to ask permission, prefers to break/fix incrementally.
Recovered draft PR #1 on `codex/az-design-workbench`, base head
`5f4fae1ece39ebe68459db3c5024a0338aeb5fa3`. Read AGENTS.md and all
continuity files. User-confirmed Windows 0.3.4 modeled-thread creation/edit
is the working baseline; do not regress this.

Incremental changes: new pure `hole_ui_policy.py` with auto-preview gates
and test; grouped native Hole UI, 350 ms Qt timer, editable initial source,
automatic native thread-size lookup, human standard labels, derived diameter
disabled when threaded, conditional helical danger warning, timer cleanup,
reversible temporary Hole on source changes, and headless Qt signal smoke
tests. `package.xml` and `__init__.py` now 0.3.5; docs updated.

Do not conflate package success with Windows GUI sign-off. ModelThread still
requires explicit Update preview + crash confirmation and durable stages.
Always inspect exact current branch, latest Az CI jobs, package artifact,
version, and newly pushed commits before continuing.

Follow-up: once both native/package CI pass, download the workflow artifact,
extract the inner `AzDesign-0.3.5.zip`, verify ZIP contents, CRC and offline
tests, record SHA256/bytes and artifact ID here. Keep draft PR #1 unmerged.
Owner should try standard-size selection, simple auto preview, original toggle,
switching center sketches before preview, then modeled thread edit (still
manual) on Windows. Next project slice can polish the Extrude task and timeline
without changing geometry engine unexpectedly.

### Verified 0.3.5 package and automated evidence — 2026-11-06

[Az Design CI run 42280673897](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42280673897)
passed both **package** and **native modeling** jobs. The GitHub artifact
[AzDesign-installer 13535765583](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42280673897/artifacts/13535765583)
contains `AzDesign-0.3.5.zip`: **182,196 bytes**, SHA256
`eea0c276d6bc18e2b7a1d5a215a597d714ddbfaa87df643f06cbea065369c50c`.
The outer and inner ZIP CRC checks passed. It contains installer, optional
modeled-thread probe, new `hole_ui_policy.py`, reworked task and tests.
The extracted package's **five focused Hole tests** (`test_hole_spec`,
`test_hole_operation`, `test_hole_diagnostics`, `test_hole_ui_policy`,
`test_hole_panel`) all passed independently on Python in the container.

The native geometry check is FreeCAD 1.0 Linux, not a Windows FreeCAD 1.1 GUI
validation. It does not execute unsafe modeled-thread helices. Owner Windows
acceptance is needed for the new grouped Qt task, debounced preview and
thread-size/source switching. The earlier Windows 0.3.4 modeled-thread
edit confirmation is still valuable, but should not be treated as a 0.3.5 test.

## 2026-11-07 — 0.3.6 timeline editing/deletion handoff

New user report: bottom roll-back ribbon is not Fusion-like; cannot delete a
feature and cannot truly modify one. Continued GitHub-first on draft PR #1,
branch `codex/az-design-workbench`, after reading AGENTS.md and four state
docs. Starting inspected branch HEAD was
`a4c1e7ad3baf275ec31cb8d84be4bd82667f3cd1` (0.3.5).

Code updates in small commits:
- `azdesign/history.py`: `deletion_plan` and transactional
  `delete_feature`; single deletion dependency refusal and explicit downstream
  same-Body cascade; snapshot FreeCAD object labels before removal; update
  Body Tip and AzHistoryEnd; refuse newly broken survivors, Undo available.
- `azdesign/ui.py`: visible Edit/Delete for selected bottom-strip step,
  Delete key, context actions with explicit destructive confirmation, helpful
  user errors and timeline refresh.
- `azdesign/workspace.py`: native PartDesign Pad/Pocket/Fillet editing now
  opens native tasks on Browser double-click.
- `azdesign/hole_operation.py`: older Hole editing with downstream final Tip
  restoration/recompute and invalid downstream refusal; modeled threads
  remain explicitly consented and logged.
- `tests/test_workflow.py`, `tests/test_hole_operation.py` test the new
  states. An initial native CI run 42341922863 had 31/32 geometry tests pass
  and one test error only because the test read `hole.Name` after native
  `doc.removeObject()` invalidated its Python proxy. The real deletion
  recompute succeeded; corrected test saves names before deletion. After
  correction, latest complete CI must be verified before release.
- Version incremented to 0.3.6 with README/install guidance.

Next: inspect exact HEAD, latest successful Az add-on CI and verified artifact;
run/install 0.3.6 Windows acceptance with leaf deletion/Undo, middle cascade
confirmation, earlier Hole edit, and native Pad/Pocket edits. Known limits:
arbitrary middle delete preserving later features, dependency repair and drag
reorder remain future stages. Do not merge draft PR #1 without owner sign-off.

### Verified 0.3.6 timeline Edit/Delete package — 2026-11-07

[Az Design CI run 42342092612](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42342092612)
passed **package** and **native modeling** jobs for source commit
`fd513f89e9d938171cefb645038ef5ed9efe9479`. Native FreeCAD 1.0 tests
cover transaction deletion/Undo, refusing an unsafe single deletion, explicit
later-branch deletion, and editing an earlier Hole beneath a later native Pad.
The prior run 42341922863 had a test-only error from dereferencing a deleted
FreeCAD Python object proxy after native deletion succeeded; the regression
was corrected to save object names before removal and the latest run passed.

[AzDesign-installer artifact 13562141196](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42342092612/artifacts/13562141196)
contains the tested `AzDesign-0.3.6.zip`: **186,564 bytes**, SHA256
`85a6f3ef177bbd501e689fb6683666010803b74f2196156a125cec2b7bff5297`.
Outer and inner ZIP CRC checks passed; contains the installer, native history,
Hole editing, UI changes and tests. Five focused Hole test scripts passed again
from the extracted ZIP in the working container. The latest checked-in repo
release ZIP remains 0.3.1; use the passing Actions artifact for 0.3.6.
**Windows FreeCAD 1.1 timeline GUI validation is still pending.** PR #1
remains draft and unmerged.

## 2026-11-07 — 0.3.7 in-app update bootstrap

User asks if Az can avoid recurring manual ZIP downloads. Project startup
confirmed public `Mr-Azrack/FreeCAD-Az`, draft PR #1 on branch
`codex/az-design-workbench` at `50a0433ad1fe5dd56be56a86399fdc5256a44e90`.
Read AGENTS.md and all continuity docs, inspected existing installer,
package CI and registered commands. Existing ZIP installer already preserves
previous installations as dated backups.

Implemented independent `azdesign/updater.py` with public GitHub API run
selection (completed successful Az Design PR workflow on the exact branch),
SHA-pinned raw source, Git Trees isolated addon manifest (not whole huge fork),
strict path/mode/size checks, Git blob verification and staged full download,
Python syntax checks and existing installer. `commands.py` adds checked,
confirmed updater dialog and safe progress/cancel, full restart warning;
`ui.py` adds visible ribbon/File entry; `catalog.py` adds Utilities and
Find a Tool command. Local module/version now 0.3.7. CI package runs new
`test_updater.py` with mocked successful/failed CI, corruption, cancellation,
same-version noop, symlink/path rejection and installed-backup recovery.

Owner must manually install 0.3.7 once via the zipped macro, then click
Update Az in future. Native FreeCAD UI/WIndows network fetch not tested in CI.
This is not a silent updater, does not use personal GitHub credentials, and
does not claim to hot reload Python in an open FreeCAD process.

Next: review final Az Design 0.3.7 CI run from latest source commit, verify
modeling AND package jobs. Download Actions AzDesign-installer artifact,
inspect ZIP CRC/package version/contents and rerun extracted offline updater
tests before shipping link. Record exact artifact ID and SHA256 in state and
handoff. PR #1 must remain draft/unmerged.

### Verified 0.3.7 self-updater bootstrap artifact — November 7, 2026

[Az Design add-on CI 42343163558](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42343163558)
passed both the **package** and **native modeling** jobs after the exact
Git-mode/symlink safety patch. Offline updater regressions (7) passed within
the package job along with installer and earlier CAD tests. Native FreeCAD
1.0 geometry checks pass in Linux CI; this does not verify HTTPS from the
owner's Windows FreeCAD 1.1 application.

[AzDesign-installer artifact 13562532527](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42343163558/artifacts/13562532527)
contains `AzDesign-0.3.7.zip`: **194,721 bytes**, SHA256
`3c2acf28ca11067d3cdc5ec5a8b872c9aeb176622d5563310cedafb2901776b7`.
Outer and inner ZIP integrity tests passed, packaging version is 0.3.7,
contains `Install_AzDesign.FCMacro`, `azdesign/updater.py`, existing
backup-aware installer, UI command, and updater tests. On extracted package,
seven dedicated offline test scripts passed: test_install, test_updater,
test_hole_spec, test_hole_operation, test_hole_diagnostics,
test_hole_ui_policy, test_hole_panel. Its root FreeCAD-Az repository remains
large; the updater intentionally fetches only the pinned AzDesign subtree.

**Owner action:** perform one final manual install of 0.3.7 ZIP, restart
FreeCAD; thereafter use ribbon Update Az or File → Check for updates,
confirm, and fully restart after installation. When already current, the
button should report 0.3.7 without modifying installation. For first live
acceptance, verify this no-op check, then use it to upgrade a future 0.3.8+
CI-passing build. The official ZIP under `addons/releases` is still older.
Keep draft PR #1 unmerged; do not claim an actual Windows network update was
observed.

## 2026-11-07 — Owner acceptance: 0.3.7 updater bootstrap

Following installation of Az Design 0.3.7, owner reported **"OK THAT WORKED WOOT"** in response to the instruction to run **Update Az** and verify the up-to-date result. Treat this as owner confirmation that the 0.3.7 installation and in-app check flow worked on their Windows FreeCAD machine. It does **not** validate downloading/installing a newer 0.3.8+ build yet; validate the actual upgrade path when a new tested version exists. Continue incremental break/fix workflow, PR #1 stays draft and unmerged.


## 2026-11-07 — Next Fusion-like UX priorities agreed for planning

User asks for next primary changes to close Fusion 360 layout, workflow,
look/feel gap. Inspected current `codex/az-design-workbench`, draft PR #1,
`ROADMAP.md`, `PROJECT_STATE.md`, `SESSION_HANDOFF.md`, `AGENTS.md`
and Az UI/Browser/session/catalog structure. No source-code edits or release
version bump were requested this turn.

Prioritize proposed sequence 0.3.8 timeline interaction/dependency-aware
edit (first; 0.3.6 Delete/Edit Windows acceptance still pending), 0.3.9
contextual sketch palette/constraints/dimensions, 0.4.0 consistent native
feature editing tasks, 0.4.1 in-canvas selection/manipulators, 0.4.2
body/component/Browser behavior, 0.4.3 cohesive visual/DPI polish.
Added detailed definitions and acceptance gates to ROADMAP.md. Autodesk
official documentation of Fusion timeline and Sketch Palette used only for
interaction comparison; copy no Autodesk source or branded assets.

Next change if owner says proceed: 0.3.8 first increment, verify Windows
0.3.6 timeline operations and the 0.3.7 updater's *real future upgrade* path.
Build small tests for Body Tip rollback marker and selection/active/rolled
visuals before any arbitrary reorder. Keep PR draft and preserve continuity.

## 2026-11-07 — Consolidated 0.4.0 Fusion-inspired workflow sprint

Owner explicitly requested all six previously proposed layout/workflow/look-and-feel upgrades be delivered **together**, rather than six incremental versions. Source changes committed on `codex/az-design-workbench`; PR #1 remains draft/unmerged. No main-branch modifications. User already tested 0.3.7 Update Az bootstrap.

### Implemented in one review build

- **Timeline**: native `history_position`, draggable slider that moves actual Body Tip on release, native incoming-dependency inspector, shared feature editor. Existing 0.3.6 Edit/Delete/Undo and safety checks retained. Body Tip scrub is **not** arbitrary reorder.
- **Sketch**: `SketchPalette` right dock, open only during sketch edits; native grid, snap, profile/dimension/constraint display flags enabled only when present on the installed FreeCAD ViewObject; tools for drawing, dimension, construction, projection, Finish Sketch; native Sketcher Tasks/solver still authoritative.
- **Feature editing**: new `feature_edit.edit` dispatch used by the timeline and Browser, preserving native PartDesign dialogs and existing Az Hole/Extrude panels.
- **Canvas**: contextual floating tool strip for selected sketches/faces/edges/features/bodies and native right-click selection menu; idle canvas still has existing radial tool menu. `quick_dimension` edits known native Pad/Pocket lengths, Fillet Radius, Chamfer Size and AzExtrude Length transactionally, with recompute and error checks; no modeled-thread shortcuts.
- **Browser**: nested true Body.Group order with Features/Sketches under each Body, active-body mark, separate unassigned items, suppress labels; active Body control and selection/visibility/isolate preserved.
- **Presentation**: accessible hint bar, consistent task controls and history slider styling, restored native FreeCAD layout on workbench exit.

### Scope/risk

Native FreeCAD object/geometry/kernel unchanged. We did NOT implement arbitrary drag-reorder of dependent features, implicit topological link rewriting or a custom Az task for every advanced native operation; these are unsafe to promise as completed without real dependency tests. ViewObject sketch flags vary by FreeCAD release and unsupported ones are disabled rather than impersonated. Direct in-canvas arbitrary face handle dragging is not done; native/Az Extrude and Press/Pull handle tools remain. Linux FreeCAD 1.0 CI and offline Qt/selection tests do not prove Windows FreeCAD 1.1 GUI interactions. Verify the exact 0.4.0 CI and artifact before owner upgrade, then test real update via 0.3.7 button and full restart.

### Tests/source

- New `tests/test_interaction.py` stubs selection-policy + feature edit dispatch.
- Native workflow adds history scrub/real dependency links and Quick Dimension/Undo checks.
- Existing Hole modeling/transaction, updater, workspace and installer tests remain in CI.
- `addons/AzDesign/package.xml`, `azdesign/__init__.py`, help dialog bumped to 0.4.0.
- Documentation updated for this combined build and remaining parity limitations.


### Verified consolidated 0.4.0 CI/artifact — 2026-11-07

[Az Design CI run 42344629492](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42344629492)
completed with successful **package** and **native modeling** jobs after
all 0.4.0 source changes. The earlier combined-feature run 42344565681 also
passed both jobs before the version bump. Native geometry includes history
scrubbing/dependency graph and Quick Dimension/Undo coverage. This verifies
FreeCAD 1.0 Linux native logic, not Windows FreeCAD 1.1 GUI behavior.

[AzDesign-installer artifact 13563450513](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42344629492/artifacts/13563450513)
contains `AzDesign-0.4.0.zip`: **207,456 bytes**, SHA256
`92adccffeae1e1aeccc05471a5dc3fd852af9a7a15c38462fbe44695497e84fa`.
Outer/inner ZIP CRC passed. ZIP contains the existing installer/updater,
sketch_palette, canvas_actions, quick_dimension, feature_edit and XML package;
7 offline tests extracted and rerun in the container all passed:
`test_updater.py`, `test_install.py`, `test_interaction.py`,
`test_hole_panel.py`, `test_hole_ui_policy.py`,
`test_hole_operation.py`, `test_hole_spec.py`.

**First owner test:** On installed 0.3.7 press **Update Az**. Confirm 0.4.0,
install and fully restart FreeCAD. Check that native FreeCAD is restored when
leaving workbench. Check (1) drag timeline scrub and restore latest;
(2) Sketch Palette and native solver; (3) Browser Body grouping;
(4) selected face right-click/canvas actions; (5) Quick Dimension/Undo on a
test solid, (6) existing modeled Hole edit. Do not yet claim actual Windows
acceptance of these integrated controls or an actual 0.3.7→0.4.0 HTTPS upgrade.
PR #1 remains draft/unmerged.


## 2026-11-07 — 0.4.1 owner Windows screenshot: repair nonfunctional oversized Sketch Palette

After installing/testing the consolidated 0.4.0 UI on Windows FreeCAD 1.1,
owner provided a screenshot showing the custom right palette consumed almost
the entire available screen height, pushing native Tasks and bottom history
below the visible area. The custom duplicated Rectangle/Circle/Line/Dimension
and Finish Sketch from the ribbon; light-on-light labels made some buttons
unreadable. Several checkboxes tried to write nonexistent Sketcher properties
(`SnapToGrid`, `ShowConstraints`, `ShowDimensions`, `ShowProfiles`);
they were visually inert. Owner correctly rejected the result as not
Fusion-like. We must not present these as completed working controls.

### 0.4.1 fix made on existing draft PR #1 / branch

- **Replaced**, not cosmetically tweaked, `azdesign/sketch_palette.py`.
  Removed all duplicate ribbon drawing buttons and its duplicate Finish
  Sketch; native Sketcher Tasks remains the geometry/constraint solver.
- The compact option-only palette has an explicit themed background,
  high-contrast labels/checkboxes, 215 px minimum width, 234 px inner
  maximum height and **210 px QDockWidget maximum height**; its native task
  dock uses the remaining right-side space. Bottom history dock limited to
  72 px (initial 58 px). Arrange sketch/native docks on sketch edit entry.
- Real ViewProviderSketch-backed toggles now only include **Show grid**
  (synced through Az appearance), **Auto grid spacing** (`GridAuto`),
  **Auto constraints** (`Autoconstraints`), and **Avoid redundant
  constraints** (`AvoidRedundant`). In a FreeCAD build supporting an actual
  checkable `Sketcher_Snap` QAction, **Snap while drawing** toggles that
  native action and tracks its state. Missing capabilities are hidden, not
  shown as fake disabled choices. User must test snap *while drawing new
  geometry*, not against existing lines.
- `test_sketch_palette.py` has four headless UI-wiring tests: compact
  control set, concrete provider property mutation, native checked Snap
  QAction, unsupported option hiding. Registered in CI alongside native
  modeling and prior installer/updater/Hole tests.
- Version bumped from 0.4.0 to **0.4.1**. Owner on 0.4.0 can click
  **Update Az** and restart; no new manual installer needed.

### Evidence and limitations

[CI run 42375950780](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42375950780)
passed both package and native modeling jobs. Its package job passed all
four new SketchPalette tests. The
[AzDesign-installer artifact 13575022990](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42375950780/artifacts/13575022990)
contains `AzDesign-0.4.1.zip`, 212,070 bytes, SHA256
`10bb043092f9cabb0a896a4d8e9d9ad8a076279956cdfe9f766e36e0411976e2`.
Both outer/inner ZIP CRC checks passed, `package.xml` is 0.4.1, and five
focused extracted tests were rerun successfully in the working container.

**Still pending:** actual owner Windows FreeCAD 1.1 screen-fit/theme
acceptance of 0.4.1. Mocked Qt wiring and Linux FreeCAD CI cannot certify
the user's native GUI panel sizing/color behavior or the precise native
checked Snap action. No custom Show Profiles/Dimensions controls until a
verified supported native implementation is available. Do not claim full
Fusion 360 Sketch Palette parity. Keep draft PR #1 unmerged.


## 2026-11-07 — 0.4.2 Windows report-view bugfix handoff

Owner reported: `tasks.py:509 int(QDialogButtonBox.Ok |
Cancel) TypeError: StandardButton` and FreeCAD native out-of-scope
link `'Body Sketch' ... 'Extrude'`. Read AGENTS.md, all state docs,
inspected branch/PR #1 and code. Existing head at start
`357450ec10824e3edda6fe12acb4362d7add0398` on
`codex/az-design-workbench`; draft PR remains unmerged.

Committed fixes: new `qt.standard_button_bits`; both `tasks.py` and
`hole.py` getStandardButtons; `features.py` new cross-Body global
LinkSubGlobal/LinkGlobal properties; `upgrade_extrude_links` for old
features under editing transaction in `operations.py`, aborting if
unexpected type; `test_qt_buttons.py`, updated Hole-panel mock,
`test_workflow.py` cross-Body/legacy-Undo tests; CI package job
includes Qt button tests. Version `0.4.2`; README and release notes
updated. The early package job failed only because `test_hole_panel.py`
mock Qt module omitted new helper; fixed in commit
`5c39c87b65a90402f32035c93db18258170d30d4`.
Earlier native modeling run `42377605469` passed all 39 FreeCAD tests
including new geometry and legacy migration tests. Final run
`42377682997` package passed, modeling was running at last check.

Continue: fetch both jobs and 0.4.2 artifact from final run, verify
inner ZIP/package/CRC/test files, record SHA256/artifact ID here and
update PR title/body. User has 0.4.1 and installed updater; tell them
click Update Az only once 0.4.2 CI is confirmed, restart fully,
then test (1) Extrude dialog opens without Qt TypeError and
(2) fresh Extrude from sketch inside another Body no link warning.
For previously saved 0.4.1 Extrudes, open Edit, accept valid preview,
save the FCStd file; changing link types occurs in native transaction.
No Windows execution evidence yet. Keep draft PR #1 unmerged.


### Verified 0.4.2 corrective release — 2026-11-07

**Both CI jobs passed:** [Az Design run 42377682997](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42377682997),
package and native modeling successful after the headless Hole Qt stub was
updated. Native Linux FreeCAD test suite passed 39 geometry cases, including
cross-Body Global links, source Body frame/placement tracking, migration of
legacy local Source links inside an explicit Edit, Cancel/Undo reversal, and
accepted migrated Extrude geometry. Qt5 and Qt6 dialog-button compatibility
regressions passed in package CI.

**Verified package:** [AzDesign-installer artifact 13576123483](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42377682997/artifacts/13576123483)
contains `AzDesign-0.4.2.zip` (**216,282 bytes**, SHA256
`0d2feef7a6a49d8bf94b783939e56f5a16b83f98947905ff8a9037bf12450b96`).
Outer and inner ZIP CRC passed, exact version in package.xml is 0.4.2,
the patched `qt.py`, `tasks.py`, `hole.py`, `features.py` and
`operations.py` and all tests are present; six extracted focused
Python tests reran and passed in the working container:
`test_qt_buttons.py`, `test_hole_panel.py`, `test_hole_operation.py`,
`test_updater.py`, `test_compat.py`, `test_sketch_palette.py`.

**Owner step:** installed 0.4.1 can now press **Update Az**, confirm 0.4.2,
then fully restart FreeCAD. Test creating/editing Extrude from sketch inside
another Body and check Report view for the exact two previous errors.
Previously saved legacy features are repaired on a user-initiated **Edit →
valid preview → OK**, then Save; merely opening old files is nonmutating.
Actual user Windows 1.1 GUI acceptance is **not yet observed**. Keep PR #1
draft/unmerged.


## 2026-11-07 — Video-driven 0.4.3 Extrude preview fix

An owner-uploaded 7.97-second 1896×908 Windows FreeCAD 1.1 video
(`20261107-2027-14.5165198.mp4`) showed solid Body
(Extrude007 → Hole → Extrude018/019) with `Sketch001` two profiles
flashing between visible/blank. Native Report view showed `Body:
Tip shape is empty`, old TopoShape hasher mismatch, plus invalid connected
solid status. No user text was present; interpreted as request to debug
observed 0.4.2 behavior. Do not infer unseen clicks or claim that every
geometry/hasher warning is resolved.

Read AGENTS.md and state docs on PR #1 branch
`codex/az-design-workbench` starting HEAD
`c4fae7f343758b579c92f66e11d563ef06996e89`.
Inspected tasks, operations, history, native tests and video frames.

Changes committed to development branch:
- `azdesign/operations.py`: `discard_preview` restores native initial
  Body Tip/visibility and removes temporary new Extrude objects.
- `azdesign/tasks.py`: no automatic multi-profile pick mode; overlay
  selection does not hide all Body features; timers stop while picking;
  zero regions cause a prompt but no preview; failed previews call
  `discard_preview` and leave task open. Existing edit Cancel remains native.
- `tests/test_workflow.py`: native geometry regression for disjoint
  Intersect cleanup, previous Body Tip/volume/object inventory, retry
  and discarded valid preview. An initial test used disconnected Join,
  which FreeCAD allowed without throwing; corrected to Intersect.
- `tests/test_extrude_preview_ui.py`: four stubbed UI behavior checks
  guarding the exact visibility/timer/invalid-preview failure; added to
  package CI.
- Version `0.4.3` in `package.xml`, `__init__.py`, `commands.py`
  and documentation.

CI run `42411545580`: package success; native failed one TEST
expectation (Join did not throw) not production behavior; new test corrected.
Run `42411861600`: package succeeded including new UI regressions;
native pending at last check. Before release check final result, artifact,
CRC, SHA256, extracted native version, package test reruns; then update
this handoff with exact evidence and PR #1 metadata. Do not merge.
Owner is on 0.4.2 with working Update Az. Windows acceptance should verify
multi-profile selection no longer blanks the block and invalid preview
returns original Body. Hasher mismatch may be a separate issue.


### Verified 0.4.3 release artifact (owner video regression) — November 7, 2026

[Az Design CI run 42411861600](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42411861600)
passed **both package and native modeling** jobs on the corrected
deterministic invalid-preview native regression. The package suite includes
four GUI-stub checks for preserving Body visibility, no-preview for zero
profiles, no timer racing while picking, and cleanup after failed preview.
Native FreeCAD tests cover disjoint Intersect invalid preview, returning
to original Body Tip/volume/object inventory, successful retry, discarded
valid preview and Cancel. Actual Windows 1.1 GUI acceptance still pending.

[Artifact 13590115605](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42411861600/artifacts/13590115605)
contains `AzDesign-0.4.3.zip`: **221,092 bytes** SHA256
`5f17639234f7be0035f34f3b75104f46ff1ba150a6463adf5358e6dc0cd77e0c`.
Outer and inner ZIP CRC passed, contains `Install_AzDesign.FCMacro`,
`azdesign/tasks.py`, `azdesign/operations.py`, new
`test_extrude_preview_ui.py` and `package.xml`.
Six focused extracted tests passed in local Python:
`test_extrude_preview_ui`, `test_qt_buttons`,
`test_updater`, `test_hole_panel`, `test_interaction`,
`test_hole_operation`.

Owner can upgrade installed 0.4.2 via **Update Az → 0.4.3 → full FreeCAD
restart**. Test selecting no profile, switching between two sketch regions,
choosing Pick profiles in view and attempting a nonconnecting Join: the
original block should remain visible when no valid preview exists.
`TopoShapeExpansion` hasher mismatch may require a separate follow-up if
still reported. Keep PR #1 draft and unmerged.


## 2026-11-08 — Az Design 0.5.0 fixture acceptance handoff

Owner authorized building 0.5.0 and requested execution rather than small
steps. Recovered actual development branch
`codex/az-design-workbench` at `706fb3117ca846eccef02a285fd27db7755b202d`
(0.4.3); draft PR #1; read AGENTS.md, all four continuity docs and actual
features, commands, tasks, Hole and history modules. Changes committed in
multiple small commits; no main merge.

Implementation:
1. `azdesign/operations.py` `_preflight_existing_body` and call before
   creating new Join/Cut/Intersect; refuse disconnected/non-cutting
   operations without inserting temporary real features.
2. `azdesign/sketch_rectangle.py` native constrained origin rectangle
   with editable dimensional width/height and Qt dialog.
3. `catalog.py` SKETCH CREATE button/command and `commands.py` dispatch.
4. `operations.accept` checks actual shapes and errors of affected
   downstream features after upstream edits.
5. `test_workflow.py`: native solver/editable constraints and complete
   fixture plate/pocket/holes/fillet/width change/Hole edits/Undo/Redo/
   FCStd save-reopen test; disjoint Join/Cut refusal before any doc
   mutation; upstream Az Extrude edit with later Fillet+Cancel regression.
6. `package.xml` and `__init__.py` 0.5.0; README and release notes.

CI run 42450272583 passed BOTH package and native modeling with
full fixture and no-op preflight tests. Subsequently added upstream
Extrude/Fillet edit regression, source commit
`8738fe99a17c9a16b4fd55dd880ac30fc2b2abcc`. Latest run
42450344286 had passed package, native still in-progress at writing;
CHECK IT BEFORE PUBLICATION.

Once both jobs pass:
- get AzDesign-installer artifact from 42450344286; download, extract
  AzDesign-0.5.0.zip, check outer/inner CRC, version, presence of new
  `azdesign/sketch_rectangle.py`, installer/updater and tests, run selected
  offline tests from packaged ZIP, compute inner ZIP SHA256/size.
- record evidence in state/handoff and update PR #1 metadata. PR must remain
  DRAFT, unmerged.
- user currently has Update Az from prior 0.4.x installs; instruct
  Update Az → 0.5.0 → fully restart FreeCAD. Owner Windows 1.1 screen
  acceptance and real first part remain necessary.
- don't claim complete Fusion parity or that the patch has fixed all
  previous TopoShape hasher warnings; those may be separate.


### Verified Az Design 0.5.0 installer and tests — November 8, 2026

[Az Design CI run 42450344286](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42450344286)
finished with successful **package** and **native modeling** jobs, including
the new upstream Az Extrude edit under a native Fillet with final Body Tip
restoration and Cancel rollback. The earlier core 0.5.0 run 42450272583
also passed both jobs (complete fixture, sketch dimensions, disconnected
Join/Cut preflight).

[Installer artifact 13604909908](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42450344286/artifacts/13604909908)
contains `AzDesign-0.5.0.zip` (**228,250 bytes**, SHA256
`e1aeaf4966a952fd69a98cfd417111d5d967f26295d4656c91f3d3398b700688`).
Outer and inner ZIP CRC tests passed; expected files are present:
`Install_AzDesign.FCMacro`, `package.xml` version 0.5.0,
`azdesign/sketch_rectangle.py`, `azdesign/operations.py`,
`azdesign/updater.py`, and `tests/test_workflow.py`.
Seven dedicated scripts from the extracted distribution passed in local
Python: `test_install.py`, `test_qt_buttons.py`, `test_updater.py`,
`test_extrude_preview_ui.py`, `test_hole_operation.py`,
`test_sketch_palette.py` and `test_interaction.py`.

**Owner action:** on their installed 0.4.x Az Design, choose **Update Az**,
confirm 0.5.0 after the latest passing CI run, save open documents and FULLY
restart FreeCAD. Create a *disposable* native fixture with Sized Rectangle,
Extrude, sketch pocket/cut, Hole, Fillet, edit initial rectangle dimensions,
Hole editing and Undo. Native Linux FreeCAD 1.0 CI does NOT constitute
Windows FreeCAD 1.1 GUI acceptance. Keep PR #1 draft/unmerged and inspect
any new first traceback rather than claiming this fixes every TopoShape
or historical topology naming issue.


## 2026-11-08 — Automatic Fusion-style snapping correction + core path

During 0.5.1 work owner clarified intended snap/center interaction is
**automatic on cursor** (midpoint triangle when sliding on an edge;
clicking a circular rim should directly target its center), rather than
a pop-up lookup tool.

Read repo AGENTS.md plus continuity docs and inspected actual
`codex/az-design-workbench` branch, existing PR #1. Implemented:
`edge_treatments.py`, `edge_treatments_ui.py`,
`snap_targets.py`, `snap_finder_ui.py`,
`snap_hover.py`, `snap_overlay.py`; integrated in
`catalog.py`, `commands.py`, `canvas_actions.py`,
`presspull.py`, `session.py`. New native
`tests/test_workflow.py` cases for tiny valid/invalid Fillet/Chamfer
and exact targets; `tests/test_snap_hover.py` pure inference;
`tests/test_snap_overlay.py` fake-GUI marker placement; registered in CI.
Updated test_interaction expected actions. Version files and README 0.5.1.

Initial CI `42453411665` failed only in new test assertions:
a headless edge-actions tuple and a Part.Point.X/Y attribute mismatch;
corrected. Source CI `42453824245` passed package and 51 native
modeling tests; `42454020125` both package and modeling passed after
version bump. Latest `42454414615` package passed, native still
running when this handoff was written.

Core assessment: inspected official FreeCAD/FreeCAD 1.1.0
`src/Mod/Sketcher/Gui/SnapManager.cpp/.h`. The native Sketcher
SnapManager receives the actual snapped XY before `DrawSketchHandler`;
core intervention is necessary for **rim-click to center** without
synthetic Qt events. Created opt-in source diff under
`native-core/patches/001-freecad-1.1.0-sketcher-circle-center.patch`
and `native-core/README.md`. Five hunks were reconstructed and
checked against exact FreeCAD 1.1.0 upstream file contents, matching
all old lines, hunk counts and patch output. This is source-level
review only, **NOT a compiled Windows FreeCAD build**. The stock
FreeCAD 1.1 addon Update Az cannot activate the core feature.

Next: verify final 0.5.1 CI both jobs, artifact ID, ZIP integrity,
SHA256 and extracted Python tests; update state, handoff, PR #1 as DRAFT
and send user Update Az instructions. Explain 0.5.1 auto hover cues
vs future native compiled full rim-click, no false parity claims.
Native core patch needs separate branch/build/test/installer track
and should not disrupt the current installed FreeCAD 1.1.


### Verified 0.5.1 packaged workbench and native-modeling CI — November 8, 2026

[Az Design CI run 42454414615](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42454414615)
passed BOTH **package** and **native FreeCAD modeling** jobs after adding
automatic Sketcher hover overlay regression tests.
[Artifact 13606378238](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42454414615/artifacts/13606378238)
contains `AzDesign-0.5.1.zip`, **246,212 bytes**, SHA256
`ba8c95c115750c0671fc732aeea0f0e76372f84c7f3f73188b6939ff95b3c7bd`.
Both outer/inner ZIP CRC passed, `package.xml` version is 0.5.1,
149 package items, and seven scripts rerun directly from the extracted
package all passed: `test_snap_hover.py`, `test_snap_overlay.py`,
`test_interaction.py`, `test_sketch_palette.py`,
`test_updater.py`, `test_qt_buttons.py`, `test_hole_panel.py`.

**Owner install:** click **Update Az**, choose CI-tested 0.5.1, then fully
restart FreeCAD. Observe while editing a sketch: hover a line midpoint
for triangle, circle/arc edge for center marker, no separate tool needed.
Fillet/Chamfer through Az now use isolated native kernel preflight and
transactional PartDesign features. **Windows UI rendering and actual
native click semantics remain unverified on user's machine.**

**Native-core scope:** the additional 1.1.0 `SnapManager` patch has
verified source hunk location/counts against upstream FreeCAD 1.1.0, but
has NOT been compiled, Windows tested or installed. It is not in the
0.5.1 installer. It would provide true circle-rim-click to center when
an independent native Az application is compiled and preference enabled.
No stock FreeCAD binaries were modified. Keep PR #1 draft/unmerged.


## 2026-11-08 — Standalone native Windows app build underway

Owner said "make it happen" after distinction between the Python workbench
updater and a separately compiled FreeCAD C++ application. Actual branch:
`codex/az-design-workbench`, draft PR #1; last confirmed code HEAD
`20a29e69d073d233de23ac7bca0183cba00cd53a` before continuity
docs. Read AGENTS.md and four project files at session start.

Created and committed:
- `.github/workflows/az-native-windows.yml`: GitHub Actions source
  validator + Windows 2022 FreeCAD 1.1 Pixi Release build and unsigned
  portable bundle; uploads archive only after real compile success.
- `native-core/windows/package_portable.py`: package real FreeCAD.exe
  from pinned Pixi env, native Sketcher and AzDesign Mod, full runtime,
  independent launcher/profile, manifest/checksum, no overwrite.
- `native-core/windows/test_package_portable.py`: 4 offline tests
  passing in local Python and GitHub Linux source validator.
- Existing C++ `native-core/patches/001-...patch` adjusted for upstream
  CRLF source; Linux `git apply --check` now succeeded. Windows
  `git apply --check` and apply succeeded in run 42487882179, then
  `git diff --check` erroneously failed because Git treats CR at end
  of original source line as trailing space; changed to
  `git -c core.whitespace=cr-at-eol diff --check` at commit 20a29e69.

Latest GitHub Actions native run `42488030121` should be inspected.
Windows C++ build has **not yet been confirmed**. If it fails, inspect
job steps + logs, apply minimal fix, rerun and update these docs.
Do not promise unsigned archive until actual successful native build and
verified artifact ID/SHA. If build takes too long, state honest
in-progress status and share CI run URL, not fake Windows installer.
Do not change `native-core/**` or new workflow unnecessarily while
native job runs; GitHub Actions concurrency cancels in-progress
previous runs on new native-code workflow runs.
No changes to installed Windows FreeCAD 1.1 or its user's files.


## 2026-11-09 — Windows native Qt startup QuickFix delivered

User screenshot: Windows dialog "This application failed to start
because no Qt platform plugin could be initialized." Repo recovery:
`Mr-Azrack/FreeCAD-Az`, development branch
`codex/az-design-workbench`, draft PR #1, FreeCAD 1.1.0 C++ core.

New files: `native-core/windows/qt_runtime.py`,
`smoke_qt.py`, `make_qt_fixkit.py`,
`.github/workflows/az-native-qt-repair.yml`. Modified
`package_portable.py`, `test_package_portable.py`,
`.github/workflows/az-native-windows.yml`.
Qt runtime stage now copies exact Pixi Windows platform plugin from
`lib/qt6/plugins/platforms` to `bin/platforms`, writes `bin/qt.conf`
and validates Qt, refusing a broken published build.
Repair workflow actually downloaded prior native build (artifact
13627854754), found `qwindows.dll` only at `lib/qt6/plugins/platforms`,
repaired plugin placement and launcher. Test output:
`Az Qt portable platform: windows`. CI
`42560734235` completed SUCCESS; artifact 13648924049.
Extracted user-facing ZIP:
`/mnt/data/AzDesign-Native-Qt-QuickFix.zip` verified active turn,
**411824 bytes**, SHA256
`bf85e6284b5e74b32d482645ccdc991c9d815585917981d61a4f6c5284c85095`;
inner/outer CRC verified and includes matching qwindows.dll, qt.conf,
updated launcher, README.

Owner instruction: extract directly into existing
`AzDesign-Native-1.1-Windows-x64` directory, replace Az Design.cmd,
then run the launcher. Do not put files directly under bin or overwrite
stock FreeCAD. User GUI acceptance pending. New full native Windows
workflow automatically rerun after packaging source changes; check
latest run/jobs if next user asks for full corrected preview, and only
claim success if compile+smoke+artifact passed.


## 2026-11-09 — Installed-app and patch updater source committed, CI running

Repo `Mr-Azrack/FreeCAD-Az`, branch
`codex/az-design-workbench`, PR #1 still draft/unmerged.
Owner confirmed Qt-fixed standalone FreeCAD runs and native snap works.
Screenshot showed chopped nav/history/browser labels, and owner
requested a proper Windows installer, desktop/Start Menu shortcuts,
and incremental patcher instead of downloading 1.3GB again.

Actual new source:
`native-core/windows/AzDesignLauncher.cs`, `AzUpdater.cs`,
`AzDesignNative.iss`, `create_patch.py`,
`ApplyAzPatch.ps1`, `test_create_patch.py`,
`test_apply_patch.ps1`, and new
`.github/workflows/az-native-installer.yml`. Also updated
`addons/AzDesign/azdesign/workspace.py` IconOnly/short fallbacks for
DPI-clipped QToolButtons.

CI run 42613250797 Windows delta patch suite PASSED all tests,
installer stage failed before Inno due csc resolving relative source
path as root. Fixed workflow by using absolute `Resolve-Path`
for C# source. Rerun
[42613707498](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42613707498):
patch-tests passed, C# launchers compiled, Inno Setup installed,
actual native setup wizard being compiled/compressed at writing.
Poll installer job, and if success check silent install/uninstall/Qt
acceptance and uploaded artifact ID/size/sha, then give user GitHub
artifact link and ordinary Windows installation instructions. If fails,
inspect job logs, correct narrowly, rerun. No code merge to main.

Current GUI updater manually accepts official downloaded `.azpatch`
ZIP and rollback. **Remote check/download of delta patches is not yet
implemented**; avoid claiming otherwise. Inno setup first install
will still be a large one-time download, but subsequent updates can be
small changed-file archives generated by create_patch.py.
Existing FreeCAD 1.1 and old portable folder left unchanged.


## 2026-11-09 — Installer pipeline recovery (current session)

- Reviewed native setup workflow and confirmed run 42613707498: Windows patch integration tests **passed**; installer job was **cancelled** during the Inno compiler step; no installer artifact was uploaded. Do not claim release readiness.
- Committed `5d5990a`: `.github/workflows/az-native-installer.yml` sets `cancel-in-progress: false` for this expensive setup pipeline and increases its upper timeout to 300 minutes. Other commits cannot cancel the current test build by concurrency policy.
- Committed `15947c4`: `AzDesignNative.iss` switches from slow LZMA2 solid archive to `lzma2/fast` non-solid packaging. This trades some one-time setup size for faster build and more tractable per-file extraction. File-delta patches remain independent.
- These two changes are **committed but not yet proven on a completed new installer run**. Next: inspect the latest Az Native Windows Installer Actions run and its artifact, ensure silent install/shortcut/Qt smoke/uninstall all succeed; if failed, diagnose exact step and commit targeted fix. Only then distribute checksum-verified installer.
- Unfinished: the updater still selects a local patch ZIP; safe automatic remote update index and signed/restricted release publication need implementation and end-to-end testing. Windows DPI/layout acceptance (100/125/150%) also pending. The user's confirmed native circle-center snapping must not regress.
- Preserve draft PR #1 and the separate existing stock FreeCAD install; no merge or force push.


## 2026-11-09 evening — owner Windows UI screenshot / Offset Plane

Owner confirmed native Windows installer 0.5.2 installs/starts without error and provided two screenshots: Az's Sketch ribbon/browser/history shows truncated short button captions and a large blue selected datum-plane overlay; native FreeCAD Part Design Datum Plane Parameters task is cumbersome and takes over the work area. No owner Windows acceptance of layout or plane UX yet.

Root cause inspected in `addons/AzDesign/azdesign/catalog.py`: the Offset Plane tool delegated directly to `PartDesign_Plane`, exposing FreeCAD's full attachment-mode panel. Added `addons/AzDesign/azdesign/offset_plane.py` (commit `ca0f8a2`), replaced catalog command with `Az_OffsetPlane` (`a442ec5`), and connected dispatcher/menu (`576ca43`). New modal creation UI accepts selected planar face or XY/XZ/YZ origin, signed millimeter/inch offset, creates native `PartDesign::Plane` with FlatFace MapMode + AttachmentOffset in a reversible transaction, and refuses an active sketch/task. No native kernel changes. **Not yet runtime-tested or CI-validated on Windows.** Test actual origin/facial support, editing, Undo, save/reopen and switching back to Az. Advanced Datum attachment remains through FreeCAD native tools; this doesn't replace existing datum editing yet.

Next: confirm current Actions run for the new changes, fix failures, add native-modeling tests for origin/face datum offsets and undo/save. Reproduce clipping under Windows at actual display scaling and repair history/navigation labels. Add a compact Az edit path for existing DatumPlane if owner wants one-step edits. Ensure native installer/patcher packages this code only after passing CI. Keep stock FreeCAD untouched and PR draft.


## 2026-11-09 evening — Design-only command boundary and automatic document routing

Owner directs: treat integrated FreeCAD core as implementation detail; do not expose accidental raw FreeCAD feature task panels through Design. Visible product/workbench name should be **Design**, not "Az Design". New ordinary model documents should default to Design after Home, while reopens preserve the last saved workbench and CAM/specialized modeling contexts are not hijacked.

- Catalog now classifies raw feature/task entry points (Revolve/Loft/Sweep/Shell/Mirror/Patterns/Move/Measure), excludes them from the main Solid ribbon, and restricts native commands in `commands.invoke`. Explicit Native CAD remains an escape hatch for not-yet-replaced advanced workflows. Native Sketcher drawing and file/open/save/undo primitives remain intentional (they do not expose raw PartDesign feature panels). This is **not** a claim that all advanced Design task editors have already been replaced.
- Visible workbench/menu/palette use **Design**; legacy internal Az command IDs and install paths remain to protect model compatibility.
- New `workspace_route.py` installs a lightweight document observer during GUI startup. Home remains visible until a document is created. Unsaved ordinary documents route into AzDesignWorkbench; existing FCStd documents with filenames are not overridden, relying on FreeCAD's native per-document workbench association saved by its GUI. New documents in CAM, Mesh, TechDraw and other specialized workbenches are exempt. No switch is performed if the document is inactive or a task is active.
- New package tests: `test_command_boundary.py` and `test_workspace_route.py`; both registered in `.github/workflows/az-design.yml`. Startup test expectations updated for menu rename.
- First add-on CI run 42733420327: **6 workspace-routing tests passed**, but command-boundary test found the remaining raw Revolve listing in Solid. Fixed in commit `e4eb11e`; check the next CI run. First run did not finish packaging; do not declare a passed package yet.
- Remaining: inspect all other pathways (context menus, keyboard dispatch, native edit handlers) that might still invoke unwanted raw task panels; design proper replacement panels per feature instead of silently bypassing FreeCAD's native kernel. Preserve explicit native CAD access and document interchange. Windows interactive workbench-restore and Home testing not yet verified by owner. Never promise exact last-used on unsaved workbench changes; FreeCAD persists its workbench association when saving a document.


## 2026-11-09 evening — Native update 0.5.3 handoff

User asked for one integrated update button after confirming installed native 0.5.2 works. Implemented source: `native-core/windows/AzOnlineUpdates.cs`, updated `AzUpdater.cs`, `commands.py`, Windows installer CI and `test_online_updates.cs`, plus manual publish workflow. Search commit history around `52dcf69`, `e762ad0`, `fd150ff`, `faf4e64`, `3001596`, `d16e9c5`, `8c86d26`. Verify branch HEAD because subsequent docs/edits may have advanced it.

Behavior: inside native 0.5.3, Design Update opens bundled AzUpdater.exe; online Check for Updates queries latest non-prerelease GitHub Release, selects exact source-version patch and verifies GitHub SHA256 digest before calling existing rollback-safe PowerShell process. For currently installed 0.5.2, UI still lacks these new features: first run Windows Native - Update with verified 0.5.2→0.5.3 .azpatch (manual selector), only AFTER artifact passes CI. Manual promotion workflow cannot run from draft feature branch alone because workflow_dispatch requires default-branch presence; no public release published yet.

Critical next action: fetch current run jobs and failures for Az Native Windows Installer workflow, verify `patch-tests` compiler and complete native 0.5.3 patch generation/Qt/rollback/artifact. Correct any compile or scripted build failure. Do not claim success until those gates pass; do not force-push/merge draft PR/replace stock FreeCAD. Update docs at next verified milestone.

### Additional updater safety checkpoint — November 9

Commit `417d25f` guards native patch initiation: if the currently installed Design FreeCAD.exe is running, AzUpdater presents a save/close instruction and rechecks the exact installed FreeCAD.exe path. It leaves the updater open and refuses mutation if the CAD process remains active. This avoids launching the independent patch process while an unsaved Design window is still running. Compiler-path fix commit `8eaa6d2` removed accidental duplicated path separators in patch-test CI. Verify those commits and the latest Windows CI status before announcing availability. Latest CI work is not yet verified passing; no public Release or downloadable 0.5.3 patch was confirmed in this session.


### 2026-11-09 22:57 ET — Windows patch CI diagnosis

Run 42735700610 completed: patch-tests succeeded; installer failed at actual 0.5.2→0.5.3 patch application. 44,382-byte patch included `AZ Native Version.json`, which ApplyAzPatch.ps1 correctly rejected. Cause was case-sensitive generator `EXCLUDES` containing `Az Native Version.json` rather than actual uppercase `AZ Native Version.json`. Fixed `files_in` exclusion using `rel.casefold()` and added safe_rel guard in commit `e29a928`; updated `test_create_patch.py` to use exact Windows marker casing and check rejection in `cd0ca8f`. New native installer workflow run 42752811713 was pending; do not announce update ready until patch apply, Qt startup, rollback and publication pass. Existing 0.5.2 remains unchanged.


## 2026-11-09 late — Owner confirms native 0.5.3 patch / readability regression

Owner showed AzUpdater.exe reporting `Installed version: 0.5.3` after manually extracting and applying `.azpatch`. This confirms the local version marker and native updater UI (not independently verified modeling task operations). Quick Start still had hardcoded 0.5.1; `commands.py` now reads installed native marker dynamically (commit `84a0d00`), not yet in owner's 0.5.3 patch.

Owner reported smaller/worse text controls in 0.5.3. Inspected explicit 9–11 px fonts and fixed-height ribbon/history in `ui.py`, Browser in `workspace.py`, and status/history in `session.py`. Enlarged readability and flexible ribbon page sizing (commits `09ad58f`, `3054eb6`, `f6f8c07`). The separate native Windows updater also had inherited small system fonts: enlarged window/font/button layout in `AzUpdater.cs` (commit `00dba95`). These fixes are committed on feature branch, **not yet installed or validated on owner's Windows PC**. Latest add-on CI run on preceding UI commit: 42758455235; native installer: 42758455231. Before shipping a new patch: ensure latest CI including C# updater resize passes, inspect Windows screenshot at 100/125/150 percent DPI, confirm main ribbon button names not clipped and Browser/history readable. Avoid reusing the fixed 0.5.3 version for an altered payload; version bump/compatible patch from installed 0.5.3 will be required. No full reinstall necessary.


## 2026-11-10 — 0.5.4 release handoff

Following owner's explicit “ok do that,” edited `.github/workflows/az-native-installer.yml` to target native 0.5.4 against original Windows 0.5.3 installer from successful run 42752856389, not more recent 0.5.3 rebuilt with typography. Patched archive is `AzDesignNative-0.5.3-to-0.5.4.azpatch`, with verified baseline installer SHA256, native installation, delta application, Qt smoke, rollback and fresh 0.5.4 installer. Updated `.github/workflows/az-native-publish.yml` for manual release and `test_online_updates.cs` for current baseline. Commits: `e6f949a`, `b71cdbf`, `6aa72df`, `183f67a`, `3648c5e`. Ensure latest CI tests actually pass and repair any failures. Do not publish or merge the draft PR automatically; existing 0.5.3 on owner's machine remains unchanged. The release promotion workflow only runs on default branch after explicit approval.


## 2026-11-10 — Native Windows CI patch-only optimization handoff

User explicitly asked to optimize slow Windows CI. Created `.github/workflows/az-native-patch.yml` commit `a2d342b` and restricted expensive `az-native-installer.yml` to manual workflow_dispatch commit `d1f01ef`; updated approved publisher to require successful new `Az Native Windows Patch` run commit `5f3be22`. Routine PR workflow downloads only original verified 0.5.3 installer (run 42752856389) rather than ALSO downloading compiled native 1.1 core. It creates partial `Mod/AzDesign` and updater/script overlays, compiles AzUpdater.exe with extracted bundled FreeCAD icon, hashes changed files via existing generator, tests real baseline apply, Qt smoke, rollback/uninstall, uploads small patch. This saves full installer recompaction/upload but still requires initial baseline download and install for trustworthy old hash checking. Never trigger full installer as part of normal PR merely for routine visual text updates. First patch-only Windows Actions run: https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42818046881, in progress during authoring. Inspect its jobs/logs, repair Windows-specific PowerShell or file layout failures, update state. Preserve draft PR; no default-branch merge or release publishing without approval. Existing owner-installed 0.5.3 untouched.


## 2026-11-10 morning — owner 0.5.4 update lookup and missing icons

Owner screenshot proves local Windows native updater `Installed version: 0.5.4`, with `Check for Updates` HTTP 404 from `/releases/latest`. This means no accessible public latest release (a private repo can also cause 404); the already-installed 0.5.4 is unaffected and a successful manual patch does not establish a public release. Adjusted `AzOnlineUpdates.Find` to interpret exact HTTP 404 as no public verified release, preserving all SHA256/HTTPS/selection validation for real published assets (commit `dd314b2`). Owner also highlighted bare text with missing icons on SOLID commands and canvas/history navigation. Source relied on native FreeCAD SVG/icon registrations not necessarily shipped in packaged runtime. Added locally painted geometry-based vector-like Qt icons in `ui.py` (commit `790c620`) and wired canvas/browser/history action buttons in `workspace.py` (commit `57a67f1`); these avoid absent native resource images and fallback abbreviations. Must verify Windows Qt painting, actual screenshot, icon sizes/legibility; automated tests alone do not establish visual quality. Latest native patch run for this change 42819280809 pending, add-on 42819280938 queued. Do not claim this fix installed on owner's 0.5.4; requires a new versioned patch baseline (likely 0.5.4→0.5.5). Release publication remains gated/manual on main and no draft PR merged.


## 2026-11-10 07:xx ET — new 0.5.5 patch follows owner 0.5.4 screen capture

After confirmation that owner has 0.5.4 installed and updater `/releases/latest` returned HTTP 404, corrected online check to report no accessible public verified update instead of fatal HTTP 404 (`dd314b2`). Owner also highlighted lack of toolbar icons (plain names) across main SOLID ribbon, navigation strip, history. Added generated Qt icons independent of native FreeCAD SVG resources in `ui.py` (`790c620`) and `workspace.py` (`57a67f1`). As owner has 0.5.4, immediately advanced fast Windows patch workflow to `AzDesignNative-0.5.4-to-0.5.5.azpatch` with original verified 0.5.4 full Windows setup from successful CI run 42809599278 pinned, hash-verified (commit `c811fda`). Updated manual full installer workflow, gated release promoter and online updater policy tests for 0.5.5 (commits `cb2ee9b`, `d6fd28b`, `14cc4a9`). Last 0.5.5 fast patch CI observed running: https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42819472920. Not yet proven green nor published; DO NOT tell user to install untested code. Auto-watch has been retargeted to 0.5.5. GitHub release publication still requires human approval and main-branch publisher; the API 404 may mean no public releases or a private repository. Do not assume missing release is resolved merely from local error handling. Need live Windows icon quality acceptance after patch.


## 2026-11-10 08:xx ET — owner-approved 0.5.5 release promotion

Owner authorized proceeding through technical steps without repeated approval. Verified fast Windows patch CI run 42819472920: patch job success and `AzDesignNative-0.5.4-to-0.5.5-PATCH` artifact present (~26 KB outer Actions archive). Repository public. To avoid merging unfinished feature PR #1, created release-only PR #2 and merged a SHA/CI-gated, manual `az-native-publish.yml` onto main (squash `6e4dba5`). Because GitHub connector lacks workflow_dispatch action, created and merged narrowly scoped one-shot push trigger PR #3 (squash `2aeb26d`) authorizing only a specific versioned release request on main. Committed `.github/release-requests/native-0.5.5.txt` to main at `43c03c1`, containing exactly `publish v0.5.5 from verified patch CI run 42819472920`. Publisher on main verifies CI workflow identity, success, branch, release not yet existing, and artifact SHA256 before `gh release create`. Independently confirmed publisher and request file both exist on main. BUT not yet confirmed GitHub Actions push-trigger run succeeded or public v0.5.5 Release published: GitHub connector only exposes PR-triggered run lookup; web/API fetch unavailable here. Environment `native-release` may require additional human review. DO NOT claim public release or online update working until separately verified via releases/latest or GitHub Actions. Existing owner 0.5.4 installation remains unchanged. Monitor and resolve any gated/publish errors using an appropriate GitHub Actions UI or Work browser; release watcher remains active.


## 2026-11-10 — user requests Design Home as native launch landing view

Owner screenshot after 0.5.5 install shows new local icons in Design ribbon, while FreeCAD's native Start page appears separately on empty launch. User wants **Design's own start screen instead of native FreeCAD Start** and better nav controls. Implemented `addons/AzDesign/azdesign/home.py` Qt widget with New/Open; `session.py` home overlay and removal of eager auto-document creation; `AzDesignLauncher.cs` sets `AZ_DESIGN_NATIVE_HOME` for no-argument launches; `InitGui.py` delayed guarded activate Design; `ui.py` and `workspace.py` more specific pan/orbit/zoom/view icons. Added widget smoke to `native-core/windows/smoke_qt.py`. Commits include `16dbb4d`, `39a8f5e`, `e6753c7`, `241c188`, `58b850a`, `46c6b88`, `4a66f30`.

Fast patch now reconstructs exact owner-installed 0.5.5 by installing verified 0.5.4 setup (run 42809599278) and applying verified 0.5.5 patch artifact (run 42819472920), then generates `AzDesignNative-0.5.5-to-0.5.6.azpatch` including new `AzDesign.exe`, updater, patch applicator, Mod/AzDesign. Clean workflow committed at `9870f42` after repairing accidental JavaScript replacement-string `$'` expansion that briefly malformed YAML in earlier commits; **always verify latest file only**. Offline metadata tests updated to 0.5.6, last commit `da4b04e`. GitHub connector commit workflow runs returned no new patch checks at time of note; cannot claim CI tested or released. Latest branch needs Windows CI run verification; do not publish on inference. User's 0.5.5 installation unchanged. Existing automated patch readiness watcher retargeted to 0.5.6. Main public release is still v0.5.5; a separately gated 0.5.6 promotion will be needed. Separate unfinished Design feature PR #1 remains unmerged.


## 2026-11-10 — live practical-part testing feedback and immediate fixes

Owner shared two screenshots and two 1918×1078 MP4 recordings. Native Preferences under Display→3D View shows camera radio circles without selected dot; native Create Sketch modal plane selection is poor; user wants click an origin plane or actual flat part face as in Fusion. Design ribbon top shortcuts are still letters. Selection action overlay Activate/Isolate blocks the cube, which lacks obvious Home. Sketcher Rectangle fails to exit on Esc after ribbon interaction, though Dimension Esc works. A long MP4 shows EXTRUDE task panel operating in Cut mode with no profile selected while a Sketch exists, blocking further commands.

Source commits on `codex/az-design-workbench`: new nonmodal `sketch_plane_picker.py` with XY/XZ/YZ actions and SelectionObserver for planar model faces (`b40ae55`), refactor `modeling.create_sketch` to call it instead of QInputDialog (`eb4df63`); canvas selection bar hidden (`b1594d6`); Escape forwards to Sketcher viewport when focus stolen and cancels plane chooser (`eaebec4`); auto-select sole valid sketch and reject Cut before first solid (`748ed6c`); native Preferences QRadioButton indicator checked style (`f6a982f`); top ribbon icon pictograms (`1a07f92`); custom cube-side Home button and teardown (`8a9056d`, `b05e1ef`); Windows CI adds Python compileall gate (`efa2cac`). These are NOT Windows-tested or released yet. Do not misstate release readiness. First clean testing action: inspect latest `Az Native Windows Patch` workflow for current SHA on PR #1; metadata lookup returned no new run IDs in previous turn. Test real 0.5.5→0.5.6 candidate, ensure source stays on designated feature branch. Check nonmodal selection observer, screenshot icon placement, native Preferences radio checks and Escape behavior under real FreeCAD 1.1 Windows.


## 2026-11-10 — real CAD part feature blockers: source work committed, testing outstanding

Owner image of Sketch001 after adding an inner rectangle on an existing Pad shows multiple crowded driving/reference dimensions (45mm, 13.5mm, 5mm, others), underconstrained 2 DoF; the actual projection button greyed out, no visible Move, Hole required manual sketch, Mirror/Pattern unavailable. Implemented in source on `codex/az-design-workbench`:
- `azdesign/move_body.py` first-pass body/component Move with XYZ and Undo, registered as Az_Move, exposed under SOLID MODIFY (commits `9165de8`, `2bdb3de`, `b26199c`, `1d75457`).
- `azdesign/feature_transform.py` Design-owned native Mirror and LinearPattern, select feature, body origin YZ/XZ/XY or X/Y/Z, one solid validation + transaction/rollback; Solid More menu and handlers (commits `b171c98`, `65d874e`, `65696c1`). Unit contract tests `test_native_transform_contracts.py` and workflow invocation (commits `f9bbf6b`, `3aa7b0d`). No real Windows modeling test yet.
- Hole from selected planar solid face creates attached Sketch 'Hole Centers', starts Circle tool, after Design Finish Sketch or native Sketch Tasks Close calls existing editable HoleTask; if no face is selected, nonmodal pick-a-face pane with Esc/cancel. Source commits `cefa581`, `24e7fc2`, `0bbdf70`, `808c46c`, `f11a1f9`, `0fa0064`. Needs actual Windows interactive acceptance.
- Native FreeCAD 1.1 source confirms `Sketcher_Projection` command (legacy `Sketcher_External` did not exist), catalog corrected commit `f6e39fe`. Selected external edge with unique planar adjacent face may establish sketch support (commit `47b6522`). In sketch mode Project produces external reference geometry; dimensions belong to sketch, not directly to raw BRep edge.
- Sketch `Show / Hide Labels` uses FreeCAD native `Sketcher_SwitchVirtualSpace` after clearing selection (commits `2723dda`, `ee7f0bb`); does not solve overlapping label layout algorithm, requires user GUI test.
- `addons/AzDesign/tests/test_command_boundary.py` now checks names and no blocked features (commit `637b358`).
Do not claim current user's installed 0.5.5 has these changes. Need verify fresh GitHub Actions run(s); connector `fetch_commit_workflow_runs` repeatedly returned no workflow runs for latest branch SHA despite commits. Investigate PR-triggered synthetic merge refs/Actions dispatch if appropriate; fix syntax/test failures. Then controlled 0.5.6 release. Keep draft PR #1 and stock FreeCAD separate.


### Latest final check — 2026-11-10 practical-part fix set

Additional source refinements: Hole-first flow now supports selecting the face *after* clicking Hole via nonmodal observer (commit f11a1f9); Escape and workspace teardown clear that observer (0fa0064); incomplete hole-center sketch state clears on workspace exit (057044a, 7036326). Native Sketcher Project now points at confirmed FreeCAD 1.1 `Sketcher_Projection` rather than stale disabled command. Pattern/Mirror have explicit allowlist tests (637b358) and native contract test registered in add-on CI (f9bbf6b, 3aa7b0d). Latest branch SHA checked: 7036326; GitHub connector reported no associated workflow runs or status contexts. All new features are source-only and not yet proven in the owner’s installed app. Do not publish 0.5.6 or say Windows-validated before CI and physical modeling tests. Once running, test face-first Hole, Sketcher projected solid edges, native mirror and linear pattern with existing pocket, Move and Undo, label toggle, real feature editing and save/reopen. Preserve .FCStd data and untouched stock FreeCAD.


## 2026-11-10 11:xx ET — Direct GitHub browser visibility restored

Owner pointed out connected Chrome GitHub Actions tab. Browser tab ID 873331943 at `https://github.com/Mr-Azrack/FreeCAD-Az/actions` exposed actual runs, proving prior `fetch_commit_workflow_runs` empty results **did not mean GitHub CI absent**. The branch push to SHA 024a339 produced **Az Native Windows Patch #17, run 42839590614, SUCCESS**, 0.5.5→0.5.6 PATCH artifact present, and **Az Design add-on #335, run 42839590701, FAILURE** in `package` job, `Test first command and hidden-document lifecycle`. Fetched failing job 129910920911 logs; specifically `test_document_context.py::test_create_sketch_with_only_hidden_calculator_opens_visible_design` imported actual `sketch_plane_picker.py` with mocked `QtWidgets` lacking QFrame because test still assumed old `QInputDialog.getItem`. This is a stale test contract after nonmodal plane chooser, **not proof of a production QFrame error**. Updated test to patch fake picker module, assert `show()` and no modal dialog, preserving visible-vs-hidden document expectations; committed SHA `5ae5a5007a3cb813b90383a81b751c1820e2ee71`. GitHub connector returned no workflow runs for that new SHA, so **this fix not yet CI verified**. Successful Windows run #17 applies only to earlier 024a339 and does not cover later Move/Mirror/Pattern/Hole code; DO NOT publish that old artifact as current release. Need check latest branch's actual Actions UI or PR workflow, confirm addon+Windows builds and address remaining test failures, then publish controlled 0.5.6 patch. Public v0.5.5 release publisher run 42821021349 was successful, consistent with owner's updater discovering 0.5.5.


## 2026-11-10 — User-directed workflow streamlining, applied

User requested middle ground between one bug/one fix and giant risky change sets. **Implemented**, not merely proposed: `.github/workflows/az-native-patch.yml` no longer triggers on ordinary `addons/AzDesign/**`/native-core push or all PRs. It runs only when `.github/validation-requests/native-0.5.6.txt` is intentionally changed on trusted `codex/az-design-workbench`, or manual dispatch. Also added preflight package contract tests on Windows ahead of the expensive 0.5.4+0.5.5 reconstructed baseline download. `.github/workflows/az-design.yml` remains fast automatic add-on/modeling CI for each ordinary source change. Root `BATCH_VALIDATION.md` establishes 3–6 related bugs or one complete owner workflow per candidate, frequent lightweight commits, grouped diagnostic review of all failures, versioned candidate validation and manual public release with real GUI owner testing. Add-on #336 failed `test_hole_panel.py` because new HoleFacePicker inherited QFrame while stub omitted it; test harness updated commit 5722293. The 0.5.6 candidate marker does not yet exist; do not create or announce release before fast CI passes. Owner's installed v0.5.5 unchanged. GitHub browser tab provides real Actions list; commit-to-runs connector lookup may be incomplete. Do not revert the deliberate batch gate simply to force a quick Windows run.


## 2026-11-10 — Owner 0.5.6 launch and four-hole pattern report

Owner supplied 20261110-1830 video: native installed 0.5.6 starts ordinary FreeCAD Part Design and Report view shows `NameError: name '_az_App' is not defined` in `InitGui.py`; owner also dislikes stock FreeCAD splash/start page. Implemented bound deferred callback references in `addons/AzDesign/InitGui.py` (commit cdddc3c), tests for cleared loader namespace and existing-doc route in `test_startup.py` (c6902cf, 55e69ce). Native-launch-only `ShowSplasher = false` preference applied to Design's own FREECAD_USER_HOME profile for next launch and callback delay reduced 1200 to 250 ms (7c34e46, 1bf376b); stock FreeCAD remains independent. Actual Windows user rerun not confirmed.

Owner also reports pattern only applied to solid features and cannot produce four hole locations in a sketch. Implemented `azdesign/sketch_pattern.py` (fb10c82) with source-circle selection/dropdown, 2×2 default row/column pitch and solver-native constraint-driven copies (Equal radius, center offsets relative to source, zero-distance alignment constraints). Wire Sketch Modify ribbon/commands (5f4d8fb, 2f18cb4). Added FreeCAD engine integration test in `test_workflow.py` (363b1ed) for pattern from one circle → 4 circles → diameter edit → native Hole removing 4 through-holes from plate; overlap/spacing rejection. New code requires successful CI + owner test; do not claim tested GUI merely from source commits.

Since 0.5.6 is already locally installed, updated `.github/workflows/az-native-patch.yml` for **0.5.6→0.5.7** (ad68421, 5cbfadd) with pinned 0.5.6 patch artifact run 42871091253, SHA256 check, reconstructed installed baseline, patch/apply/rollback/uninstall. Windows candidate is gated by Linux FreeCAD native geometry job before patch job (7d2fa3d). Trigger changed to `.github/validation-requests/native-0.5.7.txt`; NOT yet released. Need run candidate and inspect test failures as a batch, then update state; keep current 0.5.6 untouched until green and approved.


## 2026-11-10 — 0.5.7 splash fixed prelaunch, candidate must be superseded

After v0.5.7 candidate #1 was triggered, recognized native Python `InitGui` preference update only disables splash for *subsequent* launches. Owner says startup popup not needed at all, including first launch. Implemented `AzDesignLauncher.PrepareNoSplash(user.cfg)` in native C# executable (commit c2deef4): before spawning FreeCAD, ensure Design's dedicated local app profile XML `Root/BaseApp/Preferences/General/FCBool ShowSplasher=0`, preserving unrelated preferences, staged atomic file replacement + backup, idempotence; if malformed/locked, noncritical failure does not block CAD startup. Stock FreeCAD profile untouched. Added C# first-launch native profile test `native-core/windows/test_launcher_profile.cs` (335e205) and required compiler System.Xml.dll for native patch/install workflows with early validation gate (71d0178, 7967223). No actual Windows acceptance test on owner's machine yet.

**ACTION:** Supersede first 0.5.7 candidate marker with latest source SHA once all batch commits present; previous candidate does not include C# launcher fix. Run guarded geometry, headless add-on tests, Windows launcher first-run profile test, 0.5.6 baseline apply/Qt/rollback. Do not publish or advise installation of old candidate. Manual user test should be: open app no splash/stock Start; create sketch on plate face; draw one circle; Sketch → Rectangular Pattern 2×2 with X/Y pitch; Finish Sketch → Hole (through all); measure four valid holes; save/reopen. Owner already installed v0.5.6; incremental target is v0.5.7.


## 2026-11-10 — v0.5.7 GitHub workflow incident: resolved configuration, live acceptance in progress

Owner reported workflows showing errors and stuck. Browser GitHub Actions view showed #21–#35 failed instantly with no jobs. Root cause was a malformed .github/workflows/az-native-patch.yml caused by source-editing an incomplete PowerShell block; truncated SHA256 check, duplicated build steps/tail, and incorrect candidate trigger path remained. Fixed by rebuilding one contiguous 0.5.6 baseline reconstruction and patch build, requiring exactly one each of geometry, Windows patch, reconstruction and upload steps; corrected 0.5.7 marker path, System.Xml launcher compile reference, and installed baseline error wording. Commit `27569ea33f04685077d88b08d095d9883bb2e803`. Submitted 0.5.7 candidate #3 marker commit `1e9c172bb5fe1f7e38306e4238e8f7832842b10b`.

**Confirmed via GitHub API:** new [Az Native Windows Patch #36](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42899554668) was accepted and running; native FreeCAD `geometry` job completed **successfully** (including 2×2 four-hole test), Windows `patch` job running and currently installing pinned 0.5.4 baseline. At this checkpoint Windows output is NOT yet a verified patch, no 0.5.7 release published, owner's installed 0.5.6 untouched. Do not claim full release ready until Windows package/apply/rollback completes. **Process improvement:** add a lightweight actionlint/YAML structure check to fast CI in a *separate validated batch* to prevent rejected workflows. Avoid changing the running candidate SHA.

## 2026-11-10 — Fusion UX batch implemented; remaining Windows gate

After owner's full-resolution Fusion plate recording, implemented source on codex/az-design-workbench. New files: azdesign/timeline_icons.py, pattern_canvas.py, solid_pattern_engine.py, solid_pattern.py, sketch_pattern_ui.py; original SVG assets in Resources/Icons/timeline-*.svg. Updated UI and catalog/commands/feature_edit/session routing: Solid Linear Pattern on direct MODIFY toolbar; selection from canvas/Browser, Design-owned live native preview, spacing/extent, optional second grid direction, edit from timeline, Cancel/Esc transaction rollback. Sketch Rectangular Pattern on Sketch MODIFY: in-canvas panel with real solver-native live circles, X/Y drag handles, Apply/Cancel; four-hole sketch workflow feeds Hole. History feature buttons plus Edit/Delete/Resume/Settings now image icons and fixed DPI-safe sizes.

Fast tests wired: test_pattern_ui_contracts.py, test_timeline_icons.py and real native Hole→LinearPattern preview/cancel/edit in test_workflow.py. Version-robust TransformMode/Mode fixed using runtime native enum choices and Length=(count-1)*pitch. Linux Debian FreeCAD native build lacks Direction2/Occurrences2/Length2; 1D native test mandatory and two-axis assertions conditional; Windows owner's FreeCAD 1.1 must verify two-axis actually works. Latest fully verified test source b1b602ccc2884de83df6bcafc6e5646938e71fda: Az Design add-on workflow run 42928162310 (#407), package SUCCESS + modeling SUCCESS.

NEXT: Submit current complete UI batch through versioned .github/validation-requests/native-0.5.7.txt marker, inspect Windows job and artifact. Do not claim Windows GUI acceptance just because Python CI passed; user installed 0.5.6 last confirmed, keep it until patch verified. Official updater publication must be separate.

## 2026-11-10 — Fast iteration improvement after user complained about long build rotations

User requested faster development cycle. Measured completed #37 Windows candidate from GitHub Actions jobs API: Windows patch job ~8m09, old 0.5.4 installer download ~3m55, cold 0.5.4 install ~3m12; source/unit/Qt/rollback far shorter. #37 passed and has v0.5.7 candidate artifact (but remains unreleased).

Actions taken:
- .github/workflows/az-design.yml now has concurrency per branch/PR with cancel-in-progress:true; intermediate commits' obsolete tests should not queue indefinitely.
- .github/workflows/az-native-patch.yml now offers explicit manual cold_validation input, and on default batch run first restores a pinned SHA-verified installed 0.5.6 baseline from actions/cache, skipping repeated old installer and 0.5.5/0.5.6 patch reconstruction on cache hit. Cache misses/evictions fall back to pinned download+install+patch chain; a clean baseline cache is saved before applying candidate. Cache transport or quota errors are nonfatal, cache contents still must pass integrity checks. Cached run tests patch/Qt/rollback, while manual cold run tests full installer/uninstall registration.
- Structural workflow check tools/verify_native_workflows.py and fast CI step catches invalid/missing/duplicated YAML stages before Windows dispatch. One transient failure arose because old stage name contained an unquoted #20, parsed by YAML as a comment; changed stage label to 'Download pinned tested 0.5.6 patch from run 42871091253' and aligned validator. Ensure the *latest* fast CI (#412 or later) passes before the next marker request. Fast CI paths include its own verifier.
- Cache is not yet warm, and no actual cache-hit speed comparison has been run. Next batch marker will incur first cold download/installation plus cache upload; only subsequent candidates may be materially faster. Before claiming an improvement, compare cold run, cache upload size/time and subsequent cached restore duration. Respect GitHub repository cache storage quota.
- User installation remains 0.5.6 last confirmed; do not publish new version without owner GUI acceptance.

## 2026-11-10 — Correct version increment after 0.5.7 already installed

Owner reported trying a 0.5.6→0.5.7 patch while Design says installed 0.5.7; updater rejects. This is correct behavior and not a failure to override. There were two different successful 0.5.7 artifacts: original Windows candidate #36 (run 42899554668; ~333 KB) and later Fusion UI candidate #37 (run 42928685669; ~410 KB). Cannot safely install the latter over the former because both share installed version 0.5.7 and differ in file hashes. User installed 0.5.7, likely via #36 from earlier download guidance, but device provenance is unverified; Remote Desktop Commander shows laptop OFFLINE. Do not force patch, change version marker, roll back, or overwrite current installation.

Work completed in repo: native patch workflow now targets marker .github/validation-requests/native-0.5.8.txt, reconstructs pinned 0.5.6 base via verified artifacts/cache, then downloads and SHA256-validates #36 0.5.7 patch, applies it to reconstruct real 0.5.7, creates 0.5.7→0.5.8 from latest Design source, and checks apply, Qt startup, rollback to 0.5.7, and uninstall. Manual publisher updated to 0.5.8. Cheap structural validator updated to enforce the correct prior build, from/to version, checksum gate. Future marker still needs creation following fast CI green. **Critical:** target is pinned to #36's 0.5.7 file hashes; if user actually installed #37, we will need a separate #37-compatible build and explicit selection. No Windows 0.5.8 run is verified yet. Do not publish until correct baseline and GUI acceptance verified.

## 2026-11-10 — v0.5.8 officially published for the in-app Update button

Owner screenshot showed 0.5.7 Check for Updates saying "No compatible verified patch is published". Diagnosis: current installed AzOnlineUpdates.Find() only reads public https://api.github.com/repos/Mr-Azrack/FreeCAD-Az/releases/latest and selects a non-draft/non-prerelease named AzDesignNative-{installed}-to-{new}.azpatch with GitHub SHA256 asset digest. Windows CI run #39 (42949194221), source 56bfacadf8a197b49fda8e510ccc55c9fd65b3ec, had passed geometry and Windows patch tests and created 0.5.7→0.5.8 artifact but no GitHub Release; latest public release was v0.5.5.

FIX COMPLETED: On main, updated .github/workflows/az-native-publish.yml to exact-version/sha-protected 0.5.8 release. Added one-time .github/release-requests/native-0.5.8.txt marker, commit 77b5c438a6181aec42e28fea4ca658af497c039e. Publication Actions run 42952761200 succeeded. Independently fetched public GitHub releases/latest: tag v0.5.8, draft=false, prerelease=false, asset AzDesignNative-0.5.7-to-0.5.8.azpatch (406048 bytes), SHA256 digest d4a5a9244049edda3ecf1be8b43e729bcdfd520b83f9153ee898f587e7e00c78, browser URL https://github.com/Mr-Azrack/FreeCAD-Az/releases/download/v0.5.8/AzDesignNative-0.5.7-to-0.5.8.azpatch. Release page https://github.com/Mr-Azrack/FreeCAD-Az/releases/tag/v0.5.8. It should now be discoverable by the existing 0.5.7 in-app Check for Updates, WITHOUT manual ZIP handling. No local install was remotely performed. The patch is based on original 0.5.7 Build #36; if owner's installed 0.5.7 is the different Build #37, hash verification will refuse application. Never bypass it; reconstruct the appropriate installed baseline for that alternate build if necessary. Future versions MUST be unique and publisher must be updated/triggered, not just CI-built. Verify owner GUI acceptance after install.


## 2026-11-10 — Owner explicitly directed "function like Fusion", video-driven correction batch

Full owner FreeCAD 1.1.0 MP4 from zip and Fusion 360 MP4 mounted /mnt/data; reference FUSION_FREECAD_VIDEO_GAP_REVIEW.md in repo. Fusion (~3:43) completed same plate, Design (~13:06) required manual hole layout/translation, many numbered Extrude profiles, a plane popup over an existing solid, and raw FreeCAD Fillet. Implemented linked fixes (verified code commits):
- profile helper & Extrude recommended region: 826b640 and b98e205, real FreeCAD native perforated plate test beb3ace.
- Sketch plane picker hide overlay when existing model, next planar face click still observed; commit 3470710.
- Sketch Rectangular Pattern direct source selection observer while panel open, commit d68e624.
- New Design nonmodal Fillet/Chamfer pick-after-command panel, no document mutation before Apply, OCCT auto preflight, Esc/workbench cleanup, plus parametric native history editing transaction and undo; code commits ccc6d02, 8bf348a, a675456, ddbb444, 6e95143. NOT a shaded 3D preview yet.
- fast tests test_fusion_video_workflows.py + test_workflow.py actual 65x100x8 plate 8-hole perforated volume and finished Fillet radius change/Undo; test commits dd55f1a, 709e5df, CI wiring e208246, 0c8aeaa. Full Az Design CI #433 (42958378856) green for package+modeling at 709e5df; subsequent workflow-only 0.5.9-version commits pending fast CI.
- 0.5.9 native patch pipeline updated to marker native-0.5.9.txt, recovers exact 0.5.6 cache/pinned installer, applies original 0.5.7 Build #36, then checksum-verified PUBLIC 0.5.8 Build #39 patch from run 42949194221 to reconstruct installed 0.5.8 before generating candidate 0.5.8→0.5.9. Cheap YAML validator checks exact pin, from/to, rollback. Workflow version commits 639ef95, be71f93.
NEXT: confirm new fast CI green, create .github/validation-requests/native-0.5.9.txt pinned source SHA, inspect Windows 0.5.9 artifact + Qt/install/rollback, then decide release publication through updater. Owner currently testing ~0.5.8; do not reinstall or rewrite v0.5.8. Monitor actual Windows GUI edge interaction and automatic plate-hole profile behavior on same part, not just headless results. Keep Github-first durable handoff and no same-version patch rewrites.


## 2026-11-10 — v0.5.9 published for Fusion-video workflow acceptance

Verified evidence: guarded Windows candidate Build #40 (run 42959009956) completed both geometry SUCCESS and patch SUCCESS, with AzDesignNative-0.5.8-to-0.5.9-PATCH. Baseline reconstructed from hash-verified original 0.5.7 Build #36 and PUBLIC 0.5.8 Build #39. Native Windows patch install, Qt startup and rollback to 0.5.8 passed. Candidate source SHA 89cd91ba4e15381950db1543873320e90a0b80f0.

On main, v0.5.9 publishing marker committed at e72130698043e88f46717fc7416ea25439228164. Release run 42959518279 SUCCESS. Public GitHub releases/latest independently confirmed tag v0.5.9, draft=false, prerelease=false. Assets contain exact prior 0.5.7-to-0.5.8 patch plus new AzDesignNative-0.5.8-to-0.5.9.azpatch (GitHub SHA256 digest 0d87c754c04dc65f530613e3cdbc71e9d60e2926c9990770345f866adfee5cdc), with both checksum files. Release: https://github.com/Mr-Azrack/FreeCAD-Az/releases/tag/v0.5.9. Existing updater reads latest release and selects patch from current installed version: 0.5.7 can update to 0.5.8 and repeat; 0.5.8 to 0.5.9 directly.

Owner GUI still unverified: source circle picking while Sketch Pattern open; auto-selecting perforated plate region with holes; hiding large face chooser over existing body; nonmodal edge selection and Fillet edit/undo. Automated native geometry/Qt startup is not Windows UI acceptance. Fillet auto-validates the actual OCCT result but does NOT show a shaded ghost-result preview. Do not claim full Fusion behavior parity; retain rollback and unique versioning.

## 2026-11-11 — 0.5.11 Fusion workflow parity (in progress)

User authorized proceeding without routine approvals. Compare supplied Fusion 360 (3m43s) and FreeCAD (10m) recordings. Fix: body-edge reference snapping during sketch without P, streamlined sketch plane/face selection, hide incidental constraint glyphs while retaining solver, reliable pattern canvas picking, and a persistent editable pattern feature with timeline icon and double-click editing. Commits 52e1480 (selection fallback) and 506293d (generated constraint virtual space) are unvalidated. Validate native Sketcher API behavior and undo/redo; do not release until real installed baseline and Qt smoke pass. Next: implement persistent editable pattern architecture and automatic edge reference workflow; add tests. Do not confuse a geometry-copy operation with a parametric timeline feature.


## 2026-11-11 — 0.5.11 development automation checkpoint

Branch: `codex/az-design-workbench`. Source commits:
`6233bc2` (shared ambiguity-safe sketch edge resolver),
`401497f` (canvas observer uses resolver),
`30b2ee3` (regression contract).
The helper maps displayed sketch edges to underlying circle geometry by
radius/center and refuses ambiguous coincident circles. Both preselection and
live canvas selection now share the helper. No installer was published.

Tests: Added `test_sketch_circle_selection_uses_shared_geometry_resolver`
to `addons/AzDesign/tests/test_pattern_ui_contracts.py`. CI results for
the latest commit must be inspected; do not infer Windows acceptance from
a source contract. This run used GitHub file-edit tools, without a local
FreeCAD GUI or Windows installation.

**Next exact actions:** (1) inspect Actions for commit `30b2ee3`;
fix any failing job; (2) implement actual automatically projected/reference
body-edge geometry while sketch editing, ensuring read-only references do
not modify source solids; (3) design persistent editable sketch-pattern
parameters with robust undo/reopen semantics and timeline edit routing,
rather than relying on one-off generated circles; (4) add real FreeCAD
modeling tests for these features and test save/reopen and cancellation;
(5) build and validate 0.5.10 → 0.5.11 Windows patch only after all gates pass.
Do not claim 0.5.11 released yet.


## 2026-11-11 — Associative sketch edge reference implementation checkpoint

Commit 014cddade introduces `snap_targets.link_body_edge(sketch, source, edge_name)`.
This wraps native Sketcher `addExternal` in a reversible document transaction,
validates the source edge, rejects cross-document and circular dependencies,
and recomputes the sketch. It provides *associative* reference geometry rather
than the existing static projected Part.Point. **This is a backend primitive,
not yet Fusion-style automatic hover/selection integration.** No Windows GUI
validation or installer release was performed.

NEXT: wire model-edge selection while sketch editing to this backend without
disrupting native Sketcher drawing; add native geometry test verifying source
edit updates external geometry, save/reopen and undo. Then implement persistent
sketch-pattern editing with timeline icon and double-click edit, including
save/reopen and Undo/Redo tests. Inspect fast CI for 014cddade; batch Windows
0.5.10→0.5.11 patch only after full feature/tests pass.


## 2026-11-11 — Hourly development pass: native external-reference tests

Read PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and this handoff before changes.
Verified Az Design CI run 43117400436 for ce6a2c2 was SUCCESS.
Committed d147fec1 (new executable tests/test_snap_targets_contracts.py)
and 08fe43f (register the tests in az-design.yml package job).
Tests exercise native Sketcher addExternal call contract with mocked FreeCAD:
single commit, multi-edge deduplication, all-or-nothing rollback on second
edge failure, circular dependency rejection and stale-edge rejection.
No actual GUI hover behavior, save/reopen or Windows installer validation
is claimed. The new test CI outcome still needs verification.

NEXT EXACT STEPS:
1. Inspect fast CI on 08fe43f; repair failures before extending features.
2. Add real FreeCAD modeling test for native addExternal, source movement,
   persistence across FCStd save/reopen, and Undo/Redo; check actual FreeCAD
   1.1 external-reference API and dependency direction.
3. Integrate passive automatic hover/selection references while sketching
   without unintended geometry mutation or requiring P.
4. Implement persistent independently editable sketch-pattern feature and
   timeline icon/edit dispatch, retaining constrained real circle geometry,
   and test edits/cancel/reopen.
5. Only after fast and native tests pass, construct and validate the unique
   0.5.10-to-0.5.11 Windows patch, Qt startup and rollback. No release yet.


## 2026-11-11 — Development pass: associative edge-reference viewport entry

Verified fast Az Design run 43117834894 on 08fe43f SUCCESS.
Committed 3e9e469: while editing a sketch, right-clicking the viewport with
selected edges from another object now offers "Reference selected body edges".
This calls the transactional native Sketcher external-reference backend
without intercepting native Sketcher drawing clicks. Invalid/cross-document
selections do not expose the action. Committed 9e92b47 source regression
contract. This is an explicit selection action, NOT automatic hover projection,
and Windows GUI behavior has not been validated. No installer published.

NEXT: check CI for 9e92b47 and fix failures. Add real native FreeCAD 1.1
geometry save/reopen and Undo/Redo tests for external references, then
implement passive automatic model-edge midpoint/circle-center cues in the
sketch viewport without modifying source geometry. Build independent
persistent sketch-pattern parameter/history object with double-click
Design-owned editing and safe cancellation; verify generated circle
constraints, save/reopen and history undo. Only then build and test the
0.5.10-to-0.5.11 Windows patch, Qt launch and rollback.


## 2026-11-11 — 0.5.11 pattern preview geometry ownership guard

Read PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and SESSION_HANDOFF.md.
Verified latest preceding Az Design run 43128628694 SUCCESS for 9e92b47.
Committed 04011d2: SketchPatternDraft._drop_preview now checks the current
geometry count equals the original sketch geometry plus exactly the indices
generated by the panel. If the user or another command added geometry, the
panel refuses to delete unknown circles instead of silently deleting all
geometry after the original count. Committed 9984bb7 source regression
contract. **This is a data-safety improvement, not persistent sketch-pattern
history or automatic hover reference completion.** No installer published.

NEXT: verify fast CI for 9984bb7; repair failures. Strengthen preview
failure rollback for partially generated constraints/geometry and ensure
native Sketcher save/reopen and undo tests. Implement persistent independent
sketch-pattern metadata/feature and Design-owned timeline edit routing,
then automatic passive edge cues without unintended document mutation.
Validate complete native FreeCAD geometry and Windows 0.5.10→0.5.11
installed patch, Qt startup, rollback and owner GUI acceptance before
publishing. Preserve version-specific patch hash verification.


## 2026-11-11 — 0.5.11 failed Sketcher preview transaction safety

Read PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and this handoff.
Commits 812d843 and a91d2cb: SketchPatternDraft.preview now aborts the
whole open document transaction if pattern_circles raises after partially
adding Sketcher geometry/constraints; resets draft ownership and flags.
A fast source contract checks that abort and state reset remain present.
This is an atomicity fix, NOT independently editable persistent pattern
history, and NOT automatic Fusion-style body-edge projection. No Windows
patch or release was published.

NEXT EXACT STEPS:
1. Check Az Design Actions for a91d2cb and fix any failure.
2. Add executable FreeCAD native tests that deliberately reject the second
   generated circle/constraint and verify rollback restores the source sketch,
   then validate successful apply, cancel, Undo/Redo and FCStd save/reopen.
3. Build independently persisted sketch-pattern records with stable ownership
   of generated circles and constraints, edit/cancel without changing other
   sketch geometry, and route a recognizable timeline entry/double-click to
   the Design-owned edit panel. Avoid a metadata-only cosmetic timeline.
4. Implement passive, nonmutating in-sketch hover snap cues to real body
   edges/centers and associative projection on deliberate user action, without
   requiring P or interfering with Sketcher drawing.
5. After full native tests pass, validate 0.5.10→0.5.11 Windows patch install,
   Qt startup, rollback/uninstall, artifact hash/publication before release.


## 2026-11-11 — 0.5.11 independent sketch-pattern ownership groundwork

Reviewed PROJECT_STATE.md, DECISIONS.md, ROADMAP.md, AGENTS.md and this handoff.
Prior add-on CI 43142315554 passed for a91d2cb. This execution committed:
- c68a20f: SketchPatternDraft.accept records ownership inside the same native
  FreeCAD transaction as generated circles; metadata failures abort the
  transaction rather than leaving untracked geometry.
- 09e651f: new pattern_records.py stores versioned independent records as a
  sketch App::PropertyString, with source, dimensions, pitch and created
  Sketcher indices; refuses duplicate ownership and corrupt records.
- 10f82be / 5899c1b: executable pure-Python persistence, collision and
  corruption regressions, including root-run import setup.
- 91a540b: fast CI registers the new tests.

This is the first persistence layer, NOT an independently editable timeline
feature yet. Existing pattern records are not automatically migrated; editing
must validate indices and constraint ownership before deletion/replacement.
The record currently tracks generated geometry indices, NOT constraint indices,
so it is unsafe to implement deletion solely from this metadata. The record
survives FCStd serialization via native sketch property, but real native
save/reopen has not yet been exercised. No Windows patch was published.

NEXT EXACT STEPS:
1. Inspect Actions for 91a540b; repair package/modeling regressions.
2. Add native FreeCAD test for Apply/Undo/Redo and FCStd save/reopen, checking
   App::PropertyString and generated circle/constraint persistence.
3. Extend records to stable generated constraint ownership; reject stale
   indices, geometry reordering, or downstream references. Implement an
   atomic edit transaction that can rebuild only its own circles/constraints.
4. Add a Design-owned timeline entry with recognizable icon and double-click
   edit panel routing to the exact independent record. Test two patterns
   editing one without altering the other; Cancel/Undo/Redo/reopen.
5. Implement automatic passive body-edge reference cues and deliberate
   associative link without requiring P, avoiding unintended sketch mutation.
6. Validate all native FreeCAD tests and then Windows 0.5.10-to-0.5.11
   incremental patch, Qt startup, rollback/uninstall and artifact hashes.
   Publish only after all release gates pass.


## 2026-11-11 — 0.5.11 RELEASED; remaining features moved to 0.5.12

Owner approved freezing 0.5.11 scope in ROADMAP.md and deferring automatic
Fusion-style body-edge hover referencing and independently editable sketch-pattern
timeline/history to 0.5.12. Do not add those deferred features to the already
published 0.5.11 release or overwrite its immutable patch.

The 0.5.11 release gate was successfully completed in GitHub Actions run
43152125196, source ef0e32dcab3968544752c7909b57ac9e8dfa4315:
native geometry SUCCESS, Windows patch SUCCESS, installed 0.5.10 baseline
reconstructed from pinned/hash-checked patch chain, changed-only overlay,
patch apply, Qt startup, rollback and SHA256 verification SUCCESS.
The cached pinned 0.5.6 base was reused, avoiding a full installer rebuild.
The full cold uninstaller path was SKIPPED because the cached baseline was used;
do not claim cold uninstall was tested on this run.
Public GitHub release verified: https://github.com/Mr-Azrack/FreeCAD-Az/releases/tag/v0.5.11
Asset AzDesignNative-0.5.10-to-0.5.11.azpatch, 386285 bytes,
SHA256 8685ff8132b602eb37015f06f53952870a73afd5cb9733b87331db4c87c4494d.
Owner's real GUI acceptance is still pending.

NEXT: 0.5.12 development must branch/scope from immutable 0.5.11, never
modify or republish 0.5.11. First implement independent sketch-pattern
constraint ownership and safe edit/cancel/Undo/save/reopen; wire Design timeline
icon and double-click edit. Then add passive sketch body-edge/midpoint/circle
center cues and deliberate associative link without P. Test native FreeCAD
geometry and Windows patch only once the 0.5.12 feature batch is ready.


## 2026-11-12 — 0.5.12 development: constraint ownership increment

Owner confirms installed 0.5.11 works. Work remains scoped to codex/az-design-workbench; do not alter or republish 0.5.11.

Commits ea81aeb7 and 617887b add optional constraint indices to persisted sketch-pattern records, reject duplicate ownership across patterns, reject invalid/missing constraints, and add focused regression tests. Legacy records without constraints remain readable, but are NOT safe for automated edit/delete because their constraint ownership is unknown. These changes are groundwork, not a finished editable timeline feature. No local FreeCAD or Windows execution was performed in this GitHub-tool session; inspect Actions on 617887b0 before relying on tests.

NEXT EXACT ACTIONS:
1. Inspect fast add-on CI for 617887b0 and fix any failures.
2. Inspect actual SketchPatternDraft.accept and pattern_circles implementations; capture generated constraint indices from the real Sketcher API in the same transaction and pass them to append_record. Do not infer constraint ownership from geometry indices.
3. Implement fail-closed atomic per-record edit with stable geometry/constraint ownership, including shifting indices safely or rejecting unsupported dependencies; test two patterns, cancel, undo/redo and FCStd reopen with native FreeCAD.
4. Integrate each pattern record into the Design timeline with its own icon and double-click editor.
5. Add passive nonmutating body-edge/midpoint/circle-center hover cues and explicit associative link; do not interrupt native Sketcher drawing.
6. Only then run native geometry, Windows 0.5.11-to-0.5.12 patch install, Qt startup, rollback and checksum gates; publish only after all pass.


## 2026-11-12 — autonomous 0.5.12 execution: real constraint index capture

Read AGENTS.md and four continuity files from development branch. Confirmed preceding 0.5.12 commits 31c7aa2, 617887b0, ea81aeb7; commit-workflow lookup for 617887b0 returned no PR-triggered runs (this API filters to PR runs, so this is NOT proof CI failed or passed). No local working tree/FreeCAD runtime is available via GitHub file tools.

Committed da197370: SketchPatternDraft now snapshots Sketcher.ConstraintCount before preview, captures exact appended constraint index range after native pattern_circles creates three solver constraints per new circle, checks ownership counts before deleting previews or accepting, and writes both geometry and constraints into persistent pattern records within the same transaction. The existing failure path aborts the transaction. This does not yet implement editing or timeline presentation.

Committed 310ae090: updated stale fast contract that required the previous geometry-only guard, added contract for captured real Sketcher constraint indices. Do not claim these tests ran locally. Check CI and repair any failures before release.

NEXT: 1) inspect add-on Actions for 310ae090 and fix failures; 2) add executable fake/native Sketcher tests for repeated preview, generated constraints, safe cancel/accept and Undo/Redo; 3) implement independently editable per-record pattern with strict validation of generated geometry AND constraints, including protection against deletion/reindexing of other patterns; 4) route Design-owned timeline icons and double-click edit to specific pattern; 5) passive nonmutating edge/midpoint/circle cues; 6) native FCStd save/reopen and Windows 0.5.11→0.5.12 patch/Qt/rollback/checksum gates. Do not republish 0.5.11.


## 2026-11-12 — 0.5.12 autonomous pass: stable pattern identity

Read AGENTS.md and all four continuity files on codex/az-design-workbench. The preceding commits da197370/310ae090 were present in SESSION_HANDOFF.md. The GitHub commit workflow lookup for 310ae090 returned no PR-triggered runs; this is inconclusive and does not establish CI status.

Committed 50cf7027: newly created Sketch Pattern records receive stable UUID identities persisted with native sketch metadata. read_records rejects duplicate/invalid identities. find_record resolves by ID (not fragile list position) and fails closed on stale ownership. timeline_records exposes distinct per-pattern labels and editable eligibility; legacy records without IDs remain visible but noneditable. This is a data/model foundation, NOT actual timeline widget insertion or independent geometric editing. Committed 3db7b5d6: pure-Python regressions for unique identities, reorder-stable lookup, duplicate rejection, stale ownership and legacy visibility. Tests have not been executed in a local FreeCAD environment in this execution.

NEXT: 1) inspect current Actions results for 3db7b5d6 and fix any failures; 2) integrate timeline_records into workspace history UI with distinct icon and double-click targeting find_record(sketch, id); 3) implement native transactional in-place pattern editing with precise geometry and constraint ownership and safe rejection of downstream dependencies; 4) run two-pattern undo/redo and FCStd save/reopen tests under actual FreeCAD; 5) implement nonmutating sketch edge/midpoint/circle-center hover cues and deliberate associative linking; 6) validate full 0.5.11→0.5.12 Windows patch/Qt/rollback/checksums before publication. No release or Windows install changed.


## 2026-11-12 — 0.5.12 autonomous pass: guarded native pitch edit groundwork

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and SESSION_HANDOFF.md from the development branch. Owner's working 0.5.11 remains untouched. Commits:
- b91fe333: pattern_records.pitch_edit_plan resolves an individual persistent record by stable ID, validates exact constraint ownership and nonzero pitch, and plans dimension-only edits without changing geometry counts.
- a5867b41: edit_pitch validates expected Equal/DistanceX/DistanceY/Vertical/Horizontal constraint types and source/copy links, checks other circle centers for overlap, and applies only the selected pattern's driving dimensions in a native document transaction; abort/recompute on failure. Counts cannot be edited safely with this method; do not claim full pattern editing.
- 11706ee8: pure-Python regression cases for two independent patterns, pitch changes and legacy missing-constraint rejection. These were committed but not executed in a local FreeCAD runtime in this pass.

GitHub fetch_commit_workflow_runs(11706ee8) returned an empty list; this endpoint only surfaces PR-triggered runs and is inconclusive about push CI. No Windows/native geometry acceptance or release has occurred.

CRITICAL NEXT:
1. Run fast package tests and native FreeCAD tests on current branch; fix any failing test. Verify actual FreeCAD 1.1 App.Units.Quantity(value, App.Units.Length) setDatum signature and native Constraint.First/Second semantics before GUI exposing edit_pitch. Validate Undo/Redo and FCStd save/reopen with two patterns. Inspect PR Actions using a suitable endpoint; empty commit-workflow lookup is not evidence of green CI.
2. Implement Design-owned pattern edit panel for pitch, route each pattern's stable ID from an actual timeline entry and double-click, with correct icon. Current timeline_records is metadata only, not integrated.
3. Add passive nonmutating body-edge/midpoint/circle-center Sketcher viewport cues; preserve native tool mouse interactions and no implicit geometry mutation.
4. For changing counts, explicitly design safe geometry/constraint reindexing and downstream dependency handling, or reject unsupported edits.
5. Only after native geometry and full Windows 0.5.11→0.5.12 patch, Qt startup, rollback and checksum gates pass, consider release. Do not republish 0.5.11.


## 2026-11-12 — 0.5.12 autonomous pass: first real Sketch Pattern timeline entry

Inspected AGENTS.md and all four continuity files from codex/az-design-workbench. The latest handoff before this run ended at 5e592c75; GitHub commit search defaults to main and does not establish the feature branch HEAD. Used fetch_file with the explicit development ref to avoid modifying main.

Committed 066de7b2: ui.History now includes distinct SketchPatternHistoryButton icons for each persisted pattern record, with stable-ID resolution via find_record, double-click and click opening Design-owned X/Y pitch prompts, and edit_pitch as a single native transaction. The History signature includes persisted record JSON so undo/redo or edits rebuild the icons. Invalid metadata is skipped rather than breaking the whole History widget. Legacy records lacking complete constraint ownership appear disabled. No fake PartDesign solid is created; counts cannot yet be edited. Commit 28d30321 adds a headless source contract in existing test_pattern_ui_contracts.py, already included in add-on CI. These are actual source commits, not verified native GUI tests.

CI lookup for 066de7b2 returned no PR-triggered runs; that connector is insufficient to determine push Actions status. No FreeCAD runtime/Windows install was available in this tool session, so GUI behavior, Qt5/Qt6 compatibility, real save/reopen and Undo/Redo are NOT verified. Do not publish.

NEXT EXACT ACTIONS:
1. Run Python syntax/fast tests and actual FreeCAD native geometry on 28d30321; inspect push Actions via repository Actions UI/API and fix errors. Confirm command_icon("pattern") resolves a real SVG (replace with known packaged SVG if absent).
2. Verify Qt History icon refresh and click/double-click behavior, edit_pitch setDatum Quantity compatibility, and native two-pattern edit/cancel/Undo/Redo/FCStd reopen; strengthen the editor with a single nonmodal Design panel if two QInputDialogs are awkward.
3. Add safe nonmutating passive body-edge/midpoint/circle-center cues while Sketcher drawing; ensure no accidental addExternal until deliberate selection and no native event interception.
4. Investigate reindexing-safe count changes or keep count editing explicitly unsupported.
5. Validate native geometry, 0.5.11→0.5.12 Windows patch install, Qt startup, rollback and SHA256 before release. Keep v0.5.11 immutable and user's installed 0.5.11 untouched.


## 2026-11-12 — 0.5.12 autonomous pass: read-only sketch snap candidates

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and this handoff on codex/az-design-workbench. The latest prior 0.5.12 handoff described timeline icon/edit routing in 066de7b2 and 28d30321. GitHub search_commits returns default-branch commits, NOT the development branch HEAD; file fetches used explicit development ref. A local working tree and native FreeCAD runtime were not available in this GitHub-connector session. CI status remains unverified; commit-workflow lookup is PR-trigger limited.

Committed c87f48e7: snap_targets.passive_sketch_cues computes local-plane Start/End/Midpoint/Center candidates from analytic model edges without any Sketcher geometry, external reference or transaction mutation. It rejects off-plane cues, cross-document sources and circular dependencies. This is a pure candidate provider, NOT yet an actual mouse-hover overlay or live snap constraint. Committed 1bca5467: executable mock regression for planar cues, midpoint and zero document mutation. These tests were committed but not executed in this environment.

NEXT EXACT ACTIONS:
1. Run fast tests including tests/test_snap_targets_contracts.py and native geometry suite; repair any failure. Inspect push Actions via Actions UI/API rather than treating empty PR-run lookup as success.
2. Wire passive_sketch_cues to a non-intercepting Sketcher viewport preselection/hover overlay, mapping actual screen-space cursor proximity and visual indicators; preserve native Sketcher drawing and only link geometry on deliberate action.
3. Validate native FreeCAD 1.1 behavior of per-pattern pitch edit, timeline double-click and Qt refresh; test two-pattern edits, cancel, Undo/Redo and FCStd save/reopen. Correct unsafe constraint First/Second assumptions if native Sketcher uses different reference semantics.
4. Add real native save/reopen and Undo/Redo tests and investigate safe count editing or keep count edits disabled.
5. Only after passing geometry and fast CI, build hash-checked 0.5.11-to-0.5.12 Windows patch and verify Qt startup, rollback and checksums. Do not publish until gates pass; keep owner's working 0.5.11 intact.


## 2026-11-12 — 0.5.12 autonomous pass: pixel-space snap candidate resolver

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and this handoff from the explicit development branch. Prior c87f48e7 provided read-only local-plane candidates but no screen-space proximity resolver. GitHub search_commits lists default-branch commits, not the active development branch HEAD; branch-specific fetch_file used for all changes.

Commits 349db9c4 and 3e4b0562 add snap_targets.nearest_passive_cue(cues, project_to_screen, cursor, radius_px) and focused mock regression cases. The resolver filters clipped/nonfinite points, enforces pixel radius, accepts coincident cues, rejects equally near *different* positions, and never mutates Sketcher. It is a deterministic geometry-to-screen adapter, NOT a live viewport overlay or automatic constraint snap. These changes were committed via GitHub; no local Python, FreeCAD GUI or Windows test execution occurred. Push CI status remains unverified; fetch_commit_workflow_runs only reports PR-triggered runs.

NEXT EXACT ACTIONS:
1. Execute tests/test_snap_targets_contracts.py and native geometry suite; fix failures. Inspect push Actions via appropriate API/UI rather than inferring green from missing PR runs.
2. Integrate passive_sketch_cues + nearest_passive_cue with real Sketcher viewport cursor preselection/projection using non-intercepting observer/overlay. Validate FreeCAD 1.1 Qt6 pixel-coordinate conventions, visibility, screen scaling and teardown on sketch exit. No addExternal until deliberate selection.
3. Native two-pattern pitch edit with transaction/Undo/Redo, save/reopen and timeline double-click; verify constraint ownership and rejected legacy records.
4. Extend history editor to safe row/column count edits only after proving index/constraint dependency safety, otherwise keep disabled.
5. Build and validate unique 0.5.11-to-0.5.12 Windows patch after native tests, Qt startup, rollback, hashes and CI pass. Do not publish or modify 0.5.11.


## 2026-11-12 — 0.5.12 autonomous pass: fail-safe passive hover

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and this handoff on explicit codex/az-design-workbench. GitHub search_commits returned default-branch history, not development HEAD. Branch-specific file fetches verified snap_targets.py and its test contract before editing.

Commits 52e9ec5 and ba65913: passive_sketch_cues now ignores stale/unsupported hover topology instead of raising DesignError during native Sketcher drawing, and drops nonfinite/unprojectable points; nearest_passive_cue ignores transient projection failures instead of interrupting Sketcher. New tests cover invalid Edge99/Face1 hover and a viewport projection callback that raises. Both are fail-safe groundwork for live viewport integration; no native Sketcher event interception, geometry mutation, or automatic linking was introduced. GitHub commit-workflow lookup for ba65913 returned [] (PR-trigger-only API); CI is UNVERIFIED. No local FreeCAD runtime or Windows patch testing in this execution.

NEXT EXACT STEPS:
1. Run focused test_snap_targets_contracts.py plus native geometry tests in an actual Python/FreeCAD environment; fix failures. Inspect push Actions through a workflow-runs API/UI, not the PR-only commit-workflow endpoint.
2. Integrate the passive candidate provider and nearest resolver with actual Qt6 FreeCAD 1.1 Sketcher viewport hover/projection, nonintercepting native drawing; show small visible endpoint/midpoint/center indicators. Test enter/leave/edit mode cleanup and high-DPI scaling.
3. Run native two-pattern editing, constraint ownership, timeline double-click, Undo/Redo, save/reopen and stale-ownership rejection; fix errors. Keep unsupported count editing disabled.
4. Only after fast/native checks pass, validate 0.5.11→0.5.12 Windows incremental patch, Qt startup, rollback and hashes. Preserve immutable v0.5.11 and do not publish prematurely.


## 2026-11-12 — 0.5.12 viewport coordinate adapter checkpoint

Reviewed AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and current SESSION_HANDOFF.md on codex/az-design-workbench. Latest previous checkpoint was cd4b7d3. This run committed 49edd5e2 (snap_targets.viewport_passive_cue) and 2c612261 (focused adapter regressions). The new adapter transforms sketch-local candidate coordinates back through sketch.Placement into global FreeCAD vectors before viewport projection. It delegates ambiguity/radius filtering to nearest_passive_cue and never changes geometry or transactions. Tests cover offset sketch placement, correct midpoint selection, and read-only behavior. This is NOT live Qt hover drawing or automatic constraint insertion.

No local FreeCAD/Qt installation was available through the GitHub connector. No tests were executed in this run; commit-workflow lookup is PR-only and not proof of push CI. Windows 0.5.11 remains unchanged. Do not publish 0.5.12 yet.

NEXT EXACT ACTIONS:
1. Execute tests/test_snap_targets_contracts.py in actual Python, inspect push CI via Actions API/UI, and fix failures.
2. Find active Sketcher viewport event/preselection lifecycle in workspace.py/session.py and attach a nonintercepting hover indicator using viewport_passive_cue; ensure project_world uses FreeCAD 1.1 view projection with correct logical/device pixel scaling. Teardown on edit exit and workbench switch; no native drawing interference.
3. Native FreeCAD geometry validation: two independently persisted sketch patterns, pitch editing via timeline double-click, Cancel/Undo/Redo, FCStd save/reopen and stale index/constraint rejection.
4. Keep count editing disabled until safe geometry/constraint reindexing and dependency semantics are proven.
5. Only after fast/native checks pass, run 0.5.11-to-0.5.12 Windows hash-guarded patch, Qt startup, rollback and checksum verification, then consider release. Never overwrite immutable 0.5.11.


## 2026-11-12 — 0.5.12 live hover integration checkpoint

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md, SESSION_HANDOFF.md and inspected snap_targets.py, snap_overlay.py, session.py and existing tests on branch codex/az-design-workbench. GitHub search_commits lists default-branch commits, not development HEAD; branch file fetches were authoritative. No local worktree available through GitHub connector.

Commits 920bf31 and 93496c3: snap_overlay.HoverGuides.move now falls back to Gui.Selection.getPreselection when native sketch geometry produces no nearby snap. It uses viewport_passive_cue with FreeCAD world projection and Qt viewport scaling to display passive Start/End/Midpoint/Center symbols for model edges. Existing sketch cues take priority. No mouse event is consumed, no geometry/external link is inserted, and failures hide the overlay. A source contract asserts integration and absence of document mutations. This is not proof that getPreselection returns expected fields on FreeCAD 1.1 Windows, nor that all cues are visually aligned; owner GUI acceptance is pending. No test execution or release.

NEXT EXACT ACTIONS:
1. Run focused Python tests including test_snap_overlay_body_contract.py and test_snap_targets_contracts.py; register new test in CI workflow if not automatically discovered. Fix failures.
2. Verify FreeCAD 1.1 Qt6 getPreselection() shape and viewport coordinate origins with a real installed GUI. Adjust projection and DPI as necessary; test native Rectangle/Line clicks, enter/leave, edit exit and workbench deactivation.
3. Native FreeCAD tests for two independently owned sketch patterns, timeline double-click pitch edit, Cancel, Undo/Redo and FCStd save/reopen. Fix ownership corruption/stale references; keep unsupported count editing disabled.
4. Inspect push CI via actual Actions runs (PR-only commit lookup cannot establish push status). Once fast/native tests pass, run guarded unique 0.5.11→0.5.12 Windows patch, Qt smoke, rollback and SHA256 checks.
5. Never overwrite or republish 0.5.11; publish 0.5.12 only after verified gates.

## 2026-11-12 — Direct Windows 0.5.12 development test (laptop)

Connected LAPTOP-O8QBOF2P through Desktop Commander. Installed Az Design Native 0.5.11 was confirmed by AZ Native Version.json and remains unchanged at %LOCALAPPDATA%\Programs\Az Design Native; original FreeCAD process continued running. Cloned branch codex/az-design-workbench at af266d7 to %USERPROFILE%\AzDesign-Dev-0512. Created independent 8.43 GB copy at %LOCALAPPDATA%\Programs\Az Design Native 0.5.12 TEST and mirrored only development addons/AzDesign to its Mod/AzDesign. Created Az Design 0512 DEV.cmd with separate profile %LOCALAPPDATA%\AzDesign\Native-1.1-0512DEV, labeled its copied version metadata 0.5.12-dev, and created desktop shortcut AZ Design 0.5.12 DEV.lnk. Verified both FreeCAD processes running concurrently (original PID 15832, dev PID 17080). GUI launch alone does NOT establish interactive feature acceptance.

Using bundled FreeCAD 1.1 Python with PYTHONPATH including test app lib/Part/Sketcher, focused pattern tests: 20 pass after correcting the erroneous expected constraint ID 4 to 5 in test_pattern_records.py; focused snap tests: 21 pass. Full unittest discovery: 193 tests, 1 failure (disconnected Join error wording) and 1 error (legacy Source property missing after cancel), both in test_workflow.py; not resolved. Note standalone Python imported an older roaming azdesign package unless FREECAD_USER_HOME and FREECAD_USER_DATA were set to the DEV profile.

Added tests/native_0512_smoke.py, ran real FreeCAD Sketcher 2x2 circle pattern and pitch editing 10x20 to 12x24; relative spacing validated and FCStd save/reopen with persistent record passed. Unconstrained source geometry can move during solver recompute; test intentionally verifies relative spacing instead of absolute coordinates. This proves native pitch edit path but NOT UI timeline double-click, cursor snapping, undo/redo, or two independent patterns.

NEXT: user hands-on dev GUI validation of body edge/midpoint/center passive hover and timeline pitch controls; capture errors precisely. Resolve remaining native workflow suite failures, add two-pattern undo/redo native tests, and only afterward prepare signed-off guarded 0.5.11-to-0.5.12 update. Never alter user's 0.5.11 baseline. Local development test copy is experimental and NOT a released installer.

## 2026-11-12 — Native two-pattern undo/redo validation (Windows dev copy)

Recovered branch codex/az-design-workbench at 5bf4d75 on LAPTOP-O8QBOF2P; clean tracked worktree before this test. Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and handoff, inspected native pattern_records.py and prior smoke test. Added addons/AzDesign/tests/native_0512_two_patterns.py. Ran it with the bundled Windows FreeCAD 1.1 Python in the independent 0.5.12 TEST installation. PASS: two separately owned 2x2 native circle patterns, edit A without changing B, persist both stable IDs and pitch values across FCStd save/reopen, edit B after reopen, then Undo and Redo its native dimension/metadata transaction. Headless FreeCAD defaults UndoMode=0; the test explicitly enables doc.UndoMode=1 after reopen. No GUI timeline double-click or viewport hover was tested. Initial test runs identified the headless UndoMode prerequisite and the interpreter's preload of another azdesign package; test now resolves source package from its own file path. Tests were executed, not merely authored. CI and Windows patch/Qt/rollback/checksums remain unverified; no release or 0.5.11 changes.

NEXT EXACT: (1) rerun full native test_workflow.py and resolve the two known failures (disconnected Join error wording and old Source property after Cancel); (2) validate timeline pattern editor double-click and passive snap hover in real Qt FreeCAD 1.1 UI with high-DPI, enter/exit and tool click checks; (3) wire two-pattern native test into CI and check actual push Actions; (4) validate guarded 0.5.11→0.5.12 patch, Qt startup, rollback and SHA256 before release. Local run_native_0512.ps1 is untracked test launcher, not for release. Do not modify the installed 0.5.11 baseline.

## 2026-11-12 — 0.5.12 CI contract integration checkpoint

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and this handoff on the development branch. Prior Windows native two-pattern validation remains the latest recorded native evidence; it was not rerun in this execution. Connected LAPTOP-O8QBOF2P was online, but Desktop Commander command execution returned internal errors twice, so no local worktree status, FreeCAD test, or Qt inspection could be verified. The separate 0.5.11 installation was not touched.

GitHub commits bbab7b37 and ac676bff update `.github/workflows/az-design.yml` to execute the existing `test_snap_overlay_body_contract.py` on push/PR. An initially proposed timeline test filename was checked and found absent, then immediately removed before this handoff. CI outcomes are NOT verified. No release or patch was published.

NEXT EXACT ACTIONS:
1. Recover Windows remote shell, inspect dev checkout `git status`, HEAD and diff before editing. Run full native `test_workflow.py` and resolve disconnected Join wording and cancelled Source property regressions.
2. Locate actual timeline contract filename via repository tree; add it to package CI only after confirming existence. Run full CI and investigate failures.
3. Exercise FreeCAD 1.1 Qt GUI timeline double-click, body-edge midpoint/center hover, high-DPI alignment, edit exit and native drawing click-through; test independent patterns, undo/redo and save/reopen.
4. Validate guarded Windows 0.5.11-to-0.5.12 patch, Qt startup, rollback and SHA256 on disposable test copy only. Keep working 0.5.11 immutable; do not release until all gates pass.


## 2026-11-12 — 0.5.12 CI failure triage (11:18 EST)

Reviewed AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and current handoff on codex/az-design-workbench. Confirmed GitHub branch HEAD 0e3afc80 before editing. Inspected real push Actions run 43252319034: native modeling job succeeded, package job failed in tools/verify_native_workflows.py because the verifier still required the obsolete native-0.5.10.txt marker while az-native-patch.yml deliberately triggers only on native-0.5.11.txt. This is a real CI failure, not an absent PR workflow. Committed 45598e70 to align only that batch-trigger assertion, retaining the expensive Windows validation guard. No Windows/Qt test or release performed here. Package workflow may expose additional stale 0.5.10 assertions on rerun; do not claim green until checked.

NEXT EXACT STEPS:
1. Inspect new push Actions for 45598e70 and this documentation commit. If package job fails again, fetch job logs and reconcile other obsolete verifier expectations against the actual guarded az-native-patch.yml without weakening cache, rollback, or publishing gates. Confirm modeling and package both green.
2. Recover Windows dev shell, check checkout branch/HEAD/status/diff, run test_workflow.py and fix disconnected Join wording and cancelled Source regression. Preserve the independent 0.5.11 installation.
3. Verify real FreeCAD 1.1 Qt timeline double-click, passive edge/midpoint/center hover and DPI/teardown/click-through. Rerun two-pattern Undo/Redo/save/reopen and ownership rejection.
4. Only after these gates, test unique 0.5.11→0.5.12 patch on disposable Windows baseline, startup, rollback and SHA256; no release before evidence. GitHub connector cannot inspect local uncommitted Windows changes.


## 2026-11-12 — 0.5.12 CI verifier and publication safety correction (11:49 EST)

Inspected branch HEAD 4ab62d24 and current push Actions run 43257440813: modeling passed; package failed at the native workflow verifier. Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and handoff, plus actual az-native-patch.yml and verifier. The previous single-marker correction was insufficient: verifier still expected a 0.5.9→0.5.10 candidate and omitted the published 0.5.10 baseline reconstruction, while the actual Windows workflow builds a 0.5.10→0.5.11 patch. This mismatch prevented fast CI from passing.

Commits cd58e169 and 2929d2f5: added an explicit main-only condition to the native patch publication step (feature branch must never release), and updated verifier stage ordering, pinned historical artifact IDs, checksums, cache integrity, 0.5.10 reconstruction, candidate 0.5.11 patch, Qt smoke, rollback and publication guard. These are safety/CI repairs; NOT a 0.5.12 package or native geometry implementation. No tests executed locally; new push Actions must be inspected for results. No Windows baseline was modified. NOTE: the existing native patch workflow is still a historical 0.5.10→0.5.11 pipeline, NOT the requested 0.5.11→0.5.12 pipeline; do not trigger it as a 0.5.12 test or publish.

NEXT EXACT STEPS:
1. Check Actions for 2929d2f5 and this handoff. If verifier fails, inspect failed step and correct actual structure without removing checksum, cache, rollback, Qt, or main-only publication checks. Verify both fast jobs green.
2. Recover Windows dev shell; inspect checkout HEAD/status and run full test_workflow.py. Fix the disconnected Join wording and cancelled Source property failures with regression tests.
3. Exercise native FreeCAD 1.1 Qt timeline double-click and passive body-edge/midpoint/center hover, DPI, teardown, drawing click-through; rerun two-pattern ownership/Undo/Redo/FCStd save/reopen.
4. Design a NEW guarded 0.5.11→0.5.12 candidate patch workflow using immutable published 0.5.11 baseline and isolated test copy. Validate geometry, Qt startup, rollback, SHA256, and package identity before any release; keep 0.5.11 untouched. Do not enable automatic feature-branch publication.


## 2026-11-12 — Windows native regression rerun (13:24 EST)

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and the branch handoff. Connected LAPTOP-O8QBOF2P; its independent C:\\Users\\matto\\AzDesign-Dev-0512 snapshot has no .git directory, so do not mistake that snapshot for a current Git checkout. The isolated native 0.5.12 TEST FreeCAD copy remains separate from installed 0.5.11. Executed run_native_0512.ps1 with PowerShell -ExecutionPolicy Bypass (default execution policy blocked scripts): actual output `UNDO AVAILABLE 1`, `AFTER UNDO [12.0, 15.0]`, `PASS two independent patterns, save/reopen, undo/redo`. This reconfirms headless native pattern ownership/edit/persistence/transaction behavior; it does NOT verify Qt timeline double-click or live hover. A separate ad-hoc workflow test command failed at PowerShell quoting before any tests executed, so no claim of full suite success. No release, installation modification, or patch validation.

NEXT EXACT STEPS: (1) inspect latest GitHub development HEAD and push Actions package/modeling results, not PR-only run lookup; (2) run the full test_workflow.py in the isolated test interpreter using a checked-in Windows launcher rather than nested PowerShell command quoting; fix the disconnected Join message and cancelled Source property failures, then commit focused regressions; (3) verify real FreeCAD 1.1 Qt timeline double-click, hover midpoint/center overlay, DPI alignment, teardown and click-through; (4) create and validate a separate 0.5.11-to-0.5.12 patch against an immutable baseline, including Qt startup, rollback and SHA256, without touching the production 0.5.11 installation; (5) do not publish until all gates pass.

## 2026-11-12 - Windows DEV native workflow regression repair
On LAPTOP-O8QBOF2P, checked codex/az-design-workbench and preserved untracked run_native_0512.ps1. In isolated Az Design Native 0.5.12 TEST, bundled FreeCAD 1.1 Python executed tests/test_workflow.py: initially 57 tests, 1 fail (disconnected Join generic error) and 1 error (legacy Source property missing after cancelled edit). Fixed both in operations.py with descriptive preflight Join error and explicit restoration of legacy migrated link types on Cancel when native abort drops dynamic properties. Retest PASS 57/57. Also reran native_0512_two_patterns.py: PASS two independent patterns/save-reopen/Undo/Redo. Windows GUI click-through, hover/DPI and timeline editing have NOT been verified by this session. Local code commit 049c776 (after rebasing atop concurrent remote docs 3b13302). Original 0.5.11 untouched; dev test copy remains experimental. NEXT: inspect and fix full suite if needed; GUI acceptance in isolated DEV; guarded 0.5.11 to 0.5.12 patch only after validation. No release.


Additional verification on same Windows isolated DEV: full unittest discovery test_*.py executed with bundled FreeCAD 1.1 interpreter and explicitly loaded DEV azdesign package: PASS 195/195 in 13.459 seconds, test exit 0. This includes previously failing native test_workflow.py. This does not replace actual Qt GUI interaction, hover/DPI, or installer patch verification.


## 2026-11-12 — Native two-pattern CI gate added (13:49 EST)

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and this handoff from the development branch. Connected Windows laptop LAPTOP-O8QBOF2P; local HEAD was 98e8b287 and `git fetch origin codex/az-design-workbench` showed no divergence, with only pre-existing untracked `run_native_0512.ps1`. The latest documented Windows isolated FreeCAD 1.1 native suite passed 195/195 and the two-pattern native script passed, but those are prior-session evidence, NOT tests rerun in this execution. Confirmed the Linux native modeling workflow previously ran `run_workflow.py` only. Commit a20d4246 adds `native_0512_two_patterns.py` as a separate offscreen FreeCAD-native modeling CI step, covering independent pattern records, edit isolation, FCStd save/reopen, and Undo/Redo. This CI job has NOT yet been observed passing; FreeCAD Linux runtime differences may require fixes. An initial local PowerShell edit command failed at parsing and changed no files; GitHub Contents API was used for the actual committed workflow edit. No release, installer, or production 0.5.11 changes.

NEXT EXACT: (1) inspect push Actions modeling and package results for a20d4246 and this handoff, fetch failing job logs and fix compatibility without removing assertions; (2) in isolated Windows DEV, refresh checkout only after `git status` and preserve untracked launcher, then rerun 195-test suite and two-pattern test; (3) verify real FreeCAD 1.1 Qt timeline double-click, body-edge/midpoint/center hover, high-DPI projection, teardown and drawing click-through; (4) construct a distinct guarded 0.5.11-to-0.5.12 patch against immutable baseline, test Qt startup, rollback, checksums, and native geometry on disposable copy; (5) publish only after every gate passes. No user action currently required.

## 2026-11-12 - 0.5.12 first-pass layout repair (Windows DEV)
On laptop isolated DEV checkout, added single Home (cube only) by removing bottom duplicate; reduced seven bottom navigation/control buttons to 34x34 with 19px icons; lightened presentation-only grid; added Advanced > Restore Design layout command to show ribbon/Browser/history and reset dock widths. Implementation commit 4e7c3bf. Executed FreeCAD 1.1 Python py_compile for three edited files (PASS), full native unittest discovery 195 tests (PASS), and git diff --check (PASS). Copied only workspace.py, session.py, appearance.py to isolated Az Design Native 0.5.12 TEST Mod/AzDesign package and SHA256 verified copies. Did not touch original Az Design Native 0.5.11. DEV FreeCAD process was running during copy; must restart DEV safely (do not close unsaved work) before GUI feedback. GUI Ribbon/Browser/timeline visual acceptance, hover/UI events, release patch and rollback are NOT yet verified. Local run_native_0512.ps1 remains untracked and preserved. NEXT: user restart DEV after save and provide full-window screenshot; inspect/repair any remaining layout clipping, then Qt UI tests and guarded 0.5.11-to-0.5.12 patch.



## 2026-11-12 — 0.5.12 CI failures identified and test bootstrap repaired (16:38 EST)

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and this handoff on GitHub branch codex/az-design-workbench. Starting remote HEAD e011aa19606e7c5c63f8d141d1834a86d165179a. Actual push Actions run 43289257222 failed in BOTH jobs, despite the native workflow's 57 test_workflow tests passing. Package test_snap_overlay.py imported snap_targets.py which imports FreeCAD on a plain Python runner, yielding ModuleNotFoundError. Modeling native_0512_two_patterns.py directly imported FreeCAD without the /usr/lib/freecad*/lib discovery already used by run_workflow.py, also yielding ModuleNotFoundError.

Committed 1e67bfee3c28e29a0542d144cf75460e82886caf: isolate plain-Python sketch overlay tests using a stub for the separately covered native body-edge adapter. Committed b764cb6ba4784681053dcca4790134602f626624: discover native FreeCAD library and Mod paths in two-pattern script before importing FreeCAD, matching run_workflow.py. These are focused test harness fixes, not claims of new GUI functionality. Both commits are pushed through GitHub API; resulting CI has NOT yet been verified. Windows LAPTOP-O8QBOF2P was online but remote start_process returned internal error, so no Windows test or worktree verification this execution. Production 0.5.11 untouched; no release.

NEXT EXACT: (1) inspect fresh push Actions on b764cb6 and this handoff; if failing fetch failed job logs and fix root cause without weakening native assertions. (2) Recover Windows isolated DEV shell and inspect git status/HEAD; rerun 195 native tests, two-pattern script, and live Qt 1.1 timeline double-click and hover midpoint/center, DPI, teardown, native click-through. (3) Implement distinct guarded Windows 0.5.11→0.5.12 patch workflow on immutable baseline and disposable copy; validate Qt startup, native geometry, rollback, SHA256 before release. (4) Keep SESSION_HANDOFF.md current and do not publish or alter working 0.5.11.

## 2026-11-12 — 0.5.12 source-index ownership hardening (17:25 EST)

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and SESSION_HANDOFF.md on the requested branch. The Windows native test laptop LAPTOP-O8QBOF2P was offline at inspection; DESKTOP-9R8AKVU was online but is not the verified isolated Windows FreeCAD 1.1 test environment. Do not substitute that device or touch installed 0.5.11. GitHub API access was available, but its commit workflow lookup only covers pull_request runs, not all push Actions, so latest CI status is not verified in this execution.

Committed 0ecff177: read_records now rejects malformed pattern source identities (negative, bool, noninteger) before editing, and validate_ownership rejects negative/out-of-range source and generated geometry indices. Committed c9bf5b73: pure-Python regression for malformed source and out-of-range native source. These are narrowly scoped safety improvements for independently editable sketch history; they do not establish live GUI acceptance. No native or local tests were executed in this run; new CI results remain unverified. No release or production install changes.

NEXT EXACT STEPS: (1) inspect push Actions for c9bf5b73 and this handoff; run test_pattern_records.py and both native pattern/workflow suites; repair any regression without weakening ownership rejection. (2) Reconnect isolated LAPTOP-O8QBOF2P, inspect branch HEAD/status/diff and preserve local launcher, rerun 195-test suite and two-pattern FCStd/Undo/Redo. (3) Exercise actual FreeCAD 1.1 Qt timeline double-click, nonmutating body-edge/midpoint/center cues, high-DPI projection, teardown, and drawing click-through. (4) Build separate guarded 0.5.11→0.5.12 patch against immutable 0.5.11 baseline on disposable Windows copy; validate native geometry, Qt startup, rollback and SHA256 before publication. Never modify the working 0.5.11 install.


## 2026-11-12 — 0.5.12 source ownership creation guard (18:xx EST)

Read all five continuity documents on codex/az-design-workbench, inspected pattern_records.py and test_pattern_records.py. The verified Windows FreeCAD 1.1 DEV laptop LAPTOP-O8QBOF2P was OFFLINE (last seen 21 minutes earlier); DESKTOP-9R8AKVU online is not a substitute for its isolated test installation. GitHub commit search does not reliably identify development branch HEAD and the available commit-run lookup excludes push Actions, so current push CI remains unverified.

Committed 3ee235f: append_record now rejects invalid/noninteger/out-of-range source identities and malformed generated geometry indices before creating a property, and prevents sourcing a new pattern from another pattern's generated geometry. Committed fd655cb: pure-Python regression asserts these cases fail without changing serialized records. These commits were made through GitHub Contents API on the requested development branch; tests were NOT executed locally or in native FreeCAD during this run. No production install, patch, or release was touched.

NEXT EXACT: (1) inspect latest development HEAD and push Actions status, execute test_pattern_records.py in a plain Python environment and native_0512_two_patterns.py plus full native FreeCAD 1.1 suite in isolated DEV; repair any failure, including cross-owned source edge cases, without weakening assertions. (2) Reconnect LAPTOP-O8QBOF2P and inspect local git HEAD/status/diff, preserve untracked launcher and running GUI state. (3) Exercise real Qt 1.1 hover body-edge/midpoint/center cues, DPI, click-through/teardown, and independent timeline double-click editing with FCStd reopen and Undo/Redo. (4) Implement separate pinned 0.5.11-to-0.5.12 patch workflow on disposable Windows copy; validate native geometry, Qt startup, rollback and SHA256. Do not publish or modify the installed 0.5.11 baseline.

## 2026-11-12 - Extrude timeline editing video regression (19:14 EST)
Owner supplied ~70 second Windows DEV GUI video showing timeline double-click successfully opens Edit Extrude but Pick face can hide a first/New Body solid and leave sketch outline. Inspected tasks.py: begin_face_pick forcibly hides operation outputs and reveals prior Body Tip even if no prior tip exists. Commit 4be48ac preserves original visible result as read-only visual reference while picking for an edit with no earlier tip; existing addSelection rejects edited/downstream features as source. Normal edit with earlier tip retains previous behavior; UI adds source selection guidance. Added two focused headless regressions in test_extrude_preview_ui.py. On LAPTOP-O8QBOF2P bundled FreeCAD 1.1 Python, full discovery PASS 199/199, code checked and DEV tasks.py copied with matching SHA256 to isolated Az Design Native 0.5.12 TEST. Live Qt GUI acceptance of this change requires DEV restart, NOT yet performed. 0.5.11 original untouched. NEXT: restart DEV safely after saving, verify Pick face no longer blanks first Extrude and rejected self-face does not mutate geometry; test distance edit and Cancel/Undo; complete timeline/sketch hover/DPI and guarded patch release gates.



## 2026-11-12 19:xx EST — isolated Windows regression checkpoint

Connected LAPTOP-O8QBOF2P, fetched development branch, and observed concurrent commits 4be48ac and 87179e8. Did not overwrite or duplicate their implementation. Personally executed `test_pattern_records.py`: PASS 12/12; `test_extrude_preview_ui.py`: PASS 6/6; isolated FreeCAD 1.1 `run_native_0512.ps1`: PASS two independent patterns, FCStd save/reopen and Undo/Redo. The full native unittest discovery attempt failed at PowerShell argument parsing before running tests; do not count it. The untracked launcher was preserved. No live Qt hover/timeline/DPI or guarded patch/startup/rollback/checksum acceptance was performed; installed 0.5.11 untouched, no release.

NEXT EXACT STEPS: (1) inspect latest branch HEAD, CI push jobs, and concurrent working-tree changes before editing; (2) run full native FreeCAD 1.1 unittest discovery through a correctly quoted test launcher and fix failures; (3) validate actual Qt passive edge/midpoint/center hover, nonmutating click-through, DPI and teardown, timeline double-click, independently editable pattern history, save/reopen and Undo/Redo; (4) build a separate immutable 0.5.11 baseline to 0.5.12 disposable Windows patch, verify native geometry, Qt startup, rollback and SHA256 before release. Do not touch installed 0.5.11 or publish early.


## 2026-11-12 20:26 EST — fail-closed generated-index guard

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and SESSION_HANDOFF.md on the development branch. Inspected pattern_records.py and test_pattern_records.py. LAPTOP-O8QBOF2P (the isolated Windows FreeCAD 1.1 DEV machine) was offline; DESKTOP-9R8AKVU was online but is not the validated isolated test environment. Did not touch either production 0.5.11 or a release. The GitHub commit-search endpoint returned old default-branch commits rather than a reliable branch HEAD, and the available workflow lookup excludes push runs; do not claim CI green.

Committed b547fcb749a4594543bc5d4165ee36656adcb014 to reject duplicate and negative generated geometry indices in append_record BEFORE a record or property is created. Committed a75ec99b06724a94bc8cd8d2bea9135f871260bc to cover (-1,6,7), (5,5,7), and (5,6,-1), asserting persistence remains unchanged. These are source/test changes, not executed tests; native geometry, Qt hover/timeline, and Windows patch gates remain open. No publication.

NEXT EXACT: (1) inspect current branch HEAD and push Actions run for a75ec99b; execute addons/AzDesign/tests/test_pattern_records.py, then native_0512_two_patterns.py and full native FreeCAD 1.1 discovery in isolated DEV; fix failures without weakening assertions. (2) Recover LAPTOP-O8QBOF2P, inspect git status/HEAD and preserve untracked launcher, restart isolated DEV safely only after saving, and verify actual Qt hover body-edge/midpoint/center nonmutating cues, DPI, click-through, teardown and timeline double-click pattern edits with FCStd reopen and Undo/Redo. (3) Implement a guarded immutable 0.5.11-to-0.5.12 Windows patch on a disposable copy; test Qt startup, geometry, rollback and SHA256. Never publish or modify the production 0.5.11 until all gates pass.

## 2026-11-12 - Windows DEV solid-edge hover regression (owner feedback)
Owner confirmed no snapping/midpoint indicators on existing solids in 0.5.12 DEV. The actual snap_overlay.py relied on Gui.Selection.getPreselection with Object/SubElementNames; native Sketcher may offer no such preselection. Also passive_sketch_cues rejected an upstream dependent source, incorrectly for purely read-only display. Commit 3a6ea75: add bounded visible_body_cue fallback over up to 4 visible Body Tips / 120 edges, with fallback to previous solid when active sketch is Tip, exact planar midpoint and circular center detection and screen-space radius filtering. The hover indicator does NOT modify sketch geometry, mouse events, or create associative constraints. Add regression tests for missing preselection / midpoint / center, upstream hover while link safety still enforced. Bundled Windows FreeCAD 1.1 full unittest discovery PASS 201/201. Copied snap_targets.py and snap_overlay.py to isolated Az Design Native 0.5.12 TEST only, both SHA256 matches confirmed. Existing 0.5.11 not modified. GUI runtime has not been restarted or visually verified; production release, real snapping constraints and patch gates remain pending. NEXT: save and restart 0.5.12 DEV, test midpoint over top-face line and hole center in Sketcher. If visual indicator appears but clicking does not create usable constrained geometry, develop native associative external geometry workflow with GUI tests, not fake mouse snapping.


## 2026-11-12 21:xx EST — persisted pitch metadata validation

Read AGENTS.md, PROJECT_STATE.md, DECISIONS.md, ROADMAP.md and SESSION_HANDOFF.md on codex/az-design-workbench. Inspected pattern_records.py and test_pattern_records.py. Committed 7650f05ad34a5ed047e5a11242958b8f4dcc0396 to reject bool dimensions and nonnumeric/nonfinite/out-of-range persisted pitches before producing a pitch-edit plan; committed 1b6febea4e5115b46591b581b5baf70696f0996d with corruption regressions asserting the serialized record is unchanged after rejection. These are source/test commits through the GitHub API, NOT executed test passes. No local worktree was inspected, no Windows/Qt/native tests ran, and push CI status is not verified. Production 0.5.11 and release artifacts untouched.

NEXT EXACT: (1) inspect current HEAD/push Actions and run python addons/AzDesign/tests/test_pattern_records.py, especially new corrupted metadata tests; fix any failure. (2) On isolated LAPTOP-O8QBOF2P, inspect git status/HEAD and preserve local untracked launcher; run complete native FreeCAD 1.1 suite and native_0512_two_patterns.py, verifying independent constraints, FCStd save/reopen, Undo/Redo. (3) Save/restart isolated 0.5.12 DEV GUI and verify visible_body_cue fallback for line midpoint and circular center, click-through, high-DPI, teardown, and timeline double-click pattern edit. (4) Build and validate pinned 0.5.11-to-0.5.12 Windows patch on disposable copy, including Qt startup, native geometry, rollback, and SHA256. Do not publish or modify installed 0.5.11 before all gates pass.

## 2026-11-12 - Native Sketcher solid-edge snapping reference workflow
Owner confirmed visual midpoint/center markers appeared in 0.5.12 DEV but clicking while drawing did NOT snap. FreeCAD 1.1 source inspection in src/Mod/Sketcher/Gui/SnapManager.cpp and Command.cpp confirmed native SnapToObjects is separate from overlay, controlled by User parameter:BaseApp/Preferences/Mod/Sketcher/Snap flags Snap and SnapToObjects; the native snap manager uses Sketcher preselected geometry. New source commit e521ffa adds explicit Sketch Palette button Use solid edges for snapping, implementing enable_solid_edge_snapping(sketch) to reference only the preceding valid solid in the same Body, coplanar edges only, bounded 80 edges, no duplicates, one native document transaction, and native Snap/SnapToObjects plus Autoconstraints enabled. It is opt-in, NOT an automatic mutation on hover. Native Windows FreeCAD 1.1 actual headless test verified four top-face references, repeated call zero, Undo clears references, Redo restores, save/reopen retains reference links and sketch up-to-date. New permanent test_solid_edge_snapping_native.py. Full local Windows native unittest discovery 203/203 PASS after rebasing over concurrent pattern-record commits; syntax checks passed. Source snap_targets.py, sketch_palette.py, session.py copied only to isolated Az Design Native 0.5.12 TEST installation with SHA256 matches. Running DEV FreeCAD process not restarted; user must save and relaunch DEV to load new palette. 0.5.11 untouched. Native GUI click snapping, line midpoint, hole center and actual parametric constraints STILL require live acceptance; do not claim full Fusion snap parity. NEXT: restart DEV, in a new sketch click Use solid edges for snapping, confirm purple/magenta native projected edges and snapping while Line/Circle drawing, test save/reopen; if points are only position snaps, implement explicit native Coincident/PointOnObject constraints to stabilize geometry.

