# Phase 0 Research: settlement/civic_grounds.py -> settlement/civic_grounds/

Every item here resolves something the plan would otherwise have to guess at. Items marked
**decision** changed what the plan does; items marked **record** exist so a later reader does not
re-derive them or mistake an omission for an oversight.

---

## R1 - The partition rule (decision)

**Question**: how are 22 members grouped into modules?

**Finding**: the same rule features 113 and 114 arrived at - **group by what a session comes here to
change**, not by theme and not by size. The four subsystems in this file are discovered rather than
imposed: they are already contiguous in source order, which is the tell that feature 025's residue
bucket accreted them in four sittings rather than interleaving them.

**Decision**: five modules - `funerary.py`, `justice.py`, `civic.py`, `lodging.py`,
`stable_yard.py`. Sizes are deliberately uneven (190 to 385 lines) because tasks are uneven.

### R1a - `_ward_fence_cap` goes with the funerary grounds (decision)

It is called by `mausoleum` inside this file, and by `settlement/structures/compounds.py` outside it.
A name with an external consumer looks like a general utility that should live somewhere neutral,
but the rule established by 113's `_ring_upslope` and 114's four door probes is **placement follows
the caller within the package being cut**. The external consumer reaches it through the composed
`Settlement` either way, so its placement costs that consumer nothing.

The alternative reading - that it belongs with the ward fences in `water_ways.py` - is a
PARENT-level move, and folding one into this feature would make the byte-identity oracle answer two
questions at once. Recorded in the index as a future move, not made here.

### R1b - `precinct_interior` goes in `civic.py` (decision)

It draws a sovereign temple precinct's interior program (abbot's residence, order administration,
library, two dormitories, kitchen). Thematically it is religious ground, and its natural eventual
home is beside the shrines in `shrines_wells.py`. It also calls `self.cemetery`, which after the
split lives in `funerary.py`.

Neither fact moves it. Cross-module `self.` calls resolve through the composed class and are normal
in this package (114 has several). And moving it to `shrines_wells.py` is again a parent-level move.
It sits in `civic.py` as the "institutional works" member, with a note.

### R1c - `_stable_yard` gets a module to itself (decision)

At 335 lines it is larger than three of the other four modules. Folding it into `lodging.py` with
its caller `flush_stable_yards` would produce a ~575-line module - not a clause-13 violation, but
more than half the pre-split file, which would leave the feature having moved the grab-bag problem
rather than solved it. A single-method module is unusual; a module that swallows half the split is
worse.

---

## R2 - Clause 14 does not apply (record)

`civic_grounds.py` is not roster-shaped. Its 22 members are hand-written drawing and siting logic
with distinct behavior; nothing restates what code elsewhere declares, so there is no surface to
derive. The new `__init__.py` is composition-only at ~40 lines - the same shape 112/113/114 shipped,
and far below the size at which feature 027's star-import derivation pays for itself.

Recorded because the constitution's clause 14 is newer than clause 13 and a reader may reasonably ask
why a 2026-08-16 feature did not apply the 2026-08-16 clause. It was evaluated. See R6 for the one
clause-14-adjacent finding that DID change the plan.

---

## R3 - The oracle is a scratch-copy baseline, not the committed manifests (record)

Feature 110's research R3 established this and it holds unchanged: the committed manifests under
`pool/` are not a valid baseline, because the engine may have drifted since they were committed. A
mismatch against them would be indistinguishable from a refactor bug.

**Decision**: capture `sha256sum` over every `pool/**` artifact from a scratch copy of the PRE-split
tree via `pipeline/regen.py --no-cache --frozen-ok`, and compare after each stage.

---

## R4 - Three stages, not two (decision)

Feature 114 deferred the per-method decomposition stage and said why: its largest member was 130
lines, under the ~150-line bar feature 112 settled on, and decomposing anyway would have put
behavior-changing risk inside a move whose whole value was that it changed nothing.

Both halves of that reasoning point the other way here. `_stable_yard` is 335 lines - 2.2x the bar,
29% of the file, the largest function in the engine. And the risk is managed rather than avoided by
**sequencing**: the move lands and is hash-verified first, so the decomposition runs against a tree
already proven byte-identical. A mismatch then has exactly one possible cause.

**Decision**: baseline -> move -> sweep -> decompose -> sweep. Three sweeps, not two.

---

## R5 - The slicing rule protects comments, but only in stage 1 (decision)

The transformer slices `(previous member's end + 1 .. this member's end)` rather than by
`node.lineno`, which is what carries decorators, blank lines, and comment blocks written ABOVE a
member. This lineage runs back to feature 025's `split_settlement.py` and it is the part worth
preserving.

**What is new here**: slicing protects comments only across the MOVE. Stage 2 physically relocates
~90 lines of dated GM-decision comments from inside one function body into seven stage functions, and
no slicing rule can protect that. `civic_grounds.py` holds the densest concentration of
record-the-why prose in the engine - the Qingming Shanghe Tu gate convention, the ox-consumption
arithmetic behind the trough count, the two-round dung-heap clearance history, the "no animals
because the drawn oxen kept reading as muck piles" doctrine.

**Decision**: quickstart step 7 is an explicit comment-survival check - extract every comment line
from the pre-split `_stable_yard` and assert each appears verbatim somewhere in `stable_yard.py`. It
is a set-comparison, not an eyeball.

---

## R6 - Consumer census, and one near-miss worth recording (decision)

22 members. External consumers exist for all of them except three private helpers, and every public
member is reached as a `Settlement` method by `pool/` generators, `tests/`, or the `check_village`
gate's check strings.

Cross-module private consumers, which must keep resolving:

| helper | consumer |
|---|---|
| `_ward_fence_cap` | `settlement/structures/compounds.py`, `tests/settlement/test_water_ways.py` |
| `_way_bearing_near` | `settlement/trades.py` |
| `_stable_yard` | `settlement/core.py` (via `flush_stable_yards`), and by name in `settlement/_geom.py`'s comments |

**The near-miss**: the pre-spec census reported `_way_seat_near` as having ZERO consumers anywhere
in the tree, and the spec's first draft proposed deleting it as a clause-14 dead-member cleanup. It
is live: `_way_bearing_near` calls it, one line, inside the defining file - which the census had
excluded to avoid counting the definition itself as a use.

**Decision**: no member is deleted in this feature. And the general rule, which belongs in any future
clause-14 pass: **a dead-member census MUST count intra-file callers**. Excluding the defining file
is right for finding the definition and wrong for finding the uses. Feature 027's census got this
right because it was censusing an `__init__.py` with no internal calls at all; the same script
pointed at a behavior module would have proposed deleting live code.

Also recorded: unlike 114, **no consumer asserts on the source filename**, so the expected
outside-the-package change count is zero, not one.

---

## R7 - Coverage (record)

`SETTLEMENT_COV_FLOOR = 94`, in `.claude/skills/diagram/Makefile:62` - the SKILL's Makefile, not the
webapp's. (The spec's FR-014 says "the settlement coverage ratchet floor" without naming a file;
this pins it.)

A pure move changes no executable line, so stage 1 cannot move the number. Stage 2 adds seven `def`
statements, which execute at class-creation time and are therefore covered by any test that imports
the package - so the arithmetic predicts a floor unchanged or a hair higher.

**Decision**: any DOWNWARD movement is a defect to investigate, not a floor to adjust. In particular,
a fall would most likely mean a stage function is never called - which is exactly the failure the
contract's third red proof exists to catch.

---

## R8 - Monkeypatching is unaffected (record)

`settlement/CLAUDE.md` warns that submodules bind helper names at import, so patching
`settlement.<name>` does not reach a mixin that already imported it.

Not a hazard here: `civic_grounds.py` has **no module-level functions or constants at all** - the
file is a docstring, imports, and one class. A grep for `civic_grounds.` across the skill returns no
hits outside the file itself. Everything reached from outside goes through `self.` or through
`settlement.Settlement`, and class-level patching is unaffected by the split.

---

## R9 - Principle XII is N/A, argued (record)

The gate asks whether the feature changes what a generator ASSERTS ABOUT THE WORLD. It does not: no
element added or changed, no size, spacing, prevalence or siting rule touched.

The closing bookend - re-examine the RENDERED ARTIFACT - is satisfied more strongly than by eye. An
empty hash diff over every `.png` in the pool proves the depiction is unchanged pixel for pixel,
which is a stronger statement than "a reviewer looked at it and it seemed the same".

The separate risk that the decomposition damages the grounding PROSE is real and is handled by R5's
check, not by this gate.

---

## R10 - The test file stays whole (decision)

`tests/settlement/test_civic_grounds.py` is 489 lines - well under the clause-13 bar, and it is
already dominated by stable-yard tests driven through `flush_stable_yards` (about 25 of them). Since
the decomposition is internal to a private method, those tests should pass unmodified, which is
itself a useful signal.

**Decision**: left whole, plus the guard test. It becomes a split candidate if it passes ~1,000
lines, at which point it mirrors the package - the same threshold 112, 113 and 114 all recorded.

---

## R11 - `wip/shiro-daika.gen.py` gets one run (decision)

Features 112 and 114 excluded it from the byte-identity sweep on cost - research R11 there measured
it at over 6 minutes against ~3 for the whole pool, and it exercised no member the three provincial
cities did not.

**That second half is false for this feature.** `precinct_interior` has exactly one consumer in the
entire tree, and it is `wip/shiro-daika.gen.py`. Excluding it would leave a moved member with no
artifact-level proof at all.

**Decision**: one run, in the stage-1 sweep, against a baseline captured the same way. It is skipped
in the stage-2 sweep, because the decomposition touches only `_stable_yard`, which shiro-daika does
not exercise more than the cities do.

---

## R12 - The RNG bracket is the decomposition's only real risk (decision)

`_stable_yard` does not take an injected RNG. It brackets its whole body:

```python
st = random.getstate()
random.seed(int(abs(sx) * 11 + abs(sy) * 7 + round(r)))
...                       # scatter, shuffle, rails, troughs, heaps
random.setstate(st)
```

and draws from the GLOBAL `random` stream throughout - `random.uniform` and `random.random` in the
litter scatter, `random.shuffle` on the furniture candidate list, and further draws in the rail and
trough passes. The seed is derived from the yard's own position and radius, so each yard is
independently deterministic, but WITHIN a yard the output depends on the exact sequence of draws.

**Consequences for the extraction, all three of which are requirements on the code rather than
observations**:

1. The `getstate` / `seed` / `setstate` bracket stays in the OUTER method. A stage that seeded its
   own stream, or that ran outside the bracket, would leak state into the rest of the map.
2. Stages are called in the original order, and no draw moves across a stage boundary. Extracting a
   block that ends mid-expression is the way this goes wrong.
3. No stage may become eagerly evaluated where it was previously short-circuited. The interior-rail
   pass has bounded retries and the trough pass has a "no reachable well -> dig one" fallback; both
   are branches whose draw count depends on the map. Hoisting a candidate list out of a branch to
   "clean up" the signature would change the draw count on maps that take the other branch.

**Decision**: the sweep after stage 2 is the proof, and it is a strong one precisely BECAUSE the
stream is global and order-sensitive - a faithful extraction is the only way to get an empty diff.
Point 3 is written into the index as a standing warning, since it is the one that looks like an
improvement while being a bug.
