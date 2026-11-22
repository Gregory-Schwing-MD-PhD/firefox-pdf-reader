#!/bin/sh
# Builds firefox-pdf-reader_VERSION_all.deb for Ubuntu, Debian, Linux Mint,
# Pop!_OS and ChromeOS (double-click it in the Files app to install).
#
# Usage:  sh ./linux/package/build-deb.sh OUTPUT_DIR [VERSION]
set -eu

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="${1:?usage: build-deb.sh OUTPUT_DIR [VERSION]}"
VERSION="${2:-1.0}"
PKG=firefox-pdf-reader

ROOT="$(mktemp -d)"
trap 'rm -rf "$ROOT"' EXIT

install -Dm755 "$REPO_DIR/linux/package/firefox-pdf-reader" "$ROOT/usr/bin/firefox-pdf-reader"
install -Dm644 "$REPO_DIR/profile/user.js" "$ROOT/usr/share/$PKG/profile/user.js"
for css in "$REPO_DIR/profile/chrome/"*.css; do
  install -Dm644 "$css" "$ROOT/usr/share/$PKG/profile/chrome/$(basename "$css")"
done
# The reader's own viewer (pdf.js, Apache License 2.0; see its NOTICE) and the
# helper that makes a PDF's address in it
cp -R "$REPO_DIR/viewer" "$ROOT/usr/share/$PKG/viewer"
chmod -R u=rwX,go=rX "$ROOT/usr/share/$PKG/viewer"
install -Dm644 "$REPO_DIR/launchers/viewer-url.sh" "$ROOT/usr/share/$PKG/viewer-url.sh"
install -Dm644 "$REPO_DIR/LICENSE" "$ROOT/usr/share/doc/$PKG/copyright"

install -d "$ROOT/usr/share/applications"
cat > "$ROOT/usr/share/applications/$PKG.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Firefox PDF Reader
GenericName=PDF Reader
Comment=Read PDFs, each in its own window, with nothing but the pages
Exec=firefox-pdf-reader %F
Icon=firefox
Terminal=false
Categories=Office;Viewer;
MimeType=application/pdf;
StartupWMClass=firefox
EOF

install -d "$ROOT/DEBIAN"
cat > "$ROOT/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Architecture: all
Maintainer: Firefox PDF Reader <noreply@github.com>
Depends: firefox-esr | firefox, xdg-utils
Section: text
Priority: optional
Homepage: https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/
Description: Distraction-free PDF reader built on Firefox
 Opens each PDF in its own window of Firefox's PDF viewer, in the reader's own
 profile: a window filling the screen (F11 for full screen), black pages with
 white text and pictures in their own colours, fit to page width,
 continuous vertical scrolling, no toolbar or sidebar, and it remembers where
 you left off. Becomes the default PDF app for every user who hasn't chosen
 one.
EOF

# Make it the system-wide default for PDFs (users who picked their own
# default keep it; the launcher also sets it for each user on first run).
cat > "$ROOT/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
LIST=/etc/xdg/mimeapps.list
LINE='application/pdf=firefox-pdf-reader.desktop;'
mkdir -p /etc/xdg
[ -f "$LIST" ] || printf '[Default Applications]\n' > "$LIST"
if ! grep -q '^\[Default Applications\]' "$LIST"; then printf '\n[Default Applications]\n' >> "$LIST"; fi
if grep -q '^application/pdf=' "$LIST"; then
  sed -i "s|^application/pdf=.*|$LINE|" "$LIST"
else
  sed -i "/^\[Default Applications\]/a $LINE" "$LIST"
fi
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q /usr/share/applications || true
exit 0
EOF

cat > "$ROOT/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = remove ] || [ "$1" = purge ]; then
  [ -f /etc/xdg/mimeapps.list ] && sed -i '/^application\/pdf=firefox-pdf-reader\.desktop;$/d' /etc/xdg/mimeapps.list || true
  command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q /usr/share/applications || true
fi
exit 0
EOF
chmod 755 "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/postrm"

mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/${PKG}_${VERSION}_all.deb"
dpkg-deb --root-owner-group --build "$ROOT" "$OUT" >/dev/null
echo "$OUT"
