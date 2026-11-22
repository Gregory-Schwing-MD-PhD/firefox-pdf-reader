# Helpers for the Linux tests: the reader's windows as the window manager
# lists them (wmctrl, the list Alt+Tab goes through), keys pressed with
# xdotool, and screenshots. Needs DISPLAY, wmctrl, xdotool, xprop, ImageMagick.
# Use:  . tests/linux/reader-windows.sh

# "id title" for each Firefox window, one per line
reader_windows() {
  wmctrl -lx | awk 'tolower($3) ~ /firefox/ { id = $1; $1 = $2 = $3 = $4 = ""; sub(/^ +/, ""); print id, $0 }'
}

reader_window_count() {
  reader_windows | grep -c . || true
}

# wait_windows N [seconds]: wait until there are exactly N reader windows
wait_windows() {
  for _ in $(seq 1 "${2:-60}"); do
    [ "$(reader_window_count)" -eq "$1" ] && { reader_windows; return 0; }
    sleep 1
  done
  echo "Expected $1 reader windows, found $(reader_window_count):" >&2
  reader_windows >&2
  return 1
}

# wait_title TEXT [seconds]: wait until a reader window's title holds TEXT
wait_title() {
  for _ in $(seq 1 "${2:-60}"); do
    reader_windows | grep -qF -- "$1" && return 0
    sleep 1
  done
  echo "No reader window titled with $1:" >&2
  reader_windows >&2
  return 1
}

window_id() {  # window_id TEXT: the id of the reader window whose title holds TEXT
  reader_windows | grep -F -- "$1" | head -n1 | cut -d' ' -f1
}

is_fullscreen() {  # is_fullscreen ID
  xprop -id "$1" _NET_WM_STATE | grep -q _NET_WM_STATE_FULLSCREEN
}

is_maximized() {  # is_maximized ID: maximised (filling the screen under its title bar)
  s="$(xprop -id "$1" _NET_WM_STATE)"
  case "$s" in *_NET_WM_STATE_MAXIMIZED_VERT*) ;; *) return 1 ;; esac
  case "$s" in *_NET_WM_STATE_MAXIMIZED_HORZ*) ;; *) return 1 ;; esac
}

# click_page_point JSON POINTS_DOWN: click the middle of the page, POINTS_DOWN
# PDF points below its top, using where compare_colours.py found the page
click_page_point() {
  set -- $(python -c "import json, sys; p = json.load(open(sys.argv[1]))['page_in_screenshot']; print(p['left'] + p['width'] // 2, p['top'] + round(p['width'] / 612 * float(sys.argv[2])))" "$1" "$2")
  echo "clicking at $1,$2"
  xdotool mousemove "$1" "$2" click 1
}

front_title() {
  xdotool getactivewindow getwindowname
}

shot() {  # shot FILE
  import -window root "$1" && echo "screenshot: $1"
}

# Firefox's main processes for the reader's profile (not its page processes)
reader_processes() {
  ps -eo pid,args | grep -E '[f]irefox(-esr|-bin)? .*-profile' | grep -v -- '-contentproc' || true
}
