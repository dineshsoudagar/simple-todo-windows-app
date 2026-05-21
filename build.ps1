$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

python -m PyInstaller --noconfirm --clean --windowed --onefile --name SimpleTodo --collect-submodules webview app.py

Write-Host ""
Write-Host "Built: $Root\dist\SimpleTodo.exe"
Write-Host "Run .\install.ps1 to install it for the current Windows user."
