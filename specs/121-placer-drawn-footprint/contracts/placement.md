# Contract: what the placer may measure, and with what

This is the internal contract feature 121 must not violate. It restates the project's centers/footprints doctrine for the two call sites being changed, so a future reader can check the code against a rule rather than against a memory.

## C1. The prefilter prunes; it never decides

```
reach box (circumscribed, generous)  ->  candidate set  ->  exact test (rotated quads)  ->  verdict
```

**Invariant**: the prefilter's extent must be **greater than or equal to** the exact test's reach, always.

**Why**: over-stating an extent can only ADMIT a pair the exact test then rejects. Under-stating it starts rejecting pairs before the exact test ever runs - the index silently becomes the decision-maker, and the exact test becomes decoration.

**Consequence for this feature**: `_reach_index` / `_reach_boxed` keep the half-diagonal (`hypot(w, h) / 2 + 4`). They are **not** part of item 2. Only the verdict inside the loop changes. A change that "tidies up" the reach box to match the new exact test is a bug, not a cleanup.

**Ratcheted by**: the existing prefilter entries. Any new call site added here gets one.

## C2. A gap verdict reads real rotated corners

A rule that answers *"do these overlap"* or *"is there N ft of clearance"* is measured with `sat_overlap` / `edge_gap` on real rotated corner quads. **Never** a center. **Never** a circumscribed radius.

The three conventions that were live before this doctrine, and what each costs:

| convention | error |
|---|---|
| raw center-to-center | understates clearance by the sum of both half-extents - a rule promising 120 ft delivered ~60 |
| `0.5 * hypot(w, h)` (half-diagonal) | over by up to 41% on a square, more on a long rect |
| `max(w, h) / 2` | the same error, differently sized |

The error **flips sign** with the rule - subtracting too much makes a "must be far" rule strict and a "must be near" rule lenient - so none of them is even a uniform safety margin.

## C3. Rotation is part of the footprint

A building drawn at 90 or 180 degrees has its placement-frame `w` and `h` **exchanged**; a house is drawn at a few degrees of rake. An axis-aligned test on placement dimensions is therefore wrong for anything rotated.

This is the specific reason item 2 cannot ship first: the circumscribed circle is rotation-invariant, and that invariance is what has been absorbing item 3. Replacing it with an axis-aligned box gap - tried 2026-08-08 - produced five gate failures including two genuine overlaps, a fire tower on a wellhead, and a well inside a building.

**Order is therefore normative, not stylistic**: rotated-footprint plumbing (item 3) lands and is green before the verdict swap (item 2) is attempted.

## C4. A surface is not a clearance

| kind | examples | measured by |
|---|---|---|
| **surface** | a lane's drawn tread, a building's walls | the whole rotated footprint |
| **clearance** | a way's corridor, a caption band, a civic apron, a fence standoff | the candidate's center |

Applying the footprint test to a clearance has a recorded price: it cost Nagahara a well and pushed Hoshizora's punishment ground off its street. The split is the fix; conflating them was the bug.

**Consequence for this feature**: item 3 gives the bundle path the *tread* test. It does **not** give it a footprint test against corridors.

## C5. Sanctioned abutment survives

Two things are allowed to touch and must stay allowed after the verdict tightens:

- a grove may **hug** a paddy bund (it is tested against everything but the fields and the water lines);
- adjacent groves may **abut** into a single shared windbreak (a sliver of tolerance exists for exactly this).

A tightened exact test that forbids either has broken a feature, not fixed one. Each gets a ratchet entry so a passing cohort is not the only thing standing between us and losing them.

## C6. Every new distance rule joins the table and gets a ratchet

A rule that lives only in a document has already been proven not to hold. Any distance rule this feature adds or moves is classified into its doctrine row (gap verdict / classification / association-reach / prefilter / point fixture) in a comment **at the point of the test**, and gains an entry in the gap-verdict ratchet.

The ratchet is known to have teeth: of its nine entries, reverting the helper to raw centers breaks six and reverting it to circumscribed radii breaks the other three - every entry is caught by one revert or the other. A new entry that survives both reverts is not testing anything.

## C7. One measurement, not several

`edge_gap` is the only exact footprint-gap helper; `sat_overlap` is the only overlap predicate. **Do not write a third.** Two correct helpers for one question is how the three wrong conventions in C2 got started - a duplicate was folded back in on 2026-07-27 for exactly this reason.
