$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "== Backend: entorno virtual y librerias ==" -ForegroundColor Cyan
Set-Location "$root\backend"
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

if (-not (Test-Path "data\visitantes.sqlite")) {
    Copy-Item "data\visitantes_prueba.sqlite" "data\visitantes.sqlite"
}

Write-Host "== Frontend: dependencias de npm ==" -ForegroundColor Cyan
Set-Location "$root\frontend-vr"
npm install

Set-Location $root
Write-Host "Instalacion completa. Para arrancar: .\iniciar.ps1" -ForegroundColor Green
