// Preferences for the dedicated "Firefox PDF Reader" profile.
// Firefox applies this file on every start of the profile.

// ---- PDF view: page width, vertical scrolling, no sidebar, dark UI, dark pages
user_pref("pdfjs.defaultZoomValue", "page-width");
user_pref("pdfjs.scrollModeOnLoad", 0);      // 0 = vertical scrolling
user_pref("pdfjs.spreadModeOnLoad", 0);      // 0 = no spreads
user_pref("pdfjs.sidebarViewOnLoad", 0);     // 0 = sidebar closed
user_pref("pdfjs.viewerCssTheme", 2);        // 2 = dark viewer theme
user_pref("pdfjs.forcePageColors", true);    // recolour pages
user_pref("pdfjs.pageColorsBackground", "#1a1a1a");
user_pref("pdfjs.pageColorsForeground", "#dcdcdc");

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

// ---- Load chrome/userContent.css (hides the PDF toolbar)
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);

// ---- Quiet first run
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("datareporting.policy.dataSubmissionPolicyBypassNotification", true);
user_pref("browser.tabs.warnOnClose", false);
user_pref("browser.sessionstore.resume_from_crash", false);
