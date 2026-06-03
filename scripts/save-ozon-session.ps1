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

$pythonCode = @'
from pathlib import Path
import sys
from urllib.parse import quote_plus

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


output = Path(sys.argv[1]).resolve()
query = "iphone"
user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)


def is_antibot_page(html: str) -> bool:
    lowered = html.lower()
    return "antibot challenge" in lowered or "abt-challenge" in lowered or "captcha" in lowered


def ozon_cookie_count(context) -> int:
    return len([cookie for cookie in context.cookies() if "ozon" in cookie.get("domain", "")])


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(locale="ru-RU", user_agent=user_agent)
    page = context.new_page()
    search_url = f"https://www.ozon.ru/search/?text={quote_plus(query)}&from_global=true"
    composer_url = (
        "https://www.ozon.ru/api/composer-api.bx/page/json/v2"
        f"?url=/search/?text={quote_plus(query)}&from_global=true"
    )

    while True:
        response = page.goto(search_url, wait_until="domcontentloaded")
        print("")
        print("In the opened browser, make sure Ozon shows real search results, not a captcha or access page.")
        print("If needed, sign in or finish the access check. Then return here and press Enter.")
        command = input("Press Enter to validate the Ozon session, or type q to cancel: ").strip().lower()
        if command in {"q", "quit", "exit"}:
            browser.close()
            raise SystemExit(1)

        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except PlaywrightTimeoutError:
            pass

        status_code = response.status if response else 0
        html = page.content()
        product_links = page.locator('a[href*="/product/"]').count()
        cookie_count = ozon_cookie_count(context)
        composer_status = 0
        try:
            composer_status = context.request.get(composer_url, timeout=12000).status
        except Exception:
            composer_status = 0

        blocked = status_code in {403, 429} or composer_status in {403, 429} or is_antibot_page(html)
        if not blocked and (product_links > 0 or (200 <= composer_status < 400)):
            context.storage_state(path=str(output))
            print(
                "Validated Ozon session: "
                f"page={status_code}, composer={composer_status}, products={product_links}, cookies={cookie_count}"
            )
            browser.close()
            break

        print(
            "Ozon session is still not usable: "
            f"page={status_code}, composer={composer_status}, products={product_links}, cookies={cookie_count}."
        )
        print("Keep the browser open, finish Ozon access until product cards are visible, then try validation again.")

print(f"Saved Ozon storage state: {output}")
'@

& $Python -c $pythonCode $ResolvedOutput

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
