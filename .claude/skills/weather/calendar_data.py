#!/usr/bin/env python3
"""Parse the /calendar skill's month-by-month breakdown into structured data.

The canonical calendar lives in `.claude/skills/calendar/SKILL.md` inside a
`SOURCE: GM NOTES` block, so it is read-only here - this module never writes to
it. The breakdown is regular enough to parse directly rather than duplicating it
into a JSON pool, which keeps the GM's prose as the single source of truth: edit
SKILL.md and every weather report picks the change up on its next build.

Shape of the source, per month:

    3rd Month: Yayoi ("new life"), Month of the Serpent   <- header
    5 April - 5 May                                       <- Gregorian span
    Seasonal color: ...                                   <- meta lines
    Flowers of Spring: ...
    Flowers of Yayoi: ...
                                                          <- blank
    <intro paragraphs>
    3rd Day (7 Apr): Hinamatsuri (Doll Festival) ...      <- day entry
    <body paragraphs>

Day entries may have an empty body (the 12th month lists four bare day headers),
and the parenthesised Gregorian date is optional.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TypedDict

CALENDAR_MD = Path(__file__).resolve().parent.parent / "calendar" / "SKILL.md"

MONTH_RE = re.compile(r"^(\d+)(?:st|nd|rd|th) Month: (\S+) \((.*)\), Month of the (.+)$")
DAY_RE = re.compile(r"^(\d+)(?:st|nd|rd|th) Day(?: \(([^)]+)\))?: (.+)$")
META_RE = re.compile(r"^(Seasonal colou?r|Flowers of [^:]+): (.+)$")


class Day(TypedDict):
    day: int
    title: str
    greg: str  # "7 Apr", or "" when the source omits it
    body: list[str]


class Month(TypedDict):
    month: int
    name: str
    meaning: str
    zodiac: str
    span: str  # "5 April - 5 May"
    meta: list[tuple[str, str]]  # ("Seasonal color", "Cherry combination ...")
    intro: list[str]
    days: dict[int, Day]


def _clean_meaning(raw: str) -> str:
    """`"new life"` -> `new life`; `"unohana" or "deutzia"` is left intact."""
    inner = raw.strip()
    if inner.count('"') == 2 and inner.startswith('"') and inner.endswith('"'):
        return inner[1:-1]
    return inner


def parse_calendar(path: Path | None = None) -> dict[int, Month]:
    """Return {month number: Month} for all twelve months."""
    text = (path or CALENDAR_MD).read_text()
    months: dict[int, Month] = {}
    cur: Month | None = None
    day: Day | None = None
    in_head = False  # between the month header and its first blank line

    for line in text.splitlines():
        stripped = line.strip()

        m = MONTH_RE.match(stripped)
        if m:
            cur = Month(month=int(m[1]), name=m[2], meaning=_clean_meaning(m[3]),
                        zodiac=m[4], span="", meta=[], intro=[], days={})
            months[cur["month"]] = cur
            day, in_head = None, True
            continue

        if cur is None:
            continue

        d = DAY_RE.match(stripped)
        if d:
            day = Day(day=int(d[1]), greg=d[2] or "", title=d[3], body=[])
            cur["days"][day["day"]] = day
            in_head = False
            continue

        if not stripped:
            in_head = False
            continue

        if in_head:
            meta = META_RE.match(stripped)
            if meta:
                cur["meta"].append((meta[1], meta[2]))
            elif not cur["span"]:
                cur["span"] = stripped
            else:  # pragma: no cover - no month currently has other head lines
                cur["intro"].append(stripped)
        elif day is not None:
            day["body"].append(stripped)
        else:
            cur["intro"].append(stripped)

    return months


if __name__ == "__main__":  # pragma: no cover - manual inspection aid
    cal = parse_calendar()
    for n in sorted(cal):
        mo = cal[n]
        print(f"{n:2d} {mo['name']} ({mo['meaning']}), {mo['zodiac']} - {mo['span']}"
              f"  [{len(mo['meta'])} meta, {len(mo['intro'])} intro, {len(mo['days'])} days]")
        for dn in sorted(mo["days"]):
            dd = mo["days"][dn]
            print(f"     {dn:2d} {dd['title']!r:60} ({len(dd['body'])} paras)")
