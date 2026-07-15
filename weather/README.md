# Campaign Weather

Historical weather for the PCs' current location, modeled on **Roanoke Rapids, North Carolina** (36.46 N, -77.65 W) - chosen as a real-world analog for the party's latitude and distance from the ocean.

## What's here

- `raw/roanoke-rapids-2015.json` - the full-fidelity source pull: a rich set of daily and hourly variables for all of 2015, saved locally so we never have to re-fetch to add a column.
- `build_weather_csv.py` - reads the raw JSON and emits the stripped-down GM CSV.
- `weather-2015.csv` - the working file: one row per day with just what matters at the table.
- `rokugani_weather.py` - give it a Rokugani month and day; it translates to the matching Gregorian date and reports that night's cloud cover plus the moon phase.

## Rokugani date lookup

```
python3 rokugani_weather.py <month 1-12> <day 1-30>
python3 rokugani_weather.py 3 2
```

Calendar translation follows the `/calendar` skill: a 360-day year of twelve
30-day lunar months, with day 1 (1st of Mutsuki / Risshun) anchored at 4
February, so every Rokugani date is a fixed offset with no per-year lunar drift.
A 360-day year anchored at 4 Feb runs a few days into the next January, so late
dates wrap back to the same weather year (the data is one representative year
used as climatology). The moon follows the setting's fixed cycle: new moon on
day 1, full moon on day 15, so the phase is read straight off the day-of-month.
"Night" cloud cover is the mean of the hourly values from sunset to the next
sunrise.

## The CSV columns

`date, weekday, high_f, low_f, precip_in, cloud_pct, sunrise, sunset, conditions`

- Temperatures in Fahrenheit, precip in inches, cloud cover a daily mean percentage.
- `sunrise` / `sunset` are real local wall-clock times (12-hour).
- `conditions` is a plain-English sky label from the day's WMO weather code.

## Source

[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) - free, no API key, ERA5 reanalysis back to 1940. The raw file was fetched from the `archive-api.open-meteo.com/v1/archive` endpoint.

**Year:** 2015, picked arbitrarily from the 21st century. ERA5 has complete, gap-free coverage for any finished past year, so Jan 1 - Dec 31 is fully populated (365 days, 8760 hourly samples, zero nulls).

## Two source quirks handled in the script (not baked into the raw data)

1. **Fixed-offset timestamps.** Open-Meteo reports an entire request at one UTC
   offset (GMT-4 / EDT here), so winter sun times come out an hour late. The
   script reinterprets each sun time at the file's stated offset and converts to
   true `America/New_York` wall-clock time - restoring EST in winter, leaving
   EDT summer times unchanged.
2. **Cloud cover is hourly-only.** There's no daily cloud variable, so the
   script averages the 24 hourly values per day into `cloud_pct`.

Note: `conditions` (from the daily WMO `weather_code`) reflects the day's *most
significant* weather, while `cloud_pct` is the day's *average* sky. They can
disagree - e.g. a day that was clear on average but had a rainy hour reads low
`cloud_pct` but "Light rain" conditions. Both are honest; they answer different
questions ("what was the sky like overall" vs "did anything notable happen").

## Regenerating / changing the year

Re-run the build step any time:

```
python3 build_weather_csv.py                       # defaults: raw/roanoke-rapids-2015.json -> weather-2015.csv
python3 build_weather_csv.py <raw.json> <out.csv>  # explicit paths
```

To use a different year or location, re-fetch the raw JSON from Open-Meteo with
the desired `start_date` / `end_date` / `latitude` / `longitude`, then point the
script at the new file. The rich variable set to request is preserved in the
existing raw file's structure.
