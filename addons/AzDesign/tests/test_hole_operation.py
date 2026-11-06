# SPDX-License-Identifier: LGPL-2.1-or-later
"""Source-level and stubbed regressions for the reversible Hole operation."""

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ADDON = Path(__file__).resolve().parents[1]


class Shape:
    def __init__(self, volume):
        self.Volume = volume
        self.Solids = [object()] if volume > 0 else []

    def isNull(self):
        return not self.Solids

    def isValid(self):
        return bool(self.Solids)


class HoleOperationTest(unittest.TestCase):
    def setUp(self):
        self.old_path = list(sys.path)
        self.old_modules = {
            n: m for n, m in sys.modules.items() if n == "azdesign" or n.startswith("azdesign.")
        }
        for name in self.old_modules:
            del sys.modules[name]
        sys.path.insert(0, str(ADDON))
        app = types.ModuleType("FreeCAD")
        app.GuiUp = False
        app.Console = types.SimpleNamespace(PrintWarning=Mock())
        fake = types.ModuleType("azdesign.features")
        fake.DesignError = ValueError
        fake.owner_body = lambda obj: next((x for x in obj.InList if x.isDerivedFrom("PartDesign::Body")), None)
        fake.body_tip = Mock()
        fake.begin_transaction = Mock()
        self.mock_modules = patch.dict(sys.modules, {"FreeCAD": app, "azdesign.features": fake})
        self.mock_modules.start()
        self.module = importlib.import_module("azdesign.hole_operation")
        self.features = sys.modules["azdesign.features"]
        self.features.begin_transaction = Mock()
        self.doc = types.SimpleNamespace(Objects=[], openTransaction=Mock(),
                                         commitTransaction=Mock(), abortTransaction=Mock(),
                                         recompute=Mock())
        self.body = types.SimpleNamespace(Name="Body", Tip=None)
        self.base = types.SimpleNamespace(Name="Pad", Shape=Shape(100), ViewObject=None)
        self.sketch = types.SimpleNamespace(Name="Centers", Document=self.doc,
                                            InList=[self.body], ViewObject=None)
        self.sketch.isDerivedFrom = lambda cls: cls == "Sketcher::SketchObject"
        self.body.isDerivedFrom = lambda cls: cls == "PartDesign::Body"
        self.body.Tip = self.base
        self.features.body_tip = Mock(return_value=self.base)
        self.doc.Objects = [self.body, self.base, self.sketch]
        self.objects = {"Body": self.body, "Pad": self.base, "Centers": self.sketch}
        self.doc.getObject = lambda name: self.objects.get(name)

        def new_object(kind, name):
            self.assertEqual(kind, "PartDesign::Hole")
            obj = types.SimpleNamespace(Name=name, Shape=Shape(80), ViewObject=None)
            obj.isDerivedFrom = lambda cls: cls == kind
            obj.getEnumerationsOfProperty = lambda key: ["M3", "M4"]
            self.doc.Objects.append(obj)
            self.objects[name] = obj
            self.hole = obj
            return obj

        self.body.newObject = new_object

    def tearDown(self):
        self.mock_modules.stop()
        for name in list(sys.modules):
            if name == "azdesign" or name.startswith("azdesign."):
                del sys.modules[name]
        sys.modules.update(self.old_modules)
        sys.path[:] = self.old_path

    def test_preview_and_accept_keep_native_hole(self):
        op = self.module.HoleOperation(self.doc, self.sketch)
        self.assertEqual(op.preview(self.module.HoleSpec(diameter=4)), 80)
        self.assertEqual(self.body.Tip, self.hole)
        self.assertTrue(op.show_result())
        self.assertEqual(op.accept(), self.hole)
        self.doc.commitTransaction.assert_called_once()
        self.assertFalse(self.hole.ModelThread)

    def test_invalid_result_preserves_existing_tip_and_cancel_reverts(self):
        op = self.module.HoleOperation(self.doc, self.sketch)
        def invalid(kind, name):
            obj = types.SimpleNamespace(Name=name, Shape=Shape(100), ViewObject=None)
            obj.getEnumerationsOfProperty = lambda key: []
            obj.isDerivedFrom = lambda cls: cls == kind
            self.objects[name] = obj
            self.doc.Objects.append(obj)
            return obj
        self.body.newObject = invalid
        with self.assertRaisesRegex(ValueError, "did not remove material"):
            op.preview(self.module.HoleSpec())
        self.assertEqual(self.body.Tip, self.base)
        self.assertFalse(op.show_result())
        op.cancel()
        self.doc.abortTransaction.assert_called_once()
        self.assertEqual(self.body.Tip, self.base)

    def test_opt_in_modeled_preview_logs_before_risky_recompute(self):
        # The offline fake permits modeled geometry; live modeled Hole tests
        # stay out of CI because the native kernel may terminate the process.
        diagnostic = Mock()
        diagnostic.path = "/fake/model-thread-debug.jsonl"
        with patch("azdesign.hole_diagnostics.start_for_freecad",
                   return_value=diagnostic) as start:
            op = self.module.HoleOperation(self.doc, self.sketch)
            spec = self.module.HoleSpec(
                diameter=4, depth=8, thread_type="ISOMetricProfile",
                thread_size="M4", model_thread=True, experimental=True,
            )
            self.assertEqual(op.preview(spec), 80)
            self.assertTrue(op.hole.ModelThread)
            self.assertEqual(op.last_diagnostic, str(diagnostic.path))
            stages = [call.args[0] for call in diagnostic.record_spec.call_args_list]
            self.assertEqual(
                stages,
                ["before_transaction", "before_property_configuration",
                 "before_model_thread_enable", "before_native_recompute",
                 "after_native_recompute"],
            )
            start.assert_called_once()
            op.cancel()

    def test_bad_dimensions_create_no_feature_or_transaction(self):
        op = self.module.HoleOperation(self.doc, self.sketch)
        with self.assertRaisesRegex(ValueError, "diameter"):
            op.preview(self.module.HoleSpec(diameter=-1))
        self.assertFalse(op.started)
        self.features.begin_transaction.assert_not_called()
        op.cancel()
        self.doc.abortTransaction.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
