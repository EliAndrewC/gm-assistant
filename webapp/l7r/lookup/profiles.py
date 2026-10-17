"""Who is asking: the asker's Wasp character, so "who is our boss?" has an "our".

The GM: "make sure that the player sending the command ... the model knows
which character that is." The character-sheet app knows which Discord account
owns which character (`owner_discord_id` on its authenticated `/api/characters`);
school, Dan and lineage are only on each character's PUBLIC sheet page.

Two halves, split by where they run:

- `build` runs at DEPLOY time, on the GM's machine, with the sheet's bearer
  token. It produces the baked `profiles.json` the bot ships with.
- `refresh` runs ON THE BOX, from the public sheet page only, so a PC who
  changes school or gains a Dan is current within the hour without the box ever
  holding the token (which reads every character, NPCs included).

CLAN OF ORIGIN is inferred from the school, as the GM directed: "anyone with a
Lion Clan school came from the Lion Clan prior to being a Wasp". A school
belongs to the clan of the family that names it. A generic school (Courtier,
Merchant, Priest, Shugenja, the Brotherhood) says nothing about a clan, so the
profile says the clan of origin is not recorded rather than guessing.
"""

from __future__ import annotations

import contextlib
import html
import re
import time
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass, replace
from typing import Any

from l7r.mention.lore.topics import CLAN_FAMILIES

SHEET_URL = 'https://l7r-character-sheet.fly.dev/characters/{id}'

#: Families that name a school but are not in the Great Clans table, from the
#: non-PC schools (rules/11-non_pc_schools.md) and the Wasp's own house.
MINOR_FAMILIES: dict[str, str] = {
    'Kitsune': 'Fox',
    'Suzume': 'Sparrow',
    'Mantis': 'Mantis',
    'Tsuruchi': 'Wasp',
    'Hantei': 'Imperial',
}

#: Schools that belong to no clan. Listed rather than inferred from "no family
#: matched", so a misspelled family is a test failure and not a silent shrug.
GENERIC_SCHOOLS = frozenset(
    {'Brotherhood of Shinsei Monk', 'Courtier', 'Merchant', 'Priest', 'Shugenja', 'Bloodspeaker'}
)

#: How long a public-page refresh is trusted before the box fetches it again.
REFRESH_SECONDS = 3600.0


def family_clans() -> dict[str, str]:
    """Family name -> clan name, derived from the one Great Clan table plus the minors."""
    table = {fam: clan.capitalize() for clan, fams in CLAN_FAMILIES.items() for fam in fams}
    table.update(MINOR_FAMILIES)
    return table


def clan_of_school(school: str) -> str | None:
    """The clan a school's family belongs to, or None for a clanless school.

    Raises ValueError for a school that is neither, so a new school added to the
    rules cannot fall through to "no clan" unnoticed."""
    if school in GENERIC_SCHOOLS:
        return None
    first = school.split()[0] if school else ''
    clan = family_clans().get(first)
    if clan is None:
        raise ValueError(f'no clan known for the school {school!r}')
    return clan


@dataclass(frozen=True)
class Profile:
    discord_id: str
    sheet_id: int
    name: str
    group: str
    school: str = ''
    dan: int = 0
    lineage: str = ''
    player: str = ''

    @property
    def sheet_url(self) -> str:
        return SHEET_URL.format(id=self.sheet_id)

    @property
    def clan_of_origin(self) -> str | None:
        try:
            return clan_of_school(self.school) if self.school else None
        except ValueError:
            return None

    def describe(self) -> str:
        """The profile as a few prompt lines."""
        parts = [f'{self.name} (character sheet {self.sheet_url})']
        if self.player:
            parts.append(f'played by {self.player}')
        if self.school:
            parts.append(
                f'{self.school} school' + (f', {_ordinal(self.dan)} Dan' if self.dan else '')
            )
        if self.lineage:
            parts.append(self.lineage)
        # Worded as what the school SHOWS, not as "joined the Wasp from X": not every
        # PC at a Wasp table is a Wasp (Kitsune Moriko is a Fox, l7r.md says so), and
        # the notes, not this line, are what say who belongs to which clan.
        origin = self.clan_of_origin
        parts.append(
            f'trained in a {origin} school, so originally of the {origin} Clan'
            if origin
            else 'clan of origin not recorded'
        )
        parts.append(f'plays in the {self.group}')
        return '; '.join(parts) + '.'

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def from_json(raw: Mapping[str, Any]) -> Profile:
    return Profile(**{k: raw[k] for k in Profile.__dataclass_fields__ if k in raw})


def _ordinal(n: int) -> str:
    suffix = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f'{n}{suffix}'


_SCHOOL = re.compile(r'<h2 class="text-xl font-bold text-accent shrink-0">\s*([^<]+?)\s*</h2>')
_DAN = re.compile(r'>\s*(\d+)(?:st|nd|rd|th) Dan\s*<')
_HEADER = re.compile(r'<p class="text-ink/60">(.*?)</p>', re.DOTALL)
_TOOLTIP = re.compile(r'<span class="tooltip-content.*?</span>', re.DOTALL)
_TAGS = re.compile(r'<[^>]+>')


def parse_sheet(page: str) -> dict[str, Any]:
    """School, Dan, lineage and player from a public sheet page; absent ones omitted."""
    found: dict[str, Any] = {}
    if school := _SCHOOL.search(page):
        found['school'] = html.unescape(school.group(1))
    if dan := _DAN.search(page):
        found['dan'] = int(dan.group(1))
    if header := _HEADER.search(page):
        text = html.unescape(_TAGS.sub(' ', _TOOLTIP.sub('', header.group(1))))
        for piece in (p.strip() for p in text.split('·')):
            words = ' '.join(piece.split())
            if words.startswith('Player:'):
                found['player'] = words.removeprefix('Player:').strip()
            elif words.endswith('lineage'):
                found['lineage'] = words
    return found


def build(
    characters: Iterable[Mapping[str, Any]],
    groups: Iterable[str],
    fetch_page: Callable[[int], str],
) -> list[Profile]:
    """Profiles for every non-NPC character in the campaign's gaming groups.

    `characters` is the sheet API's `characters` list. A page that cannot be
    fetched still yields a profile (name and group are enough to answer "our"),
    just without school and Dan."""
    wanted = set(groups)
    out: list[Profile] = []
    for c in characters:
        if c.get('is_npc') or c.get('gaming_group_name') not in wanted:
            continue
        if not c.get('owner_discord_id'):
            continue
        base = Profile(
            discord_id=str(c['owner_discord_id']),
            sheet_id=int(c['id']),
            name=' '.join(str(c['name']).split()),
            group=str(c['gaming_group_name']),
        )
        # Without the page the profile is still useful: name and group answer "our".
        with contextlib.suppress(Exception):
            base = replace(base, **parse_sheet(fetch_page(base.sheet_id)))
        out.append(base)
    return out


def fetch_page(sheet_id: int, opener: Callable[..., Any] = urllib.request.urlopen) -> str:
    request = urllib.request.Request(
        SHEET_URL.format(id=sheet_id), headers={'User-Agent': 'L7RLookup (gm-assistant)'}
    )
    with opener(request, timeout=10) as response:
        return str(response.read().decode('utf-8'))


class Profiles:
    """The baked profiles, kept fresh from the public pages, looked up by Discord id."""

    def __init__(
        self,
        profiles: Iterable[Profile],
        *,
        fetch: Callable[[int], str] = fetch_page,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._profiles = list(profiles)
        self._fetch = fetch
        self._clock = clock
        self._fresh: dict[int, float] = {}

    def __len__(self) -> int:
        return len(self._profiles)

    @property
    def all(self) -> list[Profile]:
        return list(self._profiles)

    def for_discord(self, discord_id: str) -> list[Profile]:
        """Every campaign character this account owns, each refreshed if it is stale.

        All of them, not a guess at one: a player with two Wasp PCs gets both
        described, and the model can tell from the question which is meant."""
        out: list[Profile] = []
        for i, p in enumerate(self._profiles):
            if p.discord_id != discord_id:
                continue
            last = self._fresh.get(p.sheet_id)
            if last is None or self._clock() - last >= REFRESH_SECONDS:
                try:
                    p = replace(p, **parse_sheet(self._fetch(p.sheet_id)))
                    self._profiles[i] = p
                except Exception:  # noqa: BLE001 - the baked profile is the fallback
                    pass
                self._fresh[p.sheet_id] = self._clock()
            out.append(p)
        return out
