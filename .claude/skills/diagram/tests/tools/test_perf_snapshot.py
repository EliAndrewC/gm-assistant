"""The perf report's two bands - the DIAGNOSE trigger and the CAP - proven to fire and to stay quiet.

Constitution XVIII: a guard ships with a test companion, and the companion proves it FIRES. This one
is worth pinning harder than most, because the guard's whole history is of noticing without acting -
it printed "diagnose before shipping" and returned 0 for its first three weeks, so feature 127 shipped
its own push before the report had been read. A test that only checked the printed text would have
passed throughout that.
"""

from __future__ import annotations

import json
import os
from typing import Any

import pytest

from l7r.diagram.tools import perf_snapshot as ps


def _snap(tmp: Any, label: str, seconds: dict[int, float], utc: str) -> None:
    rows = [{"seed": s, "seconds": v} for s, v in seconds.items()]
    total = sum(seconds.values())
    body = {
        "utc": utc,
        "label": label,
        "commit": "abc1234",
        "rows": rows,
        "total_seconds": total,
        "median_seconds": sorted(seconds.values())[len(seconds) // 2],
        "worst_seconds": max(seconds.values()),
    }
    (tmp / f"{utc}-{label}.json").write_text(json.dumps(body), encoding="utf-8")


@pytest.fixture
def logdir(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setattr(ps, "LOG_DIR", str(tmp_path))
    os.makedirs(tmp_path, exist_ok=True)
    return tmp_path


def test_the_cap_FIRES_on_an_aggregate_slowdown(logdir: Any, capsys: pytest.CaptureFixture[str]) -> None:
    """Over the cap is a REGRESSION, and the report must exit nonzero so a merge can be blocked."""
    _snap(logdir, "900-start", {1: 100.0, 2: 100.0}, "20260824T000000Z")
    _snap(logdir, "900-end", {1: 120.0, 2: 120.0}, "20260824T010000Z")
    assert ps.report("900-start") == 1
    out = capsys.readouterr().out
    assert "REGRESSION" in out
    assert "+20.0%" in out


def test_the_cap_STAYS_QUIET_when_the_aggregate_improves_even_with_a_slower_seed(logdir: Any, capsys: pytest.CaptureFixture[str]) -> None:
    """The motivating case: feature 128 reordered the stages, so the maps are genuinely different.

    One seed 31% slower, another 64% faster, total down 30%. The old rule blocked on the seed alone;
    the seed still has to be DIAGNOSED, but it no longer stops the merge."""
    _snap(logdir, "901-start", {4: 23.7, 25: 222.7, 39: 67.8, 47: 68.3}, "20260824T000000Z")
    _snap(logdir, "901-end", {4: 26.8, 25: 80.6, 39: 71.5, 47: 89.3}, "20260824T010000Z")
    assert ps.report("901-start") == 0
    out = capsys.readouterr().out
    assert "DIAGNOSE" in out, "a seed over 5% must still be called out"
    assert "REGRESSION" not in out
    assert "-29.9%" in out


def test_a_seed_inside_the_noise_band_is_not_even_mentioned(logdir: Any, capsys: pytest.CaptureFixture[str]) -> None:
    """Under 5% nothing is owed - that band is the noise of a loaded machine."""
    _snap(logdir, "902-start", {1: 100.0}, "20260824T000000Z")
    _snap(logdir, "902-end", {1: 103.0}, "20260824T010000Z")
    assert ps.report("902-start") == 0
    out = capsys.readouterr().out
    assert "DIAGNOSE" not in out
    assert "REGRESSION" not in out


def test_the_cap_is_the_number_the_GM_set() -> None:
    """Pinned so a later session cannot drift it without the test saying so out loud."""
    assert ps.TOTAL_SLOWDOWN_CAP_PCT == 10.0
