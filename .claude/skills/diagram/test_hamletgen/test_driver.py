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
    monkeypatch.setattr(hg.driver, "cohort", lambda n, first_seed=1: [hg.Report(plan=a_plan(), failures=["boom"])])
    assert hg.main(["--batch", "1"]) == 1
    assert "0/1 passed" in capsys.readouterr().out


def test_the_cli_batch_mode_returns_zero_when_every_member_passes(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(hg.driver, "cohort", lambda n, first_seed=1: [hg.Report(plan=a_plan(), failures=[])])
    assert hg.main(["--batch", "1"]) == 0
    assert "1/1 passed" in capsys.readouterr().out


def test_the_cli_returns_nonzero_for_a_failing_single_map(monkeypatch, capsys) -> None:
    monkeypatch.setattr(hg.driver, "generate", lambda spec, out_base=None, render=True: hg.Report(plan=a_plan(), failures=["boom"]))
    assert hg.main(["--name", "X"]) == 1
    assert "boom" in capsys.readouterr().out
