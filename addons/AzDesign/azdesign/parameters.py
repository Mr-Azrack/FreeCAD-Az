# SPDX-License-Identifier: LGPL-2.1-or-later
"""User parameters and model dimensions backed by native expressions."""

import re
import FreeCAD as App
from . import operations, features
from .features import DesignError


def user_parameters(doc):
    sheet = doc.getObject("Parameters")
    if sheet and not sheet.isDerivedFrom("Spreadsheet::Sheet"):
        raise DesignError(
            "An object named Parameters already exists. Rename it before creating user parameters."
        )
    if not sheet:
        return []
    return [
        (sheet.getAlias(cell), sheet.getContents(cell), cell)
        for cell in sheet.getNonEmptyCells()
        if sheet.getAlias(cell)
    ]


def model_dimensions(doc):
    rows = []
    for obj in doc.Objects:
        if getattr(obj, "AzPreview", False):
            continue
        expr = operations.expressions(obj)
        if obj.isDerivedFrom("Sketcher::SketchObject"):
            for index, constraint in enumerate(obj.Constraints):
                if constraint.Type not in (
                    "Distance",
                    "DistanceX",
                    "DistanceY",
                    "Radius",
                    "Diameter",
                    "Angle",
                    "SnellsLaw",
                ) or not obj.getDriving(index):
                    continue
                path = "Constraints[{}]".format(index)
                label = constraint.Name or "{} {}".format(constraint.Type, index + 1)
                rows.append((obj, path, label, expr.get(path, obj.getDatum(index).UserString)))
        else:
            for path in (
                "Length",
                "Length2",
                "Width",
                "Height",
                "Radius",
                "Radius1",
                "Radius2",
                "Diameter",
                "Depth",
                "Angle",
                "TaperAngle",
                "TaperAngle2",
                "StartOffset",
            ):
                if path not in obj.PropertiesList or obj.getTypeIdOfProperty(path) not in (
                    "App::PropertyLength",
                    "App::PropertyDistance",
                    "App::PropertyAngle",
                ):
                    continue
                value = getattr(obj, path)
                rows.append((obj, path, path, expr.get(path, value.UserString)))
    return rows


class ParameterEdit:
    def __init__(self, doc):
        features.ensure_calculator()
        self.doc = doc
        self.closed = False
        self.cells = {name: cell for name, _, cell in user_parameters(doc)}
        features.begin_transaction(self.doc, "Az: Change Parameters")

    def update(self, users, dimensions=()):
        names = [name for name, _ in users if name.strip()]
        if len(names) != len(set(names)):
            raise DesignError("Each parameter needs a unique name.")
        for name in names:
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
                raise DesignError(
                    "Use letters, numbers and underscores; start parameter names with a letter."
                )
        if names:
            sheet = self.doc.getObject("Parameters")
            if sheet is None:
                sheet = self.doc.addObject("Spreadsheet::Sheet", "Parameters")
                sheet.Label = "User Parameters"
            used_rows = [int(re.search(r"\d+$", c).group()) for c in sheet.getNonEmptyCells()]
            next_row = max(used_rows, default=1) + 1
            for name, value in users:
                if not name.strip():
                    continue
                if not value.strip():
                    raise DesignError("Enter a value for " + name + ".")
                cell = self.cells.get(name)
                if cell is None:
                    cell = "B" + str(next_row)
                    sheet.set("A" + str(next_row), name)
                    self.cells[name] = cell
                    next_row += 1
                sheet.set(cell, value)
                sheet.setAlias(cell, name)
            sheet.setColumnWidth("A", 150)
            sheet.setColumnWidth("B", 180)
        self.doc.recompute()
        for obj, path, expression in dimensions:
            if not expression.strip():
                raise DesignError("Enter a value or expression for " + obj.Label + "." + path)
            obj.setExpression(path, expression)
        self.doc.recompute()
        broken = [
            o.Label for o in self.doc.Objects if "Invalid" in o.State or getattr(o, "Error", "")
        ]
        if broken:
            raise DesignError("These parameters break: " + ", ".join(broken))

    def accept(self):
        self.doc.commitTransaction()
        self.closed = True

    def cancel(self):
        if not self.closed:
            self.doc.abortTransaction()
            self.doc.recompute()
            self.closed = True


def show():
    import FreeCADGui as Gui
    from .qt import QtCore, QtWidgets
    from .tasks import track, forget

    if not App.ActiveDocument:
        raise DesignError("Create or open a design first.")
    if Gui.Control.activeDialog():
        raise DesignError("Finish or cancel the current operation first.")
    doc = App.ActiveDocument

    class Task:
        def __init__(self):
            initial = user_parameters(doc)
            self.dimensions = model_dimensions(doc)
            self.edit = ParameterEdit(doc)
            self.form = QtWidgets.QWidget()
            self.form.setWindowTitle("Change Parameters")
            layout = QtWidgets.QVBoxLayout(self.form)
            note = QtWidgets.QLabel(
                "USER PARAMETERS\nUse names such as Width. In feature dimensions enter Parameters.Width. Spreadsheet formulas use =Width / 2."
            )
            note.setWordWrap(True)
            layout.addWidget(note)
            self.users = QtWidgets.QTableWidget(0, 2)
            self.users.setObjectName("AzUserParameters")
            self.users.setHorizontalHeaderLabels(["Name", "Value / formula"])
            self.users.horizontalHeader().setStretchLastSection(True)
            layout.addWidget(self.users)
            for name, value, _ in initial:
                self.add_user(name, value)
            button = QtWidgets.QPushButton("Add user parameter")
            button.clicked.connect(lambda *_: self.add_user())
            layout.addWidget(button)
            layout.addWidget(
                QtWidgets.QLabel("MODEL DIMENSIONS · native expressions update the model")
            )
            self.models = QtWidgets.QTableWidget(len(self.dimensions), 3)
            self.models.setObjectName("AzModelParameters")
            self.models.setHorizontalHeaderLabels(["Feature", "Dimension", "Value / expression"])
            self.models.horizontalHeader().setStretchLastSection(True)
            for row, (obj, path, label, expression) in enumerate(self.dimensions):
                for col, text in enumerate((obj.Label, label, expression)):
                    item = QtWidgets.QTableWidgetItem(text)
                    if col < 2:
                        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                    self.models.setItem(row, col, item)
            layout.addWidget(self.models)
            preview = QtWidgets.QPushButton("Update model")
            preview.clicked.connect(self.preview)
            layout.addWidget(preview)
            self.status = QtWidgets.QLabel(
                "Changes stay in one undo step. Cancel restores the original model."
            )
            self.status.setWordWrap(True)
            layout.addWidget(self.status)

        def add_user(self, name="", value=""):
            row = self.users.rowCount()
            self.users.insertRow(row)
            item = QtWidgets.QTableWidgetItem(name)
            if name:
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.users.setItem(row, 0, item)
            self.users.setItem(row, 1, QtWidgets.QTableWidgetItem(value))

        def preview(self):
            try:
                users = [
                    (self.users.item(r, 0).text().strip(), self.users.item(r, 1).text())
                    for r in range(self.users.rowCount())
                ]
                dimensions = [
                    (obj, path, self.models.item(r, 2).text())
                    for r, (obj, path, _, _) in enumerate(self.dimensions)
                ]
                self.edit.update(users, dimensions)
                for row in range(self.users.rowCount()):
                    item = self.users.item(row, 0)
                    if item.text().strip():
                        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.status.setText(
                    "Model updated. OK keeps these changes; Cancel restores the original."
                )
                self.status.setStyleSheet("color: #21734a")
                return True
            except Exception as exc:
                self.status.setText(str(exc))
                self.status.setStyleSheet("color: #ac422e")
                return False

        def accept(self):
            if not self.preview():
                return False
            self.edit.accept()
            forget(self)
            Gui.Control.closeDialog()
            return True

        def reject(self):
            self.edit.cancel()
            forget(self)
            Gui.Control.closeDialog()
            return True

        def getStandardButtons(self):
            return int(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

    task = Task()
    Gui.Control.showDialog(task)
    track(task)
    return task
