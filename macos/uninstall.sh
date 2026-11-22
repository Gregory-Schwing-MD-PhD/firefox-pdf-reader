#!/bin/bash
# Removes Firefox PDF Reader from macOS.
# The profile folder (per-PDF reading positions) is kept unless --remove-profile is given.
#
# Usage:  ./macos/uninstall.sh [--profile-dir DIR] [--remove-profile]
set -euo pipefail

PROFILE_DIR="$HOME/Library/Application Support/FirefoxPDF"
APP_DIR="$HOME/Applications/Firefox PDF Reader.app"
REMOVE_PROFILE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --profile-dir)    PROFILE_DIR="$2"; shift 2 ;;
    --remove-profile) REMOVE_PROFILE=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

LSREGISTER=/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister
[ -d "$APP_DIR" ] && "$LSREGISTER" -u "$APP_DIR" 2>/dev/null || true
rm -rf "$APP_DIR"

if [ "$REMOVE_PROFILE" = 1 ]; then
  rm -rf "$PROFILE_DIR"
  echo "Removed profile folder $PROFILE_DIR"
else
  echo "Kept profile folder $PROFILE_DIR (use --remove-profile to delete it)"
fi

echo "Uninstalled. Choose a new default PDF app: Finder > a PDF > Get Info > Open with > Change All..."
