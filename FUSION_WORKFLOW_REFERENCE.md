# Fusion 360 workflow reference — owner's plate demonstration (2026-11-10)

Source: user-supplied video `Untitled - Autodesk Fusion Personal (Not for Commercial Use)  2026-11-10 18-00-40.mp4`, ~222.8 seconds, 1920×992. This is a behavior/reference observation; preserve original FreeCAD file compatibility and design original UI assets rather than copying proprietary assets.

## What was directly visible

| Approx. time | Observed interaction/result | Design implication |
| --- | --- | --- |
| 0:00–0:30 | Clean canvas; transition into top-oriented grid and a rectangular plate sketch with dimensional annotations | Direct face/plane sketch entry, stable top view, visible live dimensions, no disruptive native mode changes |
| 0:30–1:50 | Initial circle positioned by dimensions; repeated circle positions appear in two columns, including a longer lower group | In-sketch pattern must be usable for actual hole geometry, clear source and spacing semantics, editable constrained results, stable viewport |
| 1:50–2:30 | Sketch completes into a real plate with through-holes; raised rectangular geometry is sketched on the plate | Finish Sketch must immediately enable downstream Extrude/Hole operations without moving into a different native UI |
| 2:30–3:40 | Raised shape becomes a solid, model is orbited and viewed from top/side/isometric; edges are rounded by later operations | Features remain editable in ordered history; selection/orbit and preview shouldn't bury model; native geometry kernel remains source of truth |
| Throughout | Context ribbon differs between Sketch and Solid; bottom timeline shows recognizable, fixed-size **icons** plus a history cursor, not tiny text abbreviations | Replace Design timeline abbreviations with original vector/icon images and responsive hit targets; preserve tooltips and contextual editing |

The video is not a complete capture of the Fusion rectangular pattern settings panel. Do **not** infer exact dialog settings, controls or unobserved behaviors from it. The user's stated acceptance requirement remains the authority: Design must own pattern selection, preview, parameters and edits; native FreeCAD task panels are implementation leaks.

## Design functional acceptance contract

1. **Sketch:** Select planar face or origin plane directly and enter Design sketch context; draw and dimension rectangle/circle; infer endpoints/midpoints/centers without disruptive modal dialogs.
2. **Sketch Rectangular Pattern:** Select actual sketch circle(s); 2×2 and larger grids with X/Y instance counts and pitch; intuitive in-canvas direction handles with synchronized Design controls; source and copies real, solver-constrained, editable; Finish Sketch → Hole must produce all holes in one valid feature.
3. **Solid Linear Pattern:** Fully Design-owned workflow for Pad, Pocket and Hole feature(s): selection from canvas or Browser, axis/direction choice, occurrences, spacing/extent, temporary visual preview, cancel with no mutation, accept with valid native PartDesign transformation; no escape to stock FreeCAD task controls.
4. **Feature timeline:** Stable 18–24px original SVG/vector icons or raster-rendered assets for Sketch, Extrude, Cut, Hole, Pattern, Fillet etc. Consistent 28–36px click targets, DPI-independent layout, selected/hover state, tooltips. No single-letter/text abbreviations occupying timeline. Double-click edit, context menu, rollback marker and Undo/Redo remain functioning.
5. **End-to-end:** Open owner's actual FCStd or create similar plate, add multiple hole rows via Pattern, Extrude/Hole/cut, add upper pad and fillets, revisit source sketch/Pattern from timeline, modify pitch/diameter/count, recompute a valid single solid, save/reopen with history intact. Protect old model and support rolling back a failed operation.

## Priority / batch boundary

Implement together as one coordinated pattern-and-timeline **UX batch** rather than one micro-fix per patch: (a) Sketch canvas pattern handles, (b) fully owned Solid Pattern selection and task/preview, (c) fixed-size image-icon timeline, (d) edit/undo/redo/recompute regression, (e) actual Windows acceptance recording. Fast package + FreeCAD geometry CI before Windows candidate; don't run expensive patch on every commit. Avoid changing public release state during source iteration.

## Status

This is **reference-analysis and acceptance criteria only**, not an assertion that the functions have been implemented or Windows-tested. Prior v0.5.7 candidate status is separate from the next UI batch.
