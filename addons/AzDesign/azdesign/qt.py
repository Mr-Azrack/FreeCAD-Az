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

def standard_button_bits(*buttons):
    """C++ FreeCAD task dialog mask compatible with PySide2 and PySide6.

    PySide6 StandardButton is a Python enum.Flag: direct int(flag) raises
    TypeError, while its .value contains the native C++ bit mask. Older
    PySide bindings expose an integer-convertible flag object instead.
    """
    if not buttons:
        return 0
    flags = buttons[0]
    for button in buttons[1:]:
        flags |= button
    return int(getattr(flags, "value", flags))
