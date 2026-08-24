# Asking the engine questions - the tools, and how a probe lies to you

**Load this file when:** A map came out wrong and you need to know WHY, you want to know where a feature fits or who placed one, or you are about to write a throwaway probe.

Split out of [`../CLAUDE.md`](../CLAUDE.md) so it is not in every diagram session's
context. The text is verbatim; the short always-on version of each rule stays in the index.

## Ask the ENGINE where a feature fits - do not guess coordinates

When a map change ripples (an avenue shortens, ground frees, a pack seats more houses, a well goes
over its household cap), the fix needs a spot for one more feature. **Guessing coordinates and
regenerating is the most expensive loop in this skill**: 2026-07-25 spent three regenerate-and-check
cycles on two full batches of hand-picked well seats, every one refused. A scan of the MANIFEST
cannot predict `_fits` - those refusals came from a ward fence's 15px no-build corridor, which no
manifest records.

`s.open_seat(rect, w, h, clear_of=[...], well=True)` asks the engine's own `_fits`, at the point in
the gen where the feature would be placed, and returns the best clear seat (furthest from
`clear_of`, ties toward the rect center) or `None` if the ground is genuinely full. It found the
seat both hand-picked batches had missed, first try. Reach for it on any "this pocket needs one more
X" - and note the DRAW ORDER caveat: it can only see what has been drawn so far, so call it where
the feature belongs, not earlier.

## Ask the GEN who placed it - do not grep for the caller

The other half of the same lesson. `open_seat` answers "where does this fit?"; **[`tools/why_placed.py`](../l7r/diagram/tools/why_placed.py)** answers *"who put this here?"* and *"what refused to put anything here?"* - the two questions you actually have when a map comes out wrong.

    python3 -m l7r.diagram.tools.why_placed pool/provincial-cities/nagahara.gen.py --at 1102.6,1429.5
    python3 -m l7r.diagram.tools.why_placed pool/provincial-cities/nagahara.gen.py --refused 1102.6,1429.5 --radius 12

`--at` prints every manifest record appended within the radius **with its call chain** - the gen
line to go and look at, and the engine method under it that chose the spot. `--refused` prints how
many `_fits` candidates were tested there, how many were refused, and **which sub-test said no**,
counted by cause.

WHY IT EXISTS (2026-08-08): a manifest record carries geometry and nothing about its provenance, and
~200 engine methods can append one. Chasing a single servant house that was abutting a ministry cost
about ten sequential greps through the `settlement/` package and the gen - `top_up`, then `servant_ranges`,
then the apron block polys, then `_fits` - and none of them answered it. A throwaway monkeypatch over
`M["buildings"]` answered it first try, in one run. This is that, made permanent.

**It OBSERVES, it never restates.** The refusal cause is read off the real `_in_blocked` /
`_near_corridor` / `_hard_clear` as they return; when `_fits` refuses and none of those did, it says
so in exactly those words rather than guessing which of the remaining clauses it was. Same discipline
as `tools/site_justice.py` asking the gate instead of re-implementing it - a diagnostic that re-derives a
rule drifts from it and then tells you the wrong thing with total confidence.

Two notes worth having: `--refused` reporting **"no candidate was ever tested here"** is a different
finding from a refusal - the ground is UNVISITED, so look at the region the placer was given, not at
the keep-outs. And a `--at` miss usually just wants a bigger `--radius`: a re-pack moves things.

## Siting a feature with interacting rules: adjudicate against the GATE, never a re-statement of it

`open_seat` (above) answers "does this fit here?" - geometry only. When a feature's placement is
governed by many INTERACTING rules, that is not enough: the justice works (feature 015) must be
outside the wall, on the way out, past the boundary stone, clear of the community's dead, off the
farmland, on the outcast side, clear of every structure, and inside the map's current view. Use
[`tools/site_justice.py`](../l7r/diagram/tools/site_justice.py):

    python3 -m l7r.diagram.tools.site_justice pool/provincial-cities/nagahara.json execution_ground --limit=25
    python3 -m l7r.diagram.tools.site_justice pool/towns/hirameki.json boundary_marker --ground=1620,1900

It proposes seats **cheapest-on-the-frame first** (`frame_cost=0` means the crop is unchanged by
that seat) and adjudicates each one by building a trial manifest and running `check_village.gate()`
on it, reporting the checks that fail there but not with the feature absent.

**The lesson, which generalizes past this feature.** Its predecessor was a scratchpad script that
re-implemented every rule as its own predicate, and it drifted *within a single session*: a
relaxation made to satisfy one map silently persisted and put Nagahara's boundary stone in a field
off the highway. The gate accepted it because the rule it broke was not yet checked, and only the
rendered PNG showed the problem. So a siting tool must never restate a rule - it must ASK the gate.
New rules are then picked up for free, and the tool cannot disagree with the checker. This is the
same trap as "placement and its check must read the SAME manifest source" ([`gate.md`](gate.md)), one level up.
The cheap geometric pass in that file is a RANKING only: it orders candidates to keep the number of
gate runs small, and it never rejects, so a stale heuristic costs runtime rather than correctness.

**The second trap, found the same way (2026-07-26): "adds no new failure" is only HALF of legal.**
The tool's baseline is the gate with the feature ABSENT - so for a feature whose absence is itself a
failure, the very check that governs it is already IN the baseline, and a seat that leaves it
failing adds nothing new and scores as legal. Every candidate stone therefore looked equally good,
and the tool duly recommended the one that put Ubame's dosojin among the west-end shops. `propose`
now also requires a seat to CURE the checks the absence causes, with "curable" derived from the gate
(a check some adjudicated seat clears) rather than declared - so the tool still names no rule of its
own. The general lesson: when an oracle scores a candidate as a DELTA against a baseline, ask what
the baseline is already failing, because a delta cannot see a rule the empty case breaks too.

**Known limit:** label collisions cannot be judged from a manifest - a label box is produced at draw
time, not recorded for a hypothetical placement - so `labels_clear_of_other_buildings` and
`no_label_overlaps` still surface only on regeneration. That is why `punishment_spot` and
`execution_ground` both take `label_above` / `label_xy`.

## Read derived geometry from the MANIFEST, not by re-running the generators

Second-biggest sink in that same profile: **7.6 minutes across three runs of a throwaway analysis
script that re-ran all 17 generators** to compute where trees overlapped buildings. Every one of
those runs was answering a question the manifests could answer directly - the same analysis reading
`pool/*/*.json` takes **0.2 seconds**. The pool JSON is the artifact: outlines, footprints, clump
centers, `tree_crowns`, ditch polylines are all in there. Re-run a generator when you need to change
what it DRAWS; read the manifest when you need to know what it drew. If the geometry you need is not
recorded, that is usually a sign the CHECK needs it too - record it once and both problems go away.

## Batch the rendered-map inspection

Reading a map means: render -> crop the region(s) of interest -> Read the PNG. The turn-latency
killer is doing this serially, one crop per turn (`crop -> Read -> crop -> Read ...`). ~78% of
wall time is model-turn latency (root CLAUDE.md, 2026-07-20 profile), so each extra round-trip is
pure cost. Instead: in ONE Bash call, crop EVERY region you want to look at (all four viewports of
a defect, before/after of several maps, the toe + the top + a control), then Read them together in
the next turn. A footbridge review that touched 3 maps should be ~2 turns of imagery, not ~10.
**Use [`tools/crop_map.py`](../l7r/diagram/tools/crop_map.py) rather than re-writing the arithmetic** - it reads the viewBox
itself and takes as many regions as you like in one invocation, which is the batching win made easy:

    python3 -m l7r.diagram.tools.crop_map pool/towns/hoshizora 1600,900,220 1200,400,150   # x,y,radius (world coords)
    python3 -m l7r.diagram.tools.crop_map pool/hamlets/moritono --box 2100,150,2418,760 --zoom 1.5
    python3 -m l7r.diagram.tools.crop_map pool/villages/ueda --whole --zoom 0.4            # whole map, downscaled

It prints one path per line - feed them straight to Read, together. (The conversion is
`(coord - viewBox_origin) * (png_w / viewBox_w)`; it was hand-written five times in one session,
once wrong, which is why it is a script now.)

## A DIAGNOSTIC that restates what it observes will lie to you, or die

Three probes in one session, two of them wrong in ways that cost a full round trip each:

- `tools/why_placed.py`'s `_fits` wrapper had **re-declared `_fits`'s parameter list**, so the day
  `_fits` gained a keyword the tool died with a `TypeError` in the middle of the gen it was
  supposed to be observing. It takes `*a, **kw` now. Same rule as `tools/site_justice.py` asking the
  gate instead of re-deriving it: a tool that OBSERVES must not re-declare the thing it observes.
- A hand-rolled probe listed, for each refused seat, every corridor **covering** it - which is not
  the same set as the corridors that **refused** it, because it ignored `skip`. It named the very
  street being fronted as the culprit. Patch the real predicate and read its verdict; do not
  reconstruct the verdict beside it.
- The next probe measured refusals **near a point** rather than **inside the run**, so it charged
  a frontage row for refusals belonging to the pack that ran after it. Attribute by CALL (wrap the
  helper and tag everything inside it), not by proximity.

The good version of this is cheap: wrap `_shortfall` and walk `inspect.stack()` for the frame in
the GEN file, and every run is attributed to the exact gen line that wrote it - which is how 10
call sites across three shipped cities got classified in one run.

**A FOURTH AND FIFTH, both from one session (2026-08-17), and both the same tell: a probe printing a
VALUE and a LOCATION that came from different computations.** Chasing the seeds 9/11 seam regression:

- The first probe counted every `_absorb` decline as "declined by the new guard", when most were the
  pre-existing MultiPolygon / hole / bow-tie rejections that have always been there. It had
  re-implemented the candidate ranking beside the real one instead of observing which clause said no.
- The second printed the apex VALUE as `min(raw, dedup_ring(...))` and, next to it, the worst vertex
  of the RAW ring - two different rings. The value came from one and the coordinates from the other,
  which produced a confident and completely wrong finding ("these apexes are 90-100 px from the
  scrap, so they are pre-existing artifacts"). It was written into a code comment before it was
  checked, and the correct probe showed the apex 33 px away and genuinely made by the weld.

The rule that catches both: **print the value and its provenance from ONE expression, or do not print
the provenance at all.** A probe that derives its number and its explanation separately will
eventually pair a true number with a false explanation, and that is worse than no probe - it is a
wrong answer wearing the costume of a measurement. (Cost here: two wrong conclusions, one of which
became a documented "genuine geometric conflict" that did not exist. The actual causes were a unit
error and a measure-a-different-ring mismatch - see `future-work/`, "cohort seeds 9 and 11".)

## A dirty tracked manifest with no code change behind it: suspect the MEASUREMENT, not the generator

`title()` sizes its placard by measuring the name's glyphs with PIL (`_text_width`), and that
measurement is recorded in the manifest - so anything environmental that shifts it by a fraction of a
pixel rewrites every titled map's bytes with no code change in the diff. That is what a container
rebuild did on 2026-07-25: PIL picks its layout engine by what is installed (RAQM where libraqm is
present, BASIC where it is not) and the two disagree at the subpixel level, so all 16 titled
manifests came back dirty at once. The fix was to PIN the engine - see `_text_width`'s docstring and
`test_text_width_is_pinned_to_the_basic_layout_engine`, which holds the pin so it cannot come loose
silently - and the pool is byte-reproducible on any container again.

The transferable part is the DIAGNOSIS, because `render-sync` reports this and a genuinely
nondeterministic generator in the same words. Diff the manifests SEMANTICALLY, key by key
(`json.load` both sides and compare) - never as text, since these are single-line JSON files where a
text diff always shows the whole file and tells you nothing. Only `title`/`scalebar` moving, by a
hair, uniformly across every map, is a measurement-environment signature; a house, a ditch, a crown
or a count moving is a real bug. And when a recorded value depends on something git does not carry,
pin the dependency rather than re-recording the drift - re-recording just waits for the next rebuild.

## IDENTICAL NUMBERS ACROSS DIFFERENT CODE ARE EVIDENCE ABOUT THE HARNESS, NOT THE CODE

Feature 123, and it cost three cohort rolls plus a confidently-wrong write-up that had to be
retracted from its own spec.

Four cohort seeds were failing a new check. Three separate fixes were applied and measured, and each
time the failing distances came back **byte-identical** - 203 / 227 / 289 ft, to the foot, across
three supposedly different implementations. That was written up as a finding: "none of which moved
the numbers by a single foot, which is itself the diagnostic", and the conclusion drawn was that the
maps were unfixable for a structural reason.

The real diagnostic was staring at me. **Byte-identical output across three different changes does
not mean the changes were ineffective; it means the changes were not running.** All three had been
applied with heredoc'd Python patch scripts that printed a success line and never wrote to disk. The
project already has a rule against this (root CLAUDE.md: edit with `Edit`, not with Python that
rewrites files) and the reason it exists is precisely that a patch script fails SILENTLY, in the
patcher, so the anchor never gets tested. Re-applied with `Edit`, the same three ideas took every one
of those seeds green.

**The rule:** a run that reproduces a previous run to the digit, after a change that should have
altered it, is a claim about your TOOLING first. Before spending a measurement on it, verify the edit
landed - `grep` the new symbol on disk, not in the script's output. One grep would have saved three
rolls and a retraction.

The general form is the same one this file already carries for probes: **a diagnostic that restates
what it observes will lie to you.** A patch script that prints "patched" is restating its own
intention, not observing the file.
