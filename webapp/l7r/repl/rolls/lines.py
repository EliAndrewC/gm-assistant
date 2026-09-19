"""Lines of questioning, declared by the GM: `new_line_of_questioning`, `grilling`, `detected`.

Feature 207 replaces feature 206's join-which-line menu. The GM (2026-09-19): *"we
have a `new_line_of_questioning` function which can be called with a description
and a roll. For example, `new_line_of_questioning("Fumitake's contributions to the
Wasp treasury", xky(8, 3) + 10)`. Note that I am including both the description and
the sincerity roll that Fumitake is making."*

The GM normally declares the line BEFORE the players roll - *"Players always ask me
whether it's a new line of questioning before they roll another interrogation
roll"* - so a roll simply lands on the line current when it was made
(`conversation.attach`). Two kinds of EARLIER roll might belong to a new line, and
neither is ever pulled in silently; the GM is asked about each, join or discard:

- a roll on NO line - a player who rolled before the first declaration;
- a PC's REPEAT roll on the line being left. The skill is rolled once per line of
  questioning, so a second roll is the new topic's roll made early, or a mistake.

A PC's FIRST roll on the old line is never asked about: the GM's two answers (part
of this line, or discard) are both wrong for it. The fidelity review checked that
narrowing by name and found it the one class the GM's own answers cannot address.

The Sincerity roll is OPTIONAL, and the public line reads the same without it:
*"that exact same thing is registered even if I don't bother to roll sincerity
because the person is being completely truthful."*
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

from l7r.repl import dice
from l7r.repl.gmrolls import GmRoll
from l7r.repl.rolls import conversation, hidden, npcskills, rules
from l7r.repl.rolls.models import Conversation, Line, Roll

Ask = Callable[[str], str]


def _ask(question: str) -> str:
    # `annotate` the FUNCTION shadows the module on the package, so import by path.
    asker: Ask = importlib.import_module('l7r.repl.rolls.annotate').ask_quietly
    return asker(question)


def _describe(roll: Roll) -> str:
    rank = '' if roll.rank is None else f'@{roll.rank}'
    return f'{rules.personal_name(roll.character)} {roll.total}{rank} ({roll.at:%H:%M:%S})'


def _live(roll: Roll) -> bool:
    return rules.is_interrogation(roll) and not roll.discarded and roll.attributed


def candidates(conv: Conversation) -> list[int]:
    """Indexes of the earlier rolls a NEW line might own - see the module docstring."""
    found = [i for i, roll in enumerate(conv.rolls) if _live(roll) and roll.line is None]
    if conv.lines:
        leaving = conv.lines[-1].id
        seen: set[str] = set()
        for index, roll in enumerate(conv.rolls):
            if not _live(roll) or roll.line != leaving:
                continue
            who = roll.character.strip().lower()
            if who in seen:
                found.append(index)
            seen.add(who)
    return sorted(found)


def _sincerity(value: object) -> GmRoll | int | None:
    """The hidden roll as handed in: a live `xky` total, a bare number, or nothing.

    A live roll is TAGGED sincerity if it was not already - *"the roll itself
    conveys the sincerity skill"* - which records or checks the NPC's numbers exactly
    as `xky(8, 3) - sincerity` would.
    """
    if value is None:
        return None
    if isinstance(value, dice.DiceTotal):
        entry = value.entry
        if entry.tagged not in ('', 'sincerity'):
            raise ValueError(
                f'that roll is tagged {entry.tagged}, not sincerity - a line of questioning is '
                'opposed by a sincerity roll.'
            )
        if not entry.tagged:
            npcskills.build_tags()['sincerity'].tag_roll(value)
        if entry.mistake:
            raise ValueError(
                'that roll was marked a mistake - roll it again, then declare the line.'
            )
        return entry
    return int(value)  # type: ignore[call-overload,no-any-return]


def new_line_of_questioning(
    description: str,
    sincerity: object = None,
    *,
    grilling: bool = False,
    ask: Ask | None = None,
    collector: Callable[[Conversation], object] | None = None,
    now: Callable[[], datetime] | None = None,
) -> None:
    """Declare a line of questioning, with the NPC's hidden Sincerity roll if any.

    Collects ONCE first, so a roll posted seconds ago is asked about here rather
    than arriving late. Ctrl-C at the questions abandons the declaration whole.
    """
    conv = conversation.require_open()
    topic = description.strip()
    if not topic:
        raise ValueError('say what the line of questioning is about')
    secret = _sincerity(sincerity)
    with conversation._collect_lock:
        (collector or conversation.collect)(conv)
    asker = ask or _ask
    joining: list[int] = []
    discarding: list[int] = []
    pending = candidates(conv)
    if pending:
        print(f'  Earlier interrogation rolls - part of "{topic}", or discard?')
    for index in pending:
        answer = ''
        while answer not in ('p', 'd'):
            try:
                answer = asker(f'    {_describe(conv.rolls[index])} [P/d] > ').strip().lower()[:1]
            except KeyboardInterrupt, EOFError:
                print('\n  Ctrl-C - the line was not declared and nothing changed.')
                return
            answer = answer or 'p'
        (joining if answer == 'p' else discarding).append(index)
    used = [line.id for line in conv.lines] + [r.line for r in conv.rolls if r.line is not None]
    clock = now or (lambda: datetime.now(UTC))
    line = Line(
        id=max(used, default=0) + 1,
        description=topic,
        at=clock(),
        grilling=grilling,
        sincerity=secret,
    )
    conv.lines.append(line)
    for index in discarding:
        conv.rolls[index] = replace(conv.rolls[index], discarded=True)
    for index in joining:
        conv.rolls[index] = replace(
            conv.rolls[index], line=line.id, note=topic, grilling=grilling, outcome=''
        )
    flag = ' (grilling)' if grilling else ''
    rolled = '' if secret is None else ' - sincerity roll kept in the GM-only notes'
    print(f'Line of questioning{flag}: {topic}{rolled}')
    _compare_all(conv, line)


def _compare_all(conv: Conversation, line: Line) -> None:
    for roll in conv.rolls:
        if roll.line == line.id and _live(roll):
            found = hidden.compare(conv, line, roll)
            if found is not None:
                print(f'  = {found.describe()}')


def _current(conv: Conversation, number: int | None = None) -> Line:
    if not conv.lines:
        raise ValueError('no line of questioning yet - new_line_of_questioning("...") first')
    if number is None:
        return conv.lines[-1]
    if not 1 <= number <= len(conv.lines):
        listing = ', '.join(f'{i}. {ln.description}' for i, ln in enumerate(conv.lines, start=1))
        raise ValueError(f'no line {number}. The lines are: {listing}')
    return conv.lines[number - 1]


def grilling() -> None:
    """The interrogator started grilling part way through the current line.

    RETROACTIVE, as the GM asked: *"a `grilling()` function which will retroactively
    subtract the free raises which the NPC received"* - the casual-conversation
    raises come off every roll on the line, and the public line gains `(grilling)`.
    Called twice, it says so and changes nothing.
    """
    conv = conversation.require_open()
    line = _current(conv)
    if line.grilling:
        print(f'Grilling was already recorded for "{line.description}".')
        return
    line.grilling = True
    for index, roll in enumerate(conv.rolls):
        if roll.line == line.id and rules.is_interrogation(roll):
            conv.rolls[index] = replace(roll, grilling=True)
    print(f'Grilling recorded for "{line.description}" - the casual free raises come off.')
    _compare_all(conv, line)


def detected(pc: str, what: str, line: int | None = None) -> None:
    """Say what one interrogator GOT, at any point in the conversation.

    Free raises build over a line of questioning, so this is often settled long
    after the roll was captured and written: *"we also need to be able to do this
    after the roll has been registered and annotated."* The PC leaves the group and
    gets their own written line under the same topic. `line` is the line's number in
    the order declared; the current line when omitted.
    """
    conv = conversation.require_open()
    outcome = what.strip()
    if not outcome:
        raise ValueError('say what they detected')
    target = _current(conv, line)
    wanted = pc.strip().lower()
    on_line = [
        (index, roll)
        for index, roll in enumerate(conv.rolls)
        if roll.line == target.id and _live(roll)
    ]
    hits = [
        index
        for index, roll in on_line
        if wanted in (roll.character.strip().lower(), rules.personal_name(roll.character).lower())
    ]
    if not hits:
        names = sorted({rules.personal_name(roll.character) for _, roll in on_line})
        who = ', '.join(names) if names else 'nobody yet'
        raise ValueError(
            f'{pc} has no interrogation roll on "{target.description}". Rolls there: {who}.'
        )
    for index in hits:
        conv.rolls[index] = replace(conv.rolls[index], outcome=outcome)
    group = [conv.rolls[index] for index, _ in on_line]
    for rolls in rules.by_outcome(group):
        print(f'  {rules.render_interrogation(rolls)}')
