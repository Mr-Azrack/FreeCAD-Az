# SPDX-License-Identifier: LGPL-2.1-or-later
"""Use FreeCAD's Qt binding instead of installing another copy of Qt."""

try:
    from PySide import QtCore, QtGui, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
    except ImportError:
        from PySide6 import QtCore, QtGui, QtWidgets

QAction = getattr(QtWidgets, "QAction", None) or QtGui.QAction


def menu_exec(menu, position):
    return (getattr(menu, "exec", None) or menu.exec_)(position)
