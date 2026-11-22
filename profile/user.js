// Preferences for the dedicated "Firefox PDF Reader" profile.
// Firefox applies this file on every start of the profile.

// ---- PDF view: page width, vertical scrolling, no sidebar, dark viewer
user_pref("pdfjs.defaultZoomValue", "page-width");
user_pref("pdfjs.scrollModeOnLoad", 0);      // 0 = vertical scrolling
user_pref("pdfjs.spreadModeOnLoad", 0);      // 0 = no spreads
user_pref("pdfjs.sidebarViewOnLoad", 0);     // 0 = sidebar closed
user_pref("pdfjs.viewerCssTheme", 2);        // 2 = dark viewer around the pages

// ---- Black pages, white text, pictures in their own colours
// The reader opens PDFs in its own copy of pdf.js's viewer (the folder
// "viewer" in this profile), which draws pages black with white text and
// leaves pictures as they are. Firefox's built-in viewer can't: its page
// colours (pdfjs.forcePageColors) recolour pictures too. That viewer is a
// page on this computer (a file:// address) that has to read the PDF, also a
// file on this computer; Firefox lets one local file read another only with
// this setting off. It is off in this profile only, not in your own Firefox:
// a page opened from your disk in the reader can read other files on your
// disk. Web pages can't, either way.
user_pref("security.fileuri.strict_origin_policy", false);
// Firefox's built-in viewer keeps its own defaults (no recolouring), written
// out so that an older install of the reader, which recoloured every page
// with them, pictures included, gets them back: Firefox keeps a changed
// setting until something sets it again.
user_pref("pdfjs.forcePageColors", false);
user_pref("pdfjs.pageColorsBackground", "Canvas");
user_pref("pdfjs.pageColorsForeground", "CanvasText");

// ---- Every PDF in its own ordinary window
// The system's own title bar, showing the PDF's name, with its minimise,
// maximise and close buttons (Firefox's tab strip and address bar are hidden
// by chrome/userChrome.css).
user_pref("browser.tabs.inTitlebar", 0);
// A web link clicked in a PDF opens in a new window; the PDF stays where it was.
user_pref("pdfjs.externalLinkTarget", 2);    // 2 = open in a new browsing context
user_pref("browser.link.open_newwindow", 2); // 2 = a new window, not a tab
user_pref("browser.link.open_newwindow.disabled_in_fullscreen", false);  // also in full screen (macOS)
// Full screen hides Firefox's bar and slides it down when the mouse touches
// the top edge (macOS would otherwise keep it showing).
user_pref("browser.fullscreen.autohide", true);
// Cmd+Q (Ctrl+Q on Linux) closes the reader straight away, like any app.
user_pref("browser.warnOnQuitShortcut", false);

// ---- Smooth scrolling
// The mouse's own smooth scrolling (Logi Options+) does the gliding, so
// Firefox's easing stays at its defaults to avoid the two fighting.
user_pref("general.smoothScroll", true);
user_pref("apz.overscroll.enabled", true);
user_pref("general.smoothScroll.msdPhysics.enabled", false);
user_pref("general.smoothScroll.currentVelocityWeighting", "0.25");
user_pref("general.smoothScroll.stopDecelerationWeighting", "0.4");
user_pref("mousewheel.default.delta_multiplier_y", 100);

// ---- Render PDF pages on the GPU
user_pref("pdfjs.enableHWA", true);
user_pref("gfx.webrender.all", true);

// ---- Load chrome/userChrome.css (hides the browser's bars) and
// chrome/userContent.css (hides the PDF toolbar, shows the short hint)
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);

// ---- Quiet first run
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("datareporting.policy.dataSubmissionPolicyBypassNotification", true);
user_pref("browser.tabs.warnOnClose", false);
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("browser.startup.upgradeDialog.enabled", false);
user_pref("browser.shell.setDefaultPDFHandler", false);       // never take over .pdf from the reader
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features", false);
// No first-run messages from this profile (on Windows one of them asks the
// system to pin Firefox to the taskbar, which pops up over the first PDF)
user_pref("browser.newtabpage.activity-stream.asrouter.providers.onboarding", "{\"id\":\"onboarding\",\"type\":\"local\",\"localProvider\":\"OnboardingMessageProvider\",\"enabled\":false,\"exclude\":[]}");

// No usage-data uploads from this profile (also stops the data-reporting notice bar)
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("app.shield.optoutstudies.enabled", false);
