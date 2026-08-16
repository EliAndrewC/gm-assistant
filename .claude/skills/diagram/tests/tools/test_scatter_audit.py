"""Tests for scatter_audit.py (feature 108) - written RED-first against the contract in
specs/108-review-loop-efficiency/contracts/scatter-audit-cli.md.

Fixture strategy (research.md R5): parse/adjudication logic is fed SVG text + manifest dicts
directly (the pure-logic surface); the real engine renders a miniature settlement for the
integration case so the audit and the engine provably agree; `main` is exercised through tmp
files. The committed pool bytes are never touched."""

import json

import pytest

from settlement import Settlement
from tools import scatter_audit as sa


def _mini_channel_settlement(seed: int = 1) -> Settlement:
    """A tiny real-engine map: one wide drawn lateral + commons scatter laid over its ground."""
    s = Settlement(600, 800, seed=seed)
    s.meta(name="A", scale="village", ftpx=1.0)  # ftpx recorded, as every real pool map records it
    s.field_channel([(300, 100), (310, 700)], "#6C9CBE", 14.0, 14.0)
    s.commons([(60, 60), (560, 60), (560, 760), (60, 760)], role="grazing")
    return s


def _manifest(**kw):
    m = {"meta": {"ftpx": 1.0}, "streams": [], "channels": [], "drawn_channels": [], "fields": [], "dry_plots": []}
    m.update(kw)
    return m


# ---- parsing ---------------------------------------------------------------------------------


def test_parse_counts_every_family_from_engine_emission():
    s = _mini_channel_settlement()
    fams = sa.parse_bases("".join(s.out))
    assert len(fams["blade"]) > 100  # grazing commons = tufts of 3 blades each
    assert len(fams["dot"]) > 0
    assert len(fams["pine"]) > 0  # role="grazing" draws scraggly pines
    assert fams["blade"] and all(isinstance(x, float) for x, _ in fams["blade"])


def test_parse_counts_one_base_per_blade_line_three_per_tuft():
    svg = '<g stroke="#A7A860" stroke-width="0.8"><line x1="10.0" y1="20.0" x2="10.5" y2="16.0"/><line x1="10.0" y1="20.0" x2="9.4" y2="16.2"/><line x1="10.0" y1="20.0" x2="10.1" y2="15.9"/></g>'
    fams = sa.parse_bases(svg)
    assert fams["blade"] == [(10.0, 20.0)] * 3  # one BasePoint per blade line, tips ignored


def test_parse_reeds_pine_trunks_and_crowns_but_not_companion_ink():
    svg = (
        '<g stroke="#6E9377" stroke-width="0.8"><line x1="5.0" y1="6.0" x2="5.0" y2="2.0"/></g>'
        '<line x1="40.0" y1="50.0" x2="40.0" y2="38.0" stroke="#7A6A48" stroke-width="1.1"/>'  # pine trunk
        '<line x1="40.0" y1="44.0" x2="37.0" y2="46.0" stroke="#6E8452" stroke-width="1.0"/>'  # branch: ignored
        '<circle cx="80.0" cy="90.0" r="8.0" fill="#7C9856" stroke="#4C6234" stroke-width="0.7"/>'  # crown
        '<circle cx="77.4" cy="87.4" r="3.4" fill="#A6BA79" fill-opacity="0.55"/>'  # highlight: ignored
        '<ellipse cx="80.0" cy="92.0" rx="8.0" ry="5.8" fill="#59703E" fill-opacity="0.30"/>'  # shadow: ignored
        '<circle cx="60.0" cy="61.0" r="2.0" fill="#94A063" fill-opacity="0.85"/>'  # brush dot
    )
    fams = sa.parse_bases(svg)
    assert fams["reed"] == [(5.0, 6.0)]
    assert fams["pine"] == [(40.0, 50.0)]
    assert fams["crown"] == [(80.0, 90.0)]
    assert fams["dot"] == [(60.0, 61.0)]
    assert fams["blade"] == []


# ---- adjudication ----------------------------------------------------------------------------


def _one_dot_svg(x, y):
    return f'<circle cx="{x}" cy="{y}" r="2.0" fill="#94A063" fill-opacity="0.85"/>'


def test_adjudicate_flags_a_base_inside_the_cut_bank_margin():
    m = _manifest(drawn_channels=[{"pts": [[100, 100], [100, 700]], "w0": 14.0, "w1": 14.0}])
    report = sa.adjudicate(sa.parse_bases(_one_dot_svg(110.0, 400.0)), m, "t")  # 10 px off center: inside 7+2+6
    assert [v["keepout"] for v in report["violations"]] == ["water+cutbank"]
    assert report["violations"][0]["family"] == "dot"


def test_adjudicate_accepts_the_same_base_beyond_the_margin():
    m = _manifest(drawn_channels=[{"pts": [[100, 100], [100, 700]], "w0": 14.0, "w1": 14.0}])
    report = sa.adjudicate(sa.parse_bases(_one_dot_svg(118.0, 400.0)), m, "t")  # 18 px: outside 15
    assert report["violations"] == []


def test_adjudicate_margins_scale_with_ftpx():
    # The same dot 13 px off the centerline: at ftpx=2 the 6 ft margin is 3 px (keep-out 7+2+3=12,
    # clean); at ftpx=1 it is 6 px (keep-out 15, violation). The engine's px() decides, not this test.
    chan = [{"pts": [[100, 100], [100, 700]], "w0": 14.0, "w1": 14.0}]
    coarse = sa.adjudicate(sa.parse_bases(_one_dot_svg(113.0, 400.0)), _manifest(meta={"ftpx": 2.0}, drawn_channels=chan), "t")
    assert coarse["violations"] == []
    fine = sa.adjudicate(sa.parse_bases(_one_dot_svg(113.0, 400.0)), _manifest(drawn_channels=chan), "t")
    assert [v["keepout"] for v in fine["violations"]] == ["water+cutbank"]


def test_adjudicate_flags_crop_margin_violations_from_fields_outline_and_dry_plots_poly():
    m = _manifest(
        fields=[{"outline": [[200, 200], [300, 200], [300, 300], [200, 300]]}],
        dry_plots=[{"poly": [[400, 400], [460, 400], [460, 460], [400, 460]], "crop": "barley", "theta": 0}],
    )
    svg = _one_dot_svg(304.0, 250.0) + _one_dot_svg(464.0, 430.0) + _one_dot_svg(320.0, 250.0)
    report = sa.adjudicate(sa.parse_bases(svg), m, "t")
    assert [v["keepout"] for v in report["violations"]] == ["crop", "crop"]  # 4 px < 6 ft margin; 20 px clear


def test_reeds_are_counted_but_never_adjudicated():
    m = _manifest(drawn_channels=[{"pts": [[100, 100], [100, 700]], "w0": 14.0, "w1": 14.0}])
    svg = '<g stroke="#6E9377"><line x1="104.0" y1="400.0" x2="104.0" y2="396.0"/></g>'  # ON the water edge
    report = sa.adjudicate(sa.parse_bases(svg), m, "t")
    assert report["violations"] == []
    assert report["counts"]["reed"] == 1
    assert "reed" not in report["families_checked"]["adjudicated"]


def test_tapered_lateral_margin_follows_the_piece_widths():
    # An 8-point tapered lateral (w0=14 head, w1=5 tail) slices into the engine's 7-piece width
    # ladder: at the HEAD the piece runs ~13.4 wide (keep-out ~14.7), at the TAIL ~5.6 (keep-out
    # ~10.8). The same 12 px offset therefore violates at the head and is legal at the tail -
    # proving the margin follows the water's real edge down the taper.
    pts = [[100, y] for y in (100, 186, 271, 357, 443, 529, 614, 700)]
    m = _manifest(drawn_channels=[{"pts": pts, "w0": 14.0, "w1": 5.0}])
    report = sa.adjudicate(sa.parse_bases(_one_dot_svg(112.0, 120.0) + _one_dot_svg(112.0, 690.0)), m, "t")
    assert [(v["y"], v["keepout"]) for v in report["violations"]] == [(120.0, "water+cutbank")]


def test_density_bands_count_bases_just_beyond_the_water_keepout():
    m = _manifest(drawn_channels=[{"pts": [[100, 100], [100, 700]], "w0": 14.0, "w1": 14.0}])
    svg = _one_dot_svg(120.0, 300.0) + _one_dot_svg(135.0, 300.0) + _one_dot_svg(150.0, 300.0) + _one_dot_svg(400.0, 300.0)
    report = sa.adjudicate(sa.parse_bases(svg), m, "t")
    assert report["density_bands"] == {"0-15": 1, "15-30": 1, "30-45": 1}  # the far dot is in no band


def test_engine_scatter_passes_its_own_audit():
    # The integration lock: the engine's post-cut-bank-fix scatter and the audit's engine-derived
    # keep-outs must agree - a clean mini map audits clean.
    s = _mini_channel_settlement()
    report = sa.adjudicate(sa.parse_bases("".join(s.out)), s.M, "mini")
    assert report["violations"] == []
    assert report["counts"]["blade"] > 100


# ---- CLI -------------------------------------------------------------------------------------


def _write_map(tmp_path, svg_body, manifest):
    (tmp_path / "t.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800">{svg_body}</svg>')
    (tmp_path / "t.json").write_text(json.dumps(manifest))
    return str(tmp_path / "t")


def test_main_clean_map_exits_zero_with_report(tmp_path, capsys):
    stem = _write_map(tmp_path, _one_dot_svg(400.0, 300.0), _manifest(drawn_channels=[{"pts": [[100, 100], [100, 700]], "w0": 14.0, "w1": 14.0}]))
    assert sa.main([stem]) == 0
    out = capsys.readouterr().out
    assert "violations: 0" in out and "checked:" in out


@pytest.mark.parametrize("suffix", ["", ".json", ".svg"])
def test_main_resolves_stem_json_and_svg_paths(tmp_path, suffix):
    stem = _write_map(tmp_path, _one_dot_svg(400.0, 300.0), _manifest())
    assert sa.main([stem + suffix]) == 0


def test_main_violations_exit_one_and_are_listed(tmp_path, capsys):
    stem = _write_map(tmp_path, _one_dot_svg(110.0, 400.0), _manifest(drawn_channels=[{"pts": [[100, 100], [100, 700]], "w0": 14.0, "w1": 14.0}]))
    assert sa.main([stem]) == 1
    assert "VIOLATION family=dot" in capsys.readouterr().out


def test_main_json_emits_the_report_object(tmp_path, capsys):
    stem = _write_map(tmp_path, _one_dot_svg(400.0, 300.0), _manifest())
    assert sa.main([stem, "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert set(report) == {"map", "families_checked", "counts", "violations", "density_bands"}


def test_main_zero_bases_is_a_loud_failure(tmp_path, capsys):
    stem = _write_map(tmp_path, "<rect x='1' y='1' width='5' height='5'/>", _manifest())
    assert sa.main([stem]) == 2
    assert "ERROR" in capsys.readouterr().err


def test_main_missing_artifacts_exit_two(tmp_path, capsys):
    assert sa.main([str(tmp_path / "absent")]) == 2
    (tmp_path / "only.json").write_text("{}")
    assert sa.main([str(tmp_path / "only")]) == 2
    assert sa.main([]) == 2  # usage


def test_main_missing_ftpx_exits_two(tmp_path, capsys):
    stem = _write_map(tmp_path, _one_dot_svg(400.0, 300.0), {"meta": {}})
    assert sa.main([stem]) == 2
    assert "ftpx" in capsys.readouterr().err
