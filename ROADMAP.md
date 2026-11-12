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


## 0.4.3 Extrude profile selection video regression — Nov 7, 2026

- [x] Review owner Windows eight-second recording and identify blanking
      Body during implicit pick mode, failed preview leaving empty Tip.
- [x] Stop auto-entering pick mode on multi-profile sketches; require user
      check/select region without hiding existing part.
- [x] Block recompute timers while selecting, and skip geometry evaluation
      for zero selected sketch regions.
- [x] Restore original Body Tip/visibility/solid after failed new Extrude
      and allow same task to continue with a different profile.
- [x] Native FreeCAD and headless UI regressions added to model/CI workflow.
- [x] Verified native AND package CI 42411861600; artifact 13590115605
      contains 0.4.3 ZIP (221,092 bytes), CRC and SHA256 verified.
- [ ] Owner Windows 1.1 acceptance: multiple profiles, no selection, invalid
      Join and change direction/region; existing threaded part always visible
      when no valid preview exists; no repeated empty-Tip message.
- [ ] Separately inspect persistent TopoShape hasher mismatch messages if
      present after invalid preview cleanup; not covered by this fix.


## Az 0.5.0 single functional fixture milestone — 2026-11-08

- [x] Native Sized Rectangle command in SKETCH CREATE with width/height
      driving constraints, repeatable parametric edits and Undo grouping.
- [x] Preflight new Join/Cut/Intersect against actual Body geometry before
      creation; disconnected or no-material options cannot take the Body Tip.
- [x] Validate downstream actual solid Shapes and errors before committing
      edited earlier Extrude.
- [x] Native FreeCAD full fixture test: parametric plate, pocket, two Holes,
      Fillet, upstream sketch dimensions, Hole edits/Cancel, Undo/Redo,
      FCStd save/reopen and Body Tip/volume verification.
- [x] Native tests for no-op/disconnected operations with unchanged document.
- [x] Native upstream Extrude edit with later Fillet plus Cancel regression.
- [x] Final CI run 42450344286 passed both native modeling and package;
      artifact 13604909908 ZIP/CRC/0.5.0 version and SHA256 verified.
- [ ] Windows FreeCAD 1.1 0.4.3 → 0.5.0 update using Update Az, full restart
      and owner's GUI modeling acceptance.
- [ ] Production-level topology change/face-reference repair for arbitrary
      middle-history reorder; universal drag dimensions and advanced native
      feature task parity still not implemented.


## Az 0.5.1 / native Sketcher inference stage — 2026-11-08

- [x] Micro-scale exact OCCT Fillet/Chamfer preflight, selected-edge
      diagnostics and native PartDesign commit/rollback.
- [x] Actual native tests of small valid/invalid edge treatments, Undo.
- [x] Automatic in-sketch marker for line midpoint triangle, endpoint
      square and circular/arc center under hover, no manual tool required.
- [x] Tests for line/circle/arc inference and passive Qt viewport marker;
      no native drawing event is swallowed.
- [x] Optional exact XYZ center finder demoted to Utilities inspection.
- [x] Pin and stage FreeCAD 1.1.0 C++ `SnapManager` patch allowing
      rim-to-center click in native Sketcher when opted in; Alt bypass.
      Patch hunks matched 1.1.0 source but **not compiled**.
- [x] Both jobs in CI 42454414615 passed; artifact 13606378238
      contains AzDesign-0.5.1.zip (246,212 bytes), CRC and SHA256
      verified. Owner installation and Windows acceptance remain pending.
- [ ] Owner Windows FreeCAD 1.1 GUI confirmation that hover markers render
      at the correct coordinates, native snap/constraints are usable, and
      the small-geometry Fillet/Chamfer dialog behaves.
- [ ] Build a separate signed Windows FreeCAD-based application with native
      1.1.0 SnapManager patch; test automatic rim-click redirection with
      Alt bypass and ordinary point-on-rim commands; never replace the
      installed stock FreeCAD version.


## Az Native Windows standalone application — 2026-11-08

- [x] Identify official FreeCAD 1.1.0 source/Pixi Windows build workflow
      and pinned dependencies, use Windows 2022 + VS2022 in CI.
- [x] Implement independent, opt-in source patch against C++ Sketcher
      SnapManager, preserving Alt bypass and native geometry.
- [x] Verify patch applies to upstream FreeCAD 1.1.0 on Linux; correct
      upstream CRLF handling for Windows source/diff checks.
- [x] Implement guarded portable packager: compiled GUI, Sketcher, Az
      workbench, Qt/Python dependencies, license files, integrity
      manifest and isolated Windows user profile.
- [x] Add four locally passing packaging safety tests and CI gate.
- [ ] Windows native C++ compilation and installation must finish
      successfully; inspect CI `42488030121` and fix any new dependency,
      compiler or packaging failures.
- [ ] Verify compiled binary actually launches with Sketcher + AzDesign
      on Windows; test circle-rim -> center with Alt bypass and existing
      line/arc snapping on real GUI.
- [ ] Upload checksum-verified native portable preview, provide download
      only after verifiable artifact, not merely CI workflow success.
- [ ] Later: branded executable/UI, Windows application updater and
      signed installer when tested; do not ship production machine CAM
      until dedicated safety checks exist.


## 2026-11-09 — Standalone Qt plugin launch repair

- [x] Reproduce failure cause from first native archive layout:
      qwindows.dll in lib/qt6/plugins/platforms, launcher targeted
      nonexistent bin/platforms.
- [x] Windows CI repair run 42560734235 extracted previous compiled
      artifact and passed real bundled QApplication('windows') smoke.
- [x] Verified QuickFix 411,824-byte ZIP, CRC, SHA256
      bf85e6284b5e74b32d482645ccdc991c9d815585917981d61a4f6c5284c85095.
      Artifact 13648924049, user given drop-in download.
- [x] Future full native packages require matching qwindows.dll, qt.conf
      and actual QApplication launch test (no more false-green package).
- [ ] User tests patched `Az Design.cmd` on Windows and verifies Az Design
      workbench loading, Sketcher Circle snap and Alt override.
- [ ] Verify new full Windows native CI run (separate from quick-fix CI)
      produces startup-smoked portable archive, then publish new full
      preview only after artifact and SHA are confirmed.


## Native 0.5.2 installed-app and delta-patch milestone — November 9

- [x] User confirmed original repaired native Windows app launches and
      native C++ circle-edge-to-center snapping works.
- [x] Native `AzDesign.exe` launcher with independent Qt/user profile.
- [x] Native `AzUpdater.exe` GUI with patch selection/rollback.
- [x] Inno Setup per-user Windows installer, Start Menu app+updater,
      optional desktop shortcut and Windows Installed Apps/uninstall.
- [x] Versioned changed-file ZIP generator, SHA256 verification, safe
      paths, transactional PowerShell apply, previous-version rollback.
- [x] Windows tests for changed/add/delete, mismatch rejection and
      rollback passed in CI runs 42613250797 and 42613707498.
- [x] Fix clipped 32px navigation/history/Browser buttons by icon-only
      layout and short fallback glyphs; Windows owner acceptance pending.
- [ ] Inno Setup 0.5.2 real installer run 42613707498: confirm final
      setup compilation, silent install, Start Menu, full Qt GUI smoke,
      silent uninstall and uploaded verified `.exe` artifact.
- [ ] Owner installs setup on Windows, confirms Start Menu, optional
      desktop shortcut, Installed Apps/uninstall and correct layout.
- [ ] Publish versioned delta patches and remote update feed so
      `AzUpdater.exe` can **check/download** automatically; currently
      it opens a patch ZIP explicitly and can roll back.
- [ ] Later signed binaries/installer, branding/icon improvements,
      patch channel/certificate policy and Windows DPI tests at
      100/125/150 percent.


## Design-first command and document routing (2026-11-09)

- [x] Rename visible workbench/menu and Find a Tool presentation to **Design**; retain internal Az identifiers for compatibility.
- [x] Remove raw PartDesign feature task commands from the main Design Solid ribbon and Find a Tool results; retain Native CAD explicit escape.
- [x] Add command whitelist/blocked raw-feature guards and CI command-boundary regression test.
- [x] Add document observer for Home → new ordinary model → Design; preserve reopened file saved workbench and specialized CAM context; headless regression tests pass.
- [ ] Pass current full add-on packaging/modeling CI after correcting first discovered Revolve command escape; verify Windows native app integration.
- [ ] Add Design-owned replacement task panels for Revolve, Loft, Sweep, Shell, Mirror, Patterns, Move, and Measure, with native parametric semantics and tested Undo/Redo/Cancel.
- [ ] Owner Windows acceptance for Home, new models, reopened Design/CAM files, and active task preservation; investigate imported non-FCStd formats individually.


## Native one-click update 0.5.3 — November 9

- [x] Design Update button invokes installed AzUpdater.exe when running the native Windows app.
- [x] Native GUI Check for Updates and verified GitHub Release digest-pinned download path; manual ZIP and rollback preserved.
- [x] CI source wiring for .NET Framework compiler, offline metadata rejection tests and genuine installed-baseline delta/Qt/rollback.
- [x] Manually gated GitHub Release promotion workflow, no automatic release of unreviewed development code.
- [ ] Verify all 0.5.3 Windows CI jobs and uploaded patch artifact SHA256; repair any failures.
- [ ] Approve publishing exact verified patch as GitHub Release. Workflow must be available on default branch.
- [ ] Owner bootstrap using existing Native - Update manual patch selector, restart, then test Design Update → Check for Updates and rollback.
- [ ] Longer term: support chains/multiple installed baselines, no-release behavior, signing/trust beyond GitHub digest, and stable release channel.


## 0.5.4 UI readability patch

- [x] Update Windows installer workflow to 0.5.4 with original 0.5.3 run 42752856389 as baseline.
- [x] Versioned 0.5.3→0.5.4 archive names and remote release metadata tests.
- [x] Add baseline setup SHA256 verification before patch creation.
- [x] Update manual public release promotion workflow to expected 0.5.4 patch.
- [ ] Confirm full Windows patch-tests, actual patch/Qt/rollback, installer/uninstaller, uploaded artifact and hashes pass in current CI.
- [ ] After approval, publish 0.5.4 release and verify Design's Check for Updates discovers/downloads it.
- [ ] User Windows visual acceptance for larger ribbon, history/browser text and Quick Start version.


## Windows CI speedup (2026-11-10)

- [x] Implement separate routine native patch-only workflow with old/new allowlisted `Mod/AzDesign`, updater executable, patch applicator overlays.
- [x] Skip separate compiled FreeCAD core download/extract and full Inno Setup build/upload on routine PRs; full installer remains manually available.
- [x] Verify original 0.5.3 installer SHA256, real patch apply, Qt startup, rollback, uninstall, and output patch SHA256 in fast path source.
- [x] Update 0.5.4 release-promotion gate to require successful patch-only CI.
- [ ] First patch-only Windows CI run 42818046881 must pass; resolve any errors before declaring optimized pipeline validated.
- [ ] Publish 0.5.4 only after approved successful run; owner visually validates readable labels/history and help version.
- [ ] Consider separately content-addressed old-file baseline cache to remove original installer download safely once Windows byte-for-byte baseline identity is proven.


## Native Design Home — 0.5.6 candidate

- [x] Add Design-specific welcome view with New Design/Open File actions and clear modeling shortcuts.
- [x] Remove eager blank-model creation on activating Design; overlay hides on document open and is cleaned up when leaving Design.
- [x] Signal ordinary native launcher startup to select Design; preserve explicit CAD file arguments.
- [x] Differentiate native navigation orbit/pan/zoom/view icons rather than generic fallback glyphs.
- [x] Extend Qt smoke to construct Design Home and validate New/Open widgets.
- [x] Stage a pinned 0.5.5→0.5.6 patch pipeline by reconstructing 0.5.5 from verified 0.5.4 installer+0.5.5 delta; include recompiled native launcher.
- [ ] Confirm add-on CI, real Windows patch installation/Qt smoke/rollback and GUI launch behavior; repair as needed.
- [ ] Publish 0.5.6 in the controlled release channel after passing verification; visual owner acceptance for Home and icon legibility.


## 2026-11-10 practical-part acceptance testing (owner recordings)

- [x] Implement nonmodal sketch-plane chooser: choose XY/XZ/YZ directly within canvas, or click a planar model face, Cancel/Esc without creating a sketch
- [x] Route Esc to active native Sketcher viewport when Design ribbon stole focus; retain existing nav-mode cancel and picker cancel
- [x] Remove obstructive viewport Activate/Isolate strip; retain selection actions through Browser/context menu
- [x] Provide separate Home control next to FreeCAD 1.1 navigation cube
- [x] Draw recognizable top ribbon New/Save/Undo/Redo/Find/Help icons rather than letters
- [x] Avoid empty Cut task without an existing solid; auto-select lone valid unused sketch for Extrude
- [x] Add visible checked radio style scoped to native Preferences controls
- [x] Add Windows patch CI Python compileall step
- [ ] Validate the full native GUI behavior in Windows: picker face observer, Esc Rectangle exit, Preferences checked radio indicator, Home button position, and valid first extrusion. Resolve regressions before release
- [ ] Resolve why GitHub commit-workflow run lookup is returning no runs for latest branch SHA; don't claim patched build exists until verified


## 2026-11-10 — next real-part acceptance targets

- [x] Make Solid Move visible and implement native reversible Body/component XYZ placement (not individual unsupported feature relocation)
- [x] Put Hole on Solid ribbon and support select-face → auto sketch hole centers → Finish Sketch → editable native Hole settings; add nonmodal face selection for Hole-first flow
- [x] Fix Sketch Project native command name for FreeCAD 1.1: `Sketcher_Projection`, replacing disabled legacy `Sketcher_External`
- [x] Permit Create Sketch from a selected edge when exactly one adjacent face is planar; require user face choice when ambiguous
- [x] Provide temporary Show/Hide constraint label control without altering solver or geometry
- [x] Add guarded Design-native single-feature Mirror/Linear Pattern task paths with native parametrically linked features and rollback
- [x] Update catalog command boundary test and add native transformation contract tests to package CI
- [ ] Windows GUI integration tests: hole-face picker/center sketch continuity, Mirror/Pattern with real native FCStd (two pads/one pocket), Move Undo/Redo, projected edge selection, visibility toggle and existing features after edit
- [ ] Improve sketch dimension label positioning, duplicate/ref-vs-driving clarity, over/underconstrained guidance; screenshot still shows overlap and remaining 2 DoF
- [ ] Confirm fresh 0.5.5→0.5.6 Windows patch CI success and artifact, then controlled official release; currently no verified fresh run surfaced


## 2026-11-10 — Build process streamlined for integrated 3–6 issue batches

- [x] Keep fast add-on/modeling tests on trusted branch pushes for rapid feedback
- [x] Stop automatically running expensive Windows native patch CI on every small edit/PR update
- [x] Add explicit release-candidate marker trigger for version 0.5.6 and retain manual workflow entrypoint
- [x] Add headless add-on regression checks as an early Windows patch gate before downloading the pinned baseline
- [x] Document batch scope, severity exceptions, same-SHA release verification, and GitHub-first continuity in `BATCH_VALIDATION.md`
- [ ] Finish current sketch/Hole/Move/Mirror/Pattern integration batch, resolve all currently failing add-on test contracts and obtain fast green CI
- [ ] Commit candidate marker with reviewed exact SHA and scope; verify Windows patch and Qt/rollback tests, then perform owner GUI acceptance before manual publication


## 2026-11-10 — 0.5.7 integrated correction batch

- [x] Fix delayed Design Home activation NameError from FreeCAD exec loader dropping globals
- [x] Add regression simulating Qt callback after both transient InitGui namespaces have disappeared
- [x] Disable FreeCAD splasher on subsequent Design launcher runs using Design's separate native profile and shorten Home delay to 250 ms
- [x] Add Sketch Modify Rectangular Pattern for real constrained 2×2 circle pattern; each hole center is a Sketcher geometry, with editable pitch/radius constraints
- [x] Add native FreeCAD test to cut four holes in an 80×60×8 plate from the patterned sketch; reject duplicates without mutation
- [x] Prepare version-correct 0.5.6→0.5.7 Windows patch pipeline from hash-checked pinned 0.5.6 candidate #20
- [x] Gate Windows patch on real FreeCAD geometry job before downloading installed baseline
- [ ] Obtain green Linux geometry, headless packaging, Windows native install/Qt/rollback for 0.5.7 candidate and exercise native GUI on owner's machine
- [ ] Confirm no stock FreeCAD launcher/profile regressions; promote public update only after owner acceptance

## 2026-11-10 — Fusion Pattern + SVG history delivery

- [x] Move Solid Linear Pattern from More to direct MODIFY toolbar
- [x] Design-owned in-canvas Solid Pattern with source selection, count, pitch/extent, axis, optional 2D grid and transactional preview
- [x] Route timeline double-click Pattern edit into Design, not raw native FreeCAD task
- [x] Design-owned live Sketch 2D circle pattern preview, Apply/Cancel/Esc and drag handles
- [x] Original SVG images for all common timeline features, Edit/Delete/Resume/Settings controls
- [x] Native engine tests for hole pattern preview/cancel/edit, package contracts for icons/ownership
- [x] Fast package + geometry CI passed in run #407 on b1b602c
- [ ] Revalidate latest candidate SHA with Windows 0.5.6-to-0.5.7 patch/Qt/rollback job
- [ ] Owner FreeCAD 1.1 acceptance: two-axis 2x2 solid Hole pattern, live edit, timeline DPI and Cancel/Esc, save/reopen
- [ ] Publish through updater only after hands-on acceptance


## 2026-11-10 — Video-driven Fusion behavior gap batch

- [x] Record specific Fusion-vs-Design plate workflow gaps by timestamp in FUSION_FREECAD_VIDEO_GAP_REVIEW.md
- [x] Auto-suggest one dominant perforated plate region for Extrude, with holes left open
- [x] Keep ambiguous multi-profile Extrude selection explicit and editable
- [x] Hide large Sketch plane chooser when a solid is present; next click on planar face opens the actual sketch
- [x] Allow Sketch Rectangular Pattern to choose its source circle directly from canvas while Design panel is open
- [x] Replace modal preselected-edge Fillet/Chamfer with a nonmodal Design panel and live OCCT shape validation
- [x] Route Fillet/Chamfer history edits to Design rather than raw PartDesign task UI; Undo-safe parameter changes
- [x] Add headless fast-video workflow contracts and native plate-hole extrusion / Fillet edit-Undo geometry tests
- [x] Verify fast package and geometry CI #433 on commit 709e5df; full source checks passed
- [ ] Verify new source's Windows 0.5.8-to-0.5.9 candidate and actual FreeCAD 1.1 GUI interaction
- [ ] Add Fusion-style ghosted fillet visual preview and direct in-canvas radius handle, if GUI acceptance finds it needed
- [ ] Complete advanced sketch snapping/dimensions and profile-click in viewport to match Fusion more closely
- [ ] Publish unique 0.5.9 update only after accepted release gates; no same-version rewrite


## 2026-11-11 — Owner-approved 0.5.11 scope freeze / 0.5.12 deferral

Owner approved shipping the implemented 0.5.11 work as a smaller release and
moving unfinished features to 0.5.12. **Do not publish without Windows release
validation.** 0.5.11 scope: ambiguity-safe sketch circle picking, native
associative edge references via explicit selection/right-click, transactional
multi-edge linking, sketch-pattern preview/rollback safety, and persisted
pattern records. Source CI passed at 91a540b (run 43146857290).

0.5.12 backlog:
- [ ] Automatic passive Fusion-style body-edge/midpoint/circle-center cues
  during Sketcher drawing, without requiring manual reference action
- [ ] Independently editable persistent sketch-pattern timeline entry, stable
  generated geometry AND constraint ownership, safe double-click editing
- [ ] Native save/reopen, undo/redo and two-pattern editing acceptance for
  persistent sketch-pattern history

0.5.11 release gate (not yet completed):
- [ ] Retarget guarded native Windows patch from verified 0.5.10 installed
  baseline to unique 0.5.11 destination, without bypassing hash checks
- [ ] Verify native FreeCAD geometry and 0.5.10→0.5.11 silent patch install,
  Qt startup, rollback/uninstall, and artifact checksums
- [ ] Publish only the validated artifact through the existing update channel
