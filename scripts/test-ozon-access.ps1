param(
  [string]$Query = "iphone"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ApiDir = Join-Path $RepoRoot "apps\api"
$ParserDir = Join-Path $RepoRoot "services\parser"
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$Python = Join-Path $ApiDir ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
  $Python = "python"
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
    return Join-Path $RuntimeDir (Split-Path -Leaf $Value)
  }
  if ([System.IO.Path]::IsPathRooted($Value)) {
    return $Value
  }
  return Join-Path $RepoRoot $Value
}

$dotEnv = Read-DotEnv (Join-Path $RepoRoot ".env")
foreach ($key in @("PARSER_HTTP_PROXY", "PARSER_USER_AGENT", "PARSER_BROWSER_FALLBACK", "OZON_COOKIES", "OZON_COOKIES_FILE", "OZON_STORAGE_STATE_FILE")) {
  if ($dotEnv.ContainsKey($key)) {
    [Environment]::SetEnvironmentVariable($key, [string]$dotEnv[$key], "Process")
  }
}

foreach ($key in @("OZON_COOKIES_FILE", "OZON_STORAGE_STATE_FILE")) {
  $value = [Environment]::GetEnvironmentVariable($key, "Process")
  if (-not [string]::IsNullOrWhiteSpace($value)) {
    [Environment]::SetEnvironmentVariable($key, (Resolve-LocalEnvPath $value), "Process")
  }
}

$env:PARSER_MODE = "real"
$env:PYTHONPATH = "$ApiDir;$ParserDir"

@'
import sys

from market_parser.adapters.ozon import OzonAdapter
from market_parser.errors import AdapterUnavailableError
from market_parser.models import SearchParams


query = sys.argv[1]
adapter = OzonAdapter()
try:
    offers = adapter.search_products(SearchParams(query=query, marketplaces=["ozon"]))
except AdapterUnavailableError as exc:
    print(f"FAILED: {exc}")
    print(f"source={adapter.runtime.source} detail={adapter.runtime.detail}")
    raise SystemExit(1)

print(f"OK: {len(offers)} offers")
print(f"source={adapter.runtime.source} detail={adapter.runtime.detail}")
for offer in offers[:5]:
    print(f"- {offer.title[:90]} | {offer.price:.0f} | image={'yes' if offer.image_url else 'no'}")
'@ | & $Python - $Query

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
