"""`tact`, `sincerity` and the rest at the prompt: tag a roll, or roll for the NPC.

Feature 207. The GM's habit-to-be: *"instead of saying `xky(8, 3) + 10` I will try
to start saying `xky(8, 3) + 10 - sincerity`"*. The tag does three jobs:

- it says what the roll WAS, so `annotate()` can pair a player's manipulation with
  the GM's tact roll by itself;
- it reads the NPC's ring and rank off the dice and REMEMBERS them
  (`npcnumbers.py`), so the same NPC has the same tact next month;
- it checks the roll against what is remembered and STOPS when they disagree.

The same names are callable, and roll for the NPC from the record:

    tact()          roll from the record, asking for whatever is missing
    tact(2)         state the rank; the ring comes from the record or is asked for
    tact(5, 3)      exactly `xky(5, 3) - tact`
    tact(vp)        spend a void point: one more rolled AND kept; `vp * 2` for two

THE ONE DIFFERENCE between `sincerity(8, 3)` and `xky(8, 3) - sincerity` is the
automatic free raises (acting on sincerity and intimidation, history on culture, law
and strategy): ONLY the called form adds them. The GM (2026-09-19): *"The automatic
raises should only be applied when we roll with the skill function and not when I
roll with the xky function"* - because the `+ 10` they type onto an `xky` roll IS
the acting bonus, and the tag adding it again would count it twice.

`acting(2)` and `history(3)` RECORD and never roll: *"me saying `acting(2)` or
`history(3)` do not actually generate rolls the way that they do for every other
skill. Instead, that serves only to record that the NPC has that rank."*

NOTHING IS RECORDED OR CHECKED WITHOUT AN OPEN CONVERSATION. A tag made outside one
only marks the roll. The GM scoped the check to *"if we are in a conversation with
an NPC"*, and the fidelity review struck a draft that recorded such rolls later: the
numbers could land on the wrong NPC's permanent record.

SEVERAL NPCS (feature 230). `souma.tact()`, `xky(5, 3) - souma.tact`, `xky(5, 3) -
tact - souma` and `xky(5, 3) - souma - tact` are all Souma's roll; a bare `tact()` or
`xky(5, 3) - tact` is the PRIMARY's. What a tag DOES - read and record the ring and rank,
stop and ask on a disagreement, take an oppose penalty off, note a Sincerity roll - all
depends on whose roll it is, so in a conversation that has ever had a second member a
bare tag only MARKS the roll and waits (`_pending`). `- souma` settles it on Souma; the
end of the GM's statement (`settle_pending`, from the prompt hooks `shell.py` installs)
settles it on the primary. Both orders end in the same `SkillTag._settle`, which is why
`- tact - souma` and `- souma - tact` are the same (the GM asked for exactly that).
Nothing is ever applied provisionally to the primary and moved: the disagreement prompt
would already have asked about the wrong NPC's record.

Once the primary has LEFT, every default-to-primary form raises `PrimaryLeft` (GM
2026-10-26: *"I must always call e.g. `souma.sincerity()` rather than expecting that
`sincerity()` calls will dispatch to Souma"*), and a departed member's handle raises
`MemberLeft` for every roll except one made while they were there.
"""

from __future__ import annotations

import functools
import importlib
from collections.abc import Callable
from datetime import datetime

from l7r.repl import dice, gmrolls
from l7r.repl.rolls import menu, npcnumbers, oppose, voidspent
from l7r.repl.rolls.models import Conversation, Member
from l7r.repl.rolls.skills import advanced_skills, load_skills, rules_skills, skill_rings

Ask = Callable[[str], str]


class PrimaryLeft(RuntimeError):
    """A roll would default to the primary NPC, and the primary has left."""


class MemberLeft(RuntimeError):
    """A roll was made for a member who had left the conversation."""


#: Feature 230. GM rolls tagged with a skill but not yet with an NPC, waiting for the
#: statement to end (`settle_pending`) or for `- souma`. Identity matters, not equality:
#: two rolls can have equal fields.
_pending: list[gmrolls.GmRoll] = []
#: Tagged rolls whose statement ended while the primary was away: they belong to nobody
#: until the GM marks them (`_ - souma`), and are never settled by themselves.
_orphaned: list[gmrolls.GmRoll] = []

#: The NPC skill whose rolls are hidden from the players and kept in the GM-only
#: notes however they were made - Interrogation's opposing skill (`hidden.py`).
HIDDEN_SKILL = 'sincerity'

RANKS = (0, 5)
RING_VALUES = (2, 6)


def _ask(question: str) -> str:
    """Every prompt here goes through the annotate menu's quiet input, so answers
    stay out of the readline history (2026-09-09). Resolved at call time so a test
    can replace `ask_quietly`."""
    # `annotate` the FUNCTION shadows the module on the package, so import by path.
    module = importlib.import_module('l7r.repl.rolls.annotate')
    asker: Ask = module.ask_quietly
    return asker(question)


# Feature 210: this reads the real terminal, so a choice asked through it is a menu.
menu.terminal_asker(_ask)

#: The disagreement's answers. "Mistake" comes first and so starts highlighted: it is
#: also what Ctrl-C means at that prompt, and the answer that changes nothing.
MISTAKE = menu.Option('m', 'the roll was a mistake - roll it again', ('mistake',))
RECORD_WRONG = menu.Option('r', 'the record was wrong - correct it', ('record',))


def _open() -> Conversation | None:
    from l7r.repl.rolls import conversation

    return conversation._open


def _waiting(entry: gmrolls.GmRoll) -> bool:
    return any(e is entry for e in _pending) or any(e is entry for e in _orphaned)


def _forget(entry: gmrolls.GmRoll) -> None:
    _pending[:] = [e for e in _pending if e is not entry]
    _orphaned[:] = [e for e in _orphaned if e is not entry]


def present_at(conv: Conversation, member: Member, when: datetime) -> bool:
    """Was `member` in the conversation at `when`? A member named at the open counts
    from the beginning of time - the GM rolls the NPC's side BEFORE opening, as a
    rule (`gmrolls`) - and one added later from the moment they joined."""
    mine = [e for e in conv.events if e.member == member.id]
    # Named at the open: no events, or a first event that is leaving.
    inside = not mine or mine[0].kind == 'left'
    for event in mine:
        if event.at > when:
            break
        inside = event.kind == 'joined'
    return inside


def forget_pending() -> None:
    """The conversation is closing: nothing waits for an NPC any more."""
    _pending.clear()
    _orphaned.clear()


def default_member(conv: Conversation, skill: str = 'tact') -> Member:
    """The primary, for a roll that names no NPC - or `PrimaryLeft`, which says what
    to type instead."""
    if conv.primary.present:
        return conv.primary
    here = conv.present
    if not here:
        raise PrimaryLeft(f'{conv.primary.name} has left, and nobody is left in the conversation.')
    forms = ' or '.join(f'{m.handle}.{skill}()' for m in here)
    marks = ' or '.join(f'xky(...) - {m.handle}' for m in here)
    raise PrimaryLeft(
        f'{conv.primary.name} has left the conversation, so a {skill} roll that names no NPC '
        f'has nobody to belong to. Say whose it is: {forms}; for a roll already made, {marks}.'
    )


def claim(conv: Conversation, entry: gmrolls.GmRoll, member: Member) -> None:
    """Say `entry` is `member`'s roll. Refuses a second NPC, and a roll made after the
    member left (`MemberLeft`) - marking an earlier one, settled late, is allowed."""
    if entry.npc and entry.npc != member.id:
        raise ValueError(
            f"that roll is already {conv.member(entry.npc).name}'s - roll again if it was the "
            'wrong one.'
        )
    if not present_at(conv, member, entry.at):
        raise MemberLeft(f'{member.name} was not in the conversation when that roll was made.')
    entry.npc = member.id


def settle_pending(ask: Ask | None = None) -> None:
    """Settle every bare tag on the primary - the end of the GM's statement.

    Called by the prompt hooks and by every function the GM calls next, NEVER by the
    watcher thread: settling can stop and ask. With the primary gone the rolls are
    left marked and unowned, and `PrimaryLeft` says how to give them an owner.
    """
    if not _pending:
        return
    conv = _open()
    waiting = list(_pending)
    _pending.clear()
    if conv is None:
        return
    tags = tags_by_name()
    left: list[gmrolls.GmRoll] = []
    for entry in waiting:
        # `- souma` takes a roll off `_pending` as it settles it, so every roll here
        # still names no NPC.
        if not conv.primary.present:
            left.append(entry)
            continue
        entry.npc = conv.primary.id
        tags[entry.tagged]._settle(conv, conv.primary, entry, ask or _ask)
    if left:
        _orphaned.extend(left)
        default_member(conv, left[0].tagged)  # raises, naming the members still here


@functools.cache
def extra_dice_table() -> dict[str, frozenset[str]]:
    """school -> skills with an extra die. Read once; the rules do not change mid-session."""
    return npcnumbers.school_extra_dice(load_skills())


def extra_dice(skill: str, schools: tuple[str, ...]) -> tuple[int, str]:
    """How many of this pool's dice are the NPC's school's, and which school."""
    table = extra_dice_table()
    for school in schools:
        if skill in table.get(school, frozenset()):
            return 1, school
    return 0, ''


class VoidPoints:
    """`vp`: says a called roll spends a void point. `vp * 2` spends two."""

    def __init__(self, count: int = 1) -> None:
        if count < 1:
            raise ValueError('a void point marker spends at least one')
        self.count = count

    def __mul__(self, times: int) -> VoidPoints:
        return VoidPoints(self.count * int(times))

    __rmul__ = __mul__

    def __repr__(self) -> str:
        return 'vp' if self.count == 1 else f'vp * {self.count}'


vp = VoidPoints()


def _ask_number(question: str, low: int, high: int, ask: Ask) -> int:
    while True:
        answer = ask(question).strip()
        if answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        print(f'  ? a whole number from {low} to {high}')


def resolve(
    conv: Conversation,
    entry: gmrolls.GmRoll,
    reading: npcnumbers.Reading,
    ask: Ask,
    member: Member | None = None,
) -> None:
    """Record what a tagged roll says, or stop and ask when it disagrees.

    The two answers are the GM's: *"given the option to either correct the skill
    that is there or cancel ... I would like to be able to cancel either by hitting
    Ctrl+c and having that actually caught and recorded as indicating that I made a
    mistake and that I will redo the skill correctly."* So Ctrl-C here is an ANSWER,
    not an interruption, and is caught. The void point answer joined on 2026-09-19
    for a roll that is off by exactly 1k1 or 2k2. `member` is whose record it is
    (feature 230); the primary when not given.
    """
    who = member or conv.primary
    found = npcnumbers.compare(who.numbers, reading)
    if found is None:
        added = npcnumbers.fill(who.numbers, reading)
        if added:
            print(f'  recorded for {who.name}: {", ".join(added)}')
        return
    print(f'  ! {who.name}: {found.describe}.')
    choices = ['[m] the roll was a mistake (or Ctrl-C)', '[r] the record was wrong']
    if found.void_answer:
        choices.append(f'[v] {found.void_answer}')
    if not menu.interactive(ask):  # at a terminal the menu below IS this list
        print('    ' + '   '.join(choices))
    allowed = 'mrv' if found.void_answer else 'mr'
    rows = [MISTAKE, RECORD_WRONG]
    if found.void_answer:
        rows.append(menu.Option('v', found.void_answer))
    answer = ''
    while answer not in tuple(allowed):
        try:
            title = f'    {who.name}: which is it?'
            answer = menu.ask_choice(ask, '    > ', title, rows).strip().lower()[:1]
        except KeyboardInterrupt, EOFError:
            print()
            answer = 'm'
    if answer == 'm':
        entry.mistake = True
        print('  marked as a mistake - the record is unchanged. Roll it again.')
    elif answer == 'r':
        npcnumbers.accept(who.numbers, reading)
        ring = reading.ring_name.capitalize()
        print(f'  record corrected: {ring} {reading.ring}, {reading.skill} {reading.rank}')
    elif found.void_points > 0:
        entry.void_points = found.void_points
        voidspent.note(conv, entry, found.void_points)
        spent = reading_without(reading, found.void_points)
        if reading.skill not in who.numbers:
            # ASK, never read the rank off the dice here (GM 2026-10-26: *"I do want the V
            # answer to ask instead of recording a rank off the dice when none is on
            # record"*). A pool the GM built around a void point is the least trustworthy
            # place to infer a skill from - Fukushin's 4k4 recorded sincerity 0 unasked.
            rank = _ask_number(
                f"  {who.name}'s {reading.skill} rank? [{RANKS[0]}-{RANKS[1]}] > ", *RANKS, ask
            )
            spent = npcnumbers.Reading(spent.skill, spent.ring_name, spent.ring, rank)
        added = npcnumbers.fill(who.numbers, spent)
        # It said "the record is unchanged" even when this filled a rank the record lacked
        # (found 2026-10-26: `xky(4, 4) - sincerity` with Air 3 on record and [v] wrote
        # sincerity 0 while saying nothing had changed). Say what was added.
        if added:
            print(f'  noted - and recorded for {who.name}: {", ".join(added)}.')
        else:
            print('  noted - the record is unchanged.')
    else:
        # The roll the record came from spent them; logged as an earlier roll (217).
        voidspent.note(conv, entry, found.void_points)
        npcnumbers.accept(who.numbers, reading)
        print(f'  record corrected: {reading.ring_name.capitalize()} {reading.ring}')


def taxed(conv: Conversation, total: dice.DiceTotal, skill: str) -> dice.DiceTotal:
    """Take a player's Oppose Social / Oppose Knowledge off an NPC roll (feature 208).

    BOTH forms pay it - `tact()` and `xky(5, 3) - tact` - unlike the automatic acting
    and history RAISES, which only the called form adds. That rule exists because the
    GM already types the acting `+ 10` onto an `xky` roll by hand; nobody types this
    penalty by hand, and automating it is the whole of the GM's request (2026-09-19:
    *"automatically apply the penalties ... All rolls made by the NPC"*). The penalty
    is SET on the recorded roll, apart from the GM's own bonus, so it is never
    subtracted twice and `_ + 15` afterwards still lands on the right number.
    """
    found = oppose.penalize(conv, total.entry, skill)
    if found is None:
        return total
    print(f'  {found.describe()}: {total.entry.total}')
    return dice.DiceTotal(total.entry.total, total.entry)


def reading_without(reading: npcnumbers.Reading, void_points: int) -> npcnumbers.Reading:
    """The same reading with `void_points` dice taken back out of the ring."""
    return npcnumbers.Reading(
        reading.skill, reading.ring_name, reading.ring - void_points, reading.rank
    )


class SkillTag:
    """One skill's name at the prompt."""

    def __init__(
        self, name: str, ring_name: str, *, advanced: bool = False, member: str = ''
    ) -> None:
        self.name = name
        self.ring_name = ring_name
        self.advanced = advanced
        #: Feature 230. The member this tag rolls for (`souma.tact`), or '' for the
        #: bare name at the prompt, which means the primary.
        self.member = member

    def bound(self, member: str) -> SkillTag:
        """This skill for one member: what `souma.tact` is."""
        return SkillTag(self.name, self.ring_name, advanced=self.advanced, member=member)

    def __repr__(self) -> str:
        return f'<{self.name}: `roll - {self.name}` tags a roll, `{self.name}()` rolls it>'

    def _member(self, conv: Conversation) -> Member:
        """Whose roll a called form makes: the bound member, or the primary."""
        if not self.member:
            return default_member(conv, self.name)
        member = conv.member(self.member)
        if not member.present:
            raise MemberLeft(f'{member.name} has left the conversation.')
        return member

    # --- the tag form -------------------------------------------------------

    def tag_roll(self, total: dice.DiceTotal, *, ask: Ask | None = None) -> dice.DiceTotal:
        """`xky(5, 3) - tact`. Called by `DiceTotal.__sub__`; returns the same total."""
        entry = total.entry
        if entry.tagged:
            raise ValueError(
                f'that roll is already tagged {entry.tagged} - a second tag would overwrite '
                'what it was. Roll again if it was the wrong one.'
            )
        conv = _open()
        if conv is not None and self.member:
            claim(conv, entry, conv.member(self.member))  # `xky(5, 3) - souma.tact`
        entry.tagged = self.name
        if conv is None:
            print(f'  tagged {self.name} - no conversation is open, so nothing is recorded.')
            return total
        if not entry.npc and conv.ever_multi:
            # Feature 230: whose roll it is may still follow (`- souma`); the end of
            # the statement settles it on the primary otherwise.
            _pending.append(entry)
            return total
        member = conv.member(entry.npc) if entry.npc else default_member(conv, self.name)
        entry.npc = member.id
        return self._settle(conv, member, entry, ask or _ask)

    def _settle(
        self, conv: Conversation, member: Member, entry: gmrolls.GmRoll, ask: Ask
    ) -> dice.DiceTotal:
        """Everything a tag does, for `member`. The ONE place it happens, whichever
        order the GM said the skill and the NPC in (feature 230)."""
        _forget(entry)
        self._check(conv, member, entry, ask)
        # AFTER the check: a roll the GM called a mistake there pays nothing.
        return self._kept(conv, taxed(conv, dice.DiceTotal(entry.total, entry), self.name))

    def _kept(self, conv: Conversation, total: dice.DiceTotal) -> dice.DiceTotal:
        """Note a Sincerity roll on the conversation, with the line it was rolled
        during, so it reaches the GM-only notes however it was made (`hidden.py`)."""
        if self.name == HIDDEN_SKILL and not total.entry.mistake:
            line = conv.lines[-1].id if conv.lines else None
            conv.sincerity_rolls.append((total.entry, line))
        return total

    def __rsub__(self, other: object) -> object:
        """A plain number minus a tag: there is no roll behind it to tag."""
        raise TypeError(
            f'only a roll can be tagged: `xky(5, 3) - {self.name}`, or `{self.name}(5, 3)`'
        )

    def _check(self, conv: Conversation, member: Member, entry: gmrolls.GmRoll, ask: Ask) -> None:
        extra, school = extra_dice(self.name, member.schools)
        if extra:
            print(f"  ({school} school: one of those dice is the school's)")
        reading = npcnumbers.infer(
            entry.asked,
            self.name,
            self.ring_name,
            extra_dice=extra,
            void_points=entry.void_points,
        )
        resolve(conv, entry, reading, ask, member)

    # --- the called form ----------------------------------------------------

    def __call__(self, *args: int | VoidPoints, ask: Ask | None = None) -> dice.DiceTotal | None:
        asker = ask or _ask
        conv = _open()
        if conv is None:
            raise RuntimeError(
                f'no conversation open - there is no NPC to roll {self.name} for. '
                'begin_conversation("Name") first.'
            )
        settle_pending(asker)  # an earlier statement's bare tag goes first (feature 230)
        member = self._member(conv)
        spent = sum(a.count for a in args if isinstance(a, VoidPoints))
        numbers = [int(a) for a in args if not isinstance(a, VoidPoints)]
        if len(numbers) > 2:
            raise TypeError(f'{self.name}(), {self.name}(rank) or {self.name}(rolled, kept)')
        if self.name in npcnumbers.RECORD_ONLY:
            self._record_only(conv, member, numbers, spent, asker)
            return None
        if len(numbers) == 2:
            return self._kept(conv, self._pool(conv, member, numbers[0], numbers[1], spent, asker))
        rank = self._rank(member, numbers[0] if numbers else None, asker)
        if rank is None:
            return None
        ring = member.numbers.get(self.ring_name)
        if ring is None:
            ring = _ask_number(
                f"  {member.name}'s {self.ring_name.capitalize()}? "
                f'[{RING_VALUES[0]}-{RING_VALUES[1]}] > ',
                *RING_VALUES,
                asker,
            )
            member.numbers[self.ring_name] = ring
            print(f'  recorded for {member.name}: {self.ring_name.capitalize()} {ring}')
        extra, _ = extra_dice(self.name, member.schools)
        total = self._roll(conv, member, ring + rank + extra + spent, ring + spent, rank, spent)
        return self._kept(conv, total)

    def _rank(self, member: Member, stated: int | None, ask: Ask) -> int | None:
        """The rank to roll: stated, recorded, or asked for. None cancels the roll."""
        recorded = member.numbers.get(self.name)
        if stated is None:
            if recorded is not None:
                return recorded
            stated = _ask_number(
                f"  {member.name}'s {self.name} rank? [{RANKS[0]}-{RANKS[1]}] > ", *RANKS, ask
            )
        if not RANKS[0] <= stated <= RANKS[1]:
            raise ValueError(f'a rank runs from {RANKS[0]} to {RANKS[1]}, not {stated}')
        if recorded is None:
            member.numbers[self.name] = stated
            print(f'  recorded for {member.name}: {self.name} {stated}')
            return stated
        if recorded == stated:
            return stated
        print(f'  ! {member.name}: {self.name} {recorded} recorded, you said {stated}.')
        if not menu.interactive(ask):  # at a terminal the menu below IS this list
            print('    [m] I made a mistake (or Ctrl-C)   [r] the record was wrong')
        answer = ''
        while answer not in ('m', 'r'):
            try:
                title = f'    {member.name}: which is it?'
                answer = menu.ask_choice(ask, '    > ', title, (MISTAKE, RECORD_WRONG))
                answer = answer.strip().lower()[:1]
            except KeyboardInterrupt, EOFError:
                print()
                answer = 'm'
        if answer == 'm':
            print('  nothing rolled and nothing changed.')
            return None
        member.numbers[self.name] = stated
        print(f'  record corrected: {self.name} {stated}')
        return stated

    def _record_only(
        self, conv: Conversation, member: Member, numbers: list[int], spent: int, ask: Ask
    ) -> None:
        """`acting(2)` / `history(3)`: say what the NPC has. Never a roll."""
        if len(numbers) == 2 or spent:
            raise TypeError(
                f'{self.name} is recorded, never rolled: `{self.name}(2)` says the NPC has '
                f'{self.name} 2. To tag a real roll of it, `xky(6, 3) - {self.name}`.'
            )
        if not numbers and self.name in member.numbers:
            print(f'  {member.name}: {self.name} {member.numbers[self.name]}')
            return
        self._rank(member, numbers[0] if numbers else None, ask)

    def _pool(
        self, conv: Conversation, member: Member, rolled: int, kept: int, spent: int, ask: Ask
    ) -> dice.DiceTotal:
        """`tact(5, 3)` - the stated pool, checked exactly as a tagged `xky` is.

        With `vp`, the stated pool is the BASE and the void point dice go on top, so
        `tact(5, 3, vp)` rolls 6k4 and still reads as tact 2, Air 3.
        """
        extra, _ = extra_dice(self.name, member.schools)
        rank = max(0, rolled - kept - extra)
        total = self._roll(conv, member, rolled + spent, kept + spent, rank, spent)
        self._check(conv, member, total.entry, ask)
        if total.entry.mistake:
            # `_roll` priced the oppose penalty before the GM called the roll a
            # mistake; re-deriving it takes it back off (a mistake pays nothing).
            oppose.penalize(conv, total.entry, self.name)
        return total

    def _roll(
        self, conv: Conversation, member: Member, rolled: int, kept: int, rank: int, spent: int
    ) -> dice.DiceTotal:
        """Roll the pool and add what the called form adds by itself.

        A rank of 0 does not reroll tens, and an ADVANCED skill at 0 takes -10
        (`rules/02-skills.md`: *"If you roll any skill which you have at 0, you
        don't reroll 10s. If the skill is advanced, subtract 10 from your total."*).
        """
        print(f'  {member.name} {self.name}: {rolled}k{kept}')
        total = dice.xky(rolled, kept, reroll=rank > 0)
        total.entry.tagged = self.name
        total.entry.npc = member.id
        total.entry.void_points = spent
        voidspent.note(conv, total.entry, spent)
        if rank == 0 and self.advanced:
            total = total + -10
            print('  -10: an advanced skill at rank 0')
        for source, source_rank, bonus in npcnumbers.automatic_raises(self.name, member.numbers):
            total = total + bonus
            print(f'  +{bonus} {source} {source_rank}')
        return taxed(conv, total, self.name)


def build_tags() -> dict[str, SkillTag]:
    """One tag per skill in the rules' skill list, keyed by the name at the prompt.

    Read from the rules, so a skill added there is at the prompt without an edit
    here. A missing rules mount means no tags rather than a REPL that will not
    start: the dice and the name picks do not need the rules.
    """
    try:
        rings = skill_rings()
        advanced = advanced_skills()
        names = rules_skills()
    except OSError:
        return {}
    return {
        name: SkillTag(name, rings[name], advanced=name in advanced)
        for name in names
        if name in rings
    }


@functools.cache
def tags_by_name() -> dict[str, SkillTag]:
    """`build_tags()`, read once: the handles and the settling look skills up by name."""
    return build_tags()


class MemberHandle:
    """A member of the conversation at the prompt (feature 230): `souma`.

    `souma.tact()` rolls Souma's tact; `xky(5, 3) - souma.tact` and `xky(5, 3) - souma`
    say a roll is his. Holds only the member's id, so a handle never keeps a closed
    conversation's state alive.
    """

    def __init__(self, member_id: str, name: str, handle: str) -> None:
        self.member_id = member_id
        self.name = name
        self.handle = handle

    def __repr__(self) -> str:
        return (
            f'<{self.name}: `{self.handle}.tact()` rolls for them, '
            f'`xky(5, 3) - {self.handle}` marks a roll as theirs>'
        )

    @property
    def member(self) -> Member:
        conv = _open()
        if conv is None:
            raise RuntimeError(f'no conversation is open, so {self.name} is in none.')
        return conv.member(self.member_id)

    def __getattr__(self, skill: str) -> SkillTag:
        if not skill.startswith('_'):
            tags = tags_by_name()
            if skill in tags:
                return tags[skill].bound(self.member_id)
        raise AttributeError(f'{self.handle}.{skill}: no skill called {skill!r}')

    def tag_roll(self, total: dice.DiceTotal, *, ask: Ask | None = None) -> dice.DiceTotal:
        """`xky(5, 3) - souma`, before or after the skill's tag. A tag waiting for its
        NPC is settled here, on this member - the same `_settle` either order reaches."""
        member = self.member
        conv = _open()
        assert conv is not None  # `self.member` raised otherwise
        entry = total.entry
        claim(conv, entry, member)
        if entry.tagged and _waiting(entry):
            return tags_by_name()[entry.tagged]._settle(conv, member, entry, ask or _ask)
        return total

    def __rsub__(self, other: object) -> object:
        raise TypeError(f"only a roll can be marked as {self.name}'s: `xky(5, 3) - {self.handle}`")
