# Implementation Plan: Review-Loop Efficiency (scatter audit + three process rules)

**Branch**: `108-review-loop-efficiency` (SPECIFY_FEATURE convention - no git branch) | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/108-review-loop-efficiency/spec.md`

## Summary

Convert the scriptable core of a settlement-review DELTA pass (scatter base-point extraction + keep-out adjudication) into `scatter_audit.py`, a diagnostic beside `crop_map.py`/`why_placed.py`/`site_justice.py` that obtains its keep-outs from the engine's own code on the real manifest (observe-don't-restate); and land three measured process rules from the 2026-08-16 profile in the docs sessions actually load (review-launch ordering, open-decision implementation sketches, no redundant pre-gate pool sweep) plus the dated profile block itself.

## Technical Context

**Language/Version**: Python 3.14 (project pin)

**Primary Dependencies**: stdlib only (re, json, argparse, math) + the `settlement` package's own geometry helpers (`boxed_polys`, `boxed_grid`, `boxed_seg_hit`, `boxed_hit`) and unbound engine methods (`Settlement._watercourse_segs`) - deliberately, per observe-don't-restate

**Storage**: reads pool map artifacts (`<map>.json` + `<map>.svg`); writes nothing

**Testing**: pytest (-n auto), 100% coverage on the new module via the skill's `make done` gate; fixtures rendered in-test by the real engine on a tiny canvas + a doctored-SVG loud-failure fixture

**Target Platform**: dev container CLI

**Project Type**: single script + tests inside `.claude/skills/diagram/`

**Performance Goals**: full parse + adjudication of the largest pool map (Inashiro, 16.7 MB SVG, 231k bases) in low single-digit seconds; hard bound SC-001 <30s

**Constraints**: must not re-implement any margin rule; must fail loudly on zero parsed bases; must leave committed pool bytes untouched; docs-only pieces skip the gate

**Scale/Scope**: one ~300-line script + one test file + 3 doc edits + 1 agent-doc edit + 1 research retro-fit edit

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI.
- **II. Bold, Intentional Design**: N/A - no UI surfaces.
- **III. Pool Data Conventions**: N/A - no generated pool content (a diagnostic script and docs).
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks touched.
- **V. Protecting the GM's Writing**: PASS - no task touches SOURCE-marked content.
- **VI. Verify Before Reporting Done**: PASS - per-task verification listed in tasks.md: red-green pytest for the script, `make done` gate for the Python change, script run against current Inashiro (expected clean) and against the seeded-violation fixture (expected to fire) before the agent doc points at it; docs-only tasks verified by reading the rendered sections back.
- **VII. De-Localized Generation**: N/A - no pool content generated.
- **VIII. Direct Voice**: N/A - no in-world prose.
- **IX. Setting Integration**: N/A - no setting content.
- **X. Python Discipline**: PASS - commitments: ruff check + format-check, mypy --strict (module added to `files`), red-green TDD (adjudication tests written against a fixture with known violations BEFORE the adjudicator lands), 100% coverage (module added to coverage `source`; `--omit` gate already enforces non-settlement modules at 100%), no new deps, behavior-named tests, no prints outside the CLI report path (the report IS the product of a CLI diagnostic - printing is its contract, mirroring `site_justice.py`), functions and files well under human-scale bounds.
- **XII. Historical Grounding Bookends**: N/A - the feature changes no generator assertion about the world; it audits renders against rules whose grounding already lives in `research/vegetation.md`. The doc edits record process rules, not world claims.

## Project Structure

### Documentation (this feature)

```text
specs/108-review-loop-efficiency/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0 (R1-R7, all unknowns resolved)
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── scatter-audit-cli.md
└── tasks.md             # /speckit-tasks output
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── scatter_audit.py           # NEW - the diagnostic (parse + adjudicate + report)
├── test_scatter_audit.py      # NEW - 100% coverage, fixture-based
├── pyproject.toml             # EDIT - coverage source + mypy files gain scatter_audit
├── CLAUDE.md                  # EDIT - review-launch rule sharpened; open-decision sketch convention
├── research/vegetation.md     # EDIT - cut-bank open-decision entry retro-fitted as the worked example
docs/iteration-loop.md         # EDIT - dated 2026-08-16 profile block + pre-gate rule
.claude/agents/settlement-review.md  # EDIT - DELTA scatter reviews run scatter_audit.py themselves; catch-rate line
```

**Structure Decision**: single-script diagnostic inside the diagram skill, following the `site_justice.py` exemplar (CLI `main(argv) -> int`, pragma-no-cover `__main__` guard, module in coverage+mypy rosters).

## Phase 1 design highlights (details in data-model.md / contracts/)

- **Parse**: stream the SVG once with anchored regexes for the five families (R2); bases only, tips exempt. Zero total bases -> exit 2 with an ERROR line (FR-004).
- **Adjudicate**: shim object (`M`, `px`, `bscale`) + unbound `Settlement._watercourse_segs(shim, channel_margin=...)` for water+cut-bank; manifest `fields[].poly` + `dry_plots[].poly` + `_CROP_MARGIN_FT` via `boxed_polys`/`boxed_grid` for crops (R3). Marsh-reed family is counted, never adjudicated.
- **Report**: families checked + per-family base counts + violations (x, y, family, owning keep-out) + near-margin density bands (0-15 / 15-30 / 30-45 px beyond the water keep-out) so the sterile-halo judgment stays possible. `--json` for machine reading; human text default.
- **Docs**: exact wording drafted at implement-time against the current files; the pre-gate rule uses R1's verified render model (unconditional - clone pool renders feed nothing).

## Complexity Tracking

None - no constitutional gate is deferred or violated.
