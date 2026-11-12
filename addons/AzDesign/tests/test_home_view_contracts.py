# SPDX-License-Identifier: LGPL-2.1-or-later
"""Verify Home frames the working Body instead of the full document scene."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "azdesign" / "commands.py"


class HomeViewContracts(unittest.TestCase):
    def test_home_uses_active_solid_with_selection_fit_and_restores_selection(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        home = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "home")
        code = ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), home)
        self.assertIn("modeling.active_body()", code)
        self.assertIn("Gui.SendMsgToActiveView(\"ViewSelection\")", code)
        self.assertIn("Gui.Selection.getSelectionEx()", code)
        self.assertIn("finally:", code)
        self.assertIn("Gui.Selection.clearSelection()", code)
        self.assertIn("invoke(\"Std_ViewFitAll\")", code)
        self.assertIn("session.appearance.fit(fit_body)", code)
        self.assertIn("body = max(bodies,", code)


if __name__ == "__main__":
    unittest.main()
