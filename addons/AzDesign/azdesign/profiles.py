# SPDX-License-Identifier: LGPL-2.1-or-later
"""Exact planar sketch regions, including intersections, dividers and holes.

OCCT splits the edges. A half-edge walk finds bounded loops without polygonizing
the resulting CAD geometry; sampling is used only to order/orient the graph.
"""

import json
import math
from dataclasses import dataclass
import FreeCAD as App
import Part

TOL = 1e-7


class ProfileError(ValueError):
    pass


@dataclass
class Region:
    face: object
    edges: tuple
    anchor: tuple

    def descriptor(self):
        return json.dumps(
            {"edges": self.edges, "holes": len(self.face.Wires) - 1, "anchor": self.anchor},
            separators=(",", ":"),
        )


def local_edges(sketch):
    inverse = sketch.Placement.inverse()
    edges = []
    for original in sketch.Shape.Edges:
        edge = original.copy()
        edge.Placement = inverse.multiply(edge.Placement)
        if edge.Length > TOL:
            edges.append(edge)
    return edges


def _vertex_key(point, scale):
    return (round(point.x / scale), round(point.y / scale), round(point.z / scale))


def _samples(edge, reverse=False, deflection=0.01):
    if isinstance(edge.Curve, Part.Line):
        points = [edge.valueAt(edge.FirstParameter), edge.valueAt(edge.LastParameter)]
    else:
        points = edge.discretize(Deflection=deflection)
    return list(reversed(points)) if reverse else points


def _bounded_faces(original_edges):
    if not original_edges:
        raise ProfileError("The sketch has no usable edges.")
    compound = Part.makeCompound(original_edges)
    bounds = compound.BoundBox
    span = max(bounds.XLength, bounds.YLength, 1.0)
    if bounds.ZLength > max(TOL * 10, span * 1e-8):
        raise ProfileError("Extrude profiles must lie in one sketch plane.")
    split = (
        original_edges[0].generalFuse(original_edges[1:], TOL)[0]
        if len(original_edges) > 1
        else original_edges[0]
    )
    edges = []
    for candidate in split.Edges:
        if candidate.Length <= TOL or any(candidate.isSame(e) for e in edges):
            continue
        candidate = candidate.copy()
        candidate.Orientation = "Forward"
        edges.append(candidate)
    vertex_scale = max(TOL * 10, span * 1e-9)
    outgoing = {}
    halves = {}
    for index, edge in enumerate(edges):
        first, last = edge.FirstParameter, edge.LastParameter
        begin, end = edge.valueAt(first), edge.valueAt(last)
        keys = (_vertex_key(begin, vertex_scale), _vertex_key(end, vertex_scale))
        for reverse in (False, True):
            half = (index, reverse)
            tangent = -edge.tangentAt(last) if reverse else edge.tangentAt(first)
            start, finish = keys[::-1] if reverse else keys
            halves[half] = (start, finish, math.atan2(tangent.y, tangent.x))
            outgoing.setdefault(start, []).append(half)
    # Dangling lines do not enclose a profile and must not contaminate a loop.
    live = set(halves)
    changed = True
    while changed:
        changed = False
        for items in outgoing.values():
            present = [h for h in items if h in live]
            if len(present) == 1:
                half = present[0]
                live.discard(half)
                live.discard((half[0], not half[1]))
                changed = True
    order = {
        key: sorted((h for h in items if h in live), key=lambda h: halves[h][2])
        for key, items in outgoing.items()
    }
    visited, faces = set(), []
    for seed in sorted(live):
        if seed in visited:
            continue
        loop, current = [], seed
        for _ in range(len(live) + 1):
            if current in visited:
                break
            visited.add(current)
            loop.append(current)
            target = halves[current][1]
            items = order[target]
            reverse = (current[0], not current[1])
            current = items[(items.index(reverse) - 1) % len(items)]
            if current == seed:
                break
        if current != seed:
            continue
        points, wire_edges = [], []
        for index, reverse in loop:
            edge = edges[index].copy()
            points.extend(_samples(edge, reverse, max(span * 1e-4, 1e-5))[:-1])
            if reverse:
                edge.reverse()
            wire_edges.append(edge)
        signed_area = (
            sum(p.x * q.y - q.x * p.y for p, q in zip(points, points[1:] + points[:1])) / 2
        )
        if signed_area <= max(TOL * TOL, span * span * 1e-12):
            continue
        try:
            face = Part.Face(Part.Wire(wire_edges))
        except (Part.OCCError, RuntimeError):
            continue
        if face.isValid() and face.Area > TOL * TOL:
            faces.append(face)
    if not faces:
        raise ProfileError("No closed profiles were found. Close a loop or repair its gaps first.")
    # Disconnected nested loops need an arrangement: annulus and inner disk are
    # separate selectable regions, rather than treating every loop as a hole.
    if len(faces) > 1:
        arrangement = faces[0].generalFuse(faces[1:], TOL)[0]
        faces = [f for f in arrangement.Faces if f.Area > TOL * TOL]
    for face in faces:
        if face.normalAt(0, 0).z < 0:
            face.reverse()
    return faces, bounds


def interior_point(face):
    center = face.CenterOfMass
    if face.isInside(center, TOL, False):
        return center
    points, triangles = face.tessellate(max(face.BoundBox.DiagonalLength * 0.001, 1e-4))
    candidates = []
    for a, b, c in triangles:
        pa, pb, pc = points[a], points[b], points[c]
        candidates.append(((pb - pa).cross(pc - pa).Length, (pa + pb + pc) / 3))
    for _area, point in sorted(candidates, key=lambda item: item[0], reverse=True):
        if face.isInside(point, TOL, False):
            return point
    raise ProfileError("Could not identify an interior point for this region.")


def _edge_membership(face, original_edges):
    result = set()
    tolerance = max(TOL * 20, face.BoundBox.DiagonalLength * 1e-8)
    for boundary in face.Edges:
        parameters = [
            boundary.FirstParameter + (boundary.LastParameter - boundary.FirstParameter) * f
            for f in (0.17, 0.39, 0.61, 0.83)
        ]
        samples = [Part.Vertex(boundary.valueAt(p)) for p in parameters]
        for index, edge in enumerate(original_edges):
            if all(point.distToShape(edge)[0] <= tolerance for point in samples):
                result.add(index)
    return tuple(sorted(result))


def regions(sketch):
    original = local_edges(sketch)
    faces, bounds = _bounded_faces(original)
    result = []
    for face in faces:
        point = interior_point(face)
        anchor = (
            (point.x - bounds.XMin) / max(bounds.XLength, TOL),
            (point.y - bounds.YMin) / max(bounds.YLength, TOL),
        )
        result.append(Region(face, _edge_membership(face, original), anchor))
    return sorted(
        result,
        key=lambda r: (
            round(r.face.BoundBox.XMin, 7),
            round(r.face.BoundBox.YMin, 7),
            round(r.face.Area, 7),
            r.edges,
        ),
    )


def resolve(sketch, descriptors):
    available = regions(sketch)
    bounds = Part.makeCompound(local_edges(sketch)).BoundBox
    selected = []
    for encoded in descriptors:
        reference = json.loads(encoded)
        candidates = [
            r
            for r in available
            if list(r.edges) == reference["edges"] and len(r.face.Wires) - 1 == reference["holes"]
        ]
        if len(candidates) != 1:
            x, y = reference["anchor"]
            point = App.Vector(
                bounds.XMin + x * bounds.XLength, bounds.YMin + y * bounds.YLength, 0
            )
            candidates = [r for r in candidates if r.face.isInside(point, TOL, False)]
        if len(candidates) != 1:
            raise ProfileError(
                "A selected sketch region changed or became ambiguous. Edit the feature and select its profiles again."
            )
        region = candidates[0]
        if not any(region.face.isSame(r.face) for r in selected):
            selected.append(region)
    if not selected:
        raise ProfileError("Select at least one closed profile.")
    return selected


def joined_face(region_list):
    if not region_list:
        raise ProfileError("Select at least one closed profile.")
    faces = [r.face for r in region_list]
    result = faces[0].copy()
    if len(faces) > 1:
        result = result.fuse(faces[1:]).removeSplitter()
    if result.isNull() or not result.isValid():
        raise ProfileError("The selected profiles could not form a valid planar face.")
    return result


def connected_sets(region_list):
    groups = []
    remaining = list(region_list)
    while remaining:
        group = [remaining.pop(0)]
        changed = True
        while changed:
            changed = False
            for region in list(remaining):
                if any(
                    (lambda common: common.Area > TOL * TOL or common.Length > TOL)(
                        region.face.common(other.face)
                    )
                    for other in group
                ):
                    group.append(region)
                    remaining.remove(region)
                    changed = True
        groups.append(group)
    return groups
