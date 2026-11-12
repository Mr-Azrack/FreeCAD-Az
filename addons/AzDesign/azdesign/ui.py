# SPDX-License-Identifier: LGPL-2.1-or-later
"""Qt ribbon, searchable palette and a selection-linked feature strip."""

import os
import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore, QtGui, QtWidgets, QAction, menu_exec
from .catalog import TOOLS, SOLID, SKETCH, UTILITIES, RAW_FEATURE_COMMANDS
from . import modeling, commands, history as model_history

STYLE = """
QWidget#AzRibbon { background: #f7f8f9; color: #354551; }
QWidget#AzRibbon QLabel { color: #53616c; background: transparent; }
QWidget#AzRibbon QToolButton { border: 1px solid transparent; border-radius: 3px;
 padding: 3px; color: #354551; background: transparent; font-size: 13px; }
QWidget#AzRibbon QToolButton:hover { background: #e3ebf2; border-color: #c4d5e3; }
QWidget#AzRibbon QToolButton:pressed { background: #d5e6f3; }
QWidget#AzRibbon QToolButton:disabled { color: #9aa5ad; }
QWidget#AzRibbon QToolButton#AzFinish { background: #e3efdf; color: #386334; }
QWidget#AzRibbon QToolButton#AzFinish:hover { background: #cde4c5; }
QWidget#AzRibbon QTabBar::tab { background: transparent; border: 0; padding: 5px 20px;
 color: #65717a; font-size: 12px; font-weight: 600; }
QWidget#AzRibbon QTabBar::tab:selected { border-bottom: 2px solid #d57a3f; color: #354551; }
QWidget#AzRibbon QTabBar#AzDocumentTabs::tab { padding: 6px 16px; min-width: 100px;
 background: #e8ecef; border-right: 1px solid #d1d8de; font-size: 13px; font-weight: normal; }
QWidget#AzRibbon QTabBar#AzDocumentTabs::tab:selected { background: #f7f8f9; border-bottom: 2px solid #4588ba; }
QWidget#AzRibbon QComboBox { border: 0; border-right: 1px solid #d3dbe1;
 background: #e9edf0; padding: 10px; color: #374d5c; font-size: 14px; font-weight: 600; }
QWidget#AzRibbon QFrame#AzSeparator { background: #d8dfe4; border: 0; min-width: 1px; max-width: 1px; }
QWidget#AzRibbon QLabel#AzGroupLabel { color: #65717b; font-size: 11px; }
QWidget#AzRibbon QLabel#AzHint { color: #6a7782; padding: 3px 10px; font-size: 12px; }
QWidget#AzHistory { background: #e8ecef; color: #41515d; }
QWidget#AzHistory QToolButton { background: transparent; font-size: 12px; border: 1px solid transparent;
 border-radius: 2px; padding: 3px; color: #41515d; }
QWidget#AzHistory QToolButton:hover { border-color: #a2bdcf; background: #dbe6ef; }
QWidget#AzHistory QToolButton:checked { border: 1px solid #398ddf; background: #cde3f5; }
QWidget#AzHistory QLabel { color: #70808b; background: transparent; }
QWidget#AzHistory QSlider::groove:horizontal { height: 5px; border-radius: 2px;
 background: #c3d2dd; }
QWidget#AzHistory QSlider::handle:horizontal { background: #367ea7;
 width: 12px; height: 15px; margin: -5px 0; border-radius: 5px; }
QWidget#AzHistory QSlider::handle:horizontal:hover { background: #215b80; }
QWidget#AzHistory QPushButton { border: 1px solid #ccd9e3; border-radius: 4px;
 background: #f4f7fa; padding: 6px 10px; color: #375368; font-size: 12px; }
QWidget#AzHistory QPushButton:hover { background: #dbeaf5; border-color: #a9c4d7; }
QWidget#AzHistory QPushButton:disabled { color: #9faab4; }
QWidget#AzRibbon QPushButton#AzUpdateButton { border: 1px solid #aac8d5;
 border-radius: 4px; padding: 6px 9px; color: #235879;
 background: #e4f0f5; font-weight: 600; }
QWidget#AzRibbon QPushButton#AzUpdateButton:hover { background: #d2e7f1; }
"""


def command_icon(name):
    local_icon = os.path.join(os.path.dirname(__file__), "..", "Resources", "Icons", name + ".svg")
    if not os.path.isfile(local_icon):
        local_icon = os.path.join(os.path.dirname(__file__), "..", "Resources", name + ".svg")
    if os.path.isfile(local_icon):
        return QtGui.QIcon(local_icon)
    try:
        actions = Gui.Command.get(name).getAction()
        if not isinstance(actions, (list, tuple)):
            actions = [actions]
        for action in actions:
            if hasattr(action, "icon") and not action.icon().isNull():
                return action.icon()
    except (AttributeError, RuntimeError, TypeError, NameError):
        pass
    # Sketcher commands may not yet have a QAction in this workbench. Resolve
    # their compiled resources through FreeCAD's icon factory in that case.
    try:
        info = Gui.Command.get(name).getInfo()
        icon = Gui.getIcon(info.get("pixmap", "") or name)
        if not icon.isNull():
            return icon
    except (AttributeError, RuntimeError, TypeError):
        pass
    icon = QtGui.QIcon(":/icons/" + name + ".svg")
    if icon.isNull():
        icon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "Resources", "az.svg"))
    return icon



def design_icon(key):
    """Draw recognizable, resolution-independent icons even without FreeCAD resources.

    The native Windows runtime may omit registered SVG command resources; paint
    locally instead of leaving the SOLID ribbon and floating navigator blank.
    """
    pixmap = QtGui.QPixmap(40, 40)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setPen(QtGui.QPen(QtGui.QColor("#24648a"), 2.5))
    painter.setBrush(QtCore.Qt.NoBrush)
    k = key.lower()
    if k in ("sketch", "rectangle", "sizedrect", "centerrect"):
        painter.drawRect(7, 10, 25, 20)
        painter.drawLine(7, 30, 32, 10)
    elif k in ("extrude", "presspull", "body"):
        painter.drawRect(6, 15, 21, 18)
        painter.drawLine(6, 15, 16, 7)
        painter.drawLine(27, 15, 34, 7)
        painter.drawLine(16, 7, 34, 7)
        painter.drawLine(27, 33, 34, 25)
        painter.drawLine(34, 7, 34, 25)
    elif k in ("cut", "hole", "circle"):
        painter.drawEllipse(8, 8, 24, 24)
        painter.drawEllipse(15, 15, 10, 10)
        if k == "cut":
            painter.drawLine(6, 34, 34, 6)
    elif k in ("fillet", "chamfer"):
        painter.drawLine(8, 31, 8, 10)
        painter.drawLine(8, 31, 31, 31)
        if k == "fillet":
            painter.drawArc(8, 8, 24, 24, 0, 90 * 16)
        else:
            painter.drawLine(8, 17, 17, 8)
    elif k in ("plane", "offset"):
        painter.drawRect(8, 8, 22, 17)
        painter.drawLine(13, 32, 35, 32)
        painter.drawLine(19, 28, 19, 24)
        painter.drawLine(19, 28, 15, 24)
        painter.drawLine(19, 28, 23, 24)
    elif k in ("snaps", "dimension", "parameters"):
        painter.drawLine(5, 19, 35, 19)
        painter.drawLine(8, 13, 8, 25)
        painter.drawLine(32, 13, 32, 25)
        painter.drawEllipse(17, 16, 6, 6)
    elif k in ("orbit", "pan", "zoom-in", "zoom-out", "display", "standard"):
        if k == "orbit":
            painter.drawEllipse(9, 9, 22, 22)
            painter.drawArc(3, 3, 34, 34, 35 * 16, 225 * 16)
            painter.drawLine(28, 5, 36, 9)
            painter.drawLine(28, 5, 29, 14)
        elif k == "pan":
            painter.drawLine(20, 5, 20, 35)
            painter.drawLine(5, 20, 35, 20)
            for end_x, end_y, back_x, back_y in ((20, 5, 14, 12), (20, 35, 14, 28),
                                                  (5, 20, 12, 14), (35, 20, 28, 14)):
                painter.drawLine(end_x, end_y, back_x, back_y)
        elif k.startswith("zoom-"):
            painter.drawEllipse(6, 5, 23, 23)
            painter.drawLine(25, 27, 35, 37)
            painter.drawLine(12, 17, 23, 17)
            if k == "zoom-in":
                painter.drawLine(17, 11, 17, 23)
        elif k == "display":
            painter.drawRect(5, 7, 30, 21)
            painter.drawLine(16, 33, 24, 33)
            painter.drawLine(20, 28, 20, 33)
        else:
            painter.drawRect(9, 10, 22, 22)
            painter.drawLine(9, 10, 19, 5)
            painter.drawLine(31, 10, 36, 5)
            painter.drawLine(19, 5, 36, 5)
    elif k in ("home", "fit", "history-start", "history-back",
               "history-next", "history-end"):
        if k in ("home", "fit"):
            painter.drawRect(12, 15, 16, 15)
            painter.drawLine(9, 16, 20, 6)
            painter.drawLine(20, 6, 31, 16)
        else:
            right = k in ("history-next", "history-end")
            if right:
                painter.drawLine(11, 9, 27, 20)
                painter.drawLine(27, 20, 11, 31)
            else:
                painter.drawLine(29, 9, 13, 20)
                painter.drawLine(13, 20, 29, 31)
            if k.endswith(("start", "end")):
                x = 33 if right else 7
                painter.drawLine(x, 8, x, 32)
    elif k in ("new", "save", "undo", "redo", "palette", "help"):
        if k == "new":
            painter.drawRect(9, 5, 22, 30)
            painter.drawLine(15, 20, 25, 20)
            painter.drawLine(20, 15, 20, 25)
        elif k == "save":
            painter.drawRect(7, 7, 27, 27)
            painter.drawRect(12, 7, 16, 10)
            painter.drawRect(12, 24, 16, 10)
            painter.drawLine(25, 8, 25, 16)
        elif k in ("undo", "redo"):
            if k == "undo":
                painter.drawArc(8, 10, 26, 24, 40 * 16, 220 * 16)
                painter.drawLine(8, 18, 7, 8)
                painter.drawLine(7, 8, 17, 11)
            else:
                painter.drawArc(6, 10, 26, 24, -85 * 16, 220 * 16)
                painter.drawLine(32, 18, 33, 8)
                painter.drawLine(33, 8, 23, 11)
        elif k == "palette":
            painter.drawEllipse(8, 8, 22, 22)
            painter.drawLine(24, 25, 34, 35)
            painter.drawLine(17, 13, 17, 19)
            painter.drawLine(14, 16, 20, 16)
        else:
            painter.drawEllipse(7, 7, 26, 26)
            painter.drawArc(15, 12, 13, 11, 0, 180 * 16)
            painter.drawLine(21, 23, 21, 26)
            painter.drawPoint(21, 30)
    elif k in ("line", "project", "trim", "construction"):
        painter.drawLine(8, 31, 32, 9)
        painter.drawEllipse(5, 28, 6, 6)
        painter.drawEllipse(29, 6, 6, 6)
    else:
        initials = {
            "new": "+", "palette": "?", "help": "?",
            "save": "S", "undo": "↶", "redo": "↷",
            "settings": "⚙", "display": "D", "standard": "V",
        }.get(k, k[:1].upper())
        painter.setPen(QtGui.QColor("#24648a"))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(24)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, initials)
    painter.end()
    return QtGui.QIcon(pixmap)

def tool_button(key, small=False):
    tool = TOOLS[key]
    button = QtWidgets.QToolButton()
    button.setObjectName("AzTool_" + key)
    button.setText(tool.label)
    button.setToolTip(tool.tip)
    button.setIcon(design_icon(key))
    button.setIconSize(QtCore.QSize(18 if small else 29, 18 if small else 29))
    button.setToolButtonStyle(
        QtCore.Qt.ToolButtonIconOnly if small else QtCore.Qt.ToolButtonTextUnderIcon
    )
    button.setMinimumSize(36 if small else 78, 34 if small else 64)
    button.clicked.connect(lambda _checked=False: commands.invoke(tool.command))
    if key == "finish":
        button.setObjectName("AzFinish")
    return button


class Ribbon(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        from .workspace import DocumentTabs

        self.setObjectName("AzRibbon")
        self.setStyleSheet(STYLE)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(0)
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(2)
        mark = QtWidgets.QLabel("AZ")
        mark.setStyleSheet("color: #3d6886; font-weight: 700; font-size: 15px; padding: 4px 9px;")
        top.addWidget(mark)
        file_button = QtWidgets.QToolButton()
        file_button.setObjectName("AzFileMenu")
        file_button.setText("File")
        file_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.file_menu = QtWidgets.QMenu(file_button)
        for key in ("new", "open", "save", "export"):
            tool = TOOLS[key]
            self.file_menu.addAction(
                command_icon(tool.icon or tool.command),
                tool.label,
                lambda cmd=tool.command: commands.invoke(cmd),
            )
        self.file_menu.addSeparator()
        self.file_menu.addAction("Advanced FreeCAD workspace", lambda: commands.invoke("Az_Native"))
        self.file_menu.addAction(
            "Check for Design updates…", lambda: commands.invoke("Az_Update")
        )
        self.advanced_menu = self.file_menu.addMenu("Advanced native features")
        self.advanced_menu.addAction(
            "Open FreeCAD advanced modeling workspace",
            lambda _checked=False: commands.invoke("Az_Native"),
        )
        self.advanced_menu.setToolTipsVisible(True)
        file_button.setMenu(self.file_menu)
        top.addWidget(file_button)
        for key in ("save", "undo", "redo"):
            top.addWidget(tool_button(key, True))
        top.addSpacing(12)
        self.documents = DocumentTabs()
        top.addWidget(self.documents, 1)
        top.addWidget(tool_button("new", True))
        top.addWidget(tool_button("palette", True))
        update_button = QtWidgets.QPushButton("Update")
        update_button.setObjectName("AzUpdateButton")
        update_button.setToolTip(
            "Check GitHub for the latest tested Az Design build; install with an automatic backup."
        )
        update_button.clicked.connect(lambda _checked=False: commands.invoke("Az_Update"))
        top.addWidget(update_button)
        top.addWidget(tool_button("help", True))
        layout.addLayout(top)
        tools = QtWidgets.QHBoxLayout()
        tools.setSpacing(0)
        workspace = QtWidgets.QComboBox()
        workspace.setObjectName("AzWorkspaceSelector")
        workspace.addItems(["DESIGN", "Manufacture", "Native CAD"])
        workspace.setFixedWidth(118)
        workspace.setMinimumHeight(90)
        workspace.activated.connect(
            lambda index: (
                commands.invoke(TOOLS["cam" if index == 1 else "native"].command) if index else None
            )
        )
        tools.addWidget(workspace)
        content = QtWidgets.QVBoxLayout()
        content.setContentsMargins(8, 0, 0, 0)
        content.setSpacing(0)
        self.tabs = QtWidgets.QTabBar()
        self.tabs.setObjectName("AzWorkspaceTabs")
        self.tabs.setExpanding(False)
        for label in ("SOLID", "SKETCH", "UTILITIES"):
            self.tabs.addTab(label)
        content.addWidget(self.tabs)
        self.pages = QtWidgets.QStackedWidget()
        self.pages.setObjectName("AzRibbonPages")
        self.pages.setMinimumHeight(90)
        for groups in (SOLID, SKETCH, UTILITIES):
            self.pages.addWidget(self.make_page(groups))
        self.tabs.currentChanged.connect(self.pages.setCurrentIndex)
        content.addWidget(self.pages)
        tools.addLayout(content, 1)
        layout.addLayout(tools)
        self.hint = QtWidgets.QLabel()
        self.hint.setObjectName("AzHint")
        self.hint.setText(
            "Select a face to sketch · E Extrude · Q Press/Pull · "
            "F Fillet · H Hole · S Find a Tool"
        )
        self.hint.show()
        layout.addWidget(self.hint)

    def make_page(self, groups):
        scroll = QtWidgets.QScrollArea()
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea {background: transparent; border: 0;}")
        page = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(page)
        row.setContentsMargins(0, 1, 0, 0)
        row.setSpacing(5)
        for group_label, keys in groups:
            group = QtWidgets.QWidget()
            column = QtWidgets.QVBoxLayout(group)
            column.setContentsMargins(1, 0, 1, 0)
            column.setSpacing(1)
            buttons = QtWidgets.QHBoxLayout()
            buttons.setSpacing(0)
            for key in keys:
                if isinstance(key, tuple):
                    label, entries = key
                    button = tool_button(entries[0])
                    button.setText(label)
                    # Replace the first tool's direct click with a menu only.
                    button.clicked.disconnect()
                    menu = QtWidgets.QMenu(button)
                    for entry in entries:
                        tool = TOOLS[entry]
                        action = menu.addAction(command_icon(tool.icon or tool.command), tool.label)
                        action.setToolTip(tool.tip)
                        action.setEnabled(tool.command in Gui.listCommands())
                        action.triggered.connect(
                            lambda _checked=False, cmd=tool.command: commands.invoke(cmd)
                        )
                    button.setMenu(menu)
                    button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
                else:
                    button = tool_button(key)
                buttons.addWidget(button)
            column.addLayout(buttons)
            label_widget = QtWidgets.QLabel(group_label)
            label_widget.setObjectName("AzGroupLabel")
            label_widget.setAlignment(QtCore.Qt.AlignCenter)
            column.addWidget(label_widget)
            row.addWidget(group)
            separator = QtWidgets.QFrame()
            separator.setObjectName("AzSeparator")
            separator.setFrameShape(QtWidgets.QFrame.VLine)
            row.addWidget(separator)
        row.addStretch()
        scroll.setWidget(page)
        return scroll

    def update_context(self, sketch):
        if sketch:
            if self.tabs.currentIndex() != 1:
                self.tabs.setCurrentIndex(1)
            self.hint.setText(
                "Sketch: L line · R rectangle · C circle · D smart dimension · T trim · P project · X construction. Finish Sketch returns to Solid."
            )
        elif self.tabs.currentIndex() == 1:
            self.tabs.setCurrentIndex(0)
            self.hint.setText(
                "E extrudes selected profiles · Q edits faces and diameters · Right-click history to roll back · S finds any tool."
            )

    def update_enabled(self):
        for button in self.findChildren(QtWidgets.QToolButton):
            name = button.objectName()
            key = (
                name.removeprefix("AzTool_")
                if name.startswith("AzTool_")
                else "finish" if name == "AzFinish" else None
            )
            if key not in TOOLS or button.menu():
                continue
            tool = TOOLS[key]
            if tool.command.startswith("Az_"):
                enabled = key not in ("finish",) or bool(modeling.in_sketch())
            else:
                try:
                    enabled = Gui.Command.isActive(tool.command)
                except (AttributeError, RuntimeError, TypeError):
                    enabled = tool.command in Gui.listCommands()
            button.setEnabled(enabled)


class CommandPalette(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Design · Find a Tool")
        self.resize(510, 430)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        layout = QtWidgets.QVBoxLayout(self)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Find a tool…  extrude, circle, fillet, export")
        self.search.setObjectName("AzCommandSearch")
        layout.addWidget(self.search)
        self.results = QtWidgets.QListWidget()
        self.results.setObjectName("AzCommandResults")
        self.results.setIconSize(QtCore.QSize(24, 24))
        layout.addWidget(self.results)
        self.search.textChanged.connect(self.filter)
        self.search.returnPressed.connect(self.execute)
        self.results.itemActivated.connect(lambda *_: self.execute())
        self.filter("")

    def filter(self, text):
        self.results.clear()
        text = text.casefold().strip()
        for key, tool in TOOLS.items():
            if tool.command in RAW_FEATURE_COMMANDS:
                continue
            if text not in (tool.label + " " + tool.tip + " " + tool.command).casefold():
                continue
            if tool.command not in Gui.listCommands():
                continue
            item = QtWidgets.QListWidgetItem(command_icon(tool.icon or tool.command), tool.label)
            item.setToolTip(tool.tip)
            item.setData(QtCore.Qt.UserRole, key)
            item.setSizeHint(QtCore.QSize(450, 35))
            self.results.addItem(item)
        if self.results.count():
            self.results.setCurrentRow(0)

    def execute(self):
        item = self.results.currentItem()
        if item:
            command = TOOLS[item.data(QtCore.Qt.UserRole)].command
            self.close()
            QtCore.QTimer.singleShot(0, lambda: commands.invoke(command))

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Down, QtCore.Qt.Key_Up):
            offset = 1 if event.key() == QtCore.Qt.Key_Down else -1
            self.results.setCurrentRow(
                max(0, min(self.results.count() - 1, self.results.currentRow() + offset))
            )
            return
        super().keyPressEvent(event)


class FeatureButton(QtWidgets.QToolButton):
    def __init__(self, obj, history):
        super().__init__()
        self.document_name = obj.Document.Name
        self.feature_name = obj.Name
        self.history = history
        # Use our own per-feature SVG images rather than FreeCAD icon
        # resources or the tiny, truncated text that appeared in the timeline.
        from .timeline_icons import icon_path
        self.setText("")
        icon = QtGui.QIcon(icon_path(obj))
        # Windows Qt installations can lack an SVG image handler.
        # A valid path alone does not guarantee a rendered icon.
        if icon.pixmap(25, 25).isNull():
            from .timeline_icons import icon_key
            icon = design_icon(icon_key(obj))
        self.setIcon(icon)
        self.setIconSize(QtCore.QSize(23, 23))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.setCheckable(True)
        self.setFixedSize(34, 34)
        self.setAccessibleName(obj.Label)
        self.setToolTip(
            obj.Label + " · " + obj.TypeId
            + "\nClick: select · Double-click: edit · Delete: remove safely · Right-click: actions"
        )
        self.clicked.connect(self.select)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

    def object(self):
        doc = (
            App.getDocument(self.document_name)
            if self.document_name in App.listDocuments()
            else None
        )
        return doc.getObject(self.feature_name) if doc else None

    def select(self):
        obj = self.object()
        if obj:
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj)

    def edit(self):
        obj = self.object()
        if not obj:
            return
        if Gui.Control.activeDialog():
            commands.notify(
                "Finish or cancel the current operation before editing another feature.", True
            )
            return
        self.select()
        try:
            from .feature_edit import edit
            edit(obj)
        except Exception as exc:
            commands.notify("Could not edit " + obj.Label + ": " + str(exc), True)

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.edit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def context_menu(self, position):
        menu = QtWidgets.QMenu(self)
        obj = self.object()
        menu.addAction("Edit feature", self.edit)
        if obj:
            from .quick_dimension import dimension_property
            if dimension_property(obj):
                menu.addAction("Quick Dimension…", self.quick_dimension)
        menu.addAction("Select in model", self.select)
        if obj and (
            obj.isDerivedFrom("PartDesign::Feature")
            or obj.isDerivedFrom("Sketcher::SketchObject")
        ):
            menu.addSeparator()
            menu.addAction("Delete feature…", self.delete_feature)
            menu.addAction("Delete from here…", lambda: self.delete_feature(cascade=True))
        if obj and obj.isDerivedFrom("PartDesign::Feature"):
            menu.addSeparator()
            menu.addAction("Roll back here", self.roll_back)
            menu.addAction("Show dependents…", self.show_dependents)
            menu.addAction("Resume latest history", lambda: commands.invoke("Az_ResumeHistory"))
            if "Suppressed" in obj.PropertiesList:
                menu.addAction("Unsuppress" if obj.Suppressed else "Suppress", self.suppress)
            menu.addSeparator()
        menu.addAction("Toggle visibility", self.toggle_visibility)
        menu.addAction("Rename", self.rename)
        menu_exec(menu, self.mapToGlobal(position))

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
            self.delete_feature()
            event.accept()
            return
        super().keyPressEvent(event)

    def delete_feature(self, cascade=False):
        obj = self.object()
        if not obj:
            return
        if Gui.Control.activeDialog() or modeling.in_sketch():
            commands.notify("Finish the active task or sketch before deleting a feature.", True)
            return
        try:
            body, targets, _new_tip = model_history.deletion_plan(obj, cascade)
        except ValueError as exc:
            commands.notify(str(exc), True)
            return
        what = (
            "Delete " + str(len(targets)) + " timeline steps from " + obj.Label
            if cascade else "Delete " + obj.Label
        )
        details = "\n".join("  • " + item.Label for item in targets[:10])
        if len(targets) > 10:
            details += "\n  … and " + str(len(targets) - 10) + " more"
        answer = QtWidgets.QMessageBox.warning(
            self,
            "Confirm timeline deletion",
            what + "?\n\n" + details
            + "\n\nThis changes the native CAD model. You can Undo afterward.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return
        try:
            deleted = model_history.delete_feature(obj, cascade=cascade)
            Gui.Selection.clearSelection()
            commands.notify("Deleted " + str(len(deleted)) + " step(s). Undo is available.")
            self.history.signature = None
            self.history.refresh()
        except Exception as exc:
            commands.notify(str(exc), True)

    def quick_dimension(self):
        obj = self.object()
        if not obj or Gui.Control.activeDialog():
            return
        try:
            from .quick_dimension import prompt
            if prompt(obj, self):
                self.history.signature = None
                self.history.refresh()
                commands.notify("Dimension updated. Undo is available.")
        except Exception as exc:
            commands.notify("Quick Dimension: " + str(exc), True)

    def show_dependents(self):
        obj = self.object()
        if not obj:
            return
        downstream = model_history.dependents(obj)
        items = [item.Label + " · " + item.TypeId for item in downstream[:25]]
        if len(downstream) > 25:
            items.append("… and " + str(len(downstream) - 25) + " more")
        QtWidgets.QMessageBox.information(
            self,
            "Dependents of " + obj.Label,
            "\n".join(items) if items else "No dependent features or references.",
        )

    def roll_back(self):
        if Gui.Control.activeDialog():
            commands.notify("Finish or cancel the current operation first.", True)
            return
        try:
            model_history.rollback(self.object())
            commands.notify(
                "History rolled back. New extrusions insert here. Use Resume Latest to restore the end."
            )
        except ValueError as exc:
            commands.notify(str(exc), True)

    def suppress(self):
        obj = self.object()
        if not obj or Gui.Control.activeDialog():
            return
        doc = obj.Document
        doc.openTransaction("Az: Toggle suppression")
        try:
            obj.Suppressed = not obj.Suppressed
            doc.recompute()
            if any("Invalid" in o.State or getattr(o, "Error", "") for o in doc.Objects):
                raise ValueError(
                    "Suppression breaks a dependent feature. Edit those references first."
                )
            doc.commitTransaction()
        except Exception as exc:
            doc.abortTransaction()
            doc.recompute()
            commands.notify(str(exc), True)

    def toggle_visibility(self):
        obj = self.object()
        if obj:
            obj.ViewObject.Visibility = not obj.ViewObject.Visibility

    def rename(self):
        obj = self.object()
        if not obj or Gui.Control.activeDialog():
            return
        text, accepted = QtWidgets.QInputDialog.getText(
            self, "Rename feature", "Name", text=obj.Label
        )
        if accepted and text.strip():
            obj.Document.openTransaction("Az: Rename feature")
            obj.Label = text.strip()
            obj.Document.commitTransaction()


class SketchPatternHistoryButton(QtWidgets.QToolButton):
    """Independent Design history entry for one persisted sketch pattern."""

    def __init__(self, sketch, item, history_widget):
        super().__init__()
        self.sketch = sketch
        self.record_id = item["id"]
        self.history_widget = history_widget
        self.setObjectName("AzSketchPatternHistory")
        self.setIcon(command_icon("pattern"))
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFixedSize(32, 32)
        self.setToolTip(sketch.Label + " · " + item["label"] +
                        (" · double-click to edit spacing" if item["editable"]
                         else " · legacy/incomplete ownership; editing disabled"))
        self.setEnabled(bool(item["editable"]))
        self.clicked.connect(self.edit)

    def mouseDoubleClickEvent(self, event):
        self.edit()
        event.accept()

    def edit(self, *_):
        if Gui.Control.activeDialog():
            commands.notify("Finish the active operation before editing a pattern.", True)
            return
        from .pattern_records import find_record, edit_pitch
        try:
            record = find_record(self.sketch, self.record_id)
            if modeling.in_sketch() is not None:
                commands.notify("Finish Sketch before editing pattern history.", True)
                return
            x, ok = QtWidgets.QInputDialog.getDouble(
                self, "Edit sketch pattern", "X center spacing (mm)",
                float(record["pitch_x"]), -100000, 100000, 3)
            if not ok:
                return
            y, ok = QtWidgets.QInputDialog.getDouble(
                self, "Edit sketch pattern", "Y center spacing (mm)",
                float(record["pitch_y"]), -100000, 100000, 3)
            if not ok:
                return
            edit_pitch(self.sketch, self.record_id, x, y)
            self.history_widget.signature = None
            self.history_widget.refresh()
            commands.notify("Sketch pattern spacing updated; Undo is available.")
        except Exception as exc:
            commands.notify("Sketch pattern edit: " + str(exc), True)


class History(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        from .workspace import action_button

        self.setObjectName("AzHistory")
        self.setStyleSheet(STYLE)
        self.signature = None
        self.buttons = []
        self.pattern_buttons = []
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(9, 3, 9, 3)
        layout.setSpacing(4)
        for label, symbol, callback in (
            ("First solid", "history-start", lambda: self.step("first")),
            ("Previous feature", "history-back", lambda: self.step(-1)),
            ("Next feature", "history-next", lambda: self.step(1)),
            ("Latest history", "history-end", lambda: commands.invoke("Az_ResumeHistory")),
        ):
            layout.addWidget(action_button(label, symbol, callback))
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.VLine)
        divider.setStyleSheet("border: 0; background: #cad3db; min-width: 1px; max-width: 1px;")
        layout.addWidget(divider)
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setMinimumHeight(35)
        self.scroll.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget > QWidget {background: transparent; border: 0;}"
        )
        layout.addWidget(self.scroll, 1)
        scrub_box = QtWidgets.QWidget()
        scrub_box.setObjectName("AzHistoryScrubber")
        scrub_layout = QtWidgets.QVBoxLayout(scrub_box)
        scrub_layout.setContentsMargins(3, 0, 4, 0)
        scrub_layout.setSpacing(0)
        self.scrub = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.scrub.setObjectName("AzHistoryScrub")
        self.scrub.setMinimum(0)
        self.scrub.setMaximum(0)
        self.scrub.setFixedWidth(135)
        self.scrub.setToolTip("Drag, then release to move the real Body Tip. Undo is available.")
        self.scrub.sliderReleased.connect(self.scrub_released)
        scrub_layout.addWidget(self.scrub)
        layout.addWidget(scrub_box)
        # Compact local vector images: no text abbreviations that can clip at
        # Windows scaling factors of 125–200%. Tooltips supply full names.
        self.edit_selected_button = QtWidgets.QToolButton()
        self.edit_selected_button.setObjectName("AzTimelineEdit")
        self.edit_selected_button.setIcon(command_icon("timeline-edit"))
        self.edit_selected_button.setIconSize(QtCore.QSize(22, 22))
        self.edit_selected_button.setFixedSize(32, 32)
        self.edit_selected_button.setToolTip("Edit selected timeline feature")
        self.edit_selected_button.clicked.connect(self.edit_selected)
        layout.addWidget(self.edit_selected_button)
        self.delete_selected_button = QtWidgets.QToolButton()
        self.delete_selected_button.setObjectName("AzTimelineDelete")
        self.delete_selected_button.setIcon(command_icon("timeline-delete"))
        self.delete_selected_button.setIconSize(QtCore.QSize(22, 22))
        self.delete_selected_button.setFixedSize(32, 32)
        self.delete_selected_button.setToolTip("Delete selected feature safely")
        self.delete_selected_button.clicked.connect(self.delete_selected)
        layout.addWidget(self.delete_selected_button)
        self.resume = QtWidgets.QToolButton()
        self.resume.setObjectName("AzResumeHistory")
        self.resume.setIcon(command_icon("timeline-resume"))
        self.resume.setIconSize(QtCore.QSize(22, 22))
        self.resume.setFixedSize(32, 32)
        self.resume.setToolTip("Resume latest history")
        self.resume.clicked.connect(lambda *_: commands.invoke("Az_ResumeHistory"))
        layout.addWidget(self.resume)
        settings = QtWidgets.QToolButton()
        settings.setObjectName("AzTimelineSettings")
        settings.setIcon(command_icon("timeline-settings"))
        settings.setIconSize(QtCore.QSize(21, 21))
        settings.setFixedSize(32, 32)
        settings.setToolTip("Timeline settings")
        settings.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menu = QtWidgets.QMenu(settings)
        menu.addAction("Resume latest history", lambda: commands.invoke("Az_ResumeHistory"))
        settings.setMenu(menu)
        layout.addWidget(settings)
        self.labels_visible = False
        self.refresh()

    def scrub_released(self):
        if Gui.Control.activeDialog() or modeling.in_sketch():
            commands.notify("Finish or cancel the current operation before rolling history.", True)
            return
        doc = modeling.current_document()
        if not doc:
            return
        body = modeling.active_body()
        if body is None:
            bodies = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Body")]
            if len(bodies) != 1:
                commands.notify("Activate a Body before moving its history marker.", True)
                return
            body = bodies[0]
        try:
            model_history.move_history_marker(body, self.scrub.value())
            self.signature = None
            self.refresh()
        except Exception as exc:
            commands.notify(str(exc), True)

    def selected_button(self):
        selected = {(o.Document.Name, o.Name) for o in Gui.Selection.getSelection()}
        return next(
            (button for button in self.buttons
             if (button.document_name, button.feature_name) in selected),
            None,
        )

    def edit_selected(self):
        button = self.selected_button()
        if button:
            button.edit()
        else:
            commands.notify("Select a feature in the bottom timeline first.", True)

    def delete_selected(self):
        button = self.selected_button()
        if button:
            button.delete_feature()
        else:
            commands.notify("Select a feature in the bottom timeline first.", True)

    def show_labels(self, enabled):
        # Compatibility route for old settings; the timeline is icon-only.
        self.labels_visible = False

    def step(self, direction):
        if Gui.Control.activeDialog():
            commands.notify("Finish or cancel the current operation first.", True)
            return
        doc = modeling.current_document()
        if not doc:
            return
        body = modeling.active_body()
        if body is None:
            bodies = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Body")]
            if len(bodies) != 1:
                commands.notify("Select a body to step through its history.", True)
                return
            body = bodies[0]
        features = model_history.solids(body)
        if not features or body.Tip not in features:
            return
        index = features.index(body.Tip)
        target = 0 if direction == "first" else max(0, min(len(features) - 1, index + direction))
        try:
            if direction == 1 and target == len(features) - 1:
                model_history.end(body)
            elif target != index:
                model_history.rollback(features[target])
            self.refresh()
        except ValueError as exc:
            commands.notify(str(exc), True)

    def features(self):
        doc = modeling.current_document()
        if not doc:
            return []
        return model_history.ordered(doc)

    def refresh(self):
        doc = modeling.current_document()
        features = self.features()
        rolled = (
            [
                b
                for b in doc.Objects
                if b.isDerivedFrom("PartDesign::Body") and getattr(b, "AzHistoryEnd", "")
            ]
            if doc
            else []
        )
        self.resume.setVisible(bool(rolled))
        signature = (
            doc.Name if doc else None,
            tuple((o.Name, o.Label, getattr(o, "Suppressed", False)) for o in features),
            tuple((b.Name, b.Tip.Name if b.Tip else "") for b in rolled),
            tuple((o.Name, getattr(o, "AzSketchPatternRecords", "")) for o in doc.Objects
                  if hasattr(o, "AzSketchPatternRecords")) if doc else (),
        )
        if signature != self.signature:
            self.signature = signature
            self.buttons = []
            self.pattern_buttons = []
            page = QtWidgets.QWidget()
            row = QtWidgets.QHBoxLayout(page)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(1)
            if not features:
                empty = QtWidgets.QLabel("Design history")
                row.addWidget(empty)
            for obj in features:
                button = FeatureButton(obj, self)
                if getattr(obj, "Suppressed", False):
                    button.setToolTip(button.toolTip() + "\nSuppressed")
                for body in rolled:
                    if (
                        obj in body.Group
                        and body.Tip in body.Group
                        and body.Group.index(obj) > body.Group.index(body.Tip)
                    ):
                        button.setStyleSheet("color: #9099a0; background: #e9edf0;")
                self.buttons.append(button)
                row.addWidget(button)
                if any(obj == body.Tip for body in rolled):
                    marker = QtWidgets.QFrame()
                    marker.setObjectName("AzHistoryMarker")
                    marker.setFixedSize(3, 31)
                    marker.setStyleSheet("background: #3c596d;")
                    marker.setToolTip("Current Body Tip · later features are rolled back")
                    row.addWidget(marker)
            # Sketch patterns are stored on native Sketcher objects, not as
            # fake PartDesign solids. Show a distinct icon per stable record ID.
            if doc:
                from .pattern_records import timeline_records
                for sketch in doc.Objects:
                    if not getattr(sketch, "AzSketchPatternRecords", ""):
                        continue
                    try:
                        items = timeline_records(sketch)
                    except (ValueError, TypeError):
                        continue  # corrupt ownership must never break History
                    for item in items:
                        button = SketchPatternHistoryButton(sketch, item, self)
                        self.pattern_buttons.append(button)
                        row.addWidget(button)
            if features and not rolled:
                marker = QtWidgets.QFrame()
                marker.setFixedSize(3, 31)
                marker.setStyleSheet("background: #3c596d;")
                marker.setToolTip("Latest history")
                row.addWidget(marker)
            row.addStretch()
            old = self.scroll.takeWidget()
            if old:
                old.deleteLater()
            self.scroll.setWidget(page)
        selected = {(o.Document.Name, o.Name) for o in Gui.Selection.getSelection()}
        for button in self.buttons:
            button.setChecked((button.document_name, button.feature_name) in selected)
        selection_available = self.selected_button() is not None
        self.edit_selected_button.setEnabled(selection_available)
        self.delete_selected_button.setEnabled(selection_available)
        body = modeling.active_body() if doc else None
        if body is None and doc:
            bodies = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Body")]
            body = bodies[0] if len(bodies) == 1 else None
        entries, position, rolled_back = (
            model_history.history_position(body) if body else ([], -1, False)
        )
        self.scrub.blockSignals(True)
        self.scrub.setEnabled(bool(entries) and not Gui.Control.activeDialog())
        self.scrub.setMaximum(max(0, len(entries) - 1))
        self.scrub.setValue(max(0, position))
        self.scrub.setToolTip(
            (body.Label + " · " + str(position + 1) + "/" + str(len(entries))
             + (" · rolled back" if rolled_back else " · latest"))
            if entries else "Choose a Body to inspect and roll back its history."
        )
        self.scrub.blockSignals(False)
