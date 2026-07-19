---
name: weather
description: Ground Rokugan weather in real historical data by mapping each place to a continental-US climate analog (latitude, distance from ocean, elevation), then reading actual recorded weather for a translated calendar date. Answers "what is the weather like" in a principled, plot-independent way.
---

# Rokugani Weather

Weather in the campaign should be something that *happens to* the PCs, grounded and indifferent to the plot. That indifference is the point: real weather nobody chose adds verisimilitude the way invented dramatic weather never can. This skill makes that reproducible by tying each Rokugan location to a real place on Earth with the same climate, then reading that place's actual recorded historical weather.

## Core doctrine: why the mapping works

Rokugan is roughly **1,500 miles tall and 1,000 miles wide, with an ocean to its east**. A tall, mid-latitude landmass with an eastern ocean has the same fundamental geometry as the **eastern seaboard of the continental United States** - so that is the reference coast. This is not decoration; it follows from how weather actually works:

- At these latitudes (~25-45N) the prevailing winds are **westerlies** - weather moves west to east. The eastern ocean is therefore *downwind* of the land and moderates it far less than an ocean would on a west coast. This is why the US East Coast (and Rokugan's east coast) has four real seasons, cold and often snowy winters even on the coast, and hot humid summers - not a mild Mediterranean feel.

### The three drivers (first-order)

Judge any Rokugan place by these, in order:

1. **Latitude** - the primary control on temperature, day length, and seasonality. Fixes where a place sits north-to-south on the coast ladder below.
2. **Continentality (distance from the eastern ocean)** - because that ocean is *downwind*, this mostly governs **humidity, how much winter lows are moderated, and storm exposure**, and less the mean temperature than intuition suggests. Coastal-east and 100-mi-inland-east are both humid subtropical/continental; the coast is just milder in winter and muggier and stormier. A landlocked interior domain swings harder (hotter summers, colder winters).
3. **Elevation / orography** - about 3.5F cooler per 1,000 ft. A domain up in a mountain range at a given latitude is nothing like a coastal-plain domain at the same latitude (Asheville vs the NC coast). **Rain-shadow corollary:** with westerlies, the *west* face of a Rokugan range is wet and the *east* face is dry.

### The three modifiers (second-order, apply where relevant)

- **Offshore current / a genuinely cold north.** The US analogs already encode their currents (warm **Gulf Stream** / Kuroshio off the south; a cold, snowbound Maine north). **GM canon: Rokugan's north is truly harsh and Maine-like - the whole coast is basically equivalent to the US, cold north included.** This is precisely why Winter Court looms so large up north: once the snow falls you can be trapped for months, unable to travel. So map northern domains straight onto the cold US north and do *not* soften them; southern domains get warm-current mildness for free through their analogs.
- **Storm / typhoon season.** The East Coast's hurricanes have an exact Pacific analog: **typhoons**, striking late summer / early autumn. Coastal and southern domains get a typhoon season; the whole region gets a summer-thunderstorm precipitation max (East Asian summer monsoon ~ US Southeast summer max).
- **Rain shadow** - see elevation above; called out separately because it can flip a domain from wet to dry independent of its latitude.

### What does NOT matter

- **Absolute longitude / the straight coastline.** Rokugan's coast is a fairly straight north-south line; the US East Coast bends (Maine far east, Florida far south). This is a real *geometric* mismatch but **not a weather problem**: weather at a place depends on that place's own latitude and its own distance to the nearest coast, never on absolute longitude. Do not try to correct for it.

## The east-coast anchor ladder

Empire-scale reference points, north to south (GM-established). Details and per-place reasoning live in `places.jsonl`.

| Rokugan | US analog | Note |
|---|---|---|
| Kyuden Isawa (Phoenix) | Acadia NP / Bar Harbor, ME | coastal and forested; the inland Isawa Woodlands (largest forest in the Empire) are a separate, colder interior zone (own registry entry) |
| Kyuden Shiba (Phoenix) | Boston, MA | |
| **Otosan Uchi (Imperial)** | **New York City** | **baseline anchor - the ladder is pinned here** |
| Kyuden Doji (Crane) | Atlantic City, NJ | |
| Kyuden Kakita (Crane) | Ocean City, MD | coastal; map-derived, 146 mi north of Reiji |
| Shiro Etsuko (Crane) | Virginia Beach, VA | coastal Daidoji vassal house; the true seaside twin of landlocked Reiji, 25 mi north of it |
| Shiro Reiji (Crab) | Roanoke Rapids, NC | landlocked, ~100 mi inland |
| Kyuden Daidoji (Crane) | Savannah, GA | |
| Shinden Asahina (Crane) | Tampa, FL | southern tip; least-exact (Earthquake Bay << Gulf) |

Known imperfection to keep in mind: **Earthquake Bay is much smaller than the Gulf of Mexico**, so Asahina is a touch more continental than Tampa.

### Deriving a latitude from a campaign map (method, so it need not be re-invented)

Places on a hand-drawn campaign map get their latitude MEASURED, not guessed. Worked on the Three Man Alliance map, 2026-07-19:

1. **Scale.** Read the legend (there: `⊔ - 5 miles`) and confirm the glyph is one graph-paper square. Measure the grid's true pixel period rather than trusting the glyph - fold the image's faint-line mask at candidate periods and take the strongest. That map: 60 px/square, so **12 px/mile**.
2. **Orientation.** Do not assume. The ocean sits on the map's right edge, and Rokugan's ocean is east, so up = north.
3. **Positions.** Snap each castle star to the centroid of its dark ink in a small window (a mean-shift of a few iterations), then **render an overlay with the detected points circled and check every one by eye** - hand-drawn stars and nearby labels make pure automation unsafe.
4. **Convert.** Take north-south pixel offsets from an already-anchored place (Reiji, GM-established) and divide by 12 px/mile, then by **69 miles per degree** of latitude.

**Precision.** Star placement on graph paper is good to roughly half a square (~2.5 mi, ~0.04 deg). Treat inferred latitudes as +-5 miles; they are far better than eyeballing, but do not quote them to two decimals as if surveyed.

**Why this section exists.** The original Kakita entry claimed Virginia Beach was "at Reiji's latitude" while its own `lat` field said otherwise, and the map work behind the ladder was never written down - so when the GM questioned it, nothing could be checked and it had to be redone from the map. Measuring showed Kakita is 146 mi north of Reiji (lat ~38.58, hence Ocean City), and that **Virginia Beach actually belongs to Shiro Etsuko** (25 mi north of Reiji, lat ~36.83). Record the derivation for any place added this way.

## Calendar translation

A **360-day year, twelve 30-day lunar months**. Each Rokugani month is anchored to a fixed Gregorian **start date** (below), and its 30 days count forward from there. This table is canon - identical in the `/calendar` skill's source notes and the GM's date-mapping doc.

| Rokugan month | Gregorian range | | Rokugan month | Gregorian range |
|---|---|---|---|---|
| 1 Mutsuki | 4 Feb - 5 Mar | | 7 Fumizuki | 8 Aug - 7 Sep |
| 2 Kisaragi | 6 Mar - 4 Apr | | 8 Hazuki | 8 Sep - 7 Oct |
| 3 Yayoi | 5 Apr - 5 May | | 9 Nagatsuki | 8 Oct - 6 Nov |
| 4 Uzuki | 6 May - 5 Jun | | 10 Kaminazuki | 7 Nov - 6 Dec |
| 5 Satsuki | 6 Jun - 6 Jul | | 11 Shimotsuki | 7 Dec - 4 Jan |
| 6 Minazuki | 7 Jul - 7 Aug | | 12 Shiwasu | 5 Jan - 3 Feb |

**Why anchor per month instead of just counting 30-day blocks from 4 February?** Because 360 Rokugani days must cover a ~365-day Gregorian year. A naive "4 Feb + 30x(month-1)" count keeps perfect 30-day blocks but slips ~5 days behind the real year over 12 months (it would put the 7th month at 3 Aug instead of the canonical 8 Aug), pulling the later months off their real seasons. Anchoring each month to its canonical start distributes that 5-day slack and keeps every month locked to the season it belongs to - which is the whole point of a weather model. Consequence: each month is a clean 30-day run from its start, but since the Gregorian spans are 29-32 days, a day or two can fall in a gap (or a 1-day overlap) at month boundaries. Immaterial for a lookup. Late-year dates wrap back onto the same cached weather year (one representative year used as climatology).

**Moon:** the month begins on the **new moon (day 1)** and the **full moon falls on day 15**, so the phase is read straight off the day-of-month - no astronomy needed.

## Data pipeline

Source: **Open-Meteo Historical Weather API** (ERA5 reanalysis, free, no API key, complete for any finished past year). Each analog gets one rich year saved locally; scripts derive everything from it.

- `places.jsonl` - the registry: one line per Rokugan place with its US analog, coordinates, distance-from-ocean, elevation, orography, the cached `year_file`, and the **why** (per the project's record-the-why rule).
- `raw/<analog-slug>-<year>.json` - the full-fidelity local pull (rich daily + hourly set), so a new column never needs a re-fetch.
- `fetch_analog.py "<place>" <year>` - pull a year for a place's analog into `raw/`; then record the printed filename as that place's `year_file`.
- `build_weather_csv.py [raw.json] [out.csv]` - reduce a raw year to a stripped daily CSV (date, weekday, high/low, precip, cloud %, sunrise, sunset, conditions).
- `weather.py "<place>" <month> <day> [--night]` - single-day lookup: place -> analog -> translated date -> a day or night report.
- `weather_range.py "<place>" <sm> <sd> <em> <ed> [--out f.html]` - a browsable HTML table over a Rokugani date range, written to `reports/` (gitignored). Snow columns appear only if some day in the range has snow. The page is interactive: a kebab (three-dot) menu at the right of the table header shows/hides columns (persisted in localStorage, keyed by column, shared across all reports, so e.g. "hide snow" sticks everywhere); any column that is empty on every row is hidden by default on load and must be re-shown each load if wanted (this default is deliberately not persisted); and clicking a month header collapses/expands that month, with the collapsed set also remembered across loads. The same kebab menu carries a **color legend** entry explaining the row tints (dry / rain / snow / expanded calendar entry), with the Open-Meteo sourcing line at its foot; the snow swatch is omitted on a snowless range for the same reason the snow columns are. Row colors live in one `ROW_COLORS` dict in `weather_range.py` which is substituted into the CSS via `__TOKEN__` placeholders **and** used to build the legend, so a color tweak cannot leave the legend describing a shade the table no longer uses.
- `calendar_data.py` - parses the `/calendar` skill's month-by-month breakdown (`.claude/skills/calendar/SKILL.md`, read-only: it lives inside a `SOURCE: GM NOTES` block) into structured months and days. Read at build time by `weather_range.py`; the GM's prose stays the single source of truth, so editing the calendar updates every report built afterwards. Tested to 100% in `test_calendar_data.py`.

**Calendar in the range report.** The table carries a **Calendar** column between Date and Hi/Lo, showing the observance for any day the calendar names (`Joui`, `Haru Higan`, `Tanabata`, ...). The trailing gloss is trimmed for column width; clicking the name expands the calendar's **full entry** - untrimmed title, Gregorian date, and all its prose - in a detail row beneath that day, and clicking again collapses it. Detail rows are pre-rendered hidden rather than built in JS, so the text is still found by ctrl-F and survives printing. Expansion is deliberately **not** persisted (unlike columns and month collapse): reading a festival is a now-action, not a viewing preference. If no day in the range has an observance, the column self-hides via the existing empty-column rule.

**Month notes.** The month name in each month header is a button that opens a **modal** with that month's seasonal color, flower lists, intro prose, and an index of its observances. The rest of the header row still toggles collapse, so the two interactions do not fight; close via the X, the backdrop, or Escape. A modal rather than an expander because month-level material is reference-you-consult, not a row in the daily sequence.

Two source quirks handled on read, never baked into the raw data: (1) Open-Meteo reports a whole request at one fixed UTC offset, so winter sun times land an hour late - the tools reinterpret at the file's offset and convert to true local time; (2) cloud cover is hourly-only, so daily/night cloud is averaged from the hourly values.

**Snow.** The hourly pull includes `snowfall` and `snow_depth` (units vary - here inch and ft - and are normalized to inches on read). Per day we compute new snowfall, ground depth at start and end of the window, and the intraday peak, so a report can show both accumulation (depth rising as it snows) and melt (depth falling), e.g. a dusting that peaks at 1 in and melts off by evening, or 5 in on the ground melting to 3 in with no new snow. **Snow is shown only when present** - in single-day reports it is one extra line that appears only on snowy days; in range tables the three snow columns appear only if some day in the range has snow, and are omitted entirely otherwise. Adding snow was a schema change, so any analog fetched before it needs a re-fetch to carry snow depth.

## Invocation

The GM invokes this skill in free text: `/weather <place> <date>`. Parse the natural language yourself, then call `weather.py` with normalized arguments and narrate the result.

**Three report modes:**

- **Full-day (default)** - `/weather Reiji 3rd day 3rd month`. Morning -> afternoon -> evening, each with temperature, cloud, and any rain, plus the day high/low. Inline narrated report.
- **Night** - triggered by the words *night*, *evening*, or *overnight* (e.g. `/weather Shiro Reiji night of the 2nd day of the 3rd month`). Evening + overnight only, with the moon foregrounded. Inline narrated report.
- **Range -> HTML** - triggered by a *date range* or a request for a file/table (e.g. `/weather Reiji 2nd month through the end of the 4th month`). Call `weather_range.py "<place>" <start_month> <start_day> <end_month> <end_day>`, which writes a styled HTML file to `reports/` and prints its path; hand the GM that path to open in their browser. "Through the end of the 4th month" means end day 30; "the 2nd month" as a start means day 1.

Snow lines/columns appear only when there is actually snow (see Data pipeline); a snowless day or range shows nothing about snow.

**Parsing rules:**

- **Place** is fuzzy: `Reiji` resolves to `Shiro Reiji` (case-insensitive substring; the script does this). Pass whatever the GM wrote.
- **Date** accepts any ordinal phrasing - "2nd day of the 3rd month", "3rd day 3rd month", "3rd month 2nd day" all mean month 3. Normalize to `<month> <day>` integers.
- **Mode**: pass `--night` when the request names the night/evening/overnight; otherwise omit it.

So `/weather Shiro Reiji night of the 2nd day of the 3rd month` becomes `python3 weather.py "Shiro Reiji" 3 2 --night`, and `/weather Reiji 3rd day 3rd month` becomes `python3 weather.py "Shiro Reiji" 3 3`.

**Color commentary (required, grounded).** The script ends each report with a `NOTES (for color)` line holding computed facts: the day's high vs the +-1-week seasonal norm (with a plain-language tag like "unusually warm"), and any overcast or dry streak. **Open the narrated report with one or two sentences of natural color drawn ONLY from those notes** - e.g. "An unusually warm morning for early spring." or "The fourth gray day running, and still not a drop - the clouds hang low enough that today might finally break." Never invent weather facts the notes don't support; the whole point of computing them is that the flavor stays honest.

**Rejection (do not synthesize).** If the script returns a line beginning `REJECTED:` - the place is unknown, or known but has no cached weather year - relay that and stop. Do **not** improvise weather for an unmapped or uncached place. For a *known* place lacking data you may offer to fetch a year (`fetch_analog.py "<place>" <year>`); that is legitimate grounding, not synthesis.

```
python3 weather.py "Shiro Reiji" 3 3            # full day
python3 weather.py reiji 3 2 --night           # evening + overnight
python3 fetch_analog.py "Kyuden Kakita" 2015   # cache a year for a new place
```

Note: `conditions` / `Daytime` (from the daily WMO weather code) is the day's *most significant* weather and can read cloudier than a period's *average* sky - they answer different questions ("did anything notable happen" vs "what was the sky like overall").

## Status

Organically built, pre-spec-kit by design - this is still a vibes-and-experimentation stage. Formalize a spec-kit constitution section only once the framework has matured. Only Shiro Reiji has a cached weather year so far (Roanoke Rapids 2015); other registry places fetch on demand.
