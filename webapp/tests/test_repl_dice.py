"""Exact XkY odds and the dice functions of the GM REPL (l7r.repl.dice)."""

import random
from collections.abc import Iterator

import pytest

from l7r.repl.dice import Dist, actual_xky, d10, dist, initiative, percent, prob, survival, xky


def _fixed(monkeypatch: pytest.MonkeyPatch, rolls: list[int]) -> None:
    seq: Iterator[int] = iter(rolls)
    monkeypatch.setattr(random, 'randint', lambda a, b: next(seq))


class TestRolls:
    def test_d10_flat_is_1_to_10(self) -> None:
        rolls = {d10(reroll=False) for _ in range(500)}
        assert rolls <= set(range(1, 11))

    def test_d10_explodes_on_ten(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _fixed(monkeypatch, [10, 10, 3])
        assert d10() == 23

    def test_xky_prints_sorted_dice_and_keeps_the_best(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _fixed(monkeypatch, [4, 9, 1])
        assert xky(3, 2, reroll=False) == 13
        assert capsys.readouterr().out == '[1, 4, 9]\n'

    def test_xky_can_be_silent(self, capsys: pytest.CaptureFixture[str]) -> None:
        xky(3, 2, print_dice=False)
        assert capsys.readouterr().out == ''

    def test_initiative_is_lowest_kept_ascending(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _fixed(monkeypatch, [7, 2, 9])
        assert initiative(3, 2) == [2, 7]

    def test_percent_range(self) -> None:
        assert 1 <= percent() <= 100


class TestOverflow:
    def test_plain(self) -> None:
        assert actual_xky(6, 3) == (6, 3, 0)

    def test_rolled_past_ten_become_kept(self) -> None:
        assert actual_xky(12, 4) == (10, 6, 0)

    def test_kept_past_ten_become_bonus(self) -> None:
        assert actual_xky(13, 9) == (10, 10, 2)

    def test_keep_clamped_to_roll(self) -> None:
        assert actual_xky(2, 5) == (2, 2, 0)


class TestSurvival:
    def test_flat(self) -> None:
        assert survival(1, False) == 1.0
        assert survival(6, False) == 0.5
        assert survival(11, False) == 0.0

    def test_exploding(self) -> None:
        assert survival(10) == pytest.approx(0.1)
        assert survival(11) == pytest.approx(0.1)
        assert survival(12) == pytest.approx(0.09)
        assert survival(20) == pytest.approx(0.01)


class TestDist:
    def test_flat_single_die(self) -> None:
        d = dist(1, 1, reroll=False)
        assert d.mean == pytest.approx(5.5)
        assert d.at_least(6) == pytest.approx(0.5)
        assert d.exactly(3) == pytest.approx(0.1)
        assert d.exactly(11) == 0.0

    def test_exploding_single_die_mean_is_55_over_9(self) -> None:
        assert dist(1, 1).mean == pytest.approx(55 / 9, abs=1e-9)

    def test_best_of_two_flat(self) -> None:
        assert dist(2, 1, reroll=False).mean == pytest.approx(7.15)

    def test_keep_all_is_sum(self) -> None:
        assert dist(3, 3, reroll=False).mean == pytest.approx(16.5)

    def test_overflow_bonus_shifts_the_distribution(self) -> None:
        assert dist(12, 10).mean == pytest.approx(dist(10, 10).mean + 2)

    def test_mass_sums_to_one(self) -> None:
        assert sum(dist(10, 5).pmf.values()) == pytest.approx(1.0, abs=1e-9)

    def test_matches_a_seeded_monte_carlo(self) -> None:
        rng = random.Random(7)
        n = 20000
        total = 0
        for _ in range(n):
            dice_ = sorted(rng.randint(1, 10) for _ in range(6))
            total += sum(dice_[-3:])
        assert dist(6, 3, reroll=False).mean == pytest.approx(total / n, abs=0.15)

    def test_percentile_and_table(self) -> None:
        d = dist(6, 3, reroll=False)
        assert d.percentile(0.0) == min(d.pmf)
        text = d.table(step=10)
        assert text.startswith('6k3 (no reroll)  mean ')
        assert 'TN  10' in text
        e = dist(2, 1)
        assert e.table(upto=5) == f'2k1  mean {e.mean:.2f}\n  TN   5  {e.at_least(5):6.1%}'

    def test_number_like(self) -> None:
        d = dist(1, 1, reroll=False)
        assert float(d) == 5.5
        assert repr(d) == '5.50'
        assert f'{d:.1f}' == '5.5'
        assert d > 5
        assert d >= 5.5
        assert d < 6
        assert d <= 5.5
        assert d >= dist(1, 1, reroll=False)
        assert d.__lt__('x') is NotImplemented

    def test_dist_object_direct(self) -> None:
        d = Dist(1, 1, True, {2: 0.5, 1: 0.5})
        assert list(d.pmf) == [1, 2]


class TestProb:
    def test_call_forms(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert prob(6, 3) is dist(6, 3, True)
        assert prob(6, 3, 15) == pytest.approx(dist(6, 3).at_least(15))
        prob(1, 1, table=True, reroll=False)
        assert '1k1 (no reroll)' in capsys.readouterr().out

    def test_old_indexing(self) -> None:
        d = prob[False][1, 1]
        assert isinstance(d, Dist)
        assert d.mean == 5.5
        assert prob[False][1, 1, 6] == pytest.approx(0.5)
        assert prob[True][6, 3] is dist(6, 3, True)
