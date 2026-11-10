# SPDX-License-Identifier: LGPL-2.1-or-later
"""Regressions for the first command with no visible FreeCAD document.

The App stub intentionally leaves a newly created hidden temporary document
active, matching the native lifecycle that exposed the Create Sketch failure.
"""

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ADDON = Path(__file__).resolve().parents[1]


class DocumentContextTest(unittest.TestCase):
    def setUp(self):
        self.old_path = list(sys.path)
        self.old_modules = {
            n: m for n, m in sys.modules.items() if n == "azdesign" or n.startswith("azdesign.")
        }
        for name in self.old_modules:
            del sys.modules[name]
        sys.path.insert(0, str(ADDON))
        self.app = types.ModuleType("FreeCAD")
        self.app.ActiveDocument = None
        self.native_active = None
        self.app.activeDocument = lambda: self.native_active
        self.app.GuiUp = True
        self.docs, self.gui_docs = {}, {}
        self.gui_current = None
        self.gui = types.ModuleType("FreeCADGui")
        self.gui.activeDocument = lambda: self.gui_current
        self.gui.getMainWindow = Mock(return_value=object())
        self.gui.Selection = types.SimpleNamespace(
            getSelection=Mock(return_value=[]),
            getSelectionEx=Mock(return_value=[]),
            clearSelection=Mock(),
            addSelection=Mock(),
        )
        self.gui.Control = types.SimpleNamespace(activeDialog=Mock(return_value=False))
        self.gui.addCommand = Mock()
        self.app.listDocuments = lambda: dict(self.docs)
        self.app.getActiveTransaction = Mock(return_value=None)
        self.app.newDocument = Mock(side_effect=self.new_document)
        self.app.setActiveDocument = Mock(side_effect=self.activate)
        self.widgets = types.SimpleNamespace(
            QInputDialog=types.SimpleNamespace(getItem=Mock(return_value=("XY — Top", False)))
        )
        qt = types.ModuleType("azdesign.qt")
        qt.QtWidgets, qt.QtCore = self.widgets, types.SimpleNamespace()
        self.modules = patch.dict(
            sys.modules,
            {
                "FreeCAD": self.app,
                "FreeCADGui": self.gui,
                "Part": types.ModuleType("Part"),
                "azdesign.qt": qt,
                "azdesign.profiles": types.ModuleType("azdesign.profiles"),
                "azdesign.references": types.ModuleType("azdesign.references"),
            },
        )
        self.modules.start()
        self.modeling = importlib.import_module("azdesign.modeling")
        self.features = importlib.import_module("azdesign.features")

    def tearDown(self):
        self.modules.stop()
        for name in list(sys.modules):
            if name == "azdesign" or name.startswith("azdesign."):
                del sys.modules[name]
        sys.modules.update(self.old_modules)
        sys.path[:] = self.old_path

    def activate(self, name):
        self.native_active = self.docs.get(name)
        # Native setActiveDocument("") clears the C++ pointer but may leave the
        # Python module attribute stale. Model that split instead of hiding it.
        if not name:
            return
        self.app.ActiveDocument = self.native_active
        self.gui_current = self.gui_docs.get(name)

    def new_document(self, name, hidden=False, temp=False):
        name = name if name not in self.docs else name + str(len(self.docs))
        doc = types.SimpleNamespace(
            Name=name,
            Objects=[],
            UndoMode=1,
            openTransaction=Mock(),
            commitTransaction=Mock(),
            abortTransaction=Mock(),
            recompute=Mock(),
        )

        def add_object(kind, object_name):
            obj = types.SimpleNamespace(Name=object_name, Document=doc, InList=[])
            obj.isDerivedFrom = lambda value: kind == value
            doc.Objects.append(obj)
            return obj

        doc.addObject = Mock(side_effect=add_object)
        self.docs[name] = doc
        if not hidden:
            view = types.SimpleNamespace(
                getActiveObject=Mock(return_value=None), setActiveObject=Mock()
            )
            self.gui_docs[name] = types.SimpleNamespace(
                Document=doc, activeView=Mock(return_value=view)
            )
        # This is deliberate: a hidden/temp document can be App-active with no
        # Gui document when no previous document existed.
        self.activate(name)
        return doc

    def test_create_sketch_with_only_hidden_calculator_opens_visible_design(self):
        hidden = self.app.newDocument("AzGeometry", hidden=True, temp=True)
        # New Design behavior is nonmodal: opening the canvas plane picker
        # must NOT invoke the old Qt InputDialog or mutate the hidden document.
        picker = types.ModuleType("azdesign.sketch_plane_picker")
        picker.show = Mock(return_value=None)
        with patch.dict(sys.modules, {"azdesign.sketch_plane_picker": picker}):
            self.assertIsNone(self.modeling.create_sketch())
        self.assertNotEqual(self.app.ActiveDocument, hidden)
        self.assertIsNotNone(self.gui.activeDocument())
        picker.show.assert_called_once_with()
        self.widgets.QInputDialog.getItem.assert_not_called()
        self.assertEqual(hidden.Objects, [])

    def test_active_body_without_a_gui_document_returns_none(self):
        self.app.newDocument("AzGeometry", hidden=True, temp=True)
        self.assertIsNone(self.modeling.active_body())

    def test_document_uses_visible_gui_context_instead_of_hidden_app_context(self):
        visible = self.app.newDocument("Part")
        visible_gui = self.gui_current
        self.app.newDocument("AzGeometry", hidden=True, temp=True)
        self.gui_current = visible_gui
        self.assertIs(self.modeling.document(), visible)
        self.assertIs(self.app.ActiveDocument, visible)

    def test_existing_design_is_reused(self):
        visible = self.app.newDocument("Part")
        self.app.newDocument.reset_mock()
        self.assertIs(self.modeling.document(), visible)
        self.app.newDocument.assert_not_called()

    def test_create_body_never_populates_the_hidden_calculator(self):
        hidden = self.app.newDocument("AzGeometry", hidden=True, temp=True)
        body = self.modeling.new_body()
        self.assertIsNot(body.Document, hidden)
        self.assertEqual(hidden.Objects, [])
        self.gui_current.activeView().setActiveObject.assert_called_once_with("pdbody", body)

    def test_open_task_blocks_creation_before_opening_another_document(self):
        self.gui.Control.activeDialog.return_value = True
        with self.assertRaises(self.modeling.ModelingError):
            self.modeling.create_sketch()
        self.app.newDocument.assert_not_called()

    def test_calculator_creation_preserves_no_active_document(self):
        calculator = self.features.ensure_calculator()
        self.assertEqual(calculator.UndoMode, 0)
        self.assertIsNone(self.app.activeDocument())
        self.assertIs(self.app.ActiveDocument, calculator)
        self.assertIsNone(self.gui_current)

    def test_calculator_creation_preserves_the_visible_design(self):
        visible = self.app.newDocument("Part")
        gui_doc = self.gui_current
        self.features.ensure_calculator()
        self.assertIs(self.app.ActiveDocument, visible)
        self.assertIs(self.gui_current, gui_doc)

    def test_calculator_creation_error_restores_the_design(self):
        visible = self.app.newDocument("Part")

        def fail(*args, **kwargs):
            self.new_document("BrokenCalculator", hidden=True, temp=True)
            raise RuntimeError("simulated calculator creation failure")

        self.app.newDocument.side_effect = fail
        with self.assertRaisesRegex(RuntimeError, "simulated"):
            self.features.ensure_calculator()
        self.assertIs(self.app.ActiveDocument, visible)

    def test_command_registration_preserves_an_empty_modeling_context(self):
        commands = importlib.import_module("azdesign.commands")
        commands.register()
        self.assertIsNone(self.app.activeDocument())
        self.assertIsNone(self.gui_current)
        self.assertEqual(self.gui_docs, {})

    def test_closed_calculator_cache_is_recreated(self):
        class ClosedDocument:
            @property
            def Name(self):
                raise RuntimeError("Document object no longer exists")

        self.features._calculator = ClosedDocument()
        self.assertIsNotNone(self.features.ensure_calculator())
        self.assertIsNone(self.app.activeDocument())

    def test_gui_document_without_a_view_is_not_a_modeling_context(self):
        doc = self.app.newDocument("NoView")
        self.gui_current.activeView.return_value = None
        self.assertIsNone(self.modeling.active_body())
        self.assertIsNot(self.modeling.document(), doc)

    def test_active_body_ignores_selection_from_another_document(self):
        other = self.app.newDocument("Other")
        foreign_body = other.addObject("PartDesign::Body", "Body")
        self.app.newDocument("Current")
        self.gui.Selection.getSelection.return_value = [foreign_body]
        self.assertIsNone(self.modeling.active_body())


if __name__ == "__main__":
    unittest.main(verbosity=2)
