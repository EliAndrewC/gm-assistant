"""The annotate menu: saying what a roll was for.

The GM's reason, which is the whole justification for holding rolls back:
*"if I look at my notes and I see that a character made a precepts roll, That
doesn't help me very much because I might not remember what the roll was about."*
So a Precepts 25 is worth nothing in the record without a sentence beside it, and
this is where that sentence comes from.

Etiquette never appears here - those are presumed to be introductions, so the
annotation would say the same thing every time.

CTRL-C DISCARDS EVERYTHING. Annotations are staged as the GM works and committed
only when they finish, so a Ctrl-C part way through a run of five leaves all five
unannotated rather than four annotated and one not. That is the literal reading of
the GM's *"having that not save anything"*, and it is the behavior most likely to
sting in play - flagged in the spec for confirmation once it has been used in
anger. Finishing normally (blank line at the roll prompt) commits what is done.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from l7r.repl import gmrolls
from l7r.repl.rolls import rules
from l7r.repl.rolls.models import Conversation, Roll

Ask = Callable[[str], str]


class Abandoned(Exception):
    """The GM pressed Ctrl-C. Nothing is saved."""


@dataclass(frozen=True)
class Decision:
    """One staged choice: annotate a roll, or throw it away.

    Staged rather than applied as the GM works, so a Ctrl-C part way through can
    discard the whole run - which is what the GM asked for.
    """

    note: str = ''
    discard: bool = False
    #: (opposing total, bonus to the player, bonus to the NPC) when contested.
    contest: tuple[int, int, int] | None = None


def _apply(roll: Roll, decision: Decision) -> Roll:
    """Turn a staged decision into the roll it produces."""
    if decision.discard:
        return replace(roll, discarded=True)
    if decision.contest is None:
        return replace(roll, note=decision.note)
    opposed, bonus_self, bonus_opposed = decision.contest
    return replace(
        roll,
        note=decision.note,
        opposed_total=opposed,
        bonus_self=bonus_self,
        bonus_opposed=bonus_opposed,
    )


def pending(conv: Conversation) -> list[tuple[int, Roll]]:
    """Every roll awaiting annotation, as (index into conv.rolls, roll)."""
    return [
        (index, roll)
        for index, roll in enumerate(conv.rolls)
        if rules.needs_annotation(roll) and roll.attributed
    ]


def _describe(roll: Roll) -> str:
    rank = f' @{roll.rank}' if roll.rank is not None else ''
    return f'{roll.character} {roll.skill} {roll.total}{rank}  ({roll.at:%H:%M:%S})'


def _prompt(ask: Ask, question: str) -> str:
    """Ask, turning Ctrl-C and Ctrl-D into one abandonment."""
    try:
        return ask(question).strip()
    except (KeyboardInterrupt, EOFError) as exc:
        raise Abandoned from exc


def _choose(ask: Ask, question: str, count: int, *, allow_blank: bool = False) -> int | None:
    """A 1-based menu choice. None when the GM finishes with a blank line."""
    while True:
        answer = _prompt(ask, question)
        if not answer and allow_blank:
            return None
        if answer.isdigit() and 1 <= int(answer) <= count:
            return int(answer) - 1
        print(
            f'  ? enter a number from 1 to {count}'
            + (', or blank to finish' if allow_blank else '')
        )


def _number(ask: Ask, question: str, default: int) -> int:
    """A signed number, defaulting to `default` on a blank line."""
    while True:
        answer = _prompt(ask, question)
        if not answer:
            return default
        try:
            return int(answer)
        except ValueError:
            print('  ? a whole number, or blank to accept the default')


def _opposing(ask: Ask, roll: Roll, mine: Sequence[gmrolls.GmRoll]) -> tuple[int, int, int] | None:
    """Pick the opposing roll and the bonus each side gets. None falls back to open.

    Returns `(opposing total, bonus to the player, bonus to the NPC)`.

    The default bonus is the free raises the rules grant - one per point of skill
    difference, five each (`rules/02-skills.md:64` and :66). The player's skill comes
    from the rank the character-sheet app recorded when it has one, which is EXACT;
    the NPC's is inferred from their pool, which is not. Either can be overridden,
    which is the whole reason the GM asked for the prompt.
    """
    if not mine:
        print('  You have no recent rolls to contest against. Recording it as open.')
        return None
    print('  Your recent rolls:')
    for position, entry in enumerate(mine, start=1):
        print(f'    {position}. {entry.describe()}  [implies {entry.skill}]')
    chosen = _choose(ask, '  Which of yours? (number) > ', len(mine))
    assert chosen is not None  # allow_blank is False
    opponent = mine[chosen]
    theirs, ours = rules.free_raises(roll.rank, opponent.skill)
    if roll.rank is None:
        print(f'  {roll.character} has no recorded rank, so no free raises are inferred.')
    else:
        print(f'  Free raises: {roll.character} {roll.skill} {roll.rank} vs yours {opponent.skill}')
    bonus_self = _number(ask, f'  Bonus to {roll.character}? [{theirs}] > ', theirs)
    bonus_opposed = _number(ask, f'  Bonus to your side? [{ours}] > ', ours)
    return opponent.total, bonus_self, bonus_opposed


def annotate(
    conversation: Conversation | None = None,
    *,
    ask: Ask = input,
    mine: Callable[[], Sequence[gmrolls.GmRoll]] = gmrolls.recent,
) -> int:
    """Say what each waiting roll was for. Returns how many were annotated.

    Loops rather than taking one roll per call, because rolls arrive in rounds and
    annotating them one call at a time would be tedious in exactly the moment the
    GM is busiest.
    """
    from l7r.repl.rolls.conversation import require_open

    conv = conversation if conversation is not None else require_open()
    waiting = pending(conv)
    if not waiting:
        print('Nothing waiting to be annotated.')
        return 0

    staged: dict[int, Decision] = {}
    try:
        while True:
            waiting = [item for item in pending(conv) if item[0] not in staged]
            if not waiting:
                break
            if len(waiting) == 1:
                index, roll = waiting[0]
            else:
                print(f'Rolls waiting to be annotated for {conv.npc_name}:')
                for position, (_, candidate) in enumerate(waiting, start=1):
                    print(f'  {position}. {_describe(candidate)}')
                choice = _choose(
                    ask,
                    'Which roll? (number, or blank to finish) > ',
                    len(waiting),
                    allow_blank=True,
                )
                if choice is None:
                    break
                index, roll = waiting[choice]
            print(f'  {_describe(roll)}')
            # Blank finishes here as well as at the roll prompt. With one roll left
            # the "which?" question is skipped, and without this the GM would have no
            # way to stop except Ctrl-C - which discards everything already staged.
            kind = ''
            while kind not in ('o', 'c', 'd'):
                kind = _prompt(
                    ask, '  Open, contested, or discard? [o/c/d, blank to finish] > '
                ).lower()[:1]
                if not kind:
                    break
            if not kind:
                break
            if kind == 'd':
                staged[index] = Decision(discard=True)
                print('  staged: discarded')
                continue
            opposed = _opposing(ask, roll, list(mine())) if kind == 'c' else None
            note = ''
            while not note:
                note = _prompt(ask, '  What was it for? > ')
            staged[index] = Decision(note=note, contest=opposed)
            shown = _apply(roll, staged[index])
            print(f'  staged: {rules.render_annotated(shown, conv.npc_name)}')
    except Abandoned:
        # "discarded" would read as the roll-discard feature, which this is not:
        # the rolls are all still there, unannotated, and annotate() can be re-run.
        print(
            f'\nCtrl-C - nothing saved ({len(staged)} choice(s) abandoned). '
            'The rolls are untouched; run annotate() again when you are ready.'
        )
        return 0

    for index, decision in staged.items():
        conv.rolls[index] = _apply(conv.rolls[index], decision)
    discarded = sum(1 for decision in staged.values() if decision.discard)
    kept = len(staged) - discarded
    tail = f', {discarded} discarded' if discarded else ''
    print(f'Annotated {kept} roll(s){tail}.')
    return len(staged)
