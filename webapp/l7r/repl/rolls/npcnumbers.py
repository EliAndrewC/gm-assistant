"""An NPC's rings and skill ranks, remembered between sessions. PURE.

Feature 207. The GM's problem, in their words: the players talk to someone, the GM
makes a tact roll, *"and then the players come back a few weeks of real-world time
later ... And then I have to make another tact roll for that NPC. I would like to
use the same tact skill and not have the NPC's tact vary from session to session.
However, this requires me currently to either write down what I did or to just
remember. And I'm not going to be able to remember every skill for every NPC."*

So the numbers are read off the GM's own rolls and kept where the players cannot
see them: a parsable block in the NPC's GM-ONLY notes, the way Discern Honor keeps
one (`l7r/repl/honor.py`).

    NPC numbers:
    - Air 3
    - tact 2
    - sincerity 5

HOW A ROLL BECOMES NUMBERS. A skill roll is (Ring + rank)k(Ring), so the KEPT dice
are the ring the skill uses and rolled minus kept is the rank: `xky(5, 3) - tact`
says Air 3, tact 2. Two things can put extra dice in the pool, and both are taken
back out first:

- A SCHOOL that rolls an extra die on the skill. The GM: *"if someone with the
  merchant school were to roll eight dice and keep three dice, then we would know
  for a fact that they have four sincerity rather than five."* Which schools, on
  which skills, is READ from the rules' school text - every "Roll one extra die on
  ..." line - never listed here.
- A VOID POINT, one rolled and one kept die each - but only when the tool was told
  (`tact(vp)`). An untold one is exactly what `compare` exists to catch.

Flat bonuses are no part of this: a `+ 10` changes a total, not a pool.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from l7r.repl.rolls.skills import RULES_PATH

HEADING = 'NPC numbers:'
RINGS = ('air', 'earth', 'fire', 'water', 'void')

#: The files that define schools. NPC-only schools live apart from the PC ones.
SCHOOL_PATHS = (
    RULES_PATH.with_name('04-schools.md'),
    RULES_PATH.with_name('11-non_pc_schools.md'),
)

_ENTRY = re.compile(r'^- (?P<name>[A-Za-z][A-Za-z ]*?) (?P<value>\d+)$')
_SCHOOL_HEAD = re.compile(r'^#{2,3} (?P<name>[^\n#]+?)[ \t]*$', re.M)
_EXTRA_DIE = re.compile(r'^Roll one extra die on (?P<what>[^.\n]+)\.', re.M)

#: The free raises one skill hands another, PER RANK, on an NPC's roll. Written out
#: rather than parsed because the rules state them in prose, and because which ones
#: are AUTOMATIC is the GM's ruling rather than the rules' (2026-09-19):
#:
#: - acting -> sincerity and intimidation. NOT sneaking, where the rules make it
#:   conditional (*"sneaking rolls which are used to blend into crowds"*).
#: - history -> culture, law and strategy. NOT heraldry, where the rules limit it to
#:   *"places and families and institutions rather than specific individuals"*. The
#:   GM first called culture the conditional one, was shown the rules text, and
#:   corrected it: *"always apply it to culture and law and strategy. And then do
#:   not ever apply it to heraldry because I can do that for them when appropriate."*
#:
#: The conditional ones are the GM's to add by hand, and a hand bonus is never
#: adjusted by the tool.
AUTOMATIC_RAISES: dict[str, tuple[str, ...]] = {
    'acting': ('sincerity', 'intimidation'),
    'history': ('culture', 'law', 'strategy'),
}

#: Skills an NPC is never ROLLED in by the called form - `acting(2)` only records.
#: What they are for on an NPC is the raises above (GM 2026-09-19).
RECORD_ONLY = tuple(AUTOMATIC_RAISES)

FREE_RAISE = 5


def _split(gm_info: str) -> tuple[list[str], int, int]:
    """Lines of `gm_info` plus the [start, end) of the block; start -1 when absent."""
    lines = gm_info.replace('\r\n', '\n').split('\n')
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == HEADING)
    except StopIteration:
        return lines, -1, -1
    end = start + 1
    while end < len(lines) and lines[end].startswith('- '):
        end += 1
    return lines, start, end


def parse(gm_info: str) -> dict[str, int]:
    """The block's numbers, keyed by lowercased ring or skill name.

    A line that does not parse is skipped rather than raised on: the GM can edit
    these notes by hand, and one odd line must not cost them every other number.
    """
    lines, start, end = _split(gm_info)
    numbers: dict[str, int] = {}
    for line in lines[start + 1 : end] if start >= 0 else ():
        found = _ENTRY.match(line.strip())
        if found:
            numbers[found.group('name').strip().lower()] = int(found.group('value'))
    return numbers


def render(gm_info: str, numbers: Mapping[str, int]) -> str:
    """`gm_info` with the block replaced, or appended when there was none.

    Rings first, capitalized, in the rules' order; then skills in the order they
    were learned. With nothing to write the notes come back untouched - an empty
    heading would be noise on every NPC the GM ever spoke to.
    """
    if not numbers:
        return gm_info
    lines, start, end = _split(gm_info)
    rings = [f'- {ring.capitalize()} {numbers[ring]}' for ring in RINGS if ring in numbers]
    skills = [f'- {name} {value}' for name, value in numbers.items() if name not in RINGS]
    block = [HEADING, *rings, *skills]
    if start < 0:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ['', *block] if lines else block
    else:
        lines[start:end] = block
    return '\n'.join(lines)


def school_extra_dice(
    vocabulary: Sequence[str], paths: Sequence[Path] = SCHOOL_PATHS
) -> dict[str, frozenset[str]]:
    """school name (lowercased) -> the skills it rolls one extra die on.

    DERIVED from the rules text. Only names in `vocabulary` are kept, so "wound
    checks", "initiative" and the choose-your-own lines (*"any three types of
    rolls"*) fall away - the GM on those: *"I don't think that that will actually
    come up in practice."* A missing file contributes nothing.
    """
    words = {word.lower() for word in vocabulary}
    table: dict[str, frozenset[str]] = {}
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        heads = list(_SCHOOL_HEAD.finditer(text))
        for index, head in enumerate(heads):
            end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
            found = _EXTRA_DIE.search(text, head.end(), end)
            if found is None:
                continue
            items = re.split(r',|\band\b', found.group('what'))
            skills = frozenset(item.strip().lower() for item in items) & words
            if skills:
                table[head.group('name').strip().lower()] = skills
    return table


def find_schools(record: Mapping[str, object], schools: Sequence[str]) -> tuple[str, ...]:
    """Which of `schools` the Obsidian Portal record names.

    Mechanical, as the GM asked (*"we should be able to look for those strings
    mechanically"*): a school name matching a WHOLE tag, or a WHOLE line of the
    description or the GM-only notes, case-insensitively, with or without a trailing
    "school". Whole lines rather than substrings, because "merchant" inside a
    sentence of backstory is not a school.
    """
    tags = record.get('tags')
    candidates = [str(tag) for tag in tags] if isinstance(tags, (list, tuple)) else []
    for field in ('description', 'game_master_info'):
        candidates.extend(str(record.get(field) or '').replace('\r\n', '\n').split('\n'))
    seen = {re.sub(r'\s+school$', '', c.strip().lower()) for c in candidates}
    return tuple(school for school in schools if school.lower() in seen)


@dataclass(frozen=True)
class Reading:
    """What one roll says about the NPC: the ring its skill uses, and the rank."""

    skill: str
    ring_name: str
    ring: int
    rank: int


def infer(
    asked: tuple[int, int],
    skill: str,
    ring_name: str,
    *,
    extra_dice: int = 0,
    void_points: int = 0,
) -> Reading:
    """Read a pool AS ASKED FOR into a ring and a rank.

    `asked` is the pool before the ten-dice cap, because above ten dice the cap
    turns rolled dice into kept ones and the capped pool would read wrong.
    """
    rolled, kept = asked
    ring = kept - void_points
    rank = rolled - void_points - extra_dice - ring
    return Reading(skill=skill.lower(), ring_name=ring_name.lower(), ring=ring, rank=max(0, rank))


@dataclass(frozen=True)
class Disagreement:
    """A roll that does not match the record.

    `void_points` is non-zero only when a void point would explain it: the roll is
    off by EXACTLY 1k1 or 2k2 (GM 2026-09-19). Positive means THIS roll spent them;
    negative means the roll the record came from did.
    """

    reading: Reading
    recorded_ring: int | None
    recorded_rank: int | None
    void_points: int = 0

    @property
    def describe(self) -> str:
        parts = []
        if self.recorded_ring is not None and self.recorded_ring != self.reading.ring:
            ring = self.reading.ring_name.capitalize()
            parts.append(f'{ring} {self.recorded_ring} recorded, this roll says {self.reading.ring}')
        if self.recorded_rank is not None and self.recorded_rank != self.reading.rank:
            parts.append(
                f'{self.reading.skill} {self.recorded_rank} recorded, '
                f'this roll says {self.reading.rank}'
            )
        return '; '.join(parts)

    @property
    def void_answer(self) -> str:
        """The third answer, worded to the case, or '' when it does not apply."""
        if not self.void_points:
            return ''
        count = abs(self.void_points)
        spent = 'a void point' if count == 1 else f'{count} void points'
        who = 'This roll' if self.void_points > 0 else 'The previous roll'
        return f'{who} spent {spent}'


def compare(numbers: Mapping[str, int], reading: Reading) -> Disagreement | None:
    """None when the roll agrees with everything recorded (or nothing is)."""
    ring = numbers.get(reading.ring_name)
    rank = numbers.get(reading.skill)
    ring_differs = ring is not None and ring != reading.ring
    rank_differs = rank is not None and rank != reading.rank
    if not ring_differs and not rank_differs:
        return None
    void_points = 0
    if ring is not None and not rank_differs and abs(reading.ring - ring) in (1, 2):
        # One or two dice up (or down) in BOTH rolled and kept: the ring moved and
        # the rank did not, which is precisely what a void point looks like.
        void_points = reading.ring - ring
    return Disagreement(reading, ring, rank, void_points)


def accept(numbers: dict[str, int], reading: Reading) -> None:
    """Make the record say what this roll says."""
    numbers[reading.ring_name] = reading.ring
    numbers[reading.skill] = reading.rank


def fill(numbers: dict[str, int], reading: Reading) -> list[str]:
    """Record whatever this roll says that was not known; say what was added."""
    added = []
    if reading.ring_name not in numbers:
        numbers[reading.ring_name] = reading.ring
        added.append(f'{reading.ring_name.capitalize()} {reading.ring}')
    if reading.skill not in numbers:
        numbers[reading.skill] = reading.rank
        added.append(f'{reading.skill} {reading.rank}')
    return added


def automatic_raises(skill: str, numbers: Mapping[str, int]) -> list[tuple[str, int, int]]:
    """`(source skill, its rank, bonus)` for each automatic raise on `skill`."""
    return [
        (source, numbers[source], numbers[source] * FREE_RAISE)
        for source, targets in AUTOMATIC_RAISES.items()
        if skill.lower() in targets and numbers.get(source, 0) > 0
    ]
