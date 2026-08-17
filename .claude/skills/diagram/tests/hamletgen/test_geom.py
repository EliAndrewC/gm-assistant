"""Unit tests for the shared geometry predicates and measures (`hamletgen/geom.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import pytest

from l7r.diagram import hamletgen as hg

from ._builders import SQUARE

# ---- geometry helpers ---------------------------------------------------------------------------


def test_polygon_area_is_the_shoelace_area() -> None:
    assert hg.poly_area(SQUARE) == pytest.approx(600.0 * 600.0)


def test_acreage_is_measured_from_the_plots_not_the_envelope() -> None:
    """One 43,560 sq ft plot is one acre at 1 ft/px, and four of them are four - the conversion has
    to carry ftpx squared, which is the trap `build_comb`'s own `acres` falls into on a hamlet."""
    plot = [(0.0, 0.0), (220.0, 0.0), (220.0, 198.0), (0.0, 198.0)]  # 43,560 px^2
    assert hg.net_acres({"plots": [{"poly": plot}] * 4}, ftpx=1.0) == pytest.approx(4.0)
    assert hg.net_acres({"plots": [{"poly": plot}] * 4}, ftpx=2.0) == pytest.approx(16.0)


def test_centroid_and_unit() -> None:
    assert hg.centroid(SQUARE) == (700.0, 700.0)
    assert hg.unit(0.0, 0.0) == (0.0, 0.0)
    assert hg.unit(3.0, 4.0) == pytest.approx((0.6, 0.8))


def test_a_segment_through_a_polygon_is_detected() -> None:
    assert hg.crosses_poly((0.0, 700.0), (1400.0, 700.0), SQUARE)
    assert not hg.crosses_poly((0.0, 100.0), (1400.0, 100.0), SQUARE)


def test_a_segment_passing_near_a_disc_is_detected() -> None:
    assert hg.crosses_disc((0.0, 0.0), (100.0, 0.0), (50.0, 10.0), r=20.0)
    assert not hg.crosses_disc((0.0, 0.0), (100.0, 0.0), (50.0, 40.0), r=20.0)


def test_a_point_is_pulled_back_out_of_an_obstacle() -> None:
    inside = (700.0, 700.0)
    out = hg.pull_clear(inside, (200.0, 200.0), [SQUARE], margin=10.0, step=40.0)
    assert not hg.point_in_poly(out[0], out[1], SQUARE)


def test_pull_clear_gives_up_rather_than_looping_forever() -> None:
    """A point that cannot escape in the tries allowed is returned as it stands. The caller clamps
    to the canvas afterward, so a stuck point degrades the belt's shape - it does not hang."""
    huge = [(-1e5, -1e5), (1e5, -1e5), (1e5, 1e5), (-1e5, 1e5)]
    assert hg.pull_clear((0.0, 0.0), (1.0, 1.0), [huge], margin=10.0) is not None
