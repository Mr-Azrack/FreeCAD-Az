# SPDX-License-Identifier: LGPL-2.1-or-later
"""Document tabs, a grouped design Browser, canvas controls and radial tools.

All model interactions use native documents, selections and transactions. These
widgets own presentation, not a second CAD data model.
"""

import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore, QtGui, QtWidgets, menu_exec
from . import modeling, commands, history
from .catalog import TOOLS

PANEL_STYLE = """
QWidget#AzBrowser, QWidget#AzNavigation, QWidget#AzRadial { background: #f8f9fa; color: #37434e; }
QWidget#AzBrowser QLabel { color: #53616e; font-size: 12px; }
QWidget#AzBrowser QLineEdit { background: white; font-size: 13px; min-height: 28px; border: 1px solid #d7dde2;
 border-radius: 3px; padding: 6px; color: #37434e; }
QWidget#AzBrowser QTreeWidget { font-size: 13px; background: #f8f9fa; color: #37434e; border: 0; outline: 0; }
QWidget#AzBrowser QTreeWidget::item { height: 32px; border: 0; }
QWidget#AzBrowser QTreeWidget::item:selected { background: #dcebf7; color: #1c5881; }
QWidget#AzBrowser QTreeWidget::item:hover { background: #eaf0f5; }
QWidget#AzBrowser QToolButton, QWidget#AzNavigation QToolButton { background: transparent;
 border: 1px solid transparent; border-radius: 3px; padding: 4px; color: #405361; }
QWidget#AzBrowser QToolButton:hover, QWidget#AzNavigation QToolButton:hover { background: #e2eaf1; }
QWidget#AzNavigation { border: 1px solid #cad2d9; border-radius: 5px; }
QWidget#AzNavigation QToolButton:checked { background: #d6e8f7; border: 1px solid #7ba8cc; }
QWidget#AzRadial { border: 1px solid #bac8d2; border-radius: 8px; }
QWidget#AzRadial QToolButton { background: #f8f9fa; color: #354b5b;
 border: 1px solid #d2dce4; border-radius: 5px; padding: 5px; }
QWidget#AzRadial QToolButton:hover { background: #dcecf8; border-color: #4487b7; }
"""


def icon(name):
    from .ui import command_icon

    return command_icon(name)


def visible_documents():
    result = []
    for doc in App.listDocuments().values():
        try:
            gui = Gui.getDocument(doc.Name)
            if gui and gui.activeView():
                result.append(doc)
        except (RuntimeError, NameError):
            pass
    return result


def action_button(text, name, callback, parent=None):
    button = QtWidgets.QToolButton(parent)
    button.setText(text)
    button.setToolTip(text)
    button.setAccessibleName(text)
    from .ui import design_icon
    icon_keys = {
        "Home view": "home", "Fit": "fit", "Zoom in": "zoom-in",
        "Zoom out": "zoom-out", "Display settings": "display",
        "Orbit · drag with the left button · Esc to finish": "orbit",
        "Pan · drag with the left button · Esc to finish": "pan",
        "Standard views": "standard", "Show native properties": "parameters",
        "First solid": "history-start", "Previous feature": "history-back",
        "Next feature": "history-next", "Latest history": "history-end",
    }
    actual_icon = design_icon(icon_keys.get(text, "settings"))
    button.setIcon(actual_icon)
    button.setIconSize(QtCore.QSize(20, 20))
    # FreeCAD/Qt may globally configure QToolButton text beside the icon.
    # A 32-px button then shows fragments like "P...h" or "S...s".
    # Always specify icon-only; fall back to a short legible label when
    # the native command has no valid icon on a given Qt/FreeCAD build.
    button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
    if actual_icon.isNull():
        abbreviation = {
            "Home view": "H", "Fit": "Fit",
            "Zoom in": "+", "Zoom out": "−",
            "Display settings": "D", "Standard views": "V",
            "Show native properties": "P",
        }.get(text, "".join(part[:1] for part in text.split()[:2]).upper())
        button.setText(abbreviation[:3])
        button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
    button.setFixedSize(42, 40)
    button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    button.clicked.connect(lambda _checked=False: callback())
    return button


class DocumentTabs(QtWidgets.QTabBar):
    def __init__(self):
        super().__init__()
        self.setObjectName("AzDocumentTabs")
        self.setExpanding(False)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setUsesScrollButtons(True)
        self.setMinimumWidth(140)
        self.currentChanged.connect(self.activate_document)
        self.tabCloseRequested.connect(self.close_document)
        self.signature = None

    def refresh(self):
        docs = visible_documents()
        signature = tuple((doc.Name, doc.Label, doc.FileName) for doc in docs)
        if signature != self.signature:
            self.blockSignals(True)
            while self.count():
                self.removeTab(0)
            for doc in docs:
                index = self.addTab(doc.Label)
                self.setTabData(index, doc.Name)
                self.setTabToolTip(index, doc.FileName or "Unsaved design")
            self.signature = signature
            self.blockSignals(False)
        doc = modeling.current_document()
        if doc:
            for index in range(self.count()):
                if self.tabData(index) == doc.Name:
                    self.blockSignals(True)
                    self.setCurrentIndex(index)
                    self.blockSignals(False)
                    break

    def activate_document(self, index):
        name = self.tabData(index) if index >= 0 else None
        if name and name in App.listDocuments():
            if Gui.Control.activeDialog():
                commands.notify(
                    "Finish or cancel the current operation before switching designs.", True
                )
                self.refresh()
                return
            App.setActiveDocument(name)

    def close_document(self, index):
        if Gui.Control.activeDialog():
            commands.notify("Finish or cancel the current operation before closing a design.", True)
            return
        self.activate_document(index)
        # Native Close preserves FreeCAD's unsaved-document confirmation.
        commands.invoke("Std_CloseActiveWindow")
        QtCore.QTimer.singleShot(0, self.refresh)


class Browser(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("AzBrowser")
        self.setStyleSheet(PANEL_STYLE)
        self.signature = None
        self.updating = False
        self.isolated = {}
        self.items = {}
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 6, 8)
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("BROWSER")
        title.setStyleSheet("font-size: 12px; font-weight: 600; letter-spacing: 1px;")
        header.addWidget(title)
        header.addStretch()
        button = action_button("Show native properties", "Std_DlgParameter", self.properties)
        button.setObjectName("AzBrowserProperties")
        header.addWidget(button)
        layout.addLayout(header)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Find in this design")
        self.search.setObjectName("AzBrowserSearch")
        self.search.textChanged.connect(self.filter)
        layout.addWidget(self.search)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setObjectName("AzDesignTree")
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.tree.setColumnWidth(1, 29)
        self.tree.itemSelectionChanged.connect(self.select)
        self.tree.itemClicked.connect(self.click)
        self.tree.itemDoubleClicked.connect(self.edit)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.context_menu)
        layout.addWidget(self.tree)
        self.footer = QtWidgets.QLabel("Select in the Browser or canvas")
        self.footer.setStyleSheet("font-size: 12px; padding-top: 5px;")
        layout.addWidget(self.footer)

    def add(self, parent, label, symbol, obj=None, expanded=False):
        item = QtWidgets.QTreeWidgetItem(parent, [label, ""])
        item.setIcon(0, icon(symbol))
        item.setExpanded(expanded)
        if obj:
            key = (obj.Document.Name, obj.Name)
            item.setData(0, QtCore.Qt.UserRole, key)
            item.setToolTip(0, obj.Label + " · " + obj.TypeId)
            item.setToolTip(1, "Toggle visibility")
            self.items[key] = item
        return item

    def object(self, item):
        key = item.data(0, QtCore.Qt.UserRole) if item else None
        if key and key[0] in App.listDocuments():
            return App.getDocument(key[0]).getObject(key[1])
        return None

    def refresh(self):
        doc = modeling.current_document()
        objects = [o for o in doc.Objects if not getattr(o, "AzPreview", False)] if doc else []
        active = modeling.active_body() if doc else None
        signature = (
            (doc.Name, doc.Label) if doc else None,
            getattr(active, "Name", None),
            tuple((
                o.Name, o.Label, getattr(getattr(o, "Tip", None), "Name", ""),
                getattr(o, "Suppressed", False),
            ) for o in objects),
        )
        self.updating = True
        try:
            if signature != self.signature:
                expanded = {key: item.isExpanded() for key, item in self.items.items()}
                self.tree.clear()
                self.items = {}
                if doc:
                    root = self.add(self.tree, doc.Label, "PartDesign_Body", expanded=True)
                    settings = self.add(root, "Document Settings", "Std_DlgPreferences")
                    units = App.Units.Quantity("1 mm").getUserPreferred()[2]
                    self.add(settings, "Units: " + units, "Std_Measure")
                    views = self.add(root, "Named Views", "Std_ViewIsometric")
                    for label, command in (
                        ("Home", "Az_Home"),
                        ("Top", "Std_ViewTop"),
                        ("Front", "Std_ViewFront"),
                        ("Right", "Std_ViewRight"),
                    ):
                        item = self.add(views, label, "Std_ViewIsometric")
                        item.setData(0, QtCore.Qt.UserRole + 1, command)
                    origins = self.add(root, "Origin", "PartDesign_Plane")
                    bodies = self.add(root, "Bodies & Components", "folder", expanded=True)
                    loose_sketches = self.add(root, "Unassigned Sketches", "folder")
                    construction = self.add(root, "Construction", "folder")
                    loose_solids = self.add(root, "Other Geometry", "folder")
                    body_nodes = {}
                    for body in objects:
                        if not body.isDerivedFrom("PartDesign::Body"):
                            continue
                        is_active = body == active
                        name = ("● " if is_active else "") + body.Label
                        node = self.add(bodies, name, "PartDesign_Body", body, expanded=True)
                        body_nodes[body.Name] = (
                            self.add(node, "Features", "folder", expanded=True),
                            self.add(node, "Sketches", "folder", expanded=True),
                        )
                        node.setToolTip(
                            0, ("Active Body · " if is_active else "Body · ")
                            + body.Label + " · " + str(len(body.Group)) + " items"
                        )
                        node.setExpanded(expanded.get((doc.Name, body.Name), True))
                    # Native Body.Group order is the modeling history; don't
                    # invent order from document creation or alphabetical labels.
                    added = set()
                    for body in objects:
                        if not body.isDerivedFrom("PartDesign::Body"):
                            continue
                        features_folder, sketch_folder = body_nodes[body.Name]
                        for member in body.Group:
                            if member not in objects or member.Name in added:
                                continue
                            if member.isDerivedFrom("Sketcher::SketchObject"):
                                parent, symbol = sketch_folder, "PartDesign_NewSketch"
                            elif member.isDerivedFrom("PartDesign::Feature"):
                                parent, symbol = features_folder, "PartDesign_Body"
                            else:
                                continue
                            suffix = " (suppressed)" if getattr(member, "Suppressed", False) else ""
                            item = self.add(parent, member.Label + suffix, symbol, member)
                            item.setExpanded(expanded.get((doc.Name, member.Name), False))
                            added.add(member.Name)
                    for obj in objects:
                        if obj.Name in added or obj.isDerivedFrom("PartDesign::Body"):
                            continue
                        parent, symbol = None, None
                        if obj.isDerivedFrom("Sketcher::SketchObject"):
                            parent, symbol = loose_sketches, "PartDesign_NewSketch"
                        elif obj.isDerivedFrom("App::Origin"):
                            parent, symbol = origins, "PartDesign_Plane"
                        elif (obj.isDerivedFrom("PartDesign::Plane")
                              or obj.isDerivedFrom("PartDesign::Line")
                              or obj.isDerivedFrom("PartDesign::Point")):
                            parent, symbol = construction, "PartDesign_Plane"
                        elif obj.isDerivedFrom("Spreadsheet::Sheet"):
                            parent, symbol = root, "Spreadsheet_CreateSheet"
                        elif (obj.isDerivedFrom("Part::Feature")
                              and not history.owner_body(obj)):
                            parent, symbol = loose_solids, "PartDesign_Body"
                        if symbol:
                            item = self.add(parent, obj.Label, symbol, obj)
                            item.setExpanded(expanded.get((doc.Name, obj.Name), False))
                    for folder in (construction, loose_sketches, loose_solids):
                        folder.setData(0, QtCore.Qt.UserRole + 2, folder.childCount() == 0)

                self.signature = signature
                self.filter(self.search.text())
            selected = {(obj.Document.Name, obj.Name) for obj in Gui.Selection.getSelection()}
            displayed_selection = set(selected)
            for obj in Gui.Selection.getSelection():
                owner = history.owner_body(obj)
                if owner and not obj.isDerivedFrom("Sketcher::SketchObject"):
                    displayed_selection.add((owner.Document.Name, owner.Name))
            for key, item in self.items.items():
                obj = self.object(item)
                item.setSelected(key in displayed_selection)
                if obj and obj.ViewObject:
                    item.setIcon(1, icon("eye" if obj.ViewObject.Visibility else "eye-off"))
            self.footer.setText(
                (str(len(selected)) + " selected")
                if selected
                else "Select in the Browser or canvas"
            )
        finally:
            self.updating = False

    def filter(self, text):
        query = text.strip().casefold()

        def visit(item):
            match = query in item.text(0).casefold()
            children = [visit(item.child(i)) for i in range(item.childCount())]
            visible = match or any(children)
            item.setHidden(
                not visible or (not query and bool(item.data(0, QtCore.Qt.UserRole + 2)))
            )
            if query and any(children):
                item.setExpanded(True)
            return visible

        for i in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(i))

    def select(self):
        if self.updating:
            return
        Gui.Selection.clearSelection()
        for item in self.tree.selectedItems():
            obj = self.object(item)
            if obj:
                Gui.Selection.addSelection(obj)

    def click(self, item, column):
        obj = self.object(item)
        if column == 1 and obj and obj.ViewObject:
            obj.ViewObject.Visibility = not obj.ViewObject.Visibility
            self.refresh()

    def edit(self, item, column=0):
        if column != 0:
            return
        obj = self.object(item)
        if not obj:
            command = item.data(0, QtCore.Qt.UserRole + 1)
            if command:
                commands.invoke(command)
            return
        if Gui.Control.activeDialog():
            commands.notify("Finish or cancel the current operation first.", True)
            return
        try:
            from .feature_edit import edit
            edit(obj)
        except Exception as exc:
            commands.notify("Cannot edit " + obj.Label + ": " + str(exc), True)
            self.properties()

    def properties(self):
        from .session import current

        session = current()
        if session and session.model_dock:
            session.model_dock.show()
            session.model_dock.raise_()

    def isolate(self, obj):
        doc = obj.Document
        bodies = [
            o
            for o in doc.Objects
            if o.isDerivedFrom("PartDesign::Body")
            or (o.isDerivedFrom("Part::Feature") and not history.owner_body(o))
        ]
        self.isolated[doc.Name] = {o.Name: o.ViewObject.Visibility for o in bodies}
        owner = history.owner_body(obj) or obj
        for body in bodies:
            body.ViewObject.Visibility = body == owner

    def restore_visibility(self):
        doc = modeling.current_document()
        if doc:
            for name, visible in self.isolated.pop(doc.Name, {}).items():
                obj = doc.getObject(name)
                if obj:
                    obj.ViewObject.Visibility = visible

    def context_menu(self, position):
        item = self.tree.itemAt(position)
        obj = self.object(item)
        if not obj:
            return
        menu = QtWidgets.QMenu(self)
        menu.addAction("Edit / Activate", lambda: self.edit(item))
        from .quick_dimension import dimension_property
        if dimension_property(obj):
            def quick_edit():
                try:
                    from .quick_dimension import prompt
                    prompt(obj, self)
                except Exception as exc:
                    commands.notify("Quick Dimension: " + str(exc), True)
            menu.addAction("Quick Dimension…", quick_edit)
        if obj.isDerivedFrom("PartDesign::Body"):
            menu.addAction(
                "Set as active Body",
                lambda: Gui.activeDocument().activeView().setActiveObject("pdbody", obj),
            )
        menu.addAction("Properties", self.properties)
        menu.addAction("Toggle visibility", lambda: self.click(item, 1))
        menu.addSeparator()
        menu.addAction("Isolate", lambda: self.isolate(obj))
        menu.addAction("Restore visibility", self.restore_visibility)
        menu_exec(menu, self.tree.viewport().mapToGlobal(position))


class Navigation(QtWidgets.QFrame):
    def __init__(self, session, parent):
        super().__init__(parent)
        self.session = session
        self.setObjectName("AzNavigation")
        self.setStyleSheet(PANEL_STYLE)
        self.mode = None
        self.mode_buttons = {}
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(1)
        # The navigation cube has the dedicated Home control. Avoid a
        # confusing second Home icon in the bottom navigation strip.
        for mode in ("orbit", "pan"):
            button = action_button(
                mode.title() + " · drag with the left button · Esc to finish",
                mode,
                lambda mode=mode: self.set_mode(None if self.mode == mode else mode),
            )
            button.setObjectName("AzNavigate_" + mode)
            button.setFixedSize(34, 34)
            button.setIconSize(QtCore.QSize(19, 19))
            button.setCheckable(True)
            self.mode_buttons[mode] = button
            row.addWidget(button)
        for text, command in (
            ("Fit", "Std_ViewFitAll"),
            ("Zoom in", "Std_ViewZoomIn"),
            ("Zoom out", "Std_ViewZoomOut"),
        ):
            button = action_button(text, command, lambda cmd=command: commands.invoke(cmd))
            button.setFixedSize(34, 34)
            button.setIconSize(QtCore.QSize(19, 19))
            row.addWidget(button)
        display = action_button("Display settings", "display", lambda: None)
        display.setObjectName("AzDisplaySettings")
        display.setFixedSize(34, 34)
        display.setIconSize(QtCore.QSize(19, 19))
        display.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menu = QtWidgets.QMenu(display)
        for title, index in (("Shaded with visible edges", 6), ("Shaded", 5), ("Wireframe", 2)):
            menu.addAction(title, lambda index=index: Gui.runCommand("Std_DrawStyle", index))
        menu.addSeparator()
        for title, camera in (
            ("Orthographic camera", "Orthographic"),
            ("Perspective camera", "Perspective"),
        ):
            menu.addAction(title, lambda camera=camera: self.camera(camera))
        menu.addSeparator()
        grid = menu.addAction("Grid · 10 mm major / 2 mm minor")
        grid.setCheckable(True)
        grid.setChecked(session.appearance.grid_visible)
        grid.toggled.connect(session.appearance.toggle_grid)
        self.grid_action = grid
        display.setMenu(menu)
        row.addWidget(display)
        views = action_button("Standard views", "views", lambda: None)
        views.setObjectName("AzStandardViews")
        views.setFixedSize(34, 34)
        views.setIconSize(QtCore.QSize(19, 19))
        views.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        view_menu = QtWidgets.QMenu(views)
        for title, command in (
            ("Top", "Std_ViewTop"),
            ("Bottom", "Std_ViewBottom"),
            ("Front", "Std_ViewFront"),
            ("Back", "Std_ViewRear"),
            ("Left", "Std_ViewLeft"),
            ("Right", "Std_ViewRight"),
            ("Isometric", "Std_ViewIsometric"),
        ):
            view_menu.addAction(title, lambda cmd=command: commands.invoke(cmd))
        views.setMenu(view_menu)
        row.addWidget(views)
        # FreeCAD 1.1's navigation cube has no dedicated Home control.
        # Provide a separate, unobstructed Home target beside the cube.
        self.cube_home = action_button(
            "Home view", "Std_ViewIsometric", commands.home, parent=parent
        )
        self.cube_home.setObjectName("AzCubeHome")
        self.cube_home.setToolTip("Home — isometric view and fit the model")
        self.cube_home.setStyleSheet(
            "QToolButton#AzCubeHome { border: 1px solid #aac0d0;"
            " border-radius: 6px; background: #f6fafc; }"
            "QToolButton#AzCubeHome:hover { background: #dcecf7; }"
        )
        self.cube_home.hide()
        self.adjustSize()

    def camera(self, kind):
        if modeling.current_document():
            Gui.activeDocument().activeView().setCameraType(kind)

    def set_mode(self, mode):
        self.mode = mode
        for name, button in self.mode_buttons.items():
            button.setChecked(name == mode)
        self.session.main.statusBar().showMessage(
            (
                (mode.title() + ": drag the canvas with the left mouse button. Esc to finish.")
                if mode
                else "Ready"
            ),
            6000,
        )

    def place(self):
        self.adjustSize()
        parent = self.parentWidget()
        self.move(
            max(8, (parent.width() - self.width()) // 2),
            max(8, parent.height() - self.height() - 15),
        )
        gui = Gui.activeDocument()
        visible = bool(
            gui and gui.activeView() and hasattr(gui.activeView(), "getCameraNode")
        )
        self.setVisible(visible)
        self.cube_home.move(max(8, parent.width() - 202), 25)
        self.cube_home.setVisible(visible)
        if visible:
            self.cube_home.raise_()
            self.raise_()


class RadialMenu(QtWidgets.QFrame):
    def __init__(self, parent):
        super().__init__(parent, QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)
        self.setObjectName("AzRadial")
        self.setStyleSheet(PANEL_STYLE)
        self.setFixedSize(322, 278)
        positions = [
            (121, 8),
            (226, 42),
            (234, 116),
            (226, 196),
            (121, 218),
            (16, 196),
            (8, 116),
            (16, 42),
        ]
        for key, (x, y) in zip(
            ("sketch", "extrude", "presspull", "fillet", "hole", "move", "undo", "redo"), positions
        ):
            tool = TOOLS[key]
            button = QtWidgets.QToolButton(self)
            button.setText("Sketch" if key == "sketch" else tool.label)
            button.setIcon(icon(tool.icon or tool.command))
            button.setIconSize(QtCore.QSize(23, 23))
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            button.setGeometry(x, y, 80, 51)
            button.setToolTip(tool.tip)
            button.clicked.connect(lambda _checked=False, cmd=tool.command: self.run(cmd))
        close = QtWidgets.QToolButton(self)
        close.setText("Close")
        close.setGeometry(123, 118, 76, 40)
        close.clicked.connect(self.close)

    def run(self, command):
        self.close()
        QtCore.QTimer.singleShot(0, lambda: commands.invoke(command))

    def popup(self, point):
        screen = QtWidgets.QApplication.screenAt(point)
        bounds = screen.availableGeometry() if screen else self.parentWidget().geometry()
        self.move(
            max(bounds.left(), min(point.x() - 161, bounds.right() - self.width())),
            max(bounds.top(), min(point.y() - 139, bounds.bottom() - self.height())),
        )
        self.show()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)
