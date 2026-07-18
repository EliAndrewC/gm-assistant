# Implementation Plan: Budget-First City Wall Sizing

**Branch**: `main` (no feature branch - the GM handles all git) | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-city-area-budget/spec.md`

## Summary

Invert provincial-city generation from guess-the-wall-then-iterate to budget-first: a new pure-logic module computes the city's complete space budget (building inventory from the budgets.md caste mix, packed vs spaced ground costs, civic program, non-building features, a researched circulation fraction) and derives the wall ellipse/arc from it BEFORE anything is placed. The existing `city_capacity` machinery remains the verification gate but gains a budget-vs-enclosed-area check; the current too-empty Nagahara is pinned as a known-bad fixture; Nagahara is regenerated budget-first and must come out packed.

## Technical Context

**Language/Version**: Python 3.13 (same as the rest of the diagram skill)

**Primary Dependencies**: none new - stdlib only, consistent with `settlement.py` / `check_village.py`. Rendering stays `rsvg-convert`/existing pipeline.

**Storage**: pool files (`pool/nagahara.gen.py`, `pool/nagahara.{svg,png,json}`), regression fixtures under `pool/regressions/`, docs in `settlements.md`

**Testing**: pytest + pytest-cov via the skill's `make done` gate (ruff check, ruff format --check, mypy --strict, pytest, 100% coverage on the engine modules)

**Target Platform**: dev container CLI (the /diagram skill)

**Project Type**: single-project skill library (new module alongside `settlement.py`)

**Performance Goals**: n/a (offline generation; budget math is trivial arithmetic)

**Constraints**:
- A PARALLEL session is actively editing `settlement.py` / `check_village.py` (village work). Mitigation: all new logic lives in a NEW module `citybudget.py`; edits to shared engine files are kept small, additive, and anchored on text (re-grep on "file modified since read"); run the full suite before declaring done.
- Scale ladder fixed: provincial city 1px = 3ft; budget must cost DRAWN footprints (legibility floors included).
- Wall must fit the canvas; fail loudly on conflict.

**Scale/Scope**: 1 new module (~200-350 lines), 1-2 new checks in `check_village.py`, 1 regenerated pool city, 2 pinned fixtures, docs

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no webapp UI. Diagram outputs are SVG/PNG pool artifacts verified by the skill's own validator gate + visual review, not the browser viewport suite.
- **II. Bold, Intentional Design**: N/A - no new UI surface; the map style library is unchanged.
- **III. Pool Data Conventions**: PASS - no new pool *content kind*; Nagahara keeps the established settlement-pool convention (`<name>.gen.py` + `.svg` + `.png` + `.json` manifest). Regression fixtures follow `pool/regressions/<check>_fires_on_<why>.json`.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks touched. The caste mix is *referenced* from budgets.md (`Provincial city` table), never duplicated as a source block; the budget module encodes the derived family counts with a comment pointing at the table.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS - no task touches SOURCE-marked content.
- **VI. Verify Before Reporting Done**: PASS - every task ends with: `make done` in the skill dir (ruff + format + mypy --strict + pytest + 100% cov), `python3 check_village.py pool/<map>.json` green for ALL pool maps, regression suite green, PNG re-rendered and eyeballed; final Nagahara goes to the GM for visual sign-off (SC-001 explicitly reserves final judgment to the GM's eye).
- **VII. De-Localized Generation by Default**: PASS - the budget model itself is fully generic (population + program in, wall out). Nagahara is an existing named pool settlement being regenerated in place, consistent with the settlement pool's worked-example convention.
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose; map labels unchanged.
- **IX. Setting Integration**: PASS - dwelling counts derive from the budgets.md Provincial city caste table (600 families: servants 120, laborers 240, merchants 150, burakumin 30, samurai 60; zero farmers unless the agricultural-district toggle overrides); no new named figures.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS - `citybudget.py` is mypy-strict from day one (added to `pyproject.toml` `files`), ruff-clean, red-green TDD (new checks land red against the pinned bad fixture first, per the skill's established red-first check discipline), 100% line coverage via `test_citybudget.py`, no new dependencies, no prints in library code (the report formatter RETURNS a string; the CLI entry may print).
- **XI. Japanese Authenticity (NON-NEGOTIABLE)**: N/A - no new kanji-bearing content.

No DEFERRED gates; Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/009-city-area-budget/
├── plan.md              # This file
├── research.md          # Phase 0: circulation fraction + Tango/Nagahara calibration measurements
├── data-model.md        # Phase 1: CityProgram / BudgetLine / CityBudget / WallSpec entities
├── quickstart.md        # Phase 1: how to budget a new city + regenerate an existing one
├── contracts/
│   └── citybudget-api.md  # Phase 1: module API + manifest schema (M["budget"]) + check contract
└── tasks.md             # Phase 2 (/speckit-tasks - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── citybudget.py            # NEW pure-logic module: caste mix -> inventory -> area budget -> wall spec + report
├── test_citybudget.py       # NEW: 100%-coverage unit tests incl. Tango back-prediction + band sweep
├── check_village.py         # + city_wall_matches_budget check (+ manifest budget plumbing in city_capacity report)
├── test_checks.py           # + red/green tests for the new check
├── settlement.py            # minimal: s.meta(budget=...) passthrough into the manifest (if not already generic)
├── settlements.md           # + "Budget-first wall sizing" doctrine section w/ historical grounding (FR-003, SC-005)
├── SKILL.md                 # city workflow section updated: budget FIRST, wall derived
└── pool/
    ├── nagahara.gen.py      # regenerated budget-first (wall derived from citybudget output)
    ├── nagahara.{svg,png,json}
    └── regressions/
        ├── city_budget_fires_on_the_too_empty_nagahara.json   # pinned pre-feature Nagahara (known-bad)
        └── (existing fixtures unchanged)
```

**Structure Decision**: single new module inside the diagram skill, mirroring how `waterfields.py` (village water-first engine) and `pack_audit.py` sit beside `settlement.py`. This concentrates the feature in files the parallel village session is NOT editing; the only shared-file edits are the new check registration in `check_village.py` and (if needed) a one-line meta passthrough in `settlement.py`.

## Design Decisions (Phase 1 summary - details in data-model.md / contracts/)

1. **The budget is computed by the gen script BEFORE `s.city_wall`** - `citybudget.plan_city(program) -> CityBudget` returns itemized lines, required interior area, and a derived `WallSpec` (CX/CY-agnostic semi-axes RX/RY for a closed ring; equivalent-area arc parameters for a river-bank city). The gen script places the wall from the spec and records the budget into the manifest (`M["budget"]`) so checks compare promised vs delivered.
2. **Ground costs are DRAWN-footprint gross costs per spacing class** (PACKED vs SPACED), calibrated from the shipped Tango manifest (research.md): packed dwellings inherit the row-packing doctrine (touching rows + eave gaps + roji share), spaced kinds carry their measured margins. Calibration constants live in `citybudget.py` with the "why" comments (Constitution + CLAUDE.md research-rule requirement).
3. **Circulation is a fraction of interior area**, historically grounded (China first, jokamachi tiebreaker - research.md) and cross-checked against Tango's measured street+alley+ring-road share.
4. **The civic program is a fixed floor, not per-capita** - governor's mansion, 6 ministries, temples, theater, gate furniture, flophouse(s), wells etc. enter as absolute areas so a pop-2,000 city cannot squeeze them out.
5. **Toggles/program flags**: `river` (open-arc wall; wharf/canal/dock handling), `agricultural_district` (adds itemized in-wall farm ground; default False), plus explicit extras hook for city-specific features.
6. **Verification**: new check `city_wall_matches_budget` (walled-city scope) recomputes required area from `M["budget"]` and compares the measured enclosed interior; fails on mismatch beyond tolerance in EITHER direction. Pinned pre-feature Nagahara must fail it; Tango must pass. `city_capacity` verdict must be `sized_and_packed` first pass for a budget-first city.
7. **TDD order**: pin the bad fixture -> write the check red -> build `citybudget.py` under unit tests (Tango back-prediction = the calibration test) -> regenerate Nagahara green.

## Complexity Tracking

No constitutional violations to justify.
