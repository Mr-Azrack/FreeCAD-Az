#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Build the standalone installer ZIP without building the FreeCAD fork."""

import argparse
import ast
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def package(output=None):
    repo = Path(__file__).resolve().parents[1]
    addon = repo / "addons" / "AzDesign"
    version = ET.parse(addon / "package.xml").getroot().findtext("version")
    output = Path(output) if output else repo / "dist" / ("AzDesign-" + version + ".zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    required = [
        addon / "Init.py",
        addon / "InitGui.py",
        addon / "azdesign" / "workbench.py",
        addon / "azdesign" / "session.py",
        addon / "LICENSE",
    ]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)
    probe = addon / "Tools" / "Probe_Modeled_Thread.FCMacro"
    if not probe.is_file():
        raise FileNotFoundError(probe)
    ast.parse(probe.read_text(encoding="utf-8"), filename=str(probe))
    files = sorted(
        p
        for p in addon.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )
    for path in files:
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, "AzDesign/" + path.relative_to(addon).as_posix())
        archive.write(repo / "addons" / "Install_AzDesign.FCMacro", "Install_AzDesign.FCMacro")
        archive.write(probe, "Probe_Modeled_Thread.FCMacro")
        archive.write(addon / "README.md", "START_HERE.md")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(package(args.output))
