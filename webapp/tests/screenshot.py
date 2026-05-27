"""Take screenshots of the live L7R Toolkit at multiple viewports.

Assumes `cherryd --import l7r` is running at http://127.0.0.1:8080/.
"""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

BASE = 'http://127.0.0.1:8080'
OUT = Path('/tmp/l7r-shots')
OUT.mkdir(exist_ok=True)

VIEWPORTS = [
    ('gm-100', 1850, 1050, 1),
    ('gm-200', 925, 525, 1),
    ('tablet', 800, 1100, 1),
    ('mobile', 390, 844, 2),
]

PAGES = [
    ('landing', '/'),
    ('relics', '/relics'),
    ('relic-detail', '/relics/basin-of-the-lapping-wave'),
    ('chargen', '/chargen/'),
    ('names', '/names'),
]


async def shoot() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for page_name, page_url in PAGES:
            for label, w, h, dsf in VIEWPORTS:
                context = await browser.new_context(
                    viewport={'width': w, 'height': h},
                    device_scale_factor=dsf,
                )
                page = await context.new_page()
                await page.goto(BASE + page_url, wait_until='networkidle')
                await page.wait_for_timeout(800)
                out = OUT / f'{page_name}-{label}.png'
                await page.screenshot(path=str(out), full_page=True)
                print(f'  -> {out}')
                await context.close()
        await browser.close()


if __name__ == '__main__':
    asyncio.run(shoot())
