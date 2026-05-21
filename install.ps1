$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceExe = Join-Path $Root 'dist\SimpleTodo.exe'
$InstallDir = Join-Path $env:LOCALAPPDATA 'SimpleTodo'
$TargetExe = Join-Path $InstallDir 'SimpleTodo.exe'
$LauncherScript = Join-Path $InstallDir 'SimpleTodoLauncher.vbs'
$StartMenuDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$ShortcutPath = Join-Path $StartMenuDir 'Simple Todo.lnk'
$CmdLauncherPath = Join-Path $StartMenuDir 'Simple Todo.cmd'

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
$shortcut.Description = 'Simple Todo'
$shortcut.Save()

Write-Host "Installed Simple Todo to: $TargetExe"
Write-Host "Start Menu shortcut: $ShortcutPath"
