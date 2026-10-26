"""The members of a conversation with several NPCs (feature 230).

`begin_conversation('Hideki', 'Souma', 'stolen sheets')` opens one with a PRIMARY (the
first NPC named: the heading and every player roll go to their bio) and other
members, each of whom gets a link entry on their own bio. This module is everything
about the members once that has happened: their handles at the prompt (`souma`),
the link entries, `add_to_conversation` / `remove_from_conversation`, and the
join / leave marker lines `conversation.written_lines` puts in the primary's bio.
The design and its reasons are in `CLAUDE.md` beside this file (the feature 230
section) and `specs/230-multi-npc-conversations/`.

Split out of `conversation.py` on the GM's word (2026-10-26) once that module passed
1,300 lines. `conversation` imports this module, so this one reaches back into it
only inside functions - the same lazy pattern `npcskills._open` uses.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from chargen import op
from chargen.opsynth import match_character
from l7r.repl.rolls import bio as biomod
from l7r.repl.rolls import discern, npcskills, rules
from l7r.repl.rolls.models import Conversation, Event, Member


def _conversation() -> Any:
    from l7r.repl.rolls import conversation

    return conversation


#: The REPL's namespace, so a member's handle (`souma`) can be put at the prompt.
#: `shell.main` registers it; with none (tests, scripts) there are no handles there,
#: and `handle("Souma")` finds a member instead.
_namespace: dict[str, Any] | None = None


def use_namespace(ns: dict[str, Any] | None) -> None:
    global _namespace
    _namespace = ns


def _handle_name(member: Member, conv: Conversation) -> str:
    """`souma`, or `tsuruchi_souma` when `souma` is taken (feature 230, Story 3).

    Taken means: something at the prompt that is not one of this conversation's own
    handles, or another member with the same personal name. Never shadow the GM's
    names - a skill tag, a PC constant, a variable they set.
    """
    short = rules.personal_name(member.name).lower()
    full = re.sub(r'\W+', '_', ' '.join(t for t in member.name.split() if t.isascii()).lower())
    twins = [m for m in conv.members if rules.personal_name(m.name).lower() == short]
    mine = {m.handle for m in conv.members if m.handle}
    taken = _namespace is not None and short in _namespace and short not in mine
    return full if len(twins) > 1 or taken or not short.isidentifier() else short


def _install_handles(conv: Conversation) -> None:
    for member in conv.members:
        if member.handle:
            continue
        member.handle = _handle_name(member, conv)
        if _namespace is not None:
            _namespace[member.handle] = npcskills.MemberHandle(
                member.id, member.name, member.handle
            )
        short = rules.personal_name(member.name).lower()
        if member.handle != short:
            print(f'  {member.name} is `{member.handle}` at the prompt (`{short}` was taken).')


def _remove_handles(conv: Conversation) -> None:
    if _namespace is None:
        return
    for member in conv.members:
        found = _namespace.get(member.handle)
        if isinstance(found, npcskills.MemberHandle) and found.member_id == member.id:
            del _namespace[member.handle]


def handle(name: str) -> npcskills.MemberHandle:
    """The open conversation's member called `name` (whole name tokens), as a handle."""
    conv = _conversation().require_open()
    match = match_character(name, [m.npc for m in conv.members])
    if match.kind != 'unique':
        listed = ', '.join(m.name for m in conv.members)
        raise ValueError(f'{name!r} is not in this conversation ({listed}).')
    member = conv.member(str(match.character.get('id')))
    return npcskills.MemberHandle(member.id, member.name, member.handle)


def link_entry_lines(conv: Conversation) -> tuple[str, str]:
    """What a member other than the primary has written on their bio (Story 2)."""
    primary = conv.primary
    slug = str(primary.npc.get('slug') or '')
    link = f'[[:{slug}|{primary.name}]]' if slug else primary.name
    return (rules.render_heading(conv.title), f"Rolls for this conversation are on {link}'s page.")


def link_entry(
    conv: Conversation,
    member: Member,
    get_body: Callable[[str], Mapping[str, object] | None],
    update: Callable[..., object],
) -> None:
    """Write the link entry on `member`'s bio, once, when they join. Reported, never
    fatal: the conversation goes on whether or not Obsidian Portal took it."""
    try:
        body = get_body(member.id)
        if body is None:
            raise RuntimeError('could not read the record')
        bio = biomod.rewrite(str(body.get('bio') or ''), (), link_entry_lines(conv))
        update(member.id, bio=bio)
    except Exception as exc:  # noqa: BLE001 - reported; the conversation carries on
        print(f"  ! could not write the link on {member.name}'s page: {exc}")
    else:
        print(f"  {member.name}: linked to {conv.primary.name}'s page for this conversation")


def unlink(
    conv: Conversation,
    member: Member,
    get_body: Callable[[str], Mapping[str, object] | None],
    update: Callable[..., object],
) -> None:
    """Take the link entry back off `member`'s bio - `abandon_conversation()`, the
    wrong-NPC exit, undoes what the open wrote (as `discern.roll_back` does)."""
    try:
        body = get_body(member.id)
        if body is None:
            raise RuntimeError('could not read the record')
        bio = str(body.get('bio') or '')
        cleaned = biomod.remove_lines(bio, link_entry_lines(conv))
        if cleaned != bio:
            update(member.id, bio=cleaned)
    except Exception as exc:  # noqa: BLE001 - reported; abandoning carries on
        print(f"  ! could not take the link off {member.name}'s page: {exc}")


def add_to_conversation(
    *names: str,
    characters: Callable[[], Sequence[Mapping[str, object]]] = op.existing_characters,
    now: Callable[[], datetime] | None = None,
    get_body: Callable[[str], Mapping[str, object] | None] | None = None,
    update: Callable[..., object] | None = None,
    discern_open: Callable[..., None] | None = None,
) -> None:
    """NPCs join the open conversation - any number (GM 2026-10-26). All-or-nothing:
    every name is resolved before anyone is added. A departed member named again comes
    back. The join is marked in the primary's bio where it happened.

    A conversation opened with one NPC and no title must be GIVEN one here (GM
    2026-10-26: a title is required once a second NPC joins, because the newcomer's
    link entry names the topic): `add_to_conversation('Souma', 'stolen sheets')`, by
    `begin_conversation`'s rule - exactly one argument naming no character. A titled
    conversation takes none, so there every argument must name an NPC."""
    conv = _conversation().require_open()
    npcskills.settle_pending()
    if not names:
        raise TypeError('add_to_conversation("Souma") - say who joins')
    roster = characters()
    found: list[Mapping[str, object]] = []
    titles: list[str] = []
    for name in names:
        match = match_character(name, roster)
        if match.kind == 'unique':
            found.append(match.character)
        elif match.kind == 'none' and not conv.title:
            titles.append(name)
        else:
            raise ValueError(_conversation()._no_match(name, match))
    if not conv.title and (len(titles) != 1 or not found or not titles[0].strip()):
        # GM 2026-10-26: a title is REQUIRED once a second NPC joins - the link entry
        # on the newcomer's page names the conversation's topic. So an untitled
        # conversation takes it here, by `begin_conversation`'s own rule.
        which = f' (naming no character: {", ".join(repr(t) for t in titles)})' if titles else ''
        raise ValueError(
            'this conversation has no title, and one is required once a second NPC joins: '
            f"add_to_conversation('Souma', 'stolen sheets') - exactly one argument naming no "
            f'character, which becomes the title{which}.'
        )
    if titles:
        conv.title = ' '.join(titles[0].split())
        print(f'  The conversation is now titled: {conv.title}')
    _conversation()._no_repeats(found)
    clock = now or (lambda: datetime.now(UTC))
    reader = get_body or op.get_character_body
    writer = update or op.update_character
    joined: list[Member] = []
    for npc in found:
        try:
            member = conv.member(str(npc.get('id')))
        except KeyError:
            member = Member(npc)
            conv.members.append(member)
            joined.append(member)
        else:
            if member.present:
                print(f'  {member.name} is already in the conversation.')
                continue
            member.present = True
        conv.events.append(Event(member.id, 'joined', clock()))
        print(f'{member.name} joined the conversation.')
    conv.ever_multi = True
    _install_handles(conv)
    for member in joined:
        _conversation().load_numbers(conv, reader, member)
        link_entry(conv, member, reader, writer)
    (discern_open or discern.add)(conv, get_body=reader)


def remove_from_conversation(
    *names: str,
    now: Callable[[], datetime] | None = None,
    discern_leave: Callable[[Conversation], None] | None = None,
) -> None:
    """NPCs leave the open conversation - any number. Their records stay; rolling for
    them stops (`MemberLeft`). The primary leaving makes NOBODY primary: the public
    lines still go to their bio, and a roll that names no NPC raises (`PrimaryLeft`)."""
    conv = _conversation().require_open()
    npcskills.settle_pending()
    if not names:
        raise TypeError('remove_from_conversation("Souma") - say who leaves')
    leaving = [handle(name).member for name in names]
    clock = now or (lambda: datetime.now(UTC))
    for member in leaving:
        if not member.present:
            print(f'  {member.name} has already left.')
            continue
        member.present = False
        conv.events.append(Event(member.id, 'left', clock()))
        print(f'{member.name} left the conversation.')
    (discern_leave or discern.leave)(conv)


def membership_line(conv: Conversation, event: Event) -> str:
    """`Souma joined the conversation` / `Hideki left the conversation`."""
    who = rules.personal_name(conv.member(event.member).name)
    return f'{who} {event.kind} the conversation'


def _is_marker(conv: Conversation, line: str) -> bool:
    return any(line == membership_line(conv, e) for e in conv.events)
