# SPDX-License-Identifier: LGPL-2.1-or-later
"""Exact geometric snap candidates and sketch construction references.

FreeCAD Sketcher's native cursor snap/auto-constraint system remains in
charge while drawing. This module exposes otherwise hard-to-find exact
centers, arc/line midpoints and endpoints from selected 3D edges.
"""

from dataclasses import dataclass

import FreeCAD as App
import Part
import Sketcher

from .features import DesignError


@dataclass(frozen=True)
class SnapTarget:
    name: str
    point: object
    edge_name: str

    def coordinates(self):
        return (float(self.point.x), float(self.point.y), float(self.point.z))


def _near(a, b, tolerance=1e-9):
    return (a - b).Length <= tolerance


def targets(edge, edge_name="Edge"):
    """Find *geometric* points, not approximate screen-based locations."""
    if edge is None or edge.isNull():
        raise DesignError("Select a real model edge.")
    points = []
    vertices = list(edge.Vertexes)
    closed = (
        len(vertices) < 2
        or _near(vertices[0].Point, vertices[-1].Point)
    ) if vertices else True
    if not closed:
        points.append(SnapTarget("Start", vertices[0].Point, edge_name))
        points.append(SnapTarget("End", vertices[-1].Point, edge_name))
        midparam = (edge.FirstParameter + edge.LastParameter) / 2.0
        try:
            points.append(SnapTarget("Midpoint", edge.valueAt(midparam), edge_name))
        except (ValueError, RuntimeError):
            pass
    # Native OCC analytic curves expose the circle/ellipse's true center.
    # Do not treat CenterOfMass as a circle center on an arbitrary spline.
    curve = edge.Curve
    kind = type(curve).__name__
    if kind in ("Circle", "Ellipse") and hasattr(curve, "Center"):
        points.append(SnapTarget("Center", curve.Center, edge_name))
    return tuple(points)


def from_object(obj, edge_names):
    if obj is None or not hasattr(obj, "Shape") or obj.Shape.isNull():
        raise DesignError("Select a shape edge in the FreeCAD viewport.")
    names = tuple(dict.fromkeys(edge_names))
    if not names:
        raise DesignError("Select one or more edges, not the whole feature.")
    result = []
    for name in names:
        if not name.startswith("Edge") or not name[4:].isdigit():
            raise DesignError("Choose an edge, such as Edge3; not a face.")
        index = int(name[4:])
        if index < 1 or index > len(obj.Shape.Edges):
            raise DesignError(name + " no longer exists; select the edge again.")
        result.extend(targets(obj.Shape.Edges[index - 1], name))
    if not result:
        raise DesignError(
            "No snap points found. Try a straight line, circular arc or "
            "circular hole edge."
        )
    return tuple(result)


def create_sketch_reference(sketch, target):
    """Project a snapped 3D position onto a sketch, as a fixed point.

    Explicitly NOT associative to the source edge. FreeCAD's native Sketcher
    AutoConstraints supplies live coincident/point-on-object constraints for
    ordinary in-sketch geometry; this static reference is for locating a
    point from an existing 3D circular or straight edge.
    """
    if sketch is None or not sketch.isDerivedFrom("Sketcher::SketchObject"):
        raise DesignError("Edit a Sketch to place a snap reference.")
    local = sketch.Placement.inverse().multVec(target.point)
    point = App.Vector(local.x, local.y, 0)
    doc = sketch.Document
    doc.openTransaction("Az: Snap Reference Point")
    try:
        index = sketch.addGeometry(Part.Point(point), True)
        # A fixed point is deliberately independent of later source-edge
        # changes; label it as such rather than claim live associative CAD.
        sketch.addConstraint(Sketcher.Constraint("Block", index))
        doc.recompute()
        if "Invalid" in sketch.State:
            raise DesignError("Sketcher rejected the projected reference point.")
        doc.commitTransaction()
        return index
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise


def link_body_edge(sketch, source, edge_name):
    """Create an associative Sketcher external edge without modifying the solid.

    Unlike create_sketch_reference, this uses FreeCAD's native external
    geometry dependency: moving the source edge updates the sketch reference.
    The operation is transactional and refuses circular dependencies.
    """
    if sketch is None or not sketch.isDerivedFrom("Sketcher::SketchObject"):
        raise DesignError("Edit a sketch before referencing a body edge.")
    if source is None or source.Document != sketch.Document or source == sketch:
        raise DesignError("Select an edge from another object in the same document.")
    if not edge_name.startswith("Edge") or not edge_name[4:].isdigit():
        raise DesignError("Select a model edge, not a face or whole body.")
    number = int(edge_name[4:])
    if not hasattr(source, "Shape") or source.Shape.isNull() or not (
        1 <= number <= len(source.Shape.Edges)
    ):
        raise DesignError("The selected source edge no longer exists.")
    if sketch in getattr(source, "OutListRecursive", ()):
        raise DesignError("That reference would create a circular dependency.")
    doc = sketch.Document
    doc.openTransaction("Design: Link body edge to sketch")
    try:
        result = sketch.addExternal(source.Name, edge_name)
        doc.recompute()
        if "Invalid" in tuple(str(state) for state in sketch.State):
            raise DesignError("Sketcher rejected the external body edge.")
        doc.commitTransaction()
        return result
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise


def link_selected_body_edges(sketch):
    """Link uniquely selected model edges into the active sketch.

    Selection is explicit and ambiguity-safe: sketch-owned edges, faces,
    whole-object selections and cross-document geometry are ignored. Native
    Sketcher external references remain associative with their source.
    """
    import FreeCADGui as Gui
    if sketch is None or not sketch.isDerivedFrom("Sketcher::SketchObject"):
        raise DesignError("Start editing a sketch to reference model edges.")
    hits = []
    for selection in Gui.Selection.getSelectionEx():
        source = selection.Object
        if source is None or source == sketch:
            continue
        if source.Document != sketch.Document:
            continue
        for edge_name in selection.SubElementNames:
            if edge_name.startswith("Edge") and edge_name[4:].isdigit():
                pair = (source, edge_name)
                if pair not in hits:
                    hits.append(pair)
    if not hits:
        raise DesignError("Select one or more body edges to reference.")
    doc = sketch.Document
    doc.openTransaction("Design: Reference selected body edges")
    try:
        linked = []
        for source, edge_name in hits:
            if sketch in getattr(source, "OutListRecursive", ()):
                raise DesignError("A selected edge would create a circular dependency.")
            index = int(edge_name[4:])
            if not hasattr(source, "Shape") or source.Shape.isNull() or not (
                1 <= index <= len(source.Shape.Edges)
            ):
                raise DesignError("Selected source edge no longer exists.")
            linked.append(sketch.addExternal(source.Name, edge_name))
        doc.recompute()
        if "Invalid" in tuple(str(state) for state in sketch.State):
            raise DesignError("Sketcher rejected the selected external edges.")
        doc.commitTransaction()
        return tuple(linked)
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise


def passive_sketch_cues(sketch, source, edge_names, tolerance=1e-6):
    """Return read-only local-plane cues for visible source edges.

    This function deliberately does not call addExternal, addGeometry,
    openTransaction, or any native Sketcher tool. A viewport overlay can
    consume the returned coordinates without changing the document.
    Off-plane targets are rejected rather than falsely advertised as
    coincident sketch snaps. The caller controls screen-space proximity.
    """
    if sketch is None or not sketch.isDerivedFrom("Sketcher::SketchObject"):
        raise DesignError("An active sketch is required for passive cues.")
    if source is None or source == sketch or source.Document != sketch.Document:
        return ()
    if sketch in getattr(source, "OutListRecursive", ()):
        return ()
    if not hasattr(source, "Shape") or source.Shape.isNull():
        return ()
    if not isinstance(tolerance, (int, float)) or tolerance <= 0:
        raise ValueError("Snap plane tolerance must be positive.")
    inverse = sketch.Placement.inverse()
    cues = []
    seen = set()
    for target in from_object(source, edge_names):
        point = inverse.multVec(target.point)
        if abs(point.z) > tolerance:
            continue
        key = (target.edge_name, target.name,
               round(float(point.x), 9), round(float(point.y), 9))
        if key in seen:
            continue
        seen.add(key)
        cues.append((target.name, target.edge_name,
                     float(point.x), float(point.y)))
    return tuple(cues)


def nearest_passive_cue(cues, project_to_screen, cursor, radius_px=12.0):
    """Choose one unambiguous viewport cue without altering Sketcher state.

    project_to_screen(x, y) must return the pixel position of a local sketch
    coordinate, or None for a clipped/hidden point. This deliberately accepts
    a projection callback rather than assuming a particular FreeCAD/Qt version.
    Ties at different geometry locations are rejected, never guessed.
    """
    import math
    if not math.isfinite(float(radius_px)) or radius_px <= 0:
        raise ValueError("Snap radius must be finite and positive.")
    cx, cy = map(float, cursor)
    if not (math.isfinite(cx) and math.isfinite(cy)):
        return None
    ranked = []
    for cue in cues:
        name, edge, x, y = cue
        if not all(math.isfinite(float(v)) for v in (x, y)):
            continue
        screen = project_to_screen(x, y)
        if screen is None:
            continue
        sx, sy = map(float, screen)
        if not (math.isfinite(sx) and math.isfinite(sy)):
            continue
        distance = math.hypot(sx - cx, sy - cy)
        if distance <= radius_px:
            ranked.append((distance, cue))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0])
    best_distance, best = ranked[0]
    # Two overlapping points on different model edges can be coincident and
    # still describe one location; two different locations equally near the
    # cursor must not produce an arbitrary snap.
    for distance, other in ranked[1:]:
        if distance - best_distance > 0.5:
            break
        if math.hypot(other[2] - best[2], other[3] - best[3]) > 1e-7:
            return None
    return best
