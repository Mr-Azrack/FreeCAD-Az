# SPDX-License-Identifier: LGPL-2.1-or-later
"""Selection-aware Press/Pull with explicit, parametric design intent."""

from dataclasses import dataclass
import FreeCAD as App
import Part
import Sketcher
from . import features, operations
from .features import DesignError
from .compat import extrusion_side_type


@dataclass
class Binding:
    obj: object
    path: str
    label: str
    factor: float = 1.0
    delta: bool = False
    geometry: int = -1

    def prepare(self):
        if self.geometry >= 0:
            index = self.obj.addConstraint(
                Sketcher.Constraint(
                    "Diameter", self.geometry, self.obj.Geometry[self.geometry].Radius * 2
                )
            )
            self.path = "Constraints[{}]".format(index)
            self.geometry = -1

    def value(self):
        if self.path.startswith("Constraints["):
            return self.obj.getDatum(int(self.path[12:-1])).Value
        return getattr(self.obj, self.path).Value

    def expression(self):
        return operations.expressions(self.obj).get(self.path, "{} mm".format(self.value()))


def cap_binding(obj, face):
    """Resize a source extrusion, preserving even its tapered side walls."""
    body = features.owner_body(obj)
    if getattr(obj, "AzType", "") == "AzExtrude":
        if (
            obj.Operation not in ("Join", "New body")
            or obj.Direction != "One side"
            or obj.Extent != "Distance"
        ):
            return None
        profile = features.source_shape(
            obj.Source, body, obj.Regions, obj.WholeSketch, obj.SourceFaceSignature
        )
        offset = obj.StartOffset.Value
    elif (
        obj.isDerivedFrom("PartDesign::Pad")
        and obj.Type == "Length"
        and extrusion_side_type(obj) == "One side"
    ):
        profile = features.source_shape(obj.Profile, body, whole=True)
        offset = 0
    else:
        return None
    start = profile.Faces[0].CenterOfMass
    normal = profile.Faces[0].normalAt(0, 0)
    direction = -normal if obj.Reversed else normal
    expected = start + normal * offset + direction * obj.Length.Value
    end_normal = face.normalAt(0, 0)
    if (
        abs((face.CenterOfMass - expected).dot(direction)) < 1e-5
        and end_normal.dot(direction) > 0.99999
    ):
        return Binding(obj, "Length", "End face offset", delta=True)
    return None


def require_prismatic(obj, face):
    """A face prism is an exact offset only when its side walls are parallel.

    Tapered end faces use their originating feature's Length instead. Complex
    imported surfaces need an offset-surface/healing implementation, so refuse
    them before creating geometry with different design intent.
    """
    normal = face.normalAt(0, 0)
    for adjacent in obj.Shape.Faces:
        if adjacent.isSame(face) or not any(
            a.isSame(b) for a in face.Edges for b in adjacent.Edges
        ):
            continue
        surface = adjacent.Surface
        if isinstance(surface, Part.Plane):
            supported = abs(adjacent.normalAt(0, 0).dot(normal)) < 1e-6
        elif isinstance(surface, Part.Cylinder):
            supported = abs(surface.Axis.dot(normal)) > 0.999999
        else:
            supported = False
        if not supported:
            raise DesignError(
                "This face has sloped or curved side walls. Edit its source feature or use Extrude explicitly; Press/Pull cannot offset this surface safely yet."
            )


def cylinder_binding(obj, face):
    if obj.isDerivedFrom("Part::Cylinder") and abs(obj.Radius.Value - face.Surface.Radius) < 1e-5:
        return Binding(obj, "Radius", "Diameter", 2)
    if (
        obj.isDerivedFrom("PartDesign::Hole")
        and abs(obj.Diameter.Value / 2 - face.Surface.Radius) < 1e-5
    ):
        return Binding(obj, "Diameter", "Diameter")
    parent = obj.getGlobalPlacement().multiply(obj.Placement.inverse())
    world = face.copy()
    world.Placement = parent.multiply(world.Placement)
    cylinder = world.Surface
    if not isinstance(cylinder, Part.Cylinder):
        raise DesignError("Select a planar face, cylindrical face, sketch or edge.")
    queue, seen = [(obj, 0)], set()
    matches = []
    best_depth = None
    while queue:
        candidate, depth = queue.pop(0)
        if candidate.Name in seen or (best_depth is not None and depth > best_depth):
            continue
        seen.add(candidate.Name)
        if candidate.isDerivedFrom("Sketcher::SketchObject"):
            placement = candidate.getGlobalPlacement()
            for index, curve in enumerate(candidate.Geometry):
                if not isinstance(curve, Part.Circle) or candidate.getConstruction(index):
                    continue
                center = placement.multVec(curve.Center)
                axis = placement.Rotation.multVec(curve.Axis)
                if (
                    abs(axis.dot(cylinder.Axis)) > 0.999999
                    and (center - cylinder.Center).cross(cylinder.Axis).Length < 1e-5
                    and abs(curve.Radius - cylinder.Radius) < 1e-5
                ):
                    matches.append((candidate, index))
                    best_depth = depth
        queue.extend((child, depth + 1) for child in candidate.OutList)
    if len(matches) != 1:
        raise DesignError(
            "This cylindrical face has no unique editable source circle. Edit its native Hole/Cylinder parameters or source sketch."
        )
    sketch, geometry = matches[0]
    for index, constraint in enumerate(sketch.Constraints):
        if (
            constraint.First == geometry
            and constraint.Type in ("Radius", "Diameter")
            and sketch.getDriving(index)
        ):
            return Binding(
                sketch,
                "Constraints[{}]".format(index),
                "Diameter",
                2 if constraint.Type == "Radius" else 1,
            )
    return Binding(sketch, "", "Diameter", geometry=geometry)


class DimensionEdit:
    def __init__(self, binding):
        features.ensure_calculator()
        self.binding = binding
        self.doc = binding.obj.Document
        self.closed = False
        features.begin_transaction(self.doc, "Az: Press/Pull")
        try:
            binding.prepare()
            self.original = binding.expression()
        except Exception:
            self.cancel()
            raise

    def initial(self):
        if self.binding.delta:
            return "0 mm"
        return "({}) * {}".format(self.original, self.binding.factor)

    def update(self, text):
        binding = self.binding
        value = features.numeric(
            text, context=binding.obj, signed=binding.delta, zero=binding.delta
        )
        expression = (
            "({}) + ({})".format(self.original, text)
            if binding.delta
            else "({}) / {}".format(text, binding.factor)
        )
        if binding.delta and binding.value() <= 0 and value <= 0:
            raise DesignError("Keep a positive extrusion length.")
        binding.obj.setExpression(binding.path, expression)
        self.doc.recompute()
        invalid = [
            o.Label for o in self.doc.Objects if "Invalid" in o.State or getattr(o, "Error", "")
        ]
        if invalid:
            raise DesignError("This value breaks: " + ", ".join(invalid))
        return value

    def accept(self):
        self.doc.commitTransaction()
        self.closed = True

    def cancel(self):
        if not self.closed:
            self.doc.abortTransaction()
            self.doc.recompute()
            self.closed = True


def show_binding(binding):
    import FreeCADGui as Gui
    from .qt import QtCore, QtWidgets
    from .tasks import track, forget

    class Task:
        def __init__(self):
            self.edit = DimensionEdit(binding)
            self.valid = False
            self.form = QtWidgets.QWidget()
            self.form.setWindowTitle("Press/Pull")
            layout = QtWidgets.QFormLayout(self.form)
            title = QtWidgets.QLabel("PRESS / PULL · " + binding.obj.Label)
            title.setWordWrap(True)
            layout.addRow(title)
            self.value = QtWidgets.QLineEdit(self.edit.initial())
            self.value.setObjectName("AzPressPullValue")
            layout.addRow(binding.label, self.value)
            self.status = QtWidgets.QLabel(
                "Positive offsets move the end face outward. Negative offsets shorten it."
                if binding.delta
                else "Change the driving circle diameter; downstream features update."
            )
            self.status.setWordWrap(True)
            layout.addRow(self.status)
            self.timer = QtCore.QTimer(self.form)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.preview)
            self.value.textChanged.connect(lambda *_: self.timer.start(160))
            self.preview()
            self.value.selectAll()
            self.value.setFocus()

        def preview(self):
            self.timer.stop()
            try:
                self.edit.update(self.value.text())
                self.valid = True
                self.status.setText(
                    "Live preview · {} = {:.3f} mm".format(
                        binding.obj.Label, binding.value() * binding.factor
                    )
                )
                self.status.setStyleSheet("color: #21734a")
            except Exception as exc:
                self.valid = False
                self.status.setText(str(exc))
                self.status.setStyleSheet("color: #ac422e")

        def accept(self):
            self.preview()
            if not self.valid:
                return False
            self.edit.accept()
            forget(self)
            Gui.Control.closeDialog()
            return True

        def reject(self):
            self.timer.stop()
            self.edit.cancel()
            forget(self)
            Gui.Control.closeDialog()
            return True

        def getStandardButtons(self):
            return int(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

    task = Task()
    Gui.Control.showDialog(task)
    track(task)
    return task


def start():
    import FreeCADGui as Gui
    from . import tasks, modeling

    if modeling.in_sketch():
        return tasks.show_extrude()
    if Gui.Control.activeDialog():
        raise DesignError("Finish or cancel the current operation first.")
    for selection in Gui.Selection.getSelectionEx():
        obj = selection.Object
        if obj.isDerivedFrom("Sketcher::SketchObject"):
            return tasks.show_extrude((obj, []))
        for name in selection.SubElementNames:
            if name.startswith("Edge"):
                Gui.runCommand("PartDesign_Fillet", 0)
                return None
            if name.startswith("Face"):
                if obj.isDerivedFrom("PartDesign::Body"):
                    obj = features.body_tip(obj)
                face = obj.Shape.getElement(name)
                if isinstance(face.Surface, Part.Cylinder):
                    return show_binding(cylinder_binding(obj, face))
                if not isinstance(face.Surface, Part.Plane):
                    raise DesignError(
                        "Press/Pull supports planar faces and cylinders with an editable source circle."
                    )
                binding = cap_binding(obj, face)
                if binding:
                    return show_binding(binding)
                require_prismatic(obj, face)
                task = tasks.show_extrude((obj, [name]))
                task.distance.setText("2 mm")
                task.preview()
                return task
    return tasks.show_extrude()
