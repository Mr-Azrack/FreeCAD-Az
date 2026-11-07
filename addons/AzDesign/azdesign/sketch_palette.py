# SPDX-License-Identifier: LGPL-2.1-or-later
"""Persistent Az sketch controls beside FreeCAD's native solver task view.

Never substitute Az state for Sketcher's constraint solver. Properties shown
here are discovered at runtime because FreeCAD 1.0 and 1.1 differ.
"""

import FreeCADGui as Gui
from .qt import QtCore, QtWidgets
from . import commands


class SketchPalette(QtWidgets.QWidget):
    """Small Fusion-inspired palette with native sketch commands and flags."""

    def __init__(self, appearance, parent=None):
        super().__init__(parent)
        self.setObjectName("AzSketchPalette")
        self.appearance = appearance
        self.sketch = None
        self.setStyleSheet("""
        QWidget#AzSketchPalette { background: #f7f9fb; color: #314b5b; }
        QWidget#AzSketchPalette QGroupBox { border: 1px solid #d9e2ea;
            border-radius: 5px; margin-top: 11px; padding: 8px 4px 4px; }
        QWidget#AzSketchPalette QGroupBox::title { subcontrol-origin: margin;
            left: 9px; color: #42627a; font-weight: 600; }
        QWidget#AzSketchPalette QPushButton { background: #e8eff5;
            border: 1px solid #cedce7; border-radius: 4px; padding: 5px; }
        QWidget#AzSketchPalette QPushButton:hover { background: #d8e7f5; }
        QWidget#AzSketchPalette QLabel { color: #687c89; }
        """)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(9)
        title = QtWidgets.QLabel("SKETCH PALETTE")
        title.setStyleSheet("font-weight: 700; font-size: 13px; color: #31536b;")
        layout.addWidget(title)
        self.summary = QtWidgets.QLabel("Open a sketch to see constraints")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        display = QtWidgets.QGroupBox("Display & snapping")
        disp = QtWidgets.QVBoxLayout(display)
        self.flags = {}
        for label, key in (
            ("Show grid", "grid"),
            ("Snap to grid", "SnapToGrid"),
            ("Show constraints", "ShowConstraints"),
            ("Show dimensions", "ShowDimensions"),
            ("Show profiles", "ShowProfiles"),
        ):
            box = QtWidgets.QCheckBox(label)
            box.setObjectName("AzSketch_" + key)
            box.setToolTip(
                "Uses a native FreeCAD sketch display property when available. "
                "Unavailable properties are disabled, not simulated."
            )
            box.toggled.connect(lambda enabled, key=key: self.set_flag(key, enabled))
            self.flags[key] = box
            disp.addWidget(box)
        layout.addWidget(display)

        tools = QtWidgets.QGroupBox("Sketch tools")
        tool_layout = QtWidgets.QGridLayout(tools)
        for i, (name, command) in enumerate((
            ("Rectangle", "Sketcher_CreateRectangle"),
            ("Circle", "Sketcher_CreateCircle"),
            ("Line", "Sketcher_CreatePolyline"),
            ("Dimension", "Az_Dimension"),
            ("Construction", "Sketcher_ToggleConstruction"),
            ("Project", "Sketcher_External"),
        )):
            button = QtWidgets.QPushButton(name)
            button.setObjectName("AzSketchTool_" + name)
            button.setToolTip("Native Sketcher tool · " + command)
            button.clicked.connect(
                lambda _checked=False, command=command: self.run_sketch(command)
            )
            tool_layout.addWidget(button, i // 2, i % 2)
        layout.addWidget(tools)
        self.finish = QtWidgets.QPushButton("Finish Sketch")
        self.finish.setObjectName("AzFinishSketchPalette")
        self.finish.setStyleSheet(
            "background: #dbeed9; border: 1px solid #a8ceab; "
            "font-weight: 600; padding: 8px;"
        )
        self.finish.clicked.connect(
            lambda _checked=False: self.run_sketch("Az_FinishSketch")
        )
        layout.addWidget(self.finish)
        hint = QtWidgets.QLabel(
            "Sketcher remains the constraint solver. The native Tasks panel "
            "continues to provide advanced constraints and diagnostics."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()

    def run_sketch(self, command):
        if self.sketch and command in Gui.listCommands():
            commands.invoke(command)

    def set_flag(self, name, checked):
        if not self.sketch:
            return
        if name == "grid":
            self.appearance.toggle_grid(checked)
            return
        provider = self.sketch.ViewObject
        if hasattr(provider, name):
            try:
                setattr(provider, name, checked)
            except (RuntimeError, ValueError, TypeError):
                pass

    def refresh(self, sketch):
        self.sketch = sketch
        if sketch is None:
            self.summary.setText("Open a sketch to edit its dimensions and constraints.")
            return
        geometry = getattr(sketch, "GeometryCount", 0)
        constraints = getattr(sketch, "ConstraintCount", 0)
        fully = getattr(sketch, "FullyConstrained", None)
        status = ("Fully constrained" if fully else "Under constrained") if fully is not None else ""
        self.summary.setText(
            sketch.Label + " · " + str(geometry) + " geometry · "
            + str(constraints) + " constraints"
            + ("\n" + status if status else "")
        )
        provider = sketch.ViewObject
        for name, box in self.flags.items():
            box.blockSignals(True)
            if name == "grid":
                box.setEnabled(True)
                box.setChecked(self.appearance.grid_visible)
            else:
                supported = hasattr(provider, name)
                box.setEnabled(supported)
                if supported:
                    try:
                        box.setChecked(bool(getattr(provider, name)))
                    except (RuntimeError, TypeError):
                        box.setEnabled(False)
                else:
                    box.setChecked(False)
            box.blockSignals(False)
