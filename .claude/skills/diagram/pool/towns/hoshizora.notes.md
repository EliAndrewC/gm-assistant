# Design notes: Hoshizora, an unwalled county seat on the Imperial Road

*Reconstructed 2026-08-08 from the generator's docstring and comments, which until then were the
only record of this map's intent. Everything below is sourced from `hoshizora.gen.py`.*

**Subject**: a county seat of ~1,200 people / ~238 households, a **post/relay town on the Imperial
Road** in a quiet interior county. The map draws a scaled-down but complete social cross-section -
every caste present, farmers the plurality - rather than a literal 238 households: a rural farm zone
NW around the stream, a dense urban core along the road, the magistrate's walled manor and the
samurai houses SW, the segregated burakumin quarter NE, a theater stage by the monastery, barns in
the hayfield/grazing pasture SE, and a small forest.

**Why it exists**: the pool's **unwalled town WITH an Imperial road**. Its two siblings take the
other combinations deliberately - Hirameki is walled with none, Ubame is unwalled with none - so
between the three, every rule keyed off `meta.walled` or `meta.imperial_road` runs on real geometry.
`ubame.notes.md` states the same triangle from its own corner.

## GM decisions (settled - not open for re-litigation)

| Decision | Value | What it drove |
|---|---|---|
| Walls | none | no rampart, gate market, or drum tower |
| Imperial Road | yes, the SW->NE spine | earns the town its **farrier** (`imperial_road_town_has_farrier`); the road is labeled, no other way is |
| Monasteries | **ONE**, to Bishamon | a deliberate EXCEPTION to the 2-per-town default, declared via `monastery_fortunes` so the gate knows it is intentional: a quiet interior seat in a historically uncontested area really has only the one |
| Land fall | high NE, low SW - `down_deg=115`, `water_flow=145` | every channel and drain runs with it; stream and road both descend toward the SW corner |
| Magistracy | SW, walls only, `rot=-30` | its front wall runs PARALLEL to the Imperial Road and its north gate opens onto it; the interior is a separate Mode A subject |
| Fire-watch tower | none | same call as Ubame: the *hinomi-yagura* belongs to a dense enclosed wooden core, and an unwalled seat at detached village grain has field gaps for natural breaks |
| Seed | 479 | the tilted manor reshuffles the seeded packs; this seed lands the depicted population back on its mark |

## Water first, and the two combs are hydrologically separate

The valley stream crosses NE -> SW between the hay upland (NW) and the farm wedge (SE), roughly
parallel to the road, running off the west edge. **The main comb is wedged between stream and road**:
its sluice sits on the stream's east bank, a recorded **weir** taps the stream UPSTREAM of the sluice
(the historically-right tap position, which also keeps it running down-fall), the head-race forks
into supply canals, tapering delivery ditches drop down-slope, and the drain collector empties into a
**drainage tameike** at the low road-bend corner - a reservoir BELOW its field, sited in the only low
ground the town leaves open, which is exactly where a real one sits.

The **NE pocket comb** is the west TIP of a larger field running off the east edge, fed by its own
brook off the high ground NE and discharging OFF-MAP EAST. That separation is load-bearing, not
scenery: it is what makes the tanning yard's site honest (below).

**Comb grain, recorded so it is not re-derived**: at 1 px = 1 ft, `plot_across=58` with
`row_step=(52,72)` carves ~58 x 62 ft bunded paddies, ~0.08 acre - the mid premodern range, and the
scale relationship still reads (one plot visibly outsizes the 46x28 ft farmhouses beside it). The old
quilt figure of 66 px is **not** reused: `build_comb` spaces delivery ditches at 2x `plot_across`, and
that 132 px floor skips every offtake on the short canals a town-scale comb runs, degenerating the
comb to a ditchless sliver.

## Deliberate choices

- **The tanning yard sits on the NE comb's drain, not on a stream.** Hoshizora has no watercourse
  anywhere near the burakumin quarter - the valley stream runs across the far west - so the yard
  takes the one water the quarter reaches, the drainage ditch ~280 ft below their doors. It is the
  honest site rather than a convenience precisely because the NE comb discharges off-map east:
  nothing the yard fouls comes back through the town. `water="ditch"`, since an irrigation drain has
  no current to stake hides in, so the yard ponds its own soak through a gated intake cut.
- **`rot=43` on that yard is the DRAIN'S bearing, not a right angle off the map.** It was map-square
  until 2026-08-08, which passed `tanning_yard_square_to_its_water` only because the drain's short
  off-map sink stub runs 83 deg past the yard's east side - the check's "square to ANY course in
  reach" clause was satisfied by a 95 ft tail while the yard sat 47 deg askew to the 175 ft of drain
  it actually works. Green gate, wrong yard.
- **No footpath in the burakumin quarter.** Deepening its bbox to pay for the corridor moved the
  quarter and broke `burakumin_quarter_segregated`, and without the extra depth the corridor costs
  half its households. A quarter this size fronts open ground already.
- **Three keep-outs are registered BEFORE the farm rings**, because the to-scale homestead bundles
  reserve yard+garden+grove footprints and can only pack around an obstacle that already exists: the
  crematory's 120 ft ring (centered a touch west so it does not swallow the monastery's own
  ablution-well spot), a small block on the road-frontage corner where the shopfronts stand rotated
  along the diagonal road (the bundle packer's axis-aligned test cannot see a swung corner), and the
  **60 ft segregation collar** around the burakumin quarter.
- **The funerary ground is BEHIND the monastery** - parish graveyard against the back of the hall,
  cremation ground on the marginal western edge beyond it - so no one walks past the pyre to reach
  the monastery.
- **The monastery's sando stops at 3 arches by geometry, not by rounding.** The count rolled 3 on
  the town column; the avenue is authored at a 30 px stride ending at y928 because the naive 44 px
  extension dropped the third arch inside the theater court, and the stage faces the monastery, so
  its viewing ground sits on the sando axis. The arches stop where the audience ground begins.
- **The Imperial Road's caption is hinted to the NE approach**, past the last of the shopfronts. A
  caption lying along a road needs roadside that is actually bare, and the default anchor is the
  road's midpoint - here lined two rows deep on both flanks. Naming a road where the road is clear is
  the cartographer's answer, not a bigger adrift cap. The anchor is a HINT (which flank, where along
  the road), never a distance.

## Review log

- **2026-08-02 settlement-review.** The magistrate's hand caption seat was retired: angled captions
  now tilt the caption -30 with the compound, where a swung corner cannot reach text that swings
  with it. The hand seat, when kept, collided with the punishment ground's equally-tilted caption.
- **2026-07-27 GM audit.** The segregation collar started as a thin strip on the south side only; a
  bundle packed there stood hard against the quarter's door row, and the farm ring then closed in on
  the other three sides instead, leaving eight farmhouses inside the seam and one 5 ft from a hut.
  The check could not see it while it measured CENTER to center at 40 ft - less than the two houses'
  own half-diagonals.
- **2026-08-08 RNG re-roll** (positional/scoped randomness, engine-wide). This map took five fixes,
  and one of them was initially the wrong shape:
  - The re-roll walked a communal well 114 px west into the MIDDLE of the windbreak belt. Since the
    clump filter clears a halo around every structure, the belt drew as two lobes with a bare notch
    and a wellhead in it - 49 clumps where it had 67. **Growing the polygon 9% to restore the ratio
    was tried first and is the wrong fix**: it widens the outline while the middle stays eaten, i.e.
    it buys the metric rather than the form. The belt is **reserved ground** now, registered before
    the rings and both well passes, which keeps wells and ring farmsteads off it and restored the
    canopy to 89 clumps - denser than it ever was. The gen's older note about "a reflowed well [that]
    sat under the canopy" referred to the belt's bottom EDGE; the reservation now covers all of it.
  - A ring farmstead's threshing yard lapped the -35 deg shopfront at (670,764) - the bundle solve
    reserves the yard but measures a neighbor's UNROTATED dims. A thin band between them fixed it; an
    80x72 pocket was tried first and simply displaced the homestead into a worse collision.
  - A farm wellhead sank into a paddy at (217,546); that plot is reserved.
  - A burakumin house seated at (1755,406), close enough to the caste above it to read as mixed.
    Cropping the pack and shifting it south were both tried first and each cost the quarter its
    budgets.md count band - **the NW corner is the only part that was ever wrong**, so only the
    corner is reserved.

## Settled by the GM - do not re-raise

- **The servant/laborer quarter's lone footpath.** The 2026-08-08 review flagged it: a 420 ft
  perfectly horizontal bar floating in open ground, terminating at nothing at either end, in a
  district whose road and grain are both diagonal, and with only 12 dwellings fronting it after the
  re-pack. **The GM ruled it fine as drawn** (2026-08-08). It stays.
- **The single monastery** is the declared exception in the decisions table, not a shortfall.
