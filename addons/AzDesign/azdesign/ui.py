# SPDX-License-Identifier: LGPL-2.1-or-later
"""Qt ribbon, searchable palette and a selection-linked feature strip."""

import os
import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore, QtGui, QtWidgets, QAction, menu_exec
from .catalog import TOOLS, SOLID, SKETCH, UTILITIES
from . import modeling, commands, history as model_history

STYLE = """
QWidget#AzRibbon { background: #f8f9fa; color: #263746; }
QWidget#AzRibbon QLabel { color: #344451; background: transparent; }
QWidget#AzRibbon QToolButton { border: 1px solid transparent; border-radius: 5px;
    padding: 4px; color: #263746; background: transparent; }
QWidget#AzRibbon QToolButton:hover { background: #e6edf3; border-color: #bacbd8; }
QWidget#AzRibbon QToolButton:pressed { background: #d6e4ef; }
QWidget#AzRibbon QToolButton:disabled { color: #98a0a7; }
QWidget#AzRibbon QToolButton#AzFinish { background: #d8ecdf; color: #205a3a; }
QWidget#AzRibbon QToolButton#AzFinish:hover { background: #c2e4cd; }
QWidget#AzRibbon QTabBar::tab { background: transparent; border: 0; padding: 7px 19px;
    color: #62717e; font-size: 11px; font-weight: 600; }
QWidget#AzRibbon QTabBar::tab:selected { border-bottom: 3px solid #df7844; color: #234b66; }
QWidget#AzRibbon QComboBox { border: 1px solid #d3dce3; border-radius: 4px;
    background: white; padding: 5px 8px; color: #234b66; min-width: 116px; }
QWidget#AzRibbon QFrame#AzSeparator { background: #dbe1e6; max-width: 1px; }
QWidget#AzRibbon QLabel#AzGroupLabel { color: #72808a; font-size: 9px; letter-spacing: 1px; }
QWidget#AzRibbon QLabel#AzHint { color: #6a7782; padding: 2px 10px; font-size: 10px; }
QWidget#AzHistory { background: #f6f8fa; color: #334854; }
QWidget#AzHistory QToolButton { background: white; border: 1px solid #d9e0e6;
    border-radius: 5px; padding: 4px 8px; color: #334854; }
QWidget#AzHistory QToolButton:hover { border-color: #7196b1; background: #edf4f9; }
QWidget#AzHistory QToolButton:checked { border: 2px solid #df7844; background: #fff2e9; }
QWidget#AzHistory QLabel { color: #637380; background: transparent; }
"""


def command_icon(name):
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


def tool_button(key, small=False):
    tool = TOOLS[key]
    button = QtWidgets.QToolButton()
    button.setObjectName("AzTool_" + key)
    button.setText(tool.label)
    button.setToolTip(tool.tip)
    button.setIcon(command_icon(tool.icon or tool.command))
    button.setIconSize(QtCore.QSize(18 if small else 27, 18 if small else 27))
    button.setToolButtonStyle(
        QtCore.Qt.ToolButtonIconOnly if small else QtCore.Qt.ToolButtonTextUnderIcon
    )
    button.setMinimumSize(30 if small else 64, 28 if small else 57)
    button.clicked.connect(lambda _checked=False: commands.invoke(tool.command))
    if key == "finish":
        button.setObjectName("AzFinish")
    return button


class Ribbon(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("AzRibbon")
        self.setStyleSheet(STYLE)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(7, 3, 7, 0)
        layout.setSpacing(0)
        top = QtWidgets.QHBoxLayout()
        mark = QtWidgets.QLabel("AZ")
        mark.setStyleSheet(
            "background: #234b66; color: white; border-radius: 4px; font-weight: 700; padding: 5px 7px;"
        )
        top.addWidget(mark)
        name = QtWidgets.QLabel("FREECAD AZ")
        name.setStyleSheet("font-weight: 600; font-size: 11px; padding: 0 9px;")
        top.addWidget(name)
        for key in ("new", "open", "save", "undo", "redo"):
            top.addWidget(tool_button(key, True))
        self.tabs = QtWidgets.QTabBar()
        self.tabs.setObjectName("AzWorkspaceTabs")
        for label in ("SOLID", "SKETCH", "UTILITIES"):
            self.tabs.addTab(label)
        top.addSpacing(14)
        top.addWidget(self.tabs)
        top.addStretch()
        top.addWidget(tool_button("palette", True))
        workspace = QtWidgets.QComboBox()
        workspace.setObjectName("AzWorkspaceSelector")
        workspace.addItems(["Design", "Manufacture", "Native CAD"])
        workspace.activated.connect(
            lambda index: (
                commands.invoke(TOOLS["cam" if index == 1 else "native"].command) if index else None
            )
        )
        top.addWidget(workspace)
        layout.addLayout(top)
        self.pages = QtWidgets.QStackedWidget()
        self.pages.setObjectName("AzRibbonPages")
        self.pages.setFixedHeight(83)
        for groups in (SOLID, SKETCH, UTILITIES):
            self.pages.addWidget(self.make_page(groups))
        self.tabs.currentChanged.connect(self.pages.setCurrentIndex)
        layout.addWidget(self.pages)
        self.hint = QtWidgets.QLabel(
            "Create Sketch → draw and dimension → Finish Sketch → Extrude.  S finds any tool."
        )
        self.hint.setObjectName("AzHint")
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
        row.setSpacing(9)
        for group_label, keys in groups:
            group = QtWidgets.QWidget()
            column = QtWidgets.QVBoxLayout(group)
            column.setContentsMargins(1, 0, 1, 0)
            column.setSpacing(1)
            buttons = QtWidgets.QHBoxLayout()
            buttons.setSpacing(1)
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
        self.setWindowTitle("Az Design · Find a Tool")
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
        self.setText(obj.Label)
        self.setIcon(obj.ViewObject.Icon)
        self.setIconSize(QtCore.QSize(24, 24))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.setCheckable(True)
        self.setMinimumSize(84, 54)
        self.setMaximumWidth(150)
        self.setToolTip(obj.Label + "\nClick: select · Double-click: edit · Right-click: more")
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
            if obj.isDerivedFrom("Sketcher::SketchObject"):
                modeling.edit_sketch(obj)
            elif getattr(obj, "AzType", "") == "AzExtrude":
                from .tasks import edit_feature

                edit_feature(obj)
            else:
                Gui.activeDocument().setEdit(obj.Name)
        except RuntimeError:
            commands.notify("Select this feature in the Browser to edit its properties.", True)

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.edit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def context_menu(self, position):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Edit feature", self.edit)
        menu.addAction("Select in model", self.select)
        obj = self.object()
        if obj and obj.isDerivedFrom("PartDesign::Feature"):
            menu.addSeparator()
            menu.addAction("Roll back here", self.roll_back)
            menu.addAction("Resume latest history", lambda: commands.invoke("Az_ResumeHistory"))
            if "Suppressed" in obj.PropertiesList:
                menu.addAction("Unsuppress" if obj.Suppressed else "Suppress", self.suppress)
            menu.addSeparator()
        menu.addAction("Toggle visibility", self.toggle_visibility)
        menu.addAction("Rename", self.rename)
        menu_exec(menu, self.mapToGlobal(position))

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


class History(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("AzHistory")
        self.setStyleSheet(STYLE)
        self.signature = None
        self.buttons = []
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 4)
        layout.setSpacing(2)
        heading = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel(
            "FEATURE HISTORY  ·  Double-click to edit · Right-click to roll back"
        )
        title.setStyleSheet("font-size: 10px;")
        heading.addWidget(title)
        heading.addStretch()
        self.resume = QtWidgets.QPushButton("Resume Latest")
        self.resume.setObjectName("AzResumeHistory")
        self.resume.clicked.connect(lambda *_: commands.invoke("Az_ResumeHistory"))
        heading.addWidget(self.resume)
        layout.addLayout(heading)
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setMinimumHeight(58)
        layout.addWidget(self.scroll)
        self.refresh()

    def features(self):
        doc = App.ActiveDocument
        if not doc:
            return []
        return model_history.ordered(doc)

    def refresh(self):
        doc = App.ActiveDocument
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
        )
        if signature != self.signature:
            self.signature = signature
            self.buttons = []
            page = QtWidgets.QWidget()
            row = QtWidgets.QHBoxLayout(page)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            if not features:
                empty = QtWidgets.QLabel("Your sketches and solid features will appear here.")
                row.addWidget(empty)
            for obj in features:
                button = FeatureButton(obj, self)
                if getattr(obj, "Suppressed", False):
                    button.setText(obj.Label + "\n(suppressed)")
                for body in rolled:
                    if (
                        obj in body.Group
                        and body.Tip in body.Group
                        and body.Group.index(obj) > body.Group.index(body.Tip)
                    ):
                        button.setStyleSheet("color: #9099a0; background: #e9edf0;")
                self.buttons.append(button)
                row.addWidget(button)
            row.addStretch()
            old = self.scroll.takeWidget()
            if old:
                old.deleteLater()
            self.scroll.setWidget(page)
        selected = {(o.Document.Name, o.Name) for o in Gui.Selection.getSelection()}
        for button in self.buttons:
            button.setChecked((button.document_name, button.feature_name) in selected)
