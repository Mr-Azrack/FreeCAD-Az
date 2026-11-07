# SPDX-License-Identifier: LGPL-2.1-or-later
"""Run inside FreeCAD's GUI Python console, not a standalone Python process.

import runpy
suite = runpy.run_path('/path/to/AzDesign/tests/integration.py')
suite['run']('/path/to/results.json', '/path/to/example.FCStd')
"""
import json
import math
import traceback
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
from azdesign import commands, modeling
from azdesign.catalog import TOOLS
from azdesign.qt import QtCore, QtGui, QtWidgets


def rectangle(body):
    sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    points = [
        App.Vector(0, 0, 0),
        App.Vector(80, 0, 0),
        App.Vector(80, 50, 0),
        App.Vector(0, 50, 0),
    ]
    for index in range(4):
        sketch.addGeometry(Part.LineSegment(points[index], points[(index + 1) % 4]), False)
    for index in range(4):
        sketch.addConstraint(Sketcher.Constraint("Coincident", index, 2, (index + 1) % 4, 1))
        sketch.addConstraint(
            Sketcher.Constraint("Horizontal" if index % 2 == 0 else "Vertical", index)
        )
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 1, -1, 1))
    sketch.addConstraint(Sketcher.Constraint("Distance", 0, 80.0))
    sketch.addConstraint(Sketcher.Constraint("Distance", 1, 50.0))
    return sketch


def circle(body, name, x, y, z, radius):
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.Placement.Base.z = z
    sketch.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), radius), False)
    sketch.addConstraint(Sketcher.Constraint("Diameter", 0, radius * 2))
    sketch.addConstraint(Sketcher.Constraint("DistanceX", 0, 3, x))
    sketch.addConstraint(Sketcher.Constraint("DistanceY", 0, 3, y))
    return sketch


def run(report_path, example_path=None):
    result = {"freecad_version": App.Version(), "checks": [], "passed": False}
    doc = None
    toolbar_prefs = App.ParamGet("User parameter:BaseApp/MainWindow/Toolbars")
    toolbar_key = "Part Design Modeling"
    original_toolbar_setting = next(
        (value for kind, name, value in toolbar_prefs.GetContents() if name == toolbar_key), None
    )

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        result["checks"].append(name)

    try:
        commands.register()
        Gui.activateWorkbench("PartDesignWorkbench")
        toolbar_prefs.SetBool(toolbar_key, True)
        baseline_bar = Gui.getMainWindow().findChild(QtWidgets.QToolBar, toolbar_key)
        if baseline_bar:
            baseline_bar.show()
        Gui.activateWorkbench("AzDesignWorkbench")
        from azdesign.session import current, start, stop

        QtWidgets.QApplication.processEvents()
        check(
            "all catalog commands are registered",
            all(t.command in Gui.listCommands() for t in TOOLS.values()),
        )
        check(
            "one ribbon is visible",
            len(Gui.getMainWindow().findChildren(QtWidgets.QToolBar, "AzDesignRibbonBar")) == 1,
        )
        doc = App.newDocument("AzDesign_TestPlate")
        doc.UndoMode = 1
        body = doc.addObject("PartDesign::Body", "Body")
        sketch = rectangle(body)
        doc.recompute()
        check("base sketch is fully constrained", sketch.FullyConstrained)
        extrusion = modeling.Extrusion(sketch)
        volume = extrusion.update("6 mm")
        check("extrude preview creates an exact 80 x 50 x 6 solid", abs(volume - 24000) < 1e-5)
        extrusion.accept()
        check("extrude creates a native Pad", doc.getObject("Extrude").TypeId == "PartDesign::Pad")
        doc.undo()
        check("one Undo removes the complete extrusion", doc.getObject("Extrude") is None)
        doc.redo()
        doc.recompute()
        base = doc.getObject("Extrude")
        check("Redo restores exact volume", abs(base.Shape.Volume - 24000) < 1e-5)
        cut_sketch = circle(body, "CutSketch", 20, 25, 6, 5)
        doc.recompute()
        cut = modeling.Extrusion(cut_sketch, cut=True)
        cut_volume = cut.update("2 mm")
        expected = 24000 - math.pi * 5 * 5 * 2
        check("cut preview removes the specified cylinder", abs(cut_volume - expected) < 1e-5)
        cut.accept()
        check("cut creates a native Pocket", doc.getObject("Cut").TypeId == "PartDesign::Pocket")
        test_sketch = circle(body, "CancelSketch", 50, 25, 6, 3)
        doc.recompute()
        before_objects = [o.Name for o in doc.Objects]
        before_tip = body.Tip.Name
        before_visibility = {o.Name: o.ViewObject.Visibility for o in doc.Objects}
        preview = modeling.Extrusion(test_sketch)
        preview.update("2 mm")
        preview.cancel()
        check(
            "Cancel removes every preview object", before_objects == [o.Name for o in doc.Objects]
        )
        check("Cancel restores the previous Body Tip", body.Tip.Name == before_tip)
        check(
            "Cancel restores visibility",
            before_visibility == {o.Name: o.ViewObject.Visibility for o in doc.Objects},
        )
        doc.removeObject(test_sketch.Name)
        body.Tip = doc.getObject("Cut")
        doc.recompute()
        # Input validation must reject bad dimensions before changing the model.
        for invalid in ("0", "-2 mm", "1 kg", "nonsense"):
            try:
                modeling.length_mm(invalid)
                raise AssertionError("accepted invalid length: " + invalid)
            except modeling.ModelingError:
                pass
        check("invalid dimensions are rejected", True)
        check("inch fractions convert exactly", abs(modeling.length_mm("1/4 in") - 6.35) < 1e-10)
        current().tick()
        check("history follows native features", len(current().history.buttons) == 4)
        original_editing_workbench = sketch.ViewObject.EditingWorkbench
        modeling.edit_sketch(sketch)
        check(
            "editing a sketch stays in Az Design",
            Gui.activeWorkbench().name() == "AzDesignWorkbench",
        )
        check(
            "sketch editing preference is immediately restored",
            sketch.ViewObject.EditingWorkbench == original_editing_workbench,
        )
        check("native sketch editor opens", modeling.in_sketch() == sketch)
        modeling.finish_sketch()
        check(
            "Finish Sketch stays in Az Design", Gui.activeWorkbench().name() == "AzDesignWorkbench"
        )
        view = Gui.activeDocument().activeView()
        supported = view.listNavigationTypes()
        check(
            "compatible camera navigation exists",
            "Gui::BlenderNavigationStyle" in supported or "Gui::FusionNavigationStyle" in supported,
        )
        current().tick()
        QtWidgets.QApplication.processEvents()
        mdi = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)
        view_window = mdi.activeSubWindow()
        viewport = next(
            w
            for w in view_window.findChildren(QtWidgets.QWidget)
            if current().filter.is_viewport(w) and w.isVisible()
        )
        result["viewport_class"] = viewport.metaObject().className()
        animating = view.isAnimationEnabled()
        view.setAnimationEnabled(False)
        view.viewAxonometric()
        QtWidgets.QApplication.processEvents()

        def mouse_drag(modifiers):
            points = [QtCore.QPointF(200, 200), QtCore.QPointF(225, 210), QtCore.QPointF(255, 225)]
            events = [
                (
                    QtCore.QEvent.MouseButtonPress,
                    points[0],
                    QtCore.Qt.MiddleButton,
                    QtCore.Qt.MiddleButton,
                ),
                (QtCore.QEvent.MouseMove, points[1], QtCore.Qt.NoButton, QtCore.Qt.MiddleButton),
                (QtCore.QEvent.MouseMove, points[2], QtCore.Qt.NoButton, QtCore.Qt.MiddleButton),
                (
                    QtCore.QEvent.MouseButtonRelease,
                    points[2],
                    QtCore.Qt.MiddleButton,
                    QtCore.Qt.NoButton,
                ),
            ]
            for kind, position, button, buttons in events:
                event = QtGui.QMouseEvent(kind, position, button, buttons, modifiers)
                QtWidgets.QApplication.sendEvent(viewport, event)
            QtWidgets.QApplication.processEvents()

        orientation = view.getCameraOrientation().Q
        position = tuple(view.getCameraNode().position.getValue())
        mouse_drag(QtCore.Qt.NoModifier)
        rotation_after_pan = view.getCameraOrientation().Q
        result["mouse_pan"] = {
            "before": orientation,
            "after": rotation_after_pan,
            "position_before": position,
            "position_after": tuple(view.getCameraNode().position.getValue()),
        }
        same_orientation = (
            min(
                max(abs(a - b) for a, b in zip(orientation, rotation_after_pan)),
                max(abs(a + b) for a, b in zip(orientation, rotation_after_pan)),
            )
            < 1e-7
        )
        check(
            "middle mouse pans without rotating",
            same_orientation and tuple(view.getCameraNode().position.getValue()) != position,
        )
        mouse_drag(QtCore.Qt.ShiftModifier)
        check("Shift plus middle mouse orbits", view.getCameraOrientation().Q != orientation)
        view.setAnimationEnabled(animating)
        original_nav = next(style for saved, style in current().views if saved == view)
        stop()
        QtWidgets.QApplication.processEvents()
        check("leaving restores camera navigation", view.getNavigationType() == original_nav)
        check(
            "leaving removes the ribbon",
            len(Gui.getMainWindow().findChildren(QtWidgets.QToolBar, "AzDesignRibbonBar")) == 0,
        )
        start()
        current().tick()
        check(
            "re-entry creates exactly one ribbon",
            len(Gui.getMainWindow().findChildren(QtWidgets.QToolBar, "AzDesignRibbonBar")) == 1,
        )
        check(
            "saved objects require no custom proxies",
            all(o.TypeId != "PartDesign::FeaturePython" for o in doc.Objects),
        )
        Gui.activateWorkbench("PartDesignWorkbench")
        native_bar = Gui.getMainWindow().findChild(QtWidgets.QToolBar, "Part Design Modeling")
        check(
            "temporary ribbon hiding preserves native toolbar preferences",
            toolbar_prefs.GetBool(toolbar_key, False),
        )
        check(
            "switching to native CAD preserves its modeling toolbar",
            native_bar is not None and not native_bar.isHidden(),
        )
        Gui.activateWorkbench("AzDesignWorkbench")
        check(
            "switching back restores the Az ribbon",
            current() is not None and not current().toolbar.isHidden(),
        )
        if example_path:
            doc.saveAs(str(example_path))
            name = doc.Name
            App.closeDocument(name)
            doc = App.openDocument(str(example_path))
            check(
                "native file reopens with exact cut geometry",
                abs(doc.getObject("Cut").Shape.Volume - expected) < 1e-5,
            )
        for obj in doc.Objects:
            if obj.ViewObject:
                obj.ViewObject.Visibility = obj.Name in ("Body", "Cut")
        commands.home()
        current().tick()
        result["passed"] = True
    except Exception:
        result["error"] = traceback.format_exc()
        App.Console.PrintError(result["error"])
    finally:
        if original_toolbar_setting is None:
            toolbar_prefs.RemBool(toolbar_key)
        else:
            toolbar_prefs.SetBool(toolbar_key, original_toolbar_setting)
        Path(report_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(
            "AZ INTEGRATION:",
            "PASS" if result["passed"] else "FAIL",
            "checks:",
            len(result["checks"]),
        )
    return result
