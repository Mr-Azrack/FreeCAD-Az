#!/usr/bin/env python3
"""Source contract for passive model-edge cues in the live hover filter."""
import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "azdesign" / "snap_overlay.py"

class HoverBodyContract(unittest.TestCase):
    def test_hover_has_nonmutating_model_edge_fallback(self):
        source = SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "HoverGuides")
        move = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "move")
        calls = [n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
                 for n in ast.walk(move) if isinstance(n, ast.Call)
                 and isinstance(n.func, (ast.Name, ast.Attribute))]
        self.assertIn("best_snap", calls)
        self.assertIn("getPreselection", calls)
        self.assertIn("viewport_passive_cue", calls)
        self.assertNotIn("addGeometry", calls)
        self.assertNotIn("addExternal", calls)
        self.assertNotIn("openTransaction", calls)
        self.assertNotIn("commitTransaction", calls)
        self.assertIn("if kind not in self.SYMBOLS", source)

if __name__ == "__main__":
    unittest.main()
