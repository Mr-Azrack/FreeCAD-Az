#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Owner video regression: reduce extra clicks without guessing ambiguous CAD."""
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ADDON = Path(__file__).resolve().parents[1]


class _Face:
    def __init__(self, area, holes):
        self.Area = area
        self.Wires = [object()] * (holes + 1)


class _Region:
    def __init__(self, area, holes=0):
        self.face = _Face(area, holes)


class FusionVideoContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ADDON))
        with patch.dict(sys.modules, {
            "FreeCAD": types.ModuleType("FreeCAD"),
            "Part": types.ModuleType("Part"),
        }):
            cls.profiles = importlib.import_module("azdesign.profiles")

    @classmethod
    def tearDownClass(cls):
        for key in ("azdesign.profiles",):
            sys.modules.pop(key, None)
        try:
            sys.path.remove(str(ADDON))
        except ValueError:
            pass

    def test_only_obvious_plate_with_cutouts_is_selected(self):
        recommended = self.profiles.preferred_plate_region
        self.assertIsNone(recommended([]))
        self.assertEqual(recommended([_Region(125, 0)]), 0)
        self.assertEqual(
            recommended([_Region(20), _Region(6240, 12), _Region(20)]), 1
        )
        self.assertIsNone(recommended([_Region(1000, 3), _Region(600)]))
        self.assertIsNone(recommended([_Region(1000), _Region(20)]))
        self.assertIsNone(recommended([_Region(250, 2), _Region(240, 1)]))

    def test_extrude_preselects_plate_but_preserves_manual_region_selection(self):
        source = (ADDON / "azdesign" / "tasks.py").read_text(encoding="utf-8")
        self.assertIn("profiles.preferred_plate_region(self.region_data)", source)
        self.assertIn("if index == recommended", source)
        self.assertIn("self.select_all", source)
        self.assertIn("begin_face_pick", source)

    def test_face_first_sketch_entry_is_not_obscured_by_large_picker(self):
        picker = (ADDON / "azdesign" / "sketch_plane_picker.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("self.listening = True", picker)
        self.assertIn("if has_model:", picker)
        self.assertIn("self.hide()", picker)
        self.assertIn("Click a flat model face", picker)
        self.assertIn("create_sketch(support=(obj, [face_name]))", picker)
        self.assertIn("if not self.listening", picker)

    def test_sketch_pattern_lets_source_circle_be_selected_on_canvas(self):
        source = (ADDON / "azdesign" / "sketch_pattern_ui.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("class _CircleSelectionObserver:", source)
        self.assertIn("Gui.Selection.addObserver(self.observer)", source)
        self.assertIn("Gui.Selection.removeObserver(self.observer)", source)
        self.assertIn("panel.choose_circle(index)", source)

    def test_fillet_chamfer_live_edge_picker_and_history_edit_stay_in_design(self):
        source = (ADDON / "azdesign" / "edge_treatments_canvas.py").read_text(
            encoding="utf-8"
        )
        commands = (ADDON / "azdesign" / "commands.py").read_text(
            encoding="utf-8"
        )
        history = (ADDON / "azdesign" / "feature_edit.py").read_text(
            encoding="utf-8"
        )
        session = (ADDON / "azdesign" / "session.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("class EdgeTreatmentPanel", source)
        self.assertIn("Gui.Selection.addObserver(self.observer)", source)
        self.assertIn("edge_treatments.preflight(", source)
        self.assertIn("edge_treatments.create(", source)
        self.assertIn('doc.openTransaction("Design: Edit " + self.kind)', source)
        self.assertIn("doc.abortTransaction()", source)
        self.assertIn('"azdesign.edge_treatments_canvas"', commands)
        self.assertIn('return show("Fillet", editing=obj)', history)
        self.assertIn('return show("Chamfer", editing=obj)', history)
        self.assertIn("cancel_edge_tool()", session)


if __name__ == "__main__":
    unittest.main(verbosity=2)
