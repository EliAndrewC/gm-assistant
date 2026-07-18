"""Tests for the dream-scene band randomizer."""

from __future__ import annotations

import random
from collections import Counter

import pytest

from randomize_bands import (
    MEANINGFUL,
    PINNED_FACE,
    assign_bands,
    format_table,
    main,
)


def test_all_ten_faces_are_assigned_exactly_once() -> None:
    mapping = assign_bands({'none': 2, 'unrelated': 2}, random.Random(0))
    assert sorted(mapping) == list(range(1, 11))


def test_pinned_face_is_always_meaningful() -> None:
    for seed in range(50):
        mapping = assign_bands({'none': 3, 'unrelated': 3}, random.Random(seed))
        assert mapping[PINNED_FACE] == MEANINGFUL


def test_band_counts_are_respected_with_remainder_to_meaningful() -> None:
    mapping = assign_bands({'none': 2, 'unrelated': 2}, random.Random(1))
    counts = Counter(mapping.values())
    assert counts['none'] == 2
    assert counts['unrelated'] == 2
    # remaining faces, including the pinned 10, fall to meaningful
    assert counts[MEANINGFUL] == 6


def test_misleading_band_is_supported() -> None:
    mapping = assign_bands(
        {'none': 3, 'unrelated': 2, 'misleading': 1}, random.Random(2)
    )
    counts = Counter(mapping.values())
    assert counts['misleading'] == 1
    assert counts[MEANINGFUL] == 4


def test_zero_non_meaningful_bands_makes_everything_meaningful() -> None:
    mapping = assign_bands({}, random.Random(3))
    assert set(mapping.values()) == {MEANINGFUL}
    assert len(mapping) == 10


def test_filling_all_nine_free_faces_is_allowed() -> None:
    mapping = assign_bands({'none': 9}, random.Random(4))
    counts = Counter(mapping.values())
    assert counts['none'] == 9
    assert counts[MEANINGFUL] == 1  # only the pinned face


def test_overfilling_raises() -> None:
    with pytest.raises(ValueError, match='only 9 are free'):
        assign_bands({'none': 8, 'unrelated': 2}, random.Random(0))


def test_negative_count_raises() -> None:
    with pytest.raises(ValueError, match='non-negative'):
        assign_bands({'none': -1}, random.Random(0))


def test_pinned_band_may_not_be_passed_explicitly() -> None:
    with pytest.raises(ValueError, match='pinned band'):
        assign_bands({MEANINGFUL: 1}, random.Random(0))


def test_pinned_face_must_be_a_die_face() -> None:
    with pytest.raises(ValueError, match='not among the die faces'):
        assign_bands({}, random.Random(0), faces=(1, 2, 3), pinned_face=10)


def test_randomization_varies_across_seeds() -> None:
    a = assign_bands({'none': 2, 'unrelated': 2}, random.Random(1))
    b = assign_bands({'none': 2, 'unrelated': 2}, random.Random(7))
    # Different seeds should (with these counts) produce different scatters.
    assert a != b


def test_format_table_lists_every_face_in_order() -> None:
    mapping = assign_bands({'none': 2, 'unrelated': 2}, random.Random(0))
    table = format_table(mapping)
    lines = table.splitlines()
    assert lines[0].startswith('face')
    face_column = [line.split('|')[0].strip() for line in lines[2:]]
    assert face_column == [str(face) for face in range(1, 11)]


def test_format_table_handles_empty_mapping() -> None:
    assert 'face | band' in format_table({})


def test_main_seeded_is_reproducible_and_prints_a_table() -> None:
    first = main(['--none', '2', '--unrelated', '2', '--seed', '42'])
    second = main(['--none', '2', '--unrelated', '2', '--seed', '42'])
    assert first == second
    assert 'meaningful' in first


def test_main_with_misleading_flag() -> None:
    out = main(['--none', '3', '--unrelated', '2', '--misleading', '1', '--seed', '5'])
    assert 'misleading' in out
