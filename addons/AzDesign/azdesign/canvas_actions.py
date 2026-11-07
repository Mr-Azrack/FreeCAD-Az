# SPDX-License-Identifier: LGPL-2.1-or-later
"""Viewport-adjacent actions bound to the current native FreeCAD selection."""

import FreeCADGui as Gui
from .qt import QtCore, QtWidgets
from . import commands, modeling


def selection_actions(obj, subelements=()):
    """Offer only actions with recognizable native inputs.

    This is a presentation policy, not permission to modify parametric data.
    Native command dispatch still validates its selection and constraints.
    """
    if obj is None:
        return ()
    if obj.isDerivedFrom("Sketcher::SketchObject"):
        return ("edit", "extrude", "isolate")
    if obj.isDerivedFrom("PartDesign::Body"):
        if any(str(name).startswith("Face") for name in subelements):
            return ("sketch", "presspull", "isolate")
        return ("activate", "isolate")
    if obj.isDerivedFrom("PartDesign::Feature") or obj.isDerivedFrom("Part::Feature"):
        if any(str(name).startswith("Edge") for name in subelements):
            return ("fillet", "edit", "isolate")
        if any(str(name).startswith("Face") for name in subelements):
            return ("sketch", "presspull", "edit", "isolate")
        from .quick_dimension import dimension_property
        return (("edit", "dimension", "isolate") if dimension_property(obj)
                else ("edit", "isolate"))
    return ()


class CanvasActions(QtWidgets.QFrame):
    """Compact, nonmodal action strip anchored at the canvas top-right."""

    ACTIONS = (
        ("edit", "Edit"),
        ("dimension", "Dimension"),
        ("activate", "Activate"),
        ("sketch", "Sketch"),
        ("extrude", "Extrude"),
        ("presspull", "Press/Pull"),
        ("fillet", "Fillet"),
        ("isolate", "Isolate"),
    )

    def __init__(self, session, parent):
        super().__init__(parent)
        self.session = session
        self.setObjectName("AzCanvasActions")
        self.setStyleSheet("""
        QFrame#AzCanvasActions { background: #f6f9fbee;
            border: 1px solid #cbd8e0; border-radius: 7px; }
        QFrame#AzCanvasActions QPushButton { border: 0;
            border-right: 1px solid #d9e2e8; background: transparent;
            color: #385569; padding: 6px; font-weight: 600; }
        QFrame#AzCanvasActions QPushButton:hover { background: #dcebf7; }
        """)
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(1)
        self.buttons = {}
        self.current = None
        for key, label in self.ACTIONS:
            button = QtWidgets.QPushButton(label, self)
            button.setObjectName("AzCanvas_" + key)
            button.setToolTip(
                "Use FreeCAD's native selection and transactional modeling tool: "
                + label
            )
            button.clicked.connect(
                lambda _checked=False, key=key: self.run(key)
            )
            row.addWidget(button)
            self.buttons[key] = button
        self.hide()

    def run(self, key):
        if Gui.Control.activeDialog() or modeling.in_sketch():
            commands.notify("Finish the current editing task before starting a new one.", True)
            return
        selected = Gui.Selection.getSelection()
        obj = selected[0] if len(selected) == 1 else None
        if obj is None:
            return
        try:
            if key == "edit" or key == "activate":
                from .feature_edit import edit
                edit(obj)
            elif key == "dimension":
                from .quick_dimension import prompt
                prompt(obj, self)
            elif key == "isolate":
                if obj.Document.Name in self.session.browser.isolated:
                    self.session.browser.restore_visibility()
                else:
                    self.session.browser.isolate(obj)
            else:
                cmd = {
                    "sketch": "Az_Sketch",
                    "extrude": "Az_Extrude",
                    "presspull": "Az_PressPull",
                    "fillet": "PartDesign_Fillet",
                }.get(key)
                if cmd:
                    commands.invoke(cmd)
        except Exception as exc:
            commands.notify("Canvas action failed: " + str(exc), True)

    def refresh(self):
        if Gui.Control.activeDialog() or modeling.in_sketch() or not self.session.active:
            self.hide()
            return
        selections = Gui.Selection.getSelectionEx()
        sel = selections[0] if len(selections) == 1 else None
        keys = selection_actions(sel.Object, sel.SubElementNames) if sel else ()
        for key, button in self.buttons.items():
            button.setVisible(key in keys)
        self.setVisible(bool(keys))
        if keys:
            self.adjustSize()
            self.place()

    def place(self):
        parent = self.parentWidget()
        self.move(max(10, parent.width() - self.width() - 18), 16)
        if self.isVisible():
            self.raise_()
