# Feature Specification: Split the City Mega-Segment

**Feature Branch**: `main` (session-clone workflow - see CLAUDE.md; no feature branches, `SPECIFY_FEATURE=023-split-city-mega-segment`)

**Created**: 2026-08-15

**Status**: Draft

**Input**: User description: "Split the /diagram gate's mega-segment _seg_0563__city_has_six_ministries (check_village.py, 3,607 lines, 1,040 statements, emits 148 checks - the entire city/capital urban battery) into properly-sized per-check-cluster segment functions in the GATE_SEGMENTS registry, per constitution Principle XII (functions stay at human scale). Verdict identity must be preserved (oracle sweep targeted-vs-full over all fixtures), targeted execution (gate(M, only=...)) must keep working with correct dependency closure, and the registry-pin test / gate_check_names.json stay consistent."

## Context

Feature 022 turned `gate()` from a 12,944-line function into a driver over `GATE_SEGMENTS`, an
ordered registry of ~586 segment functions. That transformation carved the body at check
boundaries wherever the dataflow allowed - but one region resisted: the city/capital "urban
battery" came out as a single segment, `_seg_0563__city_has_six_ministries`, named after just one
of the **148 check names** it emits. At 3,607 raw lines and **1,040 logical statements** it is
the largest function in the /diagram skill and sits past the ~1,000-statement line that
constitution Principle XII (v1.5.0, GM-directed 2026-08-15) calls a defect absent an inline
justification. No such justification exists, and none is warranted: the checks inside it are
mostly independent rule clusters (samurai housing, caste mix, martial halls, merchant fabric,
gate furniture, fire towers, tanning/theater/temple placements, wall/moat geometry ...) that
happen to share upstream locals.

The cost is the same one that motivated 022: nothing inside the mega-segment can run separately.
A targeted run (`gate(M, only={"city_has_bathhouse"})`) that needs any one of the 148 checks
executes all 1,040 statements, and the regression replay's targeted mode gains nothing for every
city/capital fixture whose fired checks land in this segment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainer edits one city check (Priority: P1)

A session adding, tuning, or debugging a single city/capital check (the most common /diagram gate
maintenance task) can locate that check's segment as its own function of reviewable size, read
only the inputs it declares, and edit it without scrolling through the other 147 checks' logic.

**Why this priority**: this is the architecture defect Principle XII names - the function's size
is a growth accident, not a design, and every future city-tier feature (the capital tier is
actively under construction) pays the reading and editing tax.

**Independent Test**: pick any check name emitted by the current mega-segment; verify the
function that emits it is at human scale (a few hundred statements at most) and that its
registry row declares what it reads (`needs`/`free`) and provides (`writes`).

**Acceptance Scenarios**:

1. **Given** the post-split registry, **When** a maintainer greps for a city check name,
   **Then** they land in a segment function whose whole body concerns that check's cluster and
   whose statement count is at human scale.
2. **Given** the post-split `check_village.py`, **When** the largest function in the /diagram
   skill is measured in logical statements, **Then** no function exceeds the Principle XII
   defect line (~1,000 statements), and no *new* segment produced by this split exceeds 400
   statements without an inline annotation explaining why its cluster is indivisible.

---

### User Story 2 - Targeted execution stays correct and gets narrower (Priority: P2)

`gate(M, only={...})` continues to produce verdicts identical to a full run for every check name,
and for city/capital check names the executed closure shrinks: requesting one urban check no
longer drags in the whole 148-check battery.

**Why this priority**: targeted execution is why the registry exists (regression replay 480s ->
58s). Correctness of the dependency closure is NON-NEGOTIABLE; narrowing is the payoff that
makes the split worth doing beyond compliance.

**Independent Test**: the 022 oracle sweep (`oracle_sweep.py targeted`) compares targeted-vs-full
verdicts over all frozen fixtures; run it after the split.

**Acceptance Scenarios**:

1. **Given** all frozen fixtures (regression corpus + pool manifests), **When** the
   targeted-vs-full oracle sweep runs, **Then** every fixture's targeted verdicts are identical
   to its full-run verdicts.
2. **Given** a request for a single city check that today lives in the mega-segment, **When**
   its dependency closure is computed post-split, **Then** the closure executes strictly fewer
   statements than the pre-split mega-segment did.

---

### User Story 3 - Regression replay and registry pins stay green (Priority: P3)

The existing test surface - the registry-pin test against `test_fixtures/gate_check_names.json`,
the targeted regression replay (`test_regressions.py`), and the full check_village test files -
passes unchanged in what it asserts: the split changes function boundaries, never check names,
check semantics, or execution order.

**Why this priority**: these suites are the project's proof that a refactor of this size changed
nothing observable; they must stay green without weakening.

**Independent Test**: run the full diagram test bed once at the end (per the iteration-loop
doctrine); the check-name pin file needs at most a re-derivation of which segment emits which
name, never a change to the name set.

**Acceptance Scenarios**:

1. **Given** the post-split registry, **When** the registry-pin test runs, **Then** the set of
   emitted check names is byte-identical to before the split.
2. **Given** the post-split registry, **When** the regression replay runs targeted, **Then**
   every frozen fixture still fires exactly its recorded `_regression.fires`, and replay wall
   time does not regress materially.

---

### Edge Cases

- **Shared upstream locals**: many of the 148 checks read the same computed values (e.g. wall
  ring geometry, caste tallies, street graph). A naive split that recomputes them per segment
  changes cost; a split that threads them as `writes` -> `needs` edges must get every edge right
  or targeted runs silently read `_UNBOUND`.
- **The three 022 dataflow holes** (helper-closure mutation, upward-exposed reads vs raw loads,
  comprehension-target scoping - specs/022 research.md R9): each is a way a mechanical splitter
  produces a dependency edge that LOOKS right and is wrong. Any edge not validated by the
  empirical sweep is untrusted.
- **Interleaved scale branches**: the mega-segment mixes `city`-only, `capital`-only, and
  shared blocks (020 doctrine: rules that INVERT at the capital). A split boundary that
  separates a computation from the scale guard that made it safe changes behavior on the other
  scale tier.
- **Order sensitivity**: registry order IS the legacy execution order; new segments must slot
  into position 563's place as a contiguous run, or verdict-order-sensitive output (and the
  replay transcripts) drifts.
- **A check that never RUNS looks exactly like a check that passes** (diagram CLAUDE.md): if a
  split drops a segment from some scale tier's closure, the gate stays green while silently
  validating less. Verdict-identity comparison must therefore compare the full emitted check
  LIST per fixture, not just pass/fail.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The mega-segment `_seg_0563__city_has_six_ministries` MUST be replaced by multiple
  segment functions, each emitting a coherent cluster of the original 148 check names, with
  every original check name emitted by exactly one new segment.
- **FR-002**: No new segment function may exceed 400 logical statements (AST `stmt` count)
  unless an inline annotation at its definition explains why its cluster is indivisible; the
  1,000-statement Principle XII defect line MUST NOT be crossed by any function in
  `check_village.py` after the split.
- **FR-003**: Full-gate verdicts (the complete ordered list of emitted check results, names and
  pass/fail/notes alike) MUST be identical before and after the split for every frozen
  regression fixture and every pool manifest.
- **FR-004**: Targeted execution (`gate(M, only=...)`) MUST return verdicts identical to the
  full run for every check name on every fixture, demonstrated by the 022 oracle sweep's
  targeted-vs-full comparison, re-run in full after the split.
- **FR-005**: Each new segment's registry row (`free`/`writes`/`checks`/`needs`) MUST be derived
  from the actual dataflow, honoring the three documented 022 holes; no dependency edge ships
  unswept.
- **FR-006**: The set of check names in `test_fixtures/gate_check_names.json` MUST be unchanged;
  the pin test may only need its per-segment attribution refreshed.
- **FR-007**: The new segments MUST occupy the mega-segment's registry position as a contiguous,
  correctly-ordered run so overall execution order is preserved.
- **FR-008**: The targeted regression replay MUST remain green with wall time not materially
  worse (within ~10% of current), and the dependency-closure narrowing MUST be real: the median
  closure for a city-check targeted run shrinks in executed statements.
- **FR-009**: The rationale for the chosen cluster boundaries MUST be recorded where the rule
  lives (record-the-why: a short note in the diagram skill's CLAUDE.md registry section or
  alongside the segments), including any cluster deliberately kept large.

### Key Entities

- **Segment function** (`_seg_NNNN__<name>`): one body in the registry; reads inputs as keyword
  params defaulting to `_UNBOUND`, returns `_kept(locals(), <names>)`.
- **Registry row** (`_GateSeg`): `(fn, free, writes, checks, needs, meta, always)` - the
  dataflow declaration targeted execution trusts.
- **Oracle sweep**: the 022 harness (`specs/022-gate-check-registry/oracle_sweep.py`) comparing
  full-vs-targeted verdicts over all frozen fixtures - the empirical guard on closure rules.
- **Check-name pin** (`test_fixtures/gate_check_names.json`): the frozen name inventory the
  registry-pin test compares against.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The largest function in the /diagram skill drops from 3,607 lines / 1,040
  statements to at most 400 statements (annotated exceptions aside), measured by AST statement
  count over `check_village.py`.
- **SC-002**: The targeted-vs-full oracle sweep passes over 100% of frozen fixtures with zero
  verdict differences.
- **SC-003**: The full diagram test bed (registry pin, regression replay, check unit tests,
  coverage gate) is green with no weakened assertion, and replay wall time stays within ~10% of
  its pre-split baseline.
- **SC-004**: A targeted run for a single former-mega-segment check executes measurably fewer
  statements than before - the 148-check battery no longer runs as a unit when one check is
  requested.
- **SC-005**: Zero check names added, removed, or renamed.

## Assumptions

- The retired 022 migration tooling (`specs/022-gate-check-registry/` transformer + oracle
  sweeps) is the starting point; reusing or extending it is preferred over hand-splitting 3,607
  lines, but the spec does not mandate the mechanism - only the verified outcome.
- Cluster granularity is a judgment call bounded by FR-002: one segment per check is NOT
  required; tightly-coupled checks (e.g. the moat hydrology family) may share a segment when
  splitting them would duplicate substantial computation or create gratuitous dataflow edges.
- Shared expensive computations may become their own non-check "provider" segments (writes-only,
  no `checks`) if that is the cleanest way to keep clusters small - the registry model already
  supports segments that only bind values.
- The regression fixture format and `_regression.fires` semantics are unchanged.
- No behavior change of any check is in scope; any latent bug discovered inside the mega-segment
  is recorded and deferred, not fixed in this feature (verdict identity is the contract).
