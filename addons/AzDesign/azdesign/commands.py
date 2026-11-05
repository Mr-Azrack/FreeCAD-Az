# SPDX-License-Identifier: LGPL-2.1-or-later
"""Small command adapters; the ribbon and palette share these entry points."""
import os
import traceback
import FreeCAD as App
import FreeCADGui as Gui
from . import modeling
from .catalog import TOOLS
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
    try:
        if command not in Gui.listCommands():
            notify(
                "This tool is not available in your FreeCAD version. Use Find a Tool for alternatives.",
                True,
            )
            return False
        Gui.runCommand(command, 0)
        return True
    except modeling.ModelingError as exc:
        notify(str(exc), True)
    except Exception:
        App.Console.PrintError("Az Design command failed:\n" + traceback.format_exc())
        notify("The operation could not start. See View → Panels → Report view for details.", True)
    return False


def home():
    if Gui.activeDocument():
        view = Gui.activeDocument().activeView()
        view.viewAxonometric()
        view.fitAll()


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


def help_dialog():
    text = """<h2>Az Design · Quick start</h2>
    <p><b>1.</b> Create Sketch → choose XY, XZ, YZ or a flat face.<br>
    <b>2.</b> Draw and dimension a closed profile.<br>
    <b>3.</b> Finish Sketch → Extrude → distance → OK.</p>
    <p>Select a solid face and create another sketch to make a Cut.</p>
    <p><b>Solid shortcuts:</b> E/Q Extrude · F Fillet · H Hole · M Move · S Find a Tool.<br>
    <b>Sketch shortcuts:</b> L Line · R Rectangle · C Circle · D Distance ·
    T Trim · P Project · X Construction · S Find a Tool.</p>
    <p><b>Mouse:</b> Middle button pans; Shift + middle button orbits.
    Scroll to zoom. These controls apply only in Az Design.</p>
    <p><b>History:</b> Click to select; double-click to edit a feature.
    The strip shows creation order and does not roll the model backward.</p>
    <p><b>Native tools:</b> Fillet, Shell, Revolve and other advanced tools use
    FreeCAD's task dialogs. The Tasks panel is on the right.</p>
    <p><b>Return:</b> Utilities → Native CAD restores your previous layout.
    This is an independent interface, not an Autodesk product.</p>"""
    QtWidgets.QMessageBox.information(Gui.getMainWindow(), "Az Design 0.1", text)


class Command:
    def __init__(self, tool, function, needs_document=False):
        self.tool = tool
        self.function = function
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
            self.function()
        except modeling.ModelingError as exc:
            notify(str(exc), True)
        except Exception:
            App.Console.PrintError("Az Design:\n" + traceback.format_exc())
            notify("The operation could not start. See the Report view for details.", True)


def register():
    global _registered
    if _registered:
        return
    adapters = {
        "sketch": modeling.create_sketch,
        "extrude": modeling.start_extrude,
        "cut": lambda: modeling.start_extrude(cut=True),
        "finish": modeling.finish_sketch,
        "body": modeling.new_body,
        "home": home,
        "palette": palette,
        "help": help_dialog,
        "native": native,
        "cam": manufacture,
    }
    for key, function in adapters.items():
        Gui.addCommand(TOOLS[key].command, Command(TOOLS[key], function))
    _registered = True


def menu_commands():
    return [
        TOOLS[key].command
        for key in (
            "sketch",
            "finish",
            "extrude",
            "cut",
            "body",
            "home",
            "palette",
            "help",
            "cam",
            "native",
        )
    ]
