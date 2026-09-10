"""The annotate menu: saying what a roll was for.

The GM's reason, which is the whole justification for holding rolls back:
*"if I look at my notes and I see that a character made a precepts roll, That
doesn't help me very much because I might not remember what the roll was about."*
So a Precepts 25 is worth nothing in the record without a sentence beside it, and
this is where that sentence comes from.

Etiquette never appears here - those are presumed to be introductions, so the
annotation would say the same thing every time.

FOUR KINDS: open (`o`), contested (`c`), discard (`d`), and open with a bonus
(`ob`). The last is a separate menu entry rather than a "bonus?" question asked on
every open roll, because open rolls with a bonus are uncommon and a question on
the common path would be answered "no" almost every time (GM 2026-09-09). The
contested path asks for both sides' bonuses every time, because there the rules'
free raises make a bonus the usual case rather than the exception.

CTRL-C DISCARDS EVERYTHING. Annotations are staged as the GM works and committed
only when they finish, so a Ctrl-C part way through a run of five leaves all five
unannotated rather than four annotated and one not. That is the literal reading of
the GM's *"having that not save anything"*, and it is the behavior most likely to
sting in play - flagged in the spec for confirmation once it has been used in
anger. Finishing normally (blank line at the roll prompt) commits what is done.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from l7r.repl import gmrolls
from l7r.repl.rolls import rules
from l7r.repl.rolls.models import Conversation, Roll

Ask = Callable[[str], str]


class Abandoned(Exception):
    """The GM pressed Ctrl-C. Nothing is saved."""


def _history_length() -> int:
    """How many lines readline's history holds; 0 where there is no readline."""
    try:
        import readline
    except ImportError:  # pragma: no cover - Windows, or a stripped build
        return 0
    return readline.get_current_history_length()


def ask_quietly(question: str, *, reader: Ask = input) -> str:
    """`input()`, with the answer kept OUT of the readline history.

    At the REPL every `input()` line goes into the same readline history as the
    Python the GM types, so after an annotate run the up-arrow walked back through
    `o`, `5`, `what kinds of spirits cannot cross running water?` before reaching
    any code (GM 2026-09-09: *"the things that I typed into the menus on the
    annotate function show up in my Python history"*). readline appends the line
    as `input()` returns, so the fix is to take it straight back off - and only
    when the length actually grew, because readline does not record a blank line
    and removing on a blank would delete real history.
    """
    before = _history_length()
    answer = reader(question)
    with contextlib.suppress(ImportError):
        import readline

        if readline.get_current_history_length() > before:
            readline.remove_history_item(readline.get_current_history_length() - 1)
    return answer


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
    #: The player's bonus on an OPEN roll - the `ob` option. Zero for a plain `o`.
    bonus: int = 0
    #: Feature 206, interrogation only: the line of questioning the roll goes on
    #: (non-None marks an interrogation decision), the line's grilling flag, and the
    #: rank to record - the roll's own when it had one, else what the GM answered.
    line: int | None = None
    grilling: bool = False
    rank: int | None = None


def _apply(roll: Roll, decision: Decision) -> Roll:
    """Turn a staged decision into the roll it produces."""
    if decision.discard:
        return replace(roll, discarded=True)
    if decision.line is not None:
        # An interrogation roll: note, line, grilling, rank - and NOTHING about an
        # opposing side or a bonus, which is the leak feature 206 closes.
        return replace(
            roll,
            note=decision.note,
            line=decision.line,
            grilling=decision.grilling,
            rank=decision.rank,
        )
    if decision.contest is None:
        return replace(roll, note=decision.note, bonus_self=decision.bonus)
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


#: The answers the kind prompt accepts, after `_kind` has normalized them.
KINDS = ('o', 'c', 'd', 'ob')


def _kind(answer: str) -> str:
    """Normalize the GM's answer at the kind prompt.

    One letter is enough for open / contested / discard, and a whole word still
    works (`open` -> `o`). The exception is `ob` - open WITH a bonus - which is the
    GM's own spelling for the uncommon case and must not collapse to `o`; a bare `b`
    (or `bonus`) means the same thing. Anything unrecognized comes back as typed so
    the caller re-asks.
    """
    answer = answer.lower()
    if answer in ('ob', 'b', 'bonus'):
        return 'ob'
    return answer[:1]


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


def _optional_number(ask: Ask, question: str) -> int | None:
    """A whole number, or None on a blank line. Used for a rank nobody recorded."""
    while True:
        answer = _prompt(ask, question)
        if not answer:
            return None
        if answer.isdigit():
            return int(answer)
        print('  ? a whole number, or blank for none')


def _yes_no(ask: Ask, question: str, *, default: bool = False) -> bool:
    while True:
        answer = _prompt(ask, question).lower()
        if not answer:
            return default
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        print('  ? y or n, or blank for ' + ('yes' if default else 'no'))


def _overlaid(conv: Conversation, staged: dict[int, Decision]) -> list[Roll]:
    """The conversation's rolls as they WILL be once the staged decisions commit.

    The menu reads lines of questioning from this rather than from `conv.rolls`, so
    a line started earlier in the same run is offered to the next roll - and, since
    nothing here is written back, Ctrl-C still discards all of it.
    """
    return [
        _apply(roll, staged[index]) if index in staged else roll
        for index, roll in enumerate(conv.rolls)
    ]


def _interrogate(ask: Ask, roll: Roll, rolls: Sequence[Roll]) -> Decision | None:
    """The interrogation branch of the menu (feature 206).

    Instead of open / contested / discard / open-with-bonus, an interrogation roll is
    asked which LINE OF QUESTIONING it belongs to - joining one already stated, or
    starting a new one - then, in this order, its rank if nobody recorded one,
    whether the interrogator was grilling (new lines only), and what the line was
    about (new lines only). Contested is never offered because the opposing roll is
    the NPC's Sincerity, which must not be written; a bonus is never offered because
    every bonus on either side reveals NPC state (`rules.INTERROGATION`).

    Returns the staged decision, a discard, or None when the GM finished with a
    blank line. `rolls` is the conversation overlaid with what is already staged.
    """
    lines = rules.lines_of_questioning(rolls)
    if lines:
        print('  Lines of questioning so far:')
        for position, group in enumerate(lines, start=1):
            flag = '(grilling) ' if group[0].grilling else ''
            print(f'    {position}. {flag}{group[0].note}')
        question = '  Join which line? (number, n for new, d to discard, blank to finish) > '
        hint = '  ? a line number, n for new, d to discard, or blank to finish'
    else:
        question = '  New line of questioning, or discard? [n/d, blank to finish] > '
        hint = '  ? n for new, d to discard, or blank to finish'
    joined: list[Roll] | None = None
    while True:
        answer = _prompt(ask, question).lower()
        if not answer:
            return None
        if answer[:1] == 'd':
            return Decision(discard=True)
        if answer[:1] == 'n':
            break
        if lines and answer.isdigit() and 1 <= int(answer) <= len(lines):
            joined = lines[int(answer) - 1]
            break
        print(hint)
    rank = roll.rank
    if rank is None:
        who = rules.personal_name(roll.character)
        rank = _optional_number(ask, f"  {who}'s interrogation rank? [none] > ")
    if joined is not None:
        head = joined[0]
        return Decision(note=head.note, line=head.line, grilling=head.grilling, rank=rank)
    grilling = _yes_no(ask, '  Grilling? [y/N] > ')
    note = ''
    while not note:
        note = _prompt(ask, '  What was the line of questioning? > ')
    # A fresh id: above every id in use, discarded rolls included, so an id is never
    # shared between a live line and a dead one even though nothing would break.
    used = [r.line for r in rolls if r.line is not None]
    return Decision(note=note, line=max(used, default=0) + 1, grilling=grilling, rank=rank)


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
        # Name the skill the NPC is TAKEN to have rolled. It is derived from the
        # player's by the pairing rule and never asked for, so showing it here is
        # the GM's only chance to notice if the roll was not what they expected.
        print(
            f'  Free raises: {roll.character} {roll.skill} {roll.rank} '
            f'vs your {rules.opposing_skill(roll.skill)} {opponent.skill}'
        )
    bonus_self = _number(ask, f'  Bonus to {roll.character}? [{theirs}] > ', theirs)
    bonus_opposed = _number(ask, f'  Bonus to your side? [{ours}] > ', ours)
    return opponent.total, bonus_self, bonus_opposed


def annotate(
    conversation: Conversation | None = None,
    *,
    ask: Ask = ask_quietly,
    mine: Callable[[], Sequence[gmrolls.GmRoll]] = gmrolls.recent,
) -> None:
    """Say what each waiting roll was for.

    Loops rather than taking one roll per call, because rolls arrive in rounds and
    annotating them one call at a time would be tedious in exactly the moment the
    GM is busiest.

    RETURNS NOTHING, on purpose. It used to return the count of rolls annotated,
    and at the prompt that number was echoed after the summary line with no label
    on it (GM 2026-09-09: *"I do a double take sometimes when I see it to figure out
    what was happening there"*). Everything worth knowing is printed.
    """
    from l7r.repl.rolls.conversation import require_open

    conv = conversation if conversation is not None else require_open()
    waiting = pending(conv)
    if not waiting:
        print('Nothing waiting to be annotated.')
        return

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
            if rules.is_interrogation(roll):
                # Interrogation never sees o/c/d/ob: no contest (the opposing roll is
                # the NPC's Sincerity, which is never written) and no bonus (feature
                # 206). Its prompt is which line of questioning, with d and blank.
                decision = _interrogate(ask, roll, _overlaid(conv, staged))
                if decision is None:
                    break
                staged[index] = decision
                if decision.discard:
                    print('  staged: discarded')
                    continue
                line = next(
                    group
                    for group in rules.lines_of_questioning(_overlaid(conv, staged))
                    if group[0].line == decision.line
                )
                print(f'  staged: {rules.render_interrogation(line)}')
                continue
            # Blank finishes here as well as at the roll prompt. With one roll left
            # the "which?" question is skipped, and without this the GM would have no
            # way to stop except Ctrl-C - which discards everything already staged.
            kind = ''
            while kind not in KINDS:
                kind = _kind(
                    _prompt(
                        ask,
                        '  Open, contested, discard, or open with bonus? '
                        '[o/c/d/ob, blank to finish] > ',
                    )
                )
                if not kind:
                    break
            if not kind:
                break
            if kind == 'd':
                staged[index] = Decision(discard=True)
                print('  staged: discarded')
                continue
            opposed = _opposing(ask, roll, list(mine())) if kind == 'c' else None
            # An open roll with a bonus is its own menu entry rather than a question
            # asked on every open roll, because it is the uncommon case (GM
            # 2026-09-09: *"this is not as common. So instead of always asking every
            # time we add an open roll ... an open with bonus option"*).
            bonus = _number(ask, f'  Bonus to {roll.character}? [0] > ', 0) if kind == 'ob' else 0
            note = ''
            while not note:
                note = _prompt(ask, '  What was it for? > ')
            staged[index] = Decision(note=note, contest=opposed, bonus=bonus)
            shown = _apply(roll, staged[index])
            print(f'  staged: {rules.render_annotated(shown, conv.npc_name)}')
    except Abandoned:
        # "discarded" would read as the roll-discard feature, which this is not:
        # the rolls are all still there, unannotated, and annotate() can be re-run.
        print(
            f'\nCtrl-C - nothing saved ({len(staged)} choice(s) abandoned). '
            'The rolls are untouched; run annotate() again when you are ready.'
        )
        return

    for index, decision in staged.items():
        conv.rolls[index] = _apply(conv.rolls[index], decision)
    discarded = sum(1 for decision in staged.values() if decision.discard)
    kept = len(staged) - discarded
    tail = f', {discarded} discarded' if discarded else ''
    print(f'Annotated {kept} roll(s){tail}.')
