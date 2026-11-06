# SPDX-License-Identifier: LGPL-2.1-or-later
"""Az-owned Hole task with stable layout and explicit, safe native previews."""

import FreeCADGui as Gui
from .qt import QtCore, QtWidgets
from . import modeling, features
from .hole_spec import HoleSpec, THREAD_TYPES, thread_sizes
from .hole_operation import HoleOperation, hole_profile_sketch
from .hole_ui_policy import can_live_preview


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
        # Opening an existing modeled Hole is read-only until the user
        # explicitly changes settings and approves a risky new recompute.
        self.sketches = [
            obj for obj in doc.Objects
            if obj.isDerivedFrom("Sketcher::SketchObject") and features.owner_body(obj)
        ]
        if editing:
            selected = hole_profile_sketch(editing)
            if selected not in self.sketches:
                raise features.DesignError("This Hole has no usable source sketch.")

        self._initializing = True
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("Edit Hole" if editing else "Hole")
        self.form.setObjectName("AzHoleForm")
        layout = QtWidgets.QVBoxLayout(self.form)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)

        title = QtWidgets.QLabel("EDIT HOLE" if editing else "HOLE")
        title.setStyleSheet("font-size: 17px; font-weight: 600; color: #234b66;")
        layout.addWidget(title)
        subtitle = QtWidgets.QLabel(
            "Native, editable Part Design geometry · circle centers locate holes"
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #70808a;")
        layout.addWidget(subtitle)

        center_group = QtWidgets.QGroupBox("Placement")
        center_form = QtWidgets.QFormLayout(center_group)
        self.source = QtWidgets.QComboBox()
        self.source.setObjectName("AzHoleSource")
        self.source.addItem("Choose a sketch…", None)
        for obj in self.sketches:
            self.source.addItem(obj.Label, obj.Name)
        if selected in self.sketches:
            self.source.setCurrentIndex(self.sketches.index(selected) + 1)
        # Do not guess the single available sketch: it might be the Pad
        # profile rather than a deliberate sketch of hole centers.
        self.source.setEnabled(not editing)
        center_form.addRow("Centers", self.source)
        layout.addWidget(center_group)

        geometry_group = QtWidgets.QGroupBox("Geometry")
        geometry_form = QtWidgets.QFormLayout(geometry_group)
        self.diameter = QtWidgets.QDoubleSpinBox()
        self.diameter.setObjectName("AzHoleDiameter")
        self.diameter.setRange(0.01, 10000)
        self.diameter.setDecimals(3)
        self.diameter.setSuffix(" mm")
        self.diameter.setValue(mm(editing.Diameter) if editing else 6)
        geometry_form.addRow("Diameter", self.diameter)
        self.depth_type = QtWidgets.QComboBox()
        self.depth_type.addItems(["Distance", "Through all"])
        self.depth_type.setCurrentIndex(
            1 if editing and str(editing.DepthType) == "ThroughAll" else 0
        )
        geometry_form.addRow("Extent", self.depth_type)
        self.depth = QtWidgets.QDoubleSpinBox()
        self.depth.setObjectName("AzHoleDepth")
        self.depth.setRange(0.01, 10000)
        self.depth.setDecimals(3)
        self.depth.setSuffix(" mm")
        self.depth.setValue(mm(editing.Depth) if editing else 10)
        geometry_form.addRow("Depth", self.depth)
        self.depth_type.currentIndexChanged.connect(
            lambda _i: self.depth.setEnabled(self.depth_type.currentIndex() == 0)
        )
        self.depth.setEnabled(self.depth_type.currentIndex() == 0)
        layout.addWidget(geometry_group)

        thread_group = QtWidgets.QGroupBox("Thread")
        thread_form = QtWidgets.QFormLayout(thread_group)
        self.standard = QtWidgets.QComboBox()
        self.standard.setObjectName("AzHoleThreadStandard")
        for value in THREAD_TYPES:
            self.standard.addItem(value, value)
        initial = str(editing.ThreadType) if editing and editing.Threaded else "None"
        self.standard.setCurrentIndex(
            THREAD_TYPES.index(initial) if initial in THREAD_TYPES else 0
        )
        thread_form.addRow("Standard", self.standard)
        self.size = QtWidgets.QComboBox()
        self.size.setObjectName("AzHoleThreadSize")
        thread_form.addRow("Size", self.size)
        self.modeled = QtWidgets.QCheckBox("Model actual helical threads · experimental")
        self.modeled.setObjectName("AzExperimentalModelThread")
        self.modeled.setChecked(bool(editing.ModelThread) if editing else False)
        self.modeled.setEnabled(initial != "None")
        thread_form.addRow("", self.modeled)
        self.notice = QtWidgets.QLabel(
            "Modeled threads can crash FreeCAD or lose unsaved changes. "
            "Each geometric update requires confirmation and writes a diagnostic log."
        )
        self.notice.setWordWrap(True)
        self.notice.setStyleSheet("color: #976424;")
        self.notice.setVisible(self.modeled.isChecked())
        thread_form.addRow("", self.notice)
        layout.addWidget(thread_group)

        self.live = QtWidgets.QCheckBox("Automatically update plain and cosmetic holes")
        self.live.setObjectName("AzHoleLivePreview")
        self.live.setChecked(not bool(editing.ModelThread) if editing else True)
        self.live.setEnabled(not bool(editing.ModelThread) if editing else True)
        self.live.setToolTip(
            "Changes appear after a short pause. Actual modeled threads always "
            "require an explicit Update preview and confirmation."
        )
        layout.addWidget(self.live)
        buttons = QtWidgets.QHBoxLayout()
        self.result_button = QtWidgets.QPushButton("Update preview")
        self.result_button.setObjectName("AzHolePreview")
        self.result_button.clicked.connect(lambda _checked=False: self.preview())
        self.base_button = QtWidgets.QPushButton("Show original")
        self.base_button.clicked.connect(self.show_base)
        buttons.addWidget(self.result_button)
        buttons.addWidget(self.base_button)
        layout.addLayout(buttons)
        self.status = QtWidgets.QLabel("Select a sketch to begin.")
        self.status.setObjectName("AzHoleStatus")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()

        # Debounce cheap previews; never silently enter helical OCCT geometry.
        self.preview_timer = QtCore.QTimer(self.form)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(350)
        self.preview_timer.timeout.connect(self.auto_preview)
        self.standard.currentIndexChanged.connect(self.standard_changed)
        self.source.currentIndexChanged.connect(self.source_changed)
        self.diameter.valueChanged.connect(self.changed)
        self.depth.valueChanged.connect(self.changed)
        self.depth_type.currentIndexChanged.connect(self.changed)
        self.size.currentIndexChanged.connect(self.changed)
        self.modeled.toggled.connect(self.mode_changed)
        self.live.toggled.connect(self.changed)
        self.populate_sizes(initial, editing)
        if editing and editing.Threaded:
            index = self.size.findData(str(editing.ThreadSize))
            if index >= 0:
                self.size.setCurrentIndex(index)
        # Take a normalized snapshot of the original task inputs. Closing
        # an unmodified edit should not touch a native helical feature.
        self.original_spec = (
            self.settings(experimental=bool(editing.ModelThread)) if editing
            else None
        )
        self._initializing = False
        if not editing:
            self.message(
                "Adjust dimensions and thread options; valid simple holes preview automatically."
            )
        else:
            self.message("Edit the settings. Unchanged geometry will not recompute.")

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

    def source_changed(self, _index):
        if self._initializing or self.closed:
            return
        if self.standard.currentData() != "None" and self.size.count() <= 1:
            self.standard_changed(self.standard.currentIndex())
        else:
            self.changed()

    def mode_changed(self, checked):
        self.notice.setVisible(checked)
        original_modeled = bool(self.original_spec and self.original_spec.model_thread) if hasattr(self, "original_spec") else False
        self.live.setEnabled(not checked and not original_modeled)
        if checked:
            self.preview_timer.stop()
        self.changed()

    def changed(self, *_args):
        if self._initializing or self.closed:
            return
        self.preview_timer.stop()
        current = self.settings(experimental=self.modeled.isChecked())
        if self.editing and current == self.original_spec:
            self.message("No changes · original native Hole is intact.")
            return
        previously_modeled = bool(
            self.operation and self.operation.last_spec and self.operation.last_spec.model_thread
        )
        original_modeled = bool(self.original_spec and self.original_spec.model_thread)
        ready = can_live_preview(
            current,
            enabled=self.live.isChecked(),
            has_sketch=bool(self.source.currentData()),
            original_modeled=original_modeled,
            previously_modeled=previously_modeled,
        )
        if ready:
            self.message("Updating preview…")
            self.preview_timer.start()
        elif not self.source.currentData():
            self.message("Choose a hole-center sketch.")
        elif current.thread_type != "None" and not current.thread_size:
            self.message("Choose a thread size before previewing.")
        elif current.model_thread or original_modeled or previously_modeled:
            self.message("Geometric thread changes require Update preview and confirmation.")
        else:
            self.message("Changes ready · click Update preview.")

    def auto_preview(self):
        if self._initializing or self.closed:
            return
        current = self.settings(experimental=self.modeled.isChecked())
        if can_live_preview(
            current,
            enabled=self.live.isChecked(),
            has_sketch=bool(self.source.currentData()),
            original_modeled=bool(self.original_spec and self.original_spec.model_thread),
            previously_modeled=bool(
                self.operation and self.operation.last_spec and self.operation.last_spec.model_thread
            ),
        ):
            self.preview(auto=True)

    def standard_changed(self, _index):
        if self._initializing or self.closed:
            return
        self.preview_timer.stop()
        standard = self.standard.currentData()
        self.modeled.setEnabled(standard != "None")
        if standard == "None":
            self.modeled.setChecked(False)
            self.populate_sizes(standard)
            if self.operation and self.operation.started:
                self.operation.valid = False
                self.operation.show_base()
            self.changed()
            return

        if not self.source.currentData():
            self.populate_sizes(standard)
            self.message("Choose a center sketch to load available thread sizes.")
            return
        try:
            operation = self.ensure_operation()
            operation._start()
            choices = thread_sizes(operation.hole, standard)
            operation.valid = False
            operation.show_base()
        except Exception as exc:
            self.populate_sizes(standard)
            self.message(str(exc), True)
            return
        self.populate_sizes(standard)
        for value in choices:
            self.size.addItem(value, value)
        self.message("Choose a thread size; the original solid remains visible.")

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

    def preview(self, auto=False):
        if self.closed:
            return False
        if not auto:
            self.preview_timer.stop()
        try:
            # An existing native Hole already has valid geometry. Do not
            # regenerate its helix just because Show result was clicked.
            current = self.settings(experimental=self.modeled.isChecked())
            if self.editing and current == self.original_spec and not self.operation:
                self.message("Existing Hole unchanged; no recompute necessary.")
                return True
            if (
                self.operation and self.operation.valid
                and self.operation.last_spec == current
            ):
                self.operation.show_result()
                self.message("Existing valid preview displayed; no recompute.")
                return True
            # Populate native thread-size choices without turning on modeled
            # geometry or asking for crash consent prematurely.
            preliminary = self.settings()
            if preliminary.thread_type != "None" and not preliminary.thread_size:
                operation = self.ensure_operation()
                operation._start()
                options = thread_sizes(operation.hole, preliminary.thread_type)
                self.populate_sizes(preliminary.thread_type)
                for value in options:
                    self.size.addItem(value, value)
                operation.valid = False
                operation.show_base()
                self.message("Choose the actual thread size, then Show result.", True)
                return False
            if auto and (
                self.modeled.isChecked()
                or bool(self.original_spec and self.original_spec.model_thread)
            ):
                return False  # Never auto-run the helical geometry path.
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
        self.preview_timer.stop()
        if self.operation:
            self.operation.show_base()
        self.message("Original solid displayed; preview not accepted.")

    def getStandardButtons(self):
        return int(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

    def accept(self):
        self.preview_timer.stop()
        # A simple open/close (or returning settings to their starting
        # values) must not regenerate an existing helical Hole. Discard
        # any intermediate in-transaction modifications before closing.
        expected = self.settings(experimental=self.modeled.isChecked())
        if self.editing and expected == self.original_spec:
            if self.operation and self.operation.started:
                self.operation.cancel()
            self.cleanup()
            Gui.Control.closeDialog()
            restored = self.doc.getObject(self.editing.Name)
            if restored:
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(restored)
            return True
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
        self.preview_timer.stop()
        if self.operation:
            self.operation.cancel()
        self.cleanup()
        Gui.Control.closeDialog()
        return True

    def cleanup(self):
        if not self.closed:
            self.preview_timer.stop()
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
