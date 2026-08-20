# /diagram engine - dev loop

Guidance for *working on the diagram engine* (the `settlement/` package, the `check_village/` package, the pool
generators), as opposed to *invoking* `/diagram` to draw a map (that is `SKILL.md`). This file
auto-loads whenever a session edits files in this directory - which is exactly when it applies.

The project-wide iteration doctrine lives in the root [`CLAUDE.md`](../../../CLAUDE.md)
"Iteration-loop efficiency" section (batch recon into fewer bigger turns; iterate on the ONE
motivating artifact, then run the full test bed once at the end; background the final gate; never
cut the ritual/guardrail steps). Read that first; this file carries the concrete diagram numbers
and the DIAGRAM-SPECIFIC lessons that section does not cover - each earned by costing real
round-trips.

## Where things live (read this first; load only the index you need)

The skill's Python lives under **`l7r/diagram/`** (feature 119) and is grouped by what a module is
FOR. Each group carries its own `CLAUDE.md` index, so a session can open the one directory its task
is in instead of paging this file.

**Why the extra two levels.** `l7r/` here is a PEP 420 *namespace portion* - it deliberately has no
`__init__.py` - and it shares the `l7r` parent package with the L7R Toolkit webapp's `l7r.app` /
`l7r.names` in `/gm-assistant/webapp/l7r/`. Both directories contribute to one `l7r.__path__`, so
`import l7r.app` and `import l7r.diagram.settlement` work in the same interpreter and the webapp
can render a map without two colliding top-level packages named `l7r`. **Never create
`l7r/__init__.py`**: that makes it a regular package, terminates the import search, and makes the
webapp's portion silently stop existing. `tests/test_namespace_portion.py` guards it in both trees.

This directory - not `l7r/diagram/` - is still the `sys.path` root, and `pool/`, `tests/`, the
`Makefile` and `pyproject.toml` all stay here. That is why every pool generator's bootstrap block
is unchanged by the move: `SKILL = dirname(dirname(HERE))` from `pool/<tier>/x.gen.py` still lands
here. Engine modules that compute the skill root from their OWN location moved two levels deeper and
were adjusted to match (`gencache`, `pool_index`, `render_cache`, `cohort_audit`, `cache_audit`,
`make_regressions`, `timings`, `hamletgen`, `check_village/__main__`) - a test asserts three of them
still resolve here, because a wrong depth is silent and just lands one directory short of `pool/`.

| directory | what is in it | load its index when |
|---|---|---|
| [`l7r/diagram/settlement/`](l7r/diagram/settlement/CLAUDE.md) | the Mode B drawing engine (the `Settlement` class and its mixins) | you are changing what a settlement map DRAWS or where it places something |
| [`l7r/diagram/check_village/`](l7r/diagram/check_village/CLAUDE.md) | the gate: the whole check battery, as a registry of segments | you are adding, changing or running a check |
| [`l7r/diagram/waterfields/`](l7r/diagram/waterfields/CLAUDE.md) | the water-first field engine (v2 comb fields) | you are changing paddies, bunds, canals or the field frame |
| [`l7r/diagram/hamletgen/`](l7r/diagram/hamletgen/CLAUDE.md) | the scripted hamlet generator - a whole hamlet from a 9-line spec | you are working on scripted generation |
| [`l7r/diagram/sitegen/`](l7r/diagram/sitegen/CLAUDE.md) | tier-agnostic generation machinery the tiers SHARE (geometry, types, worker counts) | you are adding a tier generator, or moving a stage out of one |
| [`l7r/diagram/pipeline/`](l7r/diagram/pipeline/CLAUDE.md) | how a map gets regenerated, cached, rendered and indexed | the cache is behaving oddly, or you are changing how generation is DRIVEN |
| [`l7r/diagram/tools/`](l7r/diagram/tools/CLAUDE.md) | read-only diagnostics and audits you run by hand | a map came out wrong and you need to ask WHY, or a number needs measuring |
| [`tests/`](tests/CLAUDE.md) | every test, mirroring the source layout, plus the frozen fixtures | you need to find or add a test |
| `pool/` | the shipped maps: `<name>.gen.py`, its manifest, its render, its `.notes.md` design journal | - |
| `wip/` | maps staged outside the pool (not gated, not swept) | - |

Two engine modules are still single files rather than packages, and stay that way on purpose:
**`l7r/diagram/compound.py`** (the Mode A compound program and perimeter-first placer) and
**`l7r/diagram/citybudget.py`** (the space-budget city/capital planner). Both are peers of the
engine packages above - pool generators import them directly - and folding them into a package
would rewrite six frozen generator scripts for no navigational gain.

The prose reference (as opposed to the code) splits the same way: [`SKILL.md`](SKILL.md) is the
usage-facing index, and it indexes [`settlements/`](settlements/) and [`buildings/`](buildings/)
(the per-topic design doctrine) and [`research/`](research/) (the historical grounding). Read a
skill index, then load only the topics the subject calls for.

**Run the packaged modules as modules**, from this directory - `python3 -m l7r.diagram.pipeline.regen ...`,
`python3 -m l7r.diagram.tools.why_placed ...`. Running a package module as a loose script path puts its own
directory on `sys.path` instead of the skill root, which is how one file ends up imported twice
under two names.

## Dev-loop doctrine (load on demand)

This file used to carry all of it inline, at 1,449 lines - roughly 28k tokens charged to **every**
session that edits anything in this tree, including sessions that only regenerate a map. The
doctrine itself is unchanged and verbatim; it now lives in [`dev/`](dev/), one file per topic, each
stating when to load it. Same pattern as the root [`CLAUDE.md`](../../../CLAUDE.md) -> `docs/`
split. **Load the one file your task is in.** The short always-on version of each rule is below the
table; the file is where the evidence, the measurements and the failure stories live, and you want
those before you argue with a rule.

| doc | load it when |
|---|---|
| [`dev/loop.md`](dev/loop.md) | You are about to run the gate or a pool sweep, you want the diagram timing numbers, or you are deciding how much to re-run after a change |
| [`dev/placement.md`](dev/placement.md) | You are adding a map feature, or changing where anything is placed or drawn. Carries the DRAW ORDER map (including the scripted `STAGES` table), CENTER vs FOOTPRINT, and the KEEP-CLEAR CONTRACT. Its companion `dev/placement-stages/hamlet-placement.html` SHOWS the order - Inashiro plated after each of the thirteen stages |
| [`dev/gate.md`](dev/gate.md) | You are adding or changing a check, writing a check test, or waiving a rule for one map |
| [`dev/diagnostics.md`](dev/diagnostics.md) | A map came out wrong and you need to know WHY - `open_seat`, `why_placed`, `site_justice`, `crop_map`, and how a probe lies to you |
| [`dev/performance.md`](dev/performance.md) | A gen or a check got slow (or "hangs"), or a `GEN_TIME_BUDGETS` entry tripped |
| [`dev/cache.md`](dev/cache.md) | The cache is behaving oddly, you changed how generation is DRIVEN, or a coverage floor breached for no reason you can see |
| [`dev/pool.md`](dev/pool.md) | You are about to touch a pool map, convert one to scripted generation, or work on `hamletgen/` |
| [`dev/decisions.md`](dev/decisions.md) | You are about to build on a property of the engine nobody decided, or you are leaving a decision open for a later session |
| [`dev/reviews.md`](dev/reviews.md) | You are about to launch `settlement-review`, `building-review` or `backstory-review` |

Two more docs that were already separate: [`migration-plan.md`](migration-plan.md) (the standing
plan for converting the pool to scripted generation - **read it before drawing or scripting a
settlement map, and update its status table when a conversion lands**) and
[`timings.md`](timings.md) (the measured timing ledger; never write fresh timings into prose).

## The always-on version

Each line below is the rule; the doc named after it is the evidence. Where the two ever disagree,
the doc is right - it is where the measurement lives.

**The loop** ([`dev/loop.md`](dev/loop.md))

- Iterate on the ONE motivating map; run the full test bed exactly **once**, at the end. That final
  sweep is MANDATORY whenever shared engine code changed (`settlement/`, `check_village/`,
  `waterfields/`, a scripted engine).
- `python3 -m l7r.diagram.pipeline.regen pool/<type>/<map>.gen.py` - the cache skips the work and
  prints `CACHED` / `REGENERATED` / `FROZEN` every time.
- Cheap linters BEFORE the gate: `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy`.
- Then the WHOLE affected test file with `-n auto`, never a `-k` subset. Then `make done`, **once**,
  backgrounded, and **never polled** - act on the notification.
- Never re-run what `make done` just ran, and never run pytest serially (~7x slower here).
- Never run a pytest BESIDE a running gate - two writers on the same pool maps is a source of false RED.
- Update the predictably-affected unit tests in the SAME edit as the engine change.

**Placement** ([`dev/placement.md`](dev/placement.md))

- **Read the DRAW ORDER map before moving anything.** A drawing method sees only what is in `self.M`
  when it runs; a placer avoids only what is in the registries when it runs. Most "wrong geometry"
  is wrong ORDER.
- A new footprint feature MUST go in `_OVERLAP_STRUCTS` (or `_OVERLAP_EXEMPT`, with the reason) and
  get a caption group in `_LABEL_GROUP`. Membership alone gates it off fifteen hazards; nothing else
  has a hand-written key list to remember.
- **Record a footprint the extractor can read** - `x`+`w`/`vw`, a `poly`/`outline` ring, a stroked
  polyline, or `parts` of rotated quads. A record matching none of those is invisible to every
  matrix check in both directions and looks exactly like a feature with nothing wrong.
- **Gap verdicts read footprints, never centers** - `edge_gap` / `within_edge_gap` / `sat_overlap`.
  Classification, association-reach and prefilters may use centers, deliberately; say which family
  your rule is in, in a comment, at the test. Add a `test_gap_verdicts_read_footprints_not_centers`
  entry with every new gap rule.
- **Never let an aggregate (a centroid) stand in for the distributed thing a verdict is about.**
  Measure to the nearest member, or to the wall.
- **Randomness is POSITIONAL or SCOPED, never "wherever the stream happens to be":** `self._hjit(x, y, salt)`
  for a per-feature attribute, `with self.rng_scope(name, *key)` for a phase or region.

**The gate** ([`dev/gate.md`](dev/gate.md))

- Adding a check: write `_seg_<key>__<name>` in the `check_village/segments_*` file that covers its
  theme, body reading inputs as keyword params defaulting to `_UNBOUND` and returning
  `_kept(locals(), <literal tuple>)`; extend `tests/fixtures/gate_check_names.json`. There is **no
  registry row to write** - the row and the execution position both derive from the function itself.
- Run one check by itself with `gate(M, only={"check_name"})`. Do not go hunting for the segment by hand.
- **A check that never RUNS looks exactly like a check that passes.** Any rule behind
  `if meta.get(...)` needs a companion check that the DECLARATION EXISTS.
- Build check-test manifests with the fixture builders (`manifest`, `house`, `yard`, ...), not by hand.
- Placement and its check must read the SAME manifest source - and when you mirror a gate
  measurement, mirror its WINDOW, not just its formula.
- A map may break a rule, but only IN WRITING: `s.meta(waivers={...})` with 60+ characters of real
  reason, and freeze the pre-waiver manifest into `pool/regressions/`.

**Diagnostics** ([`dev/diagnostics.md`](dev/diagnostics.md))

- Ask the ENGINE where a feature fits (`s.open_seat(...)`) - do not guess coordinates and regenerate.
- Ask the GEN who placed it (`tools/why_placed.py --at` / `--refused`) - do not grep for the caller.
- Adjudicate a multi-rule siting against the GATE (`tools/site_justice.py`), never against a
  re-statement of the rules.
- Read derived geometry from the MANIFEST (0.2s), not by re-running the generators (minutes).
- Batch every crop you want to look at into ONE `tools/crop_map.py` call, then Read them together.
- **A diagnostic that restates what it observes will lie to you.** Print the value and its
  provenance from ONE expression, or do not print the provenance.

**Performance** ([`dev/performance.md`](dev/performance.md))

- Every slow gen ever profiled here was the same shape: *a per-candidate scan of geometry that does
  not change during the scan*. Hoist, prefilter, or index - and if a gen "hangs", suspect that shape
  and profile before bisecting.
- When a check is slow, **INDEX it - do not coarsen it.** The index prunes; it never decides.
- Trust the A/B against HEAD, not cProfile's seconds.

**The pool** ([`dev/pool.md`](dev/pool.md))

- **The legacy pool is FROZEN.** The 19 hand-authored maps are permanent exhibits: never regenerated,
  never re-gated, renders committed. The fix for a frozen map that breaks a post-freeze rule is
  CONVERSION, not retrofit - do not "fix" one, and do not treat its violations as bugs.
- New rules ship un-gated; engine changes no longer need byte-identity flags.
- A cohort of seeds is a much stronger test bed than a map - and **measure the cohort's baseline
  first**, in a detached worktree (`git worktree add --detach /tmp/base HEAD`), never by stashing.
- A seed that passed before your change and fails after it is a REGRESSION, and nothing merges to
  main carrying one (constitution Principle XIII). "It rotated" is not a defense.

**Reviews** ([`dev/reviews.md`](dev/reviews.md)) - `settlement-review` is mandatory before a Mode B
map ships. Say the SCOPE (`DELTA:` vs `FULL`), one map per agent in parallel, and launch it the
moment the map's regen + gate is green, BEFORE your own visual pass. **A finding OUTSIDE the delta
is still yours to fix** (constitution Principle XIV) - a reviewer pointed at a delta reliably turns
up unrelated defects, and that is it working.

**Fix defects where you find them** (constitution Principle XIV, NON-NEGOTIABLE) - this engine is
where the rule bites hardest, because its reviewers and diagnostics surface defects constantly and
almost none of them belong to the feature in hand. Fix them in the work at hand; defer ONLY an
architectural fix, and then with its measurement, mechanism and sketch. Do not cite Principle XIII's
"pre-existing failures stay ledgered" - that governs what blocks a push, not what you owe a defect
you have seen. And when a fix attempt FAILS, record it at the point of change: `homesteads.py`
carries two dead ends for the front-row lane cap, either of which a later session would otherwise
re-try.

**Recording decisions** ([`dev/decisions.md`](dev/decisions.md)) - before you build on a property of
the engine, check whether anyone DECIDED it; a side effect is not a rule. And an open decision
carries the 2-3 line implementation sketch, not just the question.

- **Research it before you ask the GM, and if two forms are supportable make it a KNOB.** The
  ladder: research -> decisive means implement it -> two attested forms means roll between them per
  settlement -> only a silent record earns a GM ruling. Liberty covers a DEGREE along a continuum,
  never a choice between two distinct FORMS. Constitution Principle XII; evidence and the worked
  example in the doc.
