# SPDX-License-Identifier: LGPL-2.1-or-later
"""Az Fillet/Chamfer: validate an exact native OCCT result before committing."""

import FreeCADGui as Gui

from . import edge_treatments
from .features import DesignError
from .qt import QtCore, QtWidgets


def selection():
    selected = Gui.Selection.getSelectionEx()
    if len(selected) != 1:
        raise DesignError("Select one or more edges on ONE solid before Fillet/Chamfer.")
    entry = selected[0]
    obj = entry.Object
    if obj is None:
        raise DesignError("Select a solid edge.")
    if obj.isDerivedFrom("PartDesign::Body"):
        # A Body is a visual container. Commit a native feature against the
        # current Tip rather than linking the Body back to itself.
        obj = obj.Tip
    if obj is None:
        raise DesignError("The selected Body has no solid Tip.")
    names = edge_treatments.selected_edges(obj, entry.SubElementNames)
    return obj, names


class EdgeTreatmentDialog(QtWidgets.QDialog):
    def __init__(self, obj, names, kind, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.names = names
        self.kind = kind
        self.result_feature = None
        self.setObjectName("AzEdgeTreatmentDialog")
        self.setWindowTitle(kind + " · Az Design")
        self.setMinimumWidth(350)
        self.setStyleSheet("""
          QDialog#AzEdgeTreatmentDialog { background: #f6f8fa; color: #2c4558; }
          QDialog#AzEdgeTreatmentDialog QLabel { color: #39586b; }
          QDialog#AzEdgeTreatmentDialog QPushButton {
              background: #e7f0f7; color: #264963;
              border: 1px solid #aac5d5; padding: 6px; border-radius: 4px; }
          QDialog#AzEdgeTreatmentDialog QDoubleSpinBox {
              background: white; color: #243f50;
              border: 1px solid #aac2d3; padding: 5px; }
        """)
        layout = QtWidgets.QVBoxLayout(self)
        info = QtWidgets.QLabel(
            obj.Label + " · " + ", ".join(names)
            + "\nOriginal solid stays unchanged until Create."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        form = QtWidgets.QFormLayout()
        self.size = QtWidgets.QDoubleSpinBox()
        self.size.setObjectName("AzEdgeSize")
        self.size.setDecimals(6)
        self.size.setRange(0.000001, 100000)
        self.size.setSingleStep(0.01)
        self.size.setSuffix(" mm")
        lengths = [
            length for length in (
                obj.Shape.BoundBox.XLength,
                obj.Shape.BoundBox.YLength,
                obj.Shape.BoundBox.ZLength,
            ) if length > 1e-7
        ]
        suggested = min(0.5, min(lengths) * 0.1) if lengths else 0.1
        self.size.setValue(max(0.000001, suggested))
        form.addRow("Radius" if kind == "Fillet" else "Chamfer distance", self.size)
        layout.addLayout(form)
        self.status = QtWidgets.QLabel(
            "Press Validate to check the real OCCT result without editing the design."
        )
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        actions = QtWidgets.QHBoxLayout()
        validate = QtWidgets.QPushButton("Validate geometry")
        validate.clicked.connect(self.validate)
        smaller = QtWidgets.QPushButton("Find smaller valid size")
        smaller.clicked.connect(self.suggest_smaller)
        actions.addWidget(validate)
        actions.addWidget(smaller)
        layout.addLayout(actions)
        bottom = QtWidgets.QHBoxLayout()
        create = QtWidgets.QPushButton("Create " + kind)
        create.setObjectName("AzEdgeCreate")
        create.clicked.connect(self.create_feature)
        cancel = QtWidgets.QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        bottom.addWidget(create)
        bottom.addWidget(cancel)
        layout.addLayout(bottom)
        self.size.valueChanged.connect(
            lambda _value: self.status.setText(
                "Size changed · Validate before creating the feature."
            )
        )

    def feedback(self, message, failed=False):
        self.status.setText(message)
        self.status.setStyleSheet(
            "color: #a63d35;" if failed else "color: #207247;"
        )

    def validate(self):
        try:
            edge_treatments.preflight(
                self.obj, self.names, self.size.value(), self.kind
            )
            self.feedback(
                "Valid native " + self.kind + " · one solid, no document changes."
            )
            return True
        except DesignError as exc:
            self.feedback(str(exc), True)
            return False

    def suggest_smaller(self):
        size = edge_treatments.probe_smaller(
            self.obj, self.names, self.size.value(), self.kind
        )
        if size is None:
            self.feedback(
                "No valid result in the tested smaller sizes. Try one edge "
                "or a different edge selection.", True
            )
        else:
            self.size.setValue(size)
            self.feedback("Kernel-validated smaller value: " + format(size, ".6g") + " mm")

    def create_feature(self):
        if not self.validate():
            return
        try:
            self.result_feature = edge_treatments.create(
                self.obj, self.names, self.size.value(), self.kind
            )
            self.accept()
        except DesignError as exc:
            self.feedback(str(exc), True)
        except Exception as exc:
            self.feedback("Native " + self.kind + " error: " + str(exc), True)


def show(kind):
    if Gui.Control.activeDialog():
        raise DesignError("Finish or cancel the current FreeCAD task first.")
    obj, names = selection()
    form = EdgeTreatmentDialog(obj, names, kind, Gui.getMainWindow())
    run = getattr(form, "exec", None) or form.exec_
    run()
    if form.result_feature:
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(form.result_feature)
        return form.result_feature
    return None
