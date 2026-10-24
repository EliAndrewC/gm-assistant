# File Zoom Memory (Chrome extension)

Chrome remembers zoom per host name, and a `file://` URL has none, so every local page (the diagram
research site opened from disk, for one) opens at 100% however often you zoom. This extension keeps
ONE zoom level for all `file://` pages: the last one you set with Ctrl+ / Ctrl- / Ctrl+0 is saved and
reapplied each time a local page loads, in any tab. Web pages are untouched.

## Install

1. `chrome://extensions`, turn on **Developer mode** (top right).
2. **Load unpacked**, pick this folder (`~/l7r/gm-assistant/scripts/chrome-file-zoom` on the laptop).
3. After pulling a change to it, press the reload arrow on its card in `chrome://extensions`.

Chrome warns that it can "read your browsing history" - that is the `tabs` permission, needed to see
whether a tab's URL is a `file://` one. It sends nothing anywhere and stores only the zoom number.

## Test

Open a local page, Ctrl+ twice, click a link to another local page: it opens at the same zoom.
Ctrl+0 sets it back to 100% everywhere.

Automated: `test.py` drives Playwright's Chromium with the extension loaded (`python3 test.py
<this folder> <folder with a.html linking to b.html, plus c.html>`); every line after "a before"
should read 1.5. Run against a copy whose background.js only stores the zoom, the same test shows
Chrome resetting to 1, which is the bug this fixes.
