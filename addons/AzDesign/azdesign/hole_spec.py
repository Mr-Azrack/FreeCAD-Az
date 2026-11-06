# SPDX-License-Identifier: LGPL-2.1-or-later
"""Validated native Hole settings with opt-in modeled-thread diagnostics.

Modeled geometry can crash the native OCCT process. The default is cosmetic;
helical threads require explicit experimental authorization and a durable log.
"""

from dataclasses import dataclass
from math import isfinite


THREAD_TYPES = (
    "None", "ISOMetricProfile", "ISOMetricFineProfile", "UNC", "UNF",
    "UNEF", "NPT", "BSP", "BSW", "BSF", "ISOTyre",
)


# Human-readable controls, native enum IDs remain intact for FreeCAD storage.
THREAD_LABELS = {
    "None": "None (plain hole)",
    "ISOMetricProfile": "ISO metric · coarse",
    "ISOMetricFineProfile": "ISO metric · fine",
    "UNC": "UNC · unified coarse",
    "UNF": "UNF · unified fine",
    "UNEF": "UNEF · extra fine",
    "NPT": "NPT · tapered pipe",
    "BSP": "BSP · pipe",
    "BSW": "BSW · Whitworth",
    "BSF": "BSF · fine Whitworth",
    "ISOTyre": "ISO tyre valve",
}


@dataclass(frozen=True)
class HoleSpec:
    diameter: float = 6.0
    depth: float = 10.0
    through_all: bool = False
    thread_type: str = "None"
    thread_size: str = ""
    model_thread: bool = False
    experimental: bool = False

    def validate(self):
        if not isfinite(self.diameter) or self.diameter <= 0:
            raise ValueError("Hole diameter must be a positive finite number.")
        if not isfinite(self.depth) or self.depth <= 0:
            raise ValueError("Hole depth must be a positive finite number.")
        if self.thread_type not in THREAD_TYPES:
            raise ValueError("Unsupported thread standard: " + str(self.thread_type))
        if self.model_thread and not self.experimental:
            raise ValueError(
                "Modeled threads require explicit experimental authorization and "
                "crash logging. Normal Hole previews remain cosmetic."
            )
        if self.model_thread and (self.thread_type == "None" or not self.thread_size):
            raise ValueError(
                "Choose a thread standard and an explicit size to model a thread."
            )
        if self.thread_size and self.thread_type == "None":
            raise ValueError("Choose a thread standard before choosing a thread size.")
        return self

    def apply(self, feature, before_model=None):
        """Apply dimensions first; enable the risky geometry switch last.

        Modeled-thread callers must supply a callback that durably records the
        exact pre-switch state. No log means no risky native calculation.
        """
        self.validate()
        if self.model_thread and before_model is None:
            raise ValueError("Modeled threads require an active diagnostic recorder.")
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
            feature.Threaded = True
            # FreeCAD 1.1 may keep this property read-only until Threaded
            # becomes true. Set it only after enabling the thread standard.
            if hasattr(feature, "CosmeticThread"):
                feature.CosmeticThread = not self.model_thread
        else:
            if hasattr(feature, "CosmeticThread"):
                feature.CosmeticThread = False
        if self.model_thread:
            before_model()
            feature.ModelThread = True
        else:
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
