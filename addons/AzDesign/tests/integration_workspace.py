# SPDX-License-Identifier: LGPL-2.1-or-later
"""Run in the installed FreeCAD GUI to verify the Az workspace's model behavior."""

import json
import traceback
from pathlib import Path
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
from azdesign import commands, modeling
from azdesign.session import current
from azdesign.qt import QtCore, QtGui, QtWidgets


def run(report_path):
    report = {"freecad_version": App.Version(), "checks": [], "passed": False}

    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        report["checks"].append(label)
        Path(report_path).write_text(json.dumps(report, indent=2))

    original_grid = current().appearance.grid_visible if current() else True
    try:
        Gui.activateWorkbench("AzDesignWorkbench")
        doc = App.newDocument("AzWorkspaceChecks")
        doc.UndoMode = 1
        body = doc.addObject("PartDesign::Body", "Body")
        sketch = body.newObject("Sketcher::SketchObject", "Profile")
        points = [
            App.Vector(0, 0, 0),
            App.Vector(80, 0, 0),
            App.Vector(80, 50, 0),
            App.Vector(0, 50, 0),
        ]
        for i in range(4):
            sketch.addGeometry(Part.LineSegment(points[i], points[(i + 1) % 4]))
        pad = body.newObject("PartDesign::Pad", "Pad")
        pad.Profile, pad.Length = sketch, 8
        holes = body.newObject("Sketcher::SketchObject", "HoleProfile")
        holes.Placement.Base.z = 8
        holes.addGeometry(Part.Circle(App.Vector(20, 25, 0), App.Vector(0, 0, 1), 4))
        pocket = body.newObject("PartDesign::Pocket", "Pocket")
        pocket.Profile, pocket.Length = holes, 8
        doc.recompute()
        sketch.Visibility = holes.Visibility = pad.Visibility = False
        pocket.Visibility = True
        Gui.activeDocument().activeView().setActiveObject("pdbody", body)
        view = Gui.activeDocument().activeView()
        view.setAnimationEnabled(False)
        commands.home()
        session = current()
        session.tick()
        QtWidgets.QApplication.processEvents()
        check(
            "grouped Browser contains bodies and sketches",
            all((doc.Name, o.Name) in session.browser.items for o in (body, sketch, holes)),
        )
        check(
            "Browser separates feature history from bodies",
            (doc.Name, pad.Name) not in session.browser.items,
        )
        check(
            "compact timeline contains the native feature sequence",
            len(session.history.buttons) == 4,
        )
        check(
            "native bottom tabs are hidden behind top document tabs",
            all(tab.isHidden() for tab, _ in session.native_tabs),
        )
        check(
            "top tabs omit the hidden calculator",
            all(
                not str(session.ribbon.documents.tabData(i)).startswith("AzGeometry")
                for i in range(session.ribbon.documents.count())
            ),
        )
        item = session.browser.items[(doc.Name, body.Name)]
        session.browser.tree.setCurrentItem(item)
        check("Browser selection uses FreeCAD selection", body in Gui.Selection.getSelection())
        session.browser.click(item, 1)
        check("Browser eye toggles actual body visibility", not body.ViewObject.Visibility)
        session.browser.click(item, 1)
        check("Browser eye restores actual body visibility", body.ViewObject.Visibility)
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(pocket, "Face1")
        session.browser.refresh()
        check("canvas face selection highlights its body in the Browser", item.isSelected())
        session.browser.search.setText("HoleProfile")
        check(
            "Browser search filters unrelated objects",
            session.browser.items[(doc.Name, body.Name)].isHidden()
            and not session.browser.items[(doc.Name, holes.Name)].isHidden(),
        )
        session.browser.search.clear()
        session.history.step(-1)
        check(
            "previous timeline step rolls back the actual Body Tip",
            body.Tip == pad and bool(body.AzHistoryEnd),
        )
        check(
            "rolled timeline has a visible position marker",
            session.history.findChild(QtWidgets.QFrame, "AzHistoryMarker") is not None,
        )
        session.history.step(1)
        check(
            "next timeline step restores the actual latest feature",
            body.Tip == pocket and not body.AzHistoryEnd,
        )
        session.history.show_labels(True)
        check(
            "timeline labels can be enabled without changing feature order",
            len(session.history.buttons) == 4
            and session.history.buttons[0].toolButtonStyle() == QtCore.Qt.ToolButtonTextBesideIcon,
        )
        session.history.show_labels(False)
        names = [obj.Name for obj in doc.Objects]
        session.navigation.grid_action.setChecked(True)
        check(
            "grid is presentation only",
            names == [obj.Name for obj in doc.Objects] and bool(session.appearance.grids),
        )
        commands.home()
        view = Gui.activeDocument().activeView()
        height_grid = view.getCameraNode().height.getValue()
        session.navigation.grid_action.setChecked(False)
        commands.home()
        report["fit_heights"] = [height_grid, view.getCameraNode().height.getValue()]
        check(
            "construction grid does not enlarge Home fit",
            abs(view.getCameraNode().height.getValue() - height_grid) < 1e-4,
        )
        session.navigation.camera("Perspective")
        check("camera menu changes the native projection", view.getCameraType() == "Perspective")
        session.navigation.camera("Orthographic")
        check(
            "camera menu restores orthographic projection", view.getCameraType() == "Orthographic"
        )
        session.navigation.set_mode("pan")
        check(
            "navigation modes are mutually exclusive",
            session.navigation.mode_buttons["pan"].isChecked()
            and not session.navigation.mode_buttons["orbit"].isChecked(),
        )
        viewport = next(
            w
            for w in session.mdi.activeSubWindow().findChildren(QtWidgets.QWidget)
            if session.filter.is_viewport(w) and w.isVisible()
        )

        def drag():
            for kind, position, button, buttons in (
                (
                    QtCore.QEvent.MouseButtonPress,
                    QtCore.QPointF(200, 200),
                    QtCore.Qt.LeftButton,
                    QtCore.Qt.LeftButton,
                ),
                (
                    QtCore.QEvent.MouseMove,
                    QtCore.QPointF(225, 210),
                    QtCore.Qt.NoButton,
                    QtCore.Qt.LeftButton,
                ),
                (
                    QtCore.QEvent.MouseMove,
                    QtCore.QPointF(255, 225),
                    QtCore.Qt.NoButton,
                    QtCore.Qt.LeftButton,
                ),
                (
                    QtCore.QEvent.MouseButtonRelease,
                    QtCore.QPointF(255, 225),
                    QtCore.Qt.LeftButton,
                    QtCore.Qt.NoButton,
                ),
            ):
                QtWidgets.QApplication.sendEvent(
                    viewport,
                    QtGui.QMouseEvent(kind, position, button, buttons, QtCore.Qt.NoModifier),
                )
            QtWidgets.QApplication.processEvents()

        orientation = view.getCameraOrientation().Q
        position = tuple(view.getCameraNode().position.getValue())
        drag()
        check(
            "Pan button makes left drag translate without rotation",
            view.getCameraOrientation().Q == orientation
            and tuple(view.getCameraNode().position.getValue()) != position,
        )
        session.navigation.set_mode("orbit")
        drag()
        check(
            "Orbit button makes left drag rotate the native camera",
            view.getCameraOrientation().Q != orientation,
        )
        session.navigation.set_mode(None)
        other = App.newDocument("AzWorkspaceSecond")
        session.tick()
        index = next(
            i
            for i in range(session.ribbon.documents.count())
            if session.ribbon.documents.tabData(i) == doc.Name
        )
        session.ribbon.documents.activate_document(index)
        check("top tabs activate the native design", Gui.activeDocument().Document == doc)
        session.tick()
        check(
            "Browser follows the newly active document",
            (doc.Name, body.Name) in session.browser.items,
        )
        before = {name: session.appearance.saved.get(name) for name in session.appearance.values}
        original_style = session.original_style
        original_menu = session.original_menu_visible
        Gui.activateWorkbench("PartDesignWorkbench")
        contents = {
            name: (kind, value)
            for kind, name, value in App.ParamGet(
                "User parameter:BaseApp/Preferences/View"
            ).GetContents()
        }
        check(
            "leaving restores every changed canvas preference including absence",
            all(contents.get(name) == value for name, value in before.items()),
        )
        main = Gui.getMainWindow()
        check(
            "leaving restores the prior application stylesheet", main.styleSheet() == original_style
        )
        check(
            "leaving restores the prior menu visibility",
            (not main.menuBar().isHidden()) == original_menu,
        )
        check(
            "leaving removes the custom workspace widgets",
            not main.findChildren(QtWidgets.QToolBar, "AzDesignRibbonBar")
            and not main.findChildren(QtWidgets.QDockWidget, "AzDesignBrowserDock"),
        )
        Gui.activateWorkbench("AzDesignWorkbench")
        current().tick()
        check(
            "re-entry builds one workspace and preserves the solid",
            len(main.findChildren(QtWidgets.QToolBar, "AzDesignRibbonBar")) == 1
            and pocket.Shape.isValid()
            and abs(pocket.Shape.Volume - (32000 - 128 * 3.141592653589793)) < 1e-5,
        )
        view.setAnimationEnabled(True)
        report["passed"] = True
    except BaseException:
        report["error"] = traceback.format_exc()
        App.Console.PrintError(report["error"])
    finally:
        if current():
            current().navigation.grid_action.setChecked(original_grid)
        Path(report_path).write_text(json.dumps(report, indent=2))
    return report
