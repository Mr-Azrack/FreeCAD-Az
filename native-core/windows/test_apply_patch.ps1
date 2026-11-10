# SPDX-License-Identifier: LGPL-2.1-or-later
# Integration test of real independent Windows patch application and rollback.
$ErrorActionPreference = "Stop"
$root = Join-Path $env:RUNNER_TEMP ("AzNativePatchTest-" + [guid]::NewGuid().ToString("N"))
$old = Join-Path $root "old"
$new = Join-Path $root "new"
$installed = Join-Path $root "installed"
$patch = Join-Path $root "version.azpatch"
foreach ($folder in @($old, $new, $installed)) {
    New-Item -ItemType Directory -Path (Join-Path $folder 'bin') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $folder 'Mod\AzDesign') -Force | Out-Null
}
try {
    [IO.File]::WriteAllText((Join-Path $old "bin\FreeCAD.exe"), "synthetic FreeCAD", [Text.Encoding]::UTF8)
    [IO.File]::WriteAllText((Join-Path $new "bin\FreeCAD.exe"), "synthetic FreeCAD", [Text.Encoding]::UTF8)
    [IO.File]::WriteAllText((Join-Path $old "Mod\AzDesign\ui.py"), "old UI", [Text.Encoding]::UTF8)
    [IO.File]::WriteAllText((Join-Path $new "Mod\AzDesign\ui.py"), "new UI", [Text.Encoding]::UTF8)
    [IO.File]::WriteAllText((Join-Path $old "Mod\AzDesign\old.txt"), "retire", [Text.Encoding]::UTF8)
    [IO.File]::WriteAllText((Join-Path $new "Mod\AzDesign\added.txt"), "addition", [Text.Encoding]::UTF8)
    Copy-Item -Path (Join-Path $old '*') -Destination $installed -Recurse -Force
    '{"product":"AzDesignNative","version":"0.5.2"}' |
        Set-Content -LiteralPath (Join-Path $installed 'AZ Native Version.json') -Encoding utf8

    python native-core/windows/create_patch.py --old "$old" --new "$new" --output "$patch" --from-version 0.5.2 --to-version 0.5.3
    if ($LASTEXITCODE -ne 0) { throw "Could not create integration patch" }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File native-core/windows/ApplyAzPatch.ps1 -InstallDir "$installed" -PatchZip "$patch" -NoUI
    if ($LASTEXITCODE -ne 0) { throw "Real Windows native patch application failed" }
    if ((Get-Content -LiteralPath (Join-Path $installed "Mod\AzDesign\ui.py") -Raw).Trim() -ne "new UI") {
        throw "Updated UI was not installed"
    }
    if (!(Test-Path -LiteralPath (Join-Path $installed "Mod\AzDesign\added.txt"))) {
        throw "New file was not installed"
    }
    if (Test-Path -LiteralPath (Join-Path $installed "Mod\AzDesign\old.txt")) {
        throw "Retired file wasn't removed"
    }
    $version = Get-Content -LiteralPath (Join-Path $installed 'AZ Native Version.json') -Raw | ConvertFrom-Json
    if ($version.version -ne '0.5.3') { throw "Native installed version not updated" }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File native-core/windows/ApplyAzPatch.ps1 -InstallDir "$installed" -RollbackLatest -NoUI
    if ($LASTEXITCODE -ne 0) { throw "Native rollback failed" }
    if ((Get-Content -LiteralPath (Join-Path $installed "Mod\AzDesign\ui.py") -Raw).Trim() -ne "old UI") {
        throw "Original UI not restored by rollback"
    }
    if (!(Test-Path -LiteralPath (Join-Path $installed "Mod\AzDesign\old.txt"))) {
        throw "Deleted file not restored"
    }
    if (Test-Path -LiteralPath (Join-Path $installed "Mod\AzDesign\added.txt")) {
        throw "Added file not removed by rollback"
    }
    $version = Get-Content -LiteralPath (Join-Path $installed 'AZ Native Version.json') -Raw | ConvertFrom-Json
    if ($version.version -ne '0.5.2') { throw "Original native version not restored" }

    # A user-modified installed file must fail baseline protection, before
    # the first source file is replaced. Documents are never altered.
    Set-Content -LiteralPath (Join-Path $installed "Mod\AzDesign\ui.py") -Value "user edit"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File native-core/windows/ApplyAzPatch.ps1 -InstallDir "$installed" -PatchZip "$patch" -NoUI
    if ($LASTEXITCODE -eq 0) { throw "Incorrectly accepted a patch against modified local files" }
    if ((Get-Content -LiteralPath (Join-Path $installed "Mod\AzDesign\ui.py") -Raw).Trim() -ne "user edit") {
        throw "Failed patch overwrote a user-modified file"
    }
    Write-Host "PASS: changed-only patch, add, delete, version, rollback and mismatch protection"
} finally {
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
