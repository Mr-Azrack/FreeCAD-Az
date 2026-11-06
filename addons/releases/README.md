# Az Design installer packages

## 0.3.5 compact Hole panel and safe live preview review build

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
