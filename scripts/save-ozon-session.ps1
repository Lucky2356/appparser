param(
  [string]$OutputPath = ".runtime\ozon-storage-state.json"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ApiDir = Join-Path $RepoRoot "apps\api"
$ParserDir = Join-Path $RepoRoot "services\parser"
$Python = Join-Path $ApiDir ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
  $Python = "python"
}

$ResolvedOutput = if ([System.IO.Path]::IsPathRooted($OutputPath)) {
  $OutputPath
} else {
  Join-Path $RepoRoot $OutputPath
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ResolvedOutput) | Out-Null
$env:PYTHONPATH = "$ApiDir;$ParserDir"

@'
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright


output = Path(sys.argv[1]).resolve()
user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(locale="ru-RU", user_agent=user_agent)
    page = context.new_page()
    page.goto("https://www.ozon.ru/search/?text=iphone&from_global=true", wait_until="domcontentloaded")
    input("Finish Ozon access in the opened browser, then press Enter here...")
    context.storage_state(path=str(output))
    browser.close()

print(f"Saved Ozon storage state: {output}")
'@ | & $Python - $ResolvedOutput

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$EnvPath = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $EnvPath)) {
  Copy-Item -LiteralPath (Join-Path $RepoRoot ".env.example") -Destination $EnvPath
  Write-Host "Created .env from .env.example"
}

function Set-EnvValue($Name, $Value) {
  $content = Get-Content -LiteralPath $EnvPath -ErrorAction SilentlyContinue
  $pattern = "^$([regex]::Escape($Name))="
  if ($content -match $pattern) {
    $updated = $content | ForEach-Object {
      if ($_ -match $pattern) { "$Name=$Value" } else { $_ }
    }
    Set-Content -LiteralPath $EnvPath -Value $updated
    return
  }
  Add-Content -LiteralPath $EnvPath -Value "$Name=$Value"
}

$repoFullPath = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd('\')
$outputFullPath = [System.IO.Path]::GetFullPath($ResolvedOutput)
if ($outputFullPath.StartsWith($repoFullPath, [System.StringComparison]::OrdinalIgnoreCase)) {
  $relativeOutput = $outputFullPath.Substring($repoFullPath.Length).TrimStart('\')
  $dockerPath = "/app/" + ($relativeOutput -replace "\\", "/")
  Set-EnvValue "OZON_STORAGE_STATE_FILE" $dockerPath
  Set-EnvValue "PARSER_BROWSER_FALLBACK" "true"
  Write-Host "Updated .env: OZON_STORAGE_STATE_FILE=$dockerPath"
}
else {
  Write-Host "Saved session outside repo. Set OZON_STORAGE_STATE_FILE manually so Docker can access it."
}
