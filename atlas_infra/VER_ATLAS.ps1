# Preview do Atlas Vivo MILK — arranca o mock server local.
# Executar:  powershell -NoProfile -ExecutionPolicy Bypass -File .\VER_ATLAS.ps1
# Depois abrir: http://127.0.0.1:8070   (Ctrl+C para parar)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $here ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$script = Join-Path $here "preview_atlas.py"
if (-not (Test-Path $script)) { $script = Join-Path $here "atlas_infra\preview_atlas.py" }
& $py $script
