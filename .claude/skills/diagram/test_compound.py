"""Tests for compound.py (feature 008 - feet-first program + perimeter-first placer)."""

from __future__ import annotations

import compound as c


def _env(w: float = 200.0, h: float = 200.0, div: float = 100.0, gate: float = 13.0) -> c.Envelope:
    return c.Envelope(w, h, div, gate)


def _b(name: str, w: float, h: float, court: str, wall: str, order: int = 0, rank: int = 1) -> c.BuildingSpec:
    return c.BuildingSpec(name, "service", w, h, court, wall, order, rank)


def test_courtzone_and_placed_props() -> None:
    z = c.CourtZone("g", 10, 20, 30, 40)
    assert (z.x2, z.y2) == (40, 60)
    p = c.Placed(_b("x", 10, 20, "outer", "S"), 5, 6)
    assert (p.x2, p.y2) == (15, 26)


def test_place_hugs_each_wall() -> None:
    env = _env()
    prog = c.CompoundProgram(
        "t",
        env,
        (),
        (
            _b("N", 20, 10, "inner", "N"),
            _b("Souter", 20, 10, "outer", "S"),
            _b("W", 10, 20, "inner", "W"),
            _b("E", 10, 20, "inner", "E"),
            _b("divout", 30, 10, "outer", "divider"),
            _b("divin", 30, 10, "inner", "divider"),
        ),
    )
    pos = {p.spec.name: (p.x_ft, p.y_ft) for p in c.place(prog).placed}
    assert pos["N"][1] == 0.0
    assert pos["Souter"][1] == env.h_ft - 10
    assert pos["W"][0] == 0.0
    assert pos["E"][0] == env.w_ft - 10
    assert pos["divout"][1] == env.divider_ft
    assert pos["divin"][1] == env.divider_ft - 10


def test_place_fire_gap_between_same_wall_buildings() -> None:
    prog = c.CompoundProgram("t", _env(), (), (_b("a", 20, 10, "inner", "N", 2), _b("b", 20, 10, "inner", "N", 1)))
    xs = sorted(p.x_ft for p in c.place(prog).placed)
    assert xs[1] - (xs[0] + 20) == c.FIRE_GAP_FT


def test_place_skips_the_gate_on_the_south_wall() -> None:
    env = _env(w=200.0, gate=40.0)  # gate spans x 80..120
    prog = c.CompoundProgram("t", env, (), (_b("g1", 60, 10, "outer", "S", 2), _b("g2", 60, 10, "outer", "S", 1)))
    placed = {p.spec.name: p for p in c.place(prog).placed}
    assert placed["g2"].x_ft >= 120.0


def test_place_skips_a_spine_court() -> None:
    spine = (c.CourtZone("oshirasu", 40, 0, 60, 30),)  # x 40..100 on the N band
    prog = c.CompoundProgram("t", _env(), spine, (_b("a", 30, 10, "inner", "N", 2), _b("b", 30, 10, "inner", "N", 1)))
    placed = {p.spec.name: p for p in c.place(prog).placed}
    assert placed["b"].x_ft >= 100.0


def test_place_overflow_when_building_too_wide() -> None:
    prog = c.CompoundProgram("t", _env(w=50.0), (), (_b("huge", 80, 10, "inner", "N"),))
    res = c.place(prog)
    assert res.placed == []
    assert [s.name for s in res.overflow] == ["huge"]


def _rects_overlap(a: c.Placed, b: c.Placed) -> bool:
    return c._rect_overlap(a.x_ft, a.y_ft, a.spec.w_ft, a.spec.h_ft, b.x_ft, b.y_ft, b.spec.w_ft, b.spec.h_ft)


def test_place_ns_row_owns_the_corner_and_ew_column_flows_below() -> None:
    # The N row (higher tier) takes the NW corner; the W column flows below it, not overlapping.
    prog = c.CompoundProgram("t", _env(w=200.0), (), (_b("wwall", 40, 20, "inner", "W"), _b("nwall", 30, 10, "inner", "N")))
    p = {x.spec.name: x for x in c.place(prog).placed}
    assert p["nwall"].x_ft == 3.0 and p["nwall"].y_ft == 0.0  # N owns the corner
    assert p["wwall"].x_ft == 0.0 and p["wwall"].y_ft >= p["nwall"].y2  # W flows below
    assert not _rects_overlap(p["nwall"], p["wwall"])


def test_divider_hall_centers_between_the_ew_columns() -> None:
    # A long divider hall is placed AFTER the E/W columns, so it slides past the W column
    # instead of hogging the left corner (the office-hall-behind-oshirasu case).
    prog = c.CompoundProgram(
        "t",
        _env(w=200.0),
        (),
        (_b("hall", 120, 12, "outer", "divider", order=10), _b("wkura", 30, 20, "outer", "W", order=6), _b("ekura", 30, 20, "outer", "E", order=6)),
    )
    p = {x.spec.name: x for x in c.place(prog).placed}
    assert p["wkura"].x_ft == 0.0 and p["ekura"].x2 == 200.0
    assert p["hall"].x_ft >= p["wkura"].x2  # hall flows past the W column, not into the corner


def test_second_rank_sits_behind_the_rank1_row_on_each_wall() -> None:
    # rank-2 building is offset inward past the rank-1 row, on all four straight walls.
    env = _env(w=200.0, h=200.0, div=100.0)
    for wall, court in (("N", "inner"), ("S", "outer"), ("W", "inner"), ("E", "inner")):
        prog = c.CompoundProgram("t", env, (), (_b("front", 40, 30, court, wall, order=10, rank=1), _b("rear", 20, 12, court, wall, order=1, rank=2)))
        p = {x.spec.name: x for x in c.place(prog).placed}
        assert not _rects_overlap(p["front"], p["rear"])
        if wall == "N":
            assert p["rear"].y_ft == p["front"].y2 + c.FIRE_GAP_FT
        elif wall == "S":
            assert p["rear"].y2 == p["front"].y_ft - c.FIRE_GAP_FT
        elif wall == "W":
            assert p["rear"].x_ft == p["front"].x2 + c.FIRE_GAP_FT
        else:  # E
            assert p["rear"].x2 == p["front"].x_ft - c.FIRE_GAP_FT


def test_emit_svg_contains_courts_buildings_and_walls() -> None:
    prog = c.county_magistracy_program()
    svg = c.emit_svg(prog, c.place(prog))
    for token in ("<svg", "office hall", "oshirasu", "garden", "url(#court-earth)", "#3F3A30"):
        assert token in svg


def test_county_magistracy_places_without_overflow() -> None:
    res = c.place(c.county_magistracy_program())
    assert res.overflow == []
    assert len(res.placed) == 15


def test_main_writes_a_draft(tmp_path, capsys) -> None:
    out = tmp_path / "d.svg"
    assert c.main([str(out)]) == 0
    assert out.read_text().startswith("<svg")
    assert "buildings placed" in capsys.readouterr().out


def test_main_default_path(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pool" / "magistracies").mkdir(parents=True)
    assert c.main([]) == 0
    assert (tmp_path / "pool" / "magistracies" / "county-magistracy-example.svg").exists()


def test_main_reports_overflow(tmp_path, monkeypatch, capsys) -> None:
    env = c.Envelope(50, 50, 25, 13)
    prog = c.CompoundProgram("t", env, (), (c.BuildingSpec("huge", "service", 80, 10, "inner", "N"),))
    monkeypatch.setattr(c, "county_magistracy_program", lambda: prog)
    c.main([str(tmp_path / "o.svg")])
    assert "OVERFLOW" in capsys.readouterr().out
