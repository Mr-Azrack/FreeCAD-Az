import os
import tempfile
import FreeCAD as App
import Part
from azdesign.sketch_pattern import pattern_circles
from azdesign.pattern_records import append_record, edit_pitch, read_records

doc = App.newDocument("AzNativePattern0512")
try:
    sk = doc.addObject("Sketcher::SketchObject", "Sketch")
    sk.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2), False)
    copies = pattern_circles(sk, 0, 2, 2, 10, 20)
    record = append_record(sk, (0, 2, 2, 10, 20), copies, tuple(range(sk.ConstraintCount)))
    print("BEFORE:", [(round(g.Center.x, 2), round(g.Center.y, 2)) for g in sk.Geometry])
    edit_pitch(sk, record["id"], 12, 24)
    print("AFTER:", [(round(g.Center.x, 2), round(g.Center.y, 2)) for g in sk.Geometry])
    assert round(sk.Geometry[1].Center.x - sk.Geometry[0].Center.x, 4) == 12
    assert round(sk.Geometry[2].Center.y - sk.Geometry[0].Center.y, 4) == 24
    path = os.path.join(tempfile.gettempdir(), "az_native_0512_smoke.FCStd")
    doc.saveAs(path)
    App.closeDocument(doc.Name)
    reopened = App.openDocument(path)
    assert len(read_records(reopened.getObject("Sketch"))) == 1
    print("PASS: native edit and save/reopen", path)
    App.closeDocument(reopened.Name)
except Exception:
    import traceback
    traceback.print_exc()
    raise
