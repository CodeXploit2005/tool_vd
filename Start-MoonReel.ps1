param([switch]$Rebuild)

$ErrorActionPreference = 'Stop'
$studioPath = Join-Path $PSScriptRoot 'moonreel\moonreel-studio'
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $env:Path
Set-Location -LiteralPath $studioPath
$nodePath = (Get-Command node.exe).Source

# PostgreSQL and Muse2API both run directly on Windows; Docker is not required.
$pgBinPath = 'C:\Program Files\PostgreSQL\18\bin'
$pgDataPath = Join-Path $PSScriptRoot 'moonreel-data\postgres-windows'
if (-not (Test-Path -LiteralPath "$pgDataPath\PG_VERSION")) {
    throw 'MoonReel Windows database is missing. Restore the database before starting.'
}
& "$pgBinPath\pg_ctl.exe" -D $pgDataPath status *> $null
if ($LASTEXITCODE -ne 0) {
    & "$pgBinPath\pg_ctl.exe" -D $pgDataPath -l (Join-Path $PSScriptRoot 'moonreel-data\postgres-startup.log') -w start
    if ($LASTEXITCODE -ne 0) { throw 'Could not start the MoonReel Windows database.' }
}
& $nodePath --env-file=.env scripts/check-database.mjs
if ($LASTEXITCODE -ne 0) { throw 'MoonReel database check failed. See the message above.' }

& (Join-Path $PSScriptRoot 'Start-Muse2API.ps1')

# Build once, then serve the optimized app instead of compiling pages in next dev.
# Use Start-MoonReel.ps1 -Rebuild after changing application source.
if ($Rebuild -or -not (Test-Path -LiteralPath '.next\BUILD_ID')) {
    # Never overwrite the build while its server is still serving old manifests.
    if (Test-Path -LiteralPath 'web.pid') {
        $previousWebId = [int](Get-Content -LiteralPath 'web.pid')
        $previousWeb = Get-CimInstance Win32_Process -Filter "ProcessId = $previousWebId" -ErrorAction SilentlyContinue
        if ($previousWeb -and $previousWeb.CommandLine -like '*node_modules/next/dist/bin/next start*') {
            Stop-Process -Id $previousWebId -Force
            Wait-Process -Id $previousWebId -ErrorAction SilentlyContinue
        }
    }
    # Windows can briefly report the old listener after its process has exited.
    for ($portAttempt = 0; $portAttempt -lt 10; $portAttempt++) {
        if (-not (Get-NetTCPConnection -State Listen -LocalPort 3000 -ErrorAction SilentlyContinue)) { break }
        Start-Sleep -Milliseconds 300
    }
    if (Get-NetTCPConnection -State Listen -LocalPort 3000 -ErrorAction SilentlyContinue) {
        throw 'Port 3000 is still in use. Stop that web server before rebuilding MoonReel.'
    }
    $env:NEXT_DEPLOYMENT_ID = [guid]::NewGuid().ToString('N')
    & $nodePath node_modules/next/dist/bin/next build
    if ($LASTEXITCODE -ne 0) { throw 'MoonReel production build failed.' }
    $env:NEXT_DEPLOYMENT_ID | Set-Content -LiteralPath '.next\DEPLOYMENT_ID'
}
if (Test-Path -LiteralPath '.next\DEPLOYMENT_ID') {
    $env:NEXT_DEPLOYMENT_ID = (Get-Content -LiteralPath '.next\DEPLOYMENT_ID' -Raw).Trim()
}
$webReady = $false
try { $webReady = (Invoke-WebRequest 'http://localhost:3000/' -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200 } catch {}
if (-not $webReady) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort 3000 -ErrorAction SilentlyContinue
    if ($listener) { throw 'Port 3000 is occupied by a server that is not responding. Close it before reopening MoonReel.' }
    $webProcess = Start-Process -FilePath $nodePath -ArgumentList 'node_modules/next/dist/bin/next start' -WorkingDirectory $studioPath -WindowStyle Hidden -RedirectStandardOutput "$studioPath\web.log" -RedirectStandardError "$studioPath\web-error.log" -PassThru
    $webProcess.Id | Set-Content 'web.pid'
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if ($webProcess.HasExited) { throw 'MoonReel web server stopped. Check web-error.log.' }
        try { $webReady = (Invoke-WebRequest 'http://localhost:3000/' -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 } catch {}
        if ($webReady) { break }
        Start-Sleep -Seconds 1
    }
    if (-not $webReady) { throw 'MoonReel web server did not become ready. Check web-error.log.' }
}

$workerRunning = $false
if (Test-Path -LiteralPath 'worker.pid') {
    $workerProcessId = [int](Get-Content 'worker.pid')
    $workerProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $workerProcessId" -ErrorAction SilentlyContinue
    $workerRunning = $workerProcess -and $workerProcess.CommandLine -like '*src/worker/index.ts*'
}
if (-not $workerRunning) {
    $workerProcess = Start-Process -FilePath $nodePath -ArgumentList '--env-file=.env node_modules/tsx/dist/cli.mjs src/worker/index.ts' -WorkingDirectory $studioPath -WindowStyle Hidden -RedirectStandardOutput "$studioPath\worker.log" -RedirectStandardError "$studioPath\worker-error.log" -PassThru
    $workerProcess.Id | Set-Content 'worker.pid'
}
Start-Process 'http://localhost:3000/'
Write-Host 'MoonReel: http://localhost:3000/'
