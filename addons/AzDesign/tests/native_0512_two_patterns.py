# SPDX-License-Identifier: LGPL-2.1-or-later
"""Native FreeCAD 1.1 regression: two independent patterns, undo and persistence."""
import json
import os
import tempfile
import sys
from pathlib import Path
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
# Match the Debian FreeCAD runtime discovery used by run_workflow.py.
libraries = (
    [Path(os.environ["FREECAD_LIB_DIR"])]
    if os.environ.get("FREECAD_LIB_DIR")
    else list(Path("/usr/lib").glob("freecad*/lib"))
)
sys.path[:0] = [str(PACKAGE_ROOT)] + [str(p) for p in libraries]
for root in (Path("/usr/share/freecad/Mod"), Path("/usr/share/freecad-python3/Mod")):
    if root.is_dir():
        sys.path[:0] = [str(root)] + [str(p) for p in root.iterdir() if p.is_dir()]
import FreeCAD as App
import Part
import azdesign
# The embedded FreeCAD interpreter may preload another installed AzDesign.
azdesign.__path__.insert(0, str(PACKAGE_ROOT / 'azdesign'))
from azdesign.sketch_pattern import pattern_circles
from azdesign.pattern_records import append_record, edit_pitch, read_records

doc = App.newDocument("AzTwoPattern0512")
path = os.path.join(tempfile.gettempdir(), "az_two_pattern_0512.FCStd")
try:
    sk = doc.addObject("Sketcher::SketchObject", "Sketch")
    for x in (0, 100):
        sk.addGeometry(Part.Circle(App.Vector(x, 0, 0), App.Vector(0, 0, 1), 2), False)
    a_source, b_source = 0, 1
    def create(source, dx, dy):
        before = sk.ConstraintCount
        copies = pattern_circles(sk, source, 2, 2, dx, dy)
        return append_record(sk, (source, 2, 2, dx, dy), copies,
                             tuple(range(before, sk.ConstraintCount)))
    a = create(a_source, 10, 20)
    b = create(b_source, 15, 25)
    assert len(read_records(sk)) == 2
    b_before = [(sk.Geometry[i].Center.x, sk.Geometry[i].Center.y) for i in b["created"]]
    edit_pitch(sk, a["id"], 12, 24)
    assert (read_records(sk)[0]["pitch_x"], read_records(sk)[1]["pitch_x"]) == (12, 15)
    assert [(sk.Geometry[i].Center.x, sk.Geometry[i].Center.y) for i in b["created"]] == b_before
    doc.saveAs(path)
    App.closeDocument(doc.Name)
    doc = App.openDocument(path)
    doc.UndoMode = 1  # headless FreeCAD disables transaction history by default
    sk = doc.getObject("Sketch")
    records = read_records(sk)
    assert [r["id"] for r in records] == [a["id"], b["id"]]
    assert [r["pitch_x"] for r in records] == [12, 15]
    edit_pitch(sk, b["id"], 17, 27)
    assert [r["pitch_x"] for r in read_records(sk)] == [12, 17]
    print('UNDO AVAILABLE', doc.UndoCount if hasattr(doc, 'UndoCount') else 'unknown', flush=True)
    doc.undo()
    print('AFTER UNDO', [r['pitch_x'] for r in read_records(sk)], flush=True)
    assert [r["pitch_x"] for r in read_records(sk)] == [12, 15]
    doc.redo()
    assert [r["pitch_x"] for r in read_records(sk)] == [12, 17]
    print("PASS two independent patterns, save/reopen, undo/redo")
finally:
    App.closeDocument(doc.Name)
