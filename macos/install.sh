#!/bin/bash
# Firefox PDF Reader (full screen) for macOS.
#
# 1. Creates a dedicated Firefox profile with the PDF viewer settings and a
#    style sheet that hides the toolbar.
# 2. Builds "Firefox PDF Reader.app" in ~/Applications: a small AppleScript
#    app that opens PDFs in that profile in kiosk (full-screen) mode.
# 3. Makes it the default app for PDFs.
#
# Usage:  ./macos/install.sh [--profile-dir DIR] [--no-default]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE_DIR="$HOME/Library/Application Support/FirefoxPDF"
APP_DIR="$HOME/Applications/Firefox PDF Reader.app"
BUNDLE_ID="io.github.firefox-pdf-reader"
SET_DEFAULT=1

while [ $# -gt 0 ]; do
  case "$1" in
    --profile-dir) PROFILE_DIR="$2"; shift 2 ;;
    --no-default)  SET_DEFAULT=0; shift ;;
    -h|--help)     sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

step() { printf '\033[36m==> %s\033[0m\n' "$1"; }

# --- 1. Find Firefox ---------------------------------------------------------
step "Looking for Firefox"
FIREFOX_APP=""
for c in "/Applications/Firefox.app" "$HOME/Applications/Firefox.app"; do
  [ -d "$c" ] && { FIREFOX_APP="$c"; break; }
done
if [ -z "$FIREFOX_APP" ]; then
  FIREFOX_APP="$(mdfind "kMDItemCFBundleIdentifier == 'org.mozilla.firefox'" 2>/dev/null | head -n1 || true)"
fi
if [ -z "$FIREFOX_APP" ] || [ ! -x "$FIREFOX_APP/Contents/MacOS/firefox" ]; then
  echo "Firefox not found. Install it from https://www.mozilla.org/firefox/ or: brew install --cask firefox" >&2
  exit 1
fi
FIREFOX_BIN="$FIREFOX_APP/Contents/MacOS/firefox"
echo "    $FIREFOX_APP"

# --- 2. Profile --------------------------------------------------------------
step "Writing Firefox profile files to $PROFILE_DIR"
mkdir -p "$PROFILE_DIR/chrome"
cp "$REPO_DIR/profile/user.js" "$PROFILE_DIR/"
cp "$REPO_DIR/profile/chrome/userContent.css" "$PROFILE_DIR/chrome/"

# --- 3. Launcher app -----------------------------------------------------------
step "Building $APP_DIR"
mkdir -p "$HOME/Applications"
rm -rf "$APP_DIR"

# AppleScript string literals: escape backslashes and double quotes
as_escape() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }
FF_AS="$(as_escape "$FIREFOX_BIN")"
PROF_AS="$(as_escape "$PROFILE_DIR")"

SCRIPT_FILE="$(mktemp -t firefox-pdf-reader).applescript"
cat > "$SCRIPT_FILE" <<EOF
-- Opens PDFs in the dedicated Firefox profile, full screen (kiosk mode).
property firefoxBin : "$FF_AS"
property profileDir : "$PROF_AS"

on launchWith(argString)
	do shell script quoted form of firefoxBin & " -profile " & quoted form of profileDir & " --kiosk" & argString & " > /dev/null 2>&1 &"
end launchWith

on open theFiles
	set argString to ""
	repeat with f in theFiles
		set argString to argString & " " & quoted form of (POSIX path of f)
	end repeat
	launchWith(argString)
end open

on run
	launchWith("")
end run
EOF
osacompile -o "$APP_DIR" "$SCRIPT_FILE"
rm -f "$SCRIPT_FILE"

PLIST="$APP_DIR/Contents/Info.plist"
PB=/usr/libexec/PlistBuddy
$PB -c "Set :CFBundleIdentifier $BUNDLE_ID" "$PLIST" 2>/dev/null || $PB -c "Add :CFBundleIdentifier string $BUNDLE_ID" "$PLIST"
$PB -c "Set :CFBundleName Firefox PDF Reader" "$PLIST" 2>/dev/null || $PB -c "Add :CFBundleName string Firefox PDF Reader" "$PLIST"
$PB -c "Delete :CFBundleDocumentTypes" "$PLIST" 2>/dev/null || true
$PB -c "Add :CFBundleDocumentTypes array" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0 dict" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:CFBundleTypeName string PDF Document" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:CFBundleTypeRole string Viewer" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:LSHandlerRank string Owner" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes array" "$PLIST"
$PB -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes:0 string com.adobe.pdf" "$PLIST"

# Use Firefox's icon
FF_ICON="$($PB -c "Print :CFBundleIconFile" "$FIREFOX_APP/Contents/Info.plist" 2>/dev/null || echo firefox)"
FF_ICON="${FF_ICON%.icns}.icns"
if [ -f "$FIREFOX_APP/Contents/Resources/$FF_ICON" ]; then
  cp "$FIREFOX_APP/Contents/Resources/$FF_ICON" "$APP_DIR/Contents/Resources/applet.icns"
fi

# Editing Info.plist invalidates the applet's signature; re-sign it locally
codesign --force --deep --sign - "$APP_DIR" >/dev/null 2>&1 || true

LSREGISTER=/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister
"$LSREGISTER" -f "$APP_DIR"

# --- 4. Default PDF app --------------------------------------------------------
DEFAULT_SET=0
if [ "$SET_DEFAULT" = 1 ]; then
  step "Making it the default app for PDFs"
  if command -v duti >/dev/null 2>&1 && duti -s "$BUNDLE_ID" com.adobe.pdf all; then
    DEFAULT_SET=1
  elif osascript -l JavaScript -e "ObjC.import('CoreServices'); \$.LSSetDefaultRoleHandlerForContentType('com.adobe.pdf', \$.kLSRolesAll, '$BUNDLE_ID') === 0" 2>/dev/null | grep -q true; then
    DEFAULT_SET=1
  fi
fi

echo
printf '\033[32mInstalled.\033[0m\n\n'
if [ "$SET_DEFAULT" = 1 ] && [ "$DEFAULT_SET" = 0 ]; then
  echo "Could not set the default PDF app automatically. To do it by hand:"
  echo "  Finder > select any PDF > File > Get Info > Open with: Firefox PDF Reader > Change All..."
  echo
fi
echo "Smooth mouse wheel (Logitech): Logi Options+ > your mouse > Point and Scroll"
echo "  > Scroll wheel > turn Smooth scrolling on."
echo
echo "Keys: Cmd+Q closes the reader, Ctrl+Tab switches PDFs, Cmd+W closes one."
