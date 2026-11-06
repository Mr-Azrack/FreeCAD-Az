# SPDX-License-Identifier: LGPL-2.1-or-later
"""Native grid visibility, persistence, sketch fitting and Boolean restoration."""

import json
import traceback
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
import Part
from azdesign import modeling, commands
from azdesign.session import current


def run(report_path):
    report = {"freecad_version": App.Version(), "checks": [], "passed": False}

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        report["checks"].append(name)

    try:
        session = current()
        check("fresh Az grid preference defaults to visible", session.appearance.grid_visible)
        check("display menu reflects visible grid", session.navigation.grid_action.isChecked())
        doc = App.newDocument("AzGridChecks")
        body = doc.addObject("PartDesign::Body", "Body")
        sketch = body.newObject("Sketcher::SketchObject", "Profile")
        points = [
            App.Vector(0, 0, 0),
            App.Vector(20, 0, 0),
            App.Vector(20, 20, 0),
            App.Vector(0, 20, 0),
        ]
        for i in range(4):
            sketch.addGeometry(Part.LineSegment(points[i], points[(i + 1) % 4]))
        sketch.ViewObject.ShowGrid = False
        doc.recompute()
        session.tick()
        from pivy import coin
        from azdesign.qt import QtWidgets

        QtWidgets.QApplication.processEvents()
        bounds = coin.SoGetBoundingBoxAction(coin.SbViewportRegion(800, 600))
        bounds.apply(Gui.activeDocument().activeView().getSceneGraph())
        size = tuple(bounds.getBoundingBox().getSize())
        report["model_scene_bounds"] = size
        check("floor decoration does not contribute to native scene bounds", 19 <= max(size) < 21)
        node = next(
            node
            for view, root, node in session.appearance.grids
            if view == Gui.activeDocument().activeView()
        )
        check("3D canvas grid is visible", node.whichChild.getValue() == -3)
        names = [o.Name for o in doc.Objects]
        view = Gui.activeDocument().activeView()
        view.setAnimationEnabled(False)
        modeling.edit_sketch(sketch)
        session.tick()
        check("sketch editor shows its native aligned grid", sketch.ViewObject.ShowGrid)
        check("world XY grid is hidden in sketch mode", node.whichChild.getValue() == -1)
        height = view.getCameraNode().height.getValue()
        report["sketch_camera_height"] = height
        check("entering the sketch fits its profile instead of the floor grid", height < 150)
        session.navigation.grid_action.setChecked(False)
        check("display toggle hides the sketch grid", not sketch.ViewObject.ShowGrid)
        session.navigation.grid_action.setChecked(True)
        check("display toggle restores the sketch grid", sketch.ViewObject.ShowGrid)
        modeling.finish_sketch()
        session.tick()
        check("leaving sketch restores its prior view property", not sketch.ViewObject.ShowGrid)
        check("leaving sketch restores the world grid", node.whichChild.getValue() == -3)
        check("grids create no saved model objects", names == [o.Name for o in doc.Objects])
        session.navigation.grid_action.setChecked(False)
        report["native_saved_boolean_kind"] = session.appearance.saved.get("Simple", (None,))[0]
        Gui.activateWorkbench("PartDesignWorkbench")
        check(
            "pre-existing native Boolean preference restores without exception",
            not App.ParamGet("User parameter:BaseApp/Preferences/View").GetBool("Simple", True),
        )
        check("old workspace is fully removed", current() is None)
        Gui.activateWorkbench("AzDesignWorkbench")
        check(
            "grid-off preference survives re-entry",
            not current().appearance.grid_visible
            and not current().navigation.grid_action.isChecked(),
        )
        current().navigation.grid_action.setChecked(True)
        current().tick()
        check("grid is restored after re-entry", current().appearance.grid_visible)
        report["passed"] = True
    except Exception:
        report["error"] = traceback.format_exc()
        App.Console.PrintError(report["error"])
    finally:
        Path(report_path).write_text(json.dumps(report, indent=2))
    return report
