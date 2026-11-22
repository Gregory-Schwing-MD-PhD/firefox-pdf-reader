#!/usr/bin/env python3
"""Make the two PDFs the tests open, from docs/example.pdf.

Usage: python tests/make_test_pdfs.py OUTDIR

  OUTDIR/paper.pdf   the whole example paper
  OUTDIR/figure.pdf  its page 5 alone: a page with a colour figure (CT
                     pictures with coloured vertebrae) at the top, used to
                     compare the reader's colours with poppler's drawing.
                     It also gets an invisible web link (to example.com) over
                     the empty band at the top of the page, LINK_BAND points
                     down from the top edge, for the test that clicks a link.

Needs: pypdf.
"""
import os
import shutil
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link

FIGURE_PAGE = 5
LINK_URL = "https://example.com/"
LINK_BAND = (20, 50)   # points from the top of the page


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "example.pdf")
    shutil.copyfile(src, os.path.join(out, "paper.pdf"))

    w = PdfWriter()
    page = w.add_page(PdfReader(src).pages[FIGURE_PAGE - 1])
    width, height = float(page.mediabox.width), float(page.mediabox.height)
    top, bottom = height - LINK_BAND[0], height - LINK_BAND[1]
    w.add_annotation(page_number=0, annotation=Link(rect=(72, bottom, width - 72, top),
                                                    url=LINK_URL, border=[0, 0, 0]))
    with open(os.path.join(out, "figure.pdf"), "wb") as f:
        w.write(f)
    print("wrote", os.path.join(out, "paper.pdf"), "and", os.path.join(out, "figure.pdf"),
          f"(page {width:g} x {height:g} points, link to {LINK_URL} {LINK_BAND[0]}-{LINK_BAND[1]} points from the top)")


if __name__ == "__main__":
    main()
