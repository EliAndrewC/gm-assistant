"""Tests for why_placed.py - the placement tracer.

The interesting assertions are the two that a diagnostic tool can silently get wrong: that a
manifest key created LATER by `setdefault` is still watched (that is how `farm_sheds` comes into
being, and it was one of the records this tool was written to chase), and that the monkeypatches are
fully RESTORED afterwards - the gate runs every gen in one process, so a leaked patch would follow
the tracer into unrelated maps.
"""

from __future__ import annotations

from l7r.diagram import settlement
from l7r.diagram.tools import why_placed as W

GEN = """
from l7r.diagram import settlement
s = settlement.Settlement(600, 500, seed=1)
s.meta(name="T", scale="town", ftpx=1)
s.building(300, 300, 20, 12, "shop")
s.try_building(300, 300, "shop")          # refused: it lands on the one just placed
s.M.setdefault("late_key", []).append({"x": 302.0, "y": 301.0, "w": 3.0, "h": 3.0, "kind": "late"})
"""


def _gen(tmp_path):
    p = tmp_path / "synthetic.gen.py"
    p.write_text(GEN)
    return str(p)


# ---- pure helpers ---------------------------------------------------------------------------


def test_near_uses_the_centre_when_there_is_one():
    assert W.near({"x": 100.0, "y": 100.0}, 103.0, 104.0, 8.0)
    assert not W.near({"x": 100.0, "y": 100.0}, 130.0, 100.0, 8.0)


def test_near_falls_back_to_a_ring_for_features_recorded_as_outlines():
    ring = {"poly": [[10.0, 10.0], [200.0, 200.0]]}
    assert W.near(ring, 12.0, 11.0, 8.0)
    assert not W.near(ring, 500.0, 500.0, 8.0)
    assert W.near({"outline": [[10.0, 10.0]]}, 10.0, 10.0, 1.0)
    assert not W.near({"label": "no position anywhere"}, 0.0, 0.0, 1e9)


def test_useful_frames_drops_the_tracers_own_plumbing_and_keeps_the_innermost():
    class F:
        def __init__(self, filename, lineno, name):
            self.filename, self.lineno, self.name = filename, lineno, name

    stack = [F("/x/why_placed.py", 1, "consider"), F("/x/a.gen.py", 7, "<module>")] + [F(f"/x/s{i}.py", i, f"f{i}") for i in range(5)]
    out = W.useful_frames(stack, limit=3)
    assert len(out) == 3
    assert all(n != "why_placed.py" for n, _, _ in out)
    assert out[-1] == ("s4.py", 4, "f4")  # innermost last


def test_parse_point_round_trips_and_rejects_junk():
    import argparse

    import pytest

    assert W.parse_point("1102.6,1429.5") == (1102.6, 1429.5)
    with pytest.raises(argparse.ArgumentTypeError):
        W.parse_point("nope")


# ---- the tracer -----------------------------------------------------------------------------


def test_watching_names_the_gen_line_and_the_engine_method(tmp_path):
    with W.watching(300.0, 300.0, 8.0) as hits:
        W.run_gen(_gen(tmp_path))
    keys = {h.key for h in hits}
    assert "buildings" in keys
    b = next(h for h in hits if h.key == "buildings")
    files = [f[0] for f in b.frames]
    assert "synthetic.gen.py" in files  # the call site to go and look at
    assert "urban.py" in files  # ...and the engine method that chose the spot (settlement/structures/urban.py holds building() since the 114 package split; it was structures.py from 025 until then)


def test_watching_sees_a_key_created_later_by_setdefault(tmp_path):
    # farm_sheds is born this way, and a watcher that only wrapped the keys present at construction
    # would miss it entirely - reporting "nothing is here" about a record that plainly is.
    with W.watching(300.0, 300.0, 8.0) as hits:
        W.run_gen(_gen(tmp_path))
    assert any(h.key == "late_key" for h in hits)


def test_watching_can_be_restricted_to_one_key(tmp_path):
    with W.watching(300.0, 300.0, 8.0, keys=("late_key",)) as hits:
        W.run_gen(_gen(tmp_path))
    assert {h.key for h in hits} == {"late_key"}


def test_watching_restores_the_class(tmp_path):
    before = settlement.Settlement.__init__
    with W.watching(300.0, 300.0) as _:
        W.run_gen(_gen(tmp_path))
    assert settlement.Settlement.__init__ is before
    assert not isinstance(settlement.Settlement(600, 500, seed=1).M, W._WatchDict)


def test_watching_fits_reports_a_refusal_with_an_observed_cause(tmp_path):
    with W.watching_fits(300.0, 300.0, 8.0) as refs:
        W.run_gen(_gen(tmp_path))
    assert refs, "the synthetic gen probes this exact point"
    assert any(not r.verdict for r in refs)
    assert all(isinstance(r.cause, str) and r.cause for r in refs)


def test_watching_fits_restores_every_predicate_it_patched(tmp_path):
    S = settlement.Settlement
    before = (S._fits, S._in_blocked, S._near_corridor, S._hard_clear)
    with W.watching_fits(300.0, 300.0) as _:
        W.run_gen(_gen(tmp_path))
    assert (S._fits, S._in_blocked, S._near_corridor, S._hard_clear) == before


# ---- reports --------------------------------------------------------------------------------


def test_report_hits_says_what_to_try_when_nothing_is_there():
    out = W.report_hits([], 10.0, 20.0, 8.0)
    assert "--refused" in out and "radius" in out


def test_report_refusals_distinguishes_unvisited_ground_from_refused_ground():
    out = W.report_refusals([], 10.0, 20.0, 8.0)
    assert "UNVISITED" in out
    r = W.Refusal(10.0, 5.0, False, "_in_blocked (a block_poly keep-out - CENTRE-tested)", [("g.gen.py", 3, "<module>")])
    out = W.report_refusals([r], 10.0, 20.0, 8.0)
    assert "1 refused" in out and "_in_blocked" in out and "g.gen.py:3" in out


def test_report_hits_renders_a_record(tmp_path):
    h = W.Hit("buildings", {"x": 1.0, "y": 2.0, "w": 3.0, "h": 4.0, "kind": "shop", "rot": 90}, [("a.gen.py", 9, "<module>")])
    out = W.report_hits([h], 1.0, 2.0, 8.0)
    assert "buildings: shop" in out and "3x4" in out and "rot=90" in out and "a.gen.py:9" in out
    ring = W.Hit("fields", {"poly": [[1.0, 2.0]]}, [])
    assert "(ring)" in W.report_hits([ring], 1.0, 2.0, 8.0)


# ---- CLI ------------------------------------------------------------------------------------


def test_main_runs_both_modes(tmp_path, capsys):
    g = _gen(tmp_path)
    assert W.main([g, "--at", "300,300"]) == 0
    assert "buildings" in capsys.readouterr().out
    assert W.main([g, "--refused", "300,300"]) == 0
    assert "candidate" in capsys.readouterr().out


def test_main_requires_a_target(tmp_path):
    import pytest

    with pytest.raises(SystemExit):
        W.main([_gen(tmp_path)])
