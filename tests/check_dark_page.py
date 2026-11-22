#!/usr/bin/env python3
"""Check the reader's black page, white text and pictures in their own colours.

Usage: python tests/check_dark_page.py SCREENSHOT CHART_PDF OUTDIR [--name NAME]

SCREENSHOT is a picture of the screen with the reader showing the top of
chart.pdf (made by tests/make_test_pdfs.py) at page width. The script finds
the page in the screenshot, has poppler's pdftoppm draw the same page at the
same width (poppler draws it as printed: white paper, black text), lines the
two up on the picture, and checks, using the page's layout from
make_test_pdfs.CHART:

  a. the page is black: the empty parts of the page (both margins and the gap
     between the picture and the chart) are black;
  b. the text is white: in every line of text, the strokes of the letters are
     white (not grey, not coloured) and there are about as many of them as
     poppler draws in black;
  c. the greyscale picture is as the PDF has it, not inverted: it matches
     poppler's drawing (mean and mean absolute difference per channel, and it
     goes light where poppler's goes light), and its step wedge runs from
     black on the left to white on the right; and the labels drawn on it (a
     white one, a black one) keep their colours, as poppler draws them;
  d. the chart keeps its colours: each bar has its colour from the PDF, the
     black axes are white, and the light grey grid lines are dark grey.

It writes NAME.json (every number) and NAME.png (reader above poppler, the
top of the page) into OUTDIR, prints the numbers, and fails when a check
misses.

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
from make_test_pdfs import CHART, PAGE  # noqa: E402

MAX_SHIFT = 6              # pixels searched when lining up the two drawings
BLACK_MEAN = 4.0           # (a) the empty page: mean of its channels at most this
BLACK_MOST = 16.0          #     and 99.9% of its pixels' brightest channel at most this
WHITE_CORE = 235.0         # (b) the brightest fifth of the letters' pixels: at least this bright
MAX_TEXT_TINT = 20.0       #     and their channels no further apart than this (white, not coloured;
                           #     the edges of letters may be tinted by the system's subpixel smoothing)
INK_RATIO = (0.5, 2.0)     #     letters' pixels, reader's / poppler's
MAX_MEAN_DIFF = 4.0        # (c) per channel, |reader - poppler| of the means, 0-255
MAX_MEAN_ABS_DIFF = 12.0   #     per channel, mean of |reader - poppler| per pixel
MIN_CORRELATION = 0.95     #     brightness, reader against poppler (an inverted picture gives about -1)
MAX_LABEL_DIFF = 35.0      #     a label on the picture: mean |reader - poppler| brightness over its box
MAX_BAR_DIFF = 8.0         # (d) per channel, a bar's mean colour against the PDF's colour
AXIS_WHITE = 200.0         #     the axes, where poppler draws them black: at least this bright
AXIS_BESIDE = 60.0         #     and the page beside them at most this
GRID_DARK = (15.0, 120.0)  #     the grid lines: dark grey, between these


def lum(rgb):
    return rgb @ np.array([0.2126, 0.7152, 0.0722])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("screenshot")
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--name", default="dark-page")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    shot = load_rgb(a.screenshot)
    x0, y0, x1, page_colour = find_any_page(shot)
    width = x1 - x0
    scale = width / PAGE[0]                      # pixels per point
    ref = poppler_page(a.pdf, width)
    H = shot.shape[0]

    def box(x, top, w, h, inset=0):
        """A box given in points from the page's top left, in screen pixels
        (left, top, right, bottom), shrunk by INSET pixels on every side."""
        return (int(round(x * scale)) + inset, int(round(top * scale)) + inset,
                int(round((x + w) * scale)) - inset, int(round((top + h) * scale)) - inset)

    # Line the two drawings up on the picture, which both draw alike
    pic = CHART["picture"]
    pl, pt, pr, pb = box(pic["x"], pic["top"], pic["width"], pic["height"], inset=MAX_SHIFT + 3)
    if y0 + pb + MAX_SHIFT > H:
        sys.exit("The picture runs past the bottom of the screenshot.")
    best = None
    for dy in range(-MAX_SHIFT, MAX_SHIFT + 1):
        for dx in range(-MAX_SHIFT, MAX_SHIFT + 1):
            r = shot[y0 + pt + dy:y0 + pb + dy, x0 + pl + dx:x0 + pr + dx]
            mad = float(np.abs(lum(r) - lum(ref[pt:pb, pl:pr])).mean())
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

    # a. The empty parts of the page are black
    ch = CHART["chart"]
    empty = [box(18, 130, 44, 200, 2),                                          # left margin
             box(pic["x"] + pic["width"] + 6, 130,
                 ch["x"] - 12 - pic["x"] - pic["width"] - 6, 140, 2),            # between picture and chart
             box(554, 130, 40, 200, 2)]                                         # right margin
    px = np.concatenate([reader(b).reshape(-1, 3) for b in empty])
    a_mean = float(px.mean())
    a_most = float(np.percentile(px.max(1), 99.9))
    result["a_page"] = {"mean": round(a_mean, 2), "brightest_channel_99_9_percent": round(a_most, 2),
                        "limits": {"mean": BLACK_MEAN, "brightest_99_9": BLACK_MOST}}
    if a_mean > BLACK_MEAN or a_most > BLACK_MOST:
        misses.append(f"a: the empty page is not black (mean {a_mean:.1f}, brightest {a_most:.1f})")

    # b. Every line of text is white
    size = CHART["text_size"]
    lines = [(CHART["heading"]["top"], CHART["heading"]["size"], "heading")]
    lines += [(top, size, text[:40]) for top, _, text in CHART["lines"]]
    result["b_text"] = []
    for top, sz, label in lines:
        b = box(70, top - 2, 472, sz + 6)
        r, p = lum(reader(b)), lum(poppler(b))
        ink_r = r > 64                     # letters on the reader's black page
        ink_p = p < 191                    # letters on poppler's white page
        if ink_r.any():
            order = np.argsort(r[ink_r])[-max(1, int(ink_r.sum()) // 5):]   # the brightest fifth
            core = r[ink_r][order]
            rgb = reader(b)[ink_r][order]
        else:
            core, rgb = np.array([0.0]), np.zeros((1, 3))
        tint = float((rgb.max(1) - rgb.min(1)).mean())
        ratio = float(ink_r.mean() / max(ink_p.mean(), 1e-6))
        entry = {"line": label, "letters_core_brightness": round(float(core.mean()), 1),
                 "letters_tint": round(tint, 1), "letters_reader_vs_poppler": round(ratio, 2)}
        result["b_text"].append(entry)
        if core.mean() < WHITE_CORE or tint > MAX_TEXT_TINT or not INK_RATIO[0] <= ratio <= INK_RATIO[1]:
            misses.append(f"b: text not white in '{label}' ({entry})")

    # c. The greyscale picture as the PDF has it, not inverted
    b = box(pic["x"], pic["top"], pic["width"], pic["height"], inset=3)
    r, p = reader(b), poppler(b)
    diff = r - p
    corr = float(np.corrcoef(lum(r).ravel(), lum(p).ravel())[0, 1])
    wedge = []
    wt = pic["top"] + pic["height"] * 0.84
    for i in range(8):
        sb = box(pic["x"] + pic["width"] * i / 8, wt, pic["width"] / 8, pic["height"] * 0.12, inset=3)
        wedge.append((round(float(lum(reader(sb)).mean()), 1), round(float(lum(poppler(sb)).mean()), 1)))
    result["c_picture"] = {
        "mean_difference_rgb": [round(float(v), 2) for v in diff.reshape(-1, 3).mean(0)],
        "mean_absolute_difference_rgb": [round(float(v), 2) for v in np.abs(diff).reshape(-1, 3).mean(0)],
        "brightness_correlation_with_poppler": round(corr, 4),
        "step_wedge_reader_poppler": wedge,
        "limits": {"mean_difference": MAX_MEAN_DIFF, "mean_absolute_difference": MAX_MEAN_ABS_DIFF,
                   "correlation": MIN_CORRELATION}}
    if (np.abs(diff.reshape(-1, 3).mean(0)) > MAX_MEAN_DIFF).any() or \
            (np.abs(diff).reshape(-1, 3).mean(0) > MAX_MEAN_ABS_DIFF).any() or corr < MIN_CORRELATION:
        misses.append(f"c: the picture differs from poppler's ({result['c_picture']})")
    result["c_picture"]["labels_on_picture"] = []
    for x, top, size, grey, text in CHART["picture_labels"]:
        lb = box(x - 1, top - 1, size * 0.8, size + 2)
        d = float(np.abs(lum(reader(lb)) - lum(poppler(lb))).mean())
        result["c_picture"]["labels_on_picture"].append({"label": text, "grey": grey, "mean_abs_difference": round(d, 1)})
        if d > MAX_LABEL_DIFF:
            misses.append(f"c: the {'white' if grey else 'black'} label '{text}' on the picture changed colour ({d:.0f})")
    steps = [w[0] for w in wedge]
    if not (all(s1 < s2 for s1, s2 in zip(steps, steps[1:])) and steps[0] < 25 and steps[-1] > 230):
        misses.append(f"c: the step wedge does not run from black to white, left to right: {steps}")

    # d. The chart: bars in their colours, white axes, dark grey grid lines
    cx, ctop, cw, chh = ch["x"], ch["top"], ch["width"], ch["height"]
    result["d_chart"] = {"bars": []}
    for left, height, colour in ch["bars"]:
        bb = box(cx + left * cw, ctop + chh * (1 - height), ch["bar_width"] * cw, chh * height, inset=4)
        mean = reader(bb).reshape(-1, 3).mean(0)
        pmean = poppler(bb).reshape(-1, 3).mean(0)
        entry = {"pdf": list(colour), "reader": [round(float(v), 1) for v in mean],
                 "poppler": [round(float(v), 1) for v in pmean]}
        result["d_chart"]["bars"].append(entry)
        if (np.abs(mean - np.array(colour)) > MAX_BAR_DIFF).any():
            misses.append(f"d: a bar is not its colour: {entry}")

    aw = ch["axis_width"]
    # The left axis: columns around it, over the middle of its height
    va = box(cx - 3, ctop + chh * 0.1, 6, chh * 0.8)
    vr, vp = lum(reader(va)).mean(0), lum(poppler(va)).mean(0)
    # The bottom axis: rows around it, under the middle of the chart
    ha = box(cx + cw * 0.2, ctop + chh - 3, cw * 0.7, 6)
    hr, hp = lum(reader(ha)).mean(1), lum(poppler(ha)).mean(1)
    # A grid line (the one at half height), between the bars
    g = ch["grid"][1]
    gb = box(cx + cw * (ch["bars"][0][0] + ch["bar_width"]) + 3, ctop + chh * (1 - g) - 2,
             cw * (ch["bars"][1][0] - ch["bars"][0][0] - ch["bar_width"]) - 6, 4)
    gr, gp = lum(reader(gb)).mean(1), lum(poppler(gb)).mean(1)

    def on_line(r, p):
        """(on, beside): the reader's brightness on the line poppler draws
        there (the rows or columns poppler draws darker than mid-grey, or
        else its darkest one, allowing one pixel either way), and beside it
        (two pixels and more away, on both sides)."""
        dark = np.where(p < 128)[0]
        i0, i1 = (int(dark.min()), int(dark.max())) if dark.size else (int(np.argmin(p)),) * 2
        beside = np.concatenate([r[:max(0, i0 - 2)], r[i1 + 3:]])
        return float(r[max(0, i0 - 1):i1 + 2].max()), float(beside.mean()) if beside.size else 0.0
    (v_line, v_beside), (h_line, h_beside), (g_line, _) = on_line(vr, vp), on_line(hr, hp), on_line(gr, gp)
    result["d_chart"].update({
        "left_axis_reader": round(v_line, 1), "left_axis_poppler": round(float(vp.min()), 1),
        "beside_left_axis_reader": round(v_beside, 1),
        "bottom_axis_reader": round(h_line, 1), "bottom_axis_poppler": round(float(hp.min()), 1),
        "beside_bottom_axis_reader": round(h_beside, 1),
        "grid_line_reader": round(g_line, 1), "grid_line_poppler": round(float(gp.min()), 1),
        "axis_width_points": aw,
        "limits": {"bar": MAX_BAR_DIFF, "axis_white": AXIS_WHITE, "grid_dark_grey": GRID_DARK}})
    if v_line < AXIS_WHITE or h_line < AXIS_WHITE or max(v_beside, h_beside) > AXIS_BESIDE:
        misses.append(f"d: the axes are not white on black (left {v_line:.0f} on {v_beside:.0f}, "
                      f"bottom {h_line:.0f} on {h_beside:.0f})")
    if not GRID_DARK[0] <= g_line <= GRID_DARK[1]:
        misses.append(f"d: the light grey grid line is not dark grey ({g_line:.0f})")

    result["misses"] = misses
    result["pass"] = not misses
    with open(os.path.join(a.outdir, a.name + ".json"), "w") as f:
        json.dump(result, f, indent=1)
    # The top of the page, reader above poppler
    rows = min(int(340 * scale), H - y0 - dy, ref.shape[0])
    top_r = shot[y0 + dy:y0 + dy + rows, x0 + dx:x0 + dx + width]
    w = min(top_r.shape[1], ref.shape[1])
    Image.fromarray(np.concatenate([top_r[:, :w], ref[:rows, :w]], axis=0).astype(np.uint8)).save(
        os.path.join(a.outdir, a.name + ".png"))

    print(json.dumps(result, indent=1))
    if misses:
        print("MISS: " + "; ".join(misses))
        return 1
    print("Black page, white text, the picture and the chart in their own colours.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
