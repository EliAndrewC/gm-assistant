"""Tests for the range-report helpers that are pure logic.

`range_label` is the interesting one: it decides how briefly a Rokugani date
range can be stated. The rule is per-END - name days only where the range starts
or stops mid-month - so the four combinations of whole/partial ends each need
covering, plus the single-month collapse and the year-wrap guard.
"""

from __future__ import annotations

import pytest

import weather_range as R


@pytest.mark.parametrize("sm,sd,em,ed,expected", [
    # Whole single month -> no day numbers at all.
    (1, 1, 1, 30, "1st month"),
    (12, 1, 12, 30, "12th month"),
    # Whole span of months -> just the endpoints, pluralised.
    (2, 1, 4, 30, "2nd - 4th months"),
    (1, 1, 12, 30, "1st - 12th months"),
    (11, 1, 12, 30, "11th - 12th months"),
    # Partial within one month -> days only, month named once.
    (1, 5, 1, 20, "5th - 20th of the 1st month"),
    (3, 2, 3, 30, "2nd - 30th of the 3rd month"),
    (3, 1, 3, 29, "1st - 29th of the 3rd month"),
    # Mixed: only the partial end carries day numbers.
    (2, 5, 4, 30, "5th of the 2nd month - 4th month"),
    (2, 1, 4, 12, "2nd month - 12th of the 4th month"),
    (2, 5, 4, 12, "5th of the 2nd month - 12th of the 4th month"),
    # Wrapping the new year is just a month span like any other.
    (11, 1, 2, 30, "11th - 2nd months"),
    (11, 7, 2, 3, "7th of the 11th month - 3rd of the 2nd month"),
])
def test_range_label(sm, sd, em, ed, expected):
    assert R.range_label(sm, sd, em, ed) == expected


def test_same_month_backwards_is_a_year_wrap_not_a_backwards_range():
    """sm == em with sd > ed spans ~a full year, so it must NOT collapse to
    "5th - 4th of the 1st month", which would read as a 0-day range."""
    label = R.range_label(1, 5, 1, 4)
    assert label == "5th of the 1st month - 4th of the 1st month"
    assert "5th - 4th" not in label


def test_single_day_range():
    assert R.range_label(6, 9, 6, 9) == "9th - 9th of the 6th month"


def test_every_month_pair_produces_a_nonempty_label():
    for sm in range(1, 13):
        for em in range(1, 13):
            for sd, ed in ((1, 30), (1, 12), (5, 30), (5, 12)):
                assert R.range_label(sm, sd, em, ed).strip()


def test_rok_range_wraps_the_year():
    cells = list(R.rok_range(12, 29, 1, 2))
    assert cells == [(12, 29), (12, 30), (1, 1), (1, 2)]


def test_rok_range_single_day():
    assert list(R.rok_range(4, 7, 4, 7)) == [(4, 7)]


def test_rok_range_full_year():
    assert len(list(R.rok_range(1, 1, 12, 30))) == 360


@pytest.mark.parametrize("raw,want", [
    ("6:34 AM", "6:34a"),
    ("7:05 PM", "7:05p"),
    ("12:00 PM", "12:00p"),
])
def test_compact_time(raw, want):
    assert R.compact_time(raw) == want


@pytest.mark.parametrize("raw,want", [
    ("a & b", "a &amp; b"),
    ("<tag>", "&lt;tag&gt;"),
    ("plain", "plain"),
    ("&<>", "&amp;&lt;&gt;"),
])
def test_esc(raw, want):
    assert R.esc(raw) == want


def test_slug():
    assert R.slug("Shiro Reiji") == "shiro-reiji"
    assert R.slug("Kyuden Doji") == "kyuden-doji"


def test_row_colors_are_all_distinct():
    """The legend is built from this dict, so two entries sharing a value would
    render two swatches the GM cannot tell apart."""
    values = list(R.ROW_COLORS.values())
    assert len(set(values)) == len(values)


def test_rain_and_snow_are_perceptibly_different():
    """Regression guard: these two once differed by 6/255 in their strongest
    channel, which is invisible when scanning the table."""
    def rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

    rain, snow = rgb(R.ROW_COLORS["rain"]), rgb(R.ROW_COLORS["snow"])
    assert max(abs(a - b) for a, b in zip(rain, snow)) >= 15
    # ...and they must differ in HUE, not merely lightness: rain reads blue.
    assert (rain[2] - rain[0]) - (snow[2] - snow[0]) >= 20


@pytest.mark.parametrize("place,expected", [
    # Vassal house: the family is NOT in the name, so name both.
    ({"place": "Shiro Reiji", "clan": "Crab", "family": "Hida"},
     "Hida Family, Crab Clan"),
    # Ruling-family seats: the family IS the name, so the Clan alone.
    ({"place": "Kyuden Kakita", "clan": "Crane", "family": "Kakita"}, "Crane Clan"),
    ({"place": "Shinden Asahina", "clan": "Crane", "family": "Asahina"}, "Crane Clan"),
    ({"place": "Isawa Woodlands", "clan": "Phoenix", "family": "Isawa"}, "Phoenix Clan"),
    # Suppression is case-insensitive.
    ({"place": "Kyuden Doji", "clan": "Crane", "family": "doji"}, "Crane Clan"),
    # No family recorded at all -> Clan only.
    ({"place": "Kyuden Shiba", "clan": "Phoenix"}, "Phoenix Clan"),
    # The Imperial house is not a Clan and never takes the suffix.
    ({"place": "Otosan Uchi", "clan": "Imperial"}, "Imperial"),
    # A partial word must NOT count as a match: "Hid" is not "Hida".
    ({"place": "Shiro Hidden Vale", "clan": "Crab", "family": "Hida"},
     "Hida Family, Crab Clan"),
])
def test_house_label(place, expected):
    assert R.house_label(place) == expected


def test_house_label_on_the_real_registry():
    """Every registered place must produce a sane label - no '?' clans, and the
    Kyuden/Shinden <Family> seats must not repeat their family."""
    import weather as W
    for p in W.load_places():
        label = R.house_label(p)
        assert "?" not in label, p["place"]
        fam = p.get("family")
        if fam and fam.lower() in p["place"].lower().split():
            assert fam not in label, f"{p['place']} repeats its own family"


def test_no_zebra_banding_color_remains():
    """Row shading must mean something: every color in ROW_COLORS is a legend
    entry, so a decorative stripe color must not creep back in."""
    assert "band" not in R.ROW_COLORS
