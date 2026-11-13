# SPDX-License-Identifier: LGPL-2.1-or-later
"""Headless regression for the compact, working native Sketch Palette.

No Qt dependency in the lightweight CI job: exercise all five real controls,
visibility of unsupported actions, and no duplicated ribbon draw buttons.
"""

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ADDON = Path(__file__).resolve().parents[1]


class Signal:
    def __init__(self):
        self.handlers = []

    def connect(self, handler):
        self.handlers.append(handler)

    def emit(self, checked):
        for handler in list(self.handlers):
            handler(checked)


class FakeWidget:
    def __init__(self, *args):
        self.text = args[0] if args and isinstance(args[0], str) else ""
        self.enabled = True
        self.visible = True
        self.checked = False
        self.blocked = False
        self.max_height = None
        self.toggled = Signal()
        self.clicked = Signal()
        self.children = []

    def setObjectName(self, name):
        self.name = name

    def setAttribute(self, *_args): pass
    def setStyleSheet(self, *_args): pass
    def setContentsMargins(self, *_args): pass
    def setSpacing(self, *_args): pass
    def setWordWrap(self, *_args): pass
    def setMinimumWidth(self, *_args): pass
    def setMaximumHeight(self, height):
        self.max_height = height

    def setToolTip(self, *_args): pass
    def addWidget(self, widget): self.children.append(widget)
    def setText(self, text): self.text = text
    def setVisible(self, visible): self.visible = bool(visible)
    def setEnabled(self, enabled): self.enabled = bool(enabled)
    def blockSignals(self, blocked): self.blocked = bool(blocked)
    def isChecked(self): return self.checked

    def setChecked(self, checked):
        was_changed = self.checked != bool(checked)
        self.checked = bool(checked)
        if was_changed and not self.blocked:
            self.toggled.emit(self.checked)


class NativeAction:
    def __init__(self):
        self.checked = False
        self.calls = 0

    def isCheckable(self): return True
    def isChecked(self): return self.checked
    def trigger(self):
        self.checked = not self.checked
        self.calls += 1


class SketchPaletteTest(unittest.TestCase):
    def setUp(self):
        self.old_path = list(sys.path)
        self.old_modules = {
            k: v for k, v in sys.modules.items()
            if k == "azdesign" or k.startswith("azdesign.")
        }
        for key in self.old_modules:
            del sys.modules[key]
        sys.path.insert(0, str(ADDON))
        self.action = NativeAction()
        self.gui = types.ModuleType("FreeCADGui")
        self.gui.Command = types.SimpleNamespace(
            get=lambda name: types.SimpleNamespace(
                getAction=lambda: self.action
            )
        )
        self.qt = types.ModuleType("azdesign.qt")
        self.qt.QtCore = types.SimpleNamespace(
            Qt=types.SimpleNamespace(WA_StyledBackground=1)
        )
        self.qt.QtWidgets = types.SimpleNamespace(
            QWidget=FakeWidget, QLabel=FakeWidget,
            QVBoxLayout=FakeWidget, QCheckBox=FakeWidget,
            # The sole button projects native solid-edge references, not
            # another copy of the sketch drawing controls.
            QPushButton=FakeWidget,
        )
        self.patch = patch.dict(sys.modules, {
            "FreeCADGui": self.gui,
            "azdesign.qt": self.qt,
        })
        self.patch.start()
        self.module = importlib.import_module("azdesign.sketch_palette")
        self.appearance = types.SimpleNamespace(grid_visible=True)
        self.appearance.toggle_grid = self.toggle_grid
        self.view = types.SimpleNamespace(
            ShowGrid=True, GridAuto=True,
            Autoconstraints=True, AvoidRedundant=False,
        )
        self.sketch = types.SimpleNamespace(
            Label="Sample Sketch", ViewObject=self.view,
            GeometryCount=2, ConstraintCount=1,
        )

    def tearDown(self):
        self.patch.stop()
        for key in list(sys.modules):
            if key == "azdesign" or key.startswith("azdesign."):
                del sys.modules[key]
        sys.modules.update(self.old_modules)
        sys.path[:] = self.old_path

    def toggle_grid(self, checked):
        self.appearance.grid_visible = checked

    def test_compact_real_controls_and_native_refresh(self):
        panel = self.module.SketchPalette(self.appearance)
        self.assertLessEqual(panel.max_height, 270)
        self.assertEqual(panel.solid_snap.text, "Use solid edges for snapping")
        self.assertEqual(
            set(panel.flags), {
                "grid", "auto_grid", "auto_constraints",
                "avoid_redundant", "snap",
            }
        )
        panel.refresh(self.sketch)
        self.assertTrue(all(control.visible for control in panel.flags.values()))
        self.assertIn("2 curves", panel.summary.text)
        self.assertTrue(panel.flags["grid"].checked)
        self.assertTrue(panel.flags["auto_grid"].checked)
        self.assertTrue(panel.flags["auto_constraints"].checked)
        self.assertFalse(panel.flags["avoid_redundant"].checked)

    def test_native_property_checkbox_changes_real_freecad_property(self):
        panel = self.module.SketchPalette(self.appearance)
        panel.refresh(self.sketch)
        panel.flags["auto_constraints"].setChecked(False)
        self.assertFalse(self.view.Autoconstraints)
        panel.flags["avoid_redundant"].setChecked(True)
        self.assertTrue(self.view.AvoidRedundant)
        panel.flags["auto_grid"].setChecked(False)
        self.assertFalse(self.view.GridAuto)
        panel.flags["grid"].setChecked(False)
        self.assertFalse(self.appearance.grid_visible)

    def test_snap_calls_actual_native_checked_action(self):
        panel = self.module.SketchPalette(self.appearance)
        panel.refresh(self.sketch)
        panel.flags["snap"].setChecked(True)
        self.assertEqual(self.action.calls, 1)
        self.assertTrue(self.action.isChecked())
        panel.refresh(self.sketch)
        self.assertTrue(panel.flags["snap"].checked)
        panel.flags["snap"].setChecked(False)
        self.assertEqual(self.action.calls, 2)
        self.assertFalse(self.action.isChecked())

    def test_unsupported_native_options_are_not_dead_checkboxes(self):
        del self.view.GridAuto
        del self.view.AvoidRedundant
        self.gui.Command.get = lambda name: (_ for _ in ()).throw(RuntimeError("missing"))
        panel = self.module.SketchPalette(self.appearance)
        panel.refresh(self.sketch)
        self.assertFalse(panel.flags["auto_grid"].visible)
        self.assertFalse(panel.flags["avoid_redundant"].visible)
        self.assertFalse(panel.flags["snap"].visible)
        self.assertTrue(panel.flags["grid"].visible)
        self.assertTrue(panel.flags["auto_constraints"].visible)


if __name__ == "__main__":
    unittest.main(verbosity=2)
