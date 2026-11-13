# SPDX-License-Identifier: LGPL-2.1-or-later
"""Map Qt logical pixels to FreeCAD's bottom-up viewport coordinates."""


def view_ray(view, widget, event):
    try:
        point = event.position() if hasattr(event, "position") else event.localPos()
        width, height = view.getSize()
        x = round(point.x() * width / widget.width())
        y = height - 1 - round(point.y() * height / widget.height())
        if 0 <= x < width and 0 <= y < height:
            return view.projectPointToLine(x, y)
    except (AttributeError, RuntimeError, ValueError, TypeError, ZeroDivisionError):
        return None
    return None
