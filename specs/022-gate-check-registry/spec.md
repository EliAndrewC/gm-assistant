# Feature Specification: Gate Check Registry (targeted check execution)

**Feature Branch**: `022-gate-check-registry` (no branch - `SPECIFY_FEATURE=022-gate-check-registry`, per CLAUDE.md)

**Created**: 2026-08-15

**Status**: Draft

**Input**: User description: "Split check_village.py's gate() (12,944 lines, 189 checks, one local check() closure) into a per-check registry of human-scale functions so the gate can run a requested subset of checks; switch the regression replay to targeted mode; preserve full-gate behavior exactly; oracle = identical verdicts on all 791 fixtures + 28 pool maps; measurable replay speedup in timings.md. Discharges constitution Principle X clause 12 for the repo's worst offender."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Targeted check execution (Priority: P1)

A session (or tool) asks the gate to evaluate ONE named check - or a small set - against a
manifest, and gets exactly the verdict the full gate would give for those checks, without paying
for the other ~188. This is the capability everything else builds on: the regression replay, and
any future tool that wants to ask "does this manifest still trip check X?" cheaply.

**Why this priority**: Without verdict-identical subset execution there is no safe speedup - a
targeted verdict that can disagree with the full gate is worse than slow.

**Independent Test**: For a sample of fixtures spanning small/medium/large manifests, run the full
gate and the targeted gate for each fixture's declared checks; the targeted verdicts must equal
the full-gate verdicts for those names, every time.

**Acceptance Scenarios**:

1. **Given** a frozen city manifest that fails `wells_clear_of_paddies` under the full gate,
   **When** the gate runs with `only={"wells_clear_of_paddies"}`, **Then** that check fails with
   the same verdict, and expensive unrelated work (the overlap matrix, unrelated sweeps) is not
   performed.
2. **Given** a manifest that PASSES a check under the full gate, **When** the gate runs targeted
   on that check, **Then** the check passes - a targeted run can never manufacture a failure.
3. **Given** a check name that does not exist in the registry, **When** the gate runs targeted on
   it, **Then** it raises an explicit error - never a silent "ran nothing, found nothing".
4. **Given** a parametrized check (verdicts like `field_ringed[ikegami-paddies]`), **When** the
   gate runs targeted on the BASE name, **Then** every parametrized instance of it is evaluated.
5. **Given** a check that the manifest's meta waives, **When** run targeted, **Then** the waiver
   semantics are identical to the full gate (waived = not in the failure list).

---

### User Story 2 - Regression replay switches to targeted mode (Priority: P2)

The regression corpus replay (791 fixtures, each declaring in `_regression.fires` the checks it
must trip) verifies each fixture by running only its declared checks. Today 210 frozen whole-city
fixtures each pay a full 189-check gate (2-6 s apiece, ~61% of suite CPU) to verify one check.

**Why this priority**: This is the payoff - the dominant, forever-growing cost in `make done` -
but it is only safe once User Story 1's identity guarantee holds.

**Independent Test**: The replay passes on all 791 fixtures in targeted mode, and a deliberate
check-neutering (revert one check's logic) still turns the replay red for that check's fixtures.

**Acceptance Scenarios**:

1. **Given** the current corpus, **When** the replay runs in targeted mode, **Then** all 791
   fixtures still verify their `fires` lists, and replay wall/CPU drops by the target factor.
2. **Given** a fixture whose `fires` names a whole-run meta-check (`waivers_are_documented`,
   `waivers_are_live`, `every_feature_classified_*`, or any check that reads which other checks
   ran or failed), **When** the replay reaches it, **Then** that fixture falls back to the FULL
   gate, so meta-check semantics are never approximated.
3. **Given** a future session freezing a new fixture, **When** it names its `fires`, **Then**
   nothing about the fixture format changes - targeted mode reads the same `_regression` block.

---

### User Story 3 - The gate becomes human-scale functions (Priority: P3)

`gate()` stops being a 12,944-line function. Checks become individually named, human-scale
functions in an explicit registry; shared derived geometry becomes a context that computes each
derivation once, on demand. Constitution Principle X clause 12 is discharged for the repo's worst
offender, and future tools (why-did-this-fire, per-check profiling) get an API instead of a
monolith.

**Why this priority**: Valuable and durable, but it is the means; Stories 1-2 are the ends. If
scope must be cut, a partially-decomposed gate that still meets Stories 1-2 plus full-mode
identity is acceptable for this feature, with the remainder recorded as debt.

**Independent Test**: A structural audit of `check_village.py` finds no unannotated function past
the constitution's thresholds, and every one of the ~189 check names maps to exactly one registry
entry.

**Acceptance Scenarios**:

1. **Given** the refactored module, **When** functions are measured in logical statements,
   **Then** no function exceeds a few hundred, except any explicitly annotated per clause 12.
2. **Given** the registry, **When** its names are compared with the verdict names the old gate
   could emit, **Then** they match exactly - no check lost, none renamed, none duplicated.

---

### Edge Cases

- A check whose body both computes shared state AND checks (entangled infrastructure): the shared
  computation must move to the context so a targeted run of a LATER check still sees it.
- Checks that mutate shared registries as they go (append/extend): the context must preserve the
  full-gate order of those mutations, or hold them immutable per derivation.
- A fixture whose `fires` mixes ordinary checks and a meta-check: full-gate fallback for the whole
  fixture (correctness over speed; these are rare).
- `only` containing a name the manifest's scale never runs (a city check against a hamlet): the
  targeted run must report it the same way the full gate does - not-run is not-failed, and the
  replay's "no longer trips" message must still name it missing.
- Verbose output: full mode's stdout must stay byte-identical; targeted mode prints only what it
  ran (new behavior, so no compatibility constraint beyond being truthful).
- Concurrency: the replay runs under `pytest -n auto`; targeted execution must not introduce
  cross-test shared mutable state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The gate MUST accept an optional set of requested check names and, when given one,
  evaluate only those checks plus the shared derivations they actually require.
- **FR-002**: For every requested name, the targeted verdict (fail / pass / waived) MUST be
  identical to the verdict the full gate produces on the same manifest.
- **FR-003**: With no subset requested, behavior MUST be unchanged: same verdict list in the same
  order, same PASS/FAIL/WAIVE stdout bytes, same waiver semantics, same return type.
- **FR-004**: Whole-run meta-checks (those reading which checks ran, failed, or were waived) MUST
  be excluded from targeted mode; requesting one MUST either run the full set or raise - it MUST
  NOT return an approximated verdict.
- **FR-005**: The regression replay MUST verify each fixture via targeted mode using its declared
  `fires`, falling back to the full gate for fixtures naming meta-checks; the fixture format is
  unchanged.
- **FR-006**: Every check name MUST be registered exactly once; requesting an unknown name MUST
  raise an explicit error.
- **FR-007**: Parametrized verdict names (`base[instance]`) MUST be requestable by base name.
- **FR-008**: Shared derivations MUST be computed at most once per gate invocation (full or
  targeted), preserving the full gate's derivation values exactly.
- **FR-009**: The decomposition MUST leave no unannotated function beyond constitution Principle X
  clause 12 thresholds in `check_village.py`.
- **FR-010**: The whole quality gate (`make done`: lint, format, mypy, pytest, 100% coverage on
  covered modules) MUST pass; `check_village.py` remains a covered module.

### Key Entities

- **Check**: a named predicate over a manifest, possibly emitting parametrized verdicts; belongs
  to exactly one registry entry; may be scale-gated (runs only for some settlement tiers).
- **Registry**: the ordered list of all checks; its order IS the full gate's execution and output
  order.
- **Context**: per-invocation carrier of the manifest, meta, waiver state, and shared derived
  geometry, computed lazily and at most once.
- **Meta-check**: a check whose subject is the run itself (staleness of waivers, completeness of
  classification); only meaningful for a full run.
- **Regression fixture**: a frozen manifest plus `_regression.fires` (the checks it must trip) -
  format unchanged by this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Verdict-identity sweep: sorted full-gate verdicts on all 791 regression fixtures and
  all 28 pool maps are identical before vs after the refactor - zero differences.
- **SC-002**: Replay honesty: in targeted mode, every fixture still verifies its `fires`, and
  neutering any sampled check turns its fixtures red (spot-check on 3+ checks).
- **SC-003**: Replay cost: serial replay of the 210 large fixtures drops by at least 5x; the
  replay's share of suite CPU drops from ~61% to under 25%.
- **SC-004**: Wall clock: `make done` total drops measurably (expected ~4:10 toward ~3:00 or
  better); the result is appended to `timings.md` as a dated ledger block with breakdown.
- **SC-005**: Structure: no unannotated function in `check_village.py` past clause 12 thresholds;
  registry names match the legacy verdict-name set exactly.
- **SC-006**: `make done` is green at the end, including 100% coverage.

## Assumptions

- "Verdict identity" is defined as: equal failure sets (and waiver sets) per manifest, and for
  full mode additionally byte-identical stdout and identical failure-list ORDER. Targeted-mode
  stdout is new surface and only needs to be truthful about what ran.
- The registry's execution order will be the current gate's textual order, which preserves
  full-mode output order for free.
- Targeted mode is an internal/testing surface (the replay, future tools); no CLI change is
  required beyond what falls out naturally.
- The 210 >50 KB fixtures dominate replay cost (measured 2026-08-15: corpus serial ~500 s, with
  <10 KB fixtures at ~8-25 ms each); the speedup target is set against them.
- Fixtures whose `fires` name meta-checks are rare; full-gate fallback for them costs negligible
  time.
- The decomposition may proceed in mechanical stages (sections first, per-check second) as long as
  the end state meets FR-009; intermediate committed states must still pass the full oracle.
- No behavior change to `check_village.py main()` CLI beyond, at most, an optional flag for
  targeted runs.
