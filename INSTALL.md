# Manual install, uninstall and how it works

Most people should use the one-step installer at **https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/**. This page covers installing from a copy of this repository, uninstalling, testing, and how the reader is put together.

| Platform | Script | Tested |
| --- | --- | --- |
| Windows 10 / 11 | [`windows/install.ps1`](windows/install.ps1) | Windows 11 PC, plus CI on Windows Server |
| macOS | [`macos/install.sh`](macos/install.sh) | CI on macOS 15 and the latest macOS |
| Linux: Ubuntu, Debian, Fedora, Arch, Mint, Pop!_OS, openSUSE… | [`linux/install.sh`](linux/install.sh) | CI on Ubuntu 24.04 |
| ChromeOS (Chromebooks) | [`chromeos/install.sh`](chromeos/install.sh) | CI in Debian 12, set up like ChromeOS's Linux environment |

Every push runs [the test workflow](.github/workflows/test.yml) on GitHub Actions. For each platform it:

1. runs the installer (on Ubuntu, over an install of the earlier kiosk-mode version, to test updating)
2. checks the reader is registered, and is the default PDF app where the OS allows a script to set that
3. checks the reader's profile files and the settings Firefox loaded
4. opens a PDF like a double-click, then a second PDF, and checks that each gets its own window of the one running reader, titled with its file name and filling the screen, as the system's own window list shows them
5. compares the colours and sharpness of a colour figure on screen with poppler's drawing of the same page ([`tests/compare_colours.py`](tests/compare_colours.py))
6. clicks a web link in the PDF and checks it opens in a new window
7. switches between the two windows with Alt+Tab (Cmd+` on macOS), makes one full screen with F11 (Ctrl+Cmd+F) and takes it back with F11 (Esc), then closes both
8. saves a screenshot of every step, and the colour comparison, which you can download from the run's **Artifacts**
9. uninstalls

GitHub can't run ChromeOS itself, so a real Chromebook hasn't been tried.

None of the scripts need administrator rights. Everything is installed for the current user only, except Firefox itself on ChromeOS.

First get the files:

```sh
git clone https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader.git
cd firefox-pdf-reader
```

Or download the ZIP from GitHub (**Code → Download ZIP**) and unzip it.

## Windows

**Needs:** Firefox, from the Microsoft Store or `winget install Mozilla.Firefox`.

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\install.ps1
```

The script does the following:

1. Creates the Firefox profile at `%USERPROFILE%\FirefoxPDF`.
2. Compiles [`windows/launcher/FirefoxPDF.cs`](windows/launcher/FirefoxPDF.cs) into `FirefoxPDF.exe` in that folder, using the C# compiler built into Windows.
3. Registers **Firefox PDF Reader** as a PDF app.
4. Opens **Settings → Apps → Default apps**.

**Make it the default (by hand, because Windows requires it):**

1. Type `.pdf` in **Set a default for a file type or link type**.
2. Click the app currently shown.
3. Pick **Firefox PDF Reader** and click **Set default**.

**Keys:**
- **F11** makes a PDF full screen; **F11** again leaves full screen (Esc doesn't, on Windows).
- **Alt+Tab** switches between PDFs: each has its own window.
- **Ctrl+W** closes a PDF; **Alt+F4** closes its window.

**Update:** run the same command again. If the reader is already your default PDF app, the Settings page doesn't open.

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

1. Builds **Firefox PDF Reader.app** in `~/Applications`, using [`macos/build-app.sh`](macos/build-app.sh). This is the same app as in the `.dmg`: a small AppleScript app with Firefox's icon that carries the reader's settings inside it.
2. Runs the app's setup, which creates the profile in `~/Library/Application Support/FirefoxPDF` and sets the app as the default app for PDFs.

The app refreshes the profile's settings every time it starts, so updating the app updates the reader: run `bash ./macos/install.sh` again, or drag the new app from the `.dmg` into Applications.

**Building the disk image:** `bash ./macos/build-dmg.sh dist` makes `dist/FirefoxPDFReader.dmg`.
- **Default:** the app is signed ad hoc, so macOS asks people to allow it the first time (**System Settings → Privacy & Security → Open Anyway**).
- **Signed and notarized:** with an Apple Developer ID, set `SIGN_IDENTITY`, `NOTARY_APPLE_ID`, `NOTARY_TEAM_ID` and `NOTARY_PASSWORD`. The app is then signed and the disk image notarized, so it opens with no warning, like Chrome.

On recent macOS, Finder then asks whether `.pdf` files should open with **Firefox PDF Reader** or keep using Preview. Click **Use "Firefox PDF Reader"**.

If the default didn't take, set it by hand:

1. In Finder, select any PDF and choose **File → Get Info**.
2. Under **Open with**, choose **Firefox PDF Reader**.
3. Click **Change All…**.

**Keys:**
- **Ctrl+Cmd+F** makes a PDF full screen (a space of its own); **Esc** leaves full screen.
- **Cmd+`** switches between the reader's windows that aren't full screen; **Cmd+Tab** switches apps.
- **Cmd+W** closes a PDF; **Cmd+Q** closes the reader.

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

It works on GNOME, KDE Plasma, Xfce, Cinnamon and other freedesktop.org desktops. Run it again to update an installed reader.

**Profile location by install type:**

| Firefox install | Profile folder |
| --- | --- |
| Regular package | `~/.local/share/firefox-pdf-reader` |
| Snap | `~/snap/firefox/common/firefox-pdf-reader` (Snap Firefox can't use hidden folders in your home) |
| Flatpak | `~/.var/app/org.mozilla.firefox/data/firefox-pdf-reader` |

On Flatpak, PDFs from anywhere are passed in through the document portal.

**Keys:**
- **F11** makes a PDF full screen; **F11** again leaves full screen (Esc doesn't, on Linux).
- **Alt+Tab** switches between PDFs: each has its own window. On GNOME, Alt+Tab groups windows by app: hold Alt and press **`** (the key above Tab) to step through the reader's windows.
- **Ctrl+W** closes a PDF; **Alt+F4** closes its window.

A second PDF goes to the running reader over the desktop's session bus (D-Bus), which Linux desktops and ChromeOS's Linux have.

**Uninstall:**

```sh
sh ./linux/uninstall.sh --remove-profile
```

### The .deb package (Ubuntu, Debian, Mint, Pop!_OS, ChromeOS)

`sh ./linux/package/build-deb.sh dist` builds `dist/firefox-pdf-reader_1.0_all.deb`. It installs:

- `/usr/bin/firefox-pdf-reader`: the launcher. Each time it runs, it picks the right profile folder for native, Snap or Flatpak Firefox and refreshes the settings there.
- the settings in `/usr/share/firefox-pdf-reader/`
- the desktop entry `firefox-pdf-reader.desktop`

**How it becomes the default:**
- **For everyone:** installing makes it the system-wide PDF default in `/etc/xdg/mimeapps.list`.
- **For each user:** the first time a user opens it, it makes itself their default too.
- **Choices kept:** a user who already picked a default PDF app keeps it until they choose **Firefox PDF Reader** under **Open With**.

It depends on `firefox-esr | firefox`, so installing it brings Firefox along if needed. Installing a newer `.deb` updates it. Remove it with `sudo apt remove firefox-pdf-reader`.

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
| Each PDF in its own window | The launcher passes each PDF with `-new-window`; a second PDF goes to the running reader |
| A window filling the screen | Before each start the launcher writes Firefox's saved window state, `xulstore.json`, with `"sizemode": "maximized"` |
| No tabs, address bar or sidebar; the system's title bar | [`chrome/userChrome.css`](profile/chrome/userChrome.css), and `browser.tabs.inTitlebar = 0` in [`user.js`](profile/user.js) |
| Full screen on F11, Firefox's bar at the top edge | Firefox's own full screen, with `browser.fullscreen.autohide` |
| The note on how to leave full screen | [`chrome/userContent.css`](profile/chrome/userContent.css), shown while `display-mode: fullscreen` |
| Separate from your normal Firefox | The launcher starts Firefox with `-profile <its own folder>` |
| Page width | `pdfjs.defaultZoomValue = "page-width"` |
| Vertical scrolling, no spreads | `pdfjs.scrollModeOnLoad = 0`, `pdfjs.spreadModeOnLoad = 0` |
| Sidebar closed | `pdfjs.sidebarViewOnLoad = 0` |
| Dark viewer around the pages | `pdfjs.viewerCssTheme = 2` |
| Pages and pictures in their own colours | `pdfjs.forcePageColors = false` (Firefox's default, written out so an earlier install that recoloured pages gets it back) |
| PDF toolbar hidden | [`chrome/userContent.css`](profile/chrome/userContent.css); both style sheets are enabled by `toolkit.legacyUserProfileCustomizations.stylesheets` |
| Web links open in a new window | `pdfjs.externalLinkTarget = 2`, `browser.link.open_newwindow = 2` |
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

## Updating

Install again the same way you installed; nothing needs removing first. The Windows and Linux scripts copy the new profile files and launcher; the Mac app and the `.deb` launcher copy the profile files from themselves every time they start, so a new app or package is the whole update. Close the reader's windows first: the next PDF you open uses the new version.

An install from before this change opened PDFs in kiosk mode and recoloured every page. Its launcher is replaced, and the new `user.js` sets `pdfjs.forcePageColors` back to `false`: Firefox keeps a changed setting in the profile until something sets it again, so leaving the line out would not be enough. The Ubuntu test starts from such an install and checks this.

## Alternatives that were tried (Windows)

- **Eclipse PDF (Microsoft Store).** Scrolls smoothly and has a dark mode, but it has no full-screen command and its developer console is disabled. Presentation Mode is its only full-screen view, and that shows one page at a time.
- **SumatraPDF.** Can open full screen, dark and panel-less from its settings file. But it draws pages itself, so its scrolling isn't as fluid, even with `SmoothScroll = true`.
