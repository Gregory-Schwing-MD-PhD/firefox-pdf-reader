#!/bin/bash
# Builds FirefoxPDFReader.dmg: the app plus an Applications shortcut, so
# people install it by dragging the app into Applications.
#
# Usage:  ./macos/build-dmg.sh OUTPUT_DIR [VERSION]
#
# For a download that opens without a Gatekeeper warning, set
#   SIGN_IDENTITY      "Developer ID Application: Name (TEAMID)"
#   NOTARY_APPLE_ID, NOTARY_TEAM_ID, NOTARY_PASSWORD (app-specific password)
# and the app is signed, and the disk image notarized and stapled.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${1:?usage: build-dmg.sh OUTPUT_DIR [VERSION]}"
VERSION="${2:-1.0}"
mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"
DMG="$OUT_DIR/FirefoxPDFReader.dmg"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
bash "$REPO_DIR/macos/build-app.sh" "$STAGE" "$VERSION" >/dev/null
ln -s /Applications "$STAGE/Applications"

rm -f "$DMG"
hdiutil create -volname "Firefox PDF Reader" -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null

if [ -n "${SIGN_IDENTITY:-}" ]; then
  codesign --force --timestamp --sign "$SIGN_IDENTITY" "$DMG"
fi
if [ -n "${NOTARY_APPLE_ID:-}" ] && [ -n "${NOTARY_TEAM_ID:-}" ] && [ -n "${NOTARY_PASSWORD:-}" ]; then
  xcrun notarytool submit "$DMG" --apple-id "$NOTARY_APPLE_ID" --team-id "$NOTARY_TEAM_ID" --password "$NOTARY_PASSWORD" --wait
  xcrun stapler staple "$DMG"
fi

echo "$DMG"
