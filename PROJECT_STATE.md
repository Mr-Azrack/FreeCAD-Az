# FreeCAD-Az — project state

**Inspected:** 2026-11-06
**Repository:** https://github.com/Mr-Azrack/FreeCAD-Az
**Development branch:** codex/az-design-workbench
**Implementation baseline reviewed:** dac67fee9cebb9cb7e342a45098fd913510f10f6 (Az Design 0.2)
**Draft PR:** https://github.com/Mr-Azrack/FreeCAD-Az/pull/1
**Status:** Az Design 0.3.3 modeled-thread crash-lab review build in development; opt-in helical threads and diagnostic probes implemented. Prior 0.3.2 Linux tests passed; Windows/1.1 modeled-thread crash not reproduced or fixed. The checked-in release ZIP remains 0.3.1.

## Objective

Build an independently maintainable FreeCAD-based CAD workflow approaching Fusion 360 for real shop use, rather than a superficial UI skin. User direction is to pursue the complete workflow goal while shipping evidence-backed, recoverable milestones.

## Observed code in Az Design 0.2

- Installable add-on in addons/AzDesign with packaged addons/releases/AzDesign-0.3.1.zip and local installer with backup.
- Solid/Sketch/Utilities ribbon, native Browser/Tasks arrangement, shortcuts, search, camera/navigation handling and bottom feature history.
- Sketches with separately selectable exact planar regions (including nested/overlapping/divided profiles), live extrude/cut/intersect/join/new body previews, distance handles, signed distances, symmetric/two-sided extents, taper, offsets, Through all and To face.
- Press/Pull for supported extrusion end caps, some prismatic faces, source sketch circles, and supported native cylinder/hole dimensions. Unsupported ambiguous geometry reports an error instead of silently changing the wrong feature.
- Native expression-based user parameters using a Parameters spreadsheet; geometric edits and their cancellations.
- Real Body Tip rollback, suppression and insertion for supported feature histories; reversible native transactions, mixed native/Az operations and saved geometric references.
- v0.2 Az custom parametric features use FreeCAD Pad/Pocket and OCCT evaluation, and require Az Design present for editing/recomputation. Cached geometry is preserved in saved FCStd; v0.1 native Pad/Pocket features remain native without migration.

## Validation provenance

- addons/AzDesign/tests/validation-v02-linux.json records **26 passing modeling tests**, **4 passing installer tests**, passing v0.2 GUI workflow checks, passing original 30-item navigation/native workflow checks, and a recorded manual mouse-drag diagnostic.
- Environment evidenced: FreeCAD 1.0.0, Linux / Qt5 / PySide2.
- The continuity-only checkpoint at f500e727 inspected these records without executing FreeCAD. The implementation session separately executed the tests summarized below; neither session validated Windows.
- Existing CI workflow in .github/workflows/az-design.yml includes packaging and modeling checks; current check-run status must be fetched before calling CI green.

## Unresolved gaps and restrictions

- Windows, macOS, PySide6 / Qt6 and FreeCAD 1.1 not verified by recorded tests.
- Not a complete Fusion timeline: real rollback/suppression exist, but drag reordering, arbitrary branch editing, and all dependency repair behaviors are not established.
- Press/Pull is limited to supported geometry; general arbitrary imported-surface offset/healing is not implemented.
- Revolve, Loft, Sweep, advanced Hole, Shell, patterns, Fillet and CAM still rely substantially on native FreeCAD tasks.
- Assembly/joints, fully integrated drawings, manufacturing UI parity and broad shop-part benchmarks remain future work.
- Custom Az feature recomputation needs Az installed, unlike the original v0.1 pure native feature path.

## Next evidence checkpoint

Install Az Design 0.2 on the intended Windows workstation and complete a representative fabrication part: multi-region sketch, parametric extrusion, Press/Pull edit, rollback/recompute, undo/redo, save/reopen, STEP export, and native-workbench switch. Record exact OS/FreeCAD/Qt version and pass/fail per step. Do not claim this checkpoint complete before it is actually run.

This file is a **dated snapshot**, not a replacement for inspecting the current branch HEAD, diffs, tests and PR. Read AGENTS.md and SESSION_HANDOFF.md before changing code.

## Implementation-session verification — 2026-11-05

For code commit `dac67fee9cebb9cb7e342a45098fd913510f10f6`, the implementation
session personally ran **26** native modeling tests, **27** desktop workflow
checks, **30** original modeling/navigation checks and **4** installer tests;
all passed on FreeCAD 1.0.0 / Linux / Qt5/PySide2. A real mouse drag from 2 mm to
11.6486 mm updated the solid; Cancel restored geometry and transaction state.
Mixed native/Az Fillet history survives upstream dimensional edits and reopening.
Cached FCStd solids were separately opened without importing the Az module.

[Az add-on CI run 42100114683](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42100114683)
passed both native modeling and package jobs. The inherited Dependency Review
workflow failed because this fork's Dependency graph is disabled/unsupported;
no repository settings were changed. Do not call repository-wide upstream CI all
green. Formatting, source/XML and ZIP integrity checks passed. Installer SHA256:
`b7cc3ac7c97cfe8a26b29085e7efd230c0cf92fbf507e9e7f75ce5cca765579e`.

## Startup hotfix — 0.2.1

The owner reported `name '__file__' is not defined` from InitGui.py in a Windows
FreeCAD v1-1 installation. Both entry scripts had that assumption. Previous GUI
launchers explicitly injected `__file__` and did not validate the real startup
contract. Reproduced before fixing: four startup-test errors and one resource-path
failure. The workbench now lives in imported `azdesign.workbench`; Init.py and
InitGui.py rely on FreeCAD's prepared module path. The five startup regressions
and four installer tests pass. A full installed FreeCAD 1.0/Linux restart also
automatically registered Az Design and activated its ribbon, without injecting
loader variables. See `validation-startup-0.2.1.json` for fresh startup
evidence; previous geometry checks remain evidence for the unchanged 0.2 engine.
Full Windows/1.1 acceptance remains pending the owner's reinstall and retest.

### Published 0.2.1 verification checkpoint

Startup fix/source commit: `0242b3a6f7b23026a2b33e63ad6e04ac5c5763e0`.
[Add-on CI run 42162682276](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42162682276)
passed for that commit, including the new startup regressions and native modeling/
installer/package jobs. The ZIP is `addons/releases/AzDesign-0.2.1.zip`, SHA256
`c65900d15c337f619e34a8d2fb719bdd75426ad4a68b8b39f8ec9e0e2ee0bd8d`.
PR #1 remains draft and main is unchanged. The inherited Dependency Review setting
issue persists. The remaining immediate action is the owner's Windows/1.1 reinstall
and startup/modeling retest; Linux startup validation does not close that gate.

## First-document hotfix — 0.2.2

The owner reported Create Sketch failing at `Gui.activeDocument().activeView()`
with no visible document; choosing New stopped it. Reproduced the traceback: the
hidden temporary AzGeometry calculator could be App-active while Gui had no
active design. Modeling now resolves the visible Gui document, creates a normal
Design when needed, and synchronizes the App context. Body/face selection ignores
other documents. Calculator creation restores its native active-document pointer
without closing the persistent document or committing an edit transaction. The
Python App.ActiveDocument attribute may remain stale after clearing that pointer;
it is not a reliable test for a visible modeling context.

Fresh verification: 13 context, 5 startup, 4 installer and 26 native modeling tests
passed. An installed FreeCAD 1.0/Linux restart followed by Create Sketch, XY plane,
mouse-drawn rectangle and Extrude produced a valid solid without choosing New.
All 27 native GUI workflow checks passed again, including undo/redo, parameters,
rollback, cancellation, native Fillet propagation and save/reopen. Final calculator
code was installed and reloaded before the last GUI suite. Evidence:
`addons/AzDesign/tests/validation-document-context-0.2.2.json`. CI publication is
pending at this source checkpoint. Windows/1.1 acceptance remains pending.

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

## Workspace redesign — 0.3.0, 2026-11-06

Owner confirmed their existing setup works (installed version unspecified) and
requested Fusion-like work-area layout, visuals and behavior, with freedom to
modify the whole fork. That report is useful user feedback, not a completed
Windows acceptance matrix. The new repo-owned Qt workspace replaces the surrounding
work area while retaining native FreeCAD documents and geometry. It is packaged
as an installable module so a Windows application rebuild is not required.

Implemented: top native-design tabs; left Design selector; original editable SVG
icon family; grouped searchable Browser with visibility, native selection, isolate
and properties access; compact Body-aware timeline with real previous/next Tip
steps and optional labels; light canvas and readable edit-mode sketch colors;
matching native task headers; bottom-center navigation, camera/display options and
a presentation-only grid; idle Solid radial tools. Native CAD restores previous
menus, layout, styles, navigation and changed canvas preferences. Closed document
requests use FreeCAD's own save confirmation. Core changes remain available for
future API boundaries, but this milestone modifies no C++ geometry/core code.

Fresh validation: 28 workspace, 27 v0.2 and 30 original desktop checks; 26 native
modeling, 13 document-context, 5 startup and 4 installer tests all passed. An
installed full restart registered Az and opened a visible Design automatically.
The final sketch-contrast follow-up was installed/reloaded and all 85 GUI checks
were rerun successfully. See `validation-workspace-0.3.0.json` for provenance and
manual visual observations. Environment: Linux FreeCAD 1.0/Qt5/PySide2. Native
advanced tasks remain; radial gestures during sketching, full timeline reordering,
and a complete Fusion clone are not claimed. Windows/1.1/Qt6 remains pending.

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


## Hole task stabilization — 0.3.2 review build, 2026-11-06

The owner reported that invoking native Hole changed the Az workspace, Show result
could make the solid disappear, and geometric threads crashed FreeCAD. These are
user-reported symptoms, not a verified crash backtrace or identified OCCT defect.

The new native Hole workflow uses Az_Hole, a repo-owned Qt task panel and native
PartDesign::Hole features. It supports sketch circle/arc centers, hole diameter,
dimensional/through-all depth, and specified cosmetic threads. Hole creation and
tip-feature editing use transactional previews. Show original solid and invalid
previews restore the prior Body Tip and base visibility; Cancel aborts the
transaction. The Browser, feature timeline and native-tree double-click path
route to the Az task. The native geometry remains editable without Az in FreeCAD.

IMPORTANT: ModelThread=True is deliberately blocked in Az because an in-process
OCCT thread-geometry crash cannot be caught by Python. Cosmetic thread metadata
is not a substitute for modeled helical faces. Advanced Hole options,
non-tip feature edits and previously modeled-thread features remain native CAD
paths. No full root-cause geometric-thread crash fix is claimed.

Compatibility: FreeCAD 1.0 lacks CosmeticThread; hole_spec.py detects its presence
rather than assigning a nonexistent property. The first native run failed on
this missing property; the corrected run passed. The final source-only 0.3.2
build is packaged by CI, not yet committed as a ZIP under addons/releases.

Verified evidence:
- [Native/package run 42248055124](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42248055124)
  passed **28 native modeling tests** on headless Linux FreeCAD 1.0, including
  valid native Hole preview/cancel and native cosmetic-thread metadata.
- Package checks passed 4 HoleSpec and 3 HoleOperation offline tests, along
  with the previous installer, startup, context, appearance, compatibility,
  source and XML checks.
- Real Az Hole Qt dialog, FreeCAD 1.1/Qt6, Windows display scaling, native-tree
  edit interception, STEP/save/reopen and geometric-thread crash reproduction
  are **not yet validated on the owner's Windows workstation**.

Next: download the 0.3.2 AzDesign-installer artifact from the latest passing
Az Design add-on CI, install with the backup macro, fully restart Windows
FreeCAD 1.1 and test hole Create/Show result/Show original/Cancel/Accept,
cosmetic thread standard+explicit size, subsequent Hole editing, save/reopen,
STEP export and Native CAD restoration. Capture exact traceback and versions
for failures. PR #1 remains draft; do not merge to main.

### Verified packaged review build — 0.3.2

[CI run 42248286120](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42248286120)
passed native modeling and installer/package jobs. Artifact
[AzDesign-installer 13519427193](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42248286120/artifacts/13519427193)
contains `AzDesign-0.3.2.zip`. Extracted inner ZIP: **160,781 bytes**,
SHA256 `23a308cbf2dc0d50396b95156851fbde115d7e15b3c25a9b792b337208130e11`.
The downloaded ZIP's CRC check passed and its packaged offline HoleSpec
(4) and HoleOperation (3) tests all passed separately on Python 3.13.
These package checks do not substitute for a Windows/FreeCAD 1.1 GUI retest.

## Opt-in native modeled threads and crash capture — 0.3.3, 2026-11-06

After testing 0.3.2, the owner confirmed that the normal Hole task works, albeit
less polished than Fusion, and specifically requested enabling real modeled
threads again to reproduce and investigate FreeCAD's crash.

Implemented on `codex/az-design-workbench`:
- `hole_spec.py` permits `ModelThread=True` ONLY with explicit experimental
  authorization, a recognized standard, a chosen size and a durable pre-switch
  callback. Regular holes remain cosmetic. The native ModelThread flag is set
  last, after other settings. FreeCAD 1.0/1.1 optional CosmeticThread is
  capability-checked and its read-only lifecycle respected.
- `hole.py` adds an unchecked-by-default "Actually model helical threads —
  EXPERIMENTAL" checkbox. Show result requires a specific crash-risk confirmation
  before creating geometry. The first thread-size discovery is non-geometric.
  Clicking OK on an unchanged successful preview does not recompute twice.
- `hole_operation.py` records pre-transaction, pre-property, pre-ModelThread,
  pre-recompute, post-recompute and error/valid-result checkpoints for opted-in
  modeled threads. `hole_diagnostics.py` uses fsynced JSONL logs in
  `App.getUserAppDataDir()/AzDesign-Diagnostics`, and enables Python fault
  traces where possible. These logs do not provide native C++ frames.
- `Tools/Probe_Modeled_Thread.FCMacro` builds a disposable native block,
  saves its input FCStd, then requests a genuine modeled M4 thread. The macro
  is included at the root of the installer ZIP. Run it in a SECOND FreeCAD
  process with no unsaved work. `THREAD_CRASH_LAB.md` explains reproduction,
  Windows Event Viewer, and optional ProcDump collection for a native stack.
- Offline tests check explicit opt-in, no uninstrumented model switch and
  checkpoint ordering. Live modeled helical OCCT calls are intentionally NOT
  executed by GitHub CI because the native crash may kill the worker.

**No root-cause fix is claimed.** The user must perform the first isolated
Windows/FreeCAD 1.1 reproduction and provide checkpoint/fault details. The
ordinary 0.3.2 modeled-thread safety restriction is superseded by this
experimental mode only, not removed from normal use. PR #1 remains draft.

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

## 0.3.4 — Modeled Hole editing correction (2026-11-06)

**Owner Windows feedback:** Az 0.3.3 modeled-thread creation in the interactive
Hole panel completed without crashing and visibly generated physical spiral
threads. The disposable probe macro was *not* used. Owner then tried editing
the modeled-thread Hole and encountered many error messages; verbatim error
output has not yet been captured. No Windows save/reopen test claimed.

**Confirmed code defect:** Both `HoleTask.__init__` and `HoleOperation.__init__`
still had explicit rejections of `editing.ModelThread`, inherited from 0.3.2.
0.3.3 also initialized the experimental checkbox to False even when editing a
feature where native `ModelThread=True`, risking accidental cosmetic conversion.

**0.3.4 change:** Remove those old edit-only refusal paths while retaining the
existing Body Tip and source sketch checks. Populate the edit checkbox using
native `ModelThread` and preserve original standard/size; store initial controls.
Show result/OK on an unchanged existing Hole does not touch the document or
regenerate helices. Changed modeled-thread settings still require explicit
per-preview warning and fsynced diagnostics. Transactional Cancel restores the
original. Added stubbed regression tests for existing modeled-feature edit and
native FreeCAD 1.0 cosmetic threaded-edit/cancel geometry rollback. The real
modeled-thread recompute is **not executed in CI**.

**Outstanding:** owner Windows/FreeCAD 1.1 0.3.4 trial, precise error text if
errors persist, actual modeled-thread edit/change followed by save/reopen, and
full native crash root-cause analysis if triggered. Do not label this a fully
validated modeled-thread edit implementation before those tests.

### Verified 0.3.4 editable native Hole package — 2026-11-06

**Verified CI:** [Az Design run 42271403820](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42271403820) passed both jobs. The native FreeCAD 1.0 modeling suite passed **29 tests**, including a real native threaded Hole edit, modified-depth preview and Cancel rollback test. The packaged offline HoleSpec tests (**6**), HoleOperation tests (**7**, including existing modeled-hole edit and native LinkSub Profile inputs), and durable logger test (**1**) passed, along with earlier install/workspace checks. This does **not** run helical `ModelThread=True` in FreeCAD 1.1 Windows; only the owner can validate that.

**Verified installer:** [AzDesign-installer artifact 13528953274](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42271403820/artifacts/13528953274) includes `AzDesign-0.3.4.zip`, **174,669 bytes**, SHA256 `8f7bba2e56f94446ffa427913a4951a8e92006eac49cfe84d03423e59746e6d1`.
Outer and inner ZIP CRC checks passed; both macro files and edited code were verified; the three packaged offline Hole test scripts passed when separately extracted and run.

**Specific reproduced native bug:** The first 0.3.4 CI [run 42271071660](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42271071660) failed in the newly added threaded-Hole edit test: `features.DesignError: Choose a native Hole associated with this sketch.` The native `Hole.Profile` is not always directly equal to a Sketch object. Fixed both `HoleOperation` comparison and `HoleTask` sketch selection with `hole_profile_sketch()` to resolve FreeCAD's `Profile` LinkSub representation, then reran CI successfully.

**Still pending:** User's actual Windows GUI/FreeCAD 1.1 trial of edit existing *modeled helical* threads, changing standard/size, save/reopen. If any errors persist capture first traceback, FreeCAD version and newest `AzDesign-Diagnostics` log. Do not conflate cosmetic native regression with a real modeled-helix edit stress test. PR remains draft/unmerged, checked-in release ZIP remains 0.3.1.

## 2026-11-06 — Owner confirmation: 0.3.4 modeled Hole editing

The owner installed/tested Az Design 0.3.4 after the modeled-thread editing fixes and reported **"ok that works great"**. Earlier owner testing confirmed that the Az Hole panel generated visible real helical threads on Windows without crashing. This is owner-reported GUI acceptance of the updated editing workflow, not a claim that every thread standard, size, save/reopen, downstream dependency, or native crash scenario has been tested. The 0.3.4 package/native CI checks previously passed; PR #1 remains a draft. Continue collecting exact repro cases for any remaining UX or geometry bugs.

## 0.3.5 incremental Hole task workflow polish — 2026-11-06

Owner confirmed that 0.3.4 modeled-thread creation and editing work well in
the Windows Az Hole panel, and instructed us to proceed without approvals:
"we break fix as we go." Keep iterations modest, working, backed by CI,
and preserve the modeled-thread diagnostic boundary.

Implemented:
- `hole.py` task now groups Placement, Geometry and Thread settings with
  readable labels, a short always-visible hint, and an experimental danger
  note displayed only for opted-in geometric threads.
- Human-readable thread standard names map to unmodified FreeCAD native
  enums. Threaded Hole diameter is disabled in the task because thread
  standard/size controls nominal diameter natively.
- Thread sizes load immediately when a standard is selected; no extra dummy
  Show result button press. The center sketch remains changeable during
  preliminary size discovery; changing it cancels the unpreviewed temporary
  native Hole transaction and rebuilds the options for the new source.
- 350 ms debounced optional live previews are on by default for complete
  plain/cosmetic holes only. `hole_ui_policy.can_live_preview` refuses
  modeled threads, originally modeled Holes and a recent modeled preview,
  as well as incomplete/invalid specs. Modeled previews retain manual
  Update preview, explicit warning and fsynced diagnostic logging.
- Show original, accept, cancel and cleanup stop pending preview timers.
  Existing identical modeled features remain no-op on accepting.
- New headless Qt interaction smoke test and pure policy tests cover
  signal wiring, one-step size lookup, safe auto preview and source switching.

Safety/verification: This is **not** a new geometry kernel or modeled thread
crash fix. GitHub package tests pass for the current increment, but platform
acceptance of the actual 0.3.5 task layout on Windows FreeCAD 1.1 still
requires the owner. Check latest exact GitHub HEAD, CI native/modeling job,
artifact bytes and source tests before declaring final release success.

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

## 0.3.6 — Editable and deletable bottom feature timeline (2026-11-07)

Owner reported that the bottom rollback strip did not behave like Fusion:
features could not be deleted and earlier features could not meaningfully be
modified. Development branch `codex/az-design-workbench`, draft PR #1. Changes
are explicitly incremental, not a claim of full Fusion parity.

Implementation:
- `ui.History` now has visible Edit/Delete controls for the selected timeline
  step. Feature tile double-click edits; right-click offers Delete feature and
  Delete from here, plus existing Roll back/Resume/Suppress. Delete key opens
  a confirmation while a feature tile has focus.
- Native Pad/Pocket/Fillet and other PartDesign feature double-clicks in the
  Browser open FreeCAD's native task editor instead of only Properties. Native
  task fallback remains for timeline features without Az-managed editors.
- `history.deletion_plan` checks actual FreeCAD incoming references and
  refuses a single deletion if any live object needs the feature. Explicit
  Delete from here enumerates later sketches/features within the same Body;
  cross-body/unscheduled dependencies block it. The confirmation shows the
  affected steps and explains Undo. `history.delete_feature` uses FreeCAD
  transactions, updates Body Tip/rollback marker and recomputes; it aborts
  newly invalid survivors rather than silently corrupting the file.
- `hole_operation.HoleOperation` now edits an earlier Hole while newer
  features exist, temporarily previews the Hole, restores the previous final
  Body Tip and recomputes/validates downstream solids before acceptance.
  Failed downstream validation prevents commit; Cancel rolls the transaction
  back. Existing modeled threads still require explicit warnings and logs.
- Native geometry regressions test deleting leaf Hole with Undo, refusing
  unsafe individual deletion, explicitly removing later dependent steps,
  and modifying/cancelling an earlier Hole under a later Pad.

Not implemented: arbitrary dependency repair, drag-reordering, automatic
reparenting of downstream feature references, or fully customized non-Hole
native task editors. Unsafe single deletions are rejected, and Delete from
here is intentionally destructive and confirmed; it is not a general 'remove
one middle step and magically preserve all geometry' operation.

Verification: see the latest 0.3.6 workflow and artifact; owner Windows 1.1 GUI
acceptance is pending. Do not claim the UI tested on Windows from Linux CI.

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

## 0.3.7 — In-app update bootstrap, November 7, 2026

Owner requested an end to downloading and reinstalling each Az build manually.
This workbench is in a public GitHub repository; no personal access token is
required to read successful Actions runs, Git metadata, or raw source files.
The new preview updater is a manual command, not background auto-update.

Implemented:
- `azdesign/updater.py`: select a **completed, successful** `Az Design add-on`
  pull-request workflow on the dedicated `codex/az-design-workbench` branch.
  Resolve the tested head SHA; compare the pinned `addons/AzDesign/package.xml`
  version against the local version and no-op if already current. Resolve the
  isolated AzDesign directory tree instead of downloading the multi-gigabyte
  upstream FreeCAD fork. Fetch files by SHA-pinned raw.githubusercontent.com
  URLs, reject path traversal, symlink/unsupported Git modes and outsized files,
  and verify individual Git blob hashes. Stage and syntax-check the entire
  snapshot before invoking existing backup-aware `install.install`.
- `commands.py`: Update Az command displays installed/tested versions,
  prompts to download, shows file progress/cancellation, and reminds user to
  save and restart FreeCAD (the already-loaded Python modules are NOT hot
  swapped). Blocks updates during a task. Failures report errors and preserve
  previous install unless the atomic installer itself encounters a rollback
  failure. Install leaves backup under the FreeCAD user AzDesign-backups folder.
- `ui.py`: visible **Update Az** top ribbon button and File menu entry.
  `catalog.py` registers `Az_Update` for Utilities and the command palette.
- `tests/test_updater.py`: deterministic offline mock HTTP fixtures test
  successful CI gating, SHA-pinned source, Git blob verification, complete
  backup/install, no-op same version, cancelled download, bad symlink mode,
  and rejection of unsafe paths. Package CI explicitly runs these tests.
- Version `0.3.7` source and README/install instructions updated.

**Bootstrapping:** User must install 0.3.7 by extracting the ZIP + executing
`Install_AzDesign.FCMacro` **once more**, then restart. Subsequent builds
have an Update Az button. Updates require an internet connection to public
GitHub endpoints and a full FreeCAD process restart. Linux CI and offline
HTTP mocking do not prove the user's Windows FreeCAD 1.1 network path; owner
acceptance is pending. Do not confuse a future source commit with a passing
CI-tested commit. Keep PR #1 draft and unmerged.

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
