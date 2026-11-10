# SPDX-License-Identifier: LGPL-2.1-or-later
"""Passive Fusion-style Sketcher inference. No fake model transformations.

FreeCAD Sketcher's real point snapping/autoconstraints remain authoritative.
This module produces exact *visual* cues for the line endpoint/midpoint and
analytic circle/arc center under the cursor. Screen coordinates are passed in,
so the geometry policy can be tested without GUI or OpenGL.
"""

import math


def _screen_distance(a, b):
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def _is_visible_circle_arc(geometry, center, radius, cursor, project):
    # Full circles use a continuous projected ring. An arc only triggers
    # near the actual arc span; never synthesize an invisible arc segment.
    klass = type(geometry).__name__
    first = getattr(geometry, "FirstParameter", None)
    last = getattr(geometry, "LastParameter", None)
    if klass in ("Circle", "GeomCircle") or first is None or last is None:
        return abs(_screen_distance(cursor, project(center)) - radius) <= 11
    try:
        from FreeCAD import Vector
        samples = max(10, min(96, int(abs(last - first) * 20)))
        for i in range(samples + 1):
            angle = first + (last - first) * i / samples
            local = Vector(
                center.x + geometry.Radius * math.cos(angle),
                center.y + geometry.Radius * math.sin(angle),
                center.z,
            )
            if _screen_distance(cursor, project(local)) <= 11:
                return True
    except (ValueError, RuntimeError, TypeError, AttributeError):
        return False
    return False


def hover_candidate(geometry, cursor, project):
    """Return (kind, screen_coordinate, separation_px) or None.

    `project` projects a *sketch-local* FreeCAD Vector into Qt screen
    coordinates. The caller retains control of coordinate transforms,
    device pixel ratio and viewport aspect.
    """
    klass = type(geometry).__name__
    options = []
    if klass == "LineSegment":
        start = geometry.StartPoint
        end = geometry.EndPoint
        p0 = project(start)
        p1 = project(end)
        pm = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        # Midpoint wins against close endpoints when drawing a tiny line.
        for kind, position, radius in (
            ("Midpoint", pm, 13), ("Endpoint", p0, 10),
            ("Endpoint", p1, 10),
        ):
            distance = _screen_distance(cursor, position)
            if distance <= radius:
                options.append((distance / radius, kind, position, distance))
    elif klass in ("Circle", "ArcOfCircle", "GeomCircle"):
        center = geometry.Center
        displayed_center = project(center)
        radial = project(
            type(center)(center.x + geometry.Radius, center.y, center.z)
        )
        radius_px = _screen_distance(displayed_center, radial)
        if (
            _screen_distance(cursor, displayed_center) <= 12
            or (
                radius_px >= 2
                and _is_visible_circle_arc(
                    geometry, center, radius_px, cursor, project
                )
            )
        ):
            options.append((0.0, "Center", displayed_center, 0.0))
    if not options:
        return None
    _quality, kind, position, distance = min(options, key=lambda x: x[0])
    return (kind, position, distance)


def best_snap(geometry, cursor, project, maximum_geometries=700):
    """Prefer the nearest clear target across the active Sketch's geometry."""
    ranked = []
    for i, part in enumerate(geometry):
        if i >= maximum_geometries:
            break
        try:
            candidate = hover_candidate(part, cursor, project)
        except (RuntimeError, ValueError, TypeError, AttributeError):
            continue
        if candidate is not None:
            kind, position, distance = candidate
            # Prefer geometric center and midpoint markers for Fusion-style
            # discovery when several edges have nearby endpoints.
            rank = {"Center": 0, "Midpoint": 1, "Endpoint": 2}[kind]
            ranked.append((rank, distance, i, kind, position))
    if not ranked:
        return None
    rank, distance, index, kind, position = min(ranked)
    return (kind, position, index)
