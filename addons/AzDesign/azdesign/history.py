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



def deletion_plan(feature, cascade=False):
    """Return (body, reverse-removal-safe targets, resulting tip).

    One-feature deletion refuses every referenced object; deleting a branch
    means deleting only explicitly shown downstream steps within one Body.
    External users (including other bodies) always block the operation.
    """
    if feature is None or not (
        feature.isDerivedFrom("PartDesign::Feature")
        or feature.isDerivedFrom("Sketcher::SketchObject")
    ):
        raise DesignError("Select a sketch or solid feature in the timeline.")
    body = owner_body(feature)
    if body is None or feature not in body.Group:
        raise DesignError("Choose a feature that belongs to a Part Design Body.")
    group = list(body.Group)
    position = group.index(feature)
    if cascade:
        targets = [
            member for member in group[position:]
            if member.isDerivedFrom("PartDesign::Feature")
            or member.isDerivedFrom("Sketcher::SketchObject")
        ]
    else:
        targets = [feature]
    names = {item.Name for item in targets}
    for item in targets:
        for user in item.InList:
            if user == body or user.Name in names:
                continue
            raise DesignError(
                "Cannot delete " + item.Label + ": " + user.Label
                + " still depends on it. Use 'Delete from here' for later "
                "steps in this Body, or repair external references first."
            )
    # All trailing objects not included in the plan must be independent of
    # the target. If they are not, the reference check above rejects deletion.
    tip = body.Tip
    if tip and tip.Name in names:
        tip = next(
            (
                obj for obj in reversed(group[:position])
                if obj.isDerivedFrom("PartDesign::Feature") and obj.Name not in names
            ),
            None,
        )
    return body, targets, tip


def delete_feature(feature, cascade=False):
    """Transactionally delete a safe leaf or an explicitly confirmed branch.

    This method does not show UI confirmation: callers must ask the user
    before passing cascade=True. Undo remains available after commit.
    """
    body, targets, tip = deletion_plan(feature, cascade)
    doc = feature.Document
    labels = [obj.Label for obj in targets]
    names = {obj.Name for obj in targets}
    # Existing broken unrelated objects must not prevent removing bad geometry.
    prior_errors = {
        o.Name for o in doc.Objects
        if o.isDerivedFrom("PartDesign::Feature") and (
            "Invalid" in getattr(o, "State", ())
            or bool(getattr(o, "Error", ""))
        )
    }
    doc.openTransaction("Az: Delete later steps" if cascade else "Az: Delete feature")
    try:
        if body.Tip and body.Tip.Name in names:
            body.Tip = tip
        if getattr(body, "AzHistoryEnd", "") in names:
            body.AzHistoryEnd = ""
        for obj in reversed(targets):
            if doc.getObject(obj.Name):
                doc.removeObject(obj.Name)
        if tip and doc.getObject(tip.Name) and body.Tip is None:
            body.Tip = tip
        doc.recompute()
        broken = [
            o.Label for o in doc.Objects
            if o.isDerivedFrom("PartDesign::Feature")
            and o.Name not in prior_errors
            and (
                "Invalid" in getattr(o, "State", ())
                or bool(getattr(o, "Error", ""))
            )
        ]
        if broken:
            raise DesignError(
                "Deleting this feature would break: " + ", ".join(broken)
                + ". No changes were kept."
            )
        doc.commitTransaction()
        return labels
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise


def dependents(feature):
    """Return downstream actual document objects, never infer from label/order."""
    if feature is None:
        return []
    visited = {feature.Name}
    pending = [feature]
    result = []
    while pending:
        target = pending.pop(0)
        for user in getattr(target, "InList", ()):
            if user.Name in visited:
                continue
            visited.add(user.Name)
            # Body is a container, not itself evidence of a feature edge.
            if user.isDerivedFrom("PartDesign::Body"):
                continue
            result.append(user)
            pending.append(user)
    return result


def history_position(body):
    """(features, index, rolled_back) for a native Body Tip."""
    entries = solids(body)
    tip = body.Tip
    index = entries.index(tip) if tip in entries else -1
    return entries, index, bool(getattr(body, "AzHistoryEnd", ""))


def move_history_marker(body, index):
    """Drag-release timeline scrub; only moves Body Tip, never reorders links."""
    items, current, rolled = history_position(body)
    if not items or not 0 <= index < len(items):
        raise DesignError("Choose a valid solid in the current Body history.")
    if index == len(items) - 1 and rolled:
        end(body)
    elif index != current:
        rollback(items[index])


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
