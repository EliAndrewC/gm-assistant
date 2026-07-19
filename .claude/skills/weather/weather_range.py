#!/usr/bin/env python3
"""Generate a browsable HTML weather table for a place over a Rokugani date range.

    python3 weather_range.py "Shiro Reiji" 2 1 4 30            # 2nd month through end of 4th
    python3 weather_range.py reiji 1 1 1 30 --out /tmp/win.html

One row per day: Rokugani date, Gregorian analog, calendar observance, high/low,
sky, rain, sun, moon, and a terse grounded note. Festival names in the Calendar
column expand in place to the /calendar skill's full entry for that day, and a
month header's name opens that month's seasonal notes in a modal - both are baked
into the file from `.claude/skills/calendar/SKILL.md` at build time, so the report
stays self-contained. Snow columns (new snow, ground depth start->end, peak)
appear ONLY if some day in the range has snow; a snowless range omits them
entirely. Writes a self-contained HTML file (styled, opens in any browser) and
prints its path. See SKILL.md for the invocation contract and the place -> analog
framework; all figures are real recorded weather for the place's climate analog.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import calendar_data as C
import weather as W
from build_weather_csv import local_clock

REPORTS = W.HERE / "reports"


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-").replace("--", "-")


def rok_range(sm: int, sd: int, em: int, ed: int):
    """Yield (month, day) from start to end inclusive, wrapping across the year if needed."""
    start = (sm - 1) * 30 + sd
    end = (em - 1) * 30 + ed
    count = (end - start) % 360 + 1
    for k in range(count):
        o = (start - 1 + k) % 360
        yield o // 30 + 1, o % 30 + 1


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def compact_time(t: str) -> str:
    """'6:34 AM' -> '6:34a' to save table width."""
    return t.replace(" AM", "a").replace(" PM", "p")


def build_rows(raw: dict, year: int, cells):
    daily = raw["daily"]
    records = W.hourly_local(raw)
    by_date = W.group_by_date(records)
    cloud_map = {d: sum(r["cloud"] for r in rows) / len(rows) for d, rows in by_date.items()}
    offset = int(raw["utc_offset_seconds"])
    tz = ZoneInfo(raw.get("timezone", "America/New_York"))

    rows = []
    for month, day in cells:
        target = W.to_gregorian(month, day, year)
        i = daily["time"].index(target.isoformat())
        rows.append({
            "month": month, "day": day,
            "greg": datetime(year, target.month, target.day),
            "hi": round(daily["temperature_2m_max"][i]),
            "lo": round(daily["temperature_2m_min"][i]),
            "cloud": cloud_map.get(target, 0),
            "precip": daily["precipitation_sum"][i],
            "snow": W.snow_day(by_date.get(target, [])),
            "sunrise": local_clock(daily["sunrise"][i], offset, tz),
            "sunset": local_clock(daily["sunset"][i], offset, tz),
            "tags": W.note_tags(daily, cloud_map, i),
        })
    return rows


# Row background colors. Single source of truth: the CSS below carries __TOKEN__
# placeholders that are substituted in, and the legend modal is built from the
# same dict - so a color tweak here cannot leave the legend describing a shade
# the table no longer uses.
#
# There is deliberately NO zebra striping. It used to alternate even rows, which
# broke the invariant this table depends on: a row that looks different IS
# different weather. Worse, `nth-child(even)` counted the month-header and hidden
# calendar-detail rows too, so the banding did not even alternate by day - it
# flipped parity at every month break and every expanded festival. Rows stay
# legible via the 1px border-top on each cell; if row tracking across the width
# ever needs more help, add a hover highlight, not a background stripe.
# Rain and snow are split by HUE, not just lightness: the old pair differed by
# 6/255 in their strongest channel, which is invisible while scanning. Rain is
# now decisively blue; snow is a desaturated cool gray. Gray (not a second blue,
# and not a violet) because violet would collide with the lilac calendar-detail
# row, and two blues are exactly the problem being fixed.
ROW_COLORS = {
    "plain": "#fffdf8",
    "rain": "#c7e0f4",
    "snow": "#dfe3e6",
    "detail": "#f6f1f7",
}

CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin: 0; padding: 2rem 1rem; background: #f4f1ea; color: #23201b;
       font: 15px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; }
.wrap { max-width: 1240px; margin: 0 auto; }
h1 { font: 600 1.6rem/1.2 Georgia, "Times New Roman", serif; margin: 0 0 .25rem; }
.sub { color: #6b6357; margin: 0 0 1.25rem; font-size: .95rem; }
.sub b { color: #4a4336; }
.scroll { overflow-x: auto; border: 1px solid #ddd6c8; border-radius: 8px; }
table { border-collapse: collapse; width: 100%; background: __PLAIN__; }
thead th { position: sticky; top: 0; background: #3f3a30; color: #f4f1ea;
           font-weight: 600; text-align: left; padding: .5rem .6rem; white-space: nowrap; font-size: .82rem;
           text-transform: uppercase; letter-spacing: .03em; }
td { padding: .38rem .55rem; border-top: 1px solid #ece7db; white-space: nowrap; vertical-align: top; }
tr.rain td { background: __RAIN__ !important; }
tr.snow td { background: __SNOW__ !important; }
tr.mhead td { background: #e7e0d0; color: #4a4336; font: 600 .9rem Georgia, serif;
              border-top: 2px solid #cabfa6; letter-spacing: .01em; cursor: pointer; user-select: none; }
tr.mhead:hover td { background: #e0d8c4; }
.chev { display: inline-block; transition: transform .12s ease; margin-right: .35rem; color: #8a7d5f; }
tr.mhead.collapsed .chev { transform: rotate(-90deg); }
tr.mhead .mname { background: none; border: 0; font: inherit; color: #5a4a24; cursor: pointer;
                  padding: 0; text-decoration: underline dotted #a8996f; text-underline-offset: 3px; }
tr.mhead .mname:hover { color: #23201b; text-decoration-color: #5a4a24; }
/* Titles carry their English gloss, so most are ~25 chars but a couple run to
   85 ("Shuubun (Autumnal Equinox), Hojoe (The Great Liberation), and Kangetsu
   (Moon Viewing)"). Wide enough that typical entries stay on one or two lines,
   capped so the outliers wrap instead of shoving the weather columns rightward. */
.cal { white-space: normal; min-width: 140px; max-width: 260px; }
.calbtn { background: none; border: 0; font: inherit; color: #6d4d7a; cursor: pointer; padding: 0;
          text-align: left; text-decoration: underline dotted #b09bbb; text-underline-offset: 3px; }
.calbtn:hover { color: #23201b; text-decoration-color: #6d4d7a; }
.calbtn::after { content: " \\25B8"; font-size: .8em; color: #b09bbb; }
tr.dayrow.open .calbtn::after { content: " \\25BE"; }
tr.detail { display: none; }
tr.detail.open { display: table-row; }
tr.detail td { background: __DETAIL__ !important; white-space: normal; padding: .6rem .9rem .8rem 1.1rem;
               border-left: 3px solid #b09bbb; }
tr.detail h4 { margin: 0 0 .35rem; font: 600 1rem Georgia, serif; color: #4a3a52; }
tr.detail p { margin: 0 0 .5rem; max-width: 74ch; }
tr.detail p:last-child { margin-bottom: 0; }
tr.detail .none { color: #8a8272; font-style: italic; }
.modal-back { position: fixed; inset: 0; background: rgba(35, 32, 27, .45); z-index: 60;
              display: flex; align-items: center; justify-content: center; padding: 1.5rem; }
.modal-back[hidden] { display: none; }
.modal { background: #fffdf8; border-radius: 10px; box-shadow: 0 12px 40px rgba(0, 0, 0, .3);
         max-width: 720px; width: 100%; max-height: 82vh; overflow-y: auto; padding: 1.4rem 1.6rem 1.6rem; }
.modal h2 { font: 600 1.3rem/1.3 Georgia, serif; margin: 0 0 .15rem; }
.modal .mspan { color: #6b6357; font-size: .9rem; margin: 0 0 .9rem; }
.modal dl { margin: 0 0 1rem; display: grid; grid-template-columns: max-content 1fr; gap: .3rem .8rem; }
.modal dt { font-weight: 600; color: #4a4336; font-size: .88rem; }
.modal dd { margin: 0; font-size: .9rem; }
.modal p { margin: 0 0 .7rem; max-width: 74ch; }
.modal .days { margin: .4rem 0 0; padding-left: 1.1rem; font-size: .9rem; }
.modal .days li { margin-bottom: .25rem; }
.modal-close { float: right; background: none; border: 0; font-size: 1.5rem; line-height: 1;
               color: #8a8272; cursor: pointer; padding: 0 .2rem; }
.modal-close:hover { color: #23201b; }
.hi { font-weight: 600; } .lo { color: #6b6357; }
.tags { color: #7a5a3a; font-size: .85rem; white-space: normal; min-width: 130px; max-width: 210px; }
.snowcell { color: #3a4a63; }
.muted { color: #b5ae9e; }
th.kebab-col, td.kebab-col { width: 1%; padding-left: .2rem; padding-right: .45rem; text-align: center; }
thead th.kebab-col { text-align: right; }
.kebab { background: none; border: 0; color: inherit; font: inherit; font-size: 1.25rem; line-height: 1;
         cursor: pointer; padding: 0 .3rem; border-radius: 4px; }
.kebab:hover { background: rgba(255, 255, 255, .18); }
.kebab-menu { position: fixed; z-index: 50; background: #fffdf8; border: 1px solid #ddd6c8;
             border-radius: 8px; box-shadow: 0 6px 22px rgba(0, 0, 0, .18); padding: .6rem .75rem;
             display: flex; flex-direction: column; gap: .35rem; font-size: .88rem; color: #4a4336; min-width: 168px; }
.kebab-menu[hidden] { display: none; }
.kebab-menu-title { font-weight: 600; margin-bottom: .1rem; }
.kebab-menu label { display: flex; align-items: center; gap: .4rem; white-space: nowrap; cursor: pointer; }
.kebab-menu input { margin: 0; }
.kebab-menu a { color: #7a5a3a; margin-top: .25rem; }
/* The row tints are deliberately faint, and the modal's own background is the
   same cream as an untinted row - so a small white-on-white chip reads as an
   empty box. The legend sits on a darker panel and each swatch is a full
   table-row-sized block, which is what makes two near-identical pale blues
   (rain vs snow) actually comparable. The swatches stay the REAL colors: a
   legend that saturates its samples for legibility is a legend that lies. */
.legend { list-style: none; margin: 0 0 .9rem; padding: .8rem .9rem .3rem;
          background: #efebe1; border-radius: 8px; }
.legend li { display: grid; grid-template-columns: 5rem 1fr; gap: .2rem .9rem;
             align-items: start; margin-bottom: .7rem; }
.legend .sw { grid-row: span 2; width: 5rem; height: 2.4rem; border: 1px solid #cdc5b4;
              border-radius: 4px; }
.legend .lb { font-weight: 600; color: #3f3a30; font-size: .92rem; align-self: end; }
.legend .ds { font-size: .88rem; color: #4a4336; align-self: start; }
.modal .note { color: #6b6357; font-size: .84rem; margin: 0 0 .5rem; }
.modal .src { color: #8a8272; font-size: .8rem; margin: .9rem 0 0; }
@media (max-width: 520px) {
  .legend li { grid-template-columns: 1fr; gap: .15rem; }
  .legend .sw { grid-row: auto; width: 100%; height: 1.7rem; }
}
.tip { text-decoration: underline dotted #b5ae9e; text-underline-offset: 3px; cursor: help; }
@media print { .kebab-col, .kebab-menu { display: none; } }
"""

for _token, _key in (("__PLAIN__", "plain"), ("__RAIN__", "rain"),
                     ("__SNOW__", "snow"), ("__DETAIL__", "detail")):
    CSS = CSS.replace(_token, ROW_COLORS[_key])


def month_modal_json(cal: dict, months: list[int]) -> str:
    """Serialise just the months present in this range, for the header modal."""
    import json
    out = {}
    for n in months:
        mo = cal.get(n)
        if mo is None:  # pragma: no cover - all twelve months exist in SKILL.md
            continue
        out[str(n)] = {
            "title": f"{W.ordinal(n)} Month - {mo['name']} ({mo['meaning']}), Month of the {mo['zodiac']}",
            "span": mo["span"],
            "meta": [[k, v] for k, v in mo["meta"]],
            "intro": mo["intro"],
            "days": [[d, mo["days"][d]["title"]] for d in sorted(mo["days"])],
        }
    return json.dumps(out)


def range_label(sm: int, sd: int, em: int, ed: int) -> str:
    """Describe a Rokugani date range as briefly as it can be said unambiguously.

    Days are named only for an end that starts or stops MID-month; a whole month
    needs no day numbers:

        1,1 -> 1,30   "1st month"
        2,1 -> 4,30   "2nd - 4th months"
        1,5 -> 1,20   "5th - 20th of the 1st month"
        2,5 -> 4,30   "5th of the 2nd month - 4th month"
        2,1 -> 4,12   "2nd month - 12th of the 4th month"

    A month is "whole" when the range enters it on day 1 and leaves on day 30.
    """
    o = W.ordinal
    whole_start, whole_end = sd == 1, ed == 30

    if sm == em and sd <= ed:  # one month (sd > ed would mean a year-long wrap)
        if whole_start and whole_end:
            return f"{o(sm)} month"
        return f"{o(sd)} - {o(ed)} of the {o(sm)} month"

    if whole_start and whole_end:
        return f"{o(sm)} - {o(em)} months"

    start = f"{o(sm)} month" if whole_start else f"{o(sd)} of the {o(sm)} month"
    end = f"{o(em)} month" if whole_end else f"{o(ed)} of the {o(em)} month"
    return f"{start} - {end}"


def house_label(place: dict) -> str:
    """The parenthetical after a place name: which house holds it.

    A VASSAL house names both: "Hida Family, Crab Clan". A RULING-family house
    names only the Clan - "Kyuden Kakita (Crane Clan)" - because "Kakita" is
    already in the place name and repeating it says nothing.

    That suppression is DERIVED, not a per-place flag: if the family name is
    already a word in the place name, it is a ruling-family seat. So the
    registry only has to record `family` where it is not obvious from the name,
    and adding a new Kyuden <Family> needs no extra bookkeeping.

    The Imperial house is not a clan (its four are the Imperial Families), so it
    is never given a "Clan" suffix.
    """
    clan = place.get("clan", "?")
    suffix = clan if clan == "Imperial" else f"{clan} Clan"
    family = place.get("family")
    if family and family.lower() not in place["place"].lower().split():
        return f"{family} Family, {suffix}"
    return suffix


def render(place: dict, rows: list, sm, sd, em, ed, cal: dict) -> str:
    has_snow = any(r["snow"] for r in rows)
    title = f"{place['place']} - {range_label(sm, sd, em, ed)}"
    span = f"{rows[0]['greg']:%b %-d} - {rows[-1]['greg']:%b %-d, %Y}"

    columns = [("rok", "Rokugani"), ("date", "Date"), ("cal", "Calendar"),
               ("hilo", "Hi / Lo"), ("sky", "Sky"), ("rain", "Rain")]
    if has_snow:
        columns += [("newsnow", "New snow"), ("ground", "Ground"), ("peak", "Peak")]
    columns += [("sun", "Sun (rise / set)"), ("notes", "Notes")]

    head = "".join(f'<th data-col="{k}">{esc(label)}</th>' for k, label in columns)
    head += '<th class="kebab-col"><button id="kebab-btn" class="kebab" aria-label="Show or hide columns" title="Columns">&#8942;</button></th>'
    toggles = "".join(
        f'<label><input type="checkbox" data-toggle="{k}" checked> {esc(label)}</label>'
        for k, label in columns
    )

    body = []
    cur_month = None
    ncols = len(columns) + 1  # + kebab column
    nonempty = set()  # columns that have at least one non-empty cell
    for r in rows:
        if r["month"] != cur_month:
            cur_month = r["month"]
            zod, name, meaning = W.MONTHS[cur_month]
            lo = W.to_gregorian(cur_month, 1, rows[0]["greg"].year)
            hi = W.to_gregorian(cur_month, 30, rows[0]["greg"].year)
            # The month name is its own button (opens the modal); clicking anywhere
            # else on the header row still collapses/expands the month.
            mname = f"{W.ordinal(cur_month)} Month - {name} ({meaning})"
            rest = f", Month of the {zod} - {lo:%b %-d} to {hi:%b %-d}"
            body.append(f'<tr class="mhead" data-month="{cur_month}"><td colspan="{ncols}">'
                        f'<span class="chev">&#9662;</span>'
                        f'<button class="mname" data-month="{cur_month}" '
                        f'title="Seasonal notes for this month">{esc(mname)}</button>'
                        f'{esc(rest)}</td></tr>')

        cls = "snow" if r["snow"] else ("rain" if r["precip"] >= W.WET_IN else "")
        entry = cal.get(r["month"], {}).get("days", {}).get(r["day"])
        rid = f'{r["month"]}-{r["day"]:02d}'
        if entry:
            calcell = (f'<button class="calbtn" data-day="{rid}">'
                       f'{esc(entry["title"])}</button>')
        else:
            calcell = "-"
        cell = {
            "rok": (str(r["day"]), ""),
            "date": (f'{r["greg"]:%b %-d}', ""),
            "cal": (calcell, "cal"),
            "hilo": (f'<span class="hi">{r["hi"]}</span> / <span class="lo">{r["lo"]}</span> &deg;F', ""),
            "sky": (f'{esc(W.describe_sky(r["cloud"]))} <span class="muted">{r["cloud"]:.0f}%</span>', ""),
            "rain": ((f'{r["precip"]:.2f}"', "") if r["precip"] >= W.WET_IN else ("-", "muted")),
            "sun": (f'{esc(compact_time(r["sunrise"]))} / {esc(compact_time(r["sunset"]))}', ""),
            "notes": (" &middot; ".join(esc(t) for t in r["tags"]), "tags"),
        }
        if has_snow:
            s = r["snow"]
            if s:
                new = f'{s["new"]:.1f}"' if s["new"] >= W.SNOW_IN else "-"
                cell["newsnow"] = (new, "snowcell")
                cell["ground"] = (f'{s["start"]:.1f} &rarr; {s["end"]:.1f}"', "snowcell")
                cell["peak"] = (f'{s["peak"]:.1f}"', "snowcell")
            else:
                cell["newsnow"] = cell["ground"] = cell["peak"] = ("-", "muted")

        tds = []
        for k, _ in columns:
            inner, ccls = cell[k]
            if inner not in ("-", ""):
                nonempty.add(k)
            attr = f' class="{ccls}"' if ccls else ""
            tds.append(f'<td data-col="{k}"{attr}>{inner}</td>')
        tds.append('<td class="kebab-col"></td>')
        rowcls = ("drow dayrow " + cls).strip()
        body.append(f'<tr class="{rowcls}" data-month="{r["month"]}" data-day="{rid}">'
                    + "".join(tds) + "</tr>")

        if entry:
            # Pre-rendered and hidden rather than built in JS: keeps the file
            # printable and searchable (ctrl-F finds collapsed festival text).
            paras = "".join(f"<p>{esc(p)}</p>" for p in entry["body"]) or \
                '<p class="none">No further detail in the calendar for this day.</p>'
            greg = f' <span class="muted">({esc(entry["greg"])})</span>' if entry["greg"] else ""
            body.append(
                f'<tr class="drow detail" data-month="{r["month"]}" data-detail="{rid}">'
                f'<td colspan="{ncols}"><h4>{W.ordinal(r["day"])} Day{greg} - '
                f'{esc(entry["title"])}</h4>{paras}</td></tr>')

    empty_cols = [k for k, _ in columns if k not in nonempty]
    empty_js = "[" + ", ".join(f'"{k}"' for k in empty_cols) + "]"
    months_js = month_modal_json(cal, sorted({r["month"] for r in rows}))

    # Legend rows. The snow entry is omitted on a snowless range for the same
    # reason the snow columns are: describing a color the table never shows is
    # just noise. Thresholds are read from weather.py so they cannot drift.
    import json
    legend = [
        (ROW_COLORS["plain"], "Dry",
         f"No measurable precipitation (under {W.WET_IN:g} in)."),
        (ROW_COLORS["rain"], "Rain",
         f"{W.WET_IN:g} in or more of precipitation."),
    ]
    if has_snow:
        legend.append((ROW_COLORS["snow"], "Snow",
                       "Snow fell, or lay on the ground."))
    legend.append((ROW_COLORS["detail"], "Calendar entry",
                   "An expanded festival or observance, not a day of weather."))
    legend_js = json.dumps(legend)

    # Notes, not entries: the precedence rule is the single most useful
    # disambiguator (it explains why a rainy day can look gray), so it gets its
    # own line rather than trailing off the end of the snow definition.
    notes = []
    if has_snow:
        notes.append("A day that both rained and snowed is shaded as snow.")
    notes_js = json.dumps(notes)
    snow_note = "" if has_snow else " No snow fell in this range, so snow columns are omitted."
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><style>{CSS}</style><style id="colhide"></style><style id="monthhide"></style></head>
<body><div class="wrap">
<h1>{esc(title)}</h1>
<p class="sub"><b>{esc(place['place'])}</b> ({esc(house_label(place))}) &mdash; <span class="tip" title="Weather is indifferent to the plot by design.">real recorded weather</span> for its climate analog, <b>{esc(place['us_analog'])}</b>. {esc(span)}.{snow_note}</p>
<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>
{chr(10).join(body)}
</tbody></table></div>
<div id="kebab-menu" class="kebab-menu" hidden><div class="kebab-menu-title">Show columns</div>{toggles}<a href="#" id="cols-reset">show all</a><a href="#" id="legend-open">color legend</a></div>
<div id="modal-back" class="modal-back" hidden><div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
<button class="modal-close" id="modal-close" aria-label="Close">&times;</button>
<h2 id="modal-title"></h2><p class="mspan" id="modal-span"></p><div id="modal-body"></div>
</div></div>
</div>
<script>
(function () {{
  var KEY = "l7r_weather_hidden_cols";
  var EMPTY = new Set({empty_js});  // columns empty on every row: hidden by default each load, un-hide is ephemeral
  var style = document.getElementById("colhide");
  function loadSaved() {{ try {{ return new Set(JSON.parse(localStorage.getItem(KEY) || "[]")); }} catch (e) {{ return new Set(); }} }}
  function save(s) {{ try {{ localStorage.setItem(KEY, JSON.stringify(Array.from(s))); }} catch (e) {{}} }}
  var saved = loadSaved();                       // persisted user hides (never includes empty columns)
  var hidden = new Set(saved);
  EMPTY.forEach(function (k) {{ hidden.add(k); }});
  function apply() {{
    style.textContent = Array.from(hidden).map(function (k) {{ return '[data-col="' + k + '"]{{display:none}}'; }}).join("");
    document.querySelectorAll("input[data-toggle]").forEach(function (cb) {{ cb.checked = !hidden.has(cb.dataset.toggle); }});
  }}
  document.querySelectorAll("input[data-toggle]").forEach(function (cb) {{
    cb.addEventListener("change", function () {{
      var k = cb.dataset.toggle;
      if (cb.checked) hidden.delete(k); else hidden.add(k);
      if (!EMPTY.has(k)) {{ if (cb.checked) saved.delete(k); else saved.add(k); save(saved); }}
      apply();
    }});
  }});
  var reset = document.getElementById("cols-reset");
  reset.addEventListener("click", function (e) {{ e.preventDefault(); hidden.clear(); saved.clear(); save(saved); apply(); }});
  apply();

  var btn = document.getElementById("kebab-btn");
  var menu = document.getElementById("kebab-menu");
  function openMenu() {{
    var r = btn.getBoundingClientRect();
    menu.style.top = (r.bottom + 4) + "px";
    menu.style.right = Math.max(8, window.innerWidth - r.right) + "px";
    menu.hidden = false;
  }}
  function closeMenu() {{ menu.hidden = true; }}
  btn.addEventListener("click", function (e) {{ e.stopPropagation(); if (menu.hidden) openMenu(); else closeMenu(); }});
  document.addEventListener("click", function (e) {{ if (!menu.hidden && !menu.contains(e.target) && e.target !== btn) closeMenu(); }});
  document.addEventListener("keydown", function (e) {{ if (e.key === "Escape") closeMenu(); }});
  window.addEventListener("scroll", closeMenu, true);
  window.addEventListener("resize", closeMenu);

  var MKEY = "l7r_weather_collapsed_months";
  var mstyle = document.getElementById("monthhide");
  function loadC() {{ try {{ return new Set(JSON.parse(localStorage.getItem(MKEY) || "[]")); }} catch (e) {{ return new Set(); }} }}
  function saveC(s) {{ try {{ localStorage.setItem(MKEY, JSON.stringify(Array.from(s))); }} catch (e) {{}} }}
  var collapsed = loadC();
  function applyMonths() {{
    mstyle.textContent = Array.from(collapsed).map(function (m) {{ return 'tr.drow[data-month="' + m + '"]{{display:none}}'; }}).join("");
    document.querySelectorAll("tr.mhead").forEach(function (tr) {{ tr.classList.toggle("collapsed", collapsed.has(tr.dataset.month)); }});
  }}
  document.querySelectorAll("tr.mhead").forEach(function (tr) {{
    tr.addEventListener("click", function (e) {{
      if (e.target.closest(".mname")) return;   // month name opens the modal instead
      var m = tr.dataset.month;
      if (collapsed.has(m)) collapsed.delete(m); else collapsed.add(m);
      saveC(collapsed); applyMonths();
    }});
  }});
  applyMonths();

  // --- Calendar day expand/collapse -------------------------------------
  // Purely ephemeral: unlike columns and month collapse, an expanded festival
  // is a "read this now" action, not a viewing preference worth persisting.
  document.querySelectorAll(".calbtn").forEach(function (b) {{
    b.addEventListener("click", function (e) {{
      e.stopPropagation();
      var id = b.dataset.day;
      var detail = document.querySelector('tr.detail[data-detail="' + id + '"]');
      var row = document.querySelector('tr.dayrow[data-day="' + id + '"]');
      if (!detail) return;
      var open = detail.classList.toggle("open");
      row.classList.toggle("open", open);
    }});
  }});

  // --- Month modal ------------------------------------------------------
  var MONTHS = {months_js};
  var back = document.getElementById("modal-back");
  var mTitle = document.getElementById("modal-title");
  var mSpan = document.getElementById("modal-span");
  var mBody = document.getElementById("modal-body");
  function el(tag, text) {{ var n = document.createElement(tag); if (text != null) n.textContent = text; return n; }}
  function openModal(n) {{
    var mo = MONTHS[n];
    if (!mo) return;
    mTitle.textContent = mo.title;
    mSpan.textContent = mo.span;
    mBody.textContent = "";
    if (mo.meta.length) {{
      var dl = el("dl");
      mo.meta.forEach(function (kv) {{ dl.appendChild(el("dt", kv[0])); dl.appendChild(el("dd", kv[1])); }});
      mBody.appendChild(dl);
    }}
    mo.intro.forEach(function (p) {{ mBody.appendChild(el("p", p)); }});
    if (mo.days.length) {{
      mBody.appendChild(el("h4", "Observances this month"));
      var ul = el("ul"); ul.className = "days";
      mo.days.forEach(function (d) {{ ul.appendChild(el("li", d[0] + " - " + d[1])); }});
      mBody.appendChild(ul);
    }}
    back.hidden = false;
  }}
  function closeModal() {{ back.hidden = true; }}

  // Legend reuses the month modal's shell - same close affordances, one dialog.
  var LEGEND = {legend_js};
  var NOTES = {notes_js};
  document.getElementById("legend-open").addEventListener("click", function (e) {{
    e.preventDefault();
    closeMenu();
    mTitle.textContent = "Row colors";
    mSpan.textContent = "What the shading of each row means.";
    mBody.textContent = "";
    var ul = el("ul"); ul.className = "legend";
    LEGEND.forEach(function (row) {{
      var li = el("li");
      var sw = el("span"); sw.className = "sw"; sw.style.background = row[0];
      li.appendChild(sw);
      var lb = el("span", row[1]); lb.className = "lb"; li.appendChild(lb);
      var ds = el("span", row[2]); ds.className = "ds"; li.appendChild(ds);
      ul.appendChild(li);
    }});
    mBody.appendChild(ul);
    NOTES.forEach(function (t) {{
      var n = el("p", t); n.className = "note"; mBody.appendChild(n);
    }});
    var src = el("p", "Grounded in historical reanalysis (Open-Meteo / ERA5).");
    src.className = "src";
    mBody.appendChild(src);
    back.hidden = false;
  }});
  document.querySelectorAll(".mname").forEach(function (b) {{
    b.addEventListener("click", function (e) {{ e.stopPropagation(); openModal(b.dataset.month); }});
  }});
  document.getElementById("modal-close").addEventListener("click", closeModal);
  back.addEventListener("click", function (e) {{ if (e.target === back) closeModal(); }});
  document.addEventListener("keydown", function (e) {{ if (e.key === "Escape") closeModal(); }});
}})();
</script>
</body></html>"""


def main() -> None:
    args = sys.argv[1:]
    out = None
    if "--out" in args:
        k = args.index("--out")
        out = Path(args[k + 1])
        args = args[:k] + args[k + 2:]
    if len(args) != 5:
        sys.exit('Usage: python3 weather_range.py "<place>" <start_month> <start_day> <end_month> <end_day> [--out file.html]')
    query, nums = args[0], args[1:]
    try:
        sm, sd, em, ed = (int(x) for x in nums)
    except ValueError:
        sys.exit("Month/day values must be numbers")
    for label, m, d in (("start", sm, sd), ("end", em, ed)):
        if not (1 <= m <= 12 and 1 <= d <= 30):
            sys.exit(f"{label} date out of range (month 1-12, day 1-30)")

    place = W.find_place(query)
    if place is None:
        known = ", ".join(p["place"] for p in W.load_places())
        sys.exit(f"REJECTED: no place matching '{query}'. Known places: {known}")
    loaded = W.load_year(place)
    if isinstance(loaded, str):
        sys.exit(loaded)
    raw, year = loaded

    rows = build_rows(raw, year, list(rok_range(sm, sd, em, ed)))
    html = render(place, rows, sm, sd, em, ed, C.parse_calendar())

    if out is None:
        REPORTS.mkdir(exist_ok=True)
        out = REPORTS / f"{slug(place['place'])}-{rows[0]['greg']:%Y%m%d}-{rows[-1]['greg']:%Y%m%d}.html"
    out.write_text(html)
    print(f"Wrote {len(rows)} days to {out.resolve()}")


if __name__ == "__main__":
    main()
