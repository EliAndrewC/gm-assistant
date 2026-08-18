"""`tools/jogs.py` - the by-hand report for bunds that step sideways and carry on."""

import json

from l7r.diagram.tools.jogs import jogs, main

_STEPPED = [[0.0, 0.0], [60.0, 0.0], [60.0, 9.0], [200.0, 9.0], [200.0, 100.0], [0.0, 100.0]]
_STRAIGHT = [[0.0, 0.0], [200.0, 0.0], [200.0, 100.0], [0.0, 100.0]]


def _M(rings, ftpx=1.0):
    return {"meta": {"ftpx": ftpx}, "fields": [{"name": "f", "plot_rings": rings}]}


def test_jogs_reports_the_step_with_its_size_in_real_feet():
    found = jogs(_M([_STEPPED]))
    assert len(found) == 1
    x, y, step, name = found[0]
    assert (round(x), round(y)) == (60, 4)
    assert round(step) == 9  # at ftpx 1 a pixel is a foot
    assert name == "f"


def test_jogs_says_nothing_about_a_straight_wall():
    assert jogs(_M([_STRAIGHT])) == []


def test_jogs_converts_the_step_by_the_maps_own_scale():
    # THE UNIT IS THE POINT OF THE CONVERSION: the same drawn ring is a 9 ft step on a hamlet and a
    # 27 ft one on a provincial city, and a report in pixels would say neither.
    assert round(jogs(_M([_STEPPED], ftpx=3.0))[0][2]) == 27


def test_jogs_skips_a_field_that_records_no_plot_rings():
    assert jogs({"meta": {"ftpx": 1.0}, "fields": [{"name": "f"}]}) == []
    assert jogs({"meta": {}}) == []


def test_main_exits_nonzero_when_it_finds_one_and_zero_when_it_does_not(tmp_path, capsys):
    bad, good = tmp_path / "bad.json", tmp_path / "good.json"
    bad.write_text(json.dumps(_M([_STEPPED])))
    good.write_text(json.dumps(_M([_STRAIGHT])))
    assert main([str(bad)]) == 1
    assert "1 step(s) in 1 plot ring(s)" in capsys.readouterr().out
    assert main([str(good), "--top", "2"]) == 0
