"""Feature 230: a conversation with several NPCs."""

from __future__ import annotations

import importlib
import json
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from l7r.repl import dice, gmrolls, honor
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import discern, hidden, npcskills, oppose, sheet, voidspent
from l7r.repl.rolls.models import Conversation, Member, Roll

ann = importlib.import_module('l7r.repl.rolls.annotate')
W = datetime(2026, 10, 26, 1, 0, tzinfo=UTC)
TAGS = npcskills.build_tags()
tact, sincerity = TAGS['tact'], TAGS['sincerity']

ROSTER = [
    {
        'id': 'h',
        'name': 'Tsuruchi Hideki',
        'slug': 'tsuruchi-hideki',
        'character_url': 'https://op/tsuruchi-hideki',
    },
    {
        'id': 's',
        'name': 'Tsuruchi Souma',
        'slug': 'tsuruchi-souma',
        'character_url': 'https://op/tsuruchi-souma',
    },
    {
        'id': 'k',
        'name': 'Hida Kenji',
        'slug': 'hida-kenji',
        'character_url': 'https://op/hida-kenji',
    },
    {
        'id': 'k2',
        'name': 'Isawa Kenji',
        'slug': 'isawa-kenji',
        'character_url': 'https://op/isawa-kenji',
    },
]


class Portal:
    """Obsidian Portal as three callables, with every write kept."""

    def __init__(self) -> None:
        self.bodies: dict[str, dict[str, str]] = {
            c['id']: {'bio': '[[File:1 | x.png]]\n', 'game_master_info': ''} for c in ROSTER
        }
        self.writes: list[tuple[str, dict[str, Any]]] = []

    def get_body(self, cid: str) -> dict[str, str]:
        return dict(self.bodies[cid])

    def update(self, cid: str, **fields: Any) -> None:
        self.writes.append((cid, fields))
        self.bodies[cid].update(fields)


@pytest.fixture(autouse=True)
def clean(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    conv._open = None
    gmrolls.clear()
    npcskills._pending.clear()
    monkeypatch.setattr(dice, 'd10', lambda reroll=True: 5)
    yield
    conv._open = None
    gmrolls.clear()
    npcskills._pending.clear()
    conv.use_namespace(None)


@pytest.fixture
def portal() -> Portal:
    return Portal()


def begin(portal: Portal, *args: str, ns: dict[str, Any] | None = None) -> Conversation:
    conv.use_namespace(ns)
    return conv.begin_conversation(
        *args,
        characters=lambda: ROSTER,
        now=lambda: W,
        watch=False,
        get_body=portal.get_body,
        update=portal.update,
        discern_open=lambda *a, **k: None,
    )


# --- Story 1: the arguments -------------------------------------------------------------


class TestArguments:
    def test_one_argument_is_the_npc(self, portal: Portal) -> None:
        c = begin(portal, 'Hideki')
        assert c.npc_name == 'Tsuruchi Hideki'
        assert c.title == ''
        assert [m.name for m in c.members] == ['Tsuruchi Hideki']

    def test_the_title_is_the_one_argument_that_names_nobody(self, portal: Portal) -> None:
        c = begin(portal, 'Hideki', 'Souma', 'stolen sheets')
        assert c.title == 'stolen sheets'
        assert [m.name for m in c.members] == ['Tsuruchi Hideki', 'Tsuruchi Souma']
        assert c.npc_name == 'Tsuruchi Hideki'

    def test_the_title_may_sit_anywhere(self, portal: Portal) -> None:
        c = begin(portal, 'stolen sheets', 'Souma', 'Hideki')
        assert c.title == 'stolen sheets'
        assert c.npc_name == 'Tsuruchi Souma'

    def test_the_old_two_argument_form_still_works(self, portal: Portal) -> None:
        c = begin(portal, 'Hideki', 'confrontation on the Imperial road')
        assert c.title == 'confrontation on the Imperial road'
        assert len(c.members) == 1

    def test_two_npcs_and_no_title_is_an_error(self, portal: Portal) -> None:
        with pytest.raises(ValueError, match='exactly one argument must name no character'):
            begin(portal, 'Hideki', 'Souma')

    def test_two_titles_is_an_error(self, portal: Portal) -> None:
        with pytest.raises(ValueError, match="'stolen sheets', 'tea'"):
            begin(portal, 'Hideki', 'stolen sheets', 'tea')

    def test_an_ambiguous_name_lists_the_candidates(self, portal: Portal) -> None:
        with pytest.raises(ValueError, match='Hida Kenji, Isawa Kenji'):
            begin(portal, 'Hideki', 'Kenji', 'tea')

    def test_the_same_npc_twice_is_an_error(self, portal: Portal) -> None:
        with pytest.raises(ValueError, match='twice'):
            begin(portal, 'Hideki', 'Tsuruchi Hideki', 'tea')

    def test_no_arguments_is_an_error(self, portal: Portal) -> None:
        with pytest.raises(TypeError):
            begin(portal)


# --- Story 3: whose roll ----------------------------------------------------------------


def two(portal: Portal, ns: dict[str, Any] | None = None) -> Conversation:
    return begin(portal, 'Hideki', 'Souma', 'stolen sheets', ns=ns)


def numbers(c: Conversation) -> dict[str, dict[str, int]]:
    return {m.handle: dict(m.numbers) for m in c.members}


class TestHandles:
    def test_handles_go_into_the_namespace_and_come_out(self, portal: Portal) -> None:
        ns: dict[str, Any] = {'tact': tact}
        two(portal, ns)
        assert {'hideki', 'souma'} <= set(ns)
        assert repr(ns['souma']).startswith('<Tsuruchi Souma')
        conv.end_conversation(
            get_body=portal.get_body,
            update=portal.update,
            collector=lambda c: c,
            get_conversation=lambda g: None,  # type: ignore[arg-type,return-value]
            close_sheet=lambda i: None,  # type: ignore[arg-type,return-value]
        )
        assert 'hideki' not in ns
        assert 'souma' not in ns

    def test_a_taken_name_gets_the_full_name(
        self, portal: Portal, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ns: dict[str, Any] = {'souma': 'something of the GM s'}
        two(portal, ns)
        assert ns['souma'] == 'something of the GM s'
        assert ns['tsuruchi_souma'].member_id == conv.handle('Souma').member_id == 's'
        assert 'tsuruchi_souma' in capsys.readouterr().out

    def test_npc_finds_a_member_by_any_name_token(self, portal: Portal) -> None:
        two(portal)
        assert conv.handle('Souma').member.id == 's'
        assert conv.handle('Tsuruchi Souma').member.id == 's'
        with pytest.raises(ValueError, match='not in this conversation'):
            conv.handle('Kenji')


class TestWhoseRoll:
    def test_the_bare_called_form_is_the_primary(self, portal: Portal) -> None:
        c = two(portal)
        tact(2, ask=lambda q: '3')
        assert numbers(c) == {'hideki': {'tact': 2, 'air': 3}, 'souma': {}}

    def test_a_handle_rolls_for_its_member(self, portal: Portal) -> None:
        c = two(portal)
        conv.handle('souma').tact(2, ask=lambda q: '3')
        assert numbers(c) == {'hideki': {}, 'souma': {'tact': 2, 'air': 3}}

    def test_a_bare_tag_waits_for_the_statement_to_end(self, portal: Portal) -> None:
        c = two(portal)
        dice.xky(5, 3) - tact
        assert numbers(c) == {'hideki': {}, 'souma': {}}
        npcskills.settle_pending()
        assert numbers(c) == {'hideki': {'air': 3, 'tact': 2}, 'souma': {}}

    @pytest.mark.parametrize('order', ['tag first', 'npc first', 'bound'])
    def test_every_order_lands_on_souma_alone(self, portal: Portal, order: str) -> None:
        c = two(portal)
        souma = conv.handle('souma')
        if order == 'tag first':
            total = dice.xky(5, 3) - tact - souma
        elif order == 'npc first':
            total = dice.xky(5, 3) - souma - tact
        else:
            total = dice.xky(5, 3) - souma.tact
        npcskills.settle_pending()
        assert numbers(c) == {'hideki': {}, 'souma': {'air': 3, 'tact': 2}}
        assert total.entry.npc == 's'
        assert total.entry.tagged == 'tact'

    def test_the_two_orders_are_the_same_in_every_effect(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = []
        for order in ('tag first', 'npc first'):
            conv._open = None
            gmrolls.clear()
            c = two(Portal())
            c.member('s').numbers.update({'air': 2, 'tact': 2})  # a disagreement to be asked
            souma = conv.handle('souma')
            asked: list[str] = []

            def answer(question: str, asked: list[str] = asked) -> str:
                asked.append(question)
                return 'r'

            monkeypatch.setattr(ann, 'ask_quietly', answer)
            capsys.readouterr()
            if order == 'tag first':
                total = dice.xky(5, 3) - tact - souma
            else:
                total = dice.xky(5, 3) - souma - tact
            npcskills.settle_pending()
            seen.append((numbers(c), asked, int(total), capsys.readouterr().out))
        assert seen[0] == seen[1]
        assert seen[0][0]['souma'] == {'air': 3, 'tact': 2}  # the record was corrected
        assert seen[0][1]  # and the GM was asked, once per order

    def test_a_roll_marked_for_one_member_cannot_be_marked_for_another(
        self, portal: Portal
    ) -> None:
        two(portal)
        total = dice.xky(5, 3) - conv.handle('souma')
        with pytest.raises(ValueError, match='already Tsuruchi Souma'):
            total - conv.handle('hideki')

    def test_an_untagged_roll_can_belong_to_a_member(self, portal: Portal) -> None:
        two(portal)
        total = dice.xky(5, 3) - conv.handle('souma')
        assert total.entry.npc == 's'
        assert total.entry.tagged == ''

    def test_a_one_member_conversation_settles_at_once(self, portal: Portal) -> None:
        c = begin(portal, 'Hideki')
        dice.xky(5, 3) - tact
        assert c.numbers == {'air': 3, 'tact': 2}
        assert not npcskills._pending


# --- Story 4: joining and leaving -------------------------------------------------------


def roll(who: str, skill: str, total: int, minute: int, note: str = '') -> Roll:
    return Roll(
        character=who,
        skill=skill,
        total=total,
        source='typed',
        message_id=f'{who}{minute}',
        at=W + timedelta(minutes=minute),
        note=note,
    )


class TestMembership:
    def test_add_and_remove_take_any_number(self, portal: Portal) -> None:
        c = begin(portal, 'Hideki', 'tea')
        conv.add_to_conversation(
            'Souma',
            'Hida Kenji',
            characters=lambda: ROSTER,
            now=lambda: W,
            get_body=portal.get_body,
            update=portal.update,
        )
        assert [m.handle for m in c.members] == ['hideki', 'souma', 'kenji']
        conv.remove_from_conversation('Souma', 'Kenji', now=lambda: W)
        assert [m.present for m in c.members] == [True, False, False]

    def test_adding_is_all_or_nothing(self, portal: Portal) -> None:
        c = begin(portal, 'Hideki', 'tea')
        with pytest.raises(ValueError, match='Nobody'):
            conv.add_to_conversation(
                'Souma',
                'Nobody',
                characters=lambda: ROSTER,
                get_body=portal.get_body,
                update=portal.update,
            )
        assert len(c.members) == 1

    def test_the_markers_sit_where_it_happened(self, portal: Portal) -> None:
        c = begin(portal, 'Hideki', 'tea')
        c.rolls.append(roll('Tsuruchi Jimen', 'etiquette', 25, 1))
        conv.add_to_conversation(
            'Souma',
            characters=lambda: ROSTER,
            now=lambda: W + timedelta(minutes=2),
            get_body=portal.get_body,
            update=portal.update,
        )
        c.rolls.append(roll('Tsuruchi Makoto', 'etiquette', 31, 3))
        conv.remove_from_conversation('Hideki', now=lambda: W + timedelta(minutes=4))
        c.rolls.append(roll('Tsuruchi Jimen', 'law', 40, 5, note='the arrest'))
        assert conv.written_lines(c) == (
            'h4. Tea',
            'Jimen etiquette: 25',
            'Souma joined the conversation',
            'Makoto etiquette: 30',
            'Hideki left the conversation',
            '40 law: Jimen - the arrest',
        )

    def test_a_member_gets_a_link_entry_at_once(self, portal: Portal) -> None:
        two(portal)
        souma_bio = portal.bodies['s']['bio']
        assert 'h4. Stolen sheets' in souma_bio
        assert (
            "Rolls for this conversation are on [[:tsuruchi-hideki|Tsuruchi Hideki]]'s page."
            in souma_bio
        )
        assert portal.bodies['h']['bio'] == '[[File:1 | x.png]]\n'

    def test_the_primary_leaving_stops_the_defaults(self, portal: Portal) -> None:
        c = two(portal)
        conv.remove_from_conversation('Hideki', now=lambda: W)
        with pytest.raises(npcskills.PrimaryLeft, match='souma.tact'):
            tact(2)
        dice.xky(5, 3) - tact
        with pytest.raises(npcskills.PrimaryLeft):
            npcskills.settle_pending()
        assert numbers(c) == {'hideki': {}, 'souma': {}}
        conv.handle('souma').tact(2, ask=lambda q: '3')
        assert numbers(c)['souma'] == {'tact': 2, 'air': 3}

    def test_a_departed_member_cannot_roll(self, portal: Portal) -> None:
        two(portal)
        conv.remove_from_conversation('Souma', now=lambda: W)
        with pytest.raises(npcskills.MemberLeft, match='left the conversation'):
            conv.handle('souma').tact(2)

    def test_a_departed_handle_still_marks_an_earlier_roll(self, portal: Portal) -> None:
        c = two(portal)
        earlier = dice.xky(5, 3)
        conv.remove_from_conversation('Souma', now=lambda: datetime.now(UTC) + timedelta(hours=1))
        npcskills.tags_by_name()['tact'].tag_roll(earlier)  # waits: the statement goes on
        earlier - conv.handle('souma')
        assert earlier.entry.npc == 's'
        assert numbers(c)['souma'] == {'air': 3, 'tact': 2}

    def test_a_departed_handle_cannot_mark_a_later_roll(self, portal: Portal) -> None:
        two(portal)
        conv.remove_from_conversation('Souma', now=lambda: datetime.now(UTC) - timedelta(hours=1))
        with pytest.raises(npcskills.MemberLeft, match='not in the conversation'):
            dice.xky(5, 3) - conv.handle('souma')
        with pytest.raises(npcskills.MemberLeft):
            dice.xky(5, 3) - conv.handle('souma').tact

    def test_adding_to_an_untitled_conversation_waits_for_the_gm(self, portal: Portal) -> None:
        c = begin(portal, 'Hideki')
        with pytest.raises(ValueError, match='no title'):
            conv.add_to_conversation(
                'Souma', characters=lambda: ROSTER, get_body=portal.get_body, update=portal.update
            )
        assert len(c.members) == 1

    def test_a_line_of_questioning_splits_at_a_marker(self, portal: Portal) -> None:
        c = begin(portal, 'Hideki', 'tea')
        first = roll('Tsuruchi Jimen', 'interrogation', 30, 1)
        later = roll('Tsuruchi Makoto', 'interrogation', 25, 3)
        from dataclasses import replace

        c.rolls += [
            replace(first, line=1, note='the sheets'),
            replace(later, line=1, note='the sheets'),
        ]
        conv.add_to_conversation(
            'Souma',
            characters=lambda: ROSTER,
            now=lambda: W + timedelta(minutes=2),
            get_body=portal.get_body,
            update=portal.update,
        )
        lines = conv.written_lines(c)
        assert lines.index('Souma joined the conversation') == 2
        assert lines[1].startswith('interrogation: 30 Jimen - the sheets')
        assert lines[3].startswith('interrogation: 25 Makoto - the sheets')


# --- Story 2: per-member notes ----------------------------------------------------------


class TestNotes:
    def test_each_member_keeps_its_own_numbers_and_void(self, portal: Portal) -> None:
        c = two(portal)
        conv.handle('souma').tact(2, npcskills.vp, ask=lambda q: '3')
        tact(1, ask=lambda q: '2')
        conv._tick(
            c,
            collector=lambda x: x,
            get_body=portal.get_body,
            update=portal.update,
            announce=False,
            get_conversation=lambda g: sheet.ConversationResult(),
        )
        souma = portal.bodies['s']['game_master_info']
        hideki = portal.bodies['h']['game_master_info']
        assert '- tact 2' in souma
        assert voidspent.HEADING in souma
        assert '- tact 1' in hideki
        assert voidspent.HEADING not in hideki


# --- Story 5: oppose --------------------------------------------------------------------


class TestOppose:
    def test_an_oppose_roll_taxes_the_primary_only_until_moved(self, portal: Portal) -> None:
        c = two(portal)
        c.rolls.append(
            Roll(
                character='Tsuruchi Jimen',
                skill='oppose social',
                total=30,
                source='typed',
                message_id='o',
                at=W,
                against='h',  # what `collect` sets: the primary
            )
        )
        hideki = tact(2, ask=lambda q: '3')
        souma = conv.handle('souma').tact(2, ask=lambda q: '3')
        assert hideki is not None
        assert souma is not None
        assert hideki.entry.penalty == 6
        assert souma.entry.penalty == 0
        conv.move_oppose(conv.handle('souma'))
        assert hideki.entry.penalty == 0
        assert souma.entry.penalty == 6


# --- Story 6: Discern Honor covers every member -----------------------------------------


class MiniSheet:
    """character-sheet#6's conversation store, as much of it as these tests need."""

    def __init__(self) -> None:
        self.open: dict[int, dict[str, Any]] = {}
        self.puts: list[dict[str, Any]] = []

    def get(self, group: int) -> sheet.ConversationResult:
        return sheet.ConversationResult(conversation=self.open.get(group))

    def put(self, body: Mapping[str, Any]) -> sheet.ConversationResult:
        self.puts.append(json.loads(json.dumps(body)))
        old = {n['npc_ref']: n for n in (self.open.get(int(body['group'])) or {}).get('npcs', [])}
        npcs = []
        for npc in body['npcs']:
            entries = [dict(e, asked_at=None) for e in npc['discern_honor']]
            kept = {
                e['character_id']: e for e in old.get(npc['npc_ref'], {}).get('discern_honor', [])
            }
            npcs.append({**npc, 'discern_honor': [kept.get(e['character_id'], e) for e in entries]})
        self.open[int(body['group'])] = {**body, 'npcs': npcs}
        return sheet.ConversationResult(conversation=self.open[int(body['group'])])

    def ask(self, npc_ref: str) -> None:
        for npc in self.open[2]['npcs']:
            if npc['npc_ref'] == npc_ref:
                npc['discern_honor'][0]['asked_at'] = '2026-10-26T01:05:00Z'


JIMEN = sheet.HoldersResult(holders=(sheet.KnackHolder(3, 'Tsuruchi Jimen', 2, 4),))


def with_discern(portal: Portal, app: MiniSheet, *args: str) -> Conversation:
    for cid, honor_value in (('h', '3.0'), ('s', '5.0'), ('k', '2.0')):
        portal.bodies[cid]['game_master_info'] = f'Honor: {honor_value}\n'

    def opener(opened: Conversation, **kwargs: Any) -> None:
        discern.open_(
            opened,
            holders=lambda: JIMEN,
            get_conversation=app.get,
            put=app.put,
            roll=lambda: 5,
            mint=lambda now: 'c-20261026-aaaa',
            **kwargs,
        )

    return conv.begin_conversation(
        *args,
        characters=lambda: ROSTER,
        now=lambda: W,
        watch=False,
        get_body=portal.get_body,
        update=portal.update,
        discern_open=opener,
    )


def tick(c: Conversation, portal: Portal, app: MiniSheet) -> None:
    conv._tick(
        c,
        collector=lambda x: x,
        get_body=portal.get_body,
        update=portal.update,
        announce=False,
        get_conversation=app.get,
    )


class TestDiscern:
    def test_every_member_is_planned_and_an_ask_lands_on_its_member(self, portal: Portal) -> None:
        app = MiniSheet()
        c = with_discern(portal, app, 'Hideki', 'Souma', 'tea')
        sent = app.puts[-1]['npcs']
        assert [(n['npc_ref'], n['name'], n['present']) for n in sent] == [
            ('h', 'Hideki', True),
            ('s', 'Souma', True),
        ]
        app.ask('s')
        tick(c, portal, app)
        assert '- Jimen (rank 4): told 5.0' in portal.bodies['s']['game_master_info']
        assert 'Jimen (rank' not in portal.bodies['h']['game_master_info']

    def test_joining_plans_and_leaving_tells_the_sheet(self, portal: Portal) -> None:
        app = MiniSheet()
        c = with_discern(portal, app, 'Hideki', 'tea')
        conv.add_to_conversation(
            'Souma',
            characters=lambda: ROSTER,
            get_body=portal.get_body,
            update=portal.update,
            discern_open=lambda opened, **k: discern.add(opened, put=app.put, roll=lambda: 5, **k),
        )
        assert [n['name'] for n in app.puts[-1]['npcs']] == ['Hideki', 'Souma']
        app.ask('s')
        conv.remove_from_conversation(
            'Souma', discern_leave=lambda opened: discern.leave(opened, put=app.put)
        )
        assert [n['present'] for n in app.puts[-1]['npcs']] == [True, False]
        tick(c, portal, app)  # an ask made before Souma left is still recorded
        assert '- Jimen (rank 4): told 5.0' in portal.bodies['s']['game_master_info']

    def test_the_manual_call_answers_for_any_member(self, portal: Portal) -> None:
        app = MiniSheet()
        c = with_discern(portal, app, 'Hideki', 'Souma', 'tea')
        told = honor.discern_honor(
            'Souma',
            'Tsuruchi Jimen',
            rank=4,
            characters=lambda: ROSTER,
            get_body=portal.get_body,
            update=portal.update,
            conversation=lambda: c,
        )
        assert told == c.planned('Jimen', 's')

    def test_two_present_members_with_one_name_are_sent_in_full(self) -> None:
        c = Conversation(npc={'id': 'a', 'name': 'Hida Kenji'}, opened_at=W, channels=())
        c.members.append(Member({'id': 'b', 'name': 'Isawa Kenji'}))
        assert discern._names(c) == {'a': 'Hida Kenji', 'b': 'Isawa Kenji'}
        c.members[1].present = False
        assert discern._names(c) == {'a': 'Kenji', 'b': 'Kenji'}


# --- the edges ---------------------------------------------------------------------------


class TestEdges:
    def test_two_members_with_one_personal_name_get_full_handles(self, portal: Portal) -> None:
        c = begin(portal, 'Hida Kenji', 'Isawa Kenji', 'tea', ns={})
        assert [m.handle for m in c.members] == ['hida_kenji', 'isawa_kenji']

    def test_a_failed_link_entry_is_reported_and_the_conversation_opens(
        self, portal: Portal, capsys: pytest.CaptureFixture[str]
    ) -> None:
        def broken(cid: str, **fields: Any) -> None:
            raise RuntimeError('portal down')

        conv.use_namespace(None)
        c = conv.begin_conversation(
            'Hideki',
            'Souma',
            'tea',
            characters=lambda: ROSTER,
            now=lambda: W,
            watch=False,
            get_body=lambda cid: None if cid == 's' else portal.get_body(cid),
            update=broken,
            discern_open=lambda *a, **k: None,
        )
        assert len(c.members) == 2
        assert "could not write the link on Tsuruchi Souma's page" in capsys.readouterr().out

    def test_rejoining_and_repeats_are_said_not_doubled(
        self, portal: Portal, capsys: pytest.CaptureFixture[str]
    ) -> None:
        c = two(portal)
        add = {'characters': lambda: ROSTER, 'get_body': portal.get_body, 'update': portal.update}
        conv.add_to_conversation('Souma', **add)  # type: ignore[arg-type]
        assert 'already in the conversation' in capsys.readouterr().out
        conv.remove_from_conversation('Souma', now=lambda: W)
        conv.remove_from_conversation('Souma', now=lambda: W)
        assert 'has already left' in capsys.readouterr().out
        conv.add_to_conversation('Souma', now=lambda: W, **add)  # type: ignore[arg-type]
        assert c.member('s').present
        assert [e.kind for e in c.events] == ['left', 'joined']
        with pytest.raises(TypeError):
            conv.add_to_conversation()
        with pytest.raises(TypeError):
            conv.remove_from_conversation()

    def test_markers_alone_write_nothing(self, portal: Portal) -> None:
        c = two(portal)
        conv.remove_from_conversation('Souma', now=lambda: W)
        assert conv.written_lines(c) == ()

    def test_nobody_left_at_all(self, portal: Portal) -> None:
        two(portal)
        conv.remove_from_conversation('Hideki', 'Souma', now=lambda: W)
        with pytest.raises(npcskills.PrimaryLeft, match='nobody is left'):
            tact(2)

    def test_a_handle_outside_a_conversation_and_its_errors(self, portal: Portal) -> None:
        two(portal)
        souma = conv.handle('souma')
        with pytest.raises(AttributeError, match='no skill'):
            souma.flying  # noqa: B018
        with pytest.raises(TypeError, match='only a roll'):
            5 - souma
        conv._open = None
        with pytest.raises(RuntimeError, match='no conversation'):
            souma.member  # noqa: B018

    def test_settling_with_nothing_open_forgets(self, portal: Portal) -> None:
        two(portal)
        dice.xky(5, 3) - tact
        conv._open = None
        npcskills.settle_pending()
        assert not npcskills._pending

    def test_abandoning_forgets_and_removes_handles(self, portal: Portal) -> None:
        ns: dict[str, Any] = {}
        two(portal, ns)
        dice.xky(5, 3) - tact
        conv.abandon_conversation(
            get_body=portal.get_body,
            update=portal.update,
            get_conversation=lambda g: sheet.ConversationResult(),
            close_sheet=lambda i: sheet.ConversationResult(),
        )
        assert not npcskills._pending
        assert 'souma' not in ns

    def test_the_exit_path_writes_even_when_the_primary_left(
        self, portal: Portal, capsys: pytest.CaptureFixture[str]
    ) -> None:
        two(portal)
        conv.remove_from_conversation('Hideki', now=lambda: W)
        dice.xky(5, 3) - tact
        conv.end_conversation(
            force=True,
            get_body=portal.get_body,
            update=portal.update,
            collector=lambda c: c,
            get_conversation=lambda g: sheet.ConversationResult(),
            close_sheet=lambda i: sheet.ConversationResult(),
        )
        assert 'has left the conversation' in capsys.readouterr().out
        assert conv._open is None


class TestOpposeTargets:
    def test_collecting_aims_at_the_primary_or_nobody(self, portal: Portal) -> None:
        c = two(portal)
        message = {
            'id': '1',
            'timestamp': '2026-10-26T01:01:00+00:00',
            'content': '30 oppose social',
            'author': {'id': 'p1', 'username': 'jimen'},
        }

        def collect() -> None:
            conv.collect(
                c,
                fetch=lambda channel, since: [dict(message, id=str(len(c.rolls) + 1))],
                recorded=lambda since: sheet.SheetResult(),
                roster=lambda: sheet.SheetResult(
                    characters={'p1': sheet.SheetCharacter('Tsuruchi Jimen', 'p1')}
                ),
                vocabulary=('oppose social',),
            )

        collect()
        assert c.rolls[-1].against == 'h'
        conv.remove_from_conversation('Hideki', now=lambda: W)
        collect()
        assert c.rolls[-1].against == '-'

    def test_moving_by_name_and_the_nobody_message(self, portal: Portal) -> None:
        c = two(portal)
        jimen = Roll(
            character='Tsuruchi Jimen',
            skill='oppose social',
            total=30,
            source='typed',
            message_id='o',
            at=W,
            against='-',
        )
        c.rolls.append(jimen)
        assert 'taxes nobody yet' in oppose.effect(c, jimen)
        conv.move_oppose('Souma')
        assert c.rolls[-1].against == 's'
        assert oppose.effect(c, c.rolls[-1]).startswith('Tsuruchi Souma takes')


class TestMemberAnnotate:
    def test_a_paired_roll_names_its_member(
        self, portal: Portal, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        c = two(portal)
        conv.handle('souma').tact(2, ask=lambda q: '3')
        c.rolls.append(roll('Tsuruchi Jimen', 'manipulation', 30, 1))
        replies = iter(['the debt', ''])
        ann.annotate(c, ask=lambda q: next(replies), undoable=lambda q, a: (False, a(q)))
        assert c.rolls[-1].npc == 'Tsuruchi Souma'
        assert any('Jimen vs Souma' in line for line in conv.written_lines(c))

    def test_with_the_primary_gone_a_typed_total_asks_whose(self, portal: Portal) -> None:
        c = two(portal)
        conv.remove_from_conversation('Hideki', now=lambda: W)
        c.rolls.append(roll('Tsuruchi Jimen', 'manipulation', 30, 1))
        asked: list[str] = []
        replies = iter(['t', '1', '7', '0', '0', 'the debt'])

        def ask(question: str) -> str:
            asked.append(question)
            return next(replies)

        ann.annotate(c, ask=ask, mine=lambda: (), undoable=lambda q, a: (False, a(q)))
        assert any('Which NPC?' in q for q in asked)
        assert c.rolls[-1].npc == 'Tsuruchi Souma'


class TestCoverageEdges:
    def test_the_member_question_with_nobody_or_a_bad_answer(self, portal: Portal) -> None:
        c = two(portal)
        conv.remove_from_conversation('Hideki', now=lambda: W)
        replies = iter(['9', '1'])
        menu = ann._Menu(
            ask=lambda q: next(replies),
            undoable=lambda q, a: (False, a(q)),
            conv=c,
            mine=[],
            used=set(),
        )
        assert ann._which_member(menu).id == 's'
        conv.remove_from_conversation('Souma', now=lambda: W)
        with pytest.raises(ValueError, match='nobody is left'):
            ann._which_member(menu)

    def test_closing_by_hand_with_the_primary_gone_refuses(self, portal: Portal) -> None:
        two(portal)
        conv.remove_from_conversation('Hideki', now=lambda: W)
        dice.xky(5, 3) - tact
        with pytest.raises(npcskills.PrimaryLeft):
            conv.end_conversation(
                get_body=portal.get_body,
                update=portal.update,
                collector=lambda c: c,
                get_conversation=lambda g: sheet.ConversationResult(),
                close_sheet=lambda i: sheet.ConversationResult(),
            )

    def test_a_members_own_sincerity_roll_stays_off_the_primarys_notes(
        self, portal: Portal
    ) -> None:
        c = two(portal)
        conv.handle('souma').sincerity(3, ask=lambda q: '2')
        assert hidden.entries(c, c.member('h')) == ()
        assert len(hidden.entries(c, c.member('s'))) == 1

    def test_the_primary_delegation_and_a_stale_owner(self) -> None:
        c = Conversation(npc={'id': 'a', 'name': 'A'}, opened_at=W, channels=())
        c.hidden_written = ('x',)
        c.void_written = ('y',)
        c.discern = {}
        c.honor = 3.0
        assert (c.primary.hidden_written, c.void_written, c.honor) == (('x',), ('y',), 3.0)
        stale = gmrolls.record((5,), 1, 5)
        stale.npc = 'from-another-conversation'
        assert c.owner(stale) is c.primary


class TestAdvisorFixes:
    def test_abandoning_takes_the_link_entries_back_off(self, portal: Portal) -> None:
        two(portal)
        assert 'Stolen sheets' in portal.bodies['s']['bio']
        conv.abandon_conversation(
            get_body=portal.get_body,
            update=portal.update,
            get_conversation=lambda g: sheet.ConversationResult(),
            close_sheet=lambda i: sheet.ConversationResult(),
        )
        bio = portal.bodies['s']['bio']
        assert 'Stolen sheets' not in bio
        assert 'Rolls for this conversation' not in bio
        # `bio.insert` spliced a blank line ABOVE the block too; one blank line under the
        # portrait is what remains, and Textile renders it as nothing.
        assert bio.strip() == '[[File:1 | x.png]]'

    def test_an_unreadable_record_on_abandon_is_reported(
        self, portal: Portal, capsys: pytest.CaptureFixture[str]
    ) -> None:
        two(portal)
        conv.abandon_conversation(
            get_body=lambda cid: None,
            update=portal.update,
            get_conversation=lambda g: sheet.ConversationResult(),
            close_sheet=lambda i: sheet.ConversationResult(),
        )
        assert "could not take the link off Tsuruchi Souma's page" in capsys.readouterr().out
