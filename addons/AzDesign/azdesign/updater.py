# SPDX-License-Identifier: LGPL-2.1-or-later
"""Update Az Design from an exact successful GitHub Actions source commit.

No GitHub token, shell, Git installation or Web browser download is needed
for this public development repository. Download source blobs pinned to the
tested SHA, check every Git blob hash and stage before the existing installer
atomically swaps the active workbench with a dated backup.

An update while FreeCAD is running requires a FULL process restart to load it.
"""
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
import urllib.request
from urllib.parse import quote
import xml.etree.ElementTree as ET


REPOSITORY = "Mr-Azrack/FreeCAD-Az"
BRANCH = "codex/az-design-workbench"
API = "https://api.github.com/repos/" + REPOSITORY
RAW = "https://raw.githubusercontent.com/" + REPOSITORY
WORKFLOW = "az-design.yml"
MAX_FILES = 500
MAX_TOTAL_BYTES = 25 * 1024 * 1024
MAX_BLOB_BYTES = 2 * 1024 * 1024
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class UpdateError(RuntimeError):
    pass


def _fetch_bytes(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "AzDesign-Updater/0.3",
                      "Accept": "application/vnd.github+json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = response.read(MAX_TOTAL_BYTES + 1)
    except Exception as exc:
        raise UpdateError("Cannot reach the public GitHub update source: " + str(exc)) from exc
    if len(result) > MAX_TOTAL_BYTES:
        raise UpdateError("Update response exceeds the size limit.")
    return result


def _fetch_json(url):
    try:
        return json.loads(_fetch_bytes(url))
    except (ValueError, UnicodeError) as exc:
        raise UpdateError("GitHub returned invalid update metadata.") from exc


def _version_number(version):
    text = str(version).strip()
    if not re.fullmatch(r"\d+(?:\.\d+){1,3}", text):
        raise UpdateError("Unexpected Az Design version: " + text)
    return tuple(int(x) for x in text.split("."))


def package_version(content):
    try:
        value = ET.fromstring(content).findtext("version")
    except ET.ParseError as exc:
        raise UpdateError("Downloaded package.xml is invalid.") from exc
    if not value:
        raise UpdateError("The downloaded version has no package version.")
    _version_number(value)
    return value.strip()


def local_version(installation):
    manifest = Path(installation) / "package.xml"
    return package_version(manifest.read_bytes()) if manifest.is_file() else "0.0"


def tested_revision(fetch_json=_fetch_json):
    """Only an actual SUCCESSFUL Az Design pull-request workflow is eligible."""
    url = (
        API + "/actions/workflows/" + WORKFLOW
        + "/runs?event=pull_request&branch=" + quote(BRANCH, safe="")
        + "&status=success&per_page=20"
    )
    result = fetch_json(url)
    for run in result.get("workflow_runs", []):
        sha = run.get("head_sha", "")
        if (run.get("conclusion") == "success"
                and run.get("status") == "completed"
                and run.get("event") == "pull_request"
                and run.get("head_branch") == BRANCH
                and _SHA_RE.fullmatch(sha)):
            return sha, run.get("html_url", "")
    raise UpdateError(
        "No successful Az Design CI run was found for the development branch. "
        "The current installation was left unchanged."
    )


def source_url(sha, path):
    if not _SHA_RE.fullmatch(sha):
        raise UpdateError("Invalid source commit.")
    pure = PurePosixPath(path)
    if (pure.is_absolute() or not path or ".." in pure.parts
            or "\\" in path or pure.as_posix() != path):
        raise UpdateError("Unsafe update file path: " + str(path))
    return RAW + "/" + sha + "/addons/AzDesign/" + quote(path, safe="/")


def verified_blob(data, git_sha):
    actual = hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()
    if actual != git_sha:
        raise UpdateError("A downloaded file failed its Git SHA-1 integrity check.")


def file_manifest(sha, fetch_json=_fetch_json):
    """Find the isolated AzDesign subtree rather than fetching the giant fork."""
    entries = fetch_json(API + "/contents/addons?ref=" + sha)
    directory = next(
        (entry for entry in entries
         if entry.get("name") == "AzDesign" and entry.get("type") == "dir"),
        None,
    )
    if not directory or not _SHA_RE.fullmatch(directory.get("sha", "")):
        raise UpdateError("Az Design source directory is missing from that commit.")
    tree = fetch_json(API + "/git/trees/" + directory["sha"] + "?recursive=1")
    if tree.get("truncated"):
        raise UpdateError("The GitHub file listing was truncated.")
    files = []
    total = 0
    for node in tree.get("tree", []):
        if node.get("type") != "blob":
            if node.get("type") != "tree":
                raise UpdateError("Unsupported source entry (symlink/submodule).")
            continue
        name = node.get("path", "")
        source_url(sha, name)  # Check for path traversal.
        if name.endswith(".pyc") or "__pycache__" in PurePosixPath(name).parts:
            continue
        if not _SHA_RE.fullmatch(node.get("sha", "")):
            raise UpdateError("Invalid source Git blob hash.")
        size = node.get("size", -1)
        if not isinstance(size, int) or size < 0 or size > MAX_BLOB_BYTES:
            raise UpdateError("Source file exceeds the updater limit: " + name)
        total += size
        files.append((name, node["sha"], size))
    if not files or len(files) > MAX_FILES or total > MAX_TOTAL_BYTES:
        raise UpdateError("Az Design file listing exceeds the updater limits.")
    if not {"InitGui.py", "package.xml", "azdesign/install.py",
            "azdesign/session.py", "azdesign/updater.py"}.issubset(
                {item[0] for item in files}):
        raise UpdateError("The successful build is missing mandatory Az Design files.")
    return files


def download_source(sha, destination, *, fetch_bytes=_fetch_bytes,
                    fetch_json=_fetch_json, progress=None):
    """Download and verify ALL files before touching the installed workbench."""
    destination = Path(destination)
    files = file_manifest(sha, fetch_json=fetch_json)
    destination.mkdir(parents=True, exist_ok=True)

    def worker(entry):
        name, expected_sha, expected_size = entry
        data = fetch_bytes(source_url(sha, name))
        if len(data) != expected_size:
            raise UpdateError("Downloaded size mismatch: " + name)
        verified_blob(data, expected_sha)
        return name, data

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(worker, entry): entry[0] for entry in files}
        for index, future in enumerate(as_completed(futures), 1):
            name, data = future.result()
            path = destination.joinpath(*PurePosixPath(name).parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            if progress:
                progress(index, len(files), name)
    if not (destination / "InitGui.py").is_file():
        raise UpdateError("Incomplete source download.")
    for path in destination.rglob("*.py"):
        ast.parse(path.read_bytes(), filename=str(path))
    return package_version((destination / "package.xml").read_bytes())


def update_installed(installation, *, fetch_bytes=_fetch_bytes,
                     fetch_json=_fetch_json, progress=None):
    """Return (old_version, new_version, backup_path, workflow_link)."""
    installation = Path(installation)
    old = local_version(installation)
    sha, workflow_link = tested_revision(fetch_json=fetch_json)
    remote = package_version(fetch_bytes(source_url(sha, "package.xml")))
    if _version_number(remote) <= _version_number(old):
        return old, old, None, workflow_link
    with tempfile.TemporaryDirectory(prefix="az-design-download-") as temp:
        source = Path(temp) / "AzDesign"
        downloaded_version = download_source(
            sha, source, fetch_bytes=fetch_bytes,
            fetch_json=fetch_json, progress=progress,
        )
        if downloaded_version != remote:
            raise UpdateError("Update version changed during download.")
        # Import the already installed, tested atomic installer. On Windows,
        # this runs without requiring a shell, Git, admin rights or a token.
        from .install import install
        installed, backup = install(source, installation.parent)
        if installed.resolve() != installation.resolve():
            raise UpdateError("Installer returned an unexpected target path.")
    return old, remote, backup, workflow_link
