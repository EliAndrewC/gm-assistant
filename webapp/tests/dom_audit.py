"""DOM-overflow audit. Checks every element for clip/truncation problems.

Reports:
 - elements whose scrollWidth > offsetWidth (horizontal overflow)
 - elements whose scrollHeight > offsetHeight (vertical clip without scroll)
 - elements with text-overflow:ellipsis that ARE truncating
 - elements with -webkit-line-clamp truncating
Per Constitution Principle I.
"""

import asyncio
import sys

from playwright.async_api import async_playwright

BASE = 'http://127.0.0.1:8080'

VIEWPORTS = [
    ('gm-100', 1850, 1050),
    ('gm-200', 925, 525),
    ('tablet', 800, 1100),
    ('mobile', 390, 844),
]

PAGES = [
    ('landing', '/'),
    ('relics', '/relics'),
    ('relic-detail', '/relics/basin-of-the-lapping-wave'),
    ('chargen', '/chargen/'),
    ('names', '/names'),
]

AUDIT_SCRIPT = r"""
() => {
    const issues = [];
    const els = document.querySelectorAll('*');
    for (const el of els) {
        if (el.tagName === 'HTML' || el.tagName === 'BODY' || el.tagName === 'SCRIPT' || el.tagName === 'STYLE') continue;
        const cs = getComputedStyle(el);
        // Skip elements that are explicitly scrollable (overflow auto/scroll) — those overflow with scrollbar, fine.
        const overflowX = cs.overflowX, overflowY = cs.overflowY;
        const scrollableX = overflowX === 'auto' || overflowX === 'scroll';
        const scrollableY = overflowY === 'auto' || overflowY === 'scroll';
        const w = el.offsetWidth, h = el.offsetHeight;
        if (!w || !h) continue;
        // Horizontal overflow without scroll allowance
        if (!scrollableX && el.scrollWidth > w + 1) {
            issues.push({tag: el.tagName, cls: el.className, id: el.id, kind: 'h-overflow', sw: el.scrollWidth, w});
        }
        // Vertical clip on elements with overflow:hidden (and not intentionally clipped via overflow)
        if (overflowY === 'hidden' && el.scrollHeight > h + 1 && !cs.webkitLineClamp) {
            issues.push({tag: el.tagName, cls: el.className, id: el.id, kind: 'v-clip', sh: el.scrollHeight, h});
        }
        // text-overflow: ellipsis with truncation
        if (cs.textOverflow === 'ellipsis' && (el.scrollWidth > w + 1)) {
            issues.push({tag: el.tagName, cls: el.className, id: el.id, kind: 'ellipsis-truncating', sw: el.scrollWidth, w});
        }
        // -webkit-line-clamp
        if (cs.webkitLineClamp && cs.webkitLineClamp !== 'none' && cs.webkitLineClamp !== '0') {
            // crude: if element has more rendered text than what would fit in the clamp height
            const clampN = parseInt(cs.webkitLineClamp, 10);
            if (clampN > 0) {
                const lh = parseFloat(cs.lineHeight) || (parseFloat(cs.fontSize) * 1.4);
                const expectedH = lh * clampN;
                if (el.scrollHeight > expectedH + 2) {
                    issues.push({tag: el.tagName, cls: el.className, id: el.id, kind: 'line-clamp-truncating', n: clampN, sh: el.scrollHeight});
                }
            }
        }
    }
    return issues;
}
"""


async def audit() -> int:
    total_issues = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for page_name, page_url in PAGES:
            for label, w, h in VIEWPORTS:
                context = await browser.new_context(viewport={'width': w, 'height': h})
                page = await context.new_page()
                await page.goto(BASE + page_url, wait_until='networkidle')
                await page.wait_for_timeout(500)
                issues = await page.evaluate(AUDIT_SCRIPT)
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
    print('\nNo overflow/clip issues found.')
