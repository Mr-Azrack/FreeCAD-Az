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


class _PatternSelectionObserver:
    def __init__(self, panel):
        self.panel = panel

    def addSelection(self, doc_name, object_name, _sub_name, _point):
        panel = self.panel
        if panel is None or panel._done:
            return
        QtCore.QTimer.singleShot(
            0, lambda: panel.pick_canvas_feature(doc_name, object_name)
        )


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
            "Pick a feature on the model or in the Browser, set directions "
            "and counts, then preview. Nothing is saved until Apply."
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
        if chosen is None and self.items:
            chosen = next(
                (obj for obj in reversed(self.items)
                 if obj.TypeId in ("PartDesign::Hole", "PartDesign::Pocket")),
                self.items[-1],
            )
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
        # Pattern pitch is Length / (Occurrences - 1) in the native
        # extent mode, independent of whether FreeCAD labels it "Extent"
        # or the older "Overall Length".
        old_length = getattr(editing, "Length", None) if editing else None
        pitch = (
            float(getattr(old_length, "Value", old_length)) /
            max(1, self.count.value() - 1)
            if old_length is not None else 20.0
        )
        self.spacing.setValue(max(0.001, pitch))
        form.addRow("Distance", self.spacing)
        self.reversed = QtWidgets.QCheckBox("Reverse direction")
        self.reversed.setChecked(bool(getattr(editing, "Reversed", False)))
        form.addRow("", self.reversed)
        self.second_enabled = QtWidgets.QCheckBox("Second direction · rectangular grid")
        current_second = int(getattr(editing, "Occurrences2", 1)) if editing else 1
        self.second_enabled.setChecked(current_second > 1)
        form.addRow("", self.second_enabled)
        self.axis2 = QtWidgets.QComboBox()
        for axis_label, axis_role in AXES:
            self.axis2.addItem(axis_label, axis_role)
        if editing:
            old_ref = getattr(editing, "Direction2", None)
            old_direction = old_ref[0] if isinstance(old_ref, (tuple, list)) and old_ref else None
            old_role = getattr(old_direction, "Role", "Y_Axis")
        else:
            old_role = "Y_Axis"
        for index in range(self.axis2.count()):
            if self.axis2.itemData(index) == old_role:
                self.axis2.setCurrentIndex(index)
        self.count2 = QtWidgets.QSpinBox()
        self.count2.setRange(2, 20)
        self.count2.setValue(max(2, current_second))
        self.spacing2 = QtWidgets.QDoubleSpinBox()
        self.spacing2.setRange(0.001, 100000)
        self.spacing2.setDecimals(3)
        self.spacing2.setSuffix(" mm")
        previous_total = getattr(editing, "Length2", None) if editing else None
        previous_extent = float(getattr(previous_total, "Value", previous_total)) if previous_total is not None else 40.0
        self.spacing2.setValue(max(0.001, previous_extent / max(1, current_second - 1)))
        form.addRow("Grid axis", self.axis2)
        form.addRow("Grid occurrences", self.count2)
        form.addRow("Grid spacing", self.spacing2)
        for field in (self.axis2, self.count2, self.spacing2):
            field.setEnabled(self.second_enabled.isChecked())
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
        for field in (self.source, self.axis, self.distance_mode, self.axis2):
            field.currentIndexChanged.connect(self.queue_preview)
        for field in (self.count, self.count2, self.spacing, self.spacing2):
            field.valueChanged.connect(self.queue_preview)
        self.reversed.toggled.connect(self.queue_preview)
        self.second_enabled.toggled.connect(self.second_changed)
        self.apply.clicked.connect(self.accept)
        cancel.clicked.connect(self.cancel)

        self.handles = PatternCanvasHandles(
            lambda axis: self.spacing.value() if axis == "x" else self.spacing2.value(),
            lambda axis, value: (
                self.spacing if axis == "x" else self.spacing2
            ).setValue(max(0.001, value)),
            mode="grid", parent=session.mdi.viewport(),
            get_axis_name=lambda: str(self.axis.currentText()).split()[0],
            get_second_axis_name=lambda: str(self.axis2.currentText()).split()[0],
            get_counts=lambda: (
                self.count.value(), self.count2.value() if self.second_enabled.isChecked() else 1
            ),
        )
        self.handles.hide()
        self.selection_observer = _PatternSelectionObserver(self)
        self.adjustSize()

    def second_changed(self, enabled):
        for field in (self.axis2, self.count2, self.spacing2):
            field.setEnabled(enabled)
        self.queue_preview()

    def pick_canvas_feature(self, document, object_name):
        if self._done or self.editing is not None:
            return
        if document != self.body.Document.Name:
            return
        feature = self.body.Document.getObject(object_name)
        if feature in self.items:
            index = self.items.index(feature)
            if self.source.currentIndex() != index:
                self.source.setCurrentIndex(index)

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
        Gui.Selection.addObserver(self.selection_observer)
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
            grid_count = self.count2.value() if self.second_enabled.isChecked() else 1
            obj = self.draft.preview(
                self.count.value(), distance, self.axis.currentData(),
                self.reversed.isChecked(),
                count2=grid_count, spacing2=self.spacing2.value(),
                direction2=self.axis2.currentData(),
            )
            self.handles.update()
            self.message.setText(
                "{} × {} solid occurrences · {:.3f} mm pitch · Undo supported.".format(
                    obj.Occurrences, grid_count, distance
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
        try:
            Gui.Selection.removeObserver(self.selection_observer)
        except (RuntimeError, ReferenceError):
            pass
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
