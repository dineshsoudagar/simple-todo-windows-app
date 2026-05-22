param(
    [switch]$RemoveData
)

$ErrorActionPreference = 'Stop'

$InstallDir = Join-Path $env:LOCALAPPDATA 'TODO-Tasks'
$ShortcutPath = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\TODO-Tasks.lnk'
$LauncherPath = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\TODO-Tasks.cmd'
$DataDir = Join-Path $env:APPDATA 'TODO-Tasks'

if (Test-Path -LiteralPath $ShortcutPath) {
    Remove-Item -LiteralPath $ShortcutPath -Force
}

if (Test-Path -LiteralPath $LauncherPath) {
    Remove-Item -LiteralPath $LauncherPath -Force
}

if (Test-Path -LiteralPath $InstallDir) {
    Remove-Item -LiteralPath $InstallDir -Recurse -Force
}

if ($RemoveData -and (Test-Path -LiteralPath $DataDir)) {
    Remove-Item -LiteralPath $DataDir -Recurse -Force
}

Write-Host "TODO-Tasks has been uninstalled."
if (-not $RemoveData) {
    Write-Host "Task data was kept at: $DataDir"
}
