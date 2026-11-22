# Firefox PDF Reader

[![test](https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader/actions/workflows/test.yml/badge.svg)](https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader/actions/workflows/test.yml)

## Install

### **[⬇ Download Firefox PDF Reader](https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/#install)**

The download page detects your system and gives you the matching download. Each one sets up the reader and makes it your default PDF app:

| System | Download | How it installs |
| --- | --- | --- |
| Windows | [FirefoxPDFReader-Setup.cmd](https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader/releases/latest/download/FirefoxPDFReader-Setup.cmd) | Double-click it. Installs Firefox too, if it's missing. |
| macOS | [FirefoxPDFReader.dmg](https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader/releases/latest/download/FirefoxPDFReader.dmg) | Drag **Firefox PDF Reader** into **Applications**, then open it once. |
| Ubuntu, Debian, Mint, Pop!_OS | [FirefoxPDFReader.deb](https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader/releases/latest/download/FirefoxPDFReader.deb) | Double-click it to install. Brings Firefox with it. |
| ChromeOS | [FirefoxPDFReader.deb](https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader/releases/latest/download/FirefoxPDFReader.deb) | Turn on Linux, then double-click it in **Files**. |

The Mac app isn't signed by an Apple-registered developer yet, so the first time you open it, macOS asks you to allow it. Go to **System Settings → Privacy & Security** and click **Open Anyway**; you only do this once.

<details>
<summary>Or install from a terminal</summary>

**Windows (PowerShell):**

```powershell
powershell -c "irm https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/install/windows.ps1 | iex"
```

**macOS, Linux (including Fedora, Arch and others), ChromeOS (Terminal):**

```sh
curl -fsSL https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/install/install.sh | sh
```

On ChromeOS, first turn on Linux: **Settings → About ChromeOS → Developers → Linux development environment**.

To install from a copy of this repository, or to uninstall, see [INSTALL.md](INSTALL.md).
</details>

## Try it

<img src="docs/preview.svg" width="640" height="400" alt="Firefox PDF Reader scrolling through the example paper: its colour figure in its own colours, white pages on a dark viewer, nothing but the pages">

This is the actual reader showing the example paper from its colour figure on page 5: what Firefox, with the reader's own settings, draws inside the reader's window, captured at 1440 × 900 and shown at exactly 640 × 400, the same shape with nothing cropped.

GitHub doesn't allow interactive content in a README. To scroll the paper yourself, click the animation or open the **[interactive demo](https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/demo.html)**. It remembers where you were, and F or a double-click makes it full screen.

## Features

- **Pictures in their own colours.** Pages and their figures keep the colours they were made with, drawn sharp at your screen's resolution. Only the space around the pages is dark.
- **Nothing but the PDF.** Each PDF opens in a window that fills the screen with its pages, under your system's own title bar: no tabs, address bar, toolbar, sidebar or notice bars.
- **One window per PDF.** Every PDF gets a window of its own, named after its file, so you switch between them like any other windows: **Alt+Tab** on Windows and Linux, **Cmd+`** on a Mac.
- **Full screen when you want it, and a way out.** **F11** makes a PDF full screen and **F11** again brings the window back (on a Mac: **Ctrl+Cmd+F**, and **Esc** to leave). For the first seconds of full screen, a short note at the bottom says how to leave it. A window can always be minimised, switched away from and closed like any app.
- **Continuous.** One long vertical scroll through every page, fit to the page width.
- **Remembers your spot.** Reopen a PDF and you're back where you left off, at the same zoom.
- **Smooth scrolling.** Firefox's smooth scrolling, set up to work with your mouse's own smooth scrolling. See [Smooth scrolling](INSTALL.md#smooth-scrolling) for Logitech and other mice.
- **Low latency.** Pages are drawn on the graphics card (WebRender, with GPU-accelerated PDF rendering), and there are no add-ons, start page or session restore to wait for.
- **Default PDF app.** Double-click any PDF to open it in the reader.
- **Separate from your browser.** The reader runs in its own Firefox profile, so your normal Firefox, its bookmarks and extensions are untouched.
- **Private.** The reader's profile sends no usage data to Mozilla and runs no studies.
- **Works everywhere.** Windows, macOS, Linux (Ubuntu, Debian, Fedora, Arch and others, with Firefox from your distribution, Snap or Flatpak) and ChromeOS.
- **Tested.** Every change is installed and used on Windows, macOS, Ubuntu and a ChromeOS-style Linux on [GitHub Actions](https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader/actions/workflows/test.yml): two PDFs opened into two windows, switched with Alt+Tab (Cmd+`), made full screen and back, closed; and a colour figure compared, pixel by pixel, with another PDF program's (poppler's) drawing of the same page. Screenshots of every step are saved with each run.
- **Easy to remove.** One command uninstalls it; see [INSTALL.md](INSTALL.md).

**Keys:**

| | Windows, Linux | Mac |
| --- | --- | --- |
| Full screen | **F11**, and **F11** again to leave | **Ctrl+Cmd+F**, and **Esc** to leave |
| Switch between PDFs | **Alt+Tab** | **Cmd+`** |
| Close a PDF | **Ctrl+W** | **Cmd+W** |
| Close the reader | **Alt+F4** closes a window; the reader ends with its last one | **Cmd+Q** |
| Find text | **Ctrl+F** | **Cmd+F** |
| Zoom | **Ctrl +/−** | **Cmd +/−** |

Good to know:
- Firefox has no setting that starts an ordinary window full screen. Its kiosk mode does, but leaves no way out, which is what the reader used before. So the reader opens each PDF in a window that fills the screen, and F11 takes it the rest of the way.
- On Windows and Linux, Esc doesn't leave Firefox's full screen (Firefox keeps Esc there for its own bar) and Firefox has no setting to change that; F11 does. Moving the mouse to the top edge in full screen also slides down Firefox's bar, with buttons to leave full screen or close.
- On GNOME (Ubuntu's desktop), Alt+Tab groups windows by app: hold Alt and press **`** (the key above Tab) to step through the reader's windows. On Windows, Alt+Tab lists every window.
- On a Mac, a full-screen window is a space of its own: Cmd+` switches between the reader's windows that aren't full screen, and Ctrl+← / Ctrl+→ (or a swipe) between full-screen spaces. Cmd+Tab switches between apps.
- A window's title is the PDF's file name. If the PDF has a title of its own, Firefox shows that first, then the file name.
- A web link in a PDF opens in a new window; close it (Ctrl+W, Cmd+W) to get back to the PDF.

## Updating

To update an installed reader, install it again the same way; nothing needs removing first, and nothing asks a question:

- **Windows:** run **FirefoxPDFReader-Setup.cmd** again (or the PowerShell line above). If the reader is already your default PDF app, it stays so and the Settings page doesn't open.
- **Mac:** download the new **FirefoxPDFReader.dmg** and drag the app into **Applications** again, replacing the old one (or run the Terminal line again).
- **Ubuntu, Debian, Mint, Pop!_OS, ChromeOS:** open the new **FirefoxPDFReader.deb** (or `sudo apt install ./FirefoxPDFReader.deb`).
- **Fedora, Arch and others:** run the Terminal line again.

Close the reader's windows first: the next PDF you open uses the new version. The update also undoes the earlier version's settings that recoloured every page.

## License

The code in this repository (installers, launcher, Firefox settings and the website) is released under the [MIT License](LICENSE).

The example paper, [`docs/example.pdf`](docs/example.pdf) (*Not All Spines Are Created Equal: How CT Segmenters Fail on Lumbosacral Transitional Vertebrae*), is © its authors. It's included only as a demo document and is not covered by the MIT License.

The reader uses Firefox, and its PDF viewer pdf.js, installed separately from Mozilla under the [Mozilla Public License 2.0](https://www.mozilla.org/MPL/2.0/). The web demo loads [pdf.js](https://github.com/mozilla/pdf.js) (Apache License 2.0) from cdnjs. Firefox is a trademark of the Mozilla Foundation. This project is not affiliated with or endorsed by Mozilla.

## Contact

Questions, bugs or ideas: **[open an issue](https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader/issues/new/choose)**. Replies come through GitHub, so you don't need to share an email address.
