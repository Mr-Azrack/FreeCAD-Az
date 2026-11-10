#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Discover a packaged FreeCAD runtime and run native modeling tests headlessly.

Debian: /usr/bin/python3 addons/AzDesign/tests/run_workflow.py
Other builds: set FREECAD_LIB_DIR and run their matching Python interpreter.
"""

import os
import sys
import unittest
from pathlib import Path

addon = Path(__file__).resolve().parents[1]
libraries = (
    [Path(os.environ["FREECAD_LIB_DIR"])]
    if os.environ.get("FREECAD_LIB_DIR")
    else list(Path("/usr/lib").glob("freecad*/lib"))
)
sys.path[:0] = [str(addon)] + [str(p) for p in libraries]
for root in (Path("/usr/share/freecad/Mod"), Path("/usr/share/freecad-python3/Mod")):
    if root.is_dir():
        sys.path[:0] = [str(root)] + [str(p) for p in root.iterdir() if p.is_dir()]

import FreeCAD as App

if tuple(map(int, App.Version()[:2])) < (1, 0):
    raise RuntimeError("Az Design 0.2 requires FreeCAD 1.0 or newer.")
suite = unittest.defaultTestLoader.discover(str(addon / "tests"), pattern="test_workflow.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
