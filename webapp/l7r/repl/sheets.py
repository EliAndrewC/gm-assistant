"""Player characters and their public character sheets.

The PCs with the Discern Honor knack are registered here with their sheet on
<https://l7r-character-sheet.fly.dev/>. ``resolve_pc`` accepts every form
the GM might type - ``"Jimen"``, ``"Tsuruchi Jimen"``, ``"TSURUCHI_JIMEN"``,
``"TsuruchiJimen"`` - and the REPL also exposes each PC as constants
(``Jimen``, ``TsuruchiJimen``, ``JIMEN``, ``TSURUCHI_JIMEN``) that are the
same :class:`PC` object, so quoting is optional.

``knack_rank`` reads the knack's rank off the sheet (the filled dots after
the knack's label - the site has no JSON route, so this parses the HTML) and
caches it for 24 hours in ``webapp/opcache/`` (gitignored), because ranks
change rarely and the GM said a day-old reading is fine (2026-08-27).
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import requests

SHEET_BASE = 'https://l7r-character-sheet.fly.dev/characters/'
CACHE_PATH = Path(__file__).resolve().parent.parent.parent / 'opcache' / 'sheet-knacks.json'
CACHE_TTL = 24 * 3600.0


@dataclass(frozen=True)
class PC:
    """A player character with a public sheet. ``given`` is how the OP notes
    name them (the Discern Honor block's ``- Jimen`` line)."""

    name: str
    sheet_id: int

    @property
    def given(self) -> str:
        return self.name.split()[-1]

    @property
    def url(self) -> str:
        return f'{SHEET_BASE}{self.sheet_id}'

    @property
    def constants(self) -> dict[str, PC]:
        """The REPL names this PC answers to: Jimen, TsuruchiJimen, JIMEN,
        TSURUCHI_JIMEN."""
        parts = self.name.split()
        return {
            self.given: self,
            ''.join(parts): self,
            self.given.upper(): self,
            '_'.join(p.upper() for p in parts): self,
        }


#: The PCs who have Discern Honor (GM 2026-08-27). Add a line to add a PC.
PCS: tuple[PC, ...] = (
    PC('Tsuruchi Jimen', 3),
    PC('Tsuruchi Tetsuro', 18),
    PC('Tsuruchi Makoto', 16),
)


def _norm(text: str) -> str:
    return re.sub(r'[^a-z]', '', text.lower())


def resolve_pc(who: str | PC) -> PC | None:
    """The registered PC ``who`` names, by given name or full name in any
    spacing / casing / underscore form; None if unregistered."""
    if isinstance(who, PC):
        return who
    key = _norm(who)
    for pc in PCS:
        if key in (_norm(pc.given), _norm(pc.name)):
            return pc
    return None


def parse_knack_rank(html: str, knack: str) -> int | None:
    """Filled dots after ``knack``'s label on a sheet page, or None if the
    knack is not on the sheet."""
    label = f'<span class="font-medium">{knack}</span>'
    at = html.find(label)
    if at < 0:
        return None
    m = re.search(r'flex gap-0\.5">(.*?)</div>\s*</div>', html[at:], re.DOTALL)
    if not m:
        return None
    return m.group(1).count('bg-accent border-accent')


def parse_sheet_name(html: str) -> str:
    m = re.search(r'<title>\s*L7R - ([^<]*?)\s*</title>', html)
    return m.group(1) if m else ''


def _load_cache(path: Path) -> dict[str, dict[str, object]]:
    try:
        data = json.loads(path.read_text())
    except OSError, ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def fetch_sheet(pc: PC) -> str:
    response = requests.get(pc.url, timeout=20)
    response.raise_for_status()
    return str(response.text)


def knack_rank(
    pc: PC,
    knack: str = 'Discern Honor',
    *,
    max_age: float = CACHE_TTL,
    fetch: Callable[[PC], str] = fetch_sheet,
    cache_path: Path = CACHE_PATH,
    now: Callable[[], float] = time.time,
) -> int:
    """``pc``'s rank in ``knack`` from the sheet, via the 24 h cache."""
    cache = _load_cache(cache_path)
    key = f'{pc.sheet_id}:{knack}'
    entry = cache.get(key)
    if entry and now() - float(str(entry.get('at', 0))) < max_age:
        return int(str(entry['rank']))
    html = fetch(pc)
    rank = parse_knack_rank(html, knack)
    if rank is None:
        raise ValueError(f'{pc.name} has no {knack} on the sheet at {pc.url}')
    cache[key] = {'rank': rank, 'at': now(), 'name': parse_sheet_name(html)}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2))
    return rank
