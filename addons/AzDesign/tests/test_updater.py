# SPDX-License-Identifier: LGPL-2.1-or-later
"""Offline regressions for a verified, backed-up public GitHub updater."""

import hashlib
from pathlib import Path
import tempfile
import unittest
import sys

ADDON = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON))
from azdesign import updater


class FakeGithub:
    commit = "a" * 40
    tree_sha = "b" * 40

    def __init__(self, version="0.3.7"):
        self.files = {
            "package.xml": (
                "<package><version>" + version + "</version></package>"
            ).encode(),
            "InitGui.py": b"# new version\n",
            "azdesign/install.py": b"# backup-aware installer source\n",
            "azdesign/session.py": b"# new session\n",
            "azdesign/updater.py": b"# next updater\n",
        }
        self.downloads = []

    @staticmethod
    def sha(data):
        return hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data
        ).hexdigest()

    def json(self, url):
        if "actions/workflows" in url:
            return {"workflow_runs": [{
                "head_sha": self.commit,
                "head_branch": updater.BRANCH,
                "event": "pull_request",
                "conclusion": "success",
                "status": "completed",
                "html_url": "https://github.com/example/actions/runs/1",
            }]}
        if "/contents/addons?" in url:
            return [{"name": "AzDesign", "type": "dir", "sha": self.tree_sha}]
        if "/git/trees/" in url:
            return {
                "truncated": False,
                "tree": [
                    {"path": key, "type": "blob", "mode": "100644",
                     "size": len(data), "sha": self.sha(data)}
                    for key, data in self.files.items()
                ]
            }
        raise AssertionError("Unexpected GitHub API path: " + url)

    def bytes(self, url):
        self.downloads.append(url)
        prefix = updater.RAW + "/" + self.commit + "/addons/AzDesign/"
        if not url.startswith(prefix):
            raise AssertionError("Unpinned or incorrect GitHub source URL")
        name = url[len(prefix):]
        return self.files[name]


class UpdaterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.install = self.root / "Mod" / "AzDesign"
        (self.install / "azdesign").mkdir(parents=True)
        (self.install / "package.xml").write_text(
            "<package><version>0.3.6</version></package>", encoding="utf-8"
        )
        (self.install / "InitGui.py").write_text("old version")
        (self.install / "azdesign" / "session.py").write_text("old session")

    def tearDown(self):
        self.temp.cleanup()

    def test_successful_ci_version_is_selected_and_download_pinned(self):
        gh = FakeGithub()
        old, new, backup, link = updater.update_installed(
            self.install, fetch_json=gh.json, fetch_bytes=gh.bytes
        )
        self.assertEqual((old, new), ("0.3.6", "0.3.7"))
        self.assertIsNotNone(backup)
        self.assertTrue(backup.is_dir())
        self.assertEqual((backup / "InitGui.py").read_text(), "old version")
        self.assertEqual(
            (self.install / "azdesign" / "session.py").read_text(), "# new session\n"
        )
        self.assertTrue(all(("/" + gh.commit + "/") in u for u in gh.downloads))
        self.assertEqual(link, "https://github.com/example/actions/runs/1")

    def test_same_version_never_modifies_installation(self):
        gh = FakeGithub(version="0.3.6")
        old, new, backup, _link = updater.update_installed(
            self.install, fetch_json=gh.json, fetch_bytes=gh.bytes
        )
        self.assertEqual(old, new)
        self.assertIsNone(backup)
        self.assertEqual((self.install / "InitGui.py").read_text(), "old version")
        self.assertEqual(len(gh.downloads), 1)

    def test_invalid_blob_refuses_install_and_keeps_previous_version(self):
        gh = FakeGithub()
        real_bytes = gh.bytes
        def modified(url):
            result = real_bytes(url)
            return b"tampered" if url.endswith("session.py") else result
        with self.assertRaises(updater.UpdateError):
            updater.update_installed(
                self.install, fetch_json=gh.json, fetch_bytes=modified
            )
        self.assertEqual(updater.local_version(self.install), "0.3.6")
        self.assertEqual((self.install / "InitGui.py").read_text(), "old version")

    def test_failing_ci_is_not_selected(self):
        gh = FakeGithub()
        def failure(url):
            if "actions/workflows" in url:
                return {"workflow_runs": [{
                    "head_sha": gh.commit, "head_branch": updater.BRANCH,
                    "event": "pull_request", "status": "completed",
                    "conclusion": "failure",
                }]}
            return gh.json(url)
        with self.assertRaisesRegex(updater.UpdateError, "No successful"):
            updater.update_installed(self.install, fetch_json=failure,
                                     fetch_bytes=gh.bytes)
        self.assertFalse(gh.downloads)
        self.assertEqual(updater.local_version(self.install), "0.3.6")

    def test_symlink_file_mode_is_rejected(self):
        gh = FakeGithub()
        def bad_mode(url):
            result = gh.json(url)
            if "/git/trees/" in url:
                result["tree"][0]["mode"] = "120000"
            return result
        with self.assertRaisesRegex(updater.UpdateError, "file mode"):
            updater.update_installed(self.install, fetch_json=bad_mode,
                                     fetch_bytes=gh.bytes)
        self.assertEqual(updater.local_version(self.install), "0.3.6")

    def test_untrusted_paths_are_rejected(self):
        gh = FakeGithub()
        for name in ("../outside.py", "/evil.py", "foo/../bar.py",
                     "a//b.py", "dir\\evil.py"):
            with self.subTest(path=name):
                with self.assertRaises(updater.UpdateError):
                    updater.source_url(gh.commit, name)

    def test_cancel_while_downloading_leaves_existing_files(self):
        gh = FakeGithub()
        def cancel(done, total, name):
            raise updater.UpdateError("Cancelled by user")
        with self.assertRaisesRegex(updater.UpdateError, "Cancelled"):
            updater.update_installed(
                self.install, fetch_json=gh.json, fetch_bytes=gh.bytes,
                progress=cancel,
            )
        self.assertEqual(updater.local_version(self.install), "0.3.6")
        self.assertEqual((self.install / "InitGui.py").read_text(), "old version")


if __name__ == "__main__":
    unittest.main(verbosity=2)
