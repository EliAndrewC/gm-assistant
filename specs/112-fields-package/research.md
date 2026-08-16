# Phase 0 Research: settlement/fields.py -> settlement/fields/

All four questions the plan invocation raised are resolved here. Nothing is left NEEDS
CLARIFICATION.

## R1. The partition is derived from the intra-class call graph, not chosen by theme

**Decision**: four sub-mixins - `paddy.py`, `comb.py`, `landuse.py`, `features.py`.

**Rationale**: `FieldsMixin`'s 24 methods were analyzed for `self.<method>` edges among themselves.
The graph is almost perfectly clustered - four groups, each with one or two externally-called entry
points and a tail of private helpers reached only from inside the group:

| group | entry points | private helpers reached only from within the group |
|---|---|---|
| paddy | `paddy_field`, `water_field`, `fallow_field` | `_paddy_plots`, `_split_convex`, `_taxfree_plots`, `_rows`, `_fallow_patch`, `_paddy_surface` |
| comb | `draw_comb_field`, `comb_base_fill`, `bund_junctions` | `_draw_furrows` |
| land use | `apply_land_use` | `_mulberry_rows`, `_pick_overlay_plots` |
| features | `pond`, `crescent_pond` | `_paddy_features`, `_plot_center_span`, `_plot_pond`, `_plot_rock`, `_plot_grave_island`, `_rounded_pond` |

Only **two** helper edges cross a group boundary, and both are recorded below with the home chosen
and why. Deriving the seams from the call graph rather than from the method names is the same
discipline as "derive, don't pin": a thematic guess would have put the three pond drawers in three
different places, and the graph shows they belong together.

**Alternatives considered**:

- **Split by the file's three banner comments** (`# ---- fields` at 35, `# ---- water` at 489,
  `# ---- feature 012 ...` at 946). Rejected: the banners divide the file into 454 / 457 / 558
  lines, which is a legal split, but the third region mixes the feature-012 plot features with the
  whole 266-line land-use overlay subsystem, which has nothing to do with them. The banners mark
  when code was written, not what it is.
- **Two modules only** (`fields.py` + `overlays.py`, roughly 950 / 550). Rejected: it clears the
  clause-13 bar on a technicality while leaving the largest module at 950 lines, i.e. it buys almost
  none of the token saving the feature exists for.
- **A shared `_helpers.py`** for the cross-group helpers. Rejected on R2's finding: cross-group
  calls need no import, so a helpers module would add a file and an import edge to solve a problem
  that does not exist.

## R2. Cross-group helper calls cost nothing, so each helper lands with its primary user

**Decision**: no shared-helper module. Each helper's TEXT lives in exactly one submodule, chosen by
primary caller; cross-group calls stay `self.<helper>(...)` and are resolved by the composed class.

**Rationale**: every sub-mixin is a base of the same `Settlement`, so `self._paddy_surface(...)`
resolves through the MRO wherever the caller's text happens to live. This is not a workaround - it
is how the parent `settlement/` package already works, and the engine already relies on it across
module boundaries: `settlement/land.py` calls `self._draw_furrows(...)`, which is defined in
`fields.py` today and will be defined in `fields/comb.py` afterward, with no import either way.

The two cross-group edges and their resolved homes:

| helper | callers | home | why |
|---|---|---|---|
| `_paddy_surface` | `paddy_field`, `water_field` (paddy), `apply_land_use` (land use) | `paddy.py` | two of three callers are paddy, and it renders the paddy SURFACE - the land-use overlay is a consumer of paddy rendering, not a co-owner of it |
| `_rounded_pond` | `apply_land_use` (land use) only | `features.py` | its only caller is in land use, but it is a pond GLYPH and its three siblings (`pond`, `crescent_pond`, `_plot_pond`) all live in `features.py`. A reader looking for how a pond is drawn must find all four in one place; splitting one off by caller would hide it |

`_rounded_pond` is the deliberate exception to "home = primary caller", and it is recorded here so
the next reader does not "fix" it back.

## R3. `pond` is a public entry point, not the comb builder's private helper

**Decision**: `pond`, `crescent_pond` and `_rounded_pond` go in `features.py`, not in `comb.py`.

**Rationale**: the intra-class graph shows `pond` called only by `draw_comb_field`, which would put
it in `comb.py` on the primary-caller rule. The external census contradicts that: `pond` is called
from **13 sites outside the class**, including `hamletgen/sink.py` and ten pool gens. It is a public
water glyph that the comb builder happens to also use. Burying it in the comb-field module would
mean a session looking for "how is a pond drawn" opens the comb-field builder - exactly the
navigation failure the `CLAUDE.md` index exists to prevent.

**The general lesson, worth carrying**: the intra-class call graph is the right tool for placing
PRIVATE helpers and the wrong tool for placing PUBLIC entry points. Census the external callers
before trusting a group boundary derived from internal edges alone.

## R4. The byte-identity oracle must include the frozen legacy gens, run in scratch

**Decision**: capture the baseline from a scratch copy of the pre-split tree, sweeping **every** pool
generator - live scripted maps and frozen legacy maps alike - plus `wip/shiro-daika.gen.py`. Compare
after each stage. Nothing frozen is regenerated in place and nothing frozen is committed.

**Rationale**: the live scripted pool is four `valley_paddy` hamlets, and the census shows what they
reach. `draw_comb_field` IS exercised live (`hamletgen/water.py` calls it), so the comb wing has a
live oracle. `apply_land_use` is a different story: its callers are `settlement/rolling.py`, the
frozen `pool/hamlets/kuwabata.gen.py`, and one `check_village` segment. Whether the live hamlet path
reaches it depends on `roll_village`, which the scripted hamlets do not use. So decomposing a
266-line method with no manifest-level oracle at all is the risk this decision removes: Kuwabata,
Tango, Minami and Nagahara are the only artifacts that prove the overlay code still draws what it
drew.

Running a frozen gen as a differential oracle does not violate the freeze. The freeze (skill
`CLAUDE.md`, "The legacy pool is FROZEN") forbids maintaining frozen maps against new rules,
re-gating them, and committing regenerated bytes. It does not forbid reading them. The scratch-tree
method is the one features 110 and 111 used, and for the same reason: the committed manifests are
not a valid baseline on their own, because the engine may have drifted since they were committed -
only a pre-change run of the same tree is.

**Alternatives considered**:

- **Committed manifests as the baseline.** Rejected: proven unreliable by feature 110's research
  R3. A mismatch would be indistinguishable from a refactor bug.
- **Live scripted hamlets only.** Rejected: leaves `apply_land_use` unverified, which is 266 of the
  773 lines Stage 2 touches.
- **Unit tests as the sole Stage 2 oracle.** Rejected as insufficient alone: `test_fields.py` is
  475 lines against a 1,511-line subsystem inside a package sitting at a 94% coverage floor, so
  line coverage does not imply the drawn geometry is unchanged. Used as a supplement, not a
  substitute.

## R5. Stage sequencing: pure move first, decomposition second, verified between

**Decision**: Stage 1 (move, zero logic edits) lands and is verified before any of Stage 2's three
decompositions begin; each decomposition is verified on its own.

**Rationale**: the two stages have different failure modes and mixing them destroys the diagnostic.
A pure move that breaks byte-identity means the composition or an import binding is wrong; a
decomposition that breaks it means a draw was reordered. Verified separately, a red sweep names its
own cause. Verified together, it does not. This is the same reason feature 111 sequenced its P1
harness ahead of its P2 decomposition.

Within Stage 2 the three methods are done one at a time, sweeping after each, for the same reason -
and because RNG draw order is the specific hazard: the engine's randomness is positional or scoped,
so an extraction that moves a `random` call relative to another changes every downstream coordinate.
The sweep catches it; doing three at once means bisecting to find which.

## R6. Composition mechanism and its guard

**Decision**: `fields/__init__.py` does four `from .x import XMixin` and one
`class FieldsMixin(PaddyMixin, CombMixin, LandUseMixin, FieldFeaturesMixin): pass`, with a docstring
saying the class exists only to preserve `core.py`'s single import. The guard test asserts the
composed class exposes exactly the 24 method names the pre-split class exposed, and that no two
sub-mixins define the same name.

**Rationale**: composing in the package `__init__` keeps `core.py` byte-unchanged, which is FR-002
and is worth more than the alternative's tidiness. The name-collision half of the guard matters
because MRO resolves a duplicate silently: two sub-mixins defining `_rows` would produce a working
import, a passing type check, and one dead implementation.

**Alternatives considered**:

- **Add the four sub-mixins directly to `core.py`'s base list.** Rejected: it edits `core.py`
  (violating FR-002 and SC-002), and it leaks the internal partition into the class declaration, so
  a future re-partition would touch `core.py` again.
- **`FieldsMixin = type("FieldsMixin", (...), {})`.** Rejected: identical semantics, worse
  readability, and `mypy --strict` cannot follow it.

## R7. The transformer: adapt 025's, do not re-derive it

**Decision**: reuse `specs/025-human-scale-splits/split_settlement.py` as the mechanical exemplar,
adapted for a class-to-subpackage split rather than a module-to-package one.

**Rationale**: 025 solved the same problem one level up - it carved `settlement.py` into mixin
modules and its manifest rows are exactly `(module, mixin_name, last_method)` triples, one of which
is `("fields", "FieldsMixin", "crescent_pond")`. The per-method extraction, the import header
generation and the `TYPE_CHECKING` + `self: "Settlement"` annotation pattern all carry over. What
differs is that the source is a class body rather than a module body, so slices are taken between
method boundaries rather than between top-level statements.

**The import-header rule**: each new submodule imports only the names its own methods use. Do not
copy the parent header wholesale - `ruff` will flag the unused ones, and an over-broad header
re-creates the module-level binding hazard that `settlement/CLAUDE.md` warns about (a name bound in
a module nobody patches is harmless; a name bound in four modules when a test patches one is a bug
waiting).

## R8. Consumer census result

**Decision**: no consumer file changes. Verified, not assumed.

**Rationale**: the census run before planning found:

- `FieldsMixin` the name: **one** consumer, `settlement/core.py` (one import, one base-list mention).
- `settlement.fields` module-level names reached from outside: **none**. No test, tool or gen
  imports from the module or patches a name in it.
- Private methods reached from outside the class: `_taxfree_plots`, `_paddy_features`,
  `_mulberry_rows`, `_pick_overlay_plots` (all from `test_settlement/test_fields.py`, all via
  `s.<name>` on a `Settlement` instance) and `_draw_furrows` (from `settlement/land.py`, via
  `self.`). Every one resolves through the composed class regardless of which submodule holds it, so
  none constrains the partition.
- Public methods reached from outside: 8 to 21 call sites each across pool gens, `hamletgen/`,
  `settlement/land.py`, `settlement/rolling.py`, two `check_village` segments and the tests. All are
  attribute access on a `Settlement` instance; none is an import.

**The one loose end, checked and CLOSED**: `settlement/__init__.py` re-exports the parent
package's public surface, so if it re-exported anything from `.fields` the new package `__init__`
would have to reproduce it. It does not - its re-export block draws only from `._geom` and
`._knobs`, and `fields.py` has no module-level name other than the class itself. Nothing to
preserve; the package `__init__` owes the parent nothing beyond the name `FieldsMixin`.

## R9. Two things the plan's method-only model missed, found by the transformer

Recorded during implementation, per the "record every resolved decision in the artifact where it
arose" rule.

**The class body is not only methods.** `FieldsMixin` carries three class-level ASSIGNMENTS -
`_PADDY_POND_KINDS`, `_PADDY_ROCK_KINDS`, `_PADDY_GRAVE_KINDS`, the feature-012 archetype matrix
gating which field kinds get an in-field pond, rock outcrop or grave island. data-model.md's four
tables listed 24 methods and no attributes, so a transformer that sliced the class body by its
function definitions would have dropped all three silently: the split would import, type-check and
pass every existing test, and the next comb-field regen would raise `AttributeError` deep inside
`_paddy_features`. They belong with the plot features they gate, so they are in `features.py`.

Two guards now hold this, because the surface test cannot see attributes: the transformer REFUSES
to run if the partition does not cover every class-body member by name (not just every method), and
`test_feature_012_archetype_constants_survived_the_split` asserts the three tuples resolve on
`Settlement`.

**Section-divider comments had to be triaged, not moved verbatim.** The file carried three `# ----`
banners. `# ---- fields` and `# ---- water` describe the OLD file's layout and would be actively
false once the sections live in different files (the "water" section's members split across
`features.py` and `comb.py`), so they are dropped and each module's docstring says the same thing
for its own contents. The `# ---- feature 012: ...` banner is different in kind - six lines of real
grounding documentation naming the archetype matrix, its research spec, and a disclosed calibrated
liberty the GM approved - so it travels into `features.py` with the code it documents. Invariant 5
("method text moves verbatim") is about CODE and its researched why-comments; a layout divider that
has become false is not covered by it.

**Import headers: copied wholesale, then pruned by ruff.** R7 said each module should import only
what its own methods use, and warned against copying the parent header. The mechanical route to
R7's end state is to copy the header into each module and then run
`ruff check --select F401 --fix`, which removed 63 imports across the four files. That reaches
exactly the state R7 specifies without the transformer having to model Python name resolution, and
ruff is a more reliable judge of "is this name used" than a hand-written AST walk.

## R10. The guard test cannot be proven red before the package exists

tasks.md sequenced the red proof (T005) ahead of the transformer (T007). That is not executable:
the guard's subject is the COMPOSED class and its four sub-mixins, so against a tree where
`fields.py` is still a single file the test fails with `ModuleNotFoundError` - which proves nothing
about the assertions. Corrected order, which keeps the substance of red-green intact: run the
transformer, write the guard, then prove it fires by two deliberate breakages before trusting it.
Both were observed and their failure text is recorded in tasks.md's Notes.

The general form, worth carrying to the next split: a guard on a REFACTOR's output is proven red by
BREAKING the refactor, not by predating it. Red-green on new behavior means "the test fails before
the code exists"; red-green on a structural invariant means "the test fails when the invariant is
violated", and the violation has to be constructible.

## R11. The oracle is the 19-map POOL, not pool + the capital WIP - a wall-clock decision

R4 specified sweeping "every pool generator ... plus `wip/shiro-daika.gen.py`". The WIP capital was
dropped from the oracle during implementation, deliberately, and this records why so a later reader
does not read it as an oversight.

**What happened**: the pool half of the baseline swept 28 maps in about 3 minutes. `shiro-daika`
then ran for more than 6 minutes without producing a single line of output before it was stopped -
it is a capital-scale gen whose housing pass is still open (`wip/shiro-daika.notes.md`), and its
artifacts are gitignored, so it was generating from nothing.

**Why dropping it is safe**: the cost is not one sweep, it is FIVE - the baseline plus one after
Stage 1 and one after each of Stage 2's three decompositions. Against that, the marginal oracle
value is near zero: `shiro-daika` reaches `comb_base_fill`, `bund_junctions` and `draw_comb_field`,
and every one of those is already exercised by many pool maps at four tiers. Confirmed present in
the swept set: `kuwabata` (the only land-use overlay map), `tango`, `minami`, `nagahara` (provincial
cities), `hoshizora`, `hirameki`, `ubame` (towns), `tanada`, `enokida`, `yatsuda` (comb hamlets).
Nothing `shiro-daika` touches in the field subsystem is unique to it.

**The general rule this is an instance of**: an oracle earns its place by the failures it can
catch, not by the ground it covers. A slow artifact that exercises only code other artifacts
already exercise adds wall clock and no diagnostic power - and in a design where the oracle runs
after every step, its cost is multiplied by the number of steps.

**Final oracle**: 28 generators, 884 artifacts (`.json` + `.svg` + `.png`) under `pool/`, hashed
with `sha256sum` and compared as a sorted list. `specs/112-fields-package/quickstart.md` step 1-2
commands stand with `wip/*.gen.py` removed.

## R12. The extraction's real failure mode is a DROPPED RETURN, and a type checker will not see it

Found on the first Stage 2 extraction, and worth writing down because it is the exact bug this
kind of refactor produces.

`_comb_draw_source` was cut from the span that computes `pond_rec` (the tameike center, or None for
a stream-fed fan). The span ends with the `elif` branch that draws a feeder stream - it does not
end with the assignment - so the extracted helper fell off the end and returned `None` on every
path, while the parent dutifully wrote `pond_rec = self._comb_draw_source(...)`. Every comb field
in the pool would have taken the stream branch of the hairline topology channel.

**`mypy --strict` passed.** The helper was annotated `-> Any`, and an implicit `None` return
satisfies `Any` - so the strictest type checking available said nothing. What caught it was
**ruff's F841** (`pond_rec` assigned but never used) firing inside the helper, which is a
lint about a local variable rather than about the contract that was actually broken.

Three transferable points:

- **Extracting a span that PRODUCES a value is the dangerous case**; extracting one that only draws
  is safe by construction. When the span's last statement is not the assignment you are returning,
  the return has to be added by hand, and nothing in the mechanical transformation reminds you.
- **Annotate an extracted helper with its real type, not `Any`.** `-> Any` disabled the one check
  that would have named this directly. The signature came from the variable's own
  `pond_rec: Any = None` declaration, so the imprecision was inherited rather than chosen - which
  is how it slipped past review.
- **The byte-identity sweep would also have caught it**, loudly, on every comb map. That is the
  point of running the oracle after each decomposition rather than after all three: this failure is
  attributable to one extraction in one file, instead of arriving as "something in Stage 2 moved
  four hundred artifacts".

## R13. Two shell hazards this feature hit, both worth avoiding by habit

Neither cost much, but both are silent and both recur.

**Backticks in a `git commit -m "..."` message are COMMAND SUBSTITUTION.** The water_field commit
message referred to `` `uline` `` and the shell ran it, so the commit landed reading "the remainder
is coupled through , a closure ..." with the word gone. The only visible sign was a stray
`uline: command not found` several lines above the commit confirmation, in a place nobody reads.
Amended with `git commit --amend -F -` and a QUOTED heredoc (`<<'MSG'`), which is the habit to
keep: any commit message carrying identifiers in backticks goes through `-F -`, never `-m`.

**A grep guard over a log is not a verdict.** The Stage 1 gate was declared "NOT CLEAN" by a
`grep -qiE "COVERAGE:|FAILED|ERROR|error:"` guard that matched pytest's own banner line
`_____ coverage: platform linux _____`. The gate was green. Guard on the POSITIVE signal the tool
emits on success - here `grep -q "gate green"` - rather than on a disjunction of words that might
mean failure: the positive signal has one meaning, the negative list has as many meanings as the
tool has vocabulary.

## R14. Splitting a file that another session is patching: the delete/modify collision

This happened, was cheap to resolve, and will happen again to the next split - the diagram engine
has several sessions in it at once. Recording the shape and the resolution.

**What git reports.** A package split DELETES the original file. A peer session patching that same
file produces a `DU` (deleted by us, modified by them) conflict, which git cannot auto-resolve and
which - unlike a content conflict - leaves no markers to edit. Their change simply has nowhere to
land, and the danger is resolving it by taking the deletion and silently dropping their fix.

**Why it was cheap here, and what makes it cheap in general.** The peer's fix touched
`_paddy_features` and `_plot_pond`, both of which live in `features.py` and neither of which Stage 2
had decomposed - so the port was a straight method-for-method replacement of the post-merge bodies
plus the three imports they newly needed. **A split is easiest to merge into where it moved text and
hardest where it rewrote it.** That is a reason to keep the pure-move stage separate from the
decomposition stage beyond the diagnostic argument in R5: a peer's patch merges into a MOVE almost
mechanically, and into a rewrite by hand.

**The verification that actually proves a port** is not "the tests pass" - the peer shipped their
own test and it would pass against a subtly wrong port of the code it exercises. It is that
regenerating every live map reproduces THEIR just-committed manifests with zero unstaged bytes.
Their commit had regenerated the scripted hamlets, which made the pre-split baseline obsolete and
handed us a better oracle in its place: main's own artifacts, produced by main's own version of the
code, are the fixed point the ported code has to hit.

**The process note.** A heads-up was sent to the peer session before the split landed and it expired
unapproved - cross-session messages need the recipient's user to approve them, so they are a
courtesy, never a protocol. Main is the coordination point, exactly as CLAUDE.md says for spec
numbers: the merge is where collisions are actually resolved, and it worked. A second heads-up, to
the session reorganizing the skill's directory layout, DID land and was worth sending - but the
split would have merged correctly either way.
