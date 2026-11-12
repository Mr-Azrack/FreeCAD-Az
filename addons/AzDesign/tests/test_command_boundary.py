#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Guard the Design-facing command boundary without requiring FreeCAD."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "azdesign"
spec = importlib.util.spec_from_file_location("az_catalog_under_test", ROOT / "catalog.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def keys(groups):
    for _, entries in groups:
        for entry in entries:
            if isinstance(entry, tuple):
                yield from entry[1]
            else:
                yield entry


def main():
    for name, groups in (("Solid", module.SOLID),
                         ("Sketch", module.SKETCH),
                         ("Utilities", module.UTILITIES)):
        for key in keys(groups):
            tool = module.TOOLS[key]
            assert tool.command not in module.RAW_FEATURE_COMMANDS, (
                name, key, tool.command
            )
            assert tool.command.startswith("Az_") or (
                tool.command in module.ALLOWED_NATIVE_COMMANDS
            ), (name, key, tool.command)
    assert module.TOOLS["plane"].command == "Az_OffsetPlane"
    assert module.TOOLS["hole"].command == "Az_Hole"
    assert module.TOOLS["fillet"].command == "Az_Fillet"
    assert module.TOOLS["chamfer"].command == "Az_Chamfer"
    for key in ("revolve", "loft", "sweep", "shell", "polar", "measure"):
        assert module.TOOLS[key].command in module.RAW_FEATURE_COMMANDS
    for key, command in (
        ("move", "Az_Move"),
        ("mirror", "Az_Mirror"),
        ("pattern", "Az_LinearPattern"),
        ("labels", "Az_SketchLabels"),
    ):
        assert module.TOOLS[key].command == command
        assert command not in module.RAW_FEATURE_COMMANDS
    # FreeCAD 1.1 renamed the legacy Sketcher_External tool:
    # the old name left Project permanently grey and unusable.
    assert module.TOOLS["project"].command == "Sketcher_Projection"
    assert "Sketcher_Projection" in module.ALLOWED_NATIVE_COMMANDS
    assert {"Std_ViewZoomIn", "Std_ViewZoomOut"} <= module.ALLOWED_NATIVE_COMMANDS
    print("Design command boundary: PASS")


if __name__ == "__main__":
    main()
