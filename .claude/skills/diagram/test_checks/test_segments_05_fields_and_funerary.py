"""Split from test_checks.py by feature 025 - see test_checks/CLAUDE.md for the index."""

import check_village
from test_checks._builders import (
    _FORK_MAINS,
    _MOAT,
    _MON,
    _PADDY,
    _SHR,
    WALL,
    _city_dead,
    _crem_cem,
    _crem_road,
    _crem_temple,
    _cross_M,
    _dead,
    _dryplot,
    _farmhouse,
    _field,
    _nuc_grid,
    _nuc_village_M,
    _nuc_with_windbreak,
    _paddy_field_rec,
    _supply_M,
    _tips_M,
    _town_dead,
    _water_grave,
    bldg,
    f,
    manifest,
)


# ---- field_ditches_reach_source_and_sink (role-aware: supply->source, drain->sink) ----------
def test_field_ditches_reach_source_and_sink_fires_when_ungrounded():
    # a supply ditch with no pond source AND a drain with no runoff sink - both dangle (the failure
    # path of the role-aware grounding). The GOOD case is covered by the real maps (kikuta passes with
    # its full pond->canal->cascade->drain->off-map network; the wip Hoshigaoka likewise).
    M = {"field_ditches": [{"poly": [[300, 300], [500, 300]], "role": "main", "field": "f"}, {"poly": [[300, 600], [500, 600]], "role": "drain", "field": "f"}]}
    assert "field_ditches_reach_source_and_sink" in f(M)


def test_structures_clear_of_dry_plots_fires_when_a_farmstead_stands_on_a_hem_strip():
    # GM 2026-07: farmsteads (house + threshing yard) stood on Tango's fn1/nw1 dry hems - the
    # plots were guarded center-only, so a footprint could overlap a strip edge
    M = {"dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "barley", "theta": 0.5}], "houses": [{"x": 480, "y": 372, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]}
    assert "structures_clear_of_dry_plots" in f(M)


def test_structures_clear_of_dry_plots_passes_when_the_farmstead_abuts_the_strip():
    # abutting is fine (a hem may run right up to a wall) - only real overlap fires
    M = {"dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "barley", "theta": 0.5}], "houses": [{"x": 400, "y": 396, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]}
    assert "structures_clear_of_dry_plots" not in f(M)


def test_groves_clear_of_dry_plots_fires_when_a_clump_stands_in_the_crop():
    M = {
        "dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "soy", "theta": 1.2}],
        "village_groves": [{"role": "belt", "r": 11, "clumps": [[400, 340]], "poly": [[380, 320], [420, 320], [420, 360], [380, 360]]}],
    }
    assert "groves_clear_of_dry_plots" in f(M)


def test_groves_clear_of_dry_plots_passes_when_the_belt_hugs_the_edge():
    M = {
        "dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "soy", "theta": 1.2}],
        "village_groves": [{"role": "belt", "r": 11, "clumps": [[400, 396]], "poly": [[380, 384], [420, 384], [420, 408], [380, 408]]}],
    }
    assert "groves_clear_of_dry_plots" not in f(M)


def test_field_ditches_ground_via_the_moat():
    # a MOATED city's combs ground at the moat both ways: the supply taps it (frm=moat is a SOURCE -
    # it is a fed watercourse, per city_moat_irrigates_fields) and a collector may empty into it
    # (to=moat is a SINK - the moat is the city's storm drain). Added for Tango's comb-field port.
    M = {
        "field_ditches": [{"poly": [[300, 300], [500, 300]], "role": "main", "field": "f"}, {"poly": [[300, 600], [500, 600]], "role": "drain", "field": "f"}],
        "channels": [
            {"poly": [[290, 296], [304, 308]], "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "f"}, "w": 2.5},
            {"poly": [[494, 596], [520, 612]], "frm": {"kind": "drain"}, "to": {"kind": "moat"}, "w": 2.5},
        ],
    }
    assert "field_ditches_reach_source_and_sink" not in f(M)


def test_delivery_ditches_taper_fires_on_a_blunt_ditch():
    # a delivery ditch (role "branch") ending at nearly full width - it should have shed its water
    M = {"field_ditches": [{"poly": [[300, 300], [500, 500]], "role": "branch", "field": "f", "w": 4.0, "w_tail": 4.0}]}
    assert "delivery_ditches_taper" in f(M)


def test_delivery_ditches_taper_passes_when_it_narrows():
    M = {"field_ditches": [{"poly": [[300, 300], [500, 500]], "role": "branch", "field": "f", "w": 4.0, "w_tail": 1.5}]}
    assert "delivery_ditches_taper" not in f(M)


def test_delivery_ditches_taper_exempts_ditches_without_recorded_widths():
    # the older water_field engine records no head/tail width - nothing to judge, so it is skipped
    M = {"field_ditches": [{"poly": [[300, 300], [500, 500]], "role": "branch", "field": "f"}]}
    assert "delivery_ditches_taper" not in f(M)


def test_channels_join_not_cross_at_fork_fires_on_a_delivery_at_the_division():
    # a delivery (role "branch") taking off AT the fork - the 4-way star that reads as a crossroads
    M = {"field_ditches": _FORK_MAINS + [{"poly": [[100, 100], [140, 140]], "role": "branch", "field": "f", "w": 2.7, "w_tail": 1.0}]}
    assert "channels_join_not_cross_at_fork" in f(M)


def test_channels_join_not_cross_at_fork_passes_when_the_delivery_is_downstream():
    # the delivery branches off a supply canal 50px downstream of the fork - a clean offtake
    M = {"field_ditches": _FORK_MAINS + [{"poly": [[150, 100], [150, 145]], "role": "branch", "field": "f", "w": 2.7, "w_tail": 1.0}]}
    assert "channels_join_not_cross_at_fork" not in f(M)


def test_dry_plot_furrows_vary_fires_when_two_neighbours_share_an_angle():
    # 4 dry plots in a row; the first two are edge-adjacent AND run their furrows the same way -> fires
    dp = [_dryplot(300, 0.2), _dryplot(340, 0.2), _dryplot(380, 0.9), _dryplot(420, 0.4)]
    assert "dry_plot_furrows_vary" in f({"dry_plots": dp})


def test_dry_plot_furrows_vary_passes_when_neighbours_differ():
    # adjacent plots alternate orientation, so no neighboring pair shares a row direction
    dp = [_dryplot(300, 0.2), _dryplot(340, 0.9), _dryplot(380, 0.2), _dryplot(420, 0.9)]
    assert "dry_plot_furrows_vary" not in f({"dry_plots": dp})


def test_dry_plot_furrows_vary_skipped_for_a_contour_village():
    # a STEEP / terraced village declares contour furrows (meta.dry_furrows_vary=False) - the rows converge on
    # the contour for erosion control, so identical adjacent angles are CORRECT and the check does not fire
    dp = [_dryplot(300, 0.2), _dryplot(340, 0.2), _dryplot(380, 0.2), _dryplot(420, 0.2)]  # all aligned
    assert "dry_plot_furrows_vary" not in f({"meta": {"dry_furrows_vary": False}, "dry_plots": dp})


# ---- dry_plot_seams_shared (hem seams are single straight lines both quads lie on) -----------
def test_dry_plot_seams_shared_fires_on_a_lap():
    # the concave-bend failure: the second column's quad laps 2 px into its neighbor
    a = {"poly": [[300, 300], [346, 300], [346, 336], [300, 336]], "theta": 0.2}
    b = {"poly": [[344, 300], [390, 302], [390, 338], [344, 336]], "theta": 0.9}
    assert "dry_plot_seams_shared" in f({"dry_plots": [a, b]})


def test_dry_plot_seams_shared_fires_on_a_gap_wedge():
    # the convex-bend failure: both columns share the base corner at (346,300) but the second's
    # side edge tilts 6 px off the first's over its depth - a bare wedge opens between them
    a = {"poly": [[300, 300], [346, 300], [346, 380], [300, 380]], "theta": 0.2}
    b = {"poly": [[346, 300], [392, 300], [398, 380], [352, 380]], "theta": 0.9}
    assert "dry_plot_seams_shared" in f({"dry_plots": [a, b]})


def test_dry_plot_seams_shared_passes_a_shared_seam_with_a_depth_step():
    # clean abutment: one straight seam at x=346, the second column shallower - the ragged outer
    # edge steps ALONG the shared line, which is exactly the raggedness the generator intends
    a = {"poly": [[300, 300], [346, 300], [346, 380], [300, 380]], "theta": 0.2}
    b = {"poly": [[346, 300], [392, 300], [392, 350], [346, 350]], "theta": 0.9}
    assert "dry_plot_seams_shared" not in f({"dry_plots": [a, b]})


def test_dry_plot_seams_shared_skips_singletons_and_separated_plots():
    # one plot has no seams; two plots a field apart never meet (the bbox prefilter path)
    a = {"poly": [[300, 300], [346, 300], [346, 380], [300, 380]], "theta": 0.2}
    c = {"poly": [[900, 300], [946, 300], [946, 380], [900, 380]], "theta": 0.9}
    assert "dry_plot_seams_shared" not in f({"dry_plots": [a]})
    assert "dry_plot_seams_shared" not in f({"dry_plots": [a, c]})


def test_channel_source_anchored_fires_on_bad_anchor():
    M = {"channels": [{"poly": [[100, 100], [110, 120], [120, 140]], "frm": {"kind": "bogus"}, "to": {"kind": "offmap"}}]}
    assert "channel_source_anchored[0]" in f(M)


def test_field_supply_visibly_sourced_fires_on_a_dangling_comb_origin():
    # origin (450,250): 150px from the stream, far from every view edge; the only drawn stroke
    # is nowhere near the origin, so it cannot rescue it
    assert "field_supply_visibly_sourced[x]" in f(_supply_M([450, 250], drawn_channels=[{"pts": [[900, 900], [950, 950]]}]))


def test_field_supply_visibly_sourced_passes_on_a_moat_bank():
    # a comb origin on the moat bed is sourced (the moat-fed city-comb pattern)
    M = _supply_M([450, 110])
    M["streams"] = []
    M["moat"] = [[100, 100], [800, 100], [800, 105]]
    M["moat_width"] = 26
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_supply_visibly_sourced_passes_on_a_pond_rim():
    # a comb origin inside/on the pond ellipse is sourced (Tango's in-wall nw1 comb)
    M = _supply_M([450, 250])
    M["pond"] = [455, 255, 30, 20]
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_ditch_tips_land_on_the_trunk_fires_on_a_tip_past_the_canal():
    # both tips 6px BEYOND the trunk centerline: inside near_any's 13px net (so field_ditches_terminate
    # is happy) but 3.5px outside the trunk's drawn band, so a stub shows through
    assert "field_ditch_tips_land_on_the_trunk" in f(_tips_M([[100, 256], [100, 94]]))


def test_field_ditch_tips_land_on_the_trunk_passes_on_a_tip_in_the_band():
    # tips 1px off the centerline - buried under the trunks' own strokes, a clean T at each end
    assert "field_ditch_tips_land_on_the_trunk" not in f(_tips_M([[100, 249], [100, 101]]))


def test_water_channels_join_not_cross_fires_on_a_stub_through_the_trunk():
    # the vertical stroke crosses the trunk and stops 6px past it; the trunk's own nearest end is
    # 100px away, so NEITHER tip is buried in the other's band -> it reads as a 4-way intersection.
    # The third stroke is far off in the corner (the bbox-reject path).
    M = _cross_M(
        {"pts": [[0, 100], [200, 100]], "w0": 5, "w1": 5},
        {"pts": [[100, 150], [100, 94]], "w0": 3, "w1": 3},
        {"pts": [[380, 380], [390, 390]], "w0": 3, "w1": 3},
    )
    assert "water_channels_join_not_cross" in f(M)


def test_water_channels_join_not_cross_passes_on_a_shallow_offtake():
    # a delivery taking off at a shallow angle overruns the crossing along its OWN line by ~40px,
    # yet its tip stays 1px off the trunk centerline - under the ink, a clean Y. The second pair
    # (widths defaulted, bboxes overlapping but never crossing) exercises the no-crossing path.
    M = _cross_M(
        {"pts": [[0, 100], [200, 100]], "w0": 5, "w1": 5},
        {"pts": [[150, 140], [50, 99]], "w0": 3, "w1": 3},
        {"pts": [[10, 200], [190, 200]]},
    )
    assert "water_channels_join_not_cross" not in f(M)


def test_field_supply_visibly_sourced_passes_on_a_river_bank():
    # a comb origin sitting directly on a RIVER bed is sourced (Nagahara's far-bank fan pattern)
    M = _supply_M([450, 110])
    M["streams"] = []
    M["river"] = {"pts": [[100, 100], [800, 100]], "w": 40}
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_supply_visibly_sourced_passes_on_a_cargo_canal():
    # a comb origin on a cargo-canal bank is sourced (a Lion-lands water-town form)
    M = _supply_M([450, 104])
    M["streams"] = []
    M["canals"] = [{"poly": [[100, 100], [800, 100]], "w": 12}]
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_supply_visibly_sourced_passes_on_a_cascade_ditch():
    # tail-water reuse: the origin sits on ANOTHER comb's ditch (the standard way a city's
    # drainage waters the fields below it - Hirameki's e2 pattern)
    M = _supply_M([450, 250])
    M["field_ditches"].append({"poly": [[300, 248], [600, 252]], "role": "drain", "field": "other", "w": 4})
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_supply_visibly_sourced_skips_a_field_with_no_mains():
    # no main ditches recorded for the fed field -> nothing visible starts anywhere; not this check's call
    M = _supply_M([450, 250])
    M["field_ditches"] = []
    assert not any(c.startswith("field_supply_visibly_sourced") for c in f(M))


def test_field_supply_visibly_sourced_passes_with_a_drawn_tap():
    # a drawn tap stroke joins the origin to the stream bed - the visual chain is complete
    M = _supply_M([450, 250], drawn_channels=[{"pts": [[450, 104], [450, 250]]}])
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_supply_visibly_sourced_ignores_the_combs_own_canal():
    # the only drawn stroke at the origin is the comb's own main heading INTO the field - it
    # carries water downstream, not from a source, so the origin still dangles
    M = _supply_M([450, 250], drawn_channels=[{"pts": [[450, 250], [450, 320], [460, 400]]}])
    assert "field_supply_visibly_sourced[x]" in f(M)


def test_field_supply_visibly_sourced_passes_at_the_view_edge():
    # an origin at the map edge is presumed to continue off-map (the fn1/fn2 pattern)
    assert "field_supply_visibly_sourced[x]" not in f(_supply_M([450, 20]))


def test_field_supply_visibly_sourced_skips_a_drawn_supply_channel():
    # a DRAWN supply channel carries its own visual continuity (its ends are anchor-checked)
    assert "field_supply_visibly_sourced[x]" not in f(_supply_M([450, 250], drawn=True))


def test_streams_avoid_fields_fires():
    M = {"fields": [_field("f", 100, 100, 400, 400)], "streams": [{"poly": [[200, 200], [200, 500]]}]}  # first point sits inside the field
    assert "streams_avoid_fields" in f(M)


def test_streams_avoid_fields_allows_a_drain_fed_brook():
    # a brook anchored to the field's DRAIN starts at the outfall (inside the envelope) and runs off-map - legit
    M = {"fields": [_field("f", 100, 100, 400, 400)], "streams": [{"poly": [[300, 380], [300, 550], [300, 700]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}}]}
    assert "streams_avoid_fields" not in f(M)


def test_streams_avoid_fields_still_fires_when_a_drain_brook_reenters_the_field():
    # a drain-fed brook that leaves then CUTS BACK across the crop is still a defect
    M = {"fields": [_field("f", 100, 100, 400, 400)], "streams": [{"poly": [[300, 380], [300, 600], [250, 250]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}}]}  # last leg re-enters the field
    assert "streams_avoid_fields" in f(M)


def test_streams_avoid_fields_allows_a_stream_that_ends_at_the_field():
    # a stream anchored INTO the field (to=field) ends inside it - the connection is legitimate
    M = {
        "fields": [_field("f", 100, 100, 400, 400)],
        "streams": [{"poly": [[300, 700], [300, 500], [300, 300]], "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}}],
    }  # ends inside the field
    assert "streams_avoid_fields" not in f(M)


def test_fields_clear_of_road_fires():
    M = {"fields": [_field("f", 100, 100, 400, 400)], "road": [[50, 250], [500, 250]], "road_width": 26}
    assert "fields_clear_of_road" in f(M)


def test_commons_clear_of_paddies_fires_when_scrub_sits_in_a_field():
    # The check tests the DRAWN OUTCOME, not the patch's bbox CENTER (the scatter skips every paddy point by
    # construction, so a center-over-water test was only a proxy). It fires when a patch can clothe NOTHING:
    M = _nuc_village_M(_nuc_grid(), fields=[_field("p", 540, 540, 700, 700)])
    M["commons"] = [{"x": 600, "y": 600, "w": 60, "h": 60, "rot": 0, "poly": [[570, 570], [630, 570], [630, 630], [570, 630]]}]  # wholly inside the paddy -> draws nothing
    assert "commons_clear_of_paddies" in f(M)
    # ...but an INTERIOR FILL - the patch that clothes the voids an irregular field leaves inside its own bbox -
    # legitimately has its CENTER on the crop while every glyph it draws lands in the open ground around it.
    # Scoring the center failed this correct patch, which is why the rule changed (GM, 2026-07: Akagahara's fan
    # void rendered as bare clay because nothing was allowed to cover it).
    fill = _nuc_village_M(_nuc_grid(), fields=[_field("p", 540, 540, 700, 700)])
    fill["commons"] = [{"x": 600, "y": 600, "w": 400, "h": 400, "rot": 0, "poly": [[400, 400], [800, 400], [800, 800], [400, 800]]}]
    assert "commons_clear_of_paddies" not in f(fill)
    # a patch with no recorded polygon is skipped rather than crashing
    nopoly = _nuc_village_M(_nuc_grid(), fields=[_field("p", 540, 540, 700, 700)])
    nopoly["commons"] = [{"x": 600, "y": 600, "w": 60, "h": 60, "rot": 0}]
    assert "commons_clear_of_paddies" not in f(nopoly)


def test_commons_beyond_the_windbreak_fires_when_between_grove_and_village():
    houses, ccx, ccy, M = _nuc_with_windbreak()
    M["commons"] = [{"x": ccx - 70, "y": ccy - 70, "w": 80, "h": 200, "rot": 0}]  # NOT past the grove
    assert "commons_beyond_the_windbreak" in f(M)


def test_commons_beyond_the_windbreak_passes_when_past_the_grove():
    houses, ccx, ccy, M = _nuc_with_windbreak()
    M["commons"] = [{"x": ccx - 280, "y": ccy - 280, "w": 80, "h": 200, "rot": 0}]  # well beyond the belt
    assert "commons_beyond_the_windbreak" not in f(M)


def test_commons_beyond_the_windbreak_exempts_general_hinterland_land():
    # the general marginal hill land types - 'grazing' scrub, open 'pasture', coppice 'woodland' - are the
    # hinterland catena (any dry flank), NOT the windward fuel commons, so each is exempt even when NOT beyond
    # the windbreak; only the default fuel/fodder commons follows the toposequence rule.
    for role in ("grazing", "pasture", "woodland"):
        houses, ccx, ccy, M = _nuc_with_windbreak()
        M["commons"] = [{"x": ccx - 70, "y": ccy - 70, "w": 80, "h": 200, "rot": 0, "role": role}]
        assert "commons_beyond_the_windbreak" not in f(M)


def test_commons_beyond_check_skipped_without_a_windbreak():
    # nucleated + commons but NO windbreak grove -> the beyond-the-windbreak check cannot run (wbs empty)
    M = _nuc_village_M(_nuc_grid())
    M["commons"] = [{"x": 100, "y": 100, "w": 60, "h": 60, "rot": 0}]
    assert "commons_beyond_the_windbreak" not in f(M)


def test_woodland_clear_of_crops_fires_on_overlap_and_shade_passes_when_set_back_north():
    # a managed-woodland patch must NOT overlap a crop NOR shade it from the sunny SOUTH side (trees cast
    # shadows north, maps are north-up); a patch set back to the NORTH is fine. Covers paddy + dry_plots.
    p = _field("p", 400, 400, 700, 600)
    base = {"meta": {"scale": "village"}, "fields": [p]}

    def wood(poly):
        cx = sum(v[0] for v in poly) / len(poly)
        cy = sum(v[1] for v in poly) / len(poly)
        return {"x": cx, "y": cy, "w": 100, "h": 100, "rot": 0, "role": "woodland", "poly": poly}

    over = {**base, "commons": [wood([[500, 450], [600, 450], [600, 550], [500, 550]])]}  # sits ON the paddy
    assert "woodland_clear_of_crops" in f(over)
    shade = {**base, "commons": [wood([[500, 612], [640, 612], [640, 660], [500, 660]])]}  # just SOUTH -> shades it
    assert "woodland_clear_of_crops" in f(shade)
    ok = {**base, "commons": [wood([[500, 300], [640, 300], [640, 344], [500, 344]])]}  # well NORTH -> clear
    assert "woodland_clear_of_crops" not in f(ok)
    dry = {
        **base,
        "dry_plots": [{"poly": [[800, 400], [900, 400], [900, 500], [800, 500]], "crop": "soy", "theta": 0.0}],
        "commons": [wood([[840, 420], [940, 420], [940, 520], [840, 520]])],
    }  # overlaps a DRY plot
    assert "woodland_clear_of_crops" in f(dry)


def test_woodland_clear_of_grove_fires_when_on_the_fengshui_grove():
    # a coppice woodland patch and the protected fengshui grove are DISTINCT woods - a patch sitting on a grove
    # clump fires; one on its own ground does not.
    p = _field("p", 400, 400, 700, 600)
    patch = {"x": 200, "y": 200, "w": 100, "h": 100, "rot": 0, "role": "woodland", "poly": [[150, 150], [250, 150], [250, 250], [150, 250]]}
    base = {"meta": {"scale": "village"}, "fields": [p], "commons": [patch]}
    on = {**base, "village_groves": [{"role": "windbreak", "x": 200, "y": 200, "r": 14, "clumps": [[200, 200]]}]}  # clump inside the patch
    assert "woodland_clear_of_grove" in f(on)
    off = {**base, "village_groves": [{"role": "windbreak", "x": 900, "y": 900, "r": 14, "clumps": [[900, 900]]}]}  # grove far away
    assert "woodland_clear_of_grove" not in f(off)


def test_farmhouse_sizes_vary_fires_when_flat():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(300 + 60 * i, 300) for i in range(12)]}
    assert "farmhouse_sizes_vary" in f(M)  # _farmhouse has no wealth -> all at the baseline tier


def test_farmhouse_sizes_vary_passes_with_a_spread():
    houses = []
    for i in range(12):
        h = _farmhouse(300 + 60 * i, 300)
        h["wealth"] = 0.9 if i % 3 == 0 else (1.12 if i % 3 == 1 else 1.0)
        houses.append(h)
    assert "farmhouse_sizes_vary" not in f({"meta": {"scale": "village"}, "houses": houses})


# --- labels_render_on_top (label text is never covered) ---
def test_labels_render_on_top_fires_when_a_kido_covers_a_label():
    M = {"labels": [[100, 100, 300, 120, 5, "Ministry of Retainers"]], "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_fires_when_a_gate_structure_covers_a_label():
    M = {"labels": [[150, 100, 250, 120, 5, "gate label"]], "gate_structs": [{"x": 200, "y": 110, "w": 100, "h": 40, "z": 1000}]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_fires_when_a_torii_covers_a_label():
    M = {"labels": [[185, 95, 215, 120, 5, "shrine"]], "torii": [[200, 110, 1000]]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_passes_when_the_label_is_above():
    # same overlap, but the label's draw-z is higher than the structure's - it renders on top, readable
    M = {"labels": [[100, 100, 300, 120, 9999, "Ministry of Retainers"]], "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}]}
    assert "labels_render_on_top" not in f(M)


def test_labels_render_on_top_handles_a_textless_label():
    M = {
        "labels": [[150, 100, 250, 120, 5]],  # a field label recorded without text
        "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}],
    }
    assert "labels_render_on_top" in f(M)


def test_funerary_clear_of_fields_fires_when_a_cremation_ground_sits_on_a_field():
    # GM 2026-07 (Nagahara): a cremation ground on the far-bank comb's crop + ditch
    field = [{"name": "fe1", "kind": "paddy", "outline": [[300, 300], [700, 300], [700, 700], [300, 700]], "bbox": [300, 300, 700, 700]}]
    fire = {"fields": field, "cremation_grounds": [{"x": 500, "y": 500, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_clear_of_fields" in f(fire)
    ok = {"fields": field, "cremation_grounds": [{"x": 500, "y": 850, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_clear_of_fields" not in f(ok)


def test_settlement_has_cemetery_fires_when_missing():
    assert "settlement_has_cemetery" in f(_dead("village", []))


def test_settlement_has_cemetery_exempts_hamlet():
    assert "settlement_has_cemetery" not in f(_dead("hamlet", []))


def test_settlement_has_cemetery_passes_when_present():
    assert "settlement_has_cemetery" not in f(_dead("village", [{"x": 300, "y": 300, "w": 80, "h": 56, "rot": 0}]))


def test_cemetery_clear_of_shrine_fires_when_on_the_hall():
    # graves fill the shrine's YARD but never sit ON the sacred hall itself (this grave overlaps it)
    assert "cemetery_clear_of_shrine" in f(_dead("village", [{"x": 540, "y": 520, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_cemetery_clear_of_shrine_passes_when_off_the_hall():
    assert "cemetery_clear_of_shrine" not in f(_dead("village", [{"x": 900, "y": 900, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_cemetery_clear_of_shrine_allows_a_grave_in_the_precinct():
    # NEW (L7R): the shrine is Shinseist and its monk tends the dead, so a grave NEAR the shrine (in the yard,
    # off the hall) is FINE - the old kegare-distance rule is gone; only the sacred hall + torii stay clear
    M = {
        "meta": {"scale": "village"},
        "cemeteries": [{"x": 615, "y": 500, "w": 80, "h": 56, "rot": 0}],
        "religious": _SHR,
    }  # 115px from the shrine center (old rule would fire) but clear of the hall's east edge
    assert "cemetery_clear_of_shrine" not in f(M)


def test_cemetery_clear_of_shrine_fires_on_a_grave_under_the_torii():
    # the sacred GATEWAY stays clear too - a grave on the torii arch fires (hall placed far off, so it is the torii)
    M = {
        "meta": {"scale": "village"},
        "cemeteries": [{"x": 500, "y": 504, "w": 60, "h": 40, "rot": 0}],
        "religious": [{"kind": "shrine", "x": 500, "y": 760, "w": 30, "h": 24}],
        "torii": [[500, 500, 1]],
    }
    assert "cemetery_clear_of_shrine" in f(M)


def test_village_graveyard_by_shrine_fires_when_set_apart():
    # L7R: the village shrine's monk performs the funerary rites, so the graveyard sits in its precinct
    assert "village_graveyard_by_shrine" in f(_dead("village", [{"x": 1200, "y": 1200, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_village_graveyard_by_shrine_passes_when_in_precinct():
    assert "village_graveyard_by_shrine" not in f(_dead("village", [{"x": 640, "y": 500, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_village_graveyard_by_shrine_exempts_a_hilltop_shrine():
    # a hilltop shrine is exempt (graves do not climb the sacred hill); with no flat shrine the ground is by-eye
    M = _dead("village", [{"x": 1200, "y": 1200, "w": 80, "h": 56, "rot": 0}], religious=[{"kind": "shrine", "x": 500, "y": 500, "w": 100, "h": 68}])
    M["hill"] = [500, 500, 200, 150]
    assert "village_graveyard_by_shrine" not in f(M)


def test_cemetery_in_temple_precinct_fires_when_far_from_hall():
    assert "cemetery_in_temple_precinct" in f(_dead("town", [{"x": 1500, "y": 1500, "w": 80, "h": 56, "rot": 0}], religious=_MON))


def test_cemetery_in_temple_precinct_passes_when_by_hall():
    assert "cemetery_in_temple_precinct" not in f(_dead("town", [{"x": 560, "y": 520, "w": 80, "h": 56, "rot": 0}], religious=_MON))


def test_cemetery_clear_of_shrine_fires_on_a_mausoleum_on_the_hall():
    # the off-the-hall rule covers MAUSOLEA too, not just graveyards (this one overlaps the shrine hall)
    M = {"meta": {"scale": "village"}, "mausoleums": [{"x": 540, "y": 520, "w": 74, "h": 58, "rot": 0}], "religious": [{"kind": "shrine", "x": 500, "y": 500, "w": 100, "h": 68}]}
    assert "cemetery_clear_of_shrine" in f(M)


def test_city_graveyard_count_fires_when_too_few():
    assert "city_graveyard_count" in f(_city_dead(cems=[(300, 300)]))


def test_city_graveyard_count_fires_when_too_many():
    assert "city_graveyard_count" in f(_city_dead(cems=[(300, 300), (350, 300), (400, 300), (700, 300), (100, 100)]))


def test_city_graveyard_count_passes_at_three():
    assert "city_graveyard_count" not in f(_city_dead())


def test_walled_graveyards_inside_and_outside_fires_when_all_inside():
    assert "walled_graveyards_inside_and_outside" in f(_city_dead(cems=[(300, 300), (700, 300)]))


def test_walled_graveyards_inside_and_outside_passes_when_mixed():
    assert "walled_graveyards_inside_and_outside" not in f(_city_dead())


def test_walled_exterior_cemetery_larger_fires_when_not_larger():
    # the outside common ground is no bigger than the cramped intramural one
    assert "walled_exterior_cemetery_larger" in f(_city_dead(cems=[(300, 300), (700, 300), (100, 100, 60, 40)]))


def test_walled_exterior_cemetery_larger_passes_when_larger():
    assert "walled_exterior_cemetery_larger" not in f(_city_dead())


def test_cemetery_in_temple_precinct_exempts_a_nonparish_grave():
    # an inside graveyard far from any temple is exempt when parish=False (a non-parish plot)
    assert "cemetery_in_temple_precinct" not in f(_city_dead(cems=[(300, 300), (700, 300), (100, 100), (500, 500, 60, 44, False)]))


def test_cemetery_in_temple_precinct_fires_on_an_inside_parish_grave_off_temple():
    assert "cemetery_in_temple_precinct" in f(_city_dead(cems=[(300, 300), (700, 300), (100, 100), (500, 500, 60, 44, True)]))


def test_funerary_set_back_from_water_fires_near_a_stream():
    assert "funerary_set_back_from_water" in f(_water_grave({"streams": [{"poly": [[300, 340], [600, 340]], "frm": None, "to": None, "w": 9}]}))


def test_funerary_set_back_from_water_fires_near_a_pond():
    assert "funerary_set_back_from_water" in f(_water_grave({"pond": [400, 300, 60, 40]}))


def test_funerary_set_back_from_water_passes_when_clear_of_water():
    assert "funerary_set_back_from_water" not in f(_water_grave({"streams": [{"poly": [[300, 600], [600, 600]], "frm": None, "to": None, "w": 9}], "pond": [900, 900, 60, 40]}))


def test_funerary_set_back_scales_grave_ok_by_a_stream_fails_by_a_moat():
    # a graveyard whose nearest corner is 90px from the watercourse: fine by a narrow stream (floor 75),
    # too close to a moat (set-back 110)
    def M(width):
        return {
            "meta": {"scale": "village"},
            "cemeteries": [{"x": 300, "y": 270, "w": 50, "h": 36, "rot": 0, "parish": True}],
            "streams": [{"poly": [[200, 378], [600, 378]], "frm": None, "to": None, "w": width}],
        }

    assert "funerary_set_back_from_water" not in f(M(6))  # narrow stream: floor 75, corner 90px away -> ok
    assert "funerary_set_back_from_water" in f(M(22))  # moat-width: set-back 110 -> 90px too close


def test_funerary_set_back_cremation_may_sit_nearer_than_a_grave():
    # at the SAME 50px corner distance from a wide watercourse: the cremation ground passes, a graveyard fires
    base = {"meta": {"scale": "village"}, "streams": [{"poly": [[200, 378], [600, 378]], "frm": None, "to": None, "w": 22}]}
    grave = {**base, "cemeteries": [{"x": 300, "y": 310, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    crem = {**base, "cremation_grounds": [{"x": 300, "y": 288, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_set_back_from_water" in f(grave)
    assert "funerary_set_back_from_water" not in f(crem)


def test_funerary_set_back_inside_wall_grave_exempt_from_moat():
    # a graveyard just inside the wall is shielded from the (outside) moat by the rampart -> exempt
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]
    M = {"meta": {"scale": "city"}, "wall": WALLSQ, "moat": _MOAT, "moat_width": 22, "cemeteries": [{"x": 230, "y": 500, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" not in f(M)


def test_funerary_set_back_outside_wall_grave_subject_to_moat():
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]
    M = {"meta": {"scale": "city"}, "wall": WALLSQ, "moat": _MOAT, "moat_width": 22, "cemeteries": [{"x": 120, "y": 500, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" in f(M)


def test_funerary_set_back_fires_near_a_rice_paddy():
    # a burial ground hard against a flood-prone paddy edge
    M = {"meta": {"scale": "village"}, "fields": [_PADDY], "cemeteries": [{"x": 300, "y": 300, "w": 50, "h": 36, "rot": 0, "parish": True}]}
    assert "funerary_set_back_from_water" in f(M)


def test_funerary_set_back_paddy_needs_more_than_creek_distance():
    # ~35px from a paddy edge: fine for a creek, but a flooded paddy needs a real margin -> still fires
    near = {"meta": {"scale": "village"}, "fields": [_PADDY], "cemeteries": [{"x": 300, "y": 277, "w": 50, "h": 36, "rot": 0, "parish": True}]}  # corner ~35px from the paddy
    assert "funerary_set_back_from_water" in f(near)
    far = {"meta": {"scale": "village"}, "fields": [_PADDY], "cemeteries": [{"x": 300, "y": 255, "w": 50, "h": 36, "rot": 0, "parish": True}]}  # corner ~57px -> clear
    assert "funerary_set_back_from_water" not in f(far)


def test_funerary_set_back_cremation_may_sit_by_a_paddy():
    # the cremation ground is exempt from the paddy set-back (a fire site, not flood-sensitive graves)
    M = {"meta": {"scale": "village"}, "fields": [_PADDY], "cremation_grounds": [{"x": 300, "y": 280, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_set_back_from_water" not in f(M)


def test_cremation_ground_by_external_cemetery_passes_when_adjacent():
    assert "cremation_ground_by_external_cemetery" not in f(_crem_cem((300, 300), (300, 420)))


def test_cremation_ground_by_external_cemetery_fires_when_far():
    assert "cremation_ground_by_external_cemetery" in f(_crem_cem((300, 300), (900, 900)))


def test_cremation_ground_by_external_cemetery_fires_when_only_internal_cemetery():
    # walled: cremation outside, but the only cemetery is INSIDE the wall (even adjacent) -> not external -> fires
    assert "cremation_ground_by_external_cemetery" in f(_crem_cem((150, 500), (250, 500), walled=True))


def test_cremation_ground_by_external_cemetery_passes_walled_with_external():
    # walled: cremation + cemetery both outside the wall, adjacent -> ok
    assert "cremation_ground_by_external_cemetery" not in f(_crem_cem((150, 500), (150, 620), walled=True))


def test_cremation_set_back_from_road_fires_when_on_the_road():
    assert "cremation_ground_set_back_from_main_road" in f(_crem_road((300, 260), (300, 360)))  # 60px off the road


def test_cremation_set_back_from_road_passes_when_far():
    assert "cremation_ground_set_back_from_main_road" not in f(_crem_road((300, 500), (300, 600)))


def test_cremation_set_back_from_road_passes_when_no_main_road():
    M = _crem_road((300, 260), (300, 360))
    del M["road"]  # a settlement on minor streets only - nothing to be set back from
    assert "cremation_ground_set_back_from_main_road" not in f(M)


def test_cremation_not_between_temple_and_road_fires_when_between():
    # cremation on the road side of its monastery (closer to the road than the temple), yet still
    # clear of the road's own set-back floor - only the between-temple-and-road rule should object
    fails = f(_crem_temple((300, 360)))
    assert "cremation_ground_not_between_temple_and_road" in fails
    assert "cremation_ground_set_back_from_main_road" not in fails  # isolates the new rule


def test_cremation_not_between_temple_and_road_passes_when_behind():
    assert "cremation_ground_not_between_temple_and_road" not in f(_crem_temple((300, 640)))


def test_cremation_not_between_temple_and_road_passes_when_no_temple_nearby():
    # no temple within association range -> nothing to be "in front of"
    assert "cremation_ground_not_between_temple_and_road" not in f(_crem_temple((300, 360), mon_xy=(300, 1500)))


def test_city_temples_have_graveyards_fires_when_a_temple_unserved():
    assert "city_temples_have_graveyards" in f(_city_dead(temples=[(320, 320, "A", True), (680, 700, "B", True)]))


def test_city_temples_have_graveyards_exempts_a_flagged_temple():
    assert "city_temples_have_graveyards" not in f(_city_dead(temples=[(320, 320, "A", True), (680, 700, "B", False)]))


def test_city_has_mausoleum_fires_when_missing():
    assert "city_has_mausoleum" in f(_city_dead(maus=[]))


def test_city_has_mausoleum_fires_when_outside_walls():
    assert "city_has_mausoleum" in f(_city_dead(maus=[(100, 100)]))


def test_city_has_mausoleum_fires_when_far_from_quarter():
    assert "city_has_mausoleum" in f(_city_dead(maus=[(260, 740)], gov=(740, 260)))


def test_city_has_mausoleum_passes_when_by_quarter():
    assert "city_has_mausoleum" not in f(_city_dead())


def test_city_has_cremation_ground_fires_when_inside_walls():
    assert "city_has_cremation_ground" in f(_city_dead(crem=[(500, 400)]))


def test_city_has_cremation_ground_passes_when_outside():
    assert "city_has_cremation_ground" not in f(_city_dead())


def test_city_has_ossuary_fires_when_far_from_cremation():
    assert "city_has_ossuary" in f(_city_dead(oss=[(900, 100)]))


def test_city_has_ossuary_passes_when_by_cremation():
    assert "city_has_ossuary" not in f(_city_dead())


def test_town_has_cremation_ground_fires_when_missing():
    assert "town_has_cremation_ground" in f(_town_dead([]))


def test_town_has_cremation_ground_fires_when_among_dwellings():
    assert "town_has_cremation_ground" in f(_town_dead([(320, 300)]))


def test_town_has_cremation_ground_passes_when_at_the_edge():
    assert "town_has_cremation_ground" not in f(_town_dead([(900, 900)]))


def test_sacred_and_graves_off_marsh_fires_and_passes_on_dry_ground():
    # a shrine hall or a graveyard must NOT sit on a reed marsh (the wet valley toe) - only on dry ground.
    marsh = [[400, 400], [700, 400], [700, 700], [400, 700]]  # a toe marsh
    base = {"meta": {"scale": "village"}, "houses": [bldg(200, 200, "laborer")], "marshes": [{"x": 550, "y": 550, "w": 300, "h": 300, "role": "toe", "poly": marsh}]}
    on_shrine = {**base, "religious": [{"x": 550, "y": 550, "w": 96, "h": 64, "kind": "shrine"}]}
    assert "sacred_and_graves_off_marsh" in f(on_shrine)
    on_grave = {**base, "cemeteries": [{"x": 560, "y": 560, "w": 82, "h": 58, "rot": 0}]}
    assert "sacred_and_graves_off_marsh" in f(on_grave)
    dry = {**base, "religious": [{"x": 900, "y": 900, "w": 96, "h": 64, "kind": "shrine"}], "cemeteries": [{"x": 1000, "y": 1000, "w": 82, "h": 58, "rot": 0}]}
    assert "sacred_and_graves_off_marsh" not in f(dry)
    # a pond_fringe (thin decorative shore ring) is exempt - a shrine may sit beside a pond
    fringe = {**base, "marshes": [{"x": 550, "y": 550, "w": 300, "h": 300, "role": "pond_fringe", "poly": marsh}], "religious": [{"x": 550, "y": 550, "w": 96, "h": 64, "kind": "shrine"}]}
    assert "sacred_and_graves_off_marsh" not in f(fringe)


# ---- channel_source_anchored: a channel that claims a FOREST source ------------------------
# A watercourse anchor of kind "forest" is grounded iff a forest polygon exists AND the anchor
# point lies inside it. A channel declaring a forest source whose tap sits OUTSIDE the drawn
# forest is ungrounded and must fire (exercises the forest branch of anchored()).
def test_channel_source_anchored_fires_when_forest_tap_is_outside_the_forest():
    M = {
        "forest": [[100, 100], [300, 100], [300, 300], [100, 300]],
        "channels": [{"poly": [[500, 500], [510, 400], [520, 300]], "frm": {"kind": "forest"}, "to": {"kind": "offmap"}}],
    }
    assert "channel_source_anchored[0]" in f(M)


# ---- roads_clear_of_marsh / pond_clear_of_paddies / no_structure_on_paddy (GM, Hoshizora 2026-07) ----
def test_roads_clear_of_marsh_fires_when_the_road_runs_through_a_reed_fringe():
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "marshes": [{"x": 500, "y": 500, "w": 120, "h": 80, "poly": [[440, 460], [560, 460], [560, 540], [440, 540]]}]}
    assert "roads_clear_of_marsh" in f(M)


def test_roads_clear_of_marsh_passes_when_the_marsh_sits_off_the_road():
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "marshes": [{"x": 500, "y": 700, "w": 120, "h": 80, "poly": [[440, 660], [560, 660], [560, 740], [440, 740]]}]}
    assert "roads_clear_of_marsh" not in f(M)


def test_pond_clear_of_paddies_fires_when_the_pond_laps_the_crop():
    M = {"meta": {}, "pond": [320, 320, 80, 60], "fields": [_paddy_field_rec()]}
    assert "pond_clear_of_paddies" in f(M)


def test_pond_clear_of_paddies_passes_when_the_pond_sits_beside_the_crop():
    M = {"meta": {}, "pond": [120, 120, 60, 40], "fields": [_paddy_field_rec()]}
    assert "pond_clear_of_paddies" not in f(M)


def test_roads_clear_of_marsh_skips_a_degenerate_marsh_poly():
    # a marsh record whose poly is a bare 2-point sliver carries no area to test - skipped, no crash
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "marshes": [{"x": 500, "y": 500, "w": 10, "h": 10, "poly": [[490, 495], [510, 505]]}]}
    assert "roads_clear_of_marsh" not in f(M)


def test_roads_clear_of_marsh_exempts_a_defense_belt_causeway():
    # the approach road CROSSES the defensive wet belt on a causeway (the renderer keeps the tread bare via
    # the corridor skip) - few, constricted approaches are the belt's military purpose, not a placement error
    M = {"meta": {}, "road": [[100, 500], [900, 500]], "wall": WALL, "marshes": [{"x": 500, "y": 500, "w": 120, "h": 80, "role": "defense", "poly": [[440, 460], [560, 460], [560, 540], [440, 540]]}]}
    assert "roads_clear_of_marsh" not in f(M)


def test_town_monasteries_have_graveyards_fires_when_unserved():
    M = {"meta": {"scale": "town"}, "religious": [{"x": 500, "y": 500, "w": 100, "h": 70, "kind": "monastery"}]}
    assert "town_monasteries_have_graveyards" in f(M)


def test_town_monasteries_have_graveyards_passes_with_precinct_ground_or_opt_out():
    M = {"meta": {"scale": "town"}, "religious": [{"x": 500, "y": 500, "w": 100, "h": 70, "kind": "monastery"}], "cemeteries": [{"x": 560, "y": 420, "w": 80, "h": 60, "rot": 0}]}
    assert "town_monasteries_have_graveyards" not in f(M)
    M2 = {"meta": {"scale": "town"}, "religious": [{"x": 500, "y": 500, "w": 100, "h": 70, "kind": "monastery", "graveyard": False}]}
    assert "town_monasteries_have_graveyards" not in f(M2)


def test_town_has_ossuary_fires_when_missing():
    M = {"meta": {"scale": "town"}, "cremation_grounds": [{"x": 200, "y": 800, "w": 75, "h": 52, "rot": 0}]}
    assert "town_has_ossuary" in f(M)


def test_town_has_ossuary_passes_beside_the_cremation_ground():
    M = {"meta": {"scale": "town"}, "cremation_grounds": [{"x": 200, "y": 800, "w": 75, "h": 52, "rot": 0}], "ossuaries": [{"x": 260, "y": 860, "w": 20, "h": 20, "rot": 0}]}
    assert "town_has_ossuary" not in f(M)


def test_geometry_within_canvas_fires_on_a_stray_town_wall_vertex():
    M = {"meta": {"scale": "town", "W": 2000, "H": 1300}, "wall": [[300, 300], [9999999, 300], [700, 700]]}
    assert "geometry_within_canvas" in f(M)


# ---- dry_plots_off_hill (feature 013): a hill slope carries dry hill-crops/tea/woodland/scrub, never
# flooded paddy - and the near-ring dry-field tiler must not stray onto it either (no_field_on_hill
# reads only M["fields"], so this closes the dry-plot half).
def test_dry_plots_off_hill_fires_when_a_plot_sits_on_the_hill():
    M = {"meta": {"scale": "town"}, "hill": [500, 500, 200, 150], "dry_plots": [{"poly": [[480, 480], [520, 480], [520, 520], [480, 520]], "crop": "soy", "theta": 0.0}]}
    assert "dry_plots_off_hill" in f(M)


def test_dry_plots_off_hill_passes_when_plots_avoid_the_hill():
    M = {"meta": {"scale": "town"}, "hill": [500, 500, 200, 150], "dry_plots": [{"poly": [[50, 50], [90, 50], [90, 90], [50, 90]], "crop": "soy", "theta": 0.0}]}
    assert "dry_plots_off_hill" not in f(M)


# ---- comb_supply_commands_both_flanks (2026-08-16) -----------------------------------------------
# A gravity canal commands only ground BELOW it, so a comb fan planted on both sides of its
# bunsuiguchi fork must DRAW supply down both margins (research/water.md "The head-race forks -
# supply commands both flanks"). The check reads the `fork` build_comb records on the field.


def _both_flanks_manifest(arm_b=True, west_sliver=False):
    """A comb fan falling due south, fork at (500, 300): canal A inked down the east margin, plots
    on both flanks (or only a sliver on the west when `west_sliver`), canal B optional."""
    west_x = (460, 490) if west_sliver else (210, 260)
    fld = {
        "name": "f",
        "kind": "paddy",
        "down_deg": 90,
        "fork": [500.0, 300.0],
        "outline": [[200, 300], [800, 300], [800, 900], [200, 900]],
        "bbox": [200, 300, 800, 900],
        "plot_rings": [
            [[west_x[0], 340], [west_x[1], 340], [west_x[1], 390], [west_x[0], 390]],
            [[740, 340], [790, 340], [790, 390], [740, 390]],
            [[480, 600], [520, 600], [520, 640], [480, 640]],
        ],
    }
    ditches = [
        {"field": "f", "role": "main", "w": 7.0, "poly": [[500, 260], [500, 300]]},
        {"field": "f", "role": "main", "w": 6.0, "poly": [[500, 300], [700, 420], [790, 520]]},
        {"field": "f", "role": "drain", "w": 3.0, "poly": [[210, 880], [790, 880]]},
    ]
    if arm_b:
        ditches.append({"field": "f", "role": "main", "w": 5.6, "poly": [[500, 300], [350, 420], [290, 520]]})
    return manifest(fields=[fld], field_ditches=ditches)


def test_comb_supply_commands_both_flanks_fires_on_a_bare_flank():
    fails = check_village.gate(_both_flanks_manifest(arm_b=False), verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" in fails


def test_comb_supply_commands_both_flanks_passes_with_both_arms_inked():
    fails = check_village.gate(_both_flanks_manifest(arm_b=True), verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" not in fails


def test_comb_supply_commands_both_flanks_spares_a_sliver_flank():
    # under ~150 ft of paddy past the fork demands no second arm - a genuinely lopsided fan is honest
    fails = check_village.gate(_both_flanks_manifest(arm_b=False, west_sliver=True), verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" not in fails


def test_comb_supply_commands_both_flanks_skips_manifests_without_a_fork():
    # legacy manifests record no fork (conversion, not retrofit, is their fix - migration doctrine)
    M = _both_flanks_manifest(arm_b=False)
    del M["fields"][0]["fork"]
    fails = check_village.gate(M, verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" not in fails


def test_comb_supply_commands_both_flanks_skips_a_field_with_no_declared_fall():
    M = _both_flanks_manifest(arm_b=False)
    del M["fields"][0]["down_deg"]
    fails = check_village.gate(M, verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" not in fails


def test_comb_supply_commands_both_flanks_reads_the_map_fall_when_the_field_has_none():
    M = _both_flanks_manifest(arm_b=False)
    del M["fields"][0]["down_deg"]
    M["meta"]["down_deg"] = 90
    fails = check_village.gate(M, verbose=False, only={"comb_supply_commands_both_flanks"})
    assert "comb_supply_commands_both_flanks" in fails


# ---- woodland_commons_within_the_frame: a coppice the crop cuts off is drawn but not shown ----
def _wood_M(polys, view=(100, 100, 800, 800), gen="hamletgen", role="woodland"):
    M = {"meta": {"scale": "hamlet", "W": 1200, "H": 1200}, "commons": [{"role": role, "poly": p} for p in polys]}
    if view is not None:
        M["meta"]["view"] = list(view)
    if gen:
        M["meta"]["generated_by"] = gen
    return M


def _wood_f(M):
    return check_village.gate(M, verbose=False, only={"woodland_commons_within_the_frame"})


def test_woodland_commons_fires_on_a_parcel_wholly_outside_the_view():
    # the Sawada shape: seated above the kept window, drawn onto ground the crop discards
    assert "woodland_commons_within_the_frame" in _wood_f(_wood_M([[[0, 0], [50, 0], [50, 50], [0, 50]]]))


def test_woodland_commons_fires_on_a_parcel_mostly_outside_the_view():
    # half in, half out (50% < the 70% line): Sawada's third parcel, cropped under the title
    assert "woodland_commons_within_the_frame" in _wood_f(_wood_M([[[50, 200], [150, 200], [150, 300], [50, 300]]]))


def test_woodland_commons_passes_inside_the_view():
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[[200, 200], [400, 200], [400, 400], [200, 400]]]))


def test_woodland_commons_tolerates_a_parcel_clipping_at_the_edge():
    # 75% inside: a wood CLIPPING at the frame reads as "more wood that way", which is fine
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[[75, 200], [175, 200], [175, 300], [75, 300]]]))


def test_woodland_commons_ignores_the_grazing_bleed():
    # the grazing scrub deliberately bleeds off every edge - only woodland parcels are held
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[[0, 0], [50, 0], [50, 50], [0, 50]]], role="grazing"))


def test_woodland_commons_ignores_a_parcel_with_no_poly():
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[]]))


def test_woodland_commons_skips_an_uncropped_map():
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[[0, 0], [50, 0], [50, 50], [0, 50]]], view=None))


def test_woodland_commons_skips_legacy_maps():
    assert "woodland_commons_within_the_frame" not in _wood_f(_wood_M([[[0, 0], [50, 0], [50, 50], [0, 50]]], gen=None))


# ---- woodland_commons_on_dry_ground: a coppice does not stand in the marsh --------------------
def _wood_dry_M(polys, marsh=None, gen="hamletgen", role="woodland"):
    M = _wood_M(polys, view=(0, 0, 1200, 1200), gen=gen, role=role)
    if marsh is not None:
        M["marshes"] = [{"poly": marsh}]
    return M


_TOE_MARSH = [[0, 500], [600, 500], [600, 1100], [0, 1100]]


def _wood_dry_f(M):
    return check_village.gate(M, verbose=False, only={"woodland_commons_on_dry_ground"})


def test_woodland_dry_fires_on_a_parcel_wholly_in_the_marsh():
    # the Inashiro capture: 100% wet, zero crowns of ink - an empty rectangle claiming a woodland
    assert "woodland_commons_on_dry_ground" in _wood_dry_f(_wood_dry_M([[[100, 600], [350, 600], [350, 850], [100, 850]]], marsh=_TOE_MARSH))


def test_woodland_dry_fires_on_a_parcel_mostly_in_the_marsh():
    # straddling the marsh edge, ~60% wet (the Mizuguchi capture's degree)
    assert "woodland_commons_on_dry_ground" in _wood_dry_f(_wood_dry_M([[[100, 350], [350, 350], [350, 750], [100, 750]]], marsh=_TOE_MARSH))


def test_woodland_dry_tolerates_a_marsh_fringe():
    # ~20% wet: a stand may lap the haze a little without losing its read
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 300], [350, 300], [350, 550], [100, 550]]], marsh=_TOE_MARSH))


def test_woodland_dry_passes_on_dry_ground():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 100], [350, 100], [350, 350], [100, 350]]], marsh=_TOE_MARSH))


def test_woodland_dry_skips_a_map_with_no_marsh():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 600], [350, 600], [350, 850], [100, 850]]]))


def test_woodland_dry_ignores_a_degenerate_marsh_poly():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 600], [350, 600], [350, 850], [100, 850]]], marsh=[[0, 500], [600, 500]]))


def test_woodland_dry_ignores_the_grazing_bleed():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 600], [350, 600], [350, 850], [100, 850]]], marsh=_TOE_MARSH, role="grazing"))


def test_woodland_dry_ignores_a_parcel_with_no_poly():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[]], marsh=_TOE_MARSH))


def test_woodland_dry_skips_legacy_maps():
    assert "woodland_commons_on_dry_ground" not in _wood_dry_f(_wood_dry_M([[[100, 600], [350, 600], [350, 850], [100, 850]]], marsh=_TOE_MARSH, gen=None))
