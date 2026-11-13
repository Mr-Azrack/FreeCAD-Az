# SPDX-License-Identifier: LGPL-2.1-or-later
"""Versioned, document-persistent ownership records for Sketcher circle arrays.

Records describe native geometry; they never replace Sketcher constraints.
Index validation is mandatory before an editor removes any owned geometry.
"""
import json
import uuid

PROPERTY = "AzSketchPatternRecords"
VERSION = 1


def read_records(sketch):
    raw = getattr(sketch, PROPERTY, "") or ""
    if not raw:
        return []
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError("Invalid sketch pattern record list")
    ids = []
    for record in payload:
        if not isinstance(record, dict) or record.get("version") != VERSION:
            raise ValueError("Unsupported sketch pattern record")
        record_id = record.get("id")
        if record_id is not None:
            if not isinstance(record_id, str) or not record_id.strip():
                raise ValueError("Invalid sketch pattern identity")
            ids.append(record_id)
        source = record.get("source")
        if type(source) is not int or source < 0:
            raise ValueError("Invalid sketch pattern source")
        indices = record.get("created")
        if not isinstance(indices, list) or not indices or any(
            type(index) is not int or index < 0 for index in indices
        ) or len(set(indices)) != len(indices):
            raise ValueError("Invalid sketch pattern ownership")
        constraints = record.get("constraints", [])
        if not isinstance(constraints, list) or any(type(i) is not int or i < 0 for i in constraints) or len(set(constraints)) != len(constraints):
            raise ValueError("Invalid sketch pattern constraint ownership")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate sketch pattern identity")
    all_geometry = [i for record in payload for i in record["created"]]
    all_constraints = [i for record in payload for i in record.get("constraints", [])]
    if len(all_geometry) != len(set(all_geometry)) or len(all_constraints) != len(set(all_constraints)):
        raise ValueError("Overlapping sketch pattern ownership")
    return payload


def append_record(sketch, parameters, created, constraints=()):
    """Persist one independent pattern, within the caller's open transaction."""
    source, columns, rows, pitch_x, pitch_y = parameters
    if type(source) is not int or not 0 <= source < sketch.GeometryCount:
        raise ValueError("Invalid pattern source geometry")
    if type(columns) is not int or type(rows) is not int or columns < 1 or rows < 1:
        raise ValueError("Invalid pattern dimensions")
    indices = list(created)
    if (any(type(index) is not int or index < 0 for index in indices)
            or len(set(indices)) != len(indices)):
        raise ValueError("Invalid generated geometry indices")
    if not indices or len(indices) != columns * rows - 1:
        raise ValueError("Pattern geometry count does not match dimensions")
    if source in indices or source < 0 or any(
        index >= sketch.GeometryCount for index in indices
    ):
        raise ValueError("Pattern references missing or source geometry")
    constraint_indices = list(constraints)
    if any(type(i) is not int or i < 0 for i in constraint_indices) or len(set(constraint_indices)) != len(constraint_indices):
        raise ValueError("Invalid generated constraint indices")
    if any(i >= sketch.ConstraintCount for i in constraint_indices):
        raise ValueError("Pattern references missing constraints")
    records = read_records(sketch)
    owned_constraints = {i for record in records for i in record.get("constraints", [])}
    if owned_constraints.intersection(constraint_indices):
        raise ValueError("Pattern would take ownership of another pattern's constraints")
    owned = {index for record in records for index in record["created"]}
    if source in owned or owned.intersection(indices):
        raise ValueError("Pattern would reference another pattern's generated geometry")
    if PROPERTY not in sketch.PropertiesList:
        sketch.addProperty("App::PropertyString", PROPERTY, "Design", 
                           "Versioned Sketch Pattern geometry ownership")
    record = {
        "version": VERSION,
        "id": uuid.uuid4().hex,
        "source": int(source),
        "columns": int(columns),
        "rows": int(rows),
        "pitch_x": float(pitch_x),
        "pitch_y": float(pitch_y),
        "created": indices,
        "constraints": constraint_indices,
    }
    records.append(record)
    setattr(sketch, PROPERTY, json.dumps(records, sort_keys=True))
    return record


def validate_ownership(sketch, record):
    """Fail closed before a future edit; never remove unrelated geometry."""
    indices = record["created"]
    return (0 <= record["source"] < sketch.GeometryCount
            and all(0 <= index < sketch.GeometryCount for index in indices)
            and len(set(indices)) == len(indices)
            and all(i < sketch.ConstraintCount for i in record.get("constraints", [])))


def find_record(sketch, record_id):
    """Resolve a single persistent pattern by identity, never by list position."""
    if not isinstance(record_id, str) or not record_id:
        raise ValueError("Missing sketch pattern identity")
    matches = [r for r in read_records(sketch) if r.get("id") == record_id]
    if len(matches) != 1:
        raise ValueError("Sketch pattern no longer exists or has ambiguous identity")
    record = matches[0]
    if not validate_ownership(sketch, record):
        geometry_count = sketch.GeometryCount
        constraint_count = sketch.ConstraintCount
        missing_geometry = [index for index in record["created"]
                            if index >= geometry_count]
        missing_constraints = [index for index in record.get("constraints", [])
                               if index >= constraint_count]
        raise ValueError(
            "Sketch pattern ownership is stale (geometry {}/{}, constraints {}/{}, "
            "missing geometry {}, missing constraints {}). Edit was blocked to "
            "protect the sketch.".format(
                len(record["created"]), geometry_count,
                len(record.get("constraints", [])), constraint_count,
                missing_geometry, missing_constraints))
    return record


def timeline_records(sketch):
    """Return stable identities and labels for Design's independent history items.

    Legacy records without an identity remain visible but cannot be edited
    until explicitly migrated after native geometry validation.
    """
    result = []
    for index, record in enumerate(read_records(sketch), 1):
        identity = record.get("id")
        result.append({
            "id": identity,
            "label": "Sketch Pattern {} ({} × {})".format(
                index, record["columns"], record["rows"]),
            "editable": bool(identity and record.get("constraints") and
                             validate_ownership(sketch, record)),
        })
    return result

def pitch_edit_plan(sketch, record_id, pitch_x, pitch_y):
    """Validate an in-place pitch edit without mutating native Sketcher.

    Changing occurrence counts would reindex geometry and potentially damage
    downstream features; this operation deliberately supports pitch only.
    """
    import math
    record = find_record(sketch, record_id)
    columns, rows = record["columns"], record["rows"]
    if not (isinstance(columns, int) and isinstance(rows, int)
            and columns >= 1 and rows >= 1
            and len(record["created"]) == columns * rows - 1):
        raise ValueError("Invalid persisted pattern dimensions")
    if not record.get("constraints") or len(record["constraints"]) != 3 * len(record["created"]):
        raise ValueError("Pattern constraint ownership is incomplete")
    if any(not math.isfinite(float(p)) or abs(float(p)) > 100000
           for p in (pitch_x, pitch_y)):
        raise ValueError("Invalid pattern pitch")
    pitch_x, pitch_y = float(pitch_x), float(pitch_y)
    if (columns > 1 and abs(pitch_x) < 0.001) or (rows > 1 and abs(pitch_y) < 0.001):
        raise ValueError("Pattern pitch must be nonzero")
    # The creation routine stores Equal, then X, then Y for each copy.
    # Reject a change that switches a zero-offset alignment constraint
    # (Vertical/Horizontal) into a dimensional constraint or vice versa.
    changes = []
    for position, (x, y) in enumerate(
            ( (x, y) for y in range(rows) for x in range(columns)
              if x or y )):
        ids = record["constraints"][position * 3: position * 3 + 3]
        for offset, old_pitch, new_pitch, multiplier in (
                (1, record["pitch_x"], pitch_x, x),
                (2, record["pitch_y"], pitch_y, y)):
            old_value = multiplier * old_pitch
            new_value = multiplier * new_pitch
            if (abs(old_value) < 0.001) != (abs(new_value) < 0.001):
                raise ValueError("Pattern constraint type would change")
            if abs(new_value) >= 0.001:
                changes.append((ids[offset], new_value))
    return record, changes

def edit_pitch(sketch, record_id, pitch_x, pitch_y):
    """Edit only the selected pattern's driving dimensions in one Undo step.

    No geometry/constraint deletion or reindexing is performed. All expected
    native constraints are checked before opening a transaction.
    """
    record, changes = pitch_edit_plan(sketch, record_id, pitch_x, pitch_y)
    constraints = sketch.Constraints
    source = record["source"]
    for pos, generated in enumerate(record["created"]):
        group = record["constraints"][3 * pos:3 * pos + 3]
        x = (pos + 1) % record["columns"]
        y = (pos + 1) // record["columns"]
        expected = ("Equal", "DistanceX" if x else "Vertical",
                    "DistanceY" if y else "Horizontal")
        for index, kind in zip(group, expected):
            item = constraints[index]
            if item.Type != kind or item.First != source or item.Second != generated:
                raise ValueError("Sketch pattern constraints changed; refusing unsafe edit")
    # Protect against a collision with any existing unowned circle before
    # applying a dimensional change; native solver still makes final decision.
    owned = set(record["created"])
    source_geom = sketch.Geometry[source]
    other_centers = [(g.Center.x, g.Center.y) for i, g in enumerate(sketch.Geometry)
                     if i != source and i not in owned and hasattr(g, "Center")]
    import math
    for y in range(record["rows"]):
        for x in range(record["columns"]):
            if not (x or y):
                continue
            cx = source_geom.Center.x + x * float(pitch_x)
            cy = source_geom.Center.y + y * float(pitch_y)
            if any(math.hypot(cx - ox, cy - oy) < 0.001 for ox, oy in other_centers):
                raise ValueError("Pattern would overlap another sketch circle")
    doc = sketch.Document
    doc.openTransaction("Design: Edit sketch pattern pitch")
    try:
        import FreeCAD as App
        for index, value in changes:
            sketch.setDatum(index, App.Units.Quantity(float(value), App.Units.Length))
        record["pitch_x"], record["pitch_y"] = float(pitch_x), float(pitch_y)
        records = read_records(sketch)
        for index, item in enumerate(records):
            if item.get("id") == record_id:
                records[index] = record
                break
        setattr(sketch, PROPERTY, json.dumps(records, sort_keys=True))
        doc.recompute()
        if "Invalid" in tuple(str(s) for s in getattr(sketch, "State", ())):
            raise ValueError("Sketch solver rejected the pattern edit")
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        doc.recompute()
        raise
    return record
