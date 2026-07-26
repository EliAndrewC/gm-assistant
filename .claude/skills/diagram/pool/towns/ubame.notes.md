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

## Negative fixtures frozen from this map

Six, in [`../regressions/`](../regressions/) - each the real Ubame manifest with exactly one thing
broken, so every new check has a case it demonstrably fires on:
`charcoal_yard_keeps_fire_gap` (a yard 20 ft off a house), `charcoal_yard_has_cooling_ground` (a
covered-only yard), `settlement_has_charcoal_yard` and `settlement_has_refining_forge` (a declared
district drawing nothing), `refining_forge_stands_off_dwellings` (a forge 30 ft off a house), and
`refining_forge_downwind` (a forge moved upwind of the town it smokes over).
