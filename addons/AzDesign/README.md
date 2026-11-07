# Az Design 0.4.1

## 0.4.1 — Sketch Palette layout and control repair

Windows FreeCAD 1.1 user screenshot of 0.4.0 revealed a **blocking UI
regression**: an overly tall right Sketch Palette pushed native Tasks and the
history timeline off-screen, repeated drawing and Finish Sketch buttons already
available in the ribbon, inherited dark-theme styles yielded unreadable
labels, and checkboxes for `SnapToGrid`, `ShowConstraints`,
`ShowDimensions` and `ShowProfiles` were not real Sketcher ViewObject
settings. This panel did **not** resemble a compact Fusion Sketch Palette.
The 0.4.1 patch replaces it rather than further decorating those controls.

The right-hand Sketch Palette is now **settings only**, with a maximum dock
height of 210 px, 215 px minimum width, explicit high-contrast widget and
checkbox styles, no duplicate sketch tools or Finish Sketch, and a larger
remaining native Sketcher Tasks/solver area. Native task dock is labeled
"Sketch Tasks"; bottom timeline returns to a smaller footprint.

Controls now use only genuine native FreeCAD settings:
- **Show grid**: Az session's grid control, synchronized to native
  `ViewObject.ShowGrid` on the active sketch.
- **Auto grid spacing**: `ViewObject.GridAuto` when available.
- **Auto constraints**: `ViewObject.Autoconstraints` when available.
- **Avoid redundant constraints**: `ViewObject.AvoidRedundant` when
  available.
- **Snap while drawing**: the native `Sketcher_Snap` checkable GUI action
  **only** when present in that FreeCAD build, never a fictional
  `ViewObject.SnapToGrid`. Its effect is visible while *drawing new geometry*,
  not while selecting existing entities.

Unsupported options are **hidden**, not displayed as inert checkboxes.
Display-only options such as Show Profiles and separately Show Dimensions are
**not offered** until verified native APIs exist and are implemented.
No Sketcher solver or underlying model data is replaced by custom code.

The package CI includes a headless UI wiring regression that exercises native
property mutations, checked snap actions, unsupported controls and compact
height. Real Windows theme/DPI/screensize behavior is still subject to owner
acceptance. Upgrade through the existing **Update Az** command and fully
restart FreeCAD after installing the tested 0.4.1 build.

## 0.4.0 — consolidated design-workflow preview

This release brings six previously proposed UX areas together in one build.
It is a **Fusion-inspired FreeCAD workbench**, not a claim of full Fusion
feature parity. All model solids remain FreeCAD-native.

1. **Timeline:** discrete draggable history slider rolls the active Body Tip
   back on release, shows current position and restores latest history;
   right-click reports actual incoming dependency links. Existing feature
   Edit/Delete/Undo and dependency guards are retained. Sliding does **not**
   reorder the dependency graph.
2. **Sketch Palette:** persistent right-side Az sketch panel while editing,
   with native Grid, Snap, Constraints, Dimensions and Profile display toggles
   *when the installed Sketcher exposes those properties*. Unsupported
   toggles are disabled instead of guessing; native dimension, construction,
   projection, drawing tools and Finish Sketch remain wired to Sketcher.
   Native Tasks still owns constraint solving and advanced sketch controls.
3. **Feature editing:** one edit router shared by the timeline, Browser and
   canvas. Az Extrude and Hole keep their transactional panels. Other native
   PartDesign features open native FreeCAD task editors, visually integrated
   into the Az right-side Tasks area.
4. **Canvas context:** selection-aware floating actions for sketch, face,
   edge and feature selections. Right-click on selected geometry exposes
   relevant native commands; right-click empty canvas retains the Az radial
   menu. A guarded Quick Dimension dialog edits native Pad/Pocket lengths,
   Fillet radius, Chamfer size and Az Extrude lengths with recompute and Undo,
   rejecting newly invalid downstream features. Actual Hole/threads always
   use the dedicated editor and diagnostics, never Quick Dimension.
5. **Browser:** Body-first nested native features and sketches in real
   Body.Group order, separate unassigned geometry, active Body indicator,
   suppression labels, selection/visibility/isolate and Native Properties.
6. **Look and feel:** consistent compact ribbon hints, scrubber/selection
   highlights, task inputs, right-side sketch/task docks, and persistent
   in-canvas controls. FreeCAD's native solver and workbench layout are
   restored on exit.

**What is not safe to promise yet:** arbitrary feature drag-reordering,
automatically fixing broken topological references, custom Az UI for every
FreeCAD feature (native dialogs remain), or arbitrary face dimension dragging.
Those require focused graph/geometry safety work and real Windows GUI tests;
none are silently simulated.

**Update without downloading:** From Az Design 0.3.7 click **Update Az**.
When the new 0.4.0 CI run passes, the updater should show 0.4.0; confirm,
install and fully restart FreeCAD. Prior versions are backed up. If the
update checker reports 0.3.7, the new build may still be awaiting successful
CI validation; do not replace it from an untested branch HEAD.

## One-click in-app updates — 0.3.7

After installing 0.3.7 **one final time** from the GitHub Actions artifact,
look for the **Update Az** button on the top ribbon, or use
**File → Check for Az Design updates…** or **Utilities → Update Az Design**.

The update dialog checks for the **latest successful Az Design pull-request
CI run on `codex/az-design-workbench`**, not an arbitrary untested GitHub
branch HEAD. It displays the current and tested versions and requires
confirmation before downloading. GitHub source files are pinned to the
successful source commit and checked against their individual Git blob hashes
before installation. Az stages all files, then uses its existing tested
backup-aware installer, preserving the previous version under
`AzDesign-backups` in the FreeCAD user folder. Failed/incomplete downloads
leave the installation unchanged. A cancelled download does not modify it.

Because the GitHub repository is **public**, this updater needs neither a
GitHub personal access token nor Git/CLI tools on the Windows computer.
It uses HTTPS to the public GitHub REST API and raw content service. Network
access is required. API throttling or network restrictions are reported rather
than silently installing untested bytes.

**After each in-app update, close ALL FreeCAD windows and fully restart the
application** to activate the new Python code. Save any open CAD documents
before restarting. This is manual one-click update, not background auto-update
or hot-swapping an active workbench. The GitHub branch remains a **draft**
development source and is not the main-branch official FreeCAD release.

## Timeline editing and deletion — 0.3.6

The bottom design timeline now has explicit **Edit** and **Delete** buttons for
its selected feature. Double-click a feature to edit it; right-click offers
**Edit feature**, **Delete feature…**, **Delete from here…**, **Roll back here**
and other existing options. Press Delete while focused on a feature tile to
open a confirmation. The Az Browser also opens the native FreeCAD edit task
for native Pad/Pocket/Fillet features rather than just the Properties dock.

Delete feature removes one step **only when no other live object references
it**; otherwise it refuses with the dependent name and offers an explicit
Delete from here alternative. Delete from here lists the following solid
features/sketches in that one Body and requires a confirmation; deleting
steps referenced by other bodies or unscheduled objects is blocked. All
deletions are committed as native FreeCAD transactions and can be undone.
Neither command silently reorders features or rewires unknown topology.

Earlier native Hole features can now be edited from the timeline even when
later features exist. Az temporarily previews the older Hole, then restores
the original Body Tip, recomputes and checks downstream solids on acceptance.
Invalid downstream results are refused, and Cancel retains the previous
geometry. Actual modeled-helical changes still require an explicit warning
and diagnostic log; they are not exercised in ordinary CI. Native FreeCAD
1.0 geometry tests cover leaf delete/undo, guarded cascading deletion, and
earlier Hole edit/rollback. Windows FreeCAD 1.1 GUI testing remains necessary.

## Hole workflow polish — 0.3.5

The native Hole task now uses compact **Placement**, **Geometry** and **Thread**
groups instead of a long uninterrupted stack of labels. Select a hole-center
sketch, set the diameter/depth, and choose a thread standard. Native available
thread sizes appear immediately, without a first dummy **Show result** click.
Thread standards have readable names while retaining FreeCAD's exact native
enum IDs. Diameter is disabled for threaded holes because the selected native
thread size determines the nominal diameter; choose **None (plain hole)** to
enter a free diameter.

Plain and cosmetic holes have a 350 ms debounced **automatic preview** by
default, reducing extra button clicks while typing. Auto-preview is optional.
It is **never triggered** for currently modeled threads, Holes that originally
had modeled geometry, or a session that just previewed a modeled thread.
Those still require **Update preview** and the existing explicit crash warning,
diagnostic stages, and transactional Cancel. The prominent danger note appears
only when the experimental modeled-thread option is checked. **Show original**
stops pending preview timers to keep the unmodified base visible.

If no sketch is selected, Az requires an explicit choice rather than guessing
that the only sketch drives hole centers; it may instead be the existing Pad's
profile. Changing the center sketch while loading a native thread-size list
rolls back the temporary Hole and switches to the newly selected sketch; the
source locks only after an actual valid preview. The editor continues to preserve existing modeled-thread settings and
does not recompute unchanged features. No underlying geometry kernel was
replaced, and FreeCAD 1.1 Windows GUI acceptance is still required for this
polish build.

## Editing an existing modeled Hole — 0.3.4

Az 0.3.3 could create modeled helical threads but left the old explicit
"existing modeled Hole cannot be edited" blocks in the native edit controller
and UI. The Hole task now reopens modeled features with the original modeled
checkbox and thread size preserved. Opening or accepting an unchanged Hole
**does not recompute** the expensive native helix or change geometry. Changing
thread size, standard, depth or modeled status uses the same explicitly
confirmed, logged native preview as creation. Cancel restores the previous
native Hole via the document transaction. Editing a Hole with later dependent
features still requires rollback or Native CAD.

**Risk:** A changed modeled-thread preview can still crash Windows/FreeCAD 1.1;
the owner must save before experimental edits. The old rejection errors were
reproduced from code inspection; Windows GUI retesting and the exact reported
error messages remain outstanding. See [THREAD_CRASH_LAB.md](THREAD_CRASH_LAB.md).

A Fusion-inspired modeling workspace for **FreeCAD-Az**. Install it in standard
**FreeCAD 1.0 or newer** without compiling the fork. All code is in this repository
and can be changed as our shop workflow develops. This is an independent project;
Autodesk code and artwork are not included.

## Install or update

1. From the latest passing **[Az Design add-on CI run](https://github.com/Mr-Azrack/FreeCAD-Az/actions/workflows/az-design.yml)** on PR #1, download the **AzDesign-installer** artifact, open it and extract **AzDesign-0.4.1.zip**. This is a review build; the latest checked-in release ZIP remains [0.3.1](../releases/AzDesign-0.3.1.zip).
2. In FreeCAD, choose **Macro → Macros…**. Set the macro location to the extracted
   folder, select **Install_AzDesign**, and choose **Execute**.
3. Confirm the local installation, restart FreeCAD, and choose **Az Design** from
   the workbench selector.

The installer needs no administrator rights. An existing installation is backed
up in `AzDesign-backups` beside FreeCAD's `Mod` directory before replacement.
For manual installation, copy the **AzDesign** folder into the `Mod` folder under
`App.getUserAppDataDir()` and restart FreeCAD.

## Experimental modeled-thread crash lab — 0.3.3

The Hole panel now has an **Actually model helical threads — EXPERIMENTAL**
checkbox (off by default). The user must pick an actual thread standard and
size, then explicitly approve a strong crash warning. Only then does Az enable
the native `ModelThread` property. The operation writes fsynced checkpoints
just before the native geometry switch and recomputation, plus Python fault
traces when supported. Clicking OK after a valid unchanged preview does not
repeat the expensive risky recompute.

**Reproduce in a second FreeCAD process with disposable work.** The installer
includes `Probe_Modeled_Thread.FCMacro`, which creates and saves a test block
and attempts a modeled M4 thread while recording its settings. Full
instructions, log locations and optional Windows ProcDump steps are in
[THREAD_CRASH_LAB.md](THREAD_CRASH_LAB.md).

Modeled threads can still terminate FreeCAD, and no C++ root cause has yet
been established. Default cosmetic threading stays unchanged. Modeled-thread
execution is intentionally excluded from automated CI.

## Native Hole stability improvements in 0.3.2\n\nThe Hole ribbon tool and H shortcut now open an Az task panel instead of the native\nPart Design Hole task. Select a sketch containing circles or arcs used as hole\ncenters, choose diameter and depth (or Through all), and click **Show result**.\nInvalid previews reveal the original solid instead of leaving an empty viewport;\nCancel restores the original Body Tip and visibility. Native Hole objects remain\neditable FreeCAD features, including in exported FCStd files. The Az Browser and\ntimeline route Hole editing to the same task panel.\n\nThe Hole task supports native cosmetic thread definitions (choose an explicit\nstandard and thread size). The OCCT helical **ModelThread** option is intentionally\nnot enabled; it crashed the owner's FreeCAD session and Python cannot catch an\nin-process geometry-kernel crash. This is a safety workaround, **not** a fix for\nactual geometric threads. Existing geometric-thread Hole features and non-tip\nHole edits require switching to Native CAD. Advanced native Hole settings are not\nyet in the Az task.\n\nAutomated checks cover native FreeCAD 1.0 geometry, preview rollback, and offline\nthread parameter contracts. **Windows/FreeCAD 1.1 and the visual task layout still\nrequire owner testing.** See PROJECT_STATE.md / SESSION_HANDOFF.md for details.\n\n## Compatibility fixes and grid defaults in 0.3.1

The work area now opens with the grid visible. Modeling uses 10 mm major lines
and 2 mm minor lines; sketch editing uses FreeCAD's aligned sketch grid. Toggle
**Display settings → Grid** in the bottom navigation bar. Your Az grid choice is
remembered. Floor decoration is unpickable, excluded from saved/exported geometry,
and excluded from native model bounds so it does not enlarge Home/Fit.

Native extrusion uses **SideType** on FreeCAD versions that provide it, including
modern symmetric/two-side settings, while retaining older-version support. This
removes Az's direct writes to deprecated Midplane on those versions. Preference
restoration recognizes native Boolean/Integer type names and empty groups, fixing
the reproduced `('Boolean',)` / KeyError when leaving the workspace.

Linux FreeCAD 1.0 native grid/model checks and modern API contract regressions
pass. Windows/FreeCAD 1.1 still needs the owner's retest. Previously saved native
files may emit FreeCAD's own migration notices independently of Az's scripts.

## Workspace introduced in 0.3.0

The work area now has a light canvas, original SVG tool icons, document tabs above
the tools, a Design selector on the left, a grouped Browser, compact timeline and
bottom-center navigation controls. Activating Az with no visible design opens a
normal empty Design. The native menu and auxiliary panels are available from
**File → Advanced**. **File → Native CAD / Properties** returns to Part Design and
restores the previous layout, menus, canvas colors and navigation.

- **Browser:** Bodies, Sketches, Origin, Named Views and construction geometry are
  grouped by purpose. Search filters this design. Eye icons change native
  visibility; a selected face highlights its body. Double-click a sketch to edit,
  or a body to activate it. Right-click for Properties, Isolate and Restore
  visibility. The small sliders button opens native properties.
- **Timeline:** Compact icons select features; double-click edits them and
  right-click offers rollback/suppression. Previous/Next step through the selected
  body's actual solid history; the first control goes to its first solid. A marker
  identifies the rolled-back Body Tip. The right-hand settings menu can show
  feature labels. Multiple bodies require selecting the intended body.
- **Navigation:** Home, Orbit, Pan, Fit and Zoom use the native camera. Orbit/Pan
  buttons enable left-button dragging; Esc returns to selection. Middle button
  pans and Shift + middle button orbits as before. Display settings include native
  shaded/edge/wireframe styles, orthographic/perspective cameras and the default
  modeling/sketch grid. Grid geometry is transient and excluded from Home/Fit.
- **Canvas right-click:** While idle in Solid, eight radial tools offer Sketch,
  Extrude, Press/Pull, Fillet, Hole, Move, Undo and Redo. Click a tool or press Esc.
  Active tasks and sketch drawing retain native right-click/cancel behavior.
- **Document tabs:** Switch native designs from the application bar. Closing uses
  FreeCAD's native unsaved-document confirmation. Finish active tasks before
  switching or closing a design.

This is a repo-owned Qt workspace over FreeCAD's native model/document engine.
The installable module delivers the same source without requiring a full fork
build. Core changes remain available when an API or native UI boundary requires
one. The layout follows familiar CAD conventions described in the
[Autodesk interface guide](https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GS-THE-FUSION-INTERFACE.htm);
its code and SVG artwork are independently implemented. Advanced tasks still use
native FreeCAD dialogs. History reordering and full Fusion feature parity remain
future work. Linux/FreeCAD 1.0/Qt5 is tested; Windows 1.1/Qt6 acceptance is pending.

## First sketch fix included from 0.2.2

Create Sketch now opens a visible design automatically when none is open. You do
not need to choose New first. Az's hidden geometry calculator is never used as
the modeling document. New Body, Extrude and Parameters also check the visible
document context. Existing designs are reused, and selections in other documents
are ignored when creating a sketch or choosing its body.

The reported failure was `NoneType` having no `activeView` after starting without
a document. The fix has 13 document-context regressions, a fresh installed Linux
startup/sketch/extrusion check, and 27 passing GUI workflow checks. The owner's
Windows/FreeCAD 1.1 update and full workflow retest remain pending.

## Startup fix included from 0.2.1

If 0.2.0 reports `name '__file__' is not defined` in `InitGui.py`, install 0.3.0
with the same macro and restart FreeCAD. The update keeps a backup of the old
installation. Both startup entry scripts now import a normal package module;
they no longer assume FreeCAD defines `__file__` for its executed init scripts.
Startup regression tests cover an absent or unrelated loader `__file__`, separate
loader namespaces and installation paths with spaces/non-ASCII characters.
Full Windows/FreeCAD 1.1 modeling validation is still pending.

## Build a part

1. **Create Sketch** on XY, XZ, YZ or a selected planar face.
2. Draw geometry. **D** starts native Smart Dimension for the selected line,
   circle, points or angle. Finish Sketch returns to the Solid ribbon.
3. Press **E**. A single region is selected automatically. For a sketch with
   several regions, click its shaded areas in the view or tick the profile list.
   Nested loops, crossing dividers and overlapping closed profiles form separate
   selectable regions. Curves stay exact; they are not converted to polygons.
4. Type a distance (`6 mm`, `1/4 in`, `10 mm + 2 mm`, `Parameters.Thickness`) or
   drag the blue arrow in the viewport. Choose **Auto**, **Join**, **Cut**,
   **Intersect** or **New body** and inspect the live solid before choosing OK.
5. Select edges for native Fillet or Chamfer. Sketch on another face for a boss,
   pocket or hole. Native Part Design features can follow Az extrusion features.

**Auto** cuts when the extruded volume overlaps the target, joins when it touches,
and creates a new body when it is separate. Select a target Body explicitly when
working with several bodies. Negative distances reverse direction. Explicit Cut
uses FreeCAD Pocket's inward direction; Flip reverses it.

Disconnected regions in **New body** become separate Bodies. A Body contains one
connected solid. Distance supports **One side**, **Symmetric** (total distance) and
**Two sides** (independent distances and handles). **Through all** is available for
Cut. **To face** picks an existing planar end face. Those two extents use One side.
Expand **Start offset and taper** for signed offsets and draft angles.

Cancel restores the model, Body Tips, visibility and preview objects. OK commits
one undoable edit. Leaving Az Design cancels an unfinished Az modeling task.

## Q: Press / Pull

| Selection | Behavior |
| --- | --- |
| Sketch or no selection | Open the profile extrusion workflow |
| End cap of a supported one-sided Az extrusion or native Pad | Offset its driving Length, preserving tapered walls and parameter expressions |
| Other planar face with prismatic side walls | Preview an outward Join or inward Cut from that face |
| Cylinder generated by a unique editable sketch circle | Edit its driving diameter; an unconstrained circle receives a driving dimension |
| Native Cylinder or Hole's main cylindrical face | Edit its Radius or Diameter parameter |
| Solid edge | Open native Fillet |

End-face offsets are signed changes from the original length. Cylinder edits are
absolute diameters. Unsupported curved/imported surfaces and ambiguous source
circles produce an explanation instead of creating an unrelated solid. General
surface offsets and healing of arbitrary imported models remain future work.

## Parameters

Choose **Utilities → Parameters** (also under Solid → Modify → More). Add named
user parameters, edit model dimensions and choose **Update model** to inspect the
result. OK commits; Cancel restores the original model.

User parameters live in a native `Parameters` Spreadsheet. A value can be `8 mm`,
`1/4 in` or a spreadsheet formula such as `=Thickness / 2`. Model dimensions use
native expressions such as `Parameters.Thickness`. Driving sketch constraints and
common feature lengths, radii and angles appear in the same task. Existing alias
names are fixed in this editor; use the native Spreadsheet for structural edits.

## Editable history

The bottom strip follows each Body's native feature order. Click to select and
double-click to edit. Right-click a solid feature for **Roll back here**,
**Suppress / Unsuppress**, **Resume latest history**, visibility or rename.

Rollback changes the real Body Tip and shows that stage of the solid. New Az
extrusions insert at that position and rebase the next unique feature. Resume
Latest restores the saved end of that Body. Explicit sketch/face references stay
anchored to their original features; insertion does not rewrite design intent.
Branched histories and edits that break downstream features are rejected.

This is not a drag-to-reorder Fusion timeline. Topology-changing edits may require
reselecting native downstream face/edge references. Az region and planar-face
references record geometric intent and ask for reselection when ambiguous.

## Interface and navigation

- **Solid / Sketch / Utilities ribbon**, native Browser on the left and Tasks on
  the right. Context follows sketch editing without changing workbenches.
- **S** searches tools by familiar name or native command ID.
- Middle button pans, **Shift + middle button** orbits, wheel zooms. Native Fusion
  navigation is used when available; otherwise Az adapts Blender navigation.
- **Native CAD** restores the prior layout, toolbars and camera navigation.
  **Manufacture** opens the installed native CAM workbench.

| Context | Shortcuts |
| --- | --- |
| Solid | E Extrude; Q Press/Pull; F Fillet; H Hole; M Move; S Find a Tool |
| Sketch | L Line; R Rectangle; C Circle; D Smart Dimension; T Trim; P Project; X Construction; S Find a Tool |

Shortcuts do not intercept typing in task controls, text fields, the Python
console or modal dialogs. Existing FreeCAD shortcuts are not rewritten.

## Saved models and compatibility

**Version 0.2 extrusion results are parametric Az features**, evaluated with
FreeCAD's native Pad/Pocket and exact OCCT boolean algorithms. Keep Az Design
installed to edit/recompute those features. Their cached shapes remain available
in `.FCStd`; export STEP for an independent solid exchange file. The v0.1 native
Pad/Pocket models remain native and are not migrated or rewritten.

Verified on **FreeCAD 1.0.0, Linux, Qt 5 / PySide2**. Windows, macOS, PySide6 and
FreeCAD 1.1 have not been verified. Native Revolve, Loft, Sweep, Fillet, Hole,
Shell, patterns and CAM still use FreeCAD dialogs. Assembly/joint workflows,
Fusion-style CAM setup and arbitrary direct surface modeling are not redesigned.

## Develop and verify

| Module | Responsibility |
| --- | --- |
| `catalog.py`, `commands.py` | Editable ribbon, shortcuts and command adapters |
| `profiles.py`, `references.py` | Exact planar regions and saved geometric references |
| `features.py`, `operations.py` | Parametric solids, body frames, previews and transactions |
| `tasks.py`, `manipulator.py`, `presspull.py` | Profile/face picking, viewport arrows and Q workflows |
| `parameters.py`, `history.py` | Native expressions, user parameters, rollback and insertion |
| `modeling.py` | Body/sketch setup and retained v0.1 native adapters |
| `ui.py`, `session.py` | Ribbon, palette, history and scoped layout/navigation |
| `install.py` | Local installer, backup and recovery |

Run from the repository root:

```sh
python3 addons/AzDesign/tests/test_startup.py
python3 addons/AzDesign/tests/test_install.py
/usr/bin/python3 addons/AzDesign/tests/run_workflow.py
python3 tools/package_azdesign.py
```

The modeling runner uses a packaged FreeCAD runtime and its matching Python.
Set `FREECAD_LIB_DIR` for other installations. GitHub CI installs Debian's native
runtime and runs the geometry/parameter/history tests in addition to packaging.

For desktop tests, load Az Design and run in **View → Panels → Python console**:

```python
import runpy
suite = runpy.run_path('/path/to/AzDesign/tests/integration_v02.py')
suite['run']('/path/to/results.json', '/path/to/test_part.FCStd')
```

The native Smart Dimension tool may wait for Escape before the test continues.
`integration.py` also retains the original native-feature, navigation and layout
regressions. Test reports are checked into `tests/validation-v02-linux.json`.
These tests create separate test documents and leave results open for inspection.

## License and provenance

New code is **LGPL-2.1-or-later**. FreeCAD icons are resolved from the installed
application. This fork's changes were produced with OpenAI Codex assistance and
require owner review before an upstream submission.
