"""The opposing rolls the players must never see, kept in the GM-ONLY notes. PURE.

Feature 207 reverses one rule of feature 206. That feature wrote the NPC's
Sincerity roll NOWHERE, because on the public bio it tells the players whether
"nothing hidden detected" meant a truthful NPC or a good liar. The GM still wants
the number - just not there (2026-09-19): *"the hidden number should go into the
NPC's GM only notes in a block like discern honors and never in the bio."* Acting
is the same shape: *"if you are wearing a disguise, then we want to record what the
opposing roll was. But we do not want to show the players what the roll was."*

    Hidden rolls:
    - 2026-09-19 sincerity 48 (+10 not grilling) - Chizuru's death: Jimen 37@2 +5 not detected
    - 2026-09-19 investigation 27 vs Jimen acting 32@1 - posing as a rice factor: not seen through

NOTHING HERE MAY REACH THE BIO. The entries are built from the same rolls the public
lines are, so `tests/test_rolls_hidden.py` renders both for one conversation and
asserts that no hidden total appears in the public half.

EVERY SINCERITY ROLL IS KEPT, not only the one handed to `new_line_of_questioning`
(GM 2026-10-04: *"sincerity rolls made by NPCs in contested interrogation should be
saved to the GM-only section for my own later review, but aren't currently"*). A
roll made on its own - `sincerity()`, `xky(8, 3) - sincerity` - is noted on the
conversation with the line current when it was rolled (`npcskills`), and is then:

- that line's opposing roll, when the line was declared without one (`line_roll`).
  A roll made before ANY line was declared belongs to the first line;
- otherwise an entry of its own, naming its line and the interrogation roll it came
  after, so a second roll on one line is never silently dropped:

    - 2026-10-04 sincerity 33 - debts to the Mantis (another sincerity roll on this
      line): after Sadakichi 57@1   <- one line in the notes

Derived at render time rather than settled into `Line.sincerity`, so the one race
there could be - `new_line_of_questioning("x", sincerity())` evaluates the roll
while the PREVIOUS line is still current - cannot misfile it: the declaration
`claim`s the roll before anything reads the list.

The WHO-WON on each entry is the tool's arithmetic and is ADVISORY: it knows the
dice, the ranks and whether the line was grilling, and nothing of the situational
raises the GM hands out as the questioning goes. The PUBLIC outcome stays the GM's
call - the default until they mark a detection.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from l7r.repl.gmrolls import GmRoll
from l7r.repl.rolls import npcnumbers, npcskills, oppose, rules
from l7r.repl.rolls.models import Conversation, Line, Roll

HEADING = 'Hidden rolls:'

#: The NPC's free raises when the interrogator is NOT grilling - `rules/02-skills.md`,
#: Interrogation: *"If you are speaking to them casually rather than grilling them,
#: they get 2 free raises."* Applied ONLY by the tool, from the line's flag; the GM
#: (2026-09-19): *"I would never apply the 'lack of grilling' bonuses manually."*
#: Whatever the GM adds to the roll by hand is something else and is never adjusted.
CASUAL_RAISES = 2 * rules.FREE_RAISE


@dataclass(frozen=True)
class Comparison:
    """One interrogation roll against its line's hidden Sincerity roll."""

    roll: Roll
    bonus: int
    sincerity: int
    casual: int
    npc_bonus: int
    #: Feature 208: what a player's Oppose Social takes off the line's Sincerity
    #: roll, and the knack's name for the text. Private, like everything else here.
    opposed: int = 0
    opposed_by: str = ''

    @property
    def mine(self) -> int:
        return self.roll.total + self.bonus

    @property
    def theirs(self) -> int:
        return self.sincerity + self.casual + self.npc_bonus - self.opposed

    @property
    def detected(self) -> bool:
        """Interrogation takes a tie (`rules.CONTESTED_PAIRS`)."""
        return self.mine >= self.theirs

    def describe(self) -> str:
        who = rules.personal_name(self.roll.character)
        mine = f'{self.roll.total}' + (f' (+{self.bonus})' if self.bonus else '')
        extras = [f'+{self.casual} not grilling'] if self.casual else []
        if self.npc_bonus:
            extras.append(f'+{self.npc_bonus} free raises')
        if self.opposed:
            extras.append(f'-{self.opposed} {self.opposed_by}')
        theirs = f'{self.sincerity}' + (f' ({", ".join(extras)})' if extras else '')
        verdict = 'DETECTED' if self.detected else 'not detected'
        ask = ' - annotate() to say what they got' if self.awaiting else ''
        return f'{who} {mine} vs sincerity {theirs}: {verdict}{ask}'

    @property
    def awaiting(self) -> bool:
        """The tool reckons this roll detected something and the GM has not yet
        said what. The reckoning is still ADVISORY - Enter at the question keeps the
        default outcome - but it is no longer silent (GM 2026-09-29)."""
        return self.detected and not self.roll.outcome_settled and not self.roll.discarded


def awaiting_outcome(conv: Conversation, roll: Roll) -> bool:
    """True when `roll` is an interrogation roll on a line whose Sincerity roll it
    beats, and the GM has not yet said what it got. See `Comparison.awaiting`."""
    if not rules.is_interrogation(roll) or roll.line is None:
        return False
    for line in conv.lines:
        if line.id == roll.line:
            found = compare(conv, line, roll)
            return found is not None and found.awaiting
    return False


def claim(conv: Conversation, entry: GmRoll) -> None:
    """`entry` was handed to a declaration: it is that line's, and no longer loose."""
    conv.sincerity_rolls = [(e, on) for e, on in conv.sincerity_rolls if e is not entry]


def _usable(entry: GmRoll) -> bool:
    """A roll the GM called a mistake, or spent as the open side of a contest, is
    not a hidden Sincerity roll."""
    return not entry.mistake and not entry.paired


def line_roll(conv: Conversation, line: Line) -> GmRoll | int | None:
    """The Sincerity roll opposing `line`: the one it was declared with, else the
    first kept roll made while it was current (or before any line, for the first)."""
    if line.sincerity is not None:
        return line.sincerity
    first = conv.lines[0].id if conv.lines else None
    for entry, on in conv.sincerity_rolls:
        if _usable(entry) and (on == line.id or (on is None and line.id == first)):
            return entry
    return None


def extra_rolls(conv: Conversation) -> list[tuple[GmRoll, int | None]]:
    """The kept Sincerity rolls that oppose no line - written as entries of their own."""
    used = [line_roll(conv, line) for line in conv.lines]
    return [
        (entry, on)
        for entry, on in conv.sincerity_rolls
        if _usable(entry) and not any(entry is u for u in used)
    ]


def _came_after(conv: Conversation, entry: GmRoll) -> Roll | None:
    """The latest interrogation roll at or before `entry` - what it most likely answered."""
    found = [r for r in conv.rolls if rules.is_interrogation(r) and not r.discarded]
    found = [r for r in found if r.attributed and r.at <= entry.at]
    return max(found, key=lambda r: r.at, default=None)


def describe_extra(conv: Conversation, entry: GmRoll, on: int | None) -> str:
    """Where a Sincerity roll that opposes no line belongs, in words."""
    topic = next((line.description for line in conv.lines if line.id == on), None)
    where = (
        f'{topic} (another sincerity roll on this line)'
        if topic is not None
        else 'before any line of questioning'
    )
    after = _came_after(conv, entry)
    if after is None:
        return where
    rank = '' if after.rank is None else f'@{after.rank}'
    return f'{where}: after {rules.personal_name(after.character)} {after.total}{rank}'


def sincerity_rank(conv: Conversation, sincerity: GmRoll | int | None) -> int | None:
    """The NPC's Sincerity rank: recorded if known, else read off the dice.

    A bare number has no dice to read, so no free raises are inferred - a guess
    would be worse than nothing, since the GM would have to notice it to fix it.
    """
    if 'sincerity' in conv.numbers:
        return conv.numbers['sincerity']
    if not isinstance(sincerity, GmRoll):
        return None
    extra, _ = npcskills.extra_dice('sincerity', conv.schools)
    return npcnumbers.infer(sincerity.asked, 'sincerity', 'air', extra_dice=extra).rank


def compare(conv: Conversation, line: Line, roll: Roll) -> Comparison | None:
    """How `roll` stands against `line`'s Sincerity roll; None when there is none."""
    sincerity = line_roll(conv, line)
    if sincerity is None:
        return None
    total = _sincerity_total(sincerity)
    bonus, npc_bonus = rules.free_raises(roll.rank, sincerity_rank(conv, sincerity))
    casual = 0 if line.grilling else CASUAL_RAISES
    taxed = oppose.for_line(conv, line)
    if taxed is None:
        return Comparison(roll, bonus, total, casual, npc_bonus)
    return Comparison(roll, bonus, total, casual, npc_bonus, taxed.amount, taxed.knack)


def _sincerity_total(sincerity: GmRoll | int) -> int:
    """The line's Sincerity roll BEFORE any oppose penalty (feature 208).

    `unpenalized`, not `total`: a Sincerity roll tagged after an Oppose Social has
    already had the penalty set on it as an Air roll, and the LINE applies its own
    (`oppose.for_line`, which also covers the retroactive case). Reading `total`
    here would charge the NPC twice.
    """
    if isinstance(sincerity, GmRoll):
        return sincerity.unpenalized
    return int(sincerity)


def _on_line(conv: Conversation, line: Line) -> list[Roll]:
    return [
        r
        for r in conv.rolls
        if r.line == line.id and rules.is_interrogation(r) and not r.discarded and r.attributed
    ]


def entries(conv: Conversation) -> tuple[str, ...]:
    """This conversation's hidden-roll entries, in the order things happened."""
    day = f'{conv.opened_at:%Y-%m-%d}'
    out: list[str] = []
    for line in conv.lines:
        sincerity = line_roll(conv, line)
        if sincerity is None:
            continue
        total = _sincerity_total(sincerity)
        extras = [] if line.grilling else [f'+{CASUAL_RAISES} not grilling']
        taxed = oppose.for_line(conv, line)
        if taxed is not None:
            extras.append(f'-{taxed.amount} {taxed.knack}')
        casual = f' ({", ".join(extras)})' if extras else ''
        results = []
        for roll in _on_line(conv, line):
            found = compare(conv, line, roll)
            assert found is not None  # the line has a Sincerity roll
            rank = '' if roll.rank is None else f'@{roll.rank}'
            bonus = f' +{found.bonus}' if found.bonus else ''
            verdict = 'DETECTED' if found.detected else 'not detected'
            who = rules.personal_name(roll.character)
            results.append(f'{who} {roll.total}{rank}{bonus} {verdict}')
        tail = f': {", ".join(results)}' if results else ''
        out.append(f'- {day} sincerity {total}{casual} - {line.description}{tail}')
    for entry, on in extra_rolls(conv):
        out.append(f'- {day} sincerity {entry.total} - {describe_extra(conv, entry, on)}')
    for roll in conv.rolls:
        if roll.skill.lower() != 'acting' or roll.opposed_total is None:
            continue
        if roll.discarded or not roll.attributed:
            continue
        rank = '' if roll.rank is None else f'@{roll.rank}'
        mine, theirs = roll.final_total, roll.final_opposed or 0
        # Investigation is not one of acting's fixed pairings, so a tie is a tie.
        verdict = (
            'tied' if mine == theirs else ('not seen through' if mine > theirs else 'SEEN THROUGH')
        )
        who = rules.personal_name(roll.character)
        note = f' - {roll.note}' if roll.annotated else ''
        out.append(f'- {day} investigation {theirs} vs {who} acting {mine}{rank}{note}: {verdict}')
    return tuple(out)


def _split(gm_info: str) -> tuple[list[str], int, int]:
    lines = gm_info.replace('\r\n', '\n').split('\n')
    try:
        start = next(i for i, text in enumerate(lines) if text.strip() == HEADING)
    except StopIteration:
        return lines, -1, -1
    end = start + 1
    while end < len(lines) and lines[end].startswith('- '):
        end += 1
    return lines, start, end


def rewrite(gm_info: str, previous: Sequence[str], current: Sequence[str]) -> str:
    """Swap this conversation's earlier entries for its current ones.

    Entries from OLDER conversations stay exactly where they are: the block is a
    log across sessions, and this conversation only ever owns the lines it wrote.
    A block left empty loses its heading too.
    """
    lines, start, end = _split(gm_info)
    if start < 0:
        if not current:
            return gm_info
        while lines and not lines[-1].strip():
            lines.pop()
        return '\n'.join([*lines, '', HEADING, *current] if lines else [HEADING, *current])
    gone = set(previous)
    kept = [text for text in lines[start + 1 : end] if text not in gone]
    block = [HEADING, *kept, *current] if kept or current else []
    lines[start:end] = block
    return '\n'.join(lines)
