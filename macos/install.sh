#!/bin/bash
# Firefox PDF Reader (full screen) for macOS, installed from a copy of this
# repository. (Most people should use FirefoxPDFReader.dmg instead: open it
# and drag the app into Applications.)
#
# Builds "Firefox PDF Reader.app" into ~/Applications and runs its setup:
# the reader's Firefox profile in ~/Library/Application Support/FirefoxPDF,
# and the app as the default for PDFs.
#
# Usage:  bash ./macos/install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE_ID="io.github.firefox-pdf-reader"
step() { printf '\033[36m==> %s\033[0m\n' "$1"; }

step "Looking for Firefox"
FIREFOX_APP=""
for c in "/Applications/Firefox.app" "$HOME/Applications/Firefox.app"; do
  [ -d "$c" ] && { FIREFOX_APP="$c"; break; }
done
[ -n "$FIREFOX_APP" ] || FIREFOX_APP="$(mdfind "kMDItemCFBundleIdentifier == 'org.mozilla.firefox'" 2>/dev/null | head -n1 || true)"
if [ -z "$FIREFOX_APP" ] || [ ! -x "$FIREFOX_APP/Contents/MacOS/firefox" ]; then
  echo "Firefox not found. Install it from https://www.mozilla.org/firefox/ or: brew install --cask firefox" >&2
  exit 1
fi
echo "    $FIREFOX_APP"

step "Building Firefox PDF Reader.app in ~/Applications"
APP="$(bash "$REPO_DIR/macos/build-app.sh" "$HOME/Applications")"
echo "    $APP"

step "Setting up the reader and making it the default app for PDFs"
PROFILE="$(/bin/sh "$APP/Contents/Resources/setup.sh" "$APP/Contents/Resources/")"
echo "    profile: $PROFILE"
HANDLER="$(osascript -l JavaScript -e "ObjC.import('CoreServices'); ObjC.castRefToObject(\$.LSCopyDefaultRoleHandlerForContentType(\$('com.adobe.pdf'), 0xFFFFFFFF)).js" 2>/dev/null || true)"
echo "    PDFs open with: $HANDLER"

echo
printf '\033[32mInstalled.\033[0m\n\n'
if [ "$HANDLER" != "$BUNDLE_ID" ]; then
  echo "If macOS asked, choose \"Use Firefox PDF Reader\". Otherwise set it by hand:"
  echo "  Finder > select any PDF > File > Get Info > Open with: Firefox PDF Reader > Change All..."
  echo
fi
echo "Smooth mouse wheel (Logitech): Logi Options+ > your mouse > Point and Scroll"
echo "  > Scroll wheel > turn Smooth scrolling on."
echo
echo "Keys: Cmd+Q closes the reader, Ctrl+Tab switches PDFs, Cmd+W closes one."
