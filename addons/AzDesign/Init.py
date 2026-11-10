# SPDX-License-Identifier: LGPL-2.1-or-later
"""Load the package after FreeCAD has added the workbench root to sys.path."""

# FreeCAD executes this entry script without defining __file__. A normal package
# import has its own module namespace and supports restoring saved Az proxies.
import azdesign
