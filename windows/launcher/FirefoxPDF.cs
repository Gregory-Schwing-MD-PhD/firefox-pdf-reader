// FirefoxPDF.exe: opens PDFs in the dedicated Firefox profile, full screen (kiosk mode).
// install.ps1 compiles this into the profile folder; the profile is the folder the exe sits in.
using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("Firefox PDF Reader (full screen)")]
[assembly: System.Reflection.AssemblyProduct("Firefox PDF Reader (full screen)")]

static class FirefoxPDF
{
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
        string arguments = "-profile \"" + profile + "\" --kiosk";
        foreach (string a in args)
            arguments += " \"" + a + "\"";

        Process.Start(new ProcessStartInfo(firefox, arguments) { UseShellExecute = false });
    }
}
