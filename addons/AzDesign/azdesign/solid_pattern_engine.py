# SPDX-License-Identifier: LGPL-2.1-or-later
"""Transactional native feature pattern engine owned by Design.

Geometry and history are native PartDesign::LinearPattern, while Design owns
selection, settings, preview, accept/cancel and later edits. Nothing gets
committed until the user explicitly accepts the preview.
"""
import math

from .features import DesignError, owner_body


AXES = (
    ("X axis", "X_Axis"),
    ("Y axis", "Y_Axis"),
    ("Z axis", "Z_Axis"),
)


def origin_axis(body, role):
    if role not in dict((key, key) for _, key in AXES):
        raise DesignError("Choose the X, Y or Z origin axis.")
    origin = getattr(body, "Origin", None)
    candidates = getattr(origin, "OriginFeatures", []) if origin else []
    matching = [o for o in candidates if getattr(o, "Role", None) == role]
    if len(matching) != 1:
        raise DesignError("Body origin axis is missing: " + role)
    return matching[0]


def is_eligible(obj):
    if not obj or not hasattr(obj, "isDerivedFrom"):
        return False
    if not obj.isDerivedFrom("PartDesign::Feature"):
        return False
    if getattr(obj, "TypeId", "") in (
        "PartDesign::LinearPattern", "PartDesign::PolarPattern",
        "PartDesign::Mirrored", "PartDesign::MultiTransform",
    ):
        return False
    shape = getattr(obj, "Shape", None)
    return shape is not None and not shape.isNull()


def eligible_in_body(body):
    return [obj for obj in getattr(body, "Group", []) if is_eligible(obj)]


def validate(count, spacing, direction, reversed_direction=False):
    if direction not in {axis for _, axis in AXES}:
        raise DesignError("Choose an origin axis for the pattern.")
    try:
        count = int(count)
        spacing = float(spacing)
    except (TypeError, ValueError) as exc:
        raise DesignError("Choose a numeric occurrence count and spacing.") from exc
    if not 2 <= count <= 200:
        raise DesignError("Number of occurrences must be between 2 and 200.")
    if not math.isfinite(spacing) or spacing < 0.001 or spacing > 100000:
        raise DesignError("Spacing must be from 0.001 to 100000 mm.")
    return count, spacing, direction, bool(reversed_direction)


class PatternDraft:
    """One undoable, cancellable live pattern preview in the actual Body.

    For editing an existing pattern, the original object and downstream
    dependent features stay in their native history instead of opening the
    original PartDesign task panel.
    """

    def __init__(self, feature, existing=None):
        if not is_eligible(feature):
            raise DesignError("Choose a valid solid feature such as a Pad, Pocket or Hole.")
        body = owner_body(feature)
        if body is None:
            raise DesignError("The selected source feature must be inside a Body.")
        if existing is not None:
            if getattr(existing, "TypeId", "") != "PartDesign::LinearPattern":
                raise DesignError("Only a native Linear Pattern can be edited here.")
            if owner_body(existing) != body:
                raise DesignError("The pattern and source must belong to the same Body.")
        self.source = feature
        self.body = body
        self.doc = body.Document
        self.existing = existing
        self.preview_feature = existing
        self.previous_tip = body.Tip
        self.previous_visibility = {
            obj.Name: obj.ViewObject.Visibility
            for obj in body.Group if getattr(obj, "ViewObject", None)
        }
        self.started = False
        self.ready = False

    def preview(self, count, spacing, direction="X_Axis", reversed_direction=False):
        count, spacing, direction, reversed_direction = validate(
            count, spacing, direction, reversed_direction
        )
        axis = origin_axis(self.body, direction)
        if not self.started:
            self.doc.openTransaction(
                "Design: Edit linear pattern" if self.existing
                else "Design: New linear pattern"
            )
            self.started = True
        if self.preview_feature is None:
            self.preview_feature = self.body.newObject(
                "PartDesign::LinearPattern", "DesignLinearPattern"
            )
        obj = self.preview_feature
        if "Originals" not in obj.PropertiesList:
            raise DesignError("Native FreeCAD Linear Pattern has no Originals property.")
        obj.Originals = [self.source]
        if "TransformMode" in obj.PropertiesList:
            obj.TransformMode = "Features"
        obj.Direction = (axis, [""])
        obj.Mode = "Spacing"
        obj.Offset = spacing
        obj.Occurrences = count
        if reversed_direction:
            if "Reversed" not in obj.PropertiesList:
                raise DesignError("This FreeCAD build does not expose reverse pattern direction.")
            obj.Reversed = True
        elif "Reversed" in obj.PropertiesList:
            obj.Reversed = False
        self.doc.recompute()
        shape = obj.Shape
        self.ready = (
            not shape.isNull() and shape.isValid() and len(shape.Solids) == 1
            and "Invalid" not in getattr(obj, "State", ())
        )
        if self.ready:
            if self.existing is None:
                self.body.Tip = obj
                if self.previous_tip and getattr(self.previous_tip, "ViewObject", None):
                    self.previous_tip.ViewObject.Visibility = False
            if getattr(obj, "ViewObject", None):
                obj.ViewObject.Visibility = True
        elif self.existing is None and self.previous_tip:
            self.body.Tip = self.previous_tip
            if getattr(self.previous_tip, "ViewObject", None):
                self.previous_tip.ViewObject.Visibility = True
            if getattr(obj, "ViewObject", None):
                obj.ViewObject.Visibility = False
        self.doc.recompute()
        if not self.ready:
            raise DesignError(
                "No valid single solid for this preview. Try a Pocket/Hole, "
                "reduce spacing, or select a different direction."
            )
        return obj

    def accept(self):
        if not self.started or not self.ready:
            raise DesignError("Create a valid pattern preview before accepting.")
        obj = self.preview_feature
        if self.existing is None:
            self.body.Tip = obj
        self.doc.recompute()
        if obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids) != 1:
            raise DesignError("Cannot save a pattern with invalid native geometry.")
        self.doc.commitTransaction()
        self.started = False
        self.ready = False
        return obj

    def cancel(self):
        if not self.started:
            return
        self.doc.abortTransaction()
        self.doc.recompute()
        self.started = False
        self.ready = False
        if self.previous_tip:
            restored = self.doc.getObject(self.previous_tip.Name)
            if restored and self.existing is None:
                self.body.Tip = restored
        for name, visible in self.previous_visibility.items():
            obj = self.doc.getObject(name)
            if obj is not None and getattr(obj, "ViewObject", None):
                obj.ViewObject.Visibility = visible
        self.doc.recompute()
