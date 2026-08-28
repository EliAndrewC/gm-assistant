"""Splicing the roll line into an Obsidian Portal bio, under the portrait."""

from __future__ import annotations

import pytest

from l7r.repl.rolls.bio import already_present, splice

#: A real bio opening, captured from the campaign (research.md R10) - note the
#: doubled space inside the embed and the CRLF line endings Obsidian Portal writes.
REAL = (
    '[[File:1515940  | class=media-item-align-none | Tsuruchi.png]]\r\n'
    '\r\n'
    'He is a man of few words.\r\n'
    '\r\n'
    'h3. Wish Lists and Goals\r\n'
)

LINE = 'Sadakichi / Moriko etiquette: 35 / 25'


class TestSplice:
    def test_goes_directly_under_the_portrait(self) -> None:
        out = splice(REAL, LINE)
        head, rest = out.split(LINE, 1)
        assert head.startswith('[[File:1515940')
        # Nothing but blank space between the embed and the line.
        assert head.replace('[[File:1515940  | class=media-item-align-none | Tsuruchi.png]]', '')
        assert 'He is a man of few words.' in rest

    def test_preserves_every_existing_character(self) -> None:
        out = splice(REAL, LINE)
        for fragment in (
            '[[File:1515940  | class=media-item-align-none | Tsuruchi.png]]',
            'He is a man of few words.',
            'h3. Wish Lists and Goals',
        ):
            assert fragment in out

    def test_does_not_split_a_crlf_pair(self) -> None:
        # The first implementation produced `\r\n\r\r\n` here: an anchored `\s*$`
        # pattern matched before the `\n` having already consumed the `\r`.
        assert '\r\r' not in splice(REAL, LINE)

    def test_is_idempotent(self) -> None:
        once = splice(REAL, LINE)
        assert splice(once, LINE) == once

    def test_a_record_with_no_portrait_gets_the_line_at_the_top(self) -> None:
        out = splice('Just some prose.', LINE)
        assert out.startswith(LINE)
        assert 'Just some prose.' in out

    def test_an_empty_bio_becomes_the_line(self) -> None:
        assert splice('', LINE) == LINE
        assert splice('   \r\n', LINE) == LINE

    def test_anchors_on_the_first_embed_not_a_later_one(self) -> None:
        two = (
            '[[File:1 | portrait.png]]\r\n\r\nProse.\r\n\r\n[[File:2 | a-map.png]]\r\n\r\nMore.\r\n'
        )
        out = splice(two, LINE)
        assert out.index(LINE) < out.index('[[File:2')

    def test_an_embed_with_no_trailing_newline_still_works(self) -> None:
        out = splice('[[File:1 | portrait.png]]', LINE)
        assert out.startswith('[[File:1 | portrait.png]]')
        assert LINE in out

    def test_refuses_an_empty_line(self) -> None:
        with pytest.raises(ValueError, match='refusing to splice an empty line'):
            splice(REAL, '   ')


class TestAlreadyPresent:
    def test_finds_an_identical_line(self) -> None:
        assert already_present(splice(REAL, LINE), LINE)

    def test_ignores_surrounding_whitespace(self) -> None:
        assert already_present(f'x\r\n  {LINE}  \r\ny', LINE)

    def test_false_when_absent(self) -> None:
        assert not already_present(REAL, LINE)
