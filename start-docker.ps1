param(
    [switch]$Detached
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Assert-Command($Name, $InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is not installed or not available in PATH. $InstallHint"
    }
}

Assert-Command "docker" "Install Docker Desktop and start it before running this script."

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker is installed, but the Docker engine is not running. Start Docker Desktop and run this command again."
}

docker compose version *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose v2 is not available. Update Docker Desktop and run this command again."
}

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host ""
Write-Host "Starting Appsparcer with Docker..."
Write-Host "Web:      http://localhost:3000"
Write-Host "API docs: http://localhost:8000/docs"
Write-Host ""

$args = @("compose", "up", "--build", "--remove-orphans")
if ($Detached) {
    $args += "-d"
}

& docker @args
