"""Unit tests for the ground between everything - open-ground scan, woodland, windbreak (`hamletgen/hinterland.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import pytest

from l7r.diagram import hamletgen as hg

# REACHED THROUGH THE MODULE, not through the package. `stage_windbreak` and `title_pocket` are
# internals of this stage; pinning them on hamletgen's star-import surface to satisfy one test would
# widen the package's public contract for a test's convenience (tests/hamletgen/test_surface.py).
from l7r.diagram.hamletgen import hinterland
from l7r.diagram.settlement import Settlement

from ._builders import SQUARE, a_plan


def test_a_square_far_from_the_crop_clears_and_one_on_it_does_not() -> None:
    assert hg._clear_gap((700.0, 700.0), 50.0, [SQUARE], 1.0) is None  # standing in it
    assert hg._clear_gap((700.0, 200.0), 50.0, [SQUARE], 1.0) == pytest.approx(150.0)
    assert hg._clear_gap((700.0, 1100.0), 50.0, [SQUARE], 1.0) is None  # in the crop's sunny shadow
    assert hg._clear_gap((700.0, 700.0), 50.0, [], 1.0) is None  # no crop at all - nothing to measure


def test_a_square_near_a_line_is_detected() -> None:
    assert hg._near_line((100.0, 100.0), 20.0, [(0.0, 100.0), (200.0, 100.0)], pad=10.0)
    assert not hg._near_line((100.0, 400.0), 20.0, [(0.0, 100.0), (200.0, 100.0)], pad=10.0)


def test_a_windbreak_column_with_no_house_of_its_own_leans_on_the_whole_fringe() -> None:
    """`belt_polygon` samples the windward fringe in 8 columns ACROSS the wind; a cluster with a
    gap in the middle leaves some column with no house within its own width, and that column has to
    fall back on the cluster's overall fringe rather than divide by nothing.

    Held here because the branch is reached by cluster SHAPE, not by any spec knob: it was live on
    the pool until an unrelated re-roll moved the houses, and a fallback that no map happens to hit
    is exactly the kind that rots unnoticed (the skill CLAUDE.md's 'a check that never RUNS looks
    like a check that passes', one layer over). Two tight groups 1,100 px apart across a northerly
    wind put the three middle columns outside every house's reach."""
    plan = a_plan()
    s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
    s.M["houses"] = [{"x": x, "y": 700.0, "w": 46.0, "h": 28.0} for x in (200.0, 260.0, 320.0, 1300.0, 1360.0, 1420.0)]
    belt = hg.belt_polygon(s, plan)
    assert belt, "a gapped cluster still needs a windbreak belt"
    assert len(belt) >= 4


def test_a_jittered_woodland_seat_that_leaves_the_scan_window_is_refused() -> None:
    """The accepted seat is nudged off the sampling lattice by up to half a step, and that nudge can
    carry a seat near the window's edge OUT of the window - so the qualification predicate re-tests
    the bounds rather than trusting that the scan only offered legal points.

    Held here because nothing in the pool or the cohort happens to jitter a seat past the edge, and
    an untested bounds guard on a predicate whose whole job is to re-ask about a MOVED point is the
    kind that rots silently (this engine's own 'a check that never RUNS looks exactly like a check
    that passes', one layer down). Forcing `_hjit` to its maximum drives every jitter the same way,
    +half a step on both axes, which is what an edge seat needs to escape."""
    plan = a_plan()
    s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
    s.M["houses"] = [{"x": 300.0 + 60.0 * i, "y": 700.0, "w": 46.0, "h": 28.0} for i in range(6)]
    s.M["fields"] = []
    plan.belt = []
    s._hjit = lambda x, y, salt: 1.0 if salt in (71.0, 72.0) else 0.5  # type: ignore[method-assign]
    patches = hg.hinterland.open_ground_patches(s, plan, count=3)  # via the submodule: a white-box unit test, not a package-surface consumer
    # The run must still terminate and return only legal squares - a refused jitter falls back to the
    # unjittered seat, it does not drop the parcel or escape the canvas.
    for poly in patches:
        assert all(0.0 <= px <= plan.W and 0.0 <= py <= plan.H for px, py in poly), "a seat left the canvas"


def test_a_belt_vertex_in_the_title_pocket_is_pushed_out_of_it() -> None:
    """`stage_woodland` reserves blank ground for the map's name and keeps the COPPICE out of it, but
    the belt is computed there and drawn later, so `stage_windbreak` has to dent it around the same
    pocket - otherwise the hamlet's own title is drawn over its windbreak.

    Held here for the reason the gapped-column test above gives, and it is not hypothetical: this
    branch was live on the pool until the 2026-08-19 seam-alignment change moved every fan slightly,
    after which no map's belt happened to cross its title pocket and the gate failed on coverage
    rather than on behaviour. A dent that no map happens to need is exactly the kind that rots."""
    plan = a_plan()
    s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
    s.M["houses"] = [{"x": x, "y": 700.0, "w": 46.0, "h": 28.0} for x in (500.0, 560.0, 620.0)]
    tp = hinterland.title_pocket(s, plan)
    mid = ((tp[0] + tp[2]) / 2, (tp[1] + tp[3]) / 2)
    plan.belt = [(tp[0] - 80.0, tp[1] - 80.0), mid, (tp[2] + 80.0, tp[3] + 80.0), (tp[0] - 80.0, tp[3] + 80.0)]
    hinterland.stage_windbreak(s, plan)
    belt = [g for g in s.M["village_groves"] if g.get("role") == "windbreak"]
    assert belt, "the windbreak was not recorded"
    inside = [q for q in belt[0]["poly"] if tp[0] <= q[0] <= tp[2] and tp[1] <= q[1] <= tp[3]]
    assert not inside, f"belt vertices left standing in the title's pocket: {inside}"
