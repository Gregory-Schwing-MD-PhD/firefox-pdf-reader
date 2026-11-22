#!/usr/bin/env python3
"""Check that the find bar opened: the top right of the page changed.

Usage: python tests/find_bar_shown.py BEFORE.png AFTER.png DARK_PAGE.json

BEFORE and AFTER are screenshots of the same window before and after Ctrl+F
(Cmd+F) and typing a word; DARK_PAGE.json is what tests/check_dark_page.py
wrote for BEFORE (where the page is on the screen). The reader's find bar
opens at the top right of the window, over the black page, so the band at
the top right of the page must have changed, and hold more than black.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare_colours import load_rgb  # noqa: E402


def main():
    before, after = load_rgb(sys.argv[1]), load_rgb(sys.argv[2])
    p = json.load(open(sys.argv[3]))["page_in_screenshot"]
    right = p["left"] + p["width"]
    band = (slice(p["top"], p["top"] + 48), slice(max(p["left"], right - 520), right))
    change = float(np.abs(after[band] - before[band]).mean())
    spread = float(after[band].std())
    print(f"top right of the page: mean change {change:.1f}, spread of brightness {spread:.1f}")
    if change < 4 or spread < 10:
        print("MISS: no find bar at the top right")
        return 1
    print("The find bar is open.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
