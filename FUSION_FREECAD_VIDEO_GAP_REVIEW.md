# Design Native vs Fusion — same mounting-plate workflow

Sources: owner's Fusion plate MP4 (1920×992, ~3:43), and FreeCAD Design Native MP4 from archive `FreeCAD 1.1.0 2026-11-10 22-42-46.zip` (~13:06). Timestamp values below are approximate observation points, not automatically timed command metrics. This is a workflow behavior reference; use our own UI assets.

| Task | Fusion video | Design video | Concrete fix in this batch |
| --- | --- | --- | --- |
| Create and edit the first plate sketch | First rectangle is dimensioned in-place without leaving the sketch canvas | ~0:12–0:48 rectangle / circle entry with constraint side panels | Preserve direct sketch/canvas input and accessible dimensions |
| Repeat the hole positions | By ~1:44 repeated circles are already positioned into long rows | ~1:00–5:50 many manually positioned circles, dimension annotations and Translate Parameters | Existing native constrained Sketch Rectangular Pattern now accepts picking the source circle *while its Design panel is open*, without switching tools; use exact X/Y counts and pitches |
| Extrude perforated plate | ~1:52 solid base already has all holes | ~6:10–6:35 Design Extrude demands choosing from many numbered profile regions | For an **unambiguously dominant perforated plate** automatically check just its outer face-with-holes, preserving all holes in one extrude. Do not guess for ambiguous regions. |
| Sketch directly on plate | ~2:00 enters sketch on top plate while remaining in modeling workflow | ~7:12 prominent Create Sketch plane/face chooser over part | After Create Sketch on a model, wait for next planar face click with no obstructing plane chooser; keep origin plane shortcuts for empty designs |
| Raised center feature | ~2:08–2:32 rectangle/dimensions/extrude appears directly on plate | ~7:30–10:10 dimension/profile/preview steps, occasional multi-profile choice | Preserve visible region previews; maintain manual region picking when multiple meaningful profiles remain |
| Round/edit edges | ~2:56–3:10 select and round edges in Solid context | ~12:12–12:30 switches to native FreeCAD Fillet Parameters | New **in-canvas Design Fillet/Chamfer panel** can open before edge selection, lets Ctrl+click select multiple edges, automatically checks the true OCCT outcome for each radius, supports Apply/Esc and parametric edit via timeline without raw native task panel. |
| History | Bottom uses compact recognizable feature icons and editable history | Design has icon timeline but native Fillet escaped it | Native Fillet/Chamfer history double-click routed through Design and supports undoable radius/distance editing |

## Acceptance sequence, using one plate

1. In a fresh Design document create an approximately 65×100 mm outline, add a Ø5 mm source circle, use Sketch Rectangular Pattern for the desired hole rows, confirm actual circles remain constraint-driven.
2. Finish Sketch → Extrude. With one dominant outer region enclosing many small holes, show a **single plate recommendation selected by default**; preview one intact plate with empty holes. Clicking other regions or Clear still works.
3. Choose Create Sketch while plate visible; click its top face directly in the viewport, without a covering modal or obstructing overlay. Sketch starts on that exact face.
4. Add a center rectangle and extrude the raised pad; preserve editable history and exact profiles.
5. Select Fillet before selecting edges, Ctrl+click the raised pad's vertical edges, enter radius, verify shape without mutating document, Apply once. Double-click Fillet in History, change radius, recompute, Undo and save/reopen.

## Implementation scope (2026-11-10)

- `profiles.preferred_plate_region` plus `tasks.ExtrudeTask.source_changed` safe plate default
- `sketch_plane_picker.SketchPlanePicker` non-obstructive face-first selection on existing solid
- `sketch_pattern_ui._CircleSelectionObserver` direct source circle picking
- `edge_treatments_canvas` Design-owned edge selection and kernel validation; edit route in `feature_edit.py`; Esc/workbench cleanup
- Tests: `test_fusion_video_workflows.py` fast contracts, `test_workflow.py` FreeCAD native perforated plate geometry and Fillet edit/Undo; wired into CI.

The Fillet panel uses live **kernel validation** and selected-edge highlighting; a ghosted shaded fillet preview inside the 3D viewport has **not** yet been built. In-canvas drag handles, snap behavior, dimensioning and sketch pattern mode still need owner Windows 1.1 GUI acceptance. This batch is source work, not a release or confirmation of installed behavior.

## Release discipline

Existing public v0.5.8 is already published. Do NOT create another v0.5.8 payload; when verified Windows tests and owner acceptance are ready, make a unique version-correct v0.5.8→v0.5.9 incremental patch with checksum-checked pinned baseline, safe rollback, and explicit publication for in-app updater. No large installer or premature same-version artifact.
