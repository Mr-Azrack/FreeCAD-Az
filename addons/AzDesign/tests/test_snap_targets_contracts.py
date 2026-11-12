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
