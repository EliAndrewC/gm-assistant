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

import re
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from chargen import op
from chargen.opsynth import MatchResult, match_character
from l7r.repl import gmrolls
from l7r.repl import honor as honormod
from l7r.repl.rolls import bio as biomod
from l7r.repl.rolls import boost as boostmod
from l7r.repl.rolls import (
    console,
    discern,
    discord,
    hidden,
    npcnumbers,
    npcskills,
    oppose,
    rules,
    sheet,
)
from l7r.repl.rolls.models import Conversation, RecordingRule, Roll
from l7r.repl.rolls.parse import parse_message
from l7r.repl.rolls.skills import load_skills

#: How close in time a recorded roll must sit to the Discord message that shows it.
#: Generous on purpose: a player rolls on the sheet, looks at it, copies the image
#: and pastes it, and the observed gap runs to tens of seconds. Over-wide costs
#: nothing here because the author id already narrows the join to one person.
MATCH_WINDOW_SECONDS = 300

#: How often the background watcher polls Discord while a conversation is open.
POLL_SECONDS = 20.0

#: How long to wait before writing an updated line to Obsidian Portal. The GM asked
#: for this: they want to SEE that a roll was noticed straight away, but not a write
#: per roll - "maybe we debounce so that within 2 minutes we update with the latest
#: set of rolls". Feedback is immediate and local; the write is coalesced.
WRITE_DEBOUNCE_SECONDS = 120.0

#: The character-sheet app's own bot. A `/etiquette` slash command is posted BY THE
#: BOT, not by the player who typed it, so the message author is the bot and joining
#: on `actor_discord_id` finds nothing. Measured 2026-08-28 against a real post:
#: author `1490400739934212116`, content `**Roll Tester**: **23** Etiquette@1`. The
#: character is named in the message instead, so that is what the join uses.
SHEET_BOT_ID = '1490400739934212116'

_BOT_ROLL = re.compile(r'^\s*\*\*(?P<character>[^*]{1,60})\*\*\s*:')

#: Discord's LOADING message flag. Every sheet-bot roll is a DEFERRED interaction
#: response: an empty "thinking..." message, filled in by an edit once the dice card
#: renders. A poll landing in that window used to read the empty message, move the
#: channel's cursor past it, and never see the roll (found in feature 214). A
#: channel is now read only up to its first loading message, which the next poll
#: reads again - unless it is older than an interaction token lives, in which case
#: the edit is never coming and it is passed over.
LOADING = 1 << 7
LOADING_GIVE_UP_SECONDS = 15 * 60

_lock = threading.Lock()
#: Feature 207: `new_line_of_questioning` collects synchronously, so for the first
#: time the GM's thread and the watcher can both be inside `collect`, each advancing
#: `last_seen` and appending rolls. One lock around the collect makes that a queue.
#: Reentrant because a test's collector may itself call `collect`.
_collect_lock = threading.RLock()
_open: Conversation | None = None
_stop = threading.Event()
_watcher: threading.Thread | None = None


class NotAnnotated(RuntimeError):
    """Rolls are waiting to be annotated, so the conversation is not over.

    The GM asked for this in these terms: *"if I call the end_conversation()
    function manually, and there are unannotated rolls which have not yet been
    saved ... raise an exception and print an error message saying, hey. You need to
    Annotate these rolls before they can be saved. Otherwise, the conversation is
    not over."*

    It is NOT the pre-review gate this project forbids elsewhere. That rule is about
    asking the GM to approve generated CONTENT; this is a required INPUT that only
    they can supply, which CLAUDE.md's own rule carves out. The GM was shown the
    tension and ruled on it directly - see FR-003 in
    `specs/202-roll-annotation/spec.md`.
    """


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
    title: str | None = None,
    *,
    channel: str | None = None,
    characters: Callable[[], Sequence[Mapping[str, object]]] = op.existing_characters,
    now: Callable[[], datetime] | None = None,
    watch: bool = True,
    get_body: Callable[[str], Mapping[str, object] | None] | None = None,
    new: bool = False,
    discern_open: Callable[..., None] = discern.open_,
) -> Conversation:
    """Open a conversation with `npc`. Prints what it opened; returns it.

    The name resolves through `match_character`, exactly as `discern_honor` does:
    whole name tokens only, and an ambiguous name raises listing the candidates
    rather than picking one. Which record gets written to is not a guess we make.

    `title` is what the conversation is about - `begin_conversation("Otsuki",
    "confrontation on the Imperial road")` - and is written as an `h4.` heading over
    this conversation's lines, so the record shows where one conversation ended and
    the next began (GM 2026-09-29). Optional; with none, no heading is written.

    `channel` is OPTIONAL, KEYWORD-ONLY, and normally omitted. It was the second
    positional argument until 2026-09-29, when the GM gave that place to the title.
    With no channel, the conversation
    watches EVERY monitored channel, which is what the GM asked for: one argument,
    and a roll posted anywhere lands. Naming a channel narrows it to that one -
    useful for the scratch server, rarely otherwise. The two live game channels
    belong to groups that play on different nights, so watching both at once
    cannot mix two sessions' rolls in practice.

    `new=True` matters only after a crash or a failed close (feature 212): when the
    character-sheet app still holds an unclosed conversation with this NPC, the
    default is to RESUME it - so nobody who already used `/discern-honor` is counted
    twice - and this says "no, that one is over; this is another conversation".
    """
    global _open
    with _lock:
        if _open is not None:
            raise AlreadyOpen(
                f'already talking to {_open.npc_name}. end_conversation() to write it, '
                'or abandon_conversation() to throw it away.'
            )
        if title is not None and not title.strip():
            raise ValueError('say what the conversation is about, or leave the title out')
        match = match_character(npc, characters())
        if match.kind != 'unique':
            raise ValueError(_no_match(npc, match))
        channels = resolve_channels(channel)
        clock = now or (lambda: datetime.now(UTC))
        _open = Conversation(
            npc=match.character,
            opened_at=clock(),
            channels=channels,
            title=' '.join((title or '').split()),
        )
        where = 'every monitored channel' if channel is None else _label(channels[0])
        about = f' - {_open.title}' if _open.title else ''
        print(
            f'Talking to {_open.npc_name}{about}, watching {where}. Rolls until end_conversation().'
        )
        # Feature 208: a CHECK of the oppose knacks against the rules text. Whatever
        # it says, the penalties apply as the GM stated them - this only makes a
        # rules edit that the tool has not followed visible instead of silent.
        disagreement = oppose.rules_disagreement()
        if disagreement:
            print(f'  ! {disagreement}')
        gmrolls.start()
        opened = _open
    # Feature 207: the NPC's remembered rings and ranks, read ONCE here. The GM: *"we
    # do not need to check every time, we can assume that nothing will update this in
    # Obsidian portal besides our own repl, and I have only one repl going at a time."*
    # `get_body` resolves at CALL time, not as a default bound at import, so the test
    # suite's offline patch reaches it (research R16 is the day the other shape bit).
    load_numbers(opened, get_body or op.get_character_body)
    # Feature 212: decide what each PC with Discern Honor is told, and hand ONLY
    # those told values to the sheet app. After `load_numbers` and outside the lock
    # because it is network; never raises, and never stops the conversation opening.
    discern_open(opened, new=new, get_body=get_body or op.get_character_body)
    if watch:
        start_watching(opened)
    return opened


def load_numbers(
    conv: Conversation, get_body: Callable[[str], Mapping[str, object] | None]
) -> None:
    """Read the NPC's numbers and school off their record. Fail-soft: an unreachable
    Obsidian Portal means an empty record, and the first tagged roll fills it."""
    body = get_body(conv.npc_id) or {}
    conv.numbers = npcnumbers.parse(str(body.get('game_master_info') or ''))
    conv.numbers_written = dict(conv.numbers)
    record = {**conv.npc, **body}
    conv.schools = npcnumbers.find_schools(record, tuple(npcskills.extra_dice_table()))
    if conv.numbers:
        known = ', '.join(
            f'{name.capitalize() if name in npcnumbers.RINGS else name} {value}'
            for name, value in conv.numbers.items()
        )
        print(f'  on record for {conv.npc_name}: {known}')


def collect(
    conversation: Conversation | None = None,
    *,
    fetch: Callable[..., list[dict[str, Any]]] = discord.messages_since,
    recorded: Callable[..., sheet.SheetResult] = sheet.recorded_rolls,
    roster: Callable[..., sheet.SheetResult] = sheet.characters,
    vocabulary: tuple[str, ...] | None = None,
    ceilings: Callable[[int], sheet.Ceilings] = sheet.roll_ceilings,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Conversation:
    """Read everything posted since the last poll and fold it into the conversation."""
    conv = conversation or _require()
    words = vocabulary if vocabulary is not None else load_skills()
    messages: list[dict[str, Any]] = []
    for channel_id in conv.channels:
        try:
            page = fetch(channel_id, conv.last_seen.get(channel_id) or conv.opened_at)
        except discord.DiscordUnavailable as exc:
            note = f'{_label(channel_id)}: {exc}'
            if note not in conv.unresolved:
                conv.unresolved.append(note)
            continue
        page = settled(page, now())
        for message in page:
            message['_channel_id'] = channel_id
        messages.extend(page)
    # One channel being unreadable must not hide another's rolls, so the loop above
    # continues rather than returning - and the merged stream is re-sorted, because
    # each channel arrives in its own order.
    messages.sort(key=lambda m: discord.parse_timestamp(m['timestamp']))

    from_sheet = recorded(conv.opened_at)
    cast = roster()
    who = _players(cast)
    sheet_ids = {c.name.strip().lower(): c.sheet_id for c in cast.characters.values() if c.sheet_id}
    if not from_sheet.available:
        note = f'recorded rolls unavailable ({from_sheet.reason})'
        if note not in conv.unresolved:
            conv.unresolved.append(note)

    for message in messages:
        conv.last_seen[str(message.get('_channel_id') or '')] = str(message['id'])
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
        # Feature 214. A boost is never a roll of some skill, and a message carrying
        # one contributes no roll: `8 ishi, for Jimen's etiquette` names a skill too.
        boosted = boostmod.from_bot(message, at, bot_id=SHEET_BOT_ID)
        if boosted is None and who_posted:
            boosted = boostmod.typed(message, who_posted, at)
        if boosted is not None:
            found = []
        if discord.has_image(message):
            row = _match(
                message,
                from_sheet.rolls,
                at,
                taken=conv.joined,
                boost_only=boosted is not None,
            )
            if row is not None and row.roll_key == boostmod.ROLL_KEY:
                # A pasted sheet card of the technique, or the bot's own card - whose
                # recorded row carries the message command's target.
                if boosted is None:
                    boosted = boostmod.from_recorded(
                        row.character, row.total, row.target_message_id, message, at
                    )
                elif not boosted.target_message_id:
                    boosted.target_message_id = row.target_message_id
                found = []
            elif row is not None:
                joined = _as_roll(row, message, at)
                found = [joined] + [f for f in found if f.skill != joined.skill]
            elif boosted is not None or from_sheet.available:
                # An image with no recorded roll behind it is a picture, not a roll
                # (research.md R1). Silence is correct here and is NOT a dropped
                # roll - it is the detector answering "no". A boost already read from
                # the text needs no row: the GM's pinned test character is not recorded.
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
            sheet_id = sheet_ids.get(roll.character.strip().lower(), 0)
            conv.rolls.append(attach(conv, _held(conv, roll, sheet_id, ceilings)))
            if oppose.is_oppose(roll):
                # Feature 208. HERE rather than in `_tick`, because
                # `new_line_of_questioning` collects too and the GM's rolls must be
                # right whichever path saw the oppose roll first. Collection lags the
                # message by up to a poll, so the NPC may already have rolled under
                # this penalty without the tool knowing - `settle` prices those now.
                for change in oppose.settle(conv, gmrolls.recent()):
                    say(f'  = {change.describe(conv.npc_name)}')
        if boosted is not None:
            say(boostmod.place(conv, boosted))
            if boosted.applied_to is not None:
                after_boost(conv, boosted.applied_to)
    return conv


def settled(page: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    """`page` up to (not including) its first message still LOADING - see `LOADING`."""
    for position, message in enumerate(page):
        if not int(message.get('flags') or 0) & LOADING:
            continue
        age = (now - discord.parse_timestamp(message['timestamp'])).total_seconds()
        if age < LOADING_GIVE_UP_SECONDS:
            return page[:position]
    return page


def after_boost(conv: Conversation, index: int) -> None:
    """What a boost changes beyond its own roll (feature 214, FR-010 / FR-011), and
    what taking one back changes: an oppose roll's penalty is re-derived from the
    new total, and an interrogation roll's private comparison is re-run - the same
    calls a newly collected roll of either kind gets."""
    roll = conv.rolls[index]
    if oppose.is_oppose(roll):
        announce_oppose(conv, roll)
        for change in oppose.settle(conv, gmrolls.recent()):
            say(f'  = {change.describe(conv.npc_name)}')
    announce_comparison(conv, roll)


def cancel_boost(pc: str | None = None) -> None:
    """Take back an Isawa Ishi 3rd Dan boost that landed on the wrong roll (feature 214).

    The most recent applied boost, or the most recent one `pc` made. It is not
    thrown away: it is held again, so `annotate()` asks where it goes - or discards
    it, if it was a mistake altogether.
    """
    conv = _require()
    applied = [b for b in conv.boosts if b.applied_to is not None]
    if pc is not None:
        applied = [b for b in applied if boostmod.same_character(b.character, pc)]
    if not applied:
        who = f' by {pc}' if pc is not None else ''
        raise ValueError(f'no boost{who} has been applied in this conversation.')
    boost = max(applied, key=lambda b: b.at)
    index = boost.applied_to
    assert index is not None
    restored = boostmod.unapply(conv, boost)
    print(
        f'Took {boostmod.describe(boost)} back off {rules.personal_name(restored.character)} '
        f'{restored.skill} (now {restored.total}). annotate() will ask where it goes.'
    )
    after_boost(conv, index)


def attach(conv: Conversation, roll: Roll) -> Roll:
    """Put an interrogation roll on the line of questioning that was current when
    it was MADE (feature 207). Anything else passes through untouched.

    By MESSAGE time, not by when the poll happened to see it: the watcher runs every
    `POLL_SECONDS`, so a roll posted just before a declaration is usually collected
    just after it. A roll older than the FIRST declaration is left alone - the GM is
    asked about it (`lines.new_line_of_questioning`, or `annotate()` if it turns up
    late), because *"instead of pulling in previous interrogation rolls
    automatically ... I am prompted"*.
    """
    if not rules.is_interrogation(roll) or roll.line is not None:
        return roll
    current = [line for line in conv.lines if line.at <= roll.at]
    if not current:
        return roll
    line = current[-1]
    return replace(roll, line=line.id, note=line.description, grilling=line.grilling)


def written_lines(conv: Conversation, *, include_unannotated: bool = False) -> tuple[str, ...]:
    """Everything this conversation writes to the bio: its title's heading, then its
    lines. No lines, no heading - a conversation with nothing recorded writes nothing."""
    lines = rules.render_lines(conv.rolls, conv.npc_name, include_unannotated=include_unannotated)
    if lines and conv.title:
        lines.insert(0, rules.render_heading(conv.title))
    return tuple(lines)


def _held(
    conv: Conversation, roll: Roll, sheet_id: int, lookup: Callable[[int], sheet.Ceilings]
) -> Roll:
    """`roll` carrying its roller's sheet ceilings (Withdrawn), fetched once per sheet.

    A sheet that cannot be read is reported once and the roll is written uncapped -
    the same degradation as every other sheet-app failure here.
    """
    if not sheet_id:
        return roll
    if sheet_id not in conv.ceilings:
        found = lookup(sheet_id)
        conv.ceilings[sheet_id] = found
        if found.reason:
            conv.unresolved.append(
                f'{roll.character}: {found.reason} - sheet caps such as Withdrawn not applied'
            )
    found = conv.ceilings[sheet_id]
    skill = roll.skill.lower()
    return replace(roll, ceiling=found.always.get(skill), open_ceiling=found.open.get(skill))


def _recorded_key(roll: sheet.RecordedRoll) -> tuple[str, str, int, str]:
    return (roll.character, roll.skill, roll.total, roll.at.isoformat())


def _join(
    message: Mapping[str, Any],
    candidates: Sequence[sheet.RecordedRoll],
    at: datetime,
    *,
    taken: set[tuple[str, str, int, str]] | None = None,
) -> Roll | None:
    """Find the recorded roll a pasted dice card was rendered from, as a `Roll`."""
    row = _match(message, candidates, at, taken=taken)
    return None if row is None else _as_roll(row, message, at)


def _match(
    message: Mapping[str, Any],
    candidates: Sequence[sheet.RecordedRoll],
    at: datetime,
    *,
    taken: set[tuple[str, str, int, str]] | None = None,
    boost_only: bool = False,
) -> sheet.RecordedRoll | None:
    """Find the recorded roll a pasted dice card was rendered from.

    `taken` holds the recorded rolls already joined in this conversation; a match is
    added to it, so the same recorded roll never backs a second message. Without that,
    any picture the same player posts inside `MATCH_WINDOW_SECONDS` re-joins the roll
    and it is written twice (measured 2026-09-29 - see `Conversation.joined`).
    `boost_only` (feature 214): the message is already known to be an Isawa Ishi 3rd
    Dan boost, so only that technique's rows may back it - never the booster's own
    skill roll from a minute earlier.
    """
    poster = discord.author_id(message)
    in_window = [
        r
        for r in candidates
        if abs((at - r.at).total_seconds()) <= MATCH_WINDOW_SECONDS
        and (taken is None or _recorded_key(r) not in taken)
        and (not boost_only or r.roll_key == boostmod.ROLL_KEY)
    ]
    named = bot_roll_character(message)
    if named:
        # A slash-command roll: the bot posted it, so the author id is the bot's and
        # the player is named in the message body instead.
        near = [r for r in in_window if r.character.strip().lower() == named.strip().lower()]
    else:
        near = [r for r in in_window if r.actor_discord_id == poster]
    if not near:
        return None
    best = min(near, key=lambda r: abs((at - r.at).total_seconds()))
    if taken is not None:
        taken.add(_recorded_key(best))
    return best


def _as_roll(row: sheet.RecordedRoll, message: Mapping[str, Any], at: datetime) -> Roll:
    return Roll(
        character=row.character,
        skill=row.skill,
        total=row.total,
        source='recorded',
        message_id=str(message['id']),
        at=at,
        rank=row.rank,
    )


def _tick(
    conv: Conversation,
    *,
    collector: Callable[..., Conversation] = collect,
    get_body: Callable[[str], Mapping[str, object] | None] = op.get_character_body,
    update: Callable[..., object] = op.update_character,
    clock: Callable[[], float] = time.monotonic,
    debounce: float = WRITE_DEBOUNCE_SECONDS,
    announce: bool = True,
    include_unannotated: bool = False,
    get_conversation: Callable[[int], sheet.ConversationResult] = sheet.get_conversation,
) -> bool:
    """One poll: read new rolls, say so, and write if the debounce has elapsed.

    Returns True when Obsidian Portal was written. Split out from the loop so the
    behavior the GM cares about is testable without threads or waiting.

    The FIRST write of a conversation is immediate - `conv.written` is empty, so the
    debounce does not apply. That is deliberate: seeing the line appear once
    confirms the whole path is working, and everything after it is coalesced.
    """
    before = len(conv.rolls)
    with _collect_lock:
        collector(conv)
    # Feature 212, and ORDER MATTERS: commit who used Discern Honor BEFORE the
    # notes write below, and on its own read-modify-write. It is not debounced -
    # it happens once per PC per conversation, and a REPL that dies inside the
    # debounce window must not lose the fact that a player was told a number. The
    # notes write below then re-reads the record, so it cannot drop these lines.
    if conv.discern_groups:
        discern.poll(conv, get_conversation=get_conversation, say=say)
    discern.commit(conv, get_body=get_body, update=update, say=say)
    if announce:
        for roll in conv.rolls[before:]:
            rank = f' @{roll.rank}' if roll.rank is not None else ''
            cap = roll.ceiling
            counts = f' (counts as {cap})' if cap is not None and roll.total > cap else ''
            say(f'  + {roll.character}: {roll.skill} {roll.total}{rank}{counts}')
            announce_comparison(conv, roll)
            announce_oppose(conv, roll)
        announce_sincerity(conv)
    lines = written_lines(conv, include_unannotated=include_unannotated)
    # Feature 207: the GM-only half. It can change with no player roll at all - a
    # tagged `xky` records a rank - so it is weighed beside the bio, not under it.
    secret = hidden.entries(conv)
    bio_changed = bool(lines) and lines != conv.written
    notes_changed = conv.numbers != conv.numbers_written or secret != conv.hidden_written
    if not bio_changed and not notes_changed:
        return False
    # `debounce > 0` guards the guard: end_conversation and the exit hook pass 0.0
    # meaning "write now, whatever just happened". Without it, a written_at that is
    # ahead of the clock - a forced value in a test, or a monotonic clock that has
    # not caught up - makes the elapsed time negative and blocks the FINAL write,
    # which is the one write that must never be skipped.
    wrote_before = bool(conv.written) or conv.written_at > 0
    if wrote_before and debounce > 0 and clock() - conv.written_at < debounce:
        return False
    record = get_body(conv.npc_id) or {}
    if bio_changed:
        body = str(record.get('bio') or '')
        update(conv.npc_id, bio=biomod.rewrite(body, conv.written, lines))
        conv.written = lines
    if notes_changed:
        _write_notes(conv, update, get_body, secret)
    conv.written_at = clock()
    if announce and bio_changed:
        for line in lines:
            say(f'  -> {conv.npc_name}: {line}')
    return True


def _write_notes(
    conv: Conversation,
    update: Callable[..., object],
    get_body: Callable[[str], Mapping[str, object] | None],
    secret: tuple[str, ...],
) -> None:
    """The GM-only half of a tick's write, under the notes lock and from a FRESH read:
    the GM's thread may have recorded a Discern Honor answer in these same notes
    since the tick began (feature 212), and rendering over the older copy would
    silently delete it."""
    with honormod.NOTES_LOCK:
        record = get_body(conv.npc_id) or {}
        # AFTER the bio and on its own call: a GM-only write that fails must never
        # cost the players' record (spec 207, Story 10). The numbers are snapshotted
        # first because the GM's thread can tag a roll while this one is writing.
        numbers = dict(conv.numbers)
        notes = npcnumbers.render(str(record.get('game_master_info') or ''), numbers)
        try:
            update(conv.npc_id, game_master_info=hidden.rewrite(notes, conv.hidden_written, secret))
        except Exception as exc:  # noqa: BLE001 - reported, never fatal to the bio write
            say(f"  ! could not update {conv.npc_name}'s GM-only notes: {exc}")
        else:
            conv.numbers_written = numbers
            conv.hidden_written = secret


def announce_comparison(conv: Conversation, roll: Roll) -> None:
    """Tell the GM, privately, how an interrogation roll stands (spec 207, Story 8).

    The terminal is never screen-shared (GM 2026-09-19), so this is the one place
    the comparison may appear in the clear. ADVISORY: it never sets the public
    outcome, because the raises the GM hands out as the questioning goes are not
    known here.
    """
    for line in conv.lines:
        if line.id == roll.line and rules.is_interrogation(roll):
            found = hidden.compare(conv, line, roll)
            if found is not None:
                say(f'  = {found.describe()}')


def announce_sincerity(conv: Conversation) -> None:
    """Say, once each, where a Sincerity roll made on its own was kept.

    On the watcher's tick rather than when it is rolled: `new_line_of_questioning("x",
    sincerity())` rolls while the PREVIOUS line is current, and only by the next tick
    has the declaration claimed it - announcing at roll time would name the wrong line.
    """
    for entry, on in list(conv.sincerity_rolls):
        if entry.seq in conv.sincerity_announced or entry.mistake or entry.paired:
            continue
        conv.sincerity_announced.add(entry.seq)
        line = next((ln for ln in conv.lines if hidden.line_roll(conv, ln) is entry), None)
        if line is None:
            where = hidden.describe_extra(conv, entry, on)
            say(f'  sincerity {entry.total} kept in the GM-only notes - {where}')
            continue
        say(f'  sincerity {entry.total} kept in the GM-only notes against "{line.description}"')
        for roll in conv.rolls:
            if roll.line == line.id and roll.attributed and not roll.discarded:
                announce_comparison(conv, roll)


def announce_oppose(conv: Conversation, roll: Roll) -> None:
    """Say what an oppose roll did, and re-run the line it reached back into.

    The line of questioning in progress is the ONE retroactive case (feature 208):
    its hidden Sincerity roll is still active, so every comparison already printed
    for it is stale and is printed again - what `grilling()` does for its raises.
    """
    if not oppose.is_oppose(roll):
        return
    say(f'  = {oppose.effect(conv, roll)}')
    if not conv.lines:
        return
    line = conv.lines[-1]
    found = oppose.for_line(conv, line)
    if found is None or found.roll is not roll:
        return
    for other in conv.rolls:
        if other.line == line.id and rules.is_interrogation(other) and not other.discarded:
            compared = hidden.compare(conv, line, other)
            if compared is not None:
                say(f'  = {compared.describe()}')


def cancel_oppose(pc: str | None = None, knack: str | None = None) -> None:
    """A player's oppose roll was a MISTAKE - a typo, a roll meant for someone else.

    Every other player roll is discarded from the `annotate()` menu, and an oppose
    roll never reaches that menu, so a mistyped `52 oppose social` would tax every
    Air roll for the rest of the scene. The GM, shown that gap (2026-09-19): *"if we
    had some kind of cancel_* functions for stuff like that it would be good."*

    NEVER A GUESS about which roll: with no name it cancels the one PC who has any,
    and with no knack it cancels the one knack that PC has rolled; otherwise it
    lists what is standing. A PC may hold a good Oppose Knowledge beside a mistyped
    Oppose Social, and a canceled roll cannot be put back - it came from a Discord
    post, not from this prompt. (The first version canceled everything the PC had;
    the fidelity review caught that it would destroy the good roll with the bad.)
    REPEAT rolls of the SAME knack do all go: highest-wins makes the second the
    correction of the first. The roll is not written, the GM's tagged rolls are
    re-priced, and the current line is re-run.
    """
    conv = _require()
    standing = [(i, r) for i, r in enumerate(conv.rolls) if oppose.is_oppose(r) and not r.discarded]
    names = sorted({rules.personal_name(r.character) for _, r in standing})
    if pc is None:
        if len(names) != 1:
            raise ValueError(f'whose oppose roll? Standing: {", ".join(names) or "nobody"}.')
        pc = names[0]
    wanted = pc.strip().lower()
    theirs = [
        (index, roll)
        for index, roll in standing
        if wanted in (roll.character.strip().lower(), rules.personal_name(roll.character).lower())
    ]
    if not theirs:
        raise ValueError(f'{pc} has no oppose roll. Standing: {", ".join(names) or "nobody"}.')
    knacks = sorted({roll.skill.lower() for _, roll in theirs})
    if knack is not None:
        word = knack.strip().lower()
        knacks = [k for k in knacks if word and (k == word or k.split()[-1].startswith(word))]
    if len(knacks) != 1:
        have = ', '.join(sorted({roll.skill.lower() for _, roll in theirs}))
        raise ValueError(f"which of {pc}'s oppose rolls? They have: {have}.")
    for index, gone in theirs:
        if gone.skill.lower() == knacks[0]:
            conv.rolls[index] = replace(gone, discarded=True)
            print(f'Canceled {rules.personal_name(gone.character)} {gone.skill} {gone.total}.')
    for change in oppose.settle(conv, gmrolls.recent()):
        print(f'  = {change.describe(conv.npc_name)}')
    for line in conv.lines[-1:]:
        for other in conv.rolls:
            if other.line == line.id and rules.is_interrogation(other) and not other.discarded:
                compared = hidden.compare(conv, line, other)
                if compared is not None:
                    print(f'  = {compared.describe()}')


def start_watching(conv: Conversation, *, interval: float = POLL_SECONDS, **kwargs: Any) -> None:
    """Poll in the background, following `shell.py`'s warm-cache daemon pattern.

    A daemon thread so it never keeps the REPL alive, and every exception is caught
    and printed: a watcher that dies silently is worse than one that complains,
    because the GM would go on playing while nothing was being recorded.
    """
    global _watcher
    _stop.clear()

    def loop() -> None:
        while not _stop.wait(interval):
            if _open is not conv:
                return
            try:
                _tick(conv, **kwargs)
            except Exception as exc:  # noqa: BLE001 - a dead watcher must not be silent
                say(f'  ! watching {conv.npc_name}: {exc}')

    _watcher = threading.Thread(target=loop, name='l7r-roll-watch', daemon=True)
    _watcher.start()


def stop_watching(timeout: float = 2.0) -> None:
    """Signal the watcher and wait briefly for it to notice."""
    global _watcher
    _stop.set()
    if _watcher is not None and _watcher.is_alive():
        _watcher.join(timeout=timeout)
    _watcher = None


def bot_roll_character(message: Mapping[str, Any]) -> str:
    """The character named in a roll the character-sheet bot posted, if any.

    Returns '' for anything else, including a human's message that happens to start
    with bold text - the author must be the sheet bot for this to mean anything.
    """
    author: Mapping[str, Any] = message.get('author') or {}
    if str(author.get('id') or '') != SHEET_BOT_ID:
        return ''
    found = _BOT_ROLL.match(str(message.get('content') or ''))
    return found.group('character').strip() if found else ''


def end_conversation(
    *,
    force: bool = False,
    rule: RecordingRule | None = None,
    get_body: Callable[[str], Mapping[str, object] | None] = op.get_character_body,
    update: Callable[..., object] = op.update_character,
    collector: Callable[..., Conversation] = collect,
    get_conversation: Callable[[int], sheet.ConversationResult] = sheet.get_conversation,
    close_sheet: Callable[[str], sheet.ConversationResult] = sheet.close_conversation,
) -> str:
    """Close, format, and write. No confirmation step (FR-019)."""
    global _open
    conv = _require()
    waiting = [
        roll
        for roll in conv.rolls
        if roll.attributed and (rules.needs_annotation(roll) or hidden.awaiting_outcome(conv, roll))
    ]
    held = boostmod.held(conv)
    if held and not force:
        listing = '\n'.join(f'  - {boostmod.describe(b)}: {b.held_because}' for b in held)
        raise NotAnnotated(
            f'{len(held)} Isawa Ishi 3rd Dan boost(s) are not on a roll yet:\n{listing}\n'
            'Run annotate() to say which roll each one boosts, or to discard it. '
            'The conversation is still open.'
        )
    if held and force:
        for b in held:
            say(f'Dropping {boostmod.describe(b)} - it never found its roll ({b.held_because}).')
    if waiting and not force:
        listing = '\n'.join(f'  - {roll.character} {roll.skill} {roll.total}' for roll in waiting)
        raise NotAnnotated(
            f'{len(waiting)} roll(s) still need annotating before they can be saved:\n'
            f'{listing}\n'
            'Run annotate() to say what they were for. The conversation is still open.'
            + (
                '\nAn interrogation roll joins a line of questioning: '
                'new_line_of_questioning("...") declares one.'
                if any(rules.is_interrogation(r) and r.line is None for r in waiting)
                else ''
            )
            + (
                '\nAn interrogation roll that beat the Sincerity roll needs what they '
                'detected (Enter keeps "nothing hidden detected").'
                if any(r.line is not None for r in waiting if rules.is_interrogation(r))
                else ''
            )
        )
    if waiting and force:
        say(f'Saving {len(waiting)} unannotated roll(s) - better recorded bare than lost.')
    stop_watching()
    gmrolls.stop()
    # debounce=0: the final write always happens, however recently the watcher wrote.
    _tick(
        conv,
        collector=collector,
        get_body=get_body,
        update=update,
        debounce=0.0,
        announce=False,
        include_unannotated=force,
        get_conversation=get_conversation,
    )
    # Feature 212: that tick made the last poll and recorded whoever asked; what is
    # left is to stop the sheet app answering. Unasked values are simply dropped.
    discern.close(conv, delete=close_sheet)
    with _lock:
        _open = None
    if not conv.rolls:
        _report(conv)
        print(f'Nothing to record for {conv.npc_name}.')
        return ''
    for line in conv.written:
        print(f'{conv.npc_name}: {line}')
    _report(conv)
    return '\n'.join(conv.written)


def abandon_conversation(
    *,
    get_body: Callable[[str], Mapping[str, object] | None] | None = None,
    update: Callable[..., object] | None = None,
    get_conversation: Callable[[int], sheet.ConversationResult] = sheet.get_conversation,
    close_sheet: Callable[[str], sheet.ConversationResult] = sheet.close_conversation,
) -> None:
    """Close without writing. Not part of the normal path; nothing blocks on it.

    Feature 212 gives it one thing to UNDO. A PC who used `/discern-honor` was
    recorded the moment the watcher saw it, and this is the wrong-NPC exit - so that
    record comes back off (`discern.roll_back`), after one last poll to learn who
    asked, and the GM is told who had already been given a number. The boundaries
    resolve at call time so the test suite's offline patches reach them.
    """
    global _open
    conv = _require()
    stop_watching()
    gmrolls.stop()
    if conv.discern_groups:
        discern.poll(conv, get_conversation=get_conversation)
    discern.roll_back(
        conv,
        get_body=get_body or op.get_character_body,
        update=update or op.update_character,
    )
    discern.close(conv, delete=close_sheet)
    with _lock:
        _open = None
    print(f'Threw away {len(conv.rolls)} roll(s) for {conv.npc_name}. Nothing written.')


def close_open_conversation(**kwargs: Any) -> str:
    """Write out an open conversation on the way down. Never raises.

    Registered with `atexit` by the REPL, because quitting with one open loses
    real work and it is not obvious that it does. `end_conversation` performs two
    things the watcher never gets to: a FINAL collect, catching rolls posted since
    the last poll, and a write with the debounce DISABLED, flushing everything
    collected since the last write. Without this hook, quitting inside the debounce
    window silently discards up to `WRITE_DEBOUNCE_SECONDS` of rolls plus up to
    `POLL_SECONDS` of uncollected ones - and they live only in memory, so nothing
    recovers them.

    Exceptions are swallowed deliberately: an interpreter on its way out must not
    be held up or made to fail by Obsidian Portal being unreachable. Losing the
    write is bad; hanging the GM's terminal on exit is worse.

    `kwargs` forward to `end_conversation`, which exists so this is testable at all:
    that function takes its boundaries as default arguments bound at import (the
    project's injectable-boundary convention), and a wrapper taking none of its own
    would leave nothing to inject. `atexit` calls it with no arguments and gets the
    real ones - see research.md R16 for the day this shape bit silently.
    """
    if _open is None:
        return ''
    name = _open.npc_name
    print(f'Closing the conversation with {name} before exit.')
    try:
        kwargs.setdefault('force', True)
        return end_conversation(**kwargs)
    except Exception as exc:  # noqa: BLE001 - exiting must not fail
        print(f'  ! could not write the last rolls for {name}: {exc}')
        return ''


def current() -> Conversation | None:
    """The open conversation, or None. For callers that must not print."""
    return _open


def conversation_status() -> Conversation | None:
    """What is open, and the line as it currently stands. A read, never a gate."""
    if _open is None:
        print('No conversation open.')
        return None
    print(f'Talking to {_open.npc_name} since {_open.opened_at:%H:%M:%S}.')
    if _open.rolls:
        for line in written_lines(_open):
            print(f'  {line}')
    else:
        print('  no rolls yet')
    _report(_open)
    return _open


def say(text: str) -> None:
    """Print from the watcher thread without disturbing the prompt.

    Everything the WATCHER emits goes through here; everything the GM triggers
    directly (begin/end/status) uses plain `print`, because there is no prompt to
    preserve while their own call is running.
    """
    console.print_above(text)


def resolve_channels(channel: str | None) -> tuple[str, ...]:
    """Which channels a conversation watches.

    `None` means every monitored channel - the normal case, and the reason
    `begin_conversation("Otsuki")` takes one argument. A name resolves through
    `CHANNELS`; anything else is taken as a raw channel id.
    """
    if channel is None:
        return tuple(discord.CHANNELS.values())
    named = discord.CHANNELS.get(channel.lower())
    if named:
        return (named,)
    if not channel.strip():
        raise ValueError(
            f'name a channel: one of {", ".join(sorted(discord.CHANNELS))}, or a channel id'
        )
    return (channel,)


def _label(channel_id: str) -> str:
    """A channel id as its friendly name where we have one."""
    for name, known in discord.CHANNELS.items():
        if known == channel_id:
            return f'#{name}'
    return f'channel {channel_id}'


def _report(conv: Conversation) -> None:
    for problem in conv.unresolved:
        print(f'  ! {problem}')


def require_open() -> Conversation:
    """The open conversation, or an error saying how to open one."""
    return _require()


def _require() -> Conversation:
    if _open is None:
        raise NoConversation('no conversation open - begin_conversation("Name") first')
    return _open
