# PENDING: the enclosed-fan tract floor check (GM decision 2026-08-03)

**Why pending:** the rule is DECIDED (settlements/fields.md "Paddy TRACT size") and the check below
is written and was unit-tested, but it fires on the three town maps (hoshizora-west 1.8 ac,
ubame-west 2.1 ac, hirameki w1/e1/e2 1.1-2.5 ac), each of which needs a QUARTER-SCALE recomposition
to comply - Hoshizora's stream/funerary wedge, Ubame's south quarter (crematory + flophouse +
laborer pocket), Hirameki's SE (burakumin quarter + funerary + tanning yard). Those are curated
maps; the GM chooses the recomposition. A red gate cannot land, and a scale-exempted check is the
"check that never runs" antipattern - so the check waits for the maps, not the other way round.

**What already landed with the decision (2026-08-03):** Tango's four offenders are fixed - fn1/fn2
(sluices raised off-view) and fs1 (fall extended) are honest off-view slices, nw1 is the in-wall
exemption encoded below. Town-fan probe findings worth keeping: build_comb clips its march ~40px
inside the W/H it is HANDED, so a fan crosses a canvas edge only when built on an OVERSIZED canvas
(ubame-south, hoshizora-ne already do this); a brook-fed fan can slice an edge by raising its
sluice OFF-canvas (the tango fn1 pattern); and at 1 ft/px town falls/canals, a single fan tops out
~5-7 ac, so 8-ac ENCLOSED fans need genuinely open ground.

**To restore when the towns comply:** drop the code below back into gate() right before the
`_fanft = float(meta.get("ftpx") or 1)` line (it shares EX0..EY1/meta/check from the enclosing
scope); re-freeze the pre-fix hoshizora manifest as
`pool/regressions/enclosed_fan_at_least_hamlet_grade_fires_on_the_capped_hoshizora_west_comb.json`
(git history of 2026-08-03 has it); and restore the three unit tests removed from test_checks.py
the same day (`test_enclosed_fan_at_least_hamlet_grade_fires_on_a_small_enclosed_fan`,
`test_enclosed_fan_floor_exempts_an_off_view_slice_and_passes_hamlet_grade`,
`test_enclosed_fan_floor_exempts_the_in_wall_district`).

```python
    # PADDY TRACT FLOOR (GM 2026-08-03; settlements/fields.md "Paddy TRACT size", research/fields.md
    # "Tract sizes - no settlement-class cap"). A fan that is ENCLOSED in the rendered view reads as a
    # COMPLETE field system, and the smallest attested communal waterworks - a fan with a real weir,
    # canals, and drain collector - commands ~8 acres (hamlet grade). A fan running off the view edge
    # is a SLICE of a larger tract and is exempt on-map: the truncation itself says "more beyond".
    # Universal on purpose: history sizes a tract by water/terrain/households, never settlement class.
    # AREA measure on the recorded outline (no center/footprint question arises).
    _fanft = float(meta.get("ftpx") or 1)
    _small = []
    for _ff in M.get("fields", []):
        if _ff.get("kind") != "paddy":
            continue
        _fo = _ff["outline"]
        if any(p[0] < EX0 + 8 or p[0] > EX1 - 8 or p[1] < EY0 + 8 or p[1] > EY1 - 8 for p in _fo):
            continue  # runs off (or touches) the view edge - an honest slice of a larger tract
        _fcx = sum(p[0] for p in _fo) / len(_fo)
        _fcy = sum(p[1] for p in _fo) / len(_fo)
        if M.get("wall") and point_in_poly(_fcx, _fcy, M["wall"]):
            continue  # the documented IN-WALL agricultural district (tango's nw1): bounded by the rampart, not a rural communal system claiming completeness - the floor does not govern it
        _fac = poly_area([(p[0], p[1]) for p in _fo]) * _fanft * _fanft / 43560.0
        if _fac < 8.0:
            _small.append((_ff.get("name", "?"), round(_fac, 1)))
    check(
        "enclosed_fan_at_least_hamlet_grade",
        not _small,
        f"enclosed paddy tract(s) under the 8-acre communal-waterworks floor: {_small} - a fan fully inside "
        f"the view reads as a COMPLETE system, and nobody builds a weir + canal fork + collector for less "
        f"than hamlet-grade ground; grow the fan (>= 8 real acres) or run it off the view edge as a slice "
        f"(settlements/fields.md 'Paddy TRACT size')",
    )

```
