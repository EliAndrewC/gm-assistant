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
from citybudget import BudgetLine, CityProgram, budget_to_manifest, derive_wall, format_budget, plan_city

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
