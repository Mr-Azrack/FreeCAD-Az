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

## Version compatibility and default grids — 0.3.1, 2026-11-06

Prefer property capabilities over version strings for native extrusion: SideType
and Type2 on modern features, legacy flags only when SideType is absent. Native
Press/Pull must classify side mode using the same API. Preserve old FreeCAD
support without writing deprecated properties on modern builds. Use the actual
parameter type labels from GetContents and accept empty groups.

Owner prefers a visible grid over blank canvas. Default Az grid visibility to true
and persist its toggle in Az's own preference group. Use native aligned sketch
grid while editing; keep modeling floor unpickable, outside saved geometry and
outside native scene bounds. No geometry kernel change is needed.

## 2026-11-06 — Hole preview and thread-safety decision

- A native Hole must use an Az-owned task surface while Az is active. Native
  geometry/document properties remain authoritative; no copied modeling kernel.
- Invalid Hole previews must reveal the previous real solid, not merely report
  an error while leaving the viewport empty; Reject rolls the transaction back.
- Do not call FreeCAD's modeled helical thread path from Az until its crash and
  performance are independently characterized. Keep ModelThread=False, while
  allowing native thread standards/sizes as cosmetic/machining intent.
- Require a deliberate thread size; never choose the first native size without
  informing the user. Check FreeCAD feature capabilities rather than assuming
  a property exists on every FreeCAD version.
- Restrict Az Hole editing to the Body Tip for now; native workbench handles
  advanced options, downstream-history changes and previously modeled threads.
  This is an interim stability gate, not a commitment to abandon real threads.

## 2026-11-06 — Opt-in geometric thread crash investigation

The owner explicitly wants native helical threads re-enabled for reproduction
and debugging. Keep the everyday Hole path cosmetic by default; expose
`ModelThread=True` only through explicit, per-preview experimental consent
and a durable diagnostic checkpoint. Never run the potentially crashing OCCT
helix creation in ordinary CI. Provide a disposable test macro and recommend a
separate FreeCAD process to avoid losing work. Preserve FreeCAD-native Hole
objects and the exact options used; capture C++ dumps separately if Python
fault logs cannot reveal the native failure site. This is a diagnostic enable,
not a verified kernel crash repair. Do not silently enable modelled threads on
an existing part or merge the draft PR without owner testing.

## 2026-11-06 — Restore editing for opted-in modeled holes

After the owner's Windows Az Hole panel successfully generated real threads,
editing failed because stale 0.3.2 guards explicitly rejected existing modeled
holes. Editing must preserve the current `ModelThread` state, thread size and
standard, not silently convert to cosmetic; unchanged edits should be true
no-ops to avoid expensive or crash-prone recomputation. Actual geometric edits
remain explicitly consented, transactionally reversible, and durably logged.
Keep the restriction against editing holes with downstream features until
history-aware downstream recompute can be validated. New 0.3.4 paths remain
under owner Windows acceptance and draft PR review.

## 2026-11-06 — Small reversible UI improvements over working CAD behavior

After successful owner Windows 0.3.4 modeled Hole editing, continue in
deliberate increments ("we break fix as we go"), not a disruptive top-to-bottom
rewrite. For 0.3.5 polish the existing native Hole panel first: compact grouped
controls, readable FreeCAD thread standard labels, native-derived threaded
diameter lock, immediate standard-dependent size choices and optional debounced
plain/cosmetic live previews. Never auto-run real modeled helix generation,
including after changing an originally modeled Hole or toggling modeled mode
off. Preserve explicit consent, logs, native transactions, original geometry,
reversible sketch selection before preview, and no-op edits. Maintain Windows
GUI testing as separate evidence from Linux/Qt-stub test results.

## 2026-11-07 — First reliable editable timeline increment

The owner explicitly requires the bottom strip to be a usable modeling
history, not only a rollback viewer. Add obvious selected-feature Edit/Delete,
retain double-click editing and contextual operations, and use FreeCAD's real
native feature/task/transaction semantics. Deletion is a destructive operation:
require explicit confirmation, provide Undo, reject single deletion when live
dependents exist, and offer separately confirmed same-Body Delete from here.
Refuse external dependencies rather than quietly breaking another body or
rewiring unknown topological subelements. Allow earlier native Hole editing
only with original Body Tip restoration and downstream geometry validation;
retain experimental modeled-thread consent and logs. This is intentionally
smaller than unrestricted Fusion reordering and all-feature edit parity.

## 2026-11-07 — Verified one-click updater on top of the installed workbench

Avoid forcing the owner to repeatedly download/extract separate installers.
Ship a 0.3.7 one-time bootstrap adding **Update Az** in the FreeCAD ribbon.
The updater must never install an untested moving branch HEAD: use the latest
successfully completed Az Design add-on CI run on the branch, pin all source
requests to its exact SHA, verify per-file Git blobs and stage the entire
workbench before replacing anything. Reuse the transaction-safe local installer
and preserve the previous version in AzDesign-backups; no surprise hot reload,
credential prompt or editing of open CAD files. A full restart is mandatory.
Provide clear error/cancellation feedback when GitHub is unavailable. Public
repo and branch are hard-coded to this project's development source until
proper signed releases and channels exist. Owner Windows 1.1 acceptance
remains necessary.

## 2026-11-07 — Consolidated 0.4.0 Fusion-inspired workflow sprint

Owner explicitly requested all six previously proposed layout/workflow/look-and-feel upgrades be delivered **together**, rather than six incremental versions. Source changes committed on `codex/az-design-workbench`; PR #1 remains draft/unmerged. No main-branch modifications. User already tested 0.3.7 Update Az bootstrap.

### Implemented in one review build

- **Timeline**: native `history_position`, draggable slider that moves actual Body Tip on release, native incoming-dependency inspector, shared feature editor. Existing 0.3.6 Edit/Delete/Undo and safety checks retained. Body Tip scrub is **not** arbitrary reorder.
- **Sketch**: `SketchPalette` right dock, open only during sketch edits; native grid, snap, profile/dimension/constraint display flags enabled only when present on the installed FreeCAD ViewObject; tools for drawing, dimension, construction, projection, Finish Sketch; native Sketcher Tasks/solver still authoritative.
- **Feature editing**: new `feature_edit.edit` dispatch used by the timeline and Browser, preserving native PartDesign dialogs and existing Az Hole/Extrude panels.
- **Canvas**: contextual floating tool strip for selected sketches/faces/edges/features/bodies and native right-click selection menu; idle canvas still has existing radial tool menu. `quick_dimension` edits known native Pad/Pocket lengths, Fillet Radius, Chamfer Size and AzExtrude Length transactionally, with recompute and error checks; no modeled-thread shortcuts.
- **Browser**: nested true Body.Group order with Features/Sketches under each Body, active-body mark, separate unassigned items, suppress labels; active Body control and selection/visibility/isolate preserved.
- **Presentation**: accessible hint bar, consistent task controls and history slider styling, restored native FreeCAD layout on workbench exit.

### Scope/risk

Native FreeCAD object/geometry/kernel unchanged. We did NOT implement arbitrary drag-reorder of dependent features, implicit topological link rewriting or a custom Az task for every advanced native operation; these are unsafe to promise as completed without real dependency tests. ViewObject sketch flags vary by FreeCAD release and unsupported ones are disabled rather than impersonated. Direct in-canvas arbitrary face handle dragging is not done; native/Az Extrude and Press/Pull handle tools remain. Linux FreeCAD 1.0 CI and offline Qt/selection tests do not prove Windows FreeCAD 1.1 GUI interactions. Verify the exact 0.4.0 CI and artifact before owner upgrade, then test real update via 0.3.7 button and full restart.

### Tests/source

- New `tests/test_interaction.py` stubs selection-policy + feature edit dispatch.
- Native workflow adds history scrub/real dependency links and Quick Dimension/Undo checks.
- Existing Hole modeling/transaction, updater, workspace and installer tests remain in CI.
- `addons/AzDesign/package.xml`, `azdesign/__init__.py`, help dialog bumped to 0.4.0.
- Documentation updated for this combined build and remaining parity limitations.



## 2026-11-07 — 0.4.1 owner Windows screenshot: repair nonfunctional oversized Sketch Palette

After installing/testing the consolidated 0.4.0 UI on Windows FreeCAD 1.1,
owner provided a screenshot showing the custom right palette consumed almost
the entire available screen height, pushing native Tasks and bottom history
below the visible area. The custom duplicated Rectangle/Circle/Line/Dimension
and Finish Sketch from the ribbon; light-on-light labels made some buttons
unreadable. Several checkboxes tried to write nonexistent Sketcher properties
(`SnapToGrid`, `ShowConstraints`, `ShowDimensions`, `ShowProfiles`);
they were visually inert. Owner correctly rejected the result as not
Fusion-like. We must not present these as completed working controls.

### 0.4.1 fix made on existing draft PR #1 / branch

- **Replaced**, not cosmetically tweaked, `azdesign/sketch_palette.py`.
  Removed all duplicate ribbon drawing buttons and its duplicate Finish
  Sketch; native Sketcher Tasks remains the geometry/constraint solver.
- The compact option-only palette has an explicit themed background,
  high-contrast labels/checkboxes, 215 px minimum width, 234 px inner
  maximum height and **210 px QDockWidget maximum height**; its native task
  dock uses the remaining right-side space. Bottom history dock limited to
  72 px (initial 58 px). Arrange sketch/native docks on sketch edit entry.
- Real ViewProviderSketch-backed toggles now only include **Show grid**
  (synced through Az appearance), **Auto grid spacing** (`GridAuto`),
  **Auto constraints** (`Autoconstraints`), and **Avoid redundant
  constraints** (`AvoidRedundant`). In a FreeCAD build supporting an actual
  checkable `Sketcher_Snap` QAction, **Snap while drawing** toggles that
  native action and tracks its state. Missing capabilities are hidden, not
  shown as fake disabled choices. User must test snap *while drawing new
  geometry*, not against existing lines.
- `test_sketch_palette.py` has four headless UI-wiring tests: compact
  control set, concrete provider property mutation, native checked Snap
  QAction, unsupported option hiding. Registered in CI alongside native
  modeling and prior installer/updater/Hole tests.
- Version bumped from 0.4.0 to **0.4.1**. Owner on 0.4.0 can click
  **Update Az** and restart; no new manual installer needed.

### Evidence and limitations

[CI run 42375950780](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42375950780)
passed both package and native modeling jobs. Its package job passed all
four new SketchPalette tests. The
[AzDesign-installer artifact 13575022990](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42375950780/artifacts/13575022990)
contains `AzDesign-0.4.1.zip`, 212,070 bytes, SHA256
`10bb043092f9cabb0a896a4d8e9d9ad8a076279956cdfe9f766e36e0411976e2`.
Both outer/inner ZIP CRC checks passed, `package.xml` is 0.4.1, and five
focused extracted tests were rerun successfully in the working container.

**Still pending:** actual owner Windows FreeCAD 1.1 screen-fit/theme
acceptance of 0.4.1. Mocked Qt wiring and Linux FreeCAD CI cannot certify
the user's native GUI panel sizing/color behavior or the precise native
checked Snap action. No custom Show Profiles/Dimensions controls until a
verified supported native implementation is available. Do not claim full
Fusion 360 Sketch Palette parity. Keep draft PR #1 unmerged.


## 2026-11-07 — Address real FreeCAD 1.1 task and scope failures without kernel changes

The owner's Report view errors take precedence over further visual polish.
Use one Qt StandardButton mask helper shared by Hole and Extrude for both
PySide2 and PySide6; enforce with a mocked enum.Flag regression.
FreeCAD-native Extrude input and limit links may legally cross PartDesign
Bodies (source sketch in Body A, Extrude in Body B), so declare global-scoped
source/limit and frame references rather than relying on local-only LinkSub
and producing scope warnings. Keep native local BaseFeature history.
Migrate old 0.4.1 feature link types only during a user-requested explicit
Edit inside the native transaction; preserve Undo/Cancel and do not silently
rewrite FCStd files on load. Do not claim Windows GUI verification from
Linux modeling tests.


## 2026-11-07 — Preserve valid solids while choosing Extrude profiles

Owner's FreeCAD 1.1 video shows the entire Body hiding during profile
selection. This is not appropriate Fusion-style preview semantics.
The **original valid Body remains visible** until a valid new feature is
previewed. Multi-profile sketches do not implicitly enter overlay-picking
mode and no geometry evaluation occurs when zero profiles are selected.
Explicit profile-picking overlays do not hide Bodies. Suspend pending
preview timers while picking faces/regions. Failed new extrusion geometry
discards its temporary results and restores the original Body Tip,
visibility and recomputed solid without closing the task. Keep original
editing transactions and Cancel as the full rollback mechanism for edits
of existing features; avoid deleting an edited object. Do not confuse
geometrically disconnected Join failures or FreeCAD hasher warnings with
the visibility bug, and do not claim those are all fixed without evidence.


## 2026-11-08 — Az 0.5.0 prioritizes safe end-to-end parametric fixture work

User requested 0.5.0 as one substantial upgrade. Define success using a
native parametric fixture acceptance test rather than feature-count or
look-and-feel claims: constrained plate sketch, Extrude, pocket, two Hole
centers, native Fillet, upstream dimension edit, editing Hole/Extrude with
downstream features present, Cancel/Undo/Redo and FCStd save/reopen.
Implement a practical Sized Rectangle via the native Sketcher solver
and two driving dimensions, not a new geometry system; reject insertion
into nonempty sketches to avoid creating overlapping profile loops.

For new Join/Cut/Intersect, calculate feasibility on FreeCAD's existing
independent geometry calculator BEFORE adding objects/setting Body Tip
in the real document. Require non-no-op material change and valid one
solid; offer context-specific alternatives when a profile is detached
or doesn't cut. For accepted upstream Az Extrude edits, validate real
downstream shapes and native/Az errors before committing; preserve
native transaction rollback. Avoid pretending unimplemented arbitrary
timeline reorder/topological repair and actual Qt6 Windows screen-fit
are validated by Linux CI.


## 2026-11-08 — Native snapping and micro-geometry must be truthful

User confirmed micro-scale CAD model is correct; never silently rescale.
Fillet/Chamfer errors must be diagnosed by actual OCCT geometry on the
selected edge, preserving native PartDesign parametric object and Undo,
not by a size-ratio heuristic. Use native OCC check before modifying Body.

User clarified Fusion workflow: midpoint glyph naturally appears as cursor
slides over a line and circle center is discoverable from rim, without a
manual finder. Provide passive automatic markers in the current Az Sketcher
interface, leave native mouse clicks/AutoConstraints alone, and keep any
manual XYZ finder as an optional inspection tool only.

True **click anywhere on a circular rim to make the current native drawing
tool use its center** is not solved by a Qt marker overlay. An opt-in
FreeCAD **1.1.0 C++ SnapManager** patch is staged; default disabled, Alt
bypasses to original rim snap. Do not overwrite the user's installed
`C:\Program Files\FreeCAD 1.1`, declare it complete, or ship it through
Update Az until a separate Windows native fork is compiled, tested and
packaged. No Autodesk code/assets are copied.


## 2026-11-08 — Isolated native Windows application build

Use FreeCAD **1.1.0** source and its pinned **Pixi** toolchain on a separate
`windows-2022` GitHub Actions runner with Visual Studio 2022, rather than
overwriting `C:\Program Files\FreeCAD 1.1` or inventing a new geometry kernel.
Compile C++ `SketcherGui` with reviewed `SnapManager` center-click patch
and retain the existing Python Az workbench. Prefer an unsigned isolated
PORTABLE developer preview before attempting signed MSI/auto-updating app.
Follow upstream FreeCAD/FreeCAD-Bundle's conda Windows runtime directory
layout to package dependent Qt/Python/OCCT DLLs and modules. Native launcher
uses independent `%LOCALAPPDATA%\AzDesign\Native-1.1` profile and
`--user-cfg/--system-cfg`, never changes existing user FreeCAD data.
Do not distribute if compiled FreeCAD.exe, Sketcher or AzDesign is absent;
manifest includes SHA256 and exact source/patch provenance.
Native C++ snap remains preference-gated in first experimental preview;
do not claim a Python workbench update installs C++ binaries.
GitHub Actions source diff requires special `core.whitespace=cr-at-eol`
validation because FreeCAD 1.1 SnapManager.cpp is upstream CRLF.


## 2026-11-09 — Release Windows portable app only with real Qt GUI platform smoke test

Owner's first Windows native preview produced
`no Qt platform plugin could be initialized`. Source artifact had
`qwindows.dll` under `lib/qt6/plugins/platforms`, but launcher
pointed to `bin/platforms`. Release validation must locate/copy the
correct plugin from the SAME compiled Pixi runtime, write
`bin/qt.conf`, set Qt plugin paths, validate actual WinDLL dependencies
and instantiate a real Windows PySide6 QApplication using bundled
Python before uploading a native preview. No silent swapping with
stock FreeCAD DLLs, no speculative C++ core changes or rescaling.
To avoid making owner download 1.3 GB again, ship small checked,
standalone Qt QuickFix ZIP which overlays only launcher,
`bin/qt.conf` and `bin/platforms/qwindows.dll` on existing native
extract. Never touch Program Files / system FreeCAD 1.1.


## 2026-11-09 — Ship actual Windows installer and version-pinned delta updates

A portable ZIP with `Az Design.cmd` is insufficient; owner wants
Start Menu/desktop access, Windows Installed Apps entry and normal
uninstall. Build real Inno Setup 6 per-user installer from already
compiled FreeCAD 1.1 + tested native Sketcher DLLs, avoiding unnecessary
C++ recompilation, and use Windows Forms C# GUI launchers named
`AzDesign.exe` / `AzUpdater.exe`. Do not hijack .FCStd associations
or overwrite normal FreeCAD. Keep user files/config in LocalAppData.

Subsequent deliveries should be file-delta patch ZIPs with explicit
installed from/to version and SHA256 of both old and new bytes, strict
relative path validation, staging before mutation, full backup, rollback
and native process closure before modifying running DLLs. Prefer
independent PowerShell updater process outside installed app for updates.
The initial native updater is manual/offline patch selection; auto
download/signature/release feed remain separate work before claiming
one-click internet updates. Source-root stock FreeCAD and LGPL notices
remain untouched.

For GUI clipping on Windows DPI, 32px custom QToolButtons must explicitly
set `ToolButtonIconOnly`, full tooltips and short fallback labels rather
than rendering truncated words under inherited global FreeCAD styles.


## 2026-11-09 — Design-first command and workspace policy

Owner approved the visible name **Design** (or Modeling when context warrants). Keep the internal `AzDesignWorkbench`, `Az_*` IDs, package paths and document compatibility until a separately validated migration exists. Native FreeCAD geometry, Sketcher solver, document IO, and undo remain the engine; do not allow exposed Design feature commands to silently launch raw PartDesign task dialogs. Legacy advanced native features not yet wrapped must remain available through an explicitly selected Native CAD workspace, with truthful capability labels. Preserve the Home screen, default ordinary new models to Design, respect native saved workbench per reopened FCStd document, and do not hijack CAM/specialized contexts.


## 2026-11-09 — Native update channel / one-click UI

Keep existing tested 0.5.2 installed app as the baseline. Native installed Design now routes Update into the bundled Windows updater; standalone workbench installation retains independent add-on updates. Trust a verified versioned GitHub Release asset only if its API SHA256 digest, pinned baseline and official HTTPS URL are consistent; reject drafts, prereleases, missing hashes, mismatched paths and downgrades. Download to staging; apply only after owner consent and close; old-version hash preflight, backup and rollback remain enforced by ApplyAzPatch.ps1. Ship 0.5.3 via actual 0.5.2-to-0.5.3 delta test, not a speculative patch from source folders. Publish verified patch to latest GitHub Release only after manual promotion on a reviewed default-branch workflow, never as an uncontrolled PR job.


## 2026-11-10 — 0.5.4 release baseline decision

Patch a real first-successful 0.5.3 installed baseline from workflow run 42752856389 (original 43.5 KiB patch-generation artifact) to 0.5.4, preserving exact old-file baseline hashes. Do not generate another patch from 0.5.2 or a late rebuild labeled 0.5.3. Verify original installer .sha256 before install and use current rollback-protected updater, Windows Qt smoke, real Inno install/uninstall. Keep release promotion separate and explicitly approved from main; don't merge draft feature branch without consent.


## 2026-11-10 — Separate routine patch CI from full installer

Routine Python workspace/UI/updater edits must produce only a hash-verified 0.5.3→0.5.4 native patch, testing actual old-version apply, Qt startup, rollback and uninstall. Old baseline must be the pinned successful original Windows 0.5.3 installer and checksum; do not silently rebuild a pseudo-baseline. Construct old/new **allowlisted file overlays** from the installed baseline and current source, so the patch cannot include unrelated FreeCAD runtime/C++ core files. Run the expensive full native core/Inno 1.8GB installer workflow only manually for major releases; preserve manual GitHub Release approval. The pinned baseline setup still must be downloaded for safety until a separately validated content-addressed baseline cache exists.


## 2026-11-10 — Default native startup is Design Home, not native Part Design Start

The native Start Menu launcher without a file argument should open the independent Design welcome UI in the Design workbench, without creating an empty FreeCAD document. Keep both New Design and Open File, with new ordinary models handled by Design and existing FCStd/CAM files preserving their existing workspace routing. Set a native-only launcher environment flag rather than hijacking standalone FreeCAD or other installed workbenches. Use a Qt overlay without altering FreeCAD's global Start page or document file compatibility. Package native launcher changes in a versioned patch, not just the Python add-on.


## 2026-11-10 — Batch fixes rather than one issue → one expensive Windows build

Owner explicitly prefers **several related problems addressed in one integrated batch**. Standard batch: 3–6 related issues or one complete real-part workflow; meaningful commits remain frequent for recovery, but a commit is **not** a Windows release candidate. The fast add-on tests (`.github/workflows/az-design.yml`) remain automatic on the trusted development branch. The expensive Windows installed-baseline patch workflow (`az-native-patch.yml`) is now triggered only by an explicit 0.5.6 candidate marker update (`.github/validation-requests/native-0.5.6.txt`) or manual dispatch, NOT every PR/feature commit. Its first Windows step now runs all relevant headless add-on tests before any large baseline download. Candidate marker should be submitted only after fast modeling and packaging CI green. Only a green same-revision candidate may proceed to manual, controlled release. Full installer remains manual. Critical data-loss/security/CAM breakage overrides batch cadence. Detailed policy: `BATCH_VALIDATION.md`.


## 2026-11-10 — 0.5.7 correction batch after owner's real 0.5.6 Windows launch

Owner applied tested 0.5.6 artifact and recorded actual Windows launch falling back into stock FreeCAD with `NameError: name '_az_App' is not defined` in `InitGui.py`, plus unwanted FreeCAD startup splash. Fix: the delayed native Home callback retains `App` and `Gui` through default-argument binding because FreeCAD can discard the exec loader's module globals before Qt fires. Native-only profile sets `General/ShowSplasher = False` for subsequent Design launches and activates Design Home at 250 ms (stock FreeCAD profile unaffected). Add startup regression that clears both loader namespaces before invoking Qt callback. Do not hide serious startup errors just to suppress the splash.

Owner additionally needs 4 rectangular hole locations as sketch geometry, not merely a PartDesign feature-only Linear Pattern. Implement a **Design Sketch → Modify → Rectangular Pattern** for source circle, default 2×2, X/Y pitches, native Equal/DistanceX/DistanceY/Horizontal/Vertical constraints. Copies are real Sketcher curves usable in one native Hole; source diameter change propagates to all. Reject overlaps/invalid spacing and transactionally roll back failures. Native FreeCAD geometry tests must verify plate, four centers, a single Hole feature, and resulting cut volume. 0.5.6 is already owner-installed; future revision must be **0.5.6→0.5.7**, not a new artifact mislabeled 0.5.6. 0.5.7 candidate pipeline reconstructs installed 0.5.6 from pinned 0.5.4 installer + 0.5.5 patch + successfully verified #20 0.5.6 patch, checks SHA256, and requires Linux native geometry test before expensive Windows package/Qt/rollback testing. Publish manually only after owner GUI acceptance. Source modifications are not yet a validated installed update.

## 2026-11-10 — Design owns pattern interactions, native kernel owns geometry

Creation, selection, parameters, live preview, cancel/accept and later editing for Sketch Rectangular Pattern and Solid Linear Pattern belong to Design, never the FreeCAD native task panel. Preview runs in a reversible document transaction; cancel/Esc/workbench switch aborts. 2D Solid grid uses native second-axis properties when available and fails clearly if the runtime lacks them; do not pretend unsupported geometry exists. History UI is always original DPI-safe SVG images (never text abbreviations) with fixed click targets and descriptive tooltips. Keep Fusion video acceptance criteria in FUSION_WORKFLOW_REFERENCE.md. Never publish candidate without Windows tests and owner GUI acceptance.

## 2026-11-10 — No more same-version patch candidates

Owner is installed on 0.5.7 and correctly cannot apply another 0.5.6→0.5.7 artifact. The failed attempt was caused by reusing destination 0.5.7 for several different candidate SHAs (successful #36 and #37). A patch checks both from_version and each changed file's SHA256. Never bypass that guard or merely rename an archive. Next destination is 0.5.8 from a **specific verified original 0.5.7 baseline**, initially pinned to Build #36 (run 42899554668), which was the owner-directed earlier 0.5.7 acceptance artifact. Build #37 has a different same-version payload, so its source cannot be presumed byte-identical. Until user-machine provenance is verified, do not imply the #36-targeted 0.5.8 candidate will apply to #37. Existing 0.5.7 installation is to remain intact. Future releases need unique version per changed candidate and explicit build provenance.


## 2026-11-10 — Fusion video is interaction acceptance, not merely appearance

Owner instructed that the newer Design Native plate walkthrough must be compared directly with the Fusion video, and improvements should behave like Fusion rather than requiring native FreeCAD task-panel workarounds. We reviewed the full-resolution Fusion ~3:43 and FreeCAD ~13:06 recordings and wrote the timestamped, task-by-task reference FUSION_FREECAD_VIDEO_GAP_REVIEW.md. The comparison shows largest friction around holes, profile selection, face sketch entry, and Fillet task escape.

Implemented batch: (1) auto-select only the unambiguously dominant perforated plate sketch region in Extrude; preserve cutout wires and manual selection for ambiguous multiple regions. (2) After Create Sketch with an existing solid, hide the large plane chooser and let the next planar face click enter sketch directly; blank designs retain origin shortcuts. (3) Sketch Rectangular Pattern source can be picked directly from active Sketcher geometry while its panel is open. (4) Fillet/Chamfer now have Design-owned nonmodal canvas selection of edges *after* tool invocation, automatic native OCCT preflight on dimension changes, safe Apply/Cancel/Esc and parametric editing of existing features from History in one Undo transaction. A ghost shaded 3D fillet preview is not yet implemented; do not claim full Fusion parity. Do not silently guess geometry, bypass OCCT validity or file hash checks. Native FreeCAD kernels remain the geometry back end.
