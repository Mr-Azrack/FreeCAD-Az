#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Fast headless regression: Pattern is Design-owned and previews are reversible."""
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ADDON = Path(__file__).resolve().parents[1]


class FakeShape:
    Solids = [object()]
    def isNull(self): return False
    def isValid(self): return True


class FakeDocument:
    def __init__(self):
        self.actions = []
        self.objects = {}
    def openTransaction(self, name): self.actions.append(("begin", name))
    def commitTransaction(self): self.actions.append(("commit",))
    def abortTransaction(self): self.actions.append(("abort",))
    def recompute(self): self.actions.append(("recompute",))
    def getObject(self, name): return self.objects.get(name)


class FakeFeature:
    TypeId = "PartDesign::Hole"
    PropertiesList = ()
    def __init__(self, name="Hole"):
        self.Name = name
        self.Shape = FakeShape()
        self.ViewObject = types.SimpleNamespace(Visibility=True)
        self.State = ()
    def isDerivedFrom(self, name): return name == "PartDesign::Feature"


class FakePattern(FakeFeature):
    TypeId = "PartDesign::LinearPattern"
    PropertiesList = ("TransformMode", "Originals", "Direction", "Direction2",
                      "Mode", "Mode2", "Offset", "Length", "Length2",
                      "Occurrences", "Occurrences2", "Reversed")
    def __init__(self):
        super().__init__("DesignLinearPattern")


class FakeBody:
    def __init__(self, doc, feature):
        self.Document = doc
        self.Tip = feature
        self.Group = [feature]
        self.Origin = types.SimpleNamespace(OriginFeatures=[
            types.SimpleNamespace(Role=role)
            for role in ("X_Axis", "Y_Axis", "Z_Axis")
        ])
        self.new = None
    def newObject(self, kind, name):
        assert kind == "PartDesign::LinearPattern"
        obj = FakePattern()
        self.Document.objects[obj.Name] = obj
        self.new = obj
        return obj


class PatternContracts(unittest.TestCase):
    def setUp(self):
        self.old_path = list(sys.path)
        sys.path.insert(0, str(ADDON))
        self.old_modules = {
            k: v for k, v in sys.modules.items()
            if k == "azdesign" or k.startswith("azdesign.")
        }
        for key in self.old_modules: del sys.modules[key]
        self.features = types.ModuleType("azdesign.features")
        self.features.DesignError = type("DesignError", (ValueError,), {})
        self.features.owner_body = lambda obj: self.body
        self.patch = patch.dict(sys.modules, {"azdesign.features": self.features})
        self.patch.start()
        self.engine = importlib.import_module("azdesign.solid_pattern_engine")
        self.doc = FakeDocument()
        self.feature = FakeFeature()
        self.doc.objects[self.feature.Name] = self.feature
        self.body = FakeBody(self.doc, self.feature)

    def tearDown(self):
        self.patch.stop()
        for key in list(sys.modules):
            if key == "azdesign" or key.startswith("azdesign."):
                del sys.modules[key]
        sys.modules.update(self.old_modules)
        sys.path[:] = self.old_path

    def test_preview_stays_in_open_transaction_until_apply(self):
        draft = self.engine.PatternDraft(self.feature)
        obj = draft.preview(4, 13.5, "Y_Axis")
        self.assertEqual(obj.TypeId, "PartDesign::LinearPattern")
        self.assertEqual(obj.Originals, [self.feature])
        self.assertEqual(obj.Direction[0].Role, "Y_Axis")
        self.assertEqual(obj.Occurrences, 4)
        self.assertEqual(obj.Length, 40.5)
        self.assertFalse(self.feature.ViewObject.Visibility)
        self.assertEqual(self.body.Tip, obj)
        self.assertFalse(any(a[0] == "commit" for a in self.doc.actions))
        draft.accept()
        self.assertEqual(self.doc.actions[-1], ("commit",))

    def test_two_axis_grid_is_owned_and_committed_once(self):
        draft = self.engine.PatternDraft(self.feature)
        pattern = draft.preview(2, 12, "X_Axis", count2=2,
                                spacing2=18, direction2="Y_Axis")
        self.assertEqual(pattern.Occurrences2, 2)
        self.assertEqual(pattern.Direction2[0].Role, "Y_Axis")
        self.assertEqual(pattern.Length2, 18)
        draft.accept()
        self.assertEqual(len([a for a in self.doc.actions if a[0] == "commit"]), 1)

    def test_cancel_aborts_and_restores_original_visibility(self):
        draft = self.engine.PatternDraft(self.feature)
        draft.preview(3, 12, "X_Axis")
        draft.cancel()
        self.assertEqual(self.body.Tip, self.feature)
        self.assertTrue(self.feature.ViewObject.Visibility)
        self.assertTrue(any(a[0] == "abort" for a in self.doc.actions))
        self.assertFalse(any(a[0] == "commit" for a in self.doc.actions))

    def test_bad_parameters_never_start_transaction(self):
        draft = self.engine.PatternDraft(self.feature)
        with self.assertRaisesRegex(ValueError, "between"):
            draft.preview(1, 5, "X_Axis")
        with self.assertRaisesRegex(ValueError, "Spacing"):
            draft.preview(3, 0, "X_Axis")
        self.assertFalse(self.doc.actions)

    def test_sketch_circle_selection_uses_shared_geometry_resolver(self):
        source = (ADDON / "azdesign" / "sketch_pattern.py").read_text()
        panel = (ADDON / "azdesign" / "sketch_pattern_ui.py").read_text()
        self.assertIn("def circle_for_edge(", source)
        self.assertIn("len(matches) == 1", source)
        self.assertIn("circle_for_edge(sketch, name)", source)
        self.assertIn("sketch_pattern.circle_for_edge(", panel)
        self.assertNotIn("index = int(suffix) - 1", panel)

    def test_preview_refuses_to_delete_unrelated_sketch_geometry(self):
        ui = (ADDON / "azdesign" / "sketch_pattern_ui.py").read_text()
        self.assertIn("expected = self.original_geometry_count + len(self.created)", ui)
        self.assertIn("if self.sketch.GeometryCount != expected:", ui)
        self.assertIn("the preview will not delete unrelated geometry", ui)
        self.assertLess(
            ui.index("if self.sketch.GeometryCount != expected:"),
            ui.index("self.sketch.delGeometry(index)"),
        )

    def test_failed_sketch_preview_aborts_owned_transaction(self):
        ui = (ADDON / "azdesign" / "sketch_pattern_ui.py").read_text()
        start = ui.index("    def preview(self, source, columns, rows, pitch_x, pitch_y):")
        end = ui.index("    def accept(self):", start)
        preview = ui[start:end]
        self.assertIn("except Exception:", preview)
        self.assertIn("self.doc.abortTransaction()", preview)
        self.assertIn("self.started = False", preview)
        self.assertIn("self.valid = False", preview)
        self.assertIn("self.created = ()", preview)
        self.assertLess(preview.index("self.doc.abortTransaction()"),
                        preview.index("self.started = False"))

    def test_edit_routes_and_esc_are_not_native(self):
        commands = (ADDON / "azdesign" / "commands.py").read_text()
        edit = (ADDON / "azdesign" / "feature_edit.py").read_text()
        session = (ADDON / "azdesign" / "session.py").read_text()
        solid = (ADDON / "azdesign" / "solid_pattern.py").read_text()
        sketch = (ADDON / "azdesign" / "sketch_pattern_ui.py").read_text()
        self.assertIn('"azdesign.solid_pattern"', commands)
        self.assertIn('"azdesign.sketch_pattern_ui"', commands)
        self.assertIn('obj.isDerivedFrom("PartDesign::LinearPattern")', edit)
        self.assertIn('return show(editing=obj)', edit)
        self.assertIn('cancel_solid_pattern()', session)
        self.assertIn('cancel_sketch_pattern()', session)
        self.assertIn("PatternDraft(source, self.editing)", solid)
        self.assertIn("SketchPatternDraft(sketch)", sketch)


if __name__ == "__main__":
    unittest.main(verbosity=2)
