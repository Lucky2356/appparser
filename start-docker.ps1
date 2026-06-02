param(
    [switch]$Detached
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Stop-WithMessage($Message) {
    Write-Host ""
    Write-Host $Message
    Write-Host ""
    Write-Host "For a quick local check without Docker, run:"
    Write-Host ".\start.cmd"
    Write-Host ""
    exit 1
}

function Assert-Command($Name, $InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Stop-WithMessage "$Name is not installed or not available in PATH. $InstallHint"
    }
}

Assert-Command "docker" "Install Docker Desktop and start it before running this script."

cmd /c "docker info >nul 2>nul"
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Docker is installed, but the Docker engine is not running. Start Docker Desktop and run .\start-docker.cmd again."
}

cmd /c "docker compose version >nul 2>nul"
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Docker Compose v2 is not available. Update Docker Desktop and run .\start-docker.cmd again."
}

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "Created .env from .env.example"
}

function Ensure-EnvValue($Name, $Value) {
    $envPath = Join-Path $root ".env"
    $content = Get-Content -LiteralPath $envPath -ErrorAction SilentlyContinue
    if ($content -match "^$([regex]::Escape($Name))=") {
        return
    }
    Add-Content -LiteralPath $envPath -Value "$Name=$Value"
    Write-Host "Added $Name=$Value to .env"
}

Ensure-EnvValue "POSTGRES_PORT" "55432"
Ensure-EnvValue "REDIS_PORT" "56379"
Ensure-EnvValue "API_PORT" "8001"
Ensure-EnvValue "WEB_PORT" "3000"

$envValues = @{}
Get-Content -LiteralPath ".env" | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
        $envValues[$matches[1].Trim()] = $matches[2].Trim()
    }
}

$apiPort = if ($envValues.ContainsKey("API_PORT")) { $envValues["API_PORT"] } else { "8001" }
$webPort = if ($envValues.ContainsKey("WEB_PORT")) { $envValues["WEB_PORT"] } else { "3000" }

Write-Host ""
Write-Host "Starting Appsparcer with Docker..."
Write-Host "Web:      http://localhost:$webPort"
Write-Host "API docs: http://localhost:$apiPort/docs"
Write-Host ""

$args = @("compose", "up", "--build", "--remove-orphans")
if ($Detached) {
    $args += "-d"
}

& docker @args
