#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Portable packaging safety tests without needing Windows/FreeCAD binaries."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("package_portable.py")
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

    def test_never_packages_without_az_workbench(self):
        (self.addon / "InitGui.py").unlink()
        with self.assertRaisesRegex(m.PackageError, "complete"):
            self.call()
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
