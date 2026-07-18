"""Tests for the /calendar SKILL.md parser.

These lock the parser against the shapes that actually occur in the source: the
optional Gregorian parenthetical, body-less day entries (the 12th month lists
four bare headers), a meaning that itself contains quotes (4th month), and the
month-head block of `Seasonal color` / `Flowers of ...` lines. If the GM edits
the calendar into a shape the parser silently drops, the count assertions here
are what catch it.
"""

from __future__ import annotations

import textwrap

import pytest

import calendar_data as C


@pytest.fixture(scope="module")
def cal():
    return C.parse_calendar()


def test_all_twelve_months_present(cal):
    assert sorted(cal) == list(range(1, 13))


def test_month_header_fields(cal):
    mo = cal[3]
    assert (mo["name"], mo["meaning"], mo["zodiac"]) == ("Yayoi", "new life", "Serpent")
    assert mo["span"] == "5 April - 5 May"


def test_meaning_with_embedded_quotes_kept_intact(cal):
    """4th month is `("unohana" or "deutzia")` - stripping outer quotes would corrupt it."""
    assert cal[4]["meaning"] == '"unohana" or "deutzia"'


def test_every_month_has_meta_and_intro(cal):
    for n, mo in cal.items():
        assert mo["meta"], f"month {n} lost its Seasonal color / Flowers lines"
        assert mo["intro"], f"month {n} lost its intro prose"
        assert all(k.startswith(("Seasonal", "Flowers")) for k, _ in mo["meta"])


def test_day_count_matches_source(cal):
    """56 `Nth Day` headers in SKILL.md; none may be swallowed by the head block."""
    assert sum(len(mo["days"]) for mo in cal.values()) == 56


def test_day_with_gregorian_date(cal):
    d = cal[2]["days"][12]
    assert d["greg"] == "18 Mar"
    assert d["title"] == "Haru Higan (Haru Higan festival)"
    assert d["body"] and "Vernal Equinox" in d["body"][0]


def test_day_without_gregorian_date(cal):
    d = cal[1]["days"][5]
    assert d["greg"] == ""
    assert d["title"] == "Joui (Bestowal of ranks)"
    assert len(d["body"]) == 3


def test_bodyless_day_entries(cal):
    """Month 12 lists Shoukan/Fuyu no douyou/Daikan with no prose beneath."""
    assert cal[12]["days"][1]["body"] == []
    assert cal[9]["days"][13]["body"] == []
    # ...but the last entry of that month does have prose, so parsing continued.
    assert cal[12]["days"][30]["body"]


def test_days_are_in_range(cal):
    for n, mo in cal.items():
        for dn in mo["days"]:
            assert 1 <= dn <= 30, f"month {n} day {dn} out of range"


@pytest.mark.parametrize("title,expected", [
    ("Joui (Bestowal of ranks)", "Joui"),
    ("Haru Higan (Haru Higan festival)", "Haru Higan"),
    ("End of Haru Higan", "End of Haru Higan"),
    ("Wakana no sekku or Nanakusa no sekku (Festival of Young Herbs)",
     "Wakana no sekku or Nanakusa no sekku"),
    # Interior parentheses must survive; only a trailing gloss is dropped.
    ("Shuubun (Autumnal Equinox), Hojoe (The Great Liberation), and Kangetsu",
     "Shuubun (Autumnal Equinox), Hojoe (The Great Liberation), and Kangetsu"),
    ("(all gloss)", "(all gloss)"),  # never strip down to nothing
])
def test_short_title(title, expected):
    assert C.short_title(title) == expected


def test_parses_a_synthetic_month(tmp_path):
    """Whole-shape check on a minimal file, independent of the real SKILL.md."""
    src = tmp_path / "SKILL.md"
    src.write_text(textwrap.dedent("""\
        preamble that must be ignored

        5th Month: Satsuki ("sprout"), Month of the Goat
        6 June - 6 July
        Seasonal color: Iris combination
        Flowers of Satsuki: ayame iris

        Intro paragraph one.
        Intro paragraph two.

        1st Day (6 Jun): Houshu (seed sowing)
        Body of the first day.

        5th Day: Ayame no sekku
        """))
    cal = C.parse_calendar(src)
    mo = cal[5]
    assert mo["meaning"] == "sprout"
    assert mo["meta"] == [("Seasonal color", "Iris combination"),
                          ("Flowers of Satsuki", "ayame iris")]
    assert mo["intro"] == ["Intro paragraph one.", "Intro paragraph two."]
    assert mo["days"][1] == {"day": 1, "greg": "6 Jun",
                             "title": "Houshu (seed sowing)",
                             "body": ["Body of the first day."]}
    assert mo["days"][5]["body"] == []
