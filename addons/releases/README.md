# Az Design installer packages\n\n**0.3.2 review build:** A native Hole task with guarded previews and cosmetic-thread\nsettings is being tested on the development branch. Get the passing build from\nthe [Az Design CI artifacts](https://github.com/Mr-Azrack/FreeCAD-Az/actions/workflows/az-design.yml)\nunder **AzDesign-installer** (contains AzDesign-0.3.2.zip). The ZIP below is the\nlatest checked-in release, **0.3.1**, and does **not** contain the Hole fixes.\n

Download **[AzDesign-0.3.1.zip](AzDesign-0.3.1.zip)**, extract it, then run
**Install_AzDesign.FCMacro** from FreeCAD's Macro menu. Restart FreeCAD and select
Az Design. See `AzDesign/README.md` inside the package for the workspace guide.

0.3.1 enables modeling/sketch grids by default and fixes modern extrusion-side
properties and native Boolean preference restoration. The 0.3.0 workspace introduced
the work area with a light canvas, grouped Browser, top document
tabs, compact timeline, navigation controls and idle Solid radial tools. It
includes the 0.2.1 startup and 0.2.2 first-document fixes. Source is in
`addons/AzDesign`; rebuild with
`python3 tools/package_azdesign.py --output addons/releases/AzDesign-0.3.1.zip`.

Tests cover Linux FreeCAD 1.0/Qt5/PySide2. Windows/FreeCAD 1.1 and Qt6 acceptance
remain pending. Previous packages, including 0.2.2, are retained. The installer
backs up an existing installation before updating it.
