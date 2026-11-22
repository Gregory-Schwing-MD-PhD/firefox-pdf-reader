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
// between two colours. Instead, only the colours that text, lines and fills
// are drawn with change, and of those only greys and very pale colours (a
// pale blue table cell, a cream page): they become their opposite in
// lightness and keep any tint they have. White becomes black, a pale blue a
// dark blue, and black and dark grey become white. Every other colour stays
// as the PDF has it. Pictures (images) never come here: they are drawn
// exactly as decoded. Inside a soft mask nothing changes: there a grey says
// how much shows through, not what colour it is.
const READER_GREY = 24; // a colour whose channels (0-255) differ by at most this is a grey
const READER_PALE = 192; // a colour whose channels are all at least this is very pale
const READER_DARK = 51; // greys this dark (#333333) or darker become pure white
function readerColor(graphics, color) {
  if (!graphics.pageColors || graphics.smaskStack.length > 0 || typeof color !== "string" || !/^#[0-9a-f]{6}$/i.test(color)) {
    return color;
  }
  const rgb = [1, 3, 5].map(i => parseInt(color.slice(i, i + 2), 16));
  const max = Math.max(...rgb),
    min = Math.min(...rgb);
  if (max - min > READER_GREY && min < READER_PALE) {
    return color;
  }
  const mid = (max + min) / 2;
  const v = 255 * MathClamp((255 - mid) / (255 - READER_DARK), 0, 1);
  return Util.makeHexColor(...rgb.map(c => Math.round(MathClamp(v + c - mid, 0, 255))));
}
// Text, lines and stencils (one-colour bitmaps, such as the letters of many
// scanned pages) drawn on top of a picture, or on a fill whose colour stayed
// as the PDF has it, keep their own colours too, so they read as on paper:
// labels on an X-ray, the letters of a scan stored as a picture of the paper
// with the letters on top, black text on a yellow box, white text on a dark
// blue one. readerArea() notes, in drawing order, where each picture and each
// fill is drawn on the page; readerKeeps() looks at the last one drawn under
// a box (a shape's, a stencil's, or the point where a line of text starts)
// and says whether that one kept its colours. So a white box drawn on the
// page turns black and the text on it white, while a white box drawn on a
// picture or a kept colour stays white and the text on it black.
const READER_CELL = 128; // the areas are listed by the squares of this many pixels they touch
let readerHitContext = null;
function readerUnitBox(m) {
  const box = BBOX_INIT.slice();
  Util.axialAlignedBoundingBox([0, 0, 1, 1], m, box);
  return box;
}
function readerCells(ctx, box) {
  const n = Math.ceil(Math.max(ctx.canvas.width, ctx.canvas.height, 1) / READER_CELL);
  const cell = v => MathClamp(Math.floor(v / READER_CELL), 0, n);
  return [cell(box[0]), cell(box[1]), cell(box[2]), cell(box[3]), n + 1];
}
function readerArea(graphics, box, keep, path = null, evenOdd = false) {
  if (!graphics.pageColors || graphics.smaskStack.length > 0 || !box || !(box[0] <= box[2] && box[1] <= box[3])) {
    return;
  }
  const { ctx } = graphics;
  const area = { box: Array.from(box), keep, path, evenOdd, transform: path && getCurrentTransform(ctx) };
  graphics.readerAreas ||= new Map();
  let cells = graphics.readerAreas.get(ctx);
  if (!cells) {
    graphics.readerAreas.set(ctx, (cells = new Map()));
  }
  const [x0, y0, x1, y1, n] = readerCells(ctx, box);
  for (let y = y0; y <= y1; y++) {
    for (let x = x0; x <= x1; x++) {
      const key = y * n + x;
      const list = cells.get(key);
      if (list) {
        list.push(area);
      } else {
        cells.set(key, [area]);
      }
    }
  }
}
function readerPicture(graphics) {
  readerArea(graphics, readerUnitBox(getCurrentTransform(graphics.ctx)), true);
}
function readerFill(graphics, box, kept, path = null, evenOdd = false) {
  const { current, ctx } = graphics;
  if (current.fillAlpha < 1 || ctx.globalCompositeOperation !== "source-over") {
    return;
  }
  let keep = kept;
  if (!keep && current.patternFill) {
    keep = !(current.fillColor instanceof TilingPattern);
  } else if (!keep) {
    const color = current.transferMapsFallback?.applyToColor(current.fillColor) ?? current.fillColor;
    if (typeof color !== "string" || !/^#[0-9a-f]{6}$/i.test(color)) {
      return;
    }
    keep = readerColor(graphics, color) === color;
  }
  readerArea(graphics, box, keep, path, evenOdd);
}
function readerKeeps(graphics, box) {
  const { ctx } = graphics;
  const cells = graphics.readerAreas?.get(ctx);
  if (!cells || graphics.smaskStack.length > 0) {
    return false;
  }
  const x = (box[0] + box[2]) / 2,
    y = (box[1] + box[3]) / 2;
  const [cx, cy, , , n] = readerCells(ctx, [x, y, x, y]);
  const list = cells.get(cy * n + cx) || [];
  for (let i = list.length - 1; i >= 0; i--) {
    const a = list[i];
    if (box[0] < a.box[0] - 1 || box[1] < a.box[1] - 1 || box[2] > a.box[2] + 1 || box[3] > a.box[3] + 1) {
      continue;
    }
    if (a.path) {
      readerHitContext ||= new OffscreenCanvas(1, 1).getContext("2d");
      readerHitContext.setTransform(...a.transform);
      if (!readerHitContext.isPointInPath(a.path, x, y, a.evenOdd ? "evenodd" : "nonzero")) {
        continue;
      }
    }
    return a.keep;
  }
  return false;
}
// The PDF's own colours on the canvas; returns the colours to put back after.
function readerOwnColours(graphics) {
  const { ctx, current } = graphics;
  const saved = [ctx, ctx.fillStyle, ctx.strokeStyle];
  const own = color => current.transferMapsFallback?.applyToColor(color) ?? color;
  if (!current.patternFill && typeof current.fillColor === "string") {
    ctx.fillStyle = own(current.fillColor);
  }
  if (!current.patternStroke && typeof current.strokeColor === "string") {
    ctx.strokeStyle = own(current.strokeColor);
  }
  return saved;
}
function readerKeepColours(graphics, box) {
  return readerKeeps(graphics, box) ? readerOwnColours(graphics) : null;
}
function readerPutBack(saved) {
  if (saved) {
    [saved[0].fillStyle, saved[0].strokeStyle] = saved.slice(1);
  }
}
// The colour a stencil drawn through the matrix m (from its unit square) is filled with.
function readerStencilColour(graphics, m, color) {
  const { current } = graphics;
  if (typeof current.fillColor !== "string" || !readerKeeps(graphics, readerUnitBox(Util.transform(getCurrentTransform(graphics.ctx), m)))) {
    return color;
  }
  return current.transferMapsFallback?.applyToColor(current.fillColor) ?? current.fillColor;
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
    # Where a picture is drawn (in its unit square, before it is scaled to its pixels).
    ("build/pdf.mjs",
     "    ctx.scale(1 / width, -1 / height);\n    let imgToPaint;\n",
     "    readerPicture(this); // Firefox PDF Reader\n    ctx.scale(1 / width, -1 / height);\n    let imgToPaint;\n"),
    # A shape (its box on the page is this.current.minMax) on a picture or a
    # kept colour; and a fill, noted for what is drawn on it later.
    ("build/pdf.mjs",
     "        this.current.fillColor.updatePatternDims(clippedBBox, tilingDims);\n      }\n    }\n"
     "    this[op](opIdx, path);\n    this._pathStartIdx = opIdx;\n",
     "        this.current.fillColor.updatePatternDims(clippedBBox, tilingDims);\n      }\n    }\n"
     "    // Firefox PDF Reader: readerKeepColours(). A Type3 letter drawn with a stencil comes here as an\n"
     "    // outline (rawFillPath) in its unit square, whose minMax pdf.js gives in the stencil's pixels.\n"
     "    const readerSaved = readerKeepColours(this, op === OPS.rawFillPath ? readerUnitBox(getCurrentTransform(this.ctx)) : this.current.minMax);\n"
     "    const readerBox = this.current.getClippedPathBoundingBox();\n"
     "    this[op](opIdx, path);\n"
     "    readerPutBack(readerSaved);\n"
     "    if (op === OPS.fill || op === OPS.eoFill || op === OPS.fillStroke || op === OPS.eoFillStroke ||\n"
     "        op === OPS.closeFillStroke || op === OPS.closeEOFillStroke) {\n"
     "      readerFill(this, readerBox, readerSaved !== null, path,\n"
     "        op === OPS.eoFill || op === OPS.eoFillStroke || op === OPS.closeEOFillStroke);\n"
     "    }\n"
     "    this._pathStartIdx = opIdx;\n"),
    # A line of text on a picture or a kept colour: the point a third of the
    # font size above where it starts. (showText's own ctx.restore() puts the
    # colours back.) Text in a Type3 font is drawn by shapes and stencils,
    # which decide for themselves.
    ("build/pdf.mjs",
     "    ctx.translate(current.x, current.y + current.textRise);\n    if (fontDirection > 0) {\n      ctx.scale(textHScale, -1);\n",
     "    ctx.translate(current.x, current.y + current.textRise);\n"
     "    { // Firefox PDF Reader\n"
     "      const p = [0, fontSize / 3];\n"
     "      Util.applyTransform(p, getCurrentTransform(ctx));\n"
     "      readerKeepColours(this, [p[0], p[1], p[0], p[1]]);\n    }\n"
     "    if (fontDirection > 0) {\n      ctx.scale(textHScale, -1);\n"),
    # Pictures drawn many times over, or as a group of small ones: each is noted.
    ("build/pdf.mjs",
     "      ctx.transform(...entry.transform);\n      ctx.scale(1, -1);\n      drawImageAtIntegerCoords(ctx, imgToPaint,",
     "      ctx.transform(...entry.transform);\n      readerPicture(this); // Firefox PDF Reader\n"
     "      ctx.scale(1, -1);\n      drawImageAtIntegerCoords(ctx, imgToPaint,"),
    # A stencil (image mask) on a picture or a kept colour is filled with its own colour.
    ("build/pdf.mjs",
     "    const mask = this._createMaskCanvas(opIdx, img);\n    const maskCanvas = mask.canvas;\n",
     "    const readerSaved = readerKeepColours(this, readerUnitBox(getCurrentTransform(ctx))); // Firefox PDF Reader\n"
     "    const mask = this._createMaskCanvas(opIdx, img);\n    readerPutBack(readerSaved);\n"
     "    const maskCanvas = mask.canvas;\n"),
    # The same stencil drawn many times: in its own colour where it lies on a
    # picture or a kept colour, in the page's colours elsewhere.
    ("build/pdf.mjs",
     "    ctx.transform(scaleX, skewX, skewY, scaleY, 0, 0);\n    const mask = this._createMaskCanvas(opIdx, img);\n",
     "    ctx.transform(scaleX, skewX, skewY, scaleY, 0, 0);\n"
     "    // Firefox PDF Reader: readerKeeps()\n"
     "    const readerKeep = [];\n"
     "    for (let i = 0; i < positions.length; i += 2) {\n"
     "      readerKeep.push(readerKeeps(this, readerUnitBox(Util.transform(currentTransform, [scaleX, skewX, skewY, scaleY, positions[i], positions[i + 1]]))));\n"
     "    }\n"
     "    let readerMask = null;\n"
     "    if (readerKeep.includes(true)) {\n"
     "      const saved = readerOwnColours(this);\n"
     "      readerMask = this._createMaskCanvas(opIdx, img);\n"
     "      readerPutBack(saved);\n"
     "    }\n"
     "    const mask = this._createMaskCanvas(opIdx, img);\n"),
    ("build/pdf.mjs",
     "      ctx.drawImage(mask.canvas, trans[4], trans[5]);\n",
     "      ctx.drawImage(readerKeep[i / 2] ? readerMask.canvas : mask.canvas, trans[4], trans[5]); // Firefox PDF Reader\n"),
    ("build/pdf.mjs",
     "    ctx.restore();\n    if (mask.canvasEntry) {\n      this.canvasFactory.destroy(mask.canvasEntry);\n    }\n"
     "    this.compose();\n    this.dependencyTracker?.recordOperation(opIdx);\n",
     "    ctx.restore();\n    if (mask.canvasEntry) {\n      this.canvasFactory.destroy(mask.canvasEntry);\n    }\n"
     "    if (readerMask?.canvasEntry) { // Firefox PDF Reader\n      this.canvasFactory.destroy(readerMask.canvasEntry);\n    }\n"
     "    this.compose();\n    this.dependencyTracker?.recordOperation(opIdx);\n"),
    # A group of small stencils: each decides for itself.
    ("build/pdf.mjs",
     "      maskCtx.fillStyle = isPatternFill ? fillColor.getPattern(maskCtx, this, getCurrentTransformInverse(ctx), PathType.FILL, opIdx) : fillColor;\n",
     "      maskCtx.fillStyle = isPatternFill ? fillColor.getPattern(maskCtx, this, getCurrentTransformInverse(ctx), PathType.FILL, opIdx)\n"
     "        : readerStencilColour(this, transform, fillColor); // Firefox PDF Reader\n"),
    # A stencil of one pixel fills its whole box: a filled rectangle.
    ("build/pdf.mjs",
     "    this.ctx.fillRect(0, 0, 1, 1);\n",
     "    const readerBox = readerUnitBox(getCurrentTransform(this.ctx)); // Firefox PDF Reader\n"
     "    const readerSaved = readerKeepColours(this, readerBox);\n"
     "    this.ctx.fillRect(0, 0, 1, 1);\n"
     "    readerPutBack(readerSaved);\n"
     "    readerFill(this, readerBox, readerSaved !== null);\n"),
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
  black with white text, pictures in their own colours, and text, lines and
  stencils drawn on a picture or on a colour that stays as the PDF has it in
  their own colours;
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
