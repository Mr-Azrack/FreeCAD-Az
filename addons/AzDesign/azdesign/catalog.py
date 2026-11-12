# SPDX-License-Identifier: LGPL-2.1-or-later
"""The editable command layout with explicit native UI escape hatches."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    label: str
    command: str
    tip: str
    icon: str = ""


TOOLS = {
    "sketch": Tool(
        "Create Sketch",
        "Az_Sketch",
        "Select a flat face, or choose an origin plane.",
        "PartDesign_NewSketch",
    ),
    "extrude": Tool(
        "Extrude",
        "Az_Extrude",
        "E · Select sketch regions or a planar face. Preview Join, Cut, Intersect or New body.",
        "extrude",
    ),
    "cut": Tool(
        "Cut", "Az_Cut", "Remove selected sketch regions or a planar face.", "PartDesign_Pocket"
    ),
    "presspull": Tool(
        "Press / Pull",
        "Az_PressPull",
        "Q · Offset an end face, resize an editable cylinder, extrude profiles or fillet an edge.",
        "PartDesign_Pad",
    ),
    "parameters": Tool(
        "Parameters",
        "Az_Parameters",
        "Edit user parameters and native model dimensions.",
        "Spreadsheet_CreateSheet",
    ),
    "resume": Tool(
        "Resume History",
        "Az_ResumeHistory",
        "Resume every Body at its saved latest feature.",
        "Std_SkipRecompute",
    ),
    "revolve": Tool("Revolve", "PartDesign_Revolution", "Revolve a selected sketch about an axis."),
    "loft": Tool("Loft", "PartDesign_AdditiveLoft", "Join sketch sections with a solid loft."),
    "sweep": Tool("Sweep", "PartDesign_AdditivePipe", "Sweep a profile along a selected path."),
    "hole": Tool("Hole", "Az_Hole", "H · Native holes with safe previews and cosmetic threads.", "PartDesign_Hole"),
    "fillet": Tool(
        "Fillet", "Az_Fillet",
        "F · Validate native Fillet geometry before changing the real Body.",
        "PartDesign_Fillet",
    ),
    "chamfer": Tool(
        "Chamfer", "Az_Chamfer",
        "Check edge distances against the native kernel before committing a bevel.",
        "PartDesign_Chamfer",
    ),
    "snaps": Tool(
        "Snap & Centers", "Az_SnapFinder",
        "Find exact selected-edge endpoints, midpoints and circular centers; copy XYZ or place a fixed Sketch reference.",
        "Sketcher_CreatePoint",
    ),
    "shell": Tool("Shell", "PartDesign_Thickness", "Hollow a solid; select the faces to remove."),
    "mirror": Tool("Mirror", "Az_Mirror", "Mirror a selected solid feature across an origin plane."),
    "pattern": Tool(
        "Linear Pattern", "Az_LinearPattern", "Design live preview, spacing or extent, axis and editable native feature history."
    ),
    "polar": Tool(
        "Circular Pattern", "PartDesign_PolarPattern", "Repeat selected features around an axis."
    ),
    "body": Tool(
        "New Body", "Az_Body", "Create and activate a separate solid body.", "PartDesign_Body"
    ),
    "plane": Tool(
        "Offset Plane", "Az_OffsetPlane", "Select a flat face or origin plane, then enter a signed normal offset."
    ),
    "move": Tool("Move", "Az_Move", "M · Move an entire Body or component by X/Y/Z with undo."),
    "measure": Tool("Measure", "Std_Measure", "Measure selected edges, faces or objects."),
    "home": Tool(
        "Home View", "Az_Home", "Isometric view and fit the whole model.", "Std_ViewIsometric"
    ),
    "fit": Tool("Fit", "Std_ViewFitAll", "Fit the model to the view."),
    "finish": Tool(
        "Finish Sketch",
        "Az_FinishSketch",
        "Close the sketch, return to Solid and select its profile.",
        "Sketcher_LeaveSketch",
    ),
    "line": Tool("Line", "Sketcher_CreatePolyline", "L · Draw connected sketch lines."),
    "rectangle": Tool("Rectangle", "Sketcher_CreateRectangle", "R · Draw a corner rectangle."),
    "sizedrect": Tool(
        "Sized Rectangle", "Az_SizedRectangle",
        "Enter width and height for a fully constrained, editable rectangle in an empty sketch.",
        "Sketcher_CreateRectangle",
    ),
    "centerrect": Tool(
        "Center Rectangle", "Sketcher_CreateRectangle_Center", "Draw a rectangle about its center."
    ),
    "circle": Tool("Circle", "Sketcher_CreateCircle", "C · Draw a center-and-radius circle."),
    "arc": Tool("Arc", "Sketcher_Create3PointArc", "Draw an arc through three points."),
    "slot": Tool("Slot", "Sketcher_CreateSlot", "Draw a straight slot."),
    "trim": Tool("Trim", "Sketcher_Trimming", "T · Trim unwanted sketch segments."),
    "offset": Tool("Offset", "Sketcher_Offset", "Offset selected sketch geometry."),
    "project": Tool("Project", "Sketcher_Projection", "P · Project existing solid edges into the active sketch as references."),
    "construction": Tool(
        "Construction",
        "Sketcher_ToggleConstruction",
        "X · Toggle selected sketch geometry to construction.",
    ),
    "dimension": Tool(
        "Dimension",
        "Az_Dimension",
        "D · Smart dimension: length, distance, radius, diameter or angle from the selection.",
        "Sketcher_Dimension",
    ),
    "labels": Tool(
        "Show / Hide Labels", "Az_SketchLabels",
        "Temporarily toggle sketch constraint labels without changing dimensions, geometry or solver.",
    ),
    "sketchpattern": Tool(
        "Rectangular Pattern", "Az_SketchPattern",
        "In-canvas 2D array of real constrained sketch circles, for four holes and larger patterns.",
    ),
    "horizontal": Tool(
        "Horizontal", "Sketcher_ConstrainHorizontal", "Constrain selected lines horizontally."
    ),
    "vertical": Tool(
        "Vertical", "Sketcher_ConstrainVertical", "Constrain selected lines vertically."
    ),
    "coincident": Tool("Coincident", "Sketcher_ConstrainCoincident", "Join selected points."),
    "tangent": Tool("Tangent", "Sketcher_ConstrainTangent", "Make selected geometry tangent."),
    "equal": Tool("Equal", "Sketcher_ConstrainEqual", "Give selected geometry equal size."),
    "diameter": Tool(
        "Diameter", "Sketcher_ConstrainDiameter", "Dimension the diameter of a selected circle."
    ),
    "new": Tool("New Design", "Std_New", "Create an empty FreeCAD document."),
    "open": Tool("Open", "Std_Open", "Open a native CAD document or supported exchange file."),
    "save": Tool("Save", "Std_Save", "Save this design as an editable FreeCAD document."),
    "export": Tool("Export", "Std_Export", "Export selected objects, for example STEP or STL."),
    "undo": Tool("Undo", "Std_Undo", "Undo the last document operation."),
    "redo": Tool("Redo", "Std_Redo", "Redo the last undone document operation."),
    "palette": Tool(
        "Find a Tool", "Az_Search", "S · Search modeling tools.", "search"
    ),
    "update": Tool(
        "Update Design", "Az_Update",
        "Check for the latest CI-tested build; install with automatic backup. Restart FreeCAD afterward.",
        "Std_Refresh",
    ),
    "preferences": Tool("Preferences", "Std_DlgPreferences", "Open FreeCAD preferences."),
    "help": Tool(
        "Quick Guide",
        "Az_Help",
        "Installation, shortcuts and first-part instructions.",
        "Std_WhatsThis",
    ),
    "native": Tool(
        "Native CAD",
        "Az_Native",
        "Return to FreeCAD Part Design and restore the previous layout.",
        "PartDesign_Body",
    ),
    "cam": Tool(
        "Manufacture", "Az_CAM", "Switch to FreeCAD's installed CAM workbench.", "Path_Job"
    ),
}

SOLID = [
    (
        "CREATE",
        ["sketch", "extrude", "cut", "hole", ("More", ["body"])],
    ),
    (
        "MODIFY",
        [
            "presspull",
            "fillet",
            "chamfer",
            "move",
            "pattern",
            ("More", ["parameters", "mirror"]),
        ],
    ),
    ("CONSTRUCT", ["plane"]),
    ("INSPECT", ["snaps", "home"]),
]
SKETCH = [
    ("CREATE", ["line", "rectangle", "sizedrect", "circle", ("More", ["centerrect", "arc", "slot"])]),
    ("MODIFY", ["trim", "offset", "project", "sketchpattern", "construction"]),
    (
        "CONSTRAIN",
        [
            "dimension",
            (
                "Constraints",
                ["diameter", "horizontal", "vertical", "coincident", "tangent", "equal"],
            ),
        ],
    ),
    ("COMPLETE", ["finish"]),
]
UTILITIES = [
    ("DESIGN", ["new", "open", "save", "export"]),
    ("WORKFLOW", ["cam", "native"]),
    ("SETTINGS", ["parameters", "resume", "update", "preferences", "help"]),
]

SOLID_KEYS = {
    "E": "extrude",
    "Q": "presspull",
    "F": "fillet",
    "H": "hole",
    "M": "move",
    "S": "palette",
}
SKETCH_KEYS = {
    "L": "line",
    "R": "rectangle",
    "C": "circle",
    "D": "dimension",
    "T": "trim",
    "X": "construction",
    "P": "project",
    "S": "palette",
}


# Raw FreeCAD modeling/task commands are deliberately not advertised in the
# main Design ribbon. They remain available through an explicit Native CAD
# workspace switch until a tested Design-owned task implementation replaces them.
# Sketcher drawing tools below are low-level native canvas operations, NOT
# arbitrary PartDesign task panels: our workbench keeps the surrounding UI.
RAW_FEATURE_COMMANDS = frozenset(
    tool.command for key, tool in TOOLS.items()
    if key in {"revolve", "loft", "sweep", "shell", "polar", "measure"}
)

ALLOWED_NATIVE_COMMANDS = frozenset(
    tool.command for key, tool in TOOLS.items()
    if key in {
        "line", "rectangle", "centerrect", "circle", "arc", "slot",
        "trim", "offset", "project", "construction", "horizontal",
        "vertical", "coincident", "tangent", "equal", "diameter",
        "new", "open", "save", "export", "undo", "redo",
        "fit", "preferences",
    }
) | frozenset({"Std_ViewZoomIn", "Std_ViewZoomOut"})  # View-only, no model changes
