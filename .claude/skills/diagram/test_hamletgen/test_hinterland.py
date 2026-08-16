"""Unit tests for the ground between everything - open-ground scan, woodland, windbreak (`hamletgen/hinterland.py`).

Split from test_hamletgen.py by feature 111; test bodies verbatim. See hamletgen/CLAUDE.md.
"""

import pytest

import hamletgen as hg

from ._builders import SQUARE


def test_a_square_far_from_the_crop_clears_and_one_on_it_does_not() -> None:
    assert hg._clear_gap((700.0, 700.0), 50.0, [SQUARE], 1.0) is None  # standing in it
    assert hg._clear_gap((700.0, 200.0), 50.0, [SQUARE], 1.0) == pytest.approx(150.0)
    assert hg._clear_gap((700.0, 1100.0), 50.0, [SQUARE], 1.0) is None  # in the crop's sunny shadow
    assert hg._clear_gap((700.0, 700.0), 50.0, [], 1.0) is None  # no crop at all - nothing to measure


def test_a_square_near_a_line_is_detected() -> None:
    assert hg._near_line((100.0, 100.0), 20.0, [(0.0, 100.0), (200.0, 100.0)], pad=10.0)
    assert not hg._near_line((100.0, 400.0), 20.0, [(0.0, 100.0), (200.0, 100.0)], pad=10.0)
