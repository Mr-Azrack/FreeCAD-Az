# SPDX-License-Identifier: LGPL-2.1-or-later
"""Body-aware rollback and insertion, backed by FreeCAD's actual Body Tip."""

import FreeCAD as App
from .features import owner_body, DesignError


def solids(body):
    return [o for o in body.Group if o.isDerivedFrom("PartDesign::Feature")]


def reveal(body, tip):
    body.Tip = tip
    for obj in solids(body):
        if App.GuiUp:
            obj.ViewObject.Visibility = obj == tip
    if App.GuiUp:
        body.ViewObject.Visibility = True


def rollback(feature):
    body = owner_body(feature)
    if body is None or not feature.isDerivedFrom("PartDesign::Feature"):
        raise DesignError("Choose a solid feature in a Body.")
    doc = feature.Document
    doc.openTransaction("Az: Roll back history")
    try:
        if "AzHistoryEnd" not in body.PropertiesList:
            body.addProperty("App::PropertyString", "AzHistoryEnd", "Az Design")
            body.setEditorMode("AzHistoryEnd", 2)
        if not body.AzHistoryEnd and body.Tip:
            body.AzHistoryEnd = body.Tip.Name
        reveal(body, feature)
        doc.recompute()
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise


def end(body):
    if "AzHistoryEnd" not in body.PropertiesList or not body.AzHistoryEnd:
        return
    doc = body.Document
    target = doc.getObject(body.AzHistoryEnd)
    doc.openTransaction("Az: Resume history")
    try:
        if target:
            reveal(body, target)
        body.AzHistoryEnd = ""
        doc.recompute()
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise


def resume_all(doc=None):
    doc = doc or App.ActiveDocument
    if doc:
        for body in doc.Objects:
            if body.isDerivedFrom("PartDesign::Body"):
                end(body)


def insert_after(body, base, created):
    """Rebase the next feature when inserting at a real rolled-back position."""
    if not base or not getattr(body, "AzHistoryEnd", ""):
        return
    next_features = [
        o for o in solids(body) if o != created and getattr(o, "BaseFeature", None) == base
    ]
    if len(next_features) > 1:
        raise DesignError(
            "This history has multiple branches. Resume history before inserting a feature."
        )
    if next_features:
        next_features[0].BaseFeature = created
    group = list(body.Group)
    if created in group and base in group:
        group.remove(created)
        group.insert(group.index(base) + 1, created)
        body.Group = group


def ordered(doc):
    result = []
    for obj in doc.Objects:
        if obj.isDerivedFrom("PartDesign::Body"):
            for member in obj.Group:
                if member.isDerivedFrom("Sketcher::SketchObject") or member.isDerivedFrom(
                    "PartDesign::Feature"
                ):
                    if member not in result:
                        result.append(member)
        elif (
            obj.isDerivedFrom("Sketcher::SketchObject") or obj.isDerivedFrom("Part::Feature")
        ) and not owner_body(obj):
            if not getattr(obj, "AzPreview", False):
                result.append(obj)
    return result
