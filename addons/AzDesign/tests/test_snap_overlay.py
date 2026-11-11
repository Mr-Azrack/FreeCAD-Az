# SPDX-License-Identifier: LGPL-2.1-or-later
"""GUI-independent integration tests for Az's passive sketch snap overlay."""

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class Vec:
    def __init__(self, x, y, z=0):
        self.x, self.y, self.z = x, y, z


class LineSegment:
    def __init__(self, a, b):
        self.StartPoint, self.EndPoint = a, b


class Circle:
    def __init__(self, center, radius):
        self.Center, self.Radius = center, radius


class Label:
    def __init__(self, owner):
        self.owner = owner
        self.text = ""
        self.visible = False
        self.attrs = []
        self.position = None
        self.deleted = False

    def setObjectName(self, *_): pass
    def setStyleSheet(self, *_): pass
    def setFixedSize(self, *_): pass
    def setAlignment(self, *_): pass
    def setToolTip(self, *_): pass
    def setText(self, value): self.text = value
    def setAttribute(self, key, value): self.attrs.append((key, value))
    def move(self, x, y): self.position = (x, y)
    def hide(self): self.visible = False
    def show(self): self.visible = True
    def raise_(self): pass
    def setParent(self, owner): self.owner = owner
    def deleteLater(self): self.deleted = True


class Widget:
    def width(self): return 500
    def height(self): return 400


class Position:
    def __init__(self, x, y):
        self._x, self._y = x, y

    def x(self): return self._x
    def y(self): return self._y


class Event:
    def __init__(self, x, y):
        self.pos = Position(x, y)

    def position(self): return self.pos


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.old_path = list(sys.path)
        self.old_modules = {
            k: v for k, v in sys.modules.items()
            if k == "azdesign" or k.startswith("azdesign.")
        }
        for key in self.old_modules:
            del sys.modules[key]
        sys.path.insert(0, str(ROOT))
        self.geometry = [LineSegment(Vec(60, 200), Vec(140, 200))]
        self.sketch = types.SimpleNamespace(
            Geometry=self.geometry,
            Placement=types.SimpleNamespace(multVec=lambda value: value),
        )
        view = types.SimpleNamespace(
            getSize=lambda: (500, 400),
            getPointOnScreen=lambda point: (point.x, point.y),
        )
        gui = types.ModuleType("FreeCADGui")
        gui.activeDocument = lambda: types.SimpleNamespace(activeView=lambda: view)
        modeling = types.ModuleType("azdesign.modeling")
        modeling.in_sketch = lambda: self.sketch
        qt = types.ModuleType("azdesign.qt")
        qt.QtCore = types.SimpleNamespace(Qt=types.SimpleNamespace(
            WA_TransparentForMouseEvents=10,
            WA_StyledBackground=11,
            AlignCenter=12,
        ))
        qt.QtWidgets = types.SimpleNamespace(QLabel=Label)
        self.patch = patch.dict(sys.modules, {
            "FreeCADGui": gui,
            "azdesign.modeling": modeling,
            "azdesign.qt": qt,
        })
        self.patch.start()
        self.module = importlib.import_module("azdesign.snap_overlay")

    def tearDown(self):
        self.patch.stop()
        for key in list(sys.modules):
            if key == "azdesign" or key.startswith("azdesign."):
                del sys.modules[key]
        sys.modules.update(self.old_modules)
        sys.path[:] = self.old_path

    def test_line_midpoint_shows_triangle_without_consuming_mouse(self):
        guide = self.module.HoverGuides()
        widget = Widget()
        guide.move(widget, Event(100, 200))
        self.assertTrue(guide.label.visible)
        self.assertEqual(guide.label.text, "△")
        self.assertIn((10, True), guide.label.attrs)
        self.assertEqual(guide.label.position, (92, 192))
        self.assertIs(guide.owner, widget)
        guide.move(widget, Event(490, 100))
        self.assertFalse(guide.label.visible)
        guide.release()
        self.assertIsNone(guide.label)

    def test_hover_circle_rim_shows_analytic_center_marker(self):
        self.geometry[:] = [Circle(Vec(220, 200), 20)]
        guide = self.module.HoverGuides()
        guide.move(Widget(), Event(240, 200))
        self.assertEqual(guide.label.text, "⊙")
        self.assertEqual(guide.label.position, (212, 192))
        self.assertTrue(guide.label.visible)


if __name__ == "__main__":
    unittest.main(verbosity=2)
