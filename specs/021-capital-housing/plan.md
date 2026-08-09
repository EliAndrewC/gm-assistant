# Implementation Plan: Capital Housing Layer

**Branch**: `021-capital-housing` (no git branch; `SPECIFY_FEATURE=021-capital-housing`) | **Date**: 2026-08-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/021-capital-housing/spec.md`

## Summary

Fill Shiro Daika's interior fabric around the 020 reservations and ship the first green
capital: rank-graded samurai districts (walled yashiki / detached / retainer terraces per the
`plan_capital` rank bands), commoner machi in the city row doctrine, cistern-wells in the
aqueduct's service band, the fire-tower + kido mesh, the two sovereign precinct interiors and
their monzen neighborhoods, the lean teramachi backstrip, wind-gated nuisance trades, the
wharf's kashi fabric, and the relay stables + farrier - then a caption-loudness pass, the
move to `pool/capitals/`, and a FULL settlement review. Every capability is an engine knob a
future capital gen calls; Shiro Daika is the proving map.

## Technical Context

**Language/Version**: Python 3.14 (project pin; no new runtime)

**Primary Dependencies**: none added - `settlement.py` / `check_village.py` / `citybudget.py`
engine, resvg render path, existing pool tooling (`regen.py`, `crop_map.py`, `why_placed.py`)

**Storage**: pool JSON manifests + gitignored PNG renders (existing conventions)

**Testing**: pytest (`-n auto`), 100% line coverage gate via `make done`; regression fixtures
in `pool/regressions/`; the pool sweep (`test_villages.py`) as the integration bed

**Target Platform**: the dev container (Linux); no runtime service

**Project Type**: generator library + data pool (single project, existing layout)

**Performance Goals**: the capital gen stays within a declared `GEN_TIME_BUDGETS` entry;
~2,472 dwellings vs Minami's 541 means a measured perf pass (SeatMemo re-visit share,
`fill_exactly` behavior) is IN scope, with the A/B-two-timed-runs method, before the budget
entry is set (research.md item 14)

**Constraints**: pool byte-identity for every map this feature does not touch (new engine
params default to legacy behavior); keep-clear contract for every new manifest key; DRAW
ORDER doctrine (reserve before place, draw after what you must not sit on); no new waivers

**Scale/Scope**: one map (wip -> pool/capitals/), ~2,472 dwellings, ~10-15 fire towers,
~160-240 wells, 2 precinct interiors, ~4-8 merchant estates, 2 burakumin quarters + 2
tanning yards, several theater stages

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no webapp UI; the artifact is a rendered map
  PNG whose review path is the settlement-review agent + the GM's own read (Principle XII
  closing bookend), not the viewport suite.
- **II. Bold, Intentional Design**: N/A - no new UI surface; map style is the established
  diagram vocabulary.
- **III. Pool Data Conventions**: N/A (with justification) - `/diagram`'s pool convention is
  gen.py + JSON manifest + gitignored render, established since the pool began; the
  markdown-with-YAML convention governs prose pools, not maps.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks move; doctrine additions
  go to their existing homes (`settlements/capitals.md`, `research/cities/capitals.md`).
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS - no task touches SOURCE-marked
  content.
- **VI. Verify Before Reporting Done**: PASS - per-task verification listed in tasks.md:
  red-green tests, whole-file pre-gate runs, `make done` backgrounded with its log tail
  read, rendered-crop inspection for every visual change, FULL settlement-review before
  ship, and spot-checks of any delegated review's claims.
- **VII. De-Localized Generation by Default**: PASS - engine capabilities are generic knobs
  (FR-013); Shiro Daika specifics live only in its gen, exactly as every pool map.
- **VIII. Direct Voice Over Framing Distance**: N/A - map captions only, no in-world prose.
- **IX. Setting Integration**: PASS - housing counts and caste splits come from budgets.md
  via `plan_capital`; temple staffing from the GM's temple-density canon; ashigaru are
  peasants in Rokugan (no ashigaru quarter - retainer terraces per the recorded
  correction); no new named figures.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS - ruff + ruff format + mypy --strict +
  pytest with `--cov-fail-under=100`; red-green TDD for every new check and placement
  behavior, motivating defects frozen as regression fixtures.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: PASS - opening bookend is
  research.md (14 elements, standing research cited rather than re-derived, new research
  recorded in full with the calibrated-liberty disclosures); closing bookend is an explicit
  final task re-examining the rendered PNG against those findings before "done", separate
  from the automated gate.

No DEFERRED gates; Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/021-capital-housing/
├── plan.md              # This file
├── research.md          # Phase 0 - the XII opening bookend + settled decisions
├── data-model.md        # Phase 1 - manifest keys, knobs, budget bindings
├── quickstart.md        # Phase 1 - the one-map iteration loop for this feature
├── contracts/
│   └── checks.md        # Phase 1 - new/extended gate rules and their scopes
└── tasks.md             # Phase 2 (/speckit-tasks - not created by /speckit-plan)
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── settlement.py        # capital packs, terraces, cistern-wells, precinct interiors,
│                        # wharf fabric, wind knob (all new params legacy-defaulted)
├── check_village.py     # capital-scale extensions of the city battery + new rules
├── citybudget.py        # read-only consumer (targets come from the recorded budget)
├── test_settlement.py   # engine unit tests (red-green)
├── test_checks.py       # check unit tests (red-green)
├── test_villages.py     # pool sweep + GEN_TIME_BUDGETS entry for the capital
├── wip/shiro-daika.gen.py     # grows the 021 layers, then MOVES to:
├── pool/capitals/shiro-daika.gen.py  (+ .json manifest; ship step)
├── pool/regressions/    # new fixtures frozen per defect
├── settlements/capitals.md    # doctrine updates (record-the-why)
└── research/cities/capitals.md  # research additions (durable home of the new findings)
```

**Structure Decision**: existing single-package layout; no new modules. The gen file moves
`wip/ -> pool/capitals/` at ship (its engine-walking header already survives the move).

**Agent-context note**: this project deliberately tracks no "active plan" pointer in
CLAUDE.md (root CLAUDE.md, "Key paths": the highest-numbered `specs/` dir + git log are the
status source). The template's SPECKIT-marker update is intentionally skipped;
`.specify/feature.json` carries the feature directory for downstream commands.
