# SPDX-License-Identifier: LGPL-2.1-or-later
"""Create a dimensioned, solver-native rectangle in the active sketch.

The four sides, Coincident/Horizontal/Vertical constraints, origin location
and two driving dimensions are real Sketcher geometry. Nothing is drawn as
a decorative overlay and all edits remain in the FCStd document.
"""

import math
import FreeCAD as App
import Part
import Sketcher
from .features import DesignError


def dimensioned_rectangle(sketch, width, height):
    """Add a fully constrained rectangle anchored to the sketch origin.

    Returns (four geometry indices, width constraint index, height index).
    A single native transaction owns every entity and constraint; an error
    leaves the original sketch unchanged. Use a fresh/empty sketch only:
    it avoids creating overlapping duplicate faces by accident.
    """
    if sketch is None or not sketch.isDerivedFrom("Sketcher::SketchObject"):
        raise DesignError("Open a Sketch before creating a sized rectangle.")
    if sketch.GeometryCount != 0:
        raise DesignError(
            "Sized Rectangle is for an empty sketch. Use Rectangle and "
            "Smart Dimension to add or size shapes in an existing sketch."
        )
    try:
        width, height = float(width), float(height)
    except (ValueError, TypeError) as exc:
        raise DesignError("Enter numeric rectangle dimensions.") from exc
    if not all(math.isfinite(n) and 0.01 <= n <= 100000.0 for n in (width, height)):
        raise DesignError("Width and height must be between 0.01 and 100000 mm.")
    doc = sketch.Document
    doc.openTransaction("Az: Sized Rectangle")
    try:
        corners = [
            App.Vector(0, 0, 0), App.Vector(width, 0, 0),
            App.Vector(width, height, 0), App.Vector(0, height, 0),
        ]
        indices = []
        for i in range(4):
            indices.append(sketch.addGeometry(
                Part.LineSegment(corners[i], corners[(i + 1) % 4]), False
            ))
        a, b, c, d = indices
        constraints = [
            Sketcher.Constraint("Coincident", a, 2, b, 1),
            Sketcher.Constraint("Coincident", b, 2, c, 1),
            Sketcher.Constraint("Coincident", c, 2, d, 1),
            Sketcher.Constraint("Coincident", d, 2, a, 1),
            Sketcher.Constraint("Horizontal", a),
            Sketcher.Constraint("Vertical", b),
            Sketcher.Constraint("Horizontal", c),
            Sketcher.Constraint("Vertical", d),
            Sketcher.Constraint("Coincident", a, 1, -1, 1),
            Sketcher.Constraint("Distance", a, width),
            Sketcher.Constraint("Distance", b, height),
        ]
        # Individual creation reliably retains the native constraint IDs,
        # even on old Sketcher runtimes where batch addConstraint differs.
        ids = [sketch.addConstraint(item) for item in constraints]
        doc.recompute()
        if sketch.Shape.isNull() or len(sketch.Shape.Edges) != 4:
            raise DesignError("FreeCAD could not solve the sized rectangle.")
        doc.commitTransaction()
        return tuple(indices), ids[-2], ids[-1]
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise


def prompt_sized_rectangle():
    """Small typed-size popup while editing a sketch; ribbon owns the command."""
    import FreeCADGui as Gui
    from . import modeling
    from .qt import QtWidgets
    sketch = modeling.in_sketch()
    if not sketch:
        raise DesignError("Edit an empty sketch before using Sized Rectangle.")
    dialog = QtWidgets.QDialog(Gui.getMainWindow())
    dialog.setWindowTitle("Sized Rectangle · Az Design")
    dialog.setObjectName("AzSizedRectangleDialog")
    layout = QtWidgets.QVBoxLayout(dialog)
    help_label = QtWidgets.QLabel(
        "Create a rectangle at the sketch origin with native width and "
        "height dimensions. Edit either dimension later using Sketcher."
    )
    help_label.setWordWrap(True)
    layout.addWidget(help_label)
    form = QtWidgets.QFormLayout()
    width = QtWidgets.QDoubleSpinBox()
    height = QtWidgets.QDoubleSpinBox()
    for control, default in ((width, 60), (height, 40)):
        control.setRange(0.01, 100000)
        control.setDecimals(3)
        control.setSuffix(" mm")
        control.setValue(default)
    form.addRow("Width", width)
    form.addRow("Height", height)
    layout.addLayout(form)
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    execute = getattr(dialog, "exec", None) or dialog.exec_
    if execute() != QtWidgets.QDialog.Accepted:
        return False
    dimensioned_rectangle(sketch, width.value(), height.value())
    Gui.activeDocument().activeView().fitAll()
    return True
