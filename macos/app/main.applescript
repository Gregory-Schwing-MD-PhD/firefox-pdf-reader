-- Firefox PDF Reader.app
-- Double-click the app: sets itself up (profile, default PDF app).
-- Open a PDF with it: shows the PDF in its own window of Firefox, filling the
-- screen, using the reader's own Firefox profile (Ctrl+Cmd+F: full screen),
-- in the reader's own viewer: black pages, white text, pictures in their own
-- colours.

on findFirefox()
	set home to POSIX path of (path to home folder)
	repeat with c in {"/Applications/Firefox.app", home & "Applications/Firefox.app"}
		try
			do shell script "test -x " & quoted form of (c & "/Contents/MacOS/firefox")
			return c & "/Contents/MacOS/firefox"
		end try
	end repeat
	try
		set p to do shell script "mdfind \"kMDItemCFBundleIdentifier == 'org.mozilla.firefox'\" | head -n1"
		if p is not "" then return p & "/Contents/MacOS/firefox"
	end try
	return ""
end findFirefox

-- Copies the reader's settings into its profile and, the first time, makes
-- the app the default for PDFs. Returns the profile folder.
on setUp()
	set res to (POSIX path of (path to me)) & "Contents/Resources/"
	return do shell script "/bin/sh " & quoted form of (res & "setup.sh") & " " & quoted form of res
end setUp

on needFirefox()
	set answer to button returned of (display dialog "Firefox PDF Reader uses Firefox to show PDFs. Install Firefox, then open Firefox PDF Reader again." buttons {"Cancel", "Get Firefox"} default button "Get Firefox" with title "Firefox PDF Reader" with icon caution)
	if answer is "Get Firefox" then open location "https://www.mozilla.org/firefox/"
end needFirefox

on run
	if findFirefox() is "" then
		needFirefox()
		return
	end if
	setUp()
	set msg to "Firefox PDF Reader is ready." & return & return & "Double-click any PDF to read it with nothing but the pages. Each PDF opens in its own window." & return & return & "Ctrl+Cmd+F: full screen, Esc leaves it. Cmd+` switches between open PDFs, Cmd+W closes one, Cmd+Q closes the reader."
	display dialog msg buttons {"OK"} default button "OK" with title "Firefox PDF Reader" giving up after 120
end run

on open theFiles
	set ff to findFirefox()
	if ff is "" then
		needFirefox()
		return
	end if
	set profileDir to setUp()
	set res to (POSIX path of (path to me)) & "Contents/Resources/"
	set viewer to profileDir & "/viewer/web/viewer.html"
	-- -new-window: every PDF gets a window of its own, also when the reader is
	-- already running (Firefox hands the request to the running reader).
	-- Each opens in the reader's viewer: viewer_url (viewer-url.sh) makes its
	-- address. Without the viewer, the PDF goes to Firefox's own viewer.
	set args to ""
	repeat with f in theFiles
		set pdfAddress to POSIX path of f
		try
			set pdfAddress to do shell script ". " & quoted form of (res & "viewer-url.sh") & " && test -f " & quoted form of viewer & " && viewer_url " & quoted form of viewer & " " & quoted form of pdfAddress
		end try
		set args to args & " -new-window " & quoted form of pdfAddress
	end repeat
	do shell script quoted form of ff & " -profile " & quoted form of profileDir & args & " > /dev/null 2>&1 &"
end open
