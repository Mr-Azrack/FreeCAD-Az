# SPDX-License-Identifier: LGPL-2.1-or-later
"""Temporary layout, contextual shortcuts and Fusion-style mouse navigation."""

import traceback
import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore, QtGui, QtWidgets
from .catalog import TOOLS, SOLID_KEYS, SKETCH_KEYS
from . import modeling, commands
from .ui import Ribbon, History

_session = None


def current():
    return _session


class InteractionFilter(QtCore.QObject):
    def __init__(self, session):
        super().__init__(session.main)
        self.session = session
        self.forwarding = False

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
        return any(part in name for part in ("QuarterWidget", "View3DInventorViewer", "QGLWidget"))

    def eventFilter(self, watched, event):
        if not self.session.active or self.forwarding:
            return False
        kind = event.type()
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
                and selected[0].isDerivedFrom("Sketcher::SketchObject")
                and not Gui.Control.activeDialog()
            ):
                sketch = selected[0]
                QtCore.QTimer.singleShot(0, lambda: modeling.edit_sketch(sketch))
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
        if not self.session.remap_mouse or not self.is_viewport(watched):
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
        position = event.position() if hasattr(event, "position") else event.localPos()
        global_position = (
            event.globalPosition() if hasattr(event, "globalPosition") else event.screenPos()
        )
        forwarded = QtGui.QMouseEvent(
            kind, position, global_position, event.button(), event.buttons(), modifiers
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
        self.model_dock = None
        self.tasks_dock = None
        for dock in self.main.findChildren(QtWidgets.QDockWidget):
            self.native_docks.append((dock, dock.windowTitle(), dock.minimumWidth()))
            if dock.objectName() in ("Model", "Combo View"):
                self.model_dock = dock
            if dock.objectName() == "Tasks":
                self.tasks_dock = dock
        self.toolbar = QtWidgets.QToolBar("Az Design", self.main)
        self.toolbar.setObjectName("AzDesignRibbonBar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.ribbon = Ribbon()
        self.toolbar.addWidget(self.ribbon)
        self.main.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)
        self.history_dock = QtWidgets.QDockWidget("Az Feature History", self.main)
        self.history_dock.setObjectName("AzDesignHistoryDock")
        self.history_dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        self.history_dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.history_dock.setTitleBarWidget(QtWidgets.QWidget())
        self.history = History()
        self.history_dock.setWidget(self.history)
        self.history_dock.setMinimumHeight(93)
        self.history_dock.setMaximumHeight(125)
        self.main.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.history_dock)
        self.main.resizeDocks([self.history_dock], [98], QtCore.Qt.Vertical)
        self.filter = InteractionFilter(self)
        self.timer = QtCore.QTimer(self.main)
        self.timer.setInterval(350)
        self.timer.timeout.connect(self.tick)

    def activate(self):
        self.active = True
        for bar, _visible in self.original_bars:
            bar.hide()
            # FreeCAD saves visibility only for toolbars whose toggle action is
            # available. Mark our temporary hiding as client-managed so it is
            # never written into the user's native toolbar preferences.
            bar.toggleViewAction().setVisible(False)
        if self.model_dock:
            self.model_dock.setWindowTitle("Browser")
            self.main.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.model_dock)
            self.model_dock.show()
        if self.tasks_dock:
            self.main.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.tasks_dock)
            self.tasks_dock.setMinimumWidth(280)
            self.tasks_dock.hide()
        self.toolbar.show()
        self.history_dock.show()
        QtWidgets.QApplication.instance().installEventFilter(self.filter)
        self.timer.start()
        self.tick()
        commands.notify("Az Design ready. Create Sketch to start, or S to find a tool.")

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
            sketch = modeling.in_sketch()
            editing = sketch.Name if sketch else None
            if editing != self.last_edit:
                self.ribbon.update_context(bool(sketch))
                self.last_edit = editing
            self.history.refresh()
            self.ribbon.update_enabled()
            if self.tasks_dock:
                wants_tasks = bool(
                    Gui.Control.activeDialog()
                    or (Gui.activeDocument() and Gui.activeDocument().getInEdit())
                )
                self.tasks_dock.setVisible(wants_tasks)
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

    def deactivate(self):
        from .tasks import cancel_active

        cancel_active()
        self.active = False
        self.timer.stop()
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
        self.toolbar.hide()
        self.history_dock.hide()
        # Detach before deferred deletion. A user can re-enter the workbench in
        # the same event-loop turn; its next layout snapshot must not capture
        # these retired widgets or retain dangling toolbar wrappers.
        self.toolbar.setParent(None)
        self.history_dock.setParent(None)
        for dock, title, width in self.native_docks:
            dock.setWindowTitle(title)
            dock.setMinimumWidth(width)
        self.main.restoreState(self.original_state)
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
