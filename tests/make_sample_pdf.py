#!/usr/bin/env python3
"""Write a small multi-page PDF for the CI tests (standard library only).

Usage: python3 tests/make_sample_pdf.py OUT.pdf
"""
import sys

PAGES = 4
LINES = [
    "Firefox PDF Reader - CI test document",
    "",
    "If the reader is set up correctly this page is shown:",
    "  - full screen, with no browser tabs or address bar",
    "  - with no PDF toolbar or sidebar",
    "  - with light grey text on a near-black page",
    "  - fit to the page width, scrolling vertically",
]


def page_stream(n):
    parts = ["BT", "/F1 22 Tf", "28 TL", "60 740 Td"]
    for line in LINES + ["", f"Page {n} of {PAGES}"]:
        text = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        parts.append(f"({text}) Tj T*")
    parts.append("ET")
    return "\n".join(parts).encode("latin-1")


def main(out):
    objects = []  # object bodies, numbered from 1

    def add(body):
        objects.append(body)
        return len(objects)

    catalog = add(None)
    pages = add(None)
    font = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    kids = []
    for n in range(1, PAGES + 1):
        stream = page_stream(n)
        content = add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        kids.append(add(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>" % (pages, font, content)))
    objects[catalog - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages
    objects[pages - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
        b" ".join(b"%d 0 R" % k for k in kids), len(kids))

    data = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, 1):
        offsets.append(len(data))
        data += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(data)
    data += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for off in offsets:
        data += b"%010d 00000 n \n" % off
    data += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1, catalog, xref)

    with open(out, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sample.pdf")
