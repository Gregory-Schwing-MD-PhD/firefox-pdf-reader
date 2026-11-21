#!/bin/sh
# Removes Firefox PDF Reader (full screen) from Linux (and ChromeOS's Linux).
# The profile folder (per-PDF reading positions) is kept unless --remove-profile is given.
#
# Usage:  ./linux/uninstall.sh [--remove-profile]
set -eu

APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
REMOVE_PROFILE=0
[ "${1:-}" = "--remove-profile" ] && REMOVE_PROFILE=1

# Read the profile folder from the launcher before deleting it
PROFILE_DIR="$(sed -n 's/.*-profile "\([^"]*\)".*/\1/p' "$HOME/.local/bin/firefox-pdf-reader" 2>/dev/null || true)"

rm -f "$HOME/.local/bin/firefox-pdf-reader" "$APPS_DIR/firefox-pdf-reader.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true

if [ "$REMOVE_PROFILE" = 1 ] && [ -n "$PROFILE_DIR" ]; then
  rm -rf "$PROFILE_DIR"
  echo "Removed profile folder $PROFILE_DIR"
elif [ -n "$PROFILE_DIR" ]; then
  echo "Kept profile folder $PROFILE_DIR (use --remove-profile to delete it)"
fi

echo "Uninstalled. Your desktop will fall back to its usual PDF viewer; change it in your file manager if needed."
