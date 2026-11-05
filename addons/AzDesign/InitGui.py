# SPDX-License-Identifier: LGPL-2.1-or-later
"""Register the optional Az Design workbench; loading it changes no settings."""
import os
import sys
import FreeCADGui as Gui

_az_root = os.path.dirname(__file__)
if _az_root not in sys.path:
    sys.path.insert(0, _az_root)


class AzDesignWorkbench(Gui.Workbench):
    MenuText = "Az Design"
    ToolTip = "A familiar sketch-to-solid workspace for FreeCAD"
    Icon = os.path.join(_az_root, "Resources", "az.svg")

    def Initialize(self):
        import PartGui
        import PartDesignGui
        import SketcherGui
        from azdesign import commands

        commands.register()
        self.appendMenu("Az Design", commands.menu_commands())

    def Activated(self):
        from azdesign.session import start

        start()

    def Deactivated(self):
        from azdesign.session import stop

        stop()

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(AzDesignWorkbench())
