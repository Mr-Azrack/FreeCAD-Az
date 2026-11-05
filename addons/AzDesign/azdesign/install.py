# SPDX-License-Identifier: LGPL-2.1-or-later
"""Local-only installer. Existing installations are kept as dated backups."""
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def install(source, mod_directory):
    source = Path(source).resolve()
    mod_directory = Path(mod_directory).resolve()
    target = mod_directory / "AzDesign"
    if source == target:
        raise ValueError(
            "Az Design is already in the installation folder. Restart FreeCAD and select Az Design."
        )
    if not (source / "InitGui.py").is_file() or not (source / "azdesign" / "session.py").is_file():
        raise ValueError("Select the extracted AzDesign folder containing InitGui.py.")
    mod_directory.mkdir(parents=True, exist_ok=True)
    stage_root = Path(tempfile.mkdtemp(prefix=".az-install-", dir=str(mod_directory)))
    staged = stage_root / "AzDesign"
    backup = None
    try:
        shutil.copytree(
            source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git", "tests")
        )
        if target.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_root = mod_directory.parent / "AzDesign-backups"
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / ("AzDesign-" + stamp)
            suffix = 1
            while backup.exists():
                backup = backup_root / ("AzDesign-{}-{}".format(stamp, suffix))
                suffix += 1
            os.replace(target, backup)
        try:
            os.replace(staged, target)
        except Exception:
            if backup and not target.exists():
                os.replace(backup, target)
            raise
    finally:
        shutil.rmtree(stage_root)
    return target, backup
