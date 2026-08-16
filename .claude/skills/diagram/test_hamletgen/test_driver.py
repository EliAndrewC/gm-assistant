"""Unit tests for the pipeline and the CLI that drives it (`hamletgen/driver.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import os

import hamletgen as hg

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
    `test_villages.py`; four members here keep the suite's runtime honest.)"""
    reports = hg.cohort(4, first_seed=41)
    assert len(reports) == 4
    for report in reports:
        assert report.plan.placed >= round(0.85 * report.plan.spec.households), f"{report.plan.spec.name} seated {report.plan.placed}/{report.plan.spec.households}"
        assert abs(report.plan.acres - report.plan.target_acres) / report.plan.target_acres < 0.15, (
            f"{report.plan.spec.name}: {report.plan.acres:.1f} acres against a {report.plan.target_acres:.1f} target"
        )
    # MEASURED 2026-08-12: 24 of 24 over the first two dozen seeds, and 4 of 4 here
    # (`python3 cohort_audit.py --count 24` reproduces the sweep and reports any residue by check).
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


def test_the_cli_returns_nonzero_for_a_failing_single_map(monkeypatch, capsys) -> None:
    monkeypatch.setattr(hg.driver, "generate", lambda spec, out_base=None, render=True: hg.Report(plan=a_plan(), failures=["boom"]))
    assert hg.main(["--name", "X"]) == 1
    assert "boom" in capsys.readouterr().out


def test_default_jobs_leaves_headroom_and_never_exceeds_the_cohort() -> None:
    """The fan-out courtesy rule (2026-08-16), defined once in the driver and reused by
    cohort_audit.py: never more workers than maps, never every cpu on the box."""
    assert hg.default_jobs(1) == 1
    assert hg.default_jobs(2) <= 2
    assert hg.default_jobs(10_000) == max(1, (os.cpu_count() or 2) - 2)


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


def test_the_serial_path_rolls_a_real_cohort_member() -> None:
    """`jobs=1` runs `generate` in THIS process, which is what an in-gate caller wants - and it is
    therefore also what exercises the throwaway-scratch finish a cohort member takes (`out_base`
    None). A fanned-out roll does its finishing in a worker, where this suite's coverage cannot
    see it, so the serial path is the one that has to be walked for real here."""
    (report,) = hg.cohort(1, first_seed=41, jobs=1)
    assert report.plan.spec.name == "Cohort-41"
    assert report.path is None  # a cohort member is gated, then thrown away
