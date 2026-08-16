# Phase 0 Research: settlement/city.py -> settlement/city/

Feature 113. Recorded so a later reader does not have to re-derive any of it.

## R1. Where the seams fall - settled by the CALL GRAPH, not by line order

**Decision**: six modules, not the five the spec sketched - `walls`, `moat`, `canals`,
`waterfront`, `bridges`, and a one-method `civic`.

**Method**: rather than trusting the reading-order grouping from the spec, the class's intra-class
call graph was computed (`self.X` where `X` is a `CityMixin` member) together with a census of
external consumers across `settlement/`, `hamletgen/`, `waterfields/`, `check_village/`, `pool/`,
`wip/`, `tests/`, `tools/` and `pipeline/`. The result:

    city_wall            -> _gapped_ring, _tower, _wall_arc_of, _wall_perimeter,
                            _wall_point_at_arc, _wall_walk
    inwall_drain_outfall -> sluice_gate
    farmland_ring        -> _ring_upslope, sluice_gate
    bridges              -> bridge
    channel_footbridges  -> bridge, _plank_reaches_useful_ground

Five clusters, and every private helper has exactly one caller except `bridge` (two, both inside
the bridges cluster) and `sluice_gate` (three, one of them across a seam). The reading-order
grouping and the dependency grouping AGREE, which is the fact that makes a mechanical slice safe.
`quay`, `aqueduct`, `dock`, `jetty` and `log_boom` call nothing and are called by nothing - the
waterfront module is five independent entry points, the loosest-coupled group in the class.

**The one cross-seam call**: `farmland_ring` (in `canals.py`) calls `sluice_gate` (in `moat.py`).
This needs no import and is not a design smell: sub-mixin methods reach each other through `self.`
on the composed `Settlement`, so the partition can be re-cut later without touching a call site.
Feature 112's `__init__.py` docstring states this property; it is the reason the mixin composition
was chosen over free functions.

**Why `_ring_upslope` sits in `canals.py` and not with `ring_road`**: the name suggests the ring
road, but its only caller is `farmland_ring`. Placement follows the caller, not the name. Recorded
because a future reader will have the same suspicion.

### The `governor_mansion` orphan, and why it gets its own module

`governor_mansion` (21 lines, 5 external consumers) is the last method in the file and belongs to
none of the five subsystems. The design pass found the deciding fact: its body calls
`self.manor(...)` and then re-keys the record out of `M["manors"]`. It is a STRUCTURE that reuses
the manor glyph, not a piece of city infrastructure - topically it is a sibling of the things in
`castle_civic.py` (castle, ministries, dojos), not of walls and moats.

Three options were weighed:

1. **Bury it in `bridges.py`** as a documented placement exception, the way feature 112 documented
   `_paddy_surface` and `_rounded_pond`. Rejected: those were exceptions of DEGREE - a method that
   could defensibly live in either of two places. This is a CATEGORY orphan that fits neither, and
   documenting a bad home does not make it a home. It would also make the `bridges.py` index row a
   lie, which is the one thing the sub-index exists to prevent.
2. **Relocate it to `castle_civic.py`** - topically correct, and the size works (903 + 21 = 924,
   still under the clause-13 bar). Rejected FOR THIS FEATURE, on two grounds. It widens the guard
   test's contract across two mixins at the exact moment the feature's value proposition is
   "provably nothing moved," and it makes US1 something other than a pure move, which R5 says is
   the property worth protecting. Note that the ORIGINAL reason the spec scoped this out - keeping
   the merge with the peer session mechanical - has since evaporated: that session landed first and
   never touched `settlement/`. The remaining reasons are the two above, and they stand on their
   own.
3. **Give it its own `civic.py`** - CHOSEN. It costs about twenty lines of module boilerplate and
   buys three things: no index row has to lie, the orphan is visible instead of hidden, and the
   eventual relocation becomes a one-file `git mv`-shaped change with zero ambiguity about what
   moves.

**Follow-up recorded, not done**: `settlement/city/civic.py` should fold into
`settlement/castle_civic.py` in a later feature. It is deliberately NOT done here.

## R2. Clause 14 (derive, don't maintain or split) does not apply

Constitution Principle X clause 14 says an oversized ROSTER-shaped file should be derived rather
than split - the exemplar being feature 027, which collapsed a 3,148-line re-export `__init__.py`
to 63 lines. The clause was evaluated against `city.py` and does not apply: all 27 members are
hand-written drawing logic with distinct behavior, and nothing in the file restates what code
elsewhere already declares. There is no roster and no derivable surface, so the clause-13 split is
the correct instrument.

Recorded explicitly so the non-application reads as a decision rather than an oversight. The
census clause 14 would have asked for was still spent, on the composed-mixin surface - that is what
`contracts/mixin-surface.md` pins and what the guard test enforces.

## R3. The oracle: the pool corpus, captured from a scratch copy of the PRE-split tree

**Decision**: sweep every `pool/` generator - live and frozen - in a scratch copy, hash every
resulting `.json` / `.svg` / `.png`, and compare. `wip/shiro-daika.gen.py` is excluded.

**Why not the committed manifests.** Feature 110 research R3 proved them unreliable as a baseline:
the engine may have drifted since they were committed, so a mismatch would be indistinguishable
from a refactor bug. Only a pre-change run of the SAME tree is a valid fixed point. (The peer
session independently reproduced all 9 committed manifests on its own tip, which is reassuring
about current drift but does not change the method - a baseline that happens to be correct today
is still the wrong instrument.)

**Why the frozen legacy maps are included.** `--frozen-ok` is required or `regen` prints `FROZEN`
and skips them. For this feature they matter more than they did for 112: the four provincial-city
maps (`tango`, `minami`, `nagahara`) plus the frozen legacy pool are the ONLY artifacts that
exercise the city wing at all. A sweep of the live scripted hamlets alone would leave `city_wall`,
`moat`, `farmland_ring` and the whole waterfront module unverified - which is to say, it would
leave the feature with no oracle for the code it is actually moving.

Reading a frozen map does not violate the freeze. The freeze forbids maintaining frozen maps
against new rules, re-gating them, and committing regenerated bytes; it does not forbid running one
as a differential oracle in a scratch tree. Features 110, 111 and 112 all used this method.

**Why `wip/shiro-daika.gen.py` is excluded**: feature 112 research R11 measured it - over 6 minutes
without output against roughly 3 minutes for the whole pool, because it is a capital-scale gen with
an open housing pass generating from nothing. The general rule it recorded applies here with more
force, not less: an oracle earns its place by the failures it can catch, and its cost is multiplied
by the number of times the oracle runs. This feature runs it SEVEN times (see R4), so a 6-minute
artifact that exercises only city methods the three provincial cities already exercise would cost
roughly 45 minutes of wall clock for zero additional diagnostic power.

## R4. Stage sequencing, and why the sweep runs seven times

**Decision**: baseline, then one sweep after the pure move, then one sweep after EACH of the five
decompositions. Seven runs of the oracle.

**Rationale**: the two stages have different failure modes and mixing them destroys the diagnostic
(feature 112 R5). A pure move that breaks byte-identity means the composition or an import binding
is wrong. A decomposition that breaks it means a draw was reordered. Verified separately, a red
sweep names its own cause; verified together, it does not.

Within Stage 2 the five methods are done one at a time for the same reason, and because RNG draw
order is the specific hazard: the engine's randomness is positional and scoped, so an extraction
that moves a `random` call relative to another changes every downstream coordinate while every unit
test still passes. Doing five at once means bisecting to find which.

The five, in the order they will be done - smallest first, so the technique is proven on cheap
targets before it reaches the 339-line one:

| method | lines | module | why it is on the list |
|---|---|---|---|
| `log_boom` | 97 | `waterfront.py` | smallest; no intra-class callees, the safest first cut |
| `moat` | 111 | `moat.py` | independent entry point |
| `farmland_ring` | 121 | `canals.py` | calls across a seam (`sluice_gate`) - proves the seam holds |
| `channel_footbridges` | 195 | `bridges.py` | 14 external consumers, the most-used of the five |
| `city_wall` | 339 | `walls.py` | the largest function in the skill; six private callees already |

`city_wall` is deliberately LAST. It is the one with an existing helper vocabulary
(`_wall_arc_of`, `_wall_point_at_arc`, `_wall_perimeter`, `_tower`, `_wall_walk`, `_gapped_ring`),
so the extraction has somewhere obvious to go, but it is also the one whose failure would be most
expensive to diagnose.

## R5. What changed from feature 112's R14, and what did not

Feature 112 R14 recorded the delete/modify (`DU`) collision: a package split DELETES the original
file, a peer patching that same file produces a conflict git cannot auto-resolve and which leaves
no markers, and the danger is taking the deletion and silently dropping their fix.

**It did not happen here, and the reason is worth recording.** A heads-up was sent to the "Diagram
reorganize" session before any code moved, and it answered: that session touches nothing under
`settlement/`. So the collision this feature was designed around never materialized.

**What DID matter was the second-order effect nobody would have predicted from R14** - the peer's
reorg moved this feature's TOOLING, not its subject:

- `test_settlement/` -> `tests/settlement/`, with package-qualified helper imports
  (`from tests.settlement._builders import ...`).
- The loose top-level modules became packages that must be run AS MODULES from the skill root -
  `python3 -m pipeline.regen`, `python3 -m tools.why_placed`. Run by script path, a package module
  puts its own directory on `sys.path` instead of the skill root and the same file gets imported
  twice under two names.
- `tests/` is now pruned from `gencache.engine_files()` and `render_cache.engine_fingerprint()`.

The last one is the one that could have poisoned this feature silently: if a nested
`settlement/city/` fell OUT of the engine fingerprint, a stale cache would reproduce the baseline
for the wrong reason - a green sweep that proves nothing. The peer verified on its own tip that
`settlement/fields/` (all five files) is still inside `engine_files()` and that `tests/`
contributes zero, so a nested `settlement/city/` is walked identically. **This is re-confirmed for
`city/` specifically as task T00x before any sweep is trusted** - a borrowed verification of an
analogous package is good evidence, not proof.

**The generalization, which is the part worth keeping**: a heads-up to a peer session is a
courtesy, not a protocol - it can expire unapproved, and main remains the coordination point. But
the question worth asking a peer is not only "are you touching my files?" It is "are you moving
anything I RUN?" This feature's files were never at risk; three of its commands were.

## R6. What the transformer must carry that a naive slice drops

**Decision**: adapt `specs/112-fields-package/split_fields.py` rather than write a new one, keeping
its slicing rule exactly: each member's block runs from the PREVIOUS node's `end_lineno + 1` to
this node's `end_lineno`, not from the node's own `lineno`.

**Why that rule matters**: `ast` reports `FunctionDef.lineno` at the `def`, so slicing by it
silently drops decorators sitting above it, the blank lines between members, and any comment block
written above the member. In this project the third one is the real loss - a comment above a method
is usually researched grounding, and a "pure move" that drops it is not pure. `city.py` has one
such banner (`# ---- provincial-city features (scale="city")` at line 29, inside the class body
above `_gapped_ring`); it describes the OLD file's whole contents and would be actively misleading
at the top of `walls.py`, so it is dropped deliberately via the transformer's `DROP_BANNERS` list
and each module's docstring says the same thing for its own contents.

**Header handling**: the parent header (everything above `class CityMixin:`) is copied wholesale
into every module with `._geom` -> `.._geom`, `._knobs` -> `.._knobs` and `.core` -> `..core`, then
pruned by `ruff check --select F401 --fix`. Reaching the same end state by hand-computing each
module's used names would require the script to model name resolution; letting the linter do it is
both shorter and more reliable.

**The refusal conditions** are kept from 112 and are what make the script trustworthy: it refuses
if any class-body member is unnamed, and it refuses if the partition does not exactly cover the
class (printing `missing=` and `extra=`). A partition that silently dropped a method would produce
a package that imports fine and draws nothing.

`city.py` is confirmed to have no class-level constants - all 27 members are `FunctionDef` - so the
`Assign` branch 112 needed for its `_PADDY_*_KINDS` matrices is retained but will not fire.

## R7. The coverage ratchet - what this split can and cannot move

`SETTLEMENT_COV_FLOOR` is 94 and the post-reorg measured figure is 95 (confirmed by the peer
session's green gate on its own tip: 3,176 tests, 100% on every measured module outside
`settlement/`).

**A pure move cannot change coverage** - the same statements are executed by the same tests. So a
Stage 1 sweep that comes back byte-identical should also leave the percentage untouched, and a
MOVEMENT in the figure after Stage 1 is a signal worth investigating, not a bonus to bank.

Stage 2 can move it, in either direction: extracting a helper can split a partly-covered function
into a covered part and an uncovered part (raising or lowering the ratio depending on where the
lines fall). The rule is FR-012's: the floor never falls, and it rises only to a figure this
feature measured itself.

The peer session deliberately left the floor at 94 rather than banking its own measured 95, on the
reasoning that raising a ratchet inside an unrelated refactor makes a future failure hard to
attribute. That reasoning is adopted here: this feature raises the floor only if ITS split is what
re-covered the wings, and the new measurement is recorded in the comment beside it.
