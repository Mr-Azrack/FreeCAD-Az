# SPDX-License-Identifier: LGPL-2.1-or-later
"""Versioned, document-persistent ownership records for Sketcher circle arrays.

Records describe native geometry; they never replace Sketcher constraints.
Index validation is mandatory before an editor removes any owned geometry.
"""
import json

PROPERTY = "AzSketchPatternRecords"
VERSION = 1


def read_records(sketch):
    raw = getattr(sketch, PROPERTY, "") or ""
    if not raw:
        return []
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError("Invalid sketch pattern record list")
    for record in payload:
        if not isinstance(record, dict) or record.get("version") != VERSION:
            raise ValueError("Unsupported sketch pattern record")
        indices = record.get("created")
        if not isinstance(indices, list) or not indices or any(
            type(index) is not int or index < 0 for index in indices
        ) or len(set(indices)) != len(indices):
            raise ValueError("Invalid sketch pattern ownership")
    return payload


def append_record(sketch, parameters, created):
    """Persist one independent pattern, within the caller's open transaction."""
    source, columns, rows, pitch_x, pitch_y = parameters
    indices = [int(index) for index in created]
    if not indices or len(indices) != columns * rows - 1:
        raise ValueError("Pattern geometry count does not match dimensions")
    if source in indices or source < 0 or any(
        index >= sketch.GeometryCount for index in indices
    ):
        raise ValueError("Pattern references missing or source geometry")
    records = read_records(sketch)
    owned = {index for record in records for index in record["created"]}
    if owned.intersection(indices):
        raise ValueError("Pattern would take ownership of another pattern's geometry")
    if PROPERTY not in sketch.PropertiesList:
        sketch.addProperty("App::PropertyString", PROPERTY, "Design", 
                           "Versioned Sketch Pattern geometry ownership")
    record = {
        "version": VERSION,
        "source": int(source),
        "columns": int(columns),
        "rows": int(rows),
        "pitch_x": float(pitch_x),
        "pitch_y": float(pitch_y),
        "created": indices,
    }
    records.append(record)
    setattr(sketch, PROPERTY, json.dumps(records, sort_keys=True))
    return record


def validate_ownership(sketch, record):
    """Fail closed before a future edit; never remove unrelated geometry."""
    indices = record["created"]
    return (record["source"] < sketch.GeometryCount
            and all(index < sketch.GeometryCount for index in indices)
            and len(set(indices)) == len(indices))
