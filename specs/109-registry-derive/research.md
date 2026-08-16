# Research: Derive the check_village Gate Registry (109)

All findings are empirical - two probe scripts in this directory ran the candidate derivations
against every live row. `probe_derivation.py` is the first pass (transform-style analysis,
naive); `probe2_refined.py` is the refined pass that became the design. Run them any time to
reproduce the numbers.

## R1. Census of the consumed surface (clause 14 step 1)

Live consumers of `registry.py`'s exports - the complete list:

| Consumer | Symbols | Obligation |
|---|---|---|
| `check_village/driver.py` | `GATE_SEGMENTS`, `META_CHECKS`, `_SEG_DEPS` (via `from .registry import ...`) | unchanged import, identical values |
| `check_village/__init__.py` | `from .registry import *` (feature 027 star surface -> `GATE_SEGMENTS`, `META_CHECKS`) | star-visible names preserved |
| `test_check_village_surface.py` | expects `GATE_SEGMENTS`, `META_CHECKS` on the package | must pass untouched (FR-003) |
| `test_checks/test_driver_and_fixtures.py:330` | `check_village.GATE_SEGMENTS` (checks census) | identical `checks` fields |
| `test_checks/test_segments_11_polders_and_edges.py:519` | `check_village.META_CHECKS` | identical value |
| `test_regressions.py:56` | `check_village.META_CHECKS` | identical value |

`specs/022/023/024` scripts also reference these names but are frozen one-off tooling that ran
against files that no longer exist in that shape; they are historical artifacts, not consumers
(they already do not run against the post-024 package). `_GateSeg` and `_SEG_DEPS` have no
consumers outside `driver.py` and the registry itself.

## R2. Field derivability (probed, per field, all 1,367 rows)

**Decision**: derive each field from the source listed below; keep three decided facts as
explicit data (R4, R5). **Rationale**: probe2 reproduces every row exactly except the three
decided facts. **Alternatives considered**: whole-row AST re-analysis exactly as feature 022 ran
it (probe 1) - fails on the 3 hand-added segments, which were never produced by the transform;
maintaining the roster (status quo) - 8,432 lines of restated data, the motivating defect.

| Field | Derivation | Probe result |
|---|---|---|
| roster + `fn` | scan `segments_*` modules for `_seg_*` functions | 1,367/1,367 found, no dups |
| `free` | the function's keyword-only parameter tuple, in signature order | **exact for all 1,367** (probe: `sig: 0 mismatches`) - feature 022 GENERATED the signatures from `free`, so the signature IS the roster fact |
| `writes` | the literal tuple in the terminal `return _kept(locals(), (...))` | **exact for all 1,367** (probe: `return-census: 1367/1367 literal _kept returns; writes_mismatch=0`) |
| `checks` | AST census of `check(...)` emissions incl. helper emissions (`_module_emissions` over the package) | exact for all rows |
| `meta` | body loads intersect `{_ran, _waived, fails}` | exact |
| `always` | opaque (unresolvable) check emission present | exact |
| `needs` | upward-exposed reads over the whole body, threaded across statements, + mutation targets + `via_helpers` (R3), intersected with the signature | exact for 1,366; ONE override (R5) |
| `META_CHECKS` | union of `checks` over rows with `meta=True` | exact |
| `_SEG_DEPS` | computed from `needs` x `writes` exactly as today | unchanged code |

## R3. The via_helpers fixpoint is load-bearing for `needs`

Probe 1 (no helper modeling) missed `_wtr` on `_seg_0099`/`_seg_0100`: `_wtr_add` is a gate-local
closure defined in an earlier segment that appends into `_wtr`, so a segment CALLING it must
count as toucher of `_wtr` (feature 022 found this the hard way in its targeted-vs-full sweep -
the silent-pass failure mode). The derivation MUST port the transform's `helper_mut` fixpoint:
nested `FunctionDef`s bound to gate-local names, their mutation targets, closed over helpers
calling helpers. With it (probe 2), those rows match exactly. Intersecting `needs` with the
signature also makes hand-added new-style segments (function-local temps, e.g. `_seg_0596`)
derive exactly - their temps are not parameters, so shared names with other segments' gate
locals can no longer leak in.

## R4. Order is derivable EXCEPT two placement decisions

Sorting by the numeric name key (`_seg_NNNN` / `_seg_NNNN_NNN`, sub-number -1 when absent)
reproduces the registry order for 1,365 of 1,367 rows. The two exceptions are hand-added
segments numbered PAST the legacy range but registered mid-sequence:

- `_seg_0595__paddy_bunds_clear_the_supply_channels` - runs before `_seg_0533___flow_dir`
- `_seg_0596__dry_plot_seams_shared` - runs between 0317 and 0318 (its own docstring records this)

Their execution position is a real DECISION (clause 14: "keep the decided ones"), kept as a
2-entry `PLACEMENTS` table (segment name -> anchor it runs immediately after), each entry with a
recorded why. Probe 2 verifies key-sort + placements reproduces the registry order exactly.
`_seg_0324_500` shows the OTHER insertion convention - sub-numbering encodes position in the
name - which the key sort handles with no table entry. Future insertions may use either;
sub-numbering is preferred (self-describing), the table is the fallback when a name is already
committed.

## R5. One needs override: `_seg_0324_500__comb_supply_commands_both_flanks`

The hand-written row states `needs=('M','check','meta')`; the analysis derives a superset adding
`_csf_bad`, `_csf_ext`, `_csf_reach` (loop-carried reads of names the body itself initializes -
the analysis is conservative about loops; a legacy row of this shape would have CARRIED the
superset, but the human author wrote the tighter truth). The row's value is a hand-decided fact:
kept as a 1-entry `NEEDS_OVERRIDES` table with the why inline. Verified behaviorally inert
today: the `_csf_*` names are written only by this segment itself, so the dependency set is
identical (`[]`) under either value.

## R6. Import-time cost -> cache, per the feature 026 precedent

Measured: the AST analysis over the whole package costs ~1.3-1.4 s (probe 2: `analyze_s=1.407`),
on top of the current ~1.3 s package import. Uncached, that is ~9% on a ~15 s scripted-map loop -
over the GM's 5% whole-process threshold, so it must not be paid on every import.

**Decision**: derive once, cache the derived rows keyed by a hash of the segment sources; on
import, a key match loads rows from the cache (JSON of names + fields, functions re-bound by
name), a miss re-derives and atomically rewrites the cache. Failure-soft: unreadable/stale cache
falls back to live derivation. This is the established gencache pattern (feature 026: the gate
rides a spec-keyed cache with atomic publish); the cache file is gitignored. **Alternatives
considered**: build-step generation with a committed generated file - keeps 7k generated lines in
the repo and reintroduces a stale-artifact failure mode the hash-keyed cache does not have;
accepting the 1.3 s - violates the 5% threshold; bytecode-only derivation (no AST) - `needs`,
`checks`, and `via_helpers` genuinely require the AST, and parsing is the bulk of the cost anyway.

## R7. Guard tests and the fixture (clause 14 step 2)

- **Transition oracle**: freeze all 1,367 rows (name + six fields) + `META_CHECKS` as a JSON
  fixture generated from the CURRENT registry before replacement. The equality test compares
  derived rows to fixture rows BY NAME and asserts the fixture order is a subsequence of the
  derived order - so future segment additions extend the registry without invalidating the
  frozen legacy oracle.
- **Permanent structural guards** (fail loudly on future drift): every `_seg_*` function ends in
  a literal `_kept` return (a future non-conforming segment fails at derive time, not silently);
  no duplicate names/keys; placement anchors exist; derived order is strictly increasing by key
  after placement splice; `needs subset-of free`; every override/placement entry names a live
  segment (a stale entry fails - same liveness doctrine as `waivers_are_live`).
- **Proven to fire** (FR-004): each guard and the fixture equality test gets a deliberate
  perturbation run (swap two placements, drop a needs name, flip a meta bit, delete a segment
  from the derived dict) recorded in tasks.md as red-then-green evidence.

## R8. Principle XII (Historical Grounding Bookends): N/A

This feature changes no generator assertion about the world - it re-plumbs how the validator's
segment metadata is stored. No map output, no check semantics, no thresholds change; SC-002
(identical gate results on the regression corpus) is the proof. Both bookends are therefore N/A.

## R9. Consequences for the 022-024 tooling docs

`specs/022-gate-check-registry/transform_gate.py` remains the provenance of the analysis scheme
and is not modified. The ported analysis lives in the package (typed, tested); the port must
cite the transform per FR-006. The package `CLAUDE.md` registry entry and the clause-13
justification header both describe the old file and are updated by this feature (FR-007). The
constitution's clause 13 text names "a registry whose row order is the execution contract" as
the carve-out example in the abstract - it does not name this file, so no constitution edit is
needed; CLAUDE.md's operational mirror likewise names only the 027 exemplar.

## R10. Outcome (implementation, 2026-08-16)

Post-merge corpus: **1,371 rows** (0597/0598/0599/0600 arrived from a peer session mid-feature;
`probe3_final.py` re-proved derivability and auto-discovered the placement set). Shipped:
`registry.py` 8,432 -> ~200 lines + `registry_analysis.py` ~300 lines (both 100% covered,
mypy --strict); `_PLACEMENTS` = 6 entries (0596 after 0317; 0595 after 0532 with 0600, 0597,
0599, 0598 chained after it), `_NEEDS_OVERRIDES` = 1 entry (0324_500). Fixture equality green
across all 1,371 rows. Import timing (FR-009): cold (derive + cache store) 1.84 s; warm (cache
hit) **0.415 s - faster than the old 8,432-line file's ~1.3 s import**, so the steady state is a
net speedup, not a budgeted cost. One workflow subtlety found by the T009 dry-run and written
into the package CLAUDE.md: sub-numbering places relative to the BASE key order, so a segment
meant to run beside a PLACED segment needs its own `_PLACEMENTS` entry.
