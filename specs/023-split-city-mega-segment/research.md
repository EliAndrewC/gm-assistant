# Research: Split the City Mega-Segment (023)

**Date**: 2026-08-15. All numbers measured on this container (22 cpus, python 3.14), clone at
main tip (`0ffb827`). Everything below was measured by AST census, not assumed.

## R1. What the mega-segment actually is (census)

- `_seg_0563__city_has_six_ministries`: 3,607 raw lines (of which ~620 are the keyword-param
  signature and ~590 the `_kept` return tuple), **1,040 logical statements**, registry row
  declares free=621, writes=587, needs=77, checks=148, `meta=False`, `always=False`.
- Its body is exactly three statements: the docstring, ONE `if scale in ('city', 'capital'):`
  statement (lines 21256-23645), and the generated `return _kept(...)`. This is WHY 022's
  statement-granularity split could not divide it: 022 segmented gate() at top-level statements,
  and this whole battery was one top-level statement.
- The if-body has **83 top-level statements** (median 1 logical statement, p90 6). One of them
  is itself a **795-statement `if meta.get('walled'):`** block (line 21899) containing **295
  top-level statements** (median 1, p90 6, max 51). No `orelse` on either guard.
- Largest leaf statements after both guards are unwrapped: 51, 48, 41, 34 statements - all far
  under the clause-12 line and under the spec's 400-statement bar (FR-002).
- **27 nested helper defs** live inside (e.g. `_egap`, `med_nn`, `inwall`, `crosses_ring`,
  `moat_fed`, `seg_seg_dist`) - each needs the 022 stale-cell hazard census at the NEW
  granularity: a helper defined in one sub-segment and called from a later one, with a free
  name rebound in between, would freeze a stale cell.
- 32 of the 83+295 statements carry literal `check()` calls (many emit several names - 148
  total); the rest are shared derivations, exactly the provider-segment shape the registry
  already models (a row with `writes` and no `checks`).

## R2. Split strategy

**Decision**: recurse the 022 recipe exactly one guard level deeper, per top-level statement,
bodies verbatim:

- Each of the 82 non-walled outer statements becomes a segment whose body is
  `if scale in ('city', 'capital'):` + the statement verbatim (dedented one level).
- Each of the 295 walled statements becomes a segment whose body is
  `if scale in ('city', 'capital') and meta.get('walled'):` + the statement verbatim.
- The transformer replaces the mega-function's text with the ~378 new defs at the same file
  position (order = original textual order) and replaces registry row 563 with the ~378 new
  `_GateSeg` rows at the same registry position, preserving overall execution order by
  construction (spec FR-007). Segment names: `_seg_0563_NNN__<slug>` (NNN = 000-377 in order),
  keeping grep-order stable and all names unique.

**Rationale**: identical to 022's R2 - bodies that move without rewriting are the only safe way
to relocate thousands of lines; per-statement granularity is what the registry already is
everywhere else in the file (604 gate statements -> 586 segments); and the guard-wrapping keeps
each body a statement-for-statement copy of what the legacy control flow executed. Names bound
only under a false guard simply never enter `locals()`, so `_kept` merges nothing - byte-for-
byte the semantics the mega-segment's own internal branching had on non-city scales.

**Alternatives considered**:
- *Hand-curated ~30 semantic clusters (one per check family)*: nicer names, but boundaries are
  judgment calls over 3,600 lines of load-bearing code, and every boundary is a chance to
  separate a computation from the guard that made it safe. Rejected: the registry's dependency
  closure already assembles exactly the right provider set per check at run time, which is what
  clustering would try to precompute by hand.
- *Split only the walled block, keep the outer 83 as one segment*: leaves a ~250-statement
  function carrying 100+ checks - legal under clause 12 but fails the feature's point (targeted
  narrowing) for the commonest city checks. Rejected.
- *Hoist the guards into the driver (run segments conditionally on scale)*: changes the registry
  contract (`_GateSeg` has no guard field) and the driver for one region's benefit. Rejected -
  guard-in-body keeps the registry model uniform.

## R3. Guard re-evaluation semantics

The legacy code evaluates `scale in ('city', 'capital')` once and `meta.get('walled')` once;
the split evaluates them once per segment. This is sound iff neither `scale` nor `meta` is
rebound or mutated anywhere in the mega-segment's body. **Census result: they are not** - but
the transformer HARD-FAILS (022 census style) if that ever stops holding, rather than trusting
this document. `meta.get` on an unmutated dict is a pure read; no fallback provider variable is
needed. (If the hard-fail ever fires, the fallback design is a hoisted
`_g563_walled = bool(meta.get('walled'))` provider segment evaluated at the original guard
position - recorded here so the decision is not re-derived.)

## R4. Dataflow derivation (free / writes / checks / needs)

**Decision**: import and reuse 022's analysis functions from
`specs/022-gate-check-registry/transform_gate.py` (`_stores`, `_walk_shallow`, `_loads`,
`_bound_anywhere`, `_mutation_targets`, `_free_loads`, `_exposed_reads`, `_bases_of`,
`_module_emissions`, `_check_names`) - the code that already survived the three documented
dataflow holes (R9 of 022: helper-closure mutation, upward-exposed reads vs raw loads,
comprehension-target scoping). Per new segment, computed against the wrapped (guarded) body:

- **Vocabulary**: the gate-local name universe for the sub-split is (mega free params) ∪ (mega
  writes) = 621 ∪ 587 names, plus `scale`/`meta`/`check` (already in free). Loads outside this
  set are module globals/builtins and MUST NOT become parameters (they would shadow real
  globals with `_UNBOUND` poison - 022's rule verbatim).
- **Helper-mutation fixpoint**: rebuilt over the 27 nested defs (helper mutating a list it never
  names -> every caller counts as a writer), including helpers calling helpers.
- **needs** = upward-exposed reads of the guarded body (guard names included - every segment
  reads `scale`, walled ones also `meta`), intersected with free - same formula as 022.
- **Hard-fail census within the region**: early `return` (other than the mega's final
  `return _kept`, which the transformer strips and regenerates per segment), `global` /
  `nonlocal`, `del` of a gate local, `scale`/`meta` rebinding or mutation (R3), and the
  stale-cell rule: a nested def whose free names are rebound by a LATER sub-segment before a
  later reference. Lambdas that freeze names get the 022 WARN + manual verification treatment.

## R5. The oracle (how we know nothing moved)

Reuse `specs/022-gate-check-registry/oracle_sweep.py` unchanged - it imports `check_village`
from the skill dir and needs no modification:

1. **Baseline capture BEFORE the transform** (`oracle_sweep.py capture`): all 791 regression
   fixtures + all pool manifests, verbose stdout sha256 + sorted verdicts. This is the red bar:
   the transform is correct only if `compare` then diffs to zero. (Do NOT reuse a stale 022
   baseline - main has moved since; capture fresh at the current tip.)
2. **`compare` after the transform**: full-mode byte identity (spec FR-003 / SC-002).
3. **`targeted` after the transform**: targeted-vs-full identity over every fixture's `fires` -
   the empirical guard on every new `needs`/`writes` edge (spec FR-004; diagram CLAUDE.md:
   "Never trust a dependency edge you have not swept").
4. **Teeth check**: temporarily invert 2 checks that now live in NEW segments (one outer-guard,
   one walled-guard); their fixtures must go red in targeted mode; revert. Proves the replay
   still bites through the new rows.
5. Whole affected test files (`test_checks.py`, `test_regressions.py` at minimum - never a
   `-k` subset), then `make done` in the skill dir, backgrounded, acted on at notification.

## R6. Performance model

- **Expected win**: any targeted run wanting one city check currently executes all 1,040
  statements; post-split it executes that check's closure only. The 210 frozen whole-city
  fixtures dominate replay time, so replay should get faster or stay flat; the ~10% regression
  bound (spec FR-008) is the guard against surprise, not the goal.
- **Known cost to measure**: `_SEG_DEPS` is built at import time by an O(n^2) scan
  (586 rows -> ~343k pair tests today; ~960 rows -> ~920k). Measure import time before/after
  (`python3 -c "import time,sys; t=time.perf_counter(); import check_village; ..."`);
  if it regresses noticeably, the fallback (recorded, not pre-built) is indexing writers by
  name (dict[str, list[int]]) instead of the quadratic scan - a driver-only change, unit-testable.
- **Registry size**: ~378 new rows of mostly-short tuples replace one row with three ~600-name
  tuples; net file size change is expected to be modest in either direction (the 621-param
  signature and 587-name return tuple disappear; ~378 small signatures/returns appear).

## R7. mypy / ruff / coverage over the generated region

- Bodies move verbatim WITH their existing `# type: ignore[...]` comments; new wrapper lines
  (defs, guards, returns) may need fresh ignores where param-typing as `Any` starves inference -
  022 solved this with `_inject_type_ignores` (ruff-format + mypy fixpoint); the transformer
  reuses that function scoped to the new region. `ruff format` runs on the result; the
  registry block keeps its `# fmt: off`.
- Coverage: the moved lines are executed by exactly the fixtures that executed them before
  (same manifests, same branches); new guard lines execute on every gate run. The 100% gate is
  expected to hold with no test changes; if a `# pragma: no cover` boundary artifact appears
  (like `_UnboundType._boom`), it gets the same documented-pragma treatment 022 used.

## R8. What stays untouched, deliberately

- `gate()` driver, `_GateSeg` shape, `META_CHECKS`, `_SEG_DEPS` builder (unless R6 measurement
  forces the indexed variant), `gate_check_names.json` (byte-identical - names only move
  between rows), fixture format, `test_regressions.py`, `oracle_sweep.py`.
- The clause-12 inline annotation on the mega-segment is DELETED with the function - its debt
  is what this feature pays. The registry doctrine section in the diagram skill's CLAUDE.md
  gets a short record-the-why note that the city battery is now per-statement segments under
  in-body scale guards (spec FR-009).

## R9. Risks and controls

| Risk | Control |
|---|---|
| A `needs`/`writes` edge wrong at the new granularity (the three 022 holes, one level deeper) | Reused analysis code + the full targeted-vs-full sweep over 791 real geometries; any miss surfaces as a verdict diff (the sweep caught exactly this 3 times in 022) |
| Stale closure cell from a helper split away from a later rebind | Hard-fail census rule (R4); oracle as behavioral backstop |
| Guard re-evaluation drift if `meta`/`scale` were mutated | Hard-fail census rule (R3) |
| Import-time cost of a ~960-row quadratic `_SEG_DEPS` | Measured before/after; indexed-writers fallback designed (R6) |
| mypy/ruff churn on ~378 new defs | 022's fixpoint injector reused; `make done` is the gate |
| Silent loss of record-the-why comment banks between statements | Gap-emission preserved from 022's generator; spot-check the diff for comment survival |
| Replay slower despite narrowing (row overhead) | Timed baseline vs post; FR-008's ~10% bound |

## R10. What implementation taught (added after the sweeps and the gate, 2026-08-15)

- **The sweeps caught no dataflow hole**: at per-statement granularity the region censused clean
  on the first pass - zero stale-cell merges, zero opaque check names, zero meta reads - and
  both oracle sweeps were zero-diff on the first post-transform run (816 manifests full-mode,
  793 fixtures targeted). The 022 analysis code carried over without modification; the only
  environment fix was registering the exec'd module in `sys.modules` for 3.14 dataclasses.
- **The verbatim-first guard design collided with lint, by design**: the zero-re-indentation
  nested guards (R2) tripped 341 SIM102 findings. Resolution order mattered and is the reusable
  lesson: land the transform verbatim, prove identity with the oracle FIRST, and only then let
  `ruff check --select SIM102 --fix --unsafe-fixes` (a second mechanical transformer) combine
  the guards - then RE-RUN the full oracle battery on the result. Ruff declined 26 sites where
  a comment bank sits directly under the guard; those keep the nested form under a per-line
  `# noqa: SIM102` rather than risking comment relocation. Doing the guard-combining by hand
  inside the transformer would have meant re-indenting bodies during the risky step; letting
  lint do it after identity was banked kept every step mechanical and separately verified.
- **`/usr/bin/time` does not exist in this container** - a baseline script that used it
  "succeeded" with its two most important steps silently skipped (the wrapped-exit-code lesson
  from memory, in a new costume: the failure was visible only by reading the log body). Use the
  bash `time` builtin.
