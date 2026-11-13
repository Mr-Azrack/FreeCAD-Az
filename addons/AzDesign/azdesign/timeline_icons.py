# SPDX-License-Identifier: LGPL-2.1-or-later
"""Own, vector-backed Design timeline icons independent of native GUI themes.

Icons are stable SVG images (never text abbreviations) rendered by Qt at the
current DPI. Full feature names remain available via accessibleName/tooltips.
"""
from pathlib import Path

_ICON_DIR = Path(__file__).resolve().parents[1] / "Resources" / "Icons"
_KNOWN = frozenset((
    "sketch", "extrude", "pocket", "hole", "pattern", "mirror", "fillet",
    "chamfer", "body", "revolve", "plane", "feature", "move", "slot",
))


def icon_key(obj):
    kind = getattr(obj, "TypeId", "")
    az_type = getattr(obj, "AzType", "")
    if kind == "Sketcher::SketchObject" or (
        hasattr(obj, "isDerivedFrom") and obj.isDerivedFrom("Sketcher::SketchObject")
    ):
        return "sketch"
    if kind in ("PartDesign::LinearPattern", "PartDesign::PolarPattern",
                "PartDesign::MultiTransform"):
        return "pattern"
    if kind == "PartDesign::Mirrored":
        return "mirror"
    if kind == "PartDesign::Hole":
        return "hole"
    if kind in ("PartDesign::Pocket", "PartDesign::SubtractiveLoft",
                "PartDesign::SubtractivePipe"):
        return "pocket"
    if kind == "PartDesign::Fillet":
        return "fillet"
    if kind == "PartDesign::Chamfer":
        return "chamfer"
    if kind in ("PartDesign::Pad", "PartDesign::AdditiveLoft",
                "PartDesign::AdditivePipe") or az_type == "AzExtrude":
        return "extrude"
    if kind in ("PartDesign::Revolution", "PartDesign::Groove"):
        return "revolve"
    if kind == "PartDesign::Body":
        return "body"
    if "DatumPlane" in kind:
        return "plane"
    if az_type == "AzMove":
        return "move"
    return "feature"


def icon_path(obj):
    return icon_path_for_key(icon_key(obj))


def icon_path_for_key(key):
    assert key in _KNOWN
    return str(_ICON_DIR / ("timeline-" + key + ".svg"))
