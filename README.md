# Firefox PDF Reader (full screen)

A distraction-free PDF reader built from Firefox's built-in PDF viewer, for Windows, macOS, Linux and ChromeOS. Double-click any PDF and it opens:

- **Full screen**, with no browser tabs, address bar or menus (Firefox kiosk mode)
- **Panel-less**: the PDF viewer's toolbar and sidebar are hidden, so only pages show
- **Dark**: dark viewer theme, and pages recoloured to light grey text on near-black
- **Fit to page width**, **scrolling vertically** through the document
- **Smoothly scrolling**, with the mouse wheel gliding instead of jumping

It runs in its own Firefox profile, so your normal Firefox (bookmarks, extensions, settings) is untouched.

| Platform | Script | Tested |
| --- | --- | --- |
| Windows 10 / 11 | [`windows/install.ps1`](windows/install.ps1) | Yes, Windows 11 |
| macOS | [`macos/install.sh`](macos/install.sh) | Not yet |
| Linux: Ubuntu, Debian, Fedora, Arch, Mint, Pop!_OS, openSUSE… | [`linux/install.sh`](linux/install.sh) | Not yet |
| ChromeOS (Chromebooks) | [`chromeos/install.sh`](chromeos/install.sh) | Not yet |

None of the scripts need administrator rights. Everything is installed for the current user only, except Firefox itself on ChromeOS.

First get the files:

```sh
git clone https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader.git
cd firefox-pdf-reader
```

Or download the ZIP from GitHub (**Code → Download ZIP**) and unzip it.

---

## Windows

**Needs:** Firefox, from the Microsoft Store or `winget install Mozilla.Firefox`.

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\install.ps1
```

The script does the following:

1. Creates the Firefox profile at `%USERPROFILE%\FirefoxPDF`.
2. Compiles [`windows/launcher/FirefoxPDF.cs`](windows/launcher/FirefoxPDF.cs) into `FirefoxPDF.exe` in that folder, using the C# compiler built into Windows.
3. Registers **Firefox PDF Reader (full screen)** as a PDF app.
4. Opens **Settings → Apps → Default apps**.

**Make it the default (by hand, because Windows requires it):**

1. Type `.pdf` in **Set a default for a file type or link type**.
2. Click the app currently shown.
3. Pick **Firefox PDF Reader (full screen)** and click **Set default**.

**Keys:**
- **Alt+F4** closes the reader (Esc doesn't exit kiosk mode).
- **Ctrl+Tab** switches between PDFs.
- **Ctrl+W** closes one.

**Uninstall:**

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\uninstall.ps1 -RemoveProfile
```

## macOS

**Needs:** Firefox in Applications, from [mozilla.org](https://www.mozilla.org/firefox/) or `brew install --cask firefox`.

```sh
bash ./macos/install.sh
```

The script does the following:

1. Creates the profile in `~/Library/Application Support/FirefoxPDF`.
2. Builds **Firefox PDF Reader.app** in `~/Applications`, a small AppleScript app with Firefox's icon.
3. Sets it as the default app for PDFs, using [`duti`](https://github.com/moretension/duti) if you have it, or macOS's own API if not.

If the default didn't take, set it by hand:

1. In Finder, select any PDF and choose **File → Get Info**.
2. Under **Open with**, choose **Firefox PDF Reader**.
3. Click **Change All…**.

**Keys:**
- **Cmd+Q** closes the reader.
- **Ctrl+Tab** switches between PDFs.
- **Cmd+W** closes one.

**Uninstall:**

```sh
bash ./macos/uninstall.sh --remove-profile
```

## Linux (Ubuntu and others)

**Needs:** Firefox. Any of the usual ways of installing it works:

| Distribution | Command |
| --- | --- |
| Ubuntu | `sudo snap install firefox` |
| Debian | `sudo apt install firefox-esr` |
| Fedora | `sudo dnf install firefox` |
| Arch | `sudo pacman -S firefox` |
| Any, via Flatpak | `flatpak install flathub org.mozilla.firefox` |

```sh
sh ./linux/install.sh
```

The script does the following:

1. Detects how Firefox is installed (regular package, Snap or Flatpak).
2. Creates the profile where that install is allowed to write.
3. Installs the launcher `~/.local/bin/firefox-pdf-reader` and the desktop entry `firefox-pdf-reader.desktop`.
4. Sets it as the default for `application/pdf` with `xdg-mime`.

It works on GNOME, KDE Plasma, Xfce, Cinnamon and other freedesktop.org desktops.

**Profile location by install type:**

| Firefox install | Profile folder |
| --- | --- |
| Regular package | `~/.local/share/firefox-pdf-reader` |
| Snap | `~/snap/firefox/common/firefox-pdf-reader` (Snap Firefox can't use hidden folders in your home) |
| Flatpak | `~/.var/app/org.mozilla.firefox/data/firefox-pdf-reader` |

On Flatpak, PDFs from anywhere are passed in through the document portal.

**Keys:**
- **Alt+F4** closes the reader.
- **Ctrl+Tab** switches between PDFs.
- **Ctrl+W** closes one.

**Uninstall:**

```sh
sh ./linux/uninstall.sh --remove-profile
```

## ChromeOS (Chromebooks)

Firefox runs in ChromeOS's built-in Linux environment.

1. Turn on Linux: **Settings → About ChromeOS → Developers → Linux development environment → Turn on**.
2. Open the **Terminal** app, then clone or download this repo there.
3. Run:

   ```sh
   sh ./chromeos/install.sh
   ```

   It installs Firefox ESR in the Linux container if needed, then runs the Linux installer.
4. Make it the default: in the **Files** app, right-click a PDF, choose **Open with → Change default**, and pick **Firefox PDF Reader**.
5. For smoother scrolling, turn on `chrome://flags/#crostini-gpu-support`, then restart the Chromebook.

To uninstall, run `sh ./linux/uninstall.sh --remove-profile` in the Terminal.

---

## Smooth scrolling

The reader's settings give Firefox smooth scrolling. How smooth it feels also depends on what your mouse or touchpad sends:

| Device | What to do |
| --- | --- |
| Touchpads, touchscreens, Apple Magic Mouse | Nothing. They already send continuous motion. |
| Logitech mouse on Windows or macOS | In **Logi Options+**, click your mouse, go to **Point and Scroll → Scroll wheel**, and turn **Smooth scrolling** on. This is what fixed choppy scrolling on the Windows PC this was built on. |
| Logitech mouse on Linux | [Solaar](https://pwr-solaar.github.io/Solaar/) (`sudo apt install solaar`) can turn on high-resolution scrolling on mice that support it. |
| Other mice | Look for "smooth scrolling" or "high-resolution scrolling" in the mouse's own software. |

With smooth scrolling off, a notched wheel only sends whole steps, and scrolling feels choppy in any PDF viewer.

## How it works

Every platform uses the same Firefox settings in [`profile/`](profile/). Only the launcher and the way it's registered with the OS differ.

| Behaviour | Where it's set |
| --- | --- |
| Full screen, no browser UI | The launcher starts Firefox with `--kiosk` |
| Separate from your normal Firefox | The launcher starts Firefox with `-profile <its own folder>` |
| Page width | `pdfjs.defaultZoomValue = "page-width"` in [`user.js`](profile/user.js) |
| Vertical scrolling, no spreads | `pdfjs.scrollModeOnLoad = 0`, `pdfjs.spreadModeOnLoad = 0` |
| Sidebar closed | `pdfjs.sidebarViewOnLoad = 0` |
| Dark viewer | `pdfjs.viewerCssTheme = 2` |
| Dark pages | `pdfjs.forcePageColors` with `pageColorsBackground` / `pageColorsForeground` |
| Toolbar hidden | [`chrome/userContent.css`](profile/chrome/userContent.css), enabled by `toolkit.legacyUserProfileCustomizations.stylesheets` |
| Smooth scrolling | `general.smoothScroll` on, with Firefox's easing left at defaults so it doesn't fight the mouse's own smooth scrolling |
| GPU rendering | `pdfjs.enableHWA`, `gfx.webrender.all` |

The launcher is different on each platform:

| Platform | Launcher | How it's registered |
| --- | --- | --- |
| Windows | `FirefoxPDF.exe`, compiled on your machine from C# source | Current-user registry entries; appears in **Default apps** |
| macOS | `Firefox PDF Reader.app`, an AppleScript app | Declares that it opens PDFs (`com.adobe.pdf`); registered with Launch Services |
| Linux, ChromeOS | `firefox-pdf-reader` shell script | `.desktop` entry with `MimeType=application/pdf`; set as default with `xdg-mime` |

Firefox remembers the zoom and reading position for each PDF.

To change colours or behaviour, edit the files in `profile/` and run the installer again. Firefox applies `user.js` each time the reader starts.

## Alternatives that were tried (Windows)

- **Eclipse PDF (Microsoft Store).** Scrolls smoothly and has a dark mode, but it has no full-screen command and its developer console is disabled. Presentation Mode is its only full-screen view, and that shows one page at a time.
- **SumatraPDF.** Can open full screen, dark and panel-less from its settings file. But it draws pages itself, so its scrolling isn't as fluid, even with `SmoothScroll = true`.
