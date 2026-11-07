# SPDX-License-Identifier: LGPL-2.1-or-later
"""Regression for FreeCAD 1.1 PySide6 task OK/Cancel conversion."""

import ast
from enum import Flag, IntFlag
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "azdesign"


class Qt6StandardButton(Flag):
    Ok = 0x00000400
    Cancel = 0x00400000


class Qt5StandardButton(IntFlag):
    Ok = 0x00000400
    Cancel = 0x00400000


def load_qt():
    module = types.ModuleType("PySide")
    module.QtCore = types.SimpleNamespace()
    module.QtGui = types.SimpleNamespace(QAction=object)
    module.QtWidgets = types.SimpleNamespace(QAction=object)
    with patch.dict(sys.modules, {"PySide": module}):
        spec = importlib.util.spec_from_file_location(
            "az_test_qt_compat", ROOT / "qt.py"
        )
        qt = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qt)
        return qt


class QtStandardButtonTests(unittest.TestCase):
    def test_pyside6_enum_flag_is_not_int_convertible_but_helper_is(self):
        flags = Qt6StandardButton.Ok | Qt6StandardButton.Cancel
        with self.assertRaises(TypeError):
            int(flags)
        qt = load_qt()
        self.assertEqual(
            qt.standard_button_bits(Qt6StandardButton.Ok, Qt6StandardButton.Cancel),
            0x00400400,
        )

    def test_pyside2_intflag_and_empty_mask(self):
        qt = load_qt()
        self.assertEqual(
            qt.standard_button_bits(Qt5StandardButton.Ok, Qt5StandardButton.Cancel),
            0x00400400,
        )
        self.assertEqual(qt.standard_button_bits(), 0)

    def test_both_task_panels_use_shared_qt6_safe_converter(self):
        for filename in ("tasks.py", "hole.py"):
            with self.subTest(filename=filename):
                tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
                methods = [
                    node for cls in ast.walk(tree)
                    if isinstance(cls, ast.ClassDef)
                    for node in cls.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "getStandardButtons"
                ]
                self.assertTrue(methods)
                self.assertTrue(all(
                    isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "standard_button_bits"
                    for method in methods
                    for node in ast.walk(method)
                    if isinstance(node, ast.Return)
                ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
