"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import os
import tempfile

from settlement import Settlement
from tests.settlement._builders import _crop_settlement, _town


def test_finish_writes_svg_json_and_renders_png():
    # finish() must pair a .png with the .svg automatically (the render step that used to be a
    # forgettable manual command); render=False writes only the source files.
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        s = _town()
        s.finish(base, render=False)
        assert os.path.exists(base + ".svg") and os.path.exists(base + ".json")
        assert not os.path.exists(base + ".png")
        s.finish(base)  # default render=True -> resvg produces the PNG
        assert os.path.exists(base + ".png")


def test_set_view_records_meta_and_crops_viewbox():
    # a city map crops tight to the walls: set_view records the window in meta (the checks read
    # it as the map edge) and finish() rewrites the SVG viewBox to that window. The title follows
    # the view so it stays on-canvas.
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, "t")
        s = Settlement(3000, 2000, seed=1)
        s.set_view(500, 400, 1000, 800)
        assert s.M["meta"]["view"] == [500, 400, 1000, 800]
        s.title("Edo")
        s.finish(base, render=False)
        with open(base + ".svg") as _f:
            svg = _f.read()
        assert 'viewBox="500 400 1000 800"' in svg and 'viewBox="0 0 3000 2000"' not in svg


def test_box_clear_detects_rect_poly_and_line_obstacles():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 500, "y": 500, "w": 40, "h": 30}]  # rect obstacle
    s.M["dry_plots"] = [{"poly": [[300, 300], [340, 300], [340, 340], [300, 340]]}]  # poly -> bbox'd into rects
    s.M["fields"] = [{"outline": [[600, 600], [800, 600], [800, 800], [600, 800]]}]  # polygon obstacle
    s.M["village_groves"] = [{"poly": [[1000, 1000], [1050, 1000], [1050, 1050], [1000, 1050]], "role": "copse"}]
    s.M["commons"] = [{"poly": [[50, 50], [80, 50], [80, 80], [50, 80]]}]
    s.M["streams"] = [{"poly": [[900, 100], [900, 900]]}]  # line obstacle
    s.M["lanes"] = [{"pts": [[1200, 100], [1200, 500]]}]
    obs = s._title_obstacles()
    assert s._box_clear(150, 150, 200, 180, obs) is True  # a blank patch
    assert s._box_clear(485, 490, 515, 510, obs) is False  # on the house (rect)
    assert s._box_clear(650, 650, 750, 750, obs) is False  # inside the field (poly)
    assert s._box_clear(880, 400, 920, 440, obs) is False  # across the stream (line)


def test_title_lands_over_blank_space_avoiding_the_field():
    s = _crop_settlement()
    s.set_view(0, 0, 2000, 1500)
    s.M["fields"] = [{"outline": [[200, 200], [1800, 200], [1800, 1300], [200, 1300]], "vis_bbox": [200, 200, 1800, 1300]}]
    s.M["houses"] = [{"x": 100, "y": 100, "w": 40, "h": 30}]
    s.title("Testville")
    tb = s.M["title"]["bbox"]
    assert tb[2] <= 200 or tb[0] >= 1800 or tb[3] <= 200 or tb[1] >= 1300  # clear of the field blob


def test_title_falls_back_to_the_corner_when_no_blank_space():
    s = _crop_settlement()
    s.set_view(0, 0, 200, 150)  # a tiny window...
    s.M["fields"] = [{"outline": [[-10, -10], [210, -10], [210, 160], [-10, 160]]}]  # ...covered entirely
    s.title("X")
    assert s.M["title"]["bbox"][0] == 30  # fell back to view left + 30


def test_title_without_a_view_centers_on_the_canvas():
    s = _crop_settlement()  # no set_view -> self.view is None
    s.M["fields"] = [{"outline": [[-10, -10], [2010, -10], [2010, 1510], [-10, 1510]]}]  # full-canvas cover -> no gap
    s.title("Y")
    tb = s.M["title"]["bbox"]
    assert abs((tb[0] + tb[2]) / 2 - 1000) < 2  # centered on W/2 = 1000


def test_text_width_measures_the_render_font_and_falls_back(monkeypatch):
    # the placard pads symmetrically because the width is MEASURED in the render font (DejaVu Serif
    # Bold, what resvg substitutes for serif) - 'Akagahara' measured ~180px where the old estimate
    # said 167 and ran off the card edge (GM 2026-07-21). Without PIL/the font, a generous estimate.
    s = _crop_settlement()
    w = s._text_width("Akagahara", 30)
    assert 170 < w < 195
    import PIL.ImageFont

    def _boom(*a, **k):
        raise OSError("no font")

    monkeypatch.setattr(PIL.ImageFont, "truetype", _boom)
    assert s._text_width("Akagahara", 30) == 9 * 30 * 0.62


def test_text_width_is_pinned_to_the_basic_layout_engine():
    # A title placard is sized from this measurement and RECORDED in the manifest, so the pool is
    # only byte-reproducible if the measurement depends on the font file alone. PIL otherwise picks
    # its layout engine by what the container has installed - RAQM where libraqm is present, BASIC
    # where it is not - and the two disagree in both directions at the sub-pixel level. A container
    # rebuild after a laptop crash (2026-07-25) gained libraqm and thereby dirtied all 16 titled pool
    # manifests with no code change behind it. These exact numbers are the BASIC ones the committed
    # manifests were built with; a failure here means the pin came loose (or PIL changed BASIC), and
    # it must be resolved deliberately - regenerating the pool - not by editing the expectations.
    s = _crop_settlement()
    assert s._text_width("Honda", 30) == 110.0
    assert s._text_width("Hoshizora", 30) == 170.0
    assert s._text_width("Tango", 30) == 103.953125


def test_late_water_block_carries_sheens_and_splices_after_plots():
    """field_channel(late=True) defers into the SECOND water block (spliced at its own first-call
    position so a city's comb net draws OVER the field's plots); a late course with a sheen records
    its sheenz above every late bed, mirroring the main block's contract."""
    s = Settlement(300, 300, seed=1)
    s.meta(name="T", scale="village", ftpx=2)
    rec: dict = {}
    s._water('<path d="M0,0 L10,10" stroke="#6C9CBE"/>', rec, sheen='<path d="M0,0 L10,10" stroke="#9CC"/>', late=True)
    with tempfile.TemporaryDirectory() as td:
        s.finish(os.path.join(td, "t"), render=False)
    assert rec["sheenz"] > rec["bedz"]


def test_label_takes_the_linear_clamp_only_when_the_subject_is_a_line():
    s = _town()
    s.label(500, 500, "Imperial Road", 12, rot=-26.6, linear=True)
    s.label(500, 600, "Imperial Road", 12, rot=72, linear=True)  # a near north-south road
    s.label(500, 700, "tanning yard", 9, rot=72)  # ...the same angle on a BOX subject
    recs = s.M["labels"]
    assert recs[0][7] == -26.6
    assert len(recs[1]) == 6  # level: no element [7], so the record keeps the exact pre-tilt format
    assert recs[2][7] == -18.0  # the fold, which is what a rotated building wants and a road does not


def test_label_rot_emits_a_center_rotation_and_appends_the_tilt():
    s = _town()
    s.label(500, 500, "tilted", 9, rot=150)  # a caller passes the FEATURE rotation; label() folds it
    L = s.M["labels"][-1]
    assert len(L) == 8 and L[6] is None and L[7] == -30.0
    assert any('transform="rotate(-30.0' in t for t in s.toplabels)
    s.label(500, 550, "level", 9, rot=90)  # a square rotation folds level: record format unchanged
    assert len(s.M["labels"][-1]) == 6
