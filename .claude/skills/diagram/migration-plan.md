# Migrating `/diagram` from hand-authored maps to scripted generation

*A standing project plan, not a spec-kit feature. Individual conversions ARE spec-kit features; this
document says which ones exist, what order they go in, what "done" means for each, and the rules a
conversion has to obey. **Update the status table in section 4 as part of finishing any conversion**
- a plan nobody updates is worse than no plan.*

**Load this file when:** you are about to convert a map type to scripted generation, you are picking
up this project cold, or you are deciding whether a `/diagram` request should be hand-authored or
generated.

**Status: hamlet tier converted (one archetype of five). Everything above hamlet is hand-authored -
and the whole hand-authored pool is FROZEN as of 2026-08-16 (section 2): exhibits, not maintained
artifacts.** Last updated 2026-08-16.

---

## 1. What is being converted

A `/diagram` Mode B map has three layers, and only ONE of them is changing.

| Layer | What it is | Size | Converting? |
|---|---|---|---|
| The **engine** - the `settlement/` package (split from settlement.py by feature 025) | 338 methods that DRAW things: farmhouses, paddy combs, torii, city walls, castles, markets, wards | 16.0k lines across 16 subfiles | **No.** Already spans hamlet to capital. |
| The **validator** - `check_village/` | The gate. 189 checks run on a single hamlet; more at larger tiers | 15.7k lines | **No.** It is the reason this migration is safe. |
| The **composition** - `pool/*/<name>.gen.py` | Which features exist on THIS map, where each one sits, how they relate | ~200-900 lines **per map**, hand-written | **Yes. This is the whole migration.** |

The composition layer is what costs hours per map, is where every placement bug lives, and is what
a generator can do from a nine-line spec. `hamletgen.py` (2.7k lines) replaced the per-map
composition for hamlets: it turns

```python
HamletSpec("Ikegami", seed=4, households=15)
```

into a complete, gate-passing map. Name, size and (when the surrounding geography is already
settled) the direction water runs are the facts only a person knows. Everything else - where the
lanes go, which side the marsh is on, how many wells and who they serve, where the shrine faces -
follows from those and is the script's job.

**What is NOT converting:** Mode A compound plans (magistracies, manors, temples, keeps). They are
single buildings drawn to a program, they have their own reviewer (`building-review`) and their own
dimensional auditor (`size-audit`), and there is no cohort to fit against. If they ever get scripted
it is a separate project with a separate rationale.

## 2. Why - the case, with numbers

| | hand-authored | scripted |
|---|---|---|
| Wall-clock to a gate-passing map | **hours** (a large map has taken most of a session) | **14.7 s**, generate and gate |
| Where a placement rule lives | in one map's `.gen.py`, invisible to every other map | in the generator, applied to every map it makes |
| How a defect is found | the GM opens the PNG and spots it | the cohort finds it on some seed you never thought about |
| How a defect is fixed | edit that map | edit the generator; every future map is fixed |
| Evidence a fix worked | that one map looks right | 36 maps pass 189 checks each |

The second and fourth rows matter more than the first. A hand-authored map that gets a rule right
teaches the next map nothing. That is the actual cost being paid, and it compounds: the pool has 23
hand-authored maps, and a rule discovered today reaches none of them.

**The accepted trade** (GM, 2026-08-13): when a newly-codified rule reveals a defect in existing
hand-authored maps, we do NOT go back and fix those maps. We fix it in the generator and the map
gets fixed when its type is converted. Retrofitting by hand is the cost this project exists to stop
paying. Record the decision in the map's `.notes.md` so nobody re-discovers it as a bug.

**Extended to a full FREEZE** (GM, 2026-08-16): the hand-authored pool is no longer regenerated OR
re-gated at all. The 19 legacy Mode B maps keep their committed .json/.svg/.png as permanent
exhibits (still in `pool/index.html`), the `test_villages.py` sweep covers scripted maps only, and
`regen.py` refuses a legacy gen (`FROZEN`; `--frozen-ok` overrides). `poolmaps.py` is the
classification all three tools share. What this buys: iteration on placement rules and checks costs
nothing on maps whose authoring process is deprecated, and - the bigger half - **engine changes no
longer need to hold the legacy pool byte-identical**, so new rules ship un-flagged and the
byte-identity criterion below is retired. The known cost, accepted out loud: the above-hamlet wings
of the `settlement/` package (towns, cities, the capital) are exercised by nothing until their tiers convert,
so the coverage gate holds 100% on every module except the `settlement/` package, which carries a RATCHET
floor in the Makefile (`SETTLEMENT_COV_FLOOR`) - raise it as each tier converts, never lower it.
A frozen map's defects against post-freeze rules are expected, not bugs; the fix is conversion.
The frozen maps' renders (svg + png, ~195 MB) are **committed as write-once exhibits** (GM
2026-08-16, un-ignored by name in `.gitignore`), because nothing can faithfully re-derive them
once the engine drifts; **when a map is converted to the scripted approach, its physical renders
come out of git again** (`git rm` the svg/png, delete its `!` lines in `.gitignore`) - a
converted map's renders are derived by a live generator and return to being ignored.

## 3. The two axes

Progress is not a single line. A settlement map is a **tier** crossed with a **field archetype**:

- **Tiers** (population, and the institutions that come with it): hamlet -> village -> town ->
  provincial city -> capital. Each tier adds features the one below does not have. A village needs a
  headman's house, a shrine, and tax-free plots; a town adds a market and a road frontage; a city
  adds walls, wards and a garrison.
- **Field archetypes** (how the land is farmed): `valley_paddy`, `contour_terraces`, `polder_grid`,
  `ribbon_valley`, `mulberry_dike_fishpond`, each optionally carrying a **land-use overlay**
  (`mulberry_fishpond`, `lotus`, `tea_fringe`).

The engine already builds all five (`build_comb`, `build_terraces`, `build_polder`, `build_ribbon`,
plus `apply_land_use`). The generator has to learn how to COMPOSE each one - where the water enters,
what the settlement does when the field shape changes, which way the lanes run.

Archetypes are cheaper than tiers: an archetype is one new stage in an existing generator, a tier is
a new generator (or a large conditional wing of one) plus the institutions that tier owns.

## 4. Status

**Legend:** SHIPPED = in the roll, cohort-green. FITTED = generates and passes, not promoted.
STARTED = partial. NOT STARTED = hand-authored only.

### Hamlet tier - generator `hamletgen.py`

| Archetype | Status | Evidence | Hand-authored exemplars |
|---|---|---|---|
| `valley_paddy` | **SHIPPED** | 24/24 fitted cohort, 12/12 held out | Ikegami, Akagahara, Moritono |
| `polder_grid` | **FITTED** | 29/32 (8 seeds x 4 falls). Blocker: title lands on the windbreak belt when framing is tight | Enokida |
| `contour_terraces` | NOT STARTED | engine builder exists | Tanada |
| `ribbon_valley` | NOT STARTED | engine builder exists | Yatsuda |
| `mulberry_dike_fishpond` | NOT STARTED | needs the `mulberry_fishpond` overlay first | Kuwabata |
| overlays (`mulberry_fishpond`, `lotus`, `tea_fringe`) | NOT STARTED | `apply_land_use` exists engine-side | Honda, Shimizu, Kuwabata |

Generated so far: Inashiro, Kashikawa, Mizuguchi, Sawada (`pool/hamlets/`, beside the hand-authored hamlets - the pool is foldered by tier, and `meta.generated_by` marks the scripted maps).

### Above hamlet

| Tier | Scale | Status | Hand-authored exemplars | What the tier adds |
|---|---|---|---|---|
| Village | 2 ft/px | NOT STARTED | Hoshigaoka, Ueda, Kikuta, Hikari-no-Sato | headman, shrine, tax-free plots, a second field |
| Town | 1 ft/px | NOT STARTED | Hoshizora, Hirameki, Ubame | market, road frontage, crafts row, inn |
| Provincial city | 3 ft/px | NOT STARTED | Tango, Minami, Nagahara | wall circuit, wards, garrison, temple complexes, districts |
| Capital | 3 ft/px | NOT STARTED, tier itself unfinished | Shiro Daika (`wip/`, housing pass still open) | castle, great houses, the capital's own street grammar |

### Mode A (compound plans) - out of scope, listed so nobody wonders

Magistracies (Ochiba, Hayakawa, Ubame, plus the generic county example) are hand-authored by design.

## 5. The unit of work: one conversion = one spec-kit feature

Tiers and archetypes are the right size for `/speckit-specify` -> plan -> tasks -> implement. This
document is deliberately NOT a spec-kit feature: it outlives all of them.

**A conversion is done when all of these hold:**

1. The generator makes the map type from a spec whose required fields are only facts a person knows.
2. **A cohort is green** - not a sweep, a cohort. Roll N maps from consecutive seeds with varying
   size, and gate every one. The bar for promoting an archetype into the roll is a green COHORT;
   this was learned the hard way when a green sweep of hand-picked cases dropped the fitted cohort
   from 24/24 to 19/24 the moment it was promoted.
3. **A held-out cohort is green.** Fit against one seed range, then measure on a range you never
   developed against. Fitted = seeds you tuned on; held-out = seeds that only ever get measured.
   Without the second number you have memorized the first.
4. **The frozen legacy pool is untouched on disk.** RETIRED as a byte-identity requirement by the
   2026-08-16 freeze (section 2): legacy gens are never re-run, so engine changes need no flags and
   nothing verifies 19 deprecated compositions. What remains is the trivial half: nothing in the
   conversion may regenerate or overwrite a frozen map's committed artifacts (`git status` under
   `pool/` stays clean apart from the maps you meant to change). When the conversion of a TIER
   lands, its legacy exemplars stay frozen as exhibits; raise the Makefile's
   `SETTLEMENT_COV_FLOOR` to cover the tier's newly re-exercised engine wing. And when a legacy
   MAP is itself converted (superseded by a scripted version), remove its committed renders from
   git (`git rm` the svg/png, delete its `!` lines in `.gitignore`) - see section 2.
5. **`make done` is green** - ruff, format, mypy --strict, pytest, 100% coverage.
6. **A `settlement-review` pass on at least one generated map.** The gate cannot see glyph
   legibility, feature FORM, or whether the map reads as a distinct place. The author is not a
   reliable reviewer of their own output (Constitution Principle I).
7. **The "why" of every new number is written down** where the rule lives (CLAUDE.md's
   record-the-why rule). A bare `>= 0.82` teaches the next session nothing.
8. **This document's section 4 is updated.**

## 6. Rules the conversion obeys - each one paid for

These are the failure modes that have actually cost this project time. They are not general advice.

- **Never replicate a check inside the code it governs.** Three attempts to auto-detect when a
  channel needed its head joined - by distance, by containment, by copying the check's own three
  clauses - each fixed the new maps and broke hand-authored ones, because the check reads geometry
  (crop bounds, per-field bboxes) that does not exist at draw time. Use an explicit flag. A flag
  cannot drift; a replica silently does.
- **Placement and the check must read the same geometry.** The recurring bug shape: the placer tests
  a centre and the check tests a footprint; the placer reads the envelope and the check reads the
  drawn pixels. Both are "correct" and they disagree.
- **Derive, don't pin.** A feature defined by a relationship - a towpath on a bank, a well between
  streets, a reservoir above the fields - must be computed from that geometry at draw time. A pinned
  coordinate becomes quietly false the moment the thing it referenced moves.
- **A check that never runs looks exactly like a check that passes.** `wells_off_the_wet_toe` was
  written for a hamlet and placed inside a village-scale block; it never ran on the map that
  motivated it. When you add a check, prove it FIRES on the broken artifact before you fix it.
- **Save every bad map as a negative fixture** in `pool/regressions/`. Coverage proves a check ran,
  not that it has teeth.
- **Enumerate what binds a feature BEFORE moving it.** One reservoir got moved five times because
  its three constraints (outside the crop, uphill, anchored on the main channel's last point) were
  discovered one gate failure at a time.
- **A green gate is not a good map.** A connector re-shape once deleted a well and a farmhouse and
  the gate passed it. Diff the manifest's feature counts against the previous run.

## 7. Iteration cost - measured, dated, and tracked

The GM's standing constraint: *the difference between 5 minutes and 50 minutes to implement a change
is huge, and inefficient loops have been the single biggest stumbling block.*

**The numbers live in [`timings.md`](timings.md), not here** - one dated block per measurement,
appended by `python3 timings.py`. They are deliberately NOT duplicated into this plan, because a
number written in two places eventually disagrees with itself, which is exactly how the skill's
CLAUDE.md came to claim a "~2 to 2.5 minute" sweep long after it had passed four minutes.

**Every benchmark records its BREAKDOWN, not just its total** (GM, 2026-08-15). A total says a loop
is slow; only the parts say what to do about it. This is Amdahl's law as a working rule: a phase
worth optimizing is one that dominates its parent, and a phase at 5% cannot be worth optimizing no
matter how badly it is written. The breakdown is coarse on purpose - phases, not functions.
Function-level profiling is the right tool once a phase is the identified target, and the wrong tool
for a standing record that has to stay cheap enough to re-run.

Three rules follow, and they bind:

- **If a change can only be tested by a multi-minute run, the loop is wrong and fixing the loop comes
  first.** Reach for the smallest artifact that can show the defect - one seed, one fall, one stage -
  and widen only once it is fixed. The gate is proof, not a probe.
- **Re-measure and append a block** after performance work, after adding a tier or archetype, and
  whenever a loop starts to feel slow. Feeling slow is how the last drift went unnoticed for a week.
- **These costs only grow as the pool grows.** Every conversion adds maps to sweep and checks to
  run, so the budget has to be watched on the way up rather than rediscovered at the top.

Wall-clock is dominated by model turn latency, not tool execution (78% in the last profile), so the
count of sequential turns is the real cost. Batch independent work into one turn; background the
final gate and act on its notification instead of waiting on it.

## 8. Order of work

Ordered by value per unit of effort, not by tier.

1. **Finish `polder_grid`** - one blocker (title vs windbreak belt), then a green cohort, then
   promote into the roll.
2. **Land-use overlays** - cheapest remaining item; the engine work is done, the generator needs to
   choose and declare. Unlocks Honda and Shimizu, and is a prerequisite for Kuwabata.
3. **`mulberry_dike_fishpond`** - completes Kuwabata, the hamlet the GM named as the next distinct
   type.
4. **`contour_terraces` and `ribbon_valley`** - closes the hamlet tier entirely, at which point
   every hamlet in the pool has a scripted equivalent.
5. **Village tier** - the first new generator. Biggest single step in the project: it must learn the
   institutions (headman, shrine, tax-free plots) and multi-field composition. Expect this to
   surface the architectural question of whether `hamletgen.py` generalizes or whether tiers share a
   stage library.
6. **Town, then provincial city.**
7. **Capital** - last, and blocked on the tier being finished by hand first (Shiro Daika's housing
   pass is still open). Do not script a tier whose rules are not settled.

## 9. Vocabulary

- **Mode A / Mode B** - a compound plan (one building complex) vs a settlement map.
- **Tier** - hamlet / village / town / provincial city / capital.
- **Field archetype** - how the land is farmed; **overlay** - a permanent secondary use recolored
  onto some plots.
- **Fitted cohort** - the seed range developed against. **Held-out cohort** - a seed range only ever
  measured, never tuned on. Borrowed from statistics for the same reason.
- **The roll** - the set of archetypes the generator will choose from when the spec does not name
  one. An archetype that generates but is not in the roll is opt-in only.
- **`meta.generated_by`** - the manifest tag marking a map as scripted. Checks gated on it apply new
  rules to generated maps without moving hand-authored ones. (Largely historical since the freeze:
  new rules no longer need gating, because legacy maps are never re-gated; existing gates stay for
  the regression corpus's frozen fixtures.)
- **Frozen** - a legacy map's permanent state since 2026-08-16: committed artifacts kept as
  exhibits, gen never re-run, gate never re-applied. `poolmaps.py` holds the classification.
- **The gate** - `check_village/`. **`make done`** - the full lint/type/test/coverage run.
