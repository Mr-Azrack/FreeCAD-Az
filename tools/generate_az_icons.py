#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Generate Az's original, editable SVG workspace icon family."""

from pathlib import Path

CUBE = '<path fill="#e5eff6" d="M5 10 16 4 27 10 16 16Z"/><path fill="#bbd7e9" d="M5 10v13l11 6V16Z"/><path fill="#8cb7d3" d="M16 16v13l11-6V10Z"/>'
ART = {
    "body": CUBE,
    "sketch": '<path fill="#e1eff7" d="m3 23 10-17 16 5-10 17Z"/><path stroke="#c37b3e" stroke-width="3" d="m11 21 12-13"/><path d="m10 24 1-4 3 3Z"/>',
    "extrude": '<path fill="#dceaf3" d="m4 23 12-6 12 6-12 6Z"/><path fill="#b4d2e5" d="M9 11v11l7 4 7-4V11l-7 4Z"/><path fill="#f2f7fa" d="m9 11 7-4 7 4-7 4Z"/><path stroke="#bd783f" stroke-width="2.5" d="M16 16V2m-4 5 4-5 4 5"/>',
    "cut": CUBE
    + '<path fill="#f5f7f9" stroke="#b6733b" d="m11 9 5-3 5 3-5 3Z"/><path stroke="#b6733b" stroke-width="2" d="M16 3v13m-4-4 4 4 4-4"/>',
    "fillet": '<path fill="#c8e0ef" d="M5 26V6h14q8 0 8 8v12Z"/><path d="M5 12h12q5 0 5 5v9M17 6v6M22 17h5"/>',
    "chamfer": '<path fill="#c8e0ef" d="M5 26V6h14l8 8v12Z"/><path d="M5 12h11l6 6v8M16 12l3-6m3 12 5-4"/>',
    "shell": CUBE + '<path fill="#f7f9fb" d="m10 10 6-3 6 3-6 3Z"/>',
    "revolve": '<path fill="#c6dfef" d="M13 5q13 0 13 11T13 27V5Z"/><path stroke="#bf7d43" d="M11 2v28M5 8Q0 17 6 24m-4-1 4 1-1-4"/>',
    "plane": '<path fill="#dbeaf4" d="m3 24 10-17 16 5-10 17Z"/><path stroke="#bc7c45" stroke-dasharray="3 2" d="M4 10h25M16 2v26"/>',
    "line": '<path d="m5 26 9-19 13 10"/><circle fill="#8fbdda" cx="5" cy="26" r="2"/><circle fill="#8fbdda" cx="14" cy="7" r="2"/><circle fill="#8fbdda" cx="27" cy="17" r="2"/>',
    "rectangle": '<path fill="#e9f2f8" d="M6 7h21v19H6Z"/><path stroke="#bf7c42" d="M6 20h6v6"/>',
    "circle": '<circle fill="#e9f2f8" cx="16" cy="16" r="11"/><path stroke="#bd7a41" d="M12 16h8m-4-4v8"/>',
    "dimension": '<path d="M6 6v22m20-22v22M6 23h20m-16-3-4 3 4 3m12-6 4 3-4 3"/><path stroke="#bc7b42" d="m6 13 20-5"/>',
    "finish": '<path fill="#e4efdf" d="M5 6h22v21H5Z"/><path stroke="#59804c" stroke-width="3" d="m9 16 5 5 10-11"/>',
    "search": '<circle cx="13" cy="13" r="8"/><path stroke-width="3" d="m19 19 9 9"/>',
    "folder": '<path fill="#e2e8ed" d="M3 8h10l3 4h13v15H3Z"/>',
    "eye": '<path d="M2 16q14-17 28 0-14 17-28 0Z"/><circle fill="#85aac4" cx="16" cy="16" r="4"/>',
    "eye-off": '<path stroke="#aab5bd" d="M2 16q14-17 28 0-14 17-28 0Zm3 11L27 5"/>',
    "pan": '<path d="M11 18V8q0-4 3-3v11-11q3-3 4 1v10-8q3-3 4 1v9-5q3-2 4 1v9l-5 7H12l-7-12q-1-4 2-4Z"/>',
    "orbit": '<ellipse cx="16" cy="16" rx="13" ry="6" transform="rotate(-25 16 16)"/><path d="M11 4q14 1 10 23M7 5l4-1-1 4m12 15-1 4 4-1"/>',
    "display": '<path fill="#dce8f0" d="M3 5h26v18H3Z"/><path d="M16 23v5m-7 0h14"/>',
    "views": '<path fill="#e5eff5" d="M3 4h11v11H3Zm15 0h11v11H18ZM3 19h11v10H3Zm15 0h11v10H18Z"/>',
    "home": '<path d="m3 15 13-11 13 11M7 12v16h18V12m-13 16V18h8v10"/>',
    "fit": '<path d="M4 12V4h8m8 0h8v8M4 20v8h8m8 0h8v-8"/><path fill="#c6dfef" d="M10 10h12v12H10Z"/>',
    "zoom-in": '<circle cx="13" cy="13" r="9"/><path d="m20 20 9 9M8 13h10m-5-5v10"/>',
    "zoom-out": '<circle cx="13" cy="13" r="9"/><path d="m20 20 9 9M8 13h10"/>',
    "settings": '<path d="M5 6h22M5 16h22M5 26h22"/><path fill="#c4dfef" d="M10 3h5v6h-5Zm9 10h5v6h-5ZM8 23h5v6H8Z"/>',
    "new": '<path fill="#edf3f7" d="M7 3h13l6 6v20H7Zm13 0v7h6"/><path stroke="#557f9c" d="M11 20h11m-5-5v10"/>',
    "save": '<path fill="#d6e5ef" d="M5 3h20l3 3v23H5Z"/><path fill="#f7f9fa" d="M10 3h12v9H10Zm0 16h13v10H10Z"/>',
    "open": '<path fill="#e4edf4" d="M3 9h10l3 4h12v15H3Z"/><path fill="#bfd8e8" d="m3 28 4-12h23l-4 12Z"/>',
    "undo": '<path d="M9 10q17-6 19 11m-18-5-7-6 7-6"/>',
    "redo": '<path d="M23 10Q6 4 4 21m18-5 7-6-7-6"/>',
    "history-start": '<path d="M6 7v18"/><path fill="#718a9d" d="m24 7-13 9 13 9Z"/>',
    "history-back": '<path fill="#718a9d" d="m22 7-13 9 13 9Z"/>',
    "history-next": '<path fill="#718a9d" d="m10 7 13 9-13 9Z"/>',
    "history-end": '<path d="M26 7v18"/><path fill="#718a9d" d="m8 7 13 9-13 9Z"/>',
}
ART.update(
    {
        "loft": '<path fill="#c6dfef" d="M7 24 11 6h10l4 18Z"/><ellipse fill="#e7f0f6" cx="16" cy="6" rx="5" ry="3"/><path d="M7 24q9 7 18 0"/>',
        "sweep": '<path fill="#c6dfef" d="M5 27V17Q5 5 17 5h10v8H17q-4 0-4 4v10Z"/><path d="M5 27h8M27 5v8"/>',
        "hole": CUBE
        + '<ellipse fill="#f8f9fa" cx="16" cy="10" rx="5" ry="3"/><path stroke="#bc7b42" d="M16 3v15m-3-3 3 3 3-3"/>',
        "move": '<path d="M16 2v28M2 16h28M12 6l4-4 4 4M12 26l4 4 4-4M6 12l-4 4 4 4m20-8 4 4-4 4"/>',
    }
)

ALIASES = {
    "PartDesign_Body": "body",
    "PartDesign_NewSketch": "sketch",
    "PartDesign_Pocket": "cut",
    "PartDesign_Pad": "extrude",
    "PartDesign_Fillet": "fillet",
    "PartDesign_Chamfer": "chamfer",
    "PartDesign_Thickness": "shell",
    "PartDesign_Revolution": "revolve",
    "PartDesign_Plane": "plane",
    "Sketcher_CreatePolyline": "line",
    "Sketcher_CreateRectangle": "rectangle",
    "Sketcher_CreateCircle": "circle",
    "Sketcher_Dimension": "dimension",
    "Sketcher_LeaveSketch": "finish",
    "Std_ViewIsometric": "home",
    "Std_ViewFitAll": "fit",
    "Std_ViewZoomIn": "zoom-in",
    "Std_ViewZoomOut": "zoom-out",
    "Std_DlgPreferences": "settings",
    "Std_DlgParameter": "settings",
    "Std_New": "new",
    "Std_Open": "open",
    "Std_Save": "save",
    "Std_Undo": "undo",
    "Std_Redo": "redo",
}

ALIASES.update(
    {
        "PartDesign_AdditiveLoft": "loft",
        "PartDesign_AdditivePipe": "sweep",
        "PartDesign_Hole": "hole",
        "Std_TransformManip": "move",
    }
)


def generate():
    root = Path(__file__).resolve().parents[1] / "addons/AzDesign/Resources/Icons"
    root.mkdir(parents=True, exist_ok=True)
    for name, art in ART.items():
        (root / (name + ".svg")).write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><!-- SPDX-License-Identifier: LGPL-2.1-or-later --><g fill="none" stroke="#55738a" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
            + art
            + "</g></svg>\n"
        )
    for name, source in ALIASES.items():
        (root / (name + ".svg")).write_bytes((root / (source + ".svg")).read_bytes())
    return root


if __name__ == "__main__":
    print(generate())
