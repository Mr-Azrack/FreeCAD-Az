# SPDX-License-Identifier: LGPL-2.1-or-later
"""Run in FreeCAD's GUI console; exercises the complete Az task lifecycle."""

import json
import math
import traceback
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
from azdesign import tasks, features, history, commands, parameters, modeling, presspull
from azdesign.qt import QtCore, QtWidgets


def run(report_path, example_path=None):
    report = {"freecad_version": App.Version(), "checks": [], "passed": False}
    doc = None
    task = None

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        report["checks"].append(name)
        Path(report_path).write_text(json.dumps(report, indent=2))

    try:
        Gui.activateWorkbench("AzDesignWorkbench")
        QtWidgets.QApplication.processEvents()
        doc = App.newDocument("Az_Workflow_v02")
        QtWidgets.QApplication.processEvents()
        doc.UndoMode = 1
        body = doc.addObject("PartDesign::Body", "Body")
        source = body.newObject("Sketcher::SketchObject", "PlateSketch")
        points = [
            App.Vector(0, 0, 0),
            App.Vector(80, 0, 0),
            App.Vector(80, 50, 0),
            App.Vector(0, 50, 0),
        ]
        for i in range(4):
            source.addGeometry(Part.LineSegment(points[i], points[(i + 1) % 4]))
        source.addGeometry(Part.Circle(App.Vector(20, 25, 0), App.Vector(0, 0, 1), 5))
        source.addConstraint(Sketcher.Constraint("Diameter", 4, 10.0))
        doc.recompute()
        Path(report_path).write_text(json.dumps({"step": "opening first Extrude task"}))
        original_names = [o.Name for o in doc.Objects]
        task = tasks.show_extrude((source, []))
        check(
            "nested sketch exposes two independently selectable regions",
            task.profile_list.count() == 2,
        )
        check("multi-region sketch starts in canvas profile selection", task.picking == "profiles")
        overlay = doc.getObject(task.overlay_names[0])
        Gui.Selection.addSelection(overlay, "Face1")
        task.preview()
        check("canvas selection toggles the exact profile", len(task.selected_descriptors()) == 1)
        task.distance.setText("6 mm")
        task.end_pick()
        report["preview_diagnostic"] = {
            "valid": task.valid,
            "status": task.status.text(),
            "outputs": [
                (o.Name, o.Length.Value, 0 if o.Shape.isNull() else o.Shape.Volume, o.Error)
                for o in task.operation.outputs
            ],
        }
        check(
            "live selected-region preview is an exact solid",
            task.valid
            and abs(task.operation.outputs[0].Shape.Volume - (4000 - 25 * math.pi) * 6) < 1e-5,
        )
        check(
            "native viewport distance dragger is installed",
            task.manipulator is not None and len(task.manipulator.handles) == 1,
        )
        dragger, start, motion, finish = task.manipulator.handles[0]
        start()
        dragger.translation = (8, 0, 0)
        motion()
        finish()
        QtWidgets.QApplication.processEvents()
        check(
            "viewport dragger updates the distance and solid",
            task.distance.text() == "8.0000 mm"
            and abs(task.operation.outputs[0].Length.Value - 8) < 1e-6,
        )
        task.reject()
        task = None
        check(
            "Cancel restores all objects including preview overlays",
            [o.Name for o in doc.Objects] == original_names,
        )
        task = tasks.show_extrude((source, []))
        task.profile_list.item(0).setCheckState(QtCore.Qt.Checked)
        task.distance.setText("6 mm")
        task.end_pick()
        check("OK commits the complete operation", task.accept())
        base = body.Tip
        task = None
        check(
            "accepted document has no presentation geometry",
            not any(getattr(o, "AzPreview", False) for o in doc.Objects),
        )
        check(
            "native file has one valid Body with exact geometry",
            body.Tip == base and base.Shape.isValid() and len(base.Shape.Solids) == 1,
        )
        name = base.Name
        doc.undo()
        check(
            "one Undo removes the solid and retains source sketch",
            doc.getObject(name) is None and doc.getObject(source.Name) is not None,
        )
        doc.redo()
        doc.recompute()
        base = doc.getObject(name)
        source = doc.getObject(source.Name)
        check(
            "Redo restores the editable custom feature",
            base.Proxy.Type == "AzExtrude" and base.Shape.isValid(),
        )
        top = next(
            "Face" + str(i + 1) for i, f in enumerate(base.Shape.Faces) if f.normalAt(0, 0).z > 0.99
        )
        task = tasks.show_extrude((base, [top]))
        task.operation_choice.setCurrentText("Cut")
        task.distance.setText("1 mm")
        task.preview()
        check(
            "face profile switches from Join to Cut in one task",
            task.valid and task.operation.outputs[0].Operation == "Cut",
        )
        task.operation_choice.setCurrentText("Join")
        task.direction.setCurrentText("Two sides")
        task.distance2.setText("1 mm")
        task.preview()
        check(
            "two-sided operation creates two independent handles",
            task.valid and len(task.manipulator.handles) == 2,
        )
        task.direction.setCurrentText("One side")
        task.preview()
        check("face extrusion accepts", task.accept())
        added = body.Tip
        task = tasks.edit_feature(added)
        task.distance.setText("2 mm")
        task.preview()
        check("editing retains feature identity", task.operation.outputs[0] == added)
        task.accept()
        task = None
        history.rollback(base)
        check("rollback changes the Body Tip", body.Tip == base)
        history.end(body)
        check("resume restores the latest native history position", body.Tip == added)
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(
            added,
            next(
                "Face" + str(i + 1)
                for i, f in enumerate(added.Shape.Faces)
                if f.normalAt(0, 0).z > 0.99
            ),
        )
        task = presspull.start()
        task.value.setText("1 mm")
        task.preview()
        check(
            "Q on an end face edits the originating length",
            task.valid and abs(added.Length.Value - 3) < 1e-7,
        )
        task.reject()
        task = None
        check("Press/Pull Cancel restores its source dimension", abs(added.Length.Value - 2) < 1e-7)
        task = parameters.show()
        task.add_user("Thickness", "7 mm")
        for row, (obj, path, _, _) in enumerate(task.dimensions):
            if obj == base and path == "Length":
                task.models.item(row, 2).setText("Parameters.Thickness")
        check(
            "Parameters updates exact geometry through native expressions",
            task.preview() and abs(base.Length.Value - 7) < 1e-7,
        )
        task.accept()
        task = None
        modeling.edit_sketch(source)
        commands.smart_dimension()
        check(
            "D starts native Smart Dimension without leaving Az Design",
            Gui.activeWorkbench().name() == "AzDesignWorkbench" and modeling.in_sketch() == source,
        )
        modeling.finish_sketch()
        if example_path:
            path = str(example_path)
            doc.saveAs(path)
            names = (doc.Name, base.Name, added.Name)
            App.closeDocument(doc.Name)
            doc = App.openDocument(path)
            base, added = doc.getObject(names[1]), doc.getObject(names[2])
            doc.Parameters.set("B2", "9 mm")
            doc.recompute()
            check(
                "saved model reopens and recomputes feature proxies and face references",
                not base.Error
                and not added.Error
                and abs(base.Length.Value - 9) < 1e-7
                and added.Shape.isValid(),
            )
        body = features.owner_body(added)
        fillet = body.newObject("PartDesign::Fillet", "Fillet")
        fillet.Base = (added, ["Edge1"])
        fillet.Radius = 0.5
        doc.recompute()
        base.setExpression("Length", "10 mm")
        doc.recompute()
        check(
            "native downstream Fillet survives an upstream Az dimension edit",
            "Invalid" not in fillet.State and fillet.Shape.isValid(),
        )
        if example_path:
            names = (fillet.Name, added.Name)
            doc.saveAs(str(example_path))
            App.closeDocument(doc.Name)
            doc = App.openDocument(str(example_path))
            fillet, added = doc.getObject(names[0]), doc.getObject(names[1])
            doc.recompute()
            check(
                "mixed native and Az feature history reopens correctly",
                "Invalid" not in fillet.State and fillet.Shape.isValid(),
            )
        before = added.Length.Value
        task = tasks.edit_feature(added)
        task.distance.setText("3 mm")
        task.preview()
        Gui.activateWorkbench("PartDesignWorkbench")
        check(
            "leaving the workbench cancels an unfinished Az task",
            not Gui.Control.activeDialog()
            and abs(added.Length.Value - before) < 1e-7
            and App.getActiveTransaction() is None,
        )
        task = None
        Gui.activateWorkbench("AzDesignWorkbench")
        commands.home()
        from azdesign.session import current

        current().tick()
        check(
            "history omits all transient presentation objects",
            all(
                not getattr(button.object(), "AzPreview", False)
                for button in current().history.buttons
            ),
        )
        report["passed"] = True
    except Exception:
        report["error"] = traceback.format_exc()
        if task:
            try:
                task.reject()
            except Exception:
                pass
    finally:
        Path(report_path).write_text(json.dumps(report, indent=2))
    return report
