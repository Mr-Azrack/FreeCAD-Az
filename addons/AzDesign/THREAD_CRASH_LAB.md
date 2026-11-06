# Az Design — modeled-thread crash lab (0.3.3)

This is a deliberately **dangerous but opt-in** diagnostic build. It restores
the FreeCAD native `PartDesign::Hole.ModelThread` switch for diagnosis; it does
not claim to correct the crash inside FreeCAD/OpenCASCADE.

## Safest reproduction procedure (Windows FreeCAD 1.1)

1. Install Az Design 0.3.3 using `Install_AzDesign.FCMacro`, fully close and
   restart FreeCAD.
2. Save and close unrelated CAD work. **Launch a separate FreeCAD process** for
   the experiment. Verify it is a second process in Windows Task Manager;
   merely opening a second window can reuse the same process.
3. From **Macro → Macros…**, choose the downloaded/extracted package folder,
   select `Probe_Modeled_Thread.FCMacro`, and run it. This macro lives at the
   root of the ZIP alongside the installer and under `AzDesign/Tools`.
4. The macro asks for confirmation, creates a disposable native 20×20×10 mm
   block, saves the unthreaded input as an FCStd document, and attempts a
   genuine modeled ISO metric M4 thread at 8 mm depth. **It may crash FreeCAD.**
5. After a crash, start FreeCAD normally. Locate `AzDesign-Diagnostics`
   inside the directory returned by `App.getUserAppDataDir()`. The latest
   `modeled-thread-*.jsonl` checkpoint identifies the last stage reached.
   Companion `*.fault.txt` may include Python thread stacks. Keep the
   matching `thread-probe-input-*.FCStd` model for a reproducible case.
6. Share the **JSONL checkpoint, fault text, FreeCAD version and Windows
   Event Viewer → Windows Logs → Application faulting-module entry** for
   analysis. Include the saved FCStd input if comfortable sharing it.

The last checkpoint is persisted with flush + fsync *before* native thread
configuration and recompute. A Python exception is reported; a native process
termination is not catchable with `try/except`.

## Reproduce using the normal Az Hole panel

Create a **disposable** test document with a block and circular sketch.
Select Hole → thread standard → Show result once to populate actual thread sizes.
Pick the intended size, check **Actually model helical threads — EXPERIMENTAL**,
then choose Show result and explicitly confirm the crash warning. Normal holes
stay cosmetic. The status/Report view points at the experiment's JSONL trace.
Clicking OK after a valid unchanged preview does not rebuild the helix again.

## Optional C++ crash dump (Windows)

Python fault logs cannot identify the exact OCCT C++ frame. For a real native
call stack, use Microsoft's [ProcDump](https://learn.microsoft.com/en-us/sysinternals/downloads/procdump)
on the **disposable FreeCAD process**, not the regular work session.

Create an empty `C:\\AzThreadDumps` folder and identify the *test process PID*
in Task Manager. From a Command Prompt in the extracted ProcDump directory,
before clicking the modeled-thread test:

```bat
procdump64.exe -accepteula -e -mp <TEST_FREECAD_PID> C:\AzThreadDumps
```

`-e` captures an unhandled exception; `-mp` includes thread/module data and
private memory. Reproduce the crash while ProcDump is monitoring. A native
Windows dump can contain sensitive data, so **do not upload it publicly**.
The small JSONL log and Windows faulting-module record should be our first
diagnostic exchange. A dump may require appropriate FreeCAD/OCCT symbols to
identify the exact crashing native function.

## Known limits

- FreeCAD 1.0 native and the offline contracts may pass while FreeCAD 1.1
  on Windows crashes. The crash itself is **not** executed in GitHub CI.
- Only new Az Hole previews can enter the experimental path. Editing a
  previously modeled Hole or a Hole with later dependent features still
  requires Native CAD.
- Modeled thread geometry can be slow even when it does not crash. This
  feature remains experimental until repeatable safe behavior is established.
