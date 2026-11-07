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

- [x] 0.3.6 selected-feature Edit/Delete timeline controls and context actions;
      guarded native leaf/cascade deletion with Undo and cross-body dependency
      refusal; earlier Hole edits with downstream validation and safe rollback;
      native FreeCAD geometry regressions.
- [ ] Owner Windows FreeCAD 1.1 timeline acceptance: double-click edit Hole
      before later Pad, edit native Pad/Pocket from timeline/Browser, delete
      last feature and Undo, confirm blocked single deletion, explicit Delete
      from here and Undo; report layout/selection problems.
- [ ] Fully dependency-aware removal of arbitrary middle features (rewire
      surviving steps with verified support), timeline drag reorder, broader
      native-task dialogs and broken-reference repair.

- [x] 0.3.7 Update Az ribbon/File menu/Utilities command; only successful
      branch CI builds are eligible; SHA-pinned, per-file Git integrity
      checks, temp staging, backup-aware install, no-op current version,
      cancellation/error behavior and offline tests.
- [ ] First owner Windows FreeCAD 1.1 successful in-app update check/upgrade
      over HTTPS, including restart/restore verification and UI feedback.
- [ ] Optional stable release channel and signed manifest/version pinning;
      avoid deploying private or untested development code by default for
      anyone outside this owner-focused review workflow.


## Proposed next UX milestones — owner planning conversation, November 7, 2026

These are **priorities, not completed code or committed release promises**.
Chosen to close the gap with Fusion-style modeling workflows while preserving
native FreeCAD documents, kernel and dependency semantics. Incremental
break/fix with GitHub tests and owner Windows acceptance per release.

1. **0.3.8 — History-first interaction and dependency clarity.** Harden 0.3.6
   timeline selection/edit/delete and actual Windows acceptance. Add a draggable
   Body Tip/rollback marker and clear future/active/suppressed states; expose
   dependency-aware edits and actionable failure messages. Preserve downstream
   topology where supported, but never arbitrarily rewire unstable references.
   Add safe, explicit supported reorder cases only with dependency checks.
   End-to-end acceptance: Pad → Hole → Fillet, edit Pad/Hole upstream and
   return to latest history without unexpected lost solids.
2. **0.3.9 — Contextual sketch workspace / palette.** Right-side Az Sketch
   Palette with grid/snap/show profile/show constraints/show dimensions,
   construction and projected geometry, constraint completeness cues and
   dimension feedback. Keep Sketcher-native solver/constraints. Acceptance:
   plane → rectangle + dimensions → circles + constraints → Finish Sketch
   without losing view/layout; downstream edit updates the solid.
3. **0.4.0 — Coherent feature editing tasks.** Unify on task structure for
   Extrude, Hole, Fillet/Chamfer, Revolve, Shell, Loft/Sweep where FreeCAD native
   capabilities permit; standard preview/OK/Cancel/original/broken-reference
   and in-canvas manipulators. Do not wrap every possible native property
   prematurely. Acceptance: consistent editing on a representative fabrication
   part without workbench switching.
4. **0.4.1 — In-canvas selection and direct manipulation.** Clear hover/
   selection highlighting; contextual actions for face/edge/profile/sketch;
   direct dimension editing, move/rotate controls and viewport handles with
   stable Undo; nonselectable Az grid and native CAD fallback. Acceptance:
   common edits require fewer trips to a property panel.
5. **0.4.2 — Browser and component organization.** Proper tree hierarchy
   for bodies/components/sketches/origin/construction, active body marker,
   reliable visibility/isolate and selection synchronization with timeline
   and viewport, context menus and renamed/suppressed status. Multi-body
   document tests before grouping or component manipulation promises.
6. **0.4.3 — Visual/layout consistency pass.** Unified ribbon icon sizing
   and tooltips, coherent compact right-side task/Sketch Palette, stable
   panel placement, shortcuts, theme/contrast/DPI, and 2D/3D navigation.
   Target familiar interaction rather than cloning branded visual assets.

**Guardrail:** The priority is working history + sketching + feature tasks,
not visual imitation alone. Do not promise drag-reorder/dependency repair
until the specific FreeCAD-native graph and transaction cases pass tests.
Do not advance versions for planning-only changes. 0.3.7 remains the latest
owner-confirmed updater bootstrap; actual network upgrade to a later release
must be tested after the next passing build.

## Consolidated 0.4.0 delivery — November 7, 2026

Owner overrode the six-release schedule: build all major UX work in one
reviewable batch. The source changes cover each area, but not every deep
Fusion feature-parity promise; keep explicit scope distinction.

- [x] Actual Body Tip history scrub slider and referenced-dependency inspector.
- [x] Contextual Sketch Palette with native property capability detection,
      sketch tools and constraint/geometry count.
- [x] Shared native/Az feature edit dispatcher and coherent right-side Tasks.
- [x] Contextual selected-face/edge/sketch/feature actions on the canvas
      and on right-click; parametric Quick Dimension for known types with Undo.
- [x] Body-grouped Browser native feature/sketch hierarchy and active marker.
- [x] Unified ribbon hints, task styling, timeline slider, canvas overlay.
- [ ] Owner Windows FreeCAD 1.1 end-to-end test and real 0.3.7 → 0.4.0 Update
      Az network install followed by full restart.
- [ ] Full native robust dependency-preserving drag reorder/repair of arbitrary
      middle features; do not pretend marker scrub does this.
- [ ] Full custom advanced feature panels and arbitrary in-canvas
      direct-edit handles (native FreeCAD dialogs and existing manipulator
      remain until separately validated).


## 0.4.1 Windows screenshot corrective build — 2026-11-07

- [x] Replace duplicated oversized 0.4.0 right sketch panel with compact
      options-only Sketch Palette; leave native drawing tools/Finish Sketch in
      the top ribbon and native solver/tasks in the right side.
- [x] Real native Sketcher ViewObject controls for grid, auto spacing, auto
      constraints and avoiding redundant constraints; checkable native Snap
      action only when supported; remove dead profile/dimension fake toggles.
- [x] Explicit high-contrast controls; cap sketch-dock height at 210 px,
      shorten timeline, reserve visible space for FreeCAD Tasks; test actual
      control wiring and rejected unsupported settings in CI.
- [x] 0.4.1 Linux package/native modeling CI passed; verified ZIP checksum and
      reran five extracted focused tests.
- [ ] Owner Windows 1.1 acceptance: same screen shows full Sketch Tasks and
      bottom timeline; checkbox text readable; grid toggles visibly; Auto
      constraints affects geometry drawn after enabling; native Snap, if
      available, affects drawing cursor.
- [ ] Audit true Fusion-like sketch task layout further based on actual
      Windows 0.4.1 screenshots; avoid duplicating native interface without
      functional benefit.


## 0.4.2 Qt6/Extrude cross-Body fixes — November 7, 2026

- [x] Fix PySide6 `StandardButton` `int()` TypeError for Az Extrude and Hole.
- [x] Declare FreeCAD global-scoped Extrude source/end-face/frame links across Bodies.
- [x] Repair old link types when editing within FreeCAD transaction, retaining
      Cancel/Undo and not silently rewriting reopened FCStd files.
- [x] Add Qt5/Qt6 mask regression and native cross-Body + legacy migration tests.
- [x] Exact final combined CI pass (42377682997: package + modeling) and
      artifact integrity verified (13576123483; 0.4.2 CRC/SHA256 passed).
- [ ] Owner Windows FreeCAD 1.1 acceptance on 0.4.2 via in-app Update Az;
      create new Extrude from Body-owned sketch, edit/re-save old Extrude,
      confirm both reported errors no longer reproduce.
