# SPDX-License-Identifier: LGPL-2.1-or-later
"""No automatic OCCT modeled-helix execution, including after toggle-off."""

import importlib.util
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[1] / "azdesign"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, root / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


HoleSpec = load("hole_ui_spec", "hole_spec.py").HoleSpec
can_live_preview = load("hole_ui_policy", "hole_ui_policy.py").can_live_preview


class HoleUiPolicyTest(unittest.TestCase):
    def allowed(self, spec, **options):
        return can_live_preview(
            spec, enabled=options.get("enabled", True),
            has_sketch=options.get("has_sketch", True),
            original_modeled=options.get("original_modeled", False),
            previously_modeled=options.get("previously_modeled", False),
        )

    def test_plain_and_complete_cosmetic_holes_can_auto_preview(self):
        self.assertTrue(self.allowed(HoleSpec()))
        self.assertTrue(self.allowed(HoleSpec(
            thread_type="ISOMetricProfile", thread_size="M4"
        )))
        self.assertFalse(self.allowed(HoleSpec(
            thread_type="ISOMetricProfile"
        )))

    def test_requires_enabled_option_and_selected_sketch(self):
        self.assertFalse(self.allowed(HoleSpec(), enabled=False))
        self.assertFalse(self.allowed(HoleSpec(), has_sketch=False))

    def test_modeled_and_previous_modeled_never_auto_preview(self):
        modeled = HoleSpec(
            thread_type="ISOMetricProfile", thread_size="M4",
            model_thread=True, experimental=True
        )
        self.assertFalse(self.allowed(modeled))
        self.assertFalse(self.allowed(HoleSpec(), original_modeled=True))
        self.assertFalse(self.allowed(HoleSpec(), previously_modeled=True))
        self.assertFalse(self.allowed(HoleSpec(
            thread_type="ISOMetricProfile", thread_size="M4"
        ), original_modeled=True))

    def test_invalid_values_cannot_reach_recompute(self):
        self.assertFalse(self.allowed(HoleSpec(diameter=0)))
        self.assertFalse(self.allowed(HoleSpec(depth=float("nan"))))
        self.assertFalse(self.allowed(HoleSpec(thread_type="bogus")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
