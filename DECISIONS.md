# FreeCAD-Az — decisions and constraints

## Accepted product direction

1. **Own the platform.** Build on open-source FreeCAD and maintain an editable fork/add-on rather than relying on an unmodifiable proprietary CAD product.
2. **Fusion 360-like workflow is the goal.** Familiar sketching, modeling, editing, history, navigation, component and manufacturing workflows are required. No cosmetic-only substitute is accepted as the endpoint.
3. **Full ambition, verified increments.** Work toward comprehensive parity, but label each partial release and its unimplemented features truthfully.
4. **Independent implementation.** Use FreeCAD-native geometry and document infrastructure; do not copy Autodesk source, branding or artwork.
5. **GitHub is authoritative continuity.** After timeout or memory loss, reconstruct from actual branch HEAD, history, local diffs and test evidence. Update and commit the four continuity files at milestones.
6. **Do not throw away work.** No blind reset, unreviewed overwrite or force push after session recovery.
7. **Human review and evidence.** Respect licenses and FreeCAD AI_POLICY.md, disclose AI assistance, record testing truthfully, and retain owner review.

## Recorded implementation decisions

- **v0.1:** Optional FreeCAD Python workbench provided familiar UI and native Pad/Pocket-based sketch-to-solid operations, plus a reversible installer. Original v0.1 files remain editable without Az Design installed.
- **v0.2:** Extend that workbench with custom parametric Az extrusion features built using FreeCAD's Pad/Pocket and OCCT algorithms, selected exact sketch regions, viewport manipulators, parameter expressions, supported Press/Pull, and real history rollback/suppression.
- **v0.2 compatibility consequence:** Custom feature recomputation/editing requires Az Design installed; cached FCStd shapes and STEP exports allow independent consumption. Do not misrepresent these as pure native Pad objects.
- Use small, independently verified Git commits and preserve the installation/test artifacts and evidence. Keep the CAD work on a reviewable feature branch while draft PR #1 remains open.

## Open architecture decisions (not commitments)

- How far history reordering, advanced dependency repair, direct geometry editing and arbitrary face offsets can go without FreeCAD core modifications.
- Exact supported platform/version matrix and Windows packaging/release strategy.
- Full workflow benchmark criteria for sketching, components/assemblies, drawings and CAM.
- Whether advanced CAM needs only UX integrations over native FreeCAD CAM or a substantial dedicated interface.

For each new accepted decision record date, rationale, alternatives and compatibility/test impact. A design idea is not a decision until grounded in implementation or user instruction.

## Engineering rationale from the implementation session — 2026-11-05

- Stable Az FeaturePython identity allows Join/Cut/Intersect edits without swapping
  object classes. Geometry remains exact native Pad/Pocket/OCCT; keep the add-on
  installed to recompute. This is a compatibility tradeoff, not pure-native Pad storage.
- Reuse an Undo-disabled, hidden temporary GUI calculation document. Closing one
  per preview committed FreeCAD's application-wide edit transaction and broke Cancel.
  Keep the user transaction persistent until OK/Cancel and cancel it on workbench exit.
- Transfer exact geometry through BREP to remove calculation-document topology IDs;
  this fixed native downstream Fillet on dimension changes. Topology changes can
  still require native face/edge reselection; no full topology-repair claim is made.
- Coin owns native viewport dragging; a Qt timer transfers its field values. The
  shipped Pivy remove*Callback path reproducibly segfaulted, so that API is avoided.
- Supported Q edits preserve recognized driving dimensions and refuse unsafe
  arbitrary surface offsets. History insertion preserves explicit source references
  and rejects branching rather than silently changing downstream design intent.

## Startup module boundary — 0.2.1

Keep Init.py and InitGui.py as import-only entry glue. FreeCAD executes these
scripts without guaranteeing `__file__` or a stable shared namespace. Define the
workbench and locate its resources in the normally imported package module.
Do not fix this by hard-coding a user directory or assuming one FreeCAD version's
Mod path. CI now tests the actual missing-file/separate-namespace startup contract.

## Visible modeling context — 0.2.2, 2026-11-05

Treat the active Gui document with a view as the modeling context. App-only
calculation documents must never receive user sketches/bodies/parameters.
Create Sketch and New Body create a normal visible Design if needed. Reuse an
existing visible design and synchronize App activation. This fixes the first-use
failure without requiring the owner to manually create a document or closing the
persistent calculation document, which would break transaction cancellation.
Use App.activeDocument() to preserve the native pointer; its Python module
attribute can remain stale after setActiveDocument(""). Tests model that split.

## Repo-owned workspace frontend — 0.3.0, 2026-11-06

The owner explicitly permits core/fork changes and wants the work area to look
and behave like familiar Fusion workflows. Own the surrounding Qt workspace while
retaining FreeCAD's native geometry, documents, selections and transactions. Use
public native UI APIs where sufficient; change core code when a real boundary
requires it. The module installer is a delivery mechanism for the repo-owned
frontend, not a limit on scope. A complete Windows fork build is unnecessary for
the present layout changes.

Use grouped bodies/sketches in the Browser and ordered features in the timeline.
Keep native task semantics and save confirmations. Keep sketch edit colors readable
on the light canvas, and restore changed preferences/styles when leaving Az.
Scene grid decoration must not become saved/exported document geometry or enlarge
Az Home/Fit. Idle Solid radial tools must preserve native sketch/task cancellation.
Artwork is original SVG generated by tools/generate_az_icons.py; no Autodesk
artwork or code is copied. Timeline controls operate actual Body Tips; label their
first position as First solid rather than imply an unsupported empty-history state.
