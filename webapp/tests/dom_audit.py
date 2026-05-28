"""DOM audit for layout problems.

Checks every element for:
 - horizontal/vertical clipping
 - ellipsis truncation that's actually truncating
 - line-clamp truncation
 - **layout asymmetry**: in flex/grid containers, sibling height ratios that
   exceed the configured threshold (default 2.5×). This catches the failure
   mode where a 2-column layout has a short hero on the left and a tall
   stack on the right, producing huge dead space below the short side.

Per Constitution Principle I.

Set L7R_TEST_COOKIE / L7R_BASE_URL env vars to point at non-default targets.
"""

import asyncio
import os
import sys
from typing import Any

from playwright.async_api import async_playwright

BASE = os.environ.get('L7R_BASE_URL', 'http://127.0.0.1:8080')

# Maximum sibling-height ratio inside a flex/grid container before we flag it.
# A 2.5× ratio with 3+ siblings is the threshold where the layout starts to
# read as broken rather than intentional.
BALANCE_RATIO_LIMIT = 2.5
# Don't flag tiny absolute heights — a 10px-vs-30px ratio is 3× but harmless.
BALANCE_MIN_TALL_SIBLING_PX = 200

VIEWPORTS = [
    ('gm-100', 1850, 1050),
    ('gm-200', 925, 525),
    ('tablet', 800, 1100),
    ('mobile', 390, 844),
]

PAGES = [
    ('landing', '/', True),
    ('relics', '/relics', True),
    ('relic-detail', '/relics/basin-of-the-lapping-wave', True),
    ('chargen', '/chargen/', True),
    ('names', '/names', True),
    ('auth-login', '/auth/login', False),
    ('terms', '/terms', False),
    ('privacy', '/privacy', False),
]


AUDIT_SCRIPT = r"""
(opts) => {
    const issues = [];
    for (const el of document.querySelectorAll('*')) {
        if (['HTML','BODY','SCRIPT','STYLE'].includes(el.tagName)) continue;
        const cs = getComputedStyle(el);
        const overflowX = cs.overflowX, overflowY = cs.overflowY;
        const scrollableX = overflowX === 'auto' || overflowX === 'scroll';
        const w = el.offsetWidth, h = el.offsetHeight;
        if (!w || !h) continue;
        if (!scrollableX && el.scrollWidth > w + 1) {
            issues.push({tag: el.tagName, cls: (el.className||'').slice(0,80), kind: 'h-overflow', sw: el.scrollWidth, w});
        }
        if (overflowY === 'hidden' && el.scrollHeight > h + 1 && !cs.webkitLineClamp) {
            issues.push({tag: el.tagName, cls: (el.className||'').slice(0,80), kind: 'v-clip', sh: el.scrollHeight, h});
        }
        if (cs.textOverflow === 'ellipsis' && (el.scrollWidth > w + 1)) {
            issues.push({tag: el.tagName, cls: (el.className||'').slice(0,80), kind: 'ellipsis-truncating'});
        }
        if (cs.webkitLineClamp && cs.webkitLineClamp !== 'none' && cs.webkitLineClamp !== '0') {
            const clampN = parseInt(cs.webkitLineClamp, 10);
            if (clampN > 0) {
                const lh = parseFloat(cs.lineHeight) || (parseFloat(cs.fontSize) * 1.4);
                const expectedH = lh * clampN;
                if (el.scrollHeight > expectedH + 2) {
                    issues.push({tag: el.tagName, cls: (el.className||'').slice(0,80), kind: 'line-clamp-truncating'});
                }
            }
        }

        // Layout-balance: for flex/grid containers, check sibling-height ratio.
        // Only multi-column layouts are interesting (a vertical flex is supposed
        // to have heterogeneous children).
        const isFlex = cs.display === 'flex' || cs.display === 'inline-flex';
        const isGrid = cs.display === 'grid' || cs.display === 'inline-grid';
        const horizontalFlex = isFlex && (cs.flexDirection === 'row' || cs.flexDirection === 'row-reverse');
        const horizontalGrid = isGrid && (cs.gridTemplateColumns !== 'none' && !cs.gridTemplateColumns.startsWith('0px'));
        const isWideContainer = el.offsetWidth >= 600;
        if (!isWideContainer) continue;
        if (!(horizontalFlex || horizontalGrid)) continue;
        const children = Array.from(el.children).filter(c => c.offsetWidth > 0 && c.offsetHeight > 0);
        if (children.length < 2) continue;
        // Only flag when at least one child is visibly tall; tiny components naturally
        // vary a lot in ratio and aren't a layout problem.
        const heights = children.map(c => c.offsetHeight);
        const minH = Math.min(...heights);
        const maxH = Math.max(...heights);
        if (maxH < opts.minTallSibling) continue;
        if (minH === 0) continue;
        const ratio = maxH / minH;
        if (ratio > opts.ratioLimit) {
            issues.push({
                tag: el.tagName,
                cls: (el.className||'').slice(0,80),
                kind: 'layout-imbalance',
                ratio: Math.round(ratio * 10) / 10,
                minH, maxH,
                childCount: children.length,
            });
        }
    }
    return issues;
}
"""


def _session_cookie_for_eli() -> str | None:
    import configparser
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from l7r.auth import make_session_cookie

    ini = Path(__file__).resolve().parent.parent / 'development-secrets.ini'
    if not ini.exists():
        return None
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(ini, encoding='utf-8')
    secret = parser.get('auth', 'session_secret', fallback='')
    return make_session_cookie('183026066498125825', secret) if secret else None


async def audit() -> int:
    total_issues = 0
    cookie_value = _session_cookie_for_eli()
    opts = {'ratioLimit': BALANCE_RATIO_LIMIT, 'minTallSibling': BALANCE_MIN_TALL_SIBLING_PX}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for page_name, page_url, needs_auth in PAGES:
            for label, w, h in VIEWPORTS:
                context = await browser.new_context(viewport={'width': w, 'height': h})
                if needs_auth and cookie_value:
                    domain_host = (
                        BASE.replace('http://', '')
                        .replace('https://', '')
                        .split('/')[0]
                        .split(':')[0]
                    )
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
                await page.wait_for_timeout(500)
                issues = await page.evaluate(AUDIT_SCRIPT, opts)
                if issues:
                    total_issues += len(issues)
                    print(f'\n[{page_name} @ {label}] {len(issues)} issues:')
                    for issue in issues[:20]:
                        cls = (issue.get('cls') or '')[:80]
                        print(f'  {issue["kind"]:<22} <{issue["tag"]} class="{cls}"> {issue}')
                    if len(issues) > 20:
                        print(f'  ... and {len(issues) - 20} more')
                else:
                    print(f'[{page_name} @ {label}] OK')
                await context.close()
        await browser.close()
    return total_issues


if __name__ == '__main__':
    n = asyncio.run(audit())
    if n:
        print(f'\nTOTAL ISSUES: {n}')
        sys.exit(1)
    print('\nNo layout issues found.')
