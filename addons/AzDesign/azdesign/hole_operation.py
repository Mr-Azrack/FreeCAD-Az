# SPDX-License-Identifier: LGPL-2.1-or-later
"""Transactional native Hole creation; a failed result never hides the base."""

import FreeCAD as App
from . import features
from .hole_spec import HoleSpec


class HoleOperation:
    def __init__(self, doc, sketch, editing=None):
        if not sketch or not sketch.isDerivedFrom("Sketcher::SketchObject"):
            raise features.DesignError("Select a sketch containing hole centers.")
        if sketch.Document != doc:
            raise features.DesignError("Choose a sketch from the active design.")
        self.doc = doc
        self.sketch = sketch
        self.body = features.owner_body(sketch)
        if self.body is None:
            raise features.DesignError("The hole sketch must belong to a Part Design Body.")
        self.editing = editing
        if editing:
            if not editing.isDerivedFrom("PartDesign::Hole") or editing.Profile != sketch:
                raise features.DesignError("Choose a native Hole associated with this sketch.")
            if self.body.Tip != editing:
                raise features.DesignError(
                    "Editing a Hole with later features is not yet supported in Az. "
                    "Roll back to the Hole first or edit in Native CAD."
                )
            if editing.ModelThread:
                raise features.DesignError(
                    "This Hole contains geometric threads. Open it in Native CAD; "
                    "Az will not recompute crash-prone thread geometry."
                )
        self.base = editing.BaseFeature if editing else features.body_tip(self.body)
        if not self.base or not hasattr(self.base, "Shape") or not self.base.Shape.Solids:
            raise features.DesignError("Create a solid first, then sketch hole centers on its face.")
        if self.base == editing:
            raise features.DesignError("The Hole needs a solid base before this feature.")
        self.original_tip = self.body.Tip
        self.original_visibility = {
            obj.Name: obj.ViewObject.Visibility
            for obj in self.doc.Objects
            if App.GuiUp and obj.ViewObject
        }
        self.hole = editing
        self.started = False
        self.closed = False
        self.valid = False
        self.last_spec = None

    def _start(self):
        if self.started:
            return
        features.begin_transaction(
            self.doc, "Az: Edit Hole" if self.editing else "Az: Hole"
        )
        self.started = True
        if not self.editing:
            # The sketch may have become the Tip; force the preceding solid
            # so that the native Hole inherits the proper subtractive base.
            self.body.Tip = self.base
            self.hole = self.body.newObject("PartDesign::Hole", "Hole")
            self.hole.Profile = self.sketch
            self.hole.ModelThread = False

    def _restore_visibility(self):
        if App.GuiUp:
            for name, visible in self.original_visibility.items():
                obj = self.doc.getObject(name)
                if obj and obj.ViewObject:
                    obj.ViewObject.Visibility = visible

    def show_base(self):
        """Keep a real solid visible even when a preview is invalid or hidden."""
        if self.closed:
            return
        self.body.Tip = self.original_tip
        self._restore_visibility()
        if App.GuiUp:
            self.body.ViewObject.Visibility = True
            self.base.ViewObject.Visibility = True
            if self.hole and self.hole is not self.base:
                self.hole.ViewObject.Visibility = False

    def show_result(self):
        if not self.valid or self.closed or not self.hole:
            self.show_base()
            return False
        self.body.Tip = self.hole
        self._restore_visibility()
        if App.GuiUp:
            self.body.ViewObject.Visibility = True
            self.sketch.ViewObject.Visibility = False
            self.base.ViewObject.Visibility = False
            self.hole.ViewObject.Visibility = True
        return True

    def preview(self, spec):
        if self.closed:
            raise features.DesignError("This Hole operation has finished.")
        if not isinstance(spec, HoleSpec):
            raise features.DesignError("Invalid Hole settings.")
        spec.validate()  # Do not touch the document until input is sane.
        self.valid = False
        try:
            self._start()
            self.body.Tip = self.hole
            spec.apply(self.hole)
            self.doc.recompute()
            shape = self.hole.Shape
            if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
                raise features.DesignError(
                    "The Hole did not produce one valid solid. Check sketch "
                    "placement, centers, diameter and depth."
                )
            if shape.Volume >= self.base.Shape.Volume - 1e-7:
                raise features.DesignError(
                    "The Hole did not remove material. Verify sketch placement "
                    "and direction before accepting."
                )
            self.last_spec = spec
            self.valid = True
            self.show_result()
            return shape.Volume
        except Exception:
            self.valid = False
            self.show_base()
            raise

    def accept(self):
        if self.closed or not self.valid or not self.hole:
            raise features.DesignError("Show a valid Hole result before accepting.")
        self.show_result()
        self.doc.commitTransaction()
        self.closed = True
        return self.hole

    def cancel(self):
        if self.closed:
            return
        self.closed = True
        if self.started:
            self.doc.abortTransaction()
            self.doc.recompute()
        body = self.doc.getObject(self.body.Name)
        if body:
            previous = self.doc.getObject(self.original_tip.Name) if self.original_tip else None
            body.Tip = previous
        self._restore_visibility()
