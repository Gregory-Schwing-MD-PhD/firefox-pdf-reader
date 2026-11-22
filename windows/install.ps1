<#
.SYNOPSIS
  Sets up "Firefox PDF Reader": every PDF opens in its own Firefox window,
  filling the screen, at page width, scrolling vertically, with no toolbars or
  panels, on black pages with white text and its pictures in their own
  colours. F11 makes it full screen and back.

.DESCRIPTION
  1. Creates a dedicated Firefox profile (default: %USERPROFILE%\FirefoxPDF)
     with the PDF viewer preferences, the style sheets that hide the
     browser's bars and the PDF toolbar, and the reader's own copy of pdf.js's
     viewer, which draws pages black with white text.
  2. Compiles a tiny launcher, FirefoxPDF.exe, that opens each PDF in its own
     window of that profile.
  3. Registers the launcher with Windows as a PDF app (current user only).
  4. Opens Settings > Default apps so you can make it the default for .pdf,
     unless it already is. Windows requires that last click to be yours.

  Nothing needs administrator rights, and the script asks no question.
  Running it again updates an installed reader to this version.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\windows\install.ps1
#>
[CmdletBinding()]
param(
    [string]$ProfileDir = (Join-Path $env:USERPROFILE 'FirefoxPDF'),
    [switch]$SkipDefaultAppsPage
)

$ErrorActionPreference = 'Stop'
$RepoDir  = Split-Path $PSScriptRoot -Parent   # repo root (this script is in windows\)
$AppName  = 'Firefox PDF Reader'
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
Copy-Item (Join-Path $RepoDir 'profile\chrome\*.css') (Join-Path $ProfileDir 'chrome') -Force
# The reader's own viewer (pdf.js, with black pages and white text), replaced
# as a whole so nothing of an older copy stays
$viewerDir = Join-Path $ProfileDir 'viewer'
if (Test-Path $viewerDir) { Remove-Item $viewerDir -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Force -Path $viewerDir | Out-Null
Copy-Item (Join-Path $RepoDir 'viewer\*') $viewerDir -Recurse -Force

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
& $csc @cscArgs (Join-Path $PSScriptRoot 'launcher\FirefoxPDF.cs')
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
Set-ItemProperty $cap -Name ApplicationDescription -Value 'Opens each PDF in its own Firefox window, with no toolbars'
Set-ItemProperty "$cap\FileAssociations" -Name '.pdf' -Value $ProgId
New-Item 'HKCU:\Software\RegisteredApplications' -Force -ErrorAction SilentlyContinue | Out-Null
Set-ItemProperty 'HKCU:\Software\RegisteredApplications' -Name $ProgId -Value "Software\$ProgId\Capabilities"

# Tell Explorer associations changed
Add-Type -Namespace FirefoxPDFSetup -Name Shell -MemberDefinition `
    '[DllImport("shell32.dll")] public static extern void SHChangeNotify(int e, uint f, IntPtr a, IntPtr b);'
[FirefoxPDFSetup.Shell]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)

# --- 5. Default app + mouse --------------------------------------------------
# Already the default PDF app (for example when this runs again to update)?
# Windows keeps the choice in UserChoiceLatest\ProgId (newer Windows 11) or UserChoice.
$fileExts = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.pdf'
$choices = foreach ($key in "$fileExts\UserChoiceLatest\ProgId", "$fileExts\UserChoice") {
    try { (Get-ItemProperty $key -ErrorAction Stop).ProgId } catch { }
}
$isDefault = @($choices | Where-Object { $_ }) -contains $ProgId -and
             -not (@($choices | Where-Object { $_ -and $_ -ne $ProgId }))

Write-Host ''
Write-Host 'Installed.' -ForegroundColor Green
Write-Host ''
if ($isDefault) {
    Write-Host 'It is already your default PDF app.'
} else {
    Write-Host 'One step Windows requires you to do yourself:' -ForegroundColor Yellow
    Write-Host "  Default PDF app: in the Settings page that opens, type .pdf in 'Set a default"
    Write-Host "  for a file type', click the current app, pick '$AppName', click Set default."
}
Write-Host 'Smooth mouse wheel (Logitech): Logi Options+ > your mouse > Point and Scroll'
Write-Host '  > Scroll wheel > turn Smooth scrolling on.'
Write-Host ''
Write-Host 'Each PDF opens in its own window. Keys: F11 full screen and back,'
Write-Host '  Alt+Tab switches between PDFs, Ctrl+W closes a PDF, Alt+F4 closes its window.'
if (Get-Process firefox -ErrorAction SilentlyContinue) {
    Write-Host 'If the reader is open now, close its windows: the next PDF you open uses this version.'
}

if (-not $SkipDefaultAppsPage -and -not $isDefault) {
    try { Start-Process "ms-settings:defaultapps?registeredAppUser=$ProgId" -ErrorAction Stop }
    catch { Write-Host "Open Settings > Apps > Default apps to choose the default PDF app." }
}
