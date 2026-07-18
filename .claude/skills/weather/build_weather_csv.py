#!/usr/bin/env python3
"""Build a stripped-down GM weather CSV from a raw Open-Meteo archive JSON.

The raw file (raw/roanoke-rapids-<year>.json) holds a rich set of daily and
hourly variables so we never have to re-fetch to add a column later. This
script reads that file and emits just the columns a GM cares about at the
table: date, weekday, high/low, precip, cloud cover, sunrise, sunset, and a
plain-English sky condition.

Two source quirks are corrected here rather than in the saved data:

1. Fixed-offset timestamps. Open-Meteo reports the whole request at a single
   UTC offset (here GMT-4 / EDT), so winter sunrise/sunset land an hour late.
   We reinterpret each sun time at the file's stated offset, then convert to
   true America/New_York wall-clock time, which restores EST in winter and
   leaves EDT summer times unchanged.

2. Cloud cover is only an hourly variable, so we average the 24 hourly values
   for each day into a single daily mean percentage.

Usage:
    python3 build_weather_csv.py [raw/roanoke-rapids-2015.json] [weather-2015.csv]
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# WMO weather codes -> short human-readable sky/condition label.
# https://open-meteo.com/en/docs (WMO Weather interpretation codes).
WMO_CODES = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Freezing fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Violent showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ hail",
    99: "Thunderstorm w/ hail",
}


def condition(code: int | None) -> str:
    if code is None:
        return ""
    return WMO_CODES.get(int(code), f"code {int(code)}")


def local_clock(iso: str, source_offset_seconds: int, target_tz: ZoneInfo) -> str:
    """Reinterpret a fixed-offset Open-Meteo timestamp as true local wall-clock.

    The raw string carries no zone; the file's utc_offset_seconds tells us the
    offset it was written at. We attach that offset, convert to the real zone
    (DST-aware), and format as a readable 12-hour time like "7:22 AM".
    """
    naive = datetime.fromisoformat(iso)
    source = naive.replace(tzinfo=timezone(timedelta(seconds=source_offset_seconds)))
    local = source.astimezone(target_tz)
    return local.strftime("%-I:%M %p")


def daily_mean_cloud(hourly: dict[str, list], source_offset_seconds: int, target_tz: ZoneInfo) -> dict[str, float]:
    """Average hourly cloud_cover into a per-date mean, keyed by real local date."""
    buckets: dict[str, list[float]] = {}
    tz = timezone(timedelta(seconds=source_offset_seconds))
    for iso, val in zip(hourly["time"], hourly["cloud_cover"]):
        if val is None:
            continue
        stamp = datetime.fromisoformat(iso).replace(tzinfo=tz).astimezone(target_tz)
        buckets.setdefault(stamp.strftime("%Y-%m-%d"), []).append(float(val))
    return {day: sum(vals) / len(vals) for day, vals in buckets.items()}


def build(raw_path: Path, out_path: Path) -> int:
    data = json.loads(raw_path.read_text())
    daily = data["daily"]
    offset = int(data["utc_offset_seconds"])
    tz = ZoneInfo(data.get("timezone", "America/New_York"))

    cloud_by_day = daily_mean_cloud(data["hourly"], offset, tz)

    rows = []
    for i, day in enumerate(daily["time"]):
        date = datetime.fromisoformat(day)
        rows.append(
            {
                "date": day,
                "weekday": date.strftime("%a"),
                "high_f": round(daily["temperature_2m_max"][i]),
                "low_f": round(daily["temperature_2m_min"][i]),
                "precip_in": round(daily["precipitation_sum"][i], 2),
                "cloud_pct": round(cloud_by_day.get(day, 0)),
                "sunrise": local_clock(daily["sunrise"][i], offset, tz),
                "sunset": local_clock(daily["sunset"][i], offset, tz),
                "conditions": condition(daily["weather_code"][i]),
            }
        )

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main() -> None:
    here = Path(__file__).parent
    raw_path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "raw" / "roanoke-rapids-2015.json"
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else here / "weather-2015.csv"
    n = build(raw_path, out_path)
    print(f"Wrote {n} days to {out_path}")


if __name__ == "__main__":
    main()
