# SPDX-License-Identifier: LGPL-2.1-or-later
"""Resolve face intent after a generated solid's topological numbering changes."""

import json
import FreeCAD as App
import Part
from .profiles import interior_point


def _local_shape(obj):
    shape = obj.Shape.copy()
    shape.Placement = obj.Placement.inverse().multiply(shape.Placement)
    return shape


def face_signature(obj, name):
    shape = _local_shape(obj)
    face = shape.getElement(name.lstrip("?"))
    bounds = shape.BoundBox
    point = interior_point(face)
    anchor = [
        (point.x - bounds.XMin) / max(bounds.XLength, 1e-7),
        (point.y - bounds.YMin) / max(bounds.YLength, 1e-7),
        (point.z - bounds.ZMin) / max(bounds.ZLength, 1e-7),
    ]
    normal = face.normalAt(0, 0)
    return json.dumps(
        {
            "element": name.lstrip("?"),
            "kind": type(face.Surface).__name__,
            "anchor": anchor,
            "normal": list(normal),
            "wires": len(face.Wires),
            "area_fraction": face.Area / max(shape.Area, 1e-12),
        }
    )


def resolve_face(obj, name, signature=""):
    if not signature:
        return obj.Shape.getElement(name.lstrip("?")), name.lstrip("?")
    reference = json.loads(signature)
    shape = _local_shape(obj)
    bounds = shape.BoundBox
    x, y, z = reference["anchor"]
    point = App.Vector(
        bounds.XMin + x * bounds.XLength,
        bounds.YMin + y * bounds.YLength,
        bounds.ZMin + z * bounds.ZLength,
    )
    normal = App.Vector(*reference["normal"])
    candidates = []
    for index, face in enumerate(shape.Faces):
        if type(face.Surface).__name__ != reference["kind"]:
            continue
        if reference["kind"] == "Plane" and face.normalAt(0, 0).dot(normal) < 0.99:
            continue
        distance = face.distToShape(Part.Vertex(point))[0] / max(bounds.DiagonalLength, 1e-7)
        area = abs(face.Area / max(shape.Area, 1e-12) - reference["area_fraction"])
        wire_penalty = 0 if len(face.Wires) == reference["wires"] else 0.1
        candidates.append((distance + area * 0.05 + wire_penalty, index + 1))
    candidates.sort()
    if not candidates or candidates[0][0] > 0.15:
        raise ValueError("The referenced face changed. Edit the feature and pick its face again.")
    if len(candidates) > 1 and abs(candidates[1][0] - candidates[0][0]) < 1e-6:
        raise ValueError("The referenced face became ambiguous. Pick it again instead of guessing.")
    selected = "Face" + str(candidates[0][1])
    return obj.Shape.getElement(selected), selected
