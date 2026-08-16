# Phase 0 Research: settlement/shrines_wells/ Package Split

Every finding here was resolved before Phase 1. Nothing is left as NEEDS CLARIFICATION.

The lineage matters and is stated once: this is the fourth split of this shape (112 `fields/`, 113
`city/`, 114 `structures/`). Where a predecessor already settled a question, the entry says so and
records only what is DIFFERENT here - re-deriving a settled decision is the waste this file exists to
prevent.

---

## R1 - The partition, and the rule that produced it

**Decision**: seven submodules, grouped by **what a session comes here to change**, not by theme and
not by size.

| module | the change that brings a session here |
|---|---|
| `shrines.py` | what a religious hall or a wayside shrine LOOKS like, or where its caption goes |
| `torii.py` | the approach: how many arches, how far apart, how far off the hall, how they dodge a wall |
| `wellground.py` | whether a patch of ground may take a wellhead at all (and the cost of asking) |
| `wells.py` | the wellhead glyph, and how many wells a map gets and where |
| `seats.py` | the general "where can a `w` x `h` feature stand?" API |
| `byres.py` | the draft-animal shed |
| `woods.py` | how a wood is drawn - canopy density, the fringe, what a crown refuses to cover |

**Rationale**: the file is feature 025's positional slice, so "theme" does not exist to group by -
its own name (`shrines_wells`, the only `and` in the package) concedes that two of the six subsystems
were already acknowledged as unrelated when it was created. The read-cost evidence: a session
changing `_avenue_at_threshold` (34 lines) currently loads 1,145 lines it does not need, and every
reader of any subsystem loads the 447-line well subsystem.

**Alternatives considered**: (a) two modules, `shrines.py` + `wells.py`, following the filename -
rejected because it leaves 500+ line files and files the byres, the woods and the general seat API
under one of two names that describe neither; (b) partition by tier (hamlet/village vs town/city) -
rejected because no member is tier-exclusive and the coverage wings do not follow tiers here; (c)
equal-size modules - rejected on the same ground feature 114 recorded: a partition tuned for equal
files has to cut a cluster no task cuts.

### R1a - `open_seat` + `_footprint_clear` get their own module (`seats.py`)

**Decision**: isolate, do not move out of the package in this feature.

**Rationale**: `open_seat` is a general placement API - the skill's `CLAUDE.md` documents it under
"Ask the ENGINE where a feature fits" and its consumers are 9 pool gens, `civic_grounds.py`,
`houses.py`, `rolling.py`, `structures/fixtures.py` and `wip/shiro-daika.gen.py`. It has nothing to
do with shrines or wells; it lives here because feature 025's cut put it beside the wells, whose
`well=True` refusal it optionally applies. Its natural parent-level home is `houses.py`, beside the
`_fits` it delegates to. But moving a member BETWEEN parent-level mixins is a different change with
different risk, and folding it in would make the byte-identity oracle answer two questions at once.
Isolated, the eventual move is a one-file change.

**Precedent**: feature 113 did this with `governor_mansion` (`city/civic.py`), 114 with
`road`/`pasture` (`structures/ground.py`). Both isolations are still correct today, and neither has
had to be re-litigated.

### R1b - the byres get their own module (`byres.py`)

**Decision**: isolate, do not move out of the package in this feature. Same reasoning as R1a.

**Rationale**: a draft-animal byre is a homestead appurtenance - the docstring itself says "call
AFTER farmsteads() and BEFORE the grove" - so it belongs with `homestead_parts.py`'s threshing yards,
gardens and sheds. At 54 body lines it would fit there comfortably (756 -> ~810, still under the
bar). It is not moved here for the R1a reason, and `byres.py` makes the move cheap later.

### R1c - `shrine_well` is filed with the wells, not the shrines

**Decision**: `wells.py`.

**Rationale**: the naming pulls one way and everything else pulls the other. It IS a well: it calls
`well_at` (which applies `_in_scrub_cover` + `_well_ground_clear` + `_fits`), records an `M["wells"]`
entry with `shrine=True`, and exists so a remote shrine passes `remote_shrine_has_own_well`. Its
neighbors in behavior are the other three placement passes, not the hall glyph. Placement follows the
code, not the name.

### R1d - `_hall_caption_y` is filed with the halls, not the torii

**Decision**: `shrines.py`.

**Rationale**: it reads torii seat geometry (`torii_halfbox`, the avenue's seats), which argues for
`torii.py`; but its single consumer is `shrine_hall`, and its subject is where the HALL's caption
goes. Placement follows the caller - feature 113's `_ring_upslope` precedent and 114's four door
probes. The cross-module read is free: both mixins compose onto the same `Settlement`, so
`_hall_caption_y` reaches nothing it could not reach before.

### R1e - the well subsystem is cut in two, at the ground/placement seam

**Decision**: `wellground.py` (7 members, 172 body lines) + `wells.py` (8 members, 275).

**Rationale**: 447 lines in one module would make the well subsystem alone as large as the whole
`structures/fixtures.py`, and it contains a real task boundary that the open engine work sits astride:

- **`wellground.py` answers one question** - *is this ground fit to sink a wellhead in?* - and holds
  everything that makes asking it cheap: `_build_well_index` (the three PointGrids),
  `_terrain_fingerprint`, the `frozen_terrain` scope, `_well_index`, `_wet_toe_keepout`,
  `_well_ground_clear`, `_in_scrub_cover`. This is the perf-critical layer, and its documentation is
  the 45-minute-grind post-mortem. A session tuning it needs no glyph and no pass.
- **`wells.py` puts wells on the map**: `_well_vr`, `well`, the `farm_wells`/`place_wells` passes with
  their private halves, `well_at`, `shrine_well`. A session changing how many wells a map gets, or
  fixing the recorded 30 px-vs-`ftpx` reservation defect, needs none of the index machinery.

The dependency runs one way (`wells.py` -> `wellground.py`, never back), which is what makes the seam
real rather than administrative - see R10.

**Alternatives considered**: leaving the well subsystem whole (rejected: 447 lines is over half the
budget of a split whose entire purpose is per-read cost, and the two halves have disjoint readers);
cutting `farm_wells` off into a `farmwells.py` (rejected: it shares `well_at` and the freeze scope
with `place_wells`, and separating siblings that share a helper is the cut that makes a reader open
two files instead of one).

**Naming note**: `wellground.py` and `wells.py` are near-neighbors alphabetically and in name, which
is a small legibility cost accepted deliberately - the alternative names tried (`ground.py`, already
used for a different thing in `structures/`; `siting.py`, which describes both halves) were worse.
The index disambiguates in one line each.

---

## R2 - Clause 14 (derive, don't maintain or split) does not apply

**Decision**: evaluated and rejected as inapplicable; recorded so a later reader does not mistake the
omission for an oversight.

**Rationale**: clause 14 governs ROSTER-shaped files - re-export lists, `__all__` duplicates,
registry rows a machine could regenerate from the code they point at (`check_village/__init__.py`,
3,148 lines -> 63, feature 027). `shrines_wells.py` is the opposite: 38 hand-written drawing and
placement methods with distinct behavior, no re-export surface, no registry, nothing restating what
code elsewhere declares. There is no surface to derive, so clause 13's package split is the correct
instrument.

---

## R3 - The baseline must be captured, not read from git

**Decision**: capture from a scratch copy of the PRE-split tree, by the same command the post-split
sweep uses.

**Rationale**: settled by feature 110 research R3 and re-confirmed by 112/113/114. The committed
manifests are not a valid baseline: the engine may have drifted since they were committed (and for
the 19 FROZEN legacy maps it certainly has - they are deliberately never regenerated), so a mismatch
against them cannot distinguish "this refactor broke something" from "this map was committed under
older code". Comparing a fresh pre-split sweep against a fresh post-split sweep isolates the change.

**The false-green trap, inherited from 113 R9 and kept**: `cp -a` copies the committed artifacts into
the scratch tree. A sweep that dies early leaves those bytes in place, they hash equal to a baseline
that faithfully reproduced them, and `diff` prints nothing while nothing was tested. So the pass
condition is three-part: exit code 0, the `REGENERATED` count matching the baseline's, and the empty
hash diff. Do not run the sweep beside a `make done`.

---

## R4 - One stage: no decomposition pass

**Decision**: pure move + index. No member is decomposed.

**Rationale**: the ~150-line bar features 112/113 settled on. Member sizes here, largest first:
`shrine_hall` 114, `_farm_wells` 89, `_well_ground_clear` 53, `_place_wells` 52, `well_at` 47,
`_hall_caption_y` 46, `_tree_stand` 46 - everything else under 45. Nothing is near the bar.
Decomposing anyway would put behavior-changing risk inside a move whose entire value is that it
changes nothing, and would make a byte-identity failure ambiguous about its cause.

**Noted for a future session, not acted on**: `shrine_hall`'s 114 lines are ~60% comment and
docstring; its executable body is small. Raw-line size is the wrong reason to touch it.

---

## R5 - The slicing rule, and the decorator this file introduces

**Decision**: slice each member as `(previous member's end_lineno + 1 .. this member's end_lineno)`,
never by `node.lineno`.

**Rationale**: inherited from feature 025 through 112/113/114. That span carries the decorators, the
blank lines, and any comment block written ABOVE the member - and in this project the third is the
real loss, because a comment above a method is usually researched grounding. A "pure move" that drops
a why-comment is not pure.

**What is NEW here**: this is the first file in the lineage that actually has a **decorator**.
`frozen_terrain` carries `@contextlib.contextmanager`, and `ast` reports `FunctionDef.lineno` at the
`def`, one line BELOW it. Slicing by `node.lineno` would silently produce a plain generator function -
which imports cleanly, type-checks, and then fails at every `with self.frozen_terrain():` call site
with `AttributeError: __enter__`. The slice rule already handles it; the point is that the hazard the
predecessors documented in the abstract is concrete here, so the transformer's own docstring says so
and `quickstart.md` checks the decorator survived by name.

**Mechanical check, not eyeball**: every `#` comment line in the pre-split class body must appear
somewhere in the package (quickstart step 6). Expect zero lost.

---

## R6 - Consumer census: nothing outside the package changes

**Decision**: no consumer edits at all. Feature 114 had exactly one (a filename string in
`tests/tools/test_why_placed.py` asserting `"structures.py"` appears in traced call frames), so this
was checked rather than assumed.

**Findings** (grep over the whole skill, `__pycache__` excluded):

- The string `shrines_wells` appears in exactly ONE `.py` file besides the module itself:
  `settlement/core.py:19`, `from .shrines_wells import ShrinesWellsMixin` - which the package
  preserves verbatim. No test, tool or generator names the file.
- **No test monkeypatches a module-level name** in `settlement.shrines_wells` (consistent with the
  025 consumer census, re-verified). This matters because submodules bind helper names at import, so
  patching `settlement.shrines_wells.point_in_poly` would not reach a sub-mixin that already imported
  it - a hazard that simply does not arise here.
- **Cross-module PRIVATE calls do exist and all keep working**, because they go through `self.` on
  the composed `Settlement`: `water_ways.py`, `civic_grounds.py` and `structures/compounds.py` call
  `self._assert_walls_clear_of_torii`; `civic_grounds.py` calls `self._well_vr` and
  `self._well_ground_clear`; `core.py` and `finish.py` call `self.flush_tree_stands`;
  `castle_civic.py` and `core.py` call `self._tree_stand`. None needs an import, before or after.

---

## R7 - Coverage cannot move, so any movement is a defect

**Decision**: `SETTLEMENT_COV_FLOOR` stays at 94; if the measured number moves in EITHER direction,
investigate rather than re-baseline.

**Rationale**: a pure move relocates executable lines without adding, removing or altering one, and
the Makefile measures the floor over `*/settlement/*` combined - so the arithmetic is unchanged by
construction. A drop means a member was lost or a module was left out of the composition; a RISE
means something that used to be measured no longer is (e.g. a file excluded by a path pattern).
Neither is a number to bank. The floor is a ratchet: raise it as tiers convert, never lower it.

---

## R8 - Monkeypatching guidance for the new depth

**Decision**: carry `settlement/CLAUDE.md`'s existing rule into the package index, one level deeper.

**Rationale**: patch the DEFINING submodule (`settlement._geom.point_in_poly`) or, for anything
reached through `self.`, patch `settlement.Settlement` - class-level patching is unaffected by the
split. After this feature, "the defining submodule" for a member of this subsystem is
`settlement.shrines_wells.<module>`, not `settlement.shrines_wells`. No test does this today (R6), so
the note is preventive.

---

## R9 - Principle XII (Historical Grounding Bookends) is N/A, argued

**Decision**: N/A - and argued rather than asserted, because this file carries more historical
grounding than any other module in the package.

**Rationale**: the bookends govern a feature that changes what a generator ASSERTS ABOUT THE WORLD.
This one changes no element, no size, no spacing, no prevalence and no siting rule. The canopy
density study (500-800 stems/ha, 13 ft mean spacing), the true-scale hall guard (a kondo runs
~150-190 ft), the wayside-shrine glyph, the idobata well-per-10-20-households doctrine and the
draft-buffalo sharing ratio all move verbatim and keep governing exactly what they governed.

The closing bookend is satisfied more strongly than by eye: an empty hash diff over every `.png` in
`pool/` proves the depiction is unchanged pixel for pixel, which is a stronger statement than "the
reviewer looked at the render and it seemed the same". The grounding text itself is protected by R5's
slicing rule and CHECKED by quickstart step 6.

---

## R10 - The hub, and the cross-submodule call map

**Decision**: `wellground.py` is the package's hub. Recorded in the index so the next re-cut starts
from the dependency shape rather than rediscovering it.

**Calls between submodules** (all resolved through `self.` on the composed `Settlement`; no
intra-package imports exist or are needed):

| from | to | calls |
|---|---|---|
| `wells.py` | `wellground.py` | `well_at` -> `_in_scrub_cover`, `_well_ground_clear`; `_place_wells` -> both; `farm_wells`/`place_wells` -> `frozen_terrain` |
| `seats.py` | `wellground.py` | `open_seat(well=True)` -> `_in_scrub_cover` |
| `shrines.py` | `torii.py` | `shrine_hall` -> `_avenue_pitch`, `_avenue_at_threshold`, `_avenue_short_of_walls`, `_torii` |
| `torii.py` | (itself) | `torii_path`/`torii_even` -> `_torii` |
| `byres.py`, `woods.py`, `seats.py` | outside the package | `_fits`, `_hjit`, `_canopy_keepouts`, `_corridor_buffers`, `_on_watercourse`, `_clear_ground` |

`wellground.py` calls out to nothing in the package - the shape a well-cut partition should have, and
the same property `urban.py` has in `structures/`.

---

## R11 - The test file stays whole

**Decision**: `tests/settlement/test_shrines_wells.py` (474 lines) is not split, and keeps its name.

**Rationale**: clause 13's bar is ~1,000 raw lines and applies to tests, but 474 is under half of it,
and the mirror rule in `tests/settlement/CLAUDE.md` maps a test file to a `settlement/` MODULE -
which, after this feature, is a package. All three predecessors left their mirror file whole
(`test_fields.py` 589, `test_city.py` 754, `test_structures.py` 692, each now +~100 for its guard).
Pre-emptive splitting would also make the diff harder to review for no benefit.

**The threshold at which this changes**, so the next session inherits it: if the file passes ~1,000
raw lines, split it to mirror the package - `test_wells.py` + `test_shrines.py` + `test_woods.py` is
the obvious cut, and the guard block travels with whichever file keeps the package-level tests.

---

## R12 - Concurrency with feature 115

**Decision**: proceed; the overlap is two shared documents and is line-disjoint.

**Rationale**: feature 115 (`civic_grounds.py` -> package) is running in a peer session and follows
this same lineage, so it edits the same two shared files: `settlement/CLAUDE.md`'s "look here when"
table (its own row) and, if it adds one, `tests/settlement/CLAUDE.md`'s subsystem list. Each feature
edits its own row of a markdown table, so a textual merge resolves cleanly; the sync-in before each
stop-work ritual is what keeps the window small. Both features also share `SETTLEMENT_COV_FLOOR`,
which neither may lower.

**What NOT to do** (CLAUDE.md, concurrent sessions): do not coordinate by messaging the peer session.
Main serializes with zero cooperation. The spec number was claimed that way - 115 was taken between
this spec's first draft and its first push, and the fix was to renumber and push, not to negotiate.
