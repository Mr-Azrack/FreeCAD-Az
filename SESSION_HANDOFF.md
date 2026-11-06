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
