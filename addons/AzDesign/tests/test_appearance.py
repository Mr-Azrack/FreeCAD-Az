# SPDX-License-Identifier: LGPL-2.1-or-later
"""Exercise preference restoration with Sketcher's cached-color fallback."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

APPEARANCE_SOURCE = Path(__file__).resolve().parents[1] / "azdesign" / "appearance.py"


class ParameterGroup:
    def __init__(self, original):
        self.values = dict(original)
        self.native_edge_color = self.values.get("EditedEdgeColor", (None, 0xFFFFFFFF))[1]

    def GetContents(self):
        return [(kind, name, value) for name, (kind, value) in self.values.items()] or None

    def GetBool(self, name, default=False):
        return self.values.get(name, (None, default))[1]

    def SetBool(self, name, value):
        kind = self.values.get(name, ("Boolean", None))[0]
        self.values[name] = (kind, value)

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
        grid = ParameterGroup({})
        app = types.ModuleType("FreeCAD")
        app.ParamGet = lambda path: grid if path.endswith("/AzDesign") else group
        package = types.ModuleType("azdesign")
        package.__path__ = []
        modeling = types.ModuleType("azdesign.modeling")
        modeling.current_document = lambda: None
        spec = importlib.util.spec_from_file_location("azdesign.appearance", APPEARANCE_SOURCE)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(
            sys.modules, {"FreeCAD": app, "azdesign": package, "azdesign.modeling": modeling}
        ):
            spec.loader.exec_module(module)
            appearance = module.Appearance()
            appearance.activate()
            self.assertNotEqual(group.native_edge_color, 0xFFFFFFFF)
            appearance.deactivate()
            self.assertTrue(appearance.grid_visible)
            appearance.toggle_grid(False)
            self.assertFalse(module.Appearance().grid_visible)
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

    def test_native_boolean_type_name_is_restored(self):
        self.run_lifecycle({"Simple": ("Boolean", False), "Gradient": ("Boolean", True)})

    def test_empty_native_parameter_group_is_supported(self):
        self.run_lifecycle({})


    def test_fit_hides_grid_until_camera_animation_and_skips_stale_timers(self):
        group = ParameterGroup({})
        app = types.ModuleType("FreeCAD")
        app.ParamGet = lambda path: group
        package = types.ModuleType("azdesign")
        package.__path__ = []
        modeling = types.ModuleType("azdesign.modeling")
        modeling.in_sketch = lambda: None
        qt = types.ModuleType("azdesign.qt")
        timers = []
        qt.QtCore = types.SimpleNamespace(
            QTimer=types.SimpleNamespace(singleShot=lambda delay, cb: timers.append((delay, cb)))
        )
        spec = importlib.util.spec_from_file_location("azdesign.appearance", APPEARANCE_SOURCE)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {
            "FreeCAD": app, "azdesign": package,
            "azdesign.modeling": modeling, "azdesign.qt": qt
        }):
            spec.loader.exec_module(module)
            appearance = module.Appearance()
            class Switch:
                def __init__(self):
                    self.value = -3
                def getValue(self):
                    return self.value
                def __eq__(self, other):
                    return self.value == other
            class Node:
                def __init__(self):
                    self._switch = Switch()
                @property
                def whichChild(self):
                    return self._switch
                @whichChild.setter
                def whichChild(self, value):
                    self._switch.value = value
            node = Node()
            appearance.grids = [(object(), object(), node)]
            appearance.fit(lambda: self.assertEqual(node.whichChild, -1))
            self.assertEqual(node.whichChild, -1)
            self.assertEqual(timers[0][0], 1200)
            appearance.fit(lambda: self.assertEqual(node.whichChild, -1))
            timers[0][1]()
            self.assertEqual(node.whichChild, -1)
            timers[1][1]()
            self.assertEqual(node.whichChild, -3)

if __name__ == "__main__":
    unittest.main(verbosity=2)
