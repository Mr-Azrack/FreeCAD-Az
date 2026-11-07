# SPDX-License-Identifier: LGPL-2.1-or-later
"""Workbench definition in an imported module, independent of loader globals."""

import os
import FreeCADGui as Gui


class AzDesignWorkbench(Gui.Workbench):
    MenuText = "Az Design"
    ToolTip = "A familiar sketch-to-solid workspace for FreeCAD"
    # __file__ belongs to this normally imported module, not InitGui.py's
    # shared execution environment (where it can be absent or unrelated).
    Icon = os.path.join(os.path.dirname(__file__), "..", "Resources", "az.svg")

    def Initialize(self):
        import PartGui
        import PartDesignGui
        import SketcherGui
        from . import commands

        commands.register()
        self.appendMenu("Az Design", commands.menu_commands())

    def Activated(self):
        from .session import start

        start()

    def Deactivated(self):
        from .session import stop

        stop()

    def GetClassName(self):
        return "Gui::PythonWorkbench"
