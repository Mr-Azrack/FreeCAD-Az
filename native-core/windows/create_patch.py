#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Create file-level Windows Az Native patches from two actual app directories.

The patch contains ONLY changed/new files and a JSON index containing both
old and new hashes. It cannot create arbitrary paths outside app root.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZIP_DEFLATED

SCHEMA = 1
EXCLUDES = {"unins000.exe", "unins000.dat", "Az Native Version.json", "patch.json"}


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def files_in(folder):
    result = {}
    for file in folder.rglob("*"):
        if file.is_symlink():
            raise ValueError("Symlinks are not supported in Az Native patches")
        if not file.is_file():
            continue
        rel = file.relative_to(folder).as_posix()
        if file.name.lower().startswith("unins") or rel in EXCLUDES:
            continue
        result[rel] = (file, hash_file(file))
    return result


def safe_rel(path):
    # Restrict to an app-root relative Windows path; refuse alternate streams,
    # any Windows drive, UNC path, traversal, and hidden absolute paths.
    posix = PurePosixPath(path)
    if (
        not path or not isinstance(path, str) or "\\" in path or ":" in path
        or posix.is_absolute() or ".." in posix.parts or "." in posix.parts
        or any(part in ("",) for part in posix.parts)
        or path.lower().startswith("unins")
    ):
        raise ValueError("Unsafe patch path: " + str(path))
    return path


def make_patch(old_root, new_root, output, old_version, new_version):
    old_root, new_root, output = Path(old_root), Path(new_root), Path(output)
    if not old_root.is_dir() or not new_root.is_dir():
        raise ValueError("Both version directories must exist")
    if output.exists():
        raise FileExistsError("Refusing to overwrite an existing patch archive")
    if not old_version or not new_version or old_version == new_version:
        raise ValueError("Specify distinct from/to versions")
    old = files_in(old_root)
    new = files_in(new_root)
    files = []
    delete = []
    for rel in sorted(new):
        safe_rel(rel)
        src, digest = new[rel]
        original = old.get(rel)
        if original and original[1] == digest:
            continue
        files.append({
            "path": rel, "before": original[1] if original else None,
            "after": digest, "size": src.stat().st_size,
        })
    for rel in sorted(set(old) - set(new)):
        safe_rel(rel)
        delete.append({"path": rel, "before": old[rel][1]})
    manifest = {
        "format": SCHEMA, "product": "AzDesignNative",
        "from_version": old_version, "to_version": new_version,
        "files": files, "delete": delete,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zipfile:
            zipfile.writestr("patch.json", json.dumps(manifest, indent=2, sort_keys=True))
            for entry in files:
                zipfile.write(new[entry["path"]][0], "files/" + entry["path"])
        with ZipFile(output) as archive:
            if archive.testzip():
                raise ValueError("Generated patch ZIP failed CRC validation")
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return manifest


def main():
    ap = argparse.ArgumentParser()
    for name in ("old", "new", "output"):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--from-version", required=True)
    ap.add_argument("--to-version", required=True)
    args = ap.parse_args()
    manifest = make_patch(args.old, args.new, args.output, args.from_version, args.to_version)
    print(json.dumps({"changed": len(manifest["files"]), "deleted": len(manifest["delete"]),
                      "bytes": args.output.stat().st_size}, indent=2))


if __name__ == "__main__":
    main()
