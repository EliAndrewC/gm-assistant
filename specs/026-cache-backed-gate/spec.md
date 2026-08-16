# Feature Specification: Cache-Backed Gate

**Feature Branch**: `026-cache-backed-gate` (no branch is created - this project stays on `main`; `SPECIFY_FEATURE=026-cache-backed-gate` names the active feature)

**Created**: 2026-08-16

**Status**: Draft

**Input**: User description: "Cache-backed gate: make done reuses verified gen-cache hits instead of always regenerating scripted maps. GM decision 2026-08-16 reversing the 2026-08-08 'gate never reads the cache' rule." (Full text in the conversation; the operative scope items are restated below.)

## Context and the decision being reversed

Since 2026-08-08 the diagram skill's gate (`make done` → `test_villages.py`) has ALWAYS regenerated
every live scripted map from scratch, never consulting the gen cache - pinned by
`test_the_gate_never_reads_the_cache` and documented in `gencache.py`'s docstring ("it is never the
source of truth") and the skill CLAUDE.md. The rationale was that the cache key is a claim, not a
proof, so the gate served as the backstop for key bugs.

**GM decision 2026-08-16: reverse this.** The reasoning, recorded so the "why" survives:

- A cache hit is a verified-inputs claim: the key hashes the gen's bytes, the module-level source of
  every engine module, the source of every function the map executed, every non-source file the run
  opened, and the interpreter/renderer versions. Generation is deterministic, so a sound key implies
  byte-identical output. Cross-session timing cannot produce false validity: caches are per-clone
  and every push is preceded by a locked pull, which moves the key for any pulled engine change.
- The known blind spot - third-party dependencies below the Python-source horizon (the PIL
  layout-engine incident class: a Pillow bump rewrote 16 manifests with no code change) - is
  CLOSEABLE by keying the container lockfiles / installed package versions. This feature closes it
  before flipping the default.
- Residual risk after that is "gencache itself has a bug," which is what `cache_audit.py` (empirical
  byte-comparison audit, proven teeth) and an explicit bypass exist for.
- The payoff clears the GM's stated threshold TODAY (~10-30 s of a ~3 min gate; **a >=5% speedup to a
  whole process is always above the caring threshold, even at small absolute seconds** - GM
  2026-08-16), and grows with every tier conversion: village/town/city gens cost minutes each, and
  the migration plan intends to convert all of them.
- Accepted trade-off, stated plainly: the manual step "after a dependency-level change, run the
  sweep once cache-bypassed" can be forgotten. Lockfile keying makes the *known* dependency channel
  automatic; the manual procedure is belt-and-suspenders for unknown channels. On balance the GM
  judges this the right default, with the bypass as the escape hatch.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dependency changes invalidate the cache automatically (Priority: P1)

A session upgrades or installs a Python package (or rebuilds the container with different pinned
versions). Every gen-cache entry made under the old dependency set must become invalid
automatically, with no one having to remember that maps depend on libraries.

**Why this priority**: This is the safety precondition the GM's approval was contingent on. It also
delivers standalone value immediately - `regen.py`'s interactive users are exposed to the same
blind spot today.

**Independent Test**: Warm the cache, perturb the dependency-state input (e.g. a lockfile byte),
re-run - every entry must miss. Restore it - entries hit again.

**Acceptance Scenarios**:

1. **Given** a warm cache, **When** the recorded dependency state changes in any byte, **Then** the
   next regeneration of every map is a MISS.
2. **Given** a warm cache, **When** nothing changes, **Then** hits still occur (the new key input is
   stable across runs on an unchanged environment).
3. **Given** an environment where the dependency state cannot be resolved, **Then** the key
   degrades in the conservative direction (regenerate unnecessarily, never serve staleness).

---

### User Story 2 - The gate skips generation on a verified hit (Priority: P2)

A session runs `make done` after work that did not touch the engine (a test refactor, a docs edit
caught mid-gate, a webapp change in the same tree). For every live map whose cache entry is a
verified hit, the gate loads the cached manifest and runs ALL current checks against it, skipping
only the generation step. Any miss regenerates exactly as today.

**Why this priority**: This is the payoff - the gate gets faster by the whole generation share of
the sweep whenever the engine is untouched, and the saving scales with every future tier
conversion.

**Independent Test**: Run the gate twice back-to-back with no edits; the second run's sweep skips
generation for every live map and the gate stays green. Edit an engine function a map executes; that
map regenerates.

**Acceptance Scenarios**:

1. **Given** a warm, valid cache and no source changes, **When** the gate runs, **Then** no live-map
   generation executes, all current checks still run against each cached manifest, and the gate's
   verdict is identical to a cold run.
2. **Given** a check was added or changed since the cache entry was stored, **When** the gate runs
   on a hit, **Then** the NEW check battery runs against the cached manifest (checking is never
   cached).
3. **Given** an engine edit that a map executed, **When** the gate runs, **Then** that map is a miss
   and regenerates; unaffected maps may still hit.
4. **Given** a cold or absent cache (fresh clone), **When** the gate runs, **Then** it behaves
   exactly as today (regenerate everything) and passes.
5. **Given** the coverage floors (100% on pure-logic modules, the settlement.py ratchet), **When**
   the gate runs with any mix of hits and misses, **Then** the floors are still enforced and still
   meaningful - a hit contributes the coverage its generation would have produced (carried forward
   under the same cache key), and any entry lacking carried coverage data is treated as a miss.

---

### User Story 3 - Bypass, doctrine, and the dependency-change procedure (Priority: P3)

A session (or the GM) suspects the cache is wrong, or has just made a dependency-level change. An
explicit bypass forces the gate to regenerate everything, and the written procedure says when to use
it. All doctrine text claiming "the gate never reads the cache" is updated to the new contract.

**Why this priority**: The escape hatch and the record. Without it the reversal is undocumented and
the old doctrine actively misleads future sessions.

**Independent Test**: Run the gate with the bypass set on a warm cache - everything regenerates.
Grep the docs for the old rule - no stale statement of it remains.

**Acceptance Scenarios**:

1. **Given** a warm, valid cache, **When** the gate runs with the bypass set, **Then** every map
   regenerates from scratch (and the run is otherwise a normal gate).
2. **Given** the updated docs, **When** a session reads `gencache.py`'s docstring, the skill
   CLAUDE.md, or the root CLAUDE.md, **Then** each states the new contract (hit skips generation
   only; checks always run; bypass exists; dependency-change procedure; cache_audit remains the
   standing auditor after any change to gencache or how generation is driven).
3. **Given** the retired pinning test, **Then** replacement tests pin the new contract instead:
   hit-runs-current-checks, bypass-forces-regeneration, changed-input-forces-regeneration,
   missing-coverage-data-forces-regeneration.

---

### Edge Cases

- **Partial hits**: some maps hit, some miss in one gate run - each map is independent; the verdict
  and coverage must compose correctly.
- **Corrupt or incomplete cache entry** (missing manifest, missing coverage data, unreadable
  meta): treated as a miss. The failure direction is always "regenerate unnecessarily."
- **Concurrent writers** in one clone: already covered by the cache's atomic temp-then-replace
  publish; the gate reading an entry mid-publish sees a complete entry or none.
- **The randomness-immunity test** regenerates its subject twice BY DESIGN (once with an injected
  extra draw) and is explicitly out of scope - it must keep regenerating.
- **The regression replay** reads frozen fixtures and never regenerates - unaffected.
- **Frozen legacy maps and Mode A compounds** are not swept at all (feature: the 2026-08-16 freeze) -
  unaffected.
- **Key-scheme change**: bumping the cache format version invalidates everything, including carried
  coverage data.
- **The documented cache trap** (edit → regen → checkout away → legitimate miss) still applies and
  the docs must keep saying so.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The gen-cache key MUST incorporate the environment's third-party dependency state
  (the container lockfiles and/or installed package versions), such that any dependency-level
  change invalidates every entry, and an unresolvable dependency state degrades conservatively
  (toward regeneration).
- **FR-002**: The gate's live-map sweep MUST consult the cache: on a verified hit it loads the
  cached manifest and runs the complete current check battery against it; generation alone is
  skipped. Checking is NEVER cached.
- **FR-003**: On a miss (including corrupt/incomplete entries and cold caches) the sweep MUST
  regenerate exactly as it does today.
- **FR-004**: An explicit bypass (environment variable) MUST force full regeneration regardless of
  cache state, and MUST NOT silence any test that proves the cache-backed path works (the
  DIAGRAM_ALLOW_SLOW_GENS self-test lesson).
- **FR-005**: The coverage gates (100% pure-logic, the settlement.py ratchet floor) MUST remain
  enforced and meaningful under any mix of hits and misses: per-map coverage data is stored in the
  cache entry under the same key and merged into the run's coverage on a hit; an entry without
  usable coverage data is treated as a miss.
- **FR-006**: `test_the_gate_never_reads_the_cache` MUST be retired and replaced by tests pinning
  the new contract (per US3 scenario 3), each verified to have teeth (reverting the behavior fails
  the test).
- **FR-007**: All doctrine text stating the old rule MUST be updated: `gencache.py`'s docstring
  ("WHAT IT DELIBERATELY DOES NOT DO"), the skill CLAUDE.md ("The cache is NEVER the source of
  truth" section and the gate/sweep guidance), and the root CLAUDE.md if it restates the rule. The
  updated text MUST record the GM's 2026-08-16 decision and its reasoning (record-the-why), the
  dependency-change procedure, and the >=5% whole-process threshold rationale.
- **FR-008**: The documented procedure MUST state: after a dependency-level change (pip
  install/upgrade, container rebuild outside the lockfiles), run the sweep once with the bypass on
  the main checkout; and `cache_audit.py` remains mandatory after any change to gencache or to how
  generation is driven - including THIS feature, so the implementation itself MUST run it and
  record the result.
- **FR-009**: The randomness-immunity test and the regression replay MUST be functionally
  unchanged.
- **FR-010**: `timings.py` MUST gain (or the ledger MUST record) a warm-gate measurement so the
  saving is measured rather than asserted, per the ledger's re-measure doctrine.

### Key Entities

- **Cache entry**: per-map stored artifacts (manifest JSON, SVG, optional PNG) plus metadata keyed
  by the dependency key; gains a per-map coverage-data artifact.
- **Dependency key**: the existing input hash, extended with the dependency-state input.
- **Gate sweep**: the per-map test that today always generates; becomes hit-aware.
- **Bypass**: environment variable read by the sweep (and honored end-to-end).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With a warm cache and no source changes, the full gate is measurably faster than the
  cold-cache gate by at least 5% wall clock, measured on the same box in the same load conditions
  and recorded in the timings ledger with a dated block.
- **SC-002**: `cache_audit.py` passes after the change (byte-identical artifacts with and without
  the cache under a perturbed engine literal), demonstrating the promotion of the cache into the
  gate did not change what the cache proves.
- **SC-003**: A simulated dependency change (perturbing the recorded dependency state) invalidates
  100% of warm entries; restoring it restores hits.
- **SC-004**: The gate is green both cold and warm, with identical verdicts, and every coverage
  floor unchanged (100% pure-logic modules; settlement.py >= its ratchet floor).
- **SC-005**: Every new pinning test fails when its behavior is reverted (teeth demonstrated during
  implementation, per the subagent-check TDD discipline adapted to plain tests).

## Assumptions

- The bypass variable is named `GATE_NO_CACHE=1` (consistent with the skill's existing
  `DIAGRAM_*`/`GATE_*` env-var conventions; exact name confirmable at plan time).
- The dependency-state input is derived from the container's two lockfiles (paths per
  `docs/container.md`) plus the versions of imported third-party packages actually present at run
  time; the precise composition is a plan-time decision with the constraint that its failure
  direction is conservative.
- Carried coverage data is only valid because generation is deterministic: identical inputs imply
  an identical execution trace, so the coverage a hit "would have produced" is exactly what the
  stored run produced. This is the same soundness basis as the manifest cache itself.
- The gate continues to run under `pytest -n auto`; per-map coverage artifacts must therefore
  compose under parallel collection (plan-time mechanics).
- The frozen-manifest regression replay added at the 2026-08-16 freeze continues to carry the
  check-branch coverage it was added for; this feature's coverage carry-forward concerns the
  GENERATION-side modules exercised by the sweep.
- No map output changes at all: this feature is output-preserving by construction, so no
  settlement-review pass is required (the byte-identity oracle, as with the SeatMemo work).
