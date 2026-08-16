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

**Decision, as planned**: one run, in the stage-1 sweep, against a baseline captured the same way.

**AMENDED at implementation time - the run was CUT.** The plan budgeted "over 6 minutes" on the
authority of feature 112 research R11. Reading R11 again once the run was actually underway shows
that figure is an **aborted lower bound, not a measurement**: 112 stopped the map at six minutes
"without producing a single line of output" and never learned how long it takes. This feature got it
to **10 minutes 35 seconds of CPU time, still at 100% and still with no output**, before stopping it
for the same reason. Nobody has ever let `wip/shiro-daika.gen.py` finish, so its true cost is
unknown and unbounded, and "budget over 6 minutes" was never a real budget.

**What replaces it as proof for `precinct_interior`:**

- `tests/settlement/test_civic_grounds.py::test_precinct_interior_draws_both_rear_orientations_and_the_graveyard_claim`
  exercises the member directly, both `rear` branches and the graveyard claim, and passes after the
  move.
- The move's textual purity is proven independently of any artifact: `comment lines lost: 0`, and an
  AST comparison of every member's first-argument annotation between the pre-split file and the
  package returns `pre == post` exactly.

That is weaker than a byte-identical PNG and it is honestly weaker - but the marginal value of the
artifact proof for ONE member already covered by a passing unit test does not justify blocking a
feature on a run of unknown duration. **FR-005 is not satisfied as written.** The right resolution
is either to run that map to completion once, unattended, and record its actual cost - which would
finally give 112's open question an answer - or to profile why a capital map is more than 3x the
cost of the entire 28-map pool. Both are follow-ups, not blockers, and both are recorded in
`future-work.md`.

The stage-2 sweep excludes it either way, because the decomposition touches only `_stable_yard`,
which shiro-daika does not exercise more than the cities do.

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

---

## R13 - `_stable_yard` is CLOSURE-heavy, not block-structured (decision, found at implementation time)

**What the plan assumed.** Plan.md and data-model.md Part 2 treat the seven banner comments as
marking seven straight-line blocks, extractable the way feature 111 extracted `hamletgen.py`'s
stages - each block reads some inputs, appends some output, and hands off.

**What the code actually is.** An AST walk of the method's top-level statements (run at T026 prep)
finds **eight nested `def`s** inside the 335-line body, each capturing a different slice of local
state:

| closure | lines | captures |
|---|---|---|
| `clear` | 77-88 | `corridors`, `wallp`, the keep-out list |
| `take` | 127-136 | `clear`, the furniture ring candidates |
| `rail_rec` | 150-153 | yard geometry |
| `draw_hitch` | 155-163 | `rail_rec`, the output stream |
| `_rail_clear_of_heaps` | 171-172 | `prior_heaps` |
| `_glyph_free` | 184-194 | `prior_boxes`, `prior_rails` |
| `beside` | 256-283 | `clear`, `_glyph_free`, trough geometry |
| `_clear_of_rails` | 322-327 | `all_rails` |

So the seams are real but the blocks are not independent: the "stages" share a lattice of predicates
that are defined once and read by every later stage. `beside` (the trough siter) alone reads `clear`
from stage 1 and `_glyph_free` from stage 4.

**Why this matters more than it looks.** A naive extraction into seven methods has to thread that
captured state through explicit parameters, and every threading decision is a chance to change WHEN
a predicate is evaluated - which is rule 3's failure mode (a branch that was short-circuited becomes
eager, the draw count changes, and the map changes on a minority of seeds). The RNG proof would
catch it, but only after the fact, and the diff would not say which threading decision did it.

**Options, none of which the plan chose because the plan did not know:**

- **(a) A yard-context dataclass.** One `_YardCtx` holding `corridors`, `wallp`, the keep-out list,
  `prior_boxes`, `prior_rails`, `prior_heaps`, and the output stream; the eight predicates become
  methods on it; the seven stages become methods taking it. Faithful, and it makes the shared
  lattice explicit rather than implicit - which is arguably the real readability win. Largest
  change, and the one most likely to need two passes.
- **(b) Extract only the four stages that are genuinely self-contained** (litter, road rail,
  watering, heaps), leave the predicate lattice and the furniture seater in the outer method.
  Lands the outer method at roughly 120-150 lines - under the clause-12 bar - for maybe a third of
  the work and a fraction of the risk. Does not produce seven named stages.
- **(c) Do nothing in this feature.** Ship the package split (which is the clause-13 debt and the
  stated primary motivation), record the clause-12 debt, and give the decomposition its own feature
  with its own baseline.

**Decision: (a), the yard-context dataclass. GM-chosen, 2026-08-16.** The question was put to the
GM rather than decided here, per CLAUDE.md's stop-and-ask threshold - options (a) and (b) differ in
what the resulting code teaches a reader, which is a design question rather than a mechanical one,
and (a) is an hour-plus that could be thrown away. The session's own recommendation was (b), the
partial extract, on risk grounds; the GM took (a).

The reason (a) is the better call despite the risk: the shared predicate lattice IS the thing that
makes this function hard to read, and (b) leaves it exactly as it was while making the file look
decomposed. A `_YardCtx` that names `clear`, `glyph_free` and the three prior-yard collections turns
an implicit capture graph into a declared object, which is what a future reader actually needs.

**How the RNG risk is contained under (a)**, since it is now the accepted risk rather than the
avoided one:

- The context object is BUILT once, at the top of the outer method, in the same order the closures
  were previously defined. Construction consumes no RNG - none of the eight closures draws at
  definition time, only at call time - so building it early cannot move a draw.
- Predicates become `_YardCtx` METHODS with the same bodies and the same call sites. A predicate
  that was lazily evaluated inside a branch stays inside that branch; only its definition moves.
- The stages are extracted in source order, one at a time, with the ~25 stable-yard unit tests run
  after each (tasks T031). A failure then localizes to the stage just extracted.
- The byte-identity sweep remains the proof, and under (a) it is doing more work than it would have
  under (b) - which is the trade the GM accepted.

**What is NOT in doubt**: US1, US2 and US4 are unaffected. The package split is done and verified
independently of this, which is the sequencing (research R4) working as designed - the clause-13
debt is paid whether or not the clause-12 debt is paid in the same feature.

---

## R14 - What the implementation learned that the plan got wrong (record)

Written at the end, per tasks T043. Four things, in descending order of how much they cost.

**1. The decomposition's shape (R13, already amended above).** The plan modeled `_stable_yard` as
seven banner-marked straight-line blocks; it was eight closures over a shared lattice of locals.
Found by an AST walk that took one command, and it should have been in Phase 0 rather than
discovered at implementation time. **The general rule for the next clause-12 job: before promising
a stage decomposition, walk the function for nested `FunctionDef`s.** A function with closures is
a different kind of refactor from a function with blocks, and the plan should say which it is.

**2. The RNG risk was over-estimated, and measuring it was cheap.** R12 treated the global stream
as a lattice-wide hazard. A grep of every `random.*` call site - two minutes - showed four sites
total and that stages 4-7 draw nothing, collapsing the whole hazard to one adjacency (the litter
draws vs `seat_init`'s shuffle). That measurement should have been in R12 itself. It is the
difference between "this refactor is dangerous" and "this refactor has one orderable constraint",
and it was available for free before the GM was asked to choose an option.

**3. `wip/shiro-daika`'s cost was taken on faith from a prior spec** and turned out to be an
aborted lower bound rather than a measurement (R11, amended). **A number quoted from another
feature's research is a claim, not a fact** - especially a number that reads like a timeout.

**4. A style check that tests formatting instead of meaning.** The first T012 pass verified
`self: "Settlement"` annotations by regex and reported 0 in every module, which looked like the
transformer had stripped them. It had not: this file writes the annotation unquoted, and one `def`
wraps across lines. Rewritten as an AST comparison of first-argument annotations between the
pre-split file and the package (`22 pre, 22 post, pre == post`), which is the assertion actually
worth making. A regex over a signature style fails on formatting and passes on meaning-loss - the
wrong way round.

**What the plan got RIGHT, worth keeping for the next one:** sequencing the move and the
decomposition as separately-swept commits. When the second sweep came back byte-identical there was
no ambiguity about what it proved, and had it come back dirty the cause could only have been the
decomposition. That is the single most valuable structural decision in this feature.

**No member's module assignment moved** from data-model.md Part 1, and no stage boundary had to move
to preserve RNG order. One file was ADDED that the plan did not have: `_yardctx.py`, because the
decomposition took `stable_yard.py` to 421 lines, over SC-001's 400 - split rather than waived.
