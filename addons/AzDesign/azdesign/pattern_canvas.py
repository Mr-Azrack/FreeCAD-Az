# SPDX-License-Identifier: LGPL-2.1-or-later
"""Small original in-canvas pattern spacing handles shared by sketch and solid.

These are actual Qt viewport controls, not native FreeCAD task widgets.
Dragging updates the Design-owned numeric controls, which refresh preview
geometry through its controller. They never replace the exact CAD values.
"""
from .qt import QtCore, QtGui, QtWidgets


class PatternCanvasHandles(QtWidgets.QWidget):
    def __init__(self, get_value, set_value, mode="solid", parent=None,
                 get_axis_name=None, get_counts=None):
        super().__init__(parent)
        self.get_value = get_value
        self.set_value = set_value
        self.mode = mode
        self.get_axis_name = get_axis_name or (lambda: "X")
        self.get_counts = get_counts or (lambda: (3, 2))
        self._dragging = None
        self._start_pos = (0, 0)
        self._start_pitch = 0.0
        self.setObjectName("AzPatternCanvasHandles")
        self.setFixedSize(180, 146 if mode == "sketch" else 96)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setToolTip(
            "Drag the blue arrow to adjust pattern spacing. "
            "Use the exact millimeter fields in Design for precise values."
        )
        self.setCursor(QtCore.Qt.OpenHandCursor)

    def _axis_for(self, pos):
        if self.mode != "sketch":
            return "x"
        return "y" if pos.y() >= 80 else "x"

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.setPen(QtGui.QPen(QtGui.QColor("#a8cbdc"), 1))
        p.setBrush(QtGui.QColor(255, 255, 255, 234))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 8, 8)
        p.setBrush(QtCore.Qt.NoBrush)
        p.setPen(QtGui.QPen(QtGui.QColor("#2b729e"), 2.5))
        # Horizontal spacing handle
        p.drawLine(20, 45, 157, 45)
        p.drawLine(147, 38, 158, 45)
        p.drawLine(147, 52, 158, 45)
        p.setBrush(QtGui.QColor("#2b729e"))
        count_x, count_y = self.get_counts()
        sample_x = max(1, min(int(count_x), 5))
        for i in range(sample_x):
            x = 28 + 96 * i / max(1, sample_x - 1)
            p.drawEllipse(int(x) - 5, 40, 10, 10)
        p.setPen(QtGui.QColor("#264f68"))
        p.drawText(14, 22, "{} spacing  ·  drag →".format(
            "X" if self.mode == "sketch" else self.get_axis_name()
        ))
        if self.mode == "sketch":
            p.setPen(QtGui.QPen(QtGui.QColor("#2b729e"), 2.5))
            p.drawLine(31, 85, 31, 133)
            p.drawLine(24, 124, 31, 134)
            p.drawLine(38, 124, 31, 134)
            p.setBrush(QtGui.QColor("#2b729e"))
            sample_y = max(1, min(int(count_y), 4))
            for i in range(sample_y):
                y = 90 + 33 * i / max(1, sample_y - 1)
                p.drawEllipse(27, int(y) - 4, 8, 8)
            p.setPen(QtGui.QColor("#264f68"))
            p.drawText(47, 112, "Y spacing · drag ↓")
        else:
            p.setPen(QtGui.QColor("#607f90"))
            p.drawText(14, 76, "Live solid preview")
        p.end()

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return super().mousePressEvent(event)
        self._dragging = self._axis_for(event.pos())
        self._start_pos = (event.pos().x(), event.pos().y())
        self._start_pitch = float(self.get_value(self._dragging))
        self.setCursor(QtCore.Qt.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging is None:
            return super().mouseMoveEvent(event)
        delta = (
            event.pos().x() - self._start_pos[0]
            if self._dragging == "x"
            else event.pos().y() - self._start_pos[1]
        )
        # Deliberately use a stable 0.5 mm/px scale; the exact mm spin-box
        # remains authoritative, so no camera projection or geometry drift.
        pitch = self._start_pitch + delta * (0.1 if event.modifiers() & QtCore.Qt.ShiftModifier else 0.5)
        self.set_value(self._dragging, round(pitch, 3))
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._dragging is not None:
            self._dragging = None
            self.setCursor(QtCore.Qt.OpenHandCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
