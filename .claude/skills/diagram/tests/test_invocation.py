"""Tests for `_invocation` - the process-tree determination (feature 127, layer 2).

TWO DIRECTIONS, ALWAYS. A guard is implemented when it FIRES on the case it exists to catch (FR-015)
AND stays quiet on the legitimate path (FR-016). The second half is the one that protects the feature
from causing the behavior it exists to stop: a guard that refuses correct work teaches a session that
the override is routine, which is how the observed tier-2 workaround became habitual.

The end-to-end cases build a REAL process tree with a real make, because the whole claim of this
module is about process ancestry and a mocked ancestry would prove nothing about it.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from l7r.diagram import _invocation as inv

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[2]


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """The verdict is cached per process on purpose; a test that inherited it would be testing the
    previous test's tree."""
    inv._verdict = None


# --------------------------------------------------------------------------------------------
# END TO END: a real make, a real process tree. These are the ones that matter.
# --------------------------------------------------------------------------------------------

_PROBE = "import sys; sys.path.insert(0, {skill!r}); from l7r.diagram import _invocation as i; print(i.via_make())"


def _run_probe(tmp_path: Path, recipe: str, *, cwd: Path, makefile: Path | None = None) -> str:
    """Run the probe under a real make and return what it printed."""
    mf = makefile or (cwd / "Makefile")
    mf.write_text(f"probe:\n\t@{recipe}\n")
    args = ["make", "probe"] if makefile is None else ["make", "-f", str(mf), "probe"]
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False).stdout.strip()


def _probe_cmd() -> str:
    return f'{sys.executable} -c "{_PROBE.format(skill=str(SKILL))}"'


def test_a_child_spawned_under_make_INHERITS_make() -> None:
    """STAYS QUIET - and this test replaced one that was subtly, instructively wrong.

    The original asserted that spawning `python3 -c ...` gives a process with no make in its
    ancestry, and it PASSED when the file was run directly. Under `make quick` it failed, because a
    subprocess of a make-run process still has make above it. That is not a bug in the guard; it is
    the guard being right, and it is the same inheritance that makes pytest-xdist workers and
    `cohort()`'s pool children legitimate.

    So the honest version is this: the property under test is INHERITANCE, and it is the property the
    whole design depends on. The old test could only pass when the suite was run the wrong way, which
    makes it worse than no test - it was a green light for running pytest outside make.

    THE NO-MAKE CASE IS UNTESTABLE END-TO-END FROM INSIDE A MAKE-RUN SUITE, by construction. It is
    covered at unit level instead, where the ancestry is supplied rather than inherited - see
    `test_compute_reports_a_foreign_make_differently_from_no_make`."""
    out = subprocess.run(
        [sys.executable, "-c", _PROBE.format(skill=str(SKILL))],
        capture_output=True,
        text=True,
        check=False,
    )
    expected = "True" if inv.via_make() else "False"
    assert out.stdout.strip() == expected, "a child must inherit this process's verdict, whichever it is"


def test_make_in_this_repo_is_accepted(tmp_path: Path) -> None:
    """STAYS QUIET: make -> sh -c -> python, which is EVERY make recipe.

    A parent-only check fails this case, because make runs recipe lines through a shell and the
    immediate parent is `sh`."""
    work = REPO / ".tmp-invocation-test"
    work.mkdir(exist_ok=True)
    try:
        assert _run_probe(tmp_path, _probe_cmd(), cwd=work) == "True"
    finally:
        for f in work.iterdir():
            f.unlink()
        work.rmdir()


def test_a_foreign_makefile_is_refused(tmp_path: Path) -> None:
    """FIRES: `make -f /tmp/evil.mk`, the hole a bare ancestry check leaves open.

    Measured 2026-08-24: this passes a naive check, because make really IS the parent - it is just
    not this project's make. Two lines in /tmp would otherwise defeat the entire guard."""
    assert _run_probe(tmp_path, _probe_cmd(), cwd=tmp_path, makefile=tmp_path / "evil.mk") == "False"


def test_a_make_run_outside_the_repo_is_refused(tmp_path: Path) -> None:
    """FIRES: a make whose cwd is outside the repository is not this project's make."""
    assert _run_probe(tmp_path, _probe_cmd(), cwd=tmp_path) == "False"


def test_a_multiprocessing_child_under_make_is_accepted(tmp_path: Path) -> None:
    """STAYS QUIET: pool workers sit three levels below make, and pytest-xdist and `cohort()` both
    use that shape. Detecting only the immediate parent would refuse every worker."""
    work = REPO / ".tmp-invocation-pool"
    work.mkdir(exist_ok=True)
    script = work / "pool_probe.py"
    script.write_text(
        textwrap.dedent(f"""
        import multiprocessing as mp, sys
        sys.path.insert(0, {str(SKILL)!r})
        from l7r.diagram import _invocation as i
        def kid(_):
            i._verdict = None
            return i.via_make()
        if __name__ == "__main__":
            with mp.Pool(2) as p:
                print(all(p.map(kid, [0, 1])))
        """)
    )
    try:
        assert _run_probe(tmp_path, f"{sys.executable} {script}", cwd=work) == "True"
    finally:
        for f in work.iterdir():
            f.unlink()
        work.rmdir()


# --------------------------------------------------------------------------------------------
# THE CACHE (research R4)
# --------------------------------------------------------------------------------------------


def test_the_proc_walk_happens_once_per_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """STAYS QUIET, and guards a performance property rather than a behavior.

    Every slow generator ever profiled in this engine was one shape: a per-candidate scan of geometry
    that does not change during the scan. A /proc walk in a placer loop would recreate it exactly.
    This test fails if a later refactor drops the cache - the failure mode being silently slow, which
    nothing else would catch."""
    calls = 0
    real = inv._ancestry

    def counting() -> list[int]:
        nonlocal calls
        calls += 1
        return real()

    monkeypatch.setattr(inv, "_ancestry", counting)
    inv._verdict = None
    for _ in range(50):
        inv.via_make()
    assert calls == 1, f"the ancestry walk ran {calls} times; it must be cached after the first"


# --------------------------------------------------------------------------------------------
# THE REFUSAL MESSAGE (FR-006)
# --------------------------------------------------------------------------------------------


def test_the_refusal_names_the_make_target(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """FIRES, and checks the part that makes a refusal useful rather than merely correct.

    A refusal that does not say what to run instead is a bug: the whole purpose is that the right
    route is one line away. Same rule as this project's blocking hooks, whose messages carry the
    playbook because documentation nobody re-reads does not change behavior."""
    monkeypatch.setattr(inv, "_verdict", (False, "not invoked through make"))
    with pytest.raises(SystemExit) as exc:
        inv.assert_via_make("a 25-minute cohort", "maps")
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "make maps" in err
    assert "a 25-minute cohort" in err
    assert "not invoked through make" in err


def test_a_permitted_call_says_nothing(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """STAYS QUIET: the legitimate path prints nothing at all. Noise on the correct route is how a
    guard trains people to ignore it."""
    monkeypatch.setattr(inv, "_verdict", (True, ""))
    inv.assert_via_make("the reference settlement", "reference")
    assert capsys.readouterr().err == ""


# --------------------------------------------------------------------------------------------
# UNIT: the pure predicates
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["make", "probe"], False),
        (["make", "-f", str(REPO / "Makefile"), "x"], False),
        (["make", "-f", "/tmp/evil.mk", "x"], True),
        (["make", "--file", "/tmp/evil.mk", "x"], True),
        (["make", "--makefile=/tmp/evil.mk", "x"], True),
        (["make", "-f/tmp/evil.mk", "x"], True),
        (["make", "--file=Makefile", "x"], False),
        (["make", "-f"], False),
    ],
)
def test_foreign_makefile_detection(argv: list[str], expected: bool) -> None:
    """Both directions in one table: a relative `-f` resolves against MAKE's cwd, which is why that
    is a parameter rather than something looked up from our own."""
    assert inv._foreign_makefile(argv, str(REPO)) is expected


def test_a_relative_makefile_outside_the_repo_is_foreign(tmp_path: Path) -> None:
    """The case the explicit `make_cwd` parameter exists for: `-f Makefile` is innocent inside the
    repo and foreign outside it, and the difference is invisible without the make process's cwd."""
    assert inv._foreign_makefile(["make", "-f", "Makefile"], str(tmp_path)) is True


def test_inside_repo_rejects_a_prefix_that_is_not_a_parent() -> None:
    """A path that merely SHARES A PREFIX with the repo is not inside it - `/repo-evil` must not pass
    because it starts with `/repo`. The separator in the comparison is what stops that."""
    assert inv._inside_repo(str(REPO)) is True
    assert inv._inside_repo(str(REPO / "specs")) is True
    assert inv._inside_repo(str(REPO) + "-evil") is False
    assert inv._inside_repo("") is False


def test_unreadable_proc_entries_are_survived(monkeypatch: pytest.MonkeyPatch) -> None:
    """A process can exit between reading its child's PPid and reading its own stat. A guard that
    raises on that race is a guard that gets deleted, so every reader degrades instead."""
    assert inv._comm(2**30) == ""
    assert inv._cmdline(2**30) == []
    assert inv._cwd(2**30) == ""

    def boom(*_a: object, **_k: object) -> object:
        raise OSError("vanished")

    monkeypatch.setattr("builtins.open", boom)
    assert inv._ancestry() == []


def test_a_malformed_stat_line_stops_the_walk(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """`/proc/<pid>/stat` carries comm in parentheses and comm may contain spaces and parentheses, so
    the PPid is parsed by splitting on the LAST `") "`. Garbage stops the walk rather than crashing."""

    class FakeFile:
        def __enter__(self) -> FakeFile:
            return self

        def __exit__(self, *_a: object) -> None:
            return None

        def read(self) -> str:
            return "nonsense with no parenthesis"

    monkeypatch.setattr("builtins.open", lambda *_a, **_k: FakeFile())
    assert inv._ancestry() == []


def test_compute_reports_a_foreign_make_differently_from_no_make(monkeypatch: pytest.MonkeyPatch) -> None:
    """The two refusal reasons are distinct because they call for different fixes: `run it through
    make` versus `you ran a make, but not this project's`."""
    monkeypatch.setattr(inv, "_ancestry", lambda: [10])
    monkeypatch.setattr(inv, "_comm", lambda _p: "make")
    monkeypatch.setattr(inv, "_cwd", lambda _p: "/somewhere/else")
    ok, why = inv._compute()
    assert ok is False
    assert "does not belong to this repository" in why

    monkeypatch.setattr(inv, "_comm", lambda _p: "bash")
    ok, why = inv._compute()
    assert ok is False
    assert why == "not invoked through make"


def test_a_repo_make_running_a_foreign_makefile_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """cwd inside the repo is not enough on its own - `cd <repo> && make -f /tmp/evil.mk` must still
    be refused, which is the `continue` branch after the cwd check passes."""
    monkeypatch.setattr(inv, "_ancestry", lambda: [10])
    monkeypatch.setattr(inv, "_comm", lambda _p: "make")
    monkeypatch.setattr(inv, "_cwd", lambda _p: str(REPO))
    monkeypatch.setattr(inv, "_cmdline", lambda _p: ["make", "-f", "/tmp/evil.mk", "x"])
    ok, why = inv._compute()
    assert ok is False
    assert "does not belong to this repository" in why


def test_reason_computes_the_verdict_when_asked_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_reason()` may be the first call in a process; it must compute rather than return None."""
    monkeypatch.setattr(inv, "_ancestry", lambda: [])
    inv._verdict = None
    assert inv._reason() == "not invoked through make"


def test_real_proc_readers_work_on_this_process() -> None:
    """The readers are exercised against a process that certainly exists, so a change that breaks
    the parsing is caught by something other than the end-to-end tests."""
    me = os.getpid()
    assert inv._comm(me) != ""
    assert inv._cmdline(me) != []
    assert inv._cwd(me) != ""
    assert me in inv._ancestry()


def test_a_repo_make_with_no_foreign_makefile_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    """STAYS QUIET, in-process. The end-to-end tests above prove this with a REAL make, but they run
    in subprocesses, so the accept branch of `_compute` is never executed in the process coverage is
    measuring. This is that same case at unit level - it does not replace the end-to-end proof, and
    would be worthless on its own, because a mocked ancestry cannot show that real make recipes are
    detected through the `sh -c` they run under."""
    monkeypatch.setattr(inv, "_ancestry", lambda: [10])
    monkeypatch.setattr(inv, "_comm", lambda _p: "make")
    monkeypatch.setattr(inv, "_cwd", lambda _p: str(REPO))
    monkeypatch.setattr(inv, "_cmdline", lambda _p: ["make", "reference"])
    assert inv._compute() == (True, "")
