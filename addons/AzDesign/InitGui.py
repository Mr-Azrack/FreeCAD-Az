# SPDX-License-Identifier: LGPL-2.1-or-later
"""Register Az Design in FreeCAD's exec-based startup environment."""

import FreeCADGui as Gui
from azdesign.workbench import AzDesignWorkbench

Gui.addWorkbench(AzDesignWorkbench())
