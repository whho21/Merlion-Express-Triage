# Windows PowerShell / PowerShell 7. Checks prerequisites before starting services; arguments match start.sh.
$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$ProjectPython = Join-Path $ProjectDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $ProjectPython -PathType Leaf)) {
    Write-Host '[ ] Project Python environment missing. Follow backend/api_service/backend_API_setup.md.'
    exit 1
}
& $ProjectPython (Join-Path $PSScriptRoot 'start_services.py') @args
exit $LASTEXITCODE
