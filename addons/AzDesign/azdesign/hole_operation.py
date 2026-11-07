# SPDX-License-Identifier: LGPL-2.1-or-later
"""Transactional native Hole creation; a failed result never hides the base."""

import FreeCAD as App
from . import features
from .hole_spec import HoleSpec


def hole_profile_sketch(hole):
    """Resolve FreeCAD's Profile link or LinkSub to the sketch object.

    Native PartDesign features may expose Profile directly or as a tuple
    (sketch, subelement names). Test the sketch itself, never the raw tuple.
    """
    profile = getattr(hole, "Profile", None)
    if isinstance(profile, (tuple, list)):
        if not profile:
            return None
        profile = profile[0]
    if profile and hasattr(profile, "isDerivedFrom") and profile.isDerivedFrom(
        "Sketcher::SketchObject"
    ):
        return profile
    return None


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
            if not editing.isDerivedFrom("PartDesign::Hole") or hole_profile_sketch(editing) != sketch:
                raise features.DesignError("Choose a native Hole associated with this sketch.")
            group = list(self.body.Group)
            if editing not in group:
                raise features.DesignError("This Hole is not in the owning Body history.")
            # The current Tip can be a later feature. Temporarily show this
            # Hole for preview, then resume the prior Tip on accept/cancel.
            # Reject an edit to a feature beyond the currently rolled-back
            # point; don't silently re-enable a different history branch.
            current_tip = self.body.Tip
            if (
                current_tip in group
                and group.index(editing) > group.index(current_tip)
            ):
                raise features.DesignError(
                    "This Hole is beyond the current rollback marker. "
                    "Resume history before editing it."
                )
            # Existing modeled threads are now editable through the same
            # explicitly confirmed and instrumented preview as new holes.
            # Merely opening the edit task must never recompute the feature.
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
        self.last_diagnostic = None
        self.original_model_thread = bool(editing.ModelThread) if editing else False

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
        diagnostic = None
        try:
            if spec.model_thread:
                from .hole_diagnostics import start_for_freecad

                # Create and flush this file BEFORE touching the native model.
                # Even an access violation inside OCCT leaves our last stage.
                diagnostic = start_for_freecad(
                    App, scenario="Az edit existing modeled Hole" if self.editing
                    else "Az create modeled Hole"
                )
                self.last_diagnostic = str(diagnostic.path)
                diagnostic.record_spec("before_transaction", spec)
                App.Console.PrintWarning(
                    "Az modeled-thread experiment log: " + self.last_diagnostic + "\\n"
                )
            self._start()
            self.body.Tip = self.hole
            if diagnostic:
                diagnostic.record_spec("before_property_configuration", spec, feature=self.hole)
            spec.apply(
                self.hole,
                before_model=(
                    lambda: diagnostic.record_spec(
                        "before_model_thread_enable", spec, feature=self.hole
                    )
                ) if diagnostic else None,
            )
            if diagnostic:
                diagnostic.record_spec("before_native_recompute", spec, feature=self.hole)
            self.doc.recompute()
            if diagnostic:
                diagnostic.record_spec("after_native_recompute", spec, feature=self.hole)
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
            if diagnostic:
                diagnostic.record(
                    "valid_solid", volume=float(shape.Volume),
                    solids=len(shape.Solids), valid=True
                )
            self.valid = True
            self.show_result()
            return shape.Volume
        except Exception as exc:
            if diagnostic:
                diagnostic.record("python_exception", error=repr(exc))
            self.valid = False
            self.show_base()
            raise

    def accept(self):
        if self.closed or not self.valid or not self.hole:
            raise features.DesignError("Show a valid Hole result before accepting.")
        self.show_result()
        if self.editing and self.original_tip != self.hole:
            # Recompute the rest of the actual native history, then reject a
            # newly broken downstream solid instead of silently accepting it.
            self.body.Tip = self.original_tip
            self._restore_visibility()
            self.doc.recompute()
            group = list(self.body.Group)
            pos = group.index(self.hole)
            end = group.index(self.original_tip) if self.original_tip in group else len(group) - 1
            failures = []
            for item in group[pos + 1:end + 1]:
                if not item.isDerivedFrom("PartDesign::Feature"):
                    continue
                state = getattr(item, "State", ())
                shape = getattr(item, "Shape", None)
                if (
                    "Invalid" in state
                    or bool(getattr(item, "Error", ""))
                    or not shape
                    or shape.isNull()
                    or not shape.isValid()
                ):
                    failures.append(item.Label)
            if failures:
                # Leave the edit task open, with Cancel able to abort the
                # original transaction. Do not commit this invalid design.
                self.valid = False
                self.show_base()
                raise features.DesignError(
                    "Edited Hole breaks downstream features: "
                    + ", ".join(failures)
                    + ". Cancel to restore the original, or adjust the Hole."
                )
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
