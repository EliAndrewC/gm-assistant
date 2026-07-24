# Town-scale check audit (GM-requested, 2026-07-21)

Prompted by the water/farmstead/windbreak fix rounds on Hoshizora + Hirameki: every one of
those GM catches was a rule the validator did not enforce at town scale. **STATUS 2026-07-21:
ALL HIGH + MEDIUM items below are IMPLEMENTED (GM directive), plus the windbreak-embrace
composition check via the form-aware adjacency metric** - see the check names in brackets and
settlements.md for the calibration whys. The remaining unautomated composition rule is label
restraint (review-by-eye). Inventory basis: 347 distinct checks in
`check_village.py` - ~242 ungated, ~40 city-only, ~50 town-inclusive, ~15 village/hamlet-only.

## Context: closed this session (towns now covered)

no_structure_on_paddy, roads_clear_of_marsh, pond_clear_of_paddies,
channels_join_streams_at_confluence (both ends), drain_ends_reach_water, the
dwellings_above_field_drain toe-band cap, cascade-reuse grounding, dry-hem awareness in
yards/groves/village-grove clumps, grove-vs-town-wall footprints. Towns also now run the
same nucleated homestead-bundle placement as villages, which retired the whole legacy-path
defect class (yards off-south, groves over kuras, houses lapping paddies). Later the same
day: `scrub_clear_of_urban_fabric` (town/city) + the engine's 30 ft urban-clearance halo -
scrub polys must trace the outskirts, never the built-up fabric (GM catch on Hoshizora's
"generous polys" scattering scrub through the streets and wellhead aprons; see
settlements.md's urban-clearance-halo bullet).

## HIGH priority - adapt an existing city check or close an obvious doctrine hole

1. **[DONE `walled_town_commoners_inside_walls`]** (adapted from `city_commoner_dwellings_inside_walls`; burakumin + gate-market merchants within 260px of the gate exempt).
   The jokamachi doctrine in Hirameki's own docstring - urban castes INSIDE the rampart, only
   farms/burakumin/gate-market outside - is enforced by nothing. A regenerated walled town
   could spill laborers outside and pass. Adoption cost: none expected (Hirameki conforms).
2. **[REVERTED 2026-07-24 - `walled_town_has_fire_tower`, walled-only again]** - the audit
   originally widened this to every town ("Hoshizora's packed road-front core burns just the
   same") and Hoshizora got a tower on a scanned seam. The GM questioned it and research sided
   with the original walled-only doctrine: the hinomi-yagura is the institution of a dense
   ENCLOSED contiguous core; an unwalled seat is drawn at detached village grain with field-gap
   breaks, and real unwalled administrative seats (jin'ya/daikansho towns) kept fire bells,
   stored water, and fireproof kura, not watch towers - the freestanding rural tower is
   Meiji-and-later. Hoshizora's tower removed; full grounding in settlements.md "Fire towers".
3. **[DONE `town_monasteries_have_graveyards`]** (graveyard=False opt-out; Hirameki's relic Benten monastery opted out). Both current
   towns carry parish grounds by hand; nothing requires the next one to. Adoption: none.
4. **[DONE `burakumin_quarter_segregated`]** (towns only - calibration showed city ward seams run ~10px, so cities need quarter-level treatment). The quarter is doctrine
   ("segregated") and hand-placed on every map, but no check enforces separation - a
   regenerated map could interleave burakumin dwellings with the laborer warren and pass.
   Suggested form: min gap between the burakumin cluster hull and any non-burakumin dwelling.
5. **[DONE `town_has_ossuary`]** - mounds added beside both towns' cremation grounds. A county seat cremates (town_has_
   cremation_ground exists) - its paupers' muenzuka should stand by the cremation ground as in
   cities. Adoption cost: add an ossuary mound beside both towns' cremation grounds.
6. **[DONE `geometry_within_canvas`]** (non-city scales; the city id kept for fixture continuity). Pure sanity (no feature entirely off-canvas);
   there is no reason it is city-only. Adoption: none expected.

## MEDIUM priority - real gaps, need calibration or generator work first

7. **[DONE `watercourse_ends_reach_water`]** (drains + mains; margin 18 calibrated so hikari-east's crop-edge tail is legal; Hoshizora's weir became a recorded channel via the new {kind:'ditch'} anchor). `drain_ends_reach_water` covers role=drain
   only. The same audit that motivated it found a LATENT main-canal dangle on
   hikari-no-sato's east comb (free end ~140px from any waterway). Extending to main/head
   pieces needs that map fixed first and a tolerance that keeps the approved honda/shimizu/
   kikuta main-tails (~11px past the exempt margin) legal.
8. **[DONE `canopy_clear_of_watercourses`]** + the engine's village_grove clump filter now skips watercourses itself. Nothing stops village_grove clumps from standing on
   a stream/channel (the fengshui-pond check `trees_clear_of_fengshui_ponds` covers only
   ponds). The towns' belt lobes flank the brooks by hand-shaping alone.
9. **[DONE `town_margins_clothed`]** (20% allowance; urban fabric + intramural ground count as cover; both towns clothed with role='grazing' commons bands).
   The satoyama bare-margin rule does not run at towns; Hoshizora carries sizable bare tan
   stretches that a village would fail on. Real generator work (a town `hinterland()` pass).
   The absence of a village-style toe MARSH at towns/cities is deliberate and now has recorded
   historical grounding - see settlements.md 'Towns and CITIES have NO toe marsh' (the
   drainage-investment gradient) and 'Defensive marshland' (the one sanctioned urban marsh,
   `role="defense"`, held ready for a future map).
10. **[DONE `town_samurai_housing_varied`]** (>= 1 samurai_large among a small majority; both towns place pinned larges). Towns check
    laborer + merchant variety only; town gens place a single samurai kind. Needs
    samurai_large support in the town packs first.
11. **[DONE - gates widened to towns]** (`crop_hugs_content`, `hard_features_within_frame`; latent until a town crops). Towns currently render full-canvas so the gap is latent - it bites
    the day a town uses crop_to_content.

## Composition rules that resist automation (documented, review-by-eye)

- **[DONE `village_windbreak_embraces_cluster`]** - automated after all via the form-aware adjacency metric (a substantial >= 12-clump belt within 150px of a farmhouse; real-forest maps exempt). The original distance-fraction metric remains unusable - the
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
