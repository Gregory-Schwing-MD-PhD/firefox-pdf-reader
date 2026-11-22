// Firefox PDF Reader: the settings of the reader's copy of pdf.js's viewer.
// pdf.js sends "webviewerloaded" just before its viewer starts; the settings
// made here are the ones it starts with.
document.addEventListener(
  "webviewerloaded",
  () => {
    const options = window.PDFViewerApplicationOptions;
    for (const [name, value] of Object.entries({
      // These settings, not ones the viewer may have saved in the browser
      disablePreferences: true,
      // Black pages and white text, pictures in their own colours: the
      // viewer asks for these page colours, and the reader's change in
      // build/pdf.mjs (readerColor) applies them to text, lines and fills only
      forcePageColors: true,
      pageColorsBackground: "#000000",
      pageColorsForeground: "#ffffff",
      // A dark viewer around the pages
      viewerCssTheme: 2,
      // Page width, one long vertical scroll, no spreads, sidebar closed
      defaultZoomValue: "page-width",
      scrollModeOnLoad: 0,
      spreadModeOnLoad: 0,
      sidebarViewOnLoad: 0,
      // A web link opens in a new window (Firefox's browser.link.open_newwindow)
      externalLinkTarget: 2,
      // Draw on the graphics card
      enableHWA: true,
      // Pages with page colours are drawn by the viewer itself, so its
      // separate drawing worker would only sit idle
      rendererSrc: "",
      // No sample PDF when no PDF is given
      defaultUrl: "",
    })) {
      options.set(name, value);
    }
  },
  { once: true }
);
