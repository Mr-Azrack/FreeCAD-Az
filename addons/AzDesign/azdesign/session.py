# SPDX-License-Identifier: LGPL-2.1-or-later
"""Temporary layout, contextual shortcuts and Fusion-style mouse navigation."""

import traceback
import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore, QtGui, QtWidgets, menu_exec
from .catalog import TOOLS, SOLID_KEYS, SKETCH_KEYS
from . import modeling, commands
from .ui import Ribbon, History
from .workspace import Browser, Navigation, RadialMenu
from .appearance import Appearance
from .sketch_palette import SketchPalette
from .canvas_actions import CanvasActions, selection_actions
from .snap_overlay import HoverGuides

_session = None


def current():
    return _session


class InteractionFilter(QtCore.QObject):
    def __init__(self, session):
        super().__init__(session.main)
        self.session = session
        self.forwarding = False
        self.profile_press = None
        self.snap_press = None
        self.snap_points = []
        self.snap_geometry = None

    def editable_focus(self):
        app = QtWidgets.QApplication.instance()
        if app.activeModalWidget() or app.activePopupWidget():
            return True
        focus = app.focusWidget()
        while focus and focus != self.session.main:
            if isinstance(
                focus,
                (
                    QtWidgets.QLineEdit,
                    QtWidgets.QTextEdit,
                    QtWidgets.QPlainTextEdit,
                    QtWidgets.QAbstractSpinBox,
                    QtWidgets.QComboBox,
                    QtWidgets.QDialog,
                ),
            ):
                return True
            if focus.objectName() in ("Tasks", "Combo View", "Python console", "Report view"):
                return True
            focus = focus.parentWidget()
        return False

    def is_viewport(self, widget):
        if not isinstance(widget, QtWidgets.QWidget):
            return False
        # Coin's Quarter widget is the actual CAD viewport. Other Qt widgets,
        # including Tasks, palettes and the object tree, must keep their input.
        name = widget.metaObject().className()
        return any(
            part in name
            for part in ("QuarterWidget", "View3DInventorViewer", "QGLWidget", "QOpenGLWidget")
        )

    def is_sketch_tool_cursor(self, widget):
        return (modeling.in_sketch() is not None
                and widget.cursor().shape() == QtCore.Qt.BitmapCursor)

    def eventFilter(self, watched, event):
        if not self.session.active or self.forwarding:
            return False
        kind = event.type()
        # FreeCAD 1.1's native Preferences radio indicators sometimes render
        # as two empty rings under its bundled Windows Qt style. Scope the
        # checked-state dot to that dialog; never restyle the whole CAD app.
        if (kind == QtCore.QEvent.Show and
                isinstance(watched, QtWidgets.QRadioButton)):
            window = watched.window()
            if window and "Preferences" in window.windowTitle():
                watched.setStyleSheet("""
                    QRadioButton::indicator { width: 15px; height: 15px;
                        border: 1px solid #8898a2; border-radius: 8px;
                        background: #ffffff; }
                    QRadioButton::indicator:checked { background: #247bad;
                        border: 4px solid #d9eef8; border-radius: 8px; }
                """)
        if kind == QtCore.QEvent.MouseMove and self.is_viewport(watched):
            if self.session.navigation.mode or event.buttons() or event.modifiers():
                self.session.snap_guides.hide()
            elif self.session.snap_guides.move(watched, event) and self.is_sketch_tool_cursor(watched):
                target = QtCore.QPointF(*self.session.snap_guides.last[1])
                return self.forward_mouse(watched, event, event.button(), event.buttons(),
                                          event.modifiers(), target)
        if kind == QtCore.QEvent.Leave and self.is_viewport(watched):
            self.session.snap_guides.hide()
        if kind == QtCore.QEvent.Resize and watched == self.session.mdi.viewport():
            self.session.navigation.place()
            self.session.canvas_actions.place()
        if kind == QtCore.QEvent.ContextMenu and self.is_viewport(watched):
            # In sketch edit mode offer associative model-edge references
            # without intercepting native drawing clicks or mutating on hover.
            # The selection must be a real edge of another model object.
            active_sketch = modeling.in_sketch()
            if active_sketch and not Gui.Control.activeDialog():
                selected_edges = [
                    (hit.Object, name)
                    for hit in Gui.Selection.getSelectionEx()
                    if hit.Object is not None and hit.Object != active_sketch
                    and hit.Object.Document == active_sketch.Document
                    for name in hit.SubElementNames
                    if name.startswith("Edge") and name[4:].isdigit()
                ]
                if selected_edges:
                    menu = QtWidgets.QMenu(self.session.main)
                    action = menu.addAction("Reference selected body edges")
                    def link_selected():
                        from .snap_targets import link_selected_body_edges
                        from .commands import notify
                        try:
                            linked = link_selected_body_edges(active_sketch)
                            notify("{} associative sketch edge reference(s) added.".format(len(linked)))
                        except Exception as exc:
                            notify("Cannot reference selected edges: " + str(exc))
                    action.triggered.connect(link_selected)
                    menu_exec(menu, event.globalPos())
                    event.accept()
                    return True
            if not Gui.Control.activeDialog() and not active_sketch:
                selections = Gui.Selection.getSelectionEx()
                selected = selections[0] if len(selections) == 1 else None
                actions = (
                    selection_actions(selected.Object, selected.SubElementNames)
                    if selected else ()
                )
                if actions:
                    menu = QtWidgets.QMenu(self.session.main)
                    labels = dict(CanvasActions.ACTIONS)
                    for key in actions:
                        item = menu.addAction(labels[key])
                        item.triggered.connect(
                            lambda _checked=False, key=key:
                                self.session.canvas_actions.run(key)
                        )
                    menu.addSeparator()
                    menu.addAction("Find a Tool…", lambda: commands.palette())
                    menu_exec(menu, event.globalPos())
                else:
                    self.session.radial.popup(event.globalPos())
                event.accept()
                return True
        if kind == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Escape:
            self.clear_snap_points()
            # Design-owned preview transactions must abort on global Esc,
            # even when the actual Coin viewport has keyboard focus.
            from .solid_pattern import cancel_active as cancel_solid_pattern
            if cancel_solid_pattern():
                event.accept()
                return True
            from .sketch_pattern_ui import cancel_active as cancel_sketch_pattern
            if cancel_sketch_pattern():
                event.accept()
                return True
            from .edge_treatments_canvas import cancel_active as cancel_edge_tool
            if cancel_edge_tool():
                event.accept()
                return True
            from .hole import cancel_face_picker
            if cancel_face_picker():
                event.accept()
                return True
            from .sketch_plane_picker import cancel_active as cancel_sketch_plane
            if cancel_sketch_plane():
                event.accept()
                return True
            if self.session.navigation.mode:
                self.session.navigation.set_mode(None)
                event.accept()
                return True
            # FreeCAD's Sketcher only sees Esc when its Coin3D viewport owns
            # keyboard focus. Clicking Design's ribbon moves focus to Qt
            # buttons, leaving native Rectangle/Line in an active command.
            # Forward the event once to the actual 3D view, not the main window.
            if modeling.in_sketch() and not self.is_viewport(watched) and not self.editable_focus():
                window = self.session.mdi.activeSubWindow()
                root = window.widget() if window else self.session.mdi
                target = next(
                    (w for w in root.findChildren(QtWidgets.QWidget)
                     if self.is_viewport(w) and w.isVisible()), None
                )
                if target is not None:
                    target.setFocus(QtCore.Qt.OtherFocusReason)
                    forwarded = QtGui.QKeyEvent(
                        QtCore.QEvent.KeyPress, QtCore.Qt.Key_Escape,
                        QtCore.Qt.NoModifier
                    )
                    self.forwarding = True
                    try:
                        QtWidgets.QApplication.sendEvent(target, forwarded)
                    finally:
                        self.forwarding = False
                    event.accept()
                    return True
        if kind == QtCore.QEvent.MouseButtonDblClick and event.button() == QtCore.Qt.LeftButton:
            parent = watched if isinstance(watched, QtWidgets.QWidget) else None
            in_browser = False
            while parent and parent != self.session.main:
                if parent.metaObject().className() == "Gui::TreeWidget":
                    in_browser = True
                    break
                parent = parent.parentWidget()
            selected = Gui.Selection.getSelection()
            if (
                in_browser
                and len(selected) == 1
                and not Gui.Control.activeDialog()
                and (
                    selected[0].isDerivedFrom("Sketcher::SketchObject")
                    or selected[0].isDerivedFrom("PartDesign::Hole")
                )
            ):
                feature = selected[0]
                if feature.isDerivedFrom("Sketcher::SketchObject"):
                    QtCore.QTimer.singleShot(0, lambda: modeling.edit_sketch(feature))
                else:
                    from .hole import edit_feature
                    QtCore.QTimer.singleShot(0, lambda: edit_feature(feature))
                event.accept()
                return True
        if kind in (QtCore.QEvent.ShortcutOverride, QtCore.QEvent.KeyPress):
            if self.editable_focus():
                return False
            if event.modifiers() & (
                QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier | QtCore.Qt.MetaModifier
            ):
                return False
            if event.modifiers() & QtCore.Qt.ShiftModifier:
                return False
            key = event.text().upper()
            mapping = SKETCH_KEYS if modeling.in_sketch() else SOLID_KEYS
            if key not in mapping:
                return False
            if kind == QtCore.QEvent.ShortcutOverride:
                event.accept()
                return True
            if not event.isAutoRepeat():
                command = TOOLS[mapping[key]].command
                QtCore.QTimer.singleShot(0, lambda: commands.invoke(command))
            event.accept()
            return True
        if kind not in (
            QtCore.QEvent.MouseButtonPress,
            QtCore.QEvent.MouseButtonRelease,
            QtCore.QEvent.MouseMove,
        ):
            return False
        if not self.is_viewport(watched):
            return False
        mode = self.session.navigation.mode
        if mode and (
            event.button() == QtCore.Qt.LeftButton or event.buttons() & QtCore.Qt.LeftButton
        ):
            modifiers = event.modifiers()
            if mode == "orbit":
                modifiers |= QtCore.Qt.ShiftModifier
            else:
                modifiers &= ~QtCore.Qt.ShiftModifier
            if self.session.remap_mouse:
                modifiers ^= QtCore.Qt.ShiftModifier
            button = (
                QtCore.Qt.MiddleButton
                if event.button() == QtCore.Qt.LeftButton
                else QtCore.Qt.NoButton
            )
            buttons = (
                QtCore.Qt.MiddleButton
                if event.buttons() & QtCore.Qt.LeftButton
                else QtCore.Qt.NoButton
            )
            return self.forward_mouse(watched, event, button, buttons, modifiers)
        if kind == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.RightButton:
            self.clear_snap_points()
        if event.button() == QtCore.Qt.LeftButton:
            from .tasks import active_extrude
            task = active_extrude()
            if kind == QtCore.QEvent.MouseButtonRelease and self.profile_press:
                owner, index = self.profile_press
                self.profile_press = None
                if task is owner and task.profile_at(watched, event) == index:
                    task.toggle_profile(task.profile_list.item(index))
                return True
            if kind == QtCore.QEvent.MouseButtonPress and task is not None:
                index = task.profile_at(watched, event)
                if index is not None:
                    self.profile_press = (task, index)
                    return True
            if kind == QtCore.QEvent.MouseButtonRelease and self.snap_press:
                viewport, position = self.snap_press
                self.snap_press = None
                if viewport is watched:
                    consumed = self.forward_mouse(watched, event, event.button(), event.buttons(),
                                                  event.modifiers(), position)
                    self.finish_snapped_geometry()
                    return consumed
            if (kind == QtCore.QEvent.MouseButtonPress and
                    event.modifiers() == QtCore.Qt.NoModifier and
                    self.is_sketch_tool_cursor(watched)):
                # FreeCAD's active drawing handler installs a pixmap cursor.
                # Leave ordinary selection and drag modes on native input.
                hit = self.session.snap_guides.target(watched, event, exact=True)
                if hit is not None:
                    target, local = hit
                    sketch = modeling.in_sketch()
                    if self.snap_geometry is None or self.snap_geometry[0] != sketch:
                        self.clear_snap_points()
                        self.snap_geometry = (sketch, sketch.GeometryCount)
                    if local is not None and isinstance(target[2], str):
                        self.snap_points.append(local)
                    position = QtCore.QPointF(*target[1])
                    self.snap_press = (watched, position)
                    consumed = self.forward_mouse(watched, event, event.button(), event.buttons(),
                                                  event.modifiers(), position)
                    self.finish_snapped_geometry()
                    return consumed
            if kind == QtCore.QEvent.MouseButtonRelease:
                QtCore.QTimer.singleShot(0, self.finish_snapped_geometry)
        if not self.session.remap_mouse:
            return False
        middle = event.button() == QtCore.Qt.MiddleButton or bool(
            event.buttons() & QtCore.Qt.MiddleButton
        )
        if not middle or event.modifiers() & (
            QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier | QtCore.Qt.MetaModifier
        ):
            return False
        # Blender navigation already implements both operations. Inverting only
        # the Shift modifier gives MMB=pan and Shift+MMB=orbit without replacing
        # picking, camera maths or geometry selection.
        modifiers = event.modifiers() ^ QtCore.Qt.ShiftModifier
        return self.forward_mouse(watched, event, event.button(), event.buttons(), modifiers)

    def finish_snapped_geometry(self):
        if self.snap_geometry is None:
            return
        sketch, first = self.snap_geometry
        if modeling.in_sketch() != sketch:
            self.clear_snap_points()
            return
        if sketch.GeometryCount <= first:
            return
        points = self.snap_points[:]
        self.clear_snap_points()
        if not points:
            return
        from .snap_targets import align_new_line_endpoints
        align_new_line_endpoints(sketch, first, points)

    def clear_snap_points(self):
        self.snap_geometry = None
        self.snap_points.clear()

    def forward_mouse(self, watched, event, button, buttons, modifiers, position=None):
        original = event.position() if hasattr(event, "position") else event.localPos()
        position = original if position is None else position
        global_position = (
            event.globalPosition() if hasattr(event, "globalPosition") else event.screenPos()
        )
        global_position += position - original
        forwarded = QtGui.QMouseEvent(
            event.type(), position, global_position, button, buttons, modifiers
        )
        self.forwarding = True
        try:
            QtWidgets.QApplication.sendEvent(watched, forwarded)
        finally:
            self.forwarding = False
        return True


class Session:
    def __init__(self):
        self.main = Gui.getMainWindow()
        self.active = False
        self.original_state = self.main.saveState()
        self.original_style = self.main.styleSheet()
        self.original_menu_visible = not self.main.menuBar().isHidden()
        self.original_corners = [
            (corner, self.main.corner(corner))
            for corner in (QtCore.Qt.BottomLeftCorner, QtCore.Qt.BottomRightCorner)
        ]
        self.mdi = self.main.findChild(QtWidgets.QMdiArea)
        self.native_tabs = []
        self.appearance = Appearance()
        self.original_bars = [
            (bar, not bar.isHidden()) for bar in self.main.findChildren(QtWidgets.QToolBar)
        ]
        self.original_toggle_visibility = {
            bar.objectName(): bar.toggleViewAction().isVisible() for bar, _ in self.original_bars
        }
        self.native_docks = []
        self.views = []
        self.remap_mouse = False
        self.last_edit = None
        self.last_problem = None
        self.last_task = False
        self.model_dock = None
        self.tasks_dock = None
        for dock in self.main.findChildren(QtWidgets.QDockWidget):
            self.native_docks.append((dock, dock.windowTitle(), dock.minimumWidth()))
            if dock.objectName() in ("Model", "Combo View"):
                self.model_dock = dock
            if dock.objectName() == "Tasks":
                self.tasks_dock = dock
        self.toolbar = QtWidgets.QToolBar("Design", self.main)
        self.toolbar.setObjectName("AzDesignRibbonBar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.ribbon = Ribbon()
        self.toolbar.addWidget(self.ribbon)
        self.main.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)
        self.browser_dock = QtWidgets.QDockWidget("Browser", self.main)
        self.browser_dock.setObjectName("AzDesignBrowserDock")
        self.browser_dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.browser_dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.browser_dock.setTitleBarWidget(QtWidgets.QWidget())
        self.browser = Browser()
        self.browser_dock.setWidget(self.browser)
        self.browser_dock.setMinimumWidth(235)
        self.main.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.browser_dock)
        self.history_dock = QtWidgets.QDockWidget("Az Feature History", self.main)
        self.history_dock.setObjectName("AzDesignHistoryDock")
        self.history_dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        self.history_dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.history_dock.setTitleBarWidget(QtWidgets.QWidget())
        self.history = History()
        self.history_dock.setWidget(self.history)
        self.history_dock.setMinimumHeight(40)
        self.history_dock.setMaximumHeight(48)
        self.main.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.history_dock)
        self.main.resizeDocks([self.history_dock], [44], QtCore.Qt.Vertical)
        self.sketch_dock = QtWidgets.QDockWidget("Sketch Palette", self.main)
        self.sketch_dock.setObjectName("AzSketchPaletteDock")
        self.sketch_dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.sketch_dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.sketch_dock.setTitleBarWidget(QtWidgets.QWidget())
        self.sketch_palette = SketchPalette(self.appearance)
        self.sketch_dock.setWidget(self.sketch_palette)
        self.sketch_dock.setMinimumWidth(215)
        self.sketch_dock.setMinimumHeight(110)
        self.sketch_dock.setMaximumHeight(265)
        self.main.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.sketch_dock)
        self.sketch_dock.hide()
        from .home import DesignHome
        self.home = DesignHome(self.ribbon)
        self.ribbon.layout().addWidget(self.home)
        self.navigation = Navigation(self, self.mdi.viewport())
        self.canvas_actions = CanvasActions(self, self.mdi.viewport())
        self.snap_guides = HoverGuides()
        self.radial = RadialMenu(self.main)
        for label, name in (
            ("Python console", "Python console"),
            ("Report view", "Report view"),
            ("Native Browser / Properties", "Model"),
        ):
            dock = self.main.findChild(QtWidgets.QDockWidget, name)
            if dock:
                self.ribbon.advanced_menu.addAction(
                    label, lambda dock=dock: dock.setVisible(not dock.isVisible())
                )
        self.ribbon.advanced_menu.addAction("Restore Design layout", self.restore_design_layout)
        menus = self.ribbon.advanced_menu.addAction("FreeCAD menu bar")
        menus.setCheckable(True)
        menus.toggled.connect(self.main.menuBar().setVisible)
        self.filter = InteractionFilter(self)
        self.timer = QtCore.QTimer(self.main)
        self.timer.setInterval(350)
        self.timer.timeout.connect(self.tick)

    def activate(self):
        self.active = True
        self.appearance.activate()
        # Fusion-style Esc: cancel Sketcher tools without leaving sketch edit.
        # FreeCAD TaskDlgEditSketch reads this flag when the task is created.
        # Finish Sketch remains the explicit way out of edit mode.
        App.ParamGet("User parameter:BaseApp/Preferences/Mod/Sketcher").SetBool(
            "LeaveSketchWithEscape", False
        )
        self.main.setStyleSheet(self.original_style + """
QToolBar#AzDesignRibbonBar { border: 0; padding: 0; spacing: 0; background: #f7f8f9; }
QDockWidget#AzDesignBrowserDock { background: #f8f9fa; border-right: 1px solid #d3dae0; }
QDockWidget#AzDesignHistoryDock { background: #e8ecef; border-top: 1px solid #cdd5dc; }
QDockWidget#AzSketchPaletteDock { background: #f7f9fb; border-left: 1px solid #ccd9e4; }
QDockWidget#Tasks { color: #41515d; background: #f7f8fa; }
QStatusBar { background: #e8ecef; color: #657583; font-size: 12px; }
QWidget#AzHoleForm, QWidget#AzExtrudeForm {
    background: #f8fafb; color: #374f5f; }
QWidget#AzHoleForm QLabel, QWidget#AzExtrudeForm QLabel { color: #52697a; }
QWidget#AzHoleForm QGroupBox, QWidget#AzExtrudeForm QGroupBox {
    background: #f7fafc; border: 1px solid #d2dfe8;
    border-radius: 5px; margin-top: 11px; padding: 7px; font-weight: 600; }
QWidget#AzHoleForm QGroupBox::title, QWidget#AzExtrudeForm QGroupBox::title {
    subcontrol-origin: margin; left: 10px; color: #376586; }
QWidget#AzHoleForm QDoubleSpinBox, QWidget#AzHoleForm QComboBox,
QWidget#AzExtrudeForm QComboBox, QWidget#AzExtrudeForm QLineEdit {
    border: 1px solid #bbcbd7; border-radius: 4px; padding: 5px;
    background: #ffffff; color: #30495a; min-height: 20px; }
QWidget#AzHoleForm QPushButton, QWidget#AzExtrudeForm QPushButton {
    border: 1px solid #b8cedd; border-radius: 4px; padding: 6px;
    background: #eaf3f9; color: #31536e; }
QWidget#AzHoleForm QPushButton:hover, QWidget#AzExtrudeForm QPushButton:hover {
    background: #d8ebf8; }
""")
        self.main.menuBar().hide()
        for dock, _title, _width in self.native_docks:
            dock.hide()
        for corner, _area in self.original_corners:
            self.main.setCorner(corner, QtCore.Qt.BottomDockWidgetArea)
        for bar, _visible in self.original_bars:
            bar.hide()
            # FreeCAD saves visibility only for toolbars whose toggle action is
            # available. Mark our temporary hiding as client-managed so it is
            # never written into the user's native toolbar preferences.
            bar.toggleViewAction().setVisible(False)
        if self.model_dock:
            self.model_dock.setWindowTitle("Native Properties")
            self.main.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.model_dock)
            self.model_dock.hide()
        if self.tasks_dock:
            self.main.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.tasks_dock)
            self.tasks_dock.setMinimumWidth(280)
            self.tasks_dock.hide()
            self.main.splitDockWidget(
                self.sketch_dock, self.tasks_dock, QtCore.Qt.Vertical
            )
        self.toolbar.show()
        self.browser_dock.show()
        self.history_dock.show()
        self.main.resizeDocks([self.browser_dock], [260], QtCore.Qt.Horizontal)
        # A no-document startup belongs to Design Home, not an empty model.
        # Do not create a document until the user selects New Design or a tool.
        self.home.refresh()
        QtWidgets.QApplication.instance().installEventFilter(self.filter)
        self.timer.start()
        QtWidgets.QApplication.instance().aboutToQuit.connect(self.appearance.deactivate)
        self.tick()
        commands.notify("Design ready. Create Sketch to start, or S to find a tool.")

    def restore_design_layout(self):
        """Recover the native Design ribbon, Browser and compact history."""
        if not self.active:
            return
        self.toolbar.show()
        self.browser_dock.show()
        self.history_dock.show()
        self.main.resizeDocks([self.browser_dock], [260], QtCore.Qt.Horizontal)
        self.main.resizeDocks([self.history_dock], [44], QtCore.Qt.Vertical)
        self.navigation.place()

    def configure_view(self):
        if not Gui.activeDocument():
            return
        view = Gui.activeDocument().activeView()
        if not view or any(saved_view == view for saved_view, _style in self.views):
            return
        try:
            previous = view.getNavigationType()
            available = view.listNavigationTypes()
            if "Gui::FusionNavigationStyle" in available:
                target = "Gui::FusionNavigationStyle"
            elif "Gui::BlenderNavigationStyle" in available:
                target = "Gui::BlenderNavigationStyle"
            else:
                return
            self.views.append((view, previous))
            view.setNavigationType(target)
            self.remap_mouse = target == "Gui::BlenderNavigationStyle"
        except (AttributeError, RuntimeError):
            pass

    def tick(self):
        if not self.active:
            return
        try:
            self.configure_view()
            self.home.refresh()
            sketch = modeling.in_sketch()
            if sketch is None and not Gui.Control.activeDialog():
                # The native Sketch Tasks Close button bypasses our Design
                # Finish handler; still advance face-first Hole placement.
                from .hole import complete_pending_face_hole
                complete_pending_face_hole()
            editing = sketch.Name if sketch else None
            if editing != self.last_edit:
                self.ribbon.update_context(bool(sketch))
                self.last_edit = editing
                if sketch and self.tasks_dock:
                    # Wait until the native Tasks dock has entered sketch mode,
                    # then reserve only a slim top strip for sketch options.
                    QtCore.QTimer.singleShot(0, self.arrange_sketch_docks)
            self.sketch_dock.setVisible(bool(sketch))
            if sketch:
                self.sketch_palette.refresh(sketch)
            else:
                self.filter.snap_press = None
                self.filter.clear_snap_points()
                self.snap_guides.hide()
            self.history.refresh()
            self.browser.refresh()
            self.ribbon.documents.refresh()
            self.appearance.update()
            self.navigation.place()
            self.canvas_actions.refresh()
            for tab in self.mdi.findChildren(QtWidgets.QTabBar):
                if tab.parentWidget() == self.mdi:
                    if not any(saved == tab for saved, _visible in self.native_tabs):
                        self.native_tabs.append((tab, not tab.isHidden()))
                    tab.hide()
            self.ribbon.update_enabled()
            if self.tasks_dock:
                wants_tasks = bool(
                    Gui.Control.activeDialog()
                    or (Gui.activeDocument() and Gui.activeDocument().getInEdit())
                )
                if wants_tasks != self.last_task:
                    self.navigation.set_mode(None)
                    self.last_task = wants_tasks
                self.tasks_dock.setVisible(wants_tasks)
                self.tasks_dock.setWindowTitle("Sketch Tasks" if sketch else "Tasks")
                if wants_tasks:
                    self.style_tasks()
            # Some native commands reveal their old toolbar while editing.
            for bar, _visible in self.original_bars:
                if not bar.isHidden():
                    bar.hide()
                bar.toggleViewAction().setVisible(False)
        except Exception:
            problem = traceback.format_exc()
            if problem != self.last_problem:
                App.Console.PrintError("Az Design refresh:\n" + problem)
                self.last_problem = problem

    def arrange_sketch_docks(self):
        """Keep the sketch settings compact and native solver/task view usable."""
        if not self.active or not modeling.in_sketch() or not self.tasks_dock:
            return
        try:
            self.main.resizeDocks(
                [self.sketch_dock, self.tasks_dock],
                [225, max(260, self.main.height() - 390)],
                QtCore.Qt.Vertical,
            )
        except (RuntimeError, ValueError):
            pass

    def style_tasks(self, restore=False):
        if not self.tasks_dock:
            return
        for widget in self.tasks_dock.findChildren(QtWidgets.QWidget):
            saved = widget.property("_az_original_style")
            if restore:
                if saved is not None:
                    widget.setStyleSheet(saved)
                    widget.setProperty("_az_original_style", None)
                continue
            if saved is not None:
                continue
            name = widget.metaObject().className()
            style = None
            if widget.property("class") == "header":
                style = "background: #e5ebf0; color: #405567; border: 0; border-bottom: 1px solid #ccd6de;"
            elif name in ("QSint::ActionPanel", "QSint::TaskGroup", "Gui::TaskView::TaskPanel"):
                style = "background: #f7f8fa; color: #405567; border: 0;"
            if style:
                widget.setProperty("_az_original_style", widget.styleSheet())
                widget.setStyleSheet(style)

    def deactivate(self):
        from .tasks import cancel_active
        from .solid_pattern import cancel_active as cancel_solid_pattern
        from .sketch_pattern_ui import cancel_active as cancel_sketch_pattern

        cancel_solid_pattern()
        cancel_sketch_pattern()
        from .edge_treatments_canvas import cancel_active as cancel_edge_tool
        cancel_edge_tool()
        cancel_active()
        self.active = False
        self.timer.stop()
        try:
            QtWidgets.QApplication.instance().aboutToQuit.disconnect(self.appearance.deactivate)
        except RuntimeError:
            pass
        self.appearance.deactivate()
        self.style_tasks(restore=True)
        from .sketch_plane_picker import cancel_active as cancel_sketch_plane
        cancel_sketch_plane()
        from .hole import cancel_face_picker, cancel_pending_face_hole
        cancel_face_picker()
        cancel_pending_face_hole()
        self.home.hide()
        self.navigation.hide()
        self.navigation.cube_home.hide()
        self.canvas_actions.hide()
        self.snap_guides.release()
        self.radial.close()
        QtWidgets.QApplication.instance().removeEventFilter(self.filter)
        # FreeCAD activates the destination C++ toolbars before calling this
        # Python hook. Keep those newly visible bars when restoring the layout.
        incoming = Gui.activeWorkbench()
        switching_workbench = incoming and incoming.name() != "AzDesignWorkbench"
        destination_bars = {
            bar.objectName(): not bar.isHidden()
            for bar in self.main.findChildren(QtWidgets.QToolBar)
            if bar != self.toolbar
        }
        destination_toggles = {
            bar.objectName(): bar.toggleViewAction().isVisible()
            for bar in self.main.findChildren(QtWidgets.QToolBar)
            if bar != self.toolbar
        }
        for view, previous in self.views:
            try:
                view.setNavigationType(previous)
            except (RuntimeError, ReferenceError):
                pass
        self.views = []
        self.main.removeToolBar(self.toolbar)
        self.main.removeDockWidget(self.history_dock)
        self.main.removeDockWidget(self.browser_dock)
        self.main.removeDockWidget(self.sketch_dock)
        self.toolbar.hide()
        self.history_dock.hide()
        self.browser_dock.hide()
        self.sketch_dock.hide()
        # Detach before deferred deletion. A user can re-enter the workbench in
        # the same event-loop turn; its next layout snapshot must not capture
        # these retired widgets or retain dangling toolbar wrappers.
        self.toolbar.setParent(None)
        self.history_dock.setParent(None)
        self.browser_dock.setParent(None)
        self.sketch_dock.setParent(None)
        for dock, title, width in self.native_docks:
            dock.setWindowTitle(title)
            dock.setMinimumWidth(width)
        self.main.restoreState(self.original_state)
        self.main.setStyleSheet(self.original_style)
        self.main.menuBar().setVisible(self.original_menu_visible)
        for corner, area in self.original_corners:
            self.main.setCorner(corner, area)
        for tab, visible in self.native_tabs:
            try:
                tab.setVisible(visible)
            except RuntimeError:
                pass
        for bar, visible in self.original_bars:
            destination_visible = destination_bars.get(bar.objectName(), False)
            bar.setVisible(visible or (switching_workbench and destination_visible))
            toggle_visible = (
                destination_toggles.get(bar.objectName(), False)
                if switching_workbench
                else self.original_toggle_visibility.get(bar.objectName(), False)
            )
            bar.toggleViewAction().setVisible(toggle_visible)
        if self.tasks_dock and Gui.Control.activeDialog():
            self.tasks_dock.show()
        self.toolbar.deleteLater()
        self.history_dock.deleteLater()
        self.browser_dock.deleteLater()
        self.sketch_dock.deleteLater()
        self.home.deleteLater()
        if getattr(self, "hole_face_picker", None) is not None:
            self.hole_face_picker.deleteLater()
        if getattr(self, "sketch_plane_picker", None) is not None:
            self.sketch_plane_picker.deleteLater()
        self.navigation.cube_home.deleteLater()
        self.navigation.deleteLater()
        self.canvas_actions.deleteLater()
        self.radial.deleteLater()
        self.filter.deleteLater()
        self.timer.deleteLater()


def start():
    global _session
    if _session:
        return
    session = Session()
    _session = session
    try:
        session.activate()
    except Exception:
        session.deactivate()
        _session = None
        raise


def stop():
    global _session
    if _session:
        session = _session
        _session = None
        session.deactivate()
