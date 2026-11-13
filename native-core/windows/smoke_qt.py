# SPDX-License-Identifier: LGPL-2.1-or-later
"""Real Qt Windows platform startup probe for compiled portable FreeCAD.

Run using the Python interpreter shipped with this SAME portable bundle.
This tests QPA "windows" plugin initialization, not just DLL presence.
"""

import argparse
import os
import sys
from pathlib import Path


def smoke(root):
    root = Path(root).resolve()
    bin_dir = root / "bin"
    qwindows = bin_dir / "platforms" / "qwindows.dll"
    if not qwindows.is_file():
        raise RuntimeError(f"Qt Windows platform plugin is missing: {qwindows}")
    os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
    os.environ["QT_PLUGIN_PATH"] = str(bin_dir)
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(bin_dir / "platforms")
    os.environ["PYTHONNOUSERSITE"] = "1"
    # Do not set QT_QPA_PLATFORM=offscreen: test the actual Windows plugin.
    os.environ["QT_QPA_PLATFORM"] = "windows"
    if sys.platform != "win32":
        raise RuntimeError("This GUI smoke test only runs on Windows")
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    platform = app.platformName().lower()
    print("Az Qt portable platform:", platform)
    if platform != "windows":
        raise RuntimeError(f"Expected native Qt platform 'windows', received {platform}")
    # Exercise the actual Design Home Qt widget without creating a FreeCAD
    # document. A fresh native Start Menu launch must construct this view.
    from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget
    sys.path.insert(0, str(root / "Mod" / "AzDesign"))
    from azdesign.home import DesignHome

    ribbon = QWidget()
    ribbon.setLayout(QVBoxLayout())
    home = DesignHome(ribbon)
    ribbon.layout().addWidget(home)
    ribbon.show()
    app.processEvents()
    buttons = {button.text() for button in home.findChildren(QPushButton)}
    if not {"New Design", "Open File"}.issubset(buttons):
        raise RuntimeError("Native Design Home is missing New/Open actions")
    if home.width() <= 0 or home.height() <= 0:
        raise RuntimeError("Native Design Home has invalid geometry")
    home.close()
    ribbon.close()
    print("PASS: native Design Home widget constructed and actions visible")
    app.quit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True, type=Path)
    args = ap.parse_args()
    smoke(args.bundle)
