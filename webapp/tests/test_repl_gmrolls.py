"""The GM's own rolls, and the int subclass that captures their bonuses."""

from __future__ import annotations

from typing import Any

import pytest

from l7r.repl import gmrolls
from l7r.repl.dice import DiceTotal, xky


@pytest.fixture(autouse=True)
def closed() -> Any:
    gmrolls.stop()
    yield
    gmrolls.stop()


class TestRecordingScope:
    def test_nothing_is_recorded_with_no_conversation(self) -> None:
        assert gmrolls.record((10, 9), 1, 10) is None
        assert gmrolls.recent() == ()
        assert not gmrolls.recording()

    def test_start_records_and_stop_forgets(self) -> None:
        gmrolls.start()
        assert gmrolls.recording()
        assert gmrolls.record((10, 9), 1, 10) is not None
        assert len(gmrolls.recent()) == 1
        gmrolls.stop()
        assert gmrolls.recent() == ()

    def test_start_clears_a_previous_conversation(self) -> None:
        gmrolls.start()
        gmrolls.record((5,), 1, 5)
        gmrolls.start()
        assert gmrolls.recent() == ()

    def test_rolls_are_numbered_in_order(self) -> None:
        gmrolls.start()
        for total in (10, 20, 30):
            gmrolls.record((total,), 1, total)
        assert [g.seq for g in gmrolls.recent()] == [1, 2, 3]


class TestDescribe:
    def test_names_the_pool_the_kept_dice_and_the_bonus(self) -> None:
        gmrolls.start()
        entry = gmrolls.record((10, 9, 8, 2, 1), 3, 27)
        assert entry is not None
        entry.bonus = 8
        shown = entry.describe()
        assert '35' in shown
        assert '5k3' in shown
        assert '+8' in shown

    def test_no_bonus_is_not_shown(self) -> None:
        gmrolls.start()
        entry = gmrolls.record((10, 9), 1, 10)
        assert entry is not None
        assert '+' not in entry.describe()


class TestXkyCapture:
    def test_a_plain_int_when_no_conversation_is_open(self) -> None:
        assert type(xky(6, 3, print_dice=False)) is int

    def test_a_recording_total_while_one_is_open(self) -> None:
        gmrolls.start()
        assert isinstance(xky(6, 3, print_dice=False), DiceTotal)

    def test_the_gms_habitual_form_captures_the_bonus(self) -> None:
        """xky(7, 4) + 8 - one roll, total includes the 8."""
        gmrolls.start()
        total = xky(7, 4, print_dice=False) + 8
        (entry,) = gmrolls.recent()
        assert entry.total == int(total)
        assert entry.bonus == 8

    def test_a_later_bonus_updates_the_same_roll(self) -> None:
        """The GM's own idea: `_ + 15` after seeing the dice."""
        gmrolls.start()
        first = xky(7, 4, print_dice=False) + 8
        second = first + 15
        assert len(gmrolls.recent()) == 1, 'ONE roll, not three'
        assert gmrolls.recent()[0].total == int(second)
        assert gmrolls.recent()[0].bonus == 23

    def test_a_penalty_is_captured_too(self) -> None:
        gmrolls.start()
        total = xky(6, 3, print_dice=False) - 5
        assert gmrolls.recent()[0].bonus == -5
        assert gmrolls.recent()[0].total == int(total)

    def test_a_plain_int_on_the_left(self) -> None:
        gmrolls.start()
        total = 8 + xky(6, 3, print_dice=False)
        assert gmrolls.recent()[0].bonus == 8
        assert gmrolls.recent()[0].total == int(total)

    def test_it_is_still_an_integer_everywhere(self) -> None:
        gmrolls.start()
        value = xky(6, 3, print_dice=False)
        assert isinstance(value, int)
        assert f'{value}' == str(int(value))
        assert sorted([value, 1])[0] == 1
        assert sum([value, 0]) == int(value)

    def test_each_roll_gets_its_own_record(self) -> None:
        gmrolls.start()
        first = xky(6, 3, print_dice=False) + 1
        second = xky(5, 2, print_dice=False) + 2
        assert len(gmrolls.recent()) == 2
        assert gmrolls.recent()[0].total == int(first)
        assert gmrolls.recent()[1].total == int(second)
