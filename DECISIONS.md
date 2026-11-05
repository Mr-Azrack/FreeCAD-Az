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
