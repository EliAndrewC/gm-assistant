# Contract: the composed `CivicGroundsMixin` surface

The package is correct when the composed class is indistinguishable from the pre-split class to
every consumer. This contract states what "indistinguishable" means and how each clause is proven.

Each proof is **observed failing before it is trusted** (Principle X, red-green). A guard test that
has never been red is a guard test nobody has tested.

---

## C1 - Completeness

Every one of the 22 pre-split member names resolves on the composed `CivicGroundsMixin`.

**Form**: a SUBSET assertion against a frozen census, not an equality assertion - so adding a member
later needs no bookkeeping, while dropping one still fails.

**Red proof**: delete one method from one sub-mixin; the guard must fail naming that method.

**Why it matters**: a member silently dropped by the transformer produces a package that imports
cleanly, type-checks cleanly and draws nothing. It surfaces only when whichever generator calls it
happens to run - and for `precinct_interior`, that is one `wip/` map nobody runs by default.

---

## C2 - No collisions

No two sub-mixins define the same name.

**Form**: a pairwise check over the five sub-mixins' own `__dict__` keys.

**Red proof**: define `_way_bearing_near` in a second sub-mixin; the guard must fail naming the
duplicate and both classes.

**Why it matters**: a name defined twice produces a working import, a clean `mypy --strict`, and one
silently dead implementation, because the MRO just picks the first base. Nothing else in the gate
can see this.

---

## C3 - Resolution on `Settlement` itself

All 22 names resolve on `Settlement`, not merely on `CivicGroundsMixin`.

**Form**: the same census asserted against `Settlement` directly.

**Red proof**: covered by C1's red proof, which fails both assertions; recorded separately because a
future re-cut of `core.py`'s base list could break C3 while leaving C1 green.

**Why it matters**: consumers reach these through `Settlement` - `structures/compounds.py` calls
`self._ward_fence_cap`, `trades.py` calls `self._way_bearing_near`, and the pool generators call the
public members. C1 alone would pass even if the mixin were dropped from the base list.

---

## C4 - Every extracted stage is reached (new in this feature)

Each of the seven `_stable_yard` stages is executed at least once by the test suite.

**Form**: coverage over `stable_yard.py` shows no stage function body wholly unexecuted. The
existing ~25 stable-yard tests drive the yard through `flush_stable_yards`, so this should hold
without new tests; if a stage is unreached, that is the finding.

**Red proof**: comment out one stage call in the outer method; coverage must show that stage's body
unexecuted (and, separately, the byte-identity sweep must go dirty).

**Why it matters**: C1-C3 are inherited from feature 114 and are all about the MOVE. They cannot see
the decomposition's failure mode, which is a stage that exists, type-checks, and is never called.
The byte-identity sweep would catch that too - but only for stages that affect every map, and stage
6's dig-your-own-well fallback fires on a minority of them.

---

## C5 - Byte-identity

Every regenerated `pool/**` artifact is byte-identical to the pre-split baseline, at both
checkpoints (post-move, post-decomposition), with frozen legacy maps included.

**Form**: `sha256sum` set comparison, per quickstart steps 1, 5 and 8.

**Red proof**: not applicable - this one is proven by construction each time it runs. What IS proven
first (quickstart step 0) is that the oracle can see the file at all: `gencache.engine_files()` must
list `civic_grounds.py`, or the sweep would return stale cached artifacts and pass vacuously.

---

## C6 - `core.py` untouched

`git diff --stat -- settlement/core.py` prints nothing.

**Form**: exact, not inspection.

**Why it matters**: `core.py` is where the DRAW ORDER contract lives. Every previous split in this
package kept it byte-unchanged, and that consistency is what lets a reader trust that a split never
reorders anything.
