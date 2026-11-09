# SPDX-License-Identifier: LGPL-2.1-or-later
"""Small native patch bundle tests: exact changed file set and path safety."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

module_file = Path(__file__).with_name("create_patch.py")
spec = importlib.util.spec_from_file_location("create_az_native_patch", module_file)
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)


class PatchCreationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.before = root / "before"
        self.after = root / "after"
        self.output = root / "output" / "update.azpatch"
        self.before.mkdir()
        self.after.mkdir()

    def write(self, root, path, data):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def test_delta_contains_changed_files_only_and_deletion_with_baseline(self):
        self.write(self.before, "bin/Core.dll", b"old")
        self.write(self.before, "Mod/AzDesign/ui.py", b"same")
        self.write(self.before, "Mod/AzDesign/retired.py", b"old")
        self.write(self.after, "bin/Core.dll", b"new")
        self.write(self.after, "Mod/AzDesign/ui.py", b"same")
        self.write(self.after, "Mod/AzDesign/new.py", b"added")
        manifest = patcher.make_patch(self.before, self.after, self.output, "0.5.2", "0.5.3")
        self.assertEqual(len(manifest["files"]), 2)
        self.assertEqual(len(manifest["delete"]), 1)
        self.assertEqual(manifest["delete"][0]["path"], "Mod/AzDesign/retired.py")
        with ZipFile(self.output) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {
                "patch.json", "files/bin/Core.dll", "files/Mod/AzDesign/new.py"
            })
            self.assertEqual(archive.read("files/bin/Core.dll"), b"new")
            self.assertEqual(json.loads(archive.read("patch.json"))["to_version"], "0.5.3")

    def test_refuses_overwrite_and_same_version(self):
        self.write(self.before, "a.txt", b"1")
        self.write(self.after, "a.txt", b"2")
        with self.assertRaises(ValueError):
            patcher.make_patch(self.before, self.after, self.output, "1", "1")
        patcher.make_patch(self.before, self.after, self.output, "1", "2")
        with self.assertRaises(FileExistsError):
            patcher.make_patch(self.before, self.after, self.output, "1", "3")

    def test_rejects_traversal_drive_paths_and_uninstaller(self):
        for path in ("../exfiltrate", "x/../../y", "C:/windows/system32", "/root", r"bin\evil", "unins000.exe"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                patcher.safe_rel(path)

    def test_does_not_patch_system_uninstaller_or_version_state(self):
        self.write(self.before, "unins000.exe", b"old")
        self.write(self.after, "unins000.exe", b"new")
        self.write(self.before, "Az Native Version.json", b'{"version":"1"}')
        self.write(self.after, "Az Native Version.json", b'{"version":"2"}')
        manifest = patcher.make_patch(self.before, self.after, self.output, "1", "2")
        self.assertEqual(manifest["files"], [])
        self.assertEqual(manifest["delete"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
