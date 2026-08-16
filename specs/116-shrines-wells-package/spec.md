# Feature Specification: settlement/shrines_wells.py -> settlement/shrines_wells/ Package Split

**Feature Branch**: none - this project stays on `main` (CLAUDE.md, GM 2026-07-27). Active feature
is declared with `export SPECIFY_FEATURE=116-shrines-wells-package`.

**Created**: 2026-08-16

**Status**: Draft

**Input**: User description: "Please refactor shrines_wells.py in accordance with our file size and
token count restrictions." Split `settlement/shrines_wells.py` (1,179 lines) into a
`settlement/shrines_wells/` package with its own `CLAUDE.md` index, following the method of features
112 (`fields/`), 113 (`city/`) and 114 (`structures/`): a one-shot AST transformer that moves whole
class-body members verbatim (comments and decorators included), sub-mixins composed into an
unchanged `ShrinesWellsMixin` so `settlement/core.py` stays byte-identical, a composed-surface guard
test proven red before it is trusted, and a pool-wide byte-identity oracle sweep.

## Why this file, and why now

`shrines_wells.py` is 1,179 raw lines - past the ~1,000-line bar in constitution Principle X clause
13, whose stated cost is context-window tokens.

It is not the largest file left in `settlement/`: `_geom.py` (1,303), `rolling.py` (1,197) and
`land.py` (1,187) are all bigger, and all remain debt (see Assumptions). `shrines_wells.py` is
nonetheless the right file to cut first, on the cost-per-read axis clause 13 actually names:

- **It is the most heterogeneous.** `_geom.py` is one thing (pure geometry helpers, no `self`),
  `rolling.py` is one thing (the homestead-bundle solver), `land.py` is one thing (land surfaces).
  `shrines_wells.py` is **six unrelated subsystems** whose only common ancestor is feature 025's
  slicing: religious halls, torii avenues, the whole well subsystem, a general-purpose seat-finding
  API, draft-animal byres, and woodland tree stands. Its own name concedes this - it is the only
  module in the package named with an `and`.
- **The read pattern proves it.** A session changing the torii avenue's threshold rule
  (`_avenue_at_threshold`, 34 lines) currently loads the three-grid well index, the frozen-terrain
  scope, the farm-well cluster cover, the byre shed and the canopy stand - about 1,100 lines of
  which it needs none. The well subsystem alone is 447 lines and is loaded by every reader of the
  file.
- **The heaviest documentation in the engine lives here**, which multiplies the token cost.
  `_well_ground_clear`, `well_at`, `frozen_terrain` and `_hall_caption_y` carry long researched
  grounding blocks (the 45-minute-grind post-mortem, the 30 px-vs-`ftpx` reservation table, the
  caption-vs-sando ordering). That documentation is correct and must be preserved verbatim - it is
  also why this file costs more per line than its neighbors.

The timing argument is independent of the size argument. The skill's own `CLAUDE.md` names two open
engine jobs that land squarely in this file: the wellhead-reservation defect recorded inside
`well_at` (the 30 px box that means ~30 real ft on a hamlet and ~90 on a city), and the capital's
"cannot seat a wellhead" blocker under "The collision circle is now blocking FEATURES". Both are
well-siting work. Splitting first means each loads ~300 lines instead of 1,179.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Behavior-preserving package split (Priority: P1)

A session that needs to change where wells are sited opens one file of about 300 lines instead of a
1,179-line file that also holds shrines, torii avenues, byres, the open-seat API and the woods.
Nothing about what the engine draws changes: every map already in `pool/` regenerates to
byte-identical output, and no consumer of `settlement` changes a line of behavior.

**Why this priority**: this is the whole clause-13 debt. It is independently shippable - if the
feature stopped here the token cost that motivated it is already paid, and the index in US3 becomes
optional polish rather than a blocker.

**Independent Test**: regenerate every pool generator in a scratch copy of the tree and diff the
artifact hashes against a baseline captured the same way from the PRE-split tree. The committed
manifests are deliberately not the baseline (feature 110 research R3: the engine may have drifted
since they were committed, so a mismatch would be indistinguishable from a refactor bug). An empty
diff, a clean `git status` under `pool/`, and a green `make done` with `settlement/core.py`
byte-unchanged prove it end to end.

**Acceptance Scenarios**:

1. **Given** the pre-split baseline hashes of every `pool/**` artifact, **When** the split lands and
   every map regenerates, **Then** the hash diff is empty.
2. **Given** the split has landed, **When** `git diff --stat -- settlement/core.py` runs, **Then**
   it prints nothing - the composed `ShrinesWellsMixin` kept the bases line identical.
3. **Given** a pool generator that calls `s.well_at(...)`, `s.open_seat(...)`, `s.shrine_hall(...)`
   or `s.draft_byres(...)` directly, **When** it runs after the split, **Then** it needs no edit -
   those names still resolve on `Settlement` through the MRO.
4. **Given** an engine module outside the package that calls a PRIVATE member of it
   (`water_ways.py`, `civic_grounds.py` and `structures/compounds.py` all call
   `self._assert_walls_clear_of_torii`; `civic_grounds.py` calls `self._well_vr` and
   `self._well_ground_clear`; `core.py` and `finish.py` call `self.flush_tree_stands`), **When** the
   suite runs after the split, **Then** none of them changes - a cross-submodule call resolves
   through the composed `Settlement` with no import.
5. **Given** the package exists, **When** `settlement/shrines_wells.py` is looked for, **Then** it is
   gone - a stale module beside a package of the same name is a shadowing hazard.

---

### User Story 2 - The move is proven complete, not asserted (Priority: P2)

A guard test holds that the composed surface still exposes every pre-split member and that no two
sub-mixins define the same name. Every assertion is proven to FAIL before it is trusted.

**Why this priority**: this must land WITH the move rather than after it. A member silently dropped
by the transformer produces a package that imports cleanly, type-checks cleanly, and draws nothing -
surfacing only when whichever generator calls it happens to run. A name defined twice produces a
working import, a clean `mypy --strict`, and one silently dead implementation, because MRO just picks
the first base. This file has an unusually high private-member ratio (24 of 38 members are
`_`-prefixed, and 13 of those have no consumer outside the class), which is exactly the population a
careless partition drops without any other test noticing.

**Independent Test**: delete a method from one sub-mixin and observe the guard name it; define one
name in two sub-mixins and observe the collision half fire.

**Acceptance Scenarios**:

1. **Given** the 38-name pre-split census, **When** any member is missing from the composed class,
   **Then** the guard fails naming it.
2. **Given** two sub-mixins both defining `_well_vr`, **When** the suite runs, **Then** the collision
   assertion fails naming the duplicate.
3. **Given** the guard's census reads `vars(cls)` rather than filtering on `callable`, **When** a
   future class-level constant is added to a sub-mixin, **Then** it is covered without a second test
   (feature 114's shape; this class has no class-level attribute today, and the census must not
   assume that stays true).

---

### User Story 3 - The package is navigable without reading it (Priority: P3)

A session arriving at `settlement/shrines_wells/` reads a `CLAUDE.md` index that says which submodule
holds what, and loads exactly one. The index also records the decisions a reader would otherwise
re-litigate: why the general-purpose `open_seat` sits in a module of its own, why the byres are here
at all, why `shrine_well` is filed with the wells rather than the shrines, and which submodule is the
package's hub.

**Why this priority**: the split only pays off if the reader can pick the right file without opening
several. Features 112, 113 and 114 all shipped this and all three indexes are load-bearing today. It
is last because it is docs-only and depends on the final shape.

**Independent Test**: a reader given a task ("hold the torii avenue short of a wall") can name the
file to open from the index alone, without grepping.

**Acceptance Scenarios**:

1. **Given** `settlement/shrines_wells/CLAUDE.md`, **When** a reader looks for any of the 38 members,
   **Then** exactly one row of the "look here when" table covers it.
2. **Given** `settlement/CLAUDE.md`, **When** a reader reaches the `shrines_wells` row, **Then** it
   points at the sub-index rather than listing the seven modules' contents inline - the same shape
   the `fields/`, `city/` and `structures/` rows already have.

---

### Edge Cases

- **A member assigned to no module, or to two.** The transformer must REFUSE rather than write a
  partial package - a silently dropped method is the failure mode US2 exists for, and it is cheapest
  to catch at transform time.
- **An unnamed class-body member.** `ShrinesWellsMixin` has none today (census: 38 members, all
  `FunctionDef`, no class-level `Assign`), but the transformer refuses on one rather than dropping
  it.
- **A DECORATED member.** `frozen_terrain` carries `@contextlib.contextmanager`, which `ast` reports
  ABOVE the `def` line. Slicing by `node.lineno` would drop the decorator and produce a plain
  generator function that every `with self.frozen_terrain():` call site then fails on. The
  transformer's slice - `(previous member's end + 1 .. this member's end)` - carries it, and this is
  the first split in the lineage where a decorator is actually present, so it gets its own
  acceptance check.
- **A comment block written ABOVE a method.** In this project that is usually researched grounding,
  and slicing by `node.lineno` drops it. The same slice rule carries it; the post-split check counts
  comment lines lost and must report zero.
- **The one-dot import path.** Submodules move one level deeper, so `from ._geom import ...` becomes
  `from .._geom import ...`. Feature 113 found a LAZY in-body `from .core import Settlement` that
  silently resolved to a non-existent module when only the header was rewritten; this file has no
  in-body import today, but the body rewrite stays in the transformer.
- **The frozen legacy pool.** `pipeline/regen.py` prints `FROZEN` and skips the 19 hand-authored
  maps, so both sweeps need `--frozen-ok`. For THIS feature they carry most of the diagnostic power:
  `farm_wells`, `small_shrine`, `torii_even`, `forest` and the town/city `shrine_hall` paths are
  exercised almost entirely by legacy maps, while the live scripted cohort is hamlets.
- **A consumer that asserts on the FILENAME.** Feature 114 had one (`tests/tools/test_why_placed.py`
  names `structures.py`). A census must be run for this file's name rather than assumed absent, and
  any hit is a legitimate consumer change.
- **A concurrent sibling split.** Feature 115 (`civic_grounds.py`) is running in another session and
  touches the same two shared files - `settlement/CLAUDE.md`'s table and
  `tests/settlement/CLAUDE.md`. Each edits its own row, so the merge is line-disjoint; the sync-in
  before each stop-work ritual is what keeps it that way.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The 38 members of `ShrinesWellsMixin` MUST be partitioned across exactly seven
  submodules of a `settlement/shrines_wells/` package, with every member in exactly one, and source
  order preserved within each submodule.
- **FR-002**: `settlement/core.py` MUST be byte-unchanged - `ShrinesWellsMixin` keeps its name, its
  import path (`from .shrines_wells import ShrinesWellsMixin`) and its position in the
  `class Settlement(...)` base list.
- **FR-003**: A guard test MUST hold that the composed `ShrinesWellsMixin` exposes every one of the
  38 pre-split names (as a SUBSET assertion, so adding a member later needs no bookkeeping), that no
  two sub-mixins define the same name, and that all 38 resolve on `Settlement` itself. Each
  assertion MUST be observed failing before it is trusted.
- **FR-004**: Every regenerated `pool/**` artifact (`.json`, `.svg`, `.png`) MUST be byte-identical
  to a baseline captured from the pre-split tree by the same command, with the frozen legacy maps
  INCLUDED (`--frozen-ok`).
- **FR-005**: Each submodule MUST carry `if TYPE_CHECKING: from ..core import Settlement` and every
  method MUST keep its `self: "Settlement"` annotation, so `mypy --strict` resolves cross-subsystem
  attribute access with no runtime import cycle.
- **FR-006**: `settlement/shrines_wells.py` MUST be deleted once the package exists.
- **FR-007**: `settlement/shrines_wells/CLAUDE.md` MUST index the seven submodules with a "look here
  when" row each, name the package's hub, and `settlement/CLAUDE.md`'s `shrines_wells` row MUST point
  at it rather than listing contents inline.
- **FR-008**: The index MUST record, at the point of the decision, the four placements a future
  reader would otherwise re-litigate: `open_seat`+`_footprint_clear` isolated in `seats.py` with
  their intended eventual destination; `_draw_byre`+`draft_byres` isolated in `byres.py` with theirs;
  `shrine_well` filed with the wells rather than the shrines; and `_hall_caption_y` filed with the
  halls rather than with the torii geometry it reads.
- **FR-009**: The transformer MUST refuse (non-zero exit, naming the members) when its partition does
  not exactly cover the class, when a member is assigned twice, and when it meets an unnamed
  class-body member.
- **FR-010**: `make done` MUST be green, including the `SETTLEMENT_COV_FLOOR` ratchet - which MUST
  NOT be lowered. A pure move changes no executable line, so combined package coverage is
  arithmetically unchanged.
- **FR-011**: Every comment line in the pre-split class body MUST survive somewhere in the package
  (checked mechanically, not by eye) - the researched grounding in this file is the bulk of its
  value.
- **FR-012**: `tests/settlement/test_shrines_wells.py` MUST keep its name and its test count - the
  mirror rule in `tests/settlement/CLAUDE.md` maps a test file to a `settlement/` module, and at 474
  lines the file is well under the clause-13 bar (see Assumptions).

### Key Entities

- **`ShrinesWellsMixin`**: the composed surface. After the split it lives in
  `settlement/shrines_wells/__init__.py` and has no members of its own - it exists ONLY to preserve
  `core.py`'s single import and its position in the base list, so the partition can be re-cut later
  without touching `core.py`.
- **The seven submodules**, each with its own sub-mixin (member counts and line spans from the AST
  census; `~lines` is the body slice, before each module's pruned import header):

  | module | mixin | members | ~lines |
  |---|---|---|---|
  | `shrines.py` | `ShrineHallsMixin` | `hill`, `shrine`, `small_shrine`, `_hall_caption_y`, `shrine_hall` | 230 |
  | `torii.py` | `ToriiAvenueMixin` | `_assert_walls_clear_of_torii`, `_avenue_pitch`, `_avenue_at_threshold`, `_avenue_short_of_walls`, `_torii`, `torii_path`, `torii_even` | 179 |
  | `wellground.py` | `WellGroundMixin` | `_build_well_index`, `_terrain_fingerprint`, `frozen_terrain`, `_well_index`, `_wet_toe_keepout`, `_well_ground_clear`, `_in_scrub_cover` | 172 |
  | `wells.py` | `WellsMixin` | `_well_vr`, `well`, `farm_wells`, `_farm_wells`, `well_at`, `place_wells`, `_place_wells`, `shrine_well` | 275 |
  | `seats.py` | `OpenSeatMixin` | `_footprint_clear`, `open_seat` | 69 |
  | `byres.py` | `DraftByresMixin` | `_draw_byre`, `draft_byres` | 54 |
  | `woods.py` | `TreeStandsMixin` | `_tree_stand`, `flush_tree_stands`, `_draw_stand`, `_stand_fringe`, `_crowns`, `_fringe_blocked`, `forest` | 166 |

- **The byte-identity oracle**: `sha256sum` over every `pool/**` artifact, captured from a scratch
  copy of the pre-split tree and again after, both via `python3 -m pipeline.regen --no-cache
  --frozen-ok pool/*/*.gen.py`. `wip/shiro-daika.gen.py` is excluded (feature 112 research R11: over
  6 minutes against ~3 for the whole pool, exercising no member the three provincial cities do not).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No source file in `settlement/shrines_wells/` exceeds 320 raw lines - a largest file
  about a quarter of the pre-split 1,179.
- **SC-002**: A session working on one subsystem here loads at most ~320 lines where it previously
  loaded 1,179 - a reduction of at least 72% on the worst case, and over 90% for the seat API and
  the byres.
- **SC-003**: Every regenerated map artifact is byte-identical to its pre-split baseline (hash diff
  empty across all pool maps, frozen legacy maps included), with the sweep's exit code and
  REGENERATED count part of the pass condition.
- **SC-004**: `make done` is green with the coverage ratchet floor unchanged.
- **SC-005**: `settlement/core.py` is byte-unchanged and no pool generator, `wip/` script or engine
  module outside the package changes at all.
- **SC-006**: Both halves of the composed-surface guard are demonstrated red before being trusted.
- **SC-007**: Zero comment lines from the pre-split class body are lost.

## Assumptions

- **One stage, not two.** Features 112 and 113 each ran a pure move followed by a per-method
  decomposition stage; 114 skipped decomposition because its largest member was under the ~150-line
  bar. This file's largest members are `shrine_hall` (114 lines), `_farm_wells` (89),
  `_well_ground_clear` (53) and `_place_wells` (52) - all under that bar. Decomposing them is not
  this feature's debt, and doing it here would put behavior-changing risk inside a move whose whole
  value is that it changes nothing.
- **`shrines_wells.py` is cut before the three larger files.** `_geom.py` (1,303), `rolling.py`
  (1,197) and `land.py` (1,187) are all past clause 13's bar and all remain debt - recorded here so
  the next session inherits the list rather than rediscovering it. They are deliberately NOT in this
  feature's scope: each is a single coherent subsystem, so each needs its own partition research, and
  bundling several splits into one oracle sweep would make a byte-identity failure ambiguous about
  which split caused it.
- **`open_seat` and `_footprint_clear` stay in the package.** Both are misfiled at the *parent*
  level - a general "where can this feature stand?" API whose natural home is `houses.py`, beside the
  `_fits` it delegates to - but moving a member between parent-level mixins is a different change
  with different risk, and folding it in would make the byte-identity oracle answer two questions at
  once. They get an isolated module so the eventual move is a one-file change, exactly as feature 113
  did with `governor_mansion` and 114 with `road`/`pasture`.
- **The byres stay too, for the same reason.** A draft-animal byre is a homestead appurtenance and
  belongs with `homestead_parts.py`. Isolated in `byres.py` rather than moved.
- **`shrine_well` is filed with the wells.** It is a well - it delegates to `well_at`'s test and
  records an `M['wells']` entry with `shrine=True` - placed for a shrine. The naming pulls toward
  `shrines.py`; the code and its consumers do not.
- **`_hall_caption_y` is filed with the halls.** It reads torii geometry, but its single consumer is
  `shrine_hall` and its subject is the hall's caption. Placement follows the caller (feature 113's
  `_ring_upslope` precedent, 114's door probes).
- **The existing test file is not split.** `tests/settlement/test_shrines_wells.py` is 474 lines,
  well under the clause-13 bar, and features 112/113/114 all left their mirror test file whole
  (`test_fields.py` 589, `test_city.py` 754, `test_structures.py` 692). Tests get no exemption from
  clause 13, but neither do they get pre-emptive splitting.
- The session works in its clone under `.clones/diagram-hamlet` and synced to main's tip before
  starting; the spec number is claimed by pushing `specs/116-shrines-wells-package/` the moment
  `spec.md` exists (CLAUDE.md, concurrent-sessions protocol). 115 was taken by a peer session
  mid-write, which is exactly the case the claim-in-main protocol exists for.
