#!/usr/bin/env python3
"""Rokugani weather lookup, place-aware, with day and night reports.

Two report modes, both anchored in real recorded weather for the place's
climate analog (see SKILL.md and places.jsonl):

    python3 weather.py "Shiro Reiji" 3 3            # full day: morning/afternoon/evening
    python3 weather.py reiji 3 2 --night           # evening + overnight only

The script emits the factual breakdown plus a NOTES block of grounded context
(how the day compares to the seasonal norm; overcast / dry streaks). The skill
invoker turns those NOTES into a sentence of natural color commentary - the
numbers are computed here so the commentary can never be invented. Snow lines
appear only when there is snow. For a multi-day HTML table, see weather_range.py.

Calendar and moon come from the /calendar skill (see MONTH_STARTS): 360-day
year, twelve 30-day months anchored to canonical Gregorian starts; new moon on
day 1, full moon on day 15.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from build_weather_csv import condition, local_clock

HERE = Path(__file__).parent
REGISTRY = HERE / "places.jsonl"
RAW_DIR = HERE / "raw"

OVERCAST_PCT = 80  # daily mean cloud at/above this reads as an "overcast day"
WET_IN = 0.01  # daily precip at/above this counts as measurable rain
SNOW_IN = 0.1  # snowfall or depth at/above this (inches) is worth reporting

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

# Gregorian (month, day) each Rokugani month begins on. Canon: identical in the
# /calendar skill's notes and the GM's date-mapping doc. The 360-day Rokugani
# year is stretched across the ~365-day Gregorian year so months stay locked to
# the real seasons - do NOT reintroduce a naive 30-day-from-4-Feb count, which
# drifts ~6 days behind by autumn. Each month is a clean 30-day run from its
# start; Gregorian spans are 29-32 days, so a day or two can land in a gap (or a
# 1-day overlap) at boundaries - immaterial for a lookup.
MONTH_STARTS = {
    1: (2, 4), 2: (3, 6), 3: (4, 5), 4: (5, 6), 5: (6, 6), 6: (7, 7),
    7: (8, 8), 8: (9, 8), 9: (10, 8), 10: (11, 7), 11: (12, 7), 12: (1, 5),
}

# Factors to convert Open-Meteo length/precip units to inches (units vary by
# request: here snowfall came back in inch, snow_depth in ft).
_TO_INCH = {"inch": 1.0, "in": 1.0, "cm": 0.393701, "mm": 0.0393701, "ft": 12.0, "m": 39.3701}


def load_places() -> list[dict]:
    return [json.loads(line) for line in REGISTRY.read_text().splitlines() if line.strip()]


def find_place(query: str) -> dict | None:
    places = load_places()
    q = query.strip().lower()
    for p in places:
        if p["place"].lower() == q:
            return p
    matches = [p for p in places if q in p["place"].lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        sys.exit(f"'{query}' is ambiguous: {', '.join(p['place'] for p in matches)}")
    return None


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def to_gregorian(month: int, day: int, year: int) -> date:
    """Rokugani (month, day) -> Gregorian date within the weather year."""
    gmonth, gday = MONTH_STARTS[month]
    g = date(year, gmonth, gday) + timedelta(days=day - 1)
    return date(year, g.month, g.day)  # wrap any roll into next January back onto this year


def moon(day: int) -> tuple[str, int, str]:
    illum = round((day - 1) / 14 * 100) if day <= 15 else round((30 - day) / 15 * 100)
    if day in (1, 30):
        return "new moon", illum, "moonless - the moon rides with the sun; the night is dark"
    if day <= 6:
        return "waxing crescent", illum, "a thin evening moon that sets soon after dusk; late night is dark"
    if day <= 8:
        return "first quarter", illum, "half-moon overhead at dusk, setting near midnight"
    if day <= 14:
        return "waxing gibbous", illum, "a bright moon up for most of the night, setting before dawn"
    if day == 15:
        return "full moon", illum, "a full moon up all night, rising at sunset and setting at dawn"
    if day <= 21:
        return "waning gibbous", illum, "the early night is dark; a bright moon rises later and lingers past dawn"
    if day <= 23:
        return "last quarter", illum, "no moon in the evening; a half-moon rises around midnight"
    return "waning crescent", illum, "a dark evening; a thin moon rises only in the small hours before dawn"


def describe_sky(mean: float) -> str:
    if mean >= 88:
        return "overcast"
    if mean >= 60:
        return "mostly cloudy"
    if mean >= 30:
        return "partly cloudy"
    if mean >= 12:
        return "mostly clear"
    return "clear"


def hourly_local(raw: dict) -> list[dict]:
    """Hourly rows in true-local time (DST-correct), all depths/precip in inches."""
    offset = int(raw["utc_offset_seconds"])
    tz = ZoneInfo(raw.get("timezone", "America/New_York"))
    src = timezone(timedelta(seconds=offset))
    h = raw["hourly"]
    units = raw.get("hourly_units", {})
    sf_k = _TO_INCH.get(units.get("snowfall", "inch"), 1.0)
    sd_k = _TO_INCH.get(units.get("snow_depth", "m"), 39.3701)
    snowfall = h.get("snowfall") or [0.0] * len(h["time"])
    depth = h.get("snow_depth") or [0.0] * len(h["time"])
    out = []
    for iso, t, c, p, sf, sd in zip(h["time"], h["temperature_2m"], h["cloud_cover"],
                                    h["precipitation"], snowfall, depth):
        dt = datetime.fromisoformat(iso).replace(tzinfo=src).astimezone(tz)
        out.append({
            "dt": dt, "temp": t, "cloud": c, "precip": p,
            "snowfall": (sf or 0.0) * sf_k, "depth": (sd or 0.0) * sd_k,
        })
    return out


def group_by_date(records: list[dict]) -> dict[date, list[dict]]:
    by: dict[date, list[dict]] = {}
    for r in records:
        by.setdefault(r["dt"].date(), []).append(r)
    return by


def daily_cloud(records: list[dict]) -> dict[date, float]:
    by = group_by_date(records)
    return {d: sum(r["cloud"] for r in rows) / len(rows) for d, rows in by.items()}


def period(records: list[dict], day: date, h_start: int, h_end: int) -> dict | None:
    rows = [r for r in records if r["dt"].date() == day and h_start <= r["dt"].hour < h_end]
    if not rows:
        return None
    temps = [r["temp"] for r in rows]
    return {
        "tmin": round(min(temps)),
        "tmax": round(max(temps)),
        "cloud": sum(r["cloud"] for r in rows) / len(rows),
        "precip": round(sum(r["precip"] for r in rows), 2),
    }


def snow_day(rows: list[dict]) -> dict | None:
    """Snow summary for a set of hourly rows, or None if there's no meaningful snow."""
    if not rows:
        return None
    new = sum(r["snowfall"] for r in rows)
    depths = [r["depth"] for r in rows]
    peak = max(depths)
    if new < SNOW_IN and peak < SNOW_IN:
        return None
    return {"new": new, "start": depths[0], "end": depths[-1], "peak": peak}


def describe_snow(s: dict) -> str:
    """Human phrase for a snow_day() result: new snow + ground depth, accumulation/melt."""
    new, start, end, peak = s["new"], s["start"], s["end"], s["peak"]
    bits = []
    if new >= SNOW_IN:
        bits.append(f"{new:.1f} in new snow")
    if start < SNOW_IN and end < SNOW_IN and peak >= SNOW_IN:
        bits.append(f"dusting peaked ~{peak:.1f} in and melted off (bare by evening)")
    elif abs(end - start) >= 0.3 or peak > max(start, end) + 0.3:
        g = f"ground {start:.1f} -> {end:.1f} in"
        if peak > max(start, end) + 0.3:
            g += f" (peaked {peak:.1f})"
        melted = start + new - end
        if melted >= 0.3:
            g += f", ~{melted:.1f} in melted"
        bits.append(g)
    else:
        bits.append(f"{end:.1f} in on the ground")
    return "; ".join(bits)


def climatology(daily: dict, i: int, window: int = 7) -> tuple[float, float]:
    lo, hi = max(0, i - window), i + window + 1
    highs = daily["temperature_2m_max"][lo:hi]
    lows = daily["temperature_2m_min"][lo:hi]
    return sum(highs) / len(highs), sum(lows) / len(lows)


def _date_at(daily: dict, k: int) -> date:
    return date.fromisoformat(daily["time"][k])


def back_run(ok, i: int) -> int:
    n, k = 0, i
    while k >= 0 and ok(k):
        n += 1
        k -= 1
    return n


def temp_anomaly(daily: dict, i: int) -> tuple[float, str, float, float]:
    norm_hi, norm_lo = climatology(daily, i)
    dhi = daily["temperature_2m_max"][i] - norm_hi
    if dhi >= 8:
        tag = "unusually warm"
    elif dhi >= 4:
        tag = "a bit warm"
    elif dhi <= -8:
        tag = "unusually cold"
    elif dhi <= -4:
        tag = "a bit cool"
    else:
        tag = "about normal"
    return dhi, tag, norm_hi, norm_lo


def overcast_streak(daily: dict, cloud_map: dict, i: int) -> int:
    return back_run(lambda k: cloud_map.get(_date_at(daily, k), 0) >= OVERCAST_PCT, i)


def dry_info(daily: dict, i: int) -> tuple[bool, int, int]:
    today_wet = daily["precipitation_sum"][i] >= WET_IN
    dry_run = back_run(lambda k: daily["precipitation_sum"][k] < WET_IN, i)
    prior_dry = back_run(lambda k: daily["precipitation_sum"][k] < WET_IN, i - 1) if today_wet else 0
    return today_wet, dry_run, prior_dry


def note_tags(daily: dict, cloud_map: dict, i: int) -> list[str]:
    """Terse grounded tags for a table cell (e.g. 'a bit cool', '4th grey day')."""
    _, tag, _, _ = temp_anomaly(daily, i)
    tags = [] if tag == "about normal" else [tag]
    oc = overcast_streak(daily, cloud_map, i)
    if oc >= 2:
        tags.append(f"{ordinal(oc)} grey day")
    wet, dry, prior = dry_info(daily, i)
    if wet and prior >= 3:
        tags.append(f"first rain in {prior}d")
    elif dry >= 4:
        tags.append(f"{dry}d dry")
    return tags


def build_notes(daily: dict, i: int, target: date, cloud_map: dict) -> list[str]:
    """Verbose grounded context for the single-day NOTES line."""
    dhi, tag, norm_hi, norm_lo = temp_anomaly(daily, i)
    pos = "early" if target.day <= 10 else "mid" if target.day <= 20 else "late"
    when = f"{pos} {target.strftime('%B')}"
    notes = [f"high {round(daily['temperature_2m_max'][i])} F is {dhi:+.0f} F vs the "
             f"{when} norm ({norm_hi:.0f}/{norm_lo:.0f}) - {tag}"]
    oc = overcast_streak(daily, cloud_map, i)
    if oc >= 2:
        notes.append(f"{ordinal(oc)} overcast day in a row")
    wet, dry, prior = dry_info(daily, i)
    if wet and prior >= 3:
        notes.append(f"first measurable rain after {prior} dry days")
    elif dry >= 4:
        notes.append(f"{dry} days since measurable rain")
    return notes


def load_year(place: dict):
    year_file = place.get("year_file")
    if not year_file:
        return (f"REJECTED: no weather year cached for {place['place']} "
                f"(analog: {place['us_analog']}). Fetch one with: "
                f'python3 fetch_analog.py "{place["place"]}" <year>')
    raw_path = RAW_DIR / year_file
    if not raw_path.exists():
        return f"REJECTED: registry points {place['place']} at {year_file}, but raw/{year_file} is missing."
    raw = json.loads(raw_path.read_text())
    return raw, int(raw["daily"]["time"][0][:4])


def header(place: dict, month: int, day: int, year: int, target: date) -> list[str]:
    zodiac, name, meaning = MONTHS[month]
    greg = datetime(year, target.month, target.day).strftime("%A, %B %-d, %Y")
    return [
        f"{place['place']} ({place.get('clan', '?')})  <-  {place['us_analog']}",
        f"{ordinal(day)} day of the {ordinal(month)} month "
        f"- {name} ({meaning}), Month of the {zodiac}",
        f"  Gregorian analog: {greg}  (from the {year} weather set)",
    ]


def report(place: dict, month: int, day: int, night: bool) -> str:
    loaded = load_year(place)
    if isinstance(loaded, str):
        return loaded
    raw, year = loaded
    daily = raw["daily"]
    target = to_gregorian(month, day, year)
    i = daily["time"].index(target.isoformat())
    records = hourly_local(raw)
    by_date = group_by_date(records)
    cloud_map = {d: sum(r["cloud"] for r in rows) / len(rows) for d, rows in by_date.items()}

    offset = int(raw["utc_offset_seconds"])
    tz = ZoneInfo(raw.get("timezone", "America/New_York"))
    sunrise = local_clock(daily["sunrise"][i], offset, tz)
    sunset = local_clock(daily["sunset"][i], offset, tz)
    phase, illum, moon_note = moon(day)
    lines = header(place, month, day, year, target)

    if night:
        nxt = target + timedelta(days=1)
        night_rows = ([r for r in by_date.get(target, []) if r["dt"].hour >= 18]
                      + [r for r in by_date.get(nxt, []) if r["dt"].hour < 6])
        lines += [
            "",
            f"  Sun: set {sunset}     Moon: {phase} (~{illum}% lit) - {moon_note}",
            format_period("Evening", period(records, target, 18, 24)),
            format_period("Overnight", period(records, nxt, 0, 6)),
        ]
        snow = snow_day(night_rows)
    else:
        lines += [
            "",
            f"  Sun: rose {sunrise}, set {sunset}     Moon: {phase} (~{illum}% lit)",
            format_period("Morning", period(records, target, 6, 12)),
            format_period("Afternoon", period(records, target, 12, 18)),
            format_period("Evening", period(records, target, 18, 24)),
            f"  Day high/low: {round(daily['temperature_2m_max'][i])}/"
            f"{round(daily['temperature_2m_min'][i])} F     "
            f"Daytime: {condition(daily['weather_code'][i])}",
        ]
        snow = snow_day(by_date.get(target, []))

    if snow:
        lines.append(f"  Snow:      {describe_snow(snow)}")

    notes = build_notes(daily, i, target, cloud_map)
    lines += ["", "  NOTES (for color): " + "; ".join(notes)]
    return "\n".join(lines)


def format_period(label: str, p: dict | None) -> str:
    if p is None:
        return f"  {label:<10} (no data)"
    rain = f", {p['precip']:.2f} in rain" if p["precip"] >= WET_IN else ""
    span = f"{p['tmin']}-{p['tmax']} F" if p["tmin"] != p["tmax"] else f"{p['tmin']} F"
    return f"  {label:<10} {span:<10} {describe_sky(p['cloud'])} ({p['cloud']:.0f}% cloud){rain}"


def main() -> None:
    args = sys.argv[1:]
    night = False
    for flag in ("--night", "night"):
        if flag in args:
            night = True
            args = [a for a in args if a != flag]
    if len(args) != 3:
        sys.exit('Usage: python3 weather.py "<place>" <month 1-12> <day 1-30> [--night]')
    query = args[0]
    try:
        month, day = int(args[1]), int(args[2])
    except ValueError:
        sys.exit("Month and day must be numbers, e.g. 3 2")
    if not 1 <= month <= 12:
        sys.exit("Month must be 1-12")
    if not 1 <= day <= 30:
        sys.exit("Day must be 1-30")
    place = find_place(query)
    if place is None:
        known = ", ".join(p["place"] for p in load_places())
        sys.exit(f"REJECTED: no place matching '{query}'. Known places: {known}")
    print(report(place, month, day, night))


if __name__ == "__main__":
    main()
