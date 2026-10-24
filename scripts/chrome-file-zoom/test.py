import asyncio, sys, tempfile
from playwright.async_api import async_playwright
EXT, PAGES = sys.argv[1], sys.argv[2]
async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(tempfile.mkdtemp(), channel="chromium", headless=True,
            args=[f"--disable-extensions-except={EXT}", f"--load-extension={EXT}"])
        sw = ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker")
        zoom = lambda: sw.evaluate("async () => { const [t] = await chrome.tabs.query({url:'file:///*'}); return t ? chrome.tabs.getZoom(t.id) : null }")
        page = await ctx.new_page()
        await page.goto(f"file://{PAGES}/a.html")
        print("a before:", await zoom())
        # simulate the user's Ctrl+ on a loaded page
        await sw.evaluate("async () => { const [t] = await chrome.tabs.query({url:'file:///*'}); await chrome.tabs.setZoom(t.id, 1.5) }")
        await asyncio.sleep(0.5)
        print("stored:", await sw.evaluate("() => chrome.storage.local.get('fileZoom')"))
        await page.click("a"); await page.wait_for_load_state("load"); await asyncio.sleep(0.5)
        print("b after link click:", await zoom())
        await page.goto(f"file://{PAGES}/c.html"); await asyncio.sleep(0.5)
        print("c after goto:", await zoom())
        p2 = await ctx.new_page(); await p2.goto(f"file://{PAGES}/a.html"); await asyncio.sleep(0.5)
        print("new tab:", await sw.evaluate("async () => { const ts = await chrome.tabs.query({url:'file:///*'}); return Promise.all(ts.map(t => chrome.tabs.getZoom(t.id))) }"))
        print("stored at end:", await sw.evaluate("() => chrome.storage.local.get('fileZoom')"))
        await ctx.close()
asyncio.run(main())
