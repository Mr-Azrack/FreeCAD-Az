# Az Design installer packages

## 0.3.3 modeled-thread crash-lab review build

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
