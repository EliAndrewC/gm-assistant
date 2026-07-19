"""Take screenshots of the live L7R Toolkit at multiple viewports.

For pages taller than 1.3× viewport height, captures four scroll positions
(0% / 33% / 66% / 100%) and stitches them into a per-page contact sheet so
issues mid-scroll (layout asymmetry, dead space, awkward stacking) are
visible at a glance.

The contact sheet is the Principle I verification artifact - UI changes
are not "done" until a contact sheet has been reviewed at the GM's viewport.

Assumes `cherryd --import l7r` is running at http://127.0.0.1:8080/.

To capture authenticated pages, set L7R_TEST_COOKIE to a valid session cookie
value (see tests/_session_cookie.py for the helper).
"""

import asyncio
import os
from pathlib import Path
from typing import Any

from PIL import Image
from playwright.async_api import Page, async_playwright

BASE = os.environ.get('L7R_BASE_URL', 'http://127.0.0.1:8080')
OUT = Path('/tmp/l7r-shots')
OUT.mkdir(exist_ok=True)

VIEWPORTS = [
    ('gm-100', 1850, 1050, 1),
    ('gm-200', 925, 525, 1),
    ('tablet', 800, 1100, 1),
    ('mobile', 390, 844, 2),
]

PAGES = [
    ('landing', '/', True),
    ('relics', '/relics', True),
    ('relic-detail', '/relics/basin-of-the-lapping-wave', True),
    ('chargen', '/chargen/', True),
    ('names', '/names', True),
    ('names-picked', '/names?picked=male-hiroshi', True),
    ('places', '/places', True),
    ('place-detail', '/places/owari?via=random', True),
    ('dreams', '/dreams', True),
    ('dream-detail', '/dreams/daikoku-masamune-sword-akishi', True),
    ('auth-login', '/auth/login', False),
    ('terms', '/terms', False),
    ('privacy', '/privacy', False),
]

SCROLL_FRACTIONS = (0.0, 0.33, 0.66, 1.0)


async def _capture_scroll_positions(
    page: Page, label: str, viewport_h: int
) -> tuple[list[Path], bool]:
    """Capture viewport-sized screenshots at scroll positions 0/33/66/100%.

    Returns (paths, multi_scroll_was_needed). If the page is shorter than
    1.3× viewport, only one screenshot is captured.
    """
    page_height = await page.evaluate('document.documentElement.scrollHeight')
    paths: list[Path] = []
    if page_height < viewport_h * 1.3:
        out = OUT / f'{label}-fold.png'
        await page.screenshot(path=str(out), full_page=False)
        paths.append(out)
        return paths, False
    for frac in SCROLL_FRACTIONS:
        target = (page_height - viewport_h) * frac
        await page.evaluate(f'window.scrollTo(0, {target})')
        await page.wait_for_timeout(250)
        out = OUT / f'{label}-scroll-{int(frac * 100):03d}.png'
        await page.screenshot(path=str(out), full_page=False)
        paths.append(out)
    return paths, True


def _stitch_contact_sheet(paths: list[Path], out: Path) -> None:
    """Combine N viewport-sized PNGs into a single horizontal contact sheet."""
    imgs = [Image.open(p) for p in paths]
    w_total = sum(i.width for i in imgs) + (len(imgs) - 1) * 8
    h_max = max(i.height for i in imgs)
    sheet = Image.new('RGB', (w_total, h_max), color=(244, 232, 204))
    x = 0
    for img in imgs:
        sheet.paste(img, (x, 0))
        x += img.width + 8
    sheet.save(out, optimize=True)


def _session_cookie_for_eli() -> str | None:
    """Build a valid session cookie for the GM Eli, or None if not configured."""
    import configparser
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from l7r.auth import make_session_cookie

    ini = Path(__file__).resolve().parent.parent / 'development-secrets.ini'
    if not ini.exists():
        return None
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(ini, encoding='utf-8')
    secret = parser.get('auth', 'session_secret', fallback='')
    if not secret:
        return None
    return make_session_cookie('183026066498125825', secret)


async def shoot() -> None:
    cookie_value = _session_cookie_for_eli()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for page_name, page_url, needs_auth in PAGES:
            for label, w, h, dsf in VIEWPORTS:
                ctx_args: dict[str, Any] = {
                    'viewport': {'width': w, 'height': h},
                    'device_scale_factor': dsf,
                }
                context = await browser.new_context(**ctx_args)
                if needs_auth and cookie_value:
                    domain = BASE.replace('http://', '').replace('https://', '').split('/')[0]
                    domain_host = domain.split(':')[0]
                    cookie: dict[str, Any] = {
                        'name': 'l7r_session',
                        'value': cookie_value,
                        'domain': domain_host,
                        'path': '/',
                    }
                    if BASE.startswith('https://'):
                        cookie['secure'] = True
                    await context.add_cookies([cookie])  # type: ignore[list-item]
                page = await context.new_page()
                await page.goto(BASE + page_url, wait_until='networkidle')
                await page.wait_for_timeout(600)
                paths, multi = await _capture_scroll_positions(page, f'{page_name}-{label}', h)
                if multi:
                    sheet = OUT / f'sheet-{page_name}-{label}.png'
                    _stitch_contact_sheet(paths, sheet)
                    print(f'  -> {sheet}  ({len(paths)} scroll positions)')
                else:
                    print(f'  -> {paths[0]}  (fits in one viewport)')
                await context.close()
        await browser.close()


if __name__ == '__main__':
    asyncio.run(shoot())
