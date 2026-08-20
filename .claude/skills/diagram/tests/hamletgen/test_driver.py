"""Unit tests for the pipeline and the CLI that drives it (`hamletgen/driver.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import os
import re

from l7r.diagram import check_village
from l7r.diagram import hamletgen as hg

from ._builders import a_plan


def test_the_report_line_names_the_map_and_its_verdict() -> None:
    plan = a_plan()
    assert "OK" in hg.Report(plan=plan, failures=[]).line()
    bad = hg.Report(plan=plan, failures=["a_check", "another"])
    assert not bad.ok and "FAIL" in bad.line() and "a_check" in bad.line()


def test_a_rolled_cohort_passes_the_whole_gate() -> None:
    """The experiment's actual claim, in miniature, and a RATCHET on it.

    Hamlets rolled from seeds nobody looked at come out correct. The honest figure is still a pass
    RATE rather than a guarantee - a cohort of two dozen turns up the odd siting collision - so this
    pins the rate: a change that drops it fails here by name.

    The two things that hold WITHOUT exception, on every map whether it passes the gate or not, are
    asserted for all of them: the declared households are seated, and the paddy acreage lands on the
    figure the household count implies. Those are the derivations this module exists to get right.

    (The four demo maps in `pool/hamlets/` carry the full-size version of the gate check, in
    `tests/test_villages.py`; four members here keep the suite's runtime honest.)"""
    # SERIAL ON PURPOSE (2026-08-16), for two reasons that point the same way. An in-gate caller
    # wants `jobs=1` - a pytest worker that spawns its own pool competes with the other 21 - and
    # these four rolls are also this suite's only in-process walk of the seed-dependent generator
    # branches, because a fanned-out roll executes in a worker where this run's coverage cannot see
    # it. Leaving it on the default parallel path silently uncovered `hinterland.py`'s
    # no-house-column fringe fallback. The fan-out is a CLI win, not a gate win; the parallel branch
    # is held by `test_the_fan_out_agrees_with_the_serial_path` below.
    reports = hg.cohort(4, first_seed=41, jobs=1)
    assert len(reports) == 4
    for report in reports:
        assert report.plan.placed >= round(0.85 * report.plan.spec.households), f"{report.plan.spec.name} seated {report.plan.placed}/{report.plan.spec.households}"
        assert abs(report.plan.acres - report.plan.target_acres) / report.plan.target_acres < 0.15, (
            f"{report.plan.spec.name}: {report.plan.acres:.1f} acres against a {report.plan.target_acres:.1f} target"
        )
    # MEASURED 2026-08-12: 24 of 24 over the first two dozen seeds, and 4 of 4 here
    # (`python3 -m l7r.diagram.tools.cohort_audit --count 24` reproduces the sweep and reports any residue by check).
    # It was 7 of 12 when the experiment was first reported. Keep this at 4 of 4: a change that drops
    # a single rolled hamlet now fails here by name, which is the whole point of a ratchet.
    passed = [r for r in reports if r.ok]
    assert len(passed) >= 4, f"only {len(passed)}/4 rolled hamlets pass the whole gate: " + "; ".join(f"{r.plan.spec.name}: {r.failures}" for r in reports if not r.ok)


def test_the_cli_reports_a_single_hamlet(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    out = str(tmp_path / "cli")
    # the RETURN CODE reports the gate's verdict on this particular seed, which is not what this
    # test is about - it is about the CLI writing the artifacts and reporting the map. Asserting a
    # green gate here would pin one arbitrary seed's luck (see the cohort ratchet above for the rate).
    hg.main(["--name", "Clitest", "--seed", "8", "--households", "11", "--down-deg", "90", "--sink", "offmap", "--windward", "N", "--out", out, "--no-render"])
    assert os.path.exists(out + ".json") and os.path.exists(out + ".svg")
    assert "Clitest" in capsys.readouterr().out


def test_the_cli_batch_mode_returns_nonzero_when_a_member_fails(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    """The batch exit code is the experiment's pass/fail signal, so it has to be real."""
    monkeypatch.setattr(hg.driver, "cohort", lambda n, first_seed=1, jobs=None: [hg.Report(plan=a_plan(), failures=["boom"])])
    assert hg.main(["--batch", "1"]) == 1
    assert "0/1 passed" in capsys.readouterr().out


def test_the_cli_batch_mode_returns_zero_when_every_member_passes(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(hg.driver, "cohort", lambda n, first_seed=1, jobs=None: [hg.Report(plan=a_plan(), failures=[])])
    assert hg.main(["--batch", "1"]) == 0
    assert "1/1 passed" in capsys.readouterr().out


_PIN = {22: frozenset({"field_ringed"}), 24: frozenset({"paddy_bunds_clear_the_supply_channels"})}


def _cohort(**seeds: list[str]) -> list[hg.Report]:
    """Reports keyed `s<seed>`, each failing whatever the caller names (empty = it passed)."""
    return [hg.Report(plan=hg.plan_site(hg.HamletSpec(name="T", seed=int(s[1:]), households=12, down_deg=90.0, windward="N")), failures=f) for s, f in sorted(seeds.items())]


def test_a_cohort_matching_its_pinned_baseline_is_clean() -> None:
    """The pin is what makes `22/24 passed` mean something: the RATE is identical whether the two
    failures are the expected ones or two fresh regressions."""
    lines, clean = hg.baseline_verdict(_cohort(s21=[], s22=["field_ringed[cohort-22-paddies]"], s23=[], s24=["paddy_bunds_clear_the_supply_channels"]), _PIN)
    assert clean and "NO NEW REGRESSIONS" in lines[0]


def test_the_instance_suffix_is_not_part_of_a_check_identity() -> None:
    # `field_ringed[cohort-22-paddies]` and `field_ringed[whatever]` are the same rule; the suffix
    # carries the map's own feature ids and would make the pin unmatchable
    _, clean = hg.baseline_verdict(_cohort(s22=["field_ringed[some-other-field]"], s24=["paddy_bunds_clear_the_supply_channels"]), _PIN)
    assert clean


def test_a_failure_on_an_unpinned_seed_is_a_regression() -> None:
    lines, clean = hg.baseline_verdict(_cohort(s9=["paddy_plot_seams_shared"], s22=["field_ringed"], s24=["paddy_bunds_clear_the_supply_channels"]), _PIN)
    assert not clean
    assert any("REGRESSION seed 9" in line and "paddy_plot_seams_shared" in line for line in lines)
    assert any("Principle XIII" in line for line in lines), "the message must name the rule that blocks the merge"


def test_a_NEW_check_on_an_ALREADY_failing_seed_is_still_a_regression() -> None:
    """The subtle one: seed 22 was already failing, so the pass RATE does not move at all."""
    lines, clean = hg.baseline_verdict(_cohort(s22=["field_ringed", "paddy_plot_seams_shared"], s24=["paddy_bunds_clear_the_supply_channels"]), _PIN)
    assert not clean
    assert any("REGRESSION seed 22" in line and "paddy_plot_seams_shared" in line for line in lines)


def test_a_pinned_failure_that_starts_PASSING_fails_too_so_the_pin_ratchets_down() -> None:
    """Same discipline as `waivers_are_live`: a baseline nobody maintains stops being a baseline,
    and a pin that only ever loosens hides the next real regression on that seed."""
    lines, clean = hg.baseline_verdict(_cohort(s24=["paddy_bunds_clear_the_supply_channels"]), _PIN)
    assert not clean
    assert any("STALE PIN seed 22" in line and "COHORT_BASELINE" in line for line in lines), "it must name the edit to make"


def _as_pinned() -> list[hg.Report]:
    """Reports reproducing exactly today's `COHORT_BASELINE` - built FROM the pin, so this test
    keeps testing the WIRING rather than freezing whatever the baseline happens to be."""
    return [
        hg.Report(plan=hg.plan_site(hg.HamletSpec(name="T", seed=seed, households=12, down_deg=90.0, windward="N")), failures=sorted(checks))
        for seed, checks in sorted(hg.driver.COHORT_BASELINE.items())
    ]


def test_the_canonical_cohort_is_judged_against_the_pin_not_the_rate(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    """`--batch 24` from seed 1 exits ZERO on its known failures - the steady state is success, and
    only a change from it is a failure. Before the pin this exact run exited 1, which meant the
    signal everyone read was a rate that cannot distinguish two expected failures from two new ones."""
    monkeypatch.setattr(hg.driver, "cohort", lambda n, first_seed=1, jobs=None: _as_pinned())
    assert hg.main(["--batch", str(hg.driver.COHORT_BASELINE_SIZE)]) == 0
    assert "NO NEW REGRESSIONS" in capsys.readouterr().out


def test_the_canonical_cohort_fails_on_a_seed_the_pin_does_not_cover(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    extra = hg.Report(plan=hg.plan_site(hg.HamletSpec(name="T", seed=999, households=12, down_deg=90.0, windward="N")), failures=["something_new"])
    monkeypatch.setattr(hg.driver, "cohort", lambda n, first_seed=1, jobs=None: [*_as_pinned(), extra])
    assert hg.main(["--batch", str(hg.driver.COHORT_BASELINE_SIZE)]) == 1
    assert "REGRESSION seed 999" in capsys.readouterr().out


def test_a_non_canonical_range_says_it_has_no_pin(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    """A held-out or ad-hoc range must NOT be judged against the fitted cohort's baseline, and must
    say so rather than implying it was checked."""
    monkeypatch.setattr(hg.driver, "cohort", lambda n, first_seed=1, jobs=None: [hg.Report(plan=a_plan(), failures=[])])
    assert hg.main(["--batch", "1"]) == 0
    assert "no pinned baseline for this range" in capsys.readouterr().out


def test_the_cli_returns_nonzero_for_a_failing_single_map(monkeypatch, capsys) -> None:
    monkeypatch.setattr(hg.driver, "generate", lambda spec, out_base=None, render=True: hg.Report(plan=a_plan(), failures=["boom"]))
    assert hg.main(["--name", "X"]) == 1
    assert "boom" in capsys.readouterr().out


def test_cohort_derives_each_spec_and_can_be_forced_serial(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """`jobs=1` is the path an in-gate caller wants (a pytest worker that spawns its own pool
    competes with the other 21), and the spec derivation is the same on either path: consecutive
    seeds, zero-padded names, and the household ladder unless a count is given."""
    seen: list[hg.HamletSpec] = []

    def fake(spec, out_base=None, render=True):  # type: ignore[no-untyped-def]
        seen.append(spec)
        return hg.Report(plan=a_plan(), failures=[])

    monkeypatch.setattr(hg.driver, "generate", fake)
    assert len(hg.cohort(3, first_seed=5, jobs=1)) == 3
    assert [s.seed for s in seen] == [5, 6, 7]
    assert [s.name for s in seen] == ["Cohort-05", "Cohort-06", "Cohort-07"]
    assert [s.households for s in seen] == [10 + (n * 7) % 11 for n in (5, 6, 7)]
    seen.clear()
    hg.cohort(2, first_seed=9, households=14, jobs=1)  # an explicit count overrides the ladder
    assert [s.households for s in seen] == [14, 14]


def test_the_fan_out_agrees_with_the_serial_path() -> None:
    """The fan-out's entire safety claim, pinned: a map is a pure function of its spec, so rolling
    it in a worker must produce exactly the report rolling it here does. This is also the only test
    that walks the `ProcessPoolExecutor` branch (`jobs > 1` takes the pool path even for one map),
    which is why it rolls for real rather than stubbing `generate`.

    The method matters as much as the assertion. When the fan-out landed (2026-08-16) the parallel
    24-seed run differed from the session's serial baseline on 3 of 24 maps - which looked damning
    until the baseline turned out to predate a mid-task merge of another session's engine round.
    Re-rolling exactly those seeds serially on the SAME code reproduced the parallel verdicts.
    Diff against the same code, never against an older log."""
    (parallel,) = hg.cohort(1, first_seed=41, jobs=2)
    (serial,) = hg.cohort(1, first_seed=41, jobs=1)
    assert parallel.line() == serial.line()
    assert parallel.failures == serial.failures
    assert parallel.path is None  # a cohort member is gated, then thrown away


def test_a_map_that_strands_a_farmhouse_is_re_rolled_with_that_ground_forbidden(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """`generate` re-rolls a map whose FINISHED manifest strands a farmhouse, forbidding the ground
    those houses stood on. Three seat-time tests were built before this and all three failed, because
    whether a way can reach a steading depends on fabric that does not exist when seats are chosen;
    observing it on the finished map does not have that problem.

    The gate is the oracle at every step - the seats are read off its own FAIL line rather than
    recomputed, because a hand-rolled reach measure was tried and over-counted on five of six seeds.
    So this drives the loop by faking the ORACLE, not by faking geometry."""
    calls: list[int] = []

    def fake_gate(M, verbose=True, only=None):  # type: ignore[no-untyped-def]
        calls.append(1)
        if len(calls) == 1:  # the first roll strands two houses; the gate names them
            print("FAIL farmhouses_reach_a_way  -> 2 farmhouse(s) at [(1262, 848, 211), (1397, 890, 287)] - omission")
            return ["farmhouses_reach_a_way"]
        return []

    # PATCH THE SOURCE MODULE, not `hg.driver`: `generate` imports `gate` INSIDE the function, so
    # the name is re-fetched from `check_village` on every call and a package-level patch is
    # invisible to it.
    monkeypatch.setattr(check_village, "gate", fake_gate)
    seen: list[list[tuple[float, float]]] = []
    real_build = hg.driver.build

    def spy_build(plan, avoid=()):  # type: ignore[no-untyped-def]
        seen.append(list(avoid))
        return real_build(plan, avoid=avoid)

    monkeypatch.setattr(hg.driver, "build", spy_build)
    rep = hg.generate(hg.HamletSpec(name="Retry", seed=4, households=10), out_base=None, render=False)
    assert rep.failures == []  # the re-roll's verdict is the one reported
    assert len(seen) == 2  # one roll, then exactly one re-roll
    assert seen[0] == []  # the first roll forbids nothing
    assert (1262.0, 848.0) in seen[1]  # the re-roll forbids what the GATE named
    assert (1397.0, 890.0) in seen[1]


def test_a_re_roll_that_does_not_help_is_not_kept(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The retry is self-limiting: a re-roll is kept only if the gate's verdict is no longer than the
    one it replaces. Without that a map could be re-rolled into a WORSE state and shipped, which is
    the opposite of the point."""

    rolls: list[int] = []

    def fake_gate(M, verbose=True, only=None):  # type: ignore[no-untyped-def]
        rolls.append(1)
        print("FAIL farmhouses_reach_a_way  -> 1 farmhouse(s) at [(100, 100, 200)] - omission")
        # the RE-ROLL comes back worse than the roll it would replace
        return ["farmhouses_reach_a_way"] if len(rolls) == 1 else ["farmhouses_reach_a_way", "another_rule"]

    monkeypatch.setattr(check_village, "gate", fake_gate)
    # WITH AN OUT PATH, because rejecting a re-roll leaves THAT roll's files on disk - the keeper has
    # to be re-emitted, and it cannot be done by finishing the kept Settlement a second time (that
    # splices the water block twice and its `</g>` closes the <svg> root early; see `_roll`). So the
    # rejected-re-roll path only exists when there is somewhere to write.
    out = str(tmp_path / "nohelp")
    rep = hg.generate(hg.HamletSpec(name="NoHelp", seed=4, households=10), out_base=out, render=False)
    assert rep.failures == ["farmhouses_reach_a_way"]  # the FIRST roll's verdict is kept, not the worse one
    assert len(rolls) == 3  # roll, rejected re-roll, then the keeper re-emitted
    assert rep.fail_lines and "farmhouses_reach_a_way" in rep.fail_lines[0]
    svg = (tmp_path / "nohelp.svg").read_text()
    assert svg.count("<svg") == 1 and svg.count("</svg>") == 1  # finished exactly once...
    assert len(re.findall(r"<g[\s>]", svg)) == svg.count("</g>")  # ...so its groups balance
