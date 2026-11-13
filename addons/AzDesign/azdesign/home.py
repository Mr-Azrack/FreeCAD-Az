# SPDX-License-Identifier: LGPL-2.1-or-later
"""New and Open actions in the Design ribbon when no document is open."""

from .qt import QtWidgets


class DesignHome(QtWidgets.QWidget):
    def __init__(self, ribbon):
        super().__init__(ribbon)
        self.setObjectName("AzDesignHome")
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 4)
        for label, slot in (("New Design", self.new_design), ("Open File", self.open_file)):
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(slot)
            layout.addWidget(button)
        layout.addStretch()

    def new_design(self):
        from . import modeling
        modeling.document()
        self.hide()

    def open_file(self):
        from . import commands
        commands.invoke("Std_Open")

    def refresh(self):
        from .modeling import current_document
        self.setVisible(current_document() is None)
