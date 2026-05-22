$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceExe = Join-Path $Root 'dist\TODO-Tasks.exe'
$InstallDir = Join-Path $env:LOCALAPPDATA 'TODO-Tasks'
$TargetExe = Join-Path $InstallDir 'TODO-Tasks.exe'
$LauncherScript = Join-Path $InstallDir 'TODO-TasksLauncher.vbs'
$StartMenuDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$ShortcutPath = Join-Path $StartMenuDir 'TODO-Tasks.lnk'
$CmdLauncherPath = Join-Path $StartMenuDir 'TODO-Tasks.cmd'

if (-not (Test-Path -LiteralPath $SourceExe)) {
    throw "Build first: .\build.ps1"
}

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Copy-Item -LiteralPath $SourceExe -Destination $TargetExe -Force

$launcher = @"
Set shell = CreateObject("WScript.Shell")
shell.Run """$TargetExe""", 1, False
"@
Set-Content -LiteralPath $LauncherScript -Value $launcher -Encoding ASCII

if (Test-Path -LiteralPath $ShortcutPath) {
    Remove-Item -LiteralPath $ShortcutPath -Force
}

if (Test-Path -LiteralPath $CmdLauncherPath) {
    Remove-Item -LiteralPath $CmdLauncherPath -Force
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
$shortcut.Arguments = "`"$LauncherScript`""
$shortcut.WorkingDirectory = $InstallDir
$shortcut.Description = 'TODO-Tasks'
$shortcut.Save()

Write-Host "Installed TODO-Tasks to: $TargetExe"
Write-Host "Start Menu shortcut: $ShortcutPath"
