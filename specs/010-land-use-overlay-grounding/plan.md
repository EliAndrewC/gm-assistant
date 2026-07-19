# Implementation Plan: Land-Use Overlay Historical Grounding

**Branch**: none (worked on `main`; the GM declined the feature-branch hook) | **Date**: 2026-07-19 | **Spec**: [spec.md](spec.md)

## Summary

Two corrections to the `/diagram` Mode B `land_use_overlay` knob, plus the documentation that keeps them
from being undone. Drop `mulberry_fishpond` from the overlay value space (the dike-pond system is a
landscape-scale conversion and is already correctly modeled as the `mulberry_dike_fishpond` FIELD
ARCHETYPE), and bind `lotus` to the plots the field builders already mark `FLOODED` (the low, wettest
ground on the drain) instead of `rng.sample` over all plots. `tea_fringe` is already topography-driven
and is left alone. This is the first feature run under Constitution Principle XII, so it opens with
`research.md` and closes with an artifact inspection.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: none (stdlib only); `rsvg-convert` for PNG render
**Storage**: `pool/*.json` manifests + `pool/*.svg`/`*.png` artifacts
**Testing**: pytest + pytest-cov, `fail_under = 100` in `.claude/skills/diagram/pyproject.toml`
**Target Platform**: Linux container
**Project Type**: generator library + validator gate (single package)
**Constraints**: every pool map must keep passing `check_village`; 100% line coverage; deterministic output
**Scale/Scope**: ~3 functions in `settlement.py`, 1 check in `check_village.py`, 4 pool maps regenerated

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no webapp UI; this is generator output, whose visual gate is
  Principle XII's closing bookend plus the skill's own read-the-PNG rule.
- **II. Bold, Intentional Design**: N/A - no new UI surface.
- **III. Pool Data Conventions**: N/A - no new pool content of a recurring kind; existing `pool/*.gen.py`
  maps are regenerated in place, not added to.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks touched.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS - no task modifies anything inside SOURCE markers.
- **VI. Verify Before Reporting Done**: PASS - every task ends in `python3 -m pytest` at 100%, the
  `check_village` gate on all regenerated maps, and (for the drawing tasks) reading the rendered PNG.
- **VII. De-Localized Generation by Default**: N/A - no new pool content.
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose written.
- **IX. Setting Integration**: PASS - grounding is drawn from the China-first agricultural research already
  cited in `settlements.md`; no new named figures or places, so no campaign-name collisions.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS - plan commits to `ruff check`, `ruff format --check`,
  `mypy --strict`, red-green TDD (the new `lotus_on_wet_ground_only` check gets a failing negative fixture
  BEFORE the placement change lands), `pytest --cov-fail-under=100`, no swallowed exceptions, no `print`
  in production paths, behavior-named tests.
- **XI. Japanese Authenticity**: PASS - the surviving overlay names carry existing kanji (藕田 lotus,
  茶 tea); the dropped one (桑基魚塘) keeps its kanji where it correctly lives, on the archetype.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: PASS - this feature exists BECAUSE of the
  bookends, and commits to both:
  - **Opening**: `research.md` (Phase 0) states, for lotus, the dike-pond system, and tea, what the
    historical reality was (China-first, Japan corroborating), whether the current design matches it, and
    what DETERMINES each in reality. The research is done by independent web research, not asserted from
    memory. The rejected designs (`rape`, `mulberry_fishpond`-as-overlay) have their grounding recorded too.
  - **Closing**: the final phase re-renders a lotus map and a dike-pond map and inspects the PNGs - not
    the manifests and not the code - confirming lotus sits only on wet bottom ground and the dike-pond
    landscape reads as a whole converted district.

No DEFERRED gates; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/010-land-use-overlay-grounding/
├── plan.md              # this file
├── research.md          # Phase 0 - the OPENING BOOKEND
├── data-model.md        # Phase 1 - the knob value space + plot record
├── quickstart.md        # Phase 1 - how to verify by hand
├── checklists/
│   └── requirements.md  # spec quality checklist (complete)
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code

```text
.claude/skills/diagram/
├── settlement.py          # land_use_overlay knob registration; apply_land_use()
├── waterfields.py         # FLOODED marking on comb / terrace / polder / ribbon plots
├── check_village.py       # land_use_overlay_drawn; NEW lotus_on_wet_ground_only
├── settlements.md         # historical grounding prose (per-value why, incl. rejections)
├── test_checks.py         # negative fixtures for the gate
├── test_settlement.py     # unit tests for apply_land_use branches
└── pool/
    ├── kikuta-village.gen.py / .json / .svg / .png   # rolls mulberry_fishpond -> re-rolls
    ├── kuwabata.gen.py      / ...                    # archetype AND overlay - overlay drops
    ├── rolled-a.gen.py      / ...                    # rolls lotus - placement changes
    └── rolled-b.gen.py      / ...                    # rolls mulberry_fishpond -> re-rolls
```

**Structure Decision**: single existing package, no new modules. The change is surgical: one knob value
space, one placement rule, one new check, four regenerated maps.

## Phase 0 - Opening Bookend (research.md)

Independent research into (1) where lotus was actually grown and what determined it, (2) whether a
scatter of mulberry-dike fishponds among rice ever existed, (3) what sites tea. Each finding states
explicitly whether the CURRENT design matches, and the mismatches are resolved here rather than
implemented and revisited. Also confirms the load-bearing assumption that the engine's `FLOODED` fill is
a sound proxy for "low, permanently wet ground" in all four field builders.

## Phase 1 - Design

`data-model.md`: the `land_use_overlay` value space before/after, the plot record (`poly`, `fill`) and
which builders set `FLOODED`, and the contract that `apply_land_use` returns a count that may now
legitimately be smaller than `fraction * len(plots)` (or zero).

`quickstart.md`: the by-hand verification recipe - pin the overlay, regenerate, grep the manifest for
lotus plots not on wet ground, read the PNG.

## Phase 2 - Implementation (sequenced by /speckit-tasks)

**Revised after Phase 0.** `mulberry_fishpond` is NOT dropped (research.md D2); both plot-based overlays
get the topographic filter instead.

1. Red: negative fixture asserting `overlays_on_wet_ground_only` FIRES on a manifest with an overlay plot
   off the wet ground. Confirm it fails against the current (random-sample) generator output.
2. Green: record wet-plot centroids in the manifest from the field-drawing pass, and overlaid-plot
   centroids from `apply_land_use`, so the check compares independent sources.
3. Filter both plot-based overlays to `FLOODED` plots; `fraction` becomes a share of the eligible set;
   zero eligible plots means "draw nothing, count 0".
4. Cluster the dike-pond overlay (grow patches from seed plots) rather than sampling evenly; add
   `dikeponds_are_clustered` with a negative fixture.
5. Drop the redundant overlay from the map that already uses the dike-pond ARCHETYPE (Kuwabata).
6. Relax `land_use_overlay_drawn` so a legitimately small count is not a failure, without letting a silent
   no-op through.
7. Regenerate the four affected maps; re-run the gate.
8. Record the per-value grounding (all three rejections + the corrected tea-siting language) in
   `settlements.md` and the docstring.
9. Full gate: ruff, format, mypy --strict, pytest at 100%.

## Phase 3 - Closing Bookend

Re-read the rendered PNGs of a lotus map and the dike-pond archetype map and confirm each still matches
the Phase 0 findings. This is separate from `check_village`, which proves internal consistency and never
historical truth.

## Complexity Tracking

None - no constitution gate was violated or deferred.
