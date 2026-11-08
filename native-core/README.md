# Az Design — FreeCAD 1.1 native core integration

This directory starts the **separate native application** path. It is not
installed or modified by the ordinary Az workbench updater, which intentionally
touches only the user's `Mod/AzDesign` directory.

## Why a FreeCAD core patch?

The Python workbench can show geometric midpoint/center markers on mouse
hover, but FreeCAD's C++ Sketcher `SnapManager` computes the **actual**
coordinates passed to active drawing commands. Automatically redirecting
a drawing click on a circular *rim* to the circle *center* belongs there.
Injecting synthetic Qt mouse clicks from Python would interfere with selection,
dragging and the native Sketcher constraint solver.

The source patch:

- `patches/001-freecad-1.1.0-sketcher-circle-center.patch`
- Targets upstream **FreeCAD/FreeCAD**, tag **1.1.0**, only:
  - `src/Mod/Sketcher/Gui/SnapManager.h`
  - `src/Mod/Sketcher/Gui/SnapManager.cpp`
- Adds an opt-in native setting, at
  `User parameter:BaseApp/Preferences/Mod/Sketcher/Snap`:
  `AzSnapCircleCenter` (Boolean, **false by default**).
- When enabled and while native Sketcher object snapping preselects a
  **complete circular curve**, `SnapManager::snapToObject` returns the
  analytical circle center, not the nearest point on the rim.
- Holding **Alt** temporarily bypasses center preference and preserves the
  ordinary point-on-circle behavior.
- Does not change FreeCAD document data, sketches or underlying geometry;
  does not affect linear, arc or non-circular objects.
- Is purely a patch *proposal* until checked, compiled, installed and tested
  in a native Az application. No Windows executable or C++ compiled result
  is currently available.

## Applying it for a native development build

In an independent source checkout, **not** `C:\Program Files\FreeCAD 1.1`:

```bash
git clone --branch 1.1.0 --depth 1 https://github.com/FreeCAD/FreeCAD.git FreeCAD-Az-Core
cd FreeCAD-Az-Core
git apply --check /path/to/FreeCAD-Az/native-core/patches/001-freecad-1.1.0-sketcher-circle-center.patch
git apply /path/to/FreeCAD-Az/native-core/patches/001-freecad-1.1.0-sketcher-circle-center.patch
```

Build the modified source using FreeCAD 1.1's **supported Windows** CMake,
Qt and dependency toolchain. Use a separate install prefix/build directory,
never overwrite the user's working FreeCAD 1.1 installation. C++ compilation,
signed packaging and Windows GUI acceptance are explicitly **not yet done**.

After the native build works, turn on the Az-specific setting from the
FreeCAD Python console for test purposes:

```python
import FreeCAD as App
prefs = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Sketcher/Snap")
prefs.SetBool("AzSnapCircleCenter", True)
```

Open a sketch containing a circular edge, enable native Sketcher snapping,
select a creation tool (for example Line), hover over a circle's rim, and
click: the tool's point coordinate should resolve to the circle center. Hold
Alt to target the circumference instead. Test line midpoint snapping,
selection, constraints, editing, Undo, many geometry types and actual
Windows DPI before enabling by default.

## Testing and rollout guardrail

1. Keep the current **0.5.1 workbench** functional on stock FreeCAD 1.1.
   Its automatic hover markers are presentation-only; actual point snapping
   remains native and unchanged.
2. Test the C++ patch against the exact upstream tag and compile a separate
   native build on Windows. Do not infer success from Python-only or Linux
   addon CI.
3. Validate circle center snap under different Sketcher creation commands,
   the Alt bypass, ordinary point-on-circle constraints and other Snaps.
4. Once verified, build a branded **Az native application** installer and
   separate application update path. Keep original FreeCAD untouched.
5. Do not claim that the addon `Update Az` button installed or enabled this
   C++ patch. It cannot replace the main FreeCAD GUI DLL or core files.

FreeCAD code and this source patch are subject to the applicable LGPL
licence and upstream code contribution policy.
