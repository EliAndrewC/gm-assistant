"""The glossary: what the lookup model knows, one entry per line.

Claude writes `glossary.jsonl` in a Claude Code session (the GM: "I should just
have you build the glossary. And then Gemini is handed the glossary."). This
module loads it, refuses a malformed line with the line number, and renders it
as compact text for the prompt - one line per entry, so JSON key names do not
cost tokens on every question.

THE IN/OUT RULE, which every entry must satisfy (GM 2026-10-17): anything a
player might need to NAME or RECOGNIZE is in - institutions ("the Ministry of
Retainers should be something in the glossary"), offices, ranks, clans, people,
places, vocabulary, rule terms. Hyper-specific numbers and procedures are out
even when their term is in ("the budget of a county magistrate should not, even
if the term 'county magistrate' is").
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

PATH = Path(__file__).resolve().parent / 'glossary.jsonl'

KINDS = frozenset(
    {
        'clan',
        'creature',
        'event',
        'family',
        'festival',
        'fortune',
        'group',
        'institution',
        'item',
        'office',
        'person',
        'place',
        'rank',
        'rule',
        'term',
    }
)

#: `wasp` and `world` are the two scopes a Wasp player's question is about.
#: Everything else in `l7r.md` belongs to another table's campaign. It stays in
#: the glossary, tagged, because the GM ruled l7r.md is not out of bounds - the
#: tag is what stops it being mistaken for Wasp fact.
SCOPES = frozenset(
    {
        'wasp',
        'world',
        'damasu',
        'first-toshi-ranbo',
        'hidden-way',
        'karmic-inquisitors',
        'peasant',
    }
)

#: Rendering order: what the asker's campaign is about comes first.
_SCOPE_ORDER = {'wasp': 0, 'world': 1}

_REQUIRED = ('term', 'kind', 'scope', 'summary', 'source')


class GlossaryError(ValueError):
    """A glossary line that cannot be used, with where it is."""


@dataclass(frozen=True)
class Source:
    file: str
    section: str


@dataclass(frozen=True)
class Entry:
    term: str
    kind: str
    scope: str
    summary: str
    source: Source
    aliases: tuple[str, ...] = ()
    reading: str = ''
    meaning: str = ''
    related: tuple[str, ...] = ()
    link: str = ''


def _strings(value: object, field: str, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise GlossaryError(f'{where}: {field} must be a list of non-empty strings')
    return tuple(value)


def _text(raw: dict[str, object], field: str, where: str) -> str:
    value = raw.get(field, '')
    if not isinstance(value, str):
        raise GlossaryError(f'{where}: {field} must be a string')
    return value.strip()


def parse(raw: object, where: str) -> Entry:
    """One decoded JSON line as an Entry, or a GlossaryError saying why not."""
    if not isinstance(raw, dict):
        raise GlossaryError(f'{where}: not a JSON object')
    for field in _REQUIRED:
        if not raw.get(field):
            raise GlossaryError(f'{where}: missing {field}')
    kind = _text(raw, 'kind', where)
    if kind not in KINDS:
        raise GlossaryError(f'{where}: unknown kind {kind!r}; known: {", ".join(sorted(KINDS))}')
    scope = _text(raw, 'scope', where)
    if scope not in SCOPES:
        raise GlossaryError(
            f'{where}: unknown scope {scope!r}; add it to glossary.SCOPES if it is a campaign'
        )
    link = _text(raw, 'link', where)
    if link and not link.startswith(('https://', 'http://')):
        raise GlossaryError(f'{where}: link must be an http(s) address, got {link!r}')
    source = raw['source']
    if not isinstance(source, dict) or not source.get('file') or not source.get('section'):
        raise GlossaryError(f'{where}: source must be {{"file": ..., "section": ...}}')
    return Entry(
        term=_text(raw, 'term', where),
        kind=kind,
        scope=scope,
        summary=_text(raw, 'summary', where),
        source=Source(str(source['file']), str(source['section'])),
        aliases=_strings(raw.get('aliases', []), 'aliases', where),
        reading=_text(raw, 'reading', where),
        meaning=_text(raw, 'meaning', where),
        related=_strings(raw.get('related', []), 'related', where),
        link=link,
    )


def loads(text: str, name: str = 'glossary.jsonl') -> list[Entry]:
    """Every entry in `text`. Blank lines are allowed; anything else must parse.

    A term may appear once per scope: the same word can mean one thing in the
    world and another in a campaign, but two `world` entries for one term is a
    merge that was never finished."""
    entries: list[Entry] = []
    seen: dict[tuple[str, str], int] = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        where = f'{name}:{number}'
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GlossaryError(f'{where}: not JSON ({exc.msg})') from None
        entry = parse(raw, where)
        key = (entry.term.casefold(), entry.scope)
        if key in seen:
            raise GlossaryError(
                f'{where}: {entry.term!r} ({entry.scope}) already defined on line {seen[key]}'
            )
        seen[key] = number
        entries.append(entry)
    return entries


def load(path: Path = PATH) -> list[Entry]:
    return loads(path.read_text(encoding='utf-8'), path.name)


def merge(primary: list[Entry], extra: list[Entry]) -> list[Entry]:
    """`primary` plus each `extra` entry whose name `primary` does not already cover.

    The hand-written glossary is primary; the people entries baked from
    Obsidian Portal are extra. A person Claude wrote up by hand (Tsuruchi Kyoma)
    keeps the hand entry, and every other public NPC still gets one."""
    names = {n.casefold() for e in primary for n in (e.term, *e.aliases)}
    return primary + [e for e in extra if e.term.casefold() not in names]


def links(entries: list[Entry]) -> frozenset[str]:
    """Every address the glossary vouches for - the link filter's allow-list."""
    return frozenset(e.link for e in entries if e.link)


def line(entry: Entry) -> str:
    """One entry as one prompt line: term (aliases; reading "meaning") [kind, scope]: ..."""
    head = entry.term
    extras = list(entry.aliases)
    if entry.reading or entry.meaning:
        gloss = entry.reading
        if entry.meaning:
            gloss = f'{gloss} "{entry.meaning}"'.strip()
        extras.append(gloss)
    if extras:
        head += f' ({"; ".join(extras)})'
    text = f'{head} [{entry.kind}, {entry.scope}]: {entry.summary}'
    if entry.related:
        text += f' Related: {", ".join(entry.related)}.'
    if entry.link:
        text += f' Link: {entry.link}'
    return text


def render(entries: list[Entry]) -> str:
    """The whole glossary as prompt text, Wasp first, then the world, then the rest.

    Stable order (scope, then file order) so the prompt prefix is identical from
    one question to the next, which is what Gemini's implicit caching keys on."""
    ordered = sorted(enumerate(entries), key=lambda p: (_SCOPE_ORDER.get(p[1].scope, 2), p[0]))
    return '\n'.join(line(e) for _, e in ordered)
