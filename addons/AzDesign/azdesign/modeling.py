# SPDX-License-Identifier: LGPL-2.1-or-later
"""Model edits use native FreeCAD features, with one transaction per command."""

import math
import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore, QtWidgets
from .compat import set_extrusion_sides


class ModelingError(ValueError):
    """An actionable modeling precondition was not met."""


def current_document():
    """Return the user's visible document, not an App-only calculation document."""
    gui_doc = Gui.activeDocument()
    return gui_doc.Document if gui_doc and gui_doc.activeView() else None


def document():
    doc = current_document()
    if doc is None:
        doc = App.newDocument("Design", hidden=False, temp=False)
    if App.ActiveDocument != doc:
        App.setActiveDocument(doc.Name)
    return doc


def in_sketch():
    gui_doc = Gui.activeDocument()
    editing = gui_doc.getInEdit() if gui_doc else None
    obj = getattr(editing, "Object", None)
    return obj if obj and obj.isDerivedFrom("Sketcher::SketchObject") else None


def body_of(obj):
    return next((parent for parent in obj.InList if parent.isDerivedFrom("PartDesign::Body")), None)


def active_body():
    gui_doc = Gui.activeDocument()
    if not gui_doc:
        return None
    view = gui_doc.activeView()
    if not view:
        return None
    doc = gui_doc.Document
    for obj in Gui.Selection.getSelection():
        if obj.Document != doc:
            continue
        if obj.isDerivedFrom("PartDesign::Body"):
            return obj
        body = body_of(obj)
        if body:
            return body
    return view.getActiveObject("pdbody") if hasattr(view, "getActiveObject") else None


def new_body():
    if Gui.Control.activeDialog():
        raise ModelingError("Finish or cancel the current operation before creating a body.")
    doc = document()
    doc.openTransaction("Az: New body")
    try:
        body = doc.addObject("PartDesign::Body", "Body")
        doc.recompute()
        Gui.activeDocument().activeView().setActiveObject("pdbody", body)
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(body)
        doc.commitTransaction()
        return body
    except Exception:
        doc.abortTransaction()
        raise


def create_sketch(support=None, plane=None):
    """Start a native sketch after canvas-based plane/face selection.

    A preselected planar face is accepted immediately. Otherwise the
    nonmodal picker lets users click an origin plane or model face.
    Nothing is created until they select a valid target.
    """
    if Gui.Control.activeDialog():
        raise ModelingError("Finish or cancel the current operation first.")
    doc = current_document()
    if not doc:
        doc = document()
    body = active_body()
    if not body:
        bodies = [obj for obj in doc.Objects if obj.isDerivedFrom("PartDesign::Body")]
        if len(bodies) > 1:
            raise ModelingError("Select the body to sketch in, then choose Create Sketch.")
        body = bodies[0] if bodies else None
    if support is None and plane is None:
        for selection in Gui.Selection.getSelectionEx():
            if selection.Object.Document != doc:
                continue
            for name, shape in zip(selection.SubElementNames, selection.SubObjects):
                if name.startswith("Face"):
                    import Part
                    if not isinstance(shape.Surface, Part.Plane):
                        raise ModelingError("Select a flat face for your sketch.")
                    support = (selection.Object, [name])
                    break
            if support:
                break
            # An edge does not uniquely define a sketch plane. If it borders
            # exactly one planar face, reuse that face; at a corner with two
            # plausible faces, leave the in-canvas plane picker active rather
            # than silently choosing the wrong support.
            for edge_name, subshape in zip(selection.SubElementNames, selection.SubObjects):
                if not edge_name.startswith("Edge"):
                    continue
                import Part
                faces = selection.Object.Shape.ancestorsOfType(subshape, Part.Face)
                planar = [face for face in faces if isinstance(face.Surface, Part.Plane)]
                if len(planar) != 1:
                    continue
                for number, candidate in enumerate(selection.Object.Shape.Faces, 1):
                    if candidate.isSame(planar[0]):
                        support = (selection.Object, ["Face" + str(number)])
                        break
                if support:
                    break
            if support:
                break
    if support is None and plane is None:
        from .sketch_plane_picker import show
        show()
        return None
    if plane is not None and plane not in ("XY", "XZ", "YZ"):
        raise ModelingError("Select XY, XZ, or YZ for an origin sketch.")
    doc.openTransaction("Design: Create sketch")
    try:
        if body is None:
            body = doc.addObject("PartDesign::Body", "Body")
        if support is None:
            role = plane + "_Plane"
            origin = getattr(body, "Origin", None)
            if origin is None:
                raise ModelingError("Active body has no origin planes.")
            origin_planes = [obj for obj in origin.OriginFeatures if obj.Role == role]
            if not origin_planes:
                raise ModelingError("Origin plane " + plane + " is unavailable.")
            support = (origin_planes[0], [""])
        sketch = body.newObject("Sketcher::SketchObject", "Sketch")
        property_name = (
            "AttachmentSupport" if "AttachmentSupport" in sketch.PropertiesList else "Support"
        )
        setattr(sketch, property_name, support)
        sketch.MapMode = "FlatFace"
        doc.recompute()
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise
    Gui.activeDocument().activeView().setActiveObject("pdbody", body)
    edit_sketch(sketch)
    return sketch


def edit_sketch(sketch):
    """Avoid Sketcher's workbench jump without persisting an Az dependency."""
    view_object = sketch.ViewObject
    previous = view_object.EditingWorkbench
    try:
        view_object.EditingWorkbench = ""
        from .session import current

        session = current()
        if session:
            session.appearance.fit(lambda: Gui.activeDocument().setEdit(sketch.Name))
            session.appearance.update()
        else:
            Gui.activeDocument().setEdit(sketch.Name)
    finally:
        view_object.EditingWorkbench = previous


def finish_sketch():
    sketch = in_sketch()
    if not sketch:
        raise ModelingError("There is no sketch open to finish.")
    Gui.runCommand("Sketcher_LeaveSketch", 0)
    sketch.Document.recompute()
    # FreeCAD may hide the edited sketch on exit. If its Body has no solid
    # result yet, hiding the sketch leaves the design looking completely empty.
    # Keep only such sketch-only workflows visible; don't expose consumed
    # sketches over an existing finished solid.
    owner = getattr(sketch, "_Body", None)
    if owner is None:
        from .features import owner_body
        owner = owner_body(sketch)
    tip = getattr(owner, "Tip", None) if owner is not None else None
    if tip is None or tip == sketch:
        if owner is not None:
            owner.ViewObject.Visibility = True
        sketch.ViewObject.Visibility = True
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(sketch)
    Gui.activeDocument().activeView().viewAxonometric()
    from . import commands

    commands.invoke("Std_ViewFitAll")
    return sketch


def selected_profile():
    if in_sketch():
        return finish_sketch()
    selected = [
        obj for obj in Gui.Selection.getSelection() if obj.isDerivedFrom("Sketcher::SketchObject")
    ]
    if len(selected) == 1:
        return selected[0]
    if selected:
        raise ModelingError("Select one sketch profile at a time.")
    if not App.ActiveDocument:
        raise ModelingError("Create a sketch first, then choose Extrude or Cut.")
    body = active_body()
    candidates = []
    for obj in App.ActiveDocument.Objects:
        if not obj.isDerivedFrom("Sketcher::SketchObject"):
            continue
        if body and body_of(obj) != body:
            continue
        used = any(getattr(parent, "Profile", None) == obj for parent in obj.InList)
        if not used:
            candidates.append(obj)
    if len(candidates) != 1:
        raise ModelingError("Select the sketch in the Browser, then choose Extrude or Cut.")
    return candidates[0]


def length_mm(text):
    """Bare numbers are millimetres; explicit length units and expressions work."""
    try:
        quantity = App.Units.Quantity(text.strip())
    except Exception as exc:
        raise ModelingError("Enter a length such as 10 mm or 0.25 in.") from exc
    if quantity.Unit not in (App.Units.Unit(), App.Units.Length):
        raise ModelingError("Distance must have length units, such as mm or in.")
    value = float(quantity.Value)
    if not math.isfinite(value) or value <= 0:
        raise ModelingError("Distance must be greater than zero.")
    return value


class Extrusion:
    """A preview transaction shared by the task panel and integration tests."""

    def __init__(self, sketch, cut=False):
        self.doc = sketch.Document
        self.doc_name = self.doc.Name
        self.sketch = sketch
        self.closed = False
        self.feature = None
        self.cut = cut
        self.visibility = {
            o.Name: o.ViewObject.Visibility for o in self.doc.Objects if o.ViewObject
        }
        body = body_of(sketch)
        has_solid = body is not None and any(
            hasattr(obj, "Shape") and len(obj.Shape.Solids) > 0
            for obj in body.Group
            if not obj.isDerivedFrom("Sketcher::SketchObject")
        )
        if cut and not has_solid:
            raise ModelingError(
                "Cut needs an existing solid. Extrude the first sketch to create one."
            )
        self.doc.openTransaction("Az: Cut" if cut else "Az: Extrude")
        try:
            if body is None:
                if any(parent.isDerivedFrom("App::Part") for parent in sketch.InList):
                    raise ModelingError(
                        "Place this sketch inside a Part Design body before extruding it."
                    )
                body = self.doc.addObject("PartDesign::Body", "Body")
                body.addObject(sketch)
            self.body = body
            self.previous_tip = body.Tip
            # FreeCAD may make a newly created sketch the Tip. Find the solid
            # preceding it so that Cut is also allowed after a fresh sketch.
            if self.previous_tip == sketch:
                solids = [
                    o
                    for o in body.Group
                    if o != sketch
                    and hasattr(o, "Shape")
                    and not o.isDerivedFrom("Sketcher::SketchObject")
                    and not o.Shape.isNull()
                ]
                self.previous_tip = solids[-1] if solids else None
            kind = "PartDesign::Pocket" if cut else "PartDesign::Pad"
            self.feature = body.newObject(kind, "Cut" if cut else "Extrude")
            self.feature.Profile = sketch
            self.feature.Length = 10
            self.body.Tip = self.feature
            sketch.ViewObject.Visibility = False
            if self.previous_tip:
                self.previous_tip.ViewObject.Visibility = False
            self.feature.ViewObject.Visibility = True
            self.feature.ViewObject.ShapeColor = (0.76, 0.79, 0.82)
            self.feature.ViewObject.LineColor = (0.20, 0.24, 0.28)
        except Exception:
            self.cancel()
            raise

    def update(self, distance, direction="One side"):
        if self.closed:
            raise ModelingError("This operation is already closed.")
        value = length_mm(distance)
        self.feature.Length = value
        set_extrusion_sides(self.feature, "Symmetric" if direction == "Symmetric" else "One side")
        self.feature.Reversed = direction == "Reversed"
        self.doc.recompute()
        shape = self.feature.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
            raise ModelingError(
                "The profile must form one valid solid. Check closed loops and that it meets the body."
            )
        if "Invalid" in self.feature.State:
            raise ModelingError(
                "FreeCAD could not build this feature. Check the profile and direction."
            )
        return shape.Volume

    def accept(self):
        if not self.closed:
            self.doc.recompute()
            self.doc.commitTransaction()
            self.closed = True
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(self.feature)

    def cancel(self):
        if self.closed:
            return
        self.closed = True
        self.doc.abortTransaction()
        for name, visible in self.visibility.items():
            obj = self.doc.getObject(name)
            if obj and obj.ViewObject:
                obj.ViewObject.Visibility = visible
        self.doc.recompute()


class ExtrudeTask:
    """Native Tasks panel with a live solid preview and length-unit input."""

    def __init__(self, sketch, cut=False):
        self.cut = cut
        self.operation = Extrusion(sketch, cut)
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("Cut" if cut else "Extrude")
        layout = QtWidgets.QVBoxLayout(self.form)
        title = QtWidgets.QLabel("CUT" if cut else "EXTRUDE")
        title.setStyleSheet("font-size: 17px; font-weight: 600; color: #234b66; padding: 6px 0;")
        layout.addWidget(title)
        profile = QtWidgets.QLabel("Profile: " + sketch.Label)
        profile.setWordWrap(True)
        layout.addWidget(profile)
        fields = QtWidgets.QFormLayout()
        self.distance = QtWidgets.QLineEdit("10 mm")
        self.distance.setObjectName("AzExtrudeDistance")
        self.distance.setToolTip(
            "Bare numbers use millimetres. You can also enter 0.25 in or 1/4 in."
        )
        fields.addRow("Distance", self.distance)
        self.direction = QtWidgets.QComboBox()
        self.direction.addItems(["One side", "Symmetric", "Reversed"])
        fields.addRow("Direction", self.direction)
        operation_label = QtWidgets.QLabel("Remove material" if cut else "Add material")
        fields.addRow("Operation", operation_label)
        layout.addLayout(fields)
        hint = QtWidgets.QLabel(
            "Use a closed sketch. Cancel discards the preview; OK creates an editable feature."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #626d76; padding: 8px 0;")
        layout.addWidget(hint)
        self.status = QtWidgets.QLabel()
        self.status.setWordWrap(True)
        self.status.setObjectName("AzExtrudeStatus")
        layout.addWidget(self.status)
        layout.addStretch()
        self.timer = QtCore.QTimer(self.form)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.preview)
        self.distance.textChanged.connect(lambda *_: self.timer.start(180))
        self.direction.currentIndexChanged.connect(lambda *_: self.timer.start(180))
        self.valid = False
        self.preview()
        QtCore.QTimer.singleShot(180, self.fit_preview)

    def fit_preview(self):
        if not self.operation.closed and App.ActiveDocument == self.operation.doc:
            Gui.activeDocument().activeView().fitAll()

    def preview(self):
        self.timer.stop()
        try:
            volume = self.operation.update(self.distance.text(), self.direction.currentText())
            self.valid = True
            self.status.setStyleSheet("color: #21734a; padding: 8px 0;")
            self.status.setText("Preview ready · Volume {:.2f} mm³".format(volume))
        except (ModelingError, RuntimeError, ValueError) as exc:
            self.valid = False
            self.status.setStyleSheet("color: #ac422e; padding: 8px 0;")
            self.status.setText(str(exc))

    def getStandardButtons(self):
        return int(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

    def accept(self):
        self.preview()
        if not self.valid:
            return False
        self.operation.accept()
        Gui.Control.closeDialog()
        return True

    def reject(self):
        self.timer.stop()
        self.operation.cancel()
        Gui.Control.closeDialog()
        return True

    def isAllowedAlterDocument(self):
        return False

    def isAllowedAlterSelection(self):
        return False

    def isAllowedAlterView(self):
        return True


def start_extrude(cut=False):
    sketch = selected_profile()
    if Gui.Control.activeDialog():
        raise ModelingError("Finish or cancel the current operation first.")
    task = ExtrudeTask(sketch, cut)
    try:
        Gui.Control.showDialog(task)
    except Exception:
        task.operation.cancel()
        raise
    return task
