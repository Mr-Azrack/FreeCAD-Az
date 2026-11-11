#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Fast, real-resource contracts for Design timeline image-only history."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON))
from azdesign.timeline_icons import icon_key, icon_path


class Feature:
    def __init__(self, kind, az_type=""):
        self.TypeId = kind
        self.AzType = az_type

    def isDerivedFrom(self, kind):
        return kind == self.TypeId


class Icons(unittest.TestCase):
    def test_all_common_history_features_have_distinct_original_images(self):
        expected = {
            "Sketcher::SketchObject": "sketch",
            "PartDesign::Pad": "extrude",
            "PartDesign::Pocket": "pocket",
            "PartDesign::Hole": "hole",
            "PartDesign::Fillet": "fillet",
            "PartDesign::Chamfer": "chamfer",
            "PartDesign::LinearPattern": "pattern",
            "PartDesign::PolarPattern": "pattern",
            "PartDesign::Mirrored": "mirror",
            "PartDesign::Body": "body",
            "PartDesign::Revolution": "revolve",
        }
        for kind, key in expected.items():
            with self.subTest(kind=kind):
                obj = Feature(kind)
                self.assertEqual(icon_key(obj), key)
                file = Path(icon_path(obj))
                self.assertTrue(file.is_file(), str(file))
                root = ET.parse(file).getroot()
                self.assertTrue(root.tag.endswith("svg"))
                self.assertEqual(root.attrib["viewBox"], "0 0 32 32")
                self.assertFalse(any(
                    node.tag.endswith("text") for node in root.iter()
                ), "Timeline icon must be vector graphics, never a font label")
        self.assertEqual(icon_key(Feature("PartDesign::FeaturePython", "AzExtrude")),
                         "extrude")

    def test_timeline_never_falls_back_to_text_abbreviations(self):
        source = (ADDON / "azdesign" / "ui.py").read_text(encoding="utf-8")
        part = source.split("class FeatureButton", 1)[1].split("class History", 1)[0]
        self.assertIn("QtGui.QIcon(icon_path(obj))", part)
        self.assertIn("icon.pixmap(25, 25).isNull()", part)
        self.assertIn("icon = design_icon(icon_key(obj))", part)
        self.assertIn("self.setText(\"\")", part)
        self.assertIn("QtCore.Qt.ToolButtonIconOnly", part)
        self.assertNotIn("self.setText(obj.Label)", part)
        history = source.split("class History", 1)[1]
        self.assertNotIn("QtCore.Qt.ToolButtonTextBesideIcon", history)
        self.assertNotIn('button.setText(obj.Label', history)


if __name__ == "__main__":
    unittest.main(verbosity=2)
