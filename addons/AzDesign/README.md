# Az Design

A Fusion-inspired modeling workbench for **FreeCAD-Az**, installable in standard
FreeCAD without compiling the application. Independent of Autodesk; it uses
FreeCAD's geometry engine, native commands and native document format.

## Install

1. Download the **AzDesign-0.1.0.zip** package and extract it.
2. In FreeCAD, choose **Macro → Macros…**. Set the macro location to the extracted
   folder, select **Install_AzDesign**, and choose **Execute**.
3. Confirm the installation, restart FreeCAD, and select **Az Design** from the
   workbench selector.

The installer runs locally, needs no administrator rights, and backs up an
existing installation before replacing it. Backups live in `AzDesign-backups`
beside FreeCAD's `Mod` folder, so FreeCAD will not load a second copy.

For manual installation, copy the **AzDesign** folder into the `Mod` folder
inside FreeCAD's user data directory, then restart. The exact directory can be
printed in FreeCAD's Python console with `App.getUserAppDataDir()`.

## First part

1. **Create Sketch**. Choose XY, XZ or YZ, or select a flat solid face first.
2. Draw a closed rectangle or circle, add dimensions, then **Finish Sketch**.
3. **Extrude**, enter a distance such as `6 mm` or `1/4 in`, and choose **OK**.
4. Select a face, make another sketch, finish it and choose **Cut**.
5. Select solid edges to apply **Fillet** or **Chamfer**.

Extrude and Cut have live previews. Cancel discards the entire preview; accepting
creates a native `PartDesign::Pad` or `PartDesign::Pocket`. Each operation is one
undoable document transaction. A part saved as `.FCStd` remains editable without
Az Design installed.

## Interface

- **Solid / Sketch / Utilities ribbon:** grouped tools with familiar names.
- **Browser on the left, Tasks on the right:** native FreeCAD trees, properties
  and editing dialogs.
- **Feature history along the bottom:** click to select, double-click to edit,
  right-click for rename and visibility. This is a creation-order feature list,
  not a rollback or drag-to-reorder timeline.
- **S:** search tools by familiar name or their FreeCAD command ID.
- **Mouse:** middle button pans, Shift + middle button orbits, wheel zooms.
  Native Fusion navigation is used when available; otherwise Az temporarily
  adapts FreeCAD's Blender navigation while this workbench is active.
- **Utilities → Native CAD:** return to Part Design and restore the prior dock,
  toolbar and camera-navigation setup. **Manufacture** opens the installed CAM
  workbench.

Shortcuts apply in the modeling workspace, not while typing in text fields,
task controls, the Python console or modal dialogs. Existing FreeCAD shortcuts
are not rewritten.

| Context | Shortcuts |
| --- | --- |
| Solid | E / Q Extrude; F Fillet; H Hole; M Move; S Find a Tool |
| Sketch | L Line; R Rectangle; C Circle; D Distance; T Trim; P Project; X Construction; S Find a Tool |

## Current scope

Version 0.1 provides the interface and a practical sketch-to-solid workflow.
It uses whole closed sketches as extrusion profiles and supports a single
connected solid per Body. Choosing individual sketch regions, a Fusion-style
Press/Pull face offset, feature rollback/reordering, assembly redesign and CAM
interface changes are not implemented. Q currently opens Extrude. D is a
distance constraint; circle diameters are in the Constraints menu. Fillet,
Revolve, Shell and the remaining native tools still use FreeCAD task dialogs.

Verified in **FreeCAD 1.0.0 on Linux with Qt 5 / PySide2**. The binding adapter
also supports PySide6, but Windows, macOS and FreeCAD 1.1 have not been tested.

## Improve it

All new work lives in `addons/AzDesign` in **Mr-Azrack/FreeCAD-Az**.
No changes to FreeCAD's C++ core are required for this version.

| File | Responsibility |
| --- | --- |
| `azdesign/catalog.py` | Tool labels, ribbon groups and shortcut maps |
| `azdesign/ui.py` | Ribbon, command palette and feature history |
| `azdesign/modeling.py` | Body/sketch workflow, native feature previews and transactions |
| `azdesign/session.py` | Temporary layout, input routing and restoration |
| `azdesign/commands.py` | FreeCAD command registration and adapters |
| `azdesign/install.py` | Local installer and backup behavior |

Run `python3 addons/AzDesign/tests/test_install.py` for installer regression tests.
Run `python3 tools/package_azdesign.py` from the repository root to build a ZIP.
The package does not require a full FreeCAD source build.

For the geometry and UI integration checks, load the workbench in FreeCAD, then
run this in **View → Panels → Python console**, substituting local paths:

```python
import runpy
suite = runpy.run_path('/path/to/AzDesign/tests/integration.py')
suite['run']('/path/to/results.json', '/path/to/test_plate.FCStd')
```

The checks exercise exact extrusion and cut volumes, unit conversion, input
rejection, Undo/Redo, Cancel restoration, sketch editing without a workbench
jump, repeated activation, layout/navigation cleanup and native file reopening.
They create a separate test document and leave it open for visual inspection.

## License and provenance

New code is LGPL-2.1-or-later, compatible with the parent project. FreeCAD icons
are accessed from the installed application; Autodesk code, icons and artwork
are not included. This work was produced with OpenAI Codex assistance for the
FreeCAD-Az fork and requires owner review before any upstream submission.
