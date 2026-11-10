# SPDX-License-Identifier: LGPL-2.1-or-later
"""Transactional quick dimension changes for known FreeCAD features.

Never attempt to edit a modeled Hole or an unknown topological link. Native
undo, parametric inputs and dependent solids stay authoritative.
"""

from .features import DesignError


def dimension_property(feature):
    if feature is None:
        return None
    kind = getattr(feature, "TypeId", "")
    if getattr(feature, "AzType", "") == "AzExtrude":
        return "Length" if "Length" in feature.PropertiesList else None
    if kind in ("PartDesign::Pad", "PartDesign::Pocket"):
        candidate = "Length"
    elif kind == "PartDesign::Fillet":
        candidate = "Radius"
    elif kind == "PartDesign::Chamfer":
        candidate = "Size"
    else:
        return None
    return candidate if candidate in getattr(feature, "PropertiesList", ()) else None


def dimension_value(feature):
    name = dimension_property(feature)
    if name is None:
        raise DesignError("Use Edit for this feature; Quick Dimension is unavailable.")
    value = getattr(feature, name)
    return name, float(getattr(value, "Value", value))


def change_dimension(feature, value):
    """One native transaction, with downstream validation and undo."""
    name, old_value = dimension_value(feature)
    try:
        value = float(value)
    except (ValueError, TypeError) as exc:
        raise DesignError("Enter a numeric dimension.") from exc
    if not (0.001 <= value <= 100000):
        raise DesignError("Dimension must be between 0.001 and 100000 mm.")
    if abs(value - old_value) < 0.000001:
        return old_value

    doc = feature.Document
    from .features import owner_body
    body = owner_body(feature)
    # Keep track of pre-existing failures, so repairing an already broken
    # feature is not prohibited by unrelated errors elsewhere in the file.
    original_errors = {
        o.Name for o in doc.Objects
        if o.isDerivedFrom("PartDesign::Feature")
        and (
            "Invalid" in getattr(o, "State", ())
            or bool(getattr(o, "Error", ""))
        )
    }
    doc.openTransaction("Az: Change " + name)
    try:
        setattr(feature, name, value)
        doc.recompute()
        relevant = list(body.Group) if body else [feature]
        if feature in relevant:
            relevant = relevant[relevant.index(feature):]
        failures = []
        for obj in relevant:
            if not obj.isDerivedFrom("PartDesign::Feature"):
                continue
            if obj.Name in original_errors:
                continue
            shape = getattr(obj, "Shape", None)
            if (
                "Invalid" in getattr(obj, "State", ())
                or bool(getattr(obj, "Error", ""))
                or (shape is not None and (shape.isNull() or not shape.isValid()))
            ):
                failures.append(obj.Label)
        if failures:
            raise DesignError(
                "This dimension breaks: " + ", ".join(failures)
                + ". Reverted to the previous value."
            )
        doc.commitTransaction()
        return value
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise


def prompt(feature, parent=None):
    from .qt import QtWidgets
    name, value = dimension_value(feature)
    entered, accepted = QtWidgets.QInputDialog.getDouble(
        parent, "Quick Dimension · " + feature.Label,
        name + " (mm)", value, 0.001, 100000.0, 3,
    )
    if not accepted:
        return False
    change_dimension(feature, entered)
    return True
