"""Tests for pack_audit.py (feature 007 - packing-audit hardening).

Behavior-named, parametrized, over small SYNTHETIC svg strings (not the pool
maps, which change). Covers current behavior (parse/coverage/aligned gaps/maximal
rectangle) plus the new top-N vacant rectangles and per-region density.
"""

from __future__ import annotations

import pytest

import pack_audit as pa

COURT = "url(#court-earth)"


def _rect(x: float, y: float, w: float, h: float, fill: str) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'


def _svg(*bodies: str) -> str:
    return "<svg>" + "".join(bodies) + "</svg>"


# --- parse_svg ---


def test_parse_svg_classifies_interior_building_open_and_glyphs() -> None:
    svg = _svg(
        _rect(0, 0, 300, 300, COURT),
        _rect(10, 10, 90, 90, "#DDB87A"),  # building (8100 px2)
        _rect(200, 200, 60, 60, "url(#garden-stipple)"),  # open feature
        _rect(250, 10, 20, 20, "#C9A57A"),  # too small -> not a building
        '<circle cx="150" cy="150" r="5"/>',  # glyph
        '<circle cx="5" cy="5" r="2"/>',  # too small -> ignored
        '<ellipse cx="150" cy="250" rx="20" ry="10"/>',  # glyph
    )
    plan = pa.parse_svg(svg)
    assert len(plan.interior) == 1
    assert len(plan.buildings) == 1
    assert len(plan.open_features) == 1
    assert len(plan.glyphs) == 2  # r=5 circle + ellipse; r=2 ignored


def test_parse_svg_raises_without_interior() -> None:
    with pytest.raises(ValueError, match="interior"):
        pa.parse_svg(_svg(_rect(0, 0, 10, 10, "#DDB87A")))


# --- coverage ---


def test_coverage_is_building_area_over_interior() -> None:
    plan = pa.parse_svg(_svg(_rect(0, 0, 300, 300, COURT), _rect(0, 0, 90, 90, "#DDB87A")))
    assert pa.coverage(plan) == pytest.approx(0.09, abs=0.01)


# --- aligned_gaps ---


@pytest.mark.parametrize(("afill", "expect_kura"), [("#C9A57A", False), ("#F2EFE4", True)])
def test_aligned_gaps_vertical_stack_reports_gap_and_kura(afill: str, expect_kura: bool) -> None:
    plan = pa.parse_svg(
        _svg(
            _rect(0, 0, 300, 300, COURT),
            _rect(10, 10, 60, 40, afill),
            _rect(10, 100, 60, 40, "#C9A57A"),
        )
    )
    gaps = pa.aligned_gaps(plan)
    assert gaps, "expected an aligned gap"
    assert gaps[0].orient == "V"
    assert gaps[0].ft == pytest.approx(16.7, abs=0.5)
    assert gaps[0].kura is expect_kura


def test_aligned_gaps_blocked_by_third_building_drops_the_span() -> None:
    plan = pa.parse_svg(
        _svg(
            _rect(0, 0, 300, 300, COURT),
            _rect(10, 10, 60, 40, "#C9A57A"),
            _rect(10, 100, 60, 40, "#C9A57A"),
            _rect(10, 65, 60, 20, "#C9A57A"),  # sits inside the A->B gap
        )
    )
    assert not any(g.ft == pytest.approx(16.7, abs=0.5) for g in pa.aligned_gaps(plan))


def test_aligned_gaps_horizontal_stack() -> None:
    plan = pa.parse_svg(
        _svg(
            _rect(0, 0, 300, 300, COURT),
            _rect(10, 10, 40, 60, "#C9A57A"),
            _rect(100, 10, 40, 60, "#C9A57A"),
        )
    )
    gaps = pa.aligned_gaps(plan)
    assert any(g.orient == "H" and g.ft == pytest.approx(16.7, abs=0.5) for g in gaps)


def test_aligned_gaps_horizontal_blocked_by_third_building_drops_the_span() -> None:
    plan = pa.parse_svg(
        _svg(
            _rect(0, 0, 300, 300, COURT),
            _rect(10, 10, 40, 60, "#C9A57A"),
            _rect(100, 10, 40, 60, "#C9A57A"),
            _rect(65, 10, 20, 60, "#C9A57A"),  # sits inside the A->B horizontal gap
        )
    )
    gaps = pa.aligned_gaps(plan)
    assert not any(g.orient == "H" and g.ft == pytest.approx(16.7, abs=0.5) for g in gaps)


# --- top_vacant_rects (NEW) ---


def test_top_vacant_rects_multiple_largest_first_non_overlapping() -> None:
    plan = pa.parse_svg(
        _svg(
            _rect(0, 0, 300, 300, COURT),
            _rect(120, 0, 60, 300, "#C9A57A"),  # full-height divider splits the court
        )
    )
    rects = pa.top_vacant_rects(plan, n=2)
    assert len(rects) == 2
    assert rects[0].area_sqft >= rects[1].area_sqft  # largest first
    left, right = sorted(rects, key=lambda r: r.x)
    assert left.x + left.w_ft * pa.FTPX <= right.x + 4  # disjoint in x


def test_top_vacant_rects_respects_min_area_and_n() -> None:
    plan = pa.parse_svg(_svg(_rect(0, 0, 300, 300, COURT)))
    assert len(pa.top_vacant_rects(plan, n=5, min_area_sqft=150)) >= 1
    assert pa.top_vacant_rects(plan, n=5, min_area_sqft=1e9) == []


def test_vacant_rect_orientation() -> None:
    plan = pa.parse_svg(_svg(_rect(0, 0, 300, 150, COURT)))
    assert pa.top_vacant_rects(plan, n=1)[0].orient == "horizontal"


# --- region_density (NEW) ---


def test_region_density_built_tile_higher_than_empty_tile() -> None:
    plan = pa.parse_svg(
        _svg(
            _rect(0, 0, 300, 300, COURT),
            _rect(0, 0, 100, 100, "#DDB87A"),  # fills the top-left tile
        )
    )
    tiles = {(t.row, t.col): t for t in pa.region_density(plan, rows=3, cols=3)}
    assert tiles[(0, 0)].coverage_pct > tiles[(2, 2)].coverage_pct
    assert tiles[(2, 2)].coverage_pct == pytest.approx(0.0, abs=0.02)


def test_region_density_tile_outside_non_rectangular_interior_is_zero() -> None:
    # L-shaped interior (top strip + left column); the bottom-right tile is outside it.
    plan = pa.parse_svg(_svg(_rect(0, 0, 300, 100, COURT), _rect(0, 0, 100, 300, COURT)))
    tiles = {(t.row, t.col): t for t in pa.region_density(plan, rows=3, cols=3)}
    assert tiles[(2, 2)].interior_sqft == 0
    assert tiles[(2, 2)].coverage_pct == 0.0


# --- gap_tag ---


@pytest.mark.parametrize(
    ("ft", "kura", "expected"),
    [
        (6.0, True, "fire-gap OK (kura)"),
        (12.0, True, "LOOSE (kura gap >10 ft)"),
        (6.0, False, "tight"),
        (12.0, False, "LOOSE (wooden >8 ft)"),
    ],
)
def test_gap_tag(ft: float, kura: bool, expected: str) -> None:
    assert pa.gap_tag(pa.Gap(ft, "V", 0.0, 0.0, kura)) == expected


# --- format_report + main (shell) ---


def test_format_report_rich_map_covers_all_sections() -> None:
    svg = _svg(
        _rect(0, 0, 300, 200, COURT),  # L-shaped interior (top strip
        _rect(0, 0, 200, 300, COURT),  #  + left column; bottom-right corner is outside)
        _rect(0, 0, 90, 90, "#DDB87A"),  # building
        _rect(10, 210, 60, 40, "url(#garden-stipple)"),  # open feature (inside the left column)
        '<circle cx="30" cy="130" r="5"/>',  # point glyph (occupied, not a building)
        _rect(10, 100, 60, 40, "#C9A57A"),  # stacked pair ->
        _rect(10, 180, 60, 40, "#C9A57A"),  #  an aligned gap
    )
    report = pa.format_report(pa.parse_svg(svg)).lower()
    for section in ("coverage", "top vacant", "per-region", "aligned"):
        assert section in report
    assert "ft" in report  # vacant/gap lines rendered


def test_format_report_full_map_reports_none_placeholders() -> None:
    svg = _svg(_rect(0, 0, 60, 60, COURT), _rect(0, 0, 60, 60, "#DDB87A"))
    report = pa.format_report(pa.parse_svg(svg))
    assert report.count("(none") == 2  # no vacant rectangle, no aligned gap


def test_main_reads_file_and_prints(tmp_path, capsys) -> None:
    p = tmp_path / "m.svg"
    p.write_text(_svg(_rect(0, 0, 300, 300, COURT), _rect(0, 0, 90, 90, "#DDB87A")))
    assert pa.main([str(p)]) == 0
    assert "coverage" in capsys.readouterr().out.lower()


def test_main_without_args_returns_usage_error(capsys) -> None:
    assert pa.main([]) == 2
    assert "usage" in capsys.readouterr().err.lower()
