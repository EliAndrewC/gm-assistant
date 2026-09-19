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
from l7r.repl.rolls import bio as biomod
from l7r.repl.rolls import console, discord, hidden, npcnumbers, npcskills, oppose, rules, sheet
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
    channel: str | None = None,
    *,
    characters: Callable[[], Sequence[Mapping[str, object]]] = op.existing_characters,
    now: Callable[[], datetime] | None = None,
    watch: bool = True,
    get_body: Callable[[str], Mapping[str, object] | None] | None = None,
) -> Conversation:
    """Open a conversation with `npc`. Prints what it opened; returns it.

    The name resolves through `match_character`, exactly as `discern_honor` does:
    whole name tokens only, and an ambiguous name raises listing the candidates
    rather than picking one. Which record gets written to is not a guess we make.

    `channel` is OPTIONAL and normally omitted. With no channel, the conversation
    watches EVERY monitored channel, which is what the GM asked for: one argument,
    and a roll posted anywhere lands. Naming a channel narrows it to that one -
    useful for the scratch server, rarely otherwise. The two live game channels
    belong to groups that play on different nights, so watching both at once
    cannot mix two sessions' rolls in practice.
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
        channels = resolve_channels(channel)
        clock = now or (lambda: datetime.now(UTC))
        _open = Conversation(npc=match.character, opened_at=clock(), channels=channels)
        where = 'every monitored channel' if channel is None else _label(channels[0])
        print(f'Talking to {_open.npc_name}, watching {where}. Rolls until end_conversation().')
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
        for message in page:
            message['_channel_id'] = channel_id
        messages.extend(page)
    # One channel being unreadable must not hide another's rolls, so the loop above
    # continues rather than returning - and the merged stream is re-sorted, because
    # each channel arrives in its own order.
    messages.sort(key=lambda m: discord.parse_timestamp(m['timestamp']))

    from_sheet = recorded(conv.opened_at)
    who = _players(roster())
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
            conv.rolls.append(attach(conv, roll))
            if oppose.is_oppose(roll):
                # Feature 208. HERE rather than in `_tick`, because
                # `new_line_of_questioning` collects too and the GM's rolls must be
                # right whichever path saw the oppose roll first. Collection lags the
                # message by up to a poll, so the NPC may already have rolled under
                # this penalty without the tool knowing - `settle` prices those now.
                for change in oppose.settle(conv, gmrolls.recent()):
                    say(f'  = {change.describe(conv.npc_name)}')
    return conv


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


def _join(
    message: Mapping[str, Any],
    candidates: Sequence[sheet.RecordedRoll],
    at: datetime,
) -> Roll | None:
    """Find the recorded roll a pasted dice card was rendered from."""
    poster = discord.author_id(message)
    in_window = [r for r in candidates if abs((at - r.at).total_seconds()) <= MATCH_WINDOW_SECONDS]
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
    return Roll(
        character=best.character,
        skill=best.skill,
        total=best.total,
        source='recorded',
        message_id=str(message['id']),
        at=at,
        rank=best.rank,
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
    if announce:
        for roll in conv.rolls[before:]:
            rank = f' @{roll.rank}' if roll.rank is not None else ''
            say(f'  + {roll.character}: {roll.skill} {roll.total}{rank}')
            announce_comparison(conv, roll)
            announce_oppose(conv, roll)
    lines = tuple(
        rules.render_lines(conv.rolls, conv.npc_name, include_unannotated=include_unannotated)
    )
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
    conv.written_at = clock()
    if announce and bio_changed:
        for line in lines:
            say(f'  -> {conv.npc_name}: {line}')
    return True


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
) -> str:
    """Close, format, and write. No confirmation step (FR-019)."""
    global _open
    conv = _require()
    waiting = [roll for roll in conv.rolls if rules.needs_annotation(roll) and roll.attributed]
    if waiting and not force:
        listing = '\n'.join(f'  - {roll.character} {roll.skill} {roll.total}' for roll in waiting)
        raise NotAnnotated(
            f'{len(waiting)} roll(s) still need annotating before they can be saved:\n'
            f'{listing}\n'
            'Run annotate() to say what they were for. The conversation is still open.'
            + (
                '\nAn interrogation roll joins a line of questioning: '
                'new_line_of_questioning("...") declares one.'
                if any(rules.is_interrogation(roll) for roll in waiting)
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
    )
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


def abandon_conversation() -> None:
    """Close without writing. Not part of the normal path; nothing blocks on it."""
    global _open
    conv = _require()
    stop_watching()
    gmrolls.stop()
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


def conversation_status() -> Conversation | None:
    """What is open, and the line as it currently stands. A read, never a gate."""
    if _open is None:
        print('No conversation open.')
        return None
    print(f'Talking to {_open.npc_name} since {_open.opened_at:%H:%M:%S}.')
    if _open.rolls:
        for line in rules.render_lines(_open.rolls, _open.npc_name):
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
