<#
.SYNOPSIS
  Sets up "Firefox PDF Reader (full screen)": PDFs open in Firefox full screen,
  dark, at page width, scrolling vertically, with no toolbars or panels.

.DESCRIPTION
  1. Creates a dedicated Firefox profile (default: %USERPROFILE%\FirefoxPDF)
     with the PDF viewer preferences and a style sheet that hides the toolbar.
  2. Compiles a tiny launcher, FirefoxPDF.exe, that opens a PDF in that
     profile in kiosk (full-screen) mode.
  3. Registers the launcher with Windows as a PDF app (current user only).
  4. Opens Settings > Default apps so you can make it the default for .pdf.
     Windows requires that last click to be yours.

  Nothing needs administrator rights.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\install.ps1
#>
[CmdletBinding()]
param(
    [string]$ProfileDir = (Join-Path $env:USERPROFILE 'FirefoxPDF'),
    [switch]$SkipDefaultAppsPage
)

$ErrorActionPreference = 'Stop'
$RepoDir  = $PSScriptRoot
$AppName  = 'Firefox PDF Reader (full screen)'
$ProgId   = 'FirefoxPDFReader'

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

# --- 1. Find Firefox --------------------------------------------------------
Write-Step 'Looking for Firefox'
$candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\firefox.exe'),
    (Join-Path $env:ProgramFiles 'Mozilla Firefox\firefox.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Mozilla Firefox\firefox.exe'),
    (Join-Path $env:LOCALAPPDATA 'Mozilla Firefox\firefox.exe')
)
$firefox = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $firefox) {
    throw "Firefox not found. Install it first:  winget install Mozilla.Firefox"
}
Write-Host "    $firefox"

# Real executable, for the icon (the Store alias has no icon of its own)
$iconSource = $firefox
$storePkg = Get-AppxPackage -Name 'Mozilla.Firefox' -ErrorAction SilentlyContinue
if ($storePkg) {
    $real = Join-Path $storePkg.InstallLocation 'VFS\ProgramFiles\Firefox Package Root\firefox.exe'
    if (Test-Path $real) { $iconSource = $real }
}

# --- 2. Profile -------------------------------------------------------------
Write-Step "Writing Firefox profile files to $ProfileDir"
New-Item -ItemType Directory -Force -Path (Join-Path $ProfileDir 'chrome') | Out-Null
Copy-Item (Join-Path $RepoDir 'profile\user.js') $ProfileDir -Force
Copy-Item (Join-Path $RepoDir 'profile\chrome\userContent.css') (Join-Path $ProfileDir 'chrome') -Force

# --- 3. Launcher ------------------------------------------------------------
Write-Step 'Building FirefoxPDF.exe launcher'
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path $csc)) { throw "C# compiler not found at $csc (.NET Framework 4 is part of Windows 10/11)." }

$exe  = Join-Path $ProfileDir 'FirefoxPDF.exe'
$ico  = Join-Path $env:TEMP 'FirefoxPDF.ico'
$cscArgs = @('/nologo', '/target:winexe', '/reference:System.Windows.Forms.dll', "/out:$exe")
try {
    Add-Type -AssemblyName System.Drawing
    $icon = [System.Drawing.Icon]::ExtractAssociatedIcon($iconSource)
    $fs = [IO.File]::Create($ico); $icon.Save($fs); $fs.Close()
    $cscArgs += "/win32icon:$ico"
} catch {
    Write-Warning "Could not extract Firefox's icon; the launcher will use a generic one."
}
& $csc @cscArgs (Join-Path $RepoDir 'launcher\FirefoxPDF.cs')
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $exe)) { throw 'Building the launcher failed.' }
Write-Host "    $exe"

# --- 4. Register with Windows (current user) -------------------------------
Write-Step 'Registering the PDF reader with Windows'
$cmd = "`"$exe`" `"%1`""
$classes = 'HKCU:\Software\Classes'

# ProgId
$p = "$classes\$ProgId"
New-Item "$p\shell\open\command" -Force | Out-Null
New-Item "$p\DefaultIcon" -Force | Out-Null
New-Item "$p\Application" -Force | Out-Null
Set-Item         $p -Value 'PDF Document'
Set-ItemProperty $p -Name FriendlyTypeName -Value 'PDF Document'
Set-ItemProperty "$p\Application" -Name ApplicationName -Value $AppName
Set-Item         "$p\DefaultIcon" -Value "$exe,0"
Set-ItemProperty "$p\shell\open" -Name FriendlyAppName -Value $AppName
Set-Item         "$p\shell\open\command" -Value $cmd

# Applications\FirefoxPDF.exe (makes it appear in "Open with")
$a = "$classes\Applications\FirefoxPDF.exe"
New-Item "$a\shell\open\command" -Force | Out-Null
New-Item "$a\SupportedTypes" -Force | Out-Null
New-Item "$a\DefaultIcon" -Force | Out-Null
Set-ItemProperty $a -Name FriendlyAppName -Value $AppName
Set-Item         "$a\shell\open\command" -Value $cmd
Set-Item         "$a\DefaultIcon" -Value "$exe,0"
New-ItemProperty "$a\SupportedTypes" -Name '.pdf' -Value '' -PropertyType String -Force | Out-Null

# .pdf -> offer this ProgId
New-Item "$classes\.pdf\OpenWithProgids" -Force | Out-Null
New-ItemProperty "$classes\.pdf\OpenWithProgids" -Name $ProgId -Value ([byte[]]@()) -PropertyType None -Force | Out-Null

# Registered application (makes it appear in Settings > Default apps)
$cap = "HKCU:\Software\$ProgId\Capabilities"
New-Item "$cap\FileAssociations" -Force | Out-Null
Set-ItemProperty $cap -Name ApplicationName -Value $AppName
Set-ItemProperty $cap -Name ApplicationDescription -Value 'Opens PDFs in Firefox full screen, dark, with no toolbars'
Set-ItemProperty "$cap\FileAssociations" -Name '.pdf' -Value $ProgId
New-Item 'HKCU:\Software\RegisteredApplications' -Force -ErrorAction SilentlyContinue | Out-Null
Set-ItemProperty 'HKCU:\Software\RegisteredApplications' -Name $ProgId -Value "Software\$ProgId\Capabilities"

# Tell Explorer associations changed
Add-Type -Namespace FirefoxPDFSetup -Name Shell -MemberDefinition `
    '[DllImport("shell32.dll")] public static extern void SHChangeNotify(int e, uint f, IntPtr a, IntPtr b);'
[FirefoxPDFSetup.Shell]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)

# --- 5. Default app + mouse --------------------------------------------------
Write-Host ''
Write-Host 'Installed.' -ForegroundColor Green
Write-Host ''
Write-Host 'Two steps Windows and Logitech require you to do yourself:' -ForegroundColor Yellow
Write-Host "  1. Default PDF app: in the Settings page that opens, type .pdf in 'Set a default"
Write-Host "     for a file type', click the current app, pick '$AppName', click Set default."
Write-Host "  2. Smooth mouse wheel (Logitech): Logi Options+ > your mouse > Point and Scroll"
Write-Host "     > Scroll wheel > turn Smooth scrolling on."
Write-Host ''
Write-Host 'Keys: Alt+F4 closes the reader, Ctrl+Tab switches PDFs, Ctrl+W closes one.'

if (-not $SkipDefaultAppsPage) { Start-Process "ms-settings:defaultapps?registeredAppUser=$ProgId" }
