# Az Design installer packages

Download **[AzDesign-0.2.2.zip](AzDesign-0.2.2.zip)**, extract it, then run **Install_AzDesign.FCMacro**
from FreeCAD's Macro menu. See `AzDesign/README.md` inside the package for details.

These small standalone packages are included so users do not need to download
or build the complete FreeCAD fork. Source is in `addons/AzDesign`; rebuild with
`python3 tools/package_azdesign.py --output addons/releases/AzDesign-0.2.2.zip`.

Version 0.2.2 includes the startup fix and automatic visible-document creation for
Create Sketch. It was tested in FreeCAD 1.0.0 on Linux with Qt 5 / PySide2. The
owner's Windows/FreeCAD 1.1 retest remains pending. Previous packages are retained
for reference; use 0.2.2 for a new install or update.
