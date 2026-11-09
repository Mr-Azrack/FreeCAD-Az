# SPDX-License-Identifier: LGPL-2.1-or-later
"""Repair/validate Windows Qt platform plugin inside a standalone Az bundle.

No DLL is ever imported from the user's system FreeCAD or from a different
runtime. Only the original pinned Pixi build or its existing bundle is used.
"""

import argparse
import ctypes
import shutil
import sys
from pathlib import Path


class QtRuntimeError(RuntimeError):
    pass


def candidate_paths(root: Path):
    """Known conda/Qt 6 layouts, restricted to this build's own directory."""
    return (
        root / "bin" / "platforms" / "qwindows.dll",
        root / "bin" / "plugins" / "platforms" / "qwindows.dll",
        root / "bin" / "qt6" / "plugins" / "platforms" / "qwindows.dll",
        root / "lib" / "qt6" / "plugins" / "platforms" / "qwindows.dll",
        root / "Library" / "plugins" / "platforms" / "qwindows.dll",
        root / "Library" / "lib" / "qt6" / "plugins" / "platforms" / "qwindows.dll",
    )


def install_qt_platform(bundle: Path, env: Path = None, check_load=False):
    """Stage the matching Qt Windows plugin in bin/platforms and verify it.

    env should be the very Pixi environment that compiled FreeCAD, never an
    arbitrary FreeCAD installer. If the DLL cannot be found, packaging fails.
    """
    bundle = Path(bundle).resolve()
    env = Path(env).resolve() if env else None
    exe = bundle / "bin" / "FreeCAD.exe"
    if not exe.is_file():
        raise QtRuntimeError("No compiled FreeCAD.exe found in portable bundle")
    sources = candidate_paths(bundle)
    if env:
        sources += candidate_paths(env)
    source = next((p for p in sources if p.is_file() and p.stat().st_size > 0), None)
    if source is None:
        raise QtRuntimeError(
            "qwindows.dll is missing from the compiled Pixi Qt runtime. "
            "Refusing to publish a Windows program that cannot initialize Qt."
        )

    destination = bundle / "bin" / "platforms" / "qwindows.dll"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source != destination:
        # Keep the whole platform directory, not only the Windows backend:
        # FreeCAD may use additional Qt integrations later.
        shutil.copytree(source.parent, destination.parent, dirs_exist_ok=True)
    if not destination.is_file() or destination.stat().st_size == 0:
        raise QtRuntimeError("Failed to stage Qt Windows platform plugin")

    # Qt looks up qt.conf next to the executable. FreeCAD-Bundle's older
    # qt6.conf is not a substitute for this runtime path configuration.
    (bundle / "bin" / "qt.conf").write_text(
        "[Paths]\nPrefix = .\nPlugins = .\n", encoding="utf-8"
    )
    if check_load and sys.platform == "win32":
        import os
        previous = os.environ.get("PATH", "")
        os.environ["PATH"] = str((bundle / "bin").resolve()) + os.pathsep + previous
        add = getattr(os, "add_dll_directory", None)
        handle = add(str((bundle / "bin").resolve())) if add else None
        try:
            ctypes.WinDLL(str(destination))
        except OSError as exc:
            raise QtRuntimeError(
                "qwindows.dll exists but cannot load its Qt DLL dependencies. "
                "Windows error: " + str(exc)
            ) from exc
        finally:
            if handle:
                handle.close()
            os.environ["PATH"] = previous
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--environment", type=Path)
    parser.add_argument("--check-load", action="store_true")
    args = parser.parse_args()
    try:
        result = install_qt_platform(args.bundle, args.environment, args.check_load)
    except QtRuntimeError as exc:
        print(f"Qt platform fix failed: {exc}", file=sys.stderr)
        return 1
    print(f"Qt platform plugin ready: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
