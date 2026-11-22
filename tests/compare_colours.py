#!/usr/bin/env python3
"""Compare the reader's drawing of a page with poppler's drawing of it.

Usage: python tests/compare_colours.py SCREENSHOT PDF OUTDIR [--name NAME]

SCREENSHOT is a picture of the screen with the reader showing page 1 of PDF
(a page with a colour figure near its top) at page width. The script

1. finds the page in the screenshot (the white area on the dark viewer),
2. has poppler's pdftoppm draw the same page at the same width,
3. finds the figure on poppler's drawing (the block of dark pixels near the
   top of the page) and lines the two drawings up (a shift of a few pixels at
   most), and
4. measures, over the figure:
   - colour: the mean difference per channel, reader minus poppler, and the
     mean absolute difference per channel (0 to 255);
   - sharpness: the mean edge strength (size of the change from one pixel to
     the next) of the reader's drawing divided by poppler's. Below 1 is
     blurrier than poppler, above 1 is crisper.

It writes NAME.json (every number) and NAME.png (reader | poppler |
difference x4) into OUTDIR, prints the numbers, and fails when they are past
the limits below.

Needs: pdftoppm (poppler) on PATH or in POPPLER_BIN, Pillow and numpy.
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

# Limits. Recolouring pages (what the reader did before) moves the figure's
# channels by tens of levels and removes their colour; a drawing at a lower
# resolution than the screen's loses a large part of its edge strength.
MAX_MEAN_DIFF = 4.0       # per channel, |reader - poppler| of the means, 0-255
MAX_MEAN_ABS_DIFF = 12.0  # per channel, mean of |reader - poppler| per pixel
MIN_SHARPNESS = 0.85      # reader's edge strength / poppler's
MAX_SHIFT = 4             # pixels searched when lining up the two drawings


def load_rgb(path):
    """The screenshot as sRGB pixels (macOS tags screenshots with the display's profile)."""
    img = Image.open(path)
    icc = img.info.get("icc_profile")
    img = img.convert("RGB")
    if icc:
        from PIL import ImageCms
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        dst = ImageCms.createProfile("sRGB")
        img = ImageCms.profileToProfile(img, src, dst, outputMode="RGB")
    return np.asarray(img).astype(np.float64)


def find_page(shot):
    """Left, top, right (exclusive) of the white page area in the screenshot.

    The page's columns are the ones that are white in a good part of the
    screen. Its top is the start of the longest run of rows in which the
    page's left margin is white: a light title bar or task bar is a separate,
    shorter run, kept apart from the page by the viewer's dark edge."""
    bright = (shot > 235).all(axis=2)
    colfrac = bright.mean(axis=0)
    cols = np.where(colfrac > 0.3)[0]
    if cols.size == 0:
        sys.exit("No page found in the screenshot (no white area).")
    x0, x1 = int(cols.min()), int(cols.max()) + 1
    margin = bright[:, x0 + 3:x0 + 19].all(axis=1)
    best, start = (0, 0), None
    for y, white in enumerate(list(margin) + [False]):
        if white and start is None:
            start = y
        elif not white and start is not None:
            if y - start > best[1] - best[0]:
                best = (start, y)
            start = None
    if best[1] - best[0] < 50:
        sys.exit("No page found in the screenshot (no white page margin).")
    return x0, best[0], x1


def find_figure(ref):
    """Top, bottom, left, right of the figure: the block of dark pixels in the top half."""
    h, w, _ = ref.shape
    dark = ref.mean(axis=2) < 70
    rows = np.where(dark[: h // 2].mean(axis=1) > 0.25)[0]
    if rows.size == 0:
        sys.exit("No figure found near the top of the page.")
    t, b = int(rows.min()), int(rows.max()) + 1
    cols = np.where(dark[t:b].mean(axis=0) > 0.25)[0]
    l, r = int(cols.min()), int(cols.max()) + 1
    m = MAX_SHIFT + 2  # stay inside the figure whatever the shift
    return t + m, b - m, l + m, r - m


def pdftoppm():
    exe = shutil.which("pdftoppm")
    if not exe and os.environ.get("POPPLER_BIN"):
        for name in ("pdftoppm", "pdftoppm.exe"):
            c = os.path.join(os.environ["POPPLER_BIN"], name)
            if os.path.exists(c):
                exe = c
    if not exe:
        sys.exit("pdftoppm (poppler) not found.")
    return exe


def edge_strength(rgb):
    g = rgb @ np.array([0.2126, 0.7152, 0.0722])
    dx = np.abs(np.diff(g, axis=1))[:-1, :]
    dy = np.abs(np.diff(g, axis=0))[:, :-1]
    return float(np.sqrt(dx * dx + dy * dy).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("screenshot")
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--name", default="colours")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    shot = load_rgb(a.screenshot)
    x0, y0, x1 = find_page(shot)
    width = x1 - x0

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([pdftoppm(), "-f", "1", "-l", "1", "-scale-to-x", str(width),
                        "-scale-to-y", "-1", "-png", a.pdf, os.path.join(tmp, "ref")], check=True)
        out = [f for f in os.listdir(tmp) if f.endswith(".png")][0]
        ref = np.asarray(Image.open(os.path.join(tmp, out)).convert("RGB")).astype(np.float64)
    if ref.shape[1] != width:
        sys.exit(f"pdftoppm drew {ref.shape[1]} pixels wide, wanted {width}")

    t, b, l, r = find_figure(ref)
    if y0 + b + MAX_SHIFT > shot.shape[0]:
        sys.exit("The figure runs past the bottom of the screenshot.")
    poppler = ref[t:b, l:r]

    best = None
    for dy in range(-MAX_SHIFT, MAX_SHIFT + 1):
        for dx in range(-MAX_SHIFT, MAX_SHIFT + 1):
            reader = shot[y0 + t + dy:y0 + b + dy, x0 + l + dx:x0 + r + dx]
            mad = float(np.abs(reader - poppler).mean())
            if best is None or mad < best[0]:
                best = (mad, dx, dy)
    _, dx, dy = best
    reader = shot[y0 + t + dy:y0 + b + dy, x0 + l + dx:x0 + r + dx]

    diff = reader - poppler
    result = {
        "screenshot": os.path.basename(a.screenshot),
        "pdf": os.path.basename(a.pdf),
        "page_in_screenshot": {"left": x0, "top": y0, "width": width},
        "figure_on_page": {"top": t, "bottom": b, "left": l, "right": r},
        "shift_reader_vs_poppler": {"x": dx, "y": dy},
        "mean_rgb_reader": [round(v, 2) for v in reader.reshape(-1, 3).mean(0)],
        "mean_rgb_poppler": [round(v, 2) for v in poppler.reshape(-1, 3).mean(0)],
        "mean_difference_rgb": [round(v, 2) for v in diff.reshape(-1, 3).mean(0)],
        "mean_absolute_difference_rgb": [round(v, 2) for v in np.abs(diff).reshape(-1, 3).mean(0)],
        "colourfulness_reader": round(float((reader.max(2) - reader.min(2)).mean()), 2),
        "colourfulness_poppler": round(float((poppler.max(2) - poppler.min(2)).mean()), 2),
        "edge_strength_reader": round(edge_strength(reader), 3),
        "edge_strength_poppler": round(edge_strength(poppler), 3),
        "limits": {"max_mean_difference": MAX_MEAN_DIFF, "max_mean_absolute_difference": MAX_MEAN_ABS_DIFF,
                   "min_sharpness": MIN_SHARPNESS},
    }
    result["sharpness_reader_vs_poppler"] = round(result["edge_strength_reader"] / result["edge_strength_poppler"], 3)
    misses = []
    for c, v in zip("RGB", result["mean_difference_rgb"]):
        if abs(v) > MAX_MEAN_DIFF:
            misses.append(f"{c} channel mean differs by {v}")
    for c, v in zip("RGB", result["mean_absolute_difference_rgb"]):
        if v > MAX_MEAN_ABS_DIFF:
            misses.append(f"{c} channel pixels differ by {v} on average")
    if result["sharpness_reader_vs_poppler"] < MIN_SHARPNESS:
        misses.append(f"edges only {result['sharpness_reader_vs_poppler']} as strong as poppler's")
    result["misses"] = misses
    result["pass"] = not misses

    with open(os.path.join(a.outdir, a.name + ".json"), "w") as f:
        json.dump(result, f, indent=1)
    side = np.concatenate([reader, poppler, np.clip(np.abs(diff) * 4, 0, 255)], axis=1)
    Image.fromarray(side.astype(np.uint8)).save(os.path.join(a.outdir, a.name + ".png"))

    print(json.dumps(result, indent=1))
    if misses:
        print("MISS: " + "; ".join(misses))
        return 1
    print("Colours and sharpness match poppler's drawing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
