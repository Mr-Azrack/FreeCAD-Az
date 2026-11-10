# SPDX-License-Identifier: LGPL-2.1-or-later
# Az Design Native independent file-level patch applicator.
# Run by the separate GUI updater AFTER it exits; never while FreeCAD runs.
param(
    [Parameter(Mandatory=$true)][string]$InstallDir,
    [string]$PatchZip,
    [switch]$RollbackLatest,
    [switch]$NoUI
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Notify([string]$message, [bool]$success) {
    Write-Host $message
    if (-not $NoUI) {
        Add-Type -AssemblyName System.Windows.Forms
        $icon = if ($success) { [Windows.Forms.MessageBoxIcon]::Information } else { [Windows.Forms.MessageBoxIcon]::Error }
        [Windows.Forms.MessageBox]::Show($message, "Az Design Native Update",
            [Windows.Forms.MessageBoxButtons]::OK, $icon) | Out-Null
    }
}

function Hash-File([string]$path) {
    return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Safe-Path([string]$relative) {
    if ([string]::IsNullOrWhiteSpace($relative) -or
        $relative.StartsWith('/') -or $relative.Contains('\') -or
        $relative.Contains(':') -or $relative.Contains([char]0)) {
        throw "Invalid native patch path: $relative"
    }
    $parts = $relative.Split('/')
    if ($parts | Where-Object { $_ -eq '..' -or $_ -eq '.' -or $_ -eq '' }) {
        throw "Unsafe native patch traversal: $relative"
    }
    if ($parts[0] -match '^(unins.*|AZ Native Version\.json|patch\.json)$') {
        throw "Cannot patch Windows uninstall metadata or app version marker directly: $relative"
    }
    return $relative.Replace('/', [IO.Path]::DirectorySeparatorChar)
}

function Native-Running([string]$root) {
    foreach ($name in @("FreeCAD", "AzDesign", "AzUpdater")) {
        foreach ($process in @(Get-Process -Name $name -ErrorAction SilentlyContinue)) {
            try {
                $path = $process.Path
                if ($path -and $path.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
                    return $true
                }
            } catch { }
        }
    }
    return $false
}

function Write-Json([string]$path, $data) {
    $text = $data | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText($path, $text, [Text.UTF8Encoding]::new($false))
}

function Apply-Rollback([string]$root, [string]$statePath, [string]$lastPath) {
    if (!(Test-Path -LiteralPath $lastPath)) { throw "There is no previous update to roll back." }
    $last = Get-Content -LiteralPath $lastPath -Raw | ConvertFrom-Json
    $backup = [IO.Path]::GetFullPath($last.backup_dir)
    $expectedRoot = [IO.Path]::GetFullPath((Split-Path -Parent $lastPath)) + '\'
    if (!$backup.StartsWith($expectedRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Backup folder is not inside Az Design's updates directory."
    }
    if (!(Test-Path -LiteralPath $backup)) { throw "Rollback backup no longer exists." }
    foreach ($item in @($last.touched)) {
        $relative = Safe-Path ([string]$item.path)
        $target = Join-Path $root $relative
        if ($item.existed) {
            $original = Join-Path $backup $relative
            if (!(Test-Path -LiteralPath $original)) { throw "Backup missing: $relative" }
            [IO.Directory]::CreateDirectory((Split-Path -Parent $target)) | Out-Null
            Copy-Item -LiteralPath $original -Destination $target -Force
        } elseif (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Force
        }
    }
    Write-Json $statePath @{ version = [string]$last.from_version; product = 'AzDesignNative' }
    Remove-Item -LiteralPath $lastPath -Force
    Notify "Restored Az Design Native $($last.from_version). You can launch the application." $true
}

$staging = $null
$zip = $null
$touched = New-Object System.Collections.ArrayList
$modifying = $false
try {
    $root = (Resolve-Path -LiteralPath $InstallDir).Path.TrimEnd('\')
    if (!(Test-Path -LiteralPath (Join-Path $root "bin\FreeCAD.exe"))) {
        throw "This is not an Az Design Native application directory."
    }
    $versionPath = Join-Path $root "AZ Native Version.json"
    if (!(Test-Path -LiteralPath $versionPath)) {
        throw "This installation was not created by the Az Design Windows installer."
    }
    $state = Get-Content -LiteralPath $versionPath -Raw | ConvertFrom-Json
    if ($state.product -ne 'AzDesignNative') { throw "Wrong application version marker." }
    $updates = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) "AzDesign\Updates"
    [IO.Directory]::CreateDirectory($updates) | Out-Null
    $lastPath = Join-Path $updates "last_success.json"

    # The GUI updater exits before this independent PowerShell process begins.
    for ($i=0; $i -lt 20 -and (Native-Running $root); $i++) {
        Start-Sleep -Milliseconds 500
    }
    if (Native-Running $root) {
        throw "Close Az Design Native before applying or rolling back this update."
    }
    if ($RollbackLatest) {
        Apply-Rollback $root $versionPath $lastPath
        exit 0
    }
    if (!(Test-Path -LiteralPath $PatchZip -PathType Leaf)) { throw "Select a valid Az Native patch ZIP." }
    $zip = [IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $PatchZip).Path)
    $index = $zip.GetEntry("patch.json")
    if ($null -eq $index) { throw "Patch missing patch.json manifest." }
    $reader = [IO.StreamReader]::new($index.Open())
    try { $manifest = $reader.ReadToEnd() | ConvertFrom-Json }
    finally { $reader.Dispose() }
    if ([int]$manifest.format -ne 1 -or $manifest.product -ne "AzDesignNative") {
        throw "Incompatible Az Native patch package."
    }
    if ([string]$manifest.from_version -ne [string]$state.version) {
        throw "Patch is for version $($manifest.from_version), but you have $($state.version)."
    }
    if ([string]::IsNullOrWhiteSpace($manifest.to_version) -or
        [string]$manifest.to_version -eq [string]$state.version) {
        throw "Patch version has no valid destination."
    }
    if ($zip.Entries.Count -gt 50000) { throw "Patch has too many files." }
    $expectedEntries = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    [void]$expectedEntries.Add("patch.json")
    $seenPaths = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    $all = @()
    foreach ($item in @($manifest.files)) {
        $rel = [string]$item.path
        $safe = Safe-Path $rel
        if (!$seenPaths.Add($rel)) { throw "Duplicate patch path: $rel" }
        $name = "files/" + $rel
        if (!$expectedEntries.Add($name)) { throw "Duplicate ZIP entry: $name" }
        $entry = $zip.GetEntry($name)
        if ($null -eq $entry -or $entry.Length -ne [long]$item.size) {
            throw "Patch payload missing or wrong size: $rel"
        }
        if ([string]$item.after -notmatch '^[a-fA-F0-9]{64}$' -or
            ($null -ne $item.before -and [string]$item.before -notmatch '^[a-fA-F0-9]{64}$')) {
            throw "Invalid SHA256 manifest for $rel"
        }
        $all += @{ path=$rel; safe=$safe; before=$item.before; after=$item.after; entry=$entry; delete=$false }
    }
    foreach ($item in @($manifest.delete)) {
        $rel = [string]$item.path
        $safe = Safe-Path $rel
        if (!$seenPaths.Add($rel)) { throw "Duplicate patch/delete path: $rel" }
        if ([string]$item.before -notmatch '^[a-fA-F0-9]{64}$') {
            throw "Missing delete baseline SHA256 for $rel"
        }
        $all += @{ path=$rel; safe=$safe; before=$item.before; delete=$true }
    }
    # Reject hidden extra ZIP content, including malicious relative paths.
    foreach ($entry in $zip.Entries) {
        if ($entry.FullName.EndsWith('/')) { continue }
        if (!$expectedEntries.Contains($entry.FullName)) {
            throw "Unexpected ZIP content: $($entry.FullName)"
        }
    }
    $staging = Join-Path $updates ("stage-" + [guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($staging) | Out-Null
    foreach ($item in $all) {
        $target = Join-Path $root $item.safe
        $exists = Test-Path -LiteralPath $target -PathType Leaf
        if ($null -eq $item.before) {
            if ($exists) { throw "New patch file unexpectedly already exists: $($item.path)" }
        } else {
            if (!$exists -or (Hash-File $target) -ne ([string]$item.before).ToLowerInvariant()) {
                throw "Local file differs from update baseline: $($item.path). Update refused."
            }
        }
        if (!$item.delete) {
            $stageFile = Join-Path $staging $item.safe
            [IO.Directory]::CreateDirectory((Split-Path -Parent $stageFile)) | Out-Null
            $sourceStream = $item.entry.Open()
            $outStream = [IO.File]::Create($stageFile)
            try { $sourceStream.CopyTo($outStream) }
            finally { $outStream.Dispose(); $sourceStream.Dispose() }
            if ((Hash-File $stageFile) -ne ([string]$item.after).ToLowerInvariant()) {
                throw "Downloaded patch content failed SHA256: $($item.path)"
            }
        }
    }
    $zip.Dispose()
    $zip = $null
    $backup = Join-Path $updates ("backup-" + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + "-" + [guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($backup) | Out-Null
    # Capture all existing files BEFORE changing anything. Rollback is atomic
    # from the user's perspective if a copied DLL or file ever fails.
    foreach ($item in $all) {
        $target = Join-Path $root $item.safe
        $exists = Test-Path -LiteralPath $target -PathType Leaf
        if ($exists) {
            $backupFile = Join-Path $backup $item.safe
            [IO.Directory]::CreateDirectory((Split-Path -Parent $backupFile)) | Out-Null
            Copy-Item -LiteralPath $target -Destination $backupFile
        }
        [void]$touched.Add(@{ path=$item.path; existed=$exists })
    }
    $modifying = $true
    foreach ($item in $all) {
        $target = Join-Path $root $item.safe
        if ($item.delete) {
            Remove-Item -LiteralPath $target -Force
        } else {
            [IO.Directory]::CreateDirectory((Split-Path -Parent $target)) | Out-Null
            Copy-Item -LiteralPath (Join-Path $staging $item.safe) -Destination $target -Force
            if ((Hash-File $target) -ne ([string]$item.after).ToLowerInvariant()) {
                throw "Post-install checksum mismatch: $($item.path)"
            }
        }
    }
    Write-Json $versionPath @{ version = [string]$manifest.to_version; product = "AzDesignNative" }
    $record = @{
        backup_dir = $backup; from_version = [string]$manifest.from_version
        to_version = [string]$manifest.to_version; touched = @($touched.ToArray())
    }
    Write-Json $lastPath $record
    $modifying = $false
    Notify "Updated Az Design Native to $($manifest.to_version). Restart it from the Start Menu. A rollback backup is available." $true
    exit 0
}
catch {
    $problem = $_.Exception.Message
    if ($modifying) {
        try {
            foreach ($item in @($touched)) {
                $rel = Safe-Path ([string]$item.path)
                $target = Join-Path $root $rel
                if ($item.existed) {
                    $original = Join-Path $backup $rel
                    Copy-Item -LiteralPath $original -Destination $target -Force
                } elseif (Test-Path -LiteralPath $target) {
                    Remove-Item -LiteralPath $target -Force
                }
            }
        } catch {
            $problem += " Rollback also encountered an error: " + $_.Exception.Message
        }
    }
    Notify ("Update not applied: " + $problem) $false
    exit 1
}
finally {
    if ($zip) { $zip.Dispose() }
    if ($staging -and (Test-Path -LiteralPath $staging)) {
        Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
    }
}
