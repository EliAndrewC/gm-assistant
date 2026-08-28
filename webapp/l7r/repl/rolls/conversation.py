"""The conversation: the one stateful thing, and the only module that is not pure.

The GM opens a conversation by naming the NPC, plays, and closes it. Which NPC the
players are talking to is the one fact that cannot be inferred from a Discord
channel, so it is the one fact the GM supplies:

    >>> begin_conversation("Otsuki")
    >>> end_conversation()

`end_conversation()` WRITES IMMEDIATELY. There is no confirmation step and nothing
to approve: the entire point of the feature is to remove a manual step from the
table, and a "does this look right?" prompt would put one back at the moment it is
most expensive. The record is editable afterward, and `abandon_conversation()`
exists for the one case a confirmation would really serve - realizing the
conversation was opened against the wrong NPC.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from chargen import op
from chargen.opsynth import MatchResult, match_character
from l7r.repl.rolls import bio as biomod
from l7r.repl.rolls import discord, rules, sheet
from l7r.repl.rolls.models import Conversation, RecordingRule, Roll
from l7r.repl.rolls.parse import parse_message
from l7r.repl.rolls.skills import load_skills

#: How close in time a recorded roll must sit to the Discord message that shows it.
#: Generous on purpose: a player rolls on the sheet, looks at it, copies the image
#: and pastes it, and the observed gap runs to tens of seconds. Over-wide costs
#: nothing here because the author id already narrows the join to one person.
MATCH_WINDOW_SECONDS = 300

_lock = threading.Lock()
_open: Conversation | None = None


class NoConversation(RuntimeError):
    """Nothing is open."""


class AlreadyOpen(RuntimeError):
    """A conversation is already open; it names the NPC so the GM can close it."""


def _players(result: sheet.SheetResult) -> dict[str, str]:
    """Discord id -> character name.

    Prefers the character-sheet app. Falls back to a `[discord_players]` section in
    `development-secrets.ini` (`<discord_id> = <Character Name>`), which exists so
    the TYPED path works before the sheet endpoints are built - without some map,
    every typed roll would be unattributable and FR-018's "the typed path still
    works" would be empty words. The endpoint supersedes it when it lands.
    """
    if result.characters:
        return {did: c.name for did, c in result.characters.items()}
    import configparser

    parser = configparser.ConfigParser()
    parser.read(sheet.SECRETS)
    if not parser.has_section('discord_players'):
        return {}
    return {did: name for did, name in parser.items('discord_players')}


def _no_match(npc: str, match: MatchResult) -> str:
    """Why a name did not resolve, phrased so the GM can fix it in one try.

    Which OP record gets written to is never a guess. An ambiguous name is the one
    kind of question this feature still asks the GM (CLAUDE.md: an ambiguous
    character match is a question, "because that is about which record gets written
    to"), and the fix is to add a family or lineage name.
    """
    if match.kind == 'ambiguous':
        names = ', '.join(str(c.get('name') or '') for c in match.matches)
        return f'{npc!r} matches several characters: {names}. Name one of them in full.'
    nearest = ', '.join(match.nearest)
    return f'no character called {npc!r}' + (f'. Nearest: {nearest}' if nearest else '')


def begin_conversation(
    npc: str,
    channel: str | None = None,
    *,
    characters: Callable[[], Sequence[Mapping[str, object]]] = op.existing_characters,
    now: Callable[[], datetime] | None = None,
) -> Conversation:
    """Open a conversation with `npc`. Prints what it opened; returns it.

    The name resolves through `match_character`, exactly as `discern_honor` does:
    whole name tokens only, and an ambiguous name raises listing the candidates
    rather than picking one. Which record gets written to is not a guess we make.
    """
    global _open
    with _lock:
        if _open is not None:
            raise AlreadyOpen(
                f'already talking to {_open.npc_name}. end_conversation() to write it, '
                'or abandon_conversation() to throw it away.'
            )
        match = match_character(npc, characters())
        if match.kind != 'unique':
            raise ValueError(_no_match(npc, match))
        channel_id = discord.CHANNELS.get((channel or '').lower(), channel or '')
        if not channel_id:
            raise ValueError(
                f'name the channel: one of {", ".join(sorted(discord.CHANNELS))}, or a channel id'
            )
        clock = now or (lambda: datetime.now(UTC))
        _open = Conversation(npc=match.character, opened_at=clock(), channel_id=channel_id)
        print(f'Talking to {_open.npc_name}. Rolls from now until end_conversation().')
        return _open


def collect(
    conversation: Conversation | None = None,
    *,
    fetch: Callable[..., list[dict[str, Any]]] = discord.messages_since,
    recorded: Callable[..., sheet.SheetResult] = sheet.recorded_rolls,
    roster: Callable[..., sheet.SheetResult] = sheet.characters,
    vocabulary: tuple[str, ...] | None = None,
) -> Conversation:
    """Read everything posted since the last poll and fold it into the conversation."""
    conv = conversation or _require()
    words = vocabulary if vocabulary is not None else load_skills()
    try:
        messages = fetch(conv.channel_id, conv.last_seen or conv.opened_at)
    except discord.DiscordUnavailable as exc:
        conv.unresolved.append(str(exc))
        return conv

    from_sheet = recorded(conv.opened_at)
    who = _players(roster())
    if not from_sheet.available:
        note = f'recorded rolls unavailable ({from_sheet.reason})'
        if note not in conv.unresolved:
            conv.unresolved.append(note)

    for message in messages:
        conv.last_seen = str(message['id'])
        who_posted = who.get(discord.author_id(message), '')
        at = discord.parse_timestamp(message['timestamp'])
        found, problems = parse_message(
            str(message.get('content') or ''),
            words,
            character=who_posted,
            message_id=str(message['id']),
            at=at,
        )
        conv.unresolved.extend(problems)
        if discord.has_image(message):
            joined = _join(message, from_sheet.rolls, at)
            if joined is not None:
                found = [joined] + [f for f in found if f.skill != joined.skill]
            elif from_sheet.available:
                # An image with no recorded roll behind it is a picture, not a roll
                # (research.md R1). Silence is correct here and is NOT a dropped
                # roll - it is the detector answering "no".
                pass
            else:
                conv.unresolved.append(
                    f'image from {discord.author_name(message)} at {at:%H:%M:%S} '
                    'could not be resolved'
                )
        for roll in found:
            if not roll.attributed:
                conv.unresolved.append(
                    f'{roll.skill} {roll.total} from '
                    f'{discord.author_name(message) or "an unknown poster"} - no '
                    'character known for that Discord account'
                )
                continue
            conv.rolls.append(roll)
    return conv


def _join(
    message: Mapping[str, Any],
    candidates: Sequence[sheet.RecordedRoll],
    at: datetime,
) -> Roll | None:
    """Find the recorded roll a pasted dice card was rendered from."""
    poster = discord.author_id(message)
    near = [
        r
        for r in candidates
        if r.actor_discord_id == poster and abs((at - r.at).total_seconds()) <= MATCH_WINDOW_SECONDS
    ]
    if not near:
        return None
    best = min(near, key=lambda r: abs((at - r.at).total_seconds()))
    return Roll(
        character=best.character,
        skill=best.skill,
        total=best.total,
        source='recorded',
        message_id=str(message['id']),
        at=at,
        rank=best.rank,
    )


def end_conversation(
    *,
    rule: RecordingRule | None = None,
    get_body: Callable[[str], Mapping[str, object] | None] = op.get_character_body,
    update: Callable[..., object] = op.update_character,
    collector: Callable[..., Conversation] = collect,
) -> str:
    """Close, format, and write. No confirmation step (FR-019)."""
    global _open
    conv = _require()
    collector(conv)
    with _lock:
        _open = None
    if not conv.rolls:
        _report(conv)
        print(f'Nothing to record for {conv.npc_name}.')
        return ''

    line = rules.render_open(conv.rolls, rule or rules.DEFAULT_RULE)
    body = get_body(conv.npc_id) or {}
    current = str(body.get('bio') or '')
    update(conv.npc_id, bio=biomod.splice(current, line))
    print(f'{conv.npc_name}: {line}')
    _report(conv)
    return line


def abandon_conversation() -> None:
    """Close without writing. Not part of the normal path; nothing blocks on it."""
    global _open
    conv = _require()
    with _lock:
        _open = None
    print(f'Threw away {len(conv.rolls)} roll(s) for {conv.npc_name}. Nothing written.')


def conversation_status() -> Conversation | None:
    """What is open, and the line as it currently stands. A read, never a gate."""
    if _open is None:
        print('No conversation open.')
        return None
    print(f'Talking to {_open.npc_name} since {_open.opened_at:%H:%M:%S}.')
    if _open.rolls:
        print(f'  {rules.render_open(_open.rolls)}')
    else:
        print('  no rolls yet')
    _report(_open)
    return _open


def _report(conv: Conversation) -> None:
    for problem in conv.unresolved:
        print(f'  ! {problem}')


def _require() -> Conversation:
    if _open is None:
        raise NoConversation('no conversation open - begin_conversation("Name") first')
    return _open
