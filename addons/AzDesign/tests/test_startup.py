# SPDX-License-Identifier: LGPL-2.1-or-later
"""Reproduce FreeCAD's exec-based startup without a script __file__ variable.

Run with ordinary Python; native FreeCAD supplies the add-on directory on
sys.path before executing these scripts. The GUI stub only records registration
and lifecycle calls, so this test also runs on the packaging CI job.
"""

import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ADDON = Path(__file__).resolve().parents[1]


class StartupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="Az startup Ω ")
        self.root = Path(self.temp.name) / "AppData/Roaming/FreeCAD/v1-1/Mod/AzDesign"
        shutil.copytree(ADDON, self.root, ignore=shutil.ignore_patterns("__pycache__", "tests"))
        self.old_path = list(sys.path)
        self.old_modules = {
            name: module
            for name, module in sys.modules.items()
            if name == "azdesign" or name.startswith("azdesign.")
        }
        for name in self.old_modules:
            del sys.modules[name]
        sys.path.insert(0, str(self.root))
        self.registered = []
        self.gui = types.ModuleType("FreeCADGui")

        class Workbench:
            def appendMenu(instance, name, commands):
                instance.menu = (name, commands)

        self.gui.Workbench = Workbench
        self.gui.addWorkbench = self.registered.append
        self.modules = patch.dict(sys.modules, {"FreeCADGui": self.gui})
        self.modules.start()

    def tearDown(self):
        self.modules.stop()
        for name in list(sys.modules):
            if name == "azdesign" or name.startswith("azdesign."):
                del sys.modules[name]
        sys.modules.update(self.old_modules)
        sys.path[:] = self.old_path
        self.temp.cleanup()

    def execute(self, name, namespace=None, local_namespace=None):
        namespace = {"__name__": "FreeCADStartup"} if namespace is None else namespace
        path = self.root / name
        exec(
            compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace, local_namespace
        )
        return namespace

    def assert_workbench(self):
        self.assertEqual(len(self.registered), 1)
        workbench = self.registered[0]
        self.assertEqual(workbench.MenuText, "Design")
        self.assertEqual(Path(workbench.Icon).resolve(), (self.root / "Resources/az.svg").resolve())
        self.assertTrue(Path(workbench.Icon).is_file())
        self.assertEqual(workbench.GetClassName(), "Gui::PythonWorkbench")
        return workbench

    def test_headless_entry_without_file_imports_only_the_package(self):
        namespace = self.execute("Init.py")
        self.assertNotIn("__file__", namespace)
        self.assertIn("azdesign", sys.modules)
        self.assertNotIn("azdesign.workbench", sys.modules)

    def test_gui_entry_without_file_registers_the_workbench(self):
        namespace = self.execute("InitGui.py")
        self.assertNotIn("__file__", namespace)
        self.assert_workbench()

    def test_unrelated_loader_file_does_not_change_resource_paths(self):
        self.execute(
            "InitGui.py", {"__name__": "FreeCADStartup", "__file__": "OtherAddon/InitGui.py"}
        )
        self.assert_workbench()

    def test_separate_loader_globals_and_locals_are_supported(self):
        self.execute("Init.py", {"__name__": "FreeCADStartup"}, {})
        self.execute("InitGui.py", {"__name__": "FreeCADStartup"}, {})
        self.assert_workbench()

    def test_native_home_callback_survives_discarded_initgui_namespace(self):
        """Reproduce the actual 0.5.6 Windows first-launch NameError.

        FreeCAD's exec loader doesn't retain InitGui.py's globals. QTimer
        calls the function later; it must retain its FreeCAD/Gui references.
        """
        import os
        callbacks = []
        qt = types.ModuleType("azdesign.qt")
        qt.QtCore = types.SimpleNamespace(
            QTimer=types.SimpleNamespace(
                singleShot=lambda delay, callback: callbacks.append((delay, callback))
            )
        )
        app = types.ModuleType("FreeCAD")
        app.ActiveDocument = None
        app.addDocumentObserver = Mock()
        app.Console = types.SimpleNamespace(PrintError=Mock())
        self.gui.Control = types.SimpleNamespace(activeDialog=Mock(return_value=False))
        self.gui.activeWorkbench = Mock(
            return_value=types.SimpleNamespace(name=lambda: "PartDesignWorkbench")
        )
        self.gui.activateWorkbench = Mock()
        with patch.dict(os.environ, {"AZ_DESIGN_NATIVE_HOME": "1"}), patch.dict(
            sys.modules, {"azdesign.qt": qt, "FreeCAD": app}
        ):
            ephemeral_globals = {"__name__": "FreeCADStartup"}
            ephemeral_locals = {}
            self.execute("InitGui.py", ephemeral_globals, ephemeral_locals)
            self.assertEqual(len(callbacks), 1)
            self.assertEqual(callbacks[0][0], 1200)
            # The real FreeCAD loader may discard either/both dictionaries.
            ephemeral_globals.clear()
            ephemeral_locals.clear()
            callbacks[0][1]()
            self.gui.activateWorkbench.assert_called_once_with("AzDesignWorkbench")
            app.Console.PrintError.assert_not_called()

    def test_native_home_keeps_existing_document_workspace(self):
        import os
        callbacks = []
        qt = types.ModuleType("azdesign.qt")
        qt.QtCore = types.SimpleNamespace(
            QTimer=types.SimpleNamespace(
                singleShot=lambda delay, callback: callbacks.append(callback)
            )
        )
        app = types.ModuleType("FreeCAD")
        app.ActiveDocument = object()
        app.addDocumentObserver = Mock()
        app.Console = types.SimpleNamespace(PrintError=Mock())
        self.gui.Control = types.SimpleNamespace(activeDialog=Mock(return_value=False))
        self.gui.activeWorkbench = Mock(
            return_value=types.SimpleNamespace(name=lambda: "PartDesignWorkbench")
        )
        self.gui.activateWorkbench = Mock()
        with patch.dict(os.environ, {"AZ_DESIGN_NATIVE_HOME": "1"}), patch.dict(
            sys.modules, {"azdesign.qt": qt, "FreeCAD": app}
        ):
            self.execute("InitGui.py")
            self.assertEqual(len(callbacks), 1)
            callbacks[0]()
            self.gui.activateWorkbench.assert_not_called()

    def test_hooks_keep_module_scope_after_loader_namespace_is_gone(self):
        namespace = self.execute("InitGui.py")
        workbench = self.assert_workbench()
        namespace.clear()
        commands = types.ModuleType("azdesign.commands")
        commands.register = Mock()
        commands.menu_commands = Mock(return_value=["Az_Sketch", "Az_Extrude"])
        session = types.ModuleType("azdesign.session")
        session.start = Mock()
        session.stop = Mock()
        replacements = {
            name: types.ModuleType(name) for name in ("PartGui", "PartDesignGui", "SketcherGui")
        }
        replacements.update({"azdesign.commands": commands, "azdesign.session": session})
        with patch.dict(sys.modules, replacements):
            workbench.Initialize()
            workbench.Activated()
            workbench.Deactivated()
        commands.register.assert_called_once_with()
        session.start.assert_called_once_with()
        session.stop.assert_called_once_with()
        self.assertEqual(workbench.menu, ("Design", ["Az_Sketch", "Az_Extrude"]))
        self.assertEqual(type(workbench).__module__, "azdesign.workbench")


if __name__ == "__main__":
    unittest.main(verbosity=2)
