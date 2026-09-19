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

FEATURE 207: THE QUESTION DEPENDS ON THE SKILL. `modes.py` says what each skill's
roll MAY be, and the menu stops asking what it already knows: an always-open skill
is asked only what it was for; a default-open one arrives with open SELECTED and a
two-press keystroke undoes it (`keys.py`); manipulation and sneaking go straight to
the opposing roll; acting takes a HIDDEN opposing roll and an outcome; and an
interrogation roll already sits on the line of questioning the GM declared
(`lines.py`), so it is asked about only when it arrived before any line or has no
rank. Where the GM TAGGED their own roll (`xky(5, 3) - tact`), the opposing roll is
paired without asking. Every skill not ruled on keeps the four-way question below.

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
from datetime import datetime

from l7r.repl import gmrolls
from l7r.repl.rolls import hidden, keys, modes, oppose, rules
from l7r.repl.rolls.models import Conversation, Roll

Ask = Callable[[str], str]
#: `(question, ask) -> (undone, answer)` - `keys.ask_with_undo`, or a test's script.
Undoable = Callable[[str, Ask], tuple[bool, str]]


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
    #: Feature 207. What a hidden-opposition roll got the players; '' is the default.
    outcome: str = ''
    #: The GM roll used as the opposing side (its `seq`), so it is marked paired on
    #: commit and never pre-paired with a second player roll.
    opponent: int | None = None
    #: This decision ONLY supplies a rank - an interrogation roll that was already on
    #: its line when the menu reached it.
    rank_only: bool = False


def _apply(roll: Roll, decision: Decision) -> Roll:
    """Turn a staged decision into the roll it produces."""
    if decision.discard:
        return replace(roll, discarded=True)
    if decision.rank_only:
        return replace(roll, rank=decision.rank, rank_settled=True)
    if decision.line is not None:
        # An interrogation roll: note, line, grilling, rank - and NOTHING about an
        # opposing side or a bonus, which is the leak feature 206 closes.
        return replace(
            roll,
            note=decision.note,
            line=decision.line,
            grilling=decision.grilling,
            rank=decision.rank,
            rank_settled=True,
        )
    if roll.skill.lower() == rules.ACTING:
        # The opposing investigation roll is KEPT on the roll - `hidden.entries` reads
        # it for the GM-only notes - and never rendered (`rules.render_annotated`).
        opposed, bonus_self, bonus_opposed = decision.contest or (None, 0, 0)
        return replace(
            roll,
            note=decision.note,
            outcome=decision.outcome,
            rank=decision.rank,
            rank_settled=True,
            opposed_total=opposed,
            bonus_self=bonus_self,
            bonus_opposed=bonus_opposed,
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
        if roll.attributed and (rules.needs_annotation(roll) or _needs_rank(roll))
    ]


def _needs_rank(roll: Roll) -> bool:
    """An interrogation roll already on its line, written without `@N` until the GM
    says the rank - or says there is none, after which it is never asked again."""
    return (
        rules.is_interrogation(roll)
        and roll.line is not None
        and roll.rank is None
        and not roll.rank_settled
        and not roll.discarded
    )


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


def _interrogate(ask: Ask, roll: Roll, conv: Conversation) -> Decision | None:
    """The interrogation branch, reduced by feature 207.

    Lines of questioning are DECLARED now (`lines.new_line_of_questioning`) and a
    roll lands on the line current when it was made, so most interrogation rolls
    never reach this menu. Two kinds still do:

    - a roll already on its line but with NO RANK (a hand-typed roll): asked for the
      rank and nothing else, because `37@2` cannot be written without it;
    - a roll on NO line - one that arrived before any line existed, or late. The GM
      says which declared line it joins, or discards it. It is never attached
      without being asked (*"instead of pulling in previous interrogation rolls
      automatically ... I am prompted"*).

    Contested is never offered and no bonus is asked, exactly as feature 206 ruled:
    the opposing roll is the NPC's hidden Sincerity, and every bonus reveals NPC
    state. Returns the staged decision, or None when the GM finished with a blank.
    """
    who = rules.personal_name(roll.character)
    if roll.line is not None:
        rank = _optional_number(ask, f"  {who}'s interrogation rank? [none] > ")
        return Decision(rank=rank, rank_only=True)
    if conv.lines:
        print('  Lines of questioning:')
        for position, line in enumerate(conv.lines, start=1):
            flag = '(grilling) ' if line.grilling else ''
            print(f'    {position}. {flag}{line.description}')
        question = '  Which line? (number, d to discard, blank to finish) > '
        hint = '  ? a line number, d to discard, or blank to finish'
    else:
        print('  No line of questioning yet - new_line_of_questioning("...") declares one.')
        question = '  Discard it? [d to discard, blank to leave it for now] > '
        hint = '  ? d to discard, or blank to leave it'
    while True:
        answer = _prompt(ask, question).lower()
        if not answer:
            return None
        if answer[:1] == 'd':
            return Decision(discard=True)
        if answer.isdigit() and 1 <= int(answer) <= len(conv.lines):
            chosen = conv.lines[int(answer) - 1]
            break
        print(hint)
    rank = roll.rank
    if rank is None:
        rank = _optional_number(ask, f"  {who}'s interrogation rank? [none] > ")
    return Decision(note=chosen.description, line=chosen.id, grilling=chosen.grilling, rank=rank)


def _their_rank(conv: Conversation, skill: str, entry: gmrolls.GmRoll | None) -> int | None:
    """The NPC's rank in `skill`: EXACT when it is on record (feature 207), else read
    off the chosen roll's pool - which the GM warned is *"not completely reliable"*,
    and is why both bonuses can still be overridden."""
    if skill in conv.numbers:
        return conv.numbers[skill]
    return None if entry is None else entry.skill


def _bonuses(ask: Ask, roll: Roll, their_skill: str, their_rank: int | None) -> tuple[int, int]:
    """Ask for the bonus each side gets, defaulting to the rules' free raises."""
    theirs, ours = rules.free_raises(roll.rank, their_rank)
    _say_raises(roll, their_skill, their_rank)
    bonus_self = _number(ask, f'  Bonus to {roll.character}? [{theirs}] > ', theirs)
    bonus_opposed = _number(ask, f'  Bonus to your side? [{ours}] > ', ours)
    return bonus_self, bonus_opposed


def _say_raises(roll: Roll, their_skill: str, their_rank: int | None) -> None:
    if roll.rank is None:
        print(f'  {roll.character} has no recorded rank, so no free raises are inferred.')
    elif their_rank is None:
        print(f'  No rank known for your {their_skill}, so no free raises are inferred.')
    else:
        # Name the skill the NPC is TAKEN to have rolled. It is derived from the
        # player's by the pairing rule and never asked for, so showing it here is
        # the GM's only chance to notice if the roll was not what they expected.
        print(
            f'  Free raises: {roll.character} {roll.skill} {roll.rank} '
            f'vs your {their_skill} {their_rank}'
        )


def _taxed(
    conv: Conversation,
    their_skill: str,
    total: int,
    when: datetime,
    entry: gmrolls.GmRoll | None = None,
) -> int:
    """The NPC's opposing total after a player's oppose penalty (feature 208).

    Pairing is the moment an UNTAGGED roll, or a total the GM types, becomes a roll
    of a known skill - and so of a known ring - which makes it the moment the tool
    can price it. The GM: *"All rolls made by the NPC for the remainder of the
    conversation."* A TAGGED roll was priced when it was tagged and is returned as it
    stands. A typed total has no time of its own, so it takes the player's roll's.
    The manipulation default of 15 never comes here: no roll was made.

    Works on the NUMBER and leaves the recorded roll alone, because everything in
    this menu is staged and a Ctrl-C must leave nothing behind.
    """
    if entry is not None and entry.tagged:
        return total
    found = oppose.for_skill(conv, their_skill, when)
    if found is None:
        return total
    print(f'  {found.describe()}: {total} -> {total - found.amount}')
    return total - found.amount


def _opposing(
    ask: Ask, roll: Roll, mine: Sequence[gmrolls.GmRoll], conv: Conversation
) -> tuple[int, int, int, int] | None:
    """The FULL MENU's contested path: pick the opposing roll and both bonuses.

    Returns `(opposing total, bonus to the player, bonus to the NPC, the GM roll's
    seq)`, or None - falling back to open - when the GM has no recent rolls.

    The default bonus is the free raises the rules grant - one per point of skill
    difference, five each (`rules/02-skills.md:64` and :66). The player's skill comes
    from the rank the character-sheet app recorded when it has one, which is EXACT;
    the NPC's is the recorded rank when there is one, else inferred from their pool.
    Either can be overridden, which is the whole reason the GM asked for the prompt.
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
    their_skill = rules.opposed_by(roll.skill)
    bonus_self, bonus_opposed = _bonuses(
        ask, roll, their_skill, _their_rank(conv, their_skill, opponent)
    )
    total = _taxed(conv, their_skill, opponent.total, opponent.at, opponent)
    return total, bonus_self, bonus_opposed, opponent.seq


@dataclass
class _Menu:
    """What one `annotate()` run carries from roll to roll."""

    ask: Ask
    undoable: Undoable
    conv: Conversation
    mine: list[gmrolls.GmRoll]
    #: GM rolls already used as an opposing side in THIS run (by `seq`).
    used: set[int]

    def ask_undoable(self, question: str) -> tuple[bool, str]:
        try:
            undone, answer = self.undoable(question, self.ask)
        except (KeyboardInterrupt, EOFError) as exc:
            raise Abandoned from exc
        return undone, answer.strip()


#: What a typed answer at a what-was-it-for prompt may switch to. The keystroke is
#: the GM's undo; these are what a pipe or a test has instead, and they work at a
#: terminal too. No real note is one of these tokens.
_TYPED_KINDS = {'c': 'c', 'ob': 'ob', 'b': 'ob', 'd': 'd', 'f': 'f', 'n': 'n', 't': 't'}


def _note_or_kind(
    menu: _Menu, roll: Roll, question: str, *, undo: bool, kinds: tuple[str, ...]
) -> tuple[str, str]:
    """One what-was-it-for prompt. `(what, text)`, `what` being one of:

    `note` (text is the note), `kind` (text is c / ob / d), `undo` (the keystroke),
    or `finish` (a blank line - which commits what is staged, as everywhere else in
    this menu; a bare Enter is NEVER accepted as a note).
    """
    while True:
        if undo:
            undone, answer = menu.ask_undoable(question)
            if undone:
                return 'undo', ''
        else:
            answer = _prompt(menu.ask, question)
        if not answer:
            return 'finish', ''
        kind = _TYPED_KINDS.get(answer.lower())
        if kind is None:
            return 'note', answer
        if kind in kinds:
            return 'kind', kind
        print(f'  ? {roll.skill.lower()} is never rolled that way')


def _required_note(ask: Ask) -> str:
    note = ''
    while not note:
        note = _prompt(ask, '  What was it for? > ')
    return note


def _by_kind(menu: _Menu, roll: Roll, kind: str) -> Decision:
    """Finish a roll whose kind is settled: the four-way menu's second half."""
    if kind == 'd':
        return Decision(discard=True)
    picked = _opposing(menu.ask, roll, menu.mine, menu.conv) if kind == 'c' else None
    # An open roll with a bonus is its own menu entry rather than a question asked
    # on every open roll, because it is the uncommon case (GM 2026-09-09: *"this is
    # not as common. So instead of always asking every time we add an open roll ...
    # an open with bonus option"*).
    bonus = _number(menu.ask, f'  Bonus to {roll.character}? [0] > ', 0) if kind == 'ob' else 0
    note = _required_note(menu.ask)
    if picked is None:
        return Decision(note=note, bonus=bonus)
    menu.used.add(picked[3])
    return Decision(note=note, contest=picked[:3], opponent=picked[3])


def _full_menu(menu: _Menu, roll: Roll) -> Decision | None:
    # Blank finishes here as well as at the roll prompt. With one roll left the
    # "which?" question is skipped, and without this the GM would have no way to
    # stop except Ctrl-C - which discards everything already staged.
    kind = ''
    while kind not in KINDS:
        kind = _kind(
            _prompt(
                menu.ask,
                '  Open, contested, discard, or open with bonus? [o/c/d/ob, blank to finish] > ',
            )
        )
        if not kind:
            return None
    return _by_kind(menu, roll, kind)


def _open_by_default(menu: _Menu, roll: Roll, *, only_open: bool) -> Decision | None:
    """ALWAYS OPEN and DEFAULT OPEN: open is already chosen, so ask what it was for.

    An always-open skill (pontificate, athletics) can never be contested, so there
    is nothing to undo and `c` is refused. A default-open one (history, investigation
    ...) can, rarely - the keystroke, or a bare `c`, reaches the four-way menu.
    """
    if only_open:
        question = '  open - what was it for? (ob for a bonus, d to discard) > '
        kinds: tuple[str, ...] = ('ob', 'd')
    else:
        question = '  open - what was it for? (backspace twice to change) > '
        kinds = ('c', 'ob', 'd')
    what, text = _note_or_kind(menu, roll, question, undo=not only_open, kinds=kinds)
    if what == 'finish':
        return None
    if what == 'undo':
        return _full_menu(menu, roll)
    if what == 'kind':
        return _by_kind(menu, roll, text)
    return Decision(note=text)


def _prepair(menu: _Menu, roll: Roll) -> gmrolls.GmRoll | None:
    """The GM's TAGGED roll of the opposing skill, if there is one to pair.

    The GM (2026-09-19): *"if a player rolled manipulation and I have a tact roll,
    then when I call the annotate() function, then you can pre-pair the tact and
    manipulation rolls against each other such that the only thing that I am asked
    to annotate is adding the note."* Nearest in time, never one already used, never
    one marked a mistake (`gmrolls.recent` drops those).
    """
    wanted = rules.opposed_by(roll.skill)
    free = [
        entry
        for entry in menu.mine
        if entry.tagged == wanted and not entry.paired and entry.seq not in menu.used
    ]
    if not free:
        return None
    return min(free, key=lambda entry: abs((entry.at - roll.at).total_seconds()))


def _pick(
    menu: _Menu, roll: Roll, *, fifteen: bool, nobody: bool, first: str = ''
) -> tuple[str, tuple[int, int, int] | None, int | None] | None:
    """The opposing-roll picker for a skill that is ALWAYS contested.

    `(what, contest, seq)` with `what` one of `contest`, `nobody`, `discard`; None
    when the GM finished with a blank line. Besides the GM's recent rolls it offers:

    - `f` - FIFTEEN, no roll made (manipulation): *"kind of the default value that
      someone gets if they are not actively making a roll to contest something"*,
      which presumes a tact of ZERO, so the manipulator's whole rank is free raises;
    - `n` - NOBODY opposed it (sneaking): written as an open line;
    - `t` - TYPE a total, for a roll made away from the prompt.
    """
    their_skill = rules.opposed_by(roll.skill)
    if menu.mine:
        print('  Your recent rolls:')
        for position, entry in enumerate(menu.mine, start=1):
            print(f'    {position}. {entry.describe()}  [implies {entry.skill}]')
    options = ['number'] if menu.mine else []
    if fifteen:
        options.append(f'f for {modes.UNROLLED_TOTAL} - no roll made')
    if nobody:
        options.append('n for nobody opposed it')
    options += ['t to type a total', 'd to discard', 'blank to finish']
    question = f'  Opposed by which {their_skill} roll? ({", ".join(options)}) > '
    while True:
        answer, first = first or _prompt(menu.ask, question).lower(), ''
        if not answer:
            return None
        if answer[:1] == 'd':
            return 'discard', None, None
        if nobody and answer[:1] == 'n':
            return 'nobody', None, None
        chosen: gmrolls.GmRoll | None = None
        if answer.isdigit() and 1 <= int(answer) <= len(menu.mine):
            chosen = menu.mine[int(answer) - 1]
            total = _taxed(menu.conv, their_skill, chosen.total, chosen.at, chosen)
            their_rank = _their_rank(menu.conv, their_skill, chosen)
        elif fifteen and answer[:1] == 'f':
            total, their_rank = modes.UNROLLED_TOTAL, 0
        elif answer[:1] == 't':
            total = _number(menu.ask, f'  Their {their_skill} total? > ', 0)
            total = _taxed(menu.conv, their_skill, total, roll.at)
            their_rank = _their_rank(menu.conv, their_skill, None)
        else:
            print('  ? ' + ', '.join(options))
            continue
        bonus_self, bonus_opposed = _bonuses(menu.ask, roll, their_skill, their_rank)
        return 'contest', (total, bonus_self, bonus_opposed), None if chosen is None else chosen.seq


def _contest(
    menu: _Menu, roll: Roll, *, fifteen: bool = False, nobody: bool = False
) -> tuple[str, str, tuple[int, int, int] | None, int | None] | None:
    """Settle the opposing side and the note of an always-contested roll.

    `(what, note, contest, seq)`, `what` being `contest`, `nobody` or `discard`; None
    to finish. A tagged GM roll is paired WITHOUT asking and only the note is asked;
    the two-press undo (or a blank picker afterwards) reaches everything else.
    """
    their_skill = rules.opposed_by(roll.skill)
    paired = _prepair(menu, roll)
    first = ''
    if paired is not None:
        their_rank = _their_rank(menu.conv, their_skill, paired)
        bonus_self, bonus_opposed = rules.free_raises(roll.rank, their_rank)
        print(f'  Paired with your {their_skill} roll: {paired.describe()}')
        _say_raises(roll, their_skill, their_rank)
        if bonus_self or bonus_opposed:
            print(f'  Bonus to {roll.character}: {bonus_self}; to your side: {bonus_opposed}')
        # The picker's own letters work here too. Found by running a whole scripted
        # session (2026-09-19): a tagged investigation roll pre-paired a sneaking roll,
        # the GM's `n` for "nobody opposed it" was taken as the NOTE, and the roll was
        # written as a contest it never was. No real note is one of these letters.
        shortcuts = ('t',) + (('f',) if fifteen else ()) + (('n',) if nobody else ())
        what, text = _note_or_kind(
            menu,
            roll,
            '  What was it for? (backspace twice for another roll, d to discard) > ',
            undo=True,
            kinds=('d', *shortcuts),
        )
        if what == 'finish':
            return None
        if what == 'kind' and text == 'd':
            return 'discard', '', None, None
        if what == 'note':
            return 'contest', text, (paired.total, bonus_self, bonus_opposed), paired.seq
        first = text if what == 'kind' else ''
    picked = _pick(menu, roll, fifteen=fifteen, nobody=nobody, first=first)
    if picked is None:
        return None
    what, contest, seq = picked
    if what == 'discard':
        return 'discard', '', None, None
    return what, _required_note(menu.ask), contest, seq


def _always_contested(menu: _Menu, roll: Roll, mode: modes.Mode) -> Decision | None:
    """Manipulation (an opposing number REQUIRED) and sneaking (may be unopposed)."""
    settled = _contest(
        menu,
        roll,
        fifteen=mode == 'contested_required',
        nobody=mode == 'contested_maybe_unopposed',
    )
    if settled is None:
        return None
    what, note, contest, seq = settled
    if what == 'discard':
        return Decision(discard=True)
    if seq is not None:
        menu.used.add(seq)
    # `nobody` leaves `contest` None, which IS the open-shaped line the GM confirmed
    # for an unopposed sneaking roll: rounded down to 5, no marker.
    return Decision(note=note, contest=contest, opponent=seq)


def _acting(menu: _Menu, roll: Roll) -> Decision | None:
    """Acting: ALWAYS opposed by investigation, and the opposing roll is HIDDEN.

    The GM (2026-09-19): *"acting should take an opposing roll. But then also have a
    default value like interrogation does"* - so after the opposing side and the note
    comes what the players GOT, blank for the default. The number goes to the GM-only
    notes (`hidden.py`); `rules.render_annotated` never reads it.
    """
    settled = _contest(menu, roll)
    if settled is None:
        return None
    what, note, contest, seq = settled
    if what == 'discard':
        return Decision(discard=True)
    if seq is not None:
        menu.used.add(seq)
    rank = roll.rank
    if rank is None:
        who = rules.personal_name(roll.character)
        rank = _optional_number(menu.ask, f"  {who}'s acting rank? [none] > ")
    default = modes.default_outcome(roll.skill)
    outcome = _prompt(menu.ask, f'  What did they get? [{default}] > ')
    return Decision(note=note, contest=contest, opponent=seq, rank=rank, outcome=outcome)


def _decide(menu: _Menu, roll: Roll) -> Decision | None:
    """Ask what this roll's MODE leaves to ask. None when the GM finished."""
    mode = modes.mode_of(roll.skill)
    if rules.is_interrogation(roll):
        # Interrogation never sees o/c/d/ob: no contest (the opposing roll is the
        # NPC's Sincerity, never written publicly) and no bonus (feature 206).
        return _interrogate(menu.ask, roll, menu.conv)
    if mode == 'hidden':
        return _acting(menu, roll)
    if mode in ('contested_required', 'contested_maybe_unopposed'):
        return _always_contested(menu, roll, mode)
    if mode in ('always_open', 'default_open'):
        return _open_by_default(menu, roll, only_open=mode == 'always_open')
    return _full_menu(menu, roll)


def _staged_text(conv: Conversation, roll: Roll, decision: Decision) -> str:
    if decision.discard:
        return 'discarded'
    shown = _apply(roll, decision)
    if rules.is_interrogation(shown):
        return rules.render_interrogation([shown])
    return rules.render_annotated(shown, conv.npc_name)


def annotate(
    conversation: Conversation | None = None,
    *,
    ask: Ask = ask_quietly,
    mine: Callable[[], Sequence[gmrolls.GmRoll]] = gmrolls.recent,
    undoable: Undoable = keys.ask_with_undo,
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
    menu = _Menu(ask=ask, undoable=undoable, conv=conv, mine=list(mine()), used=set())
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
            decision = _decide(menu, roll)
            if decision is None:
                break
            staged[index] = decision
            print(f'  staged: {_staged_text(conv, roll, decision)}')
            _compare_privately(conv, roll, decision)
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
    used = {decision.opponent for decision in staged.values() if decision.opponent is not None}
    for entry in menu.mine:
        if entry.seq in used:
            entry.paired = True
    discarded = sum(1 for decision in staged.values() if decision.discard)
    kept = len(staged) - discarded
    tail = f', {discarded} discarded' if discarded else ''
    print(f'Annotated {kept} roll(s){tail}.')


def _compare_privately(conv: Conversation, roll: Roll, decision: Decision) -> None:
    """A roll joining a line here gets the same private comparison the watcher gives
    one that lands on a line by itself (`conversation.announce_comparison`)."""
    if decision.line is None or decision.discard:
        return
    for line in conv.lines:
        if line.id == decision.line:
            found = hidden.compare(conv, line, _apply(roll, decision))
            if found is not None:
                print(f'  = {found.describe()}')
