"""Split from test_checks.py by feature 025 - see test_checks/CLAUDE.md for the index."""

import math

import pytest

import check_village
from tests.check_village._builders import _WHY, _farmhouse, _feature_022_manifest, _field, _waived_map, f


def test_torii_match_roll_fires_when_the_drawn_count_drifts_from_the_target():
    # the hall recorded a rolled/pinned target of 3 but only 1 arch is attributed to it
    M = {"meta": {"scale": "city"}, "religious": [{"kind": "temple", "label": "T", "x": 500, "y": 500, "w": 100, "h": 80, "torii_count": 3}], "torii": [[500, 560, 1]]}
    assert "torii_match_roll" in f(M)


def test_torii_match_roll_passes_on_match_and_skips_unrecorded_halls():
    # T matches its target; U has no recorded target (the village auto-shrine path) and is skipped
    M = {
        "meta": {"scale": "city"},
        "religious": [
            {"kind": "temple", "label": "T", "x": 500, "y": 500, "w": 100, "h": 80, "torii_count": 1},
            {"kind": "temple", "label": "U", "x": 900, "y": 900, "w": 100, "h": 80},
        ],
        "torii": [[500, 560, 1], [900, 950, 1]],
    }
    assert "torii_match_roll" not in f(M)


def test_taxfree_plots_not_required_when_absent():
    M = {"meta": {"scale": "village"}, "fields": [_field("f", 100, 100, 400, 400)], "houses": [_farmhouse(60, 250)]}
    assert "taxfree_plots_in_range" not in f(M)  # a village that does not denote them is fine


def test_taxfree_plots_range_validated_when_present():
    M = {"meta": {"scale": "village"}, "fields": [_field("f", 100, 100, 400, 400)], "houses": [_farmhouse(60, 250)], "taxfree": [[200, 200]]}  # 1 present, law wants 2-3
    assert "taxfree_plots_in_range" in f(M)


def test_torii_avenue_meets_the_hall_fires_on_a_sando_authored_away_from_its_temple():
    # GM 2026-07-27: the arches were spaced right and the whole run stood yards from the temple.
    # Here the hall's front edge is y540 and the avenue starts at y640 - 300 real ft out - while its
    # own arches stand 60 ft apart. An approach that does not reach its hall is not an approach.
    M = {
        "meta": {"scale": "city", "ftpx": 3},
        "religious": [{"kind": "temple", "label": "T", "x": 500, "y": 500, "w": 100, "h": 80, "torii_count": 3}],
        "torii": [[500, 640, 1], [500, 660, 1], [500, 680, 1]],
    }
    assert "torii_avenue_meets_the_hall" in f(M)


def test_torii_avenue_meets_the_hall_passes_when_the_gap_matches_the_pitch():
    # the same avenue seated one pitch off the hall's front (y540 + 20px) is exactly the rule
    M = {
        "meta": {"scale": "city", "ftpx": 3},
        "religious": [{"kind": "temple", "label": "T", "x": 500, "y": 500, "w": 100, "h": 80, "torii_count": 3}],
        "torii": [[500, 560, 1], [500, 580, 1], [500, 600, 1]],
    }
    assert "torii_avenue_meets_the_hall" not in f(M)


def test_torii_avenue_meets_the_hall_spares_the_villages_tighter_threshold():
    # an UPPER bound only: the village path seats its arches at 0.6-0.9 of its 30 ft stride, which
    # shrine_avenue_fronts_the_hall (GM 2026-07-22) already governs from the other side. The two
    # rules meet without either forcing churn on maps the GM has signed off.
    M = {
        "meta": {"scale": "village", "ftpx": 2},
        "religious": [{"kind": "shrine", "x": 500, "y": 500, "w": 30, "h": 20, "torii_count": 3}],
        "torii": [[500, 519, 1], [500, 534, 1], [500, 549, 1]],
    }
    assert "torii_avenue_meets_the_hall" not in f(M)


def test_temple_torii_face_the_street():
    """A temple within reach of a major way faces its torii avenue TOWARD it (GM 2026-08-09) -
    the sando exists so an approacher passes beneath the arches on the way in; arches on the
    far side put the gateway behind the temple (the capital's Jurojin marched its avenue away
    from the kagi-no-te road). No way in reach -> the hall faces where it will."""
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000},
        "road": [[100, 400], [900, 400]],
        "religious": [{"kind": "temple", "label": "T", "x": 500, "y": 500, "w": 50, "h": 33, "torii_count": 2}],
        "torii": [[500, 560, 1], [500, 590, 1]],  # arches marching AWAY from the road
    }
    assert "temple_torii_face_the_street" in f(M)
    M["torii"] = [[500, 445, 1], [500, 420, 1]]  # between hall and road - an approacher passes under
    assert "temple_torii_face_the_street" not in f(M)
    M["road"] = [[100, 60], [900, 60]]  # the way moves out of reach - the rule skips, it does not guess
    M["torii"] = [[500, 560, 1], [500, 590, 1]]
    assert "temple_torii_face_the_street" not in f(M)


# ---- dwellings must not sit in the WET low toe below the field's drainage ditch (feature 005 / GM 2026-07) ----


def test_contour_terraces_require_stepped_cross_slope_bands():
    # a field declared field_archetype=contour_terraces must show >=8 cross-slope terrace bunds; too few, or bunds
    # that run downhill (channels, not terrace lips), fires.
    base = {"meta": {"scale": "hamlet", "down_deg": 90, "field_archetype": "contour_terraces"}}
    good = {**base, "terrace_bunds": [*([[100, 200 + i * 80], [900, 200 + i * 80]] for i in range(10)), [[500, 900]]]}  # 10 wide E-W bands + a degenerate 1-pt bund (skipped)
    assert "contour_terraces_are_stepped_bands" not in f(good)
    few = {**base, "terrace_bunds": [[[100, 200 + i * 80], [900, 200 + i * 80]] for i in range(4)]}  # only 4
    assert "contour_terraces_are_stepped_bands" in f(few)
    downhill = {**base, "terrace_bunds": [[[100 + i * 40, 200], [100 + i * 40, 900]] for i in range(10)]}  # bunds run N-S (downhill)
    assert "contour_terraces_are_stepped_bands" in f(downhill)


def test_polder_field_must_fill_its_bbox():
    # a field declared field_archetype=polder_grid must FILL its bounding box (a surveyed rectangle); a fan-shaped
    # outline covering only a fraction of its bbox fires.
    base = {"meta": {"scale": "hamlet", "field_archetype": "polder_grid"}}
    rect = {**base, "fields": [{"name": "p", "kind": "paddy", "outline": [[100, 100], [900, 100], [900, 1300], [100, 1300]], "bbox": [100, 100, 900, 1300]}]}
    assert "polder_fills_its_bbox" not in f(rect)
    fan = {**base, "fields": [{"name": "p", "kind": "paddy", "outline": [[500, 100], [900, 1300], [100, 1300]], "bbox": [100, 100, 900, 1300]}]}  # a triangle covers ~half its bbox
    assert "polder_fills_its_bbox" in f(fan)


def test_structures_clear_of_dike():
    # GM 2026-07-22: no farmhouse and no windbreak clump may sit ON the perimeter dike earthwork band.
    dike = [[100, 100], [900, 100], [900, 900], [100, 900]]
    base = {"meta": {"scale": "hamlet", "field_archetype": "polder_grid"}, "dikes": [{"outline": dike, "w_min": 14.0, "w_max": 38.0}]}
    assert "structures_clear_of_dike" in f({**base, "houses": [{"x": 500, "y": 500, "w": 40, "h": 26, "rot": 0, "kind": "plain"}]})  # house on the dike
    assert "structures_clear_of_dike" in f({**base, "village_groves": [{"clumps": [[500, 500], [1200, 1200]]}]})  # a clump on the dike
    assert "structures_clear_of_dike" not in f({**base, "houses": [{"x": 1200, "y": 500, "w": 40, "h": 26, "rot": 0, "kind": "plain"}], "village_groves": [{"clumps": [[1200, 1200]]}]})
    # a non-polder map (no dike) never trips it
    assert "structures_clear_of_dike" not in f({"meta": {"scale": "hamlet", "field_archetype": "valley_paddy"}, "houses": [{"x": 500, "y": 500, "w": 40, "h": 26, "rot": 0, "kind": "plain"}]})


def test_polder_channels_clear_of_dike():
    # GM 2026-07-22: the polder ring canal runs on the INNER TOE of the dike (field side); an irrigation
    # channel buried in the dike band fires (>4 points), a couple of sluice crossings are fine.
    dike = [[100, 100], [900, 100], [900, 900], [100, 900]]  # a simple square "band" outline
    base = {"meta": {"scale": "hamlet", "field_archetype": "polder_grid"}, "dikes": [{"outline": dike, "w_min": 14.0, "w_max": 38.0}]}
    inside = {"poly": [[200, 200], [300, 200], [400, 200], [500, 200], [600, 200], [700, 200]], "role": "main", "field": "p"}  # 6 pts in the band
    assert "polder_channels_clear_of_dike" in f({**base, "field_ditches": [inside]})
    outside = {"poly": [[200, 50], [500, 50], [800, 50], [200, 1000]], "role": "main", "field": "p"}  # all outside the band
    assert "polder_channels_clear_of_dike" not in f({**base, "field_ditches": [outside]})
    sluices = {"poly": [[200, 150], [500, 1000], [800, 150]], "role": "drain", "field": "p"}  # 2 crossings <= 4
    assert "polder_channels_clear_of_dike" not in f({**base, "field_ditches": [sluices]})
    # a non-polder archetype never trips it, and no dike -> polder_dike_is_earthwork owns that case
    assert "polder_channels_clear_of_dike" not in f({"meta": {"scale": "hamlet", "field_archetype": "valley_paddy"}, "dikes": base["dikes"], "field_ditches": [inside]})


def test_polder_edges_wander():
    # GM 2026-07-22 (issue 4): a polder's dikes must WANDER (a hand-dug fish-scale polder), not run axis-perfect.
    # A dead-straight axis-aligned outline fires; an outline that runs mostly off-axis passes.
    dike = [{"outline": [[100, 100], [900, 100], [900, 1300], [100, 1300]], "w_min": 14.0, "w_max": 38.0, "gaps": []}]
    base = {"meta": {"scale": "hamlet", "down_deg": 90, "field_archetype": "polder_grid"}, "dikes": dike}
    # an axis-aligned rectangle - with a leading ZERO-LENGTH segment the check skips - scores 0% off-axis
    rect = {**base, "fields": [{"name": "p", "kind": "paddy", "outline": [[100, 100], [100, 100], [900, 100], [900, 1300], [100, 1300], [100, 100]], "bbox": [100, 100, 900, 1300]}]}
    assert "polder_edges_wander" in f(rect)
    wavy = [(100 + 45 * math.sin(i / 3.0), 100 + i * 24) for i in range(50)] + [(900 + 45 * math.sin(i / 3.0), 1300 - i * 24) for i in range(50)]
    wavy.append(wavy[0])
    passd = {**base, "fields": [{"name": "p", "kind": "paddy", "outline": [[round(x, 1), round(y, 1)] for x, y in wavy], "bbox": [55, 100, 945, 1300]}]}
    assert "polder_edges_wander" not in f(passd)


def test_polder_dike_gapped_at_sluices():
    # GM 2026-07-22 (issue 1): a THROUGH-CROSSER (a water line running from the field, through the dike band,
    # to outside the field outline) must have a recorded dike gap near where it enters the band; no gap fires.
    band = [[100, 100], [900, 100], [900, 1300], [100, 1300]]
    outline = [[150, 150], [850, 150], [850, 1250], [150, 1250]]  # the field outline sits inside the band
    base = {"meta": {"scale": "hamlet", "field_archetype": "polder_grid"}, "fields": [{"name": "p", "kind": "paddy", "outline": outline, "bbox": [150, 150, 850, 1250]}]}
    crosser = {"poly": [[500, 700], [500, 120], [500, 50]], "role": "main", "field": "p"}  # field -> through band -> outside
    assert "polder_dike_gapped_at_sluices" in f({**base, "dikes": [{"outline": band, "w_min": 14.0, "w_max": 38.0, "gaps": []}], "field_ditches": [crosser]})
    assert "polder_dike_gapped_at_sluices" not in f({**base, "dikes": [{"outline": band, "w_min": 14.0, "w_max": 38.0, "gaps": [[500, 110]]}], "field_ditches": [crosser]})


def test_dikepond_water_within_banks_and_rounded():
    # GM 2026-07-22 (issues 3 + 5): each 桑基魚塘 pond's water sits INSIDE its parcel with ROUNDED corners
    # recorded as many sampled vertices. Water spilling past the parcel fires within_banks; a 4-vertex sharp
    # quad fires corners_rounded; no recorded dikeponds fires both.
    field = {"name": "p", "kind": "paddy", "outline": [[100, 100], [900, 100], [900, 1300], [100, 1300]], "bbox": [100, 100, 900, 1300]}
    base = {"meta": {"scale": "hamlet", "field_archetype": "mulberry_dike_fishpond"}, "fields": [field]}

    def parcel(cx, cy):
        return [[cx - 50, cy - 50], [cx + 50, cy - 50], [cx + 50, cy + 50], [cx - 50, cy + 50]]

    def rounded(cx, cy):
        return [[cx + 30 * math.cos(a), cy + 30 * math.sin(a)] for a in [i * math.pi / 6 for i in range(12)]]

    good = [{"parcel": parcel(200 + 120 * i, 300), "water": rounded(200 + 120 * i, 300)} for i in range(12)]
    assert "dikepond_water_within_banks" not in f({**base, "dikeponds": good})
    assert "dikepond_corners_rounded" not in f({**base, "dikeponds": good})
    # no recorded dikeponds at all -> both fire
    assert "dikepond_water_within_banks" in f(base)
    assert "dikepond_corners_rounded" in f(base)
    # water spilling past its parcel -> within_banks fires (a rounded ring blown up to r=80, past the +-50 bank)
    spill = [
        {"parcel": parcel(200 + 120 * i, 300), "water": [[cx, cy] for cx, cy in [(200 + 120 * i + 80 * math.cos(a), 300 + 80 * math.sin(a)) for a in [j * math.pi / 6 for j in range(12)]]]}
        for i in range(12)
    ]
    assert "dikepond_water_within_banks" in f({**base, "dikeponds": spill})
    # a 4-vertex sharp quad (inside its parcel) -> corners_rounded fires
    sharp = [{"parcel": parcel(200 + 120 * i, 300), "water": [[190 + 120 * i, 290], [210 + 120 * i, 290], [210 + 120 * i, 310], [190 + 120 * i, 310]]} for i in range(12)]
    assert "dikepond_corners_rounded" in f({**base, "dikeponds": sharp})


def test_mulberry_banks_clear_of_channels():
    # GM 2026-07-23: the bank crowns are coppiced BUSHES on the dike; the canals are open water at its toe.
    # A channel centerline penetrating >1.5 px inside a recorded bank fires (bushes standing in the canal);
    # a channel skirting the bank edge passes (the canal genuinely runs along the dike toe); a pond missing
    # its `bank` record fires (the record is what gives the check teeth).
    field = {"name": "p", "kind": "paddy", "outline": [[100, 100], [1700, 100], [1700, 500], [100, 500]], "bbox": [100, 100, 1700, 500]}
    base = {"meta": {"scale": "hamlet", "field_archetype": "mulberry_dike_fishpond"}, "fields": [field]}

    def parcel(cx, cy):
        return [[cx - 50, cy - 50], [cx + 50, cy - 50], [cx + 50, cy + 50], [cx - 50, cy + 50]]

    def rounded(cx, cy):
        return [[cx + 30 * math.cos(a), cy + 30 * math.sin(a)] for a in [i * math.pi / 6 for i in range(12)]]

    def bank(cx, cy):
        return [[cx - 55, cy - 55], [cx + 55, cy - 55], [cx + 55, cy + 55], [cx - 55, cy + 55]]

    ponds = [{"parcel": parcel(200 + 120 * i, 300), "water": rounded(200 + 120 * i, 300), "bank": bank(200 + 120 * i, 300)} for i in range(12)]
    clear = {"poly": [[100, 380], [1700, 380]], "role": "lateral", "field": "p"}  # runs BELOW every bank (banks end at y=355)
    assert "mulberry_banks_clear_of_channels" not in f({**base, "dikeponds": ponds, "field_ditches": [clear]})
    grazing = {"poly": [[100, 355], [1700, 355]], "role": "lateral", "field": "p"}  # runs ON the bank edge - the dike toe
    assert "mulberry_banks_clear_of_channels" not in f({**base, "dikeponds": ponds, "field_ditches": [grazing]})
    through = {"poly": [[100, 300], [1700, 300]], "role": "lateral", "field": "p"}  # runs THROUGH the middle of every bank
    assert "mulberry_banks_clear_of_channels" in f({**base, "dikeponds": ponds, "field_ditches": [through]})
    # a pond whose bank went unrecorded fires - the record is the teeth, dropping it cannot disable the check
    unrecorded = [{k: v for k, v in p.items() if k != "bank"} for p in ponds]
    assert "mulberry_banks_clear_of_channels" in f({**base, "dikeponds": unrecorded, "field_ditches": [clear]})


def test_dikeponds_fed_and_drained():
    # GM 2026-07-23: down_deg=90 -> downhill is +y. Every 桑基魚塘 pond needs a FEED (network-end UPHILL =
    # smaller y) AND a DRAIN (network-end DOWNHILL = larger y) on its water, both reaching the network, not
    # crossing. Sealed / one-way / wrongly-angled / crossing ponds fire.
    field = {"name": "p", "kind": "paddy", "outline": [[50, 50], [400, 50], [400, 1300], [50, 1300]], "bbox": [50, 50, 400, 1300]}
    canal = {"poly": [[100, 50], [100, 1250]], "role": "lateral", "seg": "lateral", "field": "p"}  # a vertical canal at x=100
    base = {"meta": {"scale": "hamlet", "down_deg": 90, "field_archetype": "mulberry_dike_fishpond"}, "fields": [field], "field_ditches": [canal]}

    def rect(cx, cy):
        return [[cx - 20, cy - 30], [cx + 20, cy - 30], [cx + 20, cy + 30], [cx - 20, cy + 30]]

    ponds = [{"parcel": rect(200, 120 + i * 90), "water": rect(200, 120 + i * 90)} for i in range(12)]

    def good_sl():
        out = []
        for i in range(12):
            cy = 120 + i * 90
            out.append({"a": [200, cy - 30], "b": [100, cy - 50], "kind": "feed"})  # feed: network-end uphill, on the canal
            out.append({"a": [200, cy + 30], "b": [100, cy + 50], "kind": "drain"})  # drain: network-end downhill, on the canal
        return out

    assert "dikeponds_fed_and_drained" not in f({**base, "dikeponds": ponds, "dikepond_sluices": good_sl()})
    assert "dikeponds_fed_and_drained" in f({**base, "dikeponds": ponds})  # no sluices -> sealed
    bad_feed = good_sl()
    bad_feed[0] = {"a": [200, 90], "b": [100, 130], "kind": "feed"}  # pond0 feed network-end DOWNHILL -> one-way (drain only)
    assert "dikeponds_fed_and_drained" in f({**base, "dikeponds": ponds, "dikepond_sluices": bad_feed})
    bad_drain = good_sl()
    bad_drain[1] = {"a": [200, 150], "b": [100, 110], "kind": "drain"}  # pond0 drain network-end UPHILL -> drains uphill
    assert "dikeponds_fed_and_drained" in f({**base, "dikeponds": ponds, "dikepond_sluices": bad_drain})
    bad_reach = good_sl()
    bad_reach[0] = {"a": [200, 90], "b": [2000, 70], "kind": "feed"}  # feed far-end reaches nothing
    assert "dikeponds_fed_and_drained" in f({**base, "dikeponds": ponds, "dikepond_sluices": bad_reach})
    crossing = good_sl()
    crossing[0] = {"a": [220, 150], "b": [100, 90], "kind": "feed"}  # pond0: feed goes up-left...
    crossing[1] = {"a": [220, 90], "b": [100, 150], "kind": "drain"}  # ...drain goes down-left, so the two cross
    assert "dikeponds_fed_and_drained" in f({**base, "dikeponds": ponds, "dikepond_sluices": crossing})


def test_polder_floor_is_ring_interior():
    # GM 2026-07-22: the polder's green field floor must be the ring-canal INTERIOR (hug the outermost
    # channels), not the dike-boundary envelope. A floor vertex >8 px off the ring fires; a floor on the ring
    # passes. (No ring channels or no floor recorded -> the check is simply skipped.)
    ring = [
        {"poly": [[100, 100], [300, 100]], "role": "main", "seg": "feeder", "field": "p"},
        {"poly": [[300, 100], [300, 300]], "role": "lateral", "seg": "e_toe", "field": "p"},
        {"poly": [[300, 300], [100, 300]], "role": "drain", "seg": "drain", "field": "p"},
        {"poly": [[100, 300], [100, 100]], "role": "lateral", "seg": "w_toe", "field": "p"},
    ]
    base = {
        "meta": {"scale": "hamlet", "field_archetype": "polder_grid"},
        "field_ditches": ring,
        "dikes": [{"outline": [[90, 90], [310, 90], [310, 310], [90, 310]], "w_min": 14.0, "w_max": 38.0, "gaps": []}],
        "fields": [{"name": "p", "kind": "paddy", "outline": [[100, 100], [300, 100], [300, 300], [100, 300]], "bbox": [100, 100, 300, 300]}],
    }
    on_ring = {**base, "comb_floors": {"p": [[100, 100], [300, 100], [300, 300], [100, 300]]}}  # the floor IS the ring loop
    assert "polder_floor_is_ring_interior" not in f(on_ring)
    off_ring = {**base, "comb_floors": {"p": [[50, 50], [350, 50], [350, 350], [50, 350]]}}  # the dike-boundary envelope, ~50 px out
    assert "polder_floor_is_ring_interior" in f(off_ring)


def test_polder_dike_is_earthwork():
    # GM 2026-07-22: a polder/dike-pond map must record a perimeter-dike earthwork band of VARYING width;
    # a missing dike or a uniform-width one (the reverted post-1949 ruled rectangle) fires.
    base = {"meta": {"scale": "hamlet", "field_archetype": "polder_grid"}}
    assert "polder_dike_is_earthwork" in f(base)  # no dike recorded at all
    assert "polder_dike_is_earthwork" in f({**base, "dikes": [{"outline": [], "w_min": 20.0, "w_max": 22.0}]})  # near-uniform width
    assert "polder_dike_is_earthwork" not in f({**base, "dikes": [{"outline": [], "w_min": 14.0, "w_max": 38.0}]})
    assert "polder_dike_is_earthwork" in f({"meta": {"scale": "hamlet", "field_archetype": "mulberry_dike_fishpond"}})
    # a non-polder archetype never trips it
    assert "polder_dike_is_earthwork" not in f({"meta": {"scale": "hamlet", "field_archetype": "valley_paddy"}})


def test_polder_parcel_fabric_must_vary():
    # a polder's parcels must be a PATCHWORK (varied oblongs), never identical cells: the surveyed
    # chessboard was the canal grid, the parcels inside were private-tenure fragments (grounding in
    # build_polder's docstring). The uniform 66x [142,142] block is the real pre-fix Kuwabata/Enokida
    # geometry. Applies to both polder-geometry archetypes; a polder manifest with NO recorded parcel
    # geometry fires too (no passing by omission).
    field = {"name": "p", "kind": "paddy", "outline": [[100, 100], [900, 100], [900, 1300], [100, 1300]], "bbox": [100, 100, 900, 1300]}
    varied = [[142, 68], [142, 66], [75, 142], [44, 142], [142, 142], [290, 142]] * 11
    for arch in ("polder_grid", "mulberry_dike_fishpond"):
        base = {"meta": {"scale": "hamlet", "field_archetype": arch}}
        assert "polder_parcels_vary" in f({**base, "fields": [{**field, "plots": [[142.0, 142.0]] * 66}]})
        assert "polder_parcels_vary" in f({**base, "fields": [field]})  # no parcel geometry recorded
        assert "polder_parcels_vary" in f({**base, "fields": [{**field, "plots": varied[:6]}]})  # too few to judge
        assert "polder_parcels_vary" not in f({**base, "fields": [{**field, "plots": varied}]})
    # a non-polder archetype never trips it, plots or not
    assert "polder_parcels_vary" not in f({"meta": {"scale": "hamlet", "field_archetype": "valley_paddy"}, "fields": [{**field, "plots": [[142.0, 142.0]] * 66}]})


def test_torii_avenue_pitch_capped():
    # GM 2026-07-25 after the spacing research: Rokugan's sando is the 1/3/7 SET of formal gateways,
    # not a donation row (a designated-site special case) and not ranked ichi/ni/san gates (200 m -
    # 1.3 km apart), so the pitch is a house rule - ~20 ft, never more than two rail-spans (32 ft).
    # The motivating cases were town/city avenues at 45-114 ft; the village avenues at ~30 ft pass.
    def m(pitch_px, n=3, ftpx=1, **rel):
        return {
            "meta": {"scale": "town", "ftpx": ftpx},
            "religious": [{"kind": "monastery", "x": 500, "y": 500, "w": 40, "h": 28, **rel}],
            "torii": [[500, 560 + pitch_px * i, 9] for i in range(n)],
        }

    assert "torii_avenue_pitch_capped" in f(m(61))  # Hirameki's Bishamon, the town case
    assert "torii_avenue_pitch_capped" in f(m(38, ftpx=3))  # Tango's Bishamon at 114 ft, the widest in the pool
    assert "torii_avenue_pitch_capped" not in f(m(20))  # the house pitch
    assert "torii_avenue_pitch_capped" not in f(m(16, ftpx=2))  # a village avenue at 32 ft sits AT the cap and passes
    assert "torii_avenue_pitch_capped" in f(m(17, ftpx=2))  # ... 34 ft does not
    assert "torii_avenue_pitch_capped" not in f(m(61, torii_outlier=True))  # a designated donation-row site is exempt
    assert "torii_avenue_pitch_capped" not in f(m(61, n=1))  # a lone arch has no pitch to measure


def test_torii_count_canonical_numerology():
    # counts are exactly {1, 3, 7} at every proper hall (GM 2026-07-21 numerology ruling; supersedes
    # the retired torii_full_avenue_is_seven and its {1, 2, 7} set): 2 and 4 fire (Hikari's old Benten
    # pair, Hirameki's old unfinished four), 0 fires (the floor - every proper hall has a gate),
    # 1/3/7 pass, an explicitly marked outlier is exempt, and a small_shrine neither needs gates nor
    # absorbs a neighbor's (the misattribution that hid Tango's 2-arch Daikoku entrance).
    def m(n, kind="monastery", **rel_extra):
        return {
            "meta": {"scale": "town"},
            "religious": [{"kind": kind, "x": 500, "y": 500, "w": 40, "h": 28, **rel_extra}],
            "torii": [[500, 560 + 30 * i, 9] for i in range(n)],
        }

    for bad in (2, 4, 8, 0):
        assert "torii_count_canonical" in f(m(bad)), bad
    for ok in (1, 3, 7):
        assert "torii_count_canonical" not in f(m(ok)), ok
    assert "torii_count_canonical" not in f(m(4, torii_outlier=True))  # marked outlier - always with a story
    M = m(3)
    M["religious"].append({"kind": "small_shrine", "x": 510, "y": 585, "w": 12, "h": 9})  # nearer the arches than the hall
    assert "torii_count_canonical" not in f(M)  # exempt AND excluded from attribution


def test_polder_parcels_must_front_a_ditch():
    # every polder parcel must sit within reach of a supply/drain ditch (the jingbang creek-and-ditch
    # interior): parcels far from every ditch fire, parcels without recorded centroids (pre-fix format)
    # fire, and a laterals-served fabric passes. GM-flagged on the original Kuwabata (floating ponds).
    field = {"name": "p", "kind": "paddy", "outline": [[100, 100], [900, 100], [900, 1300], [100, 1300]], "bbox": [100, 100, 900, 1300]}
    lat = {"poly": [[500, 88], [500, 1312]], "role": "lateral", "field": "p", "w": 3.2, "w_tail": 2.4}
    # varied 4-tuple parcels hugging the x=500 lateral: centroids at x 430/570, spans ~140 -> reach ~103
    served = [[140, 70, 430, 100 + 90 * i] for i in range(7)] + [[140, 140, 570, 100 + 160 * i] for i in range(7)]
    for arch in ("polder_grid", "mulberry_dike_fishpond"):
        base = {"meta": {"scale": "hamlet", "field_archetype": arch}, "field_ditches": [lat]}
        assert "polder_parcels_front_water" not in f({**base, "fields": [{**field, "plots": served}]})
        adrift = [*served, [140, 140, 880, 1280]]  # one parcel ~380px from the lateral
        assert "polder_parcels_front_water" in f({**base, "fields": [{**field, "plots": adrift}]})
        no_cent = [*served, [140.0, 140.0]]  # pre-fix 2-tuple record: no centroid = no frontage
        assert "polder_parcels_front_water" in f({**base, "fields": [{**field, "plots": no_cent}]})
        # no ditches recorded at all -> everything is unfronted
        assert "polder_parcels_front_water" in f({"meta": base["meta"], "fields": [{**field, "plots": served}]})


def test_polder_parcels_must_be_organic():
    # GM 2026-07-24: a hand-piled bund has slumped, walked-round corners and paced-by-eye runs, so a
    # parcel drawn as a ruled quad (4 vertices, all 4 corners square) is the machine-cut consolidation
    # signature and must fire, as does a whole fabric on which nothing has eased. The pre-fix 4-element
    # parcel record (no outline shape at all) fires too - no passing by omission. Individual parcels
    # whose corners all stayed square are HONEST (reach is drawn from a wide spread on purpose), so the
    # corner rule is a fabric mean, not a per-parcel bound.
    field = {"name": "p", "kind": "paddy", "outline": [[100, 100], [900, 100], [900, 1300], [100, 1300]], "bbox": [100, 100, 900, 1300]}
    lat = {"poly": [[500, 88], [500, 1312]], "role": "lateral", "field": "p", "w": 3.2, "w_tail": 2.4}
    ruled = [[140, 70, 430, 100 + 90 * i, 4, 4] for i in range(7)] + [[140, 140, 570, 100 + 160 * i, 4, 4] for i in range(7)]
    organic = [[*p[:4], 30, 1] for p in ruled]
    for arch in ("polder_grid", "mulberry_dike_fishpond"):
        base = {"meta": {"scale": "hamlet", "field_archetype": arch}, "field_ditches": [lat]}
        assert "polder_parcels_are_organic" in f({**base, "fields": [{**field, "plots": ruled}]})
        assert "polder_parcels_are_organic" in f({**base, "fields": [{**field, "plots": [p[:4] for p in ruled]}]})  # pre-fix record
        assert "polder_parcels_are_organic" in f({**base, "fields": [field]})  # no parcel geometry at all
        assert "polder_parcels_are_organic" in f({**base, "fields": [{**field, "plots": [*organic, ruled[0]]}]})  # one ruled few-vertex quad is enough
        assert "polder_parcels_are_organic" in f({**base, "fields": [{**field, "plots": [[*p[:4], 8, 1] for p in ruled]}]})  # eased but barely sampled
        assert "polder_parcels_are_organic" in f({**base, "fields": [{**field, "plots": [[*p[:4], 30, 3] for p in ruled]}]})  # densely sampled, but nothing has eased
        assert "polder_parcels_are_organic" not in f({**base, "fields": [{**field, "plots": [*organic[:-2], [*organic[0][:4], 30, 4]]}]})  # a few all-square parcels are honest
        assert "polder_parcels_are_organic" not in f({**base, "fields": [{**field, "plots": organic}]})
    # a non-polder archetype never trips it
    assert "polder_parcels_are_organic" not in f({"meta": {"scale": "hamlet", "field_archetype": "valley_paddy"}, "fields": [{**field, "plots": ruled}]})


def test_ribbon_valley_must_be_long_and_narrow():
    base = {"meta": {"scale": "hamlet", "down_deg": 90, "field_archetype": "ribbon_valley"}}
    thin = {**base, "fields": [{"name": "r", "kind": "paddy", "outline": [[400, 100], [700, 100], [700, 2000], [400, 2000]], "bbox": [400, 100, 700, 2000]}]}  # 300 wide x 1900 long
    assert "ribbon_is_long_and_narrow" not in f(thin)
    squat = {**base, "fields": [{"name": "r", "kind": "paddy", "outline": [[100, 100], [1400, 100], [1400, 900], [100, 900]], "bbox": [100, 100, 1400, 900]}]}  # 1300 x 800, too broad
    assert "ribbon_is_long_and_narrow" in f(squat)


def test_mulberry_dike_fishpond_needs_a_block_of_ponds():
    base = {"meta": {"scale": "hamlet", "field_archetype": "mulberry_dike_fishpond"}}
    rect_ol = [[100, 100], [900, 100], [900, 1300], [100, 1300]]
    good = {**base, "fields": [{"name": "p", "kind": "paddy", "outline": rect_ol, "bbox": [100, 100, 900, 1300]}], "land_use": [{"overlay": "mulberry_fishpond", "count": 40}]}
    assert "dikepond_is_ponds_in_a_block" not in f(good)
    no_ponds = {**base, "fields": [{"name": "p", "kind": "paddy", "outline": rect_ol, "bbox": [100, 100, 900, 1300]}]}  # a block but no fishponds
    assert "dikepond_is_ponds_in_a_block" in f(no_ponds)


def test_overlays_must_sit_on_the_low_wet_ground():
    """Feature 010. A plot-based land-use overlay is sited by TOPOGRAPHY, not chance: deep-water lotus
    (30-50cm) cannot sit on ground that grows rice at 5-9cm, and dike-ponds were dug out of the low
    flood-prone hollows. The teeth come from `wet_plots` being written by the FIELD pass while
    `land_use[].plots` is written by the OVERLAY pass - two independent records, not a self-report."""
    base = {"meta": {"scale": "village", "land_use_overlay": "lotus"}, "wet_plots": [[100, 100], [140, 100], [180, 100]]}
    good = {**base, "land_use": [{"overlay": "lotus", "count": 2, "plots": [[100, 100], [140, 100]]}]}
    assert "overlays_on_wet_ground_only" not in f(good)
    off = {**base, "land_use": [{"overlay": "lotus", "count": 2, "plots": [[100, 100], [900, 900]]}]}  # one plot up on dry rice ground
    assert "overlays_on_wet_ground_only" in f(off)
    # the ORIGINAL defect this feature fixed: a uniform random sample over ALL plots, so nothing lands on wet ground
    random_sample = {**base, "land_use": [{"overlay": "lotus", "count": 3, "plots": [[500, 220], [730, 640], [910, 480]]}]}
    assert "overlays_on_wet_ground_only" in f(random_sample)
    # the NAMED wholesale-conversion opt-out (the dike-pond ARCHETYPE) is exempt by design, not by accident
    archetype = {**base, "land_use": [{"overlay": "lotus", "count": 2, "eligible": "all", "plots": [[900, 900]]}]}
    assert "overlays_on_wet_ground_only" not in f(archetype)


def test_land_use_overlay_drawn_tolerates_having_no_eligible_ground():
    """Feature 010. Drawing nothing is the HONEST outcome when a field has no low/wet ground, so that must
    not trip the gate - but a declared overlay that simply never called apply_land_use still must."""
    base = {"meta": {"scale": "village", "land_use_overlay": "lotus"}}
    no_ground = {**base, "wet_plots": [], "land_use": [{"overlay": "lotus", "count": 0, "plots": []}]}
    assert "land_use_overlay_drawn" not in f(no_ground)
    never_called = {**base, "wet_plots": [[100, 100]], "land_use": []}
    assert "land_use_overlay_drawn" in f(never_called)
    had_ground_but_empty = {**base, "wet_plots": [[100, 100]], "land_use": [{"overlay": "lotus", "count": 0, "plots": []}]}
    assert "land_use_overlay_drawn" in f(had_ground_but_empty)


def test_paddy_features_match_archetype_fires_on_wrong_type():
    """Feature 012: an in-field feature on the wrong paddy type must fire (rock on polder; anything on
    dike-pond), and a right-type placement must not. Ponds must also sit on low/wet ground."""
    base = {"meta": {"scale": "village", "field_archetype": "polder_grid"}, "fields": [{"name": "p", "kind": "paddy", "outline": [[0, 0], [500, 0], [500, 500], [0, 500]], "bbox": [0, 0, 500, 500]}]}
    # rock outcrop on a polder (alluvial silt, no bedrock) - wrong
    assert "paddy_features_match_archetype" in f({**base, "field_rocks": [{"x": 100, "y": 100}]})
    # a pond on a polder is fine (borrow-pit) IF on low ground
    good = {**base, "wet_plots": [[100, 100]], "field_ponds": [{"x": 100, "y": 100, "rx": 20, "ry": 14}]}
    assert "paddy_features_match_archetype" not in f(good)
    assert "field_ponds_on_low_ground" not in f(good)
    # a pond NOT on low ground fires the placement check
    offlow = {**base, "wet_plots": [[100, 100]], "field_ponds": [{"x": 400, "y": 400, "rx": 20, "ry": 14}]}
    assert "field_ponds_on_low_ground" in f(offlow)
    # NOTHING is allowed on a dike-pond map (open water is its fabric)
    dp = {**base, "meta": {"scale": "village", "field_archetype": "mulberry_dike_fishpond"}, "field_ponds": [{"x": 100, "y": 100, "rx": 20, "ry": 14}], "wet_plots": [[100, 100]]}
    assert "paddy_features_match_archetype" in f(dp)


def test_dike_top_houses_on_the_dike():
    # GM 2026-07-24 (settlements.md 'Polder siting Q&A'): the on_dike tag (dike_top_houses,
    # settlement_form 'dike_top') exempts a house from structures_clear_of_dike - so the tag must be
    # honest: a tagged house must actually be seated on the recorded dike band.
    dike = [[100, 100], [900, 100], [900, 900], [100, 900]]
    base = {"meta": {"scale": "hamlet", "field_archetype": "polder_grid"}, "dikes": [{"outline": dike, "w_min": 14.0, "w_max": 38.0}]}
    on = {**base, "houses": [{"x": 500, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain", "on_dike": True}]}
    assert "dike_top_houses_on_the_dike" not in f(on)
    assert "structures_clear_of_dike" not in f(on)  # the crest house is exempt from the keep-off rule
    off = {**base, "houses": [{"x": 1300, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain", "on_dike": True}]}
    assert "dike_top_houses_on_the_dike" in f(off)  # a tagged house floating off the bank
    # tagged houses on a map with NO dike at all fire too - the tag is never a free pass
    assert "dike_top_houses_on_the_dike" in f({"meta": {"scale": "hamlet"}, "houses": [{"x": 500, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain", "on_dike": True}]})


def test_polder_waterward_flanks_wet():
    # GM 2026-07-24 (settlements.md 'Polder siting Q&A'): outside the dike on a declared water-facing
    # flank must READ wet (waterside/toe marsh or open water), not the same dry scrub as the landward shore.
    dike = [[300, 300], [1100, 300], [1100, 1100], [300, 1100]]
    dry = {"meta": {"scale": "hamlet", "field_archetype": "polder_grid", "waterward": ["W", "E", "N", "S"]}, "dikes": [{"outline": dike, "w_min": 14.0, "w_max": 38.0}]}
    assert "polder_waterward_flanks_wet" in f(dry)  # all four declared, nothing wet anywhere
    wet_w = {
        **dry,
        "meta": {**dry["meta"], "waterward": ["W"]},
        "marshes": [{"x": 200, "y": 700, "w": 200, "h": 900, "role": "waterside", "poly": [[100, 250], [300, 250], [300, 1150], [100, 1150]]}],
    }
    assert "polder_waterward_flanks_wet" not in f(wet_w)  # a waterside reed fringe covers the west flank
    wet_s = {
        **dry,
        "meta": {**dry["meta"], "waterward": ["S"]},
        "marshes": [{"x": 700, "y": 1300, "w": 1040, "h": 330, "role": "toe", "poly": [[180, 1120], [1220, 1120], [1220, 1450], [180, 1450]]}],
    }
    assert "polder_waterward_flanks_wet" not in f(wet_s)  # the auto toe marsh already wets the low flank
    # an undeclared map skips (a valley comb has no dike facing water)
    assert "polder_waterward_flanks_wet" not in f({"meta": {"scale": "hamlet", "field_archetype": "polder_grid"}, "dikes": dry["dikes"]})


def test_the_waiver_meta_checks_cannot_themselves_be_waived():
    """Otherwise the hatch swallows its own guard: one waiver silencing waivers_are_live would let
    every other waiver rot unreported."""
    M = _waived_map({"waivers_are_live": _WHY, "tanning_yard_on_watr": _WHY})
    assert "waivers_are_live" in f(M)


def test_feature_022_gate_refuses_a_meta_check_in_targeted_mode():
    # measured (census 2026-08-15): waivers_are_documented reads only the DECLARED waivers (pure
    # manifest input), so it is legitimately targetable; waivers_are_live reads what actually
    # FIRED this run and is the true meta-check.
    assert "waivers_are_live" in set(check_village.META_CHECKS)
    with pytest.raises(ValueError, match="waivers_are_live"):
        check_village.gate(_feature_022_manifest(), verbose=False, only={"waivers_are_live"})


def test_field_ponds_sunk_into_one_plot_fires_when_bunds_cross_the_water():
    """Inashiro 2026-08-16: a bbox-fitted pond in a fan-toe wedge - bund lines through open water,
    while field_ponds_on_low_ground stayed green (it reads the host plot flag, not the extent).
    The ring the pond is sunk into TOUCHES the shore and must not fire; a line through the core must."""
    base = {"meta": {"scale": "village", "field_archetype": "valley_paddy"}, "wet_plots": [[100, 100]]}
    pond = {"x": 100, "y": 100, "rx": 30, "ry": 20}
    host = [[70, 80], [130, 80], [130, 120], [70, 120]]  # the host plot ring: touching the shore is fine
    good = {**base, "field_ponds": [pond], "fields": [{**_field("p", 0, 0, 500, 500), "plot_rings": [host]}]}
    assert "field_ponds_sunk_into_one_plot" not in f(good)
    hem = [[100, 60], [100, 140], [110, 140], [110, 60]]  # runs straight through the water
    bad = {**base, "field_ponds": [pond], "fields": [{**_field("p", 0, 0, 500, 500), "plot_rings": [host], "drain_hem": [hem]}]}
    assert "field_ponds_sunk_into_one_plot" in f(bad)
