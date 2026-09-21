# Carga .env y ejecuta el descubrimiento. Uso: .\run-discover.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"

if (-not (Test-Path .venv)) { & $py -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt

Get-Content .env | Where-Object { $_ -match '^\s*[^#\s][^=]*=' } | ForEach-Object {
    $k, $v = $_ -split '=', 2
    Set-Item -Path "Env:$($k.Trim())" -Value $v.Trim()
}
& .\.venv\Scripts\python.exe -m scraper.discover
