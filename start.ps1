param(
    [ValidateSet("mock", "hybrid", "real")]
    [string]$ParserMode = "real",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $root ".runtime"
$apiDir = Join-Path $root "apps\api"
$webDir = Join-Path $root "apps\web"
$parserDir = Join-Path $root "services\parser"
$pythonExe = Join-Path $apiDir ".venv\Scripts\python.exe"
$databasePath = Join-Path $runtimeDir "local_appsparcer.sqlite3"

function Assert-Command($Name, $InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is not installed or not available in PATH. $InstallHint"
    }
}

function Get-NpmCommand {
    $npm = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
    if ($npm) {
        return $npm.Source
    }
    $npm = Get-Command "npm" -ErrorAction SilentlyContinue
    if ($npm) {
        return $npm.Source
    }
    throw "npm is not installed or not available in PATH. Install Node.js LTS and run this command again."
}

function Assert-PortFree($Port, $Name) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        throw "$Name port $Port is already in use. Stop the process using it and run this command again."
    }
}

function Test-HttpOk($Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    }
    catch {
        return $false
    }
}

function Read-DotEnv($Path) {
    $values = @{}
    if (-not (Test-Path -LiteralPath $Path)) {
        return $values
    }
    Get-Content -LiteralPath $Path | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $values[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    return $values
}

function Resolve-LocalEnvPath($Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $Value
    }
    if ($Value.StartsWith("/app/.runtime/")) {
        $fileName = Split-Path -Leaf $Value
        return Join-Path $runtimeDir $fileName
    }
    if ([System.IO.Path]::IsPathRooted($Value)) {
        return $Value
    }
    return Join-Path $root $Value
}

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

if (-not (Test-Path -LiteralPath $pythonExe)) {
    Assert-Command "python" "Install Python 3.12+ and run this command again."
    Write-Host "Creating Python virtual environment..."
    python -m venv (Join-Path $apiDir ".venv")
}

$npmCommand = Get-NpmCommand

if (-not $SkipInstall) {
    $backendDependenciesReady = (Test-Path -LiteralPath (Join-Path $apiDir ".venv\Lib\site-packages\fastapi")) -and
        (Test-Path -LiteralPath (Join-Path $apiDir ".venv\Lib\site-packages\playwright"))
    if (-not $backendDependenciesReady) {
        Write-Host "Installing backend dependencies..."
        & $pythonExe -m pip install -r (Join-Path $apiDir "requirements.txt")
    }

    if ($ParserMode -eq "real") {
        Write-Host "Ensuring backend browser runtime is installed..."
        & $pythonExe -m playwright install chromium
    }

    if (-not (Test-Path -LiteralPath (Join-Path $webDir "node_modules"))) {
        Write-Host "Installing frontend dependencies..."
        Push-Location $webDir
        try {
            & $npmCommand install
        }
        finally {
            Pop-Location
        }
    }
}

$apiAlreadyRunning = Test-HttpOk "http://localhost:8000/health"
$webAlreadyRunning = Test-HttpOk "http://localhost:5173"

if ($apiAlreadyRunning -and $webAlreadyRunning) {
    Write-Host ""
    Write-Host "Appsparcer already appears to be running locally."
    Write-Host "Web:      http://localhost:5173"
    Write-Host "API docs: http://localhost:8000/docs"
    Write-Host ""
    return
}

Assert-PortFree 8000 "API"
Assert-PortFree 5173 "Web"

$apiEnv = @{
    "AUTO_CREATE_TABLES" = "true"
    "CORS_ORIGINS" = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    "DATABASE_URL" = "sqlite:///$($databasePath.Replace('\', '/'))"
    "JWT_SECRET" = "local-dev-secret"
    "PARSER_BROWSER_429_DELAY_SECONDS" = "10"
    "PARSER_BROWSER_429_RETRIES" = "1"
    "PARSER_BROWSER_FALLBACK" = "true"
    "PARSER_MIN_INTERVAL_SECONDS" = "2.5"
    "PARSER_MODE" = $ParserMode
    "PARSER_WB_429_DELAY_SECONDS" = "10"
    "PARSER_WB_429_RETRIES" = "1"
    "PYTHONPATH" = "$apiDir;$parserDir"
    "REDIS_URL" = "redis://127.0.0.1:6390/0"
}

$dotEnv = Read-DotEnv (Join-Path $root ".env")
foreach ($key in @("OZON_COOKIES", "OZON_COOKIES_FILE", "OZON_STORAGE_STATE_FILE", "PARSER_HTTP_PROXY", "PARSER_USER_AGENT", "WILDBERRIES_COOKIES", "WILDBERRIES_COOKIES_FILE", "WILDBERRIES_STORAGE_STATE_FILE", "WILDBERRIES_DEST")) {
    if ($dotEnv.ContainsKey($key) -and -not [string]::IsNullOrWhiteSpace($dotEnv[$key])) {
        $apiEnv[$key] = [string]$dotEnv[$key]
    }
}

foreach ($pathKey in @("OZON_COOKIES_FILE", "OZON_STORAGE_STATE_FILE", "WILDBERRIES_COOKIES_FILE", "WILDBERRIES_STORAGE_STATE_FILE")) {
    if ($apiEnv.ContainsKey($pathKey)) {
        $apiEnv[$pathKey] = Resolve-LocalEnvPath ([string]$apiEnv[$pathKey])
    }
}

$defaultOzonStatePath = Join-Path $runtimeDir "ozon-storage-state.json"
if ((Test-Path -LiteralPath $defaultOzonStatePath) -and -not $apiEnv.ContainsKey("OZON_STORAGE_STATE_FILE")) {
    $apiEnv["OZON_STORAGE_STATE_FILE"] = $defaultOzonStatePath
}

$webEnv = @{
    "VITE_API_URL" = "/api"
}

Write-Host ""
Write-Host "Starting Appsparcer locally without Docker..."
Write-Host "Web:      http://localhost:5173"
Write-Host "API docs: http://localhost:8000/docs"
Write-Host "Database: $databasePath"
Write-Host "Parser:   $ParserMode"
Write-Host ""
Write-Host "Press Ctrl+C to stop API and Web."
Write-Host ""

$jobs = @()

try {
    $jobs += Start-Job -Name "appsparcer-api" -ArgumentList $apiDir, $pythonExe, $apiEnv -ScriptBlock {
        param($WorkingDirectory, $Python, $Environment)
        Set-Location $WorkingDirectory
        foreach ($key in $Environment.Keys) {
            [Environment]::SetEnvironmentVariable($key, [string]$Environment[$key], "Process")
        }
        & $Python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    }

    $jobs += Start-Job -Name "appsparcer-web" -ArgumentList $webDir, $npmCommand, $webEnv -ScriptBlock {
        param($WorkingDirectory, $Npm, $Environment)
        Set-Location $WorkingDirectory
        foreach ($key in $Environment.Keys) {
            [Environment]::SetEnvironmentVariable($key, [string]$Environment[$key], "Process")
        }
        & $Npm run dev -- --host 127.0.0.1
    }

    while ($true) {
        foreach ($job in $jobs) {
            Receive-Job -Job $job
        }

        $stopped = $jobs | Where-Object { $_.State -in @("Completed", "Failed", "Stopped") } | Select-Object -First 1
        if ($stopped) {
            foreach ($job in $jobs) {
                Receive-Job -Job $job -ErrorAction SilentlyContinue
            }
            throw "$($stopped.Name) stopped with state $($stopped.State)."
        }

        Start-Sleep -Seconds 1
    }
}
finally {
    foreach ($job in $jobs) {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
}
