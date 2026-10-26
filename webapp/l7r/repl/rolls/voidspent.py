"""The void points an NPC spent in a conversation, kept in the GM-only notes. PURE.

Feature 217. The GM marks an NPC's void point at the prompt two ways - the called
form `tact(vp)` (`vp * 2` for two), and the `[v]` answer when a tagged roll is off
by exactly 1k1 or 2k2 - and until now that number lived only on the `GmRoll`, used
to keep the extra die from reading as a bigger ring. The GM (2026-10-17): *"if a
fight breaks out, then I have recorded all of the conversations in which the NPC
has spent void points so that I don't accidentally give them more void points for
the fight"*. So every spend is a line here:

    Void points spent:
    - 2026-10-17 1 void point on tact - confrontation on the Imperial road
    - 2026-10-17 2 void points on an earlier tact roll - confrontation on the Imperial road

Date, count, skill and the conversation's title - the line the GM approved. The
roll's total was struck by the fidelity review: it was not asked for.

The block is a LOG across conversations, exactly like `Hidden rolls:` and written
by the same `hidden.rewrite`: a conversation swaps only the lines it wrote itself.

A roll the GM called a MISTAKE spent nothing - they roll it again, and the re-roll
is the spend. Filtered at render time, because the mistake answer can come after
the void point was noted (`tact(5, 3, vp)` checks the pool after rolling it).

"The previous roll spent N" is logged too, worded as an earlier roll: that roll
may have been this conversation's or an older one's, and only the GM knows which.
"""

from __future__ import annotations

from l7r.repl.gmrolls import GmRoll
from l7r.repl.rolls.models import Conversation, Member, VoidSpend

HEADING = 'Void points spent:'


def note(conv: Conversation, entry: GmRoll, count: int) -> None:
    """Remember a spend. A negative `count` is the previous roll's (`Disagreement`)."""
    if not count:
        return
    earlier = count < 0
    for s in conv.void_spends:
        if s.entry is entry and s.earlier == earlier:
            # `tact(5, 3, vp)` notes its spend, then the check can ask again; the
            # answer is that roll's count, not a second spend.
            s.count = abs(count)
            return
    conv.void_spends.append(VoidSpend(entry, abs(count), earlier=earlier))


def _counted(conv: Conversation, member: Member) -> list[VoidSpend]:
    return [
        s
        for s in conv.void_spends
        if (s.earlier or not s.entry.mistake) and conv.owner(s.entry) is member
    ]


def entries(conv: Conversation, member: Member | None = None) -> tuple[str, ...]:
    """This conversation's `Void points spent:` lines for one member (the primary by
    default; feature 230), in the order they were spent."""
    day = f'{conv.opened_at:%Y-%m-%d}'
    about = f' - {conv.title}' if conv.title else ''
    out = []
    for s in _counted(conv, member or conv.primary):
        points = 'void point' if s.count == 1 else 'void points'
        on = f'an earlier {s.entry.tagged} roll' if s.earlier else s.entry.tagged
        out.append(f'- {day} {s.count} {points} on {on}{about}')
    return tuple(out)
