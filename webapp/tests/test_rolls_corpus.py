"""The corpus sweep: SC-002 and SC-003, measured over every real message.

`tests/fixtures/discord/messages.json` holds 615 real messages from the GM's two
campaign channels - every message that carries a digit or an image attachment,
with author ids and display names pseudonymized. Pure chatter is excluded: it is
trivially rejected and is the players' private conversation, not test data.

This file is the measurement the spec's success criteria name. The unit tests in
`test_rolls_parse.py` check the forms we thought of; this one checks the parser
against everything the players actually wrote.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from l7r.repl.rolls.parse import MIN_TOTAL, parse_message
from l7r.repl.rolls.skills import load_skills

FIXTURE = Path(__file__).parent / 'fixtures' / 'discord' / 'messages.json'

#: The number of rolls the parser finds in the corpus today. This is a REGRESSION
#: FIXTURE, not a target: coverage alone cannot prove a parser has teeth, so the
#: count is pinned and any change has to be looked at by a human. Moving it up is
#: usually good (a form we did not handle) and moving it down is usually bad (a
#: form we broke), but either way the diff has to be read before the number is
#: edited. Measured 2026-08-28, after three false positives were found and fixed,
#: and after `@27 Tact` stopped being counted twice (both the total-cluster pattern
#: and the leading-`@` pattern matched it, one character apart). This constant
#: caught that duplicate: it went 124 -> 123 and the drop had to be explained.
EXPECTED_ROLLS = 123


@pytest.fixture(scope='module')
def corpus() -> list[dict[str, Any]]:
    return list(json.loads(FIXTURE.read_text())['messages'])


@pytest.fixture(scope='module')
def words() -> tuple[str, ...]:
    return load_skills()


@pytest.fixture(scope='module')
def swept(corpus: list[dict[str, Any]], words: tuple[str, ...]) -> list[tuple[Any, Any]]:
    out = []
    for message in corpus:
        rolls, problems = parse_message(
            message['content'], words, character=message['author'], message_id=message['id']
        )
        out.append((message, (rolls, problems)))
    return out


def test_the_fixture_is_the_size_it_should_be(corpus: list[dict[str, Any]]) -> None:
    assert len(corpus) == 615


def test_the_roll_count_has_not_moved(swept: list[tuple[Any, Any]]) -> None:
    found = sum(len(rolls) for _, (rolls, _) in swept)
    assert found == EXPECTED_ROLLS, (
        f'the parser now finds {found} rolls in the corpus, not {EXPECTED_ROLLS}. '
        'Read the diff before changing the constant: more is usually a form we did '
        'not handle before, fewer is usually one we just broke.'
    )


def test_every_parsed_roll_is_structurally_sound(
    swept: list[tuple[Any, Any]], words: tuple[str, ...]
) -> None:
    """SC-002: nothing is parsed WRONGLY, as far as structure can tell."""
    for message, (rolls, _) in swept:
        for roll in rolls:
            assert roll.skill in words, f'{roll.skill!r} is not a skill: {message["content"]!r}'
            assert roll.total >= MIN_TOTAL, f'total below the floor: {message["content"]!r}'
            assert roll.total < 1000
            assert roll.rank is None or 0 <= roll.rank <= 5
            assert roll.source == 'typed'
            assert roll.message_id == message['id']


def test_the_measured_false_positives_stay_gone(swept: list[tuple[Any, Any]]) -> None:
    """The three real mis-parses the first implementation produced (research.md R3)."""
    by_content = {m['content']: rolls for m, (rolls, _) in swept}
    for fragment, forbidden in (
        ('31+15acting', 'acting'),
        ('Intimidation 8k4', 'interrogation'),
    ):
        for content, rolls in by_content.items():
            if fragment in content:
                assert not any(r.skill == forbidden for r in rolls), (
                    f'{fragment!r} parsed as {forbidden} again: {content!r}'
                )
    for content, rolls in by_content.items():
        if '15 Acting)' in content:
            assert [r.skill for r in rolls] == ['sincerity']


def test_no_date_or_ring_score_is_read_as_a_roll(swept: list[tuple[Any, Any]]) -> None:
    """SC-003, on the negatives that look most like rolls."""
    for message, (rolls, _) in swept:
        content = message['content']
        if 'December 2022' in content or 'sessions in the' in content:
            assert rolls == [], f'read a roll out of {content!r}'
        if 'Fire 5, Air 4' in content:
            assert rolls == [], f'read a ring score as a roll: {content!r}'


def test_problems_are_rare_enough_to_read(swept: list[tuple[Any, Any]]) -> None:
    """A report the GM cannot read is the same as no report.

    If this fires, the parser has started reporting rather than deciding, which is
    a different failure from parsing wrongly and wants a different fix.
    """
    problems = sum(len(found) for _, (_, found) in swept)
    assert problems <= 10, f'{problems} problems reported across the corpus'


def test_no_roll_is_attributed_to_an_empty_character(swept: list[tuple[Any, Any]]) -> None:
    for message, (rolls, _) in swept:
        for roll in rolls:
            assert roll.character == message['author']
            assert roll.attributed
