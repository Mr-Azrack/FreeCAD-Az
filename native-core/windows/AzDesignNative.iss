; SPDX-License-Identifier: LGPL-2.1-or-later
; Az Design Native user-level installer; never replaces stock FreeCAD.
#ifndef SourceDir
  #error "Pass /DSourceDir=<absolute existing complete Az native folder>"
#endif
#ifndef AppVer
  #define AppVer "0.5.2"
#endif
#ifndef OutputDir
  #define OutputDir "dist"
#endif

[Setup]
AppId={{7ACDFE56-2E4A-42A1-85C6-B7E5890A7D2B}
AppName=Az Design Native
AppVersion={#AppVer}
AppVerName=Az Design Native {#AppVer} Preview
AppPublisher=Az Design
DefaultDirName={localappdata}\Programs\Az Design Native
DefaultGroupName=Az Design Native
OutputDir={#OutputDir}
OutputBaseFilename=AzDesign-Native-Setup-{#AppVer}-x64
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UsePreviousAppDir=yes
DisableProgramGroupPage=yes
UninstallDisplayName=Az Design Native {#AppVer}
UninstallDisplayIcon={app}\AzDesign.exe
CreateUninstallRegKey=yes
CloseApplications=yes
RestartApplications=no
WizardStyle=modern
SetupLogging=yes
; Inno always registers its uninstaller in Windows Settings > Installed apps.
; No file associations to avoid changing user's normal FreeCAD setup.

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Az Design Native"; Filename: "{app}\AzDesign.exe"; WorkingDir: "{app}"; Comment: "Az Design Native (FreeCAD-based)"
Name: "{autoprograms}\Az Design Native - Update"; Filename: "{app}\AzUpdater.exe"; WorkingDir: "{app}"; Comment: "Install a verified small Az Design update"
Name: "{autodesktop}\Az Design Native"; Filename: "{app}\AzDesign.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\AzDesign.exe"; Description: "Launch Az Design Native"; Flags: nowait postinstall skipifsilent
