"""Feature 208: Oppose Social / Oppose Knowledge tax the NPC's later rolls by themselves."""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from l7r.repl import dice, gmrolls
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import hidden, lines, npcskills, oppose, rules, sheet
from l7r.repl.rolls.models import Conversation, Roll
from l7r.repl.rolls.parse import parse_message
from l7r.repl.rolls.skills import (
    AmbiguousSkill,
    UnknownSkill,
    load_knacks,
    load_skills,
    match_skill,
)

ann = importlib.import_module('l7r.repl.rolls.annotate')
#: Well in the past, so a roll the GM makes "now" is always after every message here.
W = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)


def roll(name: str, skill: str, total: int, *, rank: int | None = 2, minute: int = 0) -> Roll:
    return Roll(
        name,
        skill,
        total,
        'recorded',
        f'{name}{skill}{minute}',
        W + timedelta(minutes=minute),
        rank,
    )


def social(name: str, total: int, *, minute: int = 0) -> Roll:
    return roll(name, 'oppose social', total, minute=minute)


def gm(total: int, *, tagged: str = '', minute: int = 0) -> gmrolls.GmRoll:
    entry = gmrolls.record((9, 9, 9, 9, 9), 3, total, asked=(5, 3))
    entry.tagged = tagged
    entry.at = W + timedelta(minutes=minute)
    return entry


@pytest.fixture(autouse=True)
def clean(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    conv._open = None
    gmrolls.clear()
    monkeypatch.setattr(dice, 'd10', lambda reroll=True: 6)
    yield
    conv._open = None
    gmrolls.clear()


def talking(*rolls: Roll, **numbers: int) -> Conversation:
    c = Conversation(npc={'id': 'f', 'name': 'Fumitake'}, opened_at=W, channels=('c',))
    c.rolls.extend(rolls)
    c.numbers.update(numbers)
    conv._open = c
    return c


def declare(topic: str, sincerity: Any = None, *, minute: int = 0) -> None:
    lines.new_line_of_questioning(
        topic,
        sincerity,
        ask=lambda q: '',
        collector=lambda c: None,
        now=lambda: W + timedelta(minutes=minute),
    )


@pytest.fixture(scope='module')
def words() -> tuple[str, ...]:
    return load_skills()


class TestCapture:
    @pytest.mark.parametrize(
        ('text', 'expected'),
        [
            ('32 oppose social@3', ('oppose social', 32, 3)),
            ('32@3 Oppose Knowledge', ('oppose knowledge', 32, 3)),
            ('27 opp know', ('oppose knowledge', 27, None)),
            ('33 oppose  social at 2', ('oppose social', 33, 2)),
            ('**Tsuruchi Jimen**: **32** Oppose Social@3', ('oppose social', 32, 3)),
        ],
    )
    def test_the_forms_players_type(
        self, words: tuple[str, ...], text: str, expected: tuple[str, int, int | None]
    ) -> None:
        found, problems = parse_message(text, words)
        assert [(r.skill, r.total, r.rank) for r in found] == [expected]
        assert problems == []

    def test_a_bare_oppose_is_reported_never_guessed(self, words: tuple[str, ...]) -> None:
        found, problems = parse_message('32 oppose', words)
        assert found == []
        assert 'oppose knowledge, oppose social' in problems[0]

    def test_the_phrase_does_not_swallow_its_neighbors(self, words: tuple[str, ...]) -> None:
        found, _ = parse_message('30 investigation@2, 32 oppose social', words)
        assert {(r.skill, r.total) for r in found} == {('investigation', 30), ('oppose social', 32)}

    def test_two_words_that_are_not_a_knack_are_left_to_the_one_word_pass(
        self, words: tuple[str, ...]
    ) -> None:
        found, _ = parse_message('30 tact because reasons', words)
        assert [(r.skill, r.total) for r in found] == [('tact', 30)]

    def test_the_floor_and_the_rank_ceiling_still_apply(self, words: tuple[str, ...]) -> None:
        assert parse_message('5 oppose social', words)[0] == []
        found, problems = parse_message('32 oppose social@9', words)
        assert found == []
        assert 'rank 9' in problems[0]

    def test_a_vocabulary_with_no_phrases_skips_the_pass(self) -> None:
        found, _ = parse_message('32 tact', ('tact',))
        assert [(r.skill, r.total) for r in found] == [('tact', 32)]

    def test_only_the_two_oppose_knacks_joined_the_vocabulary(self) -> None:
        assert [k for k in load_knacks() if ' ' in k] == ['oppose knowledge', 'oppose social']

    def test_abbreviation_is_per_word(self) -> None:
        vocabulary = load_skills()
        assert match_skill('opp soc', vocabulary) == 'oppose social'
        with pytest.raises(AmbiguousSkill):
            match_skill('oppose', vocabulary)
        with pytest.raises(UnknownSkill):
            match_skill('opp soc extra', vocabulary)
        with pytest.raises(UnknownSkill):
            match_skill('soc opp', vocabulary)


class TestTheRulesCheck:
    def test_the_real_rules_agree_with_the_gm(self) -> None:
        assert oppose.rules_disagreement() == ''

    def test_a_missing_file_is_reported(self, tmp_path: Path) -> None:
        assert 'is missing' in oppose.rules_disagreement(tmp_path / 'absent.md')

    def test_a_disagreement_is_reported_and_names_both_sides(self, tmp_path: Path) -> None:
        """The trap the fidelity review named: the `**Ring:**` header is the OTHER ring."""
        path = tmp_path / 'knacks.md'
        path.write_text(
            '## Oppose Social\n\n**Ring:** Water\n\nrolls ... which roll with Fire.\n\n'
            '## Pontificate\n\n**Ring:** Water\n\nno target here\n'
        )
        said = oppose.rules_disagreement(path)
        assert 'oppose social taxes Air here but the rules say Fire' in said
        assert 'oppose knowledge taxes Water here but the rules say nothing' in said

    def test_begin_conversation_says_so_and_carries_on(
        self, monkeypatch: pytest.MonkeyPatch, capsys: Any
    ) -> None:
        monkeypatch.setattr(oppose, 'rules_disagreement', lambda: 'the rules moved')
        opened = conv.begin_conversation(
            'Otsuki',
            'tuesday',
            characters=lambda: [{'id': 'o', 'name': 'Otsuki'}],
            watch=False,
            get_body=lambda cid: {},
        )
        assert '! the rules moved' in capsys.readouterr().out
        assert opened.npc_name == 'Otsuki'

    def test_the_ring_of_a_skill(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert (oppose.ring_of('Tact'), oppose.ring_of('investigation')) == ('air', 'water')
        assert oppose.ring_of('basketweaving') == ''

        def gone() -> dict[str, str]:
            raise OSError('no mount')

        monkeypatch.setattr(oppose, 'skill_rings', gone)
        oppose.ring_of.cache_clear()
        try:
            assert oppose.ring_of('tact') == ''
        finally:
            oppose.ring_of.cache_clear()


class TestThePenaltyInEffect:
    def test_a_fifth_rounded_down_on_the_right_ring(self) -> None:
        c = talking(social('Jimen', 32), roll('Moriko', 'oppose knowledge', 27))
        late = W + timedelta(minutes=5)
        air, water = oppose.for_skill(c, 'tact', late), oppose.for_skill(c, 'investigation', late)
        assert air is not None
        assert water is not None
        assert (air.amount, water.amount) == (6, 5)
        assert air.describe() == '-6 oppose social (Jimen 32)'

    def test_the_highest_wins_and_they_never_stack(self) -> None:
        c = talking(social('Jimen', 32), social('Moriko', 41, minute=2))
        first = oppose.for_skill(c, 'tact', W + timedelta(minutes=1))
        second = oppose.for_skill(c, 'tact', W + timedelta(minutes=3))
        assert first is not None
        assert second is not None
        assert (first.amount, second.amount) == (6, 8)

    def test_a_lower_later_roll_changes_nothing_and_a_tie_keeps_the_first(self) -> None:
        c = talking(
            social('Jimen', 32), social('Moriko', 20, minute=1), social('Rei', 34, minute=2)
        )
        found = oppose.for_skill(c, 'tact', W + timedelta(minutes=9))
        assert found is not None
        assert found.roll.character == 'Jimen'

    def test_a_roll_made_before_it_pays_nothing(self) -> None:
        c = talking(social('Jimen', 32, minute=5))
        assert oppose.for_skill(c, 'tact', W + timedelta(minutes=4)) is None

    def test_what_does_not_count(self) -> None:
        nameless = replace(social('', 40), character='')
        c = talking(replace(social('Jimen', 32), discarded=True), nameless, social('Rei', 4))
        assert oppose.for_skill(c, 'tact', W + timedelta(minutes=1)) is None
        assert oppose.for_skill(c, 'basketweaving', W + timedelta(minutes=1)) is None

    def test_what_the_gm_is_told(self) -> None:
        jimen, moriko = social('Jimen', 32), social('Moriko', 41, minute=1)
        low, none = social('Rei', 20, minute=2), social('Rei', 4, minute=3)
        c = talking(jimen, moriko, low)
        assert oppose.effect(talking(jimen), jimen) == (
            'Fumitake takes -6 oppose social (Jimen 32) on every Air roll from here on'
        )
        assert oppose.effect(c, moriko).endswith("from here on, replacing Jimen's -6")
        assert oppose.effect(c, low) == (
            "-4 oppose social (Rei 20) changes nothing - Moriko's -8 stands"
        )
        assert oppose.effect(talking(), none) == (
            '-0 oppose social (Rei 4) is too low to cost Fumitake anything'
        )


class TestTheNpcsRolls:
    def test_a_tagged_roll_pays_it_and_echoes_the_reduced_total(self, capsys: Any) -> None:
        talking(social('Jimen', 32))
        total = dice.xky(5, 3) - npcskills.build_tags()['tact']
        assert (int(total), total.entry.total, total.entry.penalty) == (12, 12, 6)
        assert '-6 oppose social (Jimen 32): 12' in capsys.readouterr().out
        assert int(total + 5) == 17
        assert total.entry.bonus == 5

    def test_the_called_form_pays_it(self) -> None:
        talking(social('Jimen', 32))
        total = npcskills.build_tags()['tact'](5, 3, ask=lambda q: '')
        assert total is not None
        assert int(total) == 12

    def test_the_other_ring_pays_nothing(self) -> None:
        talking(social('Jimen', 32))
        total = dice.xky(5, 3) - npcskills.build_tags()['investigation']
        assert (int(total), total.entry.penalty) == (18, 0)

    def test_nothing_is_subtracted_with_no_conversation_open(self) -> None:
        total = dice.xky(5, 3) - npcskills.build_tags()['tact']
        assert int(total) == 18

    def test_a_roll_called_a_mistake_pays_nothing(self) -> None:
        talking(social('Jimen', 32), air=3, tact=2)
        total = npcskills.build_tags()['tact'](6, 3, ask=lambda q: 'm')
        assert total is not None
        assert (total.entry.mistake, total.entry.penalty, total.entry.total) == (True, 0, 18)

    def test_a_late_oppose_roll_reaches_the_rolls_made_after_it_and_no_others(self) -> None:
        before, after = gm(20, tagged='tact', minute=1), gm(22, tagged='tact', minute=3)
        water, untagged = gm(25, tagged='investigation', minute=3), gm(30, minute=3)
        stale = gm(19, tagged='tact', minute=-5)
        c = talking(social('Jimen', 32, minute=2))
        changes = oppose.settle(c, gmrolls.recent())
        assert [change.entry for change in changes] == [after]
        assert (before.total, after.total, water.total, untagged.total, stale.total) == (
            20,
            16,
            25,
            30,
            19,
        )
        assert changes[0].describe('Fumitake') == (
            'Fumitake tact 22 -> 16 (-6 oppose social, rolled 01:03:00)'
        )
        assert oppose.settle(c, gmrolls.recent()) == []
        assert '-6 oppose social' in after.describe()


class TestTheLineInProgress:
    def test_the_current_line_is_reached_back_into(self) -> None:
        c = talking()
        declare("Chizuru's death", 48, minute=1)
        jimen = conv.attach(c, roll('Tsuruchi Jimen', 'interrogation', 50, minute=2))
        c.rolls.append(jimen)
        line = c.lines[0]
        before = hidden.compare(c, line, jimen)
        c.rolls.append(social('Moriko', 45, minute=3))
        after = hidden.compare(c, line, jimen)
        assert before is not None
        assert after is not None
        assert (before.theirs, before.detected) == (58, False)
        assert (after.theirs, after.detected) == (49, True)
        assert after.describe() == (
            'Jimen 50 vs sincerity 48 (+10 not grilling, -9 oppose social): DETECTED'
        )
        assert hidden.entries(c) == (
            "- 2026-01-01 sincerity 48 (+10 not grilling, -9 oppose social) - Chizuru's death: "
            'Jimen 50@2 DETECTED',
        )

    def test_a_line_that_had_ended_is_left_alone_and_a_later_one_is_not(self) -> None:
        c = talking()
        declare('the treasury', 48, minute=1)
        declare('the escorts', 40, minute=4)
        c.rolls.append(social('Moriko', 45, minute=5))
        declare('the ledger', 44, minute=8)
        assert oppose.for_line(c, c.lines[0]) is None
        assert [oppose.for_line(c, line).amount for line in c.lines[1:]] == [9, 9]  # type: ignore[union-attr]

    def test_oppose_knowledge_never_touches_a_sincerity_roll(self) -> None:
        c = talking(roll('Moriko', 'oppose knowledge', 45, minute=2))
        declare('the treasury', 48, minute=1)
        assert oppose.for_line(c, c.lines[0]) is None

    def test_a_tagged_sincerity_roll_never_pays_twice(self) -> None:
        c = talking(social('Moriko', 45))
        sincerity = npcskills.build_tags()['sincerity'](5, 3, ask=lambda q: '')
        assert sincerity is not None
        assert int(sincerity) == 9
        declare('the treasury', sincerity, minute=1)
        mine = conv.attach(c, roll('Jimen', 'interrogation', 30, minute=2))
        found = hidden.compare(c, c.lines[0], mine)
        assert found is not None
        assert (found.sincerity, found.opposed, found.theirs) == (18, 9, 19)

    def test_the_public_line_never_learns_of_it(self) -> None:
        c = talking()
        declare('the treasury', 48, minute=1)
        c.rolls.append(conv.attach(c, roll('Jimen', 'interrogation', 50, minute=2)))
        public = rules.render_lines(c.rolls, 'Fumitake')
        c.rolls.append(social('Moriko', 45, minute=3))
        assert rules.render_lines(c.rolls, 'Fumitake') == [*public, '45 oppose social: Moriko']
        assert not any('48' in text or '-9' in text for text in rules.render_lines(c.rolls))


class TestTheRecord:
    def test_written_bare_in_sequence_and_never_asked_about(self, capsys: Any) -> None:
        c = talking(
            replace(roll('Jimen', 'law', 41), note='the arrest'),
            social('Jimen', 32, minute=1),
            replace(roll('Moriko', 'law', 27, minute=2), note='the warrant'),
        )
        assert rules.render_lines(c.rolls, 'Fumitake') == [
            '40 law: Jimen - the arrest',
            '30 oppose social: Jimen',
            '25 law: Moriko - the warrant',
        ]
        assert ann.pending(c) == []
        ann.annotate(c)
        assert 'Nothing waiting' in capsys.readouterr().out

    def test_it_has_a_mode_of_its_own(self) -> None:
        from l7r.repl.rolls import modes

        assert modes.mode_of('Oppose Social') == 'automatic'
        assert frozenset(modes.AUTOMATIC) == rules.WRITTEN_BARE == frozenset(oppose.TARGET_RINGS)


class TestCollecting:
    def collect(self, c: Conversation, *messages: dict[str, Any]) -> None:
        conv.collect(
            c,
            fetch=lambda cid, cursor, **k: list(messages),
            recorded=lambda *a, **k: sheet.SheetResult(),
            roster=lambda *a, **k: sheet.SheetResult(
                characters={'1': sheet.SheetCharacter(name='Tsuruchi Jimen', discord_id='1')}
            ),
        )

    def message(self, content: str, minute: int) -> dict[str, Any]:
        return {
            'id': f'm{minute}',
            'timestamp': f'2026-01-01T01:{minute:02d}:00+00:00',
            'author': {'id': '1'},
            'content': content,
            'attachments': [],
        }

    def test_collecting_one_prices_the_rolls_already_made_under_it(self, capsys: Any) -> None:
        c = talking()
        tact = gm(22, tagged='tact', minute=3)
        self.collect(c, self.message('32 oppose social@3', 2), self.message('30 law', 4))
        assert [(r.skill, r.total) for r in c.rolls] == [('oppose social', 32), ('law', 30)]
        assert tact.total == 16
        assert 'Fumitake tact 22 -> 16' in capsys.readouterr().out

    def test_the_watcher_says_what_it_did_and_re_runs_the_line(self, capsys: Any) -> None:
        c = talking()
        declare('the treasury', 48, minute=1)
        c.rolls.append(conv.attach(c, roll('Jimen', 'interrogation', 50, minute=2)))
        c.rolls.append(replace(roll('Rei', 'interrogation', 60, minute=2), discarded=True, line=1))
        capsys.readouterr()

        def collector(target: Conversation) -> Conversation:
            target.rolls.append(social('Moriko', 45, minute=3))
            return target

        conv._tick(c, collector=collector, get_body=lambda cid: {}, update=lambda *a, **k: None)
        out = capsys.readouterr().out
        assert 'Fumitake takes -9 oppose social (Moriko 45) on every Air roll' in out
        assert 'Jimen 50 vs sincerity 48 (+10 not grilling, -9 oppose social): DETECTED' in out
        assert 'Rei' not in out.split('DETECTED')[1].split('->')[0]

    @pytest.mark.parametrize('scene', ['no line', 'a lower roll', 'no sincerity roll'])
    def test_when_there_is_nothing_to_re_run(self, scene: str, capsys: Any) -> None:
        c = talking()
        if scene != 'no line':
            declare('the treasury', None if scene == 'no sincerity roll' else 48, minute=1)
            c.rolls.append(conv.attach(c, roll('Jimen', 'interrogation', 50, minute=2)))
        if scene == 'a lower roll':
            c.rolls.append(social('Rei', 47, minute=2))
        arrived = social('Moriko', 45, minute=3)
        c.rolls.append(arrived)
        capsys.readouterr()
        conv.announce_oppose(c, arrived)
        conv.announce_oppose(c, roll('Jimen', 'law', 30))
        assert 'vs sincerity' not in capsys.readouterr().out


class TestPairingInAnnotate:
    def run(self, c: Conversation, *answers: str) -> None:
        queue = list(answers)

        def ask(question: str) -> str:
            return queue.pop(0)

        ann.annotate(c, ask=ask, undoable=lambda q, a: (False, a(q)), mine=gmrolls.recent)

    def test_an_untagged_roll_is_priced_when_it_is_picked(self, capsys: Any) -> None:
        c = talking(social('Jimen', 32), roll('Jimen', 'manipulation', 30, minute=1))
        entry = gm(20, minute=2)
        self.run(c, '1', '', '', 'pressing him')
        assert c.rolls[1].opposed_total == 14
        assert '-6 oppose social (Jimen 32): 20 -> 14' in capsys.readouterr().out
        assert entry.penalty == 0

    def test_a_typed_total_takes_the_player_roll_s_time(self) -> None:
        c = talking(social('Jimen', 32), roll('Jimen', 'manipulation', 30, minute=1))
        self.run(c, 't', '28', '', '', 'pressing him')
        assert c.rolls[1].opposed_total == 22

    def test_the_default_of_fifteen_is_not_a_roll(self) -> None:
        c = talking(social('Jimen', 32), roll('Jimen', 'manipulation', 30, minute=1))
        self.run(c, 'f', '', '', 'pressing him')
        assert c.rolls[1].opposed_total == 15

    def test_the_full_menu_prices_an_untagged_roll_and_leaves_a_tagged_one(self) -> None:
        c = talking(
            social('Jimen', 32),
            roll('Jimen', 'tact', 30, minute=1),
            roll('Moriko', 'tact', 31, minute=2),
        )
        gm(20, minute=3)
        priced = gm(14, tagged='manipulation', minute=3)
        priced.penalty = 6
        self.run(c, '1', 'c', '1', '', '', 'deflecting', 'c', '2', '', '', 'deflecting again')
        assert (c.rolls[1].opposed_total, c.rolls[2].opposed_total) == (14, 8)
