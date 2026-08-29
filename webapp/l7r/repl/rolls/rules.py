"""The GM's recording rules: what a raw total becomes when it is written down.

These are NOT game rules. Nothing here decides what a roll achieves at the table -
that is the rules engine's job and it lives in the character-sheet repository.
These are the GM's note-taking conventions, which is why they live next to the
thing that writes the notes.

THE RULES, AND WHY EACH ONE IS WHAT IT IS
-----------------------------------------

**Round down to the nearest 5.** The GM: *"Open roles, I do not distinguish
between, for example, a twenty five and a twenty eight."* Recording 28 implies a
precision the GM does not act on.

**Etiquette is capped at 40 before rounding.** The GM's reasoning, recorded here
because the rule is meaningless without it and the next reader will otherwise
"fix" it: *"there is an upper limit to how much appropriate politeness you can
display. Because politeness involves restraint, a very high role on etiquette
simply cannot represent something extremely noteworthy because a thing which is
noteworthy in most circumstances is almost definitionally impolite. Whereas this
is not true for other skills. A gift can be perfunctory or a gift can be
noteworthy. A gift can be so exceptional that someone will talk about it for their
whole life."* So the ceiling is a property of what etiquette CAN express, not a
clamp on the dice - which is why it belongs to the skill and not to the roll, and
why adding another capped skill is one entry in `RecordingRule.caps`.

The cap applies BEFORE rounding. It happens not to matter at 40 (a multiple of 5),
but it would at any cap that is not, and the order is the GM's: *"if someone rolled
a sixty eight, I would simply write down forty"* - cap first, then the increment.

**Contested rolls keep both totals and round only the margin.** The GM: *"show each
of the two roles that are being compared after those roles are adjusted for bonuses
on each side. and then it should show the difference between them and who won. The
amount that the winner won by should be rounded down to the nearest increment of
five ... but the rolls themselves are not rounded."*

Note what the cap does NOT do: it applies to OPEN etiquette rolls only, which is
the GM's literal scope. That was queried, and the answer closes it rather than
narrowing it - **there is no such thing as a contested etiquette roll** (GM
2026-08-28: *"there is no contested etiquette so that can't happen"*). The case the
cap does not cover cannot arise, so the scoping is not a gap and does not want a
guard. Recorded here because the question looks live to anyone reading the rule.
"""

from __future__ import annotations

from collections.abc import Sequence

from l7r.repl.rolls.models import Contest, RecordingRule, Roll

DEFAULT_RULE = RecordingRule()

#: Skills whose rolls are written WITHOUT annotation. The GM: *"we have not bothered
#: to do this with etiquette because etiquette roles are presumed to be about making
#: an introduction. So, therefore, the annotation is redundant because almost every
#: etiquette role is the same."* Etiquette is the only one they named; another is one
#: entry here, the same way another cap is one entry in `RecordingRule.caps`.
EXEMPT_FROM_ANNOTATION = frozenset({'etiquette'})


#: A free raise adds 5 - `rules/02-skills.md:66`.
FREE_RAISE = 5


def needs_annotation(roll: Roll) -> bool:
    """True when this roll must not be written until the GM says what it was for.

    A DISCARDED roll needs nothing: the GM has said it was a mistake, so it is
    neither written nor allowed to hold the conversation open.
    """
    if roll.discarded:
        return False
    return roll.skill.lower() not in EXEMPT_FROM_ANNOTATION and not roll.annotated


def free_raises(mine: int | None, theirs: int | None) -> tuple[int, int]:
    """The contest bonus each side gets from the skill difference.

    `rules/02-skills.md:64`: *"you get a free raise for every point your character's
    skill is higher than your opponent's"*, and each raise adds 5 (line 66). Returns
    `(bonus to mine, bonus to theirs)`, one of which is always zero.

    Unknown skill on either side means no inferred bonus - a guess here would be
    worse than nothing, since the GM would have to notice it was wrong to override
    it.
    """
    if mine is None or theirs is None:
        return (0, 0)
    gap = mine - theirs
    if gap > 0:
        return (gap * FREE_RAISE, 0)
    return (0, -gap * FREE_RAISE)


def round_down(total: int, increment: int = 5) -> int:
    """Round down to the nearest `increment`, never below zero.

    Negative totals do not arise from the game - a roll is a sum of dice - but a
    mis-parse could produce one, and floor division would round -3 to -5, making a
    parse error look like a real result. Clamping at zero keeps a bad parse
    obviously bad.
    """
    if increment <= 0:
        raise ValueError(f'increment must be positive, got {increment}')
    if total <= 0:
        return 0
    return (total // increment) * increment


def record(total: int, skill: str, rule: RecordingRule = DEFAULT_RULE) -> int:
    """The number that gets written down for an open roll: cap, then round."""
    capped = min(total, rule.caps.get(skill.lower(), total))
    return round_down(capped, rule.increment)


def contest(left: Roll, right: Roll, rule: RecordingRule = DEFAULT_RULE) -> Contest:
    """Score one roll against another. Totals stay raw; only the margin rounds."""
    margin = round_down(abs(left.total - right.total), rule.increment)
    if left.total == right.total:
        winner = None
    else:
        winner = (left if left.total > right.total else right).character
    return Contest(left=left, right=right, winner=winner, margin=margin)


def render_open(rolls: Sequence[Roll], rule: RecordingRule = DEFAULT_RULE) -> str:
    """The GM's shorthand for a round of open rolls (FR-021).

        Sadakichi / Moriko / Jimen / Tetsuro / Toshihiro etiquette: 35 / 25 / 25 / 20 / 15

    Every roll in the line must share a skill - the skill is named once, after the
    names - and every roll must be attributed, since the format pairs each total
    with a name.
    """
    usable = [r for r in rolls if r.attributed]
    if not usable:
        raise ValueError('no attributed rolls to render')
    skills = {r.skill.lower() for r in usable}
    if len(skills) > 1:
        raise ValueError(f'one line holds one skill, got: {", ".join(sorted(skills))}')
    # HIGHEST FIRST. CONFIRMED BY THE GM (2026-08-28): *"ordering rolls from highest
    # to lowest is intentional"*. It was originally inferred from their one worked
    # example running 35 / 25 / 25 / 20 / 15 - perfectly descending, which five rolls
    # land on by chance about once in 120 times - against the competing reading that
    # the names were in a habitual party order. The inference was right; this is now
    # an instruction, not a guess, so do not "restore" posting order.
    usable = sorted(usable, key=lambda r: record(r.total, r.skill, rule), reverse=True)
    names = ' / '.join(r.character for r in usable)
    totals = ' / '.join(str(record(r.total, r.skill, rule)) for r in usable)
    return f'{names} {usable[0].skill.lower()}: {totals}'


def render_lines(
    rolls: Sequence[Roll],
    npc: str = '',
    rule: RecordingRule = DEFAULT_RULE,
    *,
    include_unannotated: bool = False,
) -> list[str]:
    """Everything this conversation should write, in the shape the GM reads.

    Two kinds of line, deliberately different:

    - **Exempt skills** (Etiquette) are GROUPED, one line per skill, highest-first -
      a round of introductions read at a glance, which is feature 201's format and
      the GM confirmed the ordering was intentional.
    - **Annotated rolls** are listed INDIVIDUALLY in the order they were made, each
      with what it was for. That order is the point: *"remember the conversation by
      seeing these sequence of rolls that were made."*

    A roll that needs annotation and has not had it is NOT rendered at all. Holding
    it back is the feature, not an omission - `end_conversation` refuses to close
    while any are waiting, and only the exit hook writes them bare.
    """
    order: list[str] = []
    groups: dict[str, list[Roll]] = {}
    for roll in rolls:
        if not roll.attributed or roll.discarded:
            continue
        if needs_annotation(roll) and not include_unannotated:
            continue
        if roll.skill.lower() not in EXEMPT_FROM_ANNOTATION:
            continue
        key = roll.skill.lower()
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(roll)
    lines = [render_open(groups[key], rule) for key in order]
    lines += [
        render_annotated(roll, npc, rule)
        for roll in rolls
        if roll.attributed
        and not roll.discarded
        and roll.skill.lower() not in EXEMPT_FROM_ANNOTATION
        and (roll.annotated or include_unannotated)
    ]
    return lines


def render_annotated(roll: Roll, npc: str, rule: RecordingRule = DEFAULT_RULE) -> str:
    """One annotated roll, with what it was for.

        Jimen law: 40 - assessing whether the arrest was lawful
        Jimen vs Otsuki sincerity: 41 vs 28, Jimen by 10 - claiming he never met the man

    An OPEN roll is rounded like any other. A CONTESTED one keeps both totals raw and
    rounds only the margin, which is the GM's rule from feature 201 - the annotation
    changes what is said about a roll, never how its number is recorded.
    """
    tail = f' - {roll.note}' if roll.annotated else ''
    if roll.opposed_total is None:
        shown = record(roll.total + roll.bonus_self, roll.skill, rule)
        return f'{roll.character} {roll.skill.lower()}: {shown}{tail}'
    # Each side AFTER its own bonus - feature 201's rule ("adjusted for bonuses on
    # each side") and the GM's per-side insistence are the same requirement.
    mine, theirs = roll.final_total, roll.final_opposed or 0
    margin = round_down(abs(mine - theirs), rule.increment)
    if mine == theirs:
        outcome = 'tied'
    else:
        winner = roll.character if mine > theirs else npc
        outcome = f'{winner} by {margin}'
    return f'{roll.character} vs {npc} {roll.skill.lower()}: {mine} vs {theirs}, {outcome}{tail}'


def render_contest(scored: Contest) -> str:
    """One contested roll.

        Jimen vs Otsuki sincerity: 41 vs 28, Jimen by 10

    The wording is this feature's choice rather than the GM's - they specified the
    four elements (both adjusted totals, the difference, the winner) but not the
    sentence. Recorded in the spec's Assumptions as trivially adjustable.
    """
    left, right = scored.left, scored.right
    head = (
        f'{left.character} vs {right.character} {left.skill.lower()}: {left.total} vs {right.total}'
    )
    if scored.tied:
        return f'{head}, tied'
    return f'{head}, {scored.winner} by {scored.margin}'
