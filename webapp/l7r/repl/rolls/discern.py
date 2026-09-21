"""Discern Honor inside a conversation: decide once, serve by lookup, record on use.

Feature 212. A player runs `/discern-honor` in Discord and is told their read of the
character's Honor. Three facts shape everything here:

1. The true Honor is on Obsidian Portal, which only this repository reads, while
   the slash command lives in the character-sheet app, which cannot.
2. Only the GM's `begin_conversation` knows WHO is being talked to and where the
   conversation starts and ends.
3. The GM's semantic: *"if somebody slips up and accidentally runs discern honor
   twice in the same conversation, then it will return the same result rather than
   incrementing them closer to what the actual number is"*.

So the answer for every PC with the knack is DECIDED WHEN THE CONVERSATION OPENS
(`plan`), only the told values are handed to the sheet app (`payloads`), and the
command is a lookup - it cannot give two answers because it computes nothing. The
watcher then learns who actually asked (`poll`) and writes ONLY those records
(`commit`). A value nobody asked for is forgotten, d10 and all; no player saw it.

Priced and declined (spec 212, Decision 1): the sheet bot deferring its reply while
this side resolves the request - 5-20 s of poll latency per ask, an interaction
token carried between two apps, and idempotency still to build; and the player
naming the NPC, which leaks the roster through autocomplete and leaves "the same
conversation" to be guessed from time windows.

COMMIT ON SIGHT, not at close (Decision 6): the knack's premise is that the first
answer is remembered, and a REPL that dies after a player was told a number must
not lose the fact that they were told it.

BOTH GROUPS GET THE CONVERSATION. `begin_conversation` takes one argument and
watches every channel, so it does not know which gaming group is at the table, and
the sheet app keys a conversation by group. Every group with a knack-holder is
therefore sent one (the sheet's ids must be unique across groups, hence the
`-g<group>` suffix; the Obsidian Portal marker is the bare id). The cost: a PC of
the group that is NOT playing tonight could run the command and be answered about
an NPC they have never met. Accepted - the groups play on different nights - over
asking the GM for a second argument at every open.
"""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from typing import Any

from l7r.repl import honor as honormod
from l7r.repl.rolls import sheet
from l7r.repl.rolls.models import Conversation, DiscernEntry
from l7r.repl.sheets import resolve_pc

_GROUP_SUFFIX = re.compile(r'-g\d+$')


def mint_id(now: datetime, nonce: Callable[[], str] = lambda: secrets.token_hex(2)) -> str:
    """`c-20260921-7f3a`. No spaces, commas or brackets: it sits inside the record
    line's `[...]` marker, whose pattern excludes all three."""
    return f'c-{now:%Y%m%d}-{nonce()}'


def sheet_id(conversation_id: str, group: int) -> str:
    return f'{conversation_id}-g{group}'


def base_id(sheet_conversation_id: str) -> str:
    return _GROUP_SUFFIX.sub('', sheet_conversation_id)


def given_name(name: str) -> str:
    """How the Discern Honor block names a PC: `Tsuruchi Jimen` -> `Jimen`.

    A registered PC answers for themselves. Otherwise it is the last token that is
    plain letters, because a sheet name can carry its kanji (`Tsuruchi Makoto
    鶴知誠`, measured 2026-09-21) and the naive last token would key the record on
    those."""
    known = resolve_pc(name)
    if known is not None:
        return known.given
    plain = [token for token in name.split() if token.isascii() and token.isalpha()]
    return plain[-1] if plain else name.strip()


def plan(
    holders: Sequence[sheet.KnackHolder],
    records: Mapping[str, honormod.Record],
    honor: float,
    reads: str,
    marker: str,
    roll: Callable[[], int],
    served: Mapping[int, float],
) -> dict[int, DiscernEntry]:
    """What each knack-holder is told in conversation `marker`. Pure; writes nothing.

    `served` is what the sheet app ALREADY holds for a resumed conversation, and it
    wins: a first read a player has seen must not be re-rolled because the REPL
    restarted. A record already carrying this marker was committed before the
    restart and is served exactly as it stands.
    """
    out: dict[int, DiscernEntry] = {}
    for holder in holders:
        pc = given_name(holder.name)
        stored = records.get(pc.lower())
        done = stored is not None and stored.last == marker
        die = roll() if stored is None else 0
        record = honormod.advance(
            stored, stored.pc if stored else pc, honor, holder.rank, die, reads, marker
        )
        told = served.get(holder.character_id)
        if told is not None and not done and told != record.told:
            record = replace(record, told=told, locked=told == honor)
        out[holder.character_id] = DiscernEntry(
            holder.character_id, record.pc, holder.group, record, asked=done, committed=done
        )
    return out


def payloads(conv: Conversation) -> list[dict[str, Any]]:
    """One `PUT` body per gaming group. THIS IS EVERYTHING THAT LEAVES (FR-003): the
    id, the group, an opaque NPC reference (the Obsidian Portal id - not a name),
    when it opened, and per character the told value. No true Honor, no die, no
    conversation count, no locked flag, no NPC name."""
    groups = sorted({entry.group for entry in conv.discern.values()})
    return [
        {
            'conversation_id': sheet_id(conv.conversation_id, group),
            'group': group,
            'npc_ref': conv.npc_id,
            'opened_at': conv.opened_at.isoformat(),
            'discern_honor': [
                {'character_id': entry.character_id, 'told': entry.record.told}
                for entry in conv.discern.values()
                if entry.group == group
            ],
        }
        for group in groups
    ]


def _asked(existing: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [e for e in existing.get('discern_honor') or () if e.get('asked_at')]


def open_(
    conv: Conversation,
    *,
    new: bool = False,
    get_body: Callable[[str], Mapping[str, object] | None],
    holders: Callable[[], sheet.HoldersResult] = sheet.knack_holders,
    get_conversation: Callable[[int], sheet.ConversationResult] = sheet.get_conversation,
    put: Callable[[Mapping[str, Any]], sheet.ConversationResult] = sheet.open_conversation,
    roll: Callable[[], int] = honormod.d10_flat,
    mint: Callable[[datetime], str] = mint_id,
) -> None:
    """Decide the answers and hand them to the sheet app. NEVER raises and never
    stops the conversation opening (FR-010): roll capture and the manual
    `discern_honor()` must work whatever happens here, so every failure is a line
    of output and a return."""
    body = get_body(conv.npc_id)
    if body is None:
        return
    gm_info = str(body.get('game_master_info') or '')
    honor = honormod.parse_honor(gm_info)
    if honor is None:
        print(f'  Discern Honor: {conv.npc_name} has no "Honor: X.Y" line, so it cannot answer.')
        return
    found = holders()
    if found.reason:
        print(f'  Discern Honor: {found.reason} - /discern-honor will not answer.')
        return
    if not found.holders:
        return
    served: dict[int, float] = {}
    resumed = ''
    for group in sorted({h.group for h in found.holders}):
        result = get_conversation(group)
        if result.reason:
            print(f'  Discern Honor: {result.reason} - /discern-honor will not answer.')
            return
        existing = result.conversation
        if existing is None:
            continue
        if str(existing.get('npc_ref') or '') == conv.npc_id and not new:
            # FR-011. Same NPC, never closed: the REPL died, or a close failed.
            resumed = resumed or base_id(str(existing.get('conversation_id') or ''))
            for entry in existing.get('discern_honor') or ():
                served[int(entry['character_id'])] = float(entry['told'])
            print(
                f'  Discern Honor: RESUMING the conversation opened at '
                f'{str(existing.get("opened_at") or "")[11:16]} UTC - PCs who asked keep their '
                f'answer. begin_conversation(..., new=True) starts a fresh one instead.'
            )
        elif _asked(existing):
            who = ', '.join(str(e.get('character_id')) for e in _asked(existing))
            print(
                f'  Discern Honor: replacing an unclosed conversation in which sheet '
                f'character(s) {who} had asked. Anything not yet recorded from it is lost.'
            )
    conv.conversation_id = resumed or mint(conv.opened_at)
    conv.honor = honor
    conv.discern = plan(
        found.holders,
        honormod.parse_records(gm_info),
        honor,
        honormod.perceived(gm_info),
        conv.conversation_id,
        roll,
        served,
    )
    pushed = []
    for payload in payloads(conv):
        result = put(payload)
        if result.reason:
            print(f'  Discern Honor: {result.reason} - /discern-honor will not answer.')
        else:
            pushed.append(int(payload['group']))
    conv.discern_groups = tuple(pushed)
    told = ', '.join(f'{e.pc} {e.record.told:.1f}' for e in conv.discern.values())
    print(f'  Discern Honor ({honor:.1f}): would tell {told}')


def poll(
    conv: Conversation,
    *,
    get_conversation: Callable[[int], sheet.ConversationResult] = sheet.get_conversation,
    say: Callable[[str], None] = print,
) -> None:
    """Learn which PCs have asked. An unreachable app complains ONCE."""
    for group in conv.discern_groups:
        result = get_conversation(group)
        if result.reason:
            if not conv.discern_complained:
                say(f'  ! Discern Honor: {result.reason}')
                conv.discern_complained = True
            continue
        conv.discern_complained = False
        existing = result.conversation or {}
        if existing.get('conversation_id') != sheet_id(conv.conversation_id, group):
            continue
        for row in _asked(existing):
            entry = conv.discern.get(int(row['character_id']))
            if entry is not None:
                entry.asked = True


def commit(
    conv: Conversation,
    *,
    get_body: Callable[[str], Mapping[str, object] | None],
    update: Callable[..., object],
    say: Callable[[str], None] = print,
) -> bool:
    """Write the records of PCs who asked and are not yet recorded. True if written.

    RE-READS the notes rather than trusting the copy from `open_`: the watcher's own
    debounced write and the GM's manual `discern_honor()` both rewrite this field,
    and a block rendered from a stale copy would drop their lines. Idempotent on the
    marker (FR-005): a record this conversation already advanced is left alone."""
    waiting = [e for e in conv.discern.values() if e.asked and not e.committed]
    if not waiting:
        return False
    with honormod.NOTES_LOCK:
        body = get_body(conv.npc_id)
        if body is None:
            say(f'  ! Discern Honor: could not read {conv.npc_name} to record who asked')
            return False
        gm_info = str(body.get('game_master_info') or '')
        records = honormod.parse_records(gm_info)
        fresh = []
        for entry in waiting:
            stored = records.get(entry.pc.lower())
            if stored is None or stored.last != conv.conversation_id:
                records[entry.pc.lower()] = entry.record
                fresh.append(entry)
        if fresh:
            update(conv.npc_id, game_master_info=honormod.render(gm_info, records))
    for entry in waiting:
        entry.committed = True
    for entry in fresh:
        say(f'  + {entry.pc} used Discern Honor: told {entry.record.told:.1f}')
    return bool(fresh)


def roll_back(
    conv: Conversation,
    *,
    get_body: Callable[[str], Mapping[str, object] | None],
    update: Callable[..., object],
) -> None:
    """`abandon_conversation()`: leave the NPC's block as it was before this
    conversation (FR-009), and SAY who had already been given a number - which
    character that ask should count against instead is the GM's call, not ours."""
    if not conv.conversation_id or conv.honor is None:
        return
    told = [e for e in conv.discern.values() if e.asked]
    with honormod.NOTES_LOCK:
        body = get_body(conv.npc_id)
        if body is not None:
            gm_info = str(body.get('game_master_info') or '')
            records = honormod.parse_records(gm_info)
            before = honormod.rollback(records, conv.conversation_id, conv.honor)
            if before != records:
                update(conv.npc_id, game_master_info=honormod.render(gm_info, before))
                print(f"Took this conversation's Discern Honor back off {conv.npc_name}'s record.")
        elif told:
            print(f'  ! could not read {conv.npc_name} to take Discern Honor back off the record')
    for entry in told:
        print(
            f'  {entry.pc} had already been told {entry.record.told:.1f} - '
            'credit it to the right character by hand.'
        )


def close(
    conv: Conversation,
    *,
    delete: Callable[[str], sheet.ConversationResult] = sheet.close_conversation,
) -> None:
    for group in conv.discern_groups:
        result = delete(sheet_id(conv.conversation_id, group))
        if result.reason:
            print(
                f'  ! Discern Honor: could not close the sheet conversation ({result.reason}). '
                'It stops answering 12 hours after it opened; the next begin_conversation '
                'with this character will offer to resume it.'
            )
    conv.discern_groups = ()
