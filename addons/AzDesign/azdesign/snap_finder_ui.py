# SPDX-License-Identifier: LGPL-2.1-or-later
"""Fusion-inspired exact edge snap/center finder using native FreeCAD geometry."""

import FreeCADGui as Gui

from . import modeling, snap_targets
from .features import DesignError
from .qt import QtWidgets


def selected_targets():
    entries = Gui.Selection.getSelectionEx()
    if len(entries) != 1:
        raise DesignError("Select an edge or a set of edges on ONE model object.")
    item = entries[0]
    return snap_targets.from_object(item.Object, item.SubElementNames)


class SnapFinder(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AzSnapFinder")
        self.setWindowTitle("Snap & Center Finder · Az Design")
        self.setMinimumWidth(410)
        self.targets = ()
        self.setStyleSheet("""
            QDialog#AzSnapFinder { background: #f7f9fb; color: #304b60; }
            QDialog#AzSnapFinder QLabel { color: #385468; }
            QDialog#AzSnapFinder QListWidget {
                color: #294457; background: #fff;
                selection-background-color: #c5e2f6; selection-color: #203e55;
                border: 1px solid #b9c9d4; }
            QDialog#AzSnapFinder QPushButton {
                background: #e3eef6; color: #254b68; border-radius: 4px;
                border: 1px solid #acc7d7; padding: 5px 7px; }
        """)
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(
            "Select a straight or circular edge in the model. "
            "Get exact endpoints, midpoints and circle/arc centers."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.items = QtWidgets.QListWidget()
        self.items.setObjectName("AzSnapCandidateList")
        self.items.setMaximumHeight(165)
        layout.addWidget(self.items)
        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        top = QtWidgets.QHBoxLayout()
        refresh = QtWidgets.QPushButton("Read selection")
        refresh.clicked.connect(self.refresh)
        copy = QtWidgets.QPushButton("Copy XYZ")
        copy.clicked.connect(self.copy_xyz)
        top.addWidget(refresh)
        top.addWidget(copy)
        layout.addLayout(top)
        middle = QtWidgets.QHBoxLayout()
        insert = QtWidgets.QPushButton("Place sketch reference")
        insert.setToolTip(
            "Places a fixed construction point at the snapped coordinate, "
            "projected onto the active sketch plane. Not an associative link."
        )
        insert.clicked.connect(self.insert_sketch)
        native = QtWidgets.QPushButton("Enable sketch auto constraints")
        native.clicked.connect(self.enable_native)
        middle.addWidget(insert)
        middle.addWidget(native)
        layout.addLayout(middle)
        info = QtWidgets.QLabel(
            "Sketcher's native snapping already handles lines, endpoints "
            "and midpoints while drawing. Placed reference points are FIXED "
            "and do not follow later edits of the source edge."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        close = QtWidgets.QPushButton("Close")
        close.clicked.connect(self.close)
        layout.addWidget(close)
        self.refresh()

    def refresh(self):
        self.items.clear()
        self.targets = ()
        try:
            self.targets = selected_targets()
            for target in self.targets:
                coords = ", ".join(format(x, ".6g") for x in target.coordinates())
                self.items.addItem(
                    target.edge_name + " · " + target.name + "  (" + coords + ") mm"
                )
            self.items.setCurrentRow(0)
            self.status.setText(
                str(len(self.targets)) + " exact geometric snap targets found."
            )
        except DesignError as exc:
            self.status.setText(str(exc))

    def current_target(self):
        index = self.items.currentRow()
        if not 0 <= index < len(self.targets):
            raise DesignError("Select a snap target in the list.")
        return self.targets[index]

    def copy_xyz(self):
        try:
            point = self.current_target()
            coord = ", ".join(format(n, ".9g") for n in point.coordinates())
            QtWidgets.QApplication.clipboard().setText(coord)
            self.status.setText("Copied " + point.name + " XYZ: " + coord + " mm")
        except DesignError as exc:
            self.status.setText(str(exc))

    def insert_sketch(self):
        try:
            target = self.current_target()
            sketch = modeling.in_sketch()
            if not sketch:
                raise DesignError(
                    "Open a sketch for editing first. The selected snap target "
                    "will remain in this finder window."
                )
            index = snap_targets.create_sketch_reference(sketch, target)
            self.status.setText(
                "Construction point " + str(index) + " placed at projected "
                + target.name.lower() + ". This is a fixed, non-associative reference."
            )
        except (DesignError, RuntimeError) as exc:
            self.status.setText(str(exc))

    def enable_native(self):
        sketch = modeling.in_sketch()
        if not sketch:
            self.status.setText("Open a sketch before enabling auto constraints.")
            return
        provider = sketch.ViewObject
        if hasattr(provider, "Autoconstraints"):
            provider.Autoconstraints = True
        try:
            actions = Gui.Command.get("Sketcher_Snap").getAction()
            if not isinstance(actions, (tuple, list)):
                actions = [actions]
            for action in actions:
                if action and action.isCheckable() and not action.isChecked():
                    action.trigger()
        except (AttributeError, RuntimeError, TypeError):
            pass
        self.status.setText(
            "Native Sketcher auto constraints enabled. "
            "Endpoint/midpoint snap remains controlled by FreeCAD itself."
        )


def show():
    parent = Gui.getMainWindow()
    previous = getattr(parent, "_az_snap_finder", None)
    if previous is not None and previous.isVisible():
        previous.raise_()
        previous.refresh()
        return previous
    dialog = SnapFinder(parent)
    parent._az_snap_finder = dialog
    dialog.show()
    return dialog
