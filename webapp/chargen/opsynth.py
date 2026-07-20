"""Pure helpers for the ``/synthesize`` skill.

The skill turns an existing Obsidian Portal (OP) character into a Gemini
backstory - the chat-session twin of the webapp's Synthesize Backstory button.
All the *decisions* live here as side-effect-free functions so they can be
unit-tested at 100% coverage (Constitution Principle X):

- ``match_character``     - resolve an approximate name to an OP character.
- ``infer_caste``         - pick Samurai/Monk/Peasant for the per-caste corpus.
- ``parse_tagline``       - read the one-line summary out of the OP page HTML
                            (the OAuth JSON API does not expose it).
- ``build_synthesis_character`` - map an OP record into the webapp character shape.
- ``related_by_tagline``  - find cast members linked to the same NPC as the subject.
- ``refresh_taglines``    - incremental tagline-cache merge (injected fetcher).
- ``merge_backstory``     - merge the backstory into GM-only notes as bare prose.
- ``strip_backstory_markers`` - drop the legacy sentinel lines from old records.

The network boundary (fetching OP pages, PATCHing records) lives in
``chargen.op``; this module never performs I/O.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

#: LEGACY sentinels that used to delimit the auto-managed backstory block in
#: GM-only notes. New merges write bare prose with no markers (GM decision
#: 2026-07-20); the constants remain so records that still carry them get the
#: block replaced in place (markers dropped) and can be swept clean.
BACKSTORY_START = '--- Synthesized Backstory (auto) ---'
BACKSTORY_END = '--- End Synthesized Backstory ---'

#: Ordered caste inference markers (checked against tags + GM notes, lowercased).
#: Monk = the Brotherhood/monastic orders; shugenja are samurai, so priest/
#: shugenja are deliberately NOT monk markers. Peasant markers are the heimin/
#: hinin labels. Anything else defaults to Samurai (the cast is mostly samurai).
_MONK_MARKERS: tuple[str, ...] = (
    'order of',
    'monk',
    'monastery',
    'monastic',
    'abbot',
    'brotherhood',
    'sohei',
    'ise zumi',
)
_PEASANT_MARKERS: tuple[str, ...] = (
    'peasant',
    'heimin',
    'ashigaru',
    'farmer',
    'servant',
    'laborer',
    'fisherman',
    'burakumin',
    'hinin',
)

#: Name particles ignored when tokenizing Rokugani names for matching.
_NAME_PARTICLES: frozenset[str] = frozenset({'no', 'the', 'of'})


def _tokens(text: str) -> list[str]:
    """Lowercase alphanumeric tokens, particles dropped."""
    return [t for t in re.findall(r'[a-z0-9]+', text.lower()) if t not in _NAME_PARTICLES]


@dataclass(frozen=True)
class MatchResult:
    """Outcome of resolving a typed name against the OP character list."""

    kind: str  # 'unique' | 'ambiguous' | 'none'
    matches: tuple[Mapping[str, object], ...] = ()
    nearest: tuple[str, ...] = field(default=())

    @property
    def character(self) -> Mapping[str, object]:
        """The single matched character (only valid when kind == 'unique')."""
        if self.kind != 'unique':
            raise ValueError(f'no unique match: {self.kind}')
        return self.matches[0]


def match_character(query: str, characters: Sequence[Mapping[str, object]]) -> MatchResult:
    """Resolve ``query`` to an OP character by token containment.

    A character matches when every query token appears inside some token of its
    name (so "Daidoji Jitsuyo" resolves "Daidoji no Etsuko Jitsuyo"). One match ->
    unique; several -> ambiguous; none -> the three nearest names by similarity.
    """
    q = _tokens(query)
    hits: list[Mapping[str, object]] = []
    if q:
        for ch in characters:
            name_tokens = _tokens(str(ch.get('name', '')))
            if all(any(qt in nt for nt in name_tokens) for qt in q):
                hits.append(ch)
    if len(hits) == 1:
        return MatchResult('unique', (hits[0],))
    if len(hits) > 1:
        return MatchResult('ambiguous', tuple(hits))
    names = [str(ch.get('name', '')) for ch in characters]
    nearest = difflib.get_close_matches(query, names, n=3, cutoff=0.0)
    return MatchResult('none', (), tuple(nearest))


def infer_caste(tags: Sequence[str], gm_info: str) -> str:
    """Infer 'Samurai' | 'Monk' | 'Peasant' from tags + GM notes.

    Precedence Monk > Peasant > Samurai; Samurai is the default. The result only
    selects which extra corpus sections synthesis appends, so a wrong guess
    degrades gracefully and the GM can override by re-generating.
    """
    blob = ' '.join([*tags, gm_info]).lower()
    if any(marker in blob for marker in _MONK_MARKERS):
        return 'Monk'
    if any(marker in blob for marker in _PEASANT_MARKERS):
        return 'Peasant'
    return 'Samurai'


def parse_tagline(html: str) -> str:
    """Return the character's one-line summary from OP page HTML.

    The page carries two ``class='tagline'`` elements - an empty banner and the
    populated body tagline; return the first non-empty one, or '' if none.
    """
    soup = BeautifulSoup(html, 'html.parser')
    for element in soup.find_all(class_='tagline'):
        text = element.get_text(' ', strip=True)
        if text:
            return text
    return ''


def build_synthesis_character(body: Mapping[str, object], tagline: str) -> dict[str, object]:
    """Map an OP ``get_character_body`` record + tagline into the webapp
    character shape consumed by ``synthesis.format_character``."""
    tags = body.get('tags')
    return {
        'full_name': str(body.get('name') or ''),
        'tags': list(tags) if isinstance(tags, list) else [],
        'summary': tagline or '',
        'public': str(body.get('description') or ''),
        'private': str(body.get('game_master_info') or ''),
    }


def _mentioned_names(text: str, names: Sequence[str]) -> set[str]:
    """Names whose personal (last) name token appears as a whole word in text."""
    low = text.lower()
    found: set[str] = set()
    for name in names:
        toks = _tokens(name)
        if toks and re.search(rf'\b{re.escape(toks[-1])}\b', low):
            found.add(name)
    return found


def related_by_tagline(
    subject_tagline: str,
    cast_taglines: Mapping[str, str],
    cast_names: Sequence[str],
) -> list[str]:
    """Cast members whose tagline references the same NPC the subject's does.

    e.g. subject "drinking companion of Kyoma" -> other characters whose taglines
    also mention Kyoma. Empty when the subject's tagline names no cast member.
    """
    targets = _mentioned_names(subject_tagline, cast_names)
    if not targets:
        return []
    related = [
        name for name, tagline in cast_taglines.items() if _mentioned_names(tagline, list(targets))
    ]
    return sorted(set(related))


def refresh_taglines(
    cache: Mapping[str, Mapping[str, str]],
    characters: Sequence[Mapping[str, object]],
    fetch_tagline: Callable[[Mapping[str, object]], str],
) -> tuple[dict[str, dict[str, str]], dict[str, int]]:
    """Incrementally refresh the id-keyed tagline cache.

    Fetch a tagline (via the injected ``fetch_tagline`` boundary) only for
    characters that are new or whose ``updated_at`` changed; keep unchanged
    entries; drop ids no longer present. Mirrors ``opcache.refresh``.
    """
    new_cache: dict[str, dict[str, str]] = {}
    fetched = kept = 0
    for ch in characters:
        cid = str(ch.get('id') or '')
        if not cid:
            continue
        updated_at = str(ch.get('updated_at') or '')
        prior = cache.get(cid)
        if prior is not None and prior.get('updated_at') == updated_at:
            new_cache[cid] = dict(prior)
            kept += 1
            continue
        new_cache[cid] = {'tagline': fetch_tagline(ch), 'updated_at': updated_at}
        fetched += 1
    dropped = sum(1 for cid in cache if cid not in new_cache)
    return new_cache, {'fetched': fetched, 'kept': kept, 'dropped': dropped}


def merge_backstory(existing_gm_info: str, prose: str) -> str:
    """Merge ``prose`` into GM-only notes as bare, unmarked prose.

    Backstories carry no header/footer (GM decision 2026-07-20). If a legacy
    sentinel-delimited block is still present, it is replaced in place and the
    markers dropped; otherwise the prose is appended after the existing notes.
    Without markers a re-run cannot recognize its own earlier prose, so
    re-synthesizing an already-merged character appends a second copy - an
    accepted tradeoff; the GM prunes by hand in that rare case.
    """
    block = prose.strip()
    start = existing_gm_info.find(BACKSTORY_START)
    end = existing_gm_info.find(BACKSTORY_END)
    if start != -1 and end != -1 and end > start:
        return existing_gm_info[:start] + block + existing_gm_info[end + len(BACKSTORY_END) :]
    if existing_gm_info.strip():
        return existing_gm_info.rstrip() + '\n\n' + block
    return block


def strip_backstory_markers(gm_info: str) -> str:
    """Remove legacy backstory sentinel lines, keeping the prose between them.

    One-shot cleanup for records written before the no-markers decision
    (2026-07-20). Unwraps every well-formed block; text outside the markers is
    preserved with blank-line joins. Malformed markers (end before start, or
    only one present) are left untouched rather than guessed at.
    """
    out = gm_info
    while True:
        start = out.find(BACKSTORY_START)
        end = out.find(BACKSTORY_END)
        if start == -1 or end == -1 or end < start:
            return out
        inner = out[start + len(BACKSTORY_START) : end].strip()
        before = out[:start].rstrip()
        after = out[end + len(BACKSTORY_END) :].strip()
        out = '\n\n'.join(part for part in (before, inner, after) if part)
