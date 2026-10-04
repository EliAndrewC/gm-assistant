"""Feature 214: the Isawa Ishi 3rd Dan boost, recorded WITH the roll it boosts.

The rule (`rules/04-schools.md`, Isawa Ishi, Third Dan): *"After another character
makes a roll for which void points may be spent, you may spend one void point to
roll Xk1 and add the result to their total, where X is your precepts skill. You may
only do this once per roll."*

The GM's requirement is the ORDER of operations: *"we must take care to make sure
that when we add a bonus after the fact, we add it before the rounding down"* - a
13 Etiquette boosted by 8 is a 21, written as 20, never the already-written 10 plus
8. That falls out of folding the boost into `Roll.total`: every recording rule is
applied at render time from `total`, and each write replaces the conversation's
earlier lines, so a boost that lands after a write simply re-renders.

THREE WAYS IN, ONE PLACE TO AIM:

- the character-sheet bot's message for its two commands - `**Isawa Tadashi**:
  **8** Isawa Ishi 3rd Dan[, boosting <jump link>]` (the contract is that app's
  https://github.com/EliAndrewC/character-sheet/issues/2). The jump link is the MESSAGE
  command's target;
- a dice card the player rolled on the sheet and pasted - an image whose recorded
  row is `spend_vp_xk1:isawa_ishi`;
- typed - a number beside the word "Ishi" (`8 ishi`, `Ishi 3rd Dan: 8`). "3rd Dan"
  alone is not enough: the Ide Diplomat's 3rd Dan SUBTRACTS, and is not this.

A boost posted as a Discord REPLY is aimed at the replied-to message. A slash
command cannot be sent as a reply - Discord drops the reference - which is why the
sheet app has a message command for pointing.

A target is a MESSAGE id, matched against `Roll.message_id`. Exactly one collected
roll on that message, by another character, not yet boosted: applied with no GM
input. Anything else is HELD with its reason, and `annotate()` asks which roll it
goes on. Holding never loses a boost and never guesses.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from dataclasses import replace
from datetime import datetime
from typing import Any

from l7r.repl.rolls import rules
from l7r.repl.rolls.models import Boost, Conversation, Roll

#: The sheet app's recorded key for this technique (`roll_sessions`, there).
ROLL_KEY = 'spend_vp_xk1:isawa_ishi'

_BOT_BOOST = re.compile(
    r'^\s*\*\*(?P<character>[^*]{1,60})\*\*\s*:\s*\*\*(?P<total>\d{1,3})\*\*\s+'
    r'Isawa\s+Ishi\s+3rd\s+Dan\b',
    re.IGNORECASE,
)
_JUMP = re.compile(r'discord(?:app)?\.com/channels/(?:\d+|@me)/\d+/(?P<id>\d+)')
#: `8 ishi`, `+8 Isawa Ishi`. The lookbehind keeps `@8` (a rank) and `1.8` out.
_TYPED_BEFORE = re.compile(r'(?<![\w@.])\+?(?P<total>\d{1,3})\s*(?:isawa\s+)?ishi\b', re.I)
#: `Ishi 3rd Dan: 8`, `ishi boost +8`. `ishi 3rd` alone does not match: no word
#: boundary falls between the 3 and the `rd`.
_TYPED_AFTER = re.compile(
    r'\b(?:isawa\s+)?ishi\b(?:\s+(?:3rd|third)\s+dan)?(?:\s+(?:technique|boost))?'
    r'\s*[:=]?\s*\+?(?P<total>\d{1,3})\b',
    re.I,
)
#: The reference type that means a reply. A FORWARD carries a reference too, with
#: type 1, and is not aimed at anything.
_REPLY_REFERENCE = 0


def reply_target(message: Mapping[str, Any]) -> str:
    """The id of the message this one replies to, or ''."""
    ref: Mapping[str, Any] = message.get('message_reference') or {}
    if int(ref.get('type') or _REPLY_REFERENCE) != _REPLY_REFERENCE:
        return ''
    return str(ref.get('message_id') or '')


def from_bot(message: Mapping[str, Any], at: datetime, *, bot_id: str) -> Boost | None:
    """The sheet bot's post for `/ishi-3rd-dan-technique` or the message command."""
    author: Mapping[str, Any] = message.get('author') or {}
    if str(author.get('id') or '') != bot_id:
        return None
    content = str(message.get('content') or '')
    found = _BOT_BOOST.match(content)
    if found is None:
        return None
    link = _JUMP.search(content[found.end() :])
    return Boost(
        character=found.group('character').strip(),
        total=int(found.group('total')),
        message_id=str(message['id']),
        at=at,
        target_message_id=link.group('id') if link else '',
    )


def typed(message: Mapping[str, Any], character: str, at: datetime) -> Boost | None:
    """A boost typed by a player: a number beside "Ishi". `character` is the poster's."""
    content = str(message.get('content') or '')
    found = _TYPED_BEFORE.search(content) or _TYPED_AFTER.search(content)
    if found is None:
        return None
    return Boost(
        character=character,
        total=int(found.group('total')),
        message_id=str(message['id']),
        at=at,
        target_message_id=reply_target(message),
    )


def from_recorded(
    character: str, total: int, target: str, message: Mapping[str, Any], at: datetime
) -> Boost:
    """A pasted sheet card whose recorded row is this technique. The row's own target
    (the message command's) wins; otherwise the card's reply aims it."""
    return Boost(
        character=character,
        total=total,
        message_id=str(message['id']),
        at=at,
        target_message_id=target or reply_target(message),
    )


def same_character(one: str, other: str) -> bool:
    """`Isawa Tadashi` and `Tadashi` are one character - names here are full on one
    path (the sheet) and given on another (a typed roll's roster lookup)."""
    a, b = one.strip().lower(), other.strip().lower()
    return a == b or rules.personal_name(one).lower() == rules.personal_name(other).lower()


def describe(boost: Boost) -> str:
    return f"{rules.personal_name(boost.character)}'s Ishi 3rd Dan +{boost.total}"


def place(conv: Conversation, boost: Boost) -> str:
    """Record `boost`, apply it if its target is certain, and say what happened."""
    conv.boosts.append(boost)
    reason = _why_not(conv, boost)
    if reason:
        boost.held_because = reason
        return f'  ? {describe(boost)} is waiting for annotate(): {reason}'
    index = _targets(conv, boost.target_message_id)[0]
    before = conv.rolls[index].total
    apply(conv, boost, index)
    after = conv.rolls[index]
    return (
        f'  + {describe(boost)} to {rules.personal_name(after.character)} {after.skill} '
        f'({before} -> {after.total})'
    )


def _targets(conv: Conversation, message_id: str) -> list[int]:
    return [
        index
        for index, roll in enumerate(conv.rolls)
        if roll.message_id == message_id and roll.attributed and not roll.discarded
    ]


def _why_not(conv: Conversation, boost: Boost) -> str:
    """Why `boost` cannot be applied by itself, or '' when it can."""
    if not boost.target_message_id:
        return 'it was not aimed at a roll'
    hits = _targets(conv, boost.target_message_id)
    if not hits:
        return 'the message it answers holds no roll from this conversation'
    if len(hits) > 1:
        return f'the message it answers holds {len(hits)} rolls'
    roll = conv.rolls[hits[0]]
    if same_character(roll.character, boost.character):
        return 'the rule boosts ANOTHER character, and that roll is their own'
    if roll.boost:
        return f'{rules.personal_name(roll.boosted_by)} already boosted that roll (once per roll)'
    return ''


def apply(conv: Conversation, boost: Boost, index: int) -> Roll:
    """Fold `boost` into the roll at `index` - into its RAW total, before every rule."""
    roll = conv.rolls[index]
    boosted = replace(
        roll, total=roll.total + boost.total, boost=boost.total, boosted_by=boost.character
    )
    conv.rolls[index] = boosted
    boost.applied_to = index
    boost.held_because = ''
    return boosted


def unapply(conv: Conversation, boost: Boost) -> Roll:
    """Take an applied boost back off its roll; the boost is held again."""
    assert boost.applied_to is not None
    index = boost.applied_to
    roll = conv.rolls[index]
    restored = replace(roll, total=roll.total - roll.boost, boost=0, boosted_by='')
    conv.rolls[index] = restored
    boost.applied_to = None
    boost.held_because = 'taken back with cancel_boost()'
    return restored


def eligible(conv: Conversation, exclude: Collection[int] = ()) -> list[int]:
    """Every roll a held boost may be put on in `annotate()`: attributed, undiscarded,
    annotated or not (the GM's words), and not already boosted (once per roll).
    `exclude` holds rolls another boost is staged onto in the same run."""
    return [
        index
        for index, roll in enumerate(conv.rolls)
        if roll.attributed and not roll.discarded and not roll.boost and index not in exclude
    ]


def held(conv: Conversation) -> list[Boost]:
    return [boost for boost in conv.boosts if boost.held]
