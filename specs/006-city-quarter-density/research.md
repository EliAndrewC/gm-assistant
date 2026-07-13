# Research: City Quarter Density and Wall-Sizing Correctness

## A. Empirical calibration: why per-quarter, not per-block or per-aggregate

Measured local dwelling density block-by-block (140px blocks, in-wall only) on the good city (Tango) and the broken city (current Nagahara):

| City | in-wall dwellings | interior blocks | empty (0) | near-empty (<=1) | median dwellings/block | median density /10k px^2 |
|------|------------------|-----------------|-----------|------------------|------------------------|--------------------------|
| Tango (good) | 521 | 34 | 4 | 8 | 9 | 4.6 |
| Nagahara (broken) | 525 | 35 | 8 | 8 | 9 | 4.6 |

**Decision: measure density per DECLARED QUARTER with a dead-zone guard, not per anonymous block and not per city-wide aggregate.**

**Rationale**:
- The two cities are nearly identical on every *aggregate and per-block central* statistic: same in-wall dwelling count (521 vs 525), same median block density (4.6/10k). A global-aggregate check (the old model) and an anonymous-grid median check are both blind to the difference. This is a direct, measured demonstration of why the previous approach passed the broken map.
- The ONE discriminator is the count of *empty* blocks: Nagahara has double (8 vs 4). But a naive "flag empty blocks" check would also flag Tango's 4 empty blocks (its agricultural district + civic precincts). So an empty block is only a defect if it sits in a region that is supposed to be residential.
- Therefore the check must know each region's *intent*: an empty block in a declared civic/reserve quarter is fine; an empty block (or empty sub-region) in a declared residential quarter is the defect. This is exactly the declared-quarter model, and it is why the anonymous-grid alternative was rejected.
- Block density is noisy within a single real quarter (a quarter mixes dense rows, courts, wells, a fire tower), so the density BAND is judged on the quarter AVERAGE, and the "half-dense/half-empty quarter" failure mode (which an average hides) is caught separately by a DEAD_ZONE guard: no contiguous empty sub-region larger than a fire-break inside a residential quarter.

**Alternatives considered**:
- *Tighten the global open-fraction threshold*: rejected - open_frac is 0.585 (Nagahara) vs 0.51 (Tango), too close to separate, because "open" conflates empty blocks with normal packing interstitial gaps; and it is a global scalar, the exact trap.
- *Anonymous grid density floor*: rejected - same block medians (above); cannot tell a civic/reserve empty block from a residential one without declared intent, so it either false-flags Tango's legitimate open ground or misses Nagahara's.

## B. The extramural leak (measured)

Nagahara places 35 commoner dwellings OUTSIDE the walls (29 NE, 6 SE): 17 laborer_large, 11 laborer, 3 merchant_house, 3 merchant, 1 servant. The population check counts them, so 525 in-wall + 35 out = 560 ~ target 600. Counted in-wall-only, 525 < the 558 floor -> it would read `densify`. Tango also leaks 23 outside (a latent instance of the same bug), confirming this is a systemic count defect, not a Nagahara quirk.

**Decision (GM-confirmed, FR-002)**: hard zero commoner dwellings outside the wall; population counts in-wall only. Exempt (legitimately extramural): samurai country estates, farmhouses, wharf suburb, gate-market shops.

## C. Historical grounding (China-first, Japan cross-check)

### C1. Reserve cap ~20% (RESERVE_CAP_FRAC)

**Finding**: A walled Chinese county/prefectural seat's *civic buildings* alone are small - the yamen is ~1% of the interior (Pingyao's yamen 131x203m ~= 26,600 m^2 vs ~2.25 km^2 walled), and the summed mandated roster (yamen, Confucian temple/school, City God temple, altars, granaries, drum/bell tower) runs only ~3-6%. The big open consumers are the **drill/parade ground (jiaochang, the single largest open feature)** plus a deliberately under-built remainder of gardens, ponds, and even in-wall farmland (walls were drawn wide "to ensure excess capacity for growth" - Quanzhou ~1/4 vacant into 1945; Suzhou/Nanjing enclosed farmland, lakes, forest).

**Decision**: `RESERVE_CAP_FRAC ~= 0.20`, scoped as **civic (~5%) + drill ground + garden/agricultural reserve** (not civic buildings alone). At that framing 20% is historically central-to-conservative: real Chinese seats often left far more under-built. It would be too low only for a sleepy over-walled seat (25-50% open) and too high only for a space-starved boom town that had already spilled into suburbs. A prosperous 3,000-inhabitant governor's seat sits right in the ~15-20% reserve band. Japan agrees on magnitude (jokamachi book their non-housing share as castle grounds + a ~10-15% tera-machi temple district); we follow China's flavor (drill ground + gardens/agri) for the reserve *kinds*.

### C2. Per-quarter density band ~5x spread (QUARTER_DENSITY_FLOOR/CEIL)

**Finding**: The commoner-vs-elite density inversion is the same in both traditions - the elite hold a large share of *land* but a modest share of *population*. Edo: commoners ~50% of population on ~20% of land vs samurai ~50% on ~70% -> areal density ratio ~3.5x; provincial castle towns (samurai holding 60-70% of land) reach ~4-6x. Per-lot the contrast is sharper (machiya lot ~80-120 m^2 vs samurai compounds 300 m^2 to thousands), but ward-effective density is lower because samurai compounds house servants. China matches structurally (walled courtyard siheyuan + gardens vs gap-free row/shop frontage).

**Decision**: the per-residential-quarter band must pass BOTH a packed commoner warren AND a ~1/5-as-dense samurai/official ward while failing a near-empty quarter -> a band roughly **5-6x wide** (commoner ceiling ~= 5-6x samurai floor). Narrower than ~4x risks failing legitimate samurai wards; wider than ~8x lets a genuinely empty quarter through. China and Japan agree; ~5x is safe. Calibrate the absolute floor/ceil on Tango's actual quarter densities (empirical, section A), keeping the ratio near 5x.

### C3. Extramural exemptions (the four legitimate categories)

**Finding**: The ordinary working population (laborers, artisans, most shopkeepers) lived INSIDE the wall - protecting them was the wall's purpose. Extramural residence was categorical, not general: (1) **guan-xiang approach-road suburbs** (gate-tethered inns/wholesalers/markets that overflow when the interior is full - maps to gate-market shops), (2) **wharf/riverside quarters** (docks/warehouses the wall rarely embraced), (3) **farming villages** (the agricultural population, by their fields), (4) **elite country estates/villas** (gentry leisure/rent retreats). Each is functionally bound to something outside (highway, water, fields, leisure).

**Decision**: flag ANY commoner dwelling outside the wall (hard zero, FR-002); exempt exactly samurai country estates, farmhouses, the wharf suburb, and gate-market shops. A lone artisan/laborer house outside, with no gate-suburb/wharf/farm anchor, is the true anomaly - it defeats the wall's protective purpose. China gives the cleanest justification for the exemptions; Japan supplies the "commoners live in assigned inner wards" baseline.

### C4. Civic precinct open tolerance ~70% (CIVIC_OPEN_TOL)

**Finding**: A yamen or temple compound is DEFINED by its axial courtyard sequence - a few widely-spaced ceremonial halls threaded through paved forecourts, a spirit-path, and a rear garden, behind an enclosing wall. Roofed footprint is a minority: ~25-45% built, ~55-75% open (but *structured* open - walled, gated, axial). Pingyao's yamen is offices + trial hall + prison + open courtyards.

**Decision**: `CIVIC_OPEN_TOL ~= 0.70` - a civic quarter may be majority open and still legitimate. The failure signature is openness WITHOUT structure. Mechanically our civic quarters always contain their compounds (ministries, walled temples, the governor's yamen), so the check pairs the open-share ceiling (~70%) with a floor on civic-building presence: a "civic" quarter that is >70% open AND holds little civic building area reads as merely-empty and is flagged. Japan agrees (temple/yashiki compounds equally courtyard-and-garden dominated).

### China vs Japan (recorded departures)
- China books its big non-housing reserve as drill ground + under-built farmland/gardens; Japan as castle grounds + tera-machi. **Follow China** for reserve kinds.
- China treats extramural commercial suburbs as fully normal; Japan zones commoners into assigned inner wards. **Follow China** for the extramural exemptions, Japan for the "commoners live inside" baseline.
- Density spread and civic-precinct openness: the two agree; either supports the numbers above.

**Sources**: Chinese city wall and Ancient Chinese urban planning (Wikipedia); Pingyao county yamen (Easy Tour China); G. William Skinner (ed.), *The City in Late Imperial China* (Stanford, 1977); Jokamachi and Edo land-use (Wikipedia; UW *Edo*); machiya lot dimensions (Kyoto machiya sources); Confucian temple spatial-layout study (*J. Asian Architecture and Building Engineering*, 2022).

## D. Verdict reframing

**Decision**: compute capacity against usable residential ground `R = interior - civic - reserve`, and map the four outcomes to distinct actions: `enlarge` (R too small even packed), `shrink` (R far exceeds need, or the wall is only fillable via over-cap reserve), `densify` (R right, in-wall placement below the `pop_tol` floor), `sized_and_packed` (correct). The `densify` boundary is pinned to `pop_tol` so the capacity verdict and `population_consistent_with_housing` never disagree on the same map.

**Rationale**: Nagahara's real problem is that its wall encloses more ground than its residential program fills; judged against raw interior the old model called that "about right," judged against usable residential ground it reads `shrink` (or `densify` after the empty ground is either filled or given a declared, capped purpose). The reserve cap + civic accounting mean emptiness cannot be laundered: every square of civic/reserve reduces R, so hiding empty ground as "reserve" pushes toward `shrink`, and exceeding the cap is flagged outright.
