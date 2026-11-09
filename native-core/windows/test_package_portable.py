#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Portable packaging safety tests without needing Windows/FreeCAD binaries."""

import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path

MODULE = Path(__file__).with_name("package_portable.py")
sys.path.insert(0, str(MODULE.parent))
spec = importlib.util.spec_from_file_location("az_package_portable", MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PortablePackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.env = root / "env"
        self.addon = root / "AzDesign"
        self.upstream = root / "upstream"
        self.out = root / "out"
        self.patch = root / "snap.patch"
        for p in (self.env / "Library/bin", self.env / "Library/Mod/Sketcher", self.addon, self.upstream):
            p.mkdir(parents=True)
        (self.env / "Library/bin/FreeCAD.exe").write_bytes(b"dummy compiled FreeCAD")
        plugins = self.env / "Library" / "lib" / "qt6" / "plugins" / "platforms"
        plugins.mkdir(parents=True)
        (plugins / "qwindows.dll").write_bytes(b"matching Qt 6 platform plugin mock")
        (self.env / "Library/Mod/Sketcher/SketcherGui.pyd").write_bytes(b"dummy")
        (self.addon / "InitGui.py").write_text("# InitGui")
        (self.addon / "package.xml").write_text("<package/>")
        (self.upstream / "COPYING.LIB").write_text("LGPL notice")
        self.patch.write_text("diff --git test")

    def call(self):
        return m.package(self.env, self.addon, self.upstream, self.out, self.patch, "test-sha")

    def test_portable_bundle_is_isolated_with_real_native_layout(self):
        result = self.call()
        self.assertEqual(result["base"], "FreeCAD 1.1.0")
        self.assertTrue((self.out / "bin/FreeCAD.exe").is_file())
        self.assertTrue((self.out / "Mod/Sketcher/SketcherGui.pyd").is_file())
        self.assertTrue((self.out / "Mod/AzDesign/InitGui.py").is_file())
        self.assertTrue((self.out / "bin/platforms/qwindows.dll").is_file())
        self.assertIn("Plugins = .", (self.out / "bin/qt.conf").read_text())
        self.assertEqual(result["qt_windows_plugin"], "bin/platforms/qwindows.dll")
        self.assertEqual(len(result["qt_windows_plugin_sha256"]), 64)
        self.assertIn("QT_PLUGIN_PATH", (self.out / "Az Design.cmd").read_text())
        self.assertTrue((self.out / "licenses/COPYING.LIB").is_file())
        cmd = (self.out / "Az Design.cmd").read_text()
        self.assertIn("FREECAD_USER_HOME", cmd)
        self.assertIn("%LOCALAPPDATA%", cmd)
        self.assertIn("--user-cfg", cmd)
        self.assertIn("--system-cfg", cmd)
        self.assertNotIn("C:\\Program Files\\FreeCAD 1.1", cmd)
        self.assertEqual(json.loads((self.out / "AZ_NATIVE_BUILD.json").read_text()), result)

    def test_refuses_uncompiled_build_without_creating_result(self):
        (self.env / "Library/bin/FreeCAD.exe").unlink()
        with self.assertRaisesRegex(m.PackageError, "compiled"):
            self.call()
        self.assertFalse(self.out.exists())

    def test_never_overwrites_existing_portable_directory(self):
        self.out.mkdir()
        marker = self.out / "user_file.fcstd"
        marker.write_bytes(b"real work")
        with self.assertRaisesRegex(m.PackageError, "overwrite"):
            self.call()
        self.assertEqual(marker.read_bytes(), b"real work")

    def test_missing_windows_qt_platform_dll_refuses_to_publish(self):
        (self.env / "Library/lib/qt6/plugins/platforms/qwindows.dll").unlink()
        with self.assertRaisesRegex(m.PackageError, "qwindows.dll"):
            self.call()
        self.assertFalse(self.out.exists())

    def test_windows_plugin_can_come_from_standard_conda_plugin_directory(self):
        source = self.env / "Library/lib/qt6/plugins/platforms/qwindows.dll"
        target = self.env / "Library/plugins/platforms/qwindows.dll"
        target.parent.mkdir(parents=True)
        source.replace(target)
        self.call()
        self.assertEqual(
            (self.out / "bin/platforms/qwindows.dll").read_bytes(),
            b"matching Qt 6 platform plugin mock",
        )

    def test_never_packages_without_az_workbench(self):
        (self.addon / "InitGui.py").unlink()
        with self.assertRaisesRegex(m.PackageError, "complete"):
            self.call()
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
