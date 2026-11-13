# SPDX-License-Identifier: LGPL-2.1-or-later
"""Unified, selection-aware modeling dialogs with transactional previews."""

import FreeCAD as App
import FreeCADGui as Gui
from .qt import QtCore, QtWidgets, standard_button_bits
from . import features, profiles, operations, history
from .features import DesignError

_active_task = None


def track(task):
    global _active_task
    _active_task = task


def forget(task):
    global _active_task
    if _active_task is task:
        _active_task = None


def cancel_active():
    if _active_task:
        _active_task.reject()


def selected_source():
    for selection in Gui.Selection.getSelectionEx():
        obj = selection.Object
        if obj.isDerivedFrom("Sketcher::SketchObject"):
            return (obj, [])
        for name in selection.SubElementNames:
            if name.startswith("Face"):
                if obj.isDerivedFrom("PartDesign::Body"):
                    obj = features.body_tip(obj)
                if obj:
                    return (obj, [name])
    return None


def default_target(source, doc):
    if source and source[0]:
        owner = features.owner_body(source[0])
        if owner:
            return owner
    gui_doc = Gui.activeDocument()
    view = gui_doc.activeView() if gui_doc else None
    if view and hasattr(view, "getActiveObject"):
        body = view.getActiveObject("pdbody")
        if body:
            return body
    candidates = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Body")]
    return candidates[0] if len(candidates) == 1 else None


class ExtrudeTask:
    def __init__(self, doc, source=None, cut=False, editing=None, selected_regions=None):
        self.doc = doc
        self.operation = operations.Operation(doc, editing)
        self.overlay_names = []
        self.region_data = []
        self.source_links = []
        self.picking = None
        self.busy = False
        self.closed = False
        self.valid = False
        self.limit = None
        self.manipulator = None
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("Edit Extrude" if editing else "Extrude")
        self.form.setObjectName("AzExtrudeForm")
        layout = QtWidgets.QVBoxLayout(self.form)
        heading = QtWidgets.QLabel("EDIT EXTRUDE" if editing else "EXTRUDE")
        heading.setStyleSheet("font-size: 17px; font-weight: 600; color: #234b66; padding: 4px 0;")
        layout.addWidget(heading)
        self.source = QtWidgets.QComboBox()
        self.source.setObjectName("AzProfileSource")
        self.source.addItem("Choose a sketch or pick a planar face…")
        self.source_links.append(None)
        for obj in doc.Objects:
            if obj.isDerivedFrom("Sketcher::SketchObject"):
                self.source.addItem(obj.Label)
                self.source_links.append((obj, []))
        layout.addWidget(self.source)
        picks = QtWidgets.QHBoxLayout()
        self.pick_source = QtWidgets.QPushButton("Pick face")
        self.pick_source.clicked.connect(lambda: self.begin_face_pick("source"))
        self.pick_regions = QtWidgets.QPushButton("Pick profiles in view")
        self.pick_regions.setCheckable(True)
        self.pick_regions.toggled.connect(self.toggle_profile_pick)
        picks.addWidget(self.pick_source)
        picks.addWidget(self.pick_regions)
        layout.addLayout(picks)
        self.profile_list = QtWidgets.QListWidget()
        self.profile_list.setObjectName("AzProfileList")
        self.profile_list.setMaximumHeight(108)
        self.profile_list.setMinimumHeight(58)
        layout.addWidget(self.profile_list)
        region_controls = QtWidgets.QHBoxLayout()
        self.region_buttons = []
        for label, checked in (("All profiles", True), ("Clear", False)):
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(lambda _=False, value=checked: self.select_all(value))
            self.region_buttons.append(button)
            region_controls.addWidget(button)
        self.count_label = QtWidgets.QLabel()
        region_controls.addWidget(self.count_label)
        layout.addLayout(region_controls)
        fields = self.fields = QtWidgets.QFormLayout()
        self.operation_choice = QtWidgets.QComboBox()
        self.operation_choice.setObjectName("AzOperation")
        self.operation_choice.addItems(["Auto", "Join", "Cut", "Intersect", "New body"])
        fields.addRow("Operation", self.operation_choice)
        self.target = QtWidgets.QComboBox()
        self.target.setObjectName("AzTargetBody")
        self.target.addItem("Choose a target body…", "")
        for body in doc.Objects:
            if body.isDerivedFrom("PartDesign::Body"):
                self.target.addItem(body.Label, body.Name)
        fields.addRow("Target body", self.target)
        self.distance = QtWidgets.QLineEdit("10 mm")
        self.distance.setObjectName("AzExtrudeDistance")
        self.distance.setToolTip(
            "Use mm, inches, fractions or expressions such as Parameters.Width / 2. Negative distances reverse direction."
        )
        fields.addRow("Distance", self.distance)
        self.direction = QtWidgets.QComboBox()
        self.direction.addItems(["One side", "Symmetric", "Two sides"])
        fields.addRow("Direction", self.direction)
        self.distance2 = QtWidgets.QLineEdit("10 mm")
        fields.addRow("Side 2 distance", self.distance2)
        self.flip = QtWidgets.QCheckBox("Flip direction")
        fields.addRow("", self.flip)
        self.extent = QtWidgets.QComboBox()
        self.extent.addItems(["Distance", "Through all", "To face"])
        fields.addRow("Extent", self.extent)
        self.pick_limit = QtWidgets.QPushButton("Pick target face")
        self.pick_limit.clicked.connect(lambda: self.begin_face_pick("limit"))
        fields.addRow("End face", self.pick_limit)
        layout.addLayout(fields)
        advanced = QtWidgets.QGroupBox("Start offset and taper")
        advanced.setCheckable(True)
        advanced.setChecked(False)
        advanced_layout = QtWidgets.QVBoxLayout(advanced)
        advanced_content = QtWidgets.QWidget()
        advanced_fields = self.advanced_fields = QtWidgets.QFormLayout(advanced_content)
        advanced_fields.setContentsMargins(0, 0, 0, 0)
        advanced_layout.addWidget(advanced_content)
        advanced_content.hide()
        advanced.toggled.connect(advanced_content.setVisible)
        self.offset = QtWidgets.QLineEdit("0 mm")
        self.taper = QtWidgets.QLineEdit("0 deg")
        self.taper2 = QtWidgets.QLineEdit("0 deg")
        advanced_fields.addRow("Start offset", self.offset)
        advanced_fields.addRow("Taper angle", self.taper)
        advanced_fields.addRow("Side 2 taper", self.taper2)
        layout.addWidget(advanced)
        self.status = QtWidgets.QLabel("Select profiles to preview the operation.")
        self.status.setObjectName("AzExtrudeStatus")
        self.status.setWordWrap(True)
        layout.insertWidget(1, self.status)
        self.show_preview = QtWidgets.QPushButton("Show solid preview")
        self.show_preview.clicked.connect(self.end_pick)
        layout.addWidget(self.show_preview)
        layout.addStretch()
        self.timer = QtCore.QTimer(self.form)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.preview)
        self.source.currentIndexChanged.connect(self.source_changed)
        self.profile_list.itemChanged.connect(self.profile_changed)
        for control in (self.operation_choice, self.target, self.direction, self.extent):
            control.currentIndexChanged.connect(self.schedule)
        for control in (self.distance, self.distance2, self.offset, self.taper, self.taper2):
            control.textChanged.connect(self.schedule)
        self.flip.toggled.connect(self.schedule)
        Gui.Selection.addObserver(self)
        initial = operations.spec_for(editing) if editing else None
        self.busy = True
        if initial:
            source = initial["source"]
            self.operation_choice.setCurrentText(initial["operation"])
            for key, widget in (
                ("distance", self.distance),
                ("distance2", self.distance2),
                ("offset", self.offset),
                ("taper", self.taper),
                ("taper2", self.taper2),
            ):
                widget.setText(initial[key])
            self.direction.setCurrentText(initial["direction"])
            self.extent.setCurrentText(initial["extent"])
            self.flip.setChecked(initial["reversed"])
            self.limit = initial["to_face"]
            target = initial["target"]
            selected_regions = initial["regions"]
        else:
            target = default_target(source, doc)
            if cut:
                self.operation_choice.setCurrentText("Cut")
        if source:
            self.set_source(source)
        self.busy = False
        self.source_changed()
        if target:
            self.target.setCurrentIndex(max(0, self.target.findData(target.Name)))
        if selected_regions:
            self.busy = True
            wanted = profiles.resolve(source[0], selected_regions)
            for index, region in enumerate(self.region_data):
                selected = any(
                    region.face.common(r.face).Area > region.face.Area - profiles.TOL
                    for r in wanted
                )
                self.profile_list.item(index).setCheckState(
                    QtCore.Qt.Checked if selected else QtCore.Qt.Unchecked
                )
            self.busy = False
        self.preview()
        self.schedule()
        # Multiple regions must not automatically enter pick mode: that
        # previously hid the Body and made the part flash/disappear.

    def set_source(self, source):
        for index, link in enumerate(self.source_links):
            if link and link[0] == source[0] and list(link[1]) == list(source[1]):
                self.source.setCurrentIndex(index)
                return
        self.source_links.append(source)
        self.source.addItem(
            source[0].Label
            + (" · " + ", ".join(n.lstrip("?") for n in source[1]) if source[1] else "")
        )
        self.source.setCurrentIndex(len(self.source_links) - 1)

    def source_link(self):
        return self.source_links[self.source.currentIndex()]

    def remove_overlays(self):
        for name in self.overlay_names:
            if self.doc.getObject(name):
                self.doc.removeObject(name)
        self.overlay_names = []

    def source_changed(self, *_):
        if self.busy:
            return
        self.remove_overlays()
        self.profile_list.blockSignals(True)
        self.profile_list.clear()
        self.region_data = []
        source = self.source_link()
        try:
            if source and source[0].isDerivedFrom("Sketcher::SketchObject"):
                self.region_data = profiles.regions(source[0])
                # Fusion-style sensible starting point: when a sketch clearly
                # contains one large outer plate surrounding many little holes,
                # preview the plate directly, leaving its cut-outs empty.
                # Ambiguous multi-profile sketches still require a click.
                recommended = profiles.preferred_plate_region(self.region_data)
                for index, region in enumerate(self.region_data):
                    is_plate = index == recommended and len(region.face.Wires) > 1
                    label = (
                        "Plate · {} cutout{} · {:.3f} mm²".format(
                            len(region.face.Wires) - 1,
                            "" if len(region.face.Wires) == 2 else "s",
                            region.face.Area,
                        ) if is_plate else
                        "Profile {} · {:.3f} mm²".format(index + 1, region.face.Area)
                    )
                    item = QtWidgets.QListWidgetItem(label)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    item.setCheckState(
                        QtCore.Qt.Checked if index == recommended else QtCore.Qt.Unchecked
                    )
                    self.profile_list.addItem(item)
                    overlay = self.doc.addObject("Part::Feature", "AzProfilePick")
                    overlay.addProperty("App::PropertyBool", "AzPreview")
                    overlay.AzPreview = True
                    overlay.addProperty("App::PropertyInteger", "RegionIndex")
                    overlay.RegionIndex = index
                    face = region.face.copy()
                    placement = source[0].getGlobalPlacement().multiply(face.Placement)
                    face.Placement = App.Placement()
                    overlay.Shape = face
                    overlay.Placement = placement
                    overlay.Label = "Profile " + str(index + 1)
                    overlay.ViewObject.ShowInTree = False
                    overlay.ViewObject.ShapeColor = (0.31, 0.65, 0.90)
                    overlay.ViewObject.LineColor = (0.15, 0.35, 0.55)
                    overlay.ViewObject.Transparency = 30
                    overlay.ViewObject.Visibility = False
                    self.overlay_names.append(overlay.Name)
                if source[0]:
                    target = default_target(source, self.doc)
                    if target:
                        self.target.setCurrentIndex(max(0, self.target.findData(target.Name)))
            elif source:
                self.profile_list.addItem("Planar face · " + ", ".join(source[1]))
        except Exception as exc:
            self.message(str(exc), True)
        finally:
            self.profile_list.blockSignals(False)
        self.pick_regions.setEnabled(bool(self.region_data))
        for button in self.region_buttons:
            button.setEnabled(bool(self.region_data))
        self.profile_changed()

    def selected_descriptors(self):
        return [
            region.descriptor()
            for index, region in enumerate(self.region_data)
            if self.profile_list.item(index).checkState() == QtCore.Qt.Checked
        ]

    def select_all(self, checked):
        self.busy = True
        for index in range(len(self.region_data)):
            self.profile_list.item(index).setCheckState(
                QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked
            )
        self.busy = False
        self.profile_changed()

    def profile_changed(self, *_):
        if self.busy:
            return
        count = len(self.selected_descriptors())
        self.count_label.setText(str(count) + " selected")
        if self.source_link() and self.source_link()[1]:
            self.count_label.setText("1 face")
        for index, name in enumerate(self.overlay_names):
            obj = self.doc.getObject(name)
            if obj:
                obj.ViewObject.ShapeColor = (
                    (0.94, 0.57, 0.27)
                    if self.profile_list.item(index).checkState() == QtCore.Qt.Checked
                    else (0.31, 0.65, 0.90)
                )
        self.schedule()

    def spec(self):
        return {
            "source": self.source_link(),
            "regions": self.selected_descriptors(),
            "whole": False,
            "operation": self.operation_choice.currentText(),
            "target": self.doc.getObject(self.target.currentData() or ""),
            "distance": self.distance.text(),
            "distance2": self.distance2.text(),
            "direction": self.direction.currentText(),
            "reversed": self.flip.isChecked(),
            "extent": self.extent.currentText(),
            "to_face": self.limit,
            "offset": self.offset.text(),
            "taper": self.taper.text(),
            "taper2": self.taper2.text(),
        }

    def schedule(self, *_):
        if self.busy or self.closed:
            return
        self.distance2.setEnabled(self.direction.currentText() == "Two sides")
        self.distance2.setVisible(self.direction.currentText() == "Two sides")
        self.fields.labelForField(self.distance2).setVisible(
            self.direction.currentText() == "Two sides"
        )
        self.taper2.setEnabled(self.direction.currentText() == "Two sides")
        self.pick_limit.setEnabled(self.extent.currentText() == "To face")
        self.pick_limit.setVisible(self.extent.currentText() == "To face")
        self.fields.labelForField(self.pick_limit).setVisible(
            self.extent.currentText() == "To face"
        )
        self.distance.setEnabled(self.extent.currentText() == "Distance")
        # Clicking profile overlays or choosing a face must not start a
        # competing timer that deletes/shows solids during selection.
        if self.picking:
            self.timer.stop()
        else:
            self.timer.start(160)

    def message(self, message, error=False):
        self.status.setText(message)
        self.status.setStyleSheet(
            "color: #ac422e; padding: 5px 0;" if error else "color: #21734a; padding: 5px 0;"
        )

    def preview(self):
        self.timer.stop()
        if self.closed:
            return
        spec = self.spec()
        source = spec.get("source")
        if (
            source and source[0]
            and source[0].isDerivedFrom("Sketcher::SketchObject")
            and not spec["regions"] and not spec["whole"]
        ):
            self.valid = False
            self.operation.discard_preview()
            self.message(
                "Check a closed profile to preview. The original solid is still visible."
            )
            return
        try:
            outputs = self.operation.update(spec)
            self.valid = True
            action = self.operation.last_spec["resolved_operation"]
            self.message(
                "{} · {} bod{} · {:.3f} mm³".format(
                    action,
                    len(outputs),
                    "y" if len(outputs) == 1 else "ies",
                    sum(o.Shape.Volume for o in outputs),
                )
            )
            if self.picking == "profiles":
                self.apply_pick_visibility()
            else:
                self.ensure_manipulator()
        except Exception as exc:
            self.valid = False
            # A failed preview must not leave a transient invalid FeaturePython
            # as the Body Tip; it produces empty-shape warnings and appears to
            # erase an otherwise valid model.
            try:
                self.operation.discard_preview()
            except Exception as restore_error:
                App.Console.PrintWarning(
                    "Az failed to restore previous Extrude preview: "
                    + str(restore_error) + "\\n"
                )
            self.message(str(exc) + " · Original geometry restored.", True)

    def toggle_profile_pick(self, checked):
        if self.closed:
            return
        self.picking = "profiles" if checked else None
        if checked:
            self.apply_pick_visibility()
            self.message(
                "Click shaded regions to select or deselect them. Choose Show solid preview when ready."
            )
        else:
            self.end_pick()

    def apply_pick_visibility(self):
        # Profile selection must be an overlay on the existing part, NOT a
        # mode that hides every Body. That 0.4.2 behavior made valid solids
        # disappear whenever multiple profiles were available.
        self.timer.stop()
        if self.manipulator:
            self.manipulator.hide()
        self.operation.discard_preview()
        self.valid = False
        for name in self.overlay_names:
            obj = self.doc.getObject(name)
            if obj:
                obj.ViewObject.Visibility = True

    def begin_face_pick(self, mode):
        self.timer.stop()
        self.operation.discard_preview()
        self.valid = False
        self.picking = mode
        self.pick_regions.blockSignals(True)
        self.pick_regions.setChecked(False)
        self.pick_regions.blockSignals(False)
        if self.manipulator:
            self.manipulator.hide()
        for name in self.overlay_names:
            obj = self.doc.getObject(name)
            if obj:
                obj.ViewObject.Visibility = False
        self.operation._restore_visibility()
        # Editing a first/New Body extrusion has no previous Body Tip to
        # reveal. Hiding the edited result leaves only a stray sketch in
        # view and makes it appear that the existing solid was deleted.
        # Keep the existing result as a visual reference; addSelection
        # already rejects this feature and downstream faces as sources.
        has_prior_tip = any(base is not None for base in self.operation.original_bases.values())
        keep_edit_reference = bool(self.operation.editing) and not has_prior_tip
        if not keep_edit_reference:
            for obj in self.operation.outputs:
                obj.ViewObject.Visibility = False
            for body_name, base in self.operation.original_bases.items():
                body = self.doc.getObject(body_name)
                if body and base:
                    history.reveal(body, base)
        self.message(
            "Click an existing planar " + ("end face." if mode == "limit" else "face to extrude.")
            + (" The current feature is reference-only; choose an independent earlier face."
               if keep_edit_reference else "")
        )
        Gui.Selection.clearSelection()

    def end_pick(self):
        self.picking = None
        self.pick_regions.blockSignals(True)
        self.pick_regions.setChecked(False)
        self.pick_regions.blockSignals(False)
        for name in self.overlay_names:
            obj = self.doc.getObject(name)
            if obj:
                obj.ViewObject.Visibility = False
        self.operation._restore_visibility()
        self.preview()
        if self.valid:
            Gui.activeDocument().activeView().fitAll()

    def addSelection(self, document, name, sub, position):
        if self.closed or document != self.doc.Name:
            return
        obj = self.doc.getObject(name)
        if self.picking == "profiles" and obj and getattr(obj, "AzPreview", False):
            item = self.profile_list.item(obj.RegionIndex)
            item.setCheckState(
                QtCore.Qt.Unchecked if item.checkState() == QtCore.Qt.Checked else QtCore.Qt.Checked
            )
            Gui.Selection.clearSelection()
        elif self.picking in ("source", "limit") and obj and sub.startswith("Face"):
            if obj.isDerivedFrom("PartDesign::Body"):
                obj = features.body_tip(obj)
            if obj in self.operation.outputs or any(
                operations.depends_on(obj, feature) for feature in self.operation.editing
            ):
                self.message("Pick an existing face before this feature in the history.", True)
                return
            link = (obj, [sub])
            if self.picking == "limit":
                self.limit = link
                self.pick_limit.setText(obj.Label + " · " + sub)
            else:
                self.set_source(link)
            Gui.Selection.clearSelection()
            self.end_pick()

    def ensure_manipulator(self):
        try:
            from .manipulator import ExtrudeHandles

            if self.manipulator is None:
                self.manipulator = ExtrudeHandles(self)
            self.manipulator.update()
        except Exception as exc:
            # A graphics-driver/pivy failure must not invalidate a correct
            # typed-distance solid. The modeling path stays fully functional.
            App.Console.PrintWarning("Az viewport handle: " + str(exc) + "\n")

    def cleanup(self):
        if self.closed:
            return
        self.closed = True
        forget(self)
        self.timer.stop()
        Gui.Selection.removeObserver(self)
        if self.manipulator:
            self.manipulator.remove()
        self.remove_overlays()

    def getStandardButtons(self):
        return standard_button_bits(
            QtWidgets.QDialogButtonBox.Ok, QtWidgets.QDialogButtonBox.Cancel
        )

    def accept(self):
        self.picking = None
        self.preview()
        if not self.valid:
            return False
        try:
            self.remove_overlays()
            self.operation.accept()
        except Exception as exc:
            self.message(str(exc), True)
            return False
        outputs = list(self.operation.outputs)
        # Preview faces are presentation objects, removed before completing the
        # accepted transaction so they do not become stray saved geometry.
        self.cleanup()
        Gui.Control.closeDialog()
        Gui.Selection.clearSelection()
        for obj in outputs:
            Gui.Selection.addSelection(obj)
        if outputs:
            Gui.activeDocument().activeView().setActiveObject(
                "pdbody", features.owner_body(outputs[-1])
            )
        return True

    def reject(self):
        self.cleanup()
        self.operation.cancel()
        Gui.Control.closeDialog()
        return True

    def isAllowedAlterDocument(self):
        return False

    def isAllowedAlterSelection(self):
        return True

    def isAllowedAlterView(self):
        return True


def show_extrude(source=None, cut=False, editing=None):
    from . import modeling

    if modeling.in_sketch():
        source = (modeling.finish_sketch(), [])
    if Gui.Control.activeDialog():
        raise DesignError("Finish or cancel the current operation first.")
    if not modeling.current_document():
        raise DesignError("Create a sketch to start a design.")
    doc = modeling.document()
    if cut:
        # 'Cut' against a first sketch silently opened a task with no valid
        # solid to remove material from. Explain the prerequisite instead.
        has_solid = any(
            o.isDerivedFrom("PartDesign::Body")
            and hasattr(o, "Shape") and not o.Shape.isNull()
            and len(o.Shape.Solids) > 0
            for o in doc.Objects
        )
        if not has_solid:
            raise DesignError("Cut needs an existing solid. Extrude your first sketch, then select a face or sketch to Cut.")
    if source is None:
        source = selected_source()
    if source is None:
        # Design defaults to the sole closed, unused sketch just as the user
        # expects after Finish Sketch. Never guess among multiple sketches.
        candidates = []
        for obj in doc.Objects:
            if not obj.isDerivedFrom("Sketcher::SketchObject"):
                continue
            if any(getattr(parent, "Profile", None) == obj for parent in obj.InList):
                continue
            try:
                if profiles.regions(obj):
                    candidates.append(obj)
            except (RuntimeError, ValueError):
                pass
        if len(candidates) == 1:
            source = (candidates[0], [])
    task = ExtrudeTask.__new__(ExtrudeTask)
    try:
        task.__init__(doc, source or selected_source(), cut, editing)
        Gui.Control.showDialog(task)
        track(task)
        return task
    except Exception:
        if hasattr(task, "timer"):
            task.cleanup()
        if hasattr(task, "operation"):
            task.operation.cancel()
        raise


def edit_feature(obj):
    return show_extrude(obj.Source, editing=obj)
