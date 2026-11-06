# SPDX-License-Identifier: LGPL-2.1-or-later
"""Exercise preference restoration with Sketcher's cached-color fallback."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class ParameterGroup:
    def __init__(self, original):
        self.values = dict(original)
        self.native_edge_color = self.values.get("EditedEdgeColor", (None, 0xFFFFFFFF))[1]

    def GetContents(self):
        return [(kind, name, value) for name, (kind, value) in self.values.items()]

    def SetBool(self, name, value):
        self.values[name] = ("Bool", value)

    def RemBool(self, name):
        self.values.pop(name, None)

    def observe(self, name):
        if name == "EditedEdgeColor":
            # Mirrors EditModeCoinManager::ParameterObserver::updateColor:
            # GetUnsigned(parametername, current_SbColor.getPackedValue()).
            self.native_edge_color = self.values.get(name, (None, self.native_edge_color))[1]

    def SetUnsigned(self, name, value):
        self.values[name] = ("Unsigned Long", value)
        self.observe(name)

    def RemUnsigned(self, name):
        self.values.pop(name, None)
        self.observe(name)


class AppearanceTest(unittest.TestCase):
    def run_lifecycle(self, original):
        group = ParameterGroup(original)
        app = types.ModuleType("FreeCAD")
        app.ParamGet = lambda _path: group
        package = types.ModuleType("azdesign")
        package.__path__ = []
        modeling = types.ModuleType("azdesign.modeling")
        path = Path(__file__).resolve().parents[1] / "azdesign" / "appearance.py"
        spec = importlib.util.spec_from_file_location("azdesign.appearance", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(
            sys.modules, {"FreeCAD": app, "azdesign": package, "azdesign.modeling": modeling}
        ):
            spec.loader.exec_module(module)
            appearance = module.Appearance()
            appearance.activate()
            self.assertNotEqual(group.native_edge_color, 0xFFFFFFFF)
            appearance.deactivate()
        self.assertEqual(group.values, original)
        return group

    def test_absent_color_restores_the_native_cache_and_removes_temporary_keys(self):
        group = self.run_lifecycle({"Unrelated": ("Bool", True)})
        self.assertEqual(group.native_edge_color, 0xFFFFFFFF)

    def test_custom_existing_colors_and_background_are_restored(self):
        group = self.run_lifecycle(
            {
                "EditedEdgeColor": ("Unsigned Long", 0x123456FF),
                "BackgroundColor": ("Unsigned Long", 0x203040FF),
                "Simple": ("Bool", False),
            }
        )
        self.assertEqual(group.native_edge_color, 0x123456FF)


if __name__ == "__main__":
    unittest.main(verbosity=2)
