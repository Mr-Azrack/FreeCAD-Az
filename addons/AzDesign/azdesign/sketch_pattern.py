# SPDX-License-Identifier: LGPL-2.1-or-later
"""Editable rectangular array of native Sketcher circles (hole centers).

Unlike PartDesign LinearPattern this works while a sketch is being edited.
All copies are real, solver-constrained circles; the same source sketch can
feed one native Hole feature for every location. No cosmetic copy overlays.
"""

import math

import FreeCAD as App
import Part
import Sketcher

from .features import DesignError


def circle_indices(sketch):
    """Exclude arcs, construction circles and external/reference geometry."""
    if sketch is None or not sketch.isDerivedFrom("Sketcher::SketchObject"):
        return []
    return [
        i for i, geom in enumerate(sketch.Geometry)
        if type(geom) is Part.Circle and not sketch.getConstruction(i)
    ]


def validate(sketch, source, columns, rows, pitch_x, pitch_y):
    if sketch is None or not sketch.isDerivedFrom("Sketcher::SketchObject"):
        raise DesignError("Edit a sketch containing a circle to create a hole pattern.")
    try:
        source, columns, rows = int(source), int(columns), int(rows)
        pitch_x, pitch_y = float(pitch_x), float(pitch_y)
    except (ValueError, TypeError) as exc:
        raise DesignError("Enter valid pattern counts and distances.") from exc
    if source not in circle_indices(sketch):
        raise DesignError("Choose a normal (non-construction) circle as the pattern source.")
    if not (1 <= columns <= 10 and 1 <= rows <= 10):
        raise DesignError("Pattern columns and rows must be between 1 and 10.")
    if columns * rows <= 1 or columns * rows > 100:
        raise DesignError("Choose 2–100 total occurrences, including the original.")
    if not all(math.isfinite(value) and abs(value) <= 100000 for value in (pitch_x, pitch_y)):
        raise DesignError("Pitch must be a finite distance within 100,000 mm.")
    if columns > 1 and abs(pitch_x) < 0.001:
        raise DesignError("Enter a nonzero X pitch for multiple columns.")
    if rows > 1 and abs(pitch_y) < 0.001:
        raise DesignError("Enter a nonzero Y pitch for multiple rows.")
    original = sketch.Geometry[source]
    # Distinguish duplicate centers from legitimate overlapping circles.
    previous = [(g.Center.x, g.Center.y) for i, g in enumerate(sketch.Geometry)
                if type(g) is Part.Circle and i != source]
    for y in range(rows):
        for x in range(columns):
            if x == 0 and y == 0:
                continue
            center_x = original.Center.x + x * pitch_x
            center_y = original.Center.y + y * pitch_y
            if any(math.hypot(center_x - px, center_y - py) < 0.001
                   for px, py in previous):
                raise DesignError(
                    "A pattern location coincides with an existing circle. "
                    "Change the pitch or choose a different source."
                )
    return source, columns, rows, pitch_x, pitch_y


def pattern_circles(sketch, source, columns=2, rows=2, pitch_x=40, pitch_y=30,
                    manage_transaction=True):
    """Create a native 2D circle pattern with dimensional and equal constraints.

    Each new center is constrained relative to the original, so editing the
    source circle position or radius updates all four hole centers. Offsets
    are real driving constraints, not fixed/baked locations.
    """
    source, columns, rows, pitch_x, pitch_y = validate(
        sketch, source, columns, rows, pitch_x, pitch_y
    )
    first = sketch.Geometry[source]
    doc = sketch.Document
    if manage_transaction:
        doc.openTransaction("Design: Rectangular sketch pattern")
    created = []
    try:
        for y in range(rows):
            for x in range(columns):
                if x == 0 and y == 0:
                    continue
                dx, dy = x * pitch_x, y * pitch_y
                point = App.Vector(first.Center.x + dx, first.Center.y + dy, 0)
                index = sketch.addGeometry(
                    Part.Circle(point, App.Vector(0, 0, 1), first.Radius), False
                )
                created.append(index)
                # All patterned hole diameters stay linked to the source.
                added_constraints = []
                added_constraints.append(sketch.addConstraint(
                    Sketcher.Constraint("Equal", source, index)))
                # Circle center uses point-position 3 in Sketcher.
                # Zero-length DistanceX/DistanceY dimensions are invalid;
                # substitute exact geometric alignment constraints instead.
                if abs(dx) >= 0.001:
                    added_constraints.append(sketch.addConstraint(
                        Sketcher.Constraint("DistanceX", source, 3, index, 3, dx)
                    ))
                else:
                    added_constraints.append(sketch.addConstraint(
                        Sketcher.Constraint("Vertical", source, 3, index, 3)
                    ))
                if abs(dy) >= 0.001:
                    added_constraints.append(sketch.addConstraint(
                        Sketcher.Constraint("DistanceY", source, 3, index, 3, dy)
                    ))
                else:
                    added_constraints.append(sketch.addConstraint(
                        Sketcher.Constraint("Horizontal", source, 3, index, 3)
                    ))
                # FreeCAD Sketcher virtual space hides generated constraint
                # glyphs/dimensions without disabling the solver constraints.
                # Do not modify source/user-authored constraint visibility.
                hide = getattr(sketch, "setVirtualSpace", None)
                if callable(hide):
                    for constraint_id in added_constraints:
                        if isinstance(constraint_id, int) and constraint_id >= 0:
                            hide(constraint_id, True)
        doc.recompute()
        state = tuple(str(x) for x in getattr(sketch, "State", ()))
        if "Invalid" in state or sketch.Shape.isNull():
            raise DesignError(
                "The Sketcher solver rejected this circle pattern. "
                "Adjust spacing or constraints before retrying."
            )
        if manage_transaction:
            doc.commitTransaction()
        return tuple(created)
    except Exception:
        if manage_transaction:
            doc.abortTransaction()
            doc.recompute()
        raise


def selected_source(sketch):
    import FreeCADGui as Gui
    eligible = set(circle_indices(sketch))
    hits = []
    for item in Gui.Selection.getSelectionEx():
        if item.Object != sketch:
            continue
        for name in item.SubElementNames:
            if name.startswith("Edge") and name[4:].isdigit():
                index = int(name[4:]) - 1
                if index in eligible:
                    hits.append(index)
    return hits[0] if len(set(hits)) == 1 else None


def show():
    import FreeCADGui as Gui
    from .qt import QtWidgets
    from . import modeling

    sketch = modeling.in_sketch()
    if sketch is None:
        raise DesignError("Start editing a sketch, then choose Sketch → Rectangular Pattern.")
    candidates = circle_indices(sketch)
    if not candidates:
        raise DesignError(
            "Draw one circle in the sketch first. Pattern creates real circle centers for Hole."
        )
    dialog = QtWidgets.QDialog(Gui.getMainWindow())
    dialog.setWindowTitle("Rectangular Sketch Pattern · Design")
    dialog.setMinimumWidth(380)
    layout = QtWidgets.QVBoxLayout(dialog)
    hint = QtWidgets.QLabel(
        "Repeat one circle as an editable 2D array. Choose 2 × 2 for four holes. "
        "The original counts as the first location, and copies keep the same diameter."
    )
    hint.setWordWrap(True)
    layout.addWidget(hint)
    form = QtWidgets.QFormLayout()
    source_input = QtWidgets.QComboBox()
    preferred = selected_source(sketch)
    for i in candidates:
        center = sketch.Geometry[i].Center
        source_input.addItem(
            "Circle {}  ·  ({:.2f}, {:.2f}) mm".format(i + 1, center.x, center.y), i
        )
    if preferred is not None:
        source_input.setCurrentIndex(candidates.index(preferred))
    form.addRow("Source circle", source_input)
    cols = QtWidgets.QSpinBox()
    rows = QtWidgets.QSpinBox()
    for control in (cols, rows):
        control.setRange(1, 10)
        control.setValue(2)
    px = QtWidgets.QDoubleSpinBox()
    py = QtWidgets.QDoubleSpinBox()
    for field, default in ((px, 45.0), (py, 45.0)):
        field.setRange(-100000, 100000)
        field.setDecimals(3)
        field.setSuffix(" mm")
        field.setValue(default)
    form.addRow("Columns", cols)
    form.addRow("Rows", rows)
    form.addRow("X center spacing", px)
    form.addRow("Y center spacing", py)
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
    created = pattern_circles(
        sketch, source_input.currentData(), cols.value(), rows.value(),
        px.value(), py.value()
    )
    Gui.Selection.clearSelection()
    Gui.activeDocument().activeView().fitAll()
    from .commands import notify
    notify(
        "{} sketch circles ready for Hole. Finish Sketch to continue.".format(
            len(created) + 1
        )
    )
    return created
