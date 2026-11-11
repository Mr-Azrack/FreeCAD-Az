# SPDX-License-Identifier: LGPL-2.1-or-later
"""Fusion-style, nonmodal Design edge finishing controls.

The viewport stays interactive while selecting edges. Each dimension change
preflights the actual OCCT result, and nothing is added to the document until
Apply. No raw FreeCAD Fillet/Chamfer task pane is needed.
"""
import FreeCADGui as Gui

from . import edge_treatments
from .features import DesignError, owner_body
from .qt import QtCore, QtWidgets

_active = None


class _SelectionObserver:
    def __init__(self, panel):
        self.panel = panel

    def addSelection(self, *_args):
        self._schedule()

    def removeSelection(self, *_args):
        self._schedule()

    def clearSelection(self, *_args):
        self._schedule()

    def _schedule(self):
        panel = self.panel
        if not panel.finished:
            QtCore.QTimer.singleShot(0, panel.refresh_selection)


class EdgeTreatmentPanel(QtWidgets.QFrame):
    def __init__(self, session, kind, editing=None):
        super().__init__()
        self.editing = editing
        self.session = session
        self.kind = kind
        self.finished = False
        self.obj = None
        self.names = ()
        self.valid = False
        self.observer = _SelectionObserver(self)
        self.setObjectName("AzEdgeTreatmentCanvas")
        self.setStyleSheet("""
            QFrame#AzEdgeTreatmentCanvas {
                background: #fbfdff; border: 1px solid #9dbed1;
                border-radius: 8px;
            }
            QFrame#AzEdgeTreatmentCanvas QLabel {
                background: transparent; color: #294b63;
            }
            QFrame#AzEdgeTreatmentCanvas QPushButton {
                min-height: 29px; background: #e2eef7;
                color: #24546d; border: 1px solid #a7c5d6;
                border-radius: 5px; padding: 5px;
            }
            QFrame#AzEdgeTreatmentCanvas QPushButton#AzEdgeApply {
                background: #21749f; color: white; font-weight: 600;
            }
        """)
        self.setMinimumWidth(270)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 11, 12, 11)
        layout.setSpacing(8)
        title = QtWidgets.QLabel(
            ("EDIT " if editing else "SOLID · ") + kind.upper()
        )
        title.setStyleSheet("font-size: 14px; font-weight: 700;")
        layout.addWidget(title)
        hint = QtWidgets.QLabel(
            ("Edit the original feature's size. The model history remains parametric."
             if editing else
             "Click edges on the model (Ctrl+click for several). "
             "Change the size below, then Apply. Esc cancels.")
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.edge_label = QtWidgets.QLabel("Select one or more edges")
        self.edge_label.setWordWrap(True)
        layout.addWidget(self.edge_label)
        form = QtWidgets.QFormLayout()
        self.size = QtWidgets.QDoubleSpinBox()
        self.size.setObjectName("AzEdgeSize")
        self.size.setDecimals(4)
        self.size.setRange(0.0001, 100000)
        self.size.setSingleStep(0.1)
        self.size.setSuffix(" mm")
        initial = (
            getattr(editing, "Radius" if kind == "Fillet" else "Size", 0.5)
            if editing is not None else 0.5
        )
        self.size.setValue(float(getattr(initial, "Value", initial)))
        form.addRow("Radius" if kind == "Fillet" else "Distance", self.size)
        layout.addLayout(form)
        self.status = QtWidgets.QLabel("Select solid edges to check with the geometry engine.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        actions = QtWidgets.QHBoxLayout()
        self.apply = QtWidgets.QPushButton("Apply " + kind)
        self.apply.setObjectName("AzEdgeApply")
        self.apply.setEnabled(False)
        cancel = QtWidgets.QPushButton("Cancel · Esc")
        actions.addWidget(self.apply)
        actions.addWidget(cancel)
        layout.addLayout(actions)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.preflight)
        self.size.valueChanged.connect(lambda _value: self.queue_preflight())
        self.apply.clicked.connect(self.accept)
        cancel.clicked.connect(self.cancel)
        self.adjustSize()

    def show_panel(self):
        if self.editing is None:
            Gui.Selection.addObserver(self.observer)
        self.dock = QtWidgets.QDockWidget(self.kind + " Tasks", self.session.main)
        self.dock.setObjectName("AzEdgeTreatmentDock")
        self.dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.dock.setWidget(self)
        self.session.main.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)
        if self.session.tasks_dock:
            self.session.main.tabifyDockWidget(self.session.tasks_dock, self.dock)
        self.dock.show()
        self.dock.raise_()
        self.refresh_selection()

    def _message(self, value, valid=False):
        self.status.setText(value)
        self.status.setStyleSheet(
            "color: #26754d;" if valid else "color: #a14b39;"
        )
        self.valid = valid
        self.apply.setEnabled(valid)

    def refresh_selection(self):
        if self.finished:
            return
        if self.editing is not None:
            base = getattr(self.editing, "Base", ())
            self.obj = base[0] if isinstance(base, (tuple, list)) and base else None
            self.names = (
                tuple(base[1]) if len(base) > 1
                else ()
            )
            if self.obj is None or not self.names:
                self._message("Cannot recover the original feature edge selection.")
                return
            self.edge_label.setText(
                "{} · {} original edge{}".format(
                    self.obj.Label, len(self.names),
                    "" if len(self.names) == 1 else "s",
                )
            )
            self.queue_preflight()
            return
        self.obj, self.names = None, ()
        selected = Gui.Selection.getSelectionEx()
        if len(selected) == 1:
            entry = selected[0]
            obj = entry.Object
            if obj is not None:
                if obj.isDerivedFrom("PartDesign::Body"):
                    obj = obj.Tip
                if obj is not None and owner_body(obj) is not None:
                    names = [
                        name for name in entry.SubElementNames
                        if name.startswith("Edge")
                    ]
                    if names:
                        try:
                            self.names = edge_treatments.selected_edges(obj, names)
                            self.obj = obj
                        except DesignError as exc:
                            self._message(str(exc))
        if self.obj is None:
            self.edge_label.setText("Select edges on one solid · Ctrl+click to add")
            self.timer.stop()
            self._message("No valid solid edges selected.")
            return
        self.edge_label.setText(
            "{} · {} edge{}".format(
                self.obj.Label, len(self.names),
                "" if len(self.names) == 1 else "s",
            )
        )
        self.queue_preflight()

    def queue_preflight(self):
        if self.finished:
            return
        self.valid = False
        self.apply.setEnabled(False)
        if self.obj is not None and self.names:
            self.timer.start()

    def preflight(self):
        if self.finished or self.obj is None or not self.names:
            return
        try:
            body = owner_body(self.obj)
            if body is None or (self.editing is None and body.Tip != self.obj):
                raise DesignError("Select edges on the current final Body feature.")
            edge_treatments.preflight(
                self.obj, self.names, self.size.value(), self.kind
            )
            self._message(
                "Valid on {} edge{} · ready to apply.".format(
                    len(self.names), "" if len(self.names) == 1 else "s"
                ), True
            )
        except Exception as exc:
            self._message("Invalid size or edge selection: " + str(exc))

    def accept(self, *_args):
        if self.finished:
            return
        self.timer.stop()
        self.preflight()
        if not self.valid:
            return
        try:
            if self.editing is not None:
                doc = self.editing.Document
                doc.openTransaction("Design: Edit " + self.kind)
                try:
                    field = "Radius" if self.kind == "Fillet" else "Size"
                    setattr(self.editing, field, self.size.value())
                    doc.recompute()
                    shape = self.editing.Shape
                    if (
                        shape.isNull() or not shape.isValid()
                        or len(shape.Solids) != 1
                        or "Invalid" in getattr(self.editing, "State", ())
                    ):
                        raise DesignError("The edited feature would invalidate the solid.")
                    doc.commitTransaction()
                except Exception:
                    doc.abortTransaction()
                    doc.recompute()
                    raise
                result = self.editing
            else:
                result = edge_treatments.create(
                    self.obj, self.names, self.size.value(), self.kind
                )
            self._cleanup()
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(result)
            try:
                self.session.history.signature = None
                self.session.history.refresh()
            except (AttributeError, RuntimeError):
                pass
        except Exception as exc:
            self._message("Cannot create " + self.kind + ": " + str(exc))

    def _cleanup(self):
        global _active
        self.finished = True
        self.timer.stop()
        if self.editing is None:
            try:
                Gui.Selection.removeObserver(self.observer)
            except (RuntimeError, ReferenceError):
                pass
        self.hide()
        if getattr(self, "dock", None):
            self.dock.hide()
            self.dock.deleteLater()
        else:
            self.deleteLater()
        if _active is self:
            _active = None

    def cancel(self, *_args):
        if not self.finished:
            self._cleanup()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.cancel()
            event.accept()
        else:
            super().keyPressEvent(event)


def show(kind, editing=None):
    global _active
    if kind not in ("Fillet", "Chamfer"):
        raise DesignError("Choose Fillet or Chamfer.")
    if Gui.Control.activeDialog():
        raise DesignError("Finish the active sketch or task before rounding edges.")
    from .session import current
    session = current()
    if not session or not session.active:
        raise DesignError("Activate Design to use the in-canvas edge controls.")
    if _active is not None:
        _active.cancel()
    panel = EdgeTreatmentPanel(session, kind, editing)
    _active = panel
    panel.show_panel()
    return panel


def cancel_active():
    if _active is None:
        return False
    _active.cancel()
    return True
