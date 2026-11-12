# SPDX-License-Identifier: LGPL-2.1-or-later
"""Automatic, mouse-transparent midpoint and center markers while sketching.

Native Sketcher owns mouse clicks, snap coordinates, AutoConstraints and
geometry creation. We only present visible cues at real sketch coordinates;
never simulate Qt click events or silently insert fixed geometry.
"""

import FreeCADGui as Gui

from . import modeling, snap_hover
from .snap_targets import viewport_passive_cue
from .qt import QtCore, QtWidgets


class HoverGuides:
    SYMBOLS = {"Midpoint": "△", "Center": "⊙", "Endpoint": "□", "Start": "□", "End": "□"}

    def __init__(self):
        self.label = None
        self.owner = None
        self.last = None

    def hide(self):
        if self.label is not None:
            self.label.hide()
        self.last = None

    def release(self):
        if self.label is not None:
            self.label.hide()
            self.label.setParent(None)
            self.label.deleteLater()
        self.label = None
        self.owner = None
        self.last = None

    def _make_label(self, widget):
        if self.owner is widget and self.label is not None:
            return
        self.release()
        self.owner = widget
        self.label = QtWidgets.QLabel(widget)
        self.label.setObjectName("AzSketchHoverSnap")
        self.label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.label.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.label.setFixedSize(16, 16)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("""
        QLabel#AzSketchHoverSnap {
            background: transparent; border: none;
            color: #008fa9; font: bold 13px Arial;
        }
        """)
        self.label.hide()

    def move(self, widget, event):
        sketch = modeling.in_sketch()
        if not sketch:
            self.hide()
            return
        active = Gui.activeDocument()
        if active is None:
            self.hide()
            return
        view = active.activeView()
        if view is None or not hasattr(view, "getPointOnScreen"):
            self.hide()
            return
        try:
            point = event.position() if hasattr(event, "position") else event.localPos()
            cursor = (float(point.x()), float(point.y()))
            size = view.getSize()
            sx = float(widget.width()) / max(1.0, float(size[0]))
            sy = float(widget.height()) / max(1.0, float(size[1]))

            def projection(local):
                world = sketch.Placement.multVec(local)
                pt = view.getPointOnScreen(world)
                x = float(pt.x) if hasattr(pt, "x") else float(pt[0])
                y = float(pt.y) if hasattr(pt, "y") else float(pt[1])
                # FreeCAD's projected screen coordinates have bottom-left
                # origin and viewport-device pixel units; Qt has top-left.
                return (x * sx, widget.height() - y * sy)

            result = snap_hover.best_snap(sketch.Geometry, cursor, projection)
            if result is None:
                # Read-only body-edge fallback; never consume Sketcher clicks.
                try:
                    pre = Gui.Selection.getPreselection()
                    source = getattr(pre, "Object", None)
                    names = tuple(getattr(pre, "SubElementNames", ()) or ())
                    if not names and getattr(pre, "SubElementName", ""):
                        names = (pre.SubElementName,)
                    if source is not None and names:
                        def project_world(world):
                            pt = view.getPointOnScreen(world)
                            x = float(pt.x) if hasattr(pt, "x") else float(pt[0])
                            y = float(pt.y) if hasattr(pt, "y") else float(pt[1])
                            return (x * sx, widget.height() - y * sy)
                        cue = viewport_passive_cue(
                            sketch, source, names, project_world, cursor)
                        if cue is not None:
                            import FreeCAD as App
                            name, edge, x, y = cue
                            screen = project_world(
                                sketch.Placement.multVec(App.Vector(x, y, 0)))
                            result = (name, screen, edge)
                except (AttributeError, RuntimeError, TypeError, ValueError,
                        ReferenceError):
                    result = None
            if result is None:
                self.hide()
                return
            kind, center, index = result
            if kind not in self.SYMBOLS:
                self.hide()
                return
            self._make_label(widget)
            self.label.setText(self.SYMBOLS[kind])
            self.label.setToolTip(
                kind + " · " + (("Body " + index) if isinstance(index, str)
                else ("Sketch geometry " + str(index + 1)))
                + " · visual cue only; native Sketcher controls constraints."
            )
            self.label.move(
                max(0, min(widget.width() - 16, round(center[0] - 8))),
                max(0, min(widget.height() - 16, round(center[1] - 8))),
            )
            self.label.show()
            self.label.raise_()
            self.last = result
        except (RuntimeError, ValueError, TypeError, AttributeError, ReferenceError):
            # Older FreeCAD/Qt viewport APIs can differ; native Sketcher
            # continues to function with no Az inference overlay.
            self.hide()
