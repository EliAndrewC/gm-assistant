"""Unit tests for where the runoff goes - the drain, the brook, the tameike (`hamletgen/sink.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import pytest

from l7r.diagram import hamletgen as hg

from ._builders import a_plan


def test_the_run_to_the_map_edge_is_measured_along_the_fall() -> None:
    plan = a_plan()  # falls due south
    assert hg.edge_run(plan, (500.0, plan.H - 300.0)) == pytest.approx(300.0)


def test_pond_setback_walks_past_blocked_probes() -> None:
    """An outfall INSIDE the field envelope blocks the first probes (every near rim point lands in
    the crop), so the walk must step outward (`d += step`) until the ellipse clears, and the
    returned distance carries the 12 px cushion past that first clear seat."""
    plan = a_plan()
    d = hg.pond_setback(plan, (700.0, 700.0), 60.0, 40.0)
    assert d > 40.0 + 46.0 + 14.0  # further than the first probe: the walk really stepped
    cx, cy = 700.0 + plan.fall[0] * d, 700.0 + plan.fall[1] * d
    assert hg.pond_clear_of_crop(plan, (cx, cy), 60.0, 40.0)


def test_a_pond_laid_over_the_crop_is_recognized() -> None:
    """The predicate `stage_sink` uses to check its own clamp: `pond_clear_of_field`'s two tests, on
    the same envelope, so the siting and the check cannot disagree."""
    plan = a_plan()
    assert hg.pond_clear_of_crop(plan, (700.0, 1400.0), 100.0, 60.0), "well below the field: clear"
    assert not hg.pond_clear_of_crop(plan, (700.0, 700.0), 100.0, 60.0), "sitting in the middle of it: not clear"
    assert not hg.pond_clear_of_crop(plan, (700.0, 1040.0), 100.0, 60.0), "rim overlapping the low edge: not clear"


@pytest.mark.parametrize(("down_deg", "start", "expect"), [(0.0, (500.0, 500.0), None), (180.0, (500.0, 500.0), 500.0), (90.0, (500.0, 500.0), None)])
def test_the_run_to_the_frame_is_measured_on_every_axis(down_deg, start, expect) -> None:  # type: ignore[no-untyped-def]
    """`edge_run` walks whichever axis the fall actually points along - east and west included, which
    the south-falling fixtures elsewhere in this file never exercise."""
    plan = hg.plan_site(hg.HamletSpec(name="X", seed=3, households=15, down_deg=down_deg))
    run = hg.edge_run(plan, start)
    assert run > 0
    if expect is not None:
        assert run == pytest.approx(expect)


# ---- end to end ---------------------------------------------------------------------------------


def test_a_pond_the_canvas_cannot_hold_falls_back_to_draining_OFF_MAP(monkeypatch: pytest.MonkeyPatch) -> None:
    """A CLAMPED pond is no pond, and the map must say so rather than draw one on the rice.

    `pond_setback` walks the tameike downslope until its rim clears the crop; the canvas clamp then
    pulls it back on-frame - and straight back onto the rice it had just cleared. The stage treats
    that as the same finding as a set-back past the limit and drains the field off the frame
    instead. Forced here by making the solver ask for a set-back the canvas cannot give, because no
    cohort seed currently produces one: the branch is real logic that the demo maps do not reach,
    which is exactly what this file is for."""
    # The set-back must pass the LIMIT test and still clamp - those are two different findings with
    # the same answer, and only the clamp is under test here.
    monkeypatch.setattr(hg.sink, "POND_SETBACK_LIMIT", 1e9)
    monkeypatch.setattr(hg.sink, "pond_setback", lambda plan, out, prx, pry, **kw: 5000.0)
    plan = hg.plan_site(hg.HamletSpec(name="Clamped", seed=23, households=12, water_sink="pond"))
    assert plan.water_sink == "pond", "the fixture must START as a pond map, or it proves nothing"
    s = hg.build(plan)
    assert plan.water_sink == "offmap", "a pond the canvas cannot hold must fall back to the off-map brook"
    assert not s.M.get("ponds"), "and no pond may be drawn"
    assert plan.sink_brook, "the fallback must actually cut the brook it promised"
