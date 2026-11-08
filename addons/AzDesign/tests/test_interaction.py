# SPDX-License-Identifier: LGPL-2.1-or-later
"""Headless Az canvas context and common edit-route regression tests."""

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ADDON = Path(__file__).resolve().parents[1]


def obj(*classes, az_type=""):
    result = types.SimpleNamespace(AzType=az_type)
    result.isDerivedFrom = lambda name: name in classes
    return result


class InteractionPoliciesTest(unittest.TestCase):
    def setUp(self):
        self.old_path = list(sys.path)
        sys.path.insert(0, str(ADDON))
        self.old_modules = {
            k: v for k, v in sys.modules.items()
            if k == "azdesign" or k.startswith("azdesign.")
        }
        for key in self.old_modules:
            del sys.modules[key]
        self.gui = types.ModuleType("FreeCADGui")
        self.gui.Control = types.SimpleNamespace(activeDialog=lambda: False)
        self.gui.listCommands = lambda: []
        self.qt = types.ModuleType("azdesign.qt")
        self.qt.QtCore = types.SimpleNamespace()
        self.qt.QtWidgets = types.SimpleNamespace(QFrame=type("FakeFrame", (), {}))
        self.commands = types.ModuleType("azdesign.commands")
        self.modeling = types.ModuleType("azdesign.modeling")
        self.features = types.ModuleType("azdesign.features")
        self.features.DesignError = ValueError
        self.patch = patch.dict(sys.modules, {
            "FreeCADGui": self.gui, "azdesign.qt": self.qt,
            "azdesign.commands": self.commands,
            "azdesign.modeling": self.modeling,
            "azdesign.features": self.features,
        })
        self.patch.start()
        self.context = importlib.import_module("azdesign.canvas_actions")
        self.edit = importlib.import_module("azdesign.feature_edit")

    def tearDown(self):
        self.patch.stop()
        for key in list(sys.modules):
            if key == "azdesign" or key.startswith("azdesign."):
                del sys.modules[key]
        sys.modules.update(self.old_modules)
        sys.path[:] = self.old_path

    def test_sketch_and_face_have_workflow_specific_actions(self):
        sketch = obj("Sketcher::SketchObject")
        solid = obj("PartDesign::Feature")
        self.assertEqual(
            self.context.selection_actions(sketch),
            ("edit", "extrude", "isolate"),
        )
        self.assertEqual(
            self.context.selection_actions(solid, ["Face4"]),
            ("sketch", "presspull", "edit", "isolate"),
        )
        self.assertEqual(
            self.context.selection_actions(solid, ["Edge2"]),
            ("fillet", "chamfer", "snaps", "edit", "isolate"),
        )
        self.assertEqual(
            self.context.selection_actions(obj("PartDesign::Body")),
            ("activate", "isolate"),
        )
        self.assertEqual(self.context.selection_actions(None), ())

    def test_native_feature_uses_native_edit_dialog(self):
        edit = Mock()
        self.gui.getDocument = lambda name: types.SimpleNamespace(setEdit=edit)
        feature = obj("PartDesign::Feature")
        feature.Name = "Pad"
        feature.Document = types.SimpleNamespace(Name="Test")
        self.edit.edit(feature)
        edit.assert_called_once_with("Pad")

    def test_active_native_task_blocks_edit_route(self):
        self.gui.Control.activeDialog = lambda: True
        feature = obj("PartDesign::Feature")
        with self.assertRaisesRegex(ValueError, "Finish or cancel"):
            self.edit.edit(feature)


if __name__ == "__main__":
    unittest.main(verbosity=2)
