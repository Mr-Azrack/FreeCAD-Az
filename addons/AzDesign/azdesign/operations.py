# SPDX-License-Identifier: LGPL-2.1-or-later
"""Undoable creation and editing of complete extrusion operations."""

import uuid
import FreeCAD as App
from . import features, profiles, history, references
from .features import DesignError


def depends_on(obj, target):
    seen, queue = set(), [obj]
    while queue:
        current = queue.pop()
        if current == target:
            return True
        if current.Name in seen:
            continue
        seen.add(current.Name)
        queue.extend(current.OutList)
    return False


def expressions(obj):
    return {name: str(expression) for name, expression in obj.ExpressionEngine}


def spec_for(obj):
    expr = expressions(obj)
    return {
        "source": obj.Source,
        "regions": list(obj.Regions),
        "whole": obj.WholeSketch,
        "operation": str(obj.Operation),
        "target": features.owner_body(obj),
        "distance": expr.get("Length", obj.Length.UserString),
        "distance2": expr.get("Length2", obj.Length2.UserString),
        "direction": str(obj.Direction),
        "reversed": obj.Reversed,
        "extent": str(obj.Extent),
        "to_face": obj.UpToFace,
        "offset": expr.get("StartOffset", obj.StartOffset.UserString),
        "taper": expr.get("TaperAngle", obj.TaperAngle.UserString),
        "taper2": expr.get("TaperAngle2", obj.TaperAngle2.UserString),
    }


class Operation:
    def __init__(self, doc, editing=None):
        features.ensure_calculator()
        self.doc = doc
        self.closed = False
        self.outputs = []
        self.new_names = []
        self.editing = []
        self.original_tips = {
            b.Name: b.Tip.Name if b.Tip else None
            for b in doc.Objects
            if b.isDerivedFrom("PartDesign::Body")
        }
        self.original_visibility = {
            o.Name: o.ViewObject.Visibility for o in doc.Objects if App.GuiUp and o.ViewObject
        }
        self.original_bases = {
            b.Name: features.body_tip(b) for b in doc.Objects if b.isDerivedFrom("PartDesign::Body")
        }
        if editing:
            group = editing.FeatureGroup
            self.editing = [
                o
                for o in doc.Objects
                if getattr(o, "AzType", "") == "AzExtrude"
                and (o == editing or (group and o.FeatureGroup == group))
            ]
            for obj in self.editing:
                body = features.owner_body(obj)
                self.original_bases[body.Name] = obj.BaseFeature
        self.group = self.editing[0].FeatureGroup if self.editing else uuid.uuid4().hex
        self.original_parents = {o.Name: features.owner_body(o).Name for o in self.editing}
        self.original_operations = {o.Name: str(o.Operation) for o in self.editing}
        self.last_spec = None
        # FreeCAD 1.1 may not restore a removed dynamic property on abort.
        # Remember the legacy type/value before migration to permit Cancel.
        self._legacy_links = []
        for obj in self.editing:
            for name, old_type, group in (
                ("Source", "App::PropertyLinkSub", "Profiles"),
                ("UpToFace", "App::PropertyLinkSub", "Extrude"),
                ("SourceFrame", "App::PropertyLink", "Az Design"),
                ("LimitFrame", "App::PropertyLink", "Az Design"),
            ):
                if name in obj.PropertiesList and obj.getTypeIdOfProperty(name) == old_type:
                    self._legacy_links.append((obj.Name, name, old_type, group, getattr(obj, name)))
        features.begin_transaction(self.doc, "Az: Edit Extrude" if self.editing else "Az: Extrude")
        # Existing 0.4.1 Extrudes used local-only LinkSub for profiles
        # belonging to other Bodies. Migrate while the editing transaction
        # is open so Reject/Cancel can roll it back atomically.
        try:
            for obj in self.editing:
                features.upgrade_extrude_links(obj)
        except Exception:
            self.doc.abortTransaction()
            raise

    def _restore_tips(self):
        for name, tip_name in self.original_tips.items():
            body = self.doc.getObject(name)
            tip = self.doc.getObject(tip_name) if tip_name else None
            if body:
                body.Tip = tip

    def _restore_visibility(self):
        if not App.GuiUp:
            return
        for name, visible in self.original_visibility.items():
            obj = self.doc.getObject(name)
            if obj and obj.ViewObject:
                obj.ViewObject.Visibility = visible

    def clear_created(self):
        for obj in self.editing:
            original = self.doc.getObject(self.original_parents[obj.Name])
            current = features.owner_body(obj)
            if current != original:
                if current:
                    current.removeObject(obj)
                original.addObject(obj)
        for name in reversed(self.new_names):
            if self.doc.getObject(name):
                self.doc.removeObject(name)
        self.new_names = []
        self.outputs = []
        self._restore_tips()
        self._restore_visibility()

    def discard_preview(self):
        """Discard transient *new* Extrudes after a failed or empty preview.

        Keep the modeling transaction alive so the user can choose a
        different profile. An edited existing feature must not be deleted:
        its full rollback remains the native Cancel transaction.
        """
        if self.closed:
            return
        if self.editing:
            # Existing features are never disposable. We can restore their
            # visibility/tip but only Cancel guarantees property rollback.
            self._restore_tips()
            self._restore_visibility()
            self.doc.recompute()
            return
        self.clear_created()
        self.doc.recompute()

    def _new_body(self):
        before = {o.Name for o in self.doc.Objects}
        body = self.doc.addObject("PartDesign::Body", "Body")
        self.new_names.extend(o.Name for o in self.doc.Objects if o.Name not in before)
        return body

    def _base(self, body):
        return self.original_bases.get(body.Name)

    def _preflight_existing_body(
        self, source, region_group, spec, operation, target, distance,
        distance2, reverse, taper, taper2, offset, limit
    ):
        """Validate a prospective change BEFORE creating a temporary Body Tip.

        The calculator operates in an independent unsaved document. The
        existing document/history and its visibility are untouched if the
        operation is disconnected or produces no material change.
        """
        base = self._base(target)
        if not base:
            raise DesignError("Select an existing target Body with a solid.")
        source_signature = (
            self.editing[0].SourceFaceSignature
            if self.editing and self.editing[0].Source[0] == source[0]
            else ""
        )
        descriptions = (
            [region.descriptor() for region in region_group]
            if region_group is not None else spec.get("regions", ())
        )
        shape = features.source_shape(
            source, target, descriptions, bool(spec.get("whole", False)),
            source_signature,
        )
        base_shape = features.shape_in_body(base, target)
        face = (
            features.face_in_body(limit, target)
            if spec.get("extent", "Distance") == "To face"
            else None
        )
        try:
            result = features.native_extrusion(
                shape,
                base=base_shape,
                operation=operation,
                distance=distance,
                distance2=distance2,
                direction=spec.get("direction", "One side"),
                reversed=reverse,
                extent=spec.get("extent", "Distance"),
                to_face=face,
                taper=taper,
                taper2=taper2,
                start=offset,
            )
        except DesignError as exc:
            if operation == "Join" and "one connected solid" in str(exc):
                raise DesignError(
                    "Join adds no material connected to this Body. Select a profile "
                    "that touches the solid or choose New body."
                ) from exc
            raise
        tolerance = max(profiles.TOL, base_shape.Volume * 1e-9)
        change = result.Volume - base_shape.Volume
        if operation == "Join" and change <= tolerance:
            raise DesignError(
                "Join adds no material to this Body. Select a profile that "
                "touches the solid, reverse direction, or choose New body."
            )
        if operation == "Cut" and change >= -tolerance:
            raise DesignError(
                "Cut removes no material from this Body. Check the profile "
                "plane and direction or choose a different region."
            )
        if operation == "Intersect" and change >= -tolerance:
            raise DesignError(
                "Intersect does not change this Body. Check the selected "
                "profile or use Join/New body."
            )

    def update(self, spec):
        if self.closed:
            raise DesignError("This operation has closed.")
        source = spec.get("source")
        if not source or source[0] is None:
            raise DesignError("Choose a sketch or planar face.")
        if source[0].Document != self.doc:
            raise DesignError("The source must be in the current document.")
        if any(depends_on(source[0], obj) for obj in self.editing):
            raise DesignError(
                "A feature cannot use its own result or a downstream feature as its profile."
            )
        limit = spec.get("to_face")
        if limit and limit[0] and any(depends_on(limit[0], obj) for obj in self.editing):
            raise DesignError("The end face cannot depend on this feature.")
        context = self.editing[0] if self.editing else source[0]
        raw_distance = features.numeric(spec.get("distance", "10 mm"), context=context, signed=True)
        if abs(raw_distance) < profiles.TOL:
            raise DesignError("Distance must be nonzero.")
        distance2 = features.numeric(spec.get("distance2", "10 mm"), context=context)
        offset = features.numeric(
            spec.get("offset", "0 mm"), context=context, signed=True, zero=True
        )
        taper = features.numeric(
            spec.get("taper", "0 deg"), "angle", context, signed=True, zero=True
        )
        taper2 = features.numeric(
            spec.get("taper2", "0 deg"), "angle", context, signed=True, zero=True
        )
        if abs(taper) >= 89 or abs(taper2) >= 89:
            raise DesignError("Taper must be between -89° and 89°.")
        operation = spec.get("operation", "Auto")
        target = spec.get("target")
        selected = (
            profiles.resolve(source[0], spec.get("regions", []))
            if source[0].isDerivedFrom("Sketcher::SketchObject") and not spec.get("whole", False)
            else None
        )
        reverse = bool(spec.get("reversed", False)) ^ (raw_distance < 0)
        if operation == "Auto":
            base = self._base(target) if target else None
            if base is None:
                operation = "New body"
            else:
                signature = (
                    self.editing[0].SourceFaceSignature
                    if self.editing and self.editing[0].Source[0] == source[0]
                    else ""
                )
                shape = features.source_shape(
                    source, target, spec.get("regions"), spec.get("whole", False), signature
                )
                tool = features.native_extrusion(
                    shape,
                    operation="New body",
                    distance=abs(raw_distance),
                    distance2=distance2,
                    direction=spec.get("direction", "One side"),
                    reversed=reverse,
                    taper=taper,
                    taper2=taper2,
                    start=offset,
                )
                base_shape = features.shape_in_body(base, target)
                overlap = base_shape.common(tool).Volume
                if overlap > profiles.TOL:
                    operation = "Cut"
                    reverse = not reverse  # Pocket's positive direction is opposite Pad's.
                elif base_shape.distToShape(tool)[0] <= profiles.TOL:
                    operation = "Join"
                else:
                    operation = "New body"
        if operation in ("Join", "Cut", "Intersect") and (
            target is None or self._base(target) is None
        ):
            if operation == "Join" and target is not None:
                operation = "New body"
            else:
                raise DesignError("Choose an existing target body.")
        groups = (
            profiles.connected_sets(selected)
            if operation == "New body" and selected
            else [selected]
        )
        if self.editing and len(groups) != len(self.editing):
            raise DesignError(
                "This edit changes the number of bodies. Create separate Extrude features for the changed regions."
            )
        if not self.editing and operation in ("Join", "Cut", "Intersect"):
            # Preflight may be costly, but it prevents invalid temporary
            # FeaturePython objects from taking over the real Body Tip.
            for region_group in groups:
                self._preflight_existing_body(
                    source, region_group, spec, operation, target,
                    abs(raw_distance), distance2, reverse, taper, taper2,
                    offset, limit,
                )
        self.clear_created()
        for index, region_group in enumerate(groups):
            if self.editing:
                obj = self.editing[index]
                body = features.owner_body(obj)
                if operation != "New body" and target != body:
                    dependents = [o for o in obj.InList if o != body and o not in self.editing]
                    if dependents:
                        raise DesignError(
                            "This feature has downstream dependencies. Keep its body or restructure those dependencies first."
                        )
                    body.removeObject(obj)
                    target.addObject(obj)
                    body = target
                elif operation == "New body" and self.original_operations[obj.Name] != "New body":
                    dependents = [o for o in obj.InList if o != body and o not in self.editing]
                    if dependents:
                        raise DesignError(
                            "This feature has downstream dependencies. Create a new Extrude for a separate body."
                        )
                    old_body = body
                    body = self._new_body()
                    old_body.removeObject(obj)
                    body.addObject(obj)
            else:
                reuse_empty = (
                    operation == "New body"
                    and index == 0
                    and target is not None
                    and self.original_bases.get(target.Name) is None
                )
                body = (
                    (target if reuse_empty else self._new_body())
                    if operation == "New body"
                    else target
                )
                obj = features.create_extrude(body, source, operation=operation)
                self.new_names.append(obj.Name)
            previous_source = obj.Source
            if source[1] and str(source[1][0]).lstrip("?").startswith("Face"):
                old_element = (
                    previous_source[1][0].lstrip("?")
                    if previous_source[0] and previous_source[1]
                    else ""
                )
                if (
                    not obj.SourceFaceSignature
                    or previous_source[0] != source[0]
                    or old_element != source[1][0].lstrip("?")
                ):
                    obj.SourceFaceSignature = references.face_signature(source[0], source[1][0])
            else:
                obj.SourceFaceSignature = ""
            obj.Source = source
            source_body = features.owner_body(source[0])
            obj.SourceFrame = source_body if source_body != body else None
            obj.Regions = [r.descriptor() for r in region_group] if region_group is not None else []
            obj.WholeSketch = bool(spec.get("whole", False))
            obj.Operation = operation
            obj.FeatureGroup = self.group
            obj.BaseFeature = self._base(body) if operation != "New body" else None
            obj.Direction = spec.get("direction", "One side")
            obj.Reversed = reverse
            obj.Extent = spec.get("extent", "Distance")
            previous_limit = obj.UpToFace
            if limit and limit[0] and limit[1]:
                old_element = (
                    previous_limit[1][0].lstrip("?")
                    if previous_limit[0] and previous_limit[1]
                    else ""
                )
                if (
                    not obj.LimitFaceSignature
                    or previous_limit[0] != limit[0]
                    or old_element != limit[1][0].lstrip("?")
                ):
                    obj.LimitFaceSignature = references.face_signature(limit[0], limit[1][0])
                limit_body = features.owner_body(limit[0])
                obj.LimitFrame = limit_body if limit_body != body else None
            else:
                obj.LimitFaceSignature = ""
                obj.LimitFrame = None
            obj.UpToFace = limit if limit and limit[0] is not None else None
            for field, text, number in (
                ("Length", spec.get("distance", "10 mm"), abs(raw_distance)),
                ("Length2", spec.get("distance2", "10 mm"), distance2),
                ("StartOffset", spec.get("offset", "0 mm"), offset),
                ("TaperAngle", spec.get("taper", "0 deg"), taper),
                ("TaperAngle2", spec.get("taper2", "0 deg"), taper2),
            ):
                obj.setExpression(field, None)
                setattr(obj, field, number)
                expression = "-(" + text + ")" if field == "Length" and raw_distance < 0 else text
                obj.setExpression(field, expression)
            self.outputs.append(obj)
            history.reveal(body, obj)
            if App.GuiUp:
                source[0].ViewObject.Visibility = False
        self.doc.recompute()
        for obj in self.outputs:
            if (
                obj.Error
                or obj.Shape.isNull()
                or not obj.Shape.isValid()
                or len(obj.Shape.Solids) != 1
            ):
                raise DesignError(obj.Error or "The operation did not produce a valid solid.")
        self.last_spec = dict(spec)
        self.last_spec["resolved_operation"] = operation
        return self.outputs

    def accept(self):
        if self.closed:
            return
        if not self.outputs or any(o.Error or o.Shape.isNull() for o in self.outputs):
            raise DesignError("Create a valid preview before accepting.")
        for obj in self.outputs:
            body = features.owner_body(obj)
            if not self.editing:
                history.insert_after(body, obj.BaseFeature, obj)
            elif body.Name in self.original_tips:
                previous = self.doc.getObject(self.original_tips[body.Name] or "")
                if previous and previous not in self.editing:
                    history.reveal(body, previous)
        self.doc.recompute()
        # A feature can have an empty/invalid Shape or an explicit Az Error
        # before FreeCAD marks its State "Invalid". Validate the actual
        # affected Body chain (including the final Tip), not unrelated Bodies.
        broken = []
        inspected = set()
        for obj in self.outputs:
            body = features.owner_body(obj)
            members = list(body.Group) if body else [obj]
            start = members.index(obj) if obj in members else 0
            for item in members[start:]:
                if item.Name in inspected or not item.isDerivedFrom("PartDesign::Feature"):
                    continue
                inspected.add(item.Name)
                shape = getattr(item, "Shape", None)
                if (
                    "Invalid" in getattr(item, "State", ())
                    or bool(getattr(item, "Error", ""))
                    or shape is None or shape.isNull() or not shape.isValid()
                    or len(shape.Solids) != 1
                ):
                    broken.append(item.Label)
        if broken:
            raise DesignError(
                "This Extrude would break downstream solids: "
                + ", ".join(broken)
                + ". Cancel to restore the original design or adjust the Extrude."
            )
        self.doc.commitTransaction()
        self.closed = True

    def cancel(self):
        if not self.closed:
            self.doc.abortTransaction()
            for obj_name, name, old_type, group, value in self._legacy_links:
                obj = self.doc.getObject(obj_name)
                if obj is None:
                    continue
                current_type = (
                    obj.getTypeIdOfProperty(name)
                    if name in obj.PropertiesList else None
                )
                if current_type != old_type:
                    if current_type is not None:
                        obj.removeProperty(name)
                    obj.addProperty(old_type, name, group)
                    if value is not None:
                        setattr(obj, name, value)
            self._restore_visibility()
            self.doc.recompute()
            self.closed = True
