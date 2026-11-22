# Helpers for the macOS tests: the reader's windows as macOS lists them
# (System Events, the list Cmd+` goes through; and the window server's own
# list), keys pressed through System Events, and screenshots.
# Use:  . tests/macos/reader-windows.sh

FF='first process whose bundle identifier is "org.mozilla.firefox"'

# One window title per line, front window first
reader_windows() {
  osascript <<EOF 2>/dev/null | grep . || true
tell application "System Events"
  if not (exists ($FF)) then return ""
  set out to ""
  repeat with w in (windows of ($FF))
    set out to out & (name of w) & linefeed
  end repeat
  return out
end tell
EOF
}

reader_window_count() {
  reader_windows | grep -c . || true
}

# The window server's own list of Firefox's windows (all Spaces): title, layer, bounds
window_server_list() {
  osascript -l JavaScript <<'EOF'
ObjC.import('CoreGraphics');
const list = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(0, 0)));
list.filter(w => w.kCGWindowOwnerName === 'Firefox' && w.kCGWindowLayer === 0 && w.kCGWindowName)
    .map(w => `${w.kCGWindowName} | ${w.kCGWindowBounds.Width}x${w.kCGWindowBounds.Height} | on screen: ${!!w.kCGWindowIsOnscreen}`)
    .join('\n');
EOF
}

wait_windows() {  # wait_windows N [seconds]
  for _ in $(seq 1 "${2:-60}"); do
    [ "$(reader_window_count)" -eq "$1" ] && { reader_windows; return 0; }
    sleep 1
  done
  echo "Expected $1 reader windows, found $(reader_window_count):" >&2
  reader_windows >&2
  return 1
}

wait_title() {  # wait_title TEXT [seconds]
  for _ in $(seq 1 "${2:-60}"); do
    reader_windows | grep -qF -- "$1" && return 0
    sleep 1
  done
  echo "No reader window titled with $1:" >&2
  reader_windows >&2
  return 1
}

front_title() {
  osascript -e "tell application \"System Events\" to tell ($FF) to get name of window 1"
}

front_is_fullscreen() {
  [ "$(osascript -e "tell application \"System Events\" to tell ($FF) to get value of attribute \"AXFullScreen\" of window 1")" = true ]
}

# The front window fills the screen's width and nearly all its height (all
# but the menu bar and the Dock), without being full screen
front_fills_screen() {
  scr="$(osascript -l JavaScript -e 'ObjC.import("AppKit"); const f = $.NSScreen.mainScreen.frame; Math.round(f.size.width) + " " + Math.round(f.size.height)')"
  win="$(osascript -e "tell application \"System Events\" to tell ($FF) to get size of window 1" | tr ',' ' ')"
  set -- $scr $win
  echo "window $3x$4, screen $1x$2"
  [ "$3" -ge $(( $1 - 2 )) ] && [ "$4" -ge $(( $2 - 160 )) ]
}

# click_page_point JSON POINTS_DOWN: a mouse click in the middle of the page,
# POINTS_DOWN PDF points below its top, using where compare_colours.py found
# the page in a screenshot (screenshots here are in screen points)
click_page_point() {
  set -- $(python -c "import json, sys; p = json.load(open(sys.argv[1]))['page_in_screenshot']; print(p['left'] + p['width'] // 2, p['top'] + round(p['width'] / 612 * float(sys.argv[2])))" "$1" "$2")
  echo "clicking at $1,$2"
  osascript -l JavaScript <<EOF
ObjC.import('CoreGraphics');
const p = { x: $1, y: $2 };
for (const t of [\$.kCGEventMouseMoved, \$.kCGEventLeftMouseDown, \$.kCGEventLeftMouseUp]) {
  \$.CGEventPost(\$.kCGHIDEventTap, \$.CGEventCreateMouseEvent(null, t, p, \$.kCGMouseButtonLeft));
  delay(0.15);
}
EOF
}

bring_front() {
  osascript -e "tell application \"System Events\" to set frontmost of ($FF) to true"
  sleep 1
}

# press KEYCODE [modifiers...]: e.g. press 53 (Esc), press 50 command (Cmd+`)
press() {
  code="$1"; shift
  if [ $# -gt 0 ]; then
    mods="$(printf '%s down, ' "$@" | sed 's/, $//')"
    osascript -e "tell application \"System Events\" to key code $code using {$mods}"
  else
    osascript -e "tell application \"System Events\" to key code $code"
  fi
}

# macOS asks whether PDFs should open with the reader or keep using Preview
# when the reader makes itself the default; click "Use ..." as a person would.
answer_default_app_question() {
  osascript <<'EOF' 2>/dev/null || true
tell application "System Events"
  if exists process "CoreServicesUIAgent" then
    tell process "CoreServicesUIAgent"
      repeat with w in windows
        repeat with b in buttons of w
          if name of b starts with "Use" then
            click b
            return "clicked: " & (name of b)
          end if
        end repeat
      end repeat
    end tell
  end if
  return "no question on screen"
end tell
EOF
}

shot() {  # shot FILE
  screencapture -x "$1" && echo "screenshot: $1"
}

reader_processes() {
  ps -axo pid,command | grep '[C]ontents/MacOS/firefox ' || true
}
