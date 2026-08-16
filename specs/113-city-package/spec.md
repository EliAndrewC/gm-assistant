# Feature Specification: settlement/city.py -> settlement/city/ Package Split

**Feature Branch**: none - this project stays on `main` (CLAUDE.md, GM 2026-07-27). Active feature
is declared with `export SPECIFY_FEATURE=113-city-package`.

**Created**: 2026-08-16

**Status**: Implemented 2026-08-16

**Input**: User description: "Split `.claude/skills/diagram/settlement/city.py` (1,582 lines, the
largest non-test source file in the /diagram skill) into a `settlement/city/` sub-package,
following the exact shape feature 112 gave `settlement/fields/`. Two stages kept separate per
feature 112 research R5: a pure move, then per-method decomposition. Stage 3 is the token-scale
index. The oracle is byte-identity of every regenerated `pool/` and `wip/` artifact. A concurrent
peer session is reorganizing the diagram skill, so the delete/modify collision documented in
feature 112 research R14 is expected."

## Why this file, and why now

`city.py` is 1,582 raw lines - past the ~1,000-line bar in constitution Principle X clause 13,
whose stated cost is context-window tokens: a session that needs one subsystem pays for all five.
It is also the only file in the skill that scores high on BOTH halves of the current refactor
effort, holding the three largest functions in the whole engine (`city_wall` at 339 lines,
`channel_footbridges` at 195, `farmland_ring` at 121).

The timing argument is independent of the size argument. The migration plan puts the city/capital
tier at the active conversion frontier, and `future-work.md` #2 (fabric-first generation) is aimed
explicitly at "the next city-tier map" - a feature whose whole subject is rewriting wall sizing,
i.e. the inside of `city_wall`. Splitting first means that feature loads ~490 lines instead of
1,582. `settlement/CLAUDE.md` also records that the uncovered wings of the 94% coverage ratchet
live "mostly in `city.py`"; per-subsystem files make that floor legible instead of one opaque
number.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Behavior-preserving package split (Priority: P1)

A session that needs to change how city walls are drawn opens one file of about 490 lines instead
of a 1,582-line file covering walls, moats, canals, waterfront and bridges. Nothing about what the
engine draws changes: every map already in `pool/` regenerates to byte-identical
output, and no consumer of `settlement` changes a line.

**Why this priority**: this is the whole clause-13 debt. It is independently shippable - if the
feature stopped here, the token cost that motivated it is already paid, and the decomposition in
US2 becomes optional cleanup rather than a blocker.

**Independent Test**: regenerate every scripted map in a scratch copy of the tree and diff the
artifact hashes against a baseline captured the same way from the PRE-split tree. The committed
manifests are deliberately not the baseline - feature 110 research R3 proved them unreliable for
this, because the engine may have drifted since they were committed, and a mismatch would then be
indistinguishable from a refactor bug. An empty diff, a clean `git status` under `pool/`, and a
green `make done` with `settlement/core.py` byte-unchanged prove it end to end.

**Acceptance Scenarios**:

1. **Given** the pre-split baseline hashes of every `pool/**` artifact, **When** the
   split lands and every scripted map regenerates, **Then** the hash diff is empty.
2. **Given** the split has landed, **When** `git diff --stat -- settlement/core.py` runs,
   **Then** it prints nothing - the composed `CityMixin` kept the bases line identical.
3. **Given** an existing test that patches `settlement.Settlement.city_wall`, **When** the suite
   runs after the split, **Then** it passes unmodified - class-level patching is unaffected.
4. **Given** the package exists, **When** `settlement/city.py` is looked for, **Then** it is gone -
   a stale module beside a package of the same name is a shadowing hazard.

---

### User Story 2 - Oversized methods decomposed (Priority: P2)

A reader of `city_wall` sees a short sequence of named steps - derive the arc, seat the gates, lay
the towers, draw the walk - instead of 339 lines of inline geometry. Each extracted step is
independently readable and independently testable.

**Why this priority**: real, but strictly downstream of US1. It is also the risky half: the
engine's randomness is positional and scoped, so an extraction that moves a `random` call relative
to another silently changes every downstream coordinate. Separating it from the move is what makes
a red sweep name its own cause (feature 112 research R5).

**Independent Test**: after EACH method's decomposition, the byte-identity sweep is re-run on its
own and must come back empty. No function is left over ~150 lines without an inline justification
at its `def`.

**Acceptance Scenarios**:

1. **Given** `city_wall` has been decomposed, **When** the sweep runs, **Then** the artifact diff
   is empty - no draw was reordered.
2. **Given** every method over the bar is decomposed, **When** function sizes are measured across
   the package, **Then** nothing exceeds ~150 lines without a one-line justification comment.
   (Measured after the fact: two methods were over the bar, not the five the spec guessed - see
   research R10, which records why the other three were measured and left whole.)
3. **Given** a decomposition changed nothing observable, **When** `GEN_TIME_BUDGETS` in
   `test_villages.py` runs unmodified, **Then** it passes - extraction did not move a per-gen CPU
   budget.

---

### User Story 3 - Token-scale package index (Priority: P3)

A session that knows what it needs ("where do sluice gates live?") resolves the file from an index
without opening a source file, the same way `check_village/`, `hamletgen/`, `waterfields/` and
`settlement/fields/` already work.

**Why this priority**: the split only pays its token dividend if the reader can find the right
submodule cheaply. Small, and depends only on US1.

**Independent Test**: a reader given any named city concern - wall towers, moat sluices, towpaths,
log booms, footbridges - resolves it to one file from `settlement/CLAUDE.md` and
`settlement/city/CLAUDE.md` alone.

**Acceptance Scenarios**:

1. **Given** the two index files, **When** a reader looks up any of the 27 moved methods' subjects,
   **Then** exactly one submodule row claims it.
2. **Given** the split has landed, **When** `settlement/CLAUDE.md`'s "Look here when" table is
   read, **Then** the single `city.py` row has been replaced by rows resolving to the new
   submodules, noting the package has its own sub-index.

---

### Edge Cases

- **A peer session patches `city.py` while it is being deleted.** Git reports `DU` (deleted by us,
  modified by them), which cannot auto-resolve and leaves no conflict markers to edit - their fix
  simply has nowhere to land, and the failure mode is resolving it by taking the deletion and
  silently dropping their work. Feature 112 research R14 records the resolution: port their
  post-merge method bodies into whichever submodule now owns them, and prove the port by
  regenerating every live map against THEIR just-committed manifests rather than by running tests.
  This is the reason US1 is a pure move and lands on its own: a peer's patch merges into a move
  almost mechanically and into a rewrite by hand.
- **An extraction moves an RNG draw.** Positional/scoped randomness means the artifacts change
  everywhere downstream while every test still passes. Only the byte-identity sweep catches it,
  which is why US2 sweeps after each method rather than at the end.
- **`governor_mansion` (21 lines) is a topical orphan** at the tail of the file. The design pass
  found the deciding fact: its body calls `self.manor(...)` and re-keys the record out of
  `M["manors"]`, so it is a STRUCTURE reusing the manor glyph, not city infrastructure. It gets its
  own one-method `civic.py` rather than being buried in a module whose index row would then be a
  lie - a one-method module is a smell, but a mislabeled module is a defect. Relocating it into
  `settlement/castle_civic.py` where it topically belongs is recorded as a follow-up and stays out
  of scope here (research R1).
- **Coverage floor moves.** Splitting redistributes the uncovered city/capital wings across five
  files. The combined `settlement/` ratchet must not fall; if the achievable figure rises, the
  floor rises with it and never falls.
- **Generated import headers over-import.** A mechanical transformer copies the source file's
  import block into every submodule; unused-import fallout is expected and is lint-fixed, not
  hand-curated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The 27 members of `CityMixin` MUST be redistributed into six submodules under
  `settlement/city/`, grouped by subsystem, with each submodule under ~1,000 raw lines.
- **FR-002**: `settlement/core.py` MUST be byte-unchanged - a composed `CityMixin` in
  `settlement/city/__init__.py` preserves the single import and the `class Settlement(...)` bases
  line.
- **FR-003**: A guard test MUST assert the composed `CityMixin` exposes exactly the pre-split name
  set, that no two sub-mixins define the same name, and that every name resolves on `Settlement`
  itself. The guard MUST be proven to fail before it is trusted - once by deleting a method, once
  by duplicating one into a second sub-mixin.
- **FR-004**: Every regenerated artifact under `pool/**` MUST be byte-identical to the
  pre-split baseline, after the move and after each decomposition.
- **FR-005**: `git status --porcelain` under `pool/` MUST print nothing after each sweep.
- **FR-006**: `settlement/city.py` MUST be deleted, not left beside the package.
- **FR-007**: Every moved method MUST keep its `self: "Settlement"` annotation and each submodule
  MUST carry the `TYPE_CHECKING` import of `Settlement` with the two-dot relative path.
- **FR-008**: Decomposition MUST preserve code order, RNG draw order and float-operation order
  exactly, and MUST proceed one method at a time with a sweep between.
- **FR-009**: No function in the package may exceed ~150 lines without an inline one-line
  justification at its `def`.
- **FR-010**: `settlement/city/CLAUDE.md` MUST exist as a "Look here when" index in the style of
  the four existing package indexes, and MUST record any method whose placement is
  counter-intuitive so nobody "fixes" it back.
- **FR-011**: `settlement/CLAUDE.md`'s table MUST resolve the new submodules and point at the
  sub-index.
- **FR-012**: The combined `settlement/` coverage floor MUST NOT be lowered; if the achievable
  figure rises, the floor is raised to match with the new measurement recorded beside it.
- **FR-013**: Prose in the skill naming the FILE `settlement/city.py` MUST be updated to the
  package. Importable-path references and prior `specs/NNN` artifacts stay verbatim as historical
  record.
- **FR-014**: US1 MUST land as its own commit, ahead of any US2 work, so a later bisect can
  separate the move from the decomposition - and so the peer session's merge stays mechanical.

### Key Entities

- **`CityMixin`**: the single class being carved. 27 methods today, no class-level constants; after the split, a composed
  class in `__init__.py` whose bases are the six sub-mixins.
- **Submodule**: one subsystem's file - a sub-mixin class, its `TYPE_CHECKING` block, and the
  imports its own methods actually use.
- **Baseline**: the hash set of every `pool/**` artifact regenerated in a scratch copy of the
  pre-split tree. The feature's only real oracle. `wip/shiro-daika.gen.py` is deliberately
  EXCLUDED per feature 112 research R11 - it ran over 6 minutes without output against roughly 3
  minutes for the whole pool, and every city method it reaches is already exercised by the four
  provincial-city maps. An oracle earns its place by the failures it can catch, and this one runs
  seven times over the feature.
- **Sweep**: a regenerate-and-diff run against the baseline. Runs after the move and after each
  decomposition.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No file in `settlement/city/` exceeds 1,000 raw lines; the largest is under 600.
- **SC-002**: A session needing one city subsystem loads at most ~40% of the lines it loads today.
- **SC-003**: Every scripted map in `pool/` regenerates byte-identically - a zero-line
  hash diff - after the move and after every decomposition.
- **SC-004**: Zero consumer files change: `settlement/core.py` and every caller outside
  `settlement/city/` are byte-unchanged apart from the two index documents.
- **SC-005**: No function in the package exceeds ~150 lines without a written justification; the
  largest function in the skill is no longer in this package.
- **SC-006**: The guard test has been observed failing for both a missing name and a duplicated
  name, with the failure text recorded.
- **SC-007**: `make done` is green, and the combined `settlement/` coverage figure is at or above
  its pre-split floor.
- **SC-008**: Any city concern is resolvable to one file from the two index documents without
  opening source.

## Assumptions

- **Grouping follows existing method order.** The five subsystems appear contiguously in the
  current file with no interleaving, so the partition is a set of slices rather than a scatter.
  This is what makes a mechanical transformer safe; a scattered partition would not be.
- **Feature 112's transformer is adaptable rather than rewritten.** `split_fields.py` already
  carves a class into sub-mixins by class-body statement, slicing from the previous node's end so
  decorators, blank lines and comment blocks above a member travel with it. Feature 113 changes its
  partition table and paths.
- **`git status` clean under `pool/` is meaningful** because the scripted maps' artifacts are
  committed - that is what makes main's own manifests usable as the fixed point.
- **The peer reorganization does NOT collide at the file level, but it moves this feature's
  tooling.** The heads-up sent to the "Diagram reorganize" session was answered (2026-08-16): that
  session touches nothing under `settlement/`, so the `DU` delete/modify collision anticipated from
  feature 112 research R14 will not occur. What its tip DOES change is three paths this feature
  uses - `test_settlement/` becomes `tests/settlement/` with package-qualified helper imports, the
  loose top-level modules become packages that must run as `python3 -m pipeline.regen` /
  `python3 -m tools.why_placed`, and `tests/` is pruned from `gencache.engine_files()` and
  `render_cache.engine_fingerprint()`. This feature therefore SYNCS IN AFTER that push and builds
  on its tip, and every path in plan.md, quickstart.md and tasks.md is written post-reorg. The
  peer verified on its own tip that `settlement/fields/` stays inside `engine_files()` and that the
  coverage globs stayed glob-shaped, so a nested `settlement/city/` is walked and measured exactly
  as `fields/` is - no cache or coverage plumbing falls to this feature.
- **The coverage floor stays this feature's to raise.** The peer left `SETTLEMENT_COV_FLOOR` at 94
  deliberately, on the reasoning that raising a ratchet inside an unrelated refactor makes a future
  failure hard to attribute. FR-012 therefore owns it.
- **Main is still the coordination point.** The reply above is a courtesy that happened to arrive;
  research R14's rule stands - cross-session messages can expire unapproved, and the merge is where
  collisions are actually resolved. The structural mitigation (land the pure move fast and alone)
  is kept regardless.
- **`governor_mansion` stays in the package** for this feature. Relocating it to `structures.py` or
  `castle_civic.py` is a topical judgment that would make the move impure.
- **No new behavior, no new checks.** This feature adds one guard test and no gate segments; the
  189-check gate and the cohort sweep are used as-is, as regression detectors.

## Out of Scope

- Relocating `governor_mansion` out of the city package.
- Any change to what the engine draws, including the wall-sizing rewrite that `future-work.md` #2
  contemplates. This feature exists to make that feature cheap, not to start it.
- Splitting the other seven files over 1,000 lines (`structures.py`, `_geom.py`, `rolling.py`,
  `land.py`, `shrines_wells.py`, `civic_grounds.py`, and the eleven `check_village/segments_*`
  files). Each is its own feature; `structures.py` is the recommended next one.
- Raising or restructuring the coverage ratchet beyond keeping it from falling.
