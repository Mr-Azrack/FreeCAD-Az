# SPDX-License-Identifier: LGPL-2.1-or-later
"""Offline verification that modeled-thread checkpoints persist to disk."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

location = Path(__file__).resolve().parents[1] / "azdesign/hole_diagnostics.py"
module_spec = importlib.util.spec_from_file_location("az_hole_diagnostics", location)
module = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(module)


class HoleDiagnosticTest(unittest.TestCase):
    def test_durable_jsonl_stage_and_native_properties(self):
        with tempfile.TemporaryDirectory() as root:
            trace = module.ThreadDiagnostic.__new__(module.ThreadDiagnostic)
            trace.path = Path(root) / "crash-stages.jsonl"
            trace.record("before_transaction", purpose="experimental")
            spec = SimpleNamespace(
                __dataclass_fields__={"model_thread": None, "thread_size": None},
                model_thread=True, thread_size="M4",
            )
            # Use the genuine dataclass; the event must remain JSON-safe.
            from dataclasses import dataclass

            @dataclass
            class Spec:
                model_thread: bool = True
                thread_size: str = "M4"

            hole = SimpleNamespace(
                ModelThread=False, Threaded=True,
                ThreadType="ISOMetricProfile", ThreadSize="M4"
            )
            trace.record_spec("before_native_recompute", Spec(), feature=hole)
            events = [json.loads(line) for line in trace.path.read_text().splitlines()]
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["stage"], "before_transaction")
            self.assertEqual(events[1]["stage"], "before_native_recompute")
            self.assertTrue(events[1]["spec"]["model_thread"])
            self.assertEqual(events[1]["native_properties"]["ThreadSize"], "M4")


if __name__ == "__main__":
    unittest.main(verbosity=2)
