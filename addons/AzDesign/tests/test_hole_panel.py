# SPDX-License-Identifier: LGPL-2.1-or-later
"""Headless Qt wiring smoke test for the Az Hole panel.

No Qt/FreeCAD GUI in the packaging runner: exercise signal hookups, native
size dropdown readiness and manual-only modeled-thread preview with stubs.
"""

import importlib
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ADDON = Path(__file__).resolve().parents[1]


class Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)


class Widget:
    def __init__(self, *args):
        self.title = args[0] if args and isinstance(args[0], str) else ""
        self.items = []
        self.index = -1
        self._value = 0
        self.checked = False
        self.blocked = False
        self.enabled = True
        self.visible = True
        self.currentIndexChanged = Signal()
        self.valueChanged = Signal()
        self.toggled = Signal()
        self.clicked = Signal()

    def setWindowTitle(self, *_): pass
    def setObjectName(self, *_): pass
    def setStyleSheet(self, *_): pass
    def setWordWrap(self, *_): pass
    def setContentsMargins(self, *_): pass
    def setSpacing(self, *_): pass
    def setRange(self, *_): pass
    def setDecimals(self, *_): pass
    def setSuffix(self, *_): pass
    def setToolTip(self, *_): pass
    def addWidget(self, *_): pass
    def addLayout(self, *_): pass
    def addRow(self, *_): pass
    def addStretch(self, *_): pass
    def setEnabled(self, value): self.enabled = value
    def setVisible(self, value): self.visible = value
    def setSingleShot(self, *_): pass
    def setInterval(self, *_): pass
    def blockSignals(self, value): self.blocked = value

    def addItem(self, label, data=None):
        self.items.append((label, data))
        if self.index == -1:
            self.index = 0

    def addItems(self, values):
        for value in values:
            self.addItem(value, value)

    def clear(self):
        self.items.clear()
        self.index = -1

    def count(self):
        return len(self.items)

    def setCurrentIndex(self, index):
        self.index = index
        if not self.blocked:
            self.currentIndexChanged.emit(index)

    def currentData(self):
        return self.items[self.index][1] if 0 <= self.index < len(self.items) else None

    def currentIndex(self):
        return self.index

    def findData(self, value):
        for i, (_, data) in enumerate(self.items):
            if data == value:
                return i
        return -1

    def setValue(self, value):
        self._value = value
        if not self.blocked:
            self.valueChanged.emit(value)

    def value(self):
        return self._value

    def setChecked(self, checked):
        changed = checked != self.checked
        self.checked = checked
        if changed and not self.blocked:
            self.toggled.emit(checked)

    def isChecked(self):
        return self.checked

    def setText(self, value):
        self.title = value


class Timer(Widget):
    def __init__(self, *_):
        super().__init__()
        self.timeout = Signal()
        self.active = False

    def start(self):
        self.active = True

    def stop(self):
        self.active = False


class FakeHole:
    def __init__(self):
        self.ModelThread = False
        self.Threaded = False
        self.ThreadType = "None"

    def getEnumerationsOfProperty(self, key):
        return ["M3", "M4", "M5"]


class Operation:
    instances = []

    def __init__(self, doc, sketch, editing=None):
        self.doc, self.sketch, self.editing = doc, sketch, editing
        self.hole = editing or FakeHole()
        self.started = False
        self.valid = False
        self.last_spec = None
        self.last_diagnostic = None
        self.calls = []
        Operation.instances.append(self)

    def _start(self):
        self.started = True

    def preview(self, spec):
        self.calls.append(spec)
        self.started = True
        self.last_spec = spec
        self.valid = True
        return 80.0

    def show_base(self): pass
    def show_result(self): pass


class HolePanelSmokeTest(unittest.TestCase):
    def setUp(self):
        Operation.instances = []
        self.old_path = list(sys.path)
        self.old_modules = {
            name: obj for name, obj in sys.modules.items()
            if name == "azdesign" or name.startswith("azdesign.")
        }
        for name in self.old_modules:
            del sys.modules[name]
        sys.path.insert(0, str(ADDON))
        qt = types.ModuleType("azdesign.qt")
        qt.QtWidgets = types.SimpleNamespace(
            QWidget=Widget, QVBoxLayout=Widget, QHBoxLayout=Widget,
            QGroupBox=Widget, QFormLayout=Widget, QLabel=Widget,
            QComboBox=Widget, QDoubleSpinBox=Widget, QCheckBox=Widget,
            QPushButton=Widget,
        )
        qt.QtCore = types.SimpleNamespace(QTimer=Timer)
        gui = types.ModuleType("FreeCADGui")
        gui.Selection = types.SimpleNamespace(getSelection=lambda: [])
        features = types.ModuleType("azdesign.features")
        features.owner_body = lambda obj: getattr(obj, "Body", None)
        features.DesignError = ValueError
        modeling = types.ModuleType("azdesign.modeling")
        operation = types.ModuleType("azdesign.hole_operation")
        operation.HoleOperation = Operation
        operation.hole_profile_sketch = lambda hole: hole.Profile
        self.patched = patch.dict(sys.modules, {
            "azdesign.qt": qt,
            "FreeCADGui": gui,
            "azdesign.features": features,
            "azdesign.modeling": modeling,
            "azdesign.hole_operation": operation,
        })
        self.patched.start()
        self.hole = importlib.import_module("azdesign.hole")
        self.sketch = types.SimpleNamespace(Name="Centers", Label="Centers", Body=object())
        self.sketch.isDerivedFrom = lambda name: name == "Sketcher::SketchObject"
        self.doc = types.SimpleNamespace(Objects=[self.sketch])
        self.doc.getObject = lambda name: self.sketch if name == "Centers" else None

    def tearDown(self):
        self.patched.stop()
        for name in list(sys.modules):
            if name == "azdesign" or name.startswith("azdesign."):
                del sys.modules[name]
        sys.modules.update(self.old_modules)
        sys.path[:] = self.old_path

    def test_simple_hole_preview_is_debounced_and_cancellable(self):
        task = self.hole.HoleTask(self.doc, selected=self.sketch)
        self.assertTrue(task.live.isChecked())
        task.diameter.setValue(8)
        self.assertTrue(task.preview_timer.active)
        task.auto_preview()
        self.assertEqual(len(Operation.instances), 1)
        self.assertEqual(Operation.instances[0].calls[0].diameter, 8)
        task.show_base()
        self.assertFalse(task.preview_timer.active)

    def test_thread_sizes_populate_on_standard_change_without_preview(self):
        task = self.hole.HoleTask(self.doc, selected=self.sketch)
        task.standard.setCurrentIndex(1)
        self.assertEqual(task.standard.items[1][0], "ISO metric · coarse")
        self.assertFalse(task.diameter.enabled)
        self.assertEqual(task.size.count(), 4)  # placeholder plus native 3
        self.assertTrue(Operation.instances[0].started)
        self.assertEqual(Operation.instances[0].calls, [])
        self.assertFalse(task.preview_timer.active)
        task.size.setCurrentIndex(2)
        self.assertTrue(task.preview_timer.active)  # cosmetic, not modeled

    def test_modeled_edit_does_not_schedule_any_automatic_recompute(self):
        native = types.SimpleNamespace(
            Profile=self.sketch, ModelThread=True, Threaded=True,
            ThreadType="ISOMetricProfile", ThreadSize="M4",
            Diameter=4, Depth=8, DepthType="Dimension",
            getEnumerationsOfProperty=lambda key: ["M3", "M4"],
        )
        task = self.hole.HoleTask(self.doc, editing=native)
        self.assertTrue(task.modeled.isChecked())
        self.assertFalse(task.live.enabled)
        task.depth.setValue(9)
        self.assertFalse(task.preview_timer.active)
        task.auto_preview()
        self.assertEqual(Operation.instances, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
