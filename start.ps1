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

$dockerInfo = docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Docker is installed, but the Docker engine is not running. Start Docker Desktop and run this command again."
}

$composeVersion = docker compose version 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose v2 is not available. Update Docker Desktop and run this command again."
}

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host ""
Write-Host "Starting Appsparcer..."
Write-Host "Web:      http://localhost:3000"
Write-Host "API docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "Parser mode is controlled by PARSER_MODE in .env. Current production default is real."
Write-Host "For stable real marketplace collection, set OZON_COOKIES/WILDBERRIES_COOKIES and/or PARSER_HTTP_PROXY in .env."
Write-Host ""

$args = @("compose", "up", "--build", "--remove-orphans")
if ($Detached) {
    $args += "-d"
}

& docker @args
