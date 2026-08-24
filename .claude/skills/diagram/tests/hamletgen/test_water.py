"""Unit tests for the water frame and the field it shapes (`hamletgen/water.py`), plus the waterfields frame math it stands on.

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import math
import os
import tempfile

import pytest

from l7r.diagram import hamletgen as hg
from l7r.diagram import waterfields as wf
from l7r.diagram.settlement import point_in_poly, seg_dist

# ---- the derivations that read the map ----------------------------------------------------------


def test_the_intake_sits_at_the_head_of_the_slope() -> None:
    """Gravity: a comb is fed from its high end. This was the first real bug in the experiment - the
    engine's canvas-relative `edge_*` anchors put a lateral intake at mid-height, which left the fan
    half a canvas to run and saturated the field far under the acreage the households needed."""
    plan = hg.plan_site(hg.HamletSpec(name="X", seed=6, households=15, down_deg=90.0))
    (sx, sy), name = hg.head_sluice(plan)
    assert sy < plan.H / 2  # upslope of the canvas middle on a south-falling map
    assert name.startswith("head_")


def test_a_fan_that_folds_back_on_itself_is_recognized() -> None:
    """The disqualifier `fit_field` uses: a hairpin in the fan's own ditch net."""
    straight = {"channels": [{"pts": [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]}]}
    hairpin = {"channels": [{"pts": [(0.0, 0.0), (100.0, 0.0), (10.0, 5.0)]}]}
    assert not hg.net_bends_acutely(straight)
    assert hg.net_bends_acutely(hairpin)


@pytest.mark.rolls_map
def test_a_polder_inlets_mouth_is_pulled_INSIDE_the_crop() -> None:
    """THE RATCHET for `draw_comb_field`'s constructed inlet end (2026-08-15).

    That end is not clipped from an anchor - it is BUILT, as the main channel's last point stepped
    70 px straight downhill, which is a COMB's geometry. On a polder the main is the ring canal
    running ALONG the high edge, so its last point is a corner and the step skims the boundary:
    seed 19 landed the mouth 2.6 px inside where `channel_field_anchored` wants 10, and no amount of
    moving the sluice changed it, because the anchor is not what sets this end.

    Seed 19 is chosen deliberately - it is the case that needed the pull (seed 3 needs it at 6.0 px,
    seed 8 does not need it at all), so this test exercises the branch rather than merely passing."""
    plan = hg.plan_site(hg.HamletSpec(name="Polder", seed=19, households=16, field_archetype="polder_grid", down_deg=90))
    s = hg.build(plan)
    with tempfile.TemporaryDirectory() as tmp:
        s.finish(os.path.join(tmp, "scratch"), render=False)
    env = [(float(a), float(b)) for a, b in s.M["fields"][0]["outline"]]
    n = len(env)
    fed = [c for c in s.M["channels"] if (c.get("to") or {}).get("kind") == "field"]
    assert fed, "the polder is fed by a channel from its header reservoir"
    for c in fed:
        end = c["poly"][-1]
        assert point_in_poly(end[0], end[1], env), f"the inlet mouth {end} must finish INSIDE the crop"
        gap = min(seg_dist(end[0], end[1], env[k], env[(k + 1) % n]) for k in range(n))
        assert gap >= 10.0, f"the mouth is {gap:.1f} px from the outline; the rule wants 10 so the field paints over it"


@pytest.mark.rolls_map
def test_a_polder_reservoir_backs_off_until_its_rim_clears_the_crop() -> None:
    """The seat is measured from the ring canal's HEAD, so anything that moves that head moves the
    reservoir - trimming the ring's doubling-back stub did exactly that and slid the pond onto the
    crop. A fixed stand-off from a moving anchor is the pinned-constant mistake in miniature, so the
    rim is tested and the pond walks uphill until it is clear.

    Seed 12 is chosen because it NEEDS the walk (one step at falls 0 and 180); seeds 3, 8, 19 and 22
    clear on the first try, so testing one of those would exercise nothing."""
    plan = hg.plan_site(hg.HamletSpec(name="Polder", seed=12, households=16, field_archetype="polder_grid", down_deg=0))
    s = hg.build(plan)
    with tempfile.TemporaryDirectory() as tmp:
        s.finish(os.path.join(tmp, "scratch"), render=False)
    pond = s.M.get("pond")
    assert pond, "the polder's water source is its header reservoir"
    rim = [(pond[0] + pond[2] * math.cos(a), pond[1] + pond[3] * math.sin(a)) for a in (k * math.pi / 8 for k in range(16))]
    assert not any(point_in_poly(q[0], q[1], list(plan.envelope)) for q in rim), "no part of the rim may lie on the crop"
    # ...and it stays UPHILL of the field, which is the rule the walk must not trade away
    dx, dy = plan.fall
    assert pond[0] * dx + pond[1] * dy < min(p[0] * dx + p[1] * dy for p in plan.envelope), "the source sits above what it waters"


@pytest.mark.rolls_map
def test_a_polder_hamlet_draws_its_grid_dike_and_reservoir() -> None:
    """THE SECOND FIELD ARCHETYPE (GM 2026-08-13), pinned at what it currently guarantees.

    The polder is WORK IN PROGRESS - it has two named gate failures in `build_polder`'s own geometry
    (see hamletgen.md) - so this does not assert a clean gate, which would be a lie. It asserts the
    things the substrate is already responsible for and which no other test covers: that the grid is
    solved to the acreage the households imply, that every household is seated, that the defining
    perimeter dike exists, and that the header reservoir sits OUTSIDE the crop rather than in it,
    which two earlier versions of the siting got wrong in two different ways."""
    plan = hg.plan_site(hg.HamletSpec(name="Polder", seed=8, households=16, field_archetype="polder_grid"))
    assert plan.field_archetype == "polder_grid"
    s = hg.build(plan)
    with tempfile.TemporaryDirectory() as tmp:
        s.finish(os.path.join(tmp, "scratch"), render=False)
    assert s.M["meta"]["field_archetype"] == "polder_grid"
    assert abs(plan.acres - plan.target_acres) / plan.target_acres < 0.12, f"{plan.acres:.1f} acres against a {plan.target_acres:.1f} target"
    assert plan.placed == plan.spec.households
    assert s.M.get("dikes"), "a polder without its perimeter dike is not a polder"
    pond = s.M.get("pond")
    assert pond, "the header reservoir is the polder's water source"
    assert not point_in_poly(pond[0], pond[1], list(plan.envelope)), "the reservoir sits BESIDE the crop, never in it"


def test_declared_knob_pins_reach_the_engine() -> None:
    """A `pins` entry is forwarded to the engine's own knob catalog, so a spec can steer a knob this
    module does not model (a land-use overlay, a field archetype)."""
    from l7r.diagram.settlement import Settlement

    plan = hg.plan_site(hg.HamletSpec(name="Pinned", seed=2, households=12, pins={"land_use_overlay": "lotus"}))
    s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
    hg.stage_water_frame(s, plan)
    assert s.knob_pins["land_use_overlay"] == "lotus"


def test_miter_normals_on_a_straight_canal_are_the_chord_normal() -> None:
    # fall points +y (down_deg=90), so upslope is -y; every chord normal flips to point that way
    bn = wf._miter_normals([(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)], wf._Frame(90.0))
    assert len(bn) == 3
    for nx, ny in bn:
        assert nx == pytest.approx(0.0) and ny == pytest.approx(-1.0)


def test_miter_normals_share_and_scale_the_seam_at_a_bend() -> None:
    # a ~17-degree bend: the interior boundary gets ONE mitred normal - the bisector of the two
    # chord normals, scaled 1/cos(half-bend) so the hem band keeps its true depth at the seam
    F = wf._Frame(90.0)
    pts = [(0.0, 0.0), (100.0, 0.0), (200.0, -30.0)]
    bn = wf._miter_normals(pts, F)
    n0, n1 = bn[0], bn[2]  # the end boundaries carry their single chord's (unit) upslope normal
    assert math.hypot(*n0) == pytest.approx(1.0) and math.hypot(*n1) == pytest.approx(1.0)
    cos_full = n0[0] * n1[0] + n0[1] * n1[1]
    cos_half = math.sqrt((1.0 + cos_full) / 2.0)
    assert math.hypot(*bn[1]) == pytest.approx(1.0 / cos_half)
    # and it bisects: equal angle to both chord normals
    ml = math.hypot(*bn[1])
    assert (bn[1][0] * n0[0] + bn[1][1] * n0[1]) / ml == pytest.approx((bn[1][0] * n1[0] + bn[1][1] * n1[1]) / ml)


def test_miter_normals_fold_falls_back_to_the_outgoing_chord() -> None:
    # out and straight back: the two upslope normals cancel exactly, so no shared offset
    # direction exists - the boundary takes its outgoing chord's normal instead of dividing by ~0
    bn = wf._miter_normals([(0.0, 0.0), (0.0, 100.0), (0.0, 0.0)], wf._Frame(90.0))
    assert bn[0] == pytest.approx((-1.0, 0.0))
    assert bn[1] == pytest.approx((1.0, 0.0))
    assert bn[2] == pytest.approx((1.0, 0.0))


def test_miter_normals_caps_the_scale_on_a_hairpin() -> None:
    # a ~160-degree divergence between the flipped chord normals: the true miter scale would be
    # 1/cos(80 deg) = 5.8x, spiking the seam far upslope - capped at 2x (max(0.5, dot))
    bn = wf._miter_normals([(0.0, 0.0), (-8.7, 49.2), (-17.4, 0.2)], wf._Frame(90.0))
    assert math.hypot(*bn[1]) == pytest.approx(2.0)
