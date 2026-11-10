# SPDX-License-Identifier: LGPL-2.1-or-later
"""Design-owned Mirror / Linear Pattern with native PartDesign feature history.

Conservative first implementation: select one eligible solid feature in a
single Body; choose a Body origin plane or axis; never make a baked copy.
A failed OCCT result is rolled back, not left in the model.
"""
import FreeCADGui as Gui
from .qt import QtWidgets
from .features import DesignError, owner_body


def selected_feature():
    selected = Gui.Selection.getSelection()
    if len(selected) != 1:
        raise DesignError("Select one solid feature (Pad, Pocket, Hole, etc.) in the Browser.")
    feature = selected[0]
    if not feature.isDerivedFrom("PartDesign::Feature"):
        raise DesignError("Select a Part Design feature to transform.")
    body = owner_body(feature)
    if body is None:
        raise DesignError("The selected feature must belong to a Body.")
    if not hasattr(feature, "Shape") or feature.Shape.isNull():
        raise DesignError("The selected feature does not contain a valid shape.")
    if feature == body.Tip and feature.TypeId in ("PartDesign::Mirrored", "PartDesign::LinearPattern"):
        raise DesignError("Select the original Pad, Pocket or Hole feature, not its existing transformation.")
    return feature, body


def origin_reference(body, role):
    origin = getattr(body, "Origin", None)
    if origin is None:
        raise DesignError("This body has no origin reference system.")
    matches = [obj for obj in origin.OriginFeatures if getattr(obj, "Role", "") == role]
    if len(matches) != 1:
        raise DesignError("Cannot locate the Body origin reference: " + role)
    return matches[0]


def parameters(mode, feature):
    dialog = QtWidgets.QDialog(Gui.getMainWindow())
    dialog.setWindowTitle(("Mirror" if mode == "mirror" else "Linear Pattern") + " · " + feature.Label)
    layout = QtWidgets.QVBoxLayout(dialog)
    explanation = QtWidgets.QLabel(
        "Create an editable native transformation of the selected feature. "
        "The result remains in this Body's parametric history."
    )
    explanation.setWordWrap(True)
    layout.addWidget(explanation)
    form = QtWidgets.QFormLayout()
    reference = QtWidgets.QComboBox()
    roles = (("XY plane", "XY_Plane"), ("XZ plane", "XZ_Plane"), ("YZ plane", "YZ_Plane")) if mode == "mirror" else (
        ("X axis", "X_Axis"), ("Y axis", "Y_Axis"), ("Z axis", "Z_Axis")
    )
    for name, role in roles:
        reference.addItem(name, role)
    form.addRow("Mirror plane" if mode == "mirror" else "Direction", reference)
    repetitions, spacing = None, None
    if mode == "linear":
        repetitions = QtWidgets.QSpinBox()
        repetitions.setRange(2, 200)
        repetitions.setValue(3)
        form.addRow("Occurrences (including original)", repetitions)
        spacing = QtWidgets.QDoubleSpinBox()
        spacing.setRange(0.01, 100000)
        spacing.setDecimals(3)
        spacing.setSuffix(" mm")
        spacing.setValue(20)
        form.addRow("Spacing", spacing)
    layout.addLayout(form)
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    if dialog.exec() != QtWidgets.QDialog.Accepted:
        return None
    return reference.currentData(), (repetitions.value() if repetitions else 0), (
        spacing.value() if spacing else 0.0
    )


def show(mode):
    if Gui.Control.activeDialog():
        raise DesignError("Finish or cancel the current sketch/task first.")
    if mode not in ("mirror", "linear"):
        raise DesignError("Unknown pattern mode.")
    feature, body = selected_feature()
    config = parameters(mode, feature)
    if config is None:
        return False
    role, count, spacing = config
    axis = origin_reference(body, role)
    doc = body.Document
    previous_tip = body.Tip
    previous_visible = {obj.Name: obj.ViewObject.Visibility for obj in body.Group if obj.ViewObject}
    doc.openTransaction("Design: " + ("Mirror" if mode == "mirror" else "Linear pattern"))
    try:
        transform = body.newObject(
            "PartDesign::Mirrored" if mode == "mirror" else "PartDesign::LinearPattern",
            "Mirror" if mode == "mirror" else "LinearPattern",
        )
        if "TransformMode" in transform.PropertiesList:
            transform.TransformMode = "Features"
        if "Originals" not in transform.PropertiesList:
            raise DesignError("The native pattern feature lacks an Originals property.")
        transform.Originals = [feature]
        if mode == "mirror":
            transform.MirrorPlane = (axis, [""])
        else:
            transform.Direction = (axis, [""])
            transform.Mode = "Spacing"
            transform.Offset = spacing
            transform.Occurrences = count
        doc.recompute()
        shape = transform.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
            raise DesignError(
                "The transformation did not form one valid solid. "
                "Check the reference, direction and overlap with the existing Body."
            )
        body.Tip = transform
        if previous_tip and previous_tip.ViewObject:
            previous_tip.ViewObject.Visibility = False
        transform.ViewObject.Visibility = True
        doc.recompute()
        doc.commitTransaction()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(transform)
        return transform
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        restored = doc.getObject(previous_tip.Name) if previous_tip else None
        if restored:
            body.Tip = restored
        for name, visible in previous_visible.items():
            obj = doc.getObject(name)
            if obj is not None and obj.ViewObject:
                obj.ViewObject.Visibility = visible
        raise
