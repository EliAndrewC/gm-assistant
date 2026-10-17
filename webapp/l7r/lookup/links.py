"""Links in a reply: people linked mechanically, and nothing linked that we did not vouch for.

The GM: "anytime we mention a person in the response, then we should link to
that person. Now that ... does not have to be something that the LLM does ...
we could mechanically do a search for them and then link to them." So the model
writes plain names and `linkify` adds the links afterwards, from the ROSTER:
every Obsidian Portal character a player can open, plus each Wasp PC (their OP
page if they have one, otherwise their character sheet).

Topic links (the Imperial Bounties page, the Wasp Hierarchy) are the model's
job, because "people will not be able to phrase the question in a way that
allows a mechanical response". The model may only use addresses the glossary
carries, and `scrub` removes any other address before the reply is posted - an
invented URL is worse than none.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

#: A markdown link `[text](address)`, or a bare http(s) address. One pattern so
#: a single left-to-right pass sees each address exactly once.
_LINK = re.compile(r'\[([^\]\n]+)\]\((https?://[^)\s]+)\)|(?<![(\w])(https?://[^\s<>()]+)')


#: Words after a name that make it a group, not a person: "Tsuruchi lineage".
_GROUP_WORDS = r'(?i:lineage|family|families|clan|house|school|bushi|archers?)\b'


@dataclass(frozen=True)
class Person:
    name: str
    url: str

    @property
    def given(self) -> str:
        parts = self.name.split()
        return parts[-1] if len(parts) > 1 else ''


def roster(
    op_characters: Iterable[Mapping[str, Any]], pcs: Iterable[tuple[str, str]]
) -> list[Person]:
    """The people `linkify` may link.

    `op_characters` is the Obsidian Portal listing (`name`, `character_url`,
    `is_game_master_only`). GM-only records are left out: a player cannot open
    them, so the link would lead nowhere. `pcs` is (name, sheet address) for the
    campaign's PCs; an OP record of the same name wins over the sheet."""
    people: dict[str, Person] = {}
    for c in op_characters:
        if c.get('is_game_master_only') or not c.get('character_url'):
            continue
        name = ' '.join(str(c.get('name', '')).split())
        if name:
            people.setdefault(name.casefold(), Person(name, str(c['character_url'])))
    for name, url in pcs:
        people.setdefault(' '.join(name.split()).casefold(), Person(' '.join(name.split()), url))
    return list(people.values())


def _patterns(people: list[Person]) -> list[tuple[str, Person]]:
    """(surface form, person), longest first, so "Tsuruchi Kyoma" beats "Kyoma".

    A bare given name is a form only when exactly one person in the roster has
    it; a shared given name stays unlinked rather than linking the wrong person."""
    givens: dict[str, list[Person]] = {}
    for p in people:
        if p.given:
            givens.setdefault(p.given.casefold(), []).append(p)
    full_names = {p.name.casefold() for p in people}
    forms = [(p.name, p) for p in people]
    for key, owners in givens.items():
        if len(owners) == 1 and key not in full_names:
            forms.append((owners[0].given, owners[0]))
    return sorted(forms, key=lambda f: -len(f[0]))


def linkify(text: str, people: list[Person]) -> str:
    """Link each person in `text` once, at their first mention.

    Text already inside a markdown link is left alone, and a match must sit on
    word boundaries, so "Kyoma" inside "Kyomaru" is not a mention."""
    forms = _patterns(people)
    if not forms:
        return text
    alternation = '|'.join(re.escape(form) for form, _ in forms)
    by_form = {form.casefold(): person for form, person in forms}
    # The lookahead: some people are known by one word that is also a family name
    # (the founder "Tsuruchi"), and "the Tsuruchi lineage" is not a mention of him.
    names = re.compile(rf'(?<![\w\[])({alternation})(?![\w\]])(?!\s+{_GROUP_WORDS})')
    linked: set[str] = set()

    def plain(chunk: str) -> str:
        def swap(m: re.Match[str]) -> str:
            person = by_form[m.group(1).casefold()]
            if person.url in linked:
                return m.group(1)
            linked.add(person.url)
            return f'[{m.group(1)}]({person.url})'

        return names.sub(swap, chunk)

    out: list[str] = []
    last = 0
    for m in _LINK.finditer(text):
        out.append(plain(text[last : m.start()]))
        out.append(m.group(0))
        if m.group(2):
            linked.add(m.group(2))
        last = m.end()
    out.append(plain(text[last:]))
    return ''.join(out)


def scrub(text: str, allowed: Iterable[str]) -> tuple[str, list[str]]:
    """`text` with every address not in `allowed` removed, and the addresses removed.

    A markdown link to an unknown address keeps its text; a bare unknown address
    disappears. Trailing sentence punctuation is not part of a bare address."""
    ok = {a.rstrip('/') for a in allowed}
    dropped: list[str] = []

    def check(m: re.Match[str]) -> str:
        if m.group(2):
            if m.group(2).rstrip('/') in ok:
                return m.group(0)
            dropped.append(m.group(2))
            return m.group(1)
        url = m.group(3)
        tail = ''
        while url and url[-1] in '.,;:!?':
            url, tail = url[:-1], url[-1] + tail
        if url.rstrip('/') in ok:
            return url + tail
        dropped.append(url)
        return tail

    return _LINK.sub(check, text), dropped
