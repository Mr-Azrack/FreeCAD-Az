# SPDX-License-Identifier: LGPL-2.1-or-later
"""Real FreeCAD regression for native solid references used by Sketcher snapping."""
import unittest
import FreeCAD as App
import Part
import Sketcher
from azdesign.snap_targets import enable_solid_edge_snapping


class SolidEdgeSnappingNativeTest(unittest.TestCase):
    def test_top_face_links_undo_and_reopen(self):
        doc = App.newDocument("AzSolidSnapNative", hidden=True, temp=True)
        try:
            body = doc.addObject("PartDesign::Body", "Body")
            base = body.newObject("Sketcher::SketchObject", "BaseSketch")
            points = [App.Vector(0, 0, 0), App.Vector(20, 0, 0),
                      App.Vector(20, 20, 0), App.Vector(0, 20, 0)]
            for i in range(4):
                base.addGeometry(Part.LineSegment(points[i], points[(i + 1) % 4]), False)
            pad = body.newObject("PartDesign::Pad", "Pad")
            pad.Profile = base
            pad.Length = 5
            doc.recompute()
            sketch = body.newObject("Sketcher::SketchObject", "TopSketch")
            sketch.Placement.Base.z = 5
            doc.recompute()
            doc.UndoMode = 1
            self.assertEqual(enable_solid_edge_snapping(sketch), 4)
            self.assertEqual(enable_solid_edge_snapping(sketch), 0)
            self.assertEqual(len(sketch.ExternalGeometry), 1)
            self.assertEqual(len(sketch.ExternalGeometry[0][1]), 4)
            self.assertEqual(sketch.State, ['Up-to-date'])
            doc.undo()
            doc.recompute()
            self.assertEqual(sketch.ExternalGeometry, [])
            doc.redo()
            doc.recompute()
            self.assertEqual(len(sketch.ExternalGeometry[0][1]), 4)
            import os
            import tempfile
            with tempfile.TemporaryDirectory() as folder:
                filename = os.path.join(folder, "Snap.FCStd")
                doc.saveAs(filename)
                App.closeDocument(doc.Name)
                doc = None
                reopened = App.openDocument(filename)
                try:
                    source = reopened.getObject("Pad")
                    linked = reopened.getObject("TopSketch")
                    self.assertEqual(linked.ExternalGeometry[0][0], source)
                    self.assertEqual(len(linked.ExternalGeometry[0][1]), 4)
                    self.assertNotIn("Invalid", linked.State)
                finally:
                    App.closeDocument(reopened.Name)
        finally:
            if doc is not None:
                App.closeDocument(doc.Name)


if __name__ == "__main__":
    unittest.main()
