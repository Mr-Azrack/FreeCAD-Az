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

## 2026-11-07 — Owner acceptance: 0.3.7 updater bootstrap

Following installation of Az Design 0.3.7, owner reported **"OK THAT WORKED WOOT"** in response to the instruction to run **Update Az** and verify the up-to-date result. Treat this as owner confirmation that the 0.3.7 installation and in-app check flow worked on their Windows FreeCAD machine. It does **not** validate downloading/installing a newer 0.3.8+ build yet; validate the actual upgrade path when a new tested version exists. Continue incremental break/fix workflow, PR #1 stays draft and unmerged.

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


## 2026-11-07 — Az Design 0.4.2 FreeCAD 1.1 Qt6 dialogs and cross-Body Extrude links

Owner's Windows 1.1 Report view errors:
`tasks.py:509 TypeError: int() ... not 'StandardButton'` when opening
Extrude task, and `PartDesign::FeaturePython: Link(s) to object(s)
'Body Sketch' go out of the allowed scope 'Extrude'; linked object(s)
reside within 'Body'` while using a Body-owned sketch.

Root causes and targeted source fixes:
- Qt6 `QDialogButtonBox.StandardButton` is an enum.Flag and direct
  `int(Ok | Cancel)` fails. New `azdesign/qt.py:standard_button_bits`
  uses the combined enum's `.value` (with backward-compatible legacy int).
  `tasks.py` and `hole.py` both call it. `test_qt_buttons.py`
  simulates Qt6 and Qt5 mask APIs and verifies both task getters.
- Extrude `Source` and `UpToFace` were declared local
  `App::PropertyLinkSub` and `SourceFrame/LimitFrame` local
  `App::PropertyLink`. New features use their respective
  `App::PropertyLinkSubGlobal` and `App::PropertyLinkGlobal` types,
  supporting legitimate references across native Bodies without
  copying/proxying source sketches. `BaseFeature` remains native
  local Body history link.
- Legacy 0.4.1 extrudes are migrated **only when explicitly opened for
  Edit**, under the existing Undo transaction using
  `features.upgrade_extrude_links`; the old source/face values are
  preserved, all four link types corrected and native Cancel rolls
  them back. No silent mutation merely from opening an old FCStd file.
  Unexpected property types abort the Edit transaction instead of
  overwriting unknown metadata.
- Native FreeCAD workflow tests cover a new body from an existing Body
  sketch, cross-Body geometry placement, migration+Cancel restoring
  the old property and an accepted update retaining geometry/identity.
  Qt compatibility package tests and old Hole-panel stub updated.

Version `0.4.2` and release notes staged; user should use **Update Az**
from 0.4.1 and completely restart FreeCAD once CI passes.
Original 0.4.1 files are backed up by updater. Older saved Extrude can
be repaired by Edit → valid preview → OK → Save.

One early CI job failed **in the mocked Hole panel test** because its
stand-in `azdesign.qt` did not expose the new helper; that stub was fixed.
Early native runs including newly added cross-Body and legacy migration
tests passed (39 geometry tests in 1.23s on Linux FreeCAD 1.0).
Check final CI run `42377682997` for BOTH package and native success
and verify artifact before release. Actual Windows 1.1 acceptance pending.


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


## 2026-11-07 — Owner video: Extrude model disappears during profile selection (0.4.3)

Owner uploaded an ~8-second Windows FreeCAD 1.1 recording after 0.4.2.
Visible: a threaded block with Body sketches, Extrude panel showing
`Sketch001` and two selectable profile regions. The solid repeatedly
vanishes and reappears while the user changes profile/pick mode. The panel
shows `0 selected` / "Select at least one closed profile", and a later
one-region attempt reports "This operation must produce one connected
solid per body. Check profiles, direction and extent." The FreeCAD
Report view shows `Body: Tip shape is empty` and some earlier
`TopoShapeExpansion.cpp(983): hasher mismatch` messages. Do not assume
the hasher warning is entirely caused by the preview problem.

Code root causes confirmed:
- `tasks.ExtrudeTask.__init__` automatically enabled profile picking
  when multiple regions were present and none was checked.
- `apply_pick_visibility` looped over all `PartDesign::Body` and
  `Part::Feature` objects and explicitly set Visibility=False, blanking
  the canvas by design.
- `schedule` allowed a 160ms timer to recompute while selecting profiles.
- `operations.Operation.update` could create/activate a transient
  invalid FeaturePython Body Tip and then raise, leaving the failed result
  in the open transaction.

0.4.3 corrective code:
- Removed automatic pick-mode activation; picking is opt-in.
- Overlay profile selection no longer hides Bodies/solids.
- Suppressed competing timer preview while picking sketch regions or faces.
- Added `Operation.discard_preview`: new Extrude previews remove created
  transient objects and restore native Body tips/visibility followed by
  recompute while retaining the task transaction. Existing-feature edits
  remain non-disposable with native full Cancel rollback.
- `ExtrudeTask.preview` now gates zero selected sketch profiles (no
  computation) and invokes cleanup after invalid previews.
- Added native geometry tests for invalid disjoint Intersect cleanup,
  preserving Body Tip/volume/document inventory, subsequent valid retry
  and a valid preview discarded before Cancel. The initial test tried a
  distant Join; native FreeCAD allowed a no-op rather than throwing, so the
  test was corrected to a deterministic disjoint Intersect case.
- Added `tests/test_extrude_preview_ui.py` with four behavioral stubs
  checking the no-profile path, invalid preview cleanup, persistent Body
  visibility in overlay mode and timer gating; registered in CI.

Version 0.4.3 source and release notes staged. Real Windows GUI acceptance
is pending. A genuinely disconnected Join is still invalid; choosing a
different profile or operation is not an engine fault. Repeated historical
`TopoShapeExpansion` hasher mismatch messages may need separate analysis.

Latest targeted run for final combined source: `42411861600`; package
passed, native geometry job still running at last check. Confirm both
passes and exact tested ZIP before user Update Az instruction. PR #1 stays
draft/unmerged.


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


## 2026-11-08 — Az Design 0.5.0 substantive fixture workflow milestone

User explicitly approved building **0.5.0** instead of further piecemeal
cosmetic revisions. Source remains on public `Mr-Azrack/FreeCAD-Az`,
`codex/az-design-workbench`, draft PR #1; main not changed. The state
at startup was 0.4.3, source HEAD
`706fb3117ca846eccef02a285fd27db7755b202d` and both 0.4.3 CI jobs
already passing. User's Windows 1.1 acceptance of 0.4.3 disappearing-solid
preview behavior is not confirmed by further user feedback.

Substantive 0.5.0 code changes:
- `azdesign/sketch_rectangle.py`: new **Sized Rectangle** command for a
  sketch that is empty and being edited, with width/height input dialog.
  Creates native Sketcher 4 lines, 11 Coincident/Horiz/Vertical/origin and
  driving length constraints inside one undoable transaction. Real dimensions
  change sketch geometry and downstream modeling, not an overlay.
  Exposed under SKETCH CREATE and command palette via
  `catalog.py` / `commands.py`.
- `operations.Operation._preflight_existing_body`: **new**
  Join/Cut/Intersect runs its prospective profile geometry against the
  real Body's base shape in FreeCAD's isolated native calculator BEFORE
  `clear_created` or creating any new FeaturePython object / Body Tip.
  Invalid/multi-solid cases or no material change refuse with actionable
  instructions; original document remains intact. Auto/New Body and
  existing-feature editing retain their separate paths.
- `Operation.accept`: validates downstream actual solid shapes, native
  invalid states and explicit feature error strings in the affected Body
  after an upstream Extrude edit, instead of relying solely on
  `State == Invalid`; rejects before transaction commit. Native Cancel
  remains the full rollback for earlier edits.
- `tests/test_workflow.py`: tests constrained native sized-rectangle
  geometry and width/height parameter edits, invalid input; tests complete
  fixture: 60x40x8 plate, 20x16x3 pocket, two through Holes, native Fillet,
  upstream width change, Hole edit Cancel/Accept/Undo/Redo, native FCStd
  save/reopen and parameter/body Tip validation. Separate tests assert
  disconnected Join/Cut preflight leaves document inventory, Tip and volume
  unchanged, and editing upstream Extrude under native Fillet restores
  final Tip and supports Cancel. No native modeled-helix auto-test is run.
- Version/package/readme/release guide now **0.5.0**. Working 0.3.7+
  `Update Az` command supports the one-step update after successful CI.

Verification: [CI run 42450272583](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42450272583)
passed BOTH package and native modeling jobs for core 0.5.0 fixtures,
new sketch dimensions, preflight, and downstream validation. A final
additional upstream-Extrude-under-Fillet edit/Cancel native regression
was added after that run; its latest CI run is 42450344286 (package
passed, native pending at handoff composition). Verify that exact run's
native result, get installer artifact and SHA256 before telling user to
update. No real Windows FreeCAD 1.1 GUI test has been performed.

Scope: 0.5.0 is usable fixture workflow progress, not complete
Fusion 360 parity. Arbitrary feature reorder, universal topological
reference repair, all-feature custom panels and fully draggable
in-canvas dimensions remain unsolved. Sized Rectangle is origin-anchored
and only in empty sketches; normal FreeCAD Rectangle/Dimension commands
remain for other cases. The owner still needs to install via Update Az,
restart and verify visual/UI behavior on Windows.


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


## 2026-11-08 — 0.5.1 exact edge treatments + sketch snap inference

User's `Design.FCStd` had intentionally micro-scale solid geometry; user
explicitly confirmed dimensions must not be rescaled. Report view showed
native Chamfer/Fillet failures, but the saved Fillet may be valid; do not
generalize to all native operations. During work user specified Fusion-like
**automatic** cursor inference: midpoint triangle upon hovering along an
edge and circle center shown immediately upon hovering/clicking its rim,
NOT a standalone manual lookup tool.

Changes on existing `codex/az-design-workbench`, draft PR #1:
- `edge_treatments.py` + `edge_treatments_ui.py`: exact selected native
  edges, radius/size validation via isolated OpenCascade operation on
  a shape (not a document feature); optional kernel-tested smaller
  size suggestion; native `PartDesign::Fillet`/`PartDesign::Chamfer`
  created only in a FreeCAD transaction, abort on invalid recompute.
  Routed from ribbon, canvas and Press/Pull. Never changes dimensions,
  heals geometry or pretends invalid radius is valid.
- `snap_targets.py` + `snap_finder_ui.py`: optional Utilities precision
  tool for exact edge endpoints/midpoints and full circle/arc center XYZ,
  copy and explicitly **fixed/non-associative** construction reference.
  Kept as optional inspection, not a step before sketching.
- `snap_hover.py` + `snap_overlay.py` + `session.py`: passive automatic
  on-hover endpoint square, line-midpoint triangle, circle/arc-center
  marker while native Sketcher is active. Uses real Sketcher geometry and
  activeView world-to-screen projection; Qt overlay does not intercept
  native mouse clicks/constraints. Native Sketcher remains responsible
  for actual snap position on stock FreeCAD.
- Source-level C++ patch
  `native-core/patches/001-freecad-1.1.0-sketcher-circle-center.patch`,
  pinned **FreeCAD/FreeCAD 1.1.0**, changes only
  `src/Mod/Sketcher/Gui/SnapManager.h/.cpp`. Adds optional
  `AzSnapCircleCenter` native parameter (default false), redirects
  snapped curve coordinate to circle center in Sketcher draw operation
  when circle rim is selected, Alt bypass to original rim snap.
  This is **not compiled, installed or used by the workbench updater**.
  5 diff hunks were checked against exact upstream 1.1.0 source lines,
  counts/context and output, but no FreeCAD C++ build yet. Separate
  native app/Windows build is needed; see `native-core/README.md`.

CI source checks: `42453824245` and `42454020125` passed both
package and native modeling jobs after correcting early test assertions.
Native FreeCAD tests cover sub-mm valid Fillet and Chamfer with Undo,
invalid too-thin edge preserving Body, exact line/circle snaps and
Sketcher fixed reference/Undo. Package tests cover midpoint/circle/arc
inference, and a new `test_snap_overlay.py` adds UI stub tests for mouse
transparent placement. Latest run `42454414615` package passed; native
in-progress while documenting. Exact 0.5.1 final artifact SHA and owner
Windows acceptance not yet confirmed. Do not merge draft PR or imply
core patch is live.


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


## 2026-11-08 — First independent native Windows application pipeline

Owner explicitly approved transitioning from the Python-only workbench into
a separately compiled Windows FreeCAD-derived Az Design application.
Existing `codex/az-design-workbench` branch and draft PR #1 remain open
and unmerged; current installed FreeCAD 1.1 is untouched.

Added `.github/workflows/az-native-windows.yml`: on native-core changes,
first checks the C++ Sketcher source patch against the exact upstream
`FreeCAD/FreeCAD` **tag 1.1.0**, then checks out a separate full copy
on `windows-2022`, applies native patch, uses upstream pinned Pixi
`configure-release` / `build-release` / `install-release`, packages a
side-by-side independent portable preview, tests 7z integrity and uploads
the actual compiled application only if the entire build succeeds.
Package is explicitly UNSIGNED EXPERIMENTAL and not a production machine
postprocessor. The native workbench updater is separate and unchanged.

Added `native-core/windows/package_portable.py`: FreeCAD/Sketcher
compiled binaries plus upstream bundled runtime dependencies, user AzDesign
workbench under `Mod/AzDesign`, portable `Az Design.cmd` launcher with
separate profile under `%LOCALAPPDATA%\AzDesign\Native-1.1`, manifest
with actual compiled exe and source patch SHA256, FreeCAD license files,
version/purpose notices. It rejects nonexistent compiled binary or Sketcher,
missing Az workbench, or existing output destination before modifying it.
Added `native-core/windows/test_package_portable.py` with four passing
offline safety tests (no dependencies on FreeCAD or Windows).

First native CI `42487740195`: packaging safety tests passed; strict
`git apply --check` failed because upstream SnapManager.cpp is CRLF.
Adjusted C++ diff to match upstream CRLF, native CI `42487882179`:
Linux source patch verified; on Windows native patch applied but generic
`git diff --check` flagged upstream CRLF as trailing whitespace.
Commit `20a29e69d073d233de23ac7bca0183cba00cd53a` changes the
Windows diff validation to `git -c core.whitespace=cr-at-eol diff --check`,
as appropriate for existing Windows-style upstream C++ source.
Latest native CI run `42488030121` was queued/in-progress when this
handoff was recorded. **There is no confirmed compiled binary or
downloadable native archive yet.** Examine final CI jobs/artifact
before announcing any complete native application.


## 2026-11-09 — Qt platform startup failure on first Windows portable build; verified drop-in fix

Owner screenshot showed FreeCAD-native preview start failure:
`This application failed to start because no Qt platform plugin could be initialized`.
The user's existing system FreeCAD 1.1 and documents were not changed.

**Verified root cause:** artifact from successful Windows native CI
[42488156221](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42488156221)
included `qwindows.dll` **only** at
`lib/qt6/plugins/platforms/qwindows.dll`, while the bundled launcher set
`QT_QPA_PLATFORM_PLUGIN_PATH=bin/platforms`. The prior package check
only asserted compiled FreeCAD.exe and Sketcher existed, not actual Qt
Windows display plugin initialization. Successful C++ compilation
was never sufficient proof of Windows GUI startup.

**Repair committed:** `native-core/windows/qt_runtime.py` detects the
plugin in matching FreeCAD 1.1 Pixi Qt layouts, copies the complete
platform plugin directory to `bin/platforms`, writes actual
`bin/qt.conf`, and optionally checks Windows DLL dependency load;
`package_portable.py` invokes it and refuses to distribute a broken
Qt bundle. Launcher includes `QT_PLUGIN_PATH=bin`.
`native-core/windows/smoke_qt.py` instantiates a *real* PySide6
`QApplication` from the bundled Python and requires
`platformName() == windows`; native CI now requires passing that
before packaging. Safety tests extended for missing plugin and two
Pixi plugin layouts. The new full native Windows CI rerun was in
progress when the repair kit was delivered.

**Small drop-in repair for original 1.3 GB build, no recompilation:**
`native-core/windows/make_qt_fixkit.py` plus dedicated
`.github/workflows/az-native-qt-repair.yml` downloaded the previous
compiled preview, inspected its exact Qt plugin path, relocated the
matching DLL, added qt.conf/launcher, and **PASSED real Windows Qt
startup** with message `Az Qt portable platform: windows`.
[Repair CI run 42560734235](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42560734235)
passed all steps; artifact ID **13648924049**, ~411 KB.
Inner `AzDesign-Native-Qt-QuickFix.zip` **411,824 bytes**,
SHA256 `bf85e6284b5e74b32d482645ccdc991c9d815585917981d61a4f6c5284c85095`,
both inner and outer ZIP CRC passed. Files: `Az Design.cmd`,
`bin/qt.conf`, `bin/platforms/qwindows.dll` (918,528 bytes), README.
Link user to verified container file
`/mnt/data/AzDesign-Native-Qt-QuickFix.zip` (only after verifying
current runtime as done in the repair session), or GitHub repair artifact.
Extract ZIP directly into the existing extracted
`AzDesign-Native-1.1-Windows-x64` root, replacing `Az Design.cmd`.
DO NOT modify stock FreeCAD. User Windows acceptance of full
Az Native GUI and snap behavior remains outstanding.


## 2026-11-09 — Windows installed-app delivery, file-delta updater and UI clipping fix

Owner confirmed original compiled native Az preview successfully **launches**
after the Qt QuickFix and **native circle-rim-to-center C++ snapping works**
on their Windows machine. Owner shared a screenshot showing clipped
`P...h` and `S...s` text in bottom floating navigation/history and
Browser property buttons; asked for Windows-style install/Start Menu/desktop
and **patches** instead of repeat full 1.3 GB downloads.

In `codex/az-design-workbench`, draft PR #1, implemented:
- `native-core/windows/AzDesignLauncher.cs`: compiled GUI
  `AzDesign.exe`, no batch-window navigation; starts our FreeCAD.exe
  with correct Qt plugins and independent app profile.
- `native-core/windows/AzUpdater.cs`: native graphical patch selector
  with rollback action. Independent PowerShell apply process starts after
  updater exits, so app files can be replaced. This first version
  **installs a downloaded small patch ZIP**; automatic online release
  discovery is **not yet wired**.
- `native-core/windows/AzDesignNative.iss`: real per-user Inno Setup
  Windows app in `%LOCALAPPDATA%\Programs\Az Design Native`,
  Start Menu application + updater shortcuts, optional desktop shortcut,
  Windows Installed Apps/uninstall registration. Never touches stock
  FreeCAD or claims .FCStd file associations.
- `native-core/windows/create_patch.py`: creates changed/new files only
  using old and new file SHA256 + deletes, version pins, zip-slip guards.
- `native-core/windows/ApplyAzPatch.ps1`: validates downloaded patch,
  installed baseline, safe paths/hashes; saves full pre-change backup
  under LocalAppData, changes only listed files, rolls back on error,
  provides explicit restore-last-update operation, and refuses if the
  native FreeCAD process is running.
- `native-core/windows/test_create_patch.py` and
  `test_apply_patch.ps1`: Windows CI tested new/changed/deleted
  file patching, version bump, successful rollback and edited-local-file
  mismatch refusal.
- `addons/AzDesign/azdesign/workspace.py`: fixed-size Browser,
  history and viewport buttons explicitly IconOnly (short fallback text)
  with full tooltips; avoids Qt's native Windows style showing clipped
  long names in 32 px buttons.
- `.github/workflows/az-native-installer.yml`: downloads the already
  verified C++ and Qt-compiled preview from run 42561086751, overlays
  latest Az Python workspace, compiles launcher/updater C# GUI EXEs, uses
  Inno Setup 6 to create `AzDesign-Native-Setup-0.5.2-x64.exe`,
  installs it silently on disposable Windows runner, verifies actual
  installed files/Start Menu/updater/uninstaller/Qt QApplication,
  uninstalls test copy and uploads checksum installer only if all steps pass.

Verification: first CI run `42613250797` **patch-tests passed**,
but installer GUI launcher compilation failed because .NET Framework
`csc.exe` treats Unix-style relative slash source paths as incorrect;
modified workflow to pass resolved absolute Windows paths. CI rerun
[42613707498](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42613707498):
both Windows patch tests passed; compiled AzDesign.exe and AzUpdater.exe
successfully; Inno Setup 6 installed, actual setup compression **still
running** at handoff time. Do not announce installer as available until
silent Windows installation/uninstallation and archive artifact have passed.
The new first installer is still a large ONE-TIME download. Subsequent
updates use changed-file ZIPs, but no automatic remote delta index
is published yet.


## 2026-11-09 — Design-first UX and document-routing work (under review)

Owner requested no surprise raw FreeCAD feature panels and simplified visible product naming. Development branch now presents the workbench as **Design**, while retaining AzDesignWorkbench internal identity and Az feature IDs for document compatibility. The main modeling ribbon excludes raw PartDesign Revolve/Loft/Sweep/Shell/Mirror/Pattern/Move/Measure task commands, and the palette hides them. An explicit Native CAD option remains for advanced unfinished features. Native Sketcher drawing tools and FreeCAD's parametric kernel remain intentionally reused; this does **not** mean the application's entire geometry/UI stack is independent of FreeCAD.

`workspace_route.py` installs a FreeCAD document observer without changing the Home screen. A new unsaved ordinary modeling document routes to Design; opened files with a saved filename are left to FreeCAD's native per-document workbench persistence; new CAM/Mesh/TechDraw documents are not hijacked; active editing tasks and inactive documents are excluded. Six new headless workspace-route tests passed in add-on CI 42733420327. First command-boundary CI test detected leftover raw Revolve entry; removed in `e4eb11e`. A subsequent CI run was queued when this record was written, so full package/native Windows validation is NOT yet confirmed.

Pending: Windows interactive acceptance for last-used workbench semantics, file format routing, native plane creation, remaining clipped timeline controls; full Design-owned task panels for advanced features. Preserve draft PR and do not override stock FreeCAD.


## 2026-11-09 — 0.5.3 one-click native updater implementation (under CI)

Owner requests **one Update button inside Design** for native Windows, incremental downloads and rollback. Changes on `codex/az-design-workbench`:
- `commands.update_az_design()` detects the true installed native root from its bundled Python path and starts `AzUpdater.exe`, instead of modifying an unrelated user-app-data FreeCAD module. Standalone add-on installs retain prior add-on update path.
- `AzOnlineUpdates.cs` queries only the official repository's public GitHub latest Release API. It requires exact baseline version, higher semver destination, official HTTPS release-download URL, published non-draft/non-prerelease, SHA256 GitHub asset digest, byte-length and 2GB cap; downloads outside the installation directory and verifies bytes before offering to hand off to existing transactional PowerShell apply. No arbitrary URL update or silent auto-install.
- `AzUpdater.cs` has Check for Updates plus existing manual patch, rollback and explicit save/close consent; uses background worker to keep UI responsive. `.github/workflows/az-native-installer.yml` compiles online updater against .NET Framework System.Web.Extensions; offline release-metadata checks in `test_online_updates.cs`.
- Windows CI changed to create version `0.5.3` from existing known compiled Qt/C++ native runtime. It downloads the actual successfully published **0.5.2** setup from run 42637783444, silently installs it, generates a 0.5.2-to-0.5.3 `.azpatch`, applies it, runs actual Qt startup smoke, rolls back and uploads patch+SHA256 as CI artifact. Full 0.5.3 installer is built separately in same job.
- `.github/workflows/az-native-publish.yml` adds **manual approval/promotion only**, restricted to `main`, exact 0.5.3 and a successful relevant CI run; verifies downloaded patch checksum before publishing GitHub latest Release.

**Not yet done/claimed:** complete 0.5.3 Windows CI and release artifact verification; owner-installed 0.5.2 does not yet include the online updater. First update must be bootstrapped via existing manual `Az Design Native - Update` once the verified .azpatch is available. The public GitHub Release is NOT published; the publisher workflow must be present on the default branch, reviewed and deliberately triggered. Do not merge draft PR #1 or imply working one-click remote updates yet.


## 2026-11-10 — 0.5.4 incremental release pipeline (source committed, CI pending)

Native CI now targets 0.5.4 and generates `AzDesignNative-0.5.3-to-0.5.4.azpatch` from the original verified 0.5.3 Windows installer artifact in run 42752856389 (the 43.5 KiB patch generation, matching owner's installed version), not later 0.5.3 rebuilds. The baseline installer download is SHA256 validated against its original published checksum; application is silently installed on Windows, patched, Qt-smoked, rolled back, uninstalled. CI also builds and tests a native 0.5.4 full installer. Manual GitHub Release promoter is adjusted to 0.5.4 with exact target artifact and existing main-branch approval restriction; no release has been published by these source edits. Includes 0.5.3→0.5.4 update metadata tests. Current source is not evidence of successful Windows build or owner installation.


## 2026-11-10 — Patch-only Windows CI optimization (source committed)

Added `.github/workflows/az-native-patch.yml`: routine pull requests now run a Windows patch-only workflow, **not** the 1.8 GB full installer workflow. It verifies existing online-update policy/delta/rollback tests; downloads ONE pinned original 0.5.3 Windows setup (successful run 42752856389), checks its published SHA256, silently installs the real baseline, and builds a limited overlay of `Mod/AzDesign`, `AzUpdater.exe` and `ApplyAzPatch.ps1`. It compares old/new overlay content using the existing hash-pinned `create_patch.py` to generate `AzDesignNative-0.5.3-to-0.5.4.azpatch`, applies it to the real baseline installation, runs bundled Qt smoke, rolls back, uninstalls, and uploads only small verified patch artifacts. This eliminates the **second** 1+GB FreeCAD core download/extract and the Inno recompaction, full installer test and 1.8GB artifact upload for routine UI changes. Pinned old 0.5.3 installer still costs network/installation time; **do not call this a zero-download or seconds-long CI**.

Changed `.github/workflows/az-native-installer.yml` to manual `workflow_dispatch` only, preserving full native release/install tests for major/core changes. Manual public release promoter `.github/workflows/az-native-publish.yml` now checks the new `Az Native Windows Patch` source workflow before publishing a 0.5.4 patch; unchanged explicit approval/default-branch requirement. First new patch-only run 42818046881 was in progress when this note was written. Neither new patch CI nor public release has yet been confirmed successful.


## 2026-11-10 — Design-owned Home screen and navigation polish (0.5.6 candidate)

Owner installed 0.5.5 successfully; screenshots show Design ribbon icons rendered and native FreeCAD's Start page when launching with no model. Implemented `addons/AzDesign/azdesign/home.py` as a no-document Design welcome overlay with New Design, Open File, and short workflow guidance. `session.py` now displays home instead of eagerly creating an empty FreeCAD document; it hides overlay on model open, resizes it on viewport changes and cleans it up on workspace exit. Native Windows launcher `AzDesignLauncher.cs` sets `AZ_DESIGN_NATIVE_HOME=1` only for a normal Start Menu launch without explicit file arguments; `InitGui.py` uses a guarded delayed Qt callback to activate Design instead of native Part Design Start. Existing `workspace_route.py` still preserves specialized CAM and stored workbenches for reopened documents. Refined navigation icons in `ui.py`/`workspace.py`, differentiating pan, orbit, zoom and camera menus. Bundled Windows `smoke_qt.py` now constructs the Design Home Qt widget and verifies New/Open actions.

To build against owner's 0.5.5, patch-only Windows CI reconstructs the original 0.5.5 installation from SHA256-verified 0.5.4 full setup (run 42809599278) plus verified 0.5.4→0.5.5 delta artifact (run 42819472920) before comparing an allowlisted 0.5.5→0.5.6 delta. Added `AzDesign.exe` native launcher compilation/delta to allowlist. Source committed but **no verified Windows CI result, release or owner acceptance** yet. No current installed 0.5.5 changes. Next: get patch-only CI results; fix any startup/Qt issues, publish only after passing and approved.


## 2026-11-10 — Owner physical-part workflow test exposes sketch and navigation blockers

Owner supplied 2 screenshots and 2 Windows screen recordings (FreeCAD 1.1 Design v0.5.5). Demonstrated: Preferences camera radio controls do not visibly indicate checked selection; viewport top-right Activate/Isolate action strip obstructs navigation cube; cube lacks quick Home; small top ribbon shortcuts were letters rather than pictograms; Create Sketch opens modal XY/XZ/YZ dropdown, preventing face/plane picking; Esc after Ribbon/Sketcher rectangle fails to leave command; Cut/Extrude task remains open without usable source on first sketch. The recordings show an EXTRUDE task set to Cut and 0 selected profiles although the model contains a sketch.

Code committed (not yet owner/Windows GUI validated): `sketch_plane_picker.py` replaces the modal plane dropdown with an in-canvas nonmodal XY/XZ/YZ choice and FreeCAD SelectionObserver for planar model faces; `modeling.create_sketch` defers actual feature creation until selection; `session.InteractionFilter` cancels picker on Esc and forwards Esc to visible native 3D viewport when sketch mode is active and focus was stolen by ribbon; `tasks.show_extrude` selects the only valid unused closed sketch when unambiguous and gives actionable error on first-solid Cut; `canvas_actions.refresh` hides obstructive Activate/Isolate strip while Browser context menus remain; `Navigation` provides separate Home control beside native cube and session cleans it on deactivation; `ui.design_icon` draws New/Save/Undo/Redo/Search/Help instead of text; `session` applies selected-state indicator style only to native Preferences QRadioButton widgets. Added Python compileall gate to fast patch CI. All changes are **source-only** until real Windows CI and owner GUI testing pass. Native FreeCAD 1.1 has documented Sketcher Esc focus problems (#14634) and continuous rectangle behavior (#23868); proper runtime test is essential. Continue preserving stock FreeCAD and parametric FCStd files.


## 2026-11-10 — Owner real-part modeling: sketch dimensions, Move, Hole, edge projection, Mirror/Pattern

Owner supplied sketch screenshot with heavily overlapping red 45 mm, 13.5 mm, 5 mm and reference annotation text and a Sketcher status showing 2 degrees of freedom remaining; requested usable solid Move, face-first Hole, edge-based sketch/dimension references, and working Mirror/Pattern. Root cause for disabled Sketch Project button was found in the actual FreeCAD 1.1 command registry: native command is `Sketcher_Projection`, not deprecated `Sketcher_External`. Updated catalog to use the registered 1.1 command, allowing external solid edges/faces to become parametric sketch references. `modeling.create_sketch` now infers the unique planar adjacent face from a selected edge (if unambiguous) instead of refusing immediately. Added Sketch `Show / Hide Labels` action via native `Sketcher_SwitchVirtualSpace` with selection cleared first; hiding annotations is presentation-only, does not alter solver or dimensional values. Dimensional label collision still needs proper Windows GUI acceptance and more advanced automatic label organization.

Added `azdesign/move_body.py` for transaction-safe X/Y/Z placement of an entire Body/component, preserving rotation and Undo; installed `Az_Move` in visible Solid Modify ribbon. Hole now prominent in Solid Create; a selected planar solid face opens a new attached native hole-center sketch and starts Circle placement, with Finish Sketch/native Close continuing into native Hole settings; an initially unselected Hole action shows a nonmodal click-face picker. Mirror and Linear Pattern now Design-owned commands in Solid Modify More (not blocked raw PartDesign tasks) backed by native parametric `PartDesign::Mirrored`/`PartDesign::LinearPattern`, selected-feature and origin-plane/axis inputs, recomputation validity guard, native transaction, rollback on error; first pass includes only one feature, origin references and simple 1D pattern; more advanced surface selection/2D patterns deferred. Updated command whitelist regression and new `test_native_transform_contracts.py` to verify transform creation/rollback; registered in add-on CI. All source changes committed to `codex/az-design-workbench`. **NO confirmed current Windows CI run or owner-installed patch.** 0.5.6 remains a candidate, not a release.


## 2026-11-10 — Real user 0.5.6 launch, 0.5.7 corrective candidate 2

Owner's video confirms 0.5.6 installed, but native Home delayed Qt callback fails with `NameError: _az_App is not defined` after ephemeral FreeCAD `InitGui.py` globals were discarded. Also owner wants no stock FreeCAD splash or start-page before Design; and cannot pattern one sketch circle into four bolt holes. In branch `codex/az-design-workbench`: bound callback dependencies in default parameters and tested namespace clearing, shortened to 250ms; Design native profile uses `General/ShowSplasher = false` without affecting stock FreeCAD. To suppress splash on **first** updated launch, `AzDesignLauncher.cs` now safely ensures the dedicated `user.cfg` value before `FreeCAD.exe` starts, using XML-preserving atomic replace and backup. Malformed preferences do not block CAD launch. Windows test `native-core/windows/test_launcher_profile.cs` verifies fresh profile, existing custom preferences, backup/idempotence and malformed config; 0.5.7 patch and installer workflows compile with System.Xml.dll and candidate runs this test.

Added native `azdesign/sketch_pattern.py` and Sketch ribbon `Rectangular Pattern`: choose one real circle, default 2x2 with editable X/Y spacing, add 3 copies bound to source circle via Sketcher Equal radius and driving center distance constraints, transactional rollback on errors. Native engine test in `test_workflow.py` patterns a 2x2 hole-center array on an 80×60×8 solid, changes source diameter, and verifies one native Hole cuts four valid holes. Also validates overlap/nonzero spacing errors. New native Windows patch workflow reconstructs v0.5.6 from verified pinned older artifacts, tests actual 0.5.6→0.5.7 apply/Qt/rollback, and is gated on real Linux FreeCAD geometry plus Windows package and launcher tests. **No 0.5.7 owner install or verified completed release yet**; after latest source change, the prior candidate request is stale and needs new marker submission. Stock FreeCAD executable/profile is unaffected.


## 2026-11-10 — v0.5.7 GitHub workflow incident: resolved configuration, live acceptance in progress

Owner reported workflows showing errors and stuck. Browser GitHub Actions view showed #21–#35 failed instantly with no jobs. Root cause was a malformed .github/workflows/az-native-patch.yml caused by source-editing an incomplete PowerShell block; truncated SHA256 check, duplicated build steps/tail, and incorrect candidate trigger path remained. Fixed by rebuilding one contiguous 0.5.6 baseline reconstruction and patch build, requiring exactly one each of geometry, Windows patch, reconstruction and upload steps; corrected 0.5.7 marker path, System.Xml launcher compile reference, and installed baseline error wording. Commit `27569ea33f04685077d88b08d095d9883bb2e803`. Submitted 0.5.7 candidate #3 marker commit `1e9c172bb5fe1f7e38306e4238e8f7832842b10b`.

**Confirmed via GitHub API:** new [Az Native Windows Patch #36](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42899554668) was accepted and running; native FreeCAD `geometry` job completed **successfully** (including 2×2 four-hole test), Windows `patch` job running and currently installing pinned 0.5.4 baseline. At this checkpoint Windows output is NOT yet a verified patch, no 0.5.7 release published, owner's installed 0.5.6 untouched. Do not claim full release ready until Windows package/apply/rollback completes. **Process improvement:** add a lightweight actionlint/YAML structure check to fast CI in a *separate validated batch* to prevent rejected workflows. Avoid changing the running candidate SHA.

## 2026-11-10 — Fusion Pattern and image-only history batch

Implemented on codex/az-design-workbench: Sketch Rectangular Pattern is now an in-canvas Design-owned panel with two-axis controls, actual solver-native circle preview in one open transaction, Apply, Cancel and Esc rollback. Solid Linear Pattern is now directly visible under Solid MODIFY, has native Body feature selection from canvas, Browser or dropdown, spacing/extent, origin axes, an optional second grid direction and in-canvas drag handles. Its PatternDraft engine previews a real native PartDesign::LinearPattern in an open transaction; edits from history route back to Design, not FreeCAD's native task editor. Native enum names vary across FreeCAD builds, so engine resolves valid feature/extent modes at runtime. It keeps native FCStd history and refuses invalid shapes.

The bottom Feature History now uses locally owned SVG image icons rather than text abbreviations for Sketch, Pad, Pocket, Hole, Fillet, Chamfer, Pattern, Mirror and other features, plus compact icon-only Edit, Delete, Resume and Settings. Feature names remain in tooltips and accessible labels.

CI: Az Design add-on run 42928162310 (#407) on b1b602ccc2884de83df6bcafc6e5646938e71fda: package SUCCESS, modeling SUCCESS. New tests test_timeline_icons.py, test_pattern_ui_contracts.py and native Hole-to-Pattern regression are wired to CI. Optional 2-axis Solid Pattern is available only where native FreeCAD exposes Direction2/Occurrences2/Length2; older Debian build does not, so real owner Windows 1.1 two-axis verification remains mandatory. This is not yet a released Windows update.

## 2026-11-10 — CI cycle optimization

Windows candidate #37 (run 42928685669) completed SUCCESS with two jobs, real FreeCAD geometry and Windows patch/install/Qt/rollback, and produced the AzDesignNative-0.5.6-to-0.5.7-PATCH artifact. Detailed times: patch job ~8m09, 0.5.4 artifact download ~3m55, real installer ~3m12; these repeated old-baseline steps dominate.

Implemented on branch codex/az-design-workbench:
- Fast source CI concurrency cancel-in-progress true, so intermediate commits no longer pile up redundant jobs.
- Windows patch workflow exact-key installed 0.5.6 snapshot cache, source pinned to immutable #0.5.4 setup/0.5.5 patch/0.5.6 patch runs, with required file and SHA256 manifest validation, cache-miss fallback and fail-open *only for cache transport/save* (not model validation); cache saved before modifying baseline.
- Cached baseline cannot prove uninstaller registry behavior, so full cold verification via workflow_dispatch cold_validation=true still checks real installation and uninstall. Cache hit continues real patch/Qt/rollback verification.
- Cheap structural YAML workflow validator in tools/verify_native_workflows.py added to package CI, catching prior malformed workflow errors (including unquoted # in step name); fast CI triggers on validator and release workflow edits.

Not yet measured: whether restoring the multi-GB Windows baseline is faster than re-downloading/reinstalling on an actual cache hit. Cache is not primed just by committing these changes; the next batch candidate must populate it. No local Windows installation or published release changed.

## 2026-11-10 — v0.5.8 baseline correction

Discovered user already has v0.5.7, so old 0.5.6→0.5.7 patch rejected correctly. Retargeted Windows patch workflow to v0.5.7→v0.5.8 from checksum-verified original build #36 baseline; all old file checksum protections remain. Changed batch marker path to v0.5.8 and manual release workflow to v0.5.8, and updated fast YAML gate to reject incorrect version/source. Source implementation carries forward the Fusion-style sketch/solid Pattern improvements and vector timeline. Important same-version fork: #36 and #37 are different 0.5.7 test packages, so build lineage must be verified on user's PC. No 0.5.8 installed or publicly published.

## 2026-11-10 — v0.5.8 officially published for the in-app Update button

Owner screenshot showed 0.5.7 Check for Updates saying "No compatible verified patch is published". Diagnosis: current installed AzOnlineUpdates.Find() only reads public https://api.github.com/repos/Mr-Azrack/FreeCAD-Az/releases/latest and selects a non-draft/non-prerelease named AzDesignNative-{installed}-to-{new}.azpatch with GitHub SHA256 asset digest. Windows CI run #39 (42949194221), source 56bfacadf8a197b49fda8e510ccc55c9fd65b3ec, had passed geometry and Windows patch tests and created 0.5.7→0.5.8 artifact but no GitHub Release; latest public release was v0.5.5.

FIX COMPLETED: On main, updated .github/workflows/az-native-publish.yml to exact-version/sha-protected 0.5.8 release. Added one-time .github/release-requests/native-0.5.8.txt marker, commit 77b5c438a6181aec42e28fea4ca658af497c039e. Publication Actions run 42952761200 succeeded. Independently fetched public GitHub releases/latest: tag v0.5.8, draft=false, prerelease=false, asset AzDesignNative-0.5.7-to-0.5.8.azpatch (406048 bytes), SHA256 digest d4a5a9244049edda3ecf1be8b43e729bcdfd520b83f9153ee898f587e7e00c78, browser URL https://github.com/Mr-Azrack/FreeCAD-Az/releases/download/v0.5.8/AzDesignNative-0.5.7-to-0.5.8.azpatch. Release page https://github.com/Mr-Azrack/FreeCAD-Az/releases/tag/v0.5.8. It should now be discoverable by the existing 0.5.7 in-app Check for Updates, WITHOUT manual ZIP handling. No local install was remotely performed. The patch is based on original 0.5.7 Build #36; if owner's installed 0.5.7 is the different Build #37, hash verification will refuse application. Never bypass it; reconstruct the appropriate installed baseline for that alternate build if necessary. Future versions MUST be unique and publisher must be updated/triggered, not just CI-built. Verify owner GUI acceptance after install.


## 2026-11-10 — Implemented Fusion-video interaction gap fixes

Full owner source recordings are the benchmark, not screenshots alone. See FUSION_FREECAD_VIDEO_GAP_REVIEW.md for timestamped Fusion (~3:43) vs Design (~13:06) comparisons. Implemented on codex/az-design-workbench:
- profiles.preferred_plate_region + ExtrudeTask.source_changed: select an unambiguous dominant plate region with existing hole wires by default, show human-readable plate/cutouts label, preserve all holes; ambiguous profiles stay unchecked.
- sketch_plane_picker.py: if a model already has a solid Body Tip, keep face-selection observer active but hide overlarge face/plane chooser; next planar face click runs create_sketch(support=(obj,[FaceN])); Esc still cancels. Empty designs retain plane buttons.
- sketch_pattern_ui.py: source circle follows selected Sketcher EdgeN while live Design Pattern panel is open; observer removed on cancel/accept.
- edge_treatments_canvas.py: nonmodal Design-owned Fillet/Chamfer canvas edge selection even if no edges selected before the command. Kernel preflight after radius/distance edits, Apply only after valid shape, Esc leaves original model unchanged, and existing parametric features edit via timeline using native transactions and native recompute/Undo. Currently kernel preflight provides validity text and highlighted selected edges, NOT shaded ghost mesh preview.
- commands/session/feature_edit route these interactions through Design and cleanup.
- Tests: test_fusion_video_workflows.py on fast/package and Windows preflight; test_workflow.py native 65x100 perforated plate region-to-extrude with 8 holes, ambiguous region guard, finished Fillet radius edit/undo. Az Design add-on run #433, 42958378856, package+modeling SUCCESS on source 709e5dfe2c7c598494e9f02283bef384228bc962.
- .github/workflows/az-native-patch.yml and tools/verify_native_workflows.py retargeted to build 0.5.8-to-0.5.9 from exact public 0.5.8 Build #39 run 42949194221, verifying SHA256 after reconstructing original 0.5.7 Build #36. Existing user install and public 0.5.8 remain unchanged. No Windows 0.5.9 verification yet.


## 2026-11-10 — v0.5.9 published for Fusion-video workflow acceptance

Verified evidence: guarded Windows candidate Build #40 (run 42959009956) completed both geometry SUCCESS and patch SUCCESS, with AzDesignNative-0.5.8-to-0.5.9-PATCH. Baseline reconstructed from hash-verified original 0.5.7 Build #36 and PUBLIC 0.5.8 Build #39. Native Windows patch install, Qt startup and rollback to 0.5.8 passed. Candidate source SHA 89cd91ba4e15381950db1543873320e90a0b80f0.

On main, v0.5.9 publishing marker committed at e72130698043e88f46717fc7416ea25439228164. Release run 42959518279 SUCCESS. Public GitHub releases/latest independently confirmed tag v0.5.9, draft=false, prerelease=false. Assets contain exact prior 0.5.7-to-0.5.8 patch plus new AzDesignNative-0.5.8-to-0.5.9.azpatch (GitHub SHA256 digest 0d87c754c04dc65f530613e3cdbc71e9d60e2926c9990770345f866adfee5cdc), with both checksum files. Release: https://github.com/Mr-Azrack/FreeCAD-Az/releases/tag/v0.5.9. Existing updater reads latest release and selects patch from current installed version: 0.5.7 can update to 0.5.8 and repeat; 0.5.8 to 0.5.9 directly.

Owner GUI still unverified: source circle picking while Sketch Pattern open; auto-selecting perforated plate region with holes; hiding large face chooser over existing body; nonmodal edge selection and Fillet edit/undo. Automated native geometry/Qt startup is not Windows UI acceptance. Fillet auto-validates the actual OCCT result but does NOT show a shaded ghost-result preview. Do not claim full Fusion behavior parity; retain rollback and unique versioning.

## 2026-11-13 — FreeCAD-Az 0.5.12 Windows candidate

The 101,114-byte 0.5.11-to-0.5.12 patch from source commit `5f87fda` was validated on a disposable copy of the installed 0.5.11 on LAPTOP-O8QBOF2P. All 29 payload checksums passed, along with 205 Windows native tests and the live Qt Design Home and independent sketch-pattern history workflows. Rollback matched 29,351 of 29,363 original files byte-for-byte. Twelve add-on Python cache files were regenerated during GUI launch and the validation script added one standard-library cache. All patch targets and the 0.5.11 version marker were restored exactly. The production installation and shared rollback state were preserved. The candidate remains private. See SESSION_HANDOFF.md for its SHA-256, artifact location, and remaining acceptance checks.
