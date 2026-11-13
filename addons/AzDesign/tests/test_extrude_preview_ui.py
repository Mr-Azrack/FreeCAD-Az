# SPDX-License-Identifier: LGPL-2.1-or-later
"""Headless behavioral regressions for Extrude profile selection stability.

Tests the actual task methods with minimal FreeCAD/Qt stubs: no GUI renderer,
but the original Body's visibility, timer, and invalid preview cleanup are
observed directly. Native geometry is exercised separately in test_workflow.
"""

import importlib
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ADDON = Path(__file__).resolve().parents[1]


class ExtrudePreviewUiTest(unittest.TestCase):
    def setUp(self):
        self.old_path = list(sys.path)
        self.old_modules = {
            key: module for key, module in sys.modules.items()
            if key == "azdesign" or key.startswith("azdesign.")
        }
        for key in self.old_modules:
            del sys.modules[key]
        sys.path.insert(0, str(ADDON))
        app = types.ModuleType("FreeCAD")
        app.Console = types.SimpleNamespace(PrintWarning=Mock())
        gui = types.ModuleType("FreeCADGui")
        qt = types.ModuleType("azdesign.qt")
        qt.QtCore = types.SimpleNamespace()
        qt.QtWidgets = types.SimpleNamespace()
        qt.standard_button_bits = lambda *_: 0x00400400
        features = types.ModuleType("azdesign.features")
        features.DesignError = ValueError
        stubs = {
            "FreeCAD": app,
            "FreeCADGui": gui,
            "azdesign.qt": qt,
            "azdesign.features": features,
            "azdesign.profiles": types.ModuleType("azdesign.profiles"),
            "azdesign.operations": types.ModuleType("azdesign.operations"),
            "azdesign.history": types.ModuleType("azdesign.history"),
        }
        self.patch = patch.dict(sys.modules, stubs)
        self.patch.start()
        self.module = importlib.import_module("azdesign.tasks")
        self.task = self.module.ExtrudeTask.__new__(self.module.ExtrudeTask)
        self.task.timer = Mock()
        self.task.closed = False
        self.task.busy = False
        self.task.valid = True
        self.task.picking = None
        self.task.operation = Mock()
        self.task.message = Mock()
        self.task.manipulator = None
        self.task.overlay_names = []

    def tearDown(self):
        self.patch.stop()
        for key in list(sys.modules):
            if key == "azdesign" or key.startswith("azdesign."):
                del sys.modules[key]
        sys.modules.update(self.old_modules)
        sys.path[:] = self.old_path

    def test_empty_multi_profile_selection_never_computes_geometry(self):
        sketch = types.SimpleNamespace()
        sketch.isDerivedFrom = lambda kind: kind == "Sketcher::SketchObject"
        self.task.spec = lambda: {
            "source": (sketch, []), "regions": [], "whole": False,
        }
        self.task.preview()
        self.task.operation.update.assert_not_called()
        self.task.operation.discard_preview.assert_called_once()
        self.assertFalse(self.task.valid)
        self.assertIn("original solid", self.task.message.call_args.args[0])

    def test_failed_new_preview_discards_temporary_geometry(self):
        solid = types.SimpleNamespace()
        solid.isDerivedFrom = lambda kind: kind == "PartDesign::Feature"
        self.task.spec = lambda: {"source": (solid, ["Face1"]), "regions": []}
        self.task.operation.update.side_effect = ValueError("Disconnected Join")
        self.task.preview()
        self.task.operation.discard_preview.assert_called_once()
        self.assertFalse(self.task.valid)
        self.assertIn("Original geometry restored", self.task.message.call_args.args[0])

    def test_profile_overlay_picking_keeps_body_and_base_visible(self):
        body = types.SimpleNamespace(
            ViewObject=types.SimpleNamespace(Visibility=True),
        )
        body.isDerivedFrom = lambda cls: cls == "PartDesign::Body"
        original = types.SimpleNamespace(
            ViewObject=types.SimpleNamespace(Visibility=True),
        )
        original.isDerivedFrom = lambda cls: cls == "PartDesign::Feature"
        self.task.doc = types.SimpleNamespace(Objects=[body, original],
                                              getObject=lambda _name: None)
        self.task.apply_pick_visibility()
        self.assertTrue(body.ViewObject.Visibility)
        self.assertTrue(original.ViewObject.Visibility)
        self.task.operation.discard_preview.assert_called_once()
        self.task.timer.stop.assert_called_once()

    def test_profile_picking_does_not_start_competing_preview_timer(self):
        self.task.picking = "profiles"
        self.task.direction = Mock()
        self.task.direction.currentText.return_value = "One side"
        self.task.extent = Mock()
        self.task.extent.currentText.return_value = "Distance"
        self.task.distance2 = Mock()
        self.task.taper2 = Mock()
        self.task.pick_limit = Mock()
        self.task.fields = Mock()
        self.task.distance = Mock()
        self.task.schedule()
        self.task.timer.stop.assert_called_once()
        self.task.timer.start.assert_not_called()

    def test_edit_first_extrude_face_pick_keeps_original_solid_visible(self):
        # New Body Extrudes have no earlier Body Tip to display while
        # picking a different source face. Never blank out their result.
        feature = types.SimpleNamespace(
            ViewObject=types.SimpleNamespace(Visibility=True)
        )
        self.task.operation.editing = [feature]
        self.task.operation.outputs = [feature]
        self.task.operation.original_bases = {"Body": None}
        self.task.doc = types.SimpleNamespace(getObject=lambda _name: None)
        self.task.pick_regions = Mock()
        self.module.Gui.Selection = types.SimpleNamespace(clearSelection=Mock())
        self.task.begin_face_pick("source")
        self.assertTrue(feature.ViewObject.Visibility)
        self.assertIn("reference-only", self.task.message.call_args.args[0])
        self.task.operation.discard_preview.assert_called_once()

    def test_face_pick_with_earlier_tip_hides_current_preview(self):
        feature = types.SimpleNamespace(
            ViewObject=types.SimpleNamespace(Visibility=True)
        )
        self.task.operation.editing = [feature]
        self.task.operation.outputs = [feature]
        self.task.operation.original_bases = {"Body": object()}
        self.task.doc = types.SimpleNamespace(getObject=lambda _name: None)
        self.task.pick_regions = Mock()
        self.module.Gui.Selection = types.SimpleNamespace(clearSelection=Mock())
        self.task.begin_face_pick("source")
        self.assertFalse(feature.ViewObject.Visibility)


if __name__ == "__main__":
    unittest.main(verbosity=2)
