"""Build the data the bot ships with: the link roster and the player profiles.

    python3 -m l7r.lookup.bake

Runs on the GM's machine (or this container), never on the box, because it
needs two credentials the box deliberately does not hold: Obsidian Portal OAuth
(for the character listing, with its GM-only flags) and the character sheet's
bearer token (for which Discord account owns which character). The deploy
script runs it, so the box always gets a roster as fresh as the deploy.

Writes `l7r/lookup/data/roster.json` and `profiles.json` (both gitignored).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from l7r.lookup import links, profiles
from l7r.lookup.service import DATA, load_settings

#: Known slips in Obsidian Portal taglines, fixed on the way into the glossary
#: (CLAUDE.md's silent-fix list, plus two found in the 2026-10-17 tagline pull).
_TAGLINE_FIXES = {'chancellary': 'chancellery', 'Soverign': 'Sovereign', 'Kitune': 'Kitsune'}


def person_entries(
    op_characters: Iterable[Mapping[str, Any]], taglines: Mapping[str, str]
) -> list[dict[str, Any]]:
    """A glossary line for every player-visible Obsidian Portal character.

    Built from what a player can see on the character's page: the one-line
    tagline and the tags (clan, lineage, office, where they are posted). Baked
    at deploy time rather than written by hand, so an NPC the GM adds on Monday
    is answerable after the next deploy without a Claude session."""
    rows: list[dict[str, Any]] = []
    for c in op_characters:
        if c.get('is_game_master_only') or not c.get('name'):
            continue
        tagline = str(taglines.get(str(c.get('slug', '')), '')).strip()
        for wrong, right in _TAGLINE_FIXES.items():
            tagline = tagline.replace(wrong, right)
        tags = [str(t) for t in c.get('tags') or []]
        parts = []
        if tagline:
            parts.append(tagline[0].upper() + tagline[1:] + '.')
        if tags:
            parts.append(f'Tags: {", ".join(tags)}.')
        rows.append(
            {
                'term': ' '.join(str(c['name']).split()),
                'kind': 'person',
                'scope': 'wasp',
                'summary': ' '.join(parts) or 'A character on the campaign wiki.',
                'link': str(c.get('character_url', '')),
                'source': {'file': 'obsidian-portal', 'section': f'characters/{c.get("slug", "")}'},
            }
        )
    return rows


def bake(
    op_characters: Iterable[Mapping[str, Any]],
    sheet_characters: Iterable[Mapping[str, Any]],
    groups: Iterable[str],
    fetch_page: Callable[[int], str],
    data: Path = DATA,
    taglines: Mapping[str, str] | None = None,
) -> tuple[list[links.Person], list[profiles.Profile]]:
    op_characters = list(op_characters)
    built = profiles.build(sheet_characters, groups, fetch_page)
    people = links.roster(op_characters, [(p.name, p.sheet_url) for p in built])
    data.mkdir(parents=True, exist_ok=True)
    (data / 'people.jsonl').write_text(
        ''.join(
            json.dumps(r, ensure_ascii=False) + '\n'
            for r in person_entries(op_characters, taglines or {})
        ),
        encoding='utf-8',
    )
    (data / 'roster.json').write_text(
        json.dumps([{'name': p.name, 'url': p.url} for p in people], indent=1, ensure_ascii=False)
        + '\n',
        encoding='utf-8',
    )
    (data / 'profiles.json').write_text(
        json.dumps([p.to_json() for p in built], indent=1, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )
    return people, built


Sources = tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]


def _sources() -> Sources:  # pragma: no cover - network and credentials only
    """The live listings and taglines. `bake` holds all the logic.

    Taglines come through the authenticated browser session because Obsidian
    Portal shows anonymous clients a human check; the tagline itself is a public
    field every player sees on the page."""
    from concurrent.futures import ThreadPoolExecutor

    import requests

    import l7r.app  # noqa: F401 - chargen's package import needs the app imported first
    from chargen import op, opsynth, sheetroster

    token = sheetroster.query_token()
    if not token:
        raise SystemExit('no [character_sheet] roll_query_token in development-secrets.ini')
    response = requests.get(
        sheetroster.API_URL, headers={'Authorization': f'Bearer {token}'}, timeout=20
    )
    response.raise_for_status()
    op_characters = list(op.existing_characters())  # type: ignore[no-untyped-call]
    visible = [c for c in op_characters if not c.get('is_game_master_only')]

    def tagline(c: dict[str, Any]) -> tuple[str, str]:
        page = op.fetch_character_page(c['character_url']) or ''
        return str(c['slug']), opsynth.parse_tagline(page)

    with ThreadPoolExecutor(4) as pool:
        taglines = dict(pool.map(tagline, visible))
    return op_characters, list(response.json()['characters']), taglines


def main(
    *,
    sources: Callable[[], Sources] = _sources,
    fetch_page: Callable[[int], str] = profiles.fetch_page,
    data: Path = DATA,
    out: Callable[[str], None] = print,
) -> int:
    settings, _ = load_settings()
    op_characters, sheet_characters, taglines = sources()
    people, built = bake(
        op_characters, sheet_characters, settings.groups, fetch_page, data, taglines
    )
    out(f'roster: {len(people)} people; profiles: {len(built)} PCs in {", ".join(settings.groups)}')
    for p in built:
        out(f'  {p.name}: {p.school or "?"} {p.dan or "?"} Dan, {p.clan_of_origin or "no clan"}')
    return 0


if __name__ == '__main__':  # pragma: no cover - the CLI entry point
    sys.exit(main())
