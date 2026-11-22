# Firefox PDF Reader: the address that opens a PDF in the reader's own viewer.
# Used by the launchers on Linux, ChromeOS and macOS (POSIX sh and awk only).
#
#   viewer_url VIEWER_HTML PDF   prints  file://VIEWER_HTML?file=<PDF's file:// address>
#                                (PDF: a path, or already a file:// address)
#
# The viewer (pdf.js's viewer.html in the reader's profile) reads the PDF's
# address from "file" after the "?", so that address is encoded once more.

# Percent-encodes $1 byte by byte, keeping letters, digits, - . _ ~ and the
# characters listed in $2.
percent_encode() {
  PE_TEXT="$1" PE_KEEP="$2" LC_ALL=C awk 'BEGIN {
    s = ENVIRON["PE_TEXT"]; keep = ENVIRON["PE_KEEP"]
    for (i = 1; i < 256; i++) code[sprintf("%c", i)] = i
    n = length(s)
    for (i = 1; i <= n; i++) {
      c = substr(s, i, 1)
      if (c ~ /[A-Za-z0-9._~-]/ || (keep != "" && index(keep, c) > 0)) printf "%s", c
      else printf "%%%02X", code[c]
    }
  }'
}

viewer_url() {
  case "$2" in
    file://*) vu_pdf="$2" ;;                                   # already an address
    /*) vu_pdf="file://$(percent_encode "$2" /)" ;;
    *) vu_pdf="file://$(percent_encode "$PWD/$2" /)" ;;
  esac
  printf 'file://%s?file=%s\n' "$(percent_encode "$1" /)" "$(percent_encode "$vu_pdf" "")"
}
