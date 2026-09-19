"""Feature 207: every rollable name has exactly one mode."""

from __future__ import annotations

from l7r.repl.rolls import modes
from l7r.repl.rolls.skills import load_skills


def test_every_vocabulary_entry_has_a_mode() -> None:
    """The safety property: a skill added to the rules must be DECIDED, not defaulted.

    Reads the rules file, so it fails the day the rules grow a skill this table has
    not heard of.
    """
    missing = [skill for skill in load_skills() if skill not in modes.MODES]
    assert not missing, f'no mode decided for: {", ".join(missing)}'


def test_no_mode_is_decided_for_a_name_the_rules_do_not_have() -> None:
    assert set(modes.MODES) <= set(load_skills())


def test_no_skill_is_listed_twice() -> None:
    listed = [skill for _, skills in modes._GROUPS for skill in skills]
    assert len(listed) == len(set(listed))


def test_the_gm_s_rulings() -> None:
    assert modes.mode_of('Pontificate') == 'always_open'
    assert modes.mode_of('athletics') == 'always_open'
    assert modes.mode_of('manipulation') == 'contested_required'
    assert modes.mode_of('sneaking') == 'contested_maybe_unopposed'
    assert modes.mode_of('interrogation') == 'hidden'
    assert modes.mode_of('acting') == 'hidden'
    assert modes.mode_of('etiquette') == 'exempt'
    for skill in ('bragging', 'intimidation', 'culture', 'heraldry', 'history', 'underworld'):
        assert modes.mode_of(skill) == 'default_open', skill


def test_investigation_was_moved_to_default_open() -> None:
    assert modes.mode_of('investigation') == 'default_open'


def test_the_other_half_of_each_pairing_is_not_presumed_contested() -> None:
    assert modes.mode_of('sincerity') == 'full_menu'
    assert modes.mode_of('tact') == 'full_menu'


def test_an_unknown_name_gets_the_full_menu() -> None:
    assert modes.mode_of('basketweaving') == 'full_menu'


def test_default_outcomes() -> None:
    assert modes.default_outcome('Interrogation') == 'nothing hidden detected'
    assert modes.default_outcome('acting') == 'no signs of the persona being seen through'
    assert modes.default_outcome('law') == ''


def test_the_unrolled_total_is_fifteen() -> None:
    assert modes.UNROLLED_TOTAL == 15
