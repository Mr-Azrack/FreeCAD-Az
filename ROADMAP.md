# FreeCAD-Az — capability roadmap

**Goal:** an independently developed, FreeCAD-based CAD workflow comparable to Fusion 360 in daily use, not a lookalike skin. Ordered below by user value and engineering dependencies. Scope is ambitious; a check is complete only with evidence.

## Stage 0 — Functional foundation (implemented on feature branch; owner sign-off pending)

- [x] Az Design workbench, grouped modeling ribbon, search, contextual shortcuts.
- [x] Browser/Tasks layout and creation-order history strip.
- [x] Native sketch → Pad and sketch → Pocket with preview/cancel transactions.
- [x] Installer, backup/recovery code, packaged v0.1 ZIP.
- [x] Linux FreeCAD 1.0 integration test evidence recorded in repository.
- [ ] Owner acceptance in real shop usage; Windows validation; CI state reconfirmed.

**Exit:** install on the intended Windows workstation, create/edit/save/reopen a parametric test part, undo/redo reliably, and retain native FreeCAD behavior after switching workbenches.

## Stage 1 — Everyday modeling speed and correctness (next)

- [ ] Select individual closed profiles and multiple regions inside sketches for extrude/cut.
- [ ] Unified sketch workflow: constraints, dimensions, projected geometry, construction geometry, trim, feedback, and dependable edit/finish behavior.
- [ ] Context-aware selection and commands; predictable right-click and keyboard behavior.
- [ ] Common solid tools with coherent Az UI: true Press/Pull, revolve, hole, patterns, mirror, shell, draft, fillet/chamfer, and Boolean operations.
- [ ] Robust negative/edge cases: disconnected solids, invalid profiles, failed recomputes, and transaction recovery.

**Exit:** independently complete a documented representative shop-part benchmark without frequent workbench changes, preserving a fully editable native feature tree.

## Stage 2 — Parametric feature history and UX parity

- [ ] Dependency-aware feature history with edit, rollback, suppression, and safe recompute semantics.
- [ ] Selection breadcrumbs, context toolbar, component/body organization, visibility/isolate, and fast navigation.
- [ ] Recovery/diagnostics for invalid references and broken downstream features; regression tests.
- [ ] Measure workflow speed and interaction count against agreed reference tasks (not just visual resemblance).

**Exit:** parametric edits propagate correctly through history, rollback is reversible, and round-trip native FreeCAD data survives.

## Stage 3 — Production mechanical design

- [ ] Multi-body/component workflows and assembly integration strategy.
- [ ] Practical drawings/annotation, exports, stock/material conventions, and reuse of shop templates.
- [ ] Performance and reliability testing on larger documents and repeated edit cycles.
- [ ] Windows, Linux, macOS support strategy with CI and packaging coverage.

**Exit:** real fabrication parts and assemblies, documented tolerance/drawing/export workflow, release and regression evidence.

## Stage 4 — Manufacturing/CAM workflow

- [ ] Map current FreeCAD CAM capabilities and gaps against Fusion-style setup/toolpath/post workflow.
- [ ] Add streamlined setup, operation parameters, simulation, post handling, tool libraries, and stock visualization as validated.
- [ ] Add integration/safety tests for toolpath generation, machine limits, units, retracts, and post outputs.

**Exit:** verified end-to-end example from design through simulation and machine-compatible output, with independent inspection before cutting metal.

## Per-stage rules

- Each feature requires an acceptance scenario, tests, expected environment, and commit/PR evidence.
- Keep roadmap boxes unchecked until implementation and verification exist.
- Reprioritize based on actual user workflows, not speculative visual polish.
- Update PROJECT_STATE.md and SESSION_HANDOFF.md at each completed milestone.
