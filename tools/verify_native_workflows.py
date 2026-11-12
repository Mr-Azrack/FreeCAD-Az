#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Fail cheap CI immediately on malformed native release/patch workflows.

This is an additional structure/safety check, not a replacement for
GitHub's workflow validator or a release approval.
"""
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def step_map(job):
    steps = job.get("steps", [])
    names = [step.get("name", "") for step in steps if "name" in step]
    assert len(names) == len(set(names)), "Duplicated workflow step names"
    return {step.get("name"): step for step in steps if step.get("name")}


def check():
    paths = (
        WORKFLOWS / "az-native-patch.yml",
        WORKFLOWS / "az-design.yml",
        WORKFLOWS / "az-native-publish.yml",
    )
    loaded = {}
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict) and isinstance(data.get("jobs"), dict), (
            f"Invalid workflow or missing jobs in {path.name}"
        )
        loaded[path.name] = data
    patch = loaded["az-native-patch.yml"]
    on = patch.get("on", patch.get(True, {}))
    marker = on["push"]["paths"]
    assert marker == [".github/validation-requests/native-0.5.11.txt"], (
        "Expensive Windows pipeline must be batch-marker-triggered only"
    )
    assert on["workflow_dispatch"]["inputs"]["cold_validation"]["type"] == "boolean"
    jobs = patch["jobs"]
    assert "geometry" in jobs and "patch" in jobs
    assert "geometry" in jobs["patch"].get("needs", [])
    steps = step_map(jobs["patch"])
    stages = (
        "Restore pinned installed 0.5.6 baseline cache",
        "Validate cached 0.5.6 baseline before use",
        "Download original, tested 0.5.4 installer",
        "Verify baseline SHA256 and install real 0.5.4",
        "Download verified 0.5.5 patch used by installed owner",
        "Reconstruct actual 0.5.5 installed baseline",
        "Download pinned tested 0.5.6 patch from run 42871091253",
        "Reconstruct actual 0.5.6 installed baseline",
        "Record exact installed baseline hashes for future cache restores",
        "Cache immutable 0.5.6 installed baseline for the next candidate",
        "Download original installed 0.5.7 Build 36 patch",
        "Verify and reconstruct original 0.5.7 Build 36",
        "Download original published 0.5.8 Build 39 patch",
        "Verify and reconstruct original 0.5.8 Build 39",
        "Download verified published 0.5.9 Build 40 patch",
        "Reconstruct exact installed 0.5.9 baseline",
        "Reconstruct verified published 0.5.10 baseline",
        "Build changed-only overlay (no native core re-download)",
        "Apply to real installed baseline, Qt smoke, rollback, uninstall",
        "Upload tested incremental patch (not a public release)",
        "Publish verified 0.5.11 patch to online updater release channel",
    )
    order = [step.get("name") for step in jobs["patch"]["steps"]]
    assert all(item in steps for item in stages), "Missing critical patch validation step"
    assert [order.index(item) for item in stages] == sorted(order.index(item) for item in stages), (
        "Pinned baseline, candidate patch, validation and upload must run in order"
    )
    for name in stages[2:8]:
        assert "cache-hit != 'true'" in steps[name].get("if", ""), (
            f"Cold baseline step must be skipped on exact cache hit: {name}"
        )
    assert "cache-hit == 'true'" in steps[stages[1]].get("if", "")
    assert steps[stages[0]].get("uses") == "actions/cache/restore@v4"
    assert steps[stages[9]].get("uses") == "actions/cache/save@v4"
    assert ".az-baseline-hashes.json" in steps[stages[1]].get("run", "")
    assert "SHA256" in steps[stages[1]].get("run", "")
    assert "cold_validation" in steps[stages[0]].get("if", "")
    for stage, run_id in ((10, 42899554668), (12, 42949194221), (14, 42959009956)):
        assert steps[stages[stage]].get("with", {}).get("run-id") == run_id, (
            f"Unpinned historical patch artifact: {stages[stage]}"
        )
    for stage in (11, 13, 15, 16):
        assert "SHA256" in steps[stages[stage]].get("run", ""), (
            f"Historical patch lacks checksum validation: {stages[stage]}"
        )
    assert "gh release download v0.5.10" in steps[stages[16]].get("run", "")
    build = steps[stages[17]].get("run", "")
    assert "--from-version 0.5.10 --to-version 0.5.11" in build
    assert "AzDesignNative-0.5.10-to-0.5.11.azpatch" in build
    verify = steps[stages[18]].get("run", "")
    assert "Patched version is not 0.5.11" in verify
    assert "Original version was not restored" in verify
    assert "smoke_qt.py" in verify and "-RollbackLatest" in verify
    assert "unins000.exe" in verify
    assert "SHA256" in verify
    assert steps[stages[19]].get("with", {}).get("name") == "AzDesignNative-0.5.10-to-0.5.11-PATCH"
    # Never let a development-branch validation job publish an update.
    assert steps[stages[20]].get("if") == "github.ref == 'refs/heads/main'", (
        "Release publication must be disabled on feature branches"
    )
    fast = loaded["az-design.yml"]
    assert fast.get("concurrency", {}).get("cancel-in-progress") is True, (
        "Superseded fast CI must be cancellable"
    )
    publication = loaded["az-native-publish.yml"]
    assert "workflow_dispatch" in publication.get("on", publication.get(True, {}))
    assert publication["jobs"]["publish"].get("if") == (
        "github.ref == 'refs/heads/main'"
    ), "Do not publish directly from feature branches"
    print("PASS: workflow YAML, batch-only patch trigger, pinned cache and release gates")


if __name__ == "__main__":
    check()
