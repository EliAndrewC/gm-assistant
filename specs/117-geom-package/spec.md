# Feature Specification: settlement/_geom.py -> settlement/_geom/ Package Split

**Feature Branch**: none - this project stays on `main` (CLAUDE.md, GM 2026-07-27). Active feature
is declared with `export SPECIFY_FEATURE=117-geom-package`.

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Please refactor _geom.py - which is over a thousand lines of code - to
comport to our documented conventions for function and file size." Split
`settlement/_geom.py` (1,303 lines) into a `settlement/_geom/` package with its own `CLAUDE.md`
index, following the method of features 112 (`fields/`), 113 (`city/`), 114 (`structures/`), 115
(`civic_grounds/`) and 116 (`shrines_wells/`), with the package surface re-exported by feature 027's
star-import idiom rather than a hand-maintained roster (Principle X clause 14).

## Why this file, and why now

`_geom.py` is 1,303 raw lines - past the ~1,000-line bar in constitution Principle X clause 13,
whose stated cost is context-window tokens. It has been the **largest file in `settlement/` since
the 025 split**, and feature 116's spec named it first on the outstanding list (`_geom.py` 1,303,
`rolling.py` 1,197, `land.py` 1,187). The three peers below it have since been narrowed by nothing,
so this is the top of that list, unchanged.

**The stated reason not to cut it first no longer survives contact with the file.** Feature 116
argued that `shrines_wells.py` was the right first cut because it was six subsystems while
"`_geom.py` is one thing (pure geometry helpers, no `self`)". That reading is true of the file's
CALLING CONVENTION and false of its CONTENTS. An 89-member census finds at least eight unrelated
populations sharing the file, and only three of them are geometry:

| what is in there | examples | lines |
|---|---|---|
| coordinate math | `point_in_poly`, `seg_dist`, `segments_cross`, `seg_intersect` | ~95 |
| footprint corners + collision/gap predicates | `sat_overlap`, `poly_gap`, `quad_hits_poly`, `_union_area` | ~175 |
| **spatial indexes and a mutation-versioned registry** | `PointGrid`, `Indexed`, `indexed_grid`, the `boxed_*` prefilters | ~245 |
| **a placement MEMO** | `SeatMemo` | ~105 |
| **caption typography policy** | the label standoff ladder, `HALL_CAPTION_FS`, `label_tilt`, `linear_tilt` | ~145 |
| **manifest readers** (the ways, the walls, the arches, the wet ground, the yard glyphs) | `lane_runs`, `wall_runs`, `torii_wall_conflicts`, `paddy_wet_rings`, `rail_quad` | ~415 |
| curve/organic-shape generation | `fillet_polyline`, `smooth_points`, `organic_bbox` | ~125 |
| **things that are not geometry at all** | the import-time main-tree guard, the land/crop palette, `village_population` | ~75 |

The manifest-reader group alone is a third of the file and is not geometry in the sense the others
are: it is the "placement and its check must read the SAME manifest source" doctrine made into
shared predicates, and it carries the researched grounding blocks that go with each rule (the plank
abutment research, the torii pitch ruling, the paddy-wet-ring reasoning, the ward arc-length
closure). A session changing the torii-vs-wall rule loads the `SeatMemo` post-mortem and the
`PointGrid` clamp story to get there.

**The read pattern proves the cost, the same way 116's did.** `_geom` is the most widely imported
module in the engine: **41 of the 47 files** under `settlement/`, plus `check_village`, `hamletgen`,
a pool gen and two `tools/` scripts, import from it. Almost none of them wants more than one of
the eight populations above - `trades.py` imports three label helpers, `homestead_parts.py` imports
five predicates, `rolling.py` imports eight - and today every one of those reads is a 1,303-line
file. That breadth is exactly why it is worth cutting: the split's saving is multiplied by the
number of distinct tasks that arrive here, and no module in this engine has more.

**Function size is separately checked and is already compliant.** The GM's phrasing names both
conventions. Clause 12 (functions stay at human scale, measured in logical statements) is satisfied
throughout: the largest member is `ward_interior` at 58 raw lines / 34 statements, and the biggest
classes (`SeatMemo` 98 raw lines, `Indexed` 81, `PointGrid` 63) are majority docstring. Nothing in
this file is near the "few hundred statements" suspicion bar, let alone the ~1,000 defect bar. So
this feature splits the FILE and deliberately decomposes no function - see Assumptions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Behavior-preserving package split (Priority: P1)

A session that needs to change the label standoff ladder, or the wellhead's drawn extent, or the
`PointGrid` cell clamp, opens one file of 250 lines or fewer instead of a 1,303-line file that also
holds the ward closure, the plank research, the organic-field jitter and the village population
roll. Nothing about what the engine draws changes: every map already in `pool/` regenerates to
byte-identical output, and no consumer of `settlement` changes a line.

**Why this priority**: this is the whole clause-13 debt. It is independently shippable - if the
feature stopped here the token cost that motivated it is already paid, and the index in US3 becomes
polish rather than a blocker.

**Independent Test**: regenerate every pool generator in a scratch copy of the tree and diff the
artifact hashes against a baseline captured the same way from the PRE-split tree. The committed
manifests are deliberately not the baseline (feature 110 research R3: the engine may have drifted
since they were committed, so a mismatch would be indistinguishable from a refactor bug). An empty
diff, a clean `git status` under `pool/`, and a green `make done` prove it end to end.

**Acceptance Scenarios**:

1. **Given** the pre-split baseline hashes of every `pool/**` artifact, **When** the split lands and
   every map regenerates, **Then** the hash diff is empty.
2. **Given** any of the 34 engine files that import from `_geom` (`from ._geom import ...`,
   `from .._geom import ...`), **When** the suite runs after the split, **Then** none of them
   changes - the package `__init__` re-exports the same names from the same import path.
3. **Given** an external consumer that imports the SUBMODULE path directly
   (`tools/scatter_audit.py` does: `from settlement._geom import boxed_grid, boxed_hit, ...`),
   **When** it runs after the split, **Then** it needs no edit.
4. **Given** a consumer that imports an underscore name (`settlement/__init__.py` re-exports
   `_assert_not_main_tree` and `_union_area`; `rolling.py` imports `_signed_area`;
   `structures/servants.py` imports `_aabb_gap`; `homestead_parts.py` imports `_union_area`),
   **When** the suite runs, **Then** it resolves - a star import does not carry underscore names, so
   each is re-exported explicitly by the aliased block.
5. **Given** the package exists, **When** `settlement/_geom.py` is looked for, **Then** it is gone -
   a stale module beside a package of the same name is a shadowing hazard.
6. **Given** the import-time main-tree guard, **When** any submodule of the package is imported from
   the MAIN `/gm-assistant` tree, **Then** it still raises `SystemExit` - importing
   `settlement._geom.overlap` runs the package `__init__` first, so the guard cannot be bypassed by
   reaching past it.

---

### User Story 2 - The move is proven complete, not asserted (Priority: P2)

A guard test holds that the package surface still exposes every pre-split name, and that no two
submodules bind the same public name to different objects. Every assertion is proven to FAIL before
it is trusted.

**Why this priority**: this must land WITH the move. A member silently dropped by the transformer
produces a package that imports cleanly, type-checks cleanly, and fails only when whichever caller
needs it happens to run. And the star-import re-export brings its own hazard, absent from features
112-116 because those composed a mixin: **a name bound in two submodules is silently shadowed by
whichever star import runs last**, with no error anywhere. That is precisely the property
`tests/check_village/test_surface.py` guards for feature 027's package, and this package needs the
same guard for the same reason.

**Independent Test**: delete a member from one submodule and observe the surface census name it;
bind one name in two submodules and observe the shadowing half fire.

**Acceptance Scenarios**:

1. **Given** the 89-name pre-split census, **When** any name is missing from `settlement._geom`,
   **Then** the guard fails naming it.
2. **Given** two submodules both defining `seg_dist`, **When** the suite runs, **Then** the
   shadowing assertion fails naming the duplicate.
3. **Given** the census is a SUBSET assertion, **When** a later helper is added to the package,
   **Then** no bookkeeping is required.
4. **Given** `settlement/__init__.py`'s own `from ._geom import X as X` roster, **When** the suite
   runs, **Then** every one of its 58 `_geom` names still resolves - which the surface census covers
   by construction, since that roster is a subset of the census.

---

### User Story 3 - The package is navigable without reading it (Priority: P3)

A session arriving at `settlement/_geom/` reads a `CLAUDE.md` index that says which submodule holds
what, and loads exactly one. The index also records the decisions a reader would otherwise
re-litigate: why the palette and the main-tree guard sit in a geometry package at all, why
`village_population` is isolated rather than moved, why the torii-vs-wall predicate is filed with
the walls, and what the layering rule between submodules is.

**Why this priority**: the split only pays off if the reader can pick the right file without opening
several. Features 112-116 all shipped this and all five indexes are load-bearing today. It is last
because it is docs-only and depends on the final shape.

**Independent Test**: a reader given a task ("stop a caption drifting off its subject", "make the
wellhead's drawn extent bigger") can name the file to open from the index alone, without grepping.

**Acceptance Scenarios**:

1. **Given** `settlement/_geom/CLAUDE.md`, **When** a reader looks for any of the 89 members,
   **Then** exactly one row of the "look here when" table covers it.
2. **Given** `settlement/CLAUDE.md`, **When** a reader reaches the `_geom` row, **Then** it points
   at the sub-index rather than listing the eleven modules' contents inline - the same shape the
   `fields/`, `city/`, `structures/`, `civic_grounds/` and `shrines_wells/` rows already have.
3. **Given** the index, **When** a reader asks which submodule may import which, **Then** the
   layering is stated (`base` <- `primitives` <- `overlap` <- everything else), so a future addition
   cannot introduce an import cycle by accident.

---

### Edge Cases

- **A member assigned to no module, or to two.** The transformer must REFUSE rather than write a
  partial package - a silently dropped helper is the failure mode US2 exists for, and it is cheapest
  to catch at transform time.
- **An unnamed module-level statement.** Unlike features 112-116 (which sliced a CLASS body of
  nothing but `def`s), this file's top level holds a bare call statement - `_assert_not_main_tree()`
  on line 35, the import-time guard. It has no name to key a partition on, and dropping it would
  silently disarm the guard while every test still passed inside a clone. The transformer folds an
  unnamed statement into the PRECEDING named member's block (so the call travels with its
  definition) and refuses if there is no preceding member.
- **A comment block written ABOVE a member.** In this project that is usually researched grounding,
  and this file is dense with it: the plank-abutment research, the torii pitch ruling, the label
  standoff ladder's calibration, the "A TORII STANDS CLEAR OF EVERY WALL" doctrine, the yard-glyph
  collision post-mortem. Slicing by `node.lineno` drops all of it. The
  `(previous node's end + 1 .. this node's end)` slice carries it, and the post-split check counts
  comment lines rather than trusting the rule.
- **A comment bank that names a POSITION in the old file.** Several banks say "below" or "above"
  about members that will land in a different module (the label ladder's "the ladder below", the
  torii doctrine's forward reference to `wall_runs()`, `box_gap`'s "the label standoff ladder
  below"). These are not dropped - they are the researched why - but their cross-references must be
  re-pointed at the module that now holds the referent. Every such edit is a comment-only edit and
  is listed in the tasks.
- **Underscore names and the star import.** `from .mod import *` does not carry `_name`. Six
  underscore members have consumers outside the package (`_assert_not_main_tree`, `_union_area`,
  `_signed_area`, `_aabb_gap`) or would lose the census's protection. They are re-exported by the
  `as`-alias idiom, exactly as `check_village/__init__.py` does for its six.
- **`from __future__` is absent and annotations are lazy.** `indexed_grid` annotates `-> PointGrid`
  ~140 lines BEFORE `PointGrid` is defined, which is legal only under Python 3.14's deferred
  annotation evaluation. The partition must not treat an annotation reference as a runtime
  dependency (it would invent an import cycle that does not exist), and must not treat a runtime
  reference as an annotation (it would omit a real one). Both names land in the same submodule here,
  which sidesteps it - but the layering rule in the index is what keeps the next addition honest.
- **The audit tool's file-shaped target.** `tools/cache_audit.py` mutates a numeric literal inside
  `TARGET = settlement/_geom.py`, chosen in feature 026 because it is the package module the live
  hamlets execute most. A directory cannot be read as text: leaving it would crash the audit exactly
  as the pre-025 target did (the comment above it records that incident). It must move to a
  submodule the live hamlets execute, and the choice must be measured rather than guessed.
- **The frozen legacy pool.** `pipeline/regen.py` prints `FROZEN` and skips the 19 hand-authored
  maps, so both oracle sweeps need `--frozen-ok`. They carry real diagnostic power here: the city
  and town wings exercise `ward_interior`, `wall_runs`, `torii_wall_conflicts`, `tower_quad` and
  `kido_bar_deg`, which the live hamlet cohort never reaches.
- **A consumer that asserts on the FILENAME.** Feature 114 had one. A census must be run for this
  file's name rather than assumed absent; `tools/cache_audit.py` is one known hit, and any other is
  a legitimate consumer change.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The 89 module-level members of `settlement/_geom.py` MUST be partitioned across
  exactly eleven submodules of a `settlement/_geom/` package, with every member in exactly one, and
  source order preserved within each submodule.
- **FR-002**: `settlement/_geom/__init__.py` MUST re-export the package's whole public surface via
  star imports (Principle X clause 14, feature 027's idiom), plus an explicit `as`-alias block for
  the underscore names, so that `from ._geom import X`, `from .._geom import X` and
  `from settlement._geom import X` all keep resolving for every name that resolved before.
- **FR-003**: A guard test MUST hold that `settlement._geom` still exposes every one of the 89
  pre-split names (a SUBSET assertion, so adding a member later needs no bookkeeping), and that no
  public name is bound to two different objects across the submodules. Each assertion MUST be
  observed failing before it is trusted.
- **FR-004**: Every regenerated `pool/**` artifact (`.json`, `.svg`, `.png`) MUST be byte-identical
  to a baseline captured from the pre-split tree by the same command, with the frozen legacy maps
  INCLUDED (`--frozen-ok`).
- **FR-005**: The import-time main-tree guard MUST still fire on import of the package or of any
  submodule of it, and `_assert_not_main_tree` MUST remain importable from `settlement` (both
  `settlement/__init__.py` and `check_village/common_01_geometry.py` consume it).
- **FR-006**: `settlement/_geom.py` MUST be deleted once the package exists.
- **FR-007**: `settlement/_geom/CLAUDE.md` MUST index the eleven submodules with a "look here when"
  row each, state the layering rule that keeps the package acyclic, and `settlement/CLAUDE.md`'s
  `_geom` row MUST point at it rather than listing contents inline.
- **FR-008**: The index MUST record, at the point of the decision, the placements a future reader
  would otherwise re-litigate: the palette and the main-tree guard living in `base.py` (neither is
  geometry; both are what every other submodule needs first), `village_population` +
  `BUNDLE_PITCH_FT` isolated in `village.py` with their intended eventual destination, the
  torii-vs-wall predicates filed with the walls rather than with `shrines_wells/torii.py`, and
  `SeatMemo` separated from the indexes it is filed beside today.
- **FR-009**: The transformer MUST refuse (non-zero exit, naming the members) when its partition
  does not exactly cover the module, when a member is assigned twice, and when an unnamed statement
  has no preceding member to attach to.
- **FR-010**: `make done` MUST be green, including the `SETTLEMENT_COV_FLOOR` ratchet - which MUST
  NOT be lowered. A pure move changes no executable line, so combined package coverage is
  arithmetically unchanged.
- **FR-011**: Every comment line in the pre-split module MUST survive somewhere in the package
  (checked mechanically, not by eye). Comment lines whose text cross-references another member's
  POSITION ("the ladder below", "see `wall_runs()` below") MUST be re-pointed at the module that now
  holds the referent; each such edit is enumerated in `tasks.md` so "edited" cannot quietly mean
  "rewritten".
- **FR-012**: `tools/cache_audit.py`'s `TARGET` MUST name a submodule that the live scripted hamlets
  actually execute and whose numeric literals move drawn geometry, and the choice MUST be verified
  by running the audit rather than argued from the code.
- **FR-013**: `tests/settlement/test_geom.py` MUST keep its name - the mirror rule in
  `tests/settlement/CLAUDE.md` maps a test file to a `settlement/` module, and at 353 lines the file
  is well under the clause-13 bar (see Assumptions).
- **FR-014**: `pyproject.toml`'s `per-file-ignores` MUST cover `settlement/_geom/__init__.py`
  (`F401`, `F403`) with the same one-line rationale the four existing star-import `__init__` entries
  carry.

### Key Entities

- **The eleven submodules** (member counts and line spans from the AST census; `~lines` is the body
  slice, before each module's pruned import header):

  | module | what it is | members | ~lines |
  |---|---|---|---|
  | `base.py` | what every other submodule needs first: the `Pt`/`Poly`/`Manifest` aliases, the import-time main-tree guard, the land/crop palette | 9 | 50 |
  | `primitives.py` | coordinate math on points, segments and rings - no map vocabulary | 9 | 95 |
  | `overlap.py` | footprint corner rings, and the predicates that ask whether two regions meet or how far apart they are | 13 | 175 |
  | `indexes.py` | the prefilter family and the spatial indexes: `boxed_*`, `PointGrid`, `Indexed`, `indexed_grid` | 8 | 245 |
  | `seatmemo.py` | `SeatMemo` - the refusal memo, and the invariant it asserts rather than assumes | 1 | 105 |
  | `labels.py` | caption typography: the standoff ladder, the two caption sizes, tilt/quad/AABB/seat | 15 | 145 |
  | `ways.py` | the travelled ways read off a manifest, the gate that bars one, and the plank/deck landing constants | 11 | 125 |
  | `walls.py` | every wall on the map, what closes a ward against one, and the arches that must stand clear of one | 9 | 170 |
  | `extents.py` | a recorded feature's DRAWN extent read back off the manifest: the wet paddy rings, the forest reveal band, the four stable-yard glyph quads | 8 | 120 |
  | `curves.py` | making a line or a ring look hand-made: fillets, Catmull-Rom smoothing, organic jitter, winding paths | 6 | 125 |
  | `village.py` | the village population distribution and the homestead-bundle pitch - not geometry; isolated for an eventual move | 3 | 25 |

- **The package surface**: `settlement/_geom/__init__.py`, star imports plus the underscore alias
  block. It has no logic of its own, exactly as `check_village/__init__.py` has none - the split is
  meant to be invisible above this line, and the partition can be re-cut later without touching a
  single consumer.
- **The byte-identity oracle**: `sha256sum` over every `pool/**` artifact, captured from a scratch
  copy of the pre-split tree and again after, both via
  `python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py`. `wip/shiro-daika.gen.py` is
  excluded (feature 112 research R11: over 6 minutes against ~3 for the whole pool, exercising no
  member the three provincial cities do not).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No source file in `settlement/_geom/` exceeds 280 raw lines - a largest file about a
  fifth of the pre-split 1,303.
- **SC-002**: A session working on one population here loads at most ~280 lines where it previously
  loaded 1,303 - a reduction of at least 78% on the worst case, and over 90% for the label
  typography, the ways, the curves and the memo.
- **SC-003**: Every regenerated map artifact is byte-identical to its pre-split baseline (hash diff
  empty across all pool maps, frozen legacy maps included), with the sweep's exit code and
  REGENERATED count part of the pass condition.
- **SC-004**: `make done` is green with the coverage ratchet floor unchanged.
- **SC-005**: No consumer changes except `tools/cache_audit.py`'s `TARGET` line and its comment: not
  one of the 34 importing engine files, not a pool generator, not a `wip/` script, not a test.
- **SC-006**: Both halves of the surface guard are demonstrated red before being trusted.
- **SC-007**: Zero comment lines from the pre-split module are lost; every cross-reference edited is
  listed in `tasks.md` and is comment-only.
- **SC-008**: `python3 -m tools.cache_audit` passes against the new `TARGET`, proving the audit still
  has a mutation site the live pool executes.

## Assumptions

- **One stage, not two - and no function decomposition.** Features 112 and 113 each ran a pure move
  followed by a per-method decomposition stage. There is nothing here to decompose: the largest
  member is 58 raw lines / 34 statements (`ward_interior`), far under clause 12's "few hundred
  statements" suspicion bar. Doing it anyway would put behavior-changing risk inside a move whose
  whole value is that it changes nothing.
- **Star imports, not a roster.** Features 025/112-116 composed a MIXIN, so their `__init__` was a
  class definition. `_geom` is module-level functions, so the equivalent is a re-export surface -
  and Principle X clause 14 (feature 027) settles how those are written here: derive it with stars,
  do not maintain a roster. mypy `--strict` treats star-imported public names as explicitly exported
  (probe-verified in `specs/027-init-star-imports/research.md` R1), so no `__all__` is needed.
- **`settlement/__init__.py`'s own 58-line `_geom` roster is left exactly as it is.** It is a
  parent-level roster and converting it to stars is feature 027's job, not this one's - and touching
  it would put a second question inside this feature's oracle. Every one of its lines keeps
  resolving unchanged.
- **`village_population` and `BUNDLE_PITCH_FT` stay in the package.** They are misfiled at the
  PARENT level - a village population roll is `rolling.py`'s business, not geometry's - but moving a
  member between parent-level modules is a different change with different risk. They get an
  isolated module so the eventual move is a one-file change, exactly as feature 116 did with
  `seats.py` and `byres.py`.
- **The palette stays too, for the same reason.** `LAND` and the four crop-shade lists are drawing
  colors that `core.py` imports from `_geom` only because feature 025's positional cut put them
  there. Isolated at the top of `base.py` rather than moved.
- **`_geom` keeps its underscore name.** The name says "package-private to `settlement`", which is
  still true and is how 34 files spell it today. Renaming it to `geom` would touch every one of them
  for no gain - and the underscore has never stopped `tools/scatter_audit.py` from importing it when
  it needed to.
- **The existing test file is not split.** `tests/settlement/test_geom.py` is 353 lines, well under
  the clause-13 bar, and features 112-116 all left their mirror test file whole. Tests get no
  exemption from clause 13, but neither do they get pre-emptive splitting.
- **`rolling.py` (1,197) and `land.py` (1,187) remain debt** and are deliberately NOT in scope -
  recorded here so the next session inherits the list rather than rediscovering it. Bundling several
  splits into one oracle sweep would make a byte-identity failure ambiguous about which split caused
  it.
- The session works in its clone under `.clones/diagram-tokens` and synced to main's tip before
  starting; the spec number is claimed by pushing `specs/117-geom-package/` the moment `spec.md`
  exists (CLAUDE.md, concurrent-sessions protocol).
