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
| Kilns / furnaces | off-map in the hills | canon: charcoal is burned where the wood grows |
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
    [`site_justice.py`](../../site_justice.py), which adjudicates candidate seats against the real
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
  - **The siting tool.** `site_justice.py` had proposed that seat and still did after the check was
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
