# SPDX-License-Identifier: LGPL-2.1-or-later
"""Offline contracts: native holes never enable unsafe modeled threads."""

import importlib.util
from pathlib import Path
import unittest

location = Path(__file__).resolve().parents[1] / "azdesign/hole_spec.py"
spec = importlib.util.spec_from_file_location("az_hole_spec", location)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)
HoleSpec = module.HoleSpec


class NativeHole:
    def __init__(self):
        self.ModelThread = False
        self.Threaded = False
        self.CosmeticThread = False
        self._thread_type = "None"
        self.ThreadSize = ""
        self.Diameter = 6
        self.Depth = 25
        self.DepthType = "Dimension"
        self.writes = []

    def __setattr__(self, name, value):
        if name == "ModelThread" and value:
            raise AssertionError("Unsafe geometric thread was enabled")
        if name not in ("writes",) and hasattr(self, "writes"):
            self.writes.append((name, value))
        object.__setattr__(self, name, value)

    @property
    def ThreadType(self):
        return self._thread_type

    @ThreadType.setter
    def ThreadType(self, value):
        self._thread_type = value

    def getEnumerationsOfProperty(self, name):
        assert name == "ThreadSize"
        return {
            "ISOMetricProfile": ["M3", "M4", "M5"],
            "UNC": ["#4", "#6", "1/4"],
        }.get(self.ThreadType, [])


class HoleSpecTest(unittest.TestCase):
    def test_plain_through_hole(self):
        hole = NativeHole()
        HoleSpec(diameter=4.5, depth=15, through_all=True).apply(hole)
        self.assertEqual((hole.Diameter, hole.DepthType), (4.5, "ThroughAll"))
        self.assertFalse(hole.Threaded)
        self.assertFalse(hole.ModelThread)

    def test_cosmetic_thread_uses_native_standard_and_size(self):
        hole = NativeHole()
        HoleSpec(diameter=4, depth=8, thread_type="ISOMetricProfile",
                 thread_size="M4").apply(hole)
        self.assertEqual(hole.ThreadType, "ISOMetricProfile")
        self.assertEqual(hole.ThreadSize, "M4")
        self.assertTrue(hole.Threaded)
        self.assertTrue(hole.CosmeticThread)
        self.assertFalse(hole.ModelThread)
        self.assertEqual(module.thread_sizes(hole, "UNC"), ["#4", "#6", "1/4"])
        self.assertFalse(hole.ModelThread)

    def test_bad_specs_fail_before_mutating_native_feature(self):
        for settings in (
            HoleSpec(diameter=0),
            HoleSpec(depth=float("nan")),
            HoleSpec(diameter=float("inf")),
            HoleSpec(thread_type="invalid"),
            HoleSpec(thread_size="M4"),
            HoleSpec(model_thread=True),
        ):
            with self.subTest(settings=settings):
                hole = NativeHole()
                hole.writes.clear()
                with self.assertRaises(ValueError):
                    settings.apply(hole)
                self.assertEqual(hole.writes, [])

    def test_invalid_size_rejected_without_turning_on_threads(self):
        hole = NativeHole()
        with self.assertRaisesRegex(ValueError, "not available"):
            HoleSpec(thread_type="ISOMetricProfile", thread_size="M99").apply(hole)
        self.assertFalse(hole.ModelThread)
        self.assertFalse(hole.Threaded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
