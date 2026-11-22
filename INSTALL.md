# Manual install, uninstall and how it works

Most people should use the one-step installer at **https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/**. This page covers installing from a copy of this repository, uninstalling, testing, and how the reader is put together.

| Platform | Script | Tested |
| --- | --- | --- |
| Windows 10 / 11 | [`windows/install.ps1`](windows/install.ps1) | Windows 11 PC, plus CI on Windows Server |
| macOS | [`macos/install.sh`](macos/install.sh) | CI on macOS 15 and the latest macOS |
| Linux: Ubuntu, Debian, Fedora, Arch, Mint, Pop!_OS, openSUSE… | [`linux/install.sh`](linux/install.sh) | CI on Ubuntu 24.04 |
| ChromeOS (Chromebooks) | [`chromeos/install.sh`](chromeos/install.sh) | CI in Debian 12, set up like ChromeOS's Linux environment |

Every push runs [the test workflow](.github/workflows/test.yml) on GitHub Actions. On Windows, macOS and Ubuntu it:

1. runs the installer (on Ubuntu, over an install of the earlier kiosk-mode version, to test updating)
2. checks the reader is registered, and is the default PDF app where the OS allows a script to set that
3. checks the reader's profile files, its copy of the viewer, and the settings Firefox loaded
4. opens a PDF like a double-click (on Ubuntu with `xdg-open`), then a second PDF, and checks that each gets its own window of the one running reader, titled with its file name and filling the screen, as the system's own window list shows them
5. compares the colours and sharpness of a colour figure on screen with poppler's drawing of the same page ([`tests/compare_colours.py`](tests/compare_colours.py))
6. clicks a web link in the PDF and checks it opens in a new window
7. switches between the two windows with Alt+Tab (Cmd+` on macOS), makes one full screen with F11 (Ctrl+Cmd+F) and takes it back with F11 (Esc)
8. opens a test page made by [`tests/make_test_pdfs.py`](tests/make_test_pdfs.py) (text in black, dark grey and CMYK black; a greyscale photograph-like picture with a step wedge, and a white label, a white arrow and a black label drawn on it; a bar chart with coloured bars, black axes and light grey grid lines), under the file name `chart page #1 & 50% é.pdf`, and checks against poppler's drawing ([`tests/check_dark_page.py`](tests/check_dark_page.py)) that the page is black, every line of text white, the picture as the PDF has it (not inverted) with the labels on it in their own colours, the bars in their colours, the axes white and the grid lines dark grey
9. closes the windows, saves a screenshot of every step and the measurements, which you can download from the run's **Artifacts**, and uninstalls

In the ChromeOS-style Debian 12 container (Firefox ESR) it installs the reader, opens two PDFs into two windows of one reader, makes one full screen with F11 and back, checks the test page as in step 8, and installs the `.deb`. It doesn't click links, switch windows or compare the colour figure there. GitHub can't run ChromeOS itself, so a real Chromebook hasn't been tried.

A separate job builds [`viewer/`](viewer/) again from pdf.js's release with [`tools/make_viewer.py`](tools/make_viewer.py) and checks it is the same, file for file.

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

**Update:** run the same command again; it asks nothing. If the reader is already your default PDF app, the Settings page doesn't open.

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
3. Installs the launcher `~/.local/bin/firefox-pdf-reader` and the desktop entry `firefox-pdf-reader.desktop`. The entry runs the launcher by its plain path, and puts it in quotes only if the path has a space or another character the [desktop entry specification](https://specifications.freedesktop.org/desktop-entry/latest/exec-variables.html) reserves (`xdg-open` can't run a quoted path on a desktop it doesn't know).
4. Sets it as the default for `application/pdf` with `xdg-mime`.

It works on GNOME, KDE Plasma, Xfce, Cinnamon and other freedesktop.org desktops. Run it again to update an installed reader.

**Profile location by install type:**

| Firefox install | Profile folder |
| --- | --- |
| Regular package | `~/.local/share/firefox-pdf-reader` |
| Snap | `~/snap/firefox/common/firefox-pdf-reader` (Snap Firefox can't use hidden folders in your home) |
| Flatpak | `~/.var/app/org.mozilla.firefox/data/firefox-pdf-reader` |

On Flatpak, Firefox can read only the files it is given: the launcher gives it each PDF with `flatpak document-export` and opens it in the reader's viewer; if that fails, the PDF goes to Firefox's own viewer through the document portal, in its own colours. The Flatpak route hasn't been tried on GitHub's machines.

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

- `/usr/bin/firefox-pdf-reader`: the launcher. Each time it runs, it picks the right profile folder for native, Snap or Flatpak Firefox and refreshes the settings there, and copies the viewer there when the package brings a different one.
- the settings and the reader's viewer in `/usr/share/firefox-pdf-reader/`
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

Every platform uses the same Firefox settings in [`profile/`](profile/) and the same PDF viewer in [`viewer/`](viewer/), copied into the profile. Only the launcher and the way it's registered with the OS differ.

| Behaviour | Where it's set |
| --- | --- |
| Each PDF in its own window | The launcher passes each PDF with `-new-window`; a second PDF goes to the running reader |
| Black pages, white text, pictures in their own colours | The launcher opens the reader's viewer, `file://<profile>/viewer/web/viewer.html?file=<the PDF's address>` (on Linux and macOS made by [`launchers/viewer-url.sh`](launchers/viewer-url.sh)); see [The reader's viewer](#the-readers-viewer) |
| The viewer may read the PDF | `security.fileuri.strict_origin_policy = false`, in the reader's profile only: a page on your computer may read other files on your computer |
| A window filling the screen | Before each start the launcher writes Firefox's saved window state, `xulstore.json`, with `"sizemode": "maximized"` |
| No tabs, address bar or sidebar; the system's title bar | [`chrome/userChrome.css`](profile/chrome/userChrome.css), and `browser.tabs.inTitlebar = 0` in [`user.js`](profile/user.js) |
| No PDF toolbar or sidebar; a find bar on Ctrl+F | [`chrome/userContent.css`](profile/chrome/userContent.css), only on pages of pdf.js's viewer (a page holding `#viewer.pdfViewer`); other pages, such as a web page opened from a link, are left as they are |
| Full screen on F11, Firefox's bar at the top edge | Firefox's own full screen, with `browser.fullscreen.autohide` |
| The note on how to leave full screen | [`chrome/userContent.css`](profile/chrome/userContent.css), shown while `display-mode: fullscreen` |
| Separate from your normal Firefox | The launcher starts Firefox with `-profile <its own folder>` |
| Page width, vertical scrolling, no spreads, sidebar closed, dark viewer around the pages | The reader's viewer settings, [`viewer-settings/reader.mjs`](viewer-settings/reader.mjs); the same `pdfjs.*` settings in [`user.js`](profile/user.js) for Firefox's own viewer |
| Firefox's own viewer doesn't recolour pages | `pdfjs.forcePageColors = false` (Firefox's default, written out so an earlier install that recoloured pages gets it back) |
| Style sheets loaded | `toolkit.legacyUserProfileCustomizations.stylesheets` |
| Web links open in a new window | `externalLinkTarget: 2` in the viewer's settings, `browser.link.open_newwindow = 2` |
| Smooth scrolling | `general.smoothScroll` on, with Firefox's easing left at defaults so it doesn't fight the mouse's own smooth scrolling |
| GPU rendering | `pdfjs.enableHWA`, `gfx.webrender.all` |

The launcher is different on each platform:

| Platform | Launcher | How it's registered |
| --- | --- | --- |
| Windows | `FirefoxPDF.exe`, compiled on your machine from C# source | Current-user registry entries; appears in **Default apps** |
| macOS | `Firefox PDF Reader.app`, an AppleScript app | Declares that it opens PDFs (`com.adobe.pdf`); registered with Launch Services |
| Linux, ChromeOS | `firefox-pdf-reader` shell script | `.desktop` entry with `MimeType=application/pdf`; set as default with `xdg-mime` |

The reader's viewer remembers the zoom and reading position for each PDF (in the profile's storage for local files).

To change colours or behaviour, edit the files in `profile/` and run the installer again. Firefox applies `user.js` each time the reader starts.

## The reader's viewer

[`viewer/`](viewer/) is pdf.js 6.5.438, Mozilla's PDF viewer (the same program Firefox has built in, here as Mozilla publishes it for web pages), under the Apache License 2.0. [`tools/make_viewer.py`](tools/make_viewer.py) makes it from pdf.js's release file, checked against its SHA-256: it leaves out the source maps and the sample PDF, makes 10 small changes, each marked "Firefox PDF Reader", and adds the reader's settings ([`viewer-settings/reader.mjs`](viewer-settings/reader.mjs)). [`viewer/NOTICE`](viewer/NOTICE) lists them. The change that matters is one function in `build/pdf.mjs`, `readerColor`: when the viewer asks for page colours, it swaps only the plain greys that text, lines and fills are drawn with, instead of pdf.js's filter over the whole finished page; pictures never pass through it, and text and shapes that lie wholly on a picture drawn before them keep their own colours (`readerPicture`, `readerKeepColours`). Printing doesn't ask for page colours, so it prints the PDF's own colours.

Why a copy: Firefox's built-in viewer has no setting that recolours text but not pictures. Its `pdfjs.forcePageColors` (with `pdfjs.pageColorsBackground` and `pdfjs.pageColorsForeground`) draws the finished page, pictures included, through a filter that turns every colour into its brightness and then into one of six shades between the two colours, which is what turned pictures into washed-out two-colour images in earlier versions of the reader.

Why `security.fileuri.strict_origin_policy = false`: the viewer is a file on your computer (`file://`), and so is the PDF. With Firefox's default, a file on your computer may read only itself, so the viewer can't even start its own scripts; with the setting off, files on your computer may read each other. The reader sets it in its own profile only; your normal Firefox keeps the default.

To move to a newer pdf.js: change `VERSION` and `SHA256` in [`tools/make_viewer.py`](tools/make_viewer.py), run `python tools/make_viewer.py`, and check the test workflow's screenshots. If a change no longer fits the new release, the script stops and says which.

## Updating

Install again the same way you installed; nothing needs removing first, and nothing asks a question. The Windows and Linux scripts copy the new profile files, viewer and launcher; the Mac app and the `.deb` launcher copy the profile files from themselves every time they start, and the viewer when theirs is different, so a new app or package is the whole update. Close the reader's windows first: the next PDF you open uses the new version.

An install from before this change opened PDFs in Firefox's own viewer: the oldest in kiosk mode, recolouring every page. Its launcher is replaced, and the new `user.js` sets `pdfjs.forcePageColors` back to `false`: Firefox keeps a changed setting in the profile until something sets it again, so leaving the line out would not be enough. The Ubuntu test starts from such an install and checks this. Reading positions kept by Firefox's own viewer don't carry over to the reader's viewer: each PDF opens once at its first page.

## Alternatives that were tried (Windows)

- **Eclipse PDF (Microsoft Store).** Scrolls smoothly and has a dark mode, but it has no full-screen command and its developer console is disabled. Presentation Mode is its only full-screen view, and that shows one page at a time.
- **SumatraPDF.** Can open full screen, dark and panel-less from its settings file. But it draws pages itself, so its scrolling isn't as fluid, even with `SmoothScroll = true`.
