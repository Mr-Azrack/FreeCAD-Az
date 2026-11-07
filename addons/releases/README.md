# Az Design installer packages

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
