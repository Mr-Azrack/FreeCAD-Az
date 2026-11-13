# SPDX-License-Identifier: LGPL-2.1-or-later
"""Find sketch snap targets and display a mouse-transparent marker."""

import FreeCADGui as Gui

from . import modeling, snap_hover
from .snap_targets import viewport_passive_cue, visible_body_cue
from .qt import QtCore, QtWidgets


class HoverGuides:
    SYMBOLS = {"Midpoint": "△", "Center": "⊙", "Endpoint": "□",
               "Start": "□", "End": "□", "Edge": "◇"}
    MARKER_SIZE = 24

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
        self.label.setFixedSize(self.MARKER_SIZE, self.MARKER_SIZE)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("""
        QLabel#AzSketchHoverSnap {
            background: #ffffff; border: 1px solid #174969; border-radius: 12px;
            color: #123c56; font: bold 17px "Segoe UI Symbol";
        }
        """)
        self.label.hide()

    def move(self, widget, event):
        result = self.target(widget, event)
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
        )
        size = self.MARKER_SIZE
        self.label.move(
            max(0, min(widget.width() - size, round(center[0] - size / 2))),
            max(0, min(widget.height() - size, round(center[1] - size / 2))),
        )
        self.label.show()
        self.label.raise_()
        self.last = result
        return True

    def target(self, widget, event):
        sketch = modeling.in_sketch()
        if not sketch:
            return None
        active = Gui.activeDocument()
        if active is None:
            return None
        view = active.activeView()
        if view is None or not hasattr(view, "getPointOnScreen"):
            return None
        try:
            point = event.position() if hasattr(event, "position") else event.localPos()
            cursor = (float(point.x()), float(point.y()))
            size = view.getSize()
            sx = float(widget.width()) / max(1.0, float(size[0]))
            sy = float(widget.height()) / max(1.0, float(size[1]))
            placement = (sketch.getGlobalPlacement() if hasattr(sketch, "getGlobalPlacement")
                         else sketch.Placement)

            def project_world(world):
                pt = view.getPointOnScreen(world)
                x = float(pt.x) if hasattr(pt, "x") else float(pt[0])
                y = float(pt.y) if hasattr(pt, "y") else float(pt[1])
                return (x * sx, (size[1] - 1 - y) * sy)

            def projection(local):
                return project_world(placement.multVec(local))

            result = snap_hover.best_snap(sketch.Geometry, cursor, projection)

            if result is None:
                # Read-only body-edge inference for both cues and drawing clicks.
                try:
                    pre = Gui.Selection.getPreselection()
                    source = getattr(pre, "Object", None)
                    names = tuple(getattr(pre, "SubElementNames", ()) or ())
                    if not names and getattr(pre, "SubElementName", ""):
                        names = (pre.SubElementName,)
                    if source is not None and names:
                        cue = viewport_passive_cue(
                            sketch, source, names, project_world, cursor)
                    else:
                        cue = None
                except (AttributeError, RuntimeError, TypeError, ValueError,
                        ReferenceError):
                    cue = None
                if cue is None:
                    # Native Sketcher may suppress model-edge preselection.
                    # Inspect a small, bounded set of visible Body Tips instead.
                    cue = visible_body_cue(sketch, project_world, cursor)
                if cue is not None:
                    import FreeCAD as App
                    name, edge, x, y = cue
                    screen = project_world(
                        placement.multVec(App.Vector(x, y, 0)))
                    result = (name, screen, edge)
            return result
        except (RuntimeError, ValueError, TypeError, AttributeError, ReferenceError):
            return None
