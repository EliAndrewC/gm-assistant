"""robots.txt parsing for the one host the census talks to (www.obsidianportal.com).

Deliberately minimal: the `*` group's `Crawl-delay`, `Allow` and `Disallow` lines, with the
longest-match rule and a `*` wildcard, which is all Obsidian Portal's file uses. Recorded on
2026-08-27 (`RECORDED`) so the census can fail closed when the file changes under us.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RobotsPolicy:
    crawl_delay: float | None
    allow: tuple[str, ...]
    disallow: tuple[str, ...]

    def allows(self, path: str) -> bool:
        """Longest-match rule (RFC 9309): the most specific pattern wins, Allow on ties."""
        best_len, best_ok = -1, True
        for patterns, ok in ((self.allow, True), (self.disallow, False)):
            for pattern in patterns:
                if _matches(pattern, path) and (
                    len(pattern) > best_len or (len(pattern) == best_len and ok)
                ):
                    best_len, best_ok = len(pattern), ok
        return best_ok


# What www.obsidianportal.com/robots.txt said on 2026-08-27. `Crawl-delay: 20` is the floor the
# census never goes under even if the live file drops it; a live file that RAISES it wins.
RECORDED = RobotsPolicy(
    crawl_delay=20.0,
    allow=('/',),
    disallow=('/messages/', '/friends', '/login?*', '/oauth*', '/profile/*', '/pre-human-check?*'),
)


def _matches(pattern: str, path: str) -> bool:
    regex = '^' + '.*'.join(re.escape(part) for part in pattern.split('*'))
    return re.match(regex, path) is not None


def parse_robots(text: str, agent: str = '*') -> RobotsPolicy:
    """The policy for `agent` (exact token match), falling back to the `*` group."""
    groups: dict[str, dict[str, list[str]]] = {}
    current: list[str] = []
    saw_rule = True
    for raw in text.splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line or ':' not in line:
            continue
        key, _, value = (s.strip() for s in line.partition(':'))
        key = key.lower()
        if key == 'user-agent':
            if saw_rule:
                current = []
                saw_rule = False
            current.append(value.lower())
            groups.setdefault(value.lower(), {'allow': [], 'disallow': [], 'delay': []})
            continue
        saw_rule = True
        for ua in current:
            if key in ('allow', 'disallow') and value:
                groups[ua][key].append(value)
            elif key == 'crawl-delay':
                groups[ua]['delay'].append(value)
    group = (
        groups.get(agent.lower()) or groups.get('*') or {'allow': [], 'disallow': [], 'delay': []}
    )
    delay = float(group['delay'][0]) if group['delay'] else None
    return RobotsPolicy(delay, tuple(group['allow']), tuple(group['disallow']))
