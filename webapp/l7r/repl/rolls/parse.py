"""Read a hand-typed roll out of a Discord message.

A third of the rolls in the GM's channels are typed rather than pasted, and the
split is per PLAYER, not per group (research.md R2) - so this is a primary path,
not a fallback, and it is the only path that works with no character-sheet
endpoint at all.

WHAT THE CORPUS ACTUALLY CONTAINS (research.md R3, three passes over 1,400 real
messages). Every one of these is a real message:

    38 Etiquette @3                 23 Investigation@2        35 Interrogation
    52 law@3 to argue that...       24 eti                    20 Underworld at 2
    26@3 Etiquette                  @27 Tact                  65@4 Intimidation
    43 Interrogation@3 (38 + 5 Discerning)
    15 etiquette (24, limited by Withdrawn)
    10->9 8 +5 Streetwise = 32 Law@2
    10->10->10->4  10->8 5 4=61+5=66 Sincerity@1
    30 investigation@3, 36 Interrogation@3: where is Tsuruchi Kyoma, really?

THE RULE THAT MAKES THIS SAFE: a number is a roll only when a REAL SKILL NAME sits
beside it. The channels are full of numbers that are not rolls, and the negatives
are adversarial rather than incidental (research.md R5) - dates (`22 December
2022`), session counts (`There were 85 sessions`), ring scores (`Fire 5, Air 4,
Water 6, Void 5, and 8 Earth`), rules discussion (`the -10 to Culture`, which
names a genuine skill), loose dice (`6 9 6 9`), and the GM's own pasted REPL
output. Requiring the skill kills almost all of them; the three guards below kill
the rest.

The cost of being wrong here is asymmetric, which is why every uncertain case is
REPORTED rather than resolved. A roll we miss is a line the GM adds by hand, as
they do today. A roll we invent is a false entry in an NPC's permanent record,
and nothing downstream will ever question it.
"""

from __future__ import annotations

import re
from datetime import datetime

from l7r.repl.rolls.models import Roll
from l7r.repl.rolls.skills import AmbiguousSkill, UnknownSkill, match_skill

#: A total below this is not treated as a roll. The lowest total actually observed
#: in the corpus is 10 (`10 heraldry, what do I know about Shiro Reiji?`), while
#: `Two people have 1 Interrogation each` is a statement about RANKS that reads
#: exactly like a roll. The floor separates them. It costs nothing real: a total
#: under 10 means every die came up near 1, and the GM records it as 5 or 0.
MIN_TOTAL = 10

#: Skill ranks stop at 5 - `rules/01-character_creation.md`: "Every skill begins at
#: 0 and must be raised 1 point at a time, to a maximum of 5", and the one knack
#: that raises a rank mid-roll (`rules/05-school_knacks.md`) also stops at five.
MAX_RANK = 5

#: `@N` is overloaded. It normally means rank, but `@27 Tact` is a real message
#: where it means the total. Magnitude decides, and the band between the two is
#: reported rather than guessed: no rank can exceed 5 and no observed total is
#: below 10, so 6-9 is empty in practice - but it is empty by luck, not by rule.
AMBIGUOUS_AT = range(MAX_RANK + 1, MIN_TOTAL)

#: Discord markup that carries digits and would otherwise offer them to the parser:
#: user mentions `<@123...>`, custom emoji `<:name:123...>`, channel links, and URLs.
_NOISE = re.compile(r'<[@#:!&][^>]*>|https?://\S+|`[^`]*`', re.S)

#: Parenthesized spans hold the player's own BREAKDOWN of a total, never the total
#: itself: `50 sincerity@5 (30 + 5 Second Dan + 15 Acting)`, `24 Underworld (13 + 5
#: Streetwise + 5 Worldly)`, `43 Interrogation@3 (38 + 5 Discerning)`. Every one of
#: those names a skill INSIDE the parentheses as a bonus source, and the first
#: measured run read `15 Acting` out of the first example as a second roll. The
#: recorded total is always outside the brackets, so the brackets are removed
#: before matching. Measured 2026-08-28: this alone removed 2 of 3 false positives.
_BREAKDOWN = re.compile(r'\([^)]*\)')

_RANK = r'(?:@\s*(?P<{0}>\d{{1,2}})|\bat\s+(?P<{1}>\d{{1,2}})\b)'

#: total, optional rank, skill, optional rank. The lookbehind refuses a number that
#: is part of a larger token or carries a minus sign, which is what keeps
#: `the -10 to Culture` and `06/20/2023` from reading as rolls.
#: A `+` before the number means it is an ADDEND in the player's arithmetic, not the
#: result: `31+15acting+10 for two free raises` parsed as "acting 15" on the first
#: measured run, when 15 is a bonus and `acting` names its source. Legitimate totals
#: are never `+`-prefixed - the corpus writes them after `=` or after a space
#: (`...=61+5=66 Sincerity@1`, `+15 65@4 Intimidation`), both of which still match.
#:
#: `[^\S\n]` rather than `\s`: a cluster must NOT span a newline. `Intimidation 8k4
#: +15\nInterrogation 7k4 +5` is two lines of pool notation, and the first run paired
#: the `15` ending line one with the `Interrogation` opening line two.
_CLUSTER = re.compile(
    r'(?<![-+@\w.:/])(?P<total>\d{1,3})[^\S\n]*'
    + _RANK.format('r1', 'r1b')
    + r'?[^\S\n]*(?P<skill>[A-Za-z][A-Za-z]{2,19})\b[^\S\n]*'
    + _RANK.format('r2', 'r2b')
    + r'?',
    re.I,
)

#: The leading-`@` form: `@27 Tact`. `@` is excluded from the main cluster's
#: lookbehind above so this form is matched HERE and only here - otherwise both
#: patterns fire on the same text and the roll is recorded twice (measured, and it
#: is why `claimed` alone was not enough: the two matches start one character apart).
_AT_FIRST = re.compile(r'@\s*(?P<total>\d{1,3})\s*(?P<skill>[A-Za-z][A-Za-z]{2,19})\b', re.I)


class Unparsed(ValueError):
    """A message that looks like a roll but could not be read with confidence."""


def _rank_of(match: re.Match[str]) -> int | None:
    for group in ('r1', 'r1b', 'r2', 'r2b'):
        value = match.groupdict().get(group)
        if value is not None:
            return int(value)
    return None


def parse_message(
    text: str,
    vocabulary: tuple[str, ...],
    *,
    character: str = '',
    message_id: str = '',
    at: datetime | None = None,
) -> tuple[list[Roll], list[str]]:
    """Extract every roll in one message.

    Returns `(rolls, problems)`. `problems` holds a human-readable line for each
    thing that looked like a roll but was not resolved - an ambiguous skill
    abbreviation, an `@N` in the ambiguous band, a rank above the maximum. Those
    go to the GM at the end of the conversation rather than into the record.
    """
    when = at or datetime.now().astimezone()
    clean = _BREAKDOWN.sub(' ', _NOISE.sub(' ', text or ''))
    rolls: list[Roll] = []
    problems: list[str] = []
    claimed: set[int] = set()

    for match in _CLUSTER.finditer(clean):
        total = int(match.group('total'))
        rank = _rank_of(match)
        skill = _resolve(match.group('skill'), vocabulary, problems)
        if skill is None:
            continue
        if total < MIN_TOTAL:
            continue
        if rank is not None and rank > MAX_RANK:
            problems.append(
                f'{match.group(0).strip()!r}: rank {rank} is above the maximum of '
                f'{MAX_RANK}, so this was not recorded'
            )
            continue
        claimed.update(range(match.start(), match.end()))
        rolls.append(
            Roll(
                character=character,
                skill=skill,
                total=total,
                source='typed',
                message_id=message_id,
                at=when,
                rank=rank,
            )
        )

    for match in _AT_FIRST.finditer(clean):
        if match.start() in claimed:
            continue
        value = int(match.group('total'))
        skill = _resolve(match.group('skill'), vocabulary, problems)
        if skill is None:
            continue
        if value in AMBIGUOUS_AT:
            problems.append(
                f'{match.group(0).strip()!r}: @{value} could be a rank or a total '
                f'(ranks stop at {MAX_RANK}, totals start around {MIN_TOTAL}); not recorded'
            )
            continue
        if value <= MAX_RANK:
            continue
        rolls.append(
            Roll(
                character=character,
                skill=skill,
                total=value,
                source='typed',
                message_id=message_id,
                at=when,
            )
        )

    return rolls, problems


def _resolve(word: str, vocabulary: tuple[str, ...], problems: list[str]) -> str | None:
    """Resolve a possible skill word, recording an ambiguity as a problem.

    An unknown word is silent: most words in a sentence are not skills, and
    reporting each one would bury the real problems. An AMBIGUOUS one is reported,
    because the writer meant a skill and we could not tell which.
    """
    try:
        return match_skill(word, vocabulary)
    except AmbiguousSkill as exc:
        problems.append(str(exc))
    except UnknownSkill:
        pass
    return None
