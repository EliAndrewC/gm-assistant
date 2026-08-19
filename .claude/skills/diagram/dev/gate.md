# The gate: adding a check, waivers, and the ways a check fails silently

**Load this file when:** You are adding or changing a check, writing a check test, waiving a rule for one map, or a check is passing when you think it should not.

Split out of [`../CLAUDE.md`](../CLAUDE.md) so it is not in every diagram session's
context. The text is verbatim; the short always-on version of each rule stays in the index.

## The gate is a REGISTRY - adding a check, and running one check by itself (feature 022)

`gate()` is no longer a 12,944-line function: it is a small driver over `GATE_SEGMENTS`, an
ordered registry of ~1,371 segment functions (per-check granularity since features 023/024; DERIVED from the segment files since feature 109) whose order IS the legacy execution order. What this
buys and how to work with it:

- **Run a subset**: `gate(M, only={"check_base_name", ...})` executes just the segments that can
  emit those names plus their dependency closure (median 7 segments), with verdicts guaranteed
  identical to the full run. Unknown names and META checks (`META_CHECKS` - whole-run state like
  `waivers_are_live`) raise ValueError rather than silently running nothing.
- **The regression replay runs targeted** (`tests/test_regressions.py`): each fixture verifies only its
  `_regression.fires` (meta names fall back to the full gate). This is what took the 210
  frozen-city fixtures from ~480 s to ~58 s serial. The fixture format is unchanged.
- **Adding a check**: write a new `_seg_<key>__<name>`-style function next to its neighbors, in
  whichever `check_village/segments_*` file covers its theme (`check_village/CLAUDE.md` is the
  index): body reads its inputs as keyword params defaulting to `_UNBOUND` and returns
  `_kept(locals(), <literal tuple of the names it binds>)`. Since feature 109 there is NO
  registry row to write - the registry DERIVES every row from the segment function itself
  (signature -> `free`, return literal -> `writes`, AST -> the rest), and the numeric key in the
  name IS the execution position (`_seg_0533_500__x` runs between 0533 and 0534; to run beside a
  PLACED segment, add a `_PLACEMENTS` entry in `check_village/registry.py` instead). Then extend
  `tests/fixtures/gate_check_names.json` (the registry-pin test compares the two). The
  `every_feature_classified_*` and KEEP-CLEAR contracts in [`placement.md`](placement.md) are unchanged.
- **The migration tooling** (one-shot, retired): `specs/022-gate-check-registry/` holds the
  transformer, the oracle sweeps (`oracle_sweep.py capture/compare/targeted`), and research.md
  with the dataflow model and the three holes the sweeps caught (helper-closure mutation,
  upward-exposed reads vs raw loads, comprehension-target scoping). Read R9 there before any
  future dataflow-over-gate work.
- **Never trust a dependency edge you have not swept**: the targeted-vs-full sweep over all 791
  fixtures is the empirical guard on the closure rules. If you change `needs`/`writes` semantics
  or add segments with unusual dataflow, re-run `oracle_sweep.py targeted`.
- **The city/capital battery is per-statement segments too (feature 023)**: 022 left the whole
  urban battery as ONE 1,040-statement segment (it was a single `if scale in ('city',
  'capital'):` statement in the legacy gate, so statement-granularity could not divide it) under
  a clause-12 debt annotation. Feature 023 paid the debt: `_seg_0563_NNN__<name>` segments carry
  the guard IN THE BODY (`if scale in ('city', 'capital') and ...:`; a few keep deliberate
  nested guards under `# noqa: SIM102` where a comment bank sits under the guard) so bodies
  moved verbatim, then ruff's SIM102 autofix combined the guards with identity re-proven by the
  oracle battery afterwards. Adding a
  city/capital check = write a small `_seg_0563_NNN`-style function with its guard in the body,
  same registry row mechanics as any other segment (tooling + census: `specs/023-split-city-
  mega-segment/`, retired one-shot like 022's).

## A check that never RUNS looks exactly like a check that passes

Three separate times in one feature (2026-07-25, the water-flow work) the defect was **not a bad map
but a check that was silently not running**, and each time the gate was green throughout. The shape is
always the same: a rule gated on an OPTIONAL declaration that almost nothing declares.

- `meta(down_deg)` gated the whole drainage-slope block, `downhill_direction_valid` and
  `marsh_on_low_ground`. The two provincial cities declared none, so they were never validated by any
  of them - the code even said so out loud: *"maps without the tag are exempt (slope unknown)"*.
- The legacy `meta(downhill)` gated `channels_flow_downhill`. Only **2 of 17** maps declared it, so 15
  skipped that check entirely.
- `moat_channels_flow_with_current` needed a stream END within 35px of the moat ring. Nagahara's river
  ends off-map (it is the MOAT's ends that meet the river), so it **never ran there at all** - and on
  Tango it ran only because the feeder happened to be drawn before the outfall.

**The cheap diagnostic.** Coverage does not catch this: the gated branch is exercised by SOME map, so
the lines are covered while other maps never reach them. What catches it is asking, per map, whether
the check appears in the output at all:

    python3 -m l7r.diagram.check_village pool/<type>/<map>.json | grep -c "<check_name>"     # 0 = never ran

Run that across the pool for any check whose body sits behind `if meta.get(...)` or
`if <thing> is not None:`. A `0` on a map that plainly has the feature is the bug.

**The ratchet.** When a rule needs a declaration to work, add a check that the DECLARATION EXISTS -
otherwise the rule is optional in practice no matter how firmly it is written.
`settlement_declares_a_land_fall` is the model: it demands a map-level `down_deg` or a per-field fall
on every paddy, and says in its own message that a map declaring nothing SKIPS every drainage rule
while still showing green. Prefer this to widening the gate quietly.

**The ENVIRONMENT-GATED variant, and it is nastier (2026-08-16).** The three cases above are gated on
map DATA. A check can just as easily be gated on where it is RUNNING, and then it disables itself in
exactly one place: the place you always run it. `tests/hamletgen/test_surface.py`'s census skipped any
file with `.clones` among its path parts - which reads as "do not walk other sessions' clones", but
tests the ABSOLUTE path. Every session works inside `/gm-assistant/.clones/<name>/`, so the condition
was true for EVERY file, the census returned the empty set, and `test_census_matches_pin` compared
nothing against its pin list. Inside a clone it saw **0 names; with the guard gone it sees 50** - and
it had been hiding two genuinely unpinned consumers (`hg.driver`, `hg.sink`) introduced by the very
feature that added the guard.

Two things to carry from it:

- **Any test predicate that inspects an ABSOLUTE path is suspect**, because a session clone, main and
  a scratch checkout differ only in their prefix, and the failure direction is silence. Match on a
  path RELATIVE to the root being walked, or do not match on paths at all. (The main-tree guards -
  `settlement._assert_not_main_tree`, `webapp/mainguard.py`, the Makefile's `guard` - are the
  legitimate exception: inspecting the absolute path IS their job, and each is tested with synthetic
  paths rather than with the one it happens to be running under.)
- **A "re-census the tree" guard must assert it FOUND something.** A census that silently returns
  nothing is indistinguishable from a clean bill of health, which is this whole section in one line.
  Cheap version: plant a consumer of a fake name and confirm the guard fires, the way
  `test_guard_fires_on_synthetic_clash` already does for the clash detector.

Found only by running `make done` from a checkout OUTSIDE `.clones/` - worth doing once after any
change to how the suite discovers files.

## Build check-test manifests with the fixture builders

`tests/check_village/` hands `gate()` hand-built manifests carrying only the keys the check under test
reads. That focus is right, but it has a tax: a record often must carry a key some OTHER check
indexes unconditionally (a threshing yard's `of`, a grove's `face`), and omitting it does not fail
your test - it raises a `KeyError` from an unrelated check, costing a fix-and-rerun cycle to
diagnose. Use the builders at the top of the file (`manifest`, `house`, `yard`, `garden`, `well`,
`grove`, `vgrove`, `bldg`); they carry the required keys and take `**kw` overrides.
`test_fixture_builders_survive_every_check` runs every check against one of each and is what keeps
them complete - if a check starts indexing a new required key, it fails there once instead of
ambushing the next person to write a test.

## Placement and its check must read the SAME manifest source

A recurring engine trap (footbridges 2026-07-22; recorded in [`settlements.md`](../settlements.md)
under "PLANK BRIDGES"): the generator in `settlement/` and the validator in `check_village/`
must classify terrain from the SAME data, or they disagree and a feature the generator dropped is
demanded by the check (or vice versa). Read the MANIFEST fields (`M["fields"]` outlines +
`M["dry_plots"]`), NOT engine-internal blocking lists like `self.field_polys` that some gens leave
empty. When a new check pairs with new placement logic, factor the shared predicate so both sides
provably use it.

## "Placer stricter than gate" means a stricter THRESHOLD on the SAME measurement

The engine is full of paired rules where a placer refuses at a generous number so a borderline case
can never false-fire the gate that judges it (supply-bank margins, the paddy apex ladder: gate 15 <
weld 18 < toe 25). The pairing is right and it broke TWICE IN ONE SESSION (2026-08-17), in opposite
directions, because "stricter" was read as being about the NUMBER when it is about the number *and*
the measurement together:

- **Stricter on a DIFFERENT measurement is not a margin, it is a second rule.** `_absorb`'s weld
  guard tested `min(raw_ring, dedup_ring(r, 1.0))` while its gate reads the deduped ring alone.
  Strictly more refusals, yes - but some of them for apexes the rule cannot see, so welds were
  declined to prevent a defect that could not exist. Cost: a doubled bund on two cohort seeds, and a
  session-long detour that concluded a nonexistent "genuine geometric conflict".
- **Replacing the gate's measurement with a better one silently DROPS the margin.** The tint
  demotion was then re-aimed at an end-width-collapsed ring, which is a genuinely better question -
  and testing it *instead of* the gate's own ring meant a plot pointed on the gate's ring but blunt
  on the new one kept its tint and tripped the gate. Cost: cohort seed 8.

- **And a measurement can differ by its SPAN alone, which looks like no difference at all.** The
  offmap drain brook's junction: the placer read the collector's heading off its final vertex pair,
  `drainage_junction_smooth` reads the same corner over a 40 px chord (`_flow_dir(span=40.0)`). Same
  quantity, same units, same corner - and on cohort seed 2 they disagreed by **76.1 deg**, because a
  comb's collector ends in a hook a couple of px long that points wherever the carve left it. The
  placer therefore scored the route that continued straight along the collector as a PERFECT
  junction (0.0 deg) while the gate scored it a 76.1 deg kink, and scored the genuinely smooth route
  (2.2 deg) as a 73.9 deg corner and refused it - electing the worst candidate and rejecting the best
  one, from one definition. Fixed by giving `drain_heading` the gate's span (`GATE_FLOW_SPAN` in
  `hamletgen/sink.py`). **When you mirror a gate measurement, mirror its WINDOW, not just its
  formula** - a bearing is a function of the chord you take it over, and a short final segment is
  noise in every polyline this engine draws.

**So the shape that is actually correct**: keep the gate's own measurement with a stricter threshold,
and ADD any extra measurement as a second clause rather than a substitution -
`pointed(gate_ring, 25) or pointed(better_ring, 25)` against a gate that fires at 15 on `gate_ring`.
The first clause is the margin; the second is coverage the gate cannot reach. If you find yourself
writing `min(a, b)` across two rings, or swapping which ring is tested, stop: one of those is a
margin and the other is a different rule, and they need separate clauses so a reader can see which
is which.

## Declared overrides: a map may break a rule, but only IN WRITING

Every placement rule in this engine is a GENERALIZATION, and a specific place is allowed to have a
specific history that beats it. Tango's samurai take the southeast because the Emperor lies that
way, which pushes the outcast quarter opposite its own tanning yard. Hirameki's walls were thrown up
in a hurry when a war turned an interior county into a border one, which is why that town looks
non-standard in several ways. The GM's rule (2026-07-27): **rules and checks are overrideable - and
an override must carry a documented explanation.**

    s.meta(waivers={"tanning_yard_on_the_outcast_side": "The Emperor lies southeast of Tango ..."})

The gate then prints `WAIVE <check>` instead of `PASS`, lists every waiver again in a closing
summary, and keeps the name out of the failure list. Two meta-checks keep the hatch from rotting:

- **`waivers_are_documented`** - the value must be 60+ characters of actual REASON. "by design" and
  `True` both fail. The waiver text is the only record that the map broke the rule on purpose, so it
  states the place's history, not the fact of the exemption.
- **`waivers_are_live`** - the waiver must name a check that ACTUALLY FAILED on this map. A waiver
  whose defect was since fixed, whose check this scale never runs, or whose name is a typo is stale
  and fails. Waivers therefore rot loudly instead of accumulating into a map that is quietly exempt
  from rules nobody remembers it was breaking.

Neither meta-check is itself waivable, or the hatch would swallow its own guard
(`test_the_waiver_meta_checks_cannot_themselves_be_waived`).

**The process lesson behind the waivers** (GM 2026-07-27), which is worth more than the mechanism:
**lock the rules in against ORDINARY settlements first.** Tango and Hirameki were both drawn early
and both are atypical - Tango's samurai take the southeast because the Emperor lies that way,
Hirameki was walled in haste mid-war when a county turned into a border - so for a long time the
defaults were being bent to fit the exceptions instead of the other way round. Build the normal cases
until the rules are settled, then let the unusual ones earn waivers.

**When NOT to reach for it.** A waiver is for a place with a REASON, never for a map that is simply
inconvenient to fix, and never as a way to ship a red gate. If you find yourself writing the reason
and it is really "another session owns this file" or "re-siting is a lot of work", the honest move is
to fix the map or ask the GM - the mechanism is built to make that distinction visible, so using it
to paper over the second kind turns the whole audit trail into noise. And when a rule genuinely
needs to bend for a whole CLASS of maps rather than one place, change the rule, not each map.

**Freeze the pre-waiver manifest as a regression fixture.** A waived map no longer fails, so the
check has no live map holding it honest. Drop the manifest as it stood BEFORE the waiver into
`pool/regressions/` with a `_regression` block (see
`tanning_yard_on_the_outcast_side_fires_on_the_pre_waiver_tango.json`) so a refactor that neuters
the check is still loud.

**A fixture whose defect the generator has since LEARNED TO HEAL is built by removing the repair -
and the provenance says so.** `lanes_do_not_break_mid_run` (feature 125) was written for a 110 ft
hole a `settlement-review` found in Sawada, and by the time the check existed the generator closed
that hole two independent ways: `_bridge_collinear_breaks` spans it, and `_join_orphan_ways` draws a
link even with the bridge pass disabled. So a straight re-roll of seed 6 could not be the fixture -
it is a green map - and the manifest frozen under that name was in fact a REPAIRED one, which is why
the check sat silently passing on its own motivating defect while looking fully covered. The fixture
is now that re-roll with the single link way deleted, and its `_regression` block records both the
deletion and the two healers, because a fixture nobody can explain is a fixture the next session will
regenerate wrong. **Check the fixture actually FIRES the moment you freeze it** - `pytest
tests/test_regressions.py` is the whole cost, and a frozen fixture that does not fire reads as
coverage and provides none.

**RE-ASSERT A FROZEN FIXTURE WHENEVER THE GENERATOR CHANGES, not only when the check does** (the
hamlets session's generalization of the case above, 2026-08-18, and it is the sharper form of the
rule). The fixture that rotted here was CORRECT on the day it was frozen; what invalidated it was a
change to `ways.py` weeks later teaching the generator to heal that hole, and nothing in the check
moved at all. So "verify it fires when you freeze it" is not enough on its own - a freeze is only
proof about the engine that existed that day. `pytest tests/test_regressions.py` replays the whole
corpus in about 14 seconds and is the cheapest guard in the tree; run it after an engine change, not
merely after a check change.

**The shape both sessions kept hitting: an EXCUSE clause keyed on PRESENCE cannot fire on ABSENCE.**
Four instances in one day between two sessions - this check excusing a hole whenever anything stood
in it; `village_windbreak_is_continuous` scoring a total gap as nothing because it skipped empty
columns; and two more of the same family. The tell is always identical and always available: the
check PASSES on the very artifact it was written for. That is precisely what a negative fixture
exists to make impossible, which is why a rotted fixture and an excuse clause are so dangerous
together - each one hides the other.

**THE PLACER AND THE CHECK DISAGREEING IS A CATEGORY, NOT A BUG** (both sessions, 2026-08-18; five
instances in one day). The excuse-clause shape above is one half of it; the other half is a placer
that mirrors its check imperfectly. Seed 31's `harvest_yards_clear_of_paddies` is the cleanest
specimen: the CHECK tests the yard's rect CORNERS against each paddy's recorded `outline`, while
`_yard_fits` tested the yard's CENTRE with a circle against `field_polys`, which holds the SMOOTHED
ENVELOPE - two different sources AND two different geometries, so a yard cleared the envelope by its
circle and still put a corner inside a drawn basin. The woodland scan the same day mirrored its
check's FORMULA but not its WINDOW. **The tell is that both halves look correct read alone**, which
is why the only thing that finds these is reading placer and check side by side and asking which
SOURCE and which GEOMETRY each one uses. The existing rule - "placement and its check must read the
SAME manifest source" - is necessary and, on this evidence, not sufficient: same source, different
geometry fails just as quietly.

**And the honesty clause of a "there is a hole here" check must list only what genuinely STOPS a way.**
The same check excused its own defect a second time after that, because tree cover was in its
blocking list: the gap lay inside a homestead grove, so every corridor read as blocked. Crop, water,
marsh and anything built stop a lane; a grove or an open common does not - a track runs through a
copse, and a *yashikirin* belt is planted around the way rather than across it. Listing ground COVER
alongside real obstacles is the easy way to write a check that can never fail.

## An unmet ASK is a defect, and the gate now says so

`_shortfall` has recorded requested-vs-landed per placement run since 2026-08-05, and recording
turned out not to be enough on its own: Shiro Daika authored **283 frontage seats and drew 129**
behind a completely green gate, because nothing ever read the record back. The GM found it from
the render (*"they look more spaced out than I expected"*). `placement_runs_meet_their_ask` now
fails any run that lands under **60%** of its ask. The line is calibrated from the pool: the only
two shipped maps that miss an AUTHORED count miss it by a hair (Ubame 21/23, Hirameki 13/14),
while every genuine drift sits far below.

Three ways to clear it, and the failure message names all three:

- **Make room** - the honest fix when the ground really should hold them.
- **TRIM the ask** to what the ground holds. Slicing the item list to a PREFIX is
  geometry-preserving: a refusal does not consume an item, so a run handed exactly the number it
  used to place seats the same buildings in the same spots. Verified byte-identical.
- **`fill=True`** where the number was always a capacity budget ("place up to N"), which is the
  city gens' district-fill idiom. It is report-only in BOTH `pack` and `frontage` - it suppresses
  the record and changes no geometry - so declaring it on the three provincial cities moved only
  the `shortfalls` key of each manifest.

## "HAS THIS WAY MET THAT ONE?" IS NEVER A DISTANCE ALONE

Two checks have now got this wrong in the same way, a feature apart, so it is written down here
rather than left in each one's comments.

`lanes_reach_something` originally accepted any lane end within 40 ft of another way as having
arrived. That made it blind to the very defect it was written for: Sawada's lane 0 ran 90 ft past its
own T with lane 2 and died 13 ft from it on an 8 degree divergence - so it was "within 40 ft of
another way", namely the lane it had ALREADY met, and passed. `_FRAY_DEG = 20.0` was added with the
note *"a lane that MEETS another crosses it; one that FRAYS runs alongside it. Proximity alone is not
arrival."*

Feature 124's `lane_ends_front_different_houses` then repeated it exactly. Its first draft exempted
any end within 40 ft of another way, reasoning that such an end is a junction rather than the spare
tine of a fan - and that silently un-fired its own motivating fixture, because the ends a review had
read as a broom stood **21.6 and 24.3 ft** from another way and near-parallel to it.

**So: if your check needs to know whether two ways have met, it needs the angle too.** Distance says
they are close; only the angle says whether one arrived at the other or is running alongside it. The
gate does not import the generator, so the constant is restated on the gate side - keep the two
numbers equal and say in a comment that they are meant to be.
