# SPDX-License-Identifier: LGPL-2.1-or-later
"""Nonmodal sketch plane picker: click XY/XZ/YZ or a planar model face.

No modal plane dropdown and no temporary FreeCAD document geometry.
FreeCAD's actual face selection remains active while the picker is open.
"""
import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore, QtWidgets

_active = None


class _FaceObserver:
    def __init__(self, picker):
        self.picker = picker

    def addSelection(self, doc_name, object_name, sub_name, _point):
        if not str(sub_name).startswith("Face"):
            return
        picker = self.picker
        if picker is None or not picker.listening:
            return
        QtCore.QTimer.singleShot(
            0, lambda: picker.select_face(doc_name, object_name, sub_name)
        )


class SketchPlanePicker(QtWidgets.QFrame):
    def __init__(self, session):
        super().__init__(session.mdi.viewport())
        self.setObjectName("AzSketchPlanePicker")
        self.session = session
        self.observer = _FaceObserver(self)
        self.listening = False
        self.setStyleSheet("""
        QFrame#AzSketchPlanePicker { background: #ffffff;
            border: 1px solid #9ebdce; border-radius: 9px; }
        QFrame#AzSketchPlanePicker QLabel { color: #294a60; background: transparent; }
        QFrame#AzSketchPlanePicker QPushButton { min-height: 37px; min-width: 80px;
            padding: 5px 12px; border: 1px solid #a9c9dc; border-radius: 5px;
            background: #eaf5fa; color: #174c72; font-weight: 600; }
        QFrame#AzSketchPlanePicker QPushButton:hover {
            background: #d6ebf7; border-color: #438db4; }
        QFrame#AzSketchPlanePicker QPushButton#AzPlaneCancel {
            background: #f6f7f9; color: #586b78; border-color: #cbd3d9; }
        """)
        self.setFixedWidth(440)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 11, 16, 12)
        layout.setSpacing(8)
        title = QtWidgets.QLabel("CREATE SKETCH — SELECT A PLANE OR FACE")
        title.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(title)
        hint = QtWidgets.QLabel("Click a planar face on the model, or choose an origin plane.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        row = QtWidgets.QHBoxLayout()
        for label, value in (("XY · Top", "XY"), ("XZ · Front", "XZ"), ("YZ · Right", "YZ")):
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(lambda _checked=False, plane=value: self.select_plane(plane))
            row.addWidget(button)
        layout.addLayout(row)
        cancel = QtWidgets.QPushButton("Cancel · Esc")
        cancel.setObjectName("AzPlaneCancel")
        cancel.clicked.connect(self.cancel)
        layout.addWidget(cancel, 0, QtCore.Qt.AlignRight)
        self.adjustSize()
        self.hide()

    def show_picker(self):
        global _active
        if _active is not None and _active is not self:
            _active.cancel()
        _active = self
        self.listening = True
        Gui.Selection.addObserver(self.observer)
        # Fusion workflow: with an existing model, do not obscure the canvas
        # with a large plane chooser. The next click on a planar face directly
        # opens its sketch. Origin plane shortcuts remain for empty documents.
        doc = App.ActiveDocument
        has_model = bool(doc and any(
            obj.isDerivedFrom("PartDesign::Body")
            and getattr(obj, "Tip", None) is not None
            and hasattr(obj.Tip, "Shape")
            and not obj.Tip.Shape.isNull()
            for obj in doc.Objects
        ))
        if has_model:
            self.hide()
            self.session.ribbon.hint.setText(
                "CREATE SKETCH · Click a flat model face · Esc cancels"
            )
        else:
            self.move(max(8, (self.parentWidget().width()-self.width())//2), 16)
            self.show()
            self.raise_()

    def release(self):
        global _active
        self.listening = False
        try:
            Gui.Selection.removeObserver(self.observer)
        except (RuntimeError, ReferenceError):
            pass
        self.hide()
        if _active is self:
            _active = None

    def cancel(self):
        self.release()

    def select_plane(self, plane):
        self.release()
        from .modeling import create_sketch
        create_sketch(plane=plane)

    def select_face(self, doc_name, obj_name, face_name):
        if not self.listening:
            return
        doc = App.ActiveDocument
        if doc is None or doc.Name != doc_name:
            return
        obj = doc.getObject(obj_name)
        if obj is None or not hasattr(obj, "Shape"):
            return
        try:
            import Part
            face = obj.Shape.getElement(face_name)
            if not isinstance(face.Surface, Part.Plane):
                return
            self.release()
            from .modeling import create_sketch
            create_sketch(support=(obj, [face_name]))
        except (ValueError, RuntimeError, AttributeError) as exc:
            App.Console.PrintWarning("Design plane selection: " + str(exc) + "\n")


def show():
    global _active
    from .session import current
    session = current()
    if session is None or not session.active:
        raise RuntimeError("Design workspace must be active to select a sketch plane.")
    if _active is not None:
        _active.cancel()
    picker = getattr(session, "sketch_plane_picker", None)
    if picker is None:
        picker = SketchPlanePicker(session)
        session.sketch_plane_picker = picker
    # Honor a preselected planar face without making the user click twice.
    selected = list(Gui.Selection.getSelectionEx())
    if len(selected) == 1 and App.ActiveDocument is not None:
        hit = selected[0]
        faces = [name for name in hit.SubElementNames if name.startswith("Face")]
        if len(faces) == 1 and hit.Object.Document == App.ActiveDocument:
            try:
                import Part
                face = hit.Object.Shape.getElement(faces[0])
                if isinstance(face.Surface, Part.Plane):
                    from .modeling import create_sketch
                    create_sketch(support=(hit.Object, [faces[0]]))
                    return None
            except (AttributeError, ValueError, RuntimeError):
                pass
    picker.show_picker()
    return picker


def cancel_active():
    if _active is not None:
        _active.cancel()
        return True
    return False
