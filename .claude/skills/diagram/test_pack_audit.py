"""Tests for pack_audit.py (feature 007 - packing-audit hardening).

Behavior-named, parametrized, over small SYNTHETIC svg strings (not the pool
maps, which change). Covers current behavior (parse/coverage/aligned gaps/maximal
rectangle) plus the new top-N vacant rectangles and per-region density.
"""

from __future__ import annotations

import os

import pytest

import pack_audit as pa

COURT = "url(#court-earth)"
_FIX = os.path.join(os.path.dirname(__file__), "test_fixtures")


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


# --- perimeter_hugging_pct (NEW, feature 008) ---


def test_perimeter_hugging_pct_high_when_buildings_line_the_walls() -> None:
    plan = pa.parse_svg(
        _svg(
            _rect(0, 0, 300, 300, COURT),
            _rect(0, 0, 300, 30, "#DDB87A"),  # top-wall building
            _rect(0, 270, 300, 30, "#DDB87A"),  # bottom-wall building
        )
    )
    assert pa.perimeter_hugging_pct(plan, depth_ft=15) > 0.95


def test_perimeter_hugging_pct_low_when_building_floats_in_the_center() -> None:
    plan = pa.parse_svg(_svg(_rect(0, 0, 300, 300, COURT), _rect(130, 130, 40, 40, "#DDB87A")))
    assert pa.perimeter_hugging_pct(plan, depth_ft=15) < 0.1


def test_perimeter_hugging_pct_zero_when_no_buildings() -> None:
    assert pa.perimeter_hugging_pct(pa.parse_svg(_svg(_rect(0, 0, 100, 100, COURT)))) == 0.0


def test_perimeter_hugging_counts_buildings_backing_an_internal_divider() -> None:
    # a building far from the OUTER walls but backing a divider line is well-placed and should hug
    plan = pa.parse_svg(
        _svg(
            _rect(0, 0, 300, 300, COURT),
            '<g stroke="#3F3A30" stroke-width="6" fill="none"><line x1="0" y1="150" x2="300" y2="150"/></g>',
            _rect(120, 120, 60, 25, "#DDB87A"),  # centered, but its bottom backs the y=150 divider
        )
    )
    assert pa.parse_svg(_svg(_rect(0, 0, 300, 300, COURT))).dividers == ()  # no false dividers
    assert len(plan.dividers) == 1
    assert pa.perimeter_hugging_pct(plan, depth_ft=15) > 0.5


# --- vacant-rect zone (central vs perimeter) (NEW, feature 008) ---


def test_vacant_rect_zone_central_when_ringed_by_wall_buildings() -> None:
    plan = pa.parse_svg(
        _svg(
            _rect(0, 0, 300, 300, COURT),
            _rect(0, 0, 300, 20, "#DDB87A"),
            _rect(0, 280, 300, 20, "#DDB87A"),
            _rect(0, 0, 20, 300, "#DDB87A"),
            _rect(280, 0, 20, 300, "#DDB87A"),
        )
    )
    assert pa.top_vacant_rects(plan, n=1)[0].zone == "central"


def test_vacant_rect_zone_perimeter_when_gap_between_wall_buildings() -> None:
    plan = pa.parse_svg(
        _svg(
            _rect(0, 0, 300, 300, COURT),
            _rect(0, 0, 120, 40, "#DDB87A"),  # top-wall building, left
            _rect(180, 0, 120, 40, "#DDB87A"),  # top-wall building, right
            _rect(0, 40, 300, 260, "#DDB87A"),  # fills the rest; only the top gap is vacant
        )
    )
    assert pa.top_vacant_rects(plan, n=1)[0].zone == "perimeter"


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


# --- fire-water tub adjacency (each gutter-fed tub must sit against a building) ---


def _tubgroup(*circles: str) -> str:
    return f'<g fill="{pa.FIRE_WATER_FILL}" stroke="#3A5060" stroke-width="1">' + "".join(circles) + "</g>"


def test_parse_svg_reads_fire_water_tubs() -> None:
    svg = _svg(_rect(0, 0, 300, 300, COURT), _tubgroup('<circle cx="50" cy="50" r="5"/>', '<circle cx="80" cy="80" r="5"/>'))
    assert len(pa.parse_svg(svg).tubs) == 2


def test_parse_svg_no_tub_group_gives_no_tubs() -> None:
    assert pa.parse_svg(_svg(_rect(0, 0, 300, 300, COURT), _rect(0, 0, 90, 90, "#DDB87A"))).tubs == ()


@pytest.mark.parametrize(
    "px, py, expected",
    [(50, 50, 0.0), (130, 50, 30.0), (50, 140, 40.0), (103, 104, 5.0)],
)
def test_point_rect_dist(px: float, py: float, expected: float) -> None:
    assert pa._point_rect_dist(px, py, pa.Rect(0, 0, 100, 100)) == pytest.approx(expected)


def test_fire_water_adrift_flags_far_and_passes_near() -> None:
    svg = _svg(
        _rect(0, 0, 300, 300, COURT),
        _rect(0, 0, 100, 100, "#DDB87A"),
        _tubgroup('<circle cx="106" cy="50" r="5"/>', '<circle cx="160" cy="90" r="5"/>', '<circle cx="220" cy="90" r="5"/>'),
    )
    adrift = pa.fire_water_adrift(pa.parse_svg(svg))
    # the 106 tub touches the east wall (2 ft) and passes; the other two are adrift, worst first
    assert [round(t.gap_ft, 1) for t in adrift] == [40.0, 20.0]
    assert adrift[0].x == 220


def test_fire_water_adrift_with_no_buildings_flags_every_tub() -> None:
    adrift = pa.fire_water_adrift(pa.parse_svg(_svg(_rect(0, 0, 300, 300, COURT), _tubgroup('<circle cx="50" cy="50" r="5"/>'))))
    assert len(adrift) == 1 and adrift[0].gap_ft == float("inf")


def test_format_report_tub_section_states_each_case() -> None:
    none = pa.format_report(pa.parse_svg(_svg(_rect(0, 0, 200, 200, COURT), _rect(0, 0, 60, 60, "#DDB87A"))))
    assert "no fire-water tubs" in none
    ok = pa.format_report(pa.parse_svg(_svg(_rect(0, 0, 200, 200, COURT), _rect(0, 0, 100, 100, "#DDB87A"), _tubgroup('<circle cx="106" cy="50" r="5"/>'))))
    assert "all 1 tubs sit against" in ok
    bad = pa.format_report(pa.parse_svg(_svg(_rect(0, 0, 200, 200, COURT), _rect(0, 0, 100, 100, "#DDB87A"), _tubgroup('<circle cx="160" cy="50" r="5"/>'))))
    assert "move it to a wall" in bad


# --- round-1 rendering checks: layers, label placement, legibility ---


def _text(x: float, y: float, content: str, extra: str = "") -> str:
    return f'<text x="{x}" y="{y}" {extra}>{content}</text>'


def _wallgroup(*segs: tuple[float, float, float, float]) -> str:
    lines = "".join(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}"/>' for a, b, c, d in segs)
    return f'<g stroke="{pa.WALL_STROKE}" stroke-width="9">{lines}</g>'


@pytest.mark.parametrize(
    "fill, dark",
    [("#000000", True), ("#ffffff", False), ("#3A2E1C", True), ("url(#g)", False), ("#abc", False)],
)
def test_luma_classifies_dark(fill: str, dark: bool) -> None:
    assert (pa._luma(fill) < pa.LABEL_DARK_LUMA) == dark


def test_parse_labels_bbox_anchor_bold_and_skips() -> None:
    svg = _svg(
        _rect(0, 0, 300, 300, COURT),
        _text(100, 50, "AB", 'font-size="10" text-anchor="middle" font-weight="bold"'),
        _text(100, 80, "AB", 'font-size="10" text-anchor="end"'),
        _text(0, 100, "x&amp;y <tspan>z</tspan>"),  # entity + inner tag stripped
        '<text y="10">no-x</text>',  # missing x -> skipped
        _text(200, 200, "   "),  # blank -> skipped
    )
    labs = {lab.text: lab for lab in pa.parse_svg(svg).labels}
    assert set(labs) == {"AB", "x&y z"}  # blank + missing-x skipped, entity decoded, tag stripped
    bold = [lab for lab in pa.parse_svg(svg).labels if lab.text == "AB" and lab.y < 45][0]
    assert bold.x == pytest.approx(100 - (2 * 10 * pa.CHAR_W_BOLD) / 2)  # middle anchor, bold width
    end = [lab for lab in pa.parse_svg(svg).labels if lab.text == "AB" and lab.y > 70][0]
    assert end.x == pytest.approx(100 - 2 * 10 * pa.CHAR_W_FRAC)  # end anchor, regular width


def test_parse_reads_walls_wells_and_dark_blocks() -> None:
    svg = _svg(
        _rect(0, 0, 300, 300, COURT),
        _wallgroup((0, 0, 300, 0)),
        _rect(50, 50, 22, 22, pa.WELL_FILL),
        _rect(100, 100, 20, 20, "#2D2A24"),  # dark block (area 400 >= 150)
        _rect(200, 200, 5, 5, "#2D2A24"),  # dark but tiny (area 25) -> not a dark block
    )
    plan = pa.parse_svg(svg)
    assert len(plan.wall_segs) == 1 and len(plan.wells) == 1 and len(plan.dark_rects) == 1


def test_occlusion_flags_later_feature_over_label_and_tub() -> None:
    # a label then a building drawn LATER on top of it; a tub then a garden on top
    svg = _svg(
        _rect(0, 0, 400, 400, COURT),
        _text(20, 60, "buried", 'font-size="12"'),  # pos early
        _tubgroup('<circle cx="200" cy="200" r="5"/>'),
        _rect(10, 40, 90, 40, "#DDB87A"),  # building drawn later, over the label
        _rect(180, 180, 60, 40, "url(#garden-stipple)"),  # garden drawn later, over the tub
    )
    occ = pa.occluded_foreground(pa.parse_svg(svg))
    kinds = {(o.kind, o.text) for o in occ}
    assert ("label", "buried") in kinds and ("tub", "") in kinds


def test_occlusion_ignores_feature_drawn_before_or_barely_touching() -> None:
    svg = _svg(
        _rect(0, 0, 400, 400, COURT),
        _rect(10, 40, 90, 40, "#DDB87A"),  # building BEFORE the label -> label on top, fine
        _text(20, 60, "ontop", 'font-size="12"'),
        _text(300, 60, "clear", 'font-size="12"'),  # not over anything
        _rect(392, 40, 40, 40, "#DDB87A"),  # later, but only grazes 'clear' by <min_px
    )
    assert pa.occluded_foreground(pa.parse_svg(svg)) == []


def test_orphan_group_label_far_flagged_near_ok_and_no_glyphs_skipped() -> None:
    far = _svg(_rect(0, 0, 400, 400, COURT), _text(20, 20, "fire-water tubs"), _tubgroup('<circle cx="300" cy="300" r="5"/>'))
    assert pa.orphan_group_labels(pa.parse_svg(far))[0].text == "fire-water tubs"
    near = _svg(_rect(0, 0, 400, 400, COURT), _text(20, 20, "fire-water tubs"), _tubgroup('<circle cx="40" cy="30" r="5"/>'))
    assert pa.orphan_group_labels(pa.parse_svg(near)) == []
    noglyph = _svg(_rect(0, 0, 400, 400, COURT), _text(20, 20, "fire-water tubs"))  # no tub group -> can't judge
    assert pa.orphan_group_labels(pa.parse_svg(noglyph)) == []
    other = _svg(_rect(0, 0, 400, 400, COURT), _text(20, 20, "kitchen"))  # not a group label
    assert pa.orphan_group_labels(pa.parse_svg(other)) == []


def test_gate_openings_finds_gaps_both_axes() -> None:
    svg = _svg(
        _rect(0, 0, 400, 400, COURT),
        _wallgroup((0, 400, 150, 400), (200, 400, 400, 400), (0, 0, 0, 150), (0, 190, 0, 400)),
    )
    ops = {(round(x), round(y)) for x, y in pa._gate_openings(pa.parse_svg(svg))}
    assert (175, 400) in ops  # south gap 150->200 = 50
    assert (0, 170) in ops  # west gap 150->190 = 40


def test_gate_openings_ignores_a_wide_gap() -> None:
    svg = _svg(_rect(0, 0, 400, 400, COURT), _wallgroup((0, 400, 100, 400), (300, 400, 400, 400)))
    assert pa._gate_openings(pa.parse_svg(svg)) == []  # gap 200 >= 80 is not a gate


def test_notice_board_far_from_gate_flagged() -> None:
    svg = _svg(
        _rect(0, 0, 400, 400, COURT),
        _wallgroup((0, 400, 180, 400), (220, 400, 400, 400)),  # gate opening at (200,400)
        _text(50, 60, "notice board"),  # far up in the NW, far from the south gate
    )
    assert pa.notice_board_adrift(pa.parse_svg(svg))[0].gap_ft > pa.NOTICE_BOARD_MAX_FT


def test_notice_board_near_gate_and_no_wall_and_no_board() -> None:
    near = _svg(_rect(0, 0, 400, 400, COURT), _wallgroup((0, 400, 180, 400), (220, 400, 400, 400)), _text(200, 395, "notice board", 'text-anchor="middle"'))
    assert pa.notice_board_adrift(pa.parse_svg(near)) == []
    nowall = _svg(_rect(0, 0, 400, 400, COURT), _text(50, 60, "notice board"))  # no gate openings at all
    assert pa.notice_board_adrift(pa.parse_svg(nowall)) == []
    noboard = _svg(_rect(0, 0, 400, 400, COURT), _wallgroup((0, 400, 180, 400), (220, 400, 400, 400)), _text(50, 60, "well"))
    assert pa.notice_board_adrift(pa.parse_svg(noboard)) == []


def test_dark_on_dark_over_rect_and_wall_with_nudge() -> None:
    over_rect = _svg(_rect(0, 0, 400, 400, COURT), _rect(80, 40, 60, 40, "#2D2A24"), _text(90, 60, "dim", 'font-size="12" fill="#3A2E1C"'))
    hit = pa.dark_on_dark_labels(pa.parse_svg(over_rect))
    assert hit and hit[0].fixable and (hit[0].nudge_dx_ft or hit[0].nudge_dy_ft)
    over_wall = _svg(_rect(0, 0, 400, 400, COURT), _wallgroup((100, 0, 100, 400)), _text(80, 60, "onwall", 'font-size="12" fill="#3A2E1C"'))
    assert pa.dark_on_dark_labels(pa.parse_svg(over_wall))


def test_dark_on_dark_skips_light_labels_and_clear_labels() -> None:
    light = _svg(_rect(0, 0, 400, 400, COURT), _rect(80, 40, 60, 40, "#2D2A24"), _text(90, 60, "pale", 'font-size="12" fill="#FFFAE6"'))
    assert pa.dark_on_dark_labels(pa.parse_svg(light)) == []
    clear = _svg(_rect(0, 0, 400, 400, COURT), _rect(300, 300, 40, 40, "#2D2A24"), _text(20, 60, "away", 'font-size="12" fill="#3A2E1C"'))
    assert pa.dark_on_dark_labels(pa.parse_svg(clear)) == []


def test_dark_on_dark_unfixable_when_dark_everywhere() -> None:
    boxed = _svg(_rect(0, 0, 400, 400, COURT), _rect(0, 0, 300, 300, "#2D2A24"), _text(120, 120, "trapped", 'font-size="12" fill="#3A2E1C"'))
    hit = pa.dark_on_dark_labels(pa.parse_svg(boxed))
    assert hit and not hit[0].fixable and hit[0].nudge_dx_ft == 0.0 and hit[0].nudge_dy_ft == 0.0


def test_format_report_layer_sections() -> None:
    clean = pa.format_report(pa.parse_svg(_svg(_rect(0, 0, 200, 200, COURT), _rect(0, 0, 60, 60, "#DDB87A"))))
    assert "labels/tubs on top: OK" in clean
    dirty = pa.format_report(
        pa.parse_svg(
            _svg(
                _rect(0, 0, 400, 400, COURT),
                _text(20, 60, "buried", 'font-size="12"'),
                _rect(10, 40, 90, 40, "#DDB87A"),
                _text(20, 20, "fire-water tubs"),
                _tubgroup('<circle cx="300" cy="300" r="5"/>'),
                _wallgroup((0, 400, 180, 400), (220, 400, 400, 400)),
                _text(50, 90, "notice board"),
                _rect(60, 300, 60, 40, "#2D2A24"),
                _text(70, 320, "dim", 'fill="#3A2E1C"'),
            )
        )
    )
    for token in ("BURIED", "ORPHAN LABEL", "NOTICE BOARD", "DARK-ON-DARK"):
        assert token in dirty


def test_layout_checks_fire_on_frozen_ochiba_fixture() -> None:
    with open(os.path.join(_FIX, "ochiba-layout-red.svg")) as fh:
        plan = pa.parse_svg(fh.read())
    occ = {(o.kind, o.text) for o in pa.occluded_foreground(plan)}
    assert ("label", "RESIDENCE") in occ  # the buried 'R'
    assert ("tub", "") in occ  # the buried guest-room tub
    assert any("fire-water" in o.text for o in pa.orphan_group_labels(plan))
    assert pa.notice_board_adrift(plan)  # notice board far from the gate


def test_layout_checks_fire_on_frozen_hayakawa_fixture() -> None:
    with open(os.path.join(_FIX, "hayakawa-layout-red.svg")) as fh:
        plan = pa.parse_svg(fh.read())
    assert pa.dark_on_dark_labels(plan)  # river door / guest-wing annotation over the wall
    assert pa.notice_board_adrift(plan)
    assert pa.occluded_foreground(plan)  # 'service gate' clipped
