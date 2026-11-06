# FreeCAD-Az — project state

**Inspected:** 2026-11-06
**Repository:** https://github.com/Mr-Azrack/FreeCAD-Az
**Development branch:** codex/az-design-workbench
**Implementation baseline reviewed:** dac67fee9cebb9cb7e342a45098fd913510f10f6 (Az Design 0.2)
**Draft PR:** https://github.com/Mr-Azrack/FreeCAD-Az/pull/1
**Status:** Az Design 0.3.2 Hole stabilization review build in development; native FreeCAD 1.0 and offline Hole tests passed, Windows/1.1 GUI acceptance outstanding. The checked-in installer ZIP remains 0.3.1.

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
