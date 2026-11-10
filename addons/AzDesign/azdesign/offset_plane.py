# SPDX-License-Identifier: LGPL-2.1-or-later
"""A compact offset-plane workflow backed by a native PartDesign datum plane.

Avoid the full Attachment task for the common Fusion-style offset workflow.
Advanced attachment modes remain available through native FreeCAD Properties.
"""
import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtWidgets
from . import modeling


def _selected_support(doc):
    """Use a selected planar face or datum plane, never a curved face."""
    import Part
    for item in Gui.Selection.getSelectionEx():
        obj = item.Object
        if obj.Document != doc:
            continue
        if obj.isDerivedFrom("PartDesign::Plane"):
            return obj, [""]
        for name, shape in zip(item.SubElementNames, item.SubObjects):
            if name.startswith("Face") and hasattr(shape, "Surface"):
                if not isinstance(shape.Surface, Part.Plane):
                    raise modeling.ModelingError(
                        "Select a flat face for Offset Plane, not a curved face."
                    )
                return obj, [name]
    return None


def _body(doc, selected):
    owner = modeling.body_of(selected[0]) if selected else None
    if owner:
        return owner
    body = modeling.active_body()
    if body:
        return body
    bodies = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Body")]
    if len(bodies) == 1:
        return bodies[0]
    if len(bodies) > 1:
        raise modeling.ModelingError(
            "Select the intended Body before creating an offset plane."
        )
    raise modeling.ModelingError("Create or select a Body before adding an offset plane.")


def show():
    if Gui.Control.activeDialog() or modeling.in_sketch():
        raise modeling.ModelingError(
            "Finish or cancel the active sketch/task before creating an offset plane."
        )
    doc = modeling.current_document()
    if doc is None:
        raise modeling.ModelingError("Open a design before creating an offset plane.")
    selected = _selected_support(doc)
    body = _body(doc, selected)
    choices = [("XY — Top", "XY_Plane"), ("XZ — Front", "XZ_Plane"),
               ("YZ — Right", "YZ_Plane")]
    dialog = QtWidgets.QDialog(Gui.getMainWindow())
    dialog.setWindowTitle("Offset Plane · Az Design")
    dialog.setMinimumWidth(370)
    form = QtWidgets.QFormLayout(dialog)
    source = QtWidgets.QComboBox(dialog)
    if selected:
        obj, subs = selected
        title = obj.Label + (" / " + subs[0] if subs[0] else "")
        source.addItem("Selected: " + title, "selected")
    for title, role in choices:
        source.addItem(title, role)
    form.addRow("Reference", source)
    distance = QtWidgets.QLineEdit(dialog)
    distance.setText("0 mm")
    distance.setPlaceholderText("e.g. 12 mm or -1/4 in")
    form.addRow("Offset (normal)", distance)
    hint = QtWidgets.QLabel(
        "Positive or negative distance along the selected plane's normal.\n"
        "Creates a real editable PartDesign Datum Plane.", dialog
    )
    hint.setWordWrap(True)
    form.addRow(hint)
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
        parent=dialog
    )
    form.addRow(buttons)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    if (getattr(dialog, "exec", None) or dialog.exec_)() != QtWidgets.QDialog.Accepted:
        return None
    chosen = source.currentData()
    try:
        value = App.Units.Quantity(distance.text().strip())
        if value.Unit not in (App.Units.Unit(), App.Units.Length):
            raise ValueError("Offset must be a length.")
        millimeters = float(value.Value)
        import math
        if not math.isfinite(millimeters):
            raise ValueError("Offset must be finite.")
    except Exception as exc:
        raise modeling.ModelingError(
            "Enter an offset such as 5 mm, -5 mm, or 0.25 in."
        ) from exc
    support = selected
    if chosen != "selected":
        origin = next(
            (o for o in body.Origin.OriginFeatures
             if getattr(o, "Role", None) == chosen), None
        )
        if origin is None:
            raise modeling.ModelingError("This Body has no " + chosen + " origin plane.")
        support = (origin, [""])
    if not support:
        raise modeling.ModelingError("Select a planar reference first.")
    doc.openTransaction("Az: Offset plane")
    try:
        plane = body.newObject("PartDesign::Plane", "DatumPlane")
        prop = "AttachmentSupport" if "AttachmentSupport" in plane.PropertiesList else "Support"
        setattr(plane, prop, support)
        plane.MapMode = "FlatFace"
        plane.AttachmentOffset = App.Placement(
            App.Vector(0, 0, millimeters), App.Rotation()
        )
        doc.recompute()
        if "Invalid" in plane.State or "Error" in plane.State:
            raise modeling.ModelingError(
                "FreeCAD could not attach the plane to this reference."
            )
        plane.Label = "Offset Plane (" + distance.text().strip() + ")"
        plane.ViewObject.Visibility = True
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(plane)
    return plane
