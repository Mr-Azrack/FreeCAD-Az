# SPDX-License-Identifier: LGPL-2.1-or-later
"""Build minimal overlay for an existing compiled Az Native Windows preview.

Use only the Qt platform plugin from the original bundle or its exact pinned
Pixi environment, not DLLs from any other installed FreeCAD.
"""

import argparse
import sys
import zipfile
from pathlib import Path

from package_portable import launcher
from qt_runtime import QtRuntimeError, install_qt_platform


def build_fixkit(root, output, env=None):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite fixkit: {output}")
    plugin = install_qt_platform(root, env, check_load=True)
    # Update the launcher in the staged preview. No user's program is changed
    # here: input is an extracted CI artifact under the runner's scratch area.
    (root / "Az Design.cmd").write_text(launcher(), encoding="utf-8", newline="\r\n")
    about = (
        "AZ DESIGN NATIVE - WINDOWS Qt PLATFORM FIX\n"
        "\n"
        "This fix is for the experimental Az Design Native 1.1 Windows x64\n"
        "PREVIEW, not for stock FreeCAD or the Python-only workbench.\n"
        "\n"
        "1. Close the broken Az Design application.\n"
        "2. Open your extracted AzDesign-Native-1.1-Windows-x64 directory.\n"
        "3. Extract this fix ZIP DIRECTLY INTO that directory, preserving\n"
        "   the 'bin' folder structure and replacing 'Az Design.cmd'.\n"
        "4. Launch the replaced 'Az Design.cmd'.\n"
        "\n"
        "Do not extract the fix into the bin subfolder or the stock FreeCAD\n"
        "installation. Your separate FreeCAD 1.1 remains unchanged.\n"
        "\n"
        "If Windows still reports a Qt platform error, open Command Prompt\n"
        "in the AzDesign-Native-1.1-Windows-x64 directory and run:\n"
        '  set QT_DEBUG_PLUGINS=1\n'
        '  "Az Design.cmd"\n'
        "Then send the reported missing DLL error to Riggs.\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ("Az Design.cmd", "bin/qt.conf", "bin/platforms/qwindows.dll"):
            file = root / name
            if not file.is_file():
                raise QtRuntimeError(f"Missing required repair file: {file}")
            archive.write(file, arcname=name)
        archive.writestr("QT-FIX-README.txt", about)
    with zipfile.ZipFile(output) as archive:
        error = archive.testzip()
        if error:
            raise QtRuntimeError(f"Fixkit archive CRC error in {error}")
    return output


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--environment", type=Path)
    args = ap.parse_args()
    try:
        print("Qt quick fix ready:", build_fixkit(args.bundle, args.output, args.environment))
        return 0
    except (OSError, QtRuntimeError) as exc:
        print("Qt quick fix failed:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
