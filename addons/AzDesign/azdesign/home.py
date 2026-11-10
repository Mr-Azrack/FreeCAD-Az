# SPDX-License-Identifier: LGPL-2.1-or-later
"""Design-owned welcome screen displayed inside the native CAD MDI viewport.

This is a presentation overlay, not a document; opening a file or creating a
design dismisses it without changing the saved document's workspace.
"""

from .qt import QtCore, QtWidgets


class DesignHome(QtWidgets.QWidget):
    def __init__(self, session):
        super().__init__(session.mdi.viewport())
        self.session = session
        self.setObjectName("AzDesignHome")
        self.setStyleSheet("""
        QWidget#AzDesignHome { background: #edf2f6; }
        QFrame#AzHomeCard { background: #ffffff; border: 1px solid #d2dde7;
                            border-radius: 10px; }
        QLabel#AzHomeTitle { font-size: 29px; font-weight: 700; color: #244a65; }
        QLabel#AzHomeSubtitle { font-size: 14px; color: #5b7080; }
        QLabel#AzHomeSection { font-size: 17px; font-weight: 600; color: #294e68; }
        QLabel#AzHomeDetail { font-size: 13px; color: #617587; }
        QPushButton#AzHomePrimary { background: #266f99; color: #ffffff;
            border: 0; border-radius: 6px; font-size: 15px; font-weight: 600;
            min-height: 47px; padding: 6px 18px; }
        QPushButton#AzHomePrimary:hover { background: #1d5c82; }
        QPushButton#AzHomeSecondary { background: #f0f6fa; color: #245977;
            border: 1px solid #aac9db; border-radius: 6px; font-size: 15px;
            min-height: 47px; padding: 6px 18px; }
        QPushButton#AzHomeSecondary:hover { background: #e2f0fa; }
        """)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.addStretch(2)
        card = QtWidgets.QFrame(self)
        card.setObjectName("AzHomeCard")
        card.setMaximumWidth(780)
        inner = QtWidgets.QVBoxLayout(card)
        inner.setContentsMargins(42, 32, 42, 32)
        inner.setSpacing(17)

        title = QtWidgets.QLabel("Design")
        title.setObjectName("AzHomeTitle")
        inner.addWidget(title)
        subtitle = QtWidgets.QLabel(
            "Your parametric modeling workspace. Start a new model or reopen an existing design."
        )
        subtitle.setObjectName("AzHomeSubtitle")
        subtitle.setWordWrap(True)
        inner.addWidget(subtitle)

        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(14)
        start = QtWidgets.QPushButton("New Design")
        start.setObjectName("AzHomePrimary")
        start.setToolTip("Create an editable parametric model in Design")
        start.clicked.connect(self.new_design)
        buttons.addWidget(start)
        open_button = QtWidgets.QPushButton("Open File")
        open_button.setObjectName("AzHomeSecondary")
        open_button.setToolTip("Open a FreeCAD design or supported CAD file")
        open_button.clicked.connect(self.open_file)
        buttons.addWidget(open_button)
        inner.addLayout(buttons)

        section = QtWidgets.QLabel("Start modeling")
        section.setObjectName("AzHomeSection")
        inner.addWidget(section)
        tip = QtWidgets.QLabel(
            "1. New Design  →  Create Sketch  →  choose an origin plane.\n"
            "2. Draw and dimension a profile  →  Finish Sketch  →  Extrude.\n"
            "Use the Browser and feature history to edit your model later."
        )
        tip.setObjectName("AzHomeDetail")
        tip.setWordWrap(True)
        inner.addWidget(tip)
        outer.addWidget(card, 0, QtCore.Qt.AlignHCenter)
        outer.addStretch(3)
        self.hide()

    def new_design(self):
        from . import modeling
        modeling.document()
        self.hide()

    def open_file(self):
        from . import commands
        commands.invoke("Std_Open")

    def refresh(self):
        from .modeling import current_document
        if current_document() is not None:
            self.hide()
            return
        self.setGeometry(self.parentWidget().rect())
        self.show()
        self.raise_()
