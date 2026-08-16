# Feature Specification: settlement/civic_grounds.py -> settlement/civic_grounds/ Package Split

**Feature Branch**: none - this project stays on `main` (CLAUDE.md, GM 2026-07-27). Active feature
is declared with `export SPECIFY_FEATURE=115-civic-grounds-package`.

**Created**: 2026-08-16

**Status**: Implemented 2026-08-16. Final per-file line counts: `civic.py` 267, `stable_yard.py` 264,
`funerary.py` 228, `justice.py` 193, `lodging.py` 187, `_yardctx.py` 173, `__init__.py` 36
(1,162 -> largest 267). Longest function in the package **85** lines, down from 335 - so the engine's
largest function is now `rolling.py::roll_village` at 256. Every `pool/` artifact byte-identical
across all 28 generators, after the move AND again after the decomposition; `core.py` byte-unchanged;
zero consumer files changed. One deviation: FR-005's `wip/shiro-daika` run was cut as unbounded (see
research R11) and is NOT satisfied.

**Input**: User description: "Refactor `.claude/skills/diagram/settlement/civic_grounds.py` (1,162
lines) into a `settlement/civic_grounds/` package of focused submodules with its own `CLAUDE.md`
index, following the `settlement/fields/` (112), `settlement/city/` (113) and
`settlement/structures/` (114) exemplars and constitution Principle X clause 13 plus clause 14. Two
motivations: TOKENS - it is the worst remaining grab bag in `settlement/`, four unrelated
subsystems in one mixin; and ENGINEERING - `_stable_yard` is 335 lines, the largest function
anywhere in the engine, and must be decomposed into named sub-stages whose dated GM-decision
comments survive verbatim. Behavior-preserving: byte-identical manifests, the gate green, the
regression corpus still firing, zero consumer changes."

## Why this file, and why now

`civic_grounds.py` is 1,162 raw lines, past the ~1,000-line bar in constitution Principle X clause
13, whose stated cost is context-window tokens.

It is **not** the largest file left in `settlement/` - `_geom.py` (1,303), `rolling.py` (1,197),
`land.py` (1,187) and `shrines_wells.py` (1,179) are all bigger. It is chosen anyway, on the same
*cost per read* argument feature 114 made against the *size* argument, and here the case is
stronger on two independent axes:

**Breadth.** Its row in `settlement/CLAUDE.md` is the longest in that index, and it earns the
length: the file is four unrelated subsystems bolted into one mixin - funerary ground, judicial
ground, civic and commercial works, and lodging with its livestock yards. A session changing where
a cemetery may sit loads the inn, the granary, the merchant residences and 335 lines of stable-yard
scatter to do it. The four files above are each *one* subsystem that happens to be long: `_geom.py`
is 84 pure geometry helpers, `rolling.py` is one homestead solver, `land.py` is the land surfaces,
`shrines_wells.py` is sacred ground and wells. Long is cheaper to live with than miscellaneous,
because a long cohesive file is one you meant to open.

**One function is 29% of the file.** `_stable_yard` is 335 lines - the largest function anywhere in
the engine, 79 lines clear of the runner-up (`rolling.py::roll_village`, 256) and more than double
the ~150-line bar feature 112 settled on. This is the axis on which `civic_grounds.py` is not
merely the worst grab bag but the worst file, full stop, and it is why this feature runs the
decomposition stage that feature 114 explicitly deferred.

The decomposition is also *ready* in a way the others are not: `_stable_yard`'s own banner comments
already name its seams (the tight footprint keep-out; "1. BEATEN-EARTH scuff + STRAW litter";
"2. FURNITURE" greedy seating; the road-parallel edge rail; the interior rails with bounded
retries; the WATERING POINT; the "1-2 DUNG HEAPS"). Feature 111 used exactly this signal - "the
file's own STAGE banner comments already mark the seams" - to justify decomposing `hamletgen.py`.

Every one of those blocks carries a dated GM-decision comment recording researched grounding: why a
wagon-train yard shows two or three rails rather than one, why troughs cluster at a well instead of
at the rail, why a yard with no reachable well digs its own, why the dung-heap clearance was raised
from 15 px to 24 px after two rounds of GM review. That is the largest concentration of
record-the-why prose in the engine, and it is currently buried inside a function no one will open
casually. Decomposition into named stages is what makes it findable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Behavior-preserving package split (Priority: P1)

A session that needs to change where a cemetery may sit opens one file of about 225 lines instead
of a 1,162-line file that also covers punishment grounds, granaries, merchant residences, inns and
stable-yard scatter. Nothing the engine draws changes: every map already in `pool/` regenerates to
byte-identical output, and no consumer of `settlement` changes a line.

**Why this priority**: this is the clause-13 debt, and it is independently shippable. If the
feature stopped here the token cost that motivated it is already paid, and the remaining stories
become improvements rather than blockers.

**Independent Test**: regenerate every scripted map in a scratch copy of the tree and diff artifact
hashes against a baseline captured the same way from the PRE-split tree. The committed manifests
are deliberately not the baseline - feature 110 research R3 proved them unreliable for this,
because the engine may have drifted since they were committed and a mismatch would then be
indistinguishable from a refactor bug. An empty hash diff, a clean `git status` under `pool/`, and
a green `make done` with `settlement/core.py` byte-unchanged prove it end to end.

**Acceptance Scenarios**:

1. **Given** the pre-split baseline hashes of every `pool/**` artifact, **When** the split lands and
   every map regenerates, **Then** the hash diff is empty.
2. **Given** the split has landed, **When** `git diff --stat -- settlement/core.py` runs, **Then**
   it prints nothing - the composed `CivicGroundsMixin` kept the bases line identical.
3. **Given** `precinct_interior` calls `self.cemetery`, and the split puts those two in DIFFERENT
   submodules, **When** a map that draws a precinct runs, **Then** the call resolves unchanged
   through the composed class.
4. **Given** the package exists, **When** `settlement/civic_grounds.py` is looked for, **Then** it
   is gone - a stale module beside a package of the same name is a shadowing hazard.
5. **Given** `settlement/structures/compounds.py` calls `self._ward_fence_cap(...)` and
   `settlement/trades.py` calls `self._way_bearing_near(...)`, **When** they run after the split,
   **Then** neither needs an edit - both names still resolve on `Settlement` through the MRO.

---

### User Story 2 - The move is proven complete, not asserted (Priority: P2)

A guard test holds that the composed surface still exposes every one of the 22 pre-split members
and that no two sub-mixins define the same name. Every assertion is proven to FAIL before it is
trusted.

**Why this priority**: feature 112's `fields/` guard caught the shape of bug this exists for, and
this story must land WITH the move. A member silently dropped by the transformer produces a package
that imports cleanly, type-checks cleanly and draws nothing, surfacing only when whichever
generator calls it happens to run. A name defined twice produces a working import, a clean
`mypy --strict` and one silently dead implementation, because the MRO just picks the first base.

**Independent Test**: delete a method from one sub-mixin and observe the guard name it; define one
name in two sub-mixins and observe the collision half fire.

**Acceptance Scenarios**:

1. **Given** the 22-name pre-split census, **When** any member is missing from the composed class,
   **Then** the guard fails naming it.
2. **Given** two sub-mixins both defining `_way_bearing_near`, **When** the suite runs, **Then** the
   collision assertion fails naming the duplicate.
3. **Given** all 22 names, **When** the guard runs, **Then** each is asserted to resolve on
   `Settlement` itself, not merely on its own sub-mixin.

---

### User Story 3 - The 335-line stable yard becomes readable stages (Priority: P3)

A session that needs to change how a hitching rail avoids a neighboring yard's dung heap reads a
named function about that, not line 1,080 of a 335-line method. The seven stages the banner
comments already describe become seven named functions, and every dated GM-decision comment moves
with the code it explains, verbatim.

**Why this priority**: this is the second stated motivation and the reason this file beat the four
larger ones. It is last of the substantive stories because it is the only stage that carries
behavior-change risk, so it must run against a package that has already proven byte-identical -
that way a hash mismatch has exactly one possible cause.

**Independent Test**: the same byte-identity oracle, re-run after decomposition alone. Because the
yard's scatter, furniture seating and heap placement all draw from a seeded RNG, any reordering of
RNG consumption changes output - so an empty hash diff is a strong proof that the extraction was
faithful, not merely a proof that it compiled.

**Acceptance Scenarios**:

1. **Given** the decomposed `stable_yard.py`, **When** every map regenerates, **Then** the hash diff
   against the post-US1 baseline is empty - RNG draw order is unchanged.
2. **Given** any of the seven banner-comment blocks, **When** it is searched for after
   decomposition, **Then** it is present verbatim, attached to the stage function it documents.
3. **Given** the decomposed module, **When** its longest function is measured, **Then** it is under
   the ~150-line bar feature 112 settled on.
4. **Given** `tests/settlement/test_civic_grounds.py`'s existing stable-yard tests (which drive the
   yard through `flush_stable_yards`), **When** the suite runs after decomposition, **Then** they
   pass unmodified - the decomposition is internal to a private method.

---

### User Story 4 - The package is navigable without reading it (Priority: P4)

A session arriving at `settlement/civic_grounds/` reads a `CLAUDE.md` index that says which
submodule holds what and loads exactly one. The index also records the placement decisions a
reader would otherwise re-litigate.

**Why this priority**: the split only pays off if the reader can pick the right file without
opening several. Features 112, 113 and 114 all shipped this and all three indexes are load-bearing
today. It is last because it is docs-only and depends on the final shape.

**Independent Test**: a reader given a task ("change how a mausoleum yields to a ward fence") can
name the file to open from the index alone, without grepping.

**Acceptance Scenarios**:

1. **Given** `settlement/civic_grounds/CLAUDE.md`, **When** a reader looks for any of the 22
   members, **Then** exactly one row of the "look here when" table covers it.
2. **Given** `settlement/CLAUDE.md`, **When** a reader reaches the `civic_grounds` row, **Then** it
   points at the sub-index rather than listing the five modules' contents inline - the same shape
   the `fields/`, `city/` and `structures/` rows already have.

---

### Edge Cases

- **A member assigned to no module, or to two.** The transformer must REFUSE rather than write a
  partial package - a silently dropped method is the failure mode US2 exists for, and it is
  cheapest to catch at transform time.
- **A helper that a cross-file census calls dead.** `_way_seat_near` has zero consumers outside
  `civic_grounds.py` and looks deletable to any grep that excludes the defining file - but
  `_way_bearing_near` calls it, one line, inside the file. It stays. Any clause-14 dead-member pass
  in this feature MUST count intra-file callers, and this instance is the worked example.
- **A comment block written ABOVE a method.** In this project that is usually researched grounding,
  and slicing by `node.lineno` drops it. The transformer slices `(previous member's end + 1 .. this
  member's end)`, which carries decorators, blank lines and the comment block.
- **The two-dot import path.** Submodules move one level deeper, so `from ._geom import ...`
  becomes `from .._geom import ...`, and the same for `._knobs`. Feature 113 found a LAZY in-body
  `from .core import Settlement` that silently resolved to a non-existent module when only the
  header was rewritten; the body rewrite stays in the transformer.
- **RNG draw order under decomposition (US3).** Extracting a stage that consumes the yard's seeded
  RNG changes nothing only if it is called at the same point with the same preceding draws. This is
  the one way this feature can break a map while passing every type check, and the byte-identity
  oracle is what catches it.
- **`precinct_interior`'s only consumer is `wip/shiro-daika.gen.py`.** Features 112 and 114
  excluded that map from the byte-identity sweep on cost (research R11 measured it at over 6
  minutes against ~3 for the whole pool). Excluding it here would leave a moved member with no
  artifact-level proof at all, so it gets ONE run rather than a routine one.
- **The frozen legacy pool.** `pipeline/regen.py` prints `FROZEN` and skips the hand-authored maps,
  so the baseline and the post-split sweep both need `--frozen-ok`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The 22 members of `CivicGroundsMixin` MUST be partitioned across exactly five
  submodules of a `settlement/civic_grounds/` package, with every member in exactly one.
- **FR-002**: `settlement/core.py` MUST be byte-unchanged - `CivicGroundsMixin` keeps its name, its
  import path (`from .civic_grounds import CivicGroundsMixin`) and its position in the
  `class Settlement(...)` base list.
- **FR-003**: A guard test MUST hold that the composed `CivicGroundsMixin` exposes every one of the
  22 pre-split names (as a SUBSET assertion, so adding a member later needs no bookkeeping), that
  no two sub-mixins define the same name, and that all 22 resolve on `Settlement` itself. Each
  assertion MUST be observed failing before it is trusted.
- **FR-004**: Every regenerated `pool/**` artifact (`.json`, `.svg`, `.png`) MUST be byte-identical
  to a baseline captured from the pre-split tree by the same command, with the frozen legacy maps
  INCLUDED (`--frozen-ok`).
- **FR-005**: `wip/shiro-daika.gen.py` MUST be regenerated and hash-compared at least once, because
  it is the sole consumer of `precinct_interior`.
- **FR-006**: Each submodule MUST carry `if TYPE_CHECKING: from ..core import Settlement` and every
  method MUST keep its `self: "Settlement"` annotation, so `mypy --strict` resolves cross-subsystem
  attribute access with no runtime import cycle.
- **FR-007**: `settlement/civic_grounds.py` MUST be deleted once the package exists.
- **FR-008**: `_stable_yard` MUST be decomposed into named stage functions, none exceeding ~150
  lines, matching the seven seams its own banner comments already mark.
- **FR-009**: Every dated GM-decision comment inside `_stable_yard` MUST survive verbatim, attached
  to the stage it documents. A decomposition that summarizes or relocates one of them away from its
  code fails this requirement.
- **FR-010**: The decomposition MUST NOT change the order in which the yard consumes its seeded RNG,
  proven by an empty hash diff rather than by inspection.
- **FR-011**: `settlement/civic_grounds/CLAUDE.md` MUST index the five submodules with a "look here
  when" row each, and `settlement/CLAUDE.md`'s `civic_grounds` row MUST point at it rather than
  listing contents inline.
- **FR-012**: The index MUST record, at the point of the decision, the three placements a future
  reader would otherwise re-litigate: why `_ward_fence_cap` sits with the funerary grounds rather
  than with the ward fences in `water_ways.py`; why `precinct_interior` sits in the civic-works
  module rather than with the shrines; and why `_stable_yard` gets a module to itself.
- **FR-013**: The transformer MUST refuse (non-zero exit, naming the members) when its partition
  does not exactly cover the class, and when it meets an unnamed class-body member.
- **FR-014**: `make done` MUST be green, including the settlement coverage ratchet floor - which
  MUST NOT be lowered.
- **FR-015**: Zero files outside `settlement/` MAY change behavior. A consumer that asserts on the
  source FILENAME (as `tests/tools/test_why_placed.py` did in feature 114) is the one permitted
  exception and MUST be updated with a comment saying which split moved it.

### Key Entities

- **`CivicGroundsMixin`**: the composed surface. After the split it lives in
  `settlement/civic_grounds/__init__.py` and has no members of its own - it exists ONLY to preserve
  `core.py`'s single import and its position in the base list, so the partition can be re-cut later
  without touching `core.py`.
- **The five submodules**, each with its own sub-mixin:

  | module | mixin | members | ~lines |
  |---|---|---|---|
  | `funerary.py` | `FuneraryGroundsMixin` | `cemetery`, `_ward_fence_cap`, `mausoleum`, `cremation_ground`, `ossuary` | 225 |
  | `justice.py` | `JusticeGroundsMixin` | `punishment_spot`, `execution_ground`, `boundary_marker` | 195 |
  | `civic.py` | `CivicWorksMixin` | `precinct_interior`, `district`, `terrace`, `granary`, `merchant_storehouses`, `merchant_residences` | 260 |
  | `lodging.py` | `LodgingMixin` | `flophouse`, `inn`, `stables`, `animal_ground`, `flush_stable_yards`, `_way_bearing_near`, `_way_seat_near` | 185 |
  | `stable_yard.py` | `StableYardMixin` | `_stable_yard` and its seven decomposed stages | 380 |
  | `__init__.py` | `CivicGroundsMixin` | composition only | 40 |

- **The seven stable-yard stages**, taken from the function's own banner comments: the tight
  footprint keep-out (including the farrier's forge, which stands ON the yard by design); the
  beaten-earth scuff and straw litter scatter; the greedy furniture seater with its tip-and-edge
  probes; the road-parallel edge rail; the one-or-two interior rails with bounded retries; the
  watering point (trough cluster hugging a well, or digging the yard's own well when none is
  reachable); and the one-or-two dung heaps with their map-wide rail clearance.
- **The byte-identity oracle**: `sha256sum` over every `pool/**` artifact, captured from a scratch
  copy of the pre-split tree and again after each stage, both via
  `pipeline/regen.py --no-cache --frozen-ok`. It runs TWICE - once after the move (US1) and once
  after the decomposition (US3) - so a mismatch names which stage caused it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No source file in `settlement/civic_grounds/` exceeds 400 raw lines.
- **SC-002**: A session working on one civic-grounds subsystem loads at most ~400 lines where it
  previously loaded 1,162 - at least a 66% reduction on the worst case, and over 80% for the
  funerary, justice and lodging subsystems.
- **SC-003**: Every regenerated map artifact is byte-identical to its pre-split baseline, after the
  move AND again after the decomposition.
- **SC-004**: The longest function in the package is under 150 lines, down from 335 - so the
  engine's largest function after this feature is `rolling.py::roll_village` at 256.
- **SC-005**: `make done` is green with the coverage ratchet floor unchanged.
- **SC-006**: Both halves of the composed-surface guard are demonstrated red before being trusted.
- **SC-007**: No file outside `settlement/` changes behavior.

## Assumptions

- **Three stages, not two.** Unlike feature 114, this feature runs the per-method decomposition
  stage, because `_stable_yard` at 335 lines is more than double the ~150-line bar feature 112
  settled on and is the largest function in the engine. It runs AFTER the pure move and is
  hash-verified separately, so the two kinds of risk never mix.
- **The existing test file is not split.** `tests/settlement/test_civic_grounds.py` is 489 lines,
  well under the clause-13 bar. Features 112, 113 and 114 all left their mirrors as single files.
  Tests get no exemption from clause 13, but neither do they get pre-emptive splitting.
- **`_ward_fence_cap` follows its internal caller.** It is called by `mausoleum` inside this file
  and by `structures/compounds.py` outside it. Placement follows the caller within the package
  being cut, per feature 113's `_ring_upslope` precedent; the external consumer reaches it through
  the composed class either way.
- **`precinct_interior` stays in the package.** It draws a temple precinct's interior program and
  its natural eventual home is a religious-ground module that does not exist yet (`shrines_wells.py`
  is the nearest). Moving a member between PARENT-level mixins is a different change with different
  risk, and folding it in would make the byte-identity oracle answer two questions at once. It gets
  a row in `civic.py` and a note, exactly as feature 114 did with `road` and `pasture`.
- **`_way_seat_near` is live and stays.** The pre-spec cross-file census reported it as having zero
  consumers; that census excluded the defining file, and `_way_bearing_near` calls it. No clause-14
  deletion happens in this feature.
- **No class-level attributes to carry.** Unlike `structures.py` (which had three), all 22 members
  of `CivicGroundsMixin` are functions, so the guard's census has no non-method half to cover.
- The session works in its clone under `.clones/` and syncs to main's tip before starting; the spec
  number is claimed by pushing `specs/115-civic-grounds-package/` the moment `spec.md` exists
  (CLAUDE.md, concurrent-sessions protocol).
