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
