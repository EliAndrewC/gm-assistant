"""The entities."""

from __future__ import annotations

from datetime import UTC, datetime

from l7r.repl.rolls.models import Contest, Conversation, RecordingRule, Roll

WHEN = datetime(2026, 8, 12, 1, 54, tzinfo=UTC)


def roll(name: str = 'Jimen', total: int = 38) -> Roll:
    return Roll(
        character=name, skill='etiquette', total=total, source='typed', message_id='1', at=WHEN
    )


class TestRoll:
    def test_attributed_when_a_character_is_named(self) -> None:
        assert roll().attributed

    def test_not_attributed_when_nameless_or_blank(self) -> None:
        assert not roll('').attributed
        assert not roll('   ').attributed

    def test_rank_defaults_to_unknown(self) -> None:
        assert roll().rank is None


class TestContest:
    def test_tied_when_there_is_no_winner(self) -> None:
        assert Contest(left=roll(), right=roll(), winner=None, margin=0).tied

    def test_not_tied_when_someone_won(self) -> None:
        assert not Contest(left=roll(), right=roll(), winner='Jimen', margin=10).tied


class TestRecordingRule:
    def test_defaults_carry_the_gms_rules(self) -> None:
        rule = RecordingRule()
        assert rule.increment == 5
        assert rule.caps == {'etiquette': 40}

    def test_each_instance_gets_its_own_caps(self) -> None:
        first, second = RecordingRule(), RecordingRule()
        assert first.caps is not second.caps


class TestConversation:
    def test_exposes_the_npcs_name_and_id(self) -> None:
        conv = Conversation(npc={'id': 'abc', 'name': 'Otsuki'}, opened_at=WHEN, channel_id='832')
        assert conv.npc_name == 'Otsuki'
        assert conv.npc_id == 'abc'

    def test_tolerates_a_record_missing_those_fields(self) -> None:
        conv = Conversation(npc={}, opened_at=WHEN, channel_id='832')
        assert conv.npc_name == ''
        assert conv.npc_id == ''

    def test_starts_empty(self) -> None:
        conv = Conversation(npc={}, opened_at=WHEN, channel_id='832')
        assert conv.rolls == []
        assert conv.unresolved == []
        assert conv.last_seen is None
