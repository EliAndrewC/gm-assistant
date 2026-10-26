"""An Obsidian Portal character's raw facts, for the character-sheet app (gm-assistant#4).

The sheet app builds a combat NPC from an Obsidian Portal record: name, earned XP, traits,
recorded numbers and the school. It cannot read Obsidian Portal, so `GET /api/op-character`
(`l7r.app.NamesApi`) hands it the facts as written, and EVERY game interpretation - which line is
a real advantage, which school becomes which NPC type - stays on the sheet's side, where its NPC
type ids and its trait / stat matchers live.

- `school_line` is read from the SINGLE-character fetch's `description`: the campaign listing
  returns every description empty (measured 2026-10-26: 0 of 203), and the opcache keeps none.
- `trait_lines` is the first paragraph after the `XP:` / `Honor:` lines, unfiltered. Measured
  2026-10-26 over the 196 cached records with an `XP:` line: in 186 it is the trait list, and in
  the rest it is either a trait list with a colon or digit in a line (`Poor - ... twenty-second`)
  or not traits at all (Kyoma's etiquette notes, Souma's `Jimen discern honor: 4.0`). No test
  separates those two without dropping real traits, so the sheet's matcher, which already sorts
  advantages from flavor, sees the paragraph as written.

PURE apart from the injected Obsidian Portal callables, the way `npcbackport.backport` takes them.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from chargen.opsynth import match_character
from l7r.repl.rolls import npcnumbers

_SCHOOL = re.compile(r'^(?:male|female)\s+\S.*$', re.IGNORECASE)
_XP = re.compile(r'^XP:\s*(\d+)\s*$', re.IGNORECASE)
_HEADER = re.compile(r'^(?:XP|Honor):', re.IGNORECASE)
#: `https://<campaign>.obsidianportal.com/characters/<slug>` (with or without a trailing part).
_URL = re.compile(r'obsidianportal\.com/characters/([^/?#\s]+)', re.IGNORECASE)


class NotFound(LookupError):
    """No record answers to the ref."""


class Ambiguous(LookupError):
    """A name matched several records; `candidates` are their names."""

    def __init__(self, ref: str, candidates: list[str]) -> None:
        super().__init__(f'{ref} matches several Obsidian Portal records: {", ".join(candidates)}')
        self.candidates = candidates


def _lines(text: str) -> list[str]:
    return text.replace('\r\n', '\n').replace('\r', '\n').split('\n')


def school_line(description: str) -> str | None:
    """The `<male|female> <school>` line of the public description, or None."""
    for line in _lines(description):
        if _SCHOOL.match(line.strip()):
            return line.strip()
    return None


def earned_xp(gm_info: str) -> int | None:
    """GM info's `XP: N` - EARNED XP, unchanged - or None."""
    for line in _lines(gm_info):
        found = _XP.match(line.strip())
        if found:
            return int(found.group(1))
    return None


def trait_lines(gm_info: str) -> list[str]:
    """The first paragraph after the `XP:` / `Honor:` lines; empty when there are none.

    It stops at the first blank line, so a later block (`NPC numbers:`, `Discern Honor:`, prose)
    never leaks in. A record with no `XP:` / `Honor:` header has no trait list to point at.
    """
    lines = _lines(gm_info)
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines) or not _HEADER.match(lines[i].strip()):
        return []
    while i < len(lines) and _HEADER.match(lines[i].strip()):
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    out: list[str] = []
    while i < len(lines) and lines[i].strip():
        if lines[i].strip() == npcnumbers.HEADING:
            break
        out.append(lines[i].strip())
        i += 1
    return out


def stat_lines(gm_info: str) -> list[str]:
    """The lines under `NPC numbers:`, exactly as written."""
    lines = _lines(gm_info)
    for i, line in enumerate(lines):
        if line.strip() == npcnumbers.HEADING:
            out = []
            for entry in lines[i + 1 :]:
                if not entry.strip():
                    break
                out.append(entry.rstrip())
            return out
    return []


def _tags(raw: object) -> list[str]:
    return [str(t) for t in raw] if isinstance(raw, (list, tuple)) else []


def resolve(ref: str, roster: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    """The one record `ref` names: an Obsidian Portal URL, a slug, or a name."""
    found = _URL.search(ref)
    slug = found.group(1) if found else ref.strip()
    for char in roster:
        if str(char.get('slug', '')) == slug:
            return char
    if found:
        raise NotFound(f'no Obsidian Portal record at {ref}')
    match = match_character(ref, roster)
    if match.kind == 'ambiguous':
        raise Ambiguous(ref, [str(c.get('name', '')) for c in match.matches])
    if match.kind == 'none':
        raise NotFound(f'no Obsidian Portal record for {ref}')
    return match.character


def facts(
    ref: str,
    *,
    characters: Callable[[], Sequence[Mapping[str, object]]],
    get_body: Callable[[str], Mapping[str, object] | None],
) -> dict[str, Any]:
    """The raw facts for `ref`. Raises NotFound / Ambiguous, and LookupError when Obsidian
    Portal cannot be read (an empty listing is what `op.existing_characters` answers then)."""
    roster = characters()
    if not roster:
        raise LookupError('could not list the Obsidian Portal characters')
    char = resolve(ref, roster)
    body = get_body(str(char.get('id', '')))
    if body is None:
        raise LookupError(f'could not read the Obsidian Portal record for {char.get("name")}')
    gm_info = str(body.get('game_master_info') or '')
    return {
        'name': str(char.get('name', '')),
        'slug': str(char.get('slug', '')),
        'school_line': school_line(str(body.get('description') or '')),
        'tags': _tags(body.get('tags') or char.get('tags')),
        'earned_xp': earned_xp(gm_info),
        'trait_lines': trait_lines(gm_info),
        'stat_lines': stat_lines(gm_info),
    }
