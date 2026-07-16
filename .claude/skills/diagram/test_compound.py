"""Tests for compound.py (feature 008 - feet-first program + perimeter-first placer)."""

from __future__ import annotations

import compound as c


def _env(w: float = 200.0, h: float = 200.0, div: float = 100.0, gate: float = 13.0) -> c.Envelope:
    return c.Envelope(w, h, div, gate)


def _b(name: str, w: float, h: float, court: str, wall: str, order: int = 0) -> c.BuildingSpec:
    return c.BuildingSpec(name, "service", w, h, court, wall, order)


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


def test_place_corner_reserve_insets_horizontal_rows() -> None:
    prog = c.CompoundProgram("t", _env(w=200.0), (), (_b("wwall", 40, 20, "inner", "W"), _b("nwall", 30, 10, "inner", "N")))
    placed = {p.spec.name: p for p in c.place(prog).placed}
    assert placed["nwall"].x_ft >= 40.0


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
    (tmp_path / "pool").mkdir()
    assert c.main([]) == 0
    assert (tmp_path / "pool" / "county-magistracy-draft.svg").exists()


def test_main_reports_overflow(tmp_path, monkeypatch, capsys) -> None:
    env = c.Envelope(50, 50, 25, 13)
    prog = c.CompoundProgram("t", env, (), (c.BuildingSpec("huge", "service", 80, 10, "inner", "N"),))
    monkeypatch.setattr(c, "county_magistracy_program", lambda: prog)
    c.main([str(tmp_path / "o.svg")])
    assert "OVERFLOW" in capsys.readouterr().out
