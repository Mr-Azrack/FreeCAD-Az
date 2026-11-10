#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Contract tests for Design native Mirror/Pattern with no FreeCAD GUI needed."""
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ADDON = Path(__file__).resolve().parents[1]


class Shape:
    Solids = [object()]

    def isNull(self):
        return False

    def isValid(self):
        return True


class FakeTransform:
    PropertiesList = ["TransformMode", "Originals", "MirrorPlane", "Direction",
                      "Mode", "Offset", "Occurrences"]

    def __init__(self, name):
        self.TypeId = name
        self.Shape = Shape()
        self.ViewObject = types.SimpleNamespace(Visibility=True)
        self.State = ()
        self.Name = "Transform"


class FakeDoc:
    def __init__(self):
        self.actions = []

    def openTransaction(self, text):
        self.actions.append("open")

    def recompute(self):
        self.actions.append("recompute")

    def commitTransaction(self):
        self.actions.append("commit")

    def abortTransaction(self):
        self.actions.append("abort")

    def getObject(self, name):
        return None


class NativeTransformContracts(unittest.TestCase):
    def setUp(self):
        self.old_path = list(sys.path)
        sys.path.insert(0, str(ADDON))
        self.old_modules = {
            key: mod for key, mod in sys.modules.items()
            if key == "azdesign" or key.startswith("azdesign.")
        }
        for key in self.old_modules:
            del sys.modules[key]
        gui = types.ModuleType("FreeCADGui")
        gui.Control = types.SimpleNamespace(activeDialog=lambda: False)
        gui.Selection = types.SimpleNamespace(
            clearSelection=lambda: None, addSelection=lambda *args: None
        )
        qt = types.ModuleType("azdesign.qt")
        qt.QtWidgets = types.SimpleNamespace()
        features = types.ModuleType("azdesign.features")
        features.DesignError = type("DesignError", (ValueError,), {})
        features.owner_body = lambda feature: None
        self.patches = patch.dict(sys.modules, {
            "FreeCADGui": gui, "azdesign.qt": qt, "azdesign.features": features
        })
        self.patches.start()
        self.module = importlib.import_module("azdesign.feature_transform")
        self.doc = FakeDoc()
        self.feature = types.SimpleNamespace(
            Name="Pad", Label="Pad", ViewObject=types.SimpleNamespace(Visibility=True)
        )
        self.body = types.SimpleNamespace(
            Document=self.doc, Tip=self.feature,
            Group=[self.feature],
            Origin=types.SimpleNamespace(OriginFeatures=[
                types.SimpleNamespace(Role=name)
                for name in ("XY_Plane", "XZ_Plane", "YZ_Plane",
                             "X_Axis", "Y_Axis", "Z_Axis")
            ]),
        )
        self.body.newObject = lambda kind, name: FakeTransform(kind)
        self.module.selected_feature = lambda: (self.feature, self.body)

    def tearDown(self):
        self.patches.stop()
        for key in list(sys.modules):
            if key == "azdesign" or key.startswith("azdesign."):
                del sys.modules[key]
        sys.modules.update(self.old_modules)
        sys.path[:] = self.old_path

    def test_mirror_uses_parametric_original_and_body_origin_plane(self):
        self.module.parameters = lambda mode, feature: ("YZ_Plane", 0, 0.0)
        obj = self.module.show("mirror")
        self.assertEqual(obj.TypeId, "PartDesign::Mirrored")
        self.assertEqual(obj.Originals, [self.feature])
        self.assertEqual(obj.MirrorPlane[0].Role, "YZ_Plane")
        self.assertEqual(self.body.Tip, obj)
        self.assertIn("commit", self.doc.actions)

    def test_linear_pattern_retains_repetition_and_spacing(self):
        self.module.parameters = lambda mode, feature: ("X_Axis", 4, 12.5)
        obj = self.module.show("linear")
        self.assertEqual(obj.TypeId, "PartDesign::LinearPattern")
        self.assertEqual(obj.Originals, [self.feature])
        self.assertEqual(obj.Direction[0].Role, "X_Axis")
        self.assertEqual(obj.Mode, "Spacing")
        self.assertEqual(obj.Occurrences, 4)
        self.assertEqual(obj.Offset, 12.5)
        self.assertIn("commit", self.doc.actions)

    def test_invalid_solid_aborts_native_transaction(self):
        class InvalidShape(Shape):
            def isValid(self):
                return False
        self.body.newObject = lambda kind, name: types.SimpleNamespace(
            PropertiesList=["TransformMode", "Originals", "MirrorPlane"],
            Shape=InvalidShape(), Name="Mirror",
            ViewObject=types.SimpleNamespace(Visibility=True),
        )
        self.module.parameters = lambda mode, feature: ("XY_Plane", 0, 0.0)
        with self.assertRaisesRegex(ValueError, "valid solid"):
            self.module.show("mirror")
        self.assertIn("abort", self.doc.actions)
        self.assertNotIn("commit", self.doc.actions)


if __name__ == "__main__":
    unittest.main(verbosity=2)
