# SPDX-License-Identifier: LGPL-2.1-or-later
"""Qt ribbon, searchable palette and a selection-linked feature strip."""

import os
import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore, QtGui, QtWidgets, QAction, menu_exec
from .catalog import TOOLS, SOLID, SKETCH, UTILITIES
from . import modeling, commands, history as model_history

STYLE = """
QWidget#AzRibbon { background: #f7f8f9; color: #354551; }
QWidget#AzRibbon QLabel { color: #53616c; background: transparent; }
QWidget#AzRibbon QToolButton { border: 1px solid transparent; border-radius: 3px;
 padding: 3px; color: #354551; background: transparent; font-size: 11px; }
QWidget#AzRibbon QToolButton:hover { background: #e3ebf2; border-color: #c4d5e3; }
QWidget#AzRibbon QToolButton:pressed { background: #d5e6f3; }
QWidget#AzRibbon QToolButton:disabled { color: #9aa5ad; }
QWidget#AzRibbon QToolButton#AzFinish { background: #e3efdf; color: #386334; }
QWidget#AzRibbon QToolButton#AzFinish:hover { background: #cde4c5; }
QWidget#AzRibbon QTabBar::tab { background: transparent; border: 0; padding: 5px 20px;
 color: #65717a; font-size: 10px; font-weight: 600; }
QWidget#AzRibbon QTabBar::tab:selected { border-bottom: 2px solid #d57a3f; color: #354551; }
QWidget#AzRibbon QTabBar#AzDocumentTabs::tab { padding: 6px 16px; min-width: 100px;
 background: #e8ecef; border-right: 1px solid #d1d8de; font-size: 11px; font-weight: normal; }
QWidget#AzRibbon QTabBar#AzDocumentTabs::tab:selected { background: #f7f8f9; border-bottom: 2px solid #4588ba; }
QWidget#AzRibbon QComboBox { border: 0; border-right: 1px solid #d3dbe1;
 background: #e9edf0; padding: 10px; color: #374d5c; font-size: 14px; font-weight: 600; }
QWidget#AzRibbon QFrame#AzSeparator { background: #d8dfe4; border: 0; min-width: 1px; max-width: 1px; }
QWidget#AzRibbon QLabel#AzGroupLabel { color: #65717b; font-size: 9px; }
QWidget#AzRibbon QLabel#AzHint { color: #6a7782; padding: 2px 10px; font-size: 10px; }
QWidget#AzHistory { background: #e8ecef; color: #41515d; }
QWidget#AzHistory QToolButton { background: transparent; border: 1px solid transparent;
 border-radius: 2px; padding: 3px; color: #41515d; }
QWidget#AzHistory QToolButton:hover { border-color: #a2bdcf; background: #dbe6ef; }
QWidget#AzHistory QToolButton:checked { border: 1px solid #398ddf; background: #cde3f5; }
QWidget#AzHistory QLabel { color: #70808b; background: transparent; }
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


def tool_button(key, small=False):
    tool = TOOLS[key]
    button = QtWidgets.QToolButton()
    button.setObjectName("AzTool_" + key)
    button.setText(tool.label)
    button.setToolTip(tool.tip)
    button.setIcon(command_icon(tool.icon or tool.command))
    button.setIconSize(QtCore.QSize(18 if small else 29, 18 if small else 29))
    button.setToolButtonStyle(
        QtCore.Qt.ToolButtonIconOnly if small else QtCore.Qt.ToolButtonTextUnderIcon
    )
    button.setMinimumSize(30 if small else 56, 28 if small else 51)
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
        self.file_menu.addAction("Native CAD / Properties", lambda: commands.invoke("Az_Native"))
        self.advanced_menu = self.file_menu.addMenu("Advanced")
        file_button.setMenu(self.file_menu)
        top.addWidget(file_button)
        for key in ("save", "undo", "redo"):
            top.addWidget(tool_button(key, True))
        top.addSpacing(12)
        self.documents = DocumentTabs()
        top.addWidget(self.documents, 1)
        top.addWidget(tool_button("new", True))
        top.addWidget(tool_button("palette", True))
        top.addWidget(tool_button("help", True))
        layout.addLayout(top)
        tools = QtWidgets.QHBoxLayout()
        tools.setSpacing(0)
        workspace = QtWidgets.QComboBox()
        workspace.setObjectName("AzWorkspaceSelector")
        workspace.addItems(["DESIGN", "Manufacture", "Native CAD"])
        workspace.setFixedWidth(118)
        workspace.setMinimumHeight(96)
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
        self.pages.setFixedHeight(74)
        for groups in (SOLID, SKETCH, UTILITIES):
            self.pages.addWidget(self.make_page(groups))
        self.tabs.currentChanged.connect(self.pages.setCurrentIndex)
        content.addWidget(self.pages)
        tools.addLayout(content, 1)
        layout.addLayout(tools)
        self.hint = QtWidgets.QLabel()
        self.hint.setObjectName("AzHint")
        self.hint.hide()
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
        symbol = (
            "PartDesign_NewSketch"
            if obj.isDerivedFrom("Sketcher::SketchObject")
            else "PartDesign_Body"
        )
        if getattr(obj, "AzType", "") == "AzExtrude" or obj.TypeId == "PartDesign::Pad":
            symbol = "extrude"
        elif obj.TypeId == "PartDesign::Pocket":
            symbol = "PartDesign_Pocket"
        elif obj.TypeId == "PartDesign::Fillet":
            symbol = "PartDesign_Fillet"
        self.setIcon(command_icon(symbol))
        self.setIconSize(QtCore.QSize(22, 22))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.setCheckable(True)
        self.setFixedSize(31, 34)
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
            if obj.isDerivedFrom("Sketcher::SketchObject"):
                modeling.edit_sketch(obj)
            elif getattr(obj, "AzType", "") == "AzExtrude":
                from .tasks import edit_feature

                edit_feature(obj)
            elif obj.isDerivedFrom("PartDesign::Hole"):
                from .hole import edit_feature

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
        obj = self.object()
        menu.addAction("Edit feature", self.edit)
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
        from .workspace import action_button

        self.setObjectName("AzHistory")
        self.setStyleSheet(STYLE)
        self.signature = None
        self.buttons = []
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
        self.scroll.setMinimumHeight(37)
        self.scroll.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget > QWidget {background: transparent; border: 0;}"
        )
        layout.addWidget(self.scroll, 1)
        self.resume = QtWidgets.QPushButton("Resume Latest")
        self.resume.setObjectName("AzResumeHistory")
        self.resume.clicked.connect(lambda *_: commands.invoke("Az_ResumeHistory"))
        layout.addWidget(self.resume)
        settings = QtWidgets.QToolButton()
        settings.setObjectName("AzTimelineSettings")
        settings.setIcon(command_icon("Std_DlgPreferences"))
        settings.setToolTip("Timeline settings")
        settings.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menu = QtWidgets.QMenu(settings)
        labels = menu.addAction("Feature labels")
        labels.setCheckable(True)
        labels.toggled.connect(self.show_labels)
        menu.addAction("Resume latest history", lambda: commands.invoke("Az_ResumeHistory"))
        settings.setMenu(menu)
        layout.addWidget(settings)
        self.labels_visible = False
        self.refresh()

    def show_labels(self, enabled):
        self.labels_visible = enabled
        self.signature = None
        self.refresh()

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
        )
        if signature != self.signature:
            self.signature = signature
            self.buttons = []
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
                    button.setText(obj.Label + "\n(suppressed)")
                for body in rolled:
                    if (
                        obj in body.Group
                        and body.Tip in body.Group
                        and body.Group.index(obj) > body.Group.index(body.Tip)
                    ):
                        button.setStyleSheet("color: #9099a0; background: #e9edf0;")
                if self.labels_visible:
                    button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
                    button.setFixedWidth(
                        max(90, button.fontMetrics().horizontalAdvance(obj.Label) + 34)
                    )
                self.buttons.append(button)
                row.addWidget(button)
                if any(obj == body.Tip for body in rolled):
                    marker = QtWidgets.QFrame()
                    marker.setObjectName("AzHistoryMarker")
                    marker.setFixedSize(3, 31)
                    marker.setStyleSheet("background: #3c596d;")
                    marker.setToolTip("Current Body Tip · later features are rolled back")
                    row.addWidget(marker)
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
