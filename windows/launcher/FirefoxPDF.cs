// FirefoxPDF.exe: opens each PDF in its own window of the dedicated Firefox profile,
// a window that fills the screen (F11 makes it full screen and back).
// install.ps1 compiles this into the profile folder; the profile is the folder the exe sits in.
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("Firefox PDF Reader")]
[assembly: System.Reflection.AssemblyProduct("Firefox PDF Reader")]

static class FirefoxPDF
{
    // Firefox restores its window's size mode from xulstore.json in the profile;
    // "maximized" makes the reader's window fill the screen. (Firefox has no
    // supported way to start an ordinary window full screen: its kiosk mode has
    // no way out. Firefox writes the file itself as windows change, so it is
    // written again before every start; it counts when the reader isn't running.)
    const string StartWindow =
        "{\"chrome://browser/content/browser.xhtml\":{\"main-window\":" +
        "{\"width\":\"1280\",\"height\":\"900\",\"sizemode\":\"maximized\"}}}";

    static string FindFirefox()
    {
        string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        string[] candidates = {
            Path.Combine(local, @"Microsoft\WindowsApps\firefox.exe"),   // Microsoft Store install
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), @"Mozilla Firefox\firefox.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), @"Mozilla Firefox\firefox.exe"),
            Path.Combine(local, @"Mozilla Firefox\firefox.exe"),
        };
        foreach (string c in candidates)
            if (File.Exists(c)) return c;
        return null;
    }

    [STAThread]
    static void Main(string[] args)
    {
        string firefox = FindFirefox();
        if (firefox == null)
        {
            MessageBox.Show("Firefox was not found. Install it with:\n\nwinget install Mozilla.Firefox",
                "Firefox PDF Reader", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }

        string profile = Path.GetDirectoryName(Application.ExecutablePath);
        try
        {
            File.WriteAllText(Path.Combine(profile, "xulstore.json"), StartWindow, new UTF8Encoding(false));
        }
        catch (Exception)
        {
            // Not fatal: the PDF still opens, in the window size Firefox remembers.
        }

        // -new-window: every PDF gets a window of its own, also when the reader is
        // already running (Firefox hands the request to the running reader), so
        // Alt+Tab shows each PDF by its file name.
        StringBuilder arguments = new StringBuilder("-profile \"" + profile + "\"");
        foreach (string a in args)
            arguments.Append(" -new-window \"" + a + "\"");

        Process.Start(new ProcessStartInfo(firefox, arguments.ToString()) { UseShellExecute = false });
    }
}
