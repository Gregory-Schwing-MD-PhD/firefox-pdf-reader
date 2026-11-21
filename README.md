# Firefox PDF Reader (full screen)

A distraction-free PDF reader for Windows 10/11 built from Firefox's built-in PDF viewer. Double-click any PDF and it opens:

- **Full screen**, with no browser tabs, address bar or menus (Firefox kiosk mode)
- **Panel-less**: the PDF viewer's toolbar and sidebar are hidden, so only pages show
- **Dark**: dark viewer theme, and pages recoloured to light grey text on near-black
- **Fit to page width**, **scrolling vertically** through the document
- **Smoothly scrolling**, with the mouse wheel gliding instead of jumping

It runs in its own Firefox profile, so your normal Firefox (bookmarks, extensions, settings) is untouched.

## Requirements

- Windows 10 or 11
- Firefox, from the Microsoft Store or the regular installer:

  ```powershell
  winget install Mozilla.Firefox
  ```

- No administrator rights are needed. Everything is installed for the current user only.

## Install

```powershell
git clone https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader.git
cd firefox-pdf-reader
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The script does the following:

1. Creates the Firefox profile at `%USERPROFILE%\FirefoxPDF`, holding [`profile/user.js`](profile/user.js) and [`profile/chrome/userContent.css`](profile/chrome/userContent.css).
2. Compiles [`launcher/FirefoxPDF.cs`](launcher/FirefoxPDF.cs) into `FirefoxPDF.exe` in that folder, using the C# compiler built into Windows.
3. Registers **Firefox PDF Reader (full screen)** with Windows as an app that opens `.pdf` files.
4. Opens **Settings → Apps → Default apps**.

Use `-ProfileDir <path>` to put the profile somewhere else.

### Two steps you do by hand

Windows won't let a script change your default apps, and Logitech's settings live in its own app, so these two steps are yours.

**1. Make it the default PDF app.** In the Settings page the script opens:

1. Type `.pdf` in **Set a default for a file type or link type**.
2. Click the app currently shown.
3. Pick **Firefox PDF Reader (full screen)** and click **Set default**.

**2. Turn on smooth scrolling for a Logitech mouse.** In Logi Options+:

1. Click your mouse.
2. Go to **Point and Scroll → Scroll wheel**.
3. Turn **Smooth scrolling** on.

With it off, a notched wheel only sends whole steps, and scrolling feels choppy in any PDF viewer. This setting is what made scrolling smooth here.

Other mice: look for a "smooth scrolling" or high-resolution scrolling option in the mouse's own software. Touchpads and touchscreens already scroll smoothly.

## Using it

| Key | Does |
| --- | --- |
| Alt+F4 | Close the reader (Esc doesn't exit kiosk mode) |
| Ctrl+Tab | Switch between open PDFs (each one opens in a hidden tab) |
| Ctrl+W | Close the current PDF |
| Ctrl+F | Find in the document |
| Ctrl+= / Ctrl+- | Zoom in / out |

Firefox remembers the zoom and reading position for each PDF.

## How it works

| Behaviour | Where it's set |
| --- | --- |
| Full screen, no browser UI | `FirefoxPDF.exe` starts Firefox with `--kiosk` |
| Separate from your normal Firefox | `FirefoxPDF.exe` starts Firefox with `-profile <its own folder>` |
| Page width | `pdfjs.defaultZoomValue = "page-width"` in `user.js` |
| Vertical scrolling, no spreads | `pdfjs.scrollModeOnLoad = 0`, `pdfjs.spreadModeOnLoad = 0` |
| Sidebar closed | `pdfjs.sidebarViewOnLoad = 0` |
| Dark viewer | `pdfjs.viewerCssTheme = 2` |
| Dark pages | `pdfjs.forcePageColors` with `pageColorsBackground` / `pageColorsForeground` |
| Toolbar hidden | `chrome/userContent.css`, enabled by `toolkit.legacyUserProfileCustomizations.stylesheets` |
| Smooth scrolling | `general.smoothScroll` on, with Firefox's easing left at defaults so it doesn't fight the mouse's smooth scrolling |
| GPU rendering | `pdfjs.enableHWA`, `gfx.webrender.all` |

To change colours or behaviour, edit the files in `profile/`, then run `install.ps1` again. Firefox applies `user.js` each time the reader starts.

### Why a launcher exe?

Windows only offers programs (`.exe` files) as default apps, and it can't pass the extra `-profile` and `--kiosk` options on its own. `FirefoxPDF.exe` is a few lines of C#: it finds Firefox and starts it with those options plus the PDF you opened. The source is in [`launcher/FirefoxPDF.cs`](launcher/FirefoxPDF.cs), and it's compiled on your machine rather than shipped as a binary.

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1                  # keeps the profile folder
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 -RemoveProfile   # deletes it too
```

Then choose a new default PDF app in **Settings → Apps → Default apps**.

## Alternatives that were tried

- **Eclipse PDF (Microsoft Store).** Scrolls smoothly and has a dark mode, but it has no full-screen command and its developer console is disabled. Presentation Mode is its only full-screen view, and that shows one page at a time.
- **SumatraPDF.** Can open full screen, dark and panel-less from its settings file. But it draws pages itself, so its scrolling isn't as fluid, even with `SmoothScroll = true`.
