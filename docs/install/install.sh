#!/bin/sh
# One-step installer for Firefox PDF Reader on macOS, Linux and ChromeOS.
# Downloads the latest version of the project and runs the installer for
# the system it's on:
#   curl -fsSL https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/install/install.sh | sh
set -eu

REPO="Gregory-Schwing-MD-PhD/firefox-pdf-reader"
printf '\033[36mFirefox PDF Reader setup\033[0m\n'

case "$(uname -s)" in
  Darwin) PLATFORM=macos ;;
  Linux)
    if [ -e /dev/.cros_milestone ] || [ -d /opt/google/cros-containers ]; then
      PLATFORM=chromeos
    else
      PLATFORM=linux
    fi ;;
  *) echo "Unsupported system: $(uname -s). On Windows, use FirefoxPDFReader-Setup.cmd." >&2; exit 1 ;;
esac
echo "==> Detected: $PLATFORM"

if [ "$PLATFORM" = macos ] && [ ! -d /Applications/Firefox.app ] && [ ! -d "$HOME/Applications/Firefox.app" ]; then
  if command -v brew >/dev/null 2>&1; then
    echo "==> Firefox not found; installing it with Homebrew"
    brew install --cask firefox
  else
    echo "Firefox is required. Opening the download page; install it, then run this again." >&2
    open "https://www.mozilla.org/firefox/"
    exit 1
  fi
fi

DIR="$(mktemp -d)"
trap 'rm -rf "$DIR"' EXIT
echo "==> Downloading Firefox PDF Reader"
curl -fsSL "https://github.com/$REPO/archive/refs/heads/main.tar.gz" | tar -xz -C "$DIR"
SRC="$(find "$DIR" -mindepth 1 -maxdepth 1 -type d | head -n1)"

case "$PLATFORM" in
  macos)    bash "$SRC/macos/install.sh" ;;
  chromeos) sh "$SRC/chromeos/install.sh" ;;
  linux)    sh "$SRC/linux/install.sh" ;;
esac
