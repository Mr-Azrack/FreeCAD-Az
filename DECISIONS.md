# FreeCAD-Az — decisions and constraints

Record choices here only when supported by user direction or observed implementation. Proposals below are explicitly marked.

## Accepted direction

1. **Own the platform.** Extend the open-source FreeCAD codebase/workbench so the experience can be changed as needed; do not depend on an unmodifiable proprietary CAD product.
2. **Target Fusion 360-like modeling workflow, not a theme.** Usable sketch creation/editing, feature generation, navigation, browser, history, and eventually mature workflow coverage are required. The current Az Design add-on is an initial milestone, not the finish line.
3. **No false parity claims.** Pursue the full long-term experience while shipping verified, recoverable increments with clearly stated gaps.
4. **Use native FreeCAD parametric geometry and FCStd files.** Keep files editable in standard FreeCAD rather than replacing the geometry kernel with an incompatible representation.
5. **Independent design.** Familiar interaction patterns are appropriate; no copied Autodesk source, icons, branding, or protected assets.
6. **GitHub-first continuity.** Repository history and checked-in state are authoritative after any Work interruption. Keep PROJECT_STATE.md, DECISIONS.md, ROADMAP.md, and SESSION_HANDOFF.md current and commit milestones.
7. **Source-backed engineering.** Run and record tests, environment, outcomes, and affected commits. Distinguish reported results from fresh execution. Preserve and inspect uncommitted work before recovery.
8. **Human oversight.** Keep work reviewable, observe upstream FreeCAD licensing and AI_POLICY.md, and do not treat assistant-produced changes as upstream-approved.

## Current implementation decisions (observed)

- The first milestone is an optional Python FreeCAD workbench in addons/AzDesign, avoiding a full application rebuild at this stage.
- Use native PartDesign Pad/Pocket and existing FreeCAD facilities for sketches, selections, feature storage, and CAD/CAM interoperability.
- Treat the feature-history strip as a browse/edit history for v0.1; no pretend timeline rollback.
- Ensure install/upgrade/rollback and restoration of prior UI/navigation settings are testable.

## Not yet decided / require evaluation

- Whether advanced timeline rollback/reordering requires core changes, a more capable workbench architecture, or both.
- Exact constraints and acceptance metrics for Fusion workflow parity across sketching, solids, assemblies, drawings, CAM, and performance.
- Windows production installer/distribution strategy and supported FreeCAD version matrix.
- Scope of future CAM integration and whether it remains native FreeCAD CAM or gains an Az-specific interface.

Document new decisions here with a date, rationale, alternatives, and test consequences; do not silently turn a proposal into a commitment.
