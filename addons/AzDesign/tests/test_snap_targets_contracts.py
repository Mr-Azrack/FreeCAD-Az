#!/usr/bin/env python3
"""Fast executable regression for native associative Sketcher references."""
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = str(Path(__file__).resolve().parents[1])

class Doc:
    def __init__(self): self.calls = []
    def openTransaction(self, _): self.calls.append("begin")
    def commitTransaction(self): self.calls.append("commit")
    def abortTransaction(self): self.calls.append("abort")
    def recompute(self): self.calls.append("recompute")

class Sketch:
    State = ()
    def __init__(self, doc):
        self.Document, self.added, self.fail = doc, [], None
    def isDerivedFrom(self, kind): return kind == "Sketcher::SketchObject"
    def addExternal(self, name, edge):
        if edge == self.fail: raise RuntimeError("native failure")
        self.added.append((name, edge))
        return len(self.added)

class EdgeReferenceTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, ROOT)
        self.old = {k: v for k, v in sys.modules.items()
                    if k == "azdesign" or k.startswith("azdesign.")}
        for k in self.old: sys.modules.pop(k)
        self.gui = types.ModuleType("FreeCADGui")
        self.gui.Selection = types.SimpleNamespace(getSelectionEx=lambda: [])
        self.stub = patch.dict(sys.modules, {
            "FreeCAD": types.ModuleType("FreeCAD"),
            "FreeCADGui": self.gui, "Part": types.ModuleType("Part"),
            "Sketcher": types.ModuleType("Sketcher"),
            "azdesign.features": types.SimpleNamespace(DesignError=ValueError),
        })
        self.stub.start()
        self.api = importlib.import_module("azdesign.snap_targets")
        self.doc = Doc()
        self.sketch = Sketch(self.doc)
        self.source = types.SimpleNamespace(
            Name="Pad", Document=self.doc,
            Shape=types.SimpleNamespace(isNull=lambda: False,
                                        Edges=[object(), object()]),
            OutListRecursive=())
    def tearDown(self):
        self.stub.stop()
        for k in list(sys.modules):
            if k == "azdesign" or k.startswith("azdesign."): sys.modules.pop(k)
        sys.modules.update(self.old)
        sys.path.remove(ROOT)
    def select(self, *names):
        hit = types.SimpleNamespace(Object=self.source, SubElementNames=names)
        self.gui.Selection.getSelectionEx = lambda: [hit]
    def test_passive_cues_do_not_mutate_sketch(self):
        class Vec:
            def __init__(self, x, y, z=0):
                self.x, self.y, self.z = x, y, z
            def __sub__(self, other):
                return Vec(self.x - other.x, self.y - other.y, self.z - other.z)
            @property
            def Length(self):
                return (self.x*self.x + self.y*self.y + self.z*self.z)**0.5
        class Edge:
            FirstParameter, LastParameter = 0, 1
            Curve = object()
            Vertexes = [types.SimpleNamespace(Point=Vec(0, 0)),
                        types.SimpleNamespace(Point=Vec(10, 0))]
            def isNull(self): return False
            def valueAt(self, t): return Vec(10*t, 0)
        self.source.Shape.Edges = [Edge()]
        self.sketch.Placement = types.SimpleNamespace(
            inverse=lambda: types.SimpleNamespace(multVec=lambda p: p))
        cues = self.api.passive_sketch_cues(self.sketch, self.source, ("Edge1",))
        self.assertEqual([item[0] for item in cues],
                         ["Start", "End", "Midpoint"])
        self.assertEqual(cues[-1][2:], (5.0, 0.0))
        self.assertEqual(self.doc.calls, [])
        self.assertEqual(self.sketch.added, [])
        self.source.Shape.Edges[0].Vertexes[0].Point.z = 1
        cues = self.api.passive_sketch_cues(self.sketch, self.source, ("Edge1",))
        self.assertNotIn("Start", [item[0] for item in cues])

    def test_passive_hover_ignores_stale_and_unsupported_topology(self):
        self.sketch.Placement = types.SimpleNamespace(
            inverse=lambda: types.SimpleNamespace(multVec=lambda p: p))
        self.assertEqual(self.api.passive_sketch_cues(
            self.sketch, self.source, ("Edge99",)), ())
        self.assertEqual(self.api.passive_sketch_cues(
            self.sketch, self.source, ("Face1",)), ())
        self.assertEqual(self.doc.calls, [])
        self.assertEqual(self.sketch.added, [])

    def test_nearest_hover_skips_failed_projection(self):
        cues = (("Start", "Edge1", 1.0, 2.0),
                ("End", "Edge2", 3.0, 4.0))
        def projection(x, y):
            if x == 1.0:
                raise RuntimeError("viewport changing")
            return (x * 10, y * 10)
        self.assertEqual(self.api.nearest_passive_cue(
            cues, projection, (30, 40)), cues[1])
        self.assertEqual(self.doc.calls, [])

    def test_nearest_passive_cue_rejects_ambiguous_screen_ties(self):
        cues = (("Midpoint", "Edge1", 5.0, 0.0),
                ("Center", "Edge2", 5.0, 0.0),
                ("End", "Edge3", 7.0, 0.0))
        project = lambda x, y: (10 * x, 10 * y)
        self.assertEqual(self.api.nearest_passive_cue(cues, project, (50, 0)),
                         cues[0])
        self.assertIsNone(self.api.nearest_passive_cue(
            (cues[0], cues[2]), project, (60, 0)))
        self.assertIsNone(self.api.nearest_passive_cue(
            cues, project, (300, 300)))
        self.assertEqual(self.doc.calls, [])
        self.assertEqual(self.sketch.added, [])

    def test_passive_cue_rejects_invalid_radius_and_clipped_points(self):
        with self.assertRaises(ValueError):
            self.api.nearest_passive_cue((), lambda x, y: (x, y),
                                         (0, 0), radius_px=0)
        self.assertIsNone(self.api.nearest_passive_cue(
            (("Center", "Edge1", 0, 0),), lambda x, y: None, (0, 0)))

    def test_viewport_adapter_transforms_local_to_world_without_mutation(self):
        class Vec:
            def __init__(self, x, y, z=0):
                self.x, self.y, self.z = x, y, z
            def __sub__(self, other):
                return Vec(self.x-other.x, self.y-other.y, self.z-other.z)
            @property
            def Length(self):
                return (self.x*self.x+self.y*self.y+self.z*self.z)**0.5
        class Edge:
            FirstParameter, LastParameter = 0, 1
            Curve = object()
            Vertexes = [types.SimpleNamespace(Point=Vec(100, 200)),
                        types.SimpleNamespace(Point=Vec(110, 200))]
            def isNull(self): return False
            def valueAt(self, t): return Vec(100+10*t, 200)
        self.source.Shape.Edges = [Edge()]
        placement = types.SimpleNamespace(
            inverse=lambda: types.SimpleNamespace(
                multVec=lambda p: Vec(p.x-100, p.y-200, p.z)),
            multVec=lambda p: Vec(p.x+100, p.y+200, p.z))
        self.sketch.Placement = placement
        self.api.App.Vector = Vec
        seen = []
        def project(point):
            seen.append((point.x, point.y, point.z))
            return (point.x, point.y)
        cue = self.api.viewport_passive_cue(
            self.sketch, self.source, ("Edge1",), project, (105, 200), 3)
        self.assertEqual(cue[0], "Midpoint")
        self.assertIn((105.0, 200.0, 0.0), seen)
        self.assertEqual(self.doc.calls, [])
        self.assertEqual(self.sketch.added, [])

    def test_viewport_adapter_fails_closed_on_projection_error(self):
        self.sketch.Placement = types.SimpleNamespace(
            inverse=lambda: types.SimpleNamespace(multVec=lambda p: p),
            multVec=lambda p: p)
        self.api.App.Vector = lambda x, y, z: (x, y, z)
        self.assertIsNone(self.api.viewport_passive_cue(
            self.sketch, self.source, ("Edge99",),
            lambda p: (_ for _ in ()).throw(RuntimeError("stale view")),
            (0, 0)))
        self.assertEqual(self.doc.calls, [])

    def test_visible_body_fallback_finds_midpoint_without_preselection(self):
        class Vec:
            def __init__(self, x, y, z=0):
                self.x, self.y, self.z = x, y, z
            def __sub__(self, other):
                return Vec(self.x-other.x, self.y-other.y, self.z-other.z)
            @property
            def Length(self):
                return (self.x*self.x+self.y*self.y+self.z*self.z)**0.5
        class Edge:
            FirstParameter, LastParameter = 0, 1
            Curve = object()
            Vertexes = [types.SimpleNamespace(Point=Vec(0, 0)),
                        types.SimpleNamespace(Point=Vec(10, 0))]
            def isNull(self): return False
            def valueAt(self, t): return Vec(10*t, 0)
        self.api.App.Vector = Vec
        self.source.Shape.Edges = [Edge()]
        self.source.OutListRecursive = (self.sketch,)
        self.sketch.Placement = types.SimpleNamespace(
            inverse=lambda: types.SimpleNamespace(multVec=lambda p: p),
            multVec=lambda p: p)
        body = types.SimpleNamespace(
            isDerivedFrom=lambda kind: kind == "PartDesign::Body",
            Tip=self.sketch, Group=[self.source, self.sketch],
            ViewObject=types.SimpleNamespace(Visibility=True))
        self.doc.Objects = [body, self.source, self.sketch]
        cue = self.api.visible_body_cue(
            self.sketch, lambda point: (point.x, point.y), (5, 0), radius_px=3)
        self.assertEqual(cue, ("Midpoint", "Edge1", 5.0, 0.0))
        self.assertEqual(self.doc.calls, [])
        self.assertEqual(self.sketch.added, [])
        # Passive inference is safe for an upstream dependency, but creating
        # an actual external link must still enforce the cycle guard.
        with self.assertRaisesRegex(ValueError, "circular"):
            self.api.link_body_edge(self.sketch, self.source, "Edge1")

    def test_visible_body_fallback_finds_circular_hole_center(self):
        class Vec:
            def __init__(self, x, y, z=0): self.x, self.y, self.z = x, y, z
            def __sub__(self, other): return Vec(self.x-other.x, self.y-other.y, self.z-other.z)
            @property
            def Length(self): return (self.x*self.x+self.y*self.y+self.z*self.z)**0.5
        class Circle:
            Center = Vec(25, 30)
        class Edge:
            Curve = Circle()
            Vertexes = []
            def isNull(self): return False
        self.api.App.Vector = Vec
        self.source.Shape.Edges = [Edge()]
        self.sketch.Placement = types.SimpleNamespace(
            inverse=lambda: types.SimpleNamespace(multVec=lambda p: p),
            multVec=lambda p: p)
        body = types.SimpleNamespace(
            isDerivedFrom=lambda kind: kind == "PartDesign::Body",
            Tip=self.source, Group=[self.source, self.sketch],
            ViewObject=types.SimpleNamespace(Visibility=True))
        self.doc.Objects = [body, self.source, self.sketch]
        self.assertEqual(self.api.visible_body_cue(
            self.sketch, lambda p: (p.x, p.y), (25, 30)),
            ("Center", "Edge1", 25.0, 30.0))
        self.assertEqual(self.doc.calls, [])
        self.assertEqual(self.sketch.added, [])

    def test_single_edge_commits(self):
        self.assertEqual(self.api.link_body_edge(self.sketch, self.source, "Edge1"), 1)
        self.assertEqual(self.doc.calls, ["begin", "recompute", "commit"])
    def test_batch_deduplicates(self):
        self.select("Edge1", "Face1", "Edge1", "Edge2")
        self.assertEqual(self.api.link_selected_body_edges(self.sketch), (1, 2))
        self.assertEqual(self.sketch.added, [("Pad", "Edge1"), ("Pad", "Edge2")])
        self.assertEqual(self.doc.calls.count("commit"), 1)
    def test_batch_failure_aborts(self):
        self.select("Edge1", "Edge2")
        self.sketch.fail = "Edge2"
        with self.assertRaisesRegex(RuntimeError, "native failure"):
            self.api.link_selected_body_edges(self.sketch)
        self.assertEqual(self.doc.calls, ["begin", "abort", "recompute"])
    def test_cycle_rejected(self):
        self.source.OutListRecursive = (self.sketch,)
        with self.assertRaisesRegex(ValueError, "circular"):
            self.api.link_body_edge(self.sketch, self.source, "Edge1")
        self.assertEqual(self.doc.calls, [])
    def test_invalid_edge_rejected(self):
        with self.assertRaisesRegex(ValueError, "no longer exists"):
            self.api.link_body_edge(self.sketch, self.source, "Edge3")
        self.assertEqual(self.doc.calls, [])

if __name__ == "__main__":
    unittest.main()
