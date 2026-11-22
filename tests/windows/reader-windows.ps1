# Helpers for the Windows test: the reader's windows as Windows lists them,
# keys pressed the way a keyboard does, and screenshots.
# Use:  . .\tests\windows\reader-windows.ps1

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class ReaderWin
{
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }

    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern bool IsZoomed(IntPtr h);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint flags, int dx, int dy, uint data, UIntPtr extra);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern int GetWindowLong(IntPtr h, int index);
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);

    public static List<IntPtr> TopLevel()
    {
        List<IntPtr> list = new List<IntPtr>();
        EnumWindows(delegate (IntPtr h, IntPtr l) { list.Add(h); return true; }, IntPtr.Zero);
        return list;
    }
    public static string Text(IntPtr h) { StringBuilder s = new StringBuilder(512); GetWindowText(h, s, 512); return s.ToString(); }
    public static string Class(IntPtr h) { StringBuilder s = new StringBuilder(256); GetClassName(h, s, 256); return s.ToString(); }
    public static uint Pid(IntPtr h) { uint p; GetWindowThreadProcessId(h, out p); return p; }
}
"@

$VK = @{ Alt = 0x12; Ctrl = 0x11; Tab = 0x09; F11 = 0x7A; F4 = 0x73; Esc = 0x1B; W = 0x57 }

# The reader's windows: visible top-level Firefox windows with a title, in the
# order Windows keeps them (front first), as Alt+Tab lists them.
function Get-ReaderWindows {
    $ff = @(Get-Process firefox -ErrorAction SilentlyContinue | ForEach-Object Id)
    $fg = [ReaderWin]::GetForegroundWindow()
    foreach ($h in [ReaderWin]::TopLevel()) {
        if (-not [ReaderWin]::IsWindowVisible($h)) { continue }
        if ([ReaderWin]::Class($h) -ne 'MozillaWindowClass') { continue }
        if ($ff -notcontains [int][ReaderWin]::Pid($h)) { continue }
        $title = [ReaderWin]::Text($h)
        if (-not $title) { continue }
        $r = New-Object ReaderWin+RECT
        [void][ReaderWin]::GetWindowRect($h, [ref]$r)
        $screen = [System.Windows.Forms.Screen]::FromHandle($h).Bounds
        $style = [ReaderWin]::GetWindowLong($h, -16)
        [pscustomobject]@{
            Handle     = $h
            Title      = $title
            ProcessId  = [ReaderWin]::Pid($h)
            Front      = ($h -eq $fg)
            Minimised  = [ReaderWin]::IsIconic($h)
            Maximised  = [ReaderWin]::IsZoomed($h)
            Rect       = "$($r.Left),$($r.Top) $($r.Right - $r.Left)x$($r.Bottom - $r.Top)"
            # Full screen: the window covers its whole screen and has no title bar.
            FullScreen = ($r.Left -le $screen.Left -and $r.Top -le $screen.Top -and
                          $r.Right -ge $screen.Right -and $r.Bottom -ge $screen.Bottom -and
                          -not ($style -band 0x00C00000))
            TitleBar   = [bool](($style -band 0x00C00000) -eq 0x00C00000)
        }
    }
}

function Wait-ReaderWindows([int]$Count, [int]$Seconds = 60) {
    for ($i = 0; $i -lt $Seconds; $i++) {
        $w = @(Get-ReaderWindows)
        if ($w.Count -eq $Count) { return $w }
        Start-Sleep 1
    }
    $w = @(Get-ReaderWindows)
    $w | Format-Table -AutoSize | Out-String | Write-Host
    throw "Expected $Count reader windows, found $($w.Count)"
}

# Presses keys like a keyboard: all down in order, then all up in reverse.
function Send-Keys([string[]]$Keys) {
    foreach ($k in $Keys) { [ReaderWin]::keybd_event([byte]$VK[$k], 0, 0, [UIntPtr]::Zero); Start-Milliseconds 60 }
    [array]::Reverse($Keys)
    foreach ($k in $Keys) { [ReaderWin]::keybd_event([byte]$VK[$k], 0, 2, [UIntPtr]::Zero); Start-Milliseconds 60 }
}
function Start-Milliseconds([int]$ms) { Start-Sleep -Milliseconds $ms }

# Brings a window to the front. Windows lets a program do this right after a
# key press, so an Alt press goes first, as Windows' own documentation allows.
function Set-Front($Window) {
    [ReaderWin]::keybd_event([byte]$VK.Alt, 0, 0, [UIntPtr]::Zero)
    [void][ReaderWin]::SetForegroundWindow($Window.Handle)
    [ReaderWin]::keybd_event([byte]$VK.Alt, 0, 2, [UIntPtr]::Zero)
    Start-Sleep 1
}

# Clicks the middle of the page, PointsDown PDF points below its top, using
# where compare_colours.py found the page in a screenshot.
function Invoke-PageClick([string]$Json, [double]$PointsDown) {
    $p = (Get-Content $Json -Raw | ConvertFrom-Json).page_in_screenshot
    $x = [int]($p.left + [math]::Floor($p.width / 2))
    $y = [int]($p.top + [math]::Round($p.width / 612 * $PointsDown))
    Write-Host "clicking at $x,$y"
    [void][ReaderWin]::SetCursorPos($x, $y)
    Start-Sleep -Milliseconds 300
    [ReaderWin]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)   # left button down
    Start-Sleep -Milliseconds 80
    [ReaderWin]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)   # left button up
}

function Save-Screen([string]$Path) {
    $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    Write-Host "screenshot: $Path"
}

# Firefox's main processes (not its page processes), with their command lines.
function Get-ReaderProcesses {
    Get-CimInstance Win32_Process -Filter "Name='firefox.exe'" |
        Where-Object { $_.CommandLine -notmatch '-contentproc' } |
        Select-Object ProcessId, CommandLine
}
