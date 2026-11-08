# Az Design installer packages

## 0.5.0 parametric machining fixture and native workflow reliability

This release closes a large functional gap between Az's visual shell
and daily modeling: **Sized Rectangle** creates native dimension-driven
Sketcher geometry; new Join/Cut/Intersect options are preflighted against
existing Body geometry before changing the real feature history; and
accepting an edited upstream Extrude validates actual downstream solids
rather than only checking FreeCAD's Invalid flag.

The native release-gate test creates a full 60×40×8 mm fixture, subtracts
a pocket, makes two holes and a Fillet, changes source sketch width,
edits a Hole and verifies Cancel/Undo/Redo plus native FCStd save/reopen.
This does not prove actual Windows FreeCAD 1.1 UI behavior, modeled-helix
safety, or complete Fusion 360 feature parity.

Owners with 0.4.3 installed use **Update Az**, confirm the CI-tested
0.5.0 version and fully restart FreeCAD. The updater backs up the old
workbench automatically, and an installer ZIP is available via CI only
for recovery.



## 0.4.3 Extrude visibility and invalid-profile preview correction

A user Windows FreeCAD 1.1 screen recording revealed an Extrude task
hiding the entire model during multi-profile selection and occasionally
leaving an invalid temporary Body Tip after a failing Join. 0.4.3 stops
auto-entering profile-picking mode; displays overlays on the existing
solid; pauses preview recomputation while picking; suppresses previews
with zero selected profiles; and discards invalid **new** Extrude previews,
restoring the previous Body Tip, visibility and recomputed solid.

A truly disconnected Join still reports a geometrically invalid result
rather than pretending to create a valid PartDesign Body. Existing edited
features retain full native Cancel rollback behavior. Native tests cover
invalid new preview cleanup and successful retry in the same transaction.

Upgrade with **Update Az** from 0.4.2, then completely restart FreeCAD
and repeat the multi-profile sketch test.



## 0.4.2 FreeCAD 1.1 Extrude dialog and link-scope corrective build

Addresses owner-reported PySide6 `getStandardButtons()` TypeError and native
`PartDesign::FeaturePython` out-of-scope sketch references during Extrude.
Both Az Hole and Extrude task button masks now work with Qt5 and Qt6.
New Extrudes use native globally scoped FreeCAD source/limit links when
modeling across Bodies. Existing 0.4.1 Extrudes can have local-only links
upgraded by explicitly reopening them in Az Edit and accepting a valid
preview; Undo/Cancel keeps original properties.

Upgrade from 0.4.1 with **Update Az**, then save work and completely restart
FreeCAD. The native CI checks link types, cross-Body recomputation and
the legacy transaction migration. Owner Windows 1.1 acceptance is pending.



## 0.4.1 Sketch Palette screen-fit and native control repair

0.4.0's owner Windows screenshot showed a large duplicate-tools sketch panel,
unreadable control labels, nonfunctional fake view settings and native Tasks
pushed below screen height. **0.4.1** replaces it with a compact, maximum
210 px high Sketch Palette containing only native-backed grid, spacing,
auto-constraints, redundancy and capability-checked Snap controls. No duplicate
draw buttons or Finish Sketch button, no unsupported ShowProfiles/Dimensions
checkboxes. Native Sketcher Tasks now receives the remaining vertical space.

Run the existing **Update Az** command from 0.4.0, accept 0.4.1 after CI
passes, save documents and completely restart FreeCAD. As always, old versions
are backed up; user Windows GUI validation follows.



## 0.4.0 consolidated design-workflow preview

A single larger UX delivery across timeline navigation/dependencies, sketch
palette, shared feature edit routing, canvas contextual actions and guarded
quick dimensions, Body-grouped Browser, and consistent ribbon/task styling.
Native FreeCAD workbench files/geometry remain authoritative; arbitrary
history reorder, reference repair, and custom feature-dialog parity are not
claimed. Review `addons/AzDesign/README.md` for exact actions and limitations.

Owners on **0.3.7** use **Update Az** to fetch a CI-passing 0.4.0 source commit
directly from the public development branch, with per-file Git integrity checks,
an automatic dated backup, and required full application restart. A downloaded
ZIP is still published in CI for recovery, not required for normal upgrades.



## 0.3.7 in-app updater bootstrap review build

Install `AzDesign-0.3.7.zip` **one final time**, using the same
`Install_AzDesign.FCMacro` process. After restarting FreeCAD, use the
**Update Az** ribbon button or **File → Check for Az Design updates…**.
Az checks the latest successful Az Design CI commit on the public development
branch, downloads hash-verified files directly, backs up the previous local
version and installs only after confirmation. Restart FreeCAD after updates.
No further ZIP downloads or separate installer macro are required for
subsequent versions of this workbench.

This is a preview feature tested with offline GitHub API fixtures and the
usual Linux FreeCAD CI; the first live Windows/FreeCAD 1.1 network update
still requires owner acceptance. A public network connection is needed.



## 0.3.6 timeline Edit/Delete review build (previous)

Selected features in the bottom timeline have visible Edit/Delete actions.
Native one-step deletion is allowed only for features without live dependent
references, and explicit **Delete from here** removes later steps in one
Body with confirmation and Undo. Earlier native Holes can now be edited with
downstream recomputation and validation before accepting; modeled threads
retain explicit consent and diagnostics. Native Pad/Pocket/Fillet edit tasks
are also accessible by double-clicking in the Az Browser.

Get the latest **AzDesign-installer** workflow artifact after CI passes from
[Az Design CI](https://github.com/Mr-Azrack/FreeCAD-Az/actions/workflows/az-design.yml)
and extract `AzDesign-0.3.6.zip`. The checked-in release ZIP remains 0.3.1.



## 0.3.5 compact Hole panel and safe live preview review build (previous)

The Hole task groups its controls, loads native thread sizes when selecting a
standard, and debounces automatic previews for **plain/cosmetic** Holes only.
Existing or previously modeled helical features remain manual-only with an
explicit crash warning and durable logs. Windows FreeCAD 1.1 acceptance remains
pending. Source code, install guidance and limitations are in
`addons/AzDesign/README.md`.

Get the **AzDesign-installer** artifact from the
[Az Design add-on workflow](https://github.com/Mr-Azrack/FreeCAD-Az/actions/workflows/az-design.yml)
after both package and modeling jobs pass. Extract `AzDesign-0.3.5.zip` and
execute `Install_AzDesign.FCMacro`. Checked-in release ZIP is still 0.3.1.


## 0.3.4 editable modeled-thread Hole review build (previous)

This review build fixes the explicit edit prohibition left over from 0.3.2.
Existing native modeled Holes now reopen with their geometric-thread setting
preserved; opening or accepting without changes does not recompute native
helical geometry. Intentional edits use the experimental warning and fsynced
logging. Save your file before a modeled-thread edit.

Download the `AzDesign-installer` artifact from the
[latest passing Az Design CI](https://github.com/Mr-Azrack/FreeCAD-Az/actions/workflows/az-design.yml)
then extract `AzDesign-0.3.4.zip`. The ZIP in the repository remains 0.3.1.

## 0.3.3 modeled-thread crash-lab review build (previous)

A controlled experimental switch restores native `ModelThread=True` only
after explicit warning/confirmation and writes durable diagnostic checkpoints.
The ZIP includes `Probe_Modeled_Thread.FCMacro` for reproduction in a separate
FreeCAD process on a disposable part. The root cause of the native crash is
**not yet fixed**. See `addons/AzDesign/THREAD_CRASH_LAB.md`.

Get `AzDesign-0.3.3.zip` from the **AzDesign-installer** artifact in the
[latest passing Az Design add-on CI workflow](https://github.com/Mr-Azrack/FreeCAD-Az/actions/workflows/az-design.yml).
The newest checked-in repository ZIP remains 0.3.1. The previous 0.3.2 review
build is available in [run 42248286120](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42248286120).
Windows/FreeCAD 1.1 crash-lab execution still needs owner testing. The installer
backs up the existing Az Design installation before replacing it.

## Earlier releases

Download **[AzDesign-0.3.1.zip](AzDesign-0.3.1.zip)**, extract it, run
`Install_AzDesign.FCMacro` in FreeCAD and restart. It provides the light
Fusion-style workspace, default grids, extrusion compatibility, startup
and hidden-document fixes but does not include 0.3.2+ Hole improvements.

### Verified 0.3.3 experimental crash-lab review artifact

[Az Design CI 42253489192](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42253489192)
passed both **package** and **native modeling** jobs on the source commit
`0d251aa10eba7ea64f16f74964e6dbbb8516668b`. The native FreeCAD 1.0
suite passed 28 modeling tests (cosmetic-thread and preview only); packaging
passed six HoleSpec, four HoleOperation and one durable-diagnostic offline test,
plus prior baseline checks. Running a real ModelThread helix is **not** part of
CI because it may crash the worker.

Download the [AzDesign-installer artifact 13521627224](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42253489192/artifacts/13521627224).
It contains `AzDesign-0.3.3.zip`: **172,372 bytes**,
SHA256 `b4a126826650fb6d9555266c1a6618406e1613f418191ce6ff1332f56b5f7fe0`.
The outer/inner ZIP CRC checks passed, and the extracted 11 dedicated offline
Hole tests passed again. `Probe_Modeled_Thread.FCMacro` is at the ZIP root
and under `AzDesign/Tools`; it was syntax-checked but **not run**.
Its SHA256 is
`af658bc61f1d3ac36a09f5dfd2fbfd4f96bea9ed0119bf30a8a29a4f8ab22e79`.

Important: Windows FreeCAD 1.1 GUI acceptance and modeled-thread crash
reproduction remain outstanding. The first real crash should be reproduced
in a separate disposable FreeCAD process, followed by log analysis.

### Verified 0.3.6 timeline Edit/Delete package — 2026-11-07

[Az Design CI run 42342092612](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42342092612)
passed **package** and **native modeling** jobs for source commit
`fd513f89e9d938171cefb645038ef5ed9efe9479`. Native FreeCAD 1.0 tests
cover transaction deletion/Undo, refusing an unsafe single deletion, explicit
later-branch deletion, and editing an earlier Hole beneath a later native Pad.
The prior run 42341922863 had a test-only error from dereferencing a deleted
FreeCAD Python object proxy after native deletion succeeded; the regression
was corrected to save object names before removal and the latest run passed.

[AzDesign-installer artifact 13562141196](https://github.com/Mr-Azrack/FreeCAD-Az/actions/runs/42342092612/artifacts/13562141196)
contains the tested `AzDesign-0.3.6.zip`: **186,564 bytes**, SHA256
`85a6f3ef177bbd501e689fb6683666010803b74f2196156a125cec2b7bff5297`.
Outer and inner ZIP CRC checks passed; contains the installer, native history,
Hole editing, UI changes and tests. Five focused Hole test scripts passed again
from the extracted ZIP in the working container. The latest checked-in repo
release ZIP remains 0.3.1; use the passing Actions artifact for 0.3.6.
**Windows FreeCAD 1.1 timeline GUI validation is still pending.** PR #1
remains draft and unmerged.
