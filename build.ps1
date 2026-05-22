$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

python -m PyInstaller --noconfirm --clean --windowed --onefile --name TODO-Tasks --collect-submodules webview app.py

Copy-Item -LiteralPath (Join-Path $Root 'dist\TODO-Tasks.exe') -Destination (Join-Path $Root 'TODO-Tasks.exe') -Force

Write-Host ""
Write-Host "Built: $Root\dist\TODO-Tasks.exe"
Write-Host "Copied: $Root\TODO-Tasks.exe"
Write-Host "You can run TODO-Tasks.exe directly. No install step is required."
