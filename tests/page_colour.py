#!/usr/bin/env python3
"""Check the colour of the PDF page on the screen.

Usage: python tests/page_colour.py SCREENSHOT black|white

Finds the page in the screenshot the way tests/compare_colours.py does and
fails unless it is the colour given: black for a PDF in the reader's own
viewer, white for a PDF in Firefox's own viewer (a PDF on the web).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare_colours import find_any_page, load_rgb  # noqa: E402


def main():
    shot, want = sys.argv[1], sys.argv[2]
    left, top, right, colour = find_any_page(load_rgb(shot))
    print(f"page: {colour}, {right - left} pixels wide, from ({left}, {top})")
    if colour != want:
        print(f"MISS: the page is {colour}, not {want}")
        return 1
    print(f"The page is {want}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
