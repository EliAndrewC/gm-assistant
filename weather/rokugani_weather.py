#!/usr/bin/env python3
"""Look up the weather and moon for a Rokugani calendar date.

Give it a Rokugani month and day; it translates to the matching Gregorian date
in the saved weather year, then reports that night's sky and the moon phase.

Calendar translation (from the /calendar skill notes):
  - 360-day year, twelve 30-day lunar months.
  - Day 1 of the year (1st of Mutsuki) = Risshun, anchored at 4 February.
  - So each Rokugani date is a fixed offset from 4 Feb; no per-year lunar drift.
  Because a 360-day year anchored at 4 Feb runs a few days into the following
  January, late-year dates wrap back to the same weather year (the data is one
  representative year used as climatology, so this is intentional).

Moon phase (from the same notes): the month begins on the new moon (day 1) and
the full moon falls on the 15th. We model illumination as a simple triangle
between those fixed anchors, matching how the setting's moon actually behaves.

Usage:
    python3 rokugani_weather.py <month 1-12> <day 1-30>
    python3 rokugani_weather.py 3 2
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from build_weather_csv import condition, local_clock

WEATHER_YEAR = 2015
RAW_FILE = Path(__file__).parent / "raw" / f"roanoke-rapids-{WEATHER_YEAR}.json"
YEAR_START = date(WEATHER_YEAR, 2, 4)  # 1st of Mutsuki = Risshun

# N: (zodiac, traditional name, meaning)
MONTHS = {
    1: ("Hare", "Mutsuki", "affection"),
    2: ("Dragon", "Kisaragi", "changing"),
    3: ("Serpent", "Yayoi", "new life"),
    4: ("Horse", "Uzuki", "unohana month"),
    5: ("Goat", "Satsuki", "sprout-planting month"),
    6: ("Monkey", "Minazuki", "waterless month"),
    7: ("Rooster", "Fumizuki", "poetry month"),
    8: ("Dog", "Hazuki", "leaf month"),
    9: ("Boar", "Nagatsuki", "long month"),
    10: ("Rat", "Kaminazuki", "month of the gods"),
    11: ("Ox", "Shimotsuki", "frost month"),
    12: ("Tiger", "Shiwasu", "priests running"),
}


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def to_gregorian(month: int, day: int) -> date:
    """Rokugani (month, day) -> Gregorian date within the weather year."""
    offset = (month - 1) * 30 + (day - 1)
    g = YEAR_START + timedelta(days=offset)
    # Wrap any roll into the next January back onto the same weather year.
    return date(WEATHER_YEAR, g.month, g.day)


def moon(day: int) -> tuple[str, int, str]:
    """Phase name, rough illumination %, and a one-line night-sky note."""
    if day <= 15:
        illum = round((day - 1) / 14 * 100)
    else:
        illum = round((30 - day) / 15 * 100)

    if day in (1, 30):
        name, note = "new moon", "moonless - the moon rides with the sun; the night is dark"
    elif day <= 6:
        name, note = "waxing crescent", "a thin evening moon that sets soon after dusk; late night is dark"
    elif day <= 8:
        name, note = "first quarter", "half-moon overhead at dusk, setting near midnight"
    elif day <= 14:
        name, note = "waxing gibbous", "a bright moon up for most of the night, setting before dawn"
    elif day == 15:
        name, note = "full moon", "a full moon up all night, rising at sunset and setting at dawn"
    elif day <= 21:
        name, note = "waning gibbous", "the early night is dark; a bright moon rises later and lingers past dawn"
    elif day <= 23:
        name, note = "last quarter", "no moon in the evening; a half-moon rises around midnight"
    else:
        name, note = "waning crescent", "a dark evening; a thin moon rises only in the small hours before dawn"

    return name, illum, note


def night_clouds(raw: dict, target: date) -> tuple[float, int, int, str, str]:
    """Mean/min/max hourly cloud cover from sunset to next sunrise, plus the times."""
    daily = raw["daily"]
    hourly = raw["hourly"]
    offset = int(raw["utc_offset_seconds"])
    tz = ZoneInfo(raw.get("timezone", "America/New_York"))

    tstr = target.isoformat()
    nstr = date(WEATHER_YEAR, *(target + timedelta(days=1)).timetuple()[1:3]).isoformat()

    i = daily["time"].index(tstr)
    sunset_raw = daily["sunset"][i]
    j = daily["time"].index(nstr)
    sunrise_raw = daily["sunrise"][j]

    # Hourly times share the file's fixed offset, so compare the raw strings
    # directly for hour selection; only convert for display.
    set_hm = sunset_raw[11:16]
    rise_hm = sunrise_raw[11:16]
    vals = []
    for iso, c in zip(hourly["time"], hourly["cloud_cover"]):
        if c is None:
            continue
        if iso.startswith(tstr) and iso[11:16] >= set_hm:
            vals.append(int(c))
        elif iso.startswith(nstr) and iso[11:16] <= rise_hm:
            vals.append(int(c))

    mean = sum(vals) / len(vals)
    sunset_disp = local_clock(sunset_raw, offset, tz)
    sunrise_disp = local_clock(sunrise_raw, offset, tz)
    return mean, min(vals), max(vals), sunset_disp, sunrise_disp


def describe_sky(mean: float) -> str:
    if mean >= 88:
        return "solid overcast"
    if mean >= 60:
        return "mostly cloudy"
    if mean >= 30:
        return "partly cloudy"
    if mean >= 12:
        return "mostly clear"
    return "clear"


def report(month: int, day: int) -> str:
    zodiac, name, meaning = MONTHS[month]
    target = to_gregorian(month, day)
    raw = json.loads(RAW_FILE.read_text())
    daily = raw["daily"]
    i = daily["time"].index(target.isoformat())

    high = round(daily["temperature_2m_max"][i])
    low = round(daily["temperature_2m_min"][i])
    precip = round(daily["precipitation_sum"][i], 2)
    cond = condition(daily["weather_code"][i])
    nmean, nmin, nmax, sunset, sunrise = night_clouds(raw, target)
    phase, illum, moon_note = moon(day)

    greg = datetime(WEATHER_YEAR, target.month, target.day).strftime("%A, %B %-d, %Y")

    lines = [
        f"{ordinal(day)} day of the {ordinal(month)} month "
        f"- {name} ({meaning}), Month of the {zodiac}",
        f"  Gregorian analog: {greg}  (from the {WEATHER_YEAR} weather set)",
        "",
        f"  Night sky:   {describe_sky(nmean)} - {nmean:.0f}% mean cloud cover "
        f"(ranged {nmin}-{nmax}%) from sunset to sunrise",
        f"  Sun:         set {sunset}, rose {sunrise}",
        f"  Moon:        {phase} (~{illum}% lit) - {moon_note}",
        f"  Day's high/low: {high}/{low} F     Precip: {precip} in     Daytime: {cond}",
    ]
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Usage: python3 rokugani_weather.py <month 1-12> <day 1-30>")
    try:
        month, day = int(sys.argv[1]), int(sys.argv[2])
    except ValueError:
        sys.exit("Month and day must be numbers, e.g. 3 2")
    if not 1 <= month <= 12:
        sys.exit("Month must be 1-12")
    if not 1 <= day <= 30:
        sys.exit("Day must be 1-30")
    print(report(month, day))


if __name__ == "__main__":
    main()
