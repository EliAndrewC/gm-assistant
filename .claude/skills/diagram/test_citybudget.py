#!/usr/bin/env python3
"""Unit tests for citybudget.py - the budget-first city wall sizer (feature 009).

The two calibration anchors are the heart of the suite:
  - Tango (GM-accepted): its program must BACK-PREDICT the shipped wall within tolerance.
  - pre-feature Nagahara (GM-rejected, pinned in pool/regressions/): its program must price the
    city's required interior far enough below the fixture's measured enclosure to breach the
    over-enclosure tolerance - the empty-space defect must be arithmetic, not opinion.
"""

import json
import math
import os

import pytest

import check_village
import citybudget
from citybudget import BudgetLine, CityProgram, budget_to_manifest, derive_wall, format_budget, plan_capital, plan_city

HERE = os.path.dirname(os.path.abspath(__file__))


def _prog(**kw):
    kw.setdefault("population", 3000)
    return CityProgram(**kw)


# ---- inventory derivation (budgets.md Provincial city caste table) ------------------------


def test_inventory_splits_600_families_per_the_caste_table_at_pop_3000():
    b = plan_city(_prog())
    assert b.dwelling_target["families"] == {"servants": 120, "laborers": 240, "merchants": 150, "burakumin": 30, "samurai": 60}
    assert b.dwelling_target["packed"] == 540  # servants + laborers + merchants + burakumin
    assert b.dwelling_target["samurai_inwall"] == 40  # 2/3 of 60 (the rest live in extramural estates)


@pytest.mark.parametrize(
    "pop,families,packed,samurai_inwall",
    [
        (2000, 400, 360, 27),
        (3000, 600, 540, 40),
        (4000, 800, 720, 53),
    ],
)
def test_inventory_scales_linearly_across_the_canonical_band(pop, families, packed, samurai_inwall):
    b = plan_city(_prog(population=pop))
    assert sum(b.dwelling_target["families"].values()) == families
    assert b.dwelling_target["packed"] == packed
    assert b.dwelling_target["samurai_inwall"] == samurai_inwall


@pytest.mark.parametrize("pop", [1999, 4001, 0, 12000])
def test_population_outside_the_provincial_band_is_rejected(pop):
    with pytest.raises(ValueError, match="2000"):
        plan_city(_prog(population=pop))


# ---- the budget lines sum to the required interior ----------------------------------------


@pytest.mark.parametrize("agri", [False, True])
@pytest.mark.parametrize("pop", [2000, 3000, 4000])
def test_lines_sum_exactly_to_required_interior(pop, agri):
    b = plan_city(_prog(population=pop, agricultural_district=agri))
    assert math.isclose(sum(ln.area_px2 for ln in b.lines), b.required_interior_px2, rel_tol=1e-9)


def test_every_line_carries_a_basis_and_a_label():
    b = plan_city(_prog(river=True, agricultural_district=True))
    for ln in b.lines:
        assert ln.label and ln.basis, ln


def test_circulation_is_the_declared_fraction_of_the_required_interior():
    b = plan_city(_prog())
    circ = next(ln for ln in b.lines if "circulation" in ln.label)
    assert math.isclose(circ.area_px2, citybudget.CIRC_FRAC * b.required_interior_px2, rel_tol=1e-9)
    assert circ.count is None


def test_extras_are_itemized_and_priced_into_the_total():
    plain = plan_city(_prog())
    extra = plan_city(_prog(extras=(BudgetLine("drill ground", None, 12000.0, "GM program"),)))
    assert any(ln.label == "drill ground" for ln in extra.lines)
    # the extra inflates the pre-circulation subtotal, so the required interior grows by extra/(1-f)
    assert math.isclose(extra.required_interior_px2 - plain.required_interior_px2, 12000.0 / (1 - citybudget.CIRC_FRAC), rel_tol=1e-9)


def test_water_line_is_labeled_for_the_program_kind():
    assert any("pond" in ln.label for ln in plan_city(_prog()).lines)
    assert any("canal" in ln.label for ln in plan_city(_prog(river=True)).lines)


# ---- the agricultural-district toggle (US3) ------------------------------------------------


@pytest.mark.parametrize("pop", [2000, 3000, 4000])
def test_agri_toggle_adds_exactly_its_itemized_line_and_grows_the_wall(pop):
    off = plan_city(_prog(population=pop))
    on = plan_city(_prog(population=pop, agricultural_district=True))
    agri = next(ln for ln in on.lines if "agricultural" in ln.label)
    assert not any("agricultural" in ln.label for ln in off.lines)
    assert math.isclose(agri.area_px2, citybudget.AGRI_FRAC * on.required_interior_px2, rel_tol=1e-9)
    # same program otherwise: the non-agri, non-circulation lines are identical
    fixed_off = sum(ln.area_px2 for ln in off.lines if "circulation" not in ln.label)
    fixed_on = sum(ln.area_px2 for ln in on.lines if "circulation" not in ln.label and "agricultural" not in ln.label)
    assert math.isclose(fixed_off, fixed_on, rel_tol=1e-9)
    assert on.wall.rx > off.wall.rx and on.wall.ry > off.wall.ry


# ---- wall derivation (N-gon geometry, not the smooth ellipse) ------------------------------


@pytest.mark.parametrize("nring", [20, 22])
@pytest.mark.parametrize("required", [400_000.0, 690_000.0])
def test_derived_wall_ngon_encloses_the_required_area(required, nring):
    w = derive_wall(required, aspect=0.93, nring=nring)
    ngon = 0.5 * nring * math.sin(2 * math.pi / nring) * w.rx * w.ry
    assert math.isclose(ngon, required, rel_tol=1e-9)
    assert math.isclose(w.interior_px2, required, rel_tol=1e-9)
    assert math.isclose(w.ry / w.rx, 0.93, rel_tol=1e-9)


def test_derived_wall_reports_a_real_perimeter():
    w = derive_wall(690_000.0, aspect=0.93, nring=20)
    # 20-gon perimeter of a ~487x453 ring is ~2,950 px = ~8,900 ft at 3 ft/px
    assert 8_000 < w.perimeter_px * 3 < 10_000


@pytest.mark.parametrize("aspect", [0.0, -1.0, 1.5])
def test_implausible_aspect_is_rejected(aspect):
    with pytest.raises(ValueError, match="aspect"):
        derive_wall(500_000.0, aspect=aspect)


def test_wall_that_cannot_fit_the_canvas_fails_loudly_with_the_numbers():
    with pytest.raises(ValueError) as ei:
        plan_city(_prog(agricultural_district=True), canvas=(900.0, 900.0))
    msg = str(ei.value)
    assert "900" in msg and "canvas" in msg.lower()


def test_canvas_with_room_is_accepted():
    b = plan_city(_prog(), canvas=(3200.0, 2700.0))
    assert 2 * (b.wall.rx + citybudget.WALL_MARGIN_PX) <= 3200


# ---- calibration anchors -------------------------------------------------------------------


def test_tango_program_back_predicts_the_shipped_wall():
    # Shipped Tango: RX,RY = 487,457 (22-vertex ring), agricultural district ON, pop 3000.
    b = plan_city(_prog(agricultural_district=True, aspect=457 / 487, nring=22))
    assert abs(b.wall.rx - 487) / 487 < 0.06
    assert abs(b.wall.ry - 457) / 457 < 0.06
    shipped_interior = 0.5 * 22 * math.sin(2 * math.pi / 22) * 487 * 457
    assert abs(b.required_interior_px2 - shipped_interior) / shipped_interior < 0.06


def test_pre_feature_nagahara_is_priced_as_over_enclosed():
    # The pinned GM-rejected map: its program (pop 3000, river city, NO agricultural district)
    # must price a required interior that its actual wall over-encloses beyond the check tolerance.
    with open(os.path.join(HERE, "pool", "regressions", "city_budget_fires_on_the_too_empty_nagahara.json")) as fh:
        M = json.load(fh)
    measured = check_village.poly_area(M["wall"])
    b = plan_city(_prog(river=True, aspect=460 / 494, nring=20))
    assert measured > b.required_interior_px2 * (1 + check_village.BUDGET_TOL_OVER)


# ---- the shipped programs are PINNED (feature 016 regression net) ---------------------------
#
# Feature 016 moved the temple program out of the static CIVIC_PROGRAM tuple and onto CityProgram
# knobs so a Fox city can declare eight small precincts instead of two great ones. The knobs
# default to the values the tuple carried, so BOTH shipped cities must reprice bit-for-bit. These
# literals were captured from the pre-refactor code and are deliberately hard-coded rather than
# recomputed: a test that derives its expectation from the code it guards cannot catch a drift.

#: (label, count, area_px2) for every line plan_city emitted for the shipped programs, pre-016.
_TANGO_LINES_PRE_016 = [
    ("packed row housing (laborer/servant/merchant/burakumin)", 540, 372_600.0),
    ("samurai houses in-wall", 40, 99_200.0),
    ("governor's mansion (yamen)", 1, 17_730.0),
    ("six provincial ministries", 6, 7_980.0),
    ("temple precincts", 2, 16_250.0),
    ("minor civic (theater, flophouses, funerary, inspection, kura)", None, 17_440.0),
    ("shops, inns, stables", 21, 4_700.0),
    ("bell-and-drum tower", 1, 250.0),
    ("provincial martial hall + 1-2 private dojos", None, 2_200.0),
    ("brewery compound", 1, 800.0),
    ("trade works (dye yard, oil press, pawn court, 1-2 bathhouses, farrier)", None, 1_500.0),
    ("adept-monk houses by the temple precincts", 5, 3_450.0),
    ("pond", 1, 2_900.0),
    ("circulation (trunk + ring road + streets + alleys)", None, 49_089.743590),
    ("agricultural district (in-wall farms, declared reserve)", None, 105_192.307692),
]

_NAGAHARA_LINES_PRE_016 = [
    *[ln for ln in _TANGO_LINES_PRE_016 if ln[0] not in ("pond", "circulation (trunk + ring road + streets + alleys)", "agricultural district (in-wall farms, declared reserve)")],
    ("cargo canal + dock basin", 1, 2_900.0),
    ("circulation (trunk + ring road + streets + alleys)", None, 41_172.043011),
]


def _tango_program(**kw):
    """Tango's shipped program - pop 3000, agricultural district, 22-vertex ring."""
    return CityProgram(population=3000, agricultural_district=True, aspect=457 / 487, nring=22, **kw)


def _nagahara_program(**kw):
    """Nagahara's shipped program - pop 3000, river city, no agricultural district."""
    return CityProgram(population=3000, river=True, aspect=460 / 494, nring=20, **kw)


@pytest.mark.parametrize(
    "program,expected_lines,expected_rx,expected_ry,expected_required",
    [
        (_tango_program(), _TANGO_LINES_PRE_016, 491.063756, 460.813422, 701_282.051282),
        (_nagahara_program(), _NAGAHARA_LINES_PRE_016, 452.111512, 420.994525, 588_172.043011),
    ],
    ids=["tango", "nagahara"],
)
def test_shipped_city_programs_price_exactly_as_they_did_before_the_temple_knobs(program, expected_lines, expected_rx, expected_ry, expected_required):
    b = plan_city(program, canvas=(3200, 2700))
    assert [(ln.label, ln.count, pytest.approx(ln.area_px2, abs=1e-6)) for ln in b.lines] == expected_lines
    assert b.wall.rx == pytest.approx(expected_rx, abs=1e-6)
    assert b.wall.ry == pytest.approx(expected_ry, abs=1e-6)
    assert b.required_interior_px2 == pytest.approx(expected_required, abs=1e-6)


# ---- the temple program as declared knobs (feature 016) -------------------------------------


def _line(budget, label):
    return next(ln for ln in budget.lines if ln.label == label)


def test_the_temple_line_keeps_its_place_in_the_civic_sequence():
    """Line ORDER is manifest bytes: the knob-driven temple row must land exactly where the
    hard-coded CIVIC_PROGRAM row sat, directly after the ministries."""
    labels = [ln.label for ln in plan_city(_prog()).lines]
    assert labels.index("temple precincts") == labels.index(citybudget.MINISTRIES_LABEL) + 1


def test_the_default_temple_knobs_reproduce_the_retired_hard_coded_row():
    b = plan_city(_prog())
    temple = _line(b, "temple precincts")
    assert (temple.count, temple.area_px2) == (2, 16_250.0)  # the row CIVIC_PROGRAM used to carry
    assert _line(b, "adept-monk houses by the temple precincts").count == 5


def test_a_fox_eight_precinct_program_prices_eight_precincts_and_scales_the_clergy_line():
    """Minami's program: eight modest precincts, each well under the 8,125 px^2 default, with
    hereditary temple families living OUT (research/religion-and-death.md finding 3)."""
    b = plan_city(_prog(population=2360, river=True, temple_precincts=8, temple_precinct_px2=3_400.0, monk_houses_per_precinct=6.0))
    temple = _line(b, "temple precincts")
    assert temple.count == 8
    assert temple.area_px2 == pytest.approx(8 * 3_400.0)
    assert temple.area_px2 / 8 < citybudget.TEMPLE_PRECINCT_PX2  # every precinct smaller than a normal complex
    monks = _line(b, "adept-monk houses by the temple precincts")
    assert monks.count == 48  # 8 precincts x 6 households, NOT the retired constant 5
    assert monks.area_px2 == pytest.approx(48 * citybudget.C_PACKED)


def test_the_clergy_line_basis_records_the_derivation_not_just_the_total():
    monks = _line(plan_city(_prog(temple_precincts=8, monk_houses_per_precinct=6.0)), "adept-monk houses by the temple precincts")
    assert "8 temple precinct(s)" in monks.basis and "6 adept-monk households" in monks.basis


def test_an_extras_line_such_as_the_inari_uplift_survives_into_the_budget():
    uplift = BudgetLine("Inari precinct uplift", 1, 1_600.0, "the Fox Inari precinct stands slightly larger than its seven siblings")
    b = plan_city(_prog(temple_precincts=8, extras=(uplift,)))
    assert _line(b, "Inari precinct uplift") == uplift


def test_a_smaller_population_derives_a_smaller_ring():
    small = plan_city(_prog(population=2360, river=True))
    standard = plan_city(_prog(population=3000, river=True))
    assert small.wall.rx < standard.wall.rx and small.required_interior_px2 < standard.required_interior_px2


# ---- scale conversion ----------------------------------------------------------------------


def test_costs_convert_from_the_3ftpx_calibration_to_other_scales():
    at3 = plan_city(_prog())
    at1 = plan_city(_prog(ftpx=1))
    assert math.isclose(at1.required_interior_px2, at3.required_interior_px2 * 9, rel_tol=1e-9)
    assert math.isclose(at1.wall.rx, at3.wall.rx * 3, rel_tol=1e-9)


# ---- manifest + report surfaces ------------------------------------------------------------


def test_manifest_round_trips_as_plain_json():
    b = plan_city(_prog(river=True, agricultural_district=True))
    d = budget_to_manifest(b)
    j = json.loads(json.dumps(d))
    assert j["required_interior_px2"] == pytest.approx(b.required_interior_px2)
    assert j["interior_px2"] == pytest.approx(b.wall.interior_px2)
    assert j["flags"] == {"river": True, "agricultural_district": True}
    assert j["wall"]["rx"] == pytest.approx(b.wall.rx)
    assert len(j["lines"]) == len(b.lines) and all(ln["basis"] for ln in j["lines"])
    assert j["dwelling_target"]["packed"] == 540


def test_report_prints_every_line_with_its_basis_and_the_wall():
    b = plan_city(_prog(agricultural_district=True))
    rep = format_budget(b)
    for ln in b.lines:
        assert ln.label in rep
    assert "basis" in rep or all(ln.basis in rep for ln in b.lines)
    assert f"{b.wall.rx:.0f}" in rep and "required" in rep.lower()


# ---- CLI -----------------------------------------------------------------------------------


def test_cli_plan_prints_the_report(capsys):
    rc = citybudget.main(["--plan", "--population", "3000", "--river", "--canvas", "3200x2700"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "required" in out.lower() and "canal" in out


def test_cli_agri_flag_adds_the_district_line(capsys):
    rc = citybudget.main(["--plan", "--population", "3000", "--agri"])
    assert rc == 0
    assert "agricultural" in capsys.readouterr().out


def test_cli_reports_errors_on_stderr_with_exit_1(capsys):
    rc = citybudget.main(["--plan", "--population", "99"])
    assert rc == 1
    assert "2000" in capsys.readouterr().err


# ---- THE DOMAIN-CAPITAL TIER (feature 018) ---------------------------------------------------
#
# A capital gets a PARALLEL entry point, not a widened band, so the provincial path above runs no
# new branches. These tests therefore also guard a negative: nothing here may move a shipped city.


def _cap(**kw):
    return citybudget.CapitalProgram(**kw)


def test_the_new_ground_costs_sit_in_their_documented_ranges_and_order():
    """A walled compound costs more ground than a detached house, which costs more than a terrace.

    The one relationship that looks wrong and is not: C_TERRACE sits just BELOW C_PACKED. That is
    because C_PACKED is the caste-WEIGHTED average of the packed castes and is pulled up by
    merchant houses (~200 px^2 footprint, against a laborer's ~99), so a bare laborer row house is
    only ~550 gross. A retainer terrace is roomier than a laborer's row and tighter than the
    merchant-inflated average - and it is already generous against the historical anchor, since
    Shibata's ashigaru-nagaya gave each household 378 sq ft to our laborer row's 891.
    """
    assert 3_500.0 <= citybudget.C_YASHIKI <= 5_000.0
    assert 500.0 <= citybudget.C_TERRACE <= 900.0
    assert citybudget.C_YASHIKI > citybudget.C_SPACED > citybudget.C_TERRACE
    assert 500.0 < citybudget.C_TERRACE < citybudget.C_PACKED


def test_the_capital_caste_table_matches_budgets_md_and_sums_to_the_declared_population():
    fam = citybudget.CAPITAL_FAMILIES
    assert fam == {"servants": 480, "laborers": 960, "merchants": 600, "burakumin": 120, "samurai": 312}
    assert "farmers" not in fam  # a capital walls its farmland out
    assert sum(fam.values()) * citybudget.HOUSEHOLD == citybudget.CAPITAL_POP


def test_the_rank_bands_sum_to_the_working_cohort_and_invert_the_provincial_mix():
    """budgets.md's capital column is 70% senior / 30% junior - the INVERSE of a provincial
    city's 27/73 - so walled compounds are the majority texture, not a minority."""
    bands = citybudget.CAPITAL_RANK_BANDS
    working = sum(sum(v) for v in bands.values())
    assert working == 800
    senior = (sum(bands["yashiki"]) + sum(bands["detached"])) / working
    assert senior == pytest.approx(0.70, abs=0.01)
    assert sum(bands["terrace"]) / working == pytest.approx(0.30, abs=0.01)


def test_a_capital_houses_more_of_its_samurai_in_wall_than_a_provincial_city():
    assert citybudget.CAPITAL_SAMURAI_INWALL_FRAC > citybudget.SAMURAI_INWALL_FRAC


@pytest.mark.parametrize("pop", [8_999, 16_001, 3_000, 40_000])
def test_population_outside_the_capital_band_is_rejected(pop):
    with pytest.raises(ValueError, match="domain-capital band"):
        _cap(population=pop)


def test_the_samurai_cohort_splits_in_wall_then_by_rank_band_and_the_three_sum_exactly():
    b = plan_capital(_cap())
    t = b.dwelling_target
    assert t["samurai_inwall"] == round(citybudget.CAPITAL_FAMILIES["samurai"] * citybudget.CAPITAL_SAMURAI_INWALL_FRAC)
    assert t["samurai_yashiki"] + t["samurai_detached"] + t["samurai_terrace"] == t["samurai_inwall"]
    assert t["dwellings"] == citybudget.CAPITAL_POP / citybudget.HOUSEHOLD


def test_capital_lines_sum_exactly_to_the_required_interior():
    b = plan_capital(_cap(river=True))
    assert sum(ln.area_px2 for ln in b.lines) == pytest.approx(b.required_interior_px2, abs=1e-6)


def test_capital_circulation_is_the_declared_fraction_of_the_interior_not_of_the_subtotal():
    b = plan_capital(_cap())
    circ = _line(b, "circulation (trunk + ring road + streets + alleys)")
    assert circ.area_px2 == pytest.approx(b.required_interior_px2 * citybudget.CIRC_FRAC, abs=1e-6)


def test_every_capital_line_carries_a_label_and_a_basis():
    for ln in plan_capital(_cap(river=True)).lines:
        assert ln.label.strip()
        assert ln.basis.strip()


def test_the_castle_is_its_own_line_and_the_samurai_are_three_separate_housing_lines():
    """US2 AS-2: the report must not hide the castle in a civic total, nor flatten the rank bands."""
    labels = [ln.label for ln in plan_capital(_cap()).lines]
    assert any(lb.startswith("the castle") for lb in labels)
    assert sum(1 for lb in labels if "in-wall (Rank" in lb) == 3


def test_the_canonical_capital_fits_the_standard_canvas():
    """SC-002: adopting the tier forces no canvas change."""
    b = plan_capital(_cap(river=True), canvas=(3200, 2700))
    assert 2 * (b.wall.rx + citybudget.WALL_MARGIN_PX) <= 3200
    assert 2 * (b.wall.ry + citybudget.WALL_MARGIN_PX) <= 2700


def test_a_capital_wall_too_large_for_its_canvas_fails_loudly_with_the_numbers():
    with pytest.raises(ValueError, match="never clamp the wall"):
        plan_capital(_cap(river=True), canvas=(1200, 1000))


# ---- the shipped capital program is PINNED the day it lands ---------------------------------
#
# Same discipline the provincial tier earned the hard way: CAPITAL_CIVIC_PROGRAM's third field is
# a ROW TOTAL, not a per-unit cost, and reading it the other way is how feature 016 nearly doubled
# every city's temple ground. These literals are deliberately hard-coded - a test that derives its
# expectation from the code it guards cannot catch a drift - and they also pin LINE ORDER, which
# is manifest bytes.

_CAPITAL_LINES_AS_SHIPPED = [
    ("packed row housing (laborer/servant/merchant/burakumin)", 2160, 1_490_400.0),
    ("the castle (enceinte: baileys + moats; interior implied)", 1, 598_000.0),
    ("samurai walled yashiki in-wall (Ranks 8-12)", 53, 219_950.0),
    ("samurai detached houses in-wall (Ranks 5-7)", 133, 329_840.0),
    ("retainer terraces in-wall (Ranks 1-4)", 79, 52_140.0),
    ("six domain ministries + government ward", 6, 16_000.0),
    ("House Chancellery (the domain's 5-10 lineage representatives)", 1, 2_000.0),
    ("Imperial Magistrate's compound (foreign; houses its own 12 households)", 1, 8_000.0),
    ("the Emperor's granaries", 1, 3_000.0),
    ("domain school (hanko)", 1, 4_000.0),
    ("domain granary + wharf brokers' row", None, 12_000.0),
    ("domain martial hall + rolled private dojos", None, 4_400.0),
    ("aqueduct in-wall works (the conduit itself is buried)", None, 500.0),
    ("minor civic (theaters, flophouses, funerary, inspection, kura)", None, 30_000.0),
    ("shops, inns, stables", 60, 13_400.0),
    ("bell-and-drum tower (sounds the kido curfew)", 1, 250.0),
    ("brewery compounds", 2, 1_600.0),
    ("trade works (dye yards, oil presses, pawn courts, bathhouses, farriers)", None, 3_000.0),
    ("sovereign temple precincts", 2, 32_500.0),
    ("adept-monk houses by the temple precincts", 5, 3_450.0),
    ("cargo canal + dock basin", 1, 5_800.0),
    ("circulation (trunk + ring road + streets + alleys)", None, 213_028.064516),
]


def test_the_shipped_capital_program_prices_and_orders_exactly_as_recorded():
    b = plan_capital(_cap(river=True), canvas=(3200, 2700))
    assert [(ln.label, ln.count, pytest.approx(ln.area_px2, abs=1e-6)) for ln in b.lines] == _CAPITAL_LINES_AS_SHIPPED
    assert b.required_interior_px2 == pytest.approx(3_043_258.064516, abs=1e-6)
    assert b.wall.rx == pytest.approx(1029.050610, abs=1e-6)
    assert b.wall.ry == pytest.approx(957.017067, abs=1e-6)


def test_the_capital_civic_rows_are_row_totals_not_per_unit_costs():
    """The six domain ministries are one row TOTAL for all six, exactly as the provincial six are."""
    row = next(r for r in citybudget.CAPITAL_CIVIC_PROGRAM if r[0].startswith("six domain ministries"))
    assert row[1] == 6
    ministries = _line(plan_capital(_cap()), row[0])
    assert ministries.area_px2 == pytest.approx(row[2], abs=1e-6)


# ---- the variant knobs are validated at DECLARATION time (US3) --------------------------------


@pytest.mark.parametrize(
    "kw,match",
    [
        ({"castle_seat": "edge"}, "requires river=True"),
        ({"castle_seat": "keep"}, "is not one of"),
        ({"imperial_granary_seat": "castle"}, "is not one of"),
        ({"castle_px2": 40_000.0}, "outside the documented band"),
        ({"castle_px2": 9_000_000.0}, "outside the documented band"),
        ({"agricultural_district": True}, "no agricultural district"),
        ({"aspect": 0.0}, "aspect must be in"),
    ],
)
def test_an_illegal_capital_declaration_is_refused_when_it_is_constructed(kw, match):
    with pytest.raises(ValueError, match=match):
        _cap(**kw)


@pytest.mark.parametrize(
    "kw",
    [
        {"castle_seat": "edge", "river": True},
        {"castle_seat": "ring"},
        {"castle_seat": "ring", "river": True},
        {"imperial_granary_seat": "wharf"},
        {"imperial_granary_seat": "magistrate"},
    ],
)
def test_a_legal_capital_declaration_is_accepted(kw):
    assert plan_capital(_cap(**kw)).wall.rx > 0


def test_a_declared_castle_reprices_the_wall_and_records_its_hectares_in_the_basis():
    small = plan_capital(_cap(castle_px2=citybudget.CASTLE_PX2))
    grand = plan_capital(_cap(castle_px2=citybudget.CASTLE_PX2 * 3))
    assert grand.wall.rx > small.wall.rx
    assert "ha" in _line(grand, "the castle (enceinte: baileys + moats; interior implied)").basis


def test_the_capital_manifest_round_trips_as_plain_json_and_adds_no_new_top_level_keys():
    """budget_to_manifest's SHAPE is manifest bytes - a new key would dirty every shipped city."""
    cap = json.loads(json.dumps(budget_to_manifest(plan_capital(_cap(river=True)))))
    prov = json.loads(json.dumps(budget_to_manifest(plan_city(_prog()))))
    assert set(cap) == set(prov)
    assert cap["dwelling_target"]["samurai_yashiki"] == 53


def test_capital_costs_convert_from_the_3ftpx_calibration_to_other_scales():
    at3 = plan_capital(_cap()).required_interior_px2
    at6 = plan_capital(_cap(ftpx=6)).required_interior_px2
    assert at6 == pytest.approx(at3 / 4, rel=1e-9)


def test_the_capital_report_prints_every_line_with_its_basis_and_the_wall():
    text = format_budget(plan_capital(_cap(river=True)))
    assert "SPACE BUDGET - population 12360" in text
    for ln in plan_capital(_cap(river=True)).lines:
        assert ln.label in text
    assert "derived wall" in text


# ---- the CLI grows a --tier, and the provincial default is untouched -------------------------


def test_cli_plans_a_capital_when_asked(capsys):
    assert citybudget.main(["--plan", "--tier", "capital", "--population", "12360", "--river"]) == 0
    out = capsys.readouterr().out
    assert "the castle" in out and "retainer terraces" in out


def test_cli_defaults_to_the_provincial_tier(capsys):
    assert citybudget.main(["--plan", "--population", "3000"]) == 0
    assert "governor's mansion" in capsys.readouterr().out


def test_cli_refuses_an_agricultural_district_at_capital_tier_rather_than_ignoring_it(capsys):
    assert citybudget.main(["--plan", "--tier", "capital", "--population", "12360", "--agri"]) == 1
    assert "walls its farms out" in capsys.readouterr().err


def test_cli_reports_a_capital_band_error_on_stderr(capsys):
    assert citybudget.main(["--plan", "--tier", "capital", "--population", "3000"]) == 1
    assert "domain-capital band" in capsys.readouterr().err


def test_cli_accepts_the_capital_knobs(capsys):
    assert citybudget.main(["--plan", "--tier", "capital", "--population", "12360", "--river", "--castle-seat", "edge", "--granary-seat", "wharf"]) == 0
    assert "seat=edge" in capsys.readouterr().out
