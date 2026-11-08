# SPDX-License-Identifier: LGPL-2.1-or-later
"""Cursor inference regressions: no modal finder or model mutation needed."""

import math
import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from azdesign.snap_hover import best_snap, hover_candidate


class Vec:
    def __init__(self, x, y, z=0):
        self.x, self.y, self.z = x, y, z


class LineSegment:
    def __init__(self, start, end):
        self.StartPoint = start
        self.EndPoint = end


class Circle:
    def __init__(self, center, radius):
        self.Center, self.Radius = center, radius


class ArcOfCircle(Circle):
    FirstParameter = 0
    LastParameter = math.pi / 2


def project(p):
    return (p.x * 2, p.y * 2)


class HoverSnapTests(unittest.TestCase):
    def test_midpoint_triangle_is_automatic_on_line_hover(self):
        line = LineSegment(Vec(1, 2), Vec(9, 2))
        kind, pos, distance = hover_candidate(line, (10, 4), project)
        self.assertEqual(kind, "Midpoint")
        self.assertEqual(pos, (10, 4))
        self.assertEqual(distance, 0)

    def test_line_endpoint_marker_when_near_start(self):
        line = LineSegment(Vec(1, 2), Vec(12, 2))
        kind, pos, _ = hover_candidate(line, (2, 4), project)
        self.assertEqual(kind, "Endpoint")
        self.assertEqual(pos, (2, 4))

    def test_circle_edge_hover_reveals_exact_center_not_ring_point(self):
        circle = Circle(Vec(8, 6), 5)
        kind, pos, _ = hover_candidate(circle, (26, 12), project)
        self.assertEqual(kind, "Center")
        self.assertEqual(pos, (16, 12))
        kind, pos, _ = hover_candidate(circle, (16, 12), project)
        self.assertEqual(kind, "Center")
        self.assertEqual(pos, (16, 12))

    def test_unrelated_cursor_has_no_marker(self):
        geo = [LineSegment(Vec(1, 2), Vec(12, 2))]
        self.assertIsNone(best_snap(geo, (400, 400), project))

    def test_automatic_best_target_needs_no_selection_or_button(self):
        geo = [LineSegment(Vec(1, 2), Vec(12, 2)), Circle(Vec(8, 6), 5)]
        selected = best_snap(geo, (26, 12), project)
        self.assertEqual(selected[0], "Center")
        self.assertEqual(selected[1], (16, 12))
        self.assertEqual(selected[2], 1)

    def test_outside_arc_span_is_not_mistaken_for_visible_circle(self):
        # Arc covers only top-right quarter. The opposite arc position
        # must not light up the center as though the circle were complete.
        arc = ArcOfCircle(Vec(10, 10), 6)
        fake = types.SimpleNamespace(Vector=Vec)
        old = sys.modules.get("FreeCAD")
        sys.modules["FreeCAD"] = fake
        try:
            self.assertIsNone(hover_candidate(arc, (8, 20), project))
            candidate = hover_candidate(arc, (32, 20), project)
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate[0], "Center")
        finally:
            if old is None:
                sys.modules.pop("FreeCAD", None)
            else:
                sys.modules["FreeCAD"] = old


if __name__ == "__main__":
    unittest.main(verbosity=2)
