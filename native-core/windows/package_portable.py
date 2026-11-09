#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Assemble an unsigned Az Native Windows preview from compiled Pixi FreeCAD.

Side-by-side bundle compatible with the upstream conda Windows bundle layout.
No copies of installed FreeCAD or modifications to the owner's configuration.
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

from qt_runtime import QtRuntimeError, install_qt_platform


class PackageError(RuntimeError):
    pass


def copy_dir(source: Path, target: Path, required=False):
    if not source.is_dir():
        if required:
            raise PackageError(f"Required compiled directory missing: {source}")
        return False
    shutil.copytree(
        source, target, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    return True


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def launcher():
    return r'''@echo off
setlocal
rem Experimental standalone Az Design Native. NEVER modify installed FreeCAD.
rem Store a separate profile in LocalAppData, not in the unpacked application.
set "AZ_PROFILE=%LOCALAPPDATA%\AzDesign\Native-1.1"
if not exist "%AZ_PROFILE%" mkdir "%AZ_PROFILE%"
if not exist "%AZ_PROFILE%\Data" mkdir "%AZ_PROFILE%\Data"
set "FREECAD_USER_HOME=%AZ_PROFILE%"
set "FREECAD_USER_DATA=%AZ_PROFILE%\Data"
set "PATH=%~dp0bin;%PATH%"
set "QT_PLUGIN_PATH=%~dp0bin"
set "QT_QPA_PLATFORM_PLUGIN_PATH=%~dp0bin\platforms"
"%~dp0bin\FreeCAD.exe" --user-cfg "%AZ_PROFILE%\user.cfg" --system-cfg "%AZ_PROFILE%\system.cfg" %*
endlocal
'''


def package(env: Path, addon: Path, source: Path, out: Path, patch: Path, commit: str):
    env = env.resolve()
    addon = addon.resolve()
    source = source.resolve()
    out = out.resolve()
    patch = patch.resolve()
    if out.exists():
        raise PackageError(f"Refusing to overwrite existing destination: {out}")
    lib = env / "Library"
    binary = lib / "bin" / "FreeCAD.exe"
    sketcher = lib / "Mod" / "Sketcher"
    if not binary.is_file() or not sketcher.is_dir():
        raise PackageError("A compiled and installed Windows FreeCAD GUI with Sketcher is required")
    if not (addon / "InitGui.py").is_file() or not (addon / "package.xml").is_file():
        raise PackageError("AzDesign must be a complete installable workbench")
    if not patch.is_file():
        raise PackageError("Verified native source patch is required")
    out.mkdir(parents=True)
    try:
        # As upstream FreeCAD-Bundle does, place runtime DLLs next to the GUI,
        # plugins under bin, Python stdlib under bin/Lib and Mod at app root.
        copy_dir(lib / "bin", out / "bin", required=True)
        copy_dir(lib / "Mod", out / "Mod", required=True)
        for name in ("data", "Ext", "lib", "doc"):
            copy_dir(lib / name, out / name)
        for name in ("plugins", "mingw-w64", "resources", "translations"):
            if name == "plugins":
                copy_dir(lib / name, out / "bin")
            elif name == "mingw-w64":
                copy_dir(lib / name / "bin", out / "bin")
            else:
                copy_dir(lib / name, out / name)
        for name in ("DLLs", "Lib", "Scripts"):
            copy_dir(env / name, out / "bin" / name)
        for name in ("python.exe", "pythonw.exe"):
            if (env / name).is_file():
                shutil.copy2(env / name, out / "bin" / name)
        for pattern in ("python*.dll", "vcruntime*.dll", "msvcp*.dll", "ucrt*.dll"):
            for src in env.glob(pattern):
                shutil.copy2(src, out / "bin" / src.name)
        if (out / "Mod" / "AzDesign").exists():
            raise PackageError("AzDesign unexpectedly already installed in FreeCAD Mod")
        copy_dir(addon, out / "Mod" / "AzDesign", required=True)
        for name in ("COPYING", "COPYING.LIB", "LICENSE"):
            if (source / name).is_file():
                (out / "licenses").mkdir(exist_ok=True)
                shutil.copy2(source / name, out / "licenses" / name)
        # Verify the actual Windows Qt plugin before publishing any bundle.
        # Earlier previews copied an incomplete platform-plugin directory
        # and passed CI despite failing to create a Qt window on Windows.
        try:
            qt_plugin = install_qt_platform(out, env, check_load=True)
        except QtRuntimeError as exc:
            raise PackageError(str(exc)) from exc
        (out / "Az Design.cmd").write_text(launcher(), encoding="utf-8", newline="\r\n")
        (out / "README-FIRST.txt").write_text(
            "AZ DESIGN NATIVE - EXPERIMENTAL WINDOWS PREVIEW\n\n"
            "Unpack to a separate folder (never C:\\Program Files\\FreeCAD 1.1).\n"
            "Double-click 'Az Design.cmd' to launch.\n"
            "The preview uses its own profile under %LOCALAPPDATA%\\AzDesign\\Native-1.1.\n"
            "This is unsigned experimental software. Do not use as a production CAM post-processor.\n"
            "Based on FreeCAD 1.1.0; FreeCAD and dependencies retain their licences.\n"
            "Circle rim to center native snap is opt-in. Open FreeCAD Python console:\n"
            "  import FreeCAD as App\n"
            "  App.ParamGet('User parameter:BaseApp/Preferences/Mod/Sketcher/Snap').SetBool('AzSnapCircleCenter', True)\n"
            "Hold Alt while clicking a circle rim to preserve point-on-circle behavior.\n"
            "Please verify geometry and save document backups before machining.\n",
            encoding="utf-8",
        )
        manifest = {
            "product": "Az Design Native",
            "base": "FreeCAD 1.1.0",
            "architecture": "Windows x64",
            "status": "experimental unsigned portable preview",
            "core_patch_sha256": sha256(patch),
            "az_repository_commit": commit,
            "freecad_executable_sha256": sha256(out / "bin" / "FreeCAD.exe"),
            "included_workbench": "Mod/AzDesign",
            "native_snap_preference": "User parameter:BaseApp/Preferences/Mod/Sketcher/Snap/AzSnapCircleCenter",
            "compiled_native_snap": "patch applied at source checkout; Windows GUI acceptance required",
            "qt_windows_plugin": str(qt_plugin.relative_to(out)).replace("\\", "/"),
            "qt_windows_plugin_sha256": sha256(qt_plugin),
        }
        (out / "AZ_NATIVE_BUILD.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if not (out / "Mod" / "Sketcher").is_dir() or not (out / "Mod" / "AzDesign" / "InitGui.py").is_file():
            raise PackageError("Portable bundle omitted Sketcher or Az Design")
        return manifest
    except Exception:
        # This was freshly created; never remove an existing user folder.
        shutil.rmtree(out)
        raise


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--environment", type=Path, required=True)
    p.add_argument("--addon", type=Path, required=True)
    p.add_argument("--freecad-source", type=Path, required=True)
    p.add_argument("--patch", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--commit", default="unknown")
    a = p.parse_args()
    try:
        result = package(a.environment, a.addon, a.freecad_source, a.output, a.patch, a.commit)
    except PackageError as exc:
        print(f"Az Native package not created: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
