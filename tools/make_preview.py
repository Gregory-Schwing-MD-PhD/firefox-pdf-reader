#!/usr/bin/env python3
"""Build docs/preview.svg: the README animation of the reader.

Opens the example paper in the reader's own viewer (viewer/, black pages
with white text, pictures in their own colours), in Firefox with the
reader's own profile files (user.js + chrome/*.css), at a 1440x900 viewport, captures the viewer at
successive scroll positions from the top of page START_PAGE (the page with
the paper's colour figure), stitches them into one tall image, and writes an
SVG that shows a 1440x900 window onto it (rendered at exactly 640x400, the
same 16:10 shape, nothing cropped), scrolling the way a mouse wheel does.

An SVG plays by itself with no player controls in a GitHub README (GitHub
adds a pause button to animated GIFs).

With --still, it also saves a picture of the whole of page START_PAGE, as
the reader draws it, for the README.

Usage: python3 tools/make_preview.py PDF OUT.svg [--frame OUT.png] [--still OUT.png]
Needs: Firefox, geckodriver, selenium, pillow.
"""
import argparse, base64, io, os, shutil, sys, tempfile, time, urllib.parse
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

W, H = 1440, 900                 # viewport captured (16:10)
OUT_W, OUT_H = 640, 400          # size shown in the README (exactly W/H scaled)
BURST = 430                      # pixels per wheel burst
BURSTS = 5
HOLD_START, MOVE, PAUSE, HOLD_END = 2.4, 0.55, 1.7, 2.2   # seconds
START_PAGE = 5                   # the page with the colour figure

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("out")
    ap.add_argument("--frame")
    ap.add_argument("--still")
    a = ap.parse_args()

    prof = tempfile.mkdtemp()
    os.makedirs(os.path.join(prof, "chrome"))
    shutil.copy(os.path.join(repo, "profile", "user.js"), prof)
    for css in ("userChrome.css", "userContent.css"):
        shutil.copy(os.path.join(repo, "profile", "chrome", css), os.path.join(prof, "chrome"))
    # Overlay scrollbars that take no space, as on Windows and macOS
    # (the capture machine is Linux, where classic scrollbars take 12px)
    with open(os.path.join(prof, "user.js"), "a") as f:
        f.write('\nuser_pref("widget.gtk.overlay-scrollbars.enabled", true);\n'
                'user_pref("ui.useOverlayScrollbars", 1);\n')

    o = Options()
    o.add_argument("-headless")
    o.add_argument("-profile")
    o.add_argument(prof)
    d = webdriver.Firefox(options=o)
    try:
        # Size the window so the page area is exactly W x H
        d.set_window_size(W, H)
        # The reader's viewer with the PDF's address after "?file=", as the launchers open it
        viewer = Path(repo, "viewer", "web", "viewer.html").resolve().as_uri()
        d.get(viewer + "?file=" + urllib.parse.quote(Path(a.pdf).resolve().as_uri(), safe=""))
        time.sleep(6)
        iw, ih = d.execute_script("return [innerWidth, innerHeight]")
        d.set_window_size(W + (W - iw), H + (H - ih))
        time.sleep(3)
        iw, ih = d.execute_script("return [innerWidth, innerHeight]")
        assert (iw, ih) == (W, H), f"viewport is {iw}x{ih}, wanted {W}x{H}"

        # Overlay scrollbars are hidden while not scrolling on Windows and macOS;
        # keep them out of the captures.
        d.execute_script("""
          const s = document.createElement('style');
          s.textContent = '#viewerContainer { scrollbar-width: none !important; }';
          document.head.append(s);
          // re-fit "page width" now that no scrollbar takes space
          window.dispatchEvent(new Event('resize'));""")
        time.sleep(3)
        gaps = d.execute_script("""
          const r = document.querySelector('.page').getBoundingClientRect();
          return [Math.round(r.left), Math.round(innerWidth - r.right)];""")
        print(f"page margins left/right: {gaps}", flush=True)
        assert abs(gaps[0] - gaps[1]) <= 2, f"page not centred: {gaps}"

        # Start a little above the top of START_PAGE
        start = d.execute_script("""
          const v = document.getElementById('viewerContainer');
          const p = document.querySelector('.page[data-page-number="' + arguments[0] + '"]');
          return Math.max(0, Math.round(p.getBoundingClientRect().top - v.getBoundingClientRect().top + v.scrollTop) - 12);""",
                                 START_PAGE)
        print(f"page {START_PAGE} starts at scrollTop {start + 12}", flush=True)
        total = BURST * BURSTS
        positions = list(range(0, total, H)) + [total]
        strip = Image.new("RGB", (W, H + total))
        for y in positions:
            y_abs = start + y
            d.execute_script("document.getElementById('viewerContainer').scrollTop = arguments[0]", y_abs)
            # wait for pages in view to finish drawing
            for _ in range(40):
                time.sleep(0.5)
                busy = d.execute_script("""
                  const v = document.getElementById('viewerContainer').getBoundingClientRect();
                  return [...document.querySelectorAll('.page')].some(p => {
                    const r = p.getBoundingClientRect();
                    return r.bottom > v.top && r.top < v.bottom && !p.querySelector('canvas');
                  }) || !!document.querySelector('.page .loadingIcon:not(.notVisible)');""")
                if not busy:
                    break
            time.sleep(1.5)
            actual = d.execute_script("return document.getElementById('viewerContainer').scrollTop")
            assert round(actual) == y_abs, f"scrolled to {actual}, wanted {y_abs}"
            shot = Image.open(io.BytesIO(d.get_screenshot_as_png())).convert("RGB")
            assert shot.size == (W, H), f"screenshot is {shot.size}"
            strip.paste(shot, (0, y))
            print(f"captured scrollTop={y_abs}", flush=True)

        if a.still:
            # The whole page, at the size of a tall window
            d.set_window_size(1100, 1500)
            time.sleep(2)
            d.execute_script("PDFViewerApplication.pdfViewer.currentScaleValue = 'page-fit';"
                             "PDFViewerApplication.page = arguments[0];", START_PAGE)
            for _ in range(40):
                time.sleep(0.5)
                if d.execute_script("""
                  const p = document.querySelector('.page[data-page-number="' + arguments[0] + '"]');
                  return !!p.querySelector('canvas') && !p.querySelector('.loadingIcon:not(.notVisible)');""",
                                    START_PAGE):
                    break
            time.sleep(2)
            box = d.execute_script("""
              const r = document.querySelector('.page[data-page-number="' + arguments[0] + '"]').getBoundingClientRect();
              return [r.left, r.top, r.right, r.bottom].map(Math.round);""", START_PAGE)
            shot = Image.open(io.BytesIO(d.get_screenshot_as_png())).convert("RGB")
            m = 12   # a little of the dark viewer around the page
            page = shot.crop((max(0, box[0] - m), max(0, box[1] - m),
                              min(shot.width, box[2] + m), min(shot.height, box[3] + m)))
            page.save(a.still, optimize=True)
            print(f"wrote {a.still}: page {START_PAGE}, {page.width}x{page.height}", flush=True)
    finally:
        d.quit()

    if a.frame:
        strip.crop((0, 0, W, H)).save(a.frame)

    buf = io.BytesIO()
    strip.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    data = base64.b64encode(buf.getvalue()).decode()

    # Timeline: hold, then BURSTS eased moves (like smooth wheel scrolling), hold,
    # then fade to the start and loop.
    times, values, splines = [0.0], [0], []
    t = HOLD_START
    times.append(t); values.append(0); splines.append("0 0 1 1")
    for i in range(1, BURSTS + 1):
        t += MOVE
        times.append(t); values.append(-BURST * i); splines.append("0.25 0.6 0.35 1")   # ease-out
        t += PAUSE if i < BURSTS else HOLD_END
        times.append(t); values.append(-BURST * i); splines.append("0 0 1 1")
    dur = t + 0.6
    times.append(dur); values.append(-BURST * BURSTS); splines.append("0 0 1 1")
    key_times = ";".join(f"{x / dur:.4f}" for x in times)
    key_values = ";".join(f"0 {v}" for v in values)
    fade_start = (dur - 0.6) / dur

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{OUT_W}" height="{OUT_H}" viewBox="0 0 {W} {H}">
<title>Firefox PDF Reader: the example paper's colour figure and text, scrolling</title>
<clipPath id="screen"><rect width="{W}" height="{H}"/></clipPath>
<g clip-path="url(#screen)">
<rect width="{W}" height="{H}" fill="#1c1b1f"/>
<image width="{W}" height="{H + total}" preserveAspectRatio="none" xlink:href="data:image/jpeg;base64,{data}">
<animateTransform attributeName="transform" type="translate" dur="{dur:.2f}s" repeatCount="indefinite" calcMode="spline" keyTimes="{key_times}" values="{key_values}" keySplines="{';'.join(splines)}"/>
</image>
<rect width="{W}" height="{H}" fill="#000" opacity="0">
<animate attributeName="opacity" dur="{dur:.2f}s" repeatCount="indefinite" keyTimes="0;{fade_start:.4f};1" values="0;0;1"/>
</rect>
</g>
</svg>
'''
    with open(a.out, "w") as f:
        f.write(svg)
    print(f"wrote {a.out}: {len(svg) // 1024} KB, {OUT_W}x{OUT_H}, loop {dur:.1f}s")


if __name__ == "__main__":
    sys.exit(main())
