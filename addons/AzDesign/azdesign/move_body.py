# SPDX-License-Identifier: LGPL-2.1-or-later
"""Design-owned Move: parametric body/component placement with native Undo.

A Part Design *feature* is not moved independently of its support chain:
select its owning Body instead. This avoids broken attached sketches and
non-parametric shape copies.
"""
import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtWidgets
from .features import DesignError


def selected_movable():
    selected = Gui.Selection.getSelection()
    if len(selected) != 1:
        raise DesignError("Select one Body or component in the Browser to Move.")
    obj = selected[0]
    if obj.isDerivedFrom("PartDesign::Body") or obj.isDerivedFrom("App::Part"):
        return obj
    if obj.isDerivedFrom("PartDesign::Feature"):
        from .features import owner_body
        owner = owner_body(obj)
        if owner:
            return owner
    raise DesignError("Move needs a Body or component, not individual sketch geometry.")


def show():
    if Gui.Control.activeDialog():
        raise DesignError("Finish or cancel the current sketch/task before moving a body.")
    obj = selected_movable()
    if "Placement" not in obj.PropertiesList:
        raise DesignError("The selected body does not expose a movable Placement.")
    dialog = QtWidgets.QDialog(Gui.getMainWindow())
    dialog.setWindowTitle("Move · " + obj.Label)
    dialog.setMinimumWidth(380)
    layout = QtWidgets.QVBoxLayout(dialog)
    heading = QtWidgets.QLabel("MOVE BODY / COMPONENT")
    heading.setStyleSheet("font-weight: 700; font-size: 16px;")
    layout.addWidget(heading)
    explanation = QtWidgets.QLabel(
        "Change the position of the complete parametric body in millimetres. "
        "Its sketches and features stay together. Rotation is unchanged."
    )
    explanation.setWordWrap(True)
    layout.addWidget(explanation)
    form = QtWidgets.QFormLayout()
    axes = []
    for label, coordinate in zip(("X", "Y", "Z"),
                                 (obj.Placement.Base.x, obj.Placement.Base.y, obj.Placement.Base.z)):
        spin = QtWidgets.QDoubleSpinBox(dialog)
        spin.setDecimals(3)
        spin.setRange(-100000.0, 100000.0)
        spin.setSuffix(" mm")
        spin.setValue(coordinate)
        form.addRow(label, spin)
        axes.append(spin)
    layout.addLayout(form)
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    if dialog.exec() != QtWidgets.QDialog.Accepted:
        return False
    new_coordinates = tuple(field.value() for field in axes)
    old = obj.Placement
    if all(abs(a-b) < 1e-7 for a,b in zip(new_coordinates, (old.Base.x, old.Base.y, old.Base.z))):
        return False
    doc = obj.Document
    doc.openTransaction("Design: Move " + obj.Label)
    try:
        placement = App.Placement(App.Vector(*new_coordinates), old.Rotation)
        obj.Placement = placement
        doc.recompute()
        if "Invalid" in getattr(obj, "State", ()):
            raise DesignError("The move invalidated the selected component.")
        doc.commitTransaction()
        return True
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise
