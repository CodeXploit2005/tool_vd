$ErrorActionPreference = 'Stop'
$musePath = Join-Path $PSScriptRoot 'muse2api-local'
$pythonPath = Join-Path $musePath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Muse2API Python environment is missing. See RUN-MOONREEL.md for setup.'
}
if (-not (Test-Path -LiteralPath (Join-Path $musePath '.env'))) {
    throw 'Muse2API .env is missing. See RUN-MOONREEL.md for setup.'
}

# Confirm the API accepts MoonReel's key before reusing a running server.
$studioEnv = Join-Path $PSScriptRoot 'moonreel\moonreel-studio\.env'
$keyLine = Get-Content -LiteralPath $studioEnv | Where-Object { $_ -match '^\s*MUSE2API_KEY\s*=' } | Select-Object -Last 1
if (-not $keyLine) { throw 'MUSE2API_KEY is missing from the studio .env.' }
$apiKey = ($keyLine -split '=', 2)[1].Trim().Trim([char]34, [char]39)
if (-not $apiKey) { throw 'MUSE2API_KEY is empty.' }
$headers = @{ Authorization = "Bearer $apiKey" }
function Test-MuseReady {
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:18610/healthz' -TimeoutSec 3
        $models = Invoke-RestMethod 'http://127.0.0.1:18610/v1/models' -Headers $headers -TimeoutSec 3
        return ($health.status -eq 'ok' -and $models.object -eq 'list')
    } catch { return $false }
}
if (Test-MuseReady) {
    Write-Host 'Muse2API ready: http://localhost:18610/admin'
    return
}
if (Get-NetTCPConnection -State Listen -LocalPort 18610 -ErrorAction SilentlyContinue) {
    throw 'Port 18610 is occupied or the API key does not match. Check Muse2API before restarting.'
}
$process = Start-Process -FilePath $pythonPath -ArgumentList '-m uvicorn app:app --host 127.0.0.1 --port 18610' -WorkingDirectory $musePath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $musePath 'muse.log') -RedirectStandardError (Join-Path $musePath 'muse-error.log') -PassThru
$process.Id | Set-Content -LiteralPath (Join-Path $musePath 'muse.pid')
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if ($process.HasExited) { throw 'Muse2API stopped. Check muse2api-local\muse-error.log.' }
    if (Test-MuseReady) {
        Write-Host 'Muse2API ready: http://localhost:18610/admin'
        return
    }
    Start-Sleep -Seconds 1
}
throw 'Muse2API did not become ready. Check muse2api-local\muse-error.log.'
