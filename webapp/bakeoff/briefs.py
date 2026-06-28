"""
Assembly of the four prompt tiers under test.

The whole point of the bakeoff is to compare context *amount* and *kind*, so the
tiers are built compositionally rather than as four hand-maintained copies:

- **t0** - the shipped philosophy-only brief (chargen/synthesis_brief.md, ~3k
  tokens). "Can principles alone carry it?"
- **t1** - t0 + hand-written clan/family/school flavor + a few real GM-written
  NPC writeups as few-shot exemplars (~12-15k). "Lean but textured."
- **t2** - t1 + material life, government, calendar, and supernatural texture
  pulled verbatim from l7r.md (~30-40k). "Does the full texture layer help?"
- **t3** - the entire l7r.md plus budgets.md (~300k). "Does curation even
  matter, or does dumping everything just work?"

t2 and t3 slice exact text out of the canonical files at build time via
``extract_section`` so the GM's writing is never retyped (and never drifts).
"""

import os
import re

from bakeoff import config

#: The shipped tier-0 brief lives with the synthesis module it serves.
_T0_PATH = os.path.join(config.HERE, '..', 'chargen', 'synthesis_brief.md')
#: Hand-written clan/family/school flavor, added at t1 and above.
_FLAVOR_PATH = os.path.join(config.HERE, 'flavor_clans.md')

#: GM-written NPC writeups used as few-shot exemplars. These are short,
#: concrete, and model the ambiguous-supernatural ethos - exactly the gestalt
#: behaviour we want. Matched by their exact l7r.md heading text.
_T1_EXEMPLAR_HEADINGS = [
    'Matsu Tsutomu',
    'Mirumoto Uta',
    'Matsu Kiyora',
    'Shiba Asayo (3rd Legion)',
    'Matsu Tonami',
]

#: Texture sections added at t2, pulled verbatim from l7r.md by heading. A mix
#: of caste/economy, government, rank/etiquette, calendar, and supernatural.
_T2_SECTION_HEADINGS = [
    'Money',
    'Merchant Families',
    'Ashigaru',
    'Monks',
    'Entertainers',
    'Bandits',
    'Maho-tsukai',
    'The Structure of Rokugani Government',
    'The Measure of Standing and the Accordances of Rank',
    'The Twelve Months',
    'Crops and Farming Seasons',
    'Soothsaying',
    'Touched by the Supernatural',
    'Wasp Clan NPCs',
    'Kitsuki Fu',
]


def _read(path: str) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()


def extract_section(md_text: str, title: str) -> str:
    """
    Return one heading's block from a markdown document.

    Finds the (first) ATX heading whose text exactly equals ``title``, then
    returns it plus everything up to the next heading of the same or higher
    level (so a ``####`` exemplar stops at the next ``####`` or ``###``, and a
    ``##`` chapter swallows its own ``###`` subsections). Raises if not found.
    """
    lines = md_text.splitlines()
    start = None
    level = 0
    for i, line in enumerate(lines):
        m = re.match(r'^(#{1,6})\s+(.*?)\s*$', line)
        if m and m.group(2) == title:
            start = i
            level = len(m.group(1))
            break
    if start is None:
        raise ValueError(f'heading not found in canonical notes: {title!r}')

    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = re.match(r'^(#{1,6})\s+', lines[j])
        if m and len(m.group(1)) <= level:
            end = j
            break
    return '\n'.join(lines[start:end]).strip()


def _exemplars_block(md_text: str, headings: list[str]) -> str:
    parts = [
        'The following are real, GM-written NPC writeups from this campaign. '
        'They are the target style and depth: concrete, grounded, laconic, and '
        'when the supernatural appears it stays ambiguous (the reader cannot '
        'tell whether it was real or imagined). Imitate this approach - do not '
        'copy these characters.',
    ]
    parts += [extract_section(md_text, h) for h in headings]
    return '# EXEMPLAR NPC WRITEUPS\n\n' + '\n\n'.join(parts)


def _sections_block(md_text: str, headings: list[str]) -> str:
    parts = [extract_section(md_text, h) for h in headings]
    return '# ADDITIONAL SETTING DETAIL (from l7r.md)\n\n' + '\n\n'.join(parts)


def build_tier(tier: str) -> str:
    """Assemble and return the full brief text for one tier id."""
    t0 = _read(_T0_PATH).strip()
    if tier == 't0':
        return t0

    if tier == 't3':
        # Everything: the whole canonical corpus, unedited.
        l7r = _read(config.L7R_MD).strip()
        budgets = _read(config.BUDGETS_MD).strip()
        return f'{l7r}\n\n# BUDGETS AND ECONOMIC MODEL (budgets.md)\n\n{budgets}'

    l7r = _read(config.L7R_MD)
    flavor = _read(_FLAVOR_PATH).strip()
    exemplars = _exemplars_block(l7r, _T1_EXEMPLAR_HEADINGS)
    t1 = '\n\n'.join([t0, flavor, exemplars])
    if tier == 't1':
        return t1

    if tier == 't2':
        sections = _sections_block(l7r, _T2_SECTION_HEADINGS)
        return '\n\n'.join([t1, sections])

    raise ValueError(f'unknown tier: {tier!r}')


def _main() -> None:
    """Print the assembled size of each tier so the tiers can be balanced."""
    for tier in config.TIERS:
        text = build_tier(tier)
        chars = len(text)
        print(f'{tier}: {chars:>8} chars  ~{chars // 4:>7} tokens')


if __name__ == '__main__':
    _main()
