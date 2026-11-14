# SPDX-License-Identifier: LGPL-2.1-or-later
"""Parametric Az features evaluated with FreeCAD's native solid algorithms.

Each output keeps a stable document identity while its operation is edited.
Transient, hidden documents invoke native Pad/Pocket algorithms, including
draft and end conditions. They never become part of the saved model.
"""

import os
import math
import FreeCAD as App
import Part
from . import profiles, references
from .compat import set_extrusion_sides

_calculator = None


class DesignError(ValueError):
    pass


def ensure_calculator():
    """Prepare GUI calculation storage before starting a user transaction.

    Closing a document in FreeCAD's GUI commits the application-wide active
    transaction, even when that document is hidden. Reuse one temporary,
    Undo-disabled calculation document for the session instead.
    """
    global _calculator
    if not App.GuiUp:
        return None
    if _calculator is not None:
        try:
            if _calculator.Name in App.listDocuments():
                return _calculator
        except RuntimeError:
            pass  # Close All can dispose of the cached C++ document wrapper.
        _calculator = None
    if App.getActiveTransaction():
        raise DesignError("Finish the current edit, then reopen the Az Design operation.")
    previous_name = getattr(App.activeDocument(), "Name", "")
    try:
        _calculator = App.newDocument("AzGeometry", hidden=True, temp=True)
        _calculator.UndoMode = 0
    finally:
        # FreeCAD can leave a hidden/temp document App-active when there was no
        # previous design. The function reads the native pointer; the Python
        # ActiveDocument attribute can remain stale after clearing that pointer.
        if getattr(App.activeDocument(), "Name", "") != previous_name:
            App.setActiveDocument(previous_name if previous_name in App.listDocuments() else "")
    return _calculator


def begin_transaction(doc, name):
    if App.GuiUp:
        # Keep the transaction open after the initiating FreeCAD command returns
        # while a nonmodal task continues receiving typed/dragged input.
        App.setActiveTransaction(name, True)
    else:
        doc.openTransaction(name)


def owner_body(obj):
    return next((parent for parent in obj.InList if parent.isDerivedFrom("PartDesign::Body")), None)


def body_tip(body):
    tip = body.Tip
    if tip and hasattr(tip, "Shape") and len(tip.Shape.Solids):
        return tip
    return next(
        (
            item
            for item in reversed(body.Group)
            if hasattr(item, "Shape")
            and not item.isDerivedFrom("Sketcher::SketchObject")
            and len(item.Shape.Solids)
        ),
        None,
    )


def body_frame(body):
    return body.getGlobalPlacement() if body else App.Placement()


def source_shape(source, target_body=None, descriptors=None, whole=False, signature=""):
    obj, subnames = source
    if obj is None:
        raise DesignError("Select a sketch profile or planar face.")
    target_inverse = body_frame(target_body).inverse()
    if obj.isDerivedFrom("Sketcher::SketchObject"):
        if whole:
            local = Part.makeFace(obj.Shape, "Part::FaceMakerBullseye")
            # Shape already includes the sketch's own placement, not its body.
            transform = target_inverse.multiply(obj.getGlobalPlacement()).multiply(
                obj.Placement.inverse()
            )
        else:
            selected = profiles.resolve(obj, descriptors or [])
            local = profiles.joined_face(selected)
            transform = target_inverse.multiply(obj.getGlobalPlacement())
        result = local.copy()
        result.Placement = transform.multiply(result.Placement)
        return result
    if len(subnames) != 1 or not subnames[0].lstrip("?").startswith("Face"):
        raise DesignError("Select one planar face.")
    face = references.resolve_face(obj, subnames[0], signature)[0].copy()
    if not isinstance(face.Surface, Part.Plane):
        raise DesignError(
            "Extrude requires a planar face. Use Diameter for an editable cylindrical face."
        )
    parent = obj.getGlobalPlacement().multiply(obj.Placement.inverse())
    face.Placement = target_inverse.multiply(parent).multiply(face.Placement)
    return face


def shape_in_body(obj, target_body):
    result = obj.Shape.copy()
    parent = obj.getGlobalPlacement().multiply(obj.Placement.inverse())
    result.Placement = body_frame(target_body).inverse().multiply(parent).multiply(result.Placement)
    return result


def face_in_body(link, target_body, signature=""):
    if not link or not link[0] or len(link[1]) != 1:
        raise DesignError("Pick a target face for the To Face extent.")
    obj, names = link
    face = references.resolve_face(obj, names[0], signature)[0].copy()
    if not isinstance(face.Surface, Part.Plane):
        raise DesignError("Pick a planar end face for the To Face extent.")
    parent = obj.getGlobalPlacement().multiply(obj.Placement.inverse())
    face.Placement = body_frame(target_body).inverse().multiply(parent).multiply(face.Placement)
    return face


def numeric(text, unit="length", context=None, signed=False, zero=False):
    raw = text.strip()
    if not raw:
        raise DesignError("Enter a value.")
    try:
        value = context.evalExpression(raw) if context else App.Units.Quantity(raw)
        if isinstance(value, (int, float)):
            result = float(value)
        else:
            expected = App.Units.Length if unit == "length" else App.Units.Angle
            if value.Unit not in (expected, App.Units.Unit()):
                raise DesignError(
                    "Use length units such as mm/in."
                    if unit == "length"
                    else "Use an angle in degrees."
                )
            result = float(value.Value)
    except DesignError:
        raise
    except Exception as exc:
        raise DesignError("Enter a valid value, unit or parameter expression.") from exc
    if not math.isfinite(result) or (not signed and (result < 0 or (result == 0 and not zero))):
        raise DesignError(
            "Enter a positive value." if not zero else "Enter zero or a positive value."
        )
    return result


def document_shape(shape):
    """Transfer exact geometry without calculator-specific topology IDs.

    Native Pad/Pocket maps contain IDs from their calculation document. Keeping
    those in another document breaks native downstream fillets on recompute.
    An exact BREP transfer removes the foreign maps and keeps analytic geometry
    and placement. Native edge/face references still require reselection when
    an edit changes topology, as with other scripted FreeCAD features.
    """
    clean = Part.Shape()
    clean.importBrepFromString(shape.exportBrepToString(), False)
    return clean


def native_extrusion(
    profile,
    base=None,
    operation="Join",
    distance=10.0,
    distance2=10.0,
    direction="One side",
    reversed=False,
    extent="Distance",
    to_face=None,
    taper=0.0,
    taper2=0.0,
    start=0.0,
    allow_disconnected_tool=False,
):
    if profile.isNull() or not profile.Faces or not profile.isValid():
        raise DesignError("The selected profiles do not form a valid planar face.")
    if distance <= 0 or (direction == "Two sides" and distance2 <= 0):
        raise DesignError("Extrusion distances must be positive.")
    if abs(taper) >= 89 or abs(taper2) >= 89:
        raise DesignError("Taper must be between -89° and 89°.")
    if operation in ("Cut", "Intersect") and (base is None or base.isNull()):
        raise DesignError("Choose an existing target body for this operation.")
    if extent == "Through all" and operation != "Cut":
        raise DesignError("Through all is available for Cut.")
    if extent != "Distance" and direction != "One side":
        raise DesignError(
            "Through All and To Face use One side. Use Distance for symmetric or two-sided extrusions."
        )
    transient = (
        ensure_calculator() if App.GuiUp else App.newDocument("AzGeometry", hidden=True, temp=True)
    )
    for existing in transient.Objects[::-1]:
        transient.removeObject(existing.Name)
    try:
        body = transient.addObject("PartDesign::Body", "Body")
        if allow_disconnected_tool:
            body.AllowCompound = True
        base_feature = None
        if base is not None and operation in ("Join", "Cut"):
            base_feature = body.newObject("PartDesign::Feature", "Base")
            base_feature.Shape = base.copy()
            base_feature.Placement = base.Placement
        sketch = body.newObject("Part::Part2DObject", "Profile")
        shape = profile.copy()
        if start:
            shape.translate(shape.Faces[0].normalAt(0, 0) * start)
        placement = shape.Placement
        shape.Placement = App.Placement()
        sketch.Shape = shape
        sketch.Placement = placement
        native = body.newObject(
            "PartDesign::Pocket" if operation == "Cut" else "PartDesign::Pad", "Calculate"
        )
        native.Profile = sketch
        if base_feature:
            native.BaseFeature = base_feature
        native.AllowMultiFace = True
        native.Length = distance
        native.Length2 = distance2
        native.Reversed = reversed
        set_extrusion_sides(native, direction)
        native.TaperAngle = taper
        native.TaperAngle2 = taper2
        native.Refine = True
        if extent == "Through all":
            native.Type = "ThroughAll"
        elif extent == "To face":
            if to_face is None:
                raise DesignError("Pick the target face.")
            limit = transient.addObject("Part::Feature", "Limit")
            limit.Shape = to_face.copy()
            limit.Placement = to_face.Placement
            native.Type = "UpToFace"
            native.UpToFace = (limit, ["Face1"])
        transient.recompute()
        result = native.Shape.copy()
        if operation == "Intersect":
            result = base.common(result).removeSplitter()
        solid_count = len(result.Solids)
        if (result.isNull() or not result.isValid() or not solid_count
                or (solid_count != 1 and not allow_disconnected_tool)):
            raise DesignError(
                "This operation must produce one connected solid per body. Check profiles, direction and extent."
            )
        return document_shape(result)
    finally:
        if not App.GuiUp:
            App.closeDocument(transient.Name)


def upgrade_extrude_links(obj):
    """Repair 0.4.1 local link properties on an Extrude being explicitly edited.

    This must be invoked inside the operation's already-open FreeCAD native
    transaction so Cancel can restore the original feature unchanged.
    A previously saved file is not silently rewritten when merely opened.
    """
    if getattr(obj, "AzType", "") != "AzExtrude":
        return False
    properties = (
        ("Source", "App::PropertyLinkSub", "App::PropertyLinkSubGlobal", "Profiles"),
        ("UpToFace", "App::PropertyLinkSub", "App::PropertyLinkSubGlobal", "Extrude"),
        ("SourceFrame", "App::PropertyLink", "App::PropertyLinkGlobal", "Az Design"),
        ("LimitFrame", "App::PropertyLink", "App::PropertyLinkGlobal", "Az Design"),
    )
    changed = False
    for name, old_type, new_type, group in properties:
        if name not in obj.PropertiesList:
            continue
        actual_type = obj.getTypeIdOfProperty(name)
        if actual_type == new_type:
            continue
        if actual_type != old_type:
            raise DesignError(
                "Unexpected " + name + " link type on " + obj.Label
                + ": " + actual_type + ". No automatic conversion was attempted."
            )
        value = getattr(obj, name)
        obj.removeProperty(name)
        obj.addProperty(new_type, name, group)
        if value is not None and not (
            isinstance(value, (tuple, list)) and value and value[0] is None
        ):
            setattr(obj, name, value)
        if name in ("SourceFrame", "LimitFrame"):
            obj.setEditorMode(name, 2)
        changed = True
    return changed


class ExtrudeProxy:
    Type = "AzExtrude"

    def __init__(self, obj):
        obj.addProperty("App::PropertyString", "AzType", "Az Design")
        obj.AzType = self.Type
        obj.setEditorMode("AzType", 2)
        obj.addProperty("App::PropertyLinkSubGlobal", "Source", "Profiles")
        obj.addProperty("App::PropertyStringList", "Regions", "Profiles")
        obj.addProperty("App::PropertyString", "SourceFaceSignature", "Profiles")
        obj.setEditorMode("SourceFaceSignature", 2)
        obj.addProperty("App::PropertyBool", "WholeSketch", "Profiles")
        obj.addProperty("App::PropertyEnumeration", "Operation", "Extrude")
        obj.Operation = ["Join", "Cut", "Intersect", "New body"]
        obj.addProperty("App::PropertyLength", "Length", "Extrude")
        obj.Length = 10
        obj.addProperty("App::PropertyLength", "Length2", "Extrude")
        obj.Length2 = 10
        obj.addProperty("App::PropertyEnumeration", "Direction", "Extrude")
        obj.Direction = ["One side", "Symmetric", "Two sides"]
        obj.addProperty("App::PropertyBool", "Reversed", "Extrude")
        obj.addProperty("App::PropertyEnumeration", "Extent", "Extrude")
        obj.Extent = ["Distance", "Through all", "To face"]
        obj.addProperty("App::PropertyLinkSubGlobal", "UpToFace", "Extrude")
        obj.addProperty("App::PropertyString", "LimitFaceSignature", "Extrude")
        obj.setEditorMode("LimitFaceSignature", 2)
        for name in ("SourceFrame", "LimitFrame"):
            obj.addProperty("App::PropertyLinkGlobal", name, "Az Design")
            obj.setEditorMode(name, 2)
        obj.addProperty("App::PropertyDistance", "StartOffset", "Extrude")
        obj.addProperty("App::PropertyAngle", "TaperAngle", "Extrude")
        obj.addProperty("App::PropertyAngle", "TaperAngle2", "Extrude")
        obj.addProperty("App::PropertyString", "FeatureGroup", "Az Design")
        obj.setEditorMode("FeatureGroup", 2)
        obj.addProperty("App::PropertyString", "Error", "Az Design")
        obj.setEditorMode("Error", 1)
        obj.Proxy = self

    def execute(self, obj):
        try:
            if obj.Suppressed:
                shape = obj.BaseFeature.Shape.copy() if obj.BaseFeature else Part.Shape()
                obj.Shape = shape
                obj.Placement = shape.Placement
                obj.Error = ""
                return
            body = owner_body(obj)
            profile = source_shape(
                obj.Source, body, obj.Regions, obj.WholeSketch, obj.SourceFaceSignature
            )
            base = (
                shape_in_body(obj.BaseFeature, body)
                if obj.BaseFeature and obj.Operation != "New body"
                else None
            )
            limit = (
                face_in_body(obj.UpToFace, body, obj.LimitFaceSignature)
                if obj.Extent == "To face"
                else None
            )
            result = native_extrusion(
                profile,
                base,
                obj.Operation,
                obj.Length.Value,
                obj.Length2.Value,
                str(obj.Direction),
                obj.Reversed,
                str(obj.Extent),
                limit,
                obj.TaperAngle.Value,
                obj.TaperAngle2.Value,
                obj.StartOffset.Value,
            )
            placement = result.Placement
            obj.Shape = result
            obj.Placement = placement
            obj.Error = ""
        except Exception as exc:
            obj.Shape = Part.Shape()
            obj.Error = str(exc)
            # The task renders this diagnostic inline. Raising here also opens
            # FreeCAD's global Report view for every intermediate typed value.

    def dumps(self):
        return None

    def loads(self, state):
        pass


class ViewProvider:
    def __init__(self, view):
        view.Proxy = self

    def attach(self, view):
        self.Object = view.Object
        if not App.getActiveTransaction():
            ensure_calculator()

    def getIcon(self):
        return os.path.join(os.path.dirname(__file__), "..", "Resources", "extrude.svg")

    def doubleClicked(self, view):
        from .tasks import edit_feature

        edit_feature(view.Object)
        return True

    def setEdit(self, view, mode=0):
        return self.doubleClicked(view)

    def dumps(self):
        return None

    def loads(self, state):
        pass


def create_extrude(body, source, operation="Join", region_descriptors=None, whole=False, base=None):
    obj = body.newObject("PartDesign::FeaturePython", "Extrude")
    ExtrudeProxy(obj)
    obj.Source = source
    source_body = owner_body(source[0])
    obj.SourceFrame = source_body if source_body != body else None
    if source[1] and str(source[1][0]).lstrip("?").startswith("Face"):
        obj.SourceFaceSignature = references.face_signature(source[0], source[1][0])
    obj.Regions = region_descriptors or []
    obj.WholeSketch = whole
    obj.Operation = operation
    obj.BaseFeature = base if operation != "New body" else None
    if App.GuiUp:
        ViewProvider(obj.ViewObject)
        obj.ViewObject.ShapeColor = (0.76, 0.79, 0.82)
        obj.ViewObject.LineColor = (0.20, 0.24, 0.28)
    return obj
