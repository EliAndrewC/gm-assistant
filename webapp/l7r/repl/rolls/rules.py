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

**Six skills contest a DIFFERENT skill, and one side of each pair takes the tie.**
Everything else contests ITSELF, and a tie there is a real tie. See
`CONTESTED_PAIRS` for the three pairings, the tie rule, and the GM's words - the
part worth having up here is WHY it is a table rather than a question the GM gets
asked: the pairing is total. *"if you see a player post one of those six skills and
then you see me record that as a contested roll against an NPC's roll, you may
always assume that the corresponding skill is what the NPC rolled. This will always
be true"* (GM 2026-09-02). So the opposing skill is DERIVED at render time from the
player's, never stored on the roll and never prompted for.

**Only the personal name is written down.** The GM records `Tetsuro`, never
`Tsuruchi Tetsuro` (2026-09-02). Every roll in a conversation is by a player
character the GM knows on sight, so the family name is four syllables of noise on
every line of a format whose whole point is to be read at a glance - and a party
drawn mostly from one family (`Tsuruchi Tetsuro / Tsuruchi Toshihiro / Tsuruchi
Sadakichi / Tsuruchi Jimen`) repeats it until the names it is supposed to
distinguish are the shortest part of the line.

This is a RECORDING rule, which is why it lives here rather than in the parser:
the full name is still what joins a Discord account to a character, what dedups a
pasted card against a typed roll, and what matches the bot's `**Name**:` prefix.
It is trimmed at the moment of writing and nowhere earlier.

**An annotated open roll leads with the number.** `40 law: Jimen assessing whether
the arrest was lawful`, not `Jimen law: 40 - ...` (2026-09-02). The GM asked for
this shape for the annotated open rolls specifically; a CONTESTED line keeps its
own order, because the thing it has to say first is which two rolls were compared.

**No line separates its note with a dash** (GM 2026-09-02, both formats). On the
open line the note follows a NAME and reads straight on from it; on the contested
line it follows the margin, and the GM's fix for the number running into the note
was to give the clause a VERB rather than a separator - `Jimen wins by >=10
arguing it is wrong to lie to a magistrate to save face`. The `wins` is doing the
work the `-` used to, so do not put the dash back alongside it.

Note what the cap does NOT do: it applies to OPEN etiquette rolls only, which is
the GM's literal scope. That was queried, and the answer closes it rather than
narrowing it - **there is no such thing as a contested etiquette roll** (GM
2026-08-28: *"there is no contested etiquette so that can't happen"*). The case the
cap does not cover cannot arise, so the scoping is not a gap and does not want a
guard. Recorded here because the question looks live to anyone reading the rule.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

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


#: The three skills that are never rolled against themselves, each paired with the
#: skill that opposes it. **The FIRST of each pair takes a tie**; the second needs
#: to beat it outright. The GM (2026-09-02): *"the advanced skill actually wins when
#: it ties the basic skill. So an interrogation roll succeeds when it ties the
#: sincerity roll ... while both investigation and sneaking are basic skills, in the
#: case of a tie, investigation wins rather than sneaking winning."*
#:
#: All three pairings are in the rules: interrogation *"contested against the
#: sincerity of an NPC"* (`rules/02-skills.md:213`), manipulation *"contested
#: against another character's tact"* (:243), sneaking *"contested against the
#: investigation of potential observers"* (:271).
#:
#: The rules corroborate the TIE rule for manipulation and are silent on the other
#: two: manipulation's own result table opens at delta **`0 - 9`** (:247), so a
#: nothing-between-them roll is already a manipulator success. Interrogation's
#: prose reads the other way - *"Exceeding the opposing sincerity roll tells you
#: whether the other person is lying"* (:217) - which taken strictly would make a
#: tie a failure for the interrogator. **That is a wording imprecision in the rules
#: file, not a rule we are overriding**: the GM ruled directly on it and the
#: manipulation table shows the intended pattern for an advanced-vs-basic pairing.
#: Raised with the GM 2026-09-02; do not "fix" this table to match :217.
CONTESTED_PAIRS = (
    ('interrogation', 'sincerity'),
    ('manipulation', 'tact'),
    ('investigation', 'sneaking'),
)

#: skill -> the skill it is contested against. DERIVED from `CONTESTED_PAIRS` in
#: both directions rather than written out, so a fourth pairing is one row above and
#: nothing else - a hand-maintained mirror of a table is a table that goes stale on
#: one side only.
OPPOSING_SKILL = {a: b for pair in CONTESTED_PAIRS for a, b in (pair, pair[::-1])}

#: skill -> which skill of its pair takes a tie. Absent means the skill contests
#: itself, where a tie is a genuine tie.
TIE_WINNER = {skill: pair[0] for pair in CONTESTED_PAIRS for skill in pair}

#: Which side of a contest won. `None` is a real tie.
Side = Literal['mine', 'theirs']


def opposing_skill(skill: str) -> str:
    """What the other side rolled, given what this side rolled.

    One of the three pairings, or the same skill back - *"if any other skill besides
    those six skills is marked as having been rolled contested, then you may always
    assume that the NPC rolled the same skill that the player character did"* (GM
    2026-09-02).
    """
    return OPPOSING_SKILL.get(skill.lower(), skill.lower())


def contested_winner(mine_skill: str, theirs_skill: str, mine: int, theirs: int) -> Side | None:
    """Which side won, resolving a tie by the skills involved.

    A tie between a skill and ITSELF is a tie. A tie across one of the three
    pairings goes to the side named first in `CONTESTED_PAIRS`, and is recorded as
    a win by the smallest margin band rather than as a draw.

    Both skills are named rather than just one so that a mismatched pair - a call
    that opposes sincerity to law, which the pairing rule says cannot happen -
    resolves to a tie rather than silently handing the win to whichever side the
    half-matching rule mentions first.
    """
    if mine != theirs:
        return 'mine' if mine > theirs else 'theirs'
    won = TIE_WINNER.get(mine_skill.lower())
    if won is None or {mine_skill.lower(), theirs_skill.lower()} != set((won, OPPOSING_SKILL[won])):
        return None
    return 'mine' if won == mine_skill.lower() else 'theirs'


def skills_text(mine_skill: str, theirs_skill: str) -> str:
    """How the skill(s) are named on a contested line.

    One name when both sides rolled the same skill, which is the GM's own shape.
    BOTH names when they differ, because otherwise a tie-break reads as a bare
    contradiction - `30 vs 30, Otsuki wins` is only sensible once you can see that
    the 30s were an interrogation and a sincerity. Everything on the line then runs
    left-vs-right in the same order: names, skills, totals.
    """
    if mine_skill.lower() == theirs_skill.lower():
        return mine_skill.lower()
    return f'{mine_skill.lower()} vs {theirs_skill.lower()}'


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


def personal_name(name: str) -> str:
    """The part of a character's name the GM writes down: `Tsuruchi Jimen` -> `Jimen`.

    A Rokugani name runs family-first, so the personal name is the LAST token. That
    holds for the compound forms too - `Hida no Reiji Kazuma` gives `Kazuma` - and a
    name that is already one word (a monk, a peasant, an NPC the GM entered as
    `Otsuki`) passes through untouched, which is what makes this safe to apply
    unconditionally at render time.

    Deliberately no roster lookup and no attempt to verify that the leading tokens
    really are a family name. There is no list to check against that would not
    itself go stale, and the failure mode of the naive rule is that an unusual name
    loses a word the GM can still read past; the failure mode of a lookup is that a
    name missing from the list is written differently from every other line.
    """
    parts = name.split()
    return parts[-1] if parts else ''


#: The margin bands the GM records a contested victory in (2026-08-29). NOT the
#: same as rounding an open roll down to 5, and it replaces the earlier "round the
#: margin down to the nearest 5" from feature 201's FR-012.
#:
#: The GM's reason is that these are BREAK POINTS, not measurements: what matters is
#: which band you cleared, and the bands get coarser as they get higher. Their
#: words: *"we round to five for low numbers, but then when it comes to higher
#: amounts, we start doing increments of ten... you beat him by at least ten, or you
#: beat him by at least twenty."*
#:
#: It also fixes a wart the old rule produced: a win by 2 rounded down to "by 0",
#: which reads as no victory at all. It is now "by <5" - a win, in the smallest band.
def margin_text(margin: int) -> str:
    """How a contested victory margin is written down.

    0-4   -> <5        (a win, but inside the smallest band)
    5-9   -> <10
    10-19 -> >=10      (from here up, bands of ten)
    20-29 -> >=20
    """
    if margin < 5:
        return '<5'
    if margin < 10:
        return '<10'
    return f'>={(margin // 10) * 10}'


def contest(left: Roll, right: Roll, rule: RecordingRule = DEFAULT_RULE) -> Contest:
    """Score one roll against another. Totals stay raw, and so does the margin -
    the banding in `margin_text` is presentation, applied when it is written.

    A tie is resolved by `contested_winner`, so an interrogation that ties a
    sincerity is a WIN with a margin of 0 rather than a draw.
    """
    margin = abs(left.total - right.total)
    side = contested_winner(left.skill, right.skill, left.total, right.total)
    winner = None if side is None else (left if side == 'mine' else right).character
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
    names = ' / '.join(personal_name(r.character) for r in usable)
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

        40 law: Jimen assessing whether the arrest was lawful
        Jimen vs Otsuki sincerity: 41 vs 28, Jimen wins by >=10 claiming he never met the man

    THE TWO ORDERS ARE DIFFERENT ON PURPOSE (2026-09-02, and see the module
    docstring). The open line leads with the number, because that is the GM's own
    shape for it; the contested line leads with the pairing, because `41 vs 28`
    means nothing until you know who the two sides were. Do not harmonize them.
    Neither takes a dash before its note.

    An OPEN roll is rounded like any other. A CONTESTED one keeps both totals raw and
    rounds only the margin, which is the GM's rule from feature 201 - the annotation
    changes what is said about a roll, never how its number is recorded.

    A roll with no note renders the same line minus the note - that is the forced
    close on interpreter exit, which writes bare rolls rather than losing them.
    """
    who = personal_name(roll.character)
    if roll.opposed_total is None:
        shown = record(roll.total + roll.bonus_self, roll.skill, rule)
        tail = f' {roll.note}' if roll.annotated else ''
        return f'{shown} {roll.skill.lower()}: {who}{tail}'
    # Each side AFTER its own bonus - feature 201's rule ("adjusted for bonuses on
    # each side") and the GM's per-side insistence are the same requirement.
    tail = f' {roll.note}' if roll.annotated else ''
    them = personal_name(npc)
    mine, theirs = roll.final_total, roll.final_opposed or 0
    # The NPC's skill is DERIVED, never stored and never asked for: the pairing is
    # total, so the player's skill determines it (GM 2026-09-02).
    their_skill = opposing_skill(roll.skill)
    side = contested_winner(roll.skill, their_skill, mine, theirs)
    if side is None:
        outcome = 'tied'
    else:
        winner = who if side == 'mine' else them
        outcome = f'{winner} wins by {margin_text(abs(mine - theirs))}'
    skills = skills_text(roll.skill, their_skill)
    return f'{who} vs {them} {skills}: {mine} vs {theirs}, {outcome}{tail}'


def render_contest(scored: Contest) -> str:
    """One contested roll, with no note on it.

        Jimen vs Otsuki sincerity: 41 vs 28, Jimen wins by >=10

    The sentence is now the GM's own (2026-09-02) rather than this feature's guess
    at it - the same clause `render_annotated` builds, so the two stay one format.
    """
    left, right = scored.left, scored.right
    head = (
        f'{personal_name(left.character)} vs {personal_name(right.character)} '
        f'{skills_text(left.skill, right.skill)}: {left.total} vs {right.total}'
    )
    if scored.tied:
        return f'{head}, tied'
    return f'{head}, {personal_name(scored.winner or "")} wins by {margin_text(scored.margin)}'
