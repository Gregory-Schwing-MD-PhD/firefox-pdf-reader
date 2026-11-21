#!/bin/sh
# Firefox PDF Reader (full screen) for ChromeOS / Chromebooks.
#
# ChromeOS can't run Firefox directly, so this runs inside ChromeOS's Linux
# environment ("Linux development environment", also called Crostini):
#   1. Installs Firefox ESR in the Linux container if it isn't there.
#   2. Runs linux/install.sh, which sets up the profile, launcher and the
#      desktop entry. ChromeOS then lists "Firefox PDF Reader" as an app and
#      offers it under Files > Open with for PDFs.
#
# Before running: Settings > About ChromeOS > Developers > Linux development
# environment > Turn on. Then open the Terminal app and run this script there.
#
# Usage:  ./chromeos/install.sh [--no-default]
set -eu

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

step() { printf '\033[36m==> %s\033[0m\n' "$1"; }

if [ ! -e /dev/.cros_milestone ] && [ ! -d /opt/google/cros-containers ]; then
  echo "This doesn't look like ChromeOS's Linux environment." >&2
  echo "On a normal Linux PC, run linux/install.sh instead." >&2
  exit 1
fi

if ! command -v firefox-esr >/dev/null 2>&1 && ! command -v firefox >/dev/null 2>&1; then
  step "Installing Firefox ESR in the Linux container (no password needed on ChromeOS)"
  sudo apt-get update
  sudo apt-get install -y firefox-esr
fi

"$REPO_DIR/linux/install.sh" "$@"

cat <<'EOF'

ChromeOS steps:
  * Default PDF app: in the Files app, right-click a PDF > Open with >
    Change default > Firefox PDF Reader.
  * PDFs outside "Linux files" are shared with Linux automatically when you
    open them this way (or right-click a folder > Share with Linux).
  * Smoother scrolling and faster rendering: turn on GPU support for Linux at
    chrome://flags/#crostini-gpu-support, then restart the Chromebook.
  * Mouse and touchpad scroll settings: Settings > Device > Mouse and touchpad.
EOF
