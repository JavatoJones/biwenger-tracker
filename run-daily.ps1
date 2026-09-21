# Actualiza los datos de la liga. Uso: .\run-daily.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = "utf-8"

if (-not (Test-Path .venv)) {
    & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
}

Get-Content .env | Where-Object { $_ -match '^\s*[^#\s][^=]*=' } | ForEach-Object {
    $k, $v = $_ -split '=', 2
    Set-Item -Path "Env:$($k.Trim())" -Value $v.Trim()
}
& .\.venv\Scripts\python.exe -m scraper.daily
