# SPDX-License-Identifier: LGPL-2.1-or-later
"""Design-owned in-canvas Sketch Rectangular Pattern with real live geometry."""
import FreeCADGui as Gui

from .qt import QtCore, QtWidgets
from .features import DesignError
from .pattern_canvas import PatternCanvasHandles
from . import modeling, sketch_pattern

_active = None


class _CircleSelectionObserver:
    """Follow the circle selected directly on the Sketcher canvas."""

    def __init__(self, panel):
        self.panel = panel

    def addSelection(self, doc_name, object_name, sub_name, _point):
        panel = self.panel
        if panel._done or doc_name != panel.sketch.Document.Name:
            return
        if object_name != panel.sketch.Name or not str(sub_name).startswith("Edge"):
            return
        index = sketch_pattern.circle_for_edge(
            panel.sketch, str(sub_name), panel.candidates
        )
        if index in panel.candidates:
            QtCore.QTimer.singleShot(0, lambda: panel.choose_circle(index))


class SketchPatternDraft:
    """Native Sketcher geometry preview within one cancelable transaction."""

    def __init__(self, sketch):
        self.sketch = sketch
        self.doc = sketch.Document
        self.original_geometry_count = sketch.GeometryCount
        self.started = False
        self.valid = False
        self.created = ()
        self.parameters = None

    def _drop_preview(self):
        expected = self.original_geometry_count + len(self.created)
        if self.sketch.GeometryCount != expected:
            raise DesignError(
                "Sketch geometry changed outside Pattern. Cancel and retry; "
                "the preview will not delete unrelated geometry."
            )
        for index in range(self.sketch.GeometryCount - 1,
                           self.original_geometry_count - 1, -1):
            self.sketch.delGeometry(index)
        self.created = ()
        self.valid = False
        self.doc.recompute()

    def preview(self, source, columns, rows, pitch_x, pitch_y):
        if not self.started:
            self.doc.openTransaction("Design: Preview sketch rectangular pattern")
            self.started = True
        self._drop_preview()
        try:
            self.created = sketch_pattern.pattern_circles(
                self.sketch, source, columns, rows, pitch_x, pitch_y,
                manage_transaction=False,
            )
            self.doc.recompute()
            self.valid = True
            self.parameters = (source, columns, rows, pitch_x, pitch_y)
            return self.created
        except Exception:
            # Native Sketcher can reject a constraint *after* adding geometry.
            # The helper does not own this transaction; abort it here so a
            # partially generated pattern cannot survive a failed preview.
            self.doc.abortTransaction()
            self.doc.recompute()
            self.started = False
            self.valid = False
            self.created = ()
            self.parameters = None
            raise

    def accept(self):
        if not self.started or not self.valid:
            raise DesignError("Choose valid sketch pattern dimensions before applying.")
        # Record native sketch geometry ownership inside the same transaction.
        # A future editor can reject stale indices rather than deleting user geometry.
        from .pattern_records import append_record
        try:
            append_record(self.sketch, self.parameters, self.created)
            self.doc.commitTransaction()
        except Exception:
            self.doc.abortTransaction()
            self.doc.recompute()
            self.started = False
            self.valid = False
            self.created = ()
            self.parameters = None
            raise
        self.started = False
        return self.created

    def cancel(self):
        if self.started:
            self.doc.abortTransaction()
            self.doc.recompute()
            self.started = False
            self.valid = False


class SketchPatternPanel(QtWidgets.QFrame):
    def __init__(self, session, sketch):
        super().__init__(session.mdi.viewport())
        self.session = session
        self.sketch = sketch
        self.draft = SketchPatternDraft(sketch)
        self._done = False
        self.observer = _CircleSelectionObserver(self)
        self._selection_observer_attached = False
        self.setObjectName("AzSketchPatternPanel")
        self.setStyleSheet("""
        QFrame#AzSketchPatternPanel {
            background: #fbfdff; border: 1px solid #9dbed1; border-radius: 9px;
        }
        QFrame#AzSketchPatternPanel QLabel { background: transparent; color: #2c5369; }
        QFrame#AzSketchPatternPanel QPushButton {
            background: #e2eef7; color: #24546d;
            border: 1px solid #a7c5d6; border-radius: 5px;
            padding: 6px; min-height: 28px;
        }
        QFrame#AzSketchPatternPanel QPushButton#AzSketchPatternApply {
            background: #21749f; color: white; font-weight: 600;
        }
        """)
        self.setFixedWidth(335)
        vertical = QtWidgets.QVBoxLayout(self)
        vertical.setContentsMargins(13, 11, 13, 11)
        vertical.setSpacing(8)
        title = QtWidgets.QLabel("SKETCH  ·  RECTANGULAR PATTERN")
        title.setStyleSheet("font-size: 14px; font-weight: 700;")
        vertical.addWidget(title)
        description = QtWidgets.QLabel(
            "Click a circle on the canvas or choose it below. Set rows and "
            "columns; copies stay the same diameter. Cancel restores the sketch."
        )
        description.setWordWrap(True)
        vertical.addWidget(description)
        form = QtWidgets.QFormLayout()
        self.source = QtWidgets.QComboBox()
        self.candidates = sketch_pattern.circle_indices(sketch)
        selected = sketch_pattern.selected_source(sketch)
        for i in self.candidates:
            point = sketch.Geometry[i].Center
            self.source.addItem(
                "Circle {} · ({:.1f}, {:.1f})".format(i + 1, point.x, point.y), i
            )
        if selected in self.candidates:
            self.source.setCurrentIndex(self.candidates.index(selected))
        form.addRow("Circle", self.source)
        self.columns = QtWidgets.QSpinBox()
        self.rows = QtWidgets.QSpinBox()
        for field in (self.columns, self.rows):
            field.setRange(1, 10)
            field.setValue(2)
        form.addRow("Columns (X)", self.columns)
        form.addRow("Rows (Y)", self.rows)
        self.pitch_x = QtWidgets.QDoubleSpinBox()
        self.pitch_y = QtWidgets.QDoubleSpinBox()
        for field in (self.pitch_x, self.pitch_y):
            field.setRange(-100000, 100000)
            field.setDecimals(3)
            field.setSingleStep(1.0)
            field.setSuffix(" mm")
            field.setValue(45)
        form.addRow("X center spacing", self.pitch_x)
        form.addRow("Y center spacing", self.pitch_y)
        vertical.addLayout(form)
        self.message = QtWidgets.QLabel("Drag arrows or enter precise center spacing.")
        self.message.setWordWrap(True)
        vertical.addWidget(self.message)
        buttons = QtWidgets.QHBoxLayout()
        self.apply = QtWidgets.QPushButton("Apply")
        self.apply.setObjectName("AzSketchPatternApply")
        self.apply.setEnabled(False)
        buttons.addWidget(self.apply)
        cancel = QtWidgets.QPushButton("Cancel · Esc")
        buttons.addWidget(cancel)
        vertical.addLayout(buttons)

        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(170)
        self.timer.timeout.connect(self.preview)
        self.source.currentIndexChanged.connect(self.queue_preview)
        for field in (self.columns, self.rows):
            field.valueChanged.connect(self.queue_preview)
        for field in (self.pitch_x, self.pitch_y):
            field.valueChanged.connect(self.queue_preview)
        self.apply.clicked.connect(self.accept)
        cancel.clicked.connect(self.cancel)

        self.handles = PatternCanvasHandles(
            lambda axis: self.pitch_x.value() if axis == "x" else self.pitch_y.value(),
            lambda axis, value: (
                self.pitch_x if axis == "x" else self.pitch_y
            ).setValue(value),
            mode="sketch", parent=session.mdi.viewport(),
            get_counts=lambda: (self.columns.value(), self.rows.value()),
        )
        self.handles.hide()
        self.adjustSize()

    def choose_circle(self, index):
        if not self._done and index in self.candidates:
            self.source.setCurrentIndex(self.candidates.index(index))

    def show_panel(self):
        Gui.Selection.addObserver(self.observer)
        self._selection_observer_attached = True
        parent = self.parentWidget()
        self.move(max(8, parent.width() - self.width() - 15), 14)
        self.handles.move(max(8, self.x() - 190), 20)
        self.show()
        self.raise_()
        self.handles.show()
        self.handles.raise_()
        self.queue_preview()

    def queue_preview(self, *_):
        if not self._done:
            self.apply.setEnabled(False)
            self.timer.start()

    def preview(self):
        if self._done:
            return
        try:
            # Source choices refer only to pre-preview sketch geometry.
            if self.sketch.GeometryCount < self.draft.original_geometry_count:
                raise DesignError("The source sketch changed during Pattern. Cancel and retry.")
            created = self.draft.preview(
                self.source.currentData(), self.columns.value(),
                self.rows.value(), self.pitch_x.value(), self.pitch_y.value(),
            )
            self.message.setText(
                "{} live circles · Finish Sketch, then use Hole.".format(
                    len(created) + 1
                )
            )
            self.message.setStyleSheet("color: #277555;")
            self.apply.setEnabled(True)
        except Exception as exc:
            self.draft.valid = False
            self.message.setText("Preview unavailable: " + str(exc))
            self.message.setStyleSheet("color: #a14836;")
            self.apply.setEnabled(False)

    def accept(self, *_):
        if self._done:
            return
        try:
            created = self.draft.accept()
            from .commands import notify
            notify("{} hole centers patterned. Finish Sketch → Hole.".format(len(created) + 1))
            self._cleanup()
        except Exception as exc:
            self.message.setText("Cannot apply pattern: " + str(exc))
            self.apply.setEnabled(False)

    def _cleanup(self):
        global _active
        self._done = True
        self.timer.stop()
        if self._selection_observer_attached:
            try:
                Gui.Selection.removeObserver(self.observer)
            except (RuntimeError, ReferenceError):
                pass
            self._selection_observer_attached = False
        self.handles.hide()
        self.handles.deleteLater()
        self.hide()
        self.deleteLater()
        if _active is self:
            _active = None

    def cancel(self, *_):
        if self._done:
            return
        self.draft.cancel()
        self._cleanup()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.cancel()
            event.accept()
        else:
            super().keyPressEvent(event)


def show():
    global _active
    from .session import current
    sketch = modeling.in_sketch()
    if sketch is None:
        raise DesignError("Edit a sketch and draw one circle before using Rectangular Pattern.")
    session = current()
    if not session or not session.active:
        raise DesignError("Activate the Design workbench before Sketch Pattern.")
    if _active is not None:
        _active.cancel()
    if not sketch_pattern.circle_indices(sketch):
        raise DesignError("Draw a circle to pattern into hole locations.")
    panel = SketchPatternPanel(session, sketch)
    _active = panel
    panel.show_panel()
    return panel


def cancel_active():
    if _active is None:
        return False
    _active.cancel()
    return True
