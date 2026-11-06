# FreeCAD-Az — workflow parity roadmap

**Destination:** an independently maintained FreeCAD-based workflow comparable to Fusion 360 in real fabrication use. Incremental work must be shippable, reviewable and testable; the visual appearance alone is not the acceptance test.

## Stage 0 — Functional modeling foundation (implemented; platform sign-off pending)

- [x] Az Design ribbon, search, contextual shortcuts, Browser/Tasks UI and navigation restoration.
- [x] Initial native Pad/Pocket sketch-to-solid and installer/backup with released v0.1 package.
- [x] v0.2 selected exact sketch regions, compound sketch geometry, interactive preview, Join/Cut/Intersect/New body, viewport distance handles and multiple extents.
- [x] v0.2 supported Press/Pull, parameters via native spreadsheet, Body Tip rollback and suppression, saved parametric Az features.
- [x] Recorded Linux FreeCAD 1.0.0 geometry and GUI validation for v0.2.
- [x] Confirm add-on native modeling and package CI for v0.2 (run 42100114683).
- [x] Reproduce and fix the Windows-reported missing `__file__` startup error in 0.2.1; add startup regression CI.
- [x] Reproduce and fix Create Sketch with no visible document in 0.2.2; validate automatic document creation, hidden calculator separation, and existing GUI workflows. Add-on CI run 42165160134 passed.
- [ ] Owner acceptance and full Windows/FreeCAD 1.1 integration and document round-trip using 0.3.2.

**Gate:** reproduce a representative shop part on the intended Windows machine and confirm save/reopen, Undo/Redo, export, Az/native feature interoperability, cancellation and install/upgrade/rollback.

## Stage 1 — Reliable everyday CAD speed (active)

- [x] 0.3.0 workspace layout and visuals: top design tabs, grouped Browser, light canvas/readable sketches, compact timeline, navigation/display controls and idle Solid radial tools; 85 desktop checks passed on Linux; add-on CI 42231553398 passed native modeling/package checks.
- [x] Owner gave positive 0.3.0 visual feedback; requested default-visible grids.
- [x] 0.3.1 uses modern extrusion sides where available, restores native Boolean preferences, and shows persistent modeling/sketch grids by default. Add-on CI 42237616994 passed.
- [ ] Full owner workflow acceptance on Windows/1.1, including DPI and Qt version.
- [ ] Expand sketch constraints/dimensions and context-aware profile selection; measure time and clicks versus familiar Fusion workflows.
- [x] 0.3.2 Az-managed native Hole UI for diameter, depth, through-all and cosmetic threads; preview/rollback; Linux FreeCAD 1.0 native and offline checks passed.
- [ ] Windows/1.1 visual and workflow sign-off for Hole, save/reopen, STEP and compatibility.
- [x] 0.3.3 explicit experimental modeled/helical thread opt-in, fsynced pre-crash logs and disposable probe macro; real kernel crash path excluded from CI.
- [ ] Reproduce Windows FreeCAD 1.1 modeled thread failure using the isolated 0.3.3 probe; analyze checkpoint and (if needed) C++ crash dump, fix root cause, then test production-safe geometric threads.
- [ ] Consistent Az task UI for remaining native dialogs: Revolve, Fillet/Chamfer, Shell, Loft, Sweep, patterns and mirror.
- [ ] Improve selection feedback, failures, reference recovery, multi-body operations and ergonomics for real parts.
- [ ] Extend Press/Pull to more safely identifiable solids and surfaces without silently changing design intent.
- [ ] Test realistic design scenarios including feature edit propagation, unit conversion, invalid profiles, and repeated undo/redo.

**Gate:** a documented set of fabrication parts can be designed and revised without frequent workbench switching; failures are recoverable.

## Stage 2 — Feature-tree and design management

- [x] Supported Body Tip rollback, suppression, history insertion and restoration (v0.2).
- [ ] Full dependency-aware edit/reorder behavior, clear rollback boundary, robust broken-reference diagnostics and repair.
- [ ] Assembly/component/body organization, selection breadcrumbs, visibility/isolate and design-history usability at scale.
- [ ] Performance tests on multi-component files and downstream reference stability.

**Gate:** complex models update predictably without unintentional topology or history corruption.

## Stage 3 — Mechanical production capability

- [ ] Validate drawings, annotations, dimensions/tolerances, templates and exports for shop use.
- [ ] Assembly and joint workflows and reuse of common shop components.
- [ ] Platform matrix: Windows, Linux, macOS / supported FreeCAD and Qt versions, release packaging and automated regression coverage.

**Gate:** repeatable fabrication workflow from editable design to usable production deliverables.

## Stage 4 — Manufacturing / CAM

- [ ] Map native FreeCAD CAM versus target setup, operation, library, simulation, post and stock workflows.
- [ ] Implement coherent Az manufacturing UI as needed, with post output inspection, limits, units and safe retract tests.
- [ ] Verify representative parts from CAD through independently reviewed machine-compatible toolpaths.

**Gate:** actual end-to-end CAD/CAM use case proven with simulation and independent toolpath review before machining.

## Rules

- A checked item means implemented with repository-backed evidence; it does not imply all edge cases are covered.
- Do not mark Windows or future Fusion parity complete on Linux tests alone.
- After each milestone update PROJECT_STATE.md, DECISIONS.md if relevant, and SESSION_HANDOFF.md with branch, commit, tests and remaining work.

- [x] 0.3.4 modeled Hole editing path removes stale geometric-thread refusal,
      preserves initial thread state, avoids unchanged recompute and retains
      transactional Cancel; native/cosmetic regression coverage added.
- [ ] Owner Windows/FreeCAD 1.1 acceptance for **edit existing modeled Hole**:
      change thread size and depth, preview, cancel/accept, save/reopen; capture
      actual error traces if another failure occurs.

- [x] 0.3.5 compact Hole UI (Placement/Geometry/Thread), readable standard
      labels, native-derived diameter control, immediate thread-size options,
      reversible source selection before preview, safe 350 ms plain/cosmetic
      live previews and headless UI/policy regression tests.
- [ ] Owner Windows/FreeCAD 1.1 acceptance of 0.3.5 task arrangement, live
      preview, source switching and unchanged modeled threads.
- [ ] Continue incremental Fusion-like interaction polish on other daily
      tools, preserving FreeCAD-native geometry, transactions and diagnostics.
