# Implementation Plan: the `land/` package

**Feature**: 120-land-package | **Spec**: [spec.md](spec.md) | **Date**: 2026-08-17

**Baseline commit**: `56f6dfb` (re-taken after a mid-feature sync-in moved main - see research.md R8)

## Summary

Split `settlement/land.py` (1,187 raw lines) into `settlement/land/`, four subject modules plus a
composing `__init__.py` and a `CLAUDE.md` index, and relocate three farmstead helpers to
`settlement/homestead_parts.py`. Pure code motion, verified by byte-identity over all 893 pool
artifacts. This is the eighth and last file in `settlement/` to be split; the practice, the
transformer lineage and the verification method all come from features 025 and 112-118.

## Technical Context

| | |
|---|---|
| Language | Python 3.14 |
| Touched | `settlement/land.py` -> `settlement/land/{__init__,dikes,wet,cover,nearring}.py` + `CLAUDE.md`; `settlement/homestead_parts.py`; `settlement/CLAUDE.md`; `settlement/civic_grounds/CLAUDE.md`; `tests/settlement/test_land.py` |
| Untouched | `settlement/core.py`, `settlement/__init__.py`, every consumer outside `settlement/` |
| Oracle | `sha256` of every `pool/**/*.{json,svg,png}` before and after - empty diff |
| Tooling | `ruff check`, `ruff format --check`, `mypy --strict`, `pytest -n auto`, `make done` |
| Transformer | [`split_land.py`](split_land.py) - one-shot, retired after use, kept for the lineage |

## Constitution Check

*GATE: passed before Phase 0 research; re-checked after Phase 1 design.*

- **I. Accessibility-First Viewports**: **N/A** - no UI. This feature ships no HTML, CSS or template
  change; the L7R Toolkit is untouched.
- **II. Bold, Intentional Design**: **N/A** - no new UI surface.
- **III. Pool Data Conventions**: **N/A** - no generated content of a recurring kind is added or
  modified. The pool is READ (as the verification oracle) and must come out byte-identical.
- **IV. One Canonical Home for GM Source**: **N/A** - no SOURCE blocks are added or moved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - no task touches content inside
  SOURCE markers, and nothing in `/host-l7r-repo` is read or written.
- **VI. Verify Before Reporting Done**: **PASS** - every task carries its verification step; see
  [quickstart.md](quickstart.md) for the runnable form. The headline verifications are the
  byte-identity sweep, the four sabotage-proven surface guards, and a green `make done`.
- **VII. De-Localized Generation by Default**: **N/A** - no pool content generated.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - no in-world content written.
- **IX. Setting Integration**: **N/A** - no setting details invented, no named figures added. The
  historical grounding already recorded in the moved comments (wei-tian dike construction, the
  alluvial-fan spring line, the von Thuenen intensity gradient) travels verbatim and is measured for
  conservation (research.md R6).
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS**, and it is the whole point of the feature.
  - clause 13 (files): the motivation. 1,187 -> four modules of 271/224/397/370 lines, and
    `homestead_parts.py` at 786. No file this feature touches is over 1,000.
  - clause 12 (functions): **already satisfied and deliberately not acted on** - measured in logic
    units, the worst member is 126 statements against a "suspect" line of a few hundred. Decomposing
    a body here would act against the clause, which explicitly rejects the 10-line-function dogma.
    Measurements in research.md R2.
  - clause 14 (derived rosters): **N/A** - there is no roster here. `land/__init__.py`'s four
    imports are each USED (in the class bases), unlike `_geom/__init__.py`'s star re-export surface,
    so no `pyproject.toml` per-file ignore is needed and nothing is derived.
  - `ruff check` + `ruff format --check` + `mypy --strict` + `pytest` + coverage: all run in
    `make done`.
  - **Red-green TDD for new behavior**: there is no new behavior, so the TDD obligation attaches to
    the only new logic - the four surface guards. Each was proven to FAIL on a synthetic sabotage
    before being trusted (contracts/surface.md records the sabotage and the observed failure for
    each). A guard that has never been seen to fire is not a guard.
- **XI. Japanese Authenticity**: **N/A** - no new Japanese script. Existing kanji in moved comments
  (圩田, 挖塘培基, 鱼鳞圩, 扇端の湧水帯) travels verbatim and unedited.
- **XII. Historical Grounding Bookends**: **N/A for new research** - this feature adds no rule and
  therefore owes no new grounding. It does owe PRESERVATION of the grounding already written down,
  which is why comment-line conservation is a measured FR (FR-009) rather than an assumption.
- **XIII. No Known Regressions (NON-NEGOTIABLE)**: **PASS** - baseline measured on unmodified code
  at `56f6dfb`, gate green, 893 artifacts hashed. Taken in a scratch copy and the clone, never by
  stashing. The post-change comparison must show an empty hash diff and no gate failure absent from
  the baseline; anything else means fix, revert, or an explicit GM waiver, with the work staying
  unpushed.

**No entry is DEFERRED. No Complexity Tracking entry is required.**

## Project Structure

```
settlement/
  land/                     <- NEW
    __init__.py             composes LandMixin from the four sub-mixins; re-exports surface_water_dist
    CLAUDE.md               the "look here when" index
    dikes.py       DikeMixin        perimeter_dike, dike_top_houses
    wet.py         WetGroundMixin   marsh, trim_off_marsh, toe_band + module-level surface_water_dist
    cover.py       GroundCoverMixin commons, hinterland, _clear_ground, reserve_clearing
    nearring.py    NearRingMixin    near_ring_cropland, near_ring_paddy
  homestead_parts.py        <- +3 relocated members, +1 import name
  land.py                   <- DELETED
```

## Phases

**Phase 0 - research** ([research.md](research.md)). Settle the partition axis (residue bucket, not
chain), measure clause 12, census the relocation candidates' callees, decide `surface_water_dist`'s
home, enumerate the transformer's novel hazards, fix the verification strategy.

**Phase 1 - design** ([data-model.md](data-model.md), [contracts/surface.md](contracts/surface.md)).
The partition member by member with measured spans, the "what does NOT change" table, the composed
surface diagram, and the four-part surface contract.

**Phase 2 - execution** ([quickstart.md](quickstart.md), [tasks.md](tasks.md)). Baseline, transform,
prune, prove the guards fire, sweep, gate, document, ship.

## Sequencing and its one hard constraint

The order is nearly linear, and the single ordering rule that matters is: **the baseline is captured
before any edit, at the commit the work will build on.** Everything else is a consequence of it.
This bit once in this session (see research.md R8): a peer session pushed an engine change to main
mid-feature, and the sync-in that pulled it invalidated a baseline already taken. Re-taking it cost
one gate cycle; building on it silently would have cost the feature's whole safety argument.

## Risks

| risk | mitigation | residual |
|---|---|---|
| a member is dropped or duplicated | transformer refuses on an inexact partition; C1/C2 guards, both proven to fire | none known |
| the module-level tail is dropped | transformer refuses if the tail lacks `surface_water_dist`; C4 guard proven to fire | none known |
| a comment bank is lost in the slice | slice from the previous member's end; comment lines counted (158 = 158) | none known |
| a stale `.pyc` shadows the new package | `__pycache__` cleared as part of the transform step | none known |
| the gencache does not see the new submodules, so a green sweep proves nothing | sweep run with `--no-cache` (28 REGENERATED, 0 CACHED); plus an explicit invalidation probe after the gate | none known |
| main moves under the clone again | re-sync and re-verify before the stop-work ritual | low - handled once already |

## Complexity Tracking

None. No constitutional gate is deferred or violated.
