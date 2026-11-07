# SPDX-License-Identifier: LGPL-2.1-or-later
"""Capability-based adapters for native FreeCAD extrusion properties."""


def set_extrusion_sides(feature, direction):
    """Use the 1.1 side API without touching its deprecated properties."""
    if direction not in ("One side", "Symmetric", "Two sides"):
        raise ValueError("Unsupported extrusion direction: " + direction)
    if "SideType" in feature.PropertiesList:
        feature.SideType = direction
        feature.Type = "Length"
        if direction == "Two sides":
            feature.Type2 = "Length"
    else:
        feature.Midplane = direction == "Symmetric"
        feature.Type = "TwoLengths" if direction == "Two sides" else "Length"


def extrusion_side_type(feature):
    if "SideType" in feature.PropertiesList:
        return str(feature.SideType)
    if feature.Midplane:
        return "Symmetric"
    return "Two sides" if feature.Type == "TwoLengths" else "One side"
