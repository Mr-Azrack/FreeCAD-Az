# SPDX-License-Identifier: LGPL-2.1-or-later
"""Installer regressions: preserve old copies and recover from failed updates."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

module_path = Path(__file__).resolve().parents[1] / "azdesign" / "install.py"
spec = importlib.util.spec_from_file_location("az_installer", module_path)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        (self.source / "azdesign").mkdir(parents=True)
        (self.source / "InitGui.py").write_text("new version", encoding="utf-8")
        (self.source / "azdesign" / "session.py").write_text("new session", encoding="utf-8")
        self.mod = self.root / "FreeCAD" / "Mod"

    def tearDown(self):
        self.temp.cleanup()

    def test_first_install_and_update_preserve_previous_version(self):
        target, backup = installer.install(self.source, self.mod)
        self.assertIsNone(backup)
        (target / "local_notes.txt").write_text("keep my notes", encoding="utf-8")
        (self.source / "InitGui.py").write_text("updated version", encoding="utf-8")
        installed, backup = installer.install(self.source, self.mod)
        self.assertEqual(installed, target)
        self.assertEqual((backup / "local_notes.txt").read_text(), "keep my notes")
        self.assertEqual((backup / "InitGui.py").read_text(), "new version")
        self.assertEqual((target / "InitGui.py").read_text(), "updated version")
        self.assertFalse(backup.is_relative_to(self.mod))

    def test_failed_replacement_restores_previous_installation(self):
        target, _ = installer.install(self.source, self.mod)
        (target / "local_notes.txt").write_text("preserve", encoding="utf-8")
        original_replace = installer.os.replace

        def fail_new_copy(source, destination):
            if Path(source).parent.name.startswith(".az-install-"):
                raise OSError("simulated replacement failure")
            return original_replace(source, destination)

        with patch.object(installer.os, "replace", side_effect=fail_new_copy):
            with self.assertRaisesRegex(OSError, "simulated"):
                installer.install(self.source, self.mod)
        self.assertEqual((target / "local_notes.txt").read_text(), "preserve")
        self.assertFalse(list(self.mod.glob(".az-install-*")))

    def test_invalid_source_does_not_touch_existing_installation(self):
        target, _ = installer.install(self.source, self.mod)
        (self.source / "InitGui.py").unlink()
        with self.assertRaises(ValueError):
            installer.install(self.source, self.mod)
        self.assertEqual((target / "InitGui.py").read_text(), "new version")

    def test_installing_from_installed_folder_is_rejected(self):
        target, _ = installer.install(self.source, self.mod)
        with self.assertRaises(ValueError):
            installer.install(target, self.mod)
        self.assertEqual((target / "InitGui.py").read_text(), "new version")


if __name__ == "__main__":
    unittest.main()
