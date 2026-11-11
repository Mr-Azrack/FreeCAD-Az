# SPDX-License-Identifier: LGPL-2.1-or-later
"""Exact geometry and parametric workflow tests; run with FreeCAD's Python."""

import math
import tempfile
import unittest
from pathlib import Path
import FreeCAD as App
import Part
import PartDesign
import Sketcher
from azdesign import features, profiles, operations, history, presspull, parameters, quick_dimension, sketch_rectangle, sketch_pattern, edge_treatments, snap_targets
from azdesign.hole_operation import HoleOperation
from azdesign.hole_spec import HoleSpec, thread_sizes
from azdesign.solid_pattern_engine import PatternDraft

RECT = [(0, 0, 10, 0), (10, 0, 10, 10), (10, 10, 0, 10), (0, 10, 0, 0)]


def sketch(doc, lines=RECT, body=None, name="Sketch", z=0):
    obj = (
        (body or doc).newObject("Sketcher::SketchObject", name)
        if body
        else doc.addObject("Sketcher::SketchObject", name)
    )
    for x, y, u, v in lines:
        obj.addGeometry(Part.LineSegment(App.Vector(x, y, 0), App.Vector(u, v, 0)))
    obj.Placement.Base.z = z
    doc.recompute()
    return obj


def top_face(obj):
    return next(
        "Face" + str(i + 1)
        for i, face in enumerate(obj.Shape.Faces)
        if face.normalAt(0, 0).z > 0.99
    )


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.doc = App.newDocument("AzWorkflowTest", hidden=True, temp=True)
        self.doc.UndoMode = 1

    def tearDown(self):
        if self.doc.Name in App.listDocuments():
            App.closeDocument(self.doc.Name)

    def base(self, height=6):
        body = self.doc.addObject("PartDesign::Body", "Body")
        source = sketch(self.doc, body=body)
        obj = features.create_extrude(body, (source, []), whole=True, operation="New body")
        obj.Length = height
        self.doc.recompute()
        return body, source, obj

    def test_fusion_style_plate_profile_preselects_outer_region_with_holes(self):
        """The plate is one region with holes, not 10 manually ticked profiles."""
        body = self.doc.addObject("PartDesign::Body", "PlateProfileBody")
        outline = [
            (0, 0, 65, 0), (65, 0, 65, 100),
            (65, 100, 0, 100), (0, 100, 0, 0),
        ]
        source = sketch(self.doc, outline, body=body, name="PerforatedPlate")
        for x in (12, 53):
            for y in (15, 28, 70, 85):
                source.addGeometry(
                    Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), 2.5)
                )
        self.doc.recompute()
        regions = profiles.regions(source)
        self.assertGreaterEqual(len(regions), 9)
        index = profiles.preferred_plate_region(regions)
        self.assertIsNotNone(index)
        plate = regions[index]
        self.assertEqual(len(plate.face.Wires) - 1, 8)
        self.assertAlmostEqual(
            plate.face.Area, 65 * 100 - 8 * math.pi * 2.5**2,
            delta=0.5,
        )
        feature = features.create_extrude(
            body, (source, []), operation="New body",
            region_descriptors=[plate.descriptor()],
        )
        feature.Length = 8
        self.doc.recompute()
        self.assertTrue(feature.Shape.isValid())
        self.assertEqual(len(feature.Shape.Solids), 1)
        self.assertAlmostEqual(
            feature.Shape.Volume, plate.face.Area * 8, delta=1.0,
        )

    def test_ambiguous_sketch_profiles_still_require_explicit_selection(self):
        class FakeRegion:
            def __init__(self, area, wires):
                self.face = type("FaceStub", (), {
                    "Area": area, "Wires": [object()] * wires
                })()
        self.assertIsNone(profiles.preferred_plate_region([]))
        self.assertEqual(profiles.preferred_plate_region([FakeRegion(20, 1)]), 0)
        self.assertIsNone(profiles.preferred_plate_region([
            FakeRegion(100, 4), FakeRegion(60, 1)
        ]))
        self.assertIsNone(profiles.preferred_plate_region([
            FakeRegion(1000, 1), FakeRegion(10, 1)
        ]))

    def test_small_scale_fillet_chamfer_validation_and_native_history(self):
        """Sub-millimetre design: never scale source to make a bevel work."""
        body = self.doc.addObject("PartDesign::Body", "MicroBody")
        original = body.newObject("PartDesign::Feature", "MicroBlock")
        original.Shape = Part.makeBox(1.005, 0.702, 2.0)
        self.doc.recompute()
        initial = original.Shape.Volume
        vertical = next(
            "Edge" + str(i + 1) for i, edge in enumerate(original.Shape.Edges)
            if edge.BoundBox.ZLength > 1.999
        )
        names, checked = edge_treatments.preflight(
            original, [vertical], 0.10, "Fillet"
        )
        self.assertEqual(names, (vertical,))
        self.assertTrue(checked.isValid())
        self.assertAlmostEqual(original.Shape.Volume, initial)
        self.assertEqual(body.Tip, original)
        new_feature = edge_treatments.create(
            original, [vertical], 0.10, "Fillet"
        )
        self.assertEqual(new_feature.TypeId, "PartDesign::Fillet")
        self.assertTrue(new_feature.Shape.isValid())
        self.assertEqual(body.Tip, new_feature)
        self.doc.undo()
        self.doc.recompute()
        self.assertEqual(body.Tip.Name, original.Name)
        self.assertAlmostEqual(body.Shape.Volume, initial)

        # Test chamfer separately on original feature (after Undo).
        original = self.doc.getObject("MicroBlock")
        name = next(
            "Edge" + str(i + 1) for i, edge in enumerate(original.Shape.Edges)
            if edge.BoundBox.ZLength > 1.999
        )
        chamfer = edge_treatments.create(
            original, [name], 0.10, "Chamfer"
        )
        self.assertEqual(chamfer.TypeId, "PartDesign::Chamfer")
        self.assertTrue(chamfer.Shape.isValid())
        self.assertEqual(body.Tip, chamfer)

    def test_fusion_style_timeline_fillet_size_edit_is_undoable(self):
        """An existing native Fillet stays parametric under Design editing."""
        body, _source, original = self.base(height=6)
        vertical = next(
            "Edge" + str(i + 1) for i, edge in enumerate(original.Shape.Edges)
            if edge.BoundBox.ZLength > 5.999
        )
        fillet = edge_treatments.create(original, [vertical], 0.5, "Fillet")
        before = fillet.Shape.Volume
        self.doc.openTransaction("Design: Edit Fillet")
        fillet.Radius = 0.25
        self.doc.recompute()
        self.assertTrue(fillet.Shape.isValid())
        self.assertEqual(len(fillet.Shape.Solids), 1)
        self.doc.commitTransaction()
        self.assertNotAlmostEqual(fillet.Shape.Volume, before, places=3)
        self.doc.undo()
        self.doc.recompute()
        restored = self.doc.getObject(fillet.Name)
        self.assertAlmostEqual(restored.Radius.Value, 0.5, places=5)
        self.assertAlmostEqual(restored.Shape.Volume, before, places=3)

    def test_edge_treatment_invalid_is_non_destructive(self):
        body = self.doc.addObject("PartDesign::Body", "ThinBody")
        source = body.newObject("PartDesign::Feature", "ThinBlock")
        source.Shape = Part.makeBox(0.007, 0.702, 2)
        self.doc.recompute()
        before = {obj.Name for obj in self.doc.Objects}
        tip = body.Tip
        edge = next(
            "Edge" + str(i + 1) for i, item in enumerate(source.Shape.Edges)
            if item.BoundBox.ZLength > 1.999
        )
        with self.assertRaises(features.DesignError):
            edge_treatments.preflight(source, [edge], 0.5, "Fillet")
        with self.assertRaises(features.DesignError):
            edge_treatments.create(source, [edge], 0.5, "Fillet")
        self.assertEqual({obj.Name for obj in self.doc.Objects}, before)
        self.assertEqual(body.Tip, tip)
        self.assertAlmostEqual(body.Shape.Volume, 0.007 * 0.702 * 2)

    def test_exact_snap_endpoints_midpoint_and_circle_center(self):
        line = Part.makeLine(App.Vector(1, 2, 0), App.Vector(5, 2, 0))
        snaps = snap_targets.targets(line, "Edge2")
        self.assertEqual([snap.name for snap in snaps], [
            "Start", "End", "Midpoint"
        ])
        self.assertAlmostEqual(snaps[2].point.x, 3)
        self.assertAlmostEqual(snaps[2].point.y, 2)
        circle = Part.makeCircle(0.5, App.Vector(2, 3, 4))
        circle_targets = snap_targets.targets(circle, "Edge7")
        centers = [target for target in circle_targets if target.name == "Center"]
        self.assertEqual(len(centers), 1)
        self.assertEqual(centers[0].edge_name, "Edge7")
        self.assertAlmostEqual(centers[0].point.x, 2)
        self.assertAlmostEqual(centers[0].point.y, 3)
        self.assertAlmostEqual(centers[0].point.z, 4)

    def test_center_snap_inserts_fixed_construction_point_and_undoes(self):
        body = self.doc.addObject("PartDesign::Body", "SnapBody")
        target = sketch(self.doc, [], body=body)
        center = snap_targets.SnapTarget(
            "Center", App.Vector(2.5, 3.25, 5), "Edge4"
        )
        initial = target.GeometryCount
        index = snap_targets.create_sketch_reference(target, center)
        self.assertEqual(target.GeometryCount, initial + 1)
        self.assertTrue(target.getConstruction(index))
        self.assertEqual(target.ConstraintCount, 1)
        self.assertAlmostEqual(target.Geometry[index].X, 2.5)
        self.assertAlmostEqual(target.Geometry[index].Y, 3.25)
        self.doc.undo()
        self.doc.recompute()
        updated = self.doc.getObject(target.Name)
        self.assertEqual(updated.GeometryCount, initial)

    def test_sized_rectangle_is_native_parametric_sketch_and_undoable(self):
        body = self.doc.addObject("PartDesign::Body", "Body")
        source = sketch(self.doc, [], body=body)
        indices, width_constraint, height_constraint = (
            sketch_rectangle.dimensioned_rectangle(source, 60, 40)
        )
        self.assertEqual(len(indices), 4)
        self.assertEqual(source.GeometryCount, 4)
        self.assertEqual(source.ConstraintCount, 11)
        self.assertAlmostEqual(profiles.regions(source)[0].face.Area, 2400)
        source.setDatum(width_constraint, App.Units.Quantity("70 mm"))
        self.doc.recompute()
        self.assertAlmostEqual(profiles.regions(source)[0].face.Area, 2800)
        source.setDatum(height_constraint, App.Units.Quantity("45 mm"))
        self.doc.recompute()
        self.assertAlmostEqual(profiles.regions(source)[0].face.Area, 3150)

    def test_sized_rectangle_rejects_overlapping_or_invalid_sizes(self):
        body = self.doc.addObject("PartDesign::Body", "Body")
        source = sketch(self.doc, [], body=body)
        for width, height in ((0, 20), (20, float("nan")), (-1, 10)):
            with self.assertRaisesRegex(features.DesignError, "between"):
                sketch_rectangle.dimensioned_rectangle(source, width, height)
        self.assertEqual(source.GeometryCount, 0)
        sketch_rectangle.dimensioned_rectangle(source, 20, 12)
        with self.assertRaisesRegex(features.DesignError, "empty sketch"):
            sketch_rectangle.dimensioned_rectangle(source, 10, 8)

    def test_four_hole_rectangular_sketch_pattern_drives_native_hole(self):
        """Owner acceptance: one circle → 2x2 pattern → four cut holes."""
        body = self.doc.addObject("PartDesign::Body", "PlateBody")
        plate_sketch = sketch(self.doc, [], body=body, name="PlateProfile")
        sketch_rectangle.dimensioned_rectangle(plate_sketch, 80, 60)
        plate = features.create_extrude(
            body, (plate_sketch, []), whole=True, operation="New body"
        )
        plate.Length = 8
        self.doc.recompute()
        self.assertTrue(plate.Shape.isValid())
        initial_volume = plate.Shape.Volume
        centers = sketch(self.doc, [], body=body, name="FourHoleCenters", z=8)
        circle = centers.addGeometry(
            Part.Circle(App.Vector(12, 12, 0), App.Vector(0, 0, 1), 2.5),
            False
        )
        size_id = centers.addConstraint(Sketcher.Constraint("Diameter", circle, 5))
        centers.addConstraint(Sketcher.Constraint("DistanceX", circle, 3, 12))
        centers.addConstraint(Sketcher.Constraint("DistanceY", circle, 3, 12))
        self.doc.recompute()
        copies = sketch_pattern.pattern_circles(
            centers, circle, columns=2, rows=2, pitch_x=45, pitch_y=35
        )
        self.assertEqual(len(copies), 3)
        self.assertEqual(centers.GeometryCount, 4)
        self.assertEqual(len(sketch_pattern.circle_indices(centers)), 4)
        self.assertEqual({
            (round(g.Center.x, 3), round(g.Center.y, 3))
            for g in centers.Geometry
        }, {(12, 12), (57, 12), (12, 47), (57, 47)})
        self.assertTrue(all(abs(g.Radius - 2.5) < 1e-6 for g in centers.Geometry))
        self.assertTrue(centers.Shape.isValid())

        # The source circle's driving dimension must update all copies.
        centers.setDatum(size_id, App.Units.Quantity("6 mm"))
        self.doc.recompute()
        self.assertTrue(all(abs(g.Radius - 3) < 1e-5 for g in centers.Geometry))
        op = HoleOperation(self.doc, centers)
        op.preview(HoleSpec(diameter=6, depth=8, through_all=True))
        hole = op.accept()
        self.assertTrue(hole.Shape.isValid())
        self.assertEqual(len(hole.Shape.Solids), 1)
        self.assertLess(hole.Shape.Volume, initial_volume)
        self.assertAlmostEqual(
            hole.Shape.Volume, initial_volume - 4 * math.pi * 3 * 3 * 8,
            delta=1,
        )
        self.assertEqual(body.Tip, hole)

    def test_sketch_pattern_rejects_overlapping_centers_without_mutation(self):
        body = self.doc.addObject("PartDesign::Body", "Body")
        centers = sketch(self.doc, [], body=body)
        src = centers.addGeometry(
            Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 2)
        )
        centers.addGeometry(
            Part.Circle(App.Vector(45, 0, 0), App.Vector(0, 0, 1), 2)
        )
        before = centers.GeometryCount
        with self.assertRaisesRegex(features.DesignError, "coincides"):
            sketch_pattern.pattern_circles(
                centers, src, columns=2, rows=1, pitch_x=45, pitch_y=0
            )
        self.assertEqual(centers.GeometryCount, before)
        with self.assertRaisesRegex(features.DesignError, "nonzero"):
            sketch_pattern.pattern_circles(
                centers, src, columns=2, rows=2, pitch_x=0, pitch_y=45
            )
        self.assertEqual(centers.GeometryCount, before)

    def test_design_solid_linear_pattern_previews_and_edits_real_holes(self):
        """Real FreeCAD kernel: pattern one hole in a plate, cancel and edit."""
        body = self.doc.addObject("PartDesign::Body", "PatternPlateBody")
        plate_profile = sketch(self.doc, [], body=body, name="PatternPlateProfile")
        sketch_rectangle.dimensioned_rectangle(plate_profile, 85, 65)
        plate = features.create_extrude(
            body, (plate_profile, []), whole=True, operation="New body"
        )
        plate.Length = 8
        self.doc.recompute()
        initial_volume = plate.Shape.Volume

        source = sketch(self.doc, [], body=body, name="PatternSourceHole", z=8)
        source.addGeometry(
            Part.Circle(App.Vector(13, 13, 0), App.Vector(0, 0, 1), 2.5)
        )
        self.doc.recompute()
        op = HoleOperation(self.doc, source)
        op.preview(HoleSpec(diameter=5, depth=8, through_all=True))
        hole = op.accept()
        self.doc.recompute()
        one_hole_volume = hole.Shape.Volume
        self.assertLess(one_hole_volume, initial_volume)

        # A draft must show a real native patterned solid before Apply.
        draft = PatternDraft(hole)
        patterned = draft.preview(2, 32, "X_Axis")
        self.assertEqual(patterned.TypeId, "PartDesign::LinearPattern")
        self.assertTrue(patterned.Shape.isValid())
        self.assertEqual(patterned.Occurrences, 2)
        self.assertLess(patterned.Shape.Volume, one_hole_volume)
        self.assertAlmostEqual(
            patterned.Shape.Volume, initial_volume - 2 * math.pi * 2.5**2 * 8,
            delta=1,
        )
        self.assertEqual(body.Tip, patterned)
        self.assertGreater(patterned.Shape.Volume, 0)
        draft.cancel()
        self.doc.recompute()
        self.assertEqual(body.Tip.Name, hole.Name)
        self.assertAlmostEqual(body.Shape.Volume, one_hole_volume, places=4)

        draft = PatternDraft(hole)
        saved = draft.preview(2, 32, "X_Axis")
        draft.accept()
        self.doc.recompute()
        self.assertTrue(saved.Shape.isValid())
        self.assertEqual(body.Tip, saved)
        # Design-owned editing operates on the same native pattern, not
        # a duplicate or a baked copy of the feature.
        editor = PatternDraft(hole, existing=saved)
        editor.preview(3, 24, "X_Axis")
        self.assertEqual(saved.Occurrences, 3)
        editor.cancel()
        self.doc.recompute()
        restored = self.doc.getObject(saved.Name)
        self.assertEqual(restored.Occurrences, 2)
        self.assertEqual(body.Tip, restored)

        # FreeCAD 1.1 provides a second native pattern direction. Earlier
        # FreeCAD runtimes used by Linux CI do not always have that property.
        # Keep the single-direction acceptance mandatory in both versions,
        # and prove the four-hole 2D grid wherever native properties exist.
        if {"Direction2", "Occurrences2", "Length2"}.issubset(
            set(restored.PropertiesList)
        ):
            two_axis = PatternDraft(hole, existing=restored)
            grid = two_axis.preview(
                2, 32, "X_Axis", count2=2, spacing2=25, direction2="Y_Axis"
            )
            self.assertEqual(grid.Occurrences2, 2)
            self.assertAlmostEqual(
                grid.Shape.Volume, initial_volume - 4 * math.pi * 2.5**2 * 8,
                delta=1,
            )
            two_axis.accept()
            self.assertTrue(body.Shape.isValid())

    def test_fixture_full_history_dimension_edit_hole_fillet_undo_and_save(self):
        """Release gate: one real machining fixture survives normal CAD edits."""
        body = self.doc.addObject("PartDesign::Body", "FixtureBody")
        plate_sketch = sketch(self.doc, [], body=body, name="PlateSketch")
        _, width_id, height_id = sketch_rectangle.dimensioned_rectangle(
            plate_sketch, 60, 40
        )
        plate = features.create_extrude(
            body, (plate_sketch, []), whole=True, operation="New body"
        )
        plate.Length = 8
        self.doc.recompute()
        self.assertAlmostEqual(body.Shape.Volume, 60 * 40 * 8)
        self.assertTrue(plate.Shape.isValid())

        pocket_sketch = sketch(
            self.doc, [
                (20, 12, 40, 12), (40, 12, 40, 28),
                (40, 28, 20, 28), (20, 28, 20, 12),
            ],
            body=body, name="PocketSketch", z=8
        )
        pocket_operation = operations.Operation(self.doc)
        pocket = pocket_operation.update({
            "source": (pocket_sketch, []),
            "whole": True,
            "operation": "Cut",
            "target": body,
            "distance": "3 mm",
        })[0]
        pocket_operation.accept()
        self.assertAlmostEqual(pocket.Shape.Volume, 19200 - 20 * 16 * 3)
        self.assertTrue(pocket.Shape.isValid())

        centers = sketch(self.doc, [], body=body, name="BoltCenters", z=8)
        for x, y in ((8, 8), (52, 32)):
            centers.addGeometry(
                Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), 1)
            )
        self.doc.recompute()
        create_holes = HoleOperation(self.doc, centers)
        hole_volume = create_holes.preview(
            HoleSpec(diameter=3, depth=8, through_all=True)
        )
        self.assertLess(hole_volume, pocket.Shape.Volume)
        holes = create_holes.accept()
        self.assertTrue(holes.Shape.isValid())

        # Choose a real outer vertical edge at the origin. This preserves the
        # fillet through plate width edits and avoids hard-coded edge numbers.
        edge_name = next(
            "Edge" + str(i + 1)
            for i, edge in enumerate(holes.Shape.Edges)
            if abs(edge.BoundBox.XMin) < 1e-6
            and abs(edge.BoundBox.XMax) < 1e-6
            and abs(edge.BoundBox.YMin) < 1e-6
            and abs(edge.BoundBox.YMax) < 1e-6
            and edge.BoundBox.ZLength > 7.9
        )
        fillet = body.newObject("PartDesign::Fillet", "CornerFillet")
        fillet.Base = (holes, [edge_name])
        fillet.Radius = 0.65
        self.doc.recompute()
        self.assertEqual(body.Tip, fillet)
        self.assertTrue(fillet.Shape.isValid())
        original_volume = fillet.Shape.Volume

        plate_sketch.setDatum(width_id, App.Units.Quantity("70 mm"))
        self.doc.recompute()
        self.assertAlmostEqual(plate.Shape.Volume, 70 * 40 * 8)
        self.assertTrue(holes.Shape.isValid())
        self.assertTrue(fillet.Shape.isValid())
        self.assertGreater(fillet.Shape.Volume, original_volume + 3000)
        self.assertEqual(body.Tip, fillet)

        edit = HoleOperation(self.doc, centers, editing=holes)
        edit.preview(HoleSpec(diameter=4, depth=8, through_all=True))
        edit.cancel()
        self.assertEqual(body.Tip, fillet)
        cancelled_volume = fillet.Shape.Volume
        edit = HoleOperation(self.doc, centers, editing=holes)
        edit.preview(HoleSpec(diameter=4, depth=8, through_all=True))
        edit.accept()
        self.assertEqual(body.Tip, fillet)
        self.assertTrue(fillet.Shape.isValid())
        self.assertLess(fillet.Shape.Volume, cancelled_volume)
        after_edit = fillet.Shape.Volume
        self.doc.undo()
        self.doc.recompute()
        self.assertAlmostEqual(fillet.Shape.Volume, cancelled_volume, places=4)
        self.doc.redo()
        self.doc.recompute()
        self.assertAlmostEqual(fillet.Shape.Volume, after_edit, places=4)

        with tempfile.TemporaryDirectory() as directory:
            filename = str(Path(directory) / "AzFixture.FCStd")
            sketch_name, plate_name = plate_sketch.Name, plate.Name
            hole_name, fillet_name = holes.Name, fillet.Name
            self.doc.saveAs(filename)
            App.closeDocument(self.doc.Name)
            self.doc = App.openDocument(filename, hidden=True)
            self.doc.recompute()
            loaded = self.doc.getObject(fillet_name)
            self.assertTrue(loaded.Shape.isValid())
            self.assertAlmostEqual(loaded.Shape.Volume, after_edit, places=4)
            self.assertEqual(
                self.doc.getObject(plate_name).Source[0],
                self.doc.getObject(sketch_name),
            )
            self.assertIsNotNone(self.doc.getObject(hole_name))
            self.assertEqual(self.doc.getObject("FixtureBody").Tip, loaded)

    def test_diagonal_and_grid_form_exact_regions(self):
        for lines, expected in (
            (RECT + [(0, 0, 10, 10)], [50, 50]),
            (RECT + [(5, 0, 5, 10), (0, 5, 10, 5)], [25] * 4),
            (RECT + [(5, 5, 5, 10)], [100]),
        ):
            source = sketch(self.doc, lines)
            result = profiles.regions(source)
            self.assertEqual(len(result), len(expected))
            for region, area in zip(result, expected):
                self.assertAlmostEqual(region.face.Area, area, places=7)
                self.assertTrue(region.face.isValid())

    def test_overlap_and_nested_loops_are_separate_regions(self):
        source = sketch(
            self.doc, RECT + [(5, 0, 15, 0), (15, 0, 15, 10), (15, 10, 5, 10), (5, 10, 5, 0)]
        )
        self.assertEqual([round(r.face.Area, 6) for r in profiles.regions(source)], [50, 50, 50])
        circles = sketch(self.doc, [])
        for radius in (10, 5):
            circles.addGeometry(Part.Circle(App.Vector(), App.Vector(0, 0, 1), radius))
        self.doc.recompute()
        regions = profiles.regions(circles)
        self.assertAlmostEqual(regions[0].face.Area, 75 * math.pi)
        self.assertAlmostEqual(regions[1].face.Area, 25 * math.pi)
        self.assertEqual(len(profiles.resolve(circles, [r.descriptor() for r in regions])), 2)

    def test_region_tracks_dimension_changes(self):
        source = sketch(self.doc)
        source.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 2))
        constraint = source.addConstraint(Sketcher.Constraint("Radius", 4, 2.0))
        self.doc.recompute()
        region = profiles.regions(source)[0]
        key = region.descriptor()
        source.setDatum(constraint, App.Units.Quantity("3 mm"))
        self.doc.recompute()
        resolved = profiles.resolve(source, [key])[0]
        self.assertAlmostEqual(resolved.face.Area, 100 - 9 * math.pi)

    def test_open_sketch_has_actionable_error(self):
        with self.assertRaisesRegex(profiles.ProfileError, "closed"):
            profiles.regions(sketch(self.doc, RECT[:3]))

    def test_profile_selection_and_expression_are_parametric(self):
        source = sketch(self.doc)
        source.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 2))
        self.doc.recompute()
        region = profiles.regions(source)[0]
        op = operations.Operation(self.doc)
        result = op.update(
            {
                "source": (source, []),
                "regions": [region.descriptor()],
                "operation": "New body",
                "distance": "10 mm + 2 mm",
            }
        )[0]
        op.accept()
        self.assertAlmostEqual(result.Shape.Volume, (100 - 4 * math.pi) * 12)
        result.Length = 9
        result.setExpression("Length", None)
        self.doc.recompute()
        self.assertAlmostEqual(result.Shape.Volume, (100 - 4 * math.pi) * 9)

    def test_disconnected_join_is_refused_before_creating_a_temporary_tip(self):
        body, source, base = self.base()
        detached = sketch(self.doc, [], body=body, name="Disconnected", z=6)
        detached.addGeometry(
            Part.Circle(App.Vector(50, 50, 0), App.Vector(0, 0, 1), 1)
        )
        self.doc.recompute()
        region = profiles.regions(detached)[0]
        names_before = {o.Name for o in self.doc.Objects}
        tip_before = body.Tip
        op = operations.Operation(self.doc)
        with self.assertRaisesRegex(features.DesignError, "Join adds no material"):
            op.update({
                "source": (detached, []),
                "regions": [region.descriptor()],
                "operation": "Join",
                "target": body,
                "distance": "3 mm",
            })
        # The preflight calculator may run, but the real FreeCAD document
        # must never receive a temporary FeaturePython result.
        self.assertEqual(names_before, {o.Name for o in self.doc.Objects})
        self.assertEqual(body.Tip, tip_before)
        self.assertAlmostEqual(body.Shape.Volume, 600)
        op.cancel()

    def test_disconnected_cut_does_not_mutate_existing_body(self):
        body, source, base = self.base()
        detached = sketch(self.doc, [], body=body, name="NoIntersection", z=6)
        detached.addGeometry(
            Part.Circle(App.Vector(40, 40, 0), App.Vector(0, 0, 1), 1)
        )
        self.doc.recompute()
        before = {o.Name for o in self.doc.Objects}
        op = operations.Operation(self.doc)
        with self.assertRaises(features.DesignError):
            op.update({
                "source": (detached, []),
                "regions": [profiles.regions(detached)[0].descriptor()],
                "operation": "Cut",
                "target": body,
                "distance": "2 mm",
            })
        self.assertEqual(before, {o.Name for o in self.doc.Objects})
        self.assertIs(body.Tip, base)
        self.assertAlmostEqual(body.Shape.Volume, 600)
        op.cancel()

    def test_failed_new_extrude_preview_restores_original_solid_and_recovers(self):
        """Video regression: bad multi-region Join must not empty Body Tip."""
        body, source, base = self.base()
        before_objects = {o.Name for o in self.doc.Objects}
        # This circle is in the same Body but lies well outside the solid.
        # An Intersect with that detached tool must fail (null result).
        detached = sketch(self.doc, [], body=body, z=6)
        detached.addGeometry(
            Part.Circle(App.Vector(50, 50, 0), App.Vector(0, 0, 1), 1)
        )
        self.doc.recompute()
        before_objects = {o.Name for o in self.doc.Objects}
        region = profiles.regions(detached)[0]
        op = operations.Operation(self.doc)
        with self.assertRaises(features.DesignError):
            op.update({
                "source": (detached, []),
                "regions": [region.descriptor()],
                "operation": "Intersect",
                "target": body,
                "distance": "2 mm",
            })
        op.discard_preview()
        self.assertIs(body.Tip, base)
        self.assertAlmostEqual(body.Shape.Volume, 600)
        self.assertEqual({o.Name for o in self.doc.Objects}, before_objects)
        # A new valid preview can still be made in the same transaction.
        result = op.update({
            "source": (base, [top_face(base)]),
            "operation": "Join",
            "target": body,
            "distance": "2 mm",
        })[0]
        self.assertAlmostEqual(result.Shape.Volume, 800)
        op.accept()
        self.assertIs(body.Tip, result)
        self.assertAlmostEqual(body.Shape.Volume, 800)

    def test_switching_off_valid_extrude_preview_restores_body_before_cancel(self):
        body, source, base = self.base()
        op = operations.Operation(self.doc)
        obj = op.update({
            "source": (base, [top_face(base)]),
            "operation": "Join",
            "target": body,
            "distance": "2 mm",
        })[0]
        self.assertAlmostEqual(body.Shape.Volume, 800)
        temporary_name = obj.Name
        op.discard_preview()
        self.assertIsNone(self.doc.getObject(temporary_name))
        self.assertIs(body.Tip, base)
        self.assertAlmostEqual(body.Shape.Volume, 600)
        op.cancel()
        self.assertAlmostEqual(body.Shape.Volume, 600)

    def test_join_cut_and_intersect_switch_in_one_preview(self):
        body, source, base = self.base()
        names = [o.Name for o in self.doc.Objects]
        op = operations.Operation(self.doc)
        spec = {
            "source": (base, [top_face(base)]),
            "target": body,
            "distance": "2 mm",
            "operation": "Join",
        }
        self.assertAlmostEqual(op.update(spec)[0].Shape.Volume, 800)
        spec["operation"] = "Cut"
        self.assertAlmostEqual(op.update(spec)[0].Shape.Volume, 400)
        spec.update(operation="Intersect", reversed=True)
        self.assertAlmostEqual(op.update(spec)[0].Shape.Volume, 200)
        op.cancel()
        self.assertEqual(names, [o.Name for o in self.doc.Objects])
        self.assertEqual(body.Tip, base)

    def test_edit_operation_keeps_feature_identity(self):
        body, source, base = self.base()
        op = operations.Operation(self.doc)
        result = op.update(
            {
                "source": (base, [top_face(base)]),
                "target": body,
                "distance": "2 mm",
                "operation": "Join",
            }
        )[0]
        op.accept()
        name = result.Name
        edit = operations.Operation(self.doc, result)
        spec = operations.spec_for(result)
        spec["operation"] = "Cut"
        edit.update(spec)
        edit.accept()
        self.assertEqual(result.Name, name)
        self.assertAlmostEqual(result.Shape.Volume, 400)

    def test_new_body_reuses_empty_sketch_body(self):
        body = self.doc.addObject("PartDesign::Body", "Body")
        source = sketch(self.doc, body=body)
        op = operations.Operation(self.doc)
        result = op.update(
            {
                "source": (source, []),
                "whole": True,
                "target": body,
                "operation": "New body",
                "distance": "2 mm",
            }
        )[0]
        self.assertEqual(features.owner_body(result), body)
        self.assertEqual(sum(o.isDerivedFrom("PartDesign::Body") for o in self.doc.Objects), 1)
        op.accept()

    def test_new_body_extrude_can_depend_on_sketch_inside_another_body(self):
        original_body, source, base = self.base()
        operation = operations.Operation(self.doc)
        result = operation.update(
            {
                "source": (source, []),
                "whole": True,
                "operation": "New body",
                "distance": "4 mm",
            }
        )[0]
        new_body = features.owner_body(result)
        self.assertIsNot(new_body, original_body)
        self.assertEqual(result.getTypeIdOfProperty("Source"), "App::PropertyLinkSubGlobal")
        self.assertEqual(result.getTypeIdOfProperty("SourceFrame"), "App::PropertyLinkGlobal")
        self.assertEqual(result.Source[0], source)
        self.assertEqual(result.SourceFrame, original_body)
        self.assertEqual(result.Error, "")
        self.assertAlmostEqual(result.Shape.Volume, 400)
        operation.accept()
        self.doc.recompute()
        self.assertNotIn("Invalid", result.State)
        self.assertAlmostEqual(new_body.Shape.Volume, 400)

    def test_edit_older_extrude_migrates_local_links_and_cancel_restores_them(self):
        source_body, source, first = self.base()
        target = self.doc.addObject("PartDesign::Body", "Other")
        obj = features.create_extrude(target, (source, []), whole=True,
                                      operation="New body")
        obj.Length = 3
        self.doc.recompute()
        name = obj.Name
        # Simulate a 0.4.1 saved feature whose local Source reaches
        # into another Body and raises the allowed-scope warning.
        current = obj.Source
        obj.removeProperty("Source")
        obj.addProperty("App::PropertyLinkSub", "Source", "Profiles")
        obj.Source = current
        self.assertEqual(obj.getTypeIdOfProperty("Source"), "App::PropertyLinkSub")
        edit = operations.Operation(self.doc, obj)
        self.assertEqual(obj.getTypeIdOfProperty("Source"), "App::PropertyLinkSubGlobal")
        self.assertEqual(obj.Source[0], source)
        edit.cancel()
        restored = self.doc.getObject(name)
        self.assertEqual(restored.getTypeIdOfProperty("Source"), "App::PropertyLinkSub")
        self.assertEqual(restored.Source[0], source)

    def test_edit_older_extrude_commits_global_link_scope_with_same_geometry(self):
        body, source, base = self.base()
        obj = base
        name = obj.Name
        original = obj.Shape.Volume
        old_source = obj.Source
        obj.removeProperty("Source")
        obj.addProperty("App::PropertyLinkSub", "Source", "Profiles")
        obj.Source = old_source
        edit = operations.Operation(self.doc, obj)
        self.assertEqual(obj.getTypeIdOfProperty("Source"), "App::PropertyLinkSubGlobal")
        edit.update(operations.spec_for(obj))
        edit.accept()
        current = self.doc.getObject(name)
        self.assertEqual(current.getTypeIdOfProperty("Source"), "App::PropertyLinkSubGlobal")
        self.assertEqual(current.Source[0], source)
        self.assertAlmostEqual(current.Shape.Volume, original)

    def test_disconnected_profiles_create_separate_bodies(self):
        source = sketch(
            self.doc, RECT + [(20, 0, 30, 0), (30, 0, 30, 10), (30, 10, 20, 10), (20, 10, 20, 0)]
        )
        selected = [r.descriptor() for r in profiles.regions(source)]
        op = operations.Operation(self.doc)
        outputs = op.update(
            {
                "source": (source, []),
                "regions": selected,
                "operation": "New body",
                "distance": "2 mm",
            }
        )
        self.assertEqual(len(outputs), 2)
        self.assertNotEqual(features.owner_body(outputs[0]), features.owner_body(outputs[1]))
        self.assertEqual([round(o.Shape.Volume) for o in outputs], [200, 200])
        op.accept()

    def test_symmetric_two_sided_and_start_offset(self):
        body, source, obj = self.base()
        obj.Direction = "Symmetric"
        self.doc.recompute()
        self.assertAlmostEqual(obj.Shape.BoundBox.ZMin, -3)
        self.assertAlmostEqual(obj.Shape.BoundBox.ZMax, 3)
        obj.Direction = "Two sides"
        obj.Length = 4
        obj.Length2 = 2
        self.doc.recompute()
        self.assertAlmostEqual(obj.Shape.BoundBox.ZMin, -2)
        self.assertAlmostEqual(obj.Shape.BoundBox.ZMax, 4)
        obj.Direction = "One side"
        obj.StartOffset = 3
        self.doc.recompute()
        self.assertAlmostEqual(obj.Shape.BoundBox.ZMin, 3)
        self.assertAlmostEqual(obj.Shape.BoundBox.ZMax, 7)

    def test_taper_uses_native_algorithm(self):
        body, source, obj = self.base(height=2)
        obj.TaperAngle = 5
        self.doc.recompute()
        self.assertTrue(obj.Shape.isValid())
        self.assertNotAlmostEqual(obj.Shape.Volume, 200)
        self.assertEqual(obj.Error, "")

    def test_through_all_and_to_face(self):
        body, source, base = self.base()
        circle = sketch(self.doc, [], body=body, z=6)
        circle.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 2))
        self.doc.recompute()
        obj = features.create_extrude(body, (circle, []), whole=True, base=base, operation="Cut")
        obj.Extent = "Through all"
        self.doc.recompute()
        self.assertAlmostEqual(obj.Shape.Volume, 600 - 24 * math.pi)
        target = self.doc.addObject("Part::Feature", "Limit")
        target.Shape = Part.makePlane(100, 100, App.Vector(-20, -20, 10))
        new_body = self.doc.addObject("PartDesign::Body", "NewBody")
        result = features.create_extrude(new_body, (source, []), whole=True, operation="New body")
        result.Extent = "To face"
        result.UpToFace = (target, ["Face1"])
        self.doc.recompute()
        self.assertAlmostEqual(result.Shape.Volume, 1000)

    def test_automatic_inward_cut_and_outward_join(self):
        body, source, base = self.base()
        op = operations.Operation(self.doc)
        spec = {
            "source": (base, [top_face(base)]),
            "target": body,
            "operation": "Auto",
            "distance": "2 mm",
        }
        self.assertEqual(op.update(spec)[0].Operation, "Join")
        spec["distance"] = "-2 mm"
        result = op.update(spec)[0]
        self.assertEqual(result.Operation, "Cut")
        self.assertAlmostEqual(result.Shape.Volume, 400)
        op.cancel()

    def test_undo_redo_and_cancel_are_atomic(self):
        source = sketch(self.doc)
        before = [o.Name for o in self.doc.Objects]
        op = operations.Operation(self.doc)
        spec = {"source": (source, []), "whole": True, "operation": "New body", "distance": "2 mm"}
        op.update(spec)
        op.update(dict(spec, distance="3 mm"))
        op.cancel()
        self.assertEqual(before, [o.Name for o in self.doc.Objects])
        op = operations.Operation(self.doc)
        result = op.update(spec)[0]
        name = result.Name
        op.accept()
        self.doc.undo()
        self.assertIsNone(self.doc.getObject(name))
        self.doc.redo()
        self.doc.recompute()
        self.assertAlmostEqual(self.doc.getObject(name).Shape.Volume, 200)

    def test_feature_reopens_and_recomputes(self):
        body, source, obj = self.base()
        name = obj.Name
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "parametric.FCStd")
            self.doc.saveAs(path)
            App.closeDocument(self.doc.Name)
            self.doc = App.openDocument(path, hidden=True)
            obj = self.doc.getObject(name)
            obj.Length = 7
            self.doc.recompute()
            self.assertEqual(obj.Error, "")
            self.assertAlmostEqual(obj.Shape.Volume, 700)
            self.assertFalse(any(name.startswith("AzGeometry") for name in App.listDocuments()))

    def test_real_rollback_and_feature_insertion(self):
        body, source, base = self.base()
        result = features.create_extrude(body, (base, [top_face(base)]), base=base)
        result.Length = 2
        self.doc.recompute()
        history.rollback(base)
        self.assertEqual(body.Tip, base)
        self.assertAlmostEqual(body.Shape.Volume, 600)
        op = operations.Operation(self.doc)
        inserted = op.update(
            {
                "source": (base, [top_face(base)]),
                "target": body,
                "operation": "Join",
                "distance": "1 mm",
            }
        )[0]
        op.accept()
        self.assertEqual(result.BaseFeature, inserted)
        history.end(body)
        self.assertEqual(body.Tip, result)
        # The downstream face reference remains explicitly anchored to base.
        self.assertAlmostEqual(body.Shape.Volume, 800)
        base.Length = 7
        self.doc.recompute()
        self.assertAlmostEqual(body.Shape.Volume, 900)

    def test_quick_dimension_changes_native_parametric_feature_and_undo(self):
        body, source, pad = self.base(height=6)
        name, value = quick_dimension.dimension_value(pad)
        self.assertEqual((name, value), ("Length", 6.0))
        new_value = quick_dimension.change_dimension(pad, 8)
        self.assertEqual(new_value, 8)
        self.assertAlmostEqual(body.Shape.Volume, 800)
        self.assertEqual(pad.Length.Value, 8)
        feature_name = pad.Name
        self.doc.undo()
        self.doc.recompute()
        restored = self.doc.getObject(feature_name)
        self.assertAlmostEqual(restored.Length.Value, 6)
        self.assertAlmostEqual(body.Shape.Volume, 600)

    def test_quick_dimension_rejects_zero_without_modifying_feature(self):
        body, source, pad = self.base(height=6)
        with self.assertRaisesRegex(features.DesignError, "between"):
            quick_dimension.change_dimension(pad, 0)
        self.assertEqual(pad.Length.Value, 6)
        self.assertAlmostEqual(body.Shape.Volume, 600)

    def test_history_scrubber_moves_native_tip_and_resumes_latest(self):
        body, source, base = self.base()
        second = features.create_extrude(
            body, (base, [top_face(base)]), base=base
        )
        second.Length = 2
        self.doc.recompute()
        self.assertEqual(body.Tip, second)
        entries, index, rolled = history.history_position(body)
        self.assertEqual(index, len(entries) - 1)
        self.assertFalse(rolled)
        history.move_history_marker(body, 0)
        self.assertEqual(body.Tip, base)
        self.assertTrue(history.history_position(body)[2])
        history.move_history_marker(body, len(entries) - 1)
        self.assertEqual(body.Tip, second)
        self.assertFalse(history.history_position(body)[2])
        self.assertAlmostEqual(body.Shape.Volume, 800)

    def test_dependency_inspector_uses_real_freecad_links(self):
        body, source, base = self.base()
        next_feature = features.create_extrude(
            body, (base, [top_face(base)]), base=base
        )
        next_feature.Length = 2
        self.doc.recompute()
        deps = history.dependents(base)
        self.assertIn(next_feature, deps)
        self.assertNotIn(body, deps)
        self.assertEqual(history.dependents(next_feature), [])

    def test_source_body_placement_recomputes_a_separate_body(self):
        body, source, base = self.base()
        body.Placement = App.Placement(
            App.Vector(20, 30, 40), App.Rotation(App.Vector(0, 1, 0), 90)
        )
        self.doc.recompute()
        other = self.doc.addObject("PartDesign::Body", "Other")
        other.Placement.Base = App.Vector(-5, 0, 0)
        obj = features.create_extrude(other, (source, []), whole=True, operation="New body")
        obj.Length = 3
        self.doc.recompute()
        self.assertEqual(obj.Error, "")
        self.assertAlmostEqual(obj.Shape.Volume, 300)
        # Global-scoped links are required when Extrude is in another Body.
        # Local-only LinkSub emitted 'go out of the allowed scope' on FreeCAD
        # 1.1, even when the solid happened to render correctly.
        self.assertEqual(obj.getTypeIdOfProperty("Source"), "App::PropertyLinkSubGlobal")
        self.assertEqual(obj.getTypeIdOfProperty("UpToFace"), "App::PropertyLinkSubGlobal")
        self.assertEqual(obj.getTypeIdOfProperty("SourceFrame"), "App::PropertyLinkGlobal")
        self.assertEqual(obj.getTypeIdOfProperty("LimitFrame"), "App::PropertyLinkGlobal")
        self.assertEqual(obj.Source[0], source)
        self.assertEqual(obj.SourceFrame, body)
        before = other.Shape.CenterOfMass + other.Placement.Base
        body.Placement.Base.x += 7
        self.doc.recompute()
        after = other.Shape.CenterOfMass + other.Placement.Base
        self.assertAlmostEqual(after.x - before.x, 7)

    def test_presspull_resizes_a_tapered_end_cap(self):
        body, source, obj = self.base()
        obj.TaperAngle = 5
        self.doc.recompute()
        face = obj.Shape.getElement(top_face(obj))
        edit = presspull.DimensionEdit(presspull.cap_binding(obj, face))
        edit.update("2 mm")
        edit.accept()
        self.assertAlmostEqual(obj.Length.Value, 8)
        self.assertEqual(obj.TaperAngle.Value, 5)
        self.assertTrue(obj.Shape.isValid())
        self.doc.undo()
        self.doc.recompute()
        self.assertAlmostEqual(obj.Length.Value, 6)

    def test_presspull_rejects_unsafe_face_prisms(self):
        body, source, obj = self.base()
        presspull.require_prismatic(obj, obj.Shape.getElement(top_face(obj)))
        obj.TaperAngle = 7
        self.doc.recompute()
        with self.assertRaisesRegex(features.DesignError, "sloped"):
            presspull.require_prismatic(obj, obj.Shape.getElement(top_face(obj)))

    def test_cylinder_diameter_edits_its_driving_sketch(self):
        body = self.doc.addObject("PartDesign::Body", "Body")
        source = sketch(self.doc, [], body=body)
        source.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 2))
        index = source.addConstraint(Sketcher.Constraint("Radius", 0, 2.0))
        obj = features.create_extrude(body, (source, []), whole=True, operation="New body")
        obj.Length = 5
        self.doc.recompute()
        face = next(f for f in obj.Shape.Faces if isinstance(f.Surface, Part.Cylinder))
        binding = presspull.cylinder_binding(obj, face)
        edit = presspull.DimensionEdit(binding)
        edit.update("10 mm")
        self.assertAlmostEqual(source.getDatum(index).Value, 5)
        self.assertAlmostEqual(obj.Shape.Volume, 125 * math.pi)
        edit.cancel()
        self.assertAlmostEqual(source.getDatum(index).Value, 2)

    def test_unconstrained_circle_gets_a_cancellable_dimension(self):
        body = self.doc.addObject("PartDesign::Body", "Body")
        source = sketch(self.doc, [], body=body)
        source.addGeometry(Part.Circle(App.Vector(), App.Vector(0, 0, 1), 2))
        obj = features.create_extrude(body, (source, []), whole=True, operation="New body")
        self.doc.recompute()
        face = next(f for f in obj.Shape.Faces if isinstance(f.Surface, Part.Cylinder))
        edit = presspull.DimensionEdit(presspull.cylinder_binding(obj, face))
        edit.update("6 mm")
        self.assertEqual(source.ConstraintCount, 1)
        edit.cancel()
        self.assertEqual(source.ConstraintCount, 0)

    def test_user_parameters_drive_dimensions_and_cancel_atomically(self):
        body, source, obj = self.base()
        edit = parameters.ParameterEdit(self.doc)
        edit.update(
            [("Thickness", "8 mm"), ("Half", "=Thickness / 2")],
            [(obj, "Length", "Parameters.Half")],
        )
        self.assertAlmostEqual(obj.Length.Value, 4)
        self.assertAlmostEqual(obj.Shape.Volume, 400)
        edit.update([("Thickness", "12 mm"), ("Half", "=Thickness / 2")])
        self.assertAlmostEqual(obj.Shape.Volume, 600)
        edit.accept()
        second = parameters.ParameterEdit(self.doc)
        second.update([("Thickness", "20 mm")])
        self.assertAlmostEqual(obj.Shape.Volume, 1000)
        second.cancel()
        self.assertAlmostEqual(obj.Shape.Volume, 600)
        self.assertEqual(len(parameters.user_parameters(self.doc)), 2)

    def test_parameter_names_and_duplicate_aliases_are_validated(self):
        edit = parameters.ParameterEdit(self.doc)
        for values in (("1Bad", "2 mm"), ("two words", "3 mm")):
            with self.assertRaises(features.DesignError):
                edit.update([values])
        with self.assertRaisesRegex(features.DesignError, "unique"):
            edit.update([("Width", "2 mm"), ("Width", "3 mm")])
        edit.cancel()

    def test_suppression_passes_through_the_actual_base(self):
        body, source, base = self.base()
        obj = features.create_extrude(body, (base, [top_face(base)]), base=base)
        obj.Length = 2
        self.doc.recompute()
        obj.Suppressed = True
        self.doc.recompute()
        self.assertAlmostEqual(obj.Shape.Volume, 600)
        obj.Suppressed = False
        self.doc.recompute()
        self.assertAlmostEqual(obj.Shape.Volume, 800)

    def test_upstream_extrude_edit_under_native_fillet_preserves_final_tip(self):
        body, source, plate = self.base(height=6)
        rounding = body.newObject("PartDesign::Fillet", "Rounding")
        rounding.Base = (plate, ["Edge1"])
        rounding.Radius = 0.5
        self.doc.recompute()
        self.assertTrue(rounding.Shape.isValid())
        initial = rounding.Shape.Volume
        edit = operations.Operation(self.doc, editing=plate)
        spec = operations.spec_for(plate)
        spec["distance"] = "8 mm"
        edit.update(spec)
        self.assertIs(body.Tip, plate)
        edit.accept()
        self.assertIs(body.Tip, rounding)
        self.assertTrue(rounding.Shape.isValid())
        grown = rounding.Shape.Volume
        self.assertGreater(grown, initial + 180)
        again = operations.Operation(self.doc, editing=plate)
        reset = operations.spec_for(plate)
        reset["distance"] = "5 mm"
        again.update(reset)
        again.cancel()
        self.assertIs(body.Tip, rounding)
        self.assertAlmostEqual(rounding.Shape.Volume, grown, places=4)

    def test_native_fillet_recomputes_after_custom_extrude_edits(self):
        body, source, base = self.base()
        fillet = body.newObject("PartDesign::Fillet", "Fillet")
        fillet.Base = (base, ["Edge1"])
        fillet.Radius = 0.5
        self.doc.recompute()
        self.assertFalse(fillet.Shape.isNull())
        self.assertTrue(fillet.Shape.isValid())
        self.assertLess(fillet.Shape.Volume, 600)
        base.Length = 8
        self.doc.recompute()
        self.assertNotIn("Invalid", fillet.State)
        self.assertTrue(fillet.Shape.isValid())
        self.assertGreater(fillet.Shape.Volume, 700)

    def test_native_hole_preview_reveals_base_and_cancels_cleanly(self):
        body, source, base = self.base()
        centers = sketch(self.doc, [], body=body, z=6)
        centers.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 2))
        self.doc.recompute()
        original_tip = body.Tip
        original_objects = {o.Name for o in self.doc.Objects}
        op = HoleOperation(self.doc, centers)
        volume = op.preview(HoleSpec(diameter=3, depth=6, through_all=True))
        self.assertLess(volume, base.Shape.Volume)
        self.assertTrue(op.hole.Shape.isValid())
        self.assertFalse(op.hole.ModelThread)
        self.assertEqual(body.Tip, op.hole)
        op.show_base()
        self.assertEqual(body.Tip, original_tip)
        self.assertTrue(op.show_result())
        self.assertEqual(body.Tip, op.hole)
        op.cancel()
        self.assertEqual(body.Tip, original_tip)
        self.assertEqual({o.Name for o in self.doc.Objects}, original_objects)

    def test_native_cosmetic_thread_metadata_without_helical_geometry(self):
        body, source, base = self.base()
        centers = sketch(self.doc, [], body=body, z=6)
        centers.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 2))
        self.doc.recompute()
        op = HoleOperation(self.doc, centers)
        op._start()
        options = thread_sizes(op.hole, "ISOMetricProfile")
        self.assertTrue(options)
        result = op.preview(HoleSpec(diameter=3, depth=6, through_all=True,
                                     thread_type="ISOMetricProfile", thread_size=options[0]))
        self.assertLess(result, base.Shape.Volume)
        self.assertTrue(op.hole.Threaded)
        self.assertFalse(op.hole.ModelThread)
        op.cancel()

    def test_native_threaded_hole_edit_is_transactional_and_cancel_restores_it(self):
        body, source, base = self.base()
        centers = sketch(self.doc, [], body=body, z=6)
        centers.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 2))
        self.doc.recompute()
        create = HoleOperation(self.doc, centers)
        create._start()
        sizes = thread_sizes(create.hole, "ISOMetricProfile")
        self.assertTrue(sizes)
        settings = HoleSpec(
            diameter=3, depth=6, through_all=True,
            thread_type="ISOMetricProfile", thread_size=sizes[0],
        )
        self.assertLess(create.preview(settings), base.Shape.Volume)
        native = create.accept()
        original_volume = native.Shape.Volume
        original_depth_mode = str(native.DepthType)
        self.assertFalse(native.ModelThread)

        edit = HoleOperation(self.doc, centers, editing=native)
        self.assertFalse(edit.started)  # Just opening the editor never mutates.
        new_settings = HoleSpec(
            diameter=3, depth=2, through_all=False,
            thread_type="ISOMetricProfile", thread_size=sizes[0],
        )
        changed_volume = edit.preview(new_settings)
        self.assertLess(changed_volume, base.Shape.Volume)
        self.assertNotAlmostEqual(changed_volume, original_volume, places=5)
        self.assertEqual(body.Tip, native)
        edit.cancel()
        restored = self.doc.getObject(native.Name)
        self.assertIsNotNone(restored)
        self.assertEqual(str(restored.DepthType), original_depth_mode)
        self.assertAlmostEqual(restored.Shape.Volume, original_volume, places=5)

    def test_timeline_delete_last_hole_preserves_base_and_undo(self):
        body, source, base = self.base()
        centers = sketch(self.doc, [], body=body, z=6)
        centers.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 1))
        self.doc.recompute()
        operation = HoleOperation(self.doc, centers)
        operation.preview(HoleSpec(diameter=2, depth=6, through_all=True))
        hole = operation.accept()
        name = hole.Name
        self.assertLess(body.Shape.Volume, base.Shape.Volume)
        self.assertEqual(history.deletion_plan(hole)[1], [hole])
        history.delete_feature(hole)
        self.assertIsNone(self.doc.getObject(name))
        self.assertEqual(body.Tip, base)
        self.assertAlmostEqual(body.Shape.Volume, 600)
        self.doc.undo()
        self.doc.recompute()
        self.assertIsNotNone(self.doc.getObject(name))
        self.assertAlmostEqual(body.Shape.Volume, 600 - 6 * math.pi, places=3)

    def test_timeline_middle_feature_delete_requires_explicit_branch(self):
        body, source, base = self.base()
        centers = sketch(self.doc, [], body=body, z=6)
        centers.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 1))
        self.doc.recompute()
        operation = HoleOperation(self.doc, centers)
        operation.preview(HoleSpec(diameter=2, depth=6, through_all=True))
        hole = operation.accept()
        boss_profile = sketch(self.doc, [], body=body, z=6)
        boss_profile.addGeometry(Part.Circle(App.Vector(2, 2, 0), App.Vector(0, 0, 1), 1))
        boss = body.newObject("PartDesign::Pad", "Boss")
        boss.Profile = boss_profile
        boss.Length = 2
        self.doc.recompute()
        self.assertTrue(boss.Shape.isValid())
        self.assertEqual(boss.BaseFeature, hole)
        with self.assertRaisesRegex(features.DesignError, "still depends"):
            history.deletion_plan(hole)
        _body, plan, _tip = history.deletion_plan(hole, cascade=True)
        self.assertEqual([obj.Name for obj in plan], [hole.Name, boss_profile.Name, boss.Name])
        hole_name, boss_name = hole.Name, boss.Name
        history.delete_feature(hole, cascade=True)
        self.assertEqual(body.Tip, base)
        self.assertAlmostEqual(body.Shape.Volume, 600)
        self.assertIsNone(self.doc.getObject(hole_name))
        self.assertIsNone(self.doc.getObject(boss_name))

    def test_edit_middle_hole_restores_latest_solid_and_cancel_reverts(self):
        body, source, base = self.base()
        centers = sketch(self.doc, [], body=body, z=6)
        centers.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 1))
        self.doc.recompute()
        operation = HoleOperation(self.doc, centers)
        operation.preview(HoleSpec(diameter=2, depth=6, through_all=True))
        hole = operation.accept()
        boss_profile = sketch(self.doc, [], body=body, z=6)
        boss_profile.addGeometry(Part.Circle(App.Vector(2, 2, 0), App.Vector(0, 0, 1), 1))
        boss = body.newObject("PartDesign::Pad", "Boss")
        boss.Profile = boss_profile
        boss.Length = 2
        self.doc.recompute()
        original = boss.Shape.Volume
        edit = HoleOperation(self.doc, centers, editing=hole)
        self.assertEqual(body.Tip, boss)
        edit.preview(HoleSpec(diameter=3, depth=6, through_all=True))
        self.assertEqual(body.Tip, hole)
        edit.accept()
        self.assertEqual(body.Tip, boss)
        self.assertTrue(boss.Shape.isValid())
        self.assertLess(boss.Shape.Volume, original)
        later_volume = boss.Shape.Volume
        second = HoleOperation(self.doc, centers, editing=hole)
        second.preview(HoleSpec(diameter=4, depth=6, through_all=True))
        second.cancel()
        self.assertEqual(body.Tip, boss)
        self.assertAlmostEqual(boss.Shape.Volume, later_volume, places=5)

    def test_native_pad_can_follow_an_az_feature(self):
        body, source, base = self.base()
        circle = sketch(self.doc, [], body=body, z=6)
        circle.addGeometry(Part.Circle(App.Vector(5, 5, 0), App.Vector(0, 0, 1), 2))
        self.doc.recompute()
        pad = body.newObject("PartDesign::Pad", "Pad")
        pad.Profile = circle
        pad.Length = 3
        self.doc.recompute()
        self.assertTrue(pad.Shape.isValid())
        self.assertEqual(pad.BaseFeature, base)
        self.assertAlmostEqual(pad.Shape.Volume, 600 + 12 * math.pi)


if __name__ == "__main__":
    unittest.main()
