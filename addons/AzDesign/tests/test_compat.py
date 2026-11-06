# SPDX-License-Identifier: LGPL-2.1-or-later
"""The modern contract forbids deprecated property access, including reads."""

import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location(
    "az_extrusion_compat", Path(__file__).resolve().parents[1] / "azdesign/compat.py"
)
compat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compat)


class ModernFeature:
    PropertiesList = ["SideType", "Type", "Type2"]

    def __init__(self):
        self.SideType = "One side"
        self.Type = "Length"
        self.Type2 = "Length"

    @property
    def Midplane(self):
        raise AssertionError("Deprecated Midplane must not be read")

    @Midplane.setter
    def Midplane(self, _value):
        raise AssertionError("Deprecated Midplane must not be written")


class ExtrusionCompatibilityTest(unittest.TestCase):
    def test_modern_modes_do_not_touch_midplane_or_two_lengths(self):
        feature = ModernFeature()
        for direction in ("Symmetric", "Two sides", "One side"):
            with self.subTest(direction=direction):
                compat.set_extrusion_sides(feature, direction)
                self.assertEqual(feature.SideType, direction)
                self.assertEqual(feature.Type, "Length")
                self.assertEqual(feature.Type2, "Length")
                self.assertEqual(compat.extrusion_side_type(feature), direction)

    def test_legacy_modes_and_mode_changes_use_legacy_properties(self):
        feature = SimpleNamespace(
            PropertiesList=["Midplane", "Type"], Midplane=False, Type="Length"
        )
        for direction, midplane, kind in (
            ("Symmetric", True, "Length"),
            ("Two sides", False, "TwoLengths"),
            ("One side", False, "Length"),
        ):
            with self.subTest(direction=direction):
                compat.set_extrusion_sides(feature, direction)
                self.assertEqual((feature.Midplane, feature.Type), (midplane, kind))
                self.assertEqual(compat.extrusion_side_type(feature), direction)

    def test_invalid_direction_is_rejected_before_mutation(self):
        feature = ModernFeature()
        with self.assertRaises(ValueError):
            compat.set_extrusion_sides(feature, "unsupported")
        self.assertEqual(feature.SideType, "One side")


if __name__ == "__main__":
    unittest.main(verbosity=2)
