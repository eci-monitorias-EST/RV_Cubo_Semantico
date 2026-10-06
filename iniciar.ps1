$root = $PSScriptRoot

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\backend'; & '.\.venv\Scripts\Activate.ps1'; uvicorn api:app --reload --port 8000"
)

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\frontend-vr'; npm run dev"
)

Write-Host "Backend en http://localhost:8000  |  Cubo en https://localhost:5173" -ForegroundColor Green
Write-Host "Para las gafas, usar la direccion 'Network' que muestra la ventana de Vite." -ForegroundColor Green
