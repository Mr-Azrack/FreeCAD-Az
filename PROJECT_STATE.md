# FreeCAD-Az — project state

**Inspected:** 2026-11-05
**Repository:** https://github.com/Mr-Azrack/FreeCAD-Az
**Development branch:** codex/az-design-workbench
**Implementation baseline reviewed:** dac67fee9cebb9cb7e342a45098fd913510f10f6 (Az Design 0.2)
**Draft PR:** https://github.com/Mr-Azrack/FreeCAD-Az/pull/1
**Status:** Az Design 0.2.1 startup hotfix implemented on the feature branch; production Windows validation and comprehensive workflow parity remain outstanding.

## Objective

Build an independently maintainable FreeCAD-based CAD workflow approaching Fusion 360 for real shop use, rather than a superficial UI skin. User direction is to pursue the complete workflow goal while shipping evidence-backed, recoverable milestones.

## Observed code in Az Design 0.2

- Installable add-on in addons/AzDesign with packaged addons/releases/AzDesign-0.2.1.zip and local installer with backup.
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
