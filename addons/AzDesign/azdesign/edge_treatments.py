# SPDX-License-Identifier: LGPL-2.1-or-later
"""Non-destructive native Fillet/Chamfer preflight and transactional commit.

No geometry is scaled or healed silently. The exact selected edge names and
requested dimensions are used; upstream FreeCAD / OpenCascade remains the
geometry engine and the committed feature remains native PartDesign.
"""

import math

import Part

from .features import DesignError, owner_body


def selected_edges(obj, names):
    """Validate edge references without changing the selected object."""
    if obj is None or not hasattr(obj, "Shape") or obj.Shape.isNull():
        raise DesignError("Choose a solid with a valid Shape.")
    if len(obj.Shape.Solids) != 1 or not obj.Shape.isValid():
        raise DesignError("The selected feature must have exactly one valid solid.")
    unique = []
    for name in names:
        if name in unique:
            continue
        if not name.startswith("Edge") or not name[4:].isdigit():
            raise DesignError("Select solid edges (Edge1, Edge2, …), not faces.")
        index = int(name[4:])
        if index < 1 or index > len(obj.Shape.Edges):
            raise DesignError("The selected edge " + name + " no longer exists. Re-select it.")
        unique.append(name)
    if not unique:
        raise DesignError("Select at least one edge on the solid.")
    return tuple(unique)


def validate_value(value):
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise DesignError("Enter a numeric edge treatment size in millimetres.") from exc
    if not math.isfinite(value) or value <= 0:
        raise DesignError("Fillet/Chamfer size must be a positive finite number.")
    return value


def check(shape, edge_names, size, kind):
    """Pure OCCT operation on a copied solid, never a document object."""
    if kind not in ("Fillet", "Chamfer"):
        raise DesignError("Choose Fillet or Chamfer.")
    size = validate_value(size)
    if shape.isNull() or len(shape.Solids) != 1 or not shape.isValid():
        raise DesignError("Source geometry is not one valid solid.")
    chosen = []
    for name in edge_names:
        index = int(name[4:])
        if index <= 0 or index > len(shape.Edges):
            raise DesignError("The edge " + name + " no longer exists.")
        chosen.append(shape.Edges[index - 1])
    if not chosen:
        raise DesignError("Choose at least one edge.")
    try:
        # The OCCT kernel is authoritative; don't infer maximum radius from
        # a global bounding-box ratio on a very narrow or complex feature.
        result = (
            shape.makeFillet(size, chosen)
            if kind == "Fillet"
            else shape.makeChamfer(size, chosen)
        )
        if result.isNull() or len(result.Solids) != 1 or not result.isValid():
            raise DesignError("FreeCAD produced an empty or invalid solid.")
        return result
    except DesignError:
        raise
    except Exception as exc:
        raise DesignError(
            kind + " could not be built on "
            + ", ".join(edge_names) + " at " + format(size, ".6g")
            + " mm. Try fewer edges or a smaller value. "
            "The original solid is unchanged. Kernel detail: " + str(exc)
        ) from exc


def preflight(obj, names, size, kind):
    names = selected_edges(obj, names)
    result = check(obj.Shape, names, size, kind)
    return names, result


def create(obj, names, size, kind):
    """Commit a native parametric PartDesign feature or roll back everything."""
    names, _ = preflight(obj, names, size, kind)
    size = validate_value(size)
    body = owner_body(obj)
    if not body:
        raise DesignError("Activate a Body containing the selected solid.")
    if body.Tip != obj:
        raise DesignError(
            "The selected geometry is not the current Body Tip. "
            "Activate its final feature or roll history back deliberately."
        )
    doc = obj.Document
    doc.openTransaction("Az: " + kind)
    try:
        feature = body.newObject("PartDesign::" + kind, kind)
        feature.Base = (obj, list(names))
        if kind == "Fillet":
            feature.Radius = size
        else:
            feature.Size = size
        doc.recompute()
        result = feature.Shape
        if (
            "Invalid" in feature.State or result.isNull()
            or not result.isValid() or len(result.Solids) != 1
        ):
            raise DesignError(
                kind + " failed after native recompute. Original solid restored."
            )
        doc.commitTransaction()
        return feature
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise


def probe_smaller(obj, names, size, kind):
    """Suggest only sizes the same kernel really builds, never theoretical ones."""
    names = selected_edges(obj, names)
    size = validate_value(size)
    for fraction in (0.5, 0.25, 0.1, 0.05, 0.01):
        candidate = size * fraction
        if candidate < 1e-6:
            continue
        try:
            check(obj.Shape, names, candidate, kind)
            return candidate
        except DesignError:
            continue
    return None
