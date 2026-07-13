# Quickstart: Building City Quarter Density and Wall-Sizing Correctness

The build order enforces the acceptance discipline we skipped last time: the known-bad map becomes a fixture that MUST fail before anything is fixed. Work from `/gm-assistant/.claude/skills/diagram/`.

## 0. Snapshot the broken map FIRST (before any code change)

```
cp pool/nagahara.json pool/regressions/city_density_broken_nagahara.json
```

This freezes the current defective state (525 in-wall dwellings, ~35 extramural commoners, empty NW quarter, near-empty block, verdict "about right"). Every new check must be shown to fire on this snapshot.

## 1. Red-first, one check at a time

For each new check (extramural commoners, quarters declared/tiling, per-quarter density + dead-zone, civic-open, reserve-cap, reworked verdict):

1. Add the GENERAL rule to `check_village.py` (no city named in the logic).
2. Prove RED: run it against the broken snapshot and confirm it fires; add a focused synthetic-manifest unit test in `test_checks.py` that fails before the check exists and passes after (red-green).
3. Only then move on. Do NOT fix the generators yet.

```
python3 -m pytest test_checks.py -k <check_name> -q
python3 -c "import json,check_village as c; c.gate(json.load(open('pool/regressions/city_density_broken_nagahara.json')))" | grep FAIL
```

## 2. Engine: declare quarters

Add `s.quarter(poly, zone, kind=...)` to `settlement.py` with unit tests in `test_settlement.py` (records `M["quarters"]`; reserves render). Keep it purely declarative + decorative (no placement change).

## 3. Retrofit Tango (the good anchor), then calibrate

- Add quarter declarations to `pool/tango.gen.py` (residential wards, civic yamen/temple precincts, the agricultural district as a `reserve`).
- Regenerate; run the new checks. Tune `QUARTER_DENSITY_FLOOR/CEIL`, `CIVIC_OPEN_TOL`, `RESERVE_CAP_FRAC`, `DEAD_ZONE_MAX` so **Tango passes and the broken-Nagahara snapshot still fails**. Record each number's "why" in `settlements.md`.

```
python3 pool/tango.gen.py && python3 check_village.py pool/tango.json
python3 check_village.py pool/tango.json --capacity --capacity-map
```

## 4. Fix Nagahara

- Declare Nagahara's quarters; ensure NO commoner dwelling is placed outside the wall (route the former extramural top-ups inside).
- Apply the capacity verdict: it should now read `densify` or `shrink`. If `shrink`, resize the wall by `suggested_wall_scale` about the centre (the whole-map coordinate scale) so the residential quarters fill it; re-run the capacity analysis until `sized_and_packed`.
- Regenerate, run the FULL validator to zero mechanical fails, render and eyeball.

```
python3 pool/nagahara.gen.py && python3 check_village.py pool/nagahara.json
rsvg-convert -w 950 pool/nagahara.svg -o /tmp/nag.png   # then view
```

## 5. Pin fixtures + wire tests

- Keep `pool/regressions/city_density_broken_nagahara.json`; add it to `test_regressions.py` asserting the new checks fire on it.
- Ensure each new check has its synthetic red fixture / unit test.

## 6. Green gate

```
python3 -m pytest          # 100% coverage gate; all pool maps pass
ruff check . && ruff format --check . && mypy --strict check_village.py settlement.py
grep -RclP '[\x{2013}\x{2014}]' *.py *.md pool/*.gen.py   # must be 0 (no em/en dashes)
```

## Definition of done (maps to Success Criteria)

- Broken-Nagahara snapshot fires all four defect checks (SC-001); Tango passes all new checks (SC-002).
- Shipped Nagahara: 0 extramural commoner dwellings, every residential quarter in band, no near-empty residential quarter, passes the full validator (SC-003, SC-004).
- Capacity verdict maps to one clear action and agrees with the population check on every map (SC-005); an over-cap-reserve city is flagged (SC-006).
- Whole pool green, 100% coverage, no forbidden dashes (SC-007).
