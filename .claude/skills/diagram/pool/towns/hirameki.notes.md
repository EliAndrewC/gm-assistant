# Design notes: Hirameki, a WALLED border town that changed hands

*Reconstructed 2026-08-08 from the generator's docstring and comments, which until then were the
only record of this map's intent. Everything below is sourced from `hirameki.gen.py`.*

**Subject**: a county seat of ~1,200, drawn to scale at 1 px = 1 ft. Historically a Chinese walled
county seat / Japanese *jokamachi*: the urban castes - merchants, artisans, laborers, servants and
samurai - live INSIDE the walls, zoned around the magistrate's hilltop citadel, and only the
farmland and farmhouses, the segregated burakumin neighborhood, and a small *guan-xiang* gate-market
lie outside. The surrounding farmers retreat inside during a raid. The hill's steep back defends the
north flank; the Imperial chrysanthemum field abuts the inside of the west rampart.

**Why it exists**: the pool's **walled town with NO Imperial road** - the third corner of the
triangle its siblings complete (Hoshizora unwalled with a road, Ubame unwalled with none), so every
rule keyed off `meta.walled` or `meta.imperial_road` runs on real geometry from every side.

**The organizing fact**: Hirameki **changed hands during the Lion/Crane war**. That is why it is
walled while its interior-county siblings are not, and it is visible in the religious geography
(below) rather than merely asserted. Per the dev-loop doctrine on unusual maps: Hirameki was drawn
early and is atypical, so lock rules in against the ORDINARY settlements first and let this one earn
its exceptions.

## GM decisions (settled - not open for re-litigation)

| Decision | Value | What it drove |
|---|---|---|
| Walls | yes, irregular, anchored to the hill | the S/SE/E faces hug the built core rather than enclosing empty corner space - a tighter line is cheaper to build (`wall_hugs_the_town`) |
| Imperial road | none | no farrier: an ordinary market town's smith shoes in his shop row |
| Clan | **Lion** (current holder) | patron fortunes Bishamon + Daikoku |
| Monasteries | **Bishamon AND Benten**, set explicitly | the override that carries the town's history: the main hall is Lion's Bishamon; a much smaller, older Benten hall (Crane's patron) survives on the far side of town, a relic of Crane rule |
| Land fall | SOUTH (`downhill="south"`, `down_deg=90`) | the hill and manor sit north, so streams run north-to-south and every irrigation channel taps upstream (north) of what it feeds |
| Scale | 1 px = 1 ft | the scale-ladder pass: the old `bscale` 0.82 grain implied ~1.3 ft/px and made this the one town out of step with the others. The rampart is the SAME real wall, redrawn - the ring is the pre-rescale ring scaled ~1.22x about the hill anchor |
| Population | 780 depicted (156 dwellings x5) | urban housing full, most farms off-map: a slice of the ~1,200 county |

## Water: five combs, each with a real source and a real sink

Every field is a `build_comb` fan, and the interesting part is how each one is fed and drained:

- **w1** (NW, outside the wall): its own hill brook off the north edge, fully diverted at the sluice
  (the akagahara pattern); MIRRORED chirality so its collector descends WEST and empties back into
  the west stream through a short culvert.
- **w2** (W, off the west edge): fed by a brook in from the west edge; collector discharges off-map
  west. Most of w2 is off-map, so its delivery tails are trimmed to the crop - otherwise a branch
  overshoots the planted edge into bare ground.
- **e1** (NE, between wall and east stream): its own hill brook off the north edge; collector
  culverts east into the east stream. A short relief culvert tees the collector's east end back into
  the stream at a proper confluence, rather than leaving it dangling mid-air beside the water.
- **e2** (E, below e1): **CASCADE-fed** - a drawn connector carries e1's surplus from its drain down
  into e2's head (*tagoshi* between fields), so the two combs' ditch nets join into one component
  tracing back to e1's brook. Because no sluice exists on a cascade-fed comb, the auto head-race
  would dangle with a free top end; it is shortened to a throat above the fork and the connector is
  routed THROUGH the throat's top, so the water visibly arrives where it enters.
- **s1** (S of the gate, off the bottom edge): the **west stream itself bends southeast below w2 and
  is swallowed whole at s1's sluice** - a stream diverted into an irrigation head, the sanctioned
  brook-into-channel ending.

Every culvert mouth reaches the receiving stream's CENTERLINE so the join is a real confluence, with
the drawn bed trimmed back onto the bank edge so the mouth covers the bank stroke without crossing
the current.

**Comb grain** is the same as Hoshizora's and recorded for the same reason: `plot_across=58`,
`row_step=(52,72)`, ~58 x 62 ft paddies at ~0.08 acre, one plot still visibly outsizing the 46x28 ft
farmhouses. The old 66 px quilt figure is not reused - the 132 px delivery-ditch floor it implies
skips every offtake on a town-scale comb's short canals.

The two LARGEST fields deliberately differ in orientation - e1 wide against s1 tall - which is what
`common_fields_vary_orientation` is asking for.

## Deliberate choices

- **The two monasteries are the town's history, drawn.** The Bishamon hall has a long clear approach
  south to the market cross-street, so it fronts a proper torii AVENUE; the older Benten hall is
  wedged hard against the west rampart and the chrysanthemum field, with room for a SINGLE arch. The
  asymmetry is the point - the conqueror's hall got the processional way, the predecessor's did not.
- **The NW wall face tucks IN toward the Benten pocket** as two segments rather than one long
  diagonal: the straight line left a ~325 ft empty run beyond the hill base.
- **The market cross-street starts EAST of the Imperial chrysanthemum field.** A public street cannot
  be cut through a protected Imperial planting. This constraint is Hirameki-specific.
- **The laborer/servant quarters have no street frontage**, sitting as deep tenement blocks accessed
  off the cross-street: the poor cannot afford frontage, and speculative back-lanes would dead-end
  empty (`streets_have_buildings`).

## Review log

- **2026-07-27: the population waiver EXPIRED BY CHECK, and the map is the argument for that
  design.** The waiver excused Hirameki for not landing on its population/household figure exactly,
  and said in its own words that `waivers_are_live` would delete it "the day the map meets its figure
  on its own." That day arrived when the comb-toe filter (`waterfields._TOE_MIN_THICKNESS`) stopped
  carving unbuildable slivers at the fan vertex, freeing ground for one more farmhouse - and the town
  stood at exactly 156 dwellings for 156 households. **Nothing was tuned to reach it**; a fix three
  features away did it. That is the whole case for waivers that expire by check rather than by
  someone remembering to revisit them.
- **2026-08-08 RNG re-roll** (positional/scoped randomness, engine-wide). The re-roll's new jitter
  fitted 5 more homesteads and several more urban dwellings than the counts were tuned against,
  putting the town 14 dwellings over its declared 780. Fixed by trimming the inner ring attempts by 2
  apiece (attempts, not placements - the homestead solve still drops roughly half) and cutting the
  fill=False laborer pack from 16 to 11. The scrub-vs-fabric failure that came with it went away with
  the same trim.

## Known open

- **No `notes.md` existed for this map until 2026-08-08**, so anything settled between its authoring
  and that date lives only in gen comments and may not be recorded here. Treat gaps as unrecorded
  rather than as decided.
