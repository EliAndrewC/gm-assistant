"""Take screenshots of the relics prototype at multiple viewport sizes.

Usage:
    python3 screenshot.py             # default viewports
    python3 screenshot.py 1440 900    # custom width/height

Requires playwright + chromium installed (one-time: python3 -m playwright install chromium).
Assumes the prototype is being served at http://127.0.0.1:8123/ - start with:
    python3 -m http.server 8123 --directory /gm-assistant/webapp-prototype/relics
"""

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8123"
OUT  = Path("/tmp/relics-shots")
OUT.mkdir(exist_ok=True)

# (label, width, height, device_scale_factor)
# The GM's actual setup: window outerWidth=1850, outerHeight=1173.
# Subtracting Chrome's UI (~120px), the viewport is ~1850 x ~1050.
# At 200% zoom, effective CSS viewport is ~925 x ~525.
VIEWPORTS = [
    ("gm-100",       1850, 1050, 1),   # user's actual viewport, 100% zoom
    ("gm-200",        925,  525, 1),   # user's actual viewport, 200% zoom
    ("tablet",        800, 1100, 1),
    ("mobile",        390,  844, 2),
]

PAGES = [
    ("index",  "/index.html"),
    ("detail", "/relic.html?slug=honest-masu-of-yasuki-bunzo"),
]


async def shoot():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for page_name, page_url in PAGES:
            for label, w, h, dsf in VIEWPORTS:
                context = await browser.new_context(
                    viewport={"width": w, "height": h},
                    device_scale_factor=dsf,
                )
                page = await context.new_page()
                await page.goto(BASE + page_url, wait_until="networkidle")
                # Wait a bit for fonts and animations to settle
                await page.wait_for_timeout(800)
                # Full-page screenshot
                out = OUT / f"{page_name}-{label}.png"
                await page.screenshot(path=str(out), full_page=True)
                print(f"  -> {out}")
                # Also above-the-fold
                out2 = OUT / f"{page_name}-{label}-fold.png"
                await page.screenshot(path=str(out2), full_page=False)
                print(f"  -> {out2}")
                await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(shoot())
