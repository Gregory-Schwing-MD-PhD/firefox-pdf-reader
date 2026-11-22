#!/bin/sh
# Runs inside Firefox PDF Reader.app each time it starts.
# $1 = the app's Contents/Resources/ folder. Prints the profile folder.
set -eu

RES="$1"
BUNDLE_ID="io.github.firefox-pdf-reader"
PROFILE="${FIREFOX_PDF_PROFILE:-$HOME/Library/Application Support/FirefoxPDF}"
APP="$(cd "$RES/../.." && pwd)"

# Reader settings (refreshed every time, so app updates apply)
mkdir -p "$PROFILE/chrome"
cp "$RES/profile/user.js" "$PROFILE/"
cp "$RES/profile/chrome/"*.css "$PROFILE/chrome/"

# Open in a window that fills the screen: Firefox restores its window's size
# mode from xulstore.json, and "maximized" is the closest it supports to
# starting full screen (Ctrl+Cmd+F does that; Esc leaves). Firefox writes the
# file itself as windows change, so it is written every time; it counts when
# the reader isn't already running.
printf '%s' '{"chrome://browser/content/browser.xhtml":{"main-window":{"width":"1280","height":"900","sizemode":"maximized"}}}' > "$PROFILE/xulstore.json" || true

# First run of this copy of the app: register it and make it the PDF default.
# macOS may ask to confirm ("Use Firefox PDF Reader" / "Keep Preview").
MARK="$PROFILE/.default-app"
if [ "$(cat "$MARK" 2>/dev/null || true)" != "$APP" ]; then
  /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP" >/dev/null 2>&1 || true
  osascript -l JavaScript -e "ObjC.import('CoreServices'); \$.LSSetDefaultRoleHandlerForContentType(\$('com.adobe.pdf'), 0xFFFFFFFF, \$('$BUNDLE_ID'))" >/dev/null 2>&1 || true
  # Fallback through Swift where the developer tools are installed
  CURRENT="$(osascript -l JavaScript -e "ObjC.import('CoreServices'); ObjC.castRefToObject(\$.LSCopyDefaultRoleHandlerForContentType(\$('com.adobe.pdf'), 0xFFFFFFFF)).js" 2>/dev/null || true)"
  # (xcode-select -p first: calling xcrun without the tools would pop up an installer)
  if [ "$CURRENT" != "$BUNDLE_ID" ] && xcode-select -p >/dev/null 2>&1 && xcrun --find swift >/dev/null 2>&1; then
    printf 'import CoreServices\n_ = LSSetDefaultRoleHandlerForContentType("com.adobe.pdf" as CFString, .all, "%s" as CFString)\n' "$BUNDLE_ID" \
      | xcrun swift - >/dev/null 2>&1 || true
  fi
  printf '%s' "$APP" > "$MARK"
fi

printf '%s' "$PROFILE"
