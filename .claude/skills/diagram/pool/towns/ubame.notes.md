# Design notes: Ubame, county town of Ubame county

**Subject**: the county seat of Ubame county, Moriguchi province, Daika domain (Scorpion Clan) - the
easternmost of Moriguchi's five counties and the one the road from the Kitsune Mori arrives in.
Canon: `l7r.md`, "The Kurogi and the dynasty province of Moriguchi". Its magistrate is Bayushi no
Daika Koharu, whose compound is the separate Mode A sheet
[`pool/magistracies/ubame-magistracy.svg`](../magistracies/ubame-magistracy.svg).

**Why it exists**: the GM asked for a third pool town to test the placement algorithms and the
automated checks on fresh geometry. It is deliberately the third **combination** - Hoshizora is
unwalled with an Imperial road, Hirameki is walled with none, Ubame is **unwalled with none** - so
every rule that keys off `meta.walled` or `meta.imperial_road` runs a path neither existing artifact
covers.

## GM decisions (settled before drawing, not open for re-litigation)

| Decision | Value | What it drove |
|---|---|---|
| Walls | none | centuries of peace with the Fox; no rampart, gate market, fire tower or drum tower |
| Magistracy | NE corner, east wall ON the border, `gate_dir="south"` | the town spreads south and west below it |
| Road | domain trunk road (the charcoal road) | **unlabeled**; no farrier |
| Land fall | mountains NE -> `down_deg = water_flow = 135` | stream runs south; downstream is SW |
| Trade | a charcoal yard **and** a refining forge, drawn | two new engine features (feature 016) |
| Charcoal kilns / iron furnaces | off-map in the hills | canon: charcoal is burned where the wood grows |
| Potters' kiln works | drawn, on the frontier strip (added 2026-08-17) | a pottery kiln stands at its CLAY, the opposite pull; carries the campaign clue |
| Clan | Scorpion | monasteries default to Benten and Jurojin |

## The border, which is the map's organizing fact

The east edge of the sheet **is** the Fox/Scorpion line. The Mode A sheet fixes the compound's
orientation - a ceremonial SOUTH face to the county town and a frontier EAST face, with a parley
room built into the border wall and the line running across its floor - so on this map the manor
sits at the northeast with its east wall on the drawn line.

- The line is `s.border_line(...)`: a **line of law**, classified `_OVERLAP_EXEMPT`, because the
  magistracy standing on it is the arrangement rather than a defect. The period *physical* marker
  was an earthen mound, which is a structure everything would have to stay clear of - the opposite
  of what this compound is for - so the mound is deliberately not what is drawn.
- **The two artifacts of one place must agree.** The manor is drawn at the Mode A envelope's real
  **290 x 200 ft**, not at a convenient size. The first draft had it at 250 x 180, which is the kind
  of quiet contradiction between two sheets of the same place that is worse than either error alone.
  The oak stand was pulled north to make room rather than shrinking the compound.

## Water and fall, settled before anything was placed

The campaign map puts the mountains northeast, so the land falls NE -> SW (`down_deg=135`) and the
valley stream comes down off that high ground, crosses the trunk road at a **bridge**, and runs away
south off the bottom edge.

**Why the stream runs nearly due SOUTH rather than diagonally**, which is the one non-obvious
geometric decision on the sheet: at `down_deg=135`, `build_comb`'s frame opens its fan to the
SOUTHWEST of the sluice (canal A at down-42 deg, canal B at down+58, delivery ditches dropping
down-fall between them). A stream angled across that fall gets **quartered by its own fields** - the
first draft ran the stream NE->SW and the west comb's fan promptly straddled it. Authored due south
down the eastern side, the fans open away from the water into the lower west, which is what a real
valley looks like anyway.

## THE TWO NUISANCE AXES DIVERGE HERE

This is the map's real value as a test bed. **Smoke goes downwind; filth goes downstream**, and they
are different rules. On Hoshizora and Hirameki both point the same way, so a bug in either is
invisible. On Ubame the wind is the default NW monsoon (downwind = SE) while the water runs S/SW, so:

- the **refining forge** sits east, downwind of the housing;
- the **tanning yard** sits south on the stream, below every intake;
- the **burakumin quarter**, the **boundary stone** and the **execution ground** sit west/southwest.

`refining_forge_downwind` is therefore doing real work here rather than agreeing by accident.

## The charcoal and iron front (feature 016)

- **Charcoal yard**, east approach, between the magistracy's tally and the town. Roofed stacking
  sheds for conditioned stock, an **open cooling apron set apart from them**, a weighing floor.
  The apron is the research made visible - charcoal self-heats, so fresh loads may not go straight
  in with the old stock - and the weighing floor is there because the charcoal bale had no standard
  weight, so nothing could be traded by count. It **stands alone by design**: the 30 ft fire gap is
  the rule, not a packing accident.
- **Refining forge** (*okaji*), east and downwind. Open-sided two-hearth shed, charcoal store,
  quench trough, slag heap, stacked bar iron. Ubame follows the **Japanese two-site** tatara/okaji
  split rather than the Chinese adjacent-hearth arrangement, and that divergence is disclosed with
  its reason: dispersed fuel forces two sites. Full grounding in
  [`../../settlements/urban-features.md`](../../settlements/urban-features.md) and
  [`../../research/urban-features.md`](../../research/urban-features.md).

## The potters' kiln works and the two carts (GM, 2026-08-17)

**The one deliberate edit to this map since the legacy pool was frozen on 2026-08-16.** The GM's
party is running an adventure in Ubame county, and asked for something in the county town that an
attentive player could notice and act on - a clue to the charcoal-counterfeiting bounty on the
Imperial bulletin (`l7r.md`, *"Kitsune Denhei" the charcoal counterfeiter*). The GM's own proposal
was carts of black and white charcoal standing at a kiln works, on the reasoning that white charcoal
has no business at a kiln works; that is what is drawn. **Who is behind the counterfeit is
deliberately not recorded in this file** - the bulletin is public canon, the culprit is not, and a
design journal that ships in the repo is the wrong place for it.

### The freeze exception, and what it actually cost

`ubame.gen.py` is in `LEGACY_FROZEN_GENS`, so this needed the GM's explicit say-so and it got it.
The cost was **measured before anything was edited** rather than assumed, and it was near zero:

- The unmodified gen was copied to `wip/`, re-run on the current engine, and its manifest compared
  key-by-key against the committed `ubame.json`. **Byte-identical** - same counts, same positions,
  every house and building in the same place. Nothing in the engine has re-rolled this map since it
  shipped, so regenerating it does not silently produce a different town.
- The gate on that re-run showed **three failures**, all in the field/water engine
  (`dry_plot_seams_shared`, `delivery_ditches_taper`, `comb_supply_commands_both_flanks`), plus the
  map's own documented `tanning_yard_on_the_outcast_side` waiver. Those are post-freeze rules landing
  on a pre-freeze map - **pre-existing, ledgered, and not fixed under this change** (constitution
  Principle XIII). The bar this edit had to clear was "no fourth failure", and it clears it.
- Regeneration is 7 s. **This does not reopen the freeze**: the list stays closed, and the fix for a
  frozen map that breaks a post-freeze rule is still conversion, not retrofit.

### Why a kiln works does not contradict this map's "kilns are off-map" canon

The GM decision table above says *Kilns / furnaces: off-map in the hills*, and that stands unchanged.
It is about **charcoal kilns and iron smelting furnaces**, which follow the fuel: a kiln reduces
roughly six parts wood to one of charcoal, so both go to the wood, miles up the county, and what
comes down to the town is finished charcoal and pig iron.

A **pottery kiln obeys the opposite pull** - it stands at its clay, not at its customer - which is
why `s.kiln` exists as a peripheral works in the first place, and why Tango, Minami and Nagahara all
carry one. Ubame was the only settlement in the pool with no kiln works at all, which on inspection
was an omission rather than a decision: every seat breaks and replaces bowls, pots and jars on a
continuous cycle, and this one has a brewery's worth of vessels to keep in service besides.

**The confusion hazard is real and is why the label is not the default.** `research/urban-features.md`
records that the pre-2026-07-27 kiln glyph was a low earthen mound - a charcoal kiln's shape - and
that Ubame's charcoal district made the two indistinguishable. The glyph is now a chambered climbing
kiln, which is a different silhouette, but on **this** sheet that is not enough on its own: a caption
reading "kiln works" in a charcoal county invites exactly the wrong reading. So it is captioned
**"potters' kiln works"**, and that is a disambiguation rather than a violation of the
don't-label-the-obvious rule.

### Where it stands, and why

On the frontier strip east of the charcoal yard, at (2000, 625). Three constraints agree there:

- **Clay and slope.** The strip is the sheet's high side - the land falls NE -> SW (`down_deg=135`) -
  and it lies under the ubame-oak hill, so a chambered climbing kiln has real rising ground to be
  built into.
- **The fire ladder, by geometry rather than luck.** The kiln body sits ~96 ft off the charcoal yard
  and ~82 ft off the refining forge, against the 60 ft attended-fire rung (`kiln_keeps_fire_gap`).
- **The ground was already the right kind.** This is the ox-teams' standing ground: hard, tamped,
  peripheral, town-owned and carted over all day. A works is what such ground grows.

### The angle is derived from TWO things, and needed both

`rot` is computed in the gen, not picked. Two wrong answers were rendered first, and both are worth
recording because each looked right until something else was consulted:

1. **A hand-picked `rot=-90`** ("climb due north up the oak stand") failed
   `roadside_works_stand_on_their_road` at 82 deg adrift. The check is right and the intuition was
   wrong: a kiln carts its fuel, its clay and its ware, so it lies along its haul road.
2. **Taking `_way_bearing_near` raw** then put the chambers WSW, and the render came out with the
   firebox high and the chimney low - a noborigama climbing downhill, which is the one thing it
   cannot do. `ROAD` is authored east-to-west, and the helper returns the way's *stored* direction.
   **Nothing in the gate can see this**: `roadside_works_stand_on_their_road` compares axes mod 180,
   so both senses pass it identically. Only the render caught it.

So the **axis** comes from the road and the **sense** comes from the fall: keep the way's bearing,
flip it 180 deg if it points down-fall. Both inputs are read at draw time, so a re-routed road or a
re-declared land fall turns the works rather than falsifying it.

**What that costs, priced rather than assumed** (`settlement-review`, 2026-08-17): the works climbs
at 351.9 deg while the fall line runs 315/135, so it lies **37 deg oblique to the slope** and takes
only cos(37) = 0.80 of the available gradient. A chambered climbing kiln would ideally be built
straight up the fall line. The road pull won, deliberately - a works that does not stand on its haul
road is wrong in a way a reader can see from the road itself, where 20% of a gradient is not - and
37 deg sits inside the obliquity this pool has accepted elsewhere. Recorded so the next reader does
not re-derive it and reach a different answer.

## Standing it in plain sight

`settlement-review` measured something the siting reasons above do not mention: the works sits
**286 ft from the magistracy's south gate and 20 ft off its ceremonial axis**, and the Mode A sheet
is explicit that the south face is this compound's formal face to the county town. So a smoking
kiln, a cordwood stack and two heimen cottages now stand on the magistrate's own approach.

**That is the intended reading, not an accident of packing**, and it is written down here precisely
because an unexamined coincidence and a deliberate choice look identical a month later. Two things
already made it defensible - the charcoal yard and the refining forge sit on the same approach 150
to 250 ft west, and the works is downwind of the compound - so nothing about it is anomalous to a
passer-by. What makes it worth choosing rather than merely tolerating is the fiction: the ground the
counterfeit runs through is not hidden, and the note above should not be read as claiming it is.
Nothing here is fenced; the works' boundary is a tamped-earth panel, not an enclosure. The claim
that "the magistrate's tally does not reach it" is **documentary, not visual** - everything crossing
the charcoal yard is weighed and sealed, and nothing crossing this yard is. Concealment was never
the mechanism. Standing it where anyone can see it, including the magistrate, is the mechanism.

**The alternative was priced and declined**: shifting the works 60 to 100 ft east or south takes it
off the gate axis and behind the charcoal yard's line, and costs nothing geometrically. It was
declined because it buys tidiness at the cost of the only thing on this part of the sheet that is
saying something.

### The frontier common is now two bands, and that is not the old defect

The strip used to be one polygon from y 450 to y 1112; the works stands on it between y 556 and 694,
and scrub may not claim ground the town stands on (`scrub_clear_of_urban_fabric`). It is now two
bands with the works standing in the gap. **This is not the 2026-07-26 "boxes with bare aisles"
finding coming back** - that was four rectangles with nothing between them, polygons satisfying a
cover check instead of being a place. Here the interruption is a building, which is what happens to
a common when a works is put up on it, and note which way the numbers go: the split makes cover fall
rather than rise, which is not an edit a check-driven author makes.

It does **not** fill the gap edge to edge, and an earlier draft of this paragraph said it did
(`settlement-review`, 2026-08-17, which measured it). The works' rotated extent is x 1922-2078
against a 1900-2104 band, so ~22 ft of bare ground survives down its west side and ~26 ft down its
east, each running the gap's ~160 ft. Left alone deliberately: scrub drawn into slivers that thin is
much closer to what the 2026-07-26 finding was actually about than a little bare margin is.

### The carts: what was accepted, and what was declined

Two handcarts stand in the works' yard, one loaded with black charcoal and one with white. A pottery
kiln burns **cordwood** - never charcoal, and least of all white charcoal, which gives radiant heat
with no flame and costs many times what a firing is worth. So a load of black charcoal here has no
business in this yard, and a load of white beside it has none twice over: the county's white charcoal
belongs in the tallied charcoal yard 100 paces west. The works is also the town's supply of the exact
material the bulletin names - sieved kiln ash, which a potter has every honest reason to keep by the
barrel for ash glaze.

- **Drawn at true size and DELIBERATELY UNLABELED.** A 12 ft bed, 5 ft wide, with shafts and wheels.
  The map states what stands there and lets the reader ask why; a caption would answer the question
  the carts exist to pose.
- **ACCEPTED: at 1 px = 1 ft they are small**, and at fit zoom they read as two pale-and-dark marks
  rather than as carts. They resolve properly at 100% and above, which is how the GM reads these
  sheets. **Two alternatives were priced and declined.** Drawing them at 1.5x-2x for legibility was
  rejected outright - to-scale modes encode true researched sizes, and this map's own notes already
  turn down size inflation elsewhere. Captioning them ("charcoal carts") was rejected because it
  destroys the only thing they are for. The residual cost is that a player handed a printout at page
  scale will not see them, and the GM points at them instead; that is the trade, chosen knowingly.
- **They are interior detail of the works' record, not a feature of their own** - the same convention
  the charcoal yard's sheds and the tanning yard's furniture follow. They sit inside one footprint
  that is already classified for overlap, so nothing in the matrix needs to learn about them.
- **The draw order is load-bearing.** The first pass drew the wheels LAST, and the outer wheel
  covered ~70% of the third bale, so a three-bale load read as two and a sliver
  (`settlement-review`, 2026-08-17). Wheels now go down first, which is also where an axle is.

### What `settlement-review` found (DELTA pass, 2026-08-17)

Verdict **pass, no errors**, five judgment findings, all invisible to the green gate. It
independently re-ran the gate against a HEAD manifest and confirmed the three pre-existing failures
report **byte-identical text**, and that the manifest blast radius is one well, one label, the new
kiln record, and eleven dry plots in the SE hem moved by <= 4.7 ft. Nothing else changed.

Applied: the "edge to edge" overclaim (above), the cart-shaft comment that named a road 233 ft in
the wrong direction, the wheel occluding the third bale, the obliquity that was underived (above),
and the magistracy gate axis, which became "Standing it in plain sight" above rather than a move.

**Two findings were referred to the ENGINE rather than fixed here**, because both are `s.kiln`
defects that this map merely became the first to exhibit, and fixing them under a one-off content
edit would put a shared glyph change on four other sheets' account. Both are logged in
[`../../future-work/`](../../future-work/):

- the kiln's **smoke wisp is drawn in the glyph's local frame**, so on this sheet it trails NNW into
  a declared NW wind - the siting is right and the ink contradicts it;
- the works' **two cottages are mirrored about its axis with the well's saturated disc centered
  above them**, which puts the loudest mark in the works on its least important object.

Two more were heard and left: the kiln bar and the charcoal yard's bale sheds are both "a brown rect
with divisions" at fit zoom (the caption is the disambiguation, which is why it is not the default
one), and a cart is the same 12x5 ft as the kosatsuba (1,550 ft apart, one of them captioned).

## Deliberate choices

- **The execution ground is on the WEST road out, not the eastern frontier approach.** Both would
  satisfy the automated rules; a county does not conduct its executions at the gate its neighbor's
  envoys ride through. This is a judgment recorded here rather than a check.
- **No fire-watch tower** - same call as Hoshizora. The *hinomi-yagura* belongs to a dense enclosed
  wooden core; an unwalled seat at detached village grain has field gaps for natural breaks.
- **`near_ring_density="thin"`** is honest, not a shortfall: this is charcoal-and-iron country in oak
  hills, where the fuel stands are the crop and the flat waterable ground is one ribbon along the
  single valley stream. The paddy takes that ribbon; the dry quilt takes the western margins.
- **The two combs deliberately differ in grain** - a deep valley-floor fan and a wide south-facing
  spur (`down_deg=85`, a LOCAL fall, not the map's). Verisimilitude over uniformity, and it is what
  `common_fields_vary_orientation` is asking for.
- **The eastern frontier strip is grazed commons**, not waste: it is the standing ground for the ox
  teams that bring the charcoal down. Kept west of the border - the far side is Fox soil.

## Review log

- **2026-07-26 authoring pass.** First draft failed 26 checks; converged to green over six passes.
  The structural errors worth recording, because each was a real modeling mistake rather than a
  tuning miss:
  - **The stream was quartering its own fields** (see above). Fixed by re-authoring the watercourse,
    not by nudging the fan.
  - **The pond sat 600 px from its own drain outlet.** A drainage *tameike* is a reservoir BELOW its
    field; it was moved to where the collector actually discharges.
  - **The funerary cluster and the execution ground were fighting for the same corner**, which is how
    `execution_ground_clear_of_the_dead` fired at 401 ft against a 400 ft rule. The cemetery group
    moved east; the ground stayed on the road out.
  - **Hand-picked seats for the notice board and the punishment ground both failed** exactly as
    `place_punishment_spot`'s own docstring warns - `open_seat` ties toward the rect's CENTER, which
    is the open ground behind the frontage, precisely where a display installation must not be.
    Both now use the engine's verge probes.
  - **The boundary stone was standing inside a merchant's house.** Re-seated with
    [`tools/site_justice.py`](../../tools/site_justice.py), which adjudicates candidate seats against the real
    gate instead of a re-statement of it.
- **2026-07-26 render read (Principle I).** Two defects visible only on the raster:
  - **The windbreak drew as a round wood dumped in the middle of town**, hard against the flophouse.
    A back-village belt is long and narrow and lies along the cluster's windward fringe; reshaped
    into a NNE-SSW belt. The check it had been passing (`village_windbreak_embraces_cluster`) tests
    adjacency, not shape, so only the eye caught this.
  - **The manor was drawn 250 x 180 ft against its own Mode A sheet's 290 x 200** (above).
- **2026-07-26 caption-registry defect, found by eye and fixed in the ENGINE.** `border_line` emitted
  its caption as a raw `<text>` element instead of going through `self.label()`, so the label was
  **not in the registry and no label check could see it** - and it duly shipped sitting on a wellhead
  with a fully green gate. This is the standing "a check that never RUNS looks exactly like a check
  that passes" trap in its caption form, and the fix is in `settlement.py` with a test
  (`test_border_line_caption_defaults_to_the_lines_midpoint_and_is_registered`) so it cannot come
  back.
- **Seed 914** was chosen by sweep after the windbreak reshape: the belt's move freed ground that a
  merchant residence then took badly (a door opening into a neighbor's back wall). Re-seeding is the
  documented answer to a packing artifact, and the cover shortfall left over was closed
  deterministically by computing the actual bare cells and placing grazing commons on them.

- **2026-07-26 `settlement-review` round 1 (the agent's founding run).** The GM asked whether a Mode B
  reviewer existed; it did not - `building-review` and `size-audit` are both Mode A only, and
  `size-audit` hardcodes 3 px = 1 ft, so pointing it at a town map would have reported every feature
  at three times its real size. `settlement-review` was written and TDD'd against this map with the
  forge-as-face and blob-windbreak defects deliberately re-planted; **the whole gate was green
  throughout**. It caught both planted defects and **four more nobody planted**. Verified against the
  manifest before acting - three held, one did not:
  - **APPLIED, and each became an automated check first**: the trunk road ran **18 px inside the
    compound's south wall**, 80 ft from its own gate (`manors` is an overlap TARGET, never a
    candidate, so nothing had ever tested a compound's wall against a roadbed) -> road dropped south,
    new check `manor_walls_clear_of_ways`; three kitchen gardens and two commons reached **43 px past
    the border** onto Fox soil, which these very notes promised did not happen -> commons clipped, a
    no-build strip registered inside the line, new check
    `structures_stay_on_their_side_of_a_border` (tested on the CENTER, so the magistracy's wall may
    still stand on the line).
  - **APPLIED, no check**: both monasteries' innermost torii was drawn through its own hall's
    caption; one `village_grove` call silently drew nothing (a no-op in a gen is the same shape as a
    check that never runs); the high street carried 6 shops against the gen's own stated ~14, now 9
    with the merchant dwellings still in band.
  - **WRONGLY DISMISSED, corrected by round 2**: the reported vegetation on the theater stage roof
    was REAL. My verification queried `theater_stages`; the manifest key is `theater_stage`,
    singular, so the lookup returned nothing, the loop never ran, and I read the empty output as a
    zero. Round 2 named the exact ink - three `#94A063` scrub circles inside the stage footprint in
    `ubame.svg`. Even the corrected query would have failed: hinterland scrub is not recorded in the
    manifest at all, so no manifest audit can ever see it. The durable lesson is the opposite of
    what I first wrote: when a finding is about INK, verify it in the SVG.
  - **CONFIRMED by the reviewer and left alone**: the diverging nuisance axes, the unlabeled trunk
    road, the execution ground on the west road rather than the frontier approach, the manor drawn at
    its Mode A envelope, and the twin-detector verdict ("reads as its own place, not a re-skin").

- **2026-07-26 the boundary stone was inside the town, and the gate could not see it** (GM, reading
  the render: *"I would have expected it was at the edge of the settlement, but that doesn't seem to
  be the case"*). The dosojin stood at (247, 807), 91 real ft from the nearest merchant house and
  right beside the punishment ground and a wellhead - in among the west-end frontage rather than
  past it. Two holes, both now closed, and the shape of each is worth more than the fix:
  - **The check.** `execution_ground_past_the_boundary_marker` tested the stone's "outside" as
    `not _inwall_j(...)`. Ubame is UNWALLED, and there that predicate is False for every point on
    the map - so the clause did not relax, it passed anything. The execution ground had carried a
    dwelling-distance fallback for exactly this since it was written; the stone never got one. It
    now shares that 120 ft figure on an unwalled map, while a rampart still settles it outright
    where there is one (see `settlements/urban-features.md`, "The boundary stone").
  - **The siting tool.** `tools/site_justice.py` had proposed that seat and still did after the check was
    fixed, because it scores a candidate as `gate(with it) - gate(without it)` and the governing
    check FAILS while there is no stone at all - so a useless seat added nothing new. `propose` now
    also requires a seat to cure what the absence breaks.
  - Re-seated to (127, 887) - on the west road where it leaves the last houses, 204 ft from the
    nearest dwelling, 88 ft short of the ground it bounds.

- **2026-07-26 `settlement-review` round 3**, run against a freshly re-rendered sheet. (The PNG had
  been STALE: `finish()` writes the svg and then rasterizes, so a generator that dies in between - as
  every gen did during the `_reclist` crash, with stderr suppressed - leaves a new svg beside an old
  png. Any judgment made on that file in the interim was made on a picture of a different map.)
  - **APPLIED, engine**: `theater_stage` seated its caption at `cy + hh + 16`, the reach along +y
    only when the stage is UPRIGHT. Ubame's stands at rot=90, where the ground reaches `hw`, so the
    caption sat INSIDE its own ground with the outline stroke through the text. No check saw it -
    `labels_clear_of_other_buildings` polices captions on features they do NOT name, and this one
    was on the one it did. Correcting the reach ALONE then dropped Tango's caption onto a monk
    house, which is the lesson: a hand seat knows the geometry and nothing about the neighbors. It
    now goes through `place_caption`'s standoff ladder against the ROTATED extent, hinted at the
    historical seat so every upright stage in the pool stays exactly where it was.
  - **APPLIED, engine**: the painted-pine roundel is gone. The kagami-ita's pine is on the VERTICAL
    back board - a plan view cannot see it - and drawn as a green disc it borrowed the sheet's own
    vegetation idiom and read as a bush growing on the stage. Two review rounds blamed scrub for
    that read; the scrub was real and removed, but the misread survived because the GLYPH supplied
    it. A defect can have two independent causes, and killing one does not prove the other absent.
  - **APPLIED, check**: a `theater stage` caption may now sit on `temple` ground. That is not an
    exemption bolted on to make a map pass - the stage IS temple furniture (`theater_stage_by_temple`
    enforces the siting), so once the caption is seated properly it is inside a precinct wherever it
    lands. The allowance is scoped, and the test asserts a stage caption on a MERCHANT house still fires.
  - **APPLIED, gen**: the inn is captioned (the flophouse beside it was, which made the omission
    read as a judgment); "grazing" -> "hayfields & grazing" on a pasture drawn full of hay bales;
    the stale "~14 shops / ~5 servants" comment now records the drawn 9 and 9 as the honest counts.
    The inn caption's first seat was boxed against the UNROTATED footprint and duly landed 3 px on
    the inn's own corner - the center-vs-footprint family again, this time in a caption box.
  - **APPLIED, gen**: the four eastern commons became ONE frontier strip. They had drawn as stacked
    tuft blocks with bare aisles between them; the ground's real reason is the ox-team standing
    ground for sealed charcoal loads, and a strip is its true form. Merging RAISED cover (~116k px
    of boxes -> ~141k continuous), which is the tell that the boxes were the wrong shape rather than
    the right amount.
  - **REJECTED, with evidence**: the four west-edge slivers, reported as check-shaped cover with no
    place-reason. Merging them into one west-margin band fails `scrub_clear_of_urban_fabric` - the
    band swallows the stables and two burakumin houses, and scrub may not claim ground the town
    stands on. They are the GAPS BETWEEN the west-edge buildings, shaped by the fabric. Dropping
    them instead lands the sheet at 21% bare against a 20% allowance. Recorded in the gen so the
    finding is not "fixed" again by the next reader.
  - **REPORTED AS AN ERROR, WITHDRAWN - the GM ruled it a convention, 2026-07-27.** The reviewer read
    the Mode A magistracy sheet's two gate boards (one carrying the `100 koku - the hermit Shoda`
    bounty), absent from the town sheet, as the two artifacts contradicting each other. They do not.
    **The manor is a GLYPH and always a box**, a simplification rather than a scale reduction: the
    Mode B footprint need not match the Mode A sheet in shape or size, features the sheet draws
    OUTSIDE the walls need not appear, and the glyph is PRESUMED to contain everything the detailed
    drawing shows. Nothing is drawn at Ubame's gate and nothing should be. The rule is now written
    into `settlement.py`'s `manor()` docstring, `settlements/towns.md`, and `settlement-review.md`
    itself - the agent had been told a disagreement was an error and the Mode A sheet authoritative,
    which is what manufactured this finding.

    This also retires round 1's manor resizing as a NON-fix. The 250 x 180 -> 290 x 200 change was
    made to match the Mode A envelope; under the convention it was never required. It is harmless
    and stands, but the reasoning recorded for it - "two artifacts of one place must contradict
    nothing" - was wrong about extent, and `towns.md` has been corrected.
  - **CONFIRMED and left alone**: the pareidolia fix on the forge holds (no face); the windbreak is a
    belt, not a blob; the manor agrees with its Mode A sheet at 290 x 200 with its east wall ON the
    line; both nuisance axes diverge and every nuisance is on its correct one; the trunk road is
    correctly unlabeled; the twin-detector still reads "its own place" - with the fair caveat that
    the ARMATURE is Hoshizora's and a reader who knows that map will recognize it.
  - **STILL OPEN, engine-wide, reported not fixed**: the forge reads as a machine at fit zoom; the
    west comb's toe degenerates into slivers too acute to hold water (`build_comb`, visible on
    Hoshizora too); the town tier draws NO lanes at all, so warrens read as scatters rather than
    fabric; the windbreak faces west against a declared NW wind.

## Negative fixtures frozen from this map

Seven, in [`../regressions/`](../regressions/) - each the real Ubame manifest with exactly one thing
broken, so every new check has a case it demonstrably fires on:
`execution_ground_past_the_boundary_marker` (the stone standing among the west-end dwellings - the
map exactly as it shipped, frozen before the re-seat),
`charcoal_yard_keeps_fire_gap` (a yard 20 ft off a house), `charcoal_yard_has_cooling_ground` (a
covered-only yard), `settlement_has_charcoal_yard` and `settlement_has_refining_forge` (a declared
district drawing nothing), `refining_forge_stands_off_dwellings` (a forge 30 ft off a house), and
`refining_forge_downwind` (a forge moved upwind of the town it smokes over).
