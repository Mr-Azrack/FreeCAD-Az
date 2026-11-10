# SPDX-License-Identifier: LGPL-2.1-or-later
"""Register Az Design in FreeCAD's exec-based startup environment."""

import FreeCADGui as Gui
from azdesign.workbench import AzDesignWorkbench

Gui.addWorkbench(AzDesignWorkbench())

# Register document routing early, without forcing a workspace at startup.
# Keep the Home screen until a new modeling document actually appears.
try:
    from azdesign.workspace_route import install as _install_design_routing
    _install_design_routing()
except ImportError:
    # Headless startup harnesses don't provide native FreeCAD/Qt.
    pass
