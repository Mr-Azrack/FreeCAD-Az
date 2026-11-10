# SPDX-License-Identifier: LGPL-2.1-or-later
"""Design-owned live Solid Linear Pattern UI, including native feature edits.

The actual model remains a native PartDesign::LinearPattern in the FCStd file.
The user never enters the stock FreeCAD pattern task panel.
"""
import FreeCADGui as Gui

from .qt import QtCore, QtWidgets
from .features import DesignError, owner_body
from . import modeling
from .pattern_canvas import PatternCanvasHandles
from .solid_pattern_engine import AXES, PatternDraft, eligible_in_body

_active = None


def _body():
    selection = Gui.Selection.getSelection()
    for obj in selection:
        body = owner_body(obj)
        if body is not None:
            return body
        if obj.isDerivedFrom("PartDesign::Body"):
            return obj
    body = modeling.active_body()
    if body is not None:
        return body
    doc = modeling.current_document()
    bodies = [o for o in getattr(doc, "Objects", ()) if o.isDerivedFrom("PartDesign::Body")]
    if len(bodies) == 1:
        return bodies[0]
    raise DesignError("Select a feature or activate the Body to pattern.")


class SolidPatternPanel(QtWidgets.QFrame):
    def __init__(self, session, body, editing=None):
        super().__init__(session.mdi.viewport())
        self.session = session
        self.body = body
        self.editing = editing
        self.draft = None
        self._done = False
        self.setObjectName("AzSolidPatternPanel")
        self.setStyleSheet("""
        QFrame#AzSolidPatternPanel {
            background: #fafcfe; border: 1px solid #97b8cd; border-radius: 9px;
        }
        QFrame#AzSolidPatternPanel QLabel { color: #2c5369; background: transparent; }
        QFrame#AzSolidPatternPanel QPushButton {
            min-height: 29px; background: #e3eef6; color: #244e69;
            border: 1px solid #a5c3d4; border-radius: 5px; padding: 4px 9px;
        }
        QFrame#AzSolidPatternPanel QPushButton#AzPatternApply {
            background: #23749b; color: white; font-weight: 600;
        }
        """)
        self.setFixedWidth(342)
        box = QtWidgets.QVBoxLayout(self)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(9)
        title = QtWidgets.QLabel("SOLID  ·  LINEAR PATTERN")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        box.addWidget(title)
        description = QtWidgets.QLabel(
            "Select a solid feature, set a direction and repetitions. "
            "The preview is the real FreeCAD solid, but is not saved until Apply."
        )
        description.setWordWrap(True)
        box.addWidget(description)
        form = QtWidgets.QFormLayout()
        self.source = QtWidgets.QComboBox()
        self.items = eligible_in_body(body)
        self.initial = (
            editing.Originals[0] if editing and getattr(editing, "Originals", [])
            else None
        )
        for obj in self.items:
            self.source.addItem(obj.Label, obj.Name)
        chosen = self.initial
        if chosen is None:
            selected = Gui.Selection.getSelection()
            chosen = next((obj for obj in selected if obj in self.items), None)
        if chosen in self.items:
            self.source.setCurrentIndex(self.items.index(chosen))
        self.source.setEnabled(editing is None)
        form.addRow("Feature", self.source)
        self.axis = QtWidgets.QComboBox()
        for label, role in AXES:
            self.axis.addItem(label, role)
        if editing:
            ref = getattr(editing, "Direction", None)
            direction = ref[0] if isinstance(ref, (tuple, list)) and ref else None
            role = getattr(direction, "Role", "X_Axis")
            for i in range(self.axis.count()):
                if self.axis.itemData(i) == role:
                    self.axis.setCurrentIndex(i)
        form.addRow("Direction", self.axis)
        self.count = QtWidgets.QSpinBox()
        self.count.setRange(2, 200)
        self.count.setValue(int(editing.Occurrences) if editing else 3)
        form.addRow("Occurrences", self.count)
        self.distance_mode = QtWidgets.QComboBox()
        self.distance_mode.addItem("Spacing between copies", "spacing")
        self.distance_mode.addItem("Total extent", "extent")
        form.addRow("Distance mode", self.distance_mode)
        self.spacing = QtWidgets.QDoubleSpinBox()
        self.spacing.setRange(0.001, 100000)
        self.spacing.setDecimals(3)
        self.spacing.setSuffix(" mm")
        old_offset = getattr(editing, "Offset", None) if editing else None
        self.spacing.setValue(float(getattr(old_offset, "Value", old_offset or 20)))
        form.addRow("Distance", self.spacing)
        self.reversed = QtWidgets.QCheckBox("Reverse direction")
        self.reversed.setChecked(bool(getattr(editing, "Reversed", False)))
        form.addRow("", self.reversed)
        box.addLayout(form)

        self.message = QtWidgets.QLabel("Adjust the controls for a live preview.")
        self.message.setWordWrap(True)
        box.addWidget(self.message)
        buttons = QtWidgets.QHBoxLayout()
        self.apply = QtWidgets.QPushButton("Apply pattern")
        self.apply.setObjectName("AzPatternApply")
        self.apply.setEnabled(False)
        buttons.addWidget(self.apply)
        cancel = QtWidgets.QPushButton("Cancel · Esc")
        buttons.addWidget(cancel)
        box.addLayout(buttons)

        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.preview)
        for field in (self.source, self.axis, self.distance_mode):
            field.currentIndexChanged.connect(self.queue_preview)
        self.count.valueChanged.connect(self.queue_preview)
        self.spacing.valueChanged.connect(self.queue_preview)
        self.reversed.toggled.connect(self.queue_preview)
        self.apply.clicked.connect(self.accept)
        cancel.clicked.connect(self.cancel)

        self.handles = PatternCanvasHandles(
            lambda _axis: self.spacing.value(),
            lambda _axis, value: self.spacing.setValue(max(0.001, value)),
            mode="solid", parent=session.mdi.viewport(),
        )
        self.handles.hide()
        self.adjustSize()

    def selected_source(self):
        name = self.source.currentData()
        obj = self.body.Document.getObject(name) if name else None
        if obj not in self.items:
            raise DesignError("Select an eligible solid feature for Pattern.")
        return obj

    def queue_preview(self, *_):
        if self._done:
            return
        self.apply.setEnabled(False)
        self.timer.start()

    def show_panel(self):
        parent = self.parentWidget()
        self.move(max(8, parent.width() - self.width() - 18), 18)
        self.handles.move(max(8, self.x() - 193), 20)
        self.show()
        self.raise_()
        self.handles.show()
        self.handles.raise_()
        self.queue_preview()

    def preview(self):
        if self._done:
            return
        try:
            source = self.selected_source()
            if self.draft is not None and self.draft.source != source:
                self.draft.cancel()
                self.draft = None
            if self.draft is None:
                self.draft = PatternDraft(source, self.editing)
            distance = self.spacing.value()
            if self.distance_mode.currentData() == "extent":
                distance /= (self.count.value() - 1)
            obj = self.draft.preview(
                self.count.value(), distance, self.axis.currentData(),
                self.reversed.isChecked(),
            )
            self.message.setText(
                "{} solid occurrences · {:.3f} mm spacing · Undo supported.".format(
                    obj.Occurrences, distance
                )
            )
            self.message.setStyleSheet("color: #2b7457;")
            self.apply.setEnabled(True)
        except Exception as exc:
            self.message.setText("Preview unavailable: " + str(exc))
            self.message.setStyleSheet("color: #a14936;")
            self.apply.setEnabled(False)

    def accept(self, *_):
        if self._done or self.draft is None:
            return
        try:
            result = self.draft.accept()
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(result)
            from .commands import notify
            notify("Design Linear Pattern saved. Double-click its timeline icon to edit.")
            self._cleanup()
        except Exception as exc:
            self.message.setText("Cannot apply: " + str(exc))
            self.message.setStyleSheet("color: #a14936;")
            self.apply.setEnabled(False)

    def _cleanup(self):
        global _active
        self._done = True
        self.timer.stop()
        self.handles.hide()
        self.handles.deleteLater()
        self.hide()
        self.deleteLater()
        if _active is self:
            _active = None
        try:
            self.session.history.signature = None
            self.session.history.refresh()
        except (AttributeError, RuntimeError):
            pass

    def cancel(self, *_):
        if self._done:
            return
        if self.draft is not None:
            self.draft.cancel()
        self._cleanup()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.cancel()
            event.accept()
        else:
            super().keyPressEvent(event)


def show(editing=None):
    global _active
    from .session import current
    if Gui.Control.activeDialog() or modeling.in_sketch():
        raise DesignError("Finish the active sketch or task before Solid Pattern.")
    session = current()
    if not session or not session.active:
        raise DesignError("Activate the Design workbench to use Solid Pattern.")
    if _active is not None:
        _active.cancel()
    body = owner_body(editing) if editing else _body()
    if body is None:
        raise DesignError("The pattern must belong to an active Body.")
    panel = SolidPatternPanel(session, body, editing)
    _active = panel
    panel.show_panel()
    return panel


def cancel_active():
    if _active is None:
        return False
    _active.cancel()
    return True
