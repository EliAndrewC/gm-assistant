"""Tests for the portrait-cropping half of chargen.art.

The regression fixture `art_full_body_profile.png` is Otomo Kagemaru's actual
generated portrait, downloaded from Obsidian Portal on 2026-09-01 after the GM
reported that his headshot showed his chest instead of his head. The figure
stands in three-quarter profile looking away, so OpenCV's FRONTAL cascade never
sees the face - and it does find a false positive in the scale-pattern chest
tattoo, which the old code then cropped as the "headshot". Both properties of
that image matter, so it is kept byte-for-byte.
"""

from pathlib import Path

import numpy as np
import pytest

from chargen import art

_FIXTURES = Path(__file__).resolve().parent / 'fixtures'

# Where the face actually is in the fixture: the profile cascade's box, as
# (left, top, right, bottom). The old code cropped (146, 221, 133, 145) - a
# rectangle that does not overlap this box at all.
FACE_BOX = (114, 73, 252, 211)
FACE_HEIGHT = FACE_BOX[3] - FACE_BOX[1]


@pytest.fixture
def full_body_profile() -> bytes:
    path = _FIXTURES / 'art_full_body_profile.png'
    return path.read_bytes()


def test_crop_finds_a_head_turned_away_from_the_camera(full_body_profile: bytes) -> None:
    x, y, width, height = art.get_headshot_crop(full_body_profile)
    left, top, right, bottom = FACE_BOX

    assert x <= left
    assert x + width >= right
    assert y <= top
    assert y + height >= bottom
    # And it is a HEADSHOT: a crop several times taller than the face it found
    # is a torso with a head on it, which is what the GM saw on 2026-09-01.
    assert height <= FACE_HEIGHT * 3


def test_crop_falls_back_to_the_head_end_of_a_faceless_figure() -> None:
    """No detection at all must still crop a HEAD-sized region off the top.

    The old fallback took the top HALF of the image, which on a standing
    full-body portrait (roughly 1:2.5) is everything down to the waist.
    """
    import cv2

    blank = np.full((1000, 400, 3), 200, np.uint8)
    encoded = cv2.imencode('.png', blank)[1].tobytes()

    x, y, width, height = art.get_headshot_crop(encoded)

    assert y == 0
    assert height <= width * 2
    assert x + width <= 400
    assert y + height <= 1000


def test_crop_headshot_returns_the_requested_region(full_body_profile: bytes) -> None:
    import cv2

    cropped = art.crop_headshot(full_body_profile, 100, 50, 120, 140)
    decoded = cv2.imdecode(np.frombuffer(cropped, np.uint8), cv2.IMREAD_COLOR)

    assert decoded is not None
    assert decoded.shape[:2] == (140, 120)


def test_the_frontal_box_wins_where_the_cascades_agree() -> None:
    """Both cascades saw one head, so crop to the tighter frontal reading."""
    frontal = (200, 100, 100, 100)
    profile = (180, 80, 160, 160)

    assert art._pick_face([(0, frontal), (2, profile)]) == frontal


def test_a_profile_head_beats_a_frontal_false_positive_lower_down() -> None:
    """Kagemaru's case in miniature: the boxes are nowhere near each other, so
    they are different faces, and the higher one is the head."""
    head = (114, 73, 138, 138)
    tattoo = (182, 257, 61, 61)

    assert art._pick_face([(0, tattoo), (2, head)]) == head
