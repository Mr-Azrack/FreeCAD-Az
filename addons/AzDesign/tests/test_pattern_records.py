# SPDX-License-Identifier: LGPL-2.1-or-later
"""Pure-Python regression for persisted sketch pattern ownership."""
import json
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from azdesign.pattern_records import append_record, read_records, validate_ownership, find_record, timeline_records


class FakeSketch:
    GeometryCount = 10
    ConstraintCount = 20
    PropertiesList = []

    def addProperty(self, _kind, name, _group, _description):
        self.PropertiesList = self.PropertiesList + [name]


class PatternRecordsTests(unittest.TestCase):
    def test_multiple_independent_records_survive_serialization(self):
        sketch = FakeSketch()
        append_record(sketch, (0, 2, 2, 10, 20), (1, 2, 3))
        append_record(sketch, (4, 2, 2, 15, 25), (5, 6, 7))
        records = read_records(sketch)
        self.assertEqual(len(records), 2)
        self.assertEqual(json.loads(sketch.AzSketchPatternRecords), records)
        self.assertTrue(all(validate_ownership(sketch, item) for item in records))

    def test_rejects_overlapping_ownership(self):
        sketch = FakeSketch()
        append_record(sketch, (0, 2, 2, 10, 20), (1, 2, 3))
        before = sketch.AzSketchPatternRecords
        with self.assertRaises(ValueError):
            append_record(sketch, (4, 2, 2, 10, 20), (2, 5, 6))
        self.assertEqual(sketch.AzSketchPatternRecords, before)

    def test_constraint_ownership_is_independent(self):
        sketch = FakeSketch()
        append_record(sketch, (0, 2, 2, 10, 20), (1, 2, 3), (0, 1))
        append_record(sketch, (4, 2, 2, 10, 20), (5, 6, 7), (2, 3))
        self.assertEqual(read_records(sketch)[0]["constraints"], [0, 1])
        before = sketch.AzSketchPatternRecords
        with self.assertRaises(ValueError):
            append_record(sketch, (8, 2, 2, 10, 20), (4, 8, 9), (1, 5))
        self.assertEqual(before, sketch.AzSketchPatternRecords)
        sketch.ConstraintCount = 1
        self.assertFalse(validate_ownership(sketch, read_records(sketch)[0]))

    def test_corrupt_constraint_ownership_fails_closed(self):
        sketch = FakeSketch()
        sketch.AzSketchPatternRecords = '[{"version": 1, "created": [1], "constraints": [2, 2]}]'
        with self.assertRaises(ValueError):
            read_records(sketch)

    def test_stable_identity_and_independent_timeline_lookup(self):
        sketch = FakeSketch()
        first = append_record(sketch, (0, 2, 2, 10, 20), (1, 2, 3), (0, 1))
        second = append_record(sketch, (4, 2, 2, 15, 25), (5, 6, 7), (2, 3))
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(find_record(sketch, second["id"])["source"], 4)
        items = timeline_records(sketch)
        self.assertEqual([item["id"] for item in items], [first["id"], second["id"]])
        self.assertTrue(all(item["editable"] for item in items))
        sketch.AzSketchPatternRecords = json.dumps([second, first])
        self.assertEqual(find_record(sketch, first["id"])["source"], 0)
        sketch.ConstraintCount = 1
        with self.assertRaises(ValueError):
            find_record(sketch, second["id"])

    def test_duplicate_identity_fails_closed(self):
        sketch = FakeSketch()
        first = append_record(sketch, (0, 2, 2, 10, 20), (1, 2, 3), (0, 1))
        second = append_record(sketch, (4, 2, 2, 10, 20), (5, 6, 7), (2, 3))
        second["id"] = first["id"]
        sketch.AzSketchPatternRecords = json.dumps([first, second])
        with self.assertRaisesRegex(ValueError, "Duplicate sketch pattern identity"):
            read_records(sketch)

    def test_legacy_record_is_visible_but_not_editable(self):
        sketch = FakeSketch()
        record = append_record(sketch, (0, 2, 2, 10, 20), (1, 2, 3))
        del record["id"]
        sketch.AzSketchPatternRecords = json.dumps([record])
        self.assertFalse(timeline_records(sketch)[0]["editable"])

    def test_corrupt_record_fails_closed(self):
        sketch = FakeSketch()
        sketch.AzSketchPatternRecords = '[{"version": 1, "created": [2, 2]}]'
        with self.assertRaises(ValueError):
            read_records(sketch)


if __name__ == "__main__":
    unittest.main()
