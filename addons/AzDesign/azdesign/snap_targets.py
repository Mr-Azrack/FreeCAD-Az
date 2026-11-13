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


def enable_solid_edge_snapping(sketch, max_edges=80, plane_tolerance=1e-5):
    """Make in-plane upstream solid edges native Sketcher snap targets.

    This is an explicit, undoable user action, never a mutation on hover.
    Only the nearest earlier solid in this sketch's Body is referenced.
    Existing links are skipped; invalid, off-plane or excessive geometry is
    rejected rather than producing unbounded dependencies.
    """
    if sketch is None or not sketch.isDerivedFrom("Sketcher::SketchObject"):
        raise DesignError("Edit a sketch to enable solid-edge snapping.")
    body = getattr(sketch, "getParentGeoFeatureGroup", lambda: None)()
    if body is None or not body.isDerivedFrom("PartDesign::Body"):
        raise DesignError("The sketch must belong to a PartDesign Body.")
    members = list(body.Group)
    if sketch not in members:
        raise DesignError("Sketch is not in its expected Body history.")
    if not 1 <= int(max_edges) <= 200:
        raise DesignError("Invalid solid-edge reference limit.")
    source = next((obj for obj in reversed(members[:members.index(sketch)])
                   if obj.isDerivedFrom("PartDesign::Feature")
                   and hasattr(obj, "Shape") and not obj.Shape.isNull()
                   and obj.Shape.isValid() and bool(obj.Shape.Edges)), None)
    if source is None:
        raise DesignError("No earlier solid exists in this Body to reference.")
    if sketch in getattr(source, "OutListRecursive", ()):
        raise DesignError("A solid reference would create a dependency cycle.")
    edges = source.Shape.Edges
    if len(edges) > max_edges:
        raise DesignError("Solid has too many edges for automatic projection; select individual edges.")
    inverse = sketch.Placement.inverse()
    existing = set()
    for linked, names in getattr(sketch, "ExternalGeometry", ()):
        if linked == source:
            existing.update(str(name) for name in names)
    eligible = []
    for index, edge in enumerate(edges, 1):
        name = "Edge" + str(index)
        if name in existing:
            continue
        try:
            if edge.isNull() or not edge.isValid():
                continue
            first, last = edge.FirstParameter, edge.LastParameter
            # Check more than one point so tilted or crossing curves do not
            # masquerade as geometry lying in the active sketch plane.
            for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
                parameter = first + (last - first) * fraction
                point = inverse.multVec(edge.valueAt(parameter))
                if abs(point.z) > plane_tolerance:
                    break
            else:
                eligible.append(name)
        except (AttributeError, RuntimeError, ValueError, TypeError):
            continue
    if not eligible:
        return 0
    doc = sketch.Document
    doc.openTransaction("Az: Enable solid-edge snapping")
    try:
        for name in eligible:
            sketch.addExternal(source.Name, name)
        doc.recompute()
        if "Invalid" in tuple(str(state) for state in sketch.State):
            raise DesignError("Sketcher rejected the projected solid edges.")
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise
    return len(eligible)


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
    # Read-only hover can examine an upstream feature on which the active
    # sketch depends. Circular-dependency checks belong to link_body_edge,
    # which actually changes model dependencies, not passive visual cues.
    if not hasattr(source, "Shape") or source.Shape.isNull():
        return ()
    if not isinstance(tolerance, (int, float)) or tolerance <= 0:
        raise ValueError("Snap plane tolerance must be positive.")
    import math
    inverse = sketch.Placement.inverse()
    cues = []
    seen = set()
    try:
        candidates = from_object(source, edge_names)
    except DesignError:
        # Hover may traverse unsupported or transiently stale topology;
        # never interrupt an active Sketcher drawing command.
        return ()
    for target in candidates:
        try:
            point = inverse.multVec(target.point)
            xyz = (float(point.x), float(point.y), float(point.z))
        except (AttributeError, TypeError, ValueError, RuntimeError):
            continue
        if not all(math.isfinite(v) for v in xyz) or abs(xyz[2]) > tolerance:
            continue
        key = (target.edge_name, target.name,
               round(xyz[0], 9), round(xyz[1], 9))
        if key in seen:
            continue
        seen.add(key)
        cues.append((target.name, target.edge_name,
                     xyz[0], xyz[1]))
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
        try:
            screen = project_to_screen(x, y)
        except (ValueError, RuntimeError, TypeError, OverflowError):
            continue
        if screen is None:
            continue
        try:
            sx, sy = map(float, screen)
        except (TypeError, ValueError, OverflowError):
            continue
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


def visible_body_cue(sketch, project_world, cursor, max_bodies=4,
                     max_edges=120, radius_px=12.0):
    """Fallback when native Sketcher does not expose model preselection.

    Inspect only a bounded number of visible Body Tips in the active document.
    This is presentation-only: no selection, projection, or geometry mutation.
    Edges outside the sketch plane are rejected by passive_sketch_cues.
    Upstream body geometry is safe for passive display; no links are created.
    """
    if sketch is None or sketch.Document is None:
        return None
    candidates = []
    bodies_seen = 0
    for body in sketch.Document.Objects:
        if not hasattr(body, "isDerivedFrom") or not body.isDerivedFrom("PartDesign::Body"):
            continue
        if bodies_seen >= max_bodies:
            break
        bodies_seen += 1
        feature = getattr(body, "Tip", None)
        if feature is None or feature == sketch or not hasattr(feature, "Shape"):
            # Some PartDesign versions make the active sketch the Body Tip.
            # Find the most recent solid before it without changing the Tip.
            feature = next((obj for obj in reversed(tuple(getattr(body, "Group", ())))
                            if obj != sketch and hasattr(obj, "Shape")
                            and not obj.Shape.isNull() and obj.Shape.Edges), None)
        if feature is None:
            continue
        try:
            if not body.ViewObject.Visibility:
                continue
            edges = feature.Shape.Edges
            if not edges or len(edges) > max_edges:
                continue
            names = tuple("Edge" + str(n) for n in range(1, len(edges) + 1))
            cues = passive_sketch_cues(sketch, feature, names)
            for name, edge, x, y in cues:
                world = sketch.Placement.multVec(App.Vector(x, y, 0))
                screen = project_world(world)
                if screen is not None:
                    candidates.append((name, edge, x, y, screen))
        except (AttributeError, RuntimeError, ValueError, TypeError):
            continue
    if not candidates:
        return None
    pixels = {(name, edge, x, y): screen for name, edge, x, y, screen in candidates}
    return nearest_passive_cue(
        tuple(pixels), lambda x, y: next(
            (point for (_name, _edge, px, py), point in pixels.items()
             if px == x and py == y), None),
        cursor, radius_px,
    )


def viewport_passive_cue(sketch, source, edge_names, project_world, cursor,
                         radius_px=12.0):
    """Resolve a hovered model edge to a sketch-plane cue in screen pixels.

    project_world receives a *global* FreeCAD Vector and returns viewport
    pixel coordinates. The sketch-local-to-global transform is essential for
    sketches attached to rotated or offset faces. No Sketcher tool or document
    transaction is invoked. The caller owns visual display and teardown.
    """
    cues = passive_sketch_cues(sketch, source, edge_names)
    if not cues:
        return None

    def project_local(x, y):
        try:
            world = sketch.Placement.multVec(App.Vector(x, y, 0))
            return project_world(world)
        except (AttributeError, ValueError, RuntimeError, TypeError,
                OverflowError):
            return None

    return nearest_passive_cue(cues, project_local, cursor, radius_px)
