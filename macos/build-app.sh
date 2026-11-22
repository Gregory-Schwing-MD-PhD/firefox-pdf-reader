#!/bin/bash
# Builds "Firefox PDF Reader.app" (used by install.sh and build-dmg.sh).
#
# Usage:  ./macos/build-app.sh OUTPUT_DIR [VERSION]
#
# Signing: ad-hoc by default. Set SIGN_IDENTITY to a "Developer ID
# Application: ..." identity to sign it for distribution.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${1:?usage: build-app.sh OUTPUT_DIR [VERSION]}"
VERSION="${2:-1.0}"
APP="$OUT_DIR/Firefox PDF Reader.app"
BUNDLE_ID="io.github.firefox-pdf-reader"
PB=/usr/libexec/PlistBuddy

mkdir -p "$OUT_DIR"
rm -rf "$APP"
osacompile -o "$APP" "$REPO_DIR/macos/app/main.applescript"

# Reader files inside the app
RES="$APP/Contents/Resources"
mkdir -p "$RES/profile/chrome"
cp "$REPO_DIR/profile/user.js" "$RES/profile/"
cp "$REPO_DIR/profile/chrome/"*.css "$RES/profile/chrome/"
cp "$REPO_DIR/macos/app/setup.sh" "$RES/"

# App identity and "opens PDFs"
PLIST="$APP/Contents/Info.plist"
setp() { $PB -c "Set :$1 $3" "$PLIST" 2>/dev/null || $PB -c "Add :$1 $2 $3" "$PLIST"; }
setp CFBundleIdentifier string "$BUNDLE_ID"
setp CFBundleName string "Firefox PDF Reader"
setp CFBundleDisplayName string "Firefox PDF Reader"
setp CFBundleShortVersionString string "$VERSION"
setp CFBundleVersion string "$VERSION"
$PB -c "Delete :CFBundleDocumentTypes" "$PLIST" 2>/dev/null || true
$PB -c "Add :CFBundleDocumentTypes array" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0 dict" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:CFBundleTypeName string PDF Document" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:CFBundleTypeRole string Viewer" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:LSHandlerRank string Owner" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes array" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes:0 string com.adobe.pdf" "$PLIST"

# Firefox's icon, if Firefox is on this Mac
for FF in /Applications/Firefox.app "$HOME/Applications/Firefox.app"; do
  if [ -d "$FF" ]; then
    ICON="$($PB -c "Print :CFBundleIconFile" "$FF/Contents/Info.plist" 2>/dev/null || echo firefox)"
    ICON="${ICON%.icns}.icns"
    [ -f "$FF/Contents/Resources/$ICON" ] && cp "$FF/Contents/Resources/$ICON" "$RES/applet.icns"
    break
  fi
done

# Sign (Info.plist edits invalidate osacompile's signature)
if [ -n "${SIGN_IDENTITY:-}" ]; then
  codesign --force --deep --options runtime --timestamp --sign "$SIGN_IDENTITY" "$APP"
else
  codesign --force --deep --sign - "$APP"
fi

echo "$APP"
