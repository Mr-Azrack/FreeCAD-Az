#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Headless tests for Design/Home and reopened-file workspace policy."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / "azdesign" / "workspace_route.py"


class Document:
    def __init__(self, name="Design", filename=""):
        self.Name = name
        self.FileName = filename


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.doc = Document()
        self.current = "StartWorkbench"
        self.app = types.ModuleType("FreeCAD")
        self.app.getDocument = Mock(return_value=self.doc)
        self.app.addDocumentObserver = Mock()
        self.gui = types.ModuleType("FreeCADGui")
        self.gui.activeDocument = lambda: types.SimpleNamespace(
            Document=self.doc, getInEdit=lambda: None
        )
        self.gui.activeWorkbench = lambda: types.SimpleNamespace(
            name=lambda: self.current
        )
        self.gui.activateWorkbench = Mock()
        self.gui.Control = types.SimpleNamespace(activeDialog=lambda: False)
        qt = types.ModuleType("azdesign.qt")
        qt.QtCore = types.SimpleNamespace(QTimer=types.SimpleNamespace(
            singleShot=lambda ms, cb: cb()
        ))
        self.packages = {
            "FreeCAD": self.app, "FreeCADGui": self.gui,
            "azdesign": types.ModuleType("azdesign"), "azdesign.qt": qt,
        }
        self.patch = patch.dict(sys.modules, self.packages)
        self.patch.start()
        spec = importlib.util.spec_from_file_location(
            "azdesign.workspace_route", SOURCE
        )
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.module
        spec.loader.exec_module(self.module)

    def tearDown(self):
        sys.modules.pop("azdesign.workspace_route", None)
        self.patch.stop()

    def test_new_design_from_home(self):
        self.module.route_new_document("Design")
        self.gui.activateWorkbench.assert_called_once_with("AzDesignWorkbench")

    def test_reopen_has_saved_context(self):
        self.doc.FileName = "shop-part.FCStd"
        self.module.route_new_document("Design")
        self.gui.activateWorkbench.assert_not_called()

    def test_cam_and_specialized_views_are_preserved(self):
        for name in ("CAMWorkbench", "MeshWorkbench", "TechDrawWorkbench"):
            self.current = name
            self.module.route_new_document("Design")
        self.gui.activateWorkbench.assert_not_called()

    def test_no_switch_while_another_document_is_active(self):
        self.gui.activeDocument = lambda: types.SimpleNamespace(
            Document=Document("Other"), getInEdit=lambda: None
        )
        self.module.route_new_document("Design")
        self.gui.activateWorkbench.assert_not_called()

    def test_no_switch_with_active_task(self):
        self.gui.Control.activeDialog = lambda: True
        self.module.route_new_document("Design")
        self.gui.activateWorkbench.assert_not_called()

    def test_router_installs_once_and_routes_new_document(self):
        observer = self.module.install()
        self.assertIs(observer, self.module.install())
        self.app.addDocumentObserver.assert_called_once_with(observer)
        observer.slotCreatedDocument(self.doc)
        self.gui.activateWorkbench.assert_called_once_with("AzDesignWorkbench")


if __name__ == "__main__":
    unittest.main(verbosity=2)
