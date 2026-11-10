# SPDX-License-Identifier: LGPL-2.1-or-later
"""Crash-surviving checkpoints for opt-in native modeled-thread experiments.

A native OCCT access violation kills FreeCAD before Python can catch it. Each
checkpoint is appended and fsynced before entering the risky native call.
The fault handler provides Python frames where supported, not a C++ stack.
"""

import faulthandler
import json
import os
from pathlib import Path
import platform
from datetime import datetime, timezone
from uuid import uuid4
from dataclasses import asdict


_FAULT_STREAMS = []  # Keep Windows fault-handler file descriptors alive.


class ThreadDiagnostic:
    def __init__(self, directory, *, version=(), scenario="Az Hole"):
        folder = Path(directory)
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.path = folder / ("modeled-thread-" + stamp + "-" + uuid4().hex[:8] + ".jsonl")
        self.fault_path = self.path.with_suffix(".fault.txt")
        self.record(
            "session_start",
            scenario=scenario,
            freecad_version=[str(x) for x in version],
            python_version=platform.python_version(),
            os=platform.platform(),
            note="Last completed checkpoint identifies where native execution stopped.",
        )
        # This handler may emit Python traces on a native fault. Windows crash
        # dumps/ProcDump remain necessary to identify the C++ OCCT frame.
        try:
            stream = open(self.fault_path, "w", encoding="utf-8", buffering=1)
            faulthandler.enable(file=stream, all_threads=True)
            _FAULT_STREAMS.append(stream)
            self.record("python_fault_handler_installed", fault_log=str(self.fault_path))
        except (OSError, RuntimeError, ValueError) as exc:
            self.record("python_fault_handler_unavailable", error=str(exc))

    def record(self, stage, **values):
        event = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
        }
        event.update(values)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, default=str, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def record_spec(self, stage, spec, *, feature=None):
        properties = {}
        if feature is not None:
            for key in (
                "ModelThread", "Threaded", "CosmeticThread", "ThreadType",
                "ThreadSize", "ThreadClass", "ThreadDepthType", "ThreadDepth",
                "DepthType", "Depth", "Diameter", "ThreadPitch",
                "UseCustomThreadClearance", "CustomThreadClearance",
            ):
                if hasattr(feature, key):
                    try:
                        properties[key] = str(getattr(feature, key))
                    except Exception as exc:
                        properties[key] = "unreadable: " + str(exc)
        self.record(stage, spec=asdict(spec), native_properties=properties)


def start_for_freecad(app, scenario="Az Hole"):
    return ThreadDiagnostic(
        Path(app.getUserAppDataDir()) / "AzDesign-Diagnostics",
        version=app.Version(),
        scenario=scenario,
    )
