# SPDX-License-Identifier: LGPL-2.1-or-later
"""Register Az Design in FreeCAD's exec-based startup environment."""

import FreeCADGui as Gui
from azdesign.workbench import AzDesignWorkbench

Gui.addWorkbench(AzDesignWorkbench())

# Register document routing before FreeCAD opens requested files.
# On native ordinary launch, our own Design Home is the initial workbench.
# Explicit file arguments and non-native installs keep their original routing.
try:
    from azdesign.workspace_route import install as _install_design_routing
    _install_design_routing()
except ImportError:
    # Headless startup harnesses don't provide native FreeCAD/Qt.
    pass

# Native Start Menu launcher opts into Design Home. The Qt event loop may not
# be initialized at InitGui load time; schedule a delayed, guarded activation.
import os as _az_os
if _az_os.environ.get("AZ_DESIGN_NATIVE_HOME") == "1":
    try:
        from azdesign.qt import QtCore as _AzQtCore
        import FreeCAD as _az_App

        def _az_show_native_home():
            if _az_App.ActiveDocument is not None:
                return
            if Gui.Control.activeDialog():
                return
            current = Gui.activeWorkbench()
            if current and current.name() == "AzDesignWorkbench":
                return
            try:
                Gui.activateWorkbench("AzDesignWorkbench")
            except (RuntimeError, ValueError):
                _az_App.Console.PrintError("Unable to activate Design Home at startup.\\n")

        _AzQtCore.QTimer.singleShot(1200, _az_show_native_home)
    except ImportError:
        pass
