# SPDX-License-Identifier: LGPL-2.1-or-later
"""Az-owned Hole task with stable layout and explicit, safe native previews."""

import FreeCADGui as Gui
from .qt import QtWidgets
from . import modeling, features
from .hole_spec import HoleSpec, THREAD_TYPES, thread_sizes
from .hole_operation import HoleOperation


def selected_sketch(doc):
    for obj in Gui.Selection.getSelection():
        if obj.Document == doc and obj.isDerivedFrom("Sketcher::SketchObject"):
            return obj
    return None


def mm(value):
    return float(getattr(value, "Value", value))


class HoleTask:
    def __init__(self, doc, selected=None, editing=None):
        self.doc, self.editing = doc, editing
        self.operation = None
        self.closed = False
        if editing and editing.ModelThread:
            raise features.DesignError(
                "This Hole contains geometric threads. Use Native CAD to edit it; "
                "Az will not trigger crash-prone helical recomputation."
            )
        self.sketches = [
            obj for obj in doc.Objects
            if obj.isDerivedFrom("Sketcher::SketchObject") and features.owner_body(obj)
        ]
        if editing:
            selected = editing.Profile
            if selected not in self.sketches:
                raise features.DesignError("This Hole has no usable source sketch.")

        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("Edit Hole" if editing else "Hole")
        self.form.setObjectName("AzHoleForm")
        layout = QtWidgets.QVBoxLayout(self.form)
        title = QtWidgets.QLabel("EDIT HOLE" if editing else "HOLE")
        title.setStyleSheet("font-size: 17px; font-weight: 600; color: #234b66;")
        layout.addWidget(title)
        description = QtWidgets.QLabel(
            "Choose a sketch containing hole centers (circle or arc centers)."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addWidget(QtWidgets.QLabel("Hole-center sketch"))
        self.source = QtWidgets.QComboBox()
        self.source.addItem("Choose a sketch…", None)
        for obj in self.sketches:
            self.source.addItem(obj.Label, obj.Name)
        if selected in self.sketches:
            self.source.setCurrentIndex(self.sketches.index(selected) + 1)
        self.source.setEnabled(not editing)
        layout.addWidget(self.source)

        layout.addWidget(QtWidgets.QLabel("Diameter"))
        self.diameter = QtWidgets.QDoubleSpinBox()
        self.diameter.setRange(0.01, 10000)
        self.diameter.setDecimals(3)
        self.diameter.setSuffix(" mm")
        self.diameter.setValue(mm(editing.Diameter) if editing else 6)
        layout.addWidget(self.diameter)
        layout.addWidget(QtWidgets.QLabel("Depth"))
        self.depth_type = QtWidgets.QComboBox()
        self.depth_type.addItems(["Distance", "Through all"])
        self.depth_type.setCurrentIndex(
            1 if editing and str(editing.DepthType) == "ThroughAll" else 0
        )
        layout.addWidget(self.depth_type)
        self.depth = QtWidgets.QDoubleSpinBox()
        self.depth.setRange(0.01, 10000)
        self.depth.setDecimals(3)
        self.depth.setSuffix(" mm")
        self.depth.setValue(mm(editing.Depth) if editing else 10)
        layout.addWidget(self.depth)
        self.depth_type.currentIndexChanged.connect(
            lambda _i: self.depth.setEnabled(self.depth_type.currentIndex() == 0)
        )
        self.depth.setEnabled(self.depth_type.currentIndex() == 0)

        layout.addWidget(QtWidgets.QLabel("Thread standard"))
        self.standard = QtWidgets.QComboBox()
        for value in THREAD_TYPES:
            self.standard.addItem(value, value)
        initial = str(editing.ThreadType) if editing and editing.Threaded else "None"
        self.standard.setCurrentIndex(
            THREAD_TYPES.index(initial) if initial in THREAD_TYPES else 0
        )
        layout.addWidget(self.standard)
        layout.addWidget(QtWidgets.QLabel("Thread size"))
        self.size = QtWidgets.QComboBox()
        layout.addWidget(self.size)
        self.modeled = QtWidgets.QCheckBox("Actually model helical threads — EXPERIMENTAL")
        self.modeled.setObjectName("AzExperimentalModelThread")
        self.modeled.setChecked(False)
        self.modeled.setEnabled(initial != "None")
        layout.addWidget(self.modeled)
        notice = QtWidgets.QLabel(
            "Normal holes use native cosmetic threads. Experimental helical threads "
            "may crash ALL of FreeCAD and lose unsaved work. For debugging, open "
            "a separate FreeCAD instance and use a disposable document. "
            "A diagnostic log is written before native recomputation."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("color: #80572b; padding: 6px 0;")
        layout.addWidget(notice)
        buttons = QtWidgets.QHBoxLayout()
        self.result_button = QtWidgets.QPushButton("Show result")
        self.result_button.clicked.connect(self.preview)
        self.base_button = QtWidgets.QPushButton("Show original solid")
        self.base_button.clicked.connect(self.show_base)
        buttons.addWidget(self.result_button)
        buttons.addWidget(self.base_button)
        layout.addLayout(buttons)
        self.status = QtWidgets.QLabel("Choose a sketch and select Show result.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()
        self.standard.currentIndexChanged.connect(self.standard_changed)
        self.populate_sizes(initial, editing)
        if editing and editing.Threaded:
            index = self.size.findData(str(editing.ThreadSize))
            if index >= 0:
                self.size.setCurrentIndex(index)

    def populate_sizes(self, standard, feature=None):
        self.size.blockSignals(True)
        self.size.clear()
        if standard == "None":
            self.size.addItem("Not threaded", "")
            self.size.setEnabled(False)
        else:
            self.size.addItem("Select thread size…", "")
            self.size.setEnabled(True)
            if feature is not None:
                for value in feature.getEnumerationsOfProperty("ThreadSize"):
                    self.size.addItem(str(value), str(value))
        self.size.blockSignals(False)

    def standard_changed(self, _index):
        standard = self.standard.currentData()
        self.modeled.setEnabled(standard != "None")
        if standard == "None":
            self.modeled.setChecked(False)
        if self.operation and self.operation.started:
            self.operation.valid = False
            self.operation.show_base()
            try:
                choices = thread_sizes(self.operation.hole, standard)
            except Exception as exc:
                self.message(str(exc), True)
                return
            self.populate_sizes(standard)
            for value in choices:
                self.size.addItem(value, value)
        else:
            self.populate_sizes(standard)
        self.message("Choose Show result to refresh the Hole.")

    def message(self, message, error=False):
        self.status.setText(message)
        self.status.setStyleSheet(
            "color: #ac422e;" if error else "color: #21734a;"
        )

    def settings(self, *, experimental=False):
        return HoleSpec(
            diameter=self.diameter.value(),
            depth=self.depth.value(),
            through_all=self.depth_type.currentIndex() == 1,
            thread_type=self.standard.currentData(),
            thread_size=self.size.currentData() or "",
            model_thread=self.modeled.isChecked(),
            experimental=experimental,
        )

    def ensure_operation(self):
        if self.operation:
            return self.operation
        name = self.source.currentData()
        sketch = self.doc.getObject(name) if name else None
        if not sketch:
            raise features.DesignError("Choose a hole-center sketch first.")
        self.operation = HoleOperation(self.doc, sketch, self.editing)
        self.source.setEnabled(False)
        return self.operation

    def preview(self):
        if self.closed:
            return False
        try:
            if self.modeled.isChecked():
                choice = QtWidgets.QMessageBox.warning(
                    self.form,
                    "Experimental modeled threads — FreeCAD may crash",
                    "This enables FreeCAD's real OCCT helical thread generator. "
                    "It has previously crashed FreeCAD on this workstation.\\n\\n"
                    "SAVE your other documents first. Prefer a second FreeCAD "
                    "instance and a disposable part. The crash may terminate "
                    "the entire process without an undo or normal traceback.\\n\\n"
                    "A diagnostic log will be flushed before the native operation. "
                    "Run this experiment now?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No,
                )
                if choice != QtWidgets.QMessageBox.Yes:
                    self.message("Modeled thread test cancelled; no geometry changed.")
                    return False
            spec = self.settings(experimental=self.modeled.isChecked()).validate()
            operation = self.ensure_operation()
            if spec.thread_type != "None" and not spec.thread_size:
                # Options depend on the native Hole standard and FreeCAD version.
                # Never silently choose the first tap size.
                operation._start()
                options = thread_sizes(operation.hole, spec.thread_type)
                self.populate_sizes(spec.thread_type)
                for value in options:
                    self.size.addItem(value, value)
                operation.valid = False
                operation.show_base()
                self.message("Choose the actual thread size, then Show result.", True)
                return False
            volume = operation.preview(spec)
            status = "Valid Hole · result volume {:.3f} mm³".format(volume)
            if spec.model_thread:
                status += " · diagnostic: " + str(operation.last_diagnostic)
            self.message(status)
            return True
        except Exception as exc:
            if self.operation:
                self.operation.valid = False
                self.operation.show_base()
            self.message(str(exc), True)
            return False

    def show_base(self):
        if self.operation:
            self.operation.show_base()
        self.message("Original solid displayed; preview not accepted.")

    def getStandardButtons(self):
        return int(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

    def accept(self):
        # Don't recompute the same successful modeled preview (which could
        # repeat the kernel crash) when the user clicks OK.
        expected = self.settings(experimental=self.modeled.isChecked())
        if (
            not self.operation
            or not self.operation.valid
            or self.operation.last_spec != expected
        ):
            if not self.preview():
                return False
        try:
            hole = self.operation.accept()
        except Exception as exc:
            self.message(str(exc), True)
            return False
        self.cleanup()
        Gui.Control.closeDialog()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(hole)
        return True

    def reject(self):
        if self.operation:
            self.operation.cancel()
        self.cleanup()
        Gui.Control.closeDialog()
        return True

    def cleanup(self):
        if not self.closed:
            self.closed = True
            from .tasks import forget
            forget(self)

    def isAllowedAlterDocument(self):
        return False


def show_hole(editing=None):
    from .tasks import track
    if modeling.in_sketch():
        raise features.DesignError("Finish the sketch before creating a Hole.")
    if Gui.Control.activeDialog():
        raise features.DesignError("Finish or cancel the current operation first.")
    doc = modeling.current_document()
    if not doc:
        raise features.DesignError("Create a solid and hole-center sketch first.")
    task = HoleTask.__new__(HoleTask)
    try:
        task.__init__(doc, selected_sketch(doc), editing)
        Gui.Control.showDialog(task)
        track(task)
        return task
    except Exception:
        if getattr(task, "operation", None):
            task.operation.cancel()
        raise


def edit_feature(obj):
    if not obj.isDerivedFrom("PartDesign::Hole"):
        raise features.DesignError("Select a native Hole feature.")
    return show_hole(editing=obj)
