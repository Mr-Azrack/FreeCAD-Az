# FreeCAD-Az — project state

**Inspected:** 2026-11-05
**Repository:** https://github.com/Mr-Azrack/FreeCAD-Az
**Development branch:** codex/az-design-workbench
**Implementation baseline reviewed:** dac67fee9cebb9cb7e342a45098fd913510f10f6 (Az Design 0.2)
**Draft PR:** https://github.com/Mr-Azrack/FreeCAD-Az/pull/1
**Status:** Az Design 0.2 implemented on the feature branch; production Windows validation and comprehensive workflow parity remain outstanding.

## Objective

Build an independently maintainable FreeCAD-based CAD workflow approaching Fusion 360 for real shop use, rather than a superficial UI skin. User direction is to pursue the complete workflow goal while shipping evidence-backed, recoverable milestones.

## Observed code in Az Design 0.2

- Installable add-on in addons/AzDesign with packaged addons/releases/AzDesign-0.2.0.zip and local installer with backup.
- Solid/Sketch/Utilities ribbon, native Browser/Tasks arrangement, shortcuts, search, camera/navigation handling and bottom feature history.
- Sketches with separately selectable exact planar regions (including nested/overlapping/divided profiles), live extrude/cut/intersect/join/new body previews, distance handles, signed distances, symmetric/two-sided extents, taper, offsets, Through all and To face.
- Press/Pull for supported extrusion end caps, some prismatic faces, source sketch circles, and supported native cylinder/hole dimensions. Unsupported ambiguous geometry reports an error instead of silently changing the wrong feature.
- Native expression-based user parameters using a Parameters spreadsheet; geometric edits and their cancellations.
- Real Body Tip rollback, suppression and insertion for supported feature histories; reversible native transactions, mixed native/Az operations and saved geometric references.
- v0.2 Az custom parametric features use FreeCAD Pad/Pocket and OCCT evaluation, and require Az Design present for editing/recomputation. Cached geometry is preserved in saved FCStd; v0.1 native Pad/Pocket features remain native without migration.

## Test evidence in repository (not newly rerun here)

- addons/AzDesign/tests/validation-v02-linux.json records **26 passing modeling tests**, **4 passing installer tests**, passing v0.2 GUI workflow checks, passing original 30-item navigation/native workflow checks, and a recorded manual mouse-drag diagnostic.
- Environment evidenced: FreeCAD 1.0.0, Linux / Qt5 / PySide2.
- The current documentation session inspected these records and code changes but **did not independently execute FreeCAD or validate the Windows installation**.
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
