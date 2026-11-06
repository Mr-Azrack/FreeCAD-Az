# SPDX-License-Identifier: LGPL-2.1-or-later
"""Validated, non-destructive settings for native PartDesign Hole features.

Real helical threading can crash the OCCT process, bypassing Python exception
handling. Az Design deliberately produces native cosmetic/thread-metadata holes
and never enables ModelThread from the interactive task.
"""

from dataclasses import dataclass
from math import isfinite


THREAD_TYPES = (
    "None", "ISOMetricProfile", "ISOMetricFineProfile", "UNC", "UNF",
    "UNEF", "NPT", "BSP", "BSW", "BSF", "ISOTyre",
)


@dataclass(frozen=True)
class HoleSpec:
    diameter: float = 6.0
    depth: float = 10.0
    through_all: bool = False
    thread_type: str = "None"
    thread_size: str = ""
    model_thread: bool = False

    def validate(self):
        if not isfinite(self.diameter) or self.diameter <= 0:
            raise ValueError("Hole diameter must be a positive finite number.")
        if not isfinite(self.depth) or self.depth <= 0:
            raise ValueError("Hole depth must be a positive finite number.")
        if self.thread_type not in THREAD_TYPES:
            raise ValueError("Unsupported thread standard: " + str(self.thread_type))
        if self.model_thread:
            raise ValueError(
                "Modeled helical threads are disabled in Az Design because native "
                "thread geometry has crashed FreeCAD. Use cosmetic threads for "
                "manufacturing intent."
            )
        if self.thread_size and self.thread_type == "None":
            raise ValueError("Choose a thread standard before choosing a thread size.")
        return self

    def apply(self, feature):
        """Set all native properties without ever entering modeled-thread mode."""
        self.validate()
        # All dimension updates happen while unthreaded; FreeCAD can make the
        # diameter read-only once a standard thread has been selected.
        feature.ModelThread = False
        feature.Threaded = False
        feature.ThreadType = "None"
        feature.Diameter = float(self.diameter)
        feature.DepthType = "ThroughAll" if self.through_all else "Dimension"
        feature.Depth = float(self.depth)
        if self.thread_type != "None":
            feature.ThreadType = self.thread_type
            choices = list(feature.getEnumerationsOfProperty("ThreadSize"))
            if self.thread_size and self.thread_size not in choices:
                raise ValueError(
                    "Thread size " + self.thread_size +
                    " is not available for " + self.thread_type + "."
                )
            if self.thread_size:
                feature.ThreadSize = self.thread_size
            feature.CosmeticThread = True
            feature.Threaded = True
        else:
            feature.CosmeticThread = False
        # Native geometry is kept native and editable in ordinary FreeCAD.
        feature.ModelThread = False


def thread_sizes(feature, thread_type):
    """Read size options from the installed FreeCAD, not a copied standard."""
    if thread_type == "None":
        return []
    if thread_type not in THREAD_TYPES:
        raise ValueError("Unsupported thread standard.")
    feature.ModelThread = False
    feature.Threaded = False
    feature.ThreadType = thread_type
    return [str(value) for value in feature.getEnumerationsOfProperty("ThreadSize")]
