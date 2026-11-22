#!/usr/bin/env python3
"""Make the PDFs the tests open.

Usage: python tests/make_test_pdfs.py OUTDIR [--chart-only]

  OUTDIR/paper.pdf   the whole example paper, docs/example.pdf
  OUTDIR/figure.pdf  its page 5 alone: a page with a colour figure (a
                     picture) at the top, used to compare the reader's
                     colours with poppler's drawing of the same page.
                     It also gets an invisible web link (to example.com) over
                     the empty band at the top of the page, LINK_BAND points
                     down from the top edge, for the test that clicks a link.
  OUTDIR/chart.pdf   a page made here, from nothing but this script: a
                     heading and lines of text (black, dark grey and the
                     CMYK black printers use), a greyscale photograph-like
                     picture with a grey step wedge and, drawn on top of it,
                     a white label and arrow and a black label (as on an
                     X-ray in a paper), and a bar chart drawn
                     with lines and fills (coloured bars, black axes, light
                     grey grid lines). Its layout is CHART below, in points
                     from the page's top left corner; tests/check_dark_page.py
                     reads it from here.
  OUTDIR/mixed.pdf   a second page made here (US Letter wide, 360 points
                     tall): a scanned page stored the small-file way, as a
                     picture of the paper with its letters drawn on top as
                     black stencils (one large stencil, a group of small
                     ones, one small one repeated, and two Type3 fonts, one
                     drawn with stencils and one with shapes); coloured boxes
                     with text on them (pale blue, yellow, dark blue, a white
                     box on a strong blue one) and a very pale blue box; a
                     line of black text on the page; and black labels on a
                     picture drawn four times over and on a group of small
                     pictures. Its layout is MIXED below; tests/
                     check_mixed_page.py reads it from here.

Needs: numpy, and pypdf for figure.pdf (not with --chart-only, which makes
chart.pdf and mixed.pdf only).
"""
import os
import shutil
import sys
import zlib

import numpy as np

FIGURE_PAGE = 5
LINK_URL = "https://example.com/"
LINK_BAND = (20, 50)   # points from the top of the page

PAGE = (612, 792)      # US Letter, points
# Everything on chart.pdf sits in the top 340 points, so that it is on the
# screen with the page at the window's width on every test machine.
CHART = {
    "heading": {"x": 72, "top": 34, "size": 18,
                "text": "A test page: text, a picture and a chart"},
    # (top of the line, grey level of the text or "cmyk", text)
    "lines": [
        (66, 0.0, "These lines are text in black, as most pages print it. On the reader's"),
        (80, 0.0, "black page they should be white, and easy to read."),
        (94, 0.2, "This line is dark grey (20% grey), which should also become white."),
        (108, "cmyk", "This line is the black printers use (CMYK black), which should become white."),
        (300, 0.0, "Below the picture and the chart, more black text: it should be white too."),
        (314, 0.0, "The picture keeps its own greys and the chart keeps its own colours."),
    ],
    "text_size": 11,
    # The greyscale picture: its box on the page, and its size in pixels
    "picture": {"x": 72, "top": 126, "width": 216, "height": 162, "pixels": (432, 324)},
    # Drawn on the picture: (x, top, size, grey, text), points from the
    # page's top left; and a white arrow from (x, top) to (x, top)
    "picture_labels": [(80, 134, 16, 1.0, "A"), (204, 216, 16, 0.0, "B")],
    "picture_arrow": ((104, 140), (150, 170)),
    # The bar chart: the box its axes span, its bars and their colours
    "chart": {"x": 336, "top": 126, "width": 204, "height": 150,
              "bars": [(0.10, 0.62, (31, 119, 180)),     # (left, height, RGB): blue
                       (0.33, 0.88, (255, 127, 14)),     # orange
                       (0.56, 0.45, (44, 160, 44)),      # green
                       (0.79, 0.30, (214, 39, 40))],     # red
              "bar_width": 0.15,                         # share of the chart's width
              "axis_width": 2.0,                         # points
              "grid": [0.25, 0.5, 0.75, 1.0],            # light grey grid lines (share of height)
              "grid_grey": 0.8},
}


MIXED_PAGE = (612, 360)
# Boxes are (x, top, width, height) in points from the page's top left.
MIXED = {
    # The scanned page: a picture of the paper; on it, the letters as black
    # stencils, in bands (what each band is, its box)
    "paper": {"box": (36, 20, 260, 130), "rgb": (239, 233, 221), "pixels_per_point": 2},
    "scan_bands": [
        ("one large stencil", (46, 28, 240, 36)),
        ("a group of small stencils", (46, 72, 236, 16)),
        ("one small stencil repeated", (46, 96, 236, 16)),
        ("Type3 font drawn with stencils", (46, 122, 112, 18)),
        ("Type3 font drawn with shapes", (172, 122, 112, 18)),
    ],
    # Coloured boxes, each with a line of text (text colour 0 = black, 1 = white)
    "boxes": [
        ("pale blue box", (316, 20, 124, 36), (219, 233, 246), 0, "Black on pale blue"),
        ("yellow box", (452, 20, 124, 36), (255, 221, 0), 0, "Black on yellow"),
        ("dark blue box", (316, 64, 124, 36), (31, 56, 100), 1, "White on dark blue"),
    ],
    # A white box with black text, on a strong blue box (as on a poster)
    "poster": {"blue": (452, 64, 124, 80), "blue_rgb": (40, 90, 200),
               "white": (462, 72, 104, 34), "text": "On a white box"},
    # A very pale blue box, no text
    "pale_tint": {"box": (316, 108, 124, 36), "rgb": (238, 243, 251)},
    # Black text on the page
    "page_text": {"box": (316, 154, 260, 14), "size": 11, "text": "Black text on the page, as most pages print it."},
    # One picture drawn four times (2 x 2), and twelve small pictures; a black
    # label on each
    "repeated": {"box": (36, 176, 160, 160), "label": (132, 276, 58, 18)},
    "group": {"box": (216, 176, 160, 120), "label": (232, 196, 58, 18)},
    "text_size": 10,
    "label_size": 15,
}


def glyph_bitmaps(count, w, h, seed):
    """Letter-like one-colour bitmaps: strokes on a w x h grid of cells."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(count):
        cells = np.zeros((7, 5), bool)
        cells[:, 0] = rng.random() < 0.7                  # a left stem
        cells[0, :] = rng.random() < 0.6                  # a top bar
        cells[3, :] = rng.random() < 0.6                  # a middle bar
        cells[6, :] = rng.random() < 0.6                  # a bottom bar
        cells[:, 4] = rng.random() < 0.5                  # a right stem
        cells |= rng.random((7, 5)) < 0.12
        if not cells.any():
            cells[:, 2] = True
        g = np.kron(cells, np.ones((h // 7, w // 5), bool))
        pad = np.zeros((h, w), bool)
        pad[:g.shape[0], :g.shape[1]] = g
        out.append(pad)
    return out


def stencil_bits(ink):
    """An image mask's data: 1 bit a pixel, rows padded to bytes; with the
    default Decode [0 1] a 0 bit is painted."""
    return np.packbits(np.where(ink, 0, 1).astype(np.uint8), axis=1).tobytes()


def write_pdf(path, objects):
    """objects: the bodies of objects 1, 2, ... (object 1 is the catalog)."""
    data = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objects, 1):
        offsets.append(len(data))
        data += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(data)
    data += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        data += f"{off:010d} 00000 n \n".encode()
    data += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    with open(path, "wb") as f:
        f.write(data)


def make_mixed_pdf(out):
    W, H = MIXED_PAGE
    m = MIXED
    objects = []

    def add(body):
        objects.append(body if isinstance(body, bytes) else body.encode())
        return len(objects)

    def stream(dictionary, data, flate=True):
        if flate:
            data = zlib.compress(data)
            dictionary += " /Filter /FlateDecode"
        return add(f"<< {dictionary} /Length {len(data)} >>\nstream\n".encode() + data + b"\nendstream")

    def cm(box):
        x, top, w, h = box
        return f"{w} 0 0 {h} {x} {H - top - h} cm"

    for _ in range(5):                                   # catalog, pages, page, two fonts
        add(b"")
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    objects[4] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
    xobjects = {}
    ops = []
    rng = np.random.default_rng(20261123)

    # The scanned page: the paper as a colour picture, faintly uneven
    p = m["paper"]
    x, top, w, h = p["box"]
    k = p["pixels_per_point"]
    paper = np.empty((h * k, w * k, 3))
    paper[:] = p["rgb"]
    paper += rng.normal(0, 3, paper.shape[:2])[..., None]
    paper += np.linspace(-4, 4, w * k)[None, :, None]
    paper = np.clip(np.round(paper), 0, 255).astype(np.uint8)
    xobjects["Paper"] = stream(f"/Type /XObject /Subtype /Image /Width {w * k} /Height {h * k} "
                               "/ColorSpace /DeviceRGB /BitsPerComponent 8", paper.tobytes())
    ops.append(f"q {cm(p['box'])} /Paper Do Q")
    ops.append("0 g")
    bands = dict(m["scan_bands"])
    # One large stencil: lines of letters, as a scan's text layer is stored
    bx, bt, bw, bh = bands["one large stencil"]
    ink = np.zeros((bh * k, bw * k), bool)
    letters = glyph_bitmaps(60, 15, 21, 1)
    i = 0
    for row in range(2):
        cx = 2
        while cx + 15 < bw * k:
            if rng.random() < 0.18:                      # a space between words
                cx += 10
                continue
            y0 = 6 + row * 36
            ink[y0:y0 + 21, cx:cx + 15] |= letters[i % len(letters)]
            i += 1
            cx += 19
    xobjects["Stencil"] = stream(f"/Type /XObject /Subtype /Image /Width {bw * k} /Height {bh * k} "
                                 "/ImageMask true /BitsPerComponent 1", stencil_bits(ink))
    ops.append(f"q {cm(bands['one large stencil'])} /Stencil Do Q")
    ops.append("0 g")                                    # (keeps pdf.js from joining the stencils below to this one)
    # Twelve small stencils, all different, drawn twice in the same places:
    # pdf.js draws the first time one by one, and the second time, from its
    # store of images already read, as one group
    bx, bt, bw, bh = bands["a group of small stencils"]
    for j, g in enumerate(glyph_bitmaps(12, 30, 35, 2)):
        xobjects[f"Small{j}"] = stream("/Type /XObject /Subtype /Image /Width 30 /Height 35 "
                                       "/ImageMask true /BitsPerComponent 1", stencil_bits(g))
    for _ in range(2):
        for j in range(12):
            ops.append(f"q {cm((bx + j * 20, bt, 14, bh))} /Small{j} Do Q")
    # One small stencil twelve times at the same size (pdf.js draws the first
    # one by itself and the other eleven as one repeated stencil)
    ops.append("0 g")
    bx, bt, bw, bh = bands["one small stencil repeated"]
    xobjects["Repeat"] = stream("/Type /XObject /Subtype /Image /Width 30 /Height 35 "
                                "/ImageMask true /BitsPerComponent 1", stencil_bits(glyph_bitmaps(1, 30, 35, 3)[0]))
    for j in range(12):
        ops.append(f"q {cm((bx + j * 20, bt, 14, bh))} /Repeat Do Q")
    # Two Type3 fonts: letters drawn with a stencil, and letters drawn with shapes
    gl = np.zeros((28, 20), bool)                        # a thick-stroked E
    gl[2:26, 2:7] = gl[2:7, 2:18] = gl[12:16, 2:15] = gl[21:26, 2:18] = True
    hexdata = stencil_bits(gl).hex()
    bitmap_glyph = stream("", (f"600 0 0 0 600 800 d1 q 600 0 0 800 0 0 cm "
                               f"BI /IM true /W 20 /H 28 /F /AHx ID\n{hexdata}>\nEI Q").encode())
    shape_glyph = stream("", b"600 0 0 0 600 800 d1 40 0 m 560 0 l 560 800 l 40 800 l h "
                             b"180 140 m 180 660 l 420 660 l 420 140 l h f*")
    fonts = {}
    for name, glyph in (("T3a", bitmap_glyph), ("T3b", shape_glyph)):
        fonts[name] = add(f"<< /Type /Font /Subtype /Type3 /FontBBox [0 0 600 800] "
                          f"/FontMatrix [0.001 0 0 0.001 0 0] /CharProcs << /a {glyph} 0 R >> "
                          f"/Encoding << /Type /Encoding /Differences [97 /a] >> /FirstChar 97 /LastChar 97 "
                          f"/Widths [700] /Resources << >> >>")
    for name, band in (("T3a", "Type3 font drawn with stencils"), ("T3b", "Type3 font drawn with shapes")):
        bx, bt, bw, bh = bands[band]
        ops.append(f"BT /{name} {bh} Tf 0 g {bx} {H - bt - bh:.2f} Td (aaaaaaaa) Tj ET")

    # Coloured boxes with text on them
    size = m["text_size"]
    for _, (x, top, w, h), (r, g, b), text_grey, text in m["boxes"]:
        ops.append(f"{r / 255:.4f} {g / 255:.4f} {b / 255:.4f} rg {x} {H - top - h} {w} {h} re f")
        ops.append(f"BT /F1 {size} Tf {text_grey} g {x + 6} {H - top - h / 2 - size * 0.35:.2f} Td "
                   f"({pdf_text(text)}) Tj ET")
    po = m["poster"]
    x, top, w, h = po["blue"]
    r, g, b = po["blue_rgb"]
    ops.append(f"{r / 255:.4f} {g / 255:.4f} {b / 255:.4f} rg {x} {H - top - h} {w} {h} re f")
    x, top, w, h = po["white"]
    ops.append(f"1 g {x} {H - top - h} {w} {h} re f")
    ops.append(f"BT /F1 {size} Tf 0 g {x + 6} {H - top - h / 2 - size * 0.35:.2f} Td ({pdf_text(po['text'])}) Tj ET")
    pt = m["pale_tint"]
    x, top, w, h = pt["box"]
    r, g, b = pt["rgb"]
    ops.append(f"{r / 255:.4f} {g / 255:.4f} {b / 255:.4f} rg {x} {H - top - h} {w} {h} re f")
    tx = m["page_text"]
    x, top, w, h = tx["box"]
    ops.append(f"BT /F2 {tx['size']} Tf 0 g {x} {H - top - tx['size']:.2f} Td ({pdf_text(tx['text'])}) Tj ET")

    # One light picture drawn four times (pdf.js draws the first by itself and
    # the other three as one repeated picture; the label is on the last)
    yy, xx = np.mgrid[0:160, 0:160] / 159.0
    tile = np.stack([215 + 35 * xx, 200 + 45 * yy, 245 - 30 * xx * yy], axis=2)
    tile += rng.normal(0, 3, tile.shape[:2])[..., None]
    tile = np.clip(np.round(tile), 0, 255).astype(np.uint8)
    xobjects["Tile"] = stream("/Type /XObject /Subtype /Image /Width 160 /Height 160 "
                              "/ColorSpace /DeviceRGB /BitsPerComponent 8", tile.tobytes())
    x, top, w, h = m["repeated"]["box"]
    for dx in (0, w / 2):
        for dy in (0, h / 2):
            ops.append(f"q {cm((x + dx, top + dy, w / 2, h / 2))} /Tile Do Q")
    # Twelve small light pictures as inline images (pdf.js draws these as one group)
    x, top, w, h = m["group"]["box"]
    for j in range(12):
        c = np.array([200 + (j * 37) % 50, 205 + (j * 23) % 45, 210 + (j * 11) % 40])
        a = np.empty((6, 6, 3), np.uint8)
        a[:] = c
        a[:3, :3] = np.minimum(c + 6, 255)
        ops.append(f"q {cm((x + (j % 4) * w / 4, top + (j // 4) * h / 3, w / 4, h / 3))} "
                   f"BI /W 6 /H 6 /CS /RGB /BPC 8 /F /AHx ID\n{a.tobytes().hex()}>\nEI Q")
    # A black label on each
    ls = m["label_size"]
    for key in ("repeated", "group"):
        x, top, w, h = m[key]["label"]
        ops.append(f"BT /F2 {ls} Tf 0 g {x + 2} {H - top - ls + 1:.2f} Td (Label) Tj ET")

    content = stream("", "\n".join(ops).encode("latin-1"))
    xo = " ".join(f"/{name} {num} 0 R" for name, num in xobjects.items())
    fo = " ".join(f"/{name} {num} 0 R" for name, num in fonts.items())
    objects[2] = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] "
                  f"/Resources << /Font << /F1 4 0 R /F2 5 0 R {fo} >> /XObject << {xo} >> >> "
                  f"/Contents {content} 0 R >>").encode()
    write_pdf(out, objects)


def make_figure_pdf(src, out):
    from pypdf import PdfReader, PdfWriter
    from pypdf.annotations import Link

    w = PdfWriter()
    page = w.add_page(PdfReader(src).pages[FIGURE_PAGE - 1])
    width, height = float(page.mediabox.width), float(page.mediabox.height)
    top, bottom = height - LINK_BAND[0], height - LINK_BAND[1]
    w.add_annotation(page_number=0, annotation=Link(rect=(72, bottom, width - 72, top),
                                                    url=LINK_URL, border=[0, 0, 0]))
    with open(out, "wb") as f:
        w.write(f)
    return width, height


def picture_pixels(width, height):
    """A photograph-like greyscale picture, like an X-ray: a dark background,
    soft bright shapes, smooth shading and fine grain, and along its bottom a
    step wedge of eight greys from black to white (left to right)."""
    rng = np.random.default_rng(20261122)
    y, x = np.mgrid[0:height, 0:width].astype(np.float64)
    x /= width
    y /= height
    img = 40 + 50 * x                                     # smooth shading
    for cx, cy, rx, ry, level in [(0.30, 0.30, 0.16, 0.10, 150), (0.32, 0.55, 0.17, 0.10, 165),
                                  (0.68, 0.35, 0.12, 0.18, 120), (0.62, 0.62, 0.20, 0.08, 185)]:
        d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        img += level * np.exp(-d ** 2)                    # soft-edged bright shapes
    img += rng.normal(0, 6, img.shape)                    # grain
    wedge = y > 0.80
    img[wedge] = np.floor(x[wedge] * 8) / 7 * 255         # 0, 36, ..., 255
    return np.clip(np.round(img), 0, 255).astype(np.uint8)


def pdf_text(s):
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_chart_pdf(out):
    W, H = PAGE
    c = CHART
    ops = []
    # Heading and lines of text
    hd = c["heading"]
    ops.append(f"BT /F2 {hd['size']} Tf 0 g {hd['x']} {H - hd['top'] - hd['size']:.2f} Td ({pdf_text(hd['text'])}) Tj ET")
    for top, grey, text in c["lines"]:
        colour = "0 0 0 1 k" if grey == "cmyk" else f"{grey} g"
        ops.append(f"BT /F1 {c['text_size']} Tf {colour} 72 {H - top - c['text_size']:.2f} Td ({pdf_text(text)}) Tj ET")
    # The picture
    p = c["picture"]
    ops.append(f"q {p['width']} 0 0 {p['height']} {p['x']} {H - p['top'] - p['height']} cm /Im1 Do Q")
    # Labels and an arrow drawn on the picture
    for x, top, size, grey, text in c["picture_labels"]:
        ops.append(f"BT /F2 {size} Tf {grey} g {x} {H - top - size:.2f} Td ({pdf_text(text)}) Tj ET")
    (ax0, at0), (ax1, at1) = c["picture_arrow"]
    ops.append(f"q 1 G 1 g 2 w {ax0} {H - at0} m {ax1 - 6} {H - at1 + 4} l S "
               f"{ax1} {H - at1} m {ax1 - 11} {H - at1 + 2} l {ax1 - 6} {H - at1 + 9} l h f Q")
    # The chart: grid lines, bars, then axes on top
    ch = c["chart"]
    x0, y0 = ch["x"], H - ch["top"] - ch["height"]        # the axes' corner (bottom left)
    cw, chh = ch["width"], ch["height"]
    ops.append(f"q {ch['grid_grey']} G 0.75 w")
    for g in ch["grid"]:
        ops.append(f"{x0} {y0 + g * chh:.2f} m {x0 + cw} {y0 + g * chh:.2f} l S")
    ops.append("Q")
    for left, height, (r, g, b) in ch["bars"]:
        ops.append(f"{r / 255:.4f} {g / 255:.4f} {b / 255:.4f} rg "
                   f"{x0 + left * cw:.2f} {y0} {ch['bar_width'] * cw:.2f} {height * chh:.2f} re f")
    aw = ch["axis_width"]
    ops.append(f"q 0 G {aw} w 2 J {x0} {y0 + chh} m {x0} {y0} l {x0 + cw} {y0} l S")
    for g in ch["grid"]:                                  # tick marks on the left axis
        ops.append(f"{x0 - 6} {y0 + g * chh:.2f} m {x0} {y0 + g * chh:.2f} l S")
    ops.append("Q")
    content = zlib.compress("\n".join(ops).encode("latin-1"))

    pw, ph = p["pixels"]
    image = zlib.compress(picture_pixels(pw, ph).tobytes())

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] "
         f"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> /XObject << /Im1 6 0 R >> >> "
         f"/Contents 7 0 R >>").encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        (f"<< /Type /XObject /Subtype /Image /Width {pw} /Height {ph} /ColorSpace /DeviceGray "
         f"/BitsPerComponent 8 /Filter /FlateDecode /Length {len(image)} >>\nstream\n").encode()
        + image + b"\nendstream",
        f"<< /Filter /FlateDecode /Length {len(content)} >>\nstream\n".encode()
        + content + b"\nendstream",
    ]
    data = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objects, 1):
        offsets.append(len(data))
        data += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(data)
    data += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        data += f"{off:010d} 00000 n \n".encode()
    data += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    with open(out, "wb") as f:
        f.write(data)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    make_chart_pdf(os.path.join(out, "chart.pdf"))
    make_mixed_pdf(os.path.join(out, "mixed.pdf"))
    if "--chart-only" in sys.argv:
        print("wrote", os.path.join(out, "chart.pdf"), "and", os.path.join(out, "mixed.pdf"))
        return
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "example.pdf")
    shutil.copyfile(src, os.path.join(out, "paper.pdf"))
    width, height = make_figure_pdf(src, os.path.join(out, "figure.pdf"))
    print("wrote", os.path.join(out, "paper.pdf"), ",", os.path.join(out, "figure.pdf"),
          f"(page {width:g} x {height:g} points, link to {LINK_URL} {LINK_BAND[0]}-{LINK_BAND[1]} points from the top)",
          ",", os.path.join(out, "chart.pdf"), "and", os.path.join(out, "mixed.pdf"))


if __name__ == "__main__":
    main()
