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
                     picture with a grey step wedge, and a bar chart drawn
                     with lines and fills (coloured bars, black axes, light
                     grey grid lines). Its layout is CHART below, in points
                     from the page's top left corner; tests/check_dark_page.py
                     reads it from here.

Needs: numpy, and pypdf for figure.pdf (not with --chart-only).
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
    if "--chart-only" in sys.argv:
        make_chart_pdf(os.path.join(out, "chart.pdf"))
        print("wrote", os.path.join(out, "chart.pdf"))
        return
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "example.pdf")
    shutil.copyfile(src, os.path.join(out, "paper.pdf"))
    width, height = make_figure_pdf(src, os.path.join(out, "figure.pdf"))
    make_chart_pdf(os.path.join(out, "chart.pdf"))
    print("wrote", os.path.join(out, "paper.pdf"), ",", os.path.join(out, "figure.pdf"),
          f"(page {width:g} x {height:g} points, link to {LINK_URL} {LINK_BAND[0]}-{LINK_BAND[1]} points from the top)",
          "and", os.path.join(out, "chart.pdf"))


if __name__ == "__main__":
    main()
