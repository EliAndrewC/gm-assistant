# Research: Budget-First City Wall Sizing

Two research streams: (A) empirical calibration measured from the shipped pool manifests (known-good Tango, known-bad Nagahara); (B) historical grounding for the circulation fraction and open-ground allowances (China first, jokamachi tiebreaker).

## A. Calibration measurements (from pool/tango.json + pool/nagahara.json)

Measured 2026-07-16 with a throwaway script (shoelace over `M["wall"]`, analytic circulation sampling clipped to the wall, `city_capacity` reruns). Key code anchors: `city_capacity` at `check_village.py:1174` (verdict logic ~:1345); `RHO_CANONICAL = 0.00127` dwellings/px^2 at `check_village.py:1141` (i.e. 787 px^2 gross per dwelling); per-quarter density at `check_village.py:1319-1340`; wall polys are ellipse N-gons built in the gen scripts (Tango `1602,1328,487,457` x22 vertices; Nagahara `1480,1330,494,460` x20).

**Important geometry fact**: Nagahara's wall is a FULL CLOSED RING beside the river (the river never enters the walls, per the China-first doctrine in `nagahara.gen.py:6-10`) - NOT an arc closed by the bank. So the wall derivation needs only the closed-ellipse form for both shipped cities; the spec's "bank_arc" shape is not needed for Nagahara and is dropped from scope (see Decision 4).

### Measured inventory and areas (in-wall)

| quantity | Tango (good) | Nagahara (bad) |
|---|---|---|
| interior (shoelace) | 689,044 px^2 | 701,884 px^2 |
| PACKED dwellings (laborer/servant/burakumin/merchant) | 509 / 62,314 px^2 (avg 122) | 519 / 65,445 (avg 126) |
| SPACED dwellings (samurai) | 33 / 9,604 (avg 291) | 41 / 12,161 (avg 297) |
| shops/inns/stables | 21 / 4,686 | 16 / 3,652 |
| civic compounds total | 31 / 59,404 | 30 / 57,055 |
| in-wall farmhouses | 19 / 2,694 (agri district) | 0 |
| circulation, drawn widths (trunk + ring road + streets + alleys) | 46,600 = **6.8% of interior** | 48,917 = 7.0% |
| water in-wall | pond 2,865 | canal 998 + dock 1,836 |
| declared reserve | 103,577 px^2 (agri district, 15.3%) | **0** |

### Gross ground costs (footprint + share of gaps/margins actually consumed)

| constant | Tango (calibration source) | Nagahara |
|---|---|---|
| packed dwelling GROSS (healthy pure-res quarters) | 448-822 px^2; ~858 over all res+mixed quarters | 666-1,044 |
| samurai GROSS (samurai-dominated quarter) | **2,915 px^2** | 1,847 |
| civic program flat total (compounds + shops) | **~64,090 px^2** | 60,707 |
| RHO_CANONICAL cross-check | 787 px^2/dwelling on res-capable ground | same constant |

### Where Nagahara's excess ground sits (the quantified defect)

- `city_capacity` calls BOTH cities `sized_and_packed` (open_frac 0.530 vs 0.576 - looks close) because Tango's slack is DECLARED (agri reserve + drawn fields are excluded from "open") while Nagahara's is not. Strip the accounting: analytic open ground (interior - buildings - circulation - water - declared reserve) = **Tango 57.7% vs Nagahara 73.2%** - about **116k px^2 of unaccounted ground** (~17% of the interior).
- The excess is CONCENTRATED: five contiguous pockets >= 35k px^2 totaling ~396k, the largest 139k px^2 (~440x512 px, in the SW samurai/governor quarter).
- One Nagahara quarter passes the density floor (0.30/1000 px^2) at **0.31** - but it is a PACKED-kind quarter (45 commoner dwellings, 0 samurai) coasting at samurai-ward sparseness. The band cannot see caste mix; the budget model can (it knows how many of each class each quarter should carry).
- Why the aggregate verdict misses it: shrink only fires at inherent_cap > 1.4xT; Nagahara reads 1.06xT because `res_capable x RHO` treats all open ground as legitimately fillable.

### Back-prediction sanity check (the model works)

Budget-first arithmetic with Tango's constants: 600 dwellings x 787 px^2 gross (~472k) + ~226k overhead (civic + circulation + reserve + water) ~= **698k px^2 required vs 689k actual interior (+1.3%)**. The same arithmetic prices Nagahara's program at ~**600k px^2 vs its 702k actual interior: the wall is ~15% oversized** for what it holds. This is exactly the defect the GM sees and the check suite misses.

### Measurement-method notes

- Circulation at DRAWN widths is 6.8-7.0% in both cities; the grid-based `city_capacity` charges the ring road a +24 px/side berm (`check_village.py:1233`) which inflates "trunk" to ~21% of ring area in both cities equally. The budget model uses the drawn-width basis (7%) plus the wall-margin strip accounted separately - do not double-count the berm.
- Out-of-wall features (manors, wharf, funerary, gate markets, out-of-wall farmhouses) are excluded from the interior budget entirely.

## B. Historical grounding (circulation fraction, open ground, civic share)

China-first (Song/Ming county seats), jokamachi as tiebreaker. Strongest source: Sen-dou Chang, "The Morphology of Walled Capitals," in Skinner, *The City in Late Imperial China* (http://web.stanford.edu/~mel1000/sen.pdf). Full memo with all citations preserved below in compact form.

- **Circulation: ~15% of BUILT-UP ground; ~10-12% of the total walled enclosure** (range 10-20%). Chinese county seats ran a deliberately sparse net: 1-2 wide gate-to-gate trunk streets in a cross/T (drum tower at the crossroads), everything else narrow lanes (Pingyao: "4 big streets, 8 small streets, 72 lanes"). Edo machi-wari block geometry (60-ken ~118 m blocks, 6-18 m streets) computes to 13-18% - the finer-grid Japanese end. Planning-literature cross-check: "medieval plan" towns 10-15% vs 25%+ for planned/modern grids (Old Urbanist street-area survey; UN-Habitat street-patterns WP).
- **Deliberate open/reserve: 25-30% of the walled area unbuilt is NORMAL for a Chinese county seat** (range 15-45%): walls were sized to administrative rank and growth expectation, not housing demand; intramural fields/gardens/ponds were siege insurance and flood refuge. Named anchors: Quanzhou still 1/4 vacant in 1945; Suzhou enclosed farmland into the Republican era; Jinan's lake = ~1/5 of the walled area; Zhengding only ~80% built-up in 2008 (Chang pp. 94-95; Chinese city wall, Wikipedia; tandfonline space-syntax study). Placement: corners and along walls away from gates, biased north (inauspicious); commerce pulls to the south gate and crossroads. A jokamachi has no equivalent (unwalled, fully allocated) - China wins per doctrine.
- **Civic share: ~10% of the walled area** (range 5-15%): yamen 3-5% in a small seat (Pingyao's yamen ~2.6 ha), Confucian temple + City God temple + exam hall + altars 3-5%, granary + drill ground 2-4%, clustered center/north-center. (Edo's 15-16% temple land is the Japanese upper bound; China leaner.)
- **Density anchors**: packed commoner wards in a SMALL city ~200-400 persons/ha net (Pingyao ~190/ha gross); Edo chonin ~600-690/ha is the metropolitan ceiling, never reached at pop 3,000. Official/elite wards ~100-150/ha. Whole-city sanity: 1910 county-capital walled areas averaged 39-175 ha by province; a pop-3,000 program = ~18-25 ha built-up, walls ~30-60 ha (built-up 55-75% of enclosure) - squarely on the small-southern-seat band.
- **Source-strength caveat (recorded per the research-rule requirement)**: no source states a circulation percentage for Chinese county seats outright; the figure is TRIANGULATED from Edo block geometry + the medieval-plan planning literature + Chang's sparse-grid models - a modeling choice with a documented basis, not a measured fact. The Pingyao yamen figure is tourism-grade but checkable against the preserved complex.

**Reconciliation with the measured maps (A vs B)**: the drawn circulation share of both shipped cities (6.8-7.0% of enclosure) sits at the sparse Chinese end of the historical band - consistent, given the maps' deep blocks and alley-warren doctrine; keep the MAP-calibrated 7% as the budget constant and cite the historical band as its plausibility envelope. The historical 25-30% open-reserve norm does NOT contradict the GM's empty-space complaint: history justifies DELIBERATE, LEGIBLE reserve (fields, gardens, ponds, drill grounds - drawn as such), which is exactly feature 006's declared-reserve concept; Nagahara's defect is ~17% UNDECLARED ambient open. The budget therefore carries reserve as an explicit itemized line (drawn as its kind, subject to the existing 20% reserve cap), and the wall is sized to program + declared reserve - never to ambient slack.

## Decisions

1. **Decision: model the budget as `interior = circulation% + civic flat + reserve lines + packed_n x C_packed + spaced_n x C_spaced (+ water lines)`.**
   Rationale: back-predicts the known-good Tango within ~1.3% and prices the known-bad Nagahara as ~15% oversized - it separates the two cities the aggregate model cannot.
   Alternatives considered: keep tuning `RHO_CANONICAL`/verdict thresholds (rejected: the aggregate is structurally blind to undeclared open ground - measured proof above); per-quarter budget targets only (rejected as the primary sizer: distribution checks already exist; the missing piece is total-area honesty before the wall exists).

2. **Decision: calibration constants (initial values, to be finalized against Section B):** `C_packed ~= 800 px^2` gross per packed dwelling (Tango healthy-quarter range 450-850, all-quarter 858; choose inside the range and validate via back-prediction test), `C_spaced ~= 2,900 px^2` gross per samurai house, civic program flat ~= 62-64k px^2 at pop 3,000 scale (itemized per compound, not one blob, so program changes reprice honestly), circulation ~= 7% of interior at drawn widths.
   Rationale: measured from the GM-approved city; each constant carries its measured basis as the "why" comment (research-rule requirement).
   Alternatives: real-world square footage converted at 3 ft/px (rejected: legibility floors make drawn footprints systematically larger - FR-011; the map must budget what it draws).

3. **Decision: tolerances for `city_wall_matches_budget` sized so Tango passes and pre-feature Nagahara fails.** Tango's back-prediction error is +1.3%; Nagahara's mismatch is ~15%. Set over-enclosure tolerance ~8% (midpoint with margin both ways), under-enclosure ~5% (tighter: an undersized wall breaks packing immediately). Final values validated by the two pinned anchors in tests.
   Alternatives: symmetric 10% (rejected: leaves less than 5% separation to the known-bad case).

4. **Decision: wall derivation ships CLOSED-RING ONLY (`shape="ring"`).** Both shipped cities are closed ellipse rings; a true bank-chord wall exists in neither. The WallSpec keeps the `shape` field so a future bank-arc city can extend it, but no numeric arc solver is built now (YAGNI; the spec's bank_arc contract moves to "future extension").
   Rationale: measured geometry (Section A note). Simplifies the module and its coverage surface.
   Alternatives: build the arc solver anyway (rejected: untestable against any real map today).

5. **Decision: reserve/agricultural-district ground must be DECLARED to be counted.** The budget only credits open ground that arrives as an itemized line (agri district, drill ground, temple forecourts); the emptiness-laundering lesson from feature 006 carries over: undeclared open is a defect, and the analytic-open measurement (Section A) is what the new check enforces via required-vs-enclosed area.

6. **Decision: `population_tol` and existing caste-floor machinery unchanged.** The budget feeds the same dwelling targets the checks already enforce (`dwelling_target` per kind); no existing check is relaxed.

7. **Decision: circulation constant = 7% of interior (map-calibrated), with the historical 10-20% band recorded as its plausibility envelope.** The drawn share of both shipped cities is 6.8-7.0%, at the sparse Chinese end (deep blocks + alley warrens per the row-packing doctrine); the historical figure is itself triangulated, not measured, so the map's own measured constant wins.
   Alternatives: adopt the historical ~10-12% of enclosure (rejected: would systematically oversize walls relative to how the maps actually draw streets - the budget must price DRAWN geometry, FR-011).

**Regen outcome (2026-07-16, recorded per T018):** Nagahara rebuilt budget-first. Wall 494x460 -> 449x418 (enclosed 702k -> 580k px^2, -17.4%); 567 in-wall dwellings (target 600, floor 558; inherent well-packed ceiling 595); per-quarter densities NE 1.43 / SE 1.70 / SW ward 0.64 / NW monzen 0.78 (all in band; the NW was 0.29 pre-grind); samurai 39 houses + 6 estates; capacity verdict `sized_and_packed` with the wall untouched (pure densify path - zero wall resizes). All 227 checks green; all 11 pool maps green; tolerances shipped as designed (+8%/-5%). Known accepted compromises (documented in the gen): merchant mix 2:1:1 (merchant caste 120 vs ~150 target, in band), the monzen back-alley removed (the shrunk west column holds ~2 dwellings - below alleys_serve_buildings' floor), the north fence band houseless (street + fence corridors overlap). GM visual sign-off on the empty-space fix: PENDING (SC-001's final acceptance).

8a. **Implementation finding (2026-07-16): `RHO_CANONICAL` recalibrated 0.00127 -> 0.00149, and `city_capacity` now deducts ALL reserve ground (agri included, minus its field cells) from residential-capable ground.** Surfaced by the first budget-first Nagahara run: the budget-derived ring (449x418 = Tango-minus-agri, consistent with the GM's density canon) read `enlarge` under the old constant. Root cause: 0.00127 was calibrated over ground that still contained Tango's ~72k px^2 of non-field agri-reserve slack (only NON-agri reserves were deducted), so the norm under-read packed urban delivery - Tango's honest urban figure is 561/377,895 = 0.00149. After recalibration: Tango `sized_and_packed` (inherent 563), budget-first Nagahara `densify` (inherent 585 - wall right, add dwellings: the correct instruction), old Nagahara fixture still non-shrink (the budget check owns that finding). The two capacity unit tests' synthetic populations were retuned to keep exercising the verdict window.

8b. **Decision: deliberate reserve is a first-class, itemized, DRAWN budget line - and the historically honest default is a modest one (~10-15% of interior), not zero.** Chinese county seats normally enclosed 25-30% unbuilt ground (siege insurance, rank-sized walls); on a diagram that reads as emptiness unless drawn as its kind, so the model supports it only as declared reserve (agri district, gardens, drill ground, pond), capped by the existing 20% reserve check. Nagahara's regen takes a SMALL reserve (or none beyond its pond) per the GM's packed-city preference; the knob and its historical why are documented in settlements.md so future cities can choose the roomier historical character deliberately.
   Alternatives: bake 25-30% reserve into every budget (rejected: the GM's explicit complaint is empty ground; historical roominess must be an opt-in, legible choice, never ambient).
