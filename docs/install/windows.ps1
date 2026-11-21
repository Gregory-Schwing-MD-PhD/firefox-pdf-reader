# One-step installer for Firefox PDF Reader on Windows.
# Downloads the latest version of the project, installs Firefox if needed,
# and runs windows\install.ps1. Used by FirefoxPDFReader-Setup.cmd and by:
#   powershell -c "irm https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/install/windows.ps1 | iex"
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Repo = 'Gregory-Schwing-MD-PhD/firefox-pdf-reader'

Write-Host 'Firefox PDF Reader setup' -ForegroundColor Cyan

# Firefox
$ff = @(
    (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\firefox.exe'),
    (Join-Path $env:ProgramFiles 'Mozilla Firefox\firefox.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Mozilla Firefox\firefox.exe'),
    (Join-Path $env:LOCALAPPDATA 'Mozilla Firefox\firefox.exe')
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $ff) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host '==> Firefox not found; installing it with winget' -ForegroundColor Cyan
        winget install --id Mozilla.Firefox -e --accept-source-agreements --accept-package-agreements
    } else {
        Write-Host 'Firefox is required. Install it from https://www.mozilla.org/firefox/ and run this again.' -ForegroundColor Yellow
        Start-Process 'https://www.mozilla.org/firefox/'
        return
    }
}

# Project files
$dir = Join-Path $env:TEMP ('firefox-pdf-reader-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $dir | Out-Null
Write-Host '==> Downloading Firefox PDF Reader' -ForegroundColor Cyan
Invoke-WebRequest "https://github.com/$Repo/archive/refs/heads/main.zip" -OutFile "$dir\src.zip" -UseBasicParsing
Expand-Archive "$dir\src.zip" $dir
$src = Get-ChildItem $dir -Directory | Select-Object -First 1

& (Join-Path $src.FullName 'windows\install.ps1')

Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
