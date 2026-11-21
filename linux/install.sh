#!/bin/sh
# Firefox PDF Reader (full screen) for Linux: Ubuntu, Debian, Fedora, Arch,
# openSUSE, Linux Mint, Pop!_OS and other desktops that follow the
# freedesktop.org standards. Also used by chromeos/install.sh.
#
# 1. Creates a dedicated Firefox profile with the PDF viewer settings and a
#    style sheet that hides the toolbar.
# 2. Installs a launcher (~/.local/bin/firefox-pdf-reader) and a desktop
#    entry that opens PDFs in that profile in kiosk (full-screen) mode.
# 3. Makes it the default app for PDFs (xdg-mime).
#
# Works with Firefox installed as a regular package, a Snap (Ubuntu's default)
# or a Flatpak.
#
# Usage:  ./linux/install.sh [--profile-dir DIR] [--no-default]
set -eu

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
LAUNCHER="$BIN_DIR/firefox-pdf-reader"
DESKTOP_ID="firefox-pdf-reader.desktop"
PROFILE_DIR=""
SET_DEFAULT=1

while [ $# -gt 0 ]; do
  case "$1" in
    --profile-dir) PROFILE_DIR="$2"; shift 2 ;;
    --no-default)  SET_DEFAULT=0; shift ;;
    -h|--help)     sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

step() { printf '\033[36m==> %s\033[0m\n' "$1"; }

# --- 1. Find Firefox -----------------------------------------------------------
# The profile has to live where the Firefox package is allowed to write:
#   Snap:    hidden folders in ~ are off-limits, so use the snap's own folder
#   Flatpak: use the app's data folder inside ~/.var
step "Looking for Firefox"
KIND=""
if command -v snap >/dev/null 2>&1 && snap list firefox >/dev/null 2>&1; then
  KIND=snap
  FIREFOX_CMD="/snap/bin/firefox"
  DEFAULT_PROFILE="$HOME/snap/firefox/common/firefox-pdf-reader"
elif command -v firefox >/dev/null 2>&1 && ! readlink -f "$(command -v firefox)" | grep -q '^/snap/'; then
  KIND=native
  FIREFOX_CMD="$(command -v firefox)"
  DEFAULT_PROFILE="${XDG_DATA_HOME:-$HOME/.local/share}/firefox-pdf-reader"
elif command -v firefox-esr >/dev/null 2>&1; then
  KIND=native
  FIREFOX_CMD="$(command -v firefox-esr)"
  DEFAULT_PROFILE="${XDG_DATA_HOME:-$HOME/.local/share}/firefox-pdf-reader"
elif command -v flatpak >/dev/null 2>&1 && flatpak info org.mozilla.firefox >/dev/null 2>&1; then
  KIND=flatpak
  FIREFOX_CMD="flatpak run org.mozilla.firefox"
  DEFAULT_PROFILE="$HOME/.var/app/org.mozilla.firefox/data/firefox-pdf-reader"
else
  echo "Firefox not found. Install it, for example:" >&2
  echo "  Ubuntu:        sudo snap install firefox" >&2
  echo "  Debian:        sudo apt install firefox-esr" >&2
  echo "  Fedora:        sudo dnf install firefox" >&2
  echo "  Arch:          sudo pacman -S firefox" >&2
  echo "  Any (Flatpak): flatpak install flathub org.mozilla.firefox" >&2
  exit 1
fi
[ -n "$PROFILE_DIR" ] || PROFILE_DIR="$DEFAULT_PROFILE"
echo "    $FIREFOX_CMD ($KIND)"

# --- 2. Profile ------------------------------------------------------------------
step "Writing Firefox profile files to $PROFILE_DIR"
mkdir -p "$PROFILE_DIR/chrome"
cp "$REPO_DIR/profile/user.js" "$PROFILE_DIR/"
cp "$REPO_DIR/profile/chrome/userContent.css" "$PROFILE_DIR/chrome/"

# --- 3. Launcher and desktop entry -----------------------------------------------
step "Installing launcher $LAUNCHER"
mkdir -p "$BIN_DIR" "$APPS_DIR"

if [ "$KIND" = flatpak ]; then
  # --file-forwarding passes PDFs from anywhere through the document portal
  cat > "$LAUNCHER" <<EOF
#!/bin/sh
# Opens PDFs in the dedicated Firefox profile, full screen (kiosk mode).
exec flatpak run --file-forwarding org.mozilla.firefox -profile "$PROFILE_DIR" --kiosk @@ "\$@" @@
EOF
else
  cat > "$LAUNCHER" <<EOF
#!/bin/sh
# Opens PDFs in the dedicated Firefox profile, full screen (kiosk mode).
# MOZ_USE_XINPUT2 gives smooth touchpad and high-resolution wheel scrolling on X11.
export MOZ_USE_XINPUT2=1
exec "$FIREFOX_CMD" -profile "$PROFILE_DIR" --kiosk "\$@"
EOF
fi
chmod +x "$LAUNCHER"

case "$KIND" in
  flatpak) ICON=org.mozilla.firefox ;;
  snap)    ICON=/snap/firefox/current/default256.png ;;
  *)       ICON=firefox ;;
esac

step "Installing desktop entry $APPS_DIR/$DESKTOP_ID"
cat > "$APPS_DIR/$DESKTOP_ID" <<EOF
[Desktop Entry]
Type=Application
Name=Firefox PDF Reader
GenericName=PDF Reader
Comment=Read PDFs in Firefox full screen, dark, with no toolbars
Exec="$LAUNCHER" %F
Icon=$ICON
Terminal=false
Categories=Office;Viewer;
MimeType=application/pdf;
StartupWMClass=firefox
EOF
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true

# --- 4. Default PDF app ----------------------------------------------------------
if [ "$SET_DEFAULT" = 1 ]; then
  step "Making it the default app for PDFs"
  if command -v xdg-mime >/dev/null 2>&1; then
    xdg-mime default "$DESKTOP_ID" application/pdf
    echo "    default for application/pdf: $(xdg-mime query default application/pdf)"
  else
    echo "    xdg-mime not found (install xdg-utils); set the default in your file manager instead."
  fi
fi

echo
printf '\033[32mInstalled.\033[0m\n\n'
case ":$PATH:" in *":$BIN_DIR:"*) ;; *) echo "Note: $BIN_DIR is not on your PATH (only matters for running the launcher by hand)."; echo ;; esac
echo "Smooth mouse wheel: touchpads already scroll smoothly. For a Logitech mouse, Solaar"
echo "  (sudo apt install solaar) can turn on high-resolution scrolling if the mouse supports it."
echo
echo "Keys: Alt+F4 closes the reader, Ctrl+Tab switches PDFs, Ctrl+W closes one."
