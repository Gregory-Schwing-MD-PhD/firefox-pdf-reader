#!/usr/bin/env python3
"""Check the reader on scanned letters, coloured boxes and labels on pictures.

Usage: python tests/check_mixed_page.py SCREENSHOT MIXED_PDF OUTDIR [--name NAME]

SCREENSHOT is a picture of the screen with the reader showing mixed.pdf (made
by tests/make_test_pdfs.py) at page width. The script finds the page in the
screenshot, has poppler's pdftoppm draw the same page at the same width (as
printed: white paper, black text), lines the two up on the picture drawn four
times, and checks, using the page's layout from make_test_pdfs.MIXED:

  a. the scanned page: in every band of letters drawn as black stencils on
     the picture of the paper (one large stencil, a group of small ones, one
     small one repeated, a Type3 font drawn with stencils and one drawn with
     shapes), the letters stay dark on the light paper, as poppler draws
     them: about as many dark pixels as poppler's, the paper as poppler's,
     and the letters at least 4.5 times darker than the paper (contrast);
  b. black text on a pale blue box: the box turns dark, keeping a blue tint,
     and the text turns white, readable on it (contrast 4.5 at least);
  c. black text on a yellow box: the box keeps its colour and the text stays
     black, readable on it; white text on a dark blue box: the box keeps its
     colour and the text stays white, readable on it;
  d. a white box with black text on a strong blue box: the blue keeps its
     colour; the white box and its text keep theirs, readable;
  e. a very pale blue box turns dark and keeps a blue tint;
  f. black text on the page turns white;
  g. a black label on a picture drawn four times over, and on a group of
     small pictures, stays black, and those pictures keep their colours.

It writes NAME.json (every number) and NAME.png (reader above poppler) into
OUTDIR, prints the numbers, and fails when a check misses.

Needs: pdftoppm (poppler) on PATH or in POPPLER_BIN, Pillow and numpy.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare_colours import find_any_page, load_rgb, poppler_page  # noqa: E402
from make_test_pdfs import MIXED, MIXED_PAGE  # noqa: E402

MAX_SHIFT = 6               # pixels searched when lining up the two drawings
DARK = 100.0                # a pixel this dark or darker (brightness 0-255) is ink
LIGHT = 160.0               # a pixel this light or lighter is light ink (or paper)
INK_RATIO = (0.5, 2.0)      # ink pixels, reader's / poppler's
MIN_CONTRAST = 4.5          # letters against what is under them (WCAG's level for text)
MAX_PAPER_DIFF = 12.0       # per channel, the paper's mean colour against poppler's
MAX_BOX_DIFF = 10.0         # per channel, a box that keeps its colour, against the PDF's colour
DARK_BOX = 60.0             # a box that turns dark: its median brightness at most this
MIN_TINT = 8.0              # and its blue channel at least this much above its red
MAX_PICTURE_DIFF = 12.0     # per channel, mean |reader - poppler| over a picture


def lum(rgb):
    return rgb @ np.array([0.2126, 0.7152, 0.0722])


def relative_luminance(rgb):
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(c @ np.array([0.2126, 0.7152, 0.0722]))


def contrast(a, b):
    la, lb = relative_luminance(a), relative_luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("screenshot")
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--name", default="mixed-page")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    shot = load_rgb(a.screenshot)
    x0, y0, x1, page_colour = find_any_page(shot)
    width = x1 - x0
    scale = width / MIXED_PAGE[0]                # pixels per point
    ref = poppler_page(a.pdf, width)
    H = shot.shape[0]

    def box(b, inset=0):
        """A box (x, top, width, height) in points from the page's top left,
        in pixels (left, top, right, bottom), shrunk by INSET pixels a side."""
        x, top, w, h = b
        return (int(round(x * scale)) + inset, int(round(top * scale)) + inset,
                int(round((x + w) * scale)) - inset, int(round((top + h) * scale)) - inset)

    # Line the two drawings up on the picture drawn four times (the seams
    # between its copies; its label left out), which both draw alike
    pl, pt, pr, pb = box(MIXED["repeated"]["box"], inset=MAX_SHIFT + 3)
    if y0 + pb + MAX_SHIFT > H:
        sys.exit("The page runs past the bottom of the screenshot.")
    ll, lt, lr, lb = box(MIXED["repeated"]["label"])
    use = np.ones((pb - pt, pr - pl), bool)
    use[max(0, lt - pt - 4):max(0, lb - pt + 4), max(0, ll - pl - 4):max(0, lr - pl + 4)] = False
    best = None
    for dy in range(-MAX_SHIFT, MAX_SHIFT + 1):
        for dx in range(-MAX_SHIFT, MAX_SHIFT + 1):
            r = shot[y0 + pt + dy:y0 + pb + dy, x0 + pl + dx:x0 + pr + dx]
            mad = float(np.abs(r - ref[pt:pb, pl:pr])[use].mean())
            if best is None or mad < best[0]:
                best = (mad, dx, dy)
    _, dx, dy = best

    def reader(b):
        l, t, r, bt = b
        return shot[y0 + t + dy:min(y0 + bt + dy, H), x0 + l + dx:x0 + r + dx]

    def poppler(b):
        l, t, r, bt = b
        rows = min(bt, H - y0 - dy) - t
        return ref[t:t + rows, l:r]

    result = {"screenshot": os.path.basename(a.screenshot), "pdf": os.path.basename(a.pdf),
              "page_in_screenshot": {"left": x0, "top": y0, "width": width, "page_colour": page_colour},
              "shift_reader_vs_poppler": {"x": dx, "y": dy}}
    misses = []
    if page_colour != "black":
        misses.append(f"the page is {page_colour}, not black")

    def ink(b, dark_ink):
        """Ink and what is under it in a box: the share of ink pixels in the
        reader's drawing and poppler's, the mean colour of the reader's ink
        (its darkest or lightest 2%) and of the rest (its median), and
        their contrast. dark_ink: the ink is dark (reader) / the letters are
        dark in poppler's drawing."""
        r, p = reader(b), poppler(b)
        lr, lp = lum(r).ravel(), lum(p).ravel()
        rr = r.reshape(-1, 3)
        order = np.argsort(lr)
        part = max(1, lr.size // 50)
        core = rr[order[:part]] if dark_ink else rr[order[-part:]]
        ground = np.median(rr, axis=0)
        share_r = float((lr <= DARK).mean() if dark_ink else (lr >= LIGHT).mean())
        return {"ink_share_reader": round(share_r, 4),
                "ink_share_poppler": round(float((lp <= DARK).mean()), 4),
                "ink_reader": [round(float(v), 1) for v in core.mean(0)],
                "ground_reader": [round(float(v), 1) for v in ground],
                "contrast": round(contrast(core.mean(0), ground), 2)}

    def ink_ok(e, label, what):
        ratio = e["ink_share_reader"] / max(e["ink_share_poppler"], 1e-6)
        e["ink_reader_vs_poppler"] = round(ratio, 2)
        if not INK_RATIO[0] <= ratio <= INK_RATIO[1]:
            misses.append(f"{label}: {what} ({e['ink_share_reader']:.3f} of the pixels, poppler "
                          f"{e['ink_share_poppler']:.3f})")
        if e["contrast"] < MIN_CONTRAST:
            misses.append(f"{label}: the letters are hard to read, contrast {e['contrast']} "
                          f"(ink {e['ink_reader']} on {e['ground_reader']})")

    # a. The scanned page: dark letters on the light paper
    paper = MIXED["paper"]
    result["a_scan"] = []
    for label, b in MIXED["scan_bands"]:
        e = ink(box(b), dark_ink=True)
        e["band"] = label
        r, p = reader(box(b)).reshape(-1, 3), poppler(box(b)).reshape(-1, 3)
        light_r, light_p = lum(r) >= LIGHT, lum(p) >= LIGHT
        e["paper_reader"] = [round(float(v), 1) for v in (r[light_r].mean(0) if light_r.any() else np.zeros(3))]
        e["paper_poppler"] = [round(float(v), 1) for v in (p[light_p].mean(0) if light_p.any() else np.zeros(3))]
        result["a_scan"].append(e)
        ink_ok(e, f"a ({label})", "the letters are not dark on the paper as poppler draws them")
        if np.abs(np.array(e["paper_reader"]) - np.array(e["paper_poppler"])).max() > MAX_PAPER_DIFF:
            misses.append(f"a ({label}): the paper is {e['paper_reader']}, poppler {e['paper_poppler']}")
    result["a_scan_paper_pdf"] = list(paper["rgb"])

    # b, c. Boxes with text
    result["b_c_boxes"] = []
    for label, b, rgb, text_grey, text in MIXED["boxes"]:
        inner = box(b, inset=3)
        median = np.median(reader(inner).reshape(-1, 3), axis=0)
        pale = label == "pale blue box"
        e = ink(inner, dark_ink=not pale and text_grey == 0)
        e.update({"box": label, "text": text, "pdf_colour": list(rgb),
                  "box_reader": [round(float(v), 1) for v in median]})
        result["b_c_boxes"].append(e)
        if pale:
            if lum(median) > DARK_BOX or median[2] - median[0] < MIN_TINT:
                misses.append(f"b: the pale blue box is not dark blue ({e['box_reader']})")
            ink_ok(e, "b (text on the pale blue box)", "the black text is not white")
        else:
            if np.abs(median - np.array(rgb)).max() > MAX_BOX_DIFF:
                misses.append(f"c: the {label} changed colour ({e['box_reader']}, PDF {list(rgb)})")
            if text_grey == 0:
                ink_ok(e, f"c (text on the {label})", "the black text is not black")
            else:
                # white text: poppler's text is light too, so count light pixels in both
                p = lum(poppler(inner)).ravel()
                e["ink_share_poppler"] = round(float((p >= LIGHT).mean()), 4)
                ink_ok(e, f"c (text on the {label})", "the white text is not white")

    # d. A white box with black text on a strong blue box
    po = MIXED["poster"]
    bx, bt, bw, bh = po["blue"]
    wx, wt, ww, wh = po["white"]
    blue_part = box((bx, wt + wh + 4, bw, bt + bh - wt - wh - 8), inset=3)
    blue = np.median(reader(blue_part).reshape(-1, 3), axis=0)
    e = ink(box(po["white"], inset=3), dark_ink=True)
    e.update({"blue_reader": [round(float(v), 1) for v in blue], "blue_pdf": list(po["blue_rgb"])})
    result["d_white_box_on_blue"] = e
    if np.abs(blue - np.array(po["blue_rgb"])).max() > MAX_BOX_DIFF:
        misses.append(f"d: the strong blue box changed colour ({e['blue_reader']})")
    if lum(np.array(e["ground_reader"])) < 230:
        misses.append(f"d: the white box on the blue one is not white ({e['ground_reader']})")
    ink_ok(e, "d (text on the white box)", "the black text is not black")

    # e. A very pale blue box: dark, with a blue tint
    pt_ = MIXED["pale_tint"]
    median = np.median(reader(box(pt_["box"], inset=3)).reshape(-1, 3), axis=0)
    result["e_pale_tint"] = {"pdf": list(pt_["rgb"]), "reader": [round(float(v), 1) for v in median]}
    if lum(median) > DARK_BOX or median[2] - median[0] < MIN_TINT:
        misses.append(f"e: the very pale blue box is not a dark blue ({result['e_pale_tint']['reader']})")

    # f. Black text on the page: white
    tx = MIXED["page_text"]
    e = ink(box(tx["box"]), dark_ink=False)
    result["f_page_text"] = e
    ink_ok(e, "f (black text on the page)", "the black text is not white")
    if np.array(e["ink_reader"]).min() < 200:
        misses.append(f"f: the text on the page is not white ({e['ink_reader']})")

    # g. Labels on pictures drawn many times over
    result["g_labels"] = []
    for key, what in (("repeated", "a picture drawn four times"), ("group", "a group of small pictures")):
        e = ink(box(MIXED[key]["label"]), dark_ink=True)
        e["picture"] = what
        # The pictures themselves, away from the label: as poppler draws them
        x, top, w, h = MIXED[key]["box"]
        lx, lt, lw, lh = MIXED[key]["label"]
        under = box((x, lt + lh + 6, w, top + h - lt - lh - 6), inset=MAX_SHIFT)
        diff = np.abs(reader(under) - poppler(under)).reshape(-1, 3).mean(0)
        e["picture_mean_absolute_difference_rgb"] = [round(float(v), 2) for v in diff]
        result["g_labels"].append(e)
        ink_ok(e, f"g (label on {what})", "the black label is not black")
        if (diff > MAX_PICTURE_DIFF).any():
            misses.append(f"g: {what} differs from poppler's drawing ({e['picture_mean_absolute_difference_rgb']})")

    result["misses"] = misses
    result["pass"] = not misses
    with open(os.path.join(a.outdir, a.name + ".json"), "w") as f:
        json.dump(result, f, indent=1)
    rows = min(int(MIXED_PAGE[1] * scale), H - y0 - dy, ref.shape[0])
    top_r = shot[y0 + dy:y0 + dy + rows, x0 + dx:x0 + dx + width]
    w = min(top_r.shape[1], ref.shape[1])
    Image.fromarray(np.concatenate([top_r[:, :w], ref[:rows, :w]], axis=0).astype(np.uint8)).save(
        os.path.join(a.outdir, a.name + ".png"))

    print(json.dumps(result, indent=1))
    if misses:
        print("MISS: " + "; ".join(misses))
        return 1
    print("Scanned letters dark on their paper, boxes and their text readable, labels on pictures in their colours.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
