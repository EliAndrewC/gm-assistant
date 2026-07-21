# Town-scale check audit (GM-requested, 2026-07-21)

Prompted by the water/farmstead/windbreak fix rounds on Hoshizora + Hirameki: every one of
those GM catches was a rule the validator did not enforce at town scale. Before the next town
is generated, this is the audit of what SHOULD exist. Inventory basis: 347 distinct checks in
`check_village.py` - ~242 ungated, ~40 city-only, ~50 town-inclusive, ~15 village/hamlet-only.

## Context: closed this session (towns now covered)

no_structure_on_paddy, roads_clear_of_marsh, pond_clear_of_paddies,
channels_join_streams_at_confluence (both ends), drain_ends_reach_water, the
dwellings_above_field_drain toe-band cap, cascade-reuse grounding, dry-hem awareness in
yards/groves/village-grove clumps, grove-vs-town-wall footprints. Towns also now run the
same nucleated homestead-bundle placement as villages, which retired the whole legacy-path
defect class (yards off-south, groves over kuras, houses lapping paddies).

## HIGH priority - adapt an existing city check or close an obvious doctrine hole

1. **walled_town_commoner_dwellings_inside_walls** (adapt `city_commoner_dwellings_inside_walls`).
   The jokamachi doctrine in Hirameki's own docstring - urban castes INSIDE the rampart, only
   farms/burakumin/gate-market outside - is enforced by nothing. A regenerated walled town
   could spill laborers outside and pass. Adoption cost: none expected (Hirameki conforms).
2. **town_has_fire_tower for UNWALLED towns.** `walled_town_has_fire_tower` exists; Hoshizora
   (unwalled, dense road-front core) has no tower and no requirement. Either extend the check
   to all towns or record why unwalled county seats are exempt. Adoption cost: add a tower to
   Hoshizora on a scanned-clear seam.
3. **town_monasteries_have_graveyards** (adapt `city_temples_have_graveyards`). Both current
   towns carry parish grounds by hand; nothing requires the next one to. Adoption: none.
4. **burakumin_quarter_segregated** (new; towns AND cities). The quarter is doctrine
   ("segregated") and hand-placed on every map, but no check enforces separation - a
   regenerated map could interleave burakumin dwellings with the laborer warren and pass.
   Suggested form: min gap between the burakumin cluster hull and any non-burakumin dwelling.
5. **town_has_ossuary** (adapt `city_has_ossuary`). A county seat cremates (town_has_
   cremation_ground exists) - its paupers' muenzuka should stand by the cremation ground as in
   cities. Adoption cost: add an ossuary mound beside both towns' cremation grounds.
6. **city_geometry_within_canvas -> all scales.** Pure sanity (no feature entirely off-canvas);
   there is no reason it is city-only. Adoption: none expected.

## MEDIUM priority - real gaps, need calibration or generator work first

7. **watercourse free-end dangles beyond drains.** `drain_ends_reach_water` covers role=drain
   only. The same audit that motivated it found a LATENT main-canal dangle on
   hikari-no-sato's east comb (free end ~140px from any waterway). Extending to main/head
   pieces needs that map fixed first and a tolerance that keeps the approved honda/shimizu/
   kikuta main-tails (~11px past the exempt margin) legal.
8. **canopy_clear_of_watercourses** (new). Nothing stops village_grove clumps from standing on
   a stream/channel (the fengshui-pond check `trees_clear_of_fengshui_ponds` covers only
   ponds). The towns' belt lobes flank the brooks by hand-shaping alone.
9. **town margins clothed** (adapt `margins_form_continuous_ring`, village/hamlet-only).
   The satoyama bare-margin rule does not run at towns; Hoshizora carries sizable bare tan
   stretches that a village would fail on. Real generator work (a town `hinterland()` pass).
10. **town samurai housing variety** (adapt `city_samurai_housing_varied`). Towns check
    laborer + merchant variety only; town gens place a single samurai kind. Needs
    samurai_large support in the town packs first.
11. **crop/frame checks at towns** (`crop_hugs_content`, `hard_features_within_frame` are
    village/hamlet-only). Towns currently render full-canvas so the gap is latent - it bites
    the day a town uses crop_to_content.

## Composition rules that resist automation (documented, review-by-eye)

- **Windbreak embrace** ("the belt NESTLES against and embraces the cluster") - the
  windward-canopy-within-R metric was calibrated across every nucleated map and cannot
  separate approved forms from bad ones (Kikuta's approved ribbon belt scores 4-18%).
  Documented in settlements.md with the calibration numbers; automating needs a form-aware
  belt-to-cluster-hull metric (own work item).
- **Label restraint** (don't label the obvious) - existing rule-of-thumb + review pass.

## Generator-parity gaps a check cannot see (fix in the engine when next touched)

- The nucleated bundle packer tests placed URBAN buildings as axis-aligned rects; a rotated
  shopfront's swung corner is invisible to it (worked around with hand block_polys on
  Hoshizora twice). Fix: rotated-aware placed-rect test in _bundle_side_fits.
- s.channel/village_grove know nothing of stream corridors when POLYS are hand-shaped; the
  gens carry that burden. A shared "clear of watercourses" helper would remove the class.

## City machinery correctly NOT applicable to towns

Quarters/ward system (quarters_declared/tile/dense, ward gates+fences), the wall/population
budget suite (wall_matches_budget, reserve_within_cap, capacity), Six Ministries + governor's
mansion + Ministry of Rites, mausoleums, wharf/canal/dock suite, row-housing doctrine,
samurai-neighborhood requirement (a town has samurai houses by the manor instead), the
city-scale funerary counts. Towns substitute: caste bands, farmers-plurality, magistrate
manor, monastery count/dedications, theater, flophouse, caravan inn, granary, storehouses.
