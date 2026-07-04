"""Assemble the full-corpus setting brief for backstory synthesis.

This is the production home of the prompt a blind evaluation selected: the design
brief, the GM's "The Great Clans" framing (sliced live from l7r.md), the per-clan
flavor summary, and the canonical corpus (l7r.md + budgets.md), minus the
prompt-irrelevant sections listed in ``_EXCLUDED_L7R_SECTIONS``,
``_EXCLUDED_BUDGET_SECTIONS``, and ``_PRUNED_BUDGET_SECTIONS`` (a cost trim;
see the comments there for the reasoning).

It is a standalone, fully typed, fully covered module (Principle X) so the brief
assembly lives outside the grace-listed chargen modules. ``synthesis.py``
delegates ``load_brief`` here; the Gemini call stays the fixture-tested boundary.

Corpus resolution (first match wins):

1. ``$L7R_SETTING_DIR`` when set (explicit override).
2. The dev bind-mount at ``/host-l7r-repo/setting`` (live; preferred in dev so
   the GM's edits take effect immediately).
3. The bundled snapshot at ``<webapp>/setting`` (the prod fallback, produced by
   ``make prepare-deploy``; the deployed app has no bind-mount).

If no candidate holds both ``l7r.md`` and ``budgets.md`` a ``CorpusNotFound`` is
raised: the brief is never silently degraded to a thinner prompt.
"""

from __future__ import annotations

import os
import re
from collections.abc import Sequence
from pathlib import Path

_CHARGEN_DIR = Path(__file__).resolve().parent
_BRIEF_PATH = _CHARGEN_DIR / 'synthesis_brief.md'
_FLAVOR_PATH = _CHARGEN_DIR / 'flavor_clans.md'

#: The dev bind-mount (live, preferred) and the bundled snapshot dir (sibling of
#: chargen, under webapp/; the prod fallback), tried in that order after the env
#: override.
_MOUNT_DIR = Path('/host-l7r-repo/setting')
_BUNDLED_DIR = _CHARGEN_DIR.parent / 'setting'

#: Heading in l7r.md whose block carries the materialist clan framing.
_CLAN_BLURB_HEADING = 'The Great Clans'

#: l7r.md sections excised from the synthesis prompt (the file itself is never
#: touched). Why: the full prompt bills at Gemini's long-context rate (>200k
#: tokens doubles the input price), and these sections cannot steer a synthesis
#: for the current campaign - it has no Moto or gaijin presence, so the Moto and
#: gaijin material (Bashi's Letter, the Gods of Death, the yassa, the Dark Moto)
#: grounds nothing, and "Moto Khuyag's Death Detectors" and "The Nameless One"
#: are one-off artifact/plot-hook discussions from past campaigns. The blind
#: evaluation's "more lore beats less" finding still governs: only sections with
#: no bearing on generated characters are cut, never load-bearing lore. Measured
#: saving as of 2026-07: ~34k of ~331k prompt tokens (~10%); the prompt remains
#: above the 200k tier boundary, so this trims spend without changing the tier.
#: Restore entries here (or make the list campaign-scoped) if a campaign returns
#: to the steppes or the Burning Sands. A missing heading raises rather than skips, so
#: a renamed section in l7r.md surfaces immediately instead of silently
#: re-inflating the prompt.
#:
#: The second group is deduplication against the OP campaign cast: the opcache
#: block in the same prompt already carries this content, verified verbatim
#: (8-word-shingle overlap plus manual reads, 2026-07). Kitsune Tatsuya's OP bio
#: contains the whole Imperial Road / Minami wardings writeup (he is the Ochiba
#: County Magistrate who maintains them); Tsuruchi Tatsuki's carries her
#: superstition gifts and all four protective amulets. A 2026-07 audit found
#: these were the ONLY substantive OP/l7r.md overlaps - in particular the Crane
#: Wives lore is NOT in the wives' OP records (those are portrait-and-stats
#: stubs), so their sections must stay. Small known cost: when the synthesis
#: subject is itself one of these two NPCs, assemble_context excludes their OP
#: block and this content drops out of that one prompt entirely.
_EXCLUDED_L7R_SECTIONS: tuple[str, ...] = (
    # Campaign-irrelevant (current campaign has no Moto or gaijin presence):
    "Moto Khuyag's Death Detectors",
    'The Nameless One',
    'Gaijin',
    'The Moto',
    # Duplicated in the OP campaign-cast block assembled by chargen.opcache:
    'The Imperial Road Through Minami',
    'Tsuruchi Tatsuki',
    # GM-directed past-campaign cuts (2026-07): prior-campaign writeups do not
    # steer current-campaign NPCs. (Temple Relics, formerly in this group, moved
    # to the monk entry of _CASTE_L7R_SECTIONS: gone for samurai, back for
    # monks. The Peasant Campaign lives in _CASTE_L7R_SECTIONS['peasant'] for
    # the same reason with a caste twist. The Karmic Inquisitors campaign was
    # briefly pruned-keeping-Damasu; once the Damasu Domain moved to the samurai
    # supplement, the whole campaign block became a plain exclusion.)
    'The First Toshi Ranbo Campaign',
    'The Hidden Way Campaign',
    'The Karmic Inquisitors Campaign',
    # The l7r.md Imperial Budget stub just points at budgets.md ("provisionally
    # located there"). It nests inside the samurai government section; listing
    # it here keeps it out of both the base and that supplement.
    'The Imperial Budget',
)

#: Caste-conditional l7r.md sections, keyed by the chargen type dropdown value
#: (lowercased). Each group is excised from the base corpus for EVERY prompt -
#: so the base stays byte-identical across castes and the shared prompt prefix
#: keeps caching - and re-appended as a SETTING BRIEF SUPPLEMENT only when the
#: synthesized character is of that type, near the END of the prompt (after the
#: stable cast block), never mid-corpus. Why (GM, 2026-07): temple internals,
#: soothsaying, and the oath/vow material matter to monks and little to anyone
#: else; government structure, rank accordances, the legion backstories, and the
#: Damasu Domain writeup are the samurai world, opaque to peasants and monks.
#: Groups may nest across castes (the monk temple sections live inside the
#: samurai Damasu block) - both the base excision (remove_sections merges spans)
#: and the supplement extraction (_remove_present strips foreign material from
#: extracted blocks) handle that in any listing order. New titles append at the
#: END of a group: group order is the supplement's section order, and a mid-list
#: insert needlessly perturbs the cached prompt prefix for that caste.
_CASTE_L7R_SECTIONS: dict[str, tuple[str, ...]] = {
    'monk': (
        'Damasu Temples',
        'Temple Daily Life',
        'Temple Relics',
        'Temple Organization',
        'Soothsaying',
        'Oaths and Vows',
    ),
    'peasant': ('The Peasant Campaign',),
    'samurai': (
        'The Structure of Rokugani Government',
        'The Measure of Standing and the Accordances of Rank',
        '3rd Imperial Legion Backstories',
        '1st Imperial Legion Backstories',
        'The Damasu Domain',
    ),
}

#: The budgets.md twin of _CASTE_L7R_SECTIONS. The ministry/office-holder/
#: Imperial budget machinery is government-facing material only samurai deal
#: with. Globally excluded sections nested inside these (the daimyo worked
#: example, the Imperial revenue/spending/scale aggregates) stay excluded from
#: the supplement too.
_CASTE_BUDGET_SECTIONS: dict[str, tuple[str, ...]] = {
    'samurai': (
        'Ministry budgets',
        'Example office-holder budgets',
        'The Imperial budget',
    ),
}

#: budgets.md sections excised from the synthesis prompt (same rules as above:
#: prompt-side only, missing headings fail loud). Why: per the GM, these are
#: pure calculation - Empire-wide multiplier arithmetic, per-tier population and
#: land-yield derivations - that grounds no character detail a synthesis could
#: use; the conclusions those calculations feed (stipends, office budgets,
#: worked examples) mostly stay. Second round (GM, 2026-07): the daimyo-tier
#: worked example and the Imperial revenue/spending/historical-scale aggregates
#: go too - NPCs live at magistrate/governor scale, and those two worked
#: examples remain in the prompt.
_EXCLUDED_BUDGET_SECTIONS: tuple[str, ...] = (
    'The two Empire-wide multipliers',
    'Land productivity',
    'Daimyo Hida no Reiji Isao of the Reiji Domain',
    'Imperial revenue (~34-36 million koku per year at baseline)',
    'Imperial spending (~30-31 million koku per year)',
    'Imperial budget scale: historical context',
)

#: budgets.md sections whose body is excised but whose heading and listed
#: subsections stay, via remove_section_except. "Domain" is per-tier population
#: math except "Discretionary budgets", which the GM keeps: what officials can
#: actually spend is real character-shaping context, not calculation.
_PRUNED_BUDGET_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ('Domain', ('Discretionary budgets',)),
)


class CorpusNotFound(RuntimeError):
    """Raised when the canonical setting corpus cannot be located."""


def _read(path: Path) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()


def _candidate_dirs() -> list[Path]:
    """Corpus directories to try, in priority order."""
    dirs: list[Path] = []
    env = os.environ.get('L7R_SETTING_DIR')
    if env:
        dirs.append(Path(env))
    dirs.append(_MOUNT_DIR)
    dirs.append(_BUNDLED_DIR)
    return dirs


def _has_corpus(directory: Path) -> bool:
    return (directory / 'l7r.md').is_file() and (directory / 'budgets.md').is_file()


def resolve_corpus_dir() -> Path:
    """Return the first candidate dir holding both l7r.md and budgets.md."""
    tried: list[str] = []
    for directory in _candidate_dirs():
        tried.append(str(directory))
        if _has_corpus(directory):
            return directory
    raise CorpusNotFound(
        'Canonical setting corpus (l7r.md + budgets.md) not found. Tried: '
        + ', '.join(tried)
        + '. In the deployed app this means `make prepare-deploy` did not bundle '
        'the snapshot into webapp/setting/.'
    )


def _section_bounds(lines: list[str], title: str) -> tuple[int, int]:
    """Return the [start, end) line span of one ATX heading's block: the heading
    plus its body up to the next heading of the same or higher level. Raises
    ``ValueError`` if the heading is not found."""
    start: int | None = None
    level = 0
    for i, line in enumerate(lines):
        match = re.match(r'^(#{1,6})\s+(.*?)\s*$', line)
        if match and match.group(2) == title:
            start = i
            level = len(match.group(1))
            break
    if start is None:
        raise ValueError(f'heading not found in canonical notes: {title!r}')

    end = len(lines)
    for j in range(start + 1, len(lines)):
        match = re.match(r'^(#{1,6})\s+', lines[j])
        if match and len(match.group(1)) <= level:
            end = j
            break
    return start, end


def extract_section(md_text: str, title: str) -> str:
    """Return one ATX heading's block: the heading plus its body up to the next
    heading of the same or higher level. Raises ``ValueError`` if not found."""
    lines = md_text.splitlines()
    start, end = _section_bounds(lines, title)
    return '\n'.join(lines[start:end]).strip()


def _delete_spans(lines: list[str], spans: list[tuple[int, int]]) -> str:
    """Delete the given ``[start, end)`` line spans; overlapping or nested
    spans merge, so a section and its own subsection may both be listed."""
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    kept: list[str] = []
    pos = 0
    for start, end in merged:
        kept += lines[pos:start]
        pos = end
    kept += lines[pos:]
    return '\n'.join(kept)


def remove_sections(md_text: str, titles: Sequence[str]) -> str:
    """Return ``md_text`` with every listed heading's block excised (same
    boundaries as ``extract_section``). All bounds are computed on the original
    text before any deletion, so the list may freely mix sections nested inside
    one another, in any order. Raises ``ValueError`` for any missing heading."""
    lines = md_text.splitlines()
    return _delete_spans(lines, [_section_bounds(lines, t) for t in titles])


def remove_section(md_text: str, title: str) -> str:
    """Return ``md_text`` with one heading's block excised (same boundaries as
    ``extract_section``). Raises ``ValueError`` if the heading is not found."""
    return remove_sections(md_text, [title])


def _remove_present(md_text: str, titles: Sequence[str]) -> str:
    """Remove the listed sections that actually appear in ``md_text``, skipping
    absent ones. Used to strip foreign material nested inside an extracted
    block, where most listed titles legitimately live elsewhere in the corpus -
    absence is the normal case there, not an error."""
    lines = md_text.splitlines()
    spans: list[tuple[int, int]] = []
    for title in titles:
        try:
            spans.append(_section_bounds(lines, title))
        except ValueError:
            continue
    return _delete_spans(lines, spans)


def remove_section_except(md_text: str, title: str, keep: tuple[str, ...]) -> str:
    """Excise a heading's block but retain its heading line and the ``keep``
    subsection blocks, in their original order. Raises ``ValueError`` if the
    section or any kept subsection is not found."""
    lines = md_text.splitlines()
    start, end = _section_bounds(lines, title)
    block = '\n'.join(lines[start:end])
    kept = [extract_section(block, k) for k in keep]
    replacement = '\n\n'.join([lines[start], *kept]).splitlines()
    tail = lines[end:]
    if tail:
        replacement.append('')  # restore the blank line before what follows
    return '\n'.join(lines[:start] + replacement + tail)


def build_full_brief(corpus_dir: Path | None = None) -> str:
    """Assemble the full-corpus setting brief.

    The full-corpus assembly a blind evaluation selected: design brief + "The
    Great Clans" blurb + per-clan flavor + l7r.md (minus
    ``_EXCLUDED_L7R_SECTIONS``) + a labeled budgets.md block (minus
    ``_EXCLUDED_BUDGET_SECTIONS``, with ``_PRUNED_BUDGET_SECTIONS`` reduced to
    their kept subsections). Pass ``corpus_dir`` to override resolution (e.g.
    in tests).
    """
    corpus = corpus_dir if corpus_dir is not None else resolve_corpus_dir()
    if not _has_corpus(corpus):
        raise CorpusNotFound(f'corpus dir is missing l7r.md or budgets.md: {corpus}')

    brief = _read(_BRIEF_PATH).strip()
    l7r = _read(corpus / 'l7r.md')
    # Caste-conditional sections come out of the base for everyone (they return
    # via build_caste_supplement), together with the global exclusions, in one
    # merged-span pass: the list mixes nested combinations freely (monk temple
    # sections inside the samurai Damasu block, the Imperial Budget stub inside
    # the samurai government section, the Damasu block inside the excluded
    # Karmic campaign).
    caste_titles = [t for group in _CASTE_L7R_SECTIONS.values() for t in group]
    l7r = remove_sections(l7r, caste_titles + list(_EXCLUDED_L7R_SECTIONS))
    flavor = _read(_FLAVOR_PATH).strip()
    clan_blurb = extract_section(l7r, _CLAN_BLURB_HEADING)
    budgets = _read(corpus / 'budgets.md').strip()
    budget_caste_titles = [t for group in _CASTE_BUDGET_SECTIONS.values() for t in group]
    budgets = remove_sections(budgets, budget_caste_titles + list(_EXCLUDED_BUDGET_SECTIONS))
    for title, keep in _PRUNED_BUDGET_SECTIONS:
        budgets = remove_section_except(budgets, title, keep)
    budgets = budgets.strip()  # removals can leave a dangling trailing newline

    base = '\n\n'.join([brief, clan_blurb, flavor])
    corpus_block = f'{l7r.strip()}\n\n# BUDGETS AND ECONOMIC MODEL (budgets.md)\n\n{budgets}'
    return '\n\n'.join([base, '# FULL CANONICAL NOTES\n\n' + corpus_block])


def _extract_caste_sections(
    md_text: str,
    caste: str,
    titles: tuple[str, ...],
    caste_map: dict[str, tuple[str, ...]],
    excluded: tuple[str, ...],
) -> list[str]:
    """Extract each of ``caste``'s section blocks, stripping any OTHER caste's
    sections and any globally excluded sections nested inside them (e.g. the
    monk temple sections inside the samurai Damasu block, the excluded daimyo
    worked example inside the samurai office-holder budgets)."""
    foreign = [t for other, group in caste_map.items() if other != caste for t in group]
    foreign += list(excluded)
    return [_remove_present(extract_section(md_text, t), foreign).strip() for t in titles]


def build_caste_supplement(character_type: str, corpus_dir: Path | None = None) -> str:
    """Return the ``# SETTING BRIEF SUPPLEMENT`` block for the given chargen
    type dropdown value ('' when that type has no conditional sections).

    Sections are extracted from the same canonical corpus (l7r.md and
    budgets.md) that ``build_full_brief`` excises them from, so together the
    base + supplement reconstruct the trimmed corpus for that caste. The caller
    appends this near the end of the prompt (after the stable cast block) to
    preserve the shared prompt prefix for implicit caching.
    """
    caste = character_type.strip().lower()
    l7r_titles = _CASTE_L7R_SECTIONS.get(caste, ())
    budget_titles = _CASTE_BUDGET_SECTIONS.get(caste, ())
    if not l7r_titles and not budget_titles:
        return ''
    corpus = corpus_dir if corpus_dir is not None else resolve_corpus_dir()
    if not _has_corpus(corpus):
        raise CorpusNotFound(f'corpus dir is missing l7r.md or budgets.md: {corpus}')
    parts: list[str] = []
    if l7r_titles:
        parts += _extract_caste_sections(
            _read(corpus / 'l7r.md'),
            caste,
            l7r_titles,
            _CASTE_L7R_SECTIONS,
            _EXCLUDED_L7R_SECTIONS,
        )
    if budget_titles:
        parts += _extract_caste_sections(
            _read(corpus / 'budgets.md'),
            caste,
            budget_titles,
            _CASTE_BUDGET_SECTIONS,
            _EXCLUDED_BUDGET_SECTIONS,
        )
    return '# SETTING BRIEF SUPPLEMENT\n\n' + '\n\n'.join(parts)
