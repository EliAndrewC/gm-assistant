"""Unit tests for the spec a caller writes and the site plan derived from it (`hamletgen/plan.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import math

import pytest

from l7r.diagram import hamletgen as hg

# ---- the spec refuses what the tier cannot draw --------------------------------------------------


@pytest.mark.parametrize("households", [0, 9, 21, 400])
def test_a_household_count_outside_the_hamlet_band_is_refused(households: int) -> None:
    """Below the band the place is an outlying farmstead; above it, it is a village and needs a
    headman, a shrine and tax-free plots this generator deliberately does not draw. Silently
    generating one anyway would produce a map that fails the gate for reasons that look unrelated."""
    with pytest.raises(ValueError, match="hamlet band"):
        hg.HamletSpec(name="X", seed=1, households=households)


def test_a_nonsense_compass_quarter_is_refused() -> None:
    with pytest.raises(ValueError, match="compass quarter"):
        hg.HamletSpec(name="X", seed=1, windward="NNW")


def test_an_unknown_water_sink_is_refused() -> None:
    with pytest.raises(ValueError, match="water_sink"):
        hg.HamletSpec(name="X", seed=1, water_sink="river")


# ---- sizing -------------------------------------------------------------------------------------


def test_the_field_target_is_gross_acres_times_households() -> None:
    plan = hg.plan_site(hg.HamletSpec(name="X", seed=1, households=15))
    assert plan.target_acres == pytest.approx(15 * hg.GROSS_ACRES_PER_HOUSEHOLD)


def test_the_canvas_grows_with_the_field_it_has_to_hold() -> None:
    small = hg.canvas_for(13.0, 1.0)
    big = hg.canvas_for(26.0, 1.0)
    assert big[0] > small[0] and big[1] > small[1]
    # ...and it is comfortably larger than the field, so `build_comb` never clamps the fan
    assert small[0] * small[1] > 13.0 * hg.SQ_FT_PER_ACRE * 2


@pytest.mark.parametrize(("households", "expect_last"), [(10, 0.93), (15, 0.93), (20, 0.93)])
def test_the_last_offtake_sits_near_the_canal_end(households: int, expect_last: float) -> None:
    """A supply canal running far past its last delivery ditch leaves a tail that dies in bare
    ground - see OFFTAKE_LADDER. Ikegami's authored 0.66 is exactly that shape of number."""
    a, _b = hg.offtakes_for(households)
    assert a[-1] == expect_last


def test_the_offtake_ladder_covers_counts_past_its_last_rung() -> None:
    assert hg.offtakes_for(999) == (hg.OFFTAKE_LADDER[-1][1], hg.OFFTAKE_LADDER[-1][2])


# ---- the rolls ----------------------------------------------------------------------------------


def test_the_same_seed_plans_the_same_hamlet() -> None:
    one = hg.plan_site(hg.HamletSpec(name="X", seed=11, households=14))
    two = hg.plan_site(hg.HamletSpec(name="X", seed=11, households=14))
    assert (one.down_deg, one.windward, one.water_sink, one.cluster_shape, one.lane_skeleton) == (two.down_deg, two.windward, two.water_sink, two.cluster_shape, two.lane_skeleton)


def test_different_seeds_roll_different_hamlets() -> None:
    """The whole point of the knob layer: a cohort must not be twenty copies of one map."""
    combos = {(p.down_deg, p.water_sink, p.cluster_shape, p.lane_skeleton) for p in (hg.plan_site(hg.HamletSpec(name="X", seed=s, households=15)) for s in range(1, 21))}
    assert len(combos) >= 12


def test_every_declared_knob_is_honored_over_its_roll() -> None:
    plan = hg.plan_site(
        hg.HamletSpec(
            name="X",
            seed=5,
            households=13,
            down_deg=180.0,
            water_flow=95.0,
            windward="E",
            water_sink="offmap",
            cluster_shape="crescent",
            lane_skeleton="Y",
            plot_size="strip",
            grain_drift=12,
            woodland_patches=1,
        )
    )
    assert (plan.down_deg, plan.water_flow, plan.windward, plan.water_sink) == (180.0, 95.0, "E", "offmap")
    assert (plan.cluster_shape, plan.lane_skeleton, plan.plot_size, plan.grain_drift, plan.woodland_patches) == ("crescent", "Y", "strip", 12, 1)


def test_the_drainage_bearing_follows_the_fall_unless_declared() -> None:
    """A hamlet is one comb draining down one valley, so absent a declaration the two agree - but
    they stay separate fields, because at any larger tier they are genuinely different facts."""
    assert hg.plan_site(hg.HamletSpec(name="X", seed=2, down_deg=45.0)).water_flow == 45.0


@pytest.mark.parametrize("down_deg", [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0])
def test_the_cold_wind_comes_off_the_high_ground(down_deg: float) -> None:
    """Cold air drains downhill, so the wind a valley settlement shelters from blows from upslope
    (turned up to 45 deg). This is what makes 'back to the hill' and 'back to the wind' one fact
    rather than two, and rolling them apart put a cluster in the drainage ditch - see WIND_TURNS."""
    wx, wy = hg.WIND_VECTORS[hg.windward_for(down_deg, seed=4)]
    up = (-math.cos(math.radians(down_deg)), -math.sin(math.radians(down_deg)))
    assert wx * up[0] + wy * up[1] > 0.5  # within 60 deg of straight upslope


def test_a_nonsense_field_archetype_is_refused() -> None:
    with pytest.raises(ValueError, match="field_archetype"):
        hg.HamletSpec(name="X", seed=1, field_archetype="terraces")


def test_the_roll_only_offers_archetypes_that_gate_clean() -> None:
    """`polder_grid` is opt-in until its own cohort is green (see ROLLED_ARCHETYPES).

    A rolled archetype with known failures mixes them into the valley tier's 36/36 and destroys the
    one number that says the scripted process is consistent - which is exactly what happened the
    moment the polder was added to the roll. Pinning it is still honoured; only the ROLL is held
    back, and this is the test that will fail (correctly) on the day someone promotes it."""
    assert set(hg.ROLLED_ARCHETYPES) <= set(hg.FIELD_ARCHETYPES)
    rolled = {hg.plan_site(hg.HamletSpec(name="X", seed=s, households=15)).field_archetype for s in range(1, 30)}
    assert rolled == set(hg.ROLLED_ARCHETYPES)
