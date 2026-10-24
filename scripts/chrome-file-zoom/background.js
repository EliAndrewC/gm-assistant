// Chrome saves zoom per host, and a file:// URL has no host, so every new local page opens at the
// default zoom. This keeps ONE zoom level for all file:// pages: the last one you set (Ctrl+/-/0)
// is stored, and reapplied whenever a file:// page commits in a tab.

const KEY = "fileZoom";
const applying = new Set(); // tabs whose zoom this extension is setting right now

const isFile = (url) => typeof url === "string" && url.startsWith("file://");

chrome.webNavigation.onCommitted.addListener(async ({ tabId, frameId, url }) => {
  if (frameId !== 0 || !isFile(url)) return;
  const { [KEY]: zoom } = await chrome.storage.local.get(KEY);
  if (!zoom) return;
  applying.add(tabId);
  try {
    await chrome.tabs.setZoom(tabId, zoom);
  } catch {
    // the tab closed or navigated away first
  } finally {
    applying.delete(tabId);
  }
});

chrome.tabs.onZoomChange.addListener(async ({ tabId, newZoomFactor }) => {
  if (applying.has(tabId)) return;
  let tab;
  try {
    tab = await chrome.tabs.get(tabId);
  } catch {
    return;
  }
  // While a page loads, a zoom change is Chrome resetting it for the new page (or this extension
  // restoring it), not the user's choice; storing it would overwrite the saved level with 100%.
  if (!isFile(tab.url) || tab.status === "loading") return;
  await chrome.storage.local.set({ [KEY]: newZoomFactor });
});
