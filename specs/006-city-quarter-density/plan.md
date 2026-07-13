# Implementation Plan: City Quarter Density and Wall-Sizing Correctness

**Branch**: `006-city-quarter-density` | **Date**: 2026-07-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-city-quarter-density/spec.md`

## Summary

Replace the `/diagram` provincial-city wall-sizing model, which is a global aggregate that passed a visibly-broken Nagahara, with a spatial, per-quarter model. Cities declare their quarters as first-class regions (polygon + zone in {residential, civic, mixed, reserve}, reserves carrying a kind). The validator judges density per residential quarter (with a dead-zone guard so a half-empty quarter cannot hide behind a good average), flags any commoner dwelling outside the walls (hard zero), caps declared reserve ground at ~20% of the interior, and reframes the capacity verdict around usable residential ground so "shrink the wall" becomes a real recommendation. Empirical anchor: Tango (good) and the current broken Nagahara have nearly identical block-density medians; the discriminator is whether empty ground sits in a declared civic/reserve quarter (fine) or a residential quarter (broken) - which is exactly why the check must read declared quarters, not infer from pixels.

## Technical Context

**Language/Version**: Python 3.14 (the `/diagram` skill's own tooling; the skill has its own `pyproject.toml` and is independent of the webapp's 3.13 pin).

**Primary Dependencies**: Standard library only for production code (`math`, `json`). Tests use `pytest` + `pytest-cov`. PNG rendering for visual verification uses the external `rsvg-convert` binary. Generators import the in-repo `settlement.py`, `waterfields.py`, and `check_village.py`.

**Storage**: Files only. City generators `pool/<city>.gen.py` emit `pool/<city>.json` (the manifest the validator reads) and `pool/<city>.svg`. Negative fixtures live under `pool/regressions/<check>_fires_on_<case>.json`.

**Testing**: `pytest` from the skill directory, gated at `--cov-fail-under=100` over `check_village.py` + `settlement.py` (per `pyproject.toml`; `pool/*.gen.py` are omitted from coverage - generators are exercised by running them, checks/engine are unit-tested). Test files: `test_checks.py`, `test_settlement.py`, `test_regressions.py`, `test_villages.py`.

**Target Platform**: Linux CLI, invoked in-session by the `/diagram` skill.

**Project Type**: Single project - a skill comprising a drawing engine (`settlement.py`), a validator (`check_village.py`), per-city generators (`pool/*.gen.py`), tests, and doctrine (`settlements.md`).

**Performance Goals**: Not latency-bound. Note the full suite runs ~9-10 minutes because `test_villages.py` regenerates the pool maps; keep new tests as direct synthetic-manifest unit tests (fast) rather than full regenerations where possible.

**Constraints**: 100% line coverage on `check_village.py` + `settlement.py`; hyphens only (no em/en-dashes) everywhere; China-first historical grounding; every research-driven threshold records its "why" (constitution + CLAUDE.md).

**Scale/Scope**: 2 worked cities (Tango, Nagahara) plus ~7 other pool maps (villages/towns) that must keep passing. `check_village.py` ~3,300 statements, `settlement.py` ~3,200; the change adds an engine helper, several checks, a reworked `city_capacity`, generator quarter declarations for both cities, fixtures, and doctrine.

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 design (below).*

- **I. Accessibility-First Viewports (NON-NEGOTIABLE)**: N/A. No webapp UI is added or changed. The artifact is an SVG/PNG map; its visual verification analog is rendering the PNG and reviewing it (and the `building-review` subagent), which the plan commits to under Principle VI rather than the webapp screenshot suite.
- **II. Bold, Intentional Design**: N/A. No new UI surface; reserve rendering reuses the existing map drawing vocabulary (textures/fills already in `settlement.py`).
- **III. Pool Data Conventions**: N/A with justification. The `/diagram` pool is code-generated SVG/JSON, not the markdown-with-YAML content pool the principle governs (relics/names). The applicable convention here is the existing `pool/regressions/*.json` negative-fixture pattern, which the plan follows (FR-012, FR-014). No city names are baked into reusable frontmatter - Tango and Nagahara are explicitly-scoped worked examples, not reusable pool content.
- **IV. One Canonical Home for GM Source**: N/A. No SOURCE blocks added or moved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS. No task modifies any content inside SOURCE markers.
- **VI. Verify Before Reporting Done**: PASS. Each check task runs `pytest` (with the 100% gate) and proves red-then-green on the defective fixture; each generator task regenerates the map, runs the full validator to zero mechanical fails, renders the PNG, and eyeballs it (with a `building-review` pass on the final Nagahara, since author is not a reliable reviewer).
- **VII. De-Localized Generation by Default**: N/A. No pool content is generated; the worked cities are GM-scoped fixtures.
- **VIII. Direct Voice Over Framing Distance**: N/A. No in-world prose is written.
- **IX. Setting Integration (NON-NEGOTIABLE for name collisions)**: PASS. Grounding cross-references `budgets.md` (city demographics) and the China-first geography stance; the reserve kinds (drill ground, garden, agricultural district) are historically grounded (Phase 0 research). No new named NPCs or places are invented, so no campaign-names-cache collision risk.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS. Commit to: `ruff check` + `ruff format --check` clean; `mypy --strict` on `check_village.py` + `settlement.py`; red-green TDD (each new check has a failing synthetic-manifest test before the check lands, and the real broken-Nagahara fixture is the motivating red per the project's red-first discipline); `pytest --cov-fail-under=100`; external boundaries (none new here) via fixtures not mocks; no swallowed exceptions; no `print` in library paths (the `--capacity` CLI print stays behind the `__main__` guard); behavior-named, parametrized tests; thresholds as named module constants with recorded rationale (no magic numbers).
- **XI. Japanese Authenticity (NON-NEGOTIABLE)**: PASS/conditional. Any Japanese label introduced for a reserve kind (e.g. a drill-ground label) MUST pass the kanji-romaji-meaning triangle; the default is to use the existing English/roman labels already in the engine and add Japanese only where it passes the triangle.

No gates are DEFERRED; no Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/006-city-quarter-density/
├── plan.md              # This file
├── spec.md              # Feature spec (complete, clarifications resolved)
├── research.md          # Phase 0 output (empirical calibration + historical grounding)
├── data-model.md        # Phase 1 output (Quarter/Reserve entities, manifest schema, verdict enum)
├── contracts/           # Phase 1 output (engine API, manifest schema, check contracts, capacity report)
│   └── interfaces.md
├── quickstart.md        # Phase 1 output (the red-first build/calibration workflow)
└── checklists/
    └── requirements.md  # Spec quality checklist (complete)
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── settlement.py          # ENGINE: add s.quarter(poly, zone, kind=...) + reserve rendering; record M["quarters"]
├── check_village.py       # VALIDATOR: inside-wall population count; new per-quarter + extramural + reserve-cap checks; reworked city_capacity verdict against usable residential ground
├── settlements.md         # DOCTRINE: quarter/zoning model, per-quarter density, reserve rules, reframed verdicts + the "why" for every threshold
├── pool/
│   ├── tango.gen.py       # retrofit: declare quarters (good calibration anchor)
│   ├── tango.json/.svg    # regenerated
│   ├── nagahara.gen.py    # fix: quarters, no extramural commoners, densify/resize per new verdict
│   ├── nagahara.json/.svg # regenerated
│   └── regressions/
│       └── <new negative fixtures>.json   # pre-change broken Nagahara + synthetic per-check fixtures
├── test_checks.py         # unit tests for each new check (synthetic manifests, red-first)
├── test_settlement.py     # unit tests for s.quarter + reserve rendering
└── test_regressions.py    # wires the pinned negative fixtures
```

**Structure Decision**: Single project, editing the existing `/diagram` skill in place. The three production surfaces are the engine (`settlement.py`), the validator (`check_village.py`), and the two city generators; tests and doctrine sit alongside per the project convention.

## Design Approach (how the pieces fit)

1. **Engine (`settlement.py`)**: add `s.quarter(poly, zone, kind=None, label=None)` that records `{poly, zone, kind}` into `M["quarters"]` and, for `zone="reserve"`, draws the declared kind as a visible feature (drill-ground surface / garden / it may delegate to the existing field routines for `agricultural_district`). Quarters are declarative overlays on the existing placement; they do not change how packs are placed, only how the map records intent.

2. **Validator (`check_village.py`)**:
   - `population_consistent_with_housing`: for a walled city, count only in-wall dwellings (fixes the leak; aligns with `city_capacity`'s `D`).
   - New `city_commoner_dwellings_inside_walls`: hard-zero commoner dwellings outside the wall; exempt kinds are samurai estates, farmhouses, wharf, gate-market shops.
   - New `city_quarters_declared` + `city_quarters_tile_interior`: a walled city must declare quarters; they must cover the interior without overlaps or extramural spill.
   - New `city_residential_quarters_dense_enough`: per residential/mixed quarter, average dwelling density in a calibrated band, PLUS a dead-zone guard (no contiguous empty sub-region larger than a fire-break inside a residential quarter) so a half-empty quarter fails even with an acceptable average.
   - New `city_civic_quarter_not_mostly_open` and `city_reserve_within_cap`.
   - Reworked `city_capacity`: `residential_capable = interior - civic - reserve`; verdict in {densify, enlarge, shrink, sized-and-packed} against that, with the densify boundary aligned to `population_tol`; the ASCII `--capacity-map` gains quarter/zone overlay.
   - Thresholds become named module constants with recorded rationale, calibrated so Tango passes and the pinned broken Nagahara fails.

3. **Generators**: Tango declares its quarters (residential wards, civic yamen/temple precincts, the agricultural district as a reserve). Nagahara declares quarters, is fixed so no commoner dwelling sits outside the wall, and its wall is resized (per the new verdict, likely shrunk) and/or its empty NW ground given a declared purpose so every residential quarter fills.

4. **Fixtures + calibration**: snapshot the current broken `nagahara.json` first; add each check red-first (prove it fires on the snapshot); calibrate the band on Tango-good + Nagahara-bad; then fix the generators; pin the snapshot and per-check synthetics under `pool/regressions/`.

## Complexity Tracking

No constitution violations; no entries required.
