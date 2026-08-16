# Feature Specification: settlement/structures.py -> settlement/structures/ Package Split

**Feature Branch**: none - this project stays on `main` (CLAUDE.md, GM 2026-07-27). Active feature
is declared with `export SPECIFY_FEATURE=114-structures-package`.

**Created**: 2026-08-16

**Status**: Draft

**Input**: User description: "Split `.claude/skills/diagram/settlement/structures.py` (1,459 lines,
now the largest non-test source file in the /diagram skill) into a `settlement/structures/`
sub-package, following the exact shape features 112 (`settlement/fields/`) and 113
(`settlement/city/`) gave their subsystems. Stage 1 is a PURE MOVE with a one-shot transformer
adapted from `split_city.py`; stage 2 is the composed-surface guard test proven red first; stage 3
is the token-scale `CLAUDE.md` index. The oracle is byte-identity of every regenerated `pool/` and
`wip/` artifact."

## Why this file, and why now

`structures.py` is 1,459 raw lines - past the ~1,000-line bar in constitution Principle X clause
13, whose stated cost is context-window tokens. With `fields/` (feature 112) and `city/` (feature
113) split, it is now **the largest non-test source file in the skill**, and it is the worst
offender on the *cost per read* axis rather than merely the size axis: its 33 members cover seven
unrelated subsystems, so a session that needs one of them pays for all seven.

That breadth is what distinguishes this file from its two predecessors. `fields.py` was one
subsystem cut four ways and `city.py` one tier cut six ways; `structures.py` is a **catch-all** -
feature 025's residue bucket for anything that was neither field, nor way, nor homestead. The
practical evidence is the read pattern: a session touching the notice-board siter (`place_kosatsuba`,
110 lines) also loads the manor glyph, the merchant estate, the whole urban palette, the servant
nagaya pass, both packing engines, the road, and the pasture - about 1,300 lines of which it needs
none.

The timing argument is independent of the size argument. The skill's own `CLAUDE.md` names the
**next substantial engine job** as the placer's rotated-footprint fix (CENTER vs FOOTPRINT item 3,
then item 2's `sat_overlap` swap). That work lands almost entirely in the placement machinery -
`pack`, `rowpack`, `try_building`, `open_face_rot`, and the door probes - which is exactly what
this split isolates into `packing.py`, `urban.py` and `servants.py`. Splitting first means that
feature loads ~300 lines instead of 1,459.

`settlement/CLAUDE.md` also records that the uncovered wings of the 94% coverage ratchet live
partly in `structures.py`. Per-subsystem files make that floor legible - the town/city wings
(`servant_ranges`, `rowpack`, the drum tower) separate from the tiers that are already covered.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Behavior-preserving package split (Priority: P1)

A session that needs to change how urban buildings are packed opens one file of about 300 lines
instead of a 1,459-line file covering compounds, roads, pastures, the urban palette, servant
ranges, packing, caption probes and public fixtures. Nothing about what the engine draws changes:
every map already in `pool/` and `wip/` regenerates to byte-identical output, and no consumer of
`settlement` changes a line of behavior.

**Why this priority**: this is the whole clause-13 debt. It is independently shippable - if the
feature stopped here, the token cost that motivated it is already paid, and the index in US2
becomes optional polish rather than a blocker.

**Independent Test**: regenerate every scripted map in a scratch copy of the tree and diff the
artifact hashes against a baseline captured the same way from the PRE-split tree. The committed
manifests are deliberately not the baseline - feature 110 research R3 proved them unreliable for
this, because the engine may have drifted since they were committed, and a mismatch would then be
indistinguishable from a refactor bug. An empty diff, a clean `git status` under `pool/`, and a
green `make done` with `settlement/core.py` byte-unchanged prove it end to end.

**Acceptance Scenarios**:

1. **Given** the pre-split baseline hashes of every `pool/**` and `wip/**` artifact, **When** the
   split lands and every scripted map regenerates, **Then** the hash diff is empty.
2. **Given** the split has landed, **When** `git diff --stat -- settlement/core.py` runs, **Then**
   it prints nothing - the composed `StructuresMixin` kept the bases line identical.
3. **Given** an existing test that patches `settlement.Settlement.building`, **When** the suite
   runs after the split, **Then** it passes unmodified - class-level patching is unaffected.
4. **Given** the package exists, **When** `settlement/structures.py` is looked for, **Then** it is
   gone - a stale module beside a package of the same name is a shadowing hazard.
5. **Given** a pool generator that calls `s._dims(...)`, `s.try_building(...)` or
   `s.open_face_rot(...)` directly, **When** it runs after the split, **Then** it needs no edit -
   those names still resolve on `Settlement` through the MRO.

---

### User Story 2 - The package is navigable without reading it (Priority: P2)

A session arriving at `settlement/structures/` reads a `CLAUDE.md` index that says which submodule
holds what, and loads exactly one. The index also records the decisions a reader would otherwise
re-litigate: why `road` and `pasture` sit in a module of their own, why the four door/solid probes
live with `servant_ranges` rather than with `building`, and how the caption probes here relate to
`place_caption` in `castle_civic.py`.

**Why this priority**: the split only pays off if the reader can pick the right file without
opening several. Features 112 and 113 both shipped this and both indexes are load-bearing today.

**Independent Test**: a reader given a task ("change how the notice board picks its verge") can
name the file to open from the index alone, without grepping.

**Acceptance Scenarios**:

1. **Given** `settlement/structures/CLAUDE.md`, **When** a reader looks for any of the 33 members,
   **Then** exactly one row of the "look here when" table covers it.
2. **Given** `settlement/CLAUDE.md`, **When** a reader reaches the `structures` row, **Then** it
   points at the sub-index rather than listing the seven modules' contents inline - the same shape
   the `fields/` and `city/` rows already have.

---

### User Story 3 - The move is proven complete, not asserted (Priority: P3)

A guard test holds that the composed surface still exposes every pre-split member and that no two
sub-mixins define the same name. Both halves are proven to FAIL before they are trusted.

**Why this priority**: feature 112's `fields/` guard caught the shape of bug this exists for. A
member silently dropped by the transformer produces a package that imports cleanly, type-checks
cleanly, and draws nothing - and surfaces only when whichever generator calls it happens to run. A
name defined twice produces a working import, a clean `mypy --strict`, and one silently dead
implementation, because MRO just picks the first base.

**Independent Test**: delete a method from one sub-mixin and observe the guard name it; define one
name in two sub-mixins and observe the collision half fire.

**Acceptance Scenarios**:

1. **Given** the 33-name pre-split census, **When** any member is missing from the composed class,
   **Then** the guard fails naming it.
2. **Given** two sub-mixins both defining `_dims`, **When** the suite runs, **Then** the collision
   assertion fails naming the duplicate.
3. **Given** the three class-level attributes (`URBAN`, `SERVANT_RANGE_DEPTH_FT`,
   `_OFFICE_STANDOFF`), **When** the guard runs, **Then** they are covered too - the surface census
   must not be methods-only, because feature 112's `features.py` proved class-body constants move
   as deliberately as methods and a method-only guard cannot see them.

---

### Edge Cases

- **A member assigned to no module, or to two.** The transformer must REFUSE rather than write a
  partial package - a silently dropped method is the failure mode US3 exists for, and it is
  cheapest to catch at transform time.
- **An unnamed class-body member** (a bare docstring, a conditional, a `for`). `StructuresMixin`
  has none today (census: 33 members, 30 `FunctionDef` + 3 `Assign`), but the transformer refuses
  on one rather than dropping it.
- **A comment block written ABOVE a method.** In this project that is usually researched grounding,
  and slicing by `node.lineno` drops it. The transformer slices `(previous member's end + 1 .. this
  member's end)`, which carries decorators, blank lines and the comment block.
- **The one-dot import path.** Submodules move one level deeper, so `from ._geom import ...`
  becomes `from .._geom import ...`. Feature 113 found a LAZY in-body `from .core import Settlement`
  that silently resolved to a non-existent module when only the header was rewritten;
  `structures.py` has no in-body import today, but the body rewrite stays in the transformer.
- **The frozen legacy pool.** `pipeline/regen.py` prints `FROZEN` and skips the 19 hand-authored
  maps, so the baseline and the post-split sweep both need `--frozen-ok` to exercise them. A sweep
  that silently skipped them would be an oracle that cannot see most of the engine.
- **A consumer that asserts on the FILENAME.** `tests/tools/test_why_placed.py` asserts
  `"structures.py"` appears in the traced call frames. The split renames that frame's file; the
  assertion must move to the new module name, and that is a legitimate consumer change rather than
  a violation of "no consumer changes".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The 33 members of `StructuresMixin` MUST be partitioned across exactly seven
  submodules of a `settlement/structures/` package, with every member in exactly one.
- **FR-002**: `settlement/core.py` MUST be byte-unchanged - `StructuresMixin` keeps its name, its
  import path (`from .structures import StructuresMixin`) and its position in the
  `class Settlement(...)` base list.
- **FR-003**: A guard test MUST hold that the composed `StructuresMixin` exposes every one of the
  33 pre-split names (as a SUBSET assertion, so adding a member later needs no bookkeeping), that
  no two sub-mixins define the same name, and that all 33 resolve on `Settlement` itself. Each
  assertion MUST be observed failing before it is trusted.
- **FR-004**: Every regenerated `pool/**` and `wip/**` artifact (`.json`, `.svg`, `.png`) MUST be
  byte-identical to a baseline captured from the pre-split tree by the same command.
- **FR-005**: Each submodule MUST carry `if TYPE_CHECKING: from ..core import Settlement` and every
  method MUST keep its `self: "Settlement"` annotation, so `mypy --strict` resolves cross-subsystem
  attribute access with no runtime import cycle.
- **FR-006**: `settlement/structures.py` MUST be deleted once the package exists.
- **FR-007**: `settlement/structures/CLAUDE.md` MUST index the seven submodules with a "look here
  when" row each, and `settlement/CLAUDE.md`'s `structures` row MUST point at it rather than listing
  contents inline.
- **FR-008**: The index MUST record, at the point of the decision, the three placements a future
  reader would otherwise re-litigate: `road`+`pasture` in `ground.py` with each member's intended
  eventual destination; the four door/solid probes with `servant_ranges` rather than with
  `building`; and the relationship between `captions.py`'s probes and `castle_civic.py`'s
  `place_caption`.
- **FR-009**: The transformer MUST refuse (non-zero exit, naming the members) when its partition
  does not exactly cover the class, and when it meets an unnamed class-body member.
- **FR-010**: `make done` MUST be green, including the `SETTLEMENT_COV_FLOOR` ratchet - which MUST
  NOT be lowered. A pure move changes no executable line, so combined package coverage is
  arithmetically unchanged.
- **FR-011**: The one consumer assertion that names the source FILE
  (`tests/tools/test_why_placed.py`) MUST be updated to the new module filename, with a comment
  saying which split moved it - the same note the 025 split left.

### Key Entities

- **`StructuresMixin`**: the composed surface. After the split it lives in
  `settlement/structures/__init__.py` and has no members of its own - it exists ONLY to preserve
  `core.py`'s single import and its position in the base list, so the partition can be re-cut later
  without touching `core.py`.
- **The seven submodules**, each with its own sub-mixin:

  | module | mixin | members | ~lines |
  |---|---|---|---|
  | `compounds.py` | `CompoundsMixin` | `manor`, `_estate_wall_clear`, `merchant_estate`, `merchant_estates` | 254 |
  | `ground.py` | `GroundMixin` | `road`, `pasture` | 72 |
  | `urban.py` | `UrbanBuildingMixin` | `URBAN`, `building`, `_dims`, `try_building`, `_face_street_rot`, `open_face_rot` | 159 |
  | `servants.py` | `ServantRangesMixin` | `SERVANT_RANGE_DEPTH_FT`, `_OFFICE_STANDOFF`, `_solid_records`, `_blocks_any_door`, `_door_is_clear`, `_office_records`, `servant_ranges` | 196 |
  | `packing.py` | `PackingMixin` | `rowpack`, `pack`, `_shortfall` | 274 |
  | `captions.py` | `CaptionProbesMixin` | `label_blockers`, `label_caption_hw`, `label_seat_clear`, `clear_label_seat`, `_under_a_caption` | 84 |
  | `fixtures.py` | `PublicFixturesMixin` | `theater_stage`, `fire_tower`, `kosatsuba`, `place_kosatsuba`, `place_punishment_spot`, `drum_tower` | 385 |

- **The byte-identity oracle**: `sha256sum` over every `pool/**` and `wip/**` artifact, captured
  from a scratch copy of the pre-split tree and again after, both via
  `pipeline/regen.py --no-cache --frozen-ok`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No source file in `settlement/structures/` exceeds 450 raw lines, and the package's
  largest file is under a third of the pre-split file.
- **SC-002**: A session working on one structures subsystem loads at most ~450 lines where it
  previously loaded 1,459 - a reduction of at least 69% on the worst case, and over 90% for the
  caption probes and the ground surfaces.
- **SC-003**: Every regenerated map artifact is byte-identical to its pre-split baseline (hash diff
  is empty across all scripted maps).
- **SC-004**: `make done` is green with the coverage ratchet floor unchanged.
- **SC-005**: Exactly one consumer file outside `settlement/` changes, and its change is a filename
  string, not behavior.
- **SC-006**: Both halves of the composed-surface guard are demonstrated red before being trusted.

## Assumptions

- **Two stages, not three.** Features 112 and 113 each ran a pure move followed by a per-method
  decomposition stage. This feature does the pure move and the index only: `structures.py`'s
  largest members are `rowpack` (130 lines), `servant_ranges` (128), `pack` (115) and
  `place_kosatsuba` (110) - all under the ~150-line bar feature 112 settled on, and none is a
  339-line `city_wall`. Decomposing them is not this feature's debt, and doing it here would put
  behavior-changing risk inside a move whose whole value is that it changes nothing. The placer
  rework the skill `CLAUDE.md` already prescribes will decompose `pack`/`rowpack` for its own
  reasons, against a file that is by then 300 lines.
- **`road` and `pasture` stay in the package.** Both are misfiled at the *parent* level - `road`
  belongs with `water_ways.py`'s ways, `pasture` with `land.py`'s land surfaces - but moving a
  member between parent-level mixins is a different change with different risk, and folding it into
  this one would make the byte-identity oracle answer two questions at once. They get an isolated
  module so each eventual move is a one-file change, exactly as feature 113 did with
  `governor_mansion` in `city/civic.py`.
- **The four door/solid probes follow their caller.** `_solid_records`, `_blocks_any_door`,
  `_door_is_clear` and `_office_records` read like general placement utilities, and a census
  confirms all four have exactly one consumer today: `servant_ranges` (`_solid_records` also
  serving `_door_is_clear`). Placement follows the caller, per feature 113's `_ring_upslope`
  precedent. If a second consumer appears they are trivially promoted.
- **The existing test file is not split.** `tests/settlement/test_structures.py` is 591 lines, well
  under the clause-13 bar, and the two predecessor features left `test_fields.py` (589) and
  `test_city.py` (754) as single files mirroring their packages. Tests get no exemption from clause
  13, but neither do they get pre-emptive splitting.
- The session works in its clone under `.clones/` and syncs to main's tip before starting; the spec
  number is claimed by pushing `specs/114-structures-package/` the moment `spec.md` exists (CLAUDE.md,
  concurrent-sessions protocol).
