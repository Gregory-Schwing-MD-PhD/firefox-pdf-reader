<#
.SYNOPSIS
  Removes "Firefox PDF Reader (full screen)" from Windows.

.DESCRIPTION
  Removes the registry entries install.ps1 added and the FirefoxPDF.exe
  launcher. The Firefox profile folder (with your per-PDF reading positions)
  is kept unless you pass -RemoveProfile.

  Afterwards, pick a new default PDF app in Settings > Apps > Default apps.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\windows\uninstall.ps1 -RemoveProfile
#>
[CmdletBinding()]
param(
    [string]$ProfileDir = (Join-Path $env:USERPROFILE 'FirefoxPDF'),
    [switch]$RemoveProfile
)

$ProgId  = 'FirefoxPDFReader'
$classes = 'HKCU:\Software\Classes'

Remove-Item "$classes\$ProgId" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$classes\Applications\FirefoxPDF.exe" -Recurse -Force -ErrorAction SilentlyContinue
Remove-ItemProperty "$classes\.pdf\OpenWithProgids" -Name $ProgId -ErrorAction SilentlyContinue
Remove-Item "HKCU:\Software\$ProgId" -Recurse -Force -ErrorAction SilentlyContinue
Remove-ItemProperty 'HKCU:\Software\RegisteredApplications' -Name $ProgId -ErrorAction SilentlyContinue

if ($RemoveProfile) {
    Remove-Item $ProfileDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Removed profile folder $ProfileDir"
} else {
    Remove-Item (Join-Path $ProfileDir 'FirefoxPDF.exe') -Force -ErrorAction SilentlyContinue
    Write-Host "Kept profile folder $ProfileDir (use -RemoveProfile to delete it)"
}

Add-Type -Namespace FirefoxPDFSetup -Name Shell -MemberDefinition `
    '[DllImport("shell32.dll")] public static extern void SHChangeNotify(int e, uint f, IntPtr a, IntPtr b);'
[FirefoxPDFSetup.Shell]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)

Write-Host 'Uninstalled. Choose a new default PDF app in Settings > Apps > Default apps.'
try { Start-Process 'ms-settings:defaultapps' } catch { }
