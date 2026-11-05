# FreeCAD-Az — project state

**Last verified by repository inspection:** 2026-11-05
**Repository:** https://github.com/Mr-Azrack/FreeCAD-Az
**Development branch at inspection:** codex/az-design-workbench
**Starting HEAD at inspection:** dac67fee9cebb9cb7e342a45098fd913510f10f6
**Review:** https://github.com/Mr-Azrack/FreeCAD-Az/pull/1 (draft)
**Status:** Az Design v0.1 implemented on a feature branch; not a completed Fusion 360-equivalent CAD environment.

## Objective

Build a practical, professional, familiar CAD experience comparable in *workflow* to Fusion 360 while keeping FreeCAD's parametric engine, native editable documents, and open-source independence. User has explicitly requested that we pursue the full objective rather than presenting a minimal cosmetic mockup as the end state. Incremental verified releases are still required.

## Repository-observed implementation

- Optional installable Az Design workbench lives in addons/AzDesign; it does not yet require modifications to the FreeCAD C++ core.
- The implemented interface includes Solid/Sketch/Utilities grouped ribbon, familiar command names/shortcuts, left Browser and right Tasks, searchable commands, and bottom creation-order feature history.
- Sketch-to-solid workflow: create sketch; rectangle/circle; native Pad (Extrude) with live preview; native Pocket (Cut) with live preview; available native tools for fillet, chamfer, and other operations.
- Native operations use document transactions; Undo/Redo and cancellation restoration are covered by recorded integration checks.
- Installer: addons/Install_AzDesign.FCMacro, installation/backup logic, and addons/releases/AzDesign-0.1.0.zip.
- CI workflow: .github/workflows/az-design.yml; tests and packaging commands are described in addons/AzDesign/README.md.

## Evidence and qualification

- addons/AzDesign/tests/validation-linux-freecad-1.0.json **records** 30 checks passing in FreeCAD 1.0.0 on Linux / Qt5 / PySide2; it includes geometry, previews, Undo/Redo, cancel behavior, layout and navigation, and FCStd reopen behavior.
- Draft PR #1 additionally **reports** four installer tests, compilation/style/package checks, and a manual end-to-end sketch/extrude flow.
- These are results recorded by the earlier implementation, **not tests independently rerun by the session establishing this documentation**.
- Windows, macOS, and FreeCAD 1.1 remain unverified by the available records.

## Known limitations — do not misstate as complete

- Profile extrusion works from whole closed sketches, not independently selectable sketch regions.
- Feature history is selection/edit UI, not Fusion-like rollback/reorder timeline.
- Press/Pull face offset, assembly redesign, and CAM UI parity are not implemented.
- Extrude keyboard alias Q does not yet constitute a true Press/Pull operation.
- Some advanced modeling tools still open native FreeCAD dialogs; there is no evidence of broad workflow parity.
- One connected solid per Body is the current supported path.

## Change protocol

The actual branch HEAD and working tree override this document if they disagree. Update this page only after checking the implementation and test evidence. See AGENTS.md and SESSION_HANDOFF.md.
