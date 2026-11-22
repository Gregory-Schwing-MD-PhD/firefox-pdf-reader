// FirefoxPDF.exe: opens each PDF in its own window of the dedicated Firefox profile,
// a window that fills the screen (F11 makes it full screen and back), in the
// reader's own viewer: black pages, white text, pictures in their own colours.
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

    // A file's address (file:///C:/My%20Papers/a.pdf, or file://server/share/a.pdf):
    // its UTF-8 bytes, all but letters, digits and - . _ ~ / : percent-encoded.
    static string FileUrl(string path)
    {
        string p = Path.GetFullPath(path).Replace('\\', '/');
        StringBuilder url = new StringBuilder(p.StartsWith("//") ? "file:" : "file:///");
        foreach (byte b in Encoding.UTF8.GetBytes(p))
        {
            char c = (char)b;
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || "-._~/:".IndexOf(c) >= 0)
                url.Append(c);
            else
                url.AppendFormat("%{0:X2}", b);
        }
        return url.ToString();
    }

    // What Firefox is asked to open for one PDF: the reader's viewer with the
    // PDF's address after "?file=", encoded once more. A PDF on this computer
    // may come as its path or as its file:/// address. A web address, or any
    // PDF when the viewer is missing, goes to Firefox as it is.
    static string Target(string arg, string viewer)
    {
        Uri uri;
        if (arg.Contains("://") && Uri.TryCreate(arg, UriKind.Absolute, out uri) && uri.IsFile)
            arg = uri.LocalPath;
        if (arg.Contains("://") || !File.Exists(viewer)) return arg;
        return FileUrl(viewer) + "?file=" + Uri.EscapeDataString(FileUrl(arg));
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
        string viewer = Path.Combine(profile, @"viewer\web\viewer.html");
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
            arguments.Append(" -new-window \"" + Target(a, viewer) + "\"");

        Process.Start(new ProcessStartInfo(firefox, arguments.ToString()) { UseShellExecute = false });
    }
}
