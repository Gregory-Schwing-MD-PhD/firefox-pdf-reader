#!/usr/bin/env python3
"""Build viewer/: the reader's own copy of pdf.js's PDF viewer.

Usage: python tools/make_viewer.py [OUTDIR] [--zip PATH]

The copy is the official pdf.js release below (Mozilla's "generic viewer",
Apache License 2.0), downloaded from GitHub and checked against its SHA-256,
with the source maps and the sample PDF left out, and with the small changes
in PATCHES applied. Then the reader's own settings, viewer-settings/reader.mjs,
are added next to viewer.html. OUTDIR is viewer/ by default. The test
workflow runs this and checks that the result is exactly what the repository
holds in viewer/.

Each change must match the release's text exactly once; if a new release
moves things around, this stops instead of guessing.
"""
import argparse
import hashlib
import io
import os
import shutil
import sys
import urllib.request
import zipfile

VERSION = "6.5.438"
URL = f"https://github.com/mozilla/pdf.js/releases/download/v{VERSION}/pdfjs-{VERSION}-dist.zip"
SHA256 = "fcbe9ba21d9911843e3502adc178a7f549a524a4055f887bedc942e5490c6ba1"
LEFT_OUT = (".map", "web/compressed.tracemonkey-pldi-09.pdf")

READER_COLOR = '''\
// Firefox PDF Reader: black pages, white text, pictures in their own colours.
// When the viewer asks for page colours ("pageColors": the reader's viewer
// does on screen, never when printing), pdf.js would draw the finished page
// through one filter that turns every colour, pictures included, into shades
// between two colours. Instead, only the plain greys that text, lines and
// fills are drawn with change: a grey becomes its opposite (white becomes
// black; black and dark grey become white) and every other colour stays as
// the PDF has it. Pictures (images) never come here: they are drawn exactly as
// decoded. Inside a soft mask nothing changes: there a grey says how much
// shows through, not what colour it is.
const READER_GREY = 24; // a colour whose channels (0-255) differ by at most this is a grey
const READER_DARK = 51; // greys this dark (#333333) or darker become pure white
function readerColor(graphics, color) {
  if (!graphics.pageColors || graphics.smaskStack.length > 0 || typeof color !== "string" || !/^#[0-9a-f]{6}$/i.test(color)) {
    return color;
  }
  const r = parseInt(color.slice(1, 3), 16),
    g = parseInt(color.slice(3, 5), 16),
    b = parseInt(color.slice(5, 7), 16);
  const max = Math.max(r, g, b),
    min = Math.min(r, g, b);
  if (max - min > READER_GREY) {
    return color;
  }
  const v = Math.round(255 * MathClamp((255 - (max + min) / 2) / (255 - READER_DARK), 0, 1));
  return Util.makeHexColor(v, v, v);
}
'''

# (file, the release's text, the reader's text)
PATCHES = [
    # The function above, just before the class that draws pages.
    ("build/pdf.mjs",
     "const EO_CLIP = {};\nclass CanvasGraphics {\n",
     "const EO_CLIP = {};\n" + READER_COLOR + "class CanvasGraphics {\n"),
    # The page's own background: white, or black in the reader's colours.
    ("build/pdf.mjs",
     '    this.ctx.fillStyle = background || "#ffffff";\n',
     '    this.ctx.fillStyle = background || readerColor(this, "#ffffff"); // Firefox PDF Reader\n'),
    # No filter over the whole finished page (it would recolour pictures).
    ("build/pdf.mjs",
     "  #drawFilter() {\n    if (this.pageColors) {\n",
     "  #drawFilter() {\n    // Firefox PDF Reader: no filter; readerColor() changes the greys instead.\n"
     "    return;\n    if (this.pageColors) {\n"),
    # Every colour text, lines and fills are drawn with goes through here.
    ("build/pdf.mjs",
     "  #transferColor(color) {\n    return this.current.transferMapsFallback?.applyToColor(color) ?? color;\n",
     "  #transferColor(color) {\n    // Firefox PDF Reader: readerColor()\n"
     "    return readerColor(this, this.current.transferMapsFallback?.applyToColor(color) ?? color);\n"),
    # The colour of a pattern filled with one colour (an "uncoloured" tiling pattern).
    ("build/pdf.mjs",
     "    ctx.fillStyle = ctx.strokeStyle = current.transferMapsFallback?.applyToColor(color) ?? color;\n",
     "    // Firefox PDF Reader: readerColor()\n"
     "    ctx.fillStyle = ctx.strokeStyle = readerColor(graphics, current.transferMapsFallback?.applyToColor(color) ?? color);\n"),
    # A pattern's own drawing (hatching, for example) gets the same colours.
    ("build/pdf.mjs",
     "        }, undefined, undefined, this.dependencyTracker ? new CanvasNestedDependencyTracker(",
     "        }, undefined, this.pageColors /* Firefox PDF Reader */, this.dependencyTracker ? new CanvasNestedDependencyTracker("),
    # The reader's settings (reader.mjs), read just before the viewer starts.
    ("web/viewer.html",
     '  <script src="viewer.mjs" type="module"></script>\n',
     "  <!-- Firefox PDF Reader: its settings, read just before the viewer starts -->\n"
     '  <script src="reader.mjs" type="module"></script>\n  <script src="viewer.mjs" type="module"></script>\n'),
]

READER_FILES = ["reader.mjs"]

NOTICE = f"""\
This folder is a copy of pdf.js {VERSION}, Mozilla's PDF viewer for the web
(https://github.com/mozilla/pdf.js), from its release file
pdfjs-{VERSION}-dist.zip (SHA-256 {SHA256}).
pdf.js is Copyright Mozilla Foundation and the pdf.js contributors, under the
Apache License 2.0 (LICENSE in this folder). The colour maps, fonts, colour
profile and WebAssembly parts it comes with carry their own licences, in the
folders that hold them (web/cmaps, web/standard_fonts, web/iccs, web/wasm).

Firefox PDF Reader changed it with tools/make_viewer.py in its repository
(https://github.com/Gregory-Schwing-MD-PhD/firefox-pdf-reader):
- left out: the source maps (*.map) and the sample PDF;
- build/pdf.mjs: {sum(1 for p in PATCHES if p[0] == "build/pdf.mjs")} changes, each marked "Firefox PDF Reader": pages are drawn
  black with white text, and pictures in their own colours;
- web/viewer.html: reads the reader's settings, web/reader.mjs, before the
  viewer starts;
- added: web/reader.mjs (the reader's settings, MIT License), NOTICE and
  VERSION.
"""


def release_zip(path):
    if path:
        with open(path, "rb") as f:
            data = f.read()
    else:
        for attempt in range(4):
            try:
                with urllib.request.urlopen(URL, timeout=120) as r:
                    data = r.read()
                break
            except OSError:
                if attempt == 3:
                    raise
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        sys.exit(f"pdf.js {VERSION}: SHA-256 {digest}, expected {SHA256}")
    return zipfile.ZipFile(io.BytesIO(data))


def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir", nargs="?", default=os.path.join(repo, "viewer"))
    ap.add_argument("--zip", help="the release zip, already downloaded")
    a = ap.parse_args()

    z = release_zip(a.zip)
    if os.path.exists(a.outdir):
        shutil.rmtree(a.outdir)
    for info in z.infolist():
        name = info.filename
        if info.is_dir() or name.endswith(LEFT_OUT[0]) or name == LEFT_OUT[1]:
            continue
        dest = os.path.join(a.outdir, *name.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(z.read(name))

    for rel, old, new in PATCHES:
        path = os.path.join(a.outdir, *rel.split("/"))
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        count = text.count(old)
        if count != 1:
            sys.exit(f"{rel}: the text to change was found {count} times, not once:\n{old}")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text.replace(old, new))

    for name in READER_FILES:
        shutil.copyfile(os.path.join(repo, "viewer-settings", name), os.path.join(a.outdir, "web", name))
    with open(os.path.join(a.outdir, "NOTICE"), "w", encoding="utf-8", newline="\n") as f:
        f.write(NOTICE)

    # VERSION names this build by a digest of all its files, so the launchers
    # can tell when the copy in a profile needs replacing.
    h = hashlib.sha256()
    for root, _, files in sorted(os.walk(a.outdir)):
        for name in sorted(files):
            path = os.path.join(root, name)
            h.update(os.path.relpath(path, a.outdir).replace(os.sep, "/").encode() + b"\0")
            with open(path, "rb") as f:
                h.update(f.read())
    with open(os.path.join(a.outdir, "VERSION"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"pdf.js {VERSION}, Firefox PDF Reader build {h.hexdigest()[:12]}\n")
    print(f"viewer: pdf.js {VERSION} with {len(PATCHES)} changes, in {a.outdir}")


if __name__ == "__main__":
    main()
