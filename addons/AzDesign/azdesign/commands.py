# SPDX-License-Identifier: LGPL-2.1-or-later
"""Small command adapters; the ribbon and palette share these entry points."""

import os
import traceback
import FreeCAD as App
import FreeCADGui as Gui
from . import modeling
from .features import DesignError
from .catalog import TOOLS, RAW_FEATURE_COMMANDS, ALLOWED_NATIVE_COMMANDS
from .qt import QtWidgets

_registered = False


def notify(message, error=False):
    Gui.getMainWindow().statusBar().showMessage(message, 14000)
    if error:
        App.Console.PrintWarning("Az Design: " + message + "\n")
    from .session import current

    session = current()
    if session:
        session.ribbon.hint.setText(message)


def invoke(command):
    # No accidental raw PartDesign task surfaces from the Design UI.
    # Native geometry and Sketcher canvas controls remain intentional.
    if command in RAW_FEATURE_COMMANDS:
        notify(
            "This advanced feature still uses FreeCAD's original task editor. "
            "Use Utilities → Native CAD explicitly until its Design editor is ready.",
            True,
        )
        return False
    if not command.startswith("Az_") and command not in ALLOWED_NATIVE_COMMANDS:
        notify("Unreviewed native command blocked in Design: " + command, True)
        return False
    try:
        if command == "Std_ViewFitAll":
            from .session import current

            session = current()
            if session and modeling.current_document():
                session.appearance.fit(Gui.activeDocument().activeView().fitAll)
                return True
        if command not in Gui.listCommands():
            notify(
                "This tool is not available in your FreeCAD version. Use Find a Tool for alternatives.",
                True,
            )
            return False
        Gui.runCommand(command, 0)
        return True
    except (modeling.ModelingError, DesignError) as exc:
        notify(str(exc), True)
    except Exception:
        App.Console.PrintError("Az Design command failed:\n" + traceback.format_exc())
        notify("The operation could not start. See View → Panels → Report view for details.", True)
    return False


def home():
    """Home frames the working solid, not every object in the document.

    A sketch/extra Body far from the active solid can make native Fit All
    compress the useful model into a tiny band. Fit the active visible Body
    using FreeCAD's native selection framing, preserving the user selection.
    """
    if not Gui.activeDocument():
        return
    view = Gui.activeDocument().activeView()
    if not view:
        return
    view.viewAxonometric()
    doc = modeling.current_document()
    body = modeling.active_body() if doc else None
    if body and (not body.ViewObject.Visibility or
                 not hasattr(body, "Shape") or body.Shape.isNull()):
        body = None
    if body is None:
        bodies = [obj for obj in doc.Objects
                  if obj.isDerivedFrom("PartDesign::Body")
                  and obj.ViewObject.Visibility
                  and not obj.Shape.isNull()] if doc else []
        if bodies:
            # Multiple visible solids are common after trial operations.
            # With no active Body, frame the most substantial solid instead
            # of letting faraway Bodies turn Home into a narrow strip.
            body = max(bodies, key=lambda obj: obj.Shape.Volume)
    if body is None:
        invoke("Std_ViewFitAll")
        return
    selected = [(item.Object, tuple(item.SubElementNames))
                for item in Gui.Selection.getSelectionEx()]
    def fit_body():
        try:
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(body)
            # The Python binding returns None even after a successful view
            # message; do not interpret that as a failed fit.
            Gui.SendMsgToActiveView("ViewSelection")
        finally:
            Gui.Selection.clearSelection()
            for obj, names in selected:
                if names:
                    for name in names:
                        Gui.Selection.addSelection(obj, name)
                else:
                    Gui.Selection.addSelection(obj)
    from .session import current
    session = current()
    try:
        if session:
            session.appearance.fit(fit_body)
        else:
            fit_body()
    except Exception:
        App.Console.PrintWarning("Az Design: body framing failed; using Fit All.\n")
        invoke("Std_ViewFitAll")


def native():
    Gui.activateWorkbench("PartDesignWorkbench")


def manufacture():
    available = Gui.listWorkbenches()
    for name in ("CAMWorkbench", "PathWorkbench"):
        if name in available:
            Gui.activateWorkbench(name)
            return
    raise modeling.ModelingError("The CAM workbench is not installed in this FreeCAD build.")


def palette():
    from .ui import CommandPalette

    dialog = CommandPalette(Gui.getMainWindow())
    # Keep a Python reference while Qt owns the nonmodal dialog.
    Gui.getMainWindow()._az_palette = dialog
    dialog.show()
    dialog.search.setFocus()


_update_running = False


def update_az_design():
    """Launch the native Windows updater for installed Design; otherwise add-on updater."""
    from pathlib import Path
    import subprocess
    from . import modeling
    # Full native install root: <root>/Mod/AzDesign/azdesign/commands.py.
    root = Path(__file__).resolve().parents[3]
    native_updater = root / "AzUpdater.exe"
    native_marker = root / "AZ Native Version.json"
    native_binary = root / "bin" / "FreeCAD.exe"
    if native_updater.is_file() and native_marker.is_file() and native_binary.is_file():
        if Gui.Control.activeDialog() or modeling.in_sketch():
            notify("Finish or cancel the current task before checking for native updates.", True)
            return
        try:
            subprocess.Popen([str(native_updater)], cwd=str(root))
            notify("Windows updater opened. Save your model and close Design before applying a patch.")
        except OSError as exc:
            notify("Could not launch Windows updater: " + str(exc), True)
        return
    global _update_running
    if _update_running:
        notify("Az Design update already running.")
        return
    from . import updater
    parent = Gui.getMainWindow()
    installation = os.path.join(App.getUserAppDataDir(), "Mod", "AzDesign")
    if Gui.Control.activeDialog():
        notify("Finish or cancel the current task before updating Az Design.", True)
        return
    _update_running = True
    progress = None
    try:
        old, new, sha, link = updater.available_update(installation)
        if updater._version_number(new) <= updater._version_number(old):
            QtWidgets.QMessageBox.information(
                parent, "Az Design is current",
                "You already have Az Design " + old
                + ".\\nThe latest CI-tested build is " + new + ".",
            )
            return
        answer = QtWidgets.QMessageBox.question(
            parent, "Update Az Design",
            "Installed: " + old + "\\n"
            "Available, CI-tested: " + new + "\\n\\n"
            "Download verified files directly from our public GitHub repo "
            "and replace Az Design?\\n\\n"
            "The current installation will be backed up. "
            "Your documents will not be modified.\\n\\n"
            "You MUST close and restart FreeCAD when finished. "
            "Save open work before restarting.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return
        progress = QtWidgets.QProgressDialog(
            "Downloading verified Az Design files…", "Cancel", 0, 100, parent
        )
        progress.setWindowTitle("Updating Az Design")
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def advance(done, total, file_name):
            progress.setRange(0, total)
            progress.setValue(done)
            progress.setLabelText(
                "Verified " + str(done) + " / " + str(total) + " files\\n"
                + file_name
            )
            QtWidgets.QApplication.processEvents()
            if progress.wasCanceled():
                raise updater.UpdateError(
                    "Update cancelled before installation. The current version is unchanged."
                )

        previous, installed, backup = updater.install_revision(
            installation, sha, new, progress=advance
        )
        progress.setValue(progress.maximum())
        message = (
            "Installed Az Design " + installed + ".\\n\\n"
            "Close ALL FreeCAD windows and restart the application before "
            "using the updated workbench."
        )
        if backup:
            message += "\\n\\nBackup of previous version: " + str(backup)
        QtWidgets.QMessageBox.information(
            parent, "Az Design update installed", message
        )
    except Exception as exc:
        App.Console.PrintError(
            "Az Design update failed:\\n" + traceback.format_exc()
        )
        QtWidgets.QMessageBox.warning(
            parent, "Az Design update not installed",
            str(exc) + "\\n\\nThe existing installation was left in place "
            "unless the installer itself reports a rollback failure.",
        )
    finally:
        if progress:
            progress.close()
        _update_running = False


def help_dialog():
    from pathlib import Path
    import json
    title = "Design · Quick Start"
    root = Path(__file__).resolve().parents[3]
    marker = root / "AZ Native Version.json"
    if marker.is_file():
        try:
            state = json.loads(marker.read_text(encoding="utf-8-sig"))
            if state.get("product") == "AzDesignNative":
                title = "Design " + str(state["version"]) + " · Quick Start"
        except (ValueError, KeyError, OSError):
            pass
    text = """<h2>Design · Quick start</h2>
    <p><b>1.</b> Create Sketch → choose XY, XZ, YZ or a flat face.<br>
    <b>2.</b> Draw or choose Sized Rectangle (exact native width/height), then finish the sketch.<br>
    <b>3.</b> Finish Sketch → Extrude → distance → OK.</p>
    <p>Select a solid face and create another sketch to make a Cut.</p>
    <p><b>Solid shortcuts:</b> E Extrude · Q Press/Pull · F Fillet · H Hole · S Find a Tool.<br>
    <b>Sketch shortcuts:</b> L Line · R Rectangle · C Circle · D Smart Dimension ·
    T Trim · P Project · X Construction · S Find a Tool.</p>
    <p><b>Mouse:</b> Middle button pans; Shift + middle button orbits.
    Scroll to zoom. These controls apply only in Design.</p>
    <p><b>History:</b> Click to select; double-click to edit a feature.
    Right-click a solid feature to roll back, insert a feature, suppress or resume history.</p>
    <p><b>Extrude:</b> Select shaded sketch regions, type or drag the distance,
    then choose Auto, Join, Cut, Intersect or New body. Use two sides, taper,
    Through All or To Face when needed. Negative distances reverse direction.</p>
    <p><b>Parameters:</b> Utilities → Parameters edits native feature dimensions
    and user parameters. Use expressions such as Parameters.Width / 2.</p>
    <p><b>Hole:</b> Design creates native, editable holes. Threads use cosmetic
    specifications; real helical threads are available only with experimental consent and crash logs.</p>
    <p><b>Advanced tools:</b> Revolve, Shell and other features without integrated
    Design editors remain available only by explicitly switching to Native CAD.</p>
    <p><b>Return:</b> Utilities → Native CAD restores your previous layout.
    This is an independent interface, not an Autodesk product.</p>"""
    QtWidgets.QMessageBox.information(Gui.getMainWindow(), title, text)


def dispatch(key):
    # Resolve functions at invocation time so developer reloads do not leave
    # registered FreeCAD commands holding stale modeling implementations.
    from . import tasks, presspull, parameters, history, hole

    adapters = {
        "sketch": modeling.create_sketch,
        "extrude": tasks.show_extrude,
        "cut": lambda: tasks.show_extrude(cut=True),
        "presspull": presspull.start,
        "hole": hole.show_hole,
        "fillet": lambda: __import__(
            "azdesign.edge_treatments_canvas", fromlist=["show"]
        ).show("Fillet"),
        "chamfer": lambda: __import__(
            "azdesign.edge_treatments_canvas", fromlist=["show"]
        ).show("Chamfer"),
        "snaps": lambda: __import__(
            "azdesign.snap_finder_ui", fromlist=["show"]
        ).show(),
        "parameters": parameters.show,
        "resume": history.resume_all,
        "dimension": smart_dimension,
        "labels": toggle_sketch_labels,
        "sketchpattern": lambda: __import__(
            "azdesign.sketch_pattern_ui", fromlist=["show"]
        ).show(),
        "sizedrect": lambda: __import__(
            "azdesign.sketch_rectangle", fromlist=["prompt_sized_rectangle"]
        ).prompt_sized_rectangle(),
        "finish": finish_sketch_command,
        "body": modeling.new_body,
        "plane": lambda: __import__(
            "azdesign.offset_plane", fromlist=["show"]
        ).show(),
        "move": lambda: __import__(
            "azdesign.move_body", fromlist=["show"]
        ).show(),
        "mirror": lambda: __import__(
            "azdesign.feature_transform", fromlist=["show"]
        ).show("mirror"),
        "pattern": lambda: __import__(
            "azdesign.solid_pattern", fromlist=["show"]
        ).show(),
        "home": home,
        "palette": palette,
        "help": help_dialog,
        "native": native,
        "cam": manufacture,
        "update": update_az_design,
    }
    return adapters[key]()


def finish_sketch_command():
    """Exit sketch edit and, for face-originated holes, open Hole settings."""
    sketch = modeling.finish_sketch()
    from .hole import finish_face_hole
    finish_face_hole(sketch)
    return sketch


def toggle_sketch_labels():
    if not modeling.in_sketch():
        raise modeling.ModelingError("Edit a sketch to show or hide its constraint labels.")
    command = "Sketcher_SwitchVirtualSpace"
    if command not in Gui.listCommands():
        raise modeling.ModelingError("This FreeCAD build does not expose Sketcher label visibility.")
    # Do not accidentally move only the selected constraints to the other
    # virtual space; clear the selection to toggle the complete view.
    Gui.Selection.clearSelection()
    Gui.runCommand(command, 0)
    notify("Sketch constraint label visibility toggled. Dimensions and solver unchanged.")


def smart_dimension():
    if not modeling.in_sketch():
        raise modeling.ModelingError("Edit a sketch to add dimensions.")
    if "Sketcher_Dimension" not in Gui.listCommands():
        raise modeling.ModelingError(
            "Smart Dimension requires FreeCAD 1.0 or newer. Choose a specific dimension from Constraints."
        )
    Gui.runCommand("Sketcher_Dimension", 0)


class Command:
    def __init__(self, key, needs_document=False):
        self.key = key
        self.tool = TOOLS[key]
        self.needs_document = needs_document

    def GetResources(self):
        return {
            "MenuText": self.tool.label,
            "ToolTip": self.tool.tip,
            "Pixmap": os.path.join(os.path.dirname(__file__), "..", "Resources", "az.svg"),
        }

    def IsActive(self):
        return not self.needs_document or App.ActiveDocument is not None

    def Activated(self):
        try:
            dispatch(self.key)
        except (modeling.ModelingError, DesignError) as exc:
            notify(str(exc), True)
        except Exception:
            App.Console.PrintError("Az Design:\n" + traceback.format_exc())
            notify("The operation could not start. See the Report view for details.", True)


def register():
    global _registered
    from .features import ensure_calculator

    ensure_calculator()
    if _registered:
        return
    for key, tool in TOOLS.items():
        if tool.command.startswith("Az_"):
            Gui.addCommand(tool.command, Command(key))
    _registered = True


def menu_commands():
    return [
        TOOLS[key].command
        for key in (
            "sketch",
            "finish",
            "extrude",
            "cut",
            "presspull",
            "hole",
            "fillet",
            "chamfer",
            "snaps",
            "parameters",
            "resume",
            "dimension",
            "labels",
            "sketchpattern",
            "sizedrect",
            "body",
            "plane",
            "move",
            "mirror",
            "pattern",
            "home",
            "palette",
            "help",
            "update",
            "cam",
            "native",
        )
    ]
