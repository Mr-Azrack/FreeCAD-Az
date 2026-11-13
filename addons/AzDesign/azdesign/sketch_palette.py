# SPDX-License-Identifier: LGPL-2.1-or-later
"""Compact sketch options backed by FreeCAD's *real* Sketcher controls.

This is a small settings palette, NOT a second set of drawing tools or a
replacement for FreeCAD's native Sketcher Tasks and constraint solver.
"""

import FreeCADGui as Gui
from .qt import QtCore, QtWidgets


# These four ViewProviderSketch properties are documented in FreeCAD 1.0/1.1.
# Do NOT add imagined "ShowProfiles" or "ShowDimensions" Python properties:
# they do not operate Sketcher editing controls.
NATIVE_PROPERTIES = (
    ("grid", "Show grid", "ShowGrid"),
    ("auto_grid", "Auto grid spacing", "GridAuto"),
    ("auto_constraints", "Auto constraints", "Autoconstraints"),
    ("avoid_redundant", "Avoid redundant constraints", "AvoidRedundant"),
)

TOOLTIPS = {
    "grid": "Show or hide FreeCAD's actual sketch grid.",
    "auto_grid": "Resize native sketch grid spacing while zooming.",
    "auto_constraints": "Automatically suggest/apply geometric constraints while drawing new sketch geometry.",
    "avoid_redundant": "Prevent Sketcher adding redundant constraints while drawing.",
    "snap": "Use FreeCAD's native sketch snapping while drawing new geometry; does not change existing geometry.",
}


def native_checked_action(command):
    """Return the native checked QAction, not an untestable fake toggle."""
    try:
        actions = Gui.Command.get(command).getAction()
        if not isinstance(actions, (tuple, list)):
            actions = [actions]
        return next(
            (a for a in actions if a and a.isCheckable()), None
        )
    except (AttributeError, RuntimeError, TypeError, NameError):
        return None


class SketchPalette(QtWidgets.QWidget):
    """Small option-only palette; drawing commands remain on the top ribbon."""

    def __init__(self, appearance, parent=None):
        super().__init__(parent)
        self.setObjectName("AzSketchPalette")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.appearance = appearance
        self.sketch = None
        self.flags = {}
        self.setStyleSheet("""
        QWidget#AzSketchPalette {
            background-color: #f5f8fb; color: #243e51;
            border: 0; }
        QWidget#AzSketchPalette QLabel {
            color: #36556b; background: transparent; font-size: 11px; }
        QWidget#AzSketchPalette QLabel#AzSketchHeader {
            color: #285a79; font-weight: 700; font-size: 12px; }
        QWidget#AzSketchPalette QLabel#AzSketchSummary {
            color: #526c7c; font-size: 10px; }
        QWidget#AzSketchPalette QCheckBox {
            color: #263e50; background: transparent;
            font-size: 11px; spacing: 9px; padding: 2px 0; }
        QWidget#AzSketchPalette QCheckBox:disabled {
            color: #788b98; }
        QWidget#AzSketchPalette QCheckBox::indicator {
            width: 15px; height: 15px; }
        QWidget#AzSketchPalette QCheckBox::indicator:unchecked {
            background: #fff; border: 1px solid #809bac;
            border-radius: 3px; }
        QWidget#AzSketchPalette QCheckBox::indicator:checked {
            background: #387da4; border: 1px solid #286083;
            border-radius: 3px; }
        QWidget#AzSketchPalette QPushButton {
            color: #275475; background: #e4eff7;
            border: 1px solid #afc7d7; border-radius: 4px;
            font-weight: 600; padding: 5px 8px; }
        QWidget#AzSketchPalette QPushButton:hover {
            background: #d1e5f3; }
        """)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)
        header = QtWidgets.QLabel("SKETCH PALETTE")
        header.setObjectName("AzSketchHeader")
        layout.addWidget(header)
        self.summary = QtWidgets.QLabel("Sketch options")
        self.summary.setObjectName("AzSketchSummary")
        self.summary.setWordWrap(True)
        self.summary.setMaximumHeight(34)
        layout.addWidget(self.summary)

        for key, label, _native in NATIVE_PROPERTIES:
            control = QtWidgets.QCheckBox(label)
            control.setObjectName("AzSketch_" + key)
            control.setToolTip(TOOLTIPS[key])
            control.toggled.connect(
                lambda checked, key=key: self.set_flag(key, checked)
            )
            self.flags[key] = control
            layout.addWidget(control)

        # Snap is native GUI state, NOT a ViewProviderSketch property.
        # Its QAction must exist and be checkable; otherwise don't display an
        # inert checkbox. FreeCAD's native Sketcher UI remains available.
        snap = QtWidgets.QCheckBox("Snap while drawing")
        snap.setObjectName("AzSketch_snap")
        snap.setToolTip(TOOLTIPS["snap"])
        snap.toggled.connect(
            lambda checked: self.set_flag("snap", checked)
        )
        self.flags["snap"] = snap
        layout.addWidget(snap)

        # One explicit action projects the preceding solid's in-plane edges
        # into native, associative Sketcher geometry. Unlike a decorative
        # hover marker, these are usable by FreeCAD's real snap manager.
        self.solid_snap = QtWidgets.QPushButton("Use solid edges for snapping")
        self.solid_snap.setObjectName("AzSketchSolidSnap")
        self.solid_snap.setToolTip(
            "Reference coplanar edges from the preceding Body feature. "
            "Undoable; repeated clicks do not duplicate references. "
            "Solid topology changes may require repairing references."
        )
        self.solid_snap.clicked.connect(self.enable_solid_snap)
        layout.addWidget(self.solid_snap)

        # No second Rectangle/Circle/Finish Sketch palette: those already
        # occupy the ribbon. This dock MUST NOT grow beyond the viewport.
        self.setMinimumWidth(215)
        self.setMaximumHeight(270)

    def enable_solid_snap(self):
        if self.sketch is None:
            return
        try:
            import FreeCAD as App
            from .snap_targets import enable_solid_edge_snapping
            count = enable_solid_edge_snapping(self.sketch)
            self.solid_snap.setText("Solid edges ready ({} linked)".format(count)
                                    if count else "Solid edges ready (existing links)")
            snap = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Sketcher/Snap")
            snap.SetBool("Snap", True)
            snap.SetBool("SnapToObjects", True)
            self.sketch.ViewObject.Autoconstraints = True
            self.summary.setText(
                "{} solid-edge reference(s) ready; native object snapping enabled".format(count)
                if count else "Existing solid references retained; native object snapping enabled"
            )
        except Exception as exc:
            self.summary.setText("Cannot enable solid snapping: " + str(exc))
            App.Console.PrintWarning("Az solid-edge snapping: " + str(exc) + "\n")

    def set_flag(self, key, checked):
        if not self.sketch:
            return
        if key == "snap":
            action = native_checked_action("Sketcher_Snap")
            if action is None:
                return
            if bool(action.isChecked()) != bool(checked):
                action.trigger()
            return
        if key == "grid":
            self.appearance.toggle_grid(checked)
            return
        provider = self.sketch.ViewObject
        field = next(
            (field for name, _label, field in NATIVE_PROPERTIES if name == key),
            None,
        )
        if field is None or not hasattr(provider, field):
            return
        try:
            setattr(provider, field, bool(checked))
        except (RuntimeError, ValueError, TypeError) as exc:
            import FreeCAD as App
            App.Console.PrintWarning(
                "Az Sketch Palette: cannot change " + field + ": " + str(exc) + "\n"
            )
        self.refresh(self.sketch)

    def refresh(self, sketch):
        self.sketch = sketch
        if sketch is None:
            self.summary.setText("Edit a sketch to see its options")
            return
        geometry = getattr(sketch, "GeometryCount", 0)
        constraints = getattr(sketch, "ConstraintCount", 0)
        self.summary.setText(
            str(sketch.Label) + " · " + str(geometry)
            + " curves · " + str(constraints) + " constraints"
        )
        provider = sketch.ViewObject
        for name, _label, field in NATIVE_PROPERTIES:
            control = self.flags[name]
            supported = (name == "grid" or hasattr(provider, field))
            control.blockSignals(True)
            control.setVisible(supported)  # No dead placeholder controls.
            control.setEnabled(supported)
            if supported:
                try:
                    value = (
                        self.appearance.grid_visible if name == "grid"
                        else bool(getattr(provider, field))
                    )
                    control.setChecked(value)
                except (RuntimeError, ValueError, TypeError):
                    control.setEnabled(False)
            control.blockSignals(False)

        snap_action = native_checked_action("Sketcher_Snap")
        snap = self.flags["snap"]
        snap.blockSignals(True)
        snap.setVisible(snap_action is not None)
        snap.setEnabled(snap_action is not None)
        if snap_action is not None:
            snap.setChecked(bool(snap_action.isChecked()))
        snap.blockSignals(False)
