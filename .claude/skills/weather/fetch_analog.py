#!/usr/bin/env python3
"""Fetch a full year of raw weather for a place's real-world analog.

Looks the place up in places.jsonl, pulls a rich daily+hourly year from the
Open-Meteo historical archive (ERA5 reanalysis, free, no API key) at the
analog's coordinates, and saves it to raw/<analog-slug>-<year>.json.

    python3 fetch_analog.py "Kyuden Kakita" 2015

After it runs, record the printed filename as that place's "year_file" in
places.jsonl so weather.py can find it. ERA5 is complete for any finished past
year, so pick any 21st-century year.

Timezone note: Open-Meteo returns a whole request at one fixed UTC offset, so
winter sun times land an hour off; build_weather_csv.py and weather.py correct
that on read (parse at the file's offset, convert to real local time). We fetch
with timezone=America/New_York regardless of the analog's true zone because the
downstream tools only use the offset for that DST correction, and all US
east-coast analogs share Eastern time.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
REGISTRY = HERE / "places.jsonl"
RAW_DIR = HERE / "raw"

DAILY = (
    "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
    "apparent_temperature_max,apparent_temperature_min,precipitation_sum,rain_sum,"
    "snowfall_sum,precipitation_hours,sunrise,sunset,daylight_duration,"
    "sunshine_duration,wind_speed_10m_max,wind_gusts_10m_max,"
    "wind_direction_10m_dominant,weather_code,shortwave_radiation_sum"
)
HOURLY = "temperature_2m,relative_humidity_2m,precipitation,snowfall,snow_depth,cloud_cover,wind_speed_10m"


def slug(analog: str) -> str:
    base = analog.split(",")[0].split("(")[0].strip().lower()
    return "".join(c if c.isalnum() else "-" for c in base).strip("-").replace("--", "-")


def find_place(query: str) -> dict:
    q = query.strip().lower()
    places = [json.loads(x) for x in REGISTRY.read_text().splitlines() if x.strip()]
    for p in places:
        if p["place"].lower() == q or q in p["place"].lower():
            return p
    sys.exit(f"No place matching '{query}'. Known: {', '.join(p['place'] for p in places)}")


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit('Usage: python3 fetch_analog.py "<place>" <year>')
    place = find_place(sys.argv[1])
    year = int(sys.argv[2])
    lat, lon = place["lat"], place["lon"]
    out = RAW_DIR / f"{slug(place['us_analog'])}-{year}.json"

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={year}-01-01&end_date={year}-12-31"
        f"&daily={DAILY}&hourly={HOURLY}"
        "&timezone=America%2FNew_York&temperature_unit=fahrenheit"
        "&precipitation_unit=inch&wind_speed_unit=mph&format=json"
    )
    RAW_DIR.mkdir(exist_ok=True)
    subprocess.run(["curl", "-sS", "-o", str(out), url], check=True)

    data = json.loads(out.read_text())
    n = len(data["daily"]["time"])
    print(f"Saved {n} days for {place['place']} ({place['us_analog']}) -> raw/{out.name}")
    print(f'Now set  "year_file": "{out.name}"  for {place["place"]} in places.jsonl')


if __name__ == "__main__":
    main()
