# Implementation Plan: Human-Scale Splits (settlement.py + the two big test files)

**Branch**: `025-human-scale-splits` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/025-human-scale-splits/spec.md`

## Summary

Apply constitution clause 13 to the diagram skill's three remaining oversized files - and first
amend the clause (plus its mirrors) to state explicitly that test files are covered. Four stories,
landed and gate-verified separately:

1. **US1 - docs**: clause 13 says tests are covered, with the why (context-window tokens; a test
   file is loaded under the same conditions as source). PATCH bump 1.6.0 -> 1.6.1; mirrors in root
   `CLAUDE.md` and the plan template updated.
2. **US2 - test_checks.py (11,475 lines)** -> `test_checks/` directory of per-segment test
   modules mirroring `check_village/`'s file layout, shared fixture builders in `conftest.py`,
   collection-identity proof.
3. **US3 - settlement.py (16,016 lines)** -> `settlement/` package. The file is one giant class
   (`Settlement`: 338 methods, lines 2032-16016) plus ~2,000 lines of module-level helpers, so the
   split shape is **mixin modules** (methods grouped by subsystem, `self: "Settlement"`
   annotations, TYPE_CHECKING back-import) composed into the final class in `core.py`, with the
   helpers split into geometry and knob-engine modules. Byte-identity proof over every
   regen-runnable pool gen + gate-verdict identity + package CLAUDE.md index.
4. **US4 - test_settlement.py (7,123 lines)** -> `test_settlement/` mirroring the final
   `settlement/` layout, same collection-identity proof.

Out of scope: `check_village/registry.py` (ordered-data exemption; separate future effort, GM
2026-08-16).

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: stdlib-only engine (settlement.py has no third-party imports); pytest +
pytest-cov + pytest-xdist for tests; ruff + mypy for the gate

**Storage**: files - SVG/PNG/JSON map artifacts in `pool/`, JSON manifests, spec artifacts

**Testing**: pytest via `make done` in `.claude/skills/diagram/` (lint + format + mypy --strict +
tests; coverage 100% on all measured modules EXCEPT settlement.py, which holds a 94% ratchet floor
per the 2026-08-16 legacy freeze - see Makefile `SETTLEMENT_COV_FLOOR`)

**Target Platform**: Linux container, CLI

**Project Type**: single project (skill-internal refactor + governance doc amendment)

**Performance Goals**: no regression in gate wall-time or regen wall-time (~15 s/map scripted);
identity sweeps are one-off feature tooling

**Constraints**: pure moves only - byte-identical generated artifacts, identical gate verdicts,
identical pytest collection; `import settlement` and every current caller keeps working;
mypy --strict stays green (settlement.py is fully strict today - no ratchet left to hide behind)

**Scale/Scope**: 34,614 lines across the three files; 338 methods to regroup; ~45 importers of
`settlement` (tests, check_village segments, tools, pool gens, wip gens)

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI introduced or modified (webapp untouched).
- **II. Bold, Intentional Design**: N/A - no new UI surfaces.
- **III. Pool Data Conventions**: N/A - no generated content added or modified; pool artifacts
  are proof fixtures here, byte-identical by requirement.
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks added or moved.
- **V. Protecting the GM's Writing**: PASS - no task touches SOURCE-marker content; the l7r.md
  canonical is untouched.
- **VI. Verify Before Reporting Done**: PASS - each story's verification is explicit: US1 grep
  the three mirror sites; US2/US4 collected-node-list diff + full `make done`; US3 byte-identity
  sweep over regen-runnable gens + gate-verdict identity + full `make done`. Delegated review:
  none required (no map pixels change; settlement-review is for map content, not refactors).
- **VII. De-Localized Generation by Default**: N/A - no content generation.
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose.
- **IX. Setting Integration**: N/A - no setting details created; nothing to collide.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS - this feature IS a clause-13 enforcement
  action. Commitments: `make done` green after every story (ruff check, ruff format --check,
  mypy --strict on the unchanged `files` surface renamed to the package, pytest, 100% coverage on
  all measured modules except the settlement package which keeps its 94 ratchet floor); no new
  behavior means no new red-green TDD obligation - the identity proofs are this feature's tests;
  no function bodies change (clause 12 dispositions from 024 R9 carry over untouched); every new
  file lands under ~2,500 lines except `settlement/__init__.py`-style re-export files which are
  trivially small. TDD exception per 024 precedent: pure-move refactor verified by identity
  oracles, not new failing tests.
- **XII. Historical Grounding Bookends**: N/A - the feature changes NOTHING a generator asserts
  about the world: outputs are proven byte-identical, so no element is added, changed, or drawn
  differently. (Both bookends would compare an artifact to itself.)

**Gate result**: PASS - no DEFERRED entries, Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/025-human-scale-splits/
├── plan.md              # This file
├── research.md          # Phase 0 - all design decisions (R1-R12)
├── data-model.md        # Phase 1 - module boundary map, proof artifacts
├── quickstart.md        # Phase 1 - how to run the proofs and the gate
├── contracts/
│   └── import-surface.md  # the preserved-API contract + how it is generated/verified
└── tasks.md             # Phase 2 output (/speckit-tasks - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
.specify/memory/constitution.md          # US1: clause 13 amended, v1.6.1
.specify/templates/plan-template.md      # US1: Principle X mirror sentence
CLAUDE.md                                # US1: "Files stay at human scale" bullet mirror

.claude/skills/diagram/
├── settlement/                          # US3: was settlement.py (16,016 lines)
│   ├── CLAUDE.md                        # "look here when" index (check_village/CLAUDE.md is the exemplar)
│   ├── __init__.py                      # full legacy re-export surface (ruff F401 per-file-ignore)
│   ├── _geom.py                         # module-level geometry/spatial helpers (was lines ~1-1300)
│   ├── _knobs.py                        # knob engine + roll helpers (was lines ~1310-2031)
│   ├── core.py                          # class Settlement(<mixins>): class attrs + __init__ + record/meta/rng/view
│   ├── fields.py                        # paddy/comb/land-use/pond mixin
│   ├── water.py                         # streams/channels/clips/moat-flow mixin
│   ├── ways.py                          # lanes/streets/kido/wards/quarters/alleys mixin
│   ├── shrines_wells.py                 # hill/shrine/torii/wells/tree-stands mixin
│   ├── structures.py                    # manor/estates/building/packing/civic mixin
│   ├── trades.py                        # brewery..tanning/kiln/forge mixin
│   ├── homesteads.py                    # yards/gardens/groves/bundles/farmsteads mixin
│   ├── land.py                          # dikes/commons/marsh/hinterland/near-ring mixin
│   ├── funerary.py                      # cemetery/mausoleum/execution/boundary mixin
│   ├── city.py                          # ring-road/wall/moat/canal/quay/bridges/castle/ministry mixin
│   ├── rolling.py                       # roll_village/seeds/cluster/water-source mixin
│   └── labels_finish.py                 # labels/title/finish/render_png mixin
│   # (exact file set and cut points are settled by data-model.md's boundary map; target
│   #  <=~2,500 lines/file; names final at implement time, index kept true)
├── test_checks/                         # US2: was test_checks.py (11,475 lines)
│   ├── CLAUDE.md                        # index: module <-> check_village file map
│   ├── conftest.py                      # shared fixture builders (f, bldg, manifest, house, yard, garden, well, grove, vgrove, ...)
│   ├── test_common_geometry.py          # tests for common_01/02/03 helpers
│   ├── test_segments_01_city_frame_and_yards.py
│   ├── ...                              # one module per check_village segments_* file
│   └── test_driver_and_fixtures.py      # gate driver, fixture-builder survival, cross-cutting tests
└── test_settlement/                     # US4: was test_settlement.py (7,123 lines)
    ├── CLAUDE.md
    ├── conftest.py
    └── test_<module>.py                 # one per settlement/ subsystem module

# Split-sensitive infrastructure updated in US3:
.claude/skills/diagram/Makefile          # coverage patterns */settlement.py -> settlement package; floor comment
.claude/skills/diagram/pyproject.toml    # mypy files + ruff per-file-ignores + coverage source/omit
.claude/skills/diagram/render_cache.py   # engine_fingerprint walks the settlement/ package (see research R6)
```

**Structure Decision**: single-project skill-internal refactor; all new directories live inside
`.claude/skills/diagram/`. Test splits use directory-per-old-file (`test_checks/`,
`test_settlement/`) so pytest collection stays rooted in the skill dir and the CLAUDE.md-index
pattern applies to tests exactly as to source.

## Complexity Tracking

No constitutional violations to justify - table intentionally empty.
