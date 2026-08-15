# Feature Specification: Human-Scale Files

**Feature Branch**: `024-human-scale-files`

**Created**: 2026-08-15

**Status**: Draft

**Input**: User description: "Add a repo-wide file-size rule of thumb (files past ~1,000 lines should prompt a split into a directory-module with a CLAUDE.md index) and apply it to check_village.py, breaking up the oversized gate segments starting with _seg_0285__wells_clear_of_shrine_and_torii."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The rule exists and is findable (Priority: P1)

The GM (and every future session) needs the file-size practice written down where the sibling
function-size rule already lives, so that any session noticing a fat file knows the expected shape
of the fix: a directory-module whose CLAUDE.md indexes the subfiles and says when to load each one.
The motivating cost is token economy - a session that needs one check from a 35,000-line file
currently pays for the whole file in its context window.

**Why this priority**: The documentation is the durable part. Files will grow again; the rule is
what keeps the practice alive after this feature's context is gone.

**Independent Test**: Read the constitution's Python Discipline principle; a clause about file
size at human scale exists, states the ~1,000-line ask-the-question threshold, names the
directory-module + CLAUDE.md-index target shape, and records token economy as the why.

**Acceptance Scenarios**:

1. **Given** the constitution at its current version, **When** the amendment lands, **Then**
   Principle X contains a new clause (sibling of clause 12) covering file size, and the
   constitution's version and sync-impact header are bumped accordingly.
2. **Given** a future session reads the clause, **When** it meets a 1,000+ line file, **Then** the
   clause tells it both the question to ask and the target shape (package of subfiles + CLAUDE.md
   index per the slim-index/load-on-demand doc pattern).

---

### User Story 2 - check_village.py becomes a navigable package (Priority: P1)

A session that needs to read or edit one gate check today loads a 35,602-line file. After the
split, `check_village/` is a package of thematically-grouped files with a CLAUDE.md that says when
to look in each one, so the session loads only the file holding the checks it cares about.

**Why this priority**: This is the motivating application of the rule and the largest single token
sink in the project. The rule without the exemplar is just words; the exemplar IS the pattern
future splits copy.

**Independent Test**: `from check_village import gate, load` still works; the gate produces
byte-identical verdicts on every saved fixture; no single file in the new package exceeds the
threshold without an inline justification; the package CLAUDE.md indexes every subfile.

**Acceptance Scenarios**:

1. **Given** the current single-file gate, **When** the package split lands, **Then** every
   existing caller (tests, regen tooling, docs, skill instructions) works unchanged or is updated
   in the same feature, and the full gate run over all pool manifests and regression fixtures
   produces identical verdicts in identical order.
2. **Given** the new package, **When** a session asks "where do I find the well checks?",
   **Then** the package CLAUDE.md answers with a specific file and a one-line description of what
   lives there.
3. **Given** the `gate(M, only={...})` targeted-execution contract, **When** the split lands,
   **Then** targeted runs still produce verdicts identical to the full run and the regression
   replay keeps its targeted speed.

---

### User Story 3 - Oversized gate segments become per-check segments (Priority: P2)

`_seg_0285__wells_clear_of_shrine_and_torii` is 1,351 lines and bundles wells, gardens, and grove
concerns in one body; several other segments similarly bundle multiple checks. A session that
wants to modify one check inside such a segment must today read and reason about the whole bundle.
After the split, each concern is its own registry segment, targetable by `gate(M, only=...)`.

**Why this priority**: P2 because the package split (Story 2) delivers most of the token savings;
this story pays down the remaining function-scale debt per Principle X clause 12. It is still in
scope for this feature - the GM asked for it explicitly.

**Independent Test**: The named oversized segments are each replaced by multiple smaller registry
segments; the oracle sweep proves verdict identity over all fixtures before and after.

**Acceptance Scenarios**:

1. **Given** `_seg_0285` at 1,351 lines, **When** the split lands, **Then** it is replaced by
   per-check segments following the established per-statement split method, and the ordered
   verdict stream over every fixture is unchanged.
2. **Given** the other multi-concern oversized segments (`_seg_0286`, `_seg_0562`, `_seg_0543`,
   `_seg_0106`, and any others past the clause-12 threshold), **When** the feature completes,
   **Then** each is either split the same way or carries an inline annotation explaining why it
   must remain one body.

---

### Edge Cases

- A segment's length comes mostly from its keyword-parameter signature (the dataflow model binds
  every read name as a parameter), not from logic. Size judgments use logic units per clause 12,
  not raw lines - the signature does not count against the segment.
- A segment that is long but genuinely single-concern (one check name, one cohesive computation)
  is clause-12-legitimate; it gets an annotation, not a forced split.
- Standalone invocation (`python check_village.py <manifest>`) must keep working in some form
  after the file becomes a package; whatever the new invocation is, every doc that names the old
  one is updated.
- The registry's order IS the legacy execution order; a thematic file grouping must not be allowed
  to perturb registry order.
- Circular imports between the new subfiles (helpers needed by segments, segments needed by the
  registry, driver needing both) must be designed away, not patched with local imports.
- The `_assert_not_main_tree` import-time guard must keep firing for package-based runs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The constitution's Python Discipline principle MUST gain a clause stating: a source
  file past roughly 1,000 lines prompts the question of whether it should become a package of
  subfiles; the split target is a directory-module whose CLAUDE.md indexes the subfiles and says
  when to load each; the recorded motivation is token economy (a session pays context-window
  tokens for the whole file to use any part of it). The clause MUST note the same
  over-fragmentation caution as clause 12 - the threshold is an ask-the-question line, not a
  mechanical mandate.
- **FR-002**: The constitution version MUST be bumped (minor: new guidance added) with its sync
  impact header updated per the constitution's own governance rules.
- **FR-003**: `check_village.py` MUST become a `check_village/` package: shared
  helpers/types/constants, thematically-grouped segment files, a registry module holding
  `GATE_SEGMENTS` in exactly the legacy order, and the `gate()` driver, with the public API
  (`gate`, `load`, and every name currently imported by tests/tools) preserved via the package
  `__init__`.
- **FR-004**: The package MUST carry a `CLAUDE.md` index listing every subfile with a "look here
  when" line, per the slim-index/load-on-demand doc pattern.
- **FR-005**: Gate verdicts MUST be proven identical before/after: the ordered verdict stream
  over every pool manifest and every regression fixture matches the pre-split capture exactly
  (oracle-sweep method from features 022/023).
- **FR-006**: `gate(M, only=...)` targeted execution and the targeted regression replay MUST
  work identically after the split (same closure semantics, verdicts identical to full run).
- **FR-007**: `_seg_0285__wells_clear_of_shrine_and_torii` MUST be split into per-check segments
  using the established per-statement split method, with oracle identity proof.
- **FR-008**: Every other gate segment past the clause-12 threshold in logic units MUST be either
  split the same way or annotated inline with why it remains one body; the feature records the
  census and each disposition.
- **FR-009**: All callers MUST be updated: test modules, regen/tooling scripts, the diagram
  skill's CLAUDE.md/SKILL.md/settlements docs, and any command lines they quote.
- **FR-010**: No file in the new package may itself exceed the FR-001 threshold without an inline
  justification comment (the registry module, if its rows alone exceed it, justifies itself as
  ordered data, not logic).
- **FR-011**: The `waterfields.py` engine builders (`build_comb`, `build_polder`, `_carve`) are
  explicitly OUT of scope as deep-but-cohesive engine functions per clause 12; this disposition
  MUST be recorded in the feature's research notes (and, if they lack one, a clause-12-style
  note where appropriate) rather than silently skipped.

### Key Entities

- **Constitution clause 13**: the file-size rule; sibling of clause 12 (function size).
- **check_village/ package**: the split gate - helpers, segment files, registry, driver, CLAUDE.md.
- **GATE_SEGMENTS registry**: ordered tuple of segment rows; order is the execution contract.
- **Oracle capture**: pre-split recording of every fixture's ordered verdict stream; the identity
  proof compares post-split runs against it.
- **Segment census**: list of segments over the size threshold with per-segment disposition
  (split vs annotated).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A session needing one check's code loads a file a fraction of the old size - no
  segment file in the package exceeds ~4,000 lines (vs 35,602 today), and the median segment file
  is under ~2,500 lines.
- **SC-002**: Verdict identity: 100% of pool manifests and regression fixtures produce
  byte-identical ordered verdict streams before and after the split.
- **SC-003**: The full quality gate (lint, format, strict typing, tests, 100% coverage on pure
  logic) passes on the new package.
- **SC-004**: Zero oversized-without-annotation functions remain in the package: every segment is
  under the clause-12 threshold in logic units or carries an inline justification.
- **SC-005**: The regression replay's targeted-run speedup is preserved (same order of magnitude
  as the ~58 s serial baseline; no regression back toward the ~480 s full-gate cost).
- **SC-006**: The constitution documents the file-size practice and the package's CLAUDE.md
  indexes every subfile - a reader can find "where do well checks live?" from the index alone.

## Assumptions

- The feature-022/023 tooling and method (segment transformer, oracle sweeps, dataflow model in
  specs/022's research.md R9) are the proven way to split segments and prove identity; this
  feature reuses that method rather than inventing a new one.
- "Roughly 1,000 lines" for files is deliberately a raw-line heuristic (unlike clause 12's
  logic-unit measure for functions) because the motivating cost - context-window tokens - scales
  with raw text, not logic density.
- The registry module and generated/registry-like data files justify exceeding the threshold as
  ordered data; the CLAUDE.md index notes this.
- Thematic grouping follows contiguous registry ranges where possible (keeps the split script
  simple and files aligned with execution order); theme names come from the dominant check-name
  prefixes in each range.
- `settlement.py` (15,993 lines) and other large files are NOT split in this feature - the rule
  makes them ask-the-question candidates for future features; this feature establishes the
  pattern with the largest offender. Recorded so it is a decision, not an oversight.
- The GM handles no part of this; the session runs specify -> plan -> tasks -> implement
  unattended per the project's spec-kit doctrine.
