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
from dataclasses import replace

from l7r.repl import gmrolls
from l7r.repl.rolls import rules
from l7r.repl.rolls.models import Conversation, Roll

Ask = Callable[[str], str]


class Abandoned(Exception):
    """The GM pressed Ctrl-C. Nothing is saved."""


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


def _contested_total(ask: Ask, mine: Sequence[gmrolls.GmRoll]) -> int | None:
    """Which of the GM's own rolls opposed this one. None falls back to open."""
    if not mine:
        print('  You have made no rolls this conversation, so there is nothing to contest')
        print('  against. Recording it as open.')
        return None
    print('  Your rolls this conversation:')
    for position, entry in enumerate(mine, start=1):
        print(f'    {position}. {entry.describe()}')
    chosen = _choose(ask, '  Which of yours? (number) > ', len(mine))
    assert chosen is not None  # allow_blank is False
    return mine[chosen].total


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

    staged: dict[int, tuple[str, int | None]] = {}
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
            while kind not in ('o', 'c'):
                kind = _prompt(ask, '  Open or contested? [o/c, blank to finish] > ').lower()[:1]
                if not kind:
                    break
            if not kind:
                break
            opposed = _contested_total(ask, list(mine())) if kind == 'c' else None
            note = ''
            while not note:
                note = _prompt(ask, '  What was it for? > ')
            staged[index] = (note, opposed)
            shown = replace(roll, note=note, opposed_total=opposed)
            print(f'  staged: {rules.render_annotated(shown, conv.npc_name)}')
    except Abandoned:
        print(f'\nCtrl-C - nothing annotated ({len(staged)} discarded).')
        return 0

    for index, (note, opposed) in staged.items():
        conv.rolls[index] = replace(conv.rolls[index], note=note, opposed_total=opposed)
    print(f'Annotated {len(staged)} roll(s).')
    return len(staged)
