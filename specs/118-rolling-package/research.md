# Phase 0 Research: rolling.py -> rolling/, and roll_village decomposed

Six decisions. Each records what was chosen, why, and what was rejected.

---

## R1 - The partition axis: the CHAIN's links, not a theme

**Decision**: cut along the pipeline `rolling.py` already is - roll -> seed -> shape -> test ->
place -> draw - giving `roll.py`, `seeds.py`, `bundle.py`, `fit.py`, `place.py`, `farmsteads.py`.

**Rationale**: the four prior splits fall into two kinds, and this file is the second kind.
`structures.py` and `civic_grounds.py` were RESIDUE BUCKETS - unrelated subsystems that feature 025
happened to leave together - so 114 and 115 grouped them by "what a session comes here to change"
and accepted deliberately uneven files. `fields/` and `city/` were ONE subsystem cut into stages.
`rolling.py` is the latter: one cohesive chain from "roll a whole village from a seed" down to
"does this rect touch a ditch". So the cut follows the chain.

The test of a partition is whether real tasks stay inside one file. Four recent and pending jobs,
checked against it:

| task | files it would load |
|---|---|
| add a settlement FORM (a new `*_seeds`) | `seeds.py` alone |
| the standing "placer must test the ROTATED footprint it draws" debt (CLAUDE.md, CENTER vs FOOTPRINT item 3) | `fit.py` alone - `_bundle_common_fits` is named as the three-line landing site |
| the collision-circle swap (item 2) | `fit.py` + `place.py` |
| change what the flush DRAWS (the kura side, the garden relaxation) | `farmsteads.py` alone |
| tune a `roll_village` phase | `roll.py` alone |

**Alternatives considered**:

- **By caller (nucleated vs dispersed vs legacy).** Rejected: the two homestead styles share almost
  every predicate - `_bundle_geom` branches internally, `_rect_blocked` is common - so this axis
  would duplicate the shared half or leave a "common" module holding most of the file.
- **Two files, solver and everything-else.** Rejected: the solver alone is over 600 lines, which
  fails the clause-13 read-cost argument this feature exists to satisfy.
- **Leave `roll_village` in `__init__.py`.** Rejected on the sibling packages' own rule: no logic
  in `__init__.py`, ever. It is the composition and nothing else.

---

## R2 - `roll_village`'s stages: the banner comments were already the design

**Decision**: seven stage methods behind a thin orchestrator, cut at the `# ---` banner comments
the function already carries.

**Rationale**: the function is not tangled - it is a straight-line pipeline that already announces
its own phases in comments (`--- roll the knobs ---`, `--- the field: sluice from the water source,
then the comb ---`, `--- seat the cluster on the field edge ---`, `--- a COMMUNAL windward
windbreak BEHIND the cluster ---`, `--- village-only civic features ---`). Cutting anywhere else
would be inventing a structure over one that exists.

Feature 115's `_stable_yard` decomposition is the precedent and also the warning: it "looked like
seven banner-marked blocks and was actually eight closures over a shared lattice", which forced a
mid-flight plan amendment. So the AST walk it prescribes was run FIRST here, and the answer is
**one** closure (`to_screen`) over six values. That is a lattice small enough to make explicit
(R3) rather than a hazard.

**Alternatives considered**:

- **Leave it whole with a clause-12 justification annotation.** Defensible on the constitution's
  literal measure - 117 statements is well inside the "suspect" bar - and rejected because the GM's
  request names function size, because `future-work.md` has this function queued by name, and
  because the annotation would have to argue against the project's own converged practice.
- **Extract only the two biggest blocks.** Rejected: it leaves an orchestrator still over the bar
  and produces an arbitrary boundary a reader cannot predict.

---

## R3 - The frame: an explicit value object, not a closure and not `self` state

**Decision**: a frozen dataclass `_MarginFrame(ccx, ccy, alx, aly, tdx, tdy, lat, dep)` with a
`to_screen(p)` method, constructed by the frame stage and passed to the stages that need it.

**Rationale**: `to_screen` closes over exactly the values that define the margin frame, so the
closure was already a value object written implicitly. Making it explicit is what lets the stages
be separate methods at all.

Frozen, and NOT stored on `self`, for the reason the engine keeps relearning: mutable state on
`Settlement` that only some phases set is how "a check that never RUNS looks exactly like a check
that passes" happens one level down. A stage that needs the frame takes it as a parameter and
cannot silently run without it - `mypy --strict` says so at edit time.

**Alternatives considered**:

- **Keep `to_screen` as a closure and make the stages nested functions.** Rejected: nested
  functions are not separately invocable, which is the architectural cost clause 12 names.
- **Set `self._frame` in the frame stage.** Rejected as above - and it would leak per-map scratch
  state onto a class whose `__init__` is already the map's public contract.
- **A plain tuple.** Rejected: eight positional floats at four call sites is exactly the shape that
  produces a silent transposition, and the engine has a documented history of measuring the wrong
  ring / the wrong footprint for want of a name.

---

## R4 - `_NUC_SIDES` stays with the nucleated placer

**Decision**: the class-level constant `_NUC_SIDES` goes to `place.py`, its source neighborhood,
and `_fits_any_side` in `fit.py` reads it through `self.`.

**Rationale**: its two consumers land in different modules, so one of them is reaching across
whatever we choose. `_place_bundle_nucleated` is the member the constant exists for - it is the
garden-side PREFERENCE ORDER the nucleated placer walks - while `_fits_any_side` merely tests the
same list. Placement follows the primary caller, which is the rule 116 used for `_hall_caption_y`.
The cross-module read costs nothing: every sub-mixin is a base of the same `Settlement`, so
`self._NUC_SIDES` needs no import.

**Alternatives considered**: `bundle.py`, on the argument that it names garden SIDES and
`_bundle_geom` takes `garden_side` as a parameter. Rejected - `_bundle_geom` never references the
constant, so that would put it in the one module that does not use it.

---

## R5 - The oracle: byte-identity across the whole pool, frozen maps INCLUDED

**Decision**: regenerate every `pool/*/*.gen.py` into a scratch copy of the tree and hash every
produced artifact against a pre-change baseline, with `--frozen-ok` so the frozen legacy maps run
too.

**Rationale**: this is a refactor, so the correct outcome is not "still defensible" but "the same
bytes", and that is mechanically checkable. It is also why this feature needs no
`settlement-review` pass - the same reasoning the `SeatMemo` optimization recorded: a change that
is output-preserving by construction has a mechanical oracle, and a judgment pass adds nothing to
a byte comparison.

**The `--frozen-ok` half is not a detail.** All three `roll_village` callers - `honda`, `shimizu`,
`kikuta` - are frozen hand-authored maps. A sweep that honored the freeze would regenerate the
scripted hamlets, exercise `farmsteads()` and the bundle solver thoroughly, and exercise this
feature's headline function **not at all**. 116 hit the same shape (`farm_wells`, `small_shrine`,
`torii_even` and `forest` are mostly reached by frozen maps) and reached the same conclusion.

The sweep runs in a SCRATCH COPY, so the committed pool artifacts are never touched - the freeze's
own rule that "any test or tool that runs a live gen must leave the committed bytes exactly as it
found them".

**Alternatives considered**:

- **Trust `make done`.** Insufficient: the gate rides the generation cache, and this change moves
  module-level source, which correctly invalidates every key - but a green gate proves the CHECKS
  pass, not that the bytes are the same bytes. A map can move and still be legal.
- **Sweep the scripted maps only.** Rejected for the reason above.

---

## R6 - Two commits, split before decomposition

**Decision**: land the package split first, sweep, then land the `roll_village` decomposition and
sweep again.

**Rationale**: the two halves have different risk profiles - a member move cannot change behavior,
a function rewrite can - and combining them makes a failure undiagnosable. If one artifact byte
moves after a combined change, the suspect set is 43 moved members plus a rewritten 256-line
function. Split first and each sweep names its own cause. The cost is one extra sweep, which is
minutes.

**Alternatives considered**: one commit, on the argument that the intermediate state ships a
package whose `roll.py` is one 256-line function. Rejected - that intermediate state is committed
in the clone, not pushed to main, so it is never a state anyone else sees, and mid-task commits are
explicitly sacred in this project.

---

## Pre-flight measurements (taken before the spec was written)

Both are the checks `future-work.md` demands of a decomposing session, and one of them overturned
the prediction on file.

- **RNG surface.** `roll_village` makes ZERO draws from the main `random` stream; all four
  generators it constructs are seeded from `self.seed`, and the six `self.resolve()` knob calls go
  through `scope_seed`/`knob_rng`. `future-work.md` predicted the opposite ("its draw density is
  likely much higher and the answer may well go the other way"), which is precisely why the rule
  says to measure rather than reason. **This finding is the feature's whole safety argument and is
  being migrated into `future-work.md` rather than deleted with the task.**
- **Closures.** One nested `FunctionDef`, `to_screen`, closing over six values. Handled by R3.
