# Vegetation and terrain: the research behind the windbreak, commons and forest rules

*The research behind the rules in [`../settlements/vegetation.md`](../settlements/vegetation.md). Findings, anchors and disclosed departures live here so the rule file stays operational; this file is where citations and deeper historical context get added as they accumulate.*

**Load this file when:** you are changing a vegetation rule, a grove size, a tree density or a check threshold - or you want the historical basis before overriding one.

Every entry: what the research found, the decision it drove, and any deliberate departure from literal reality. Anchors are stable - rules link to them by `#slug`.

---

## The fengshui forest - real scale, and why ours is honest

**Grounds:** `village_windbreak_scales_with_cluster`

**Evidence:** attested

**Sources:** [`forests-2020`](SOURCES.md#forests-2020)

- *Scale - the real numbers (research grounding, for calibrating the glyph).* Field surveys of southern-China village fengshui forests: **~2 groves per village** on average; **stem density ~3,400 woody stems/ha**, basal area ~49 m²/ha (genuine closed-canopy forest, not scattered trees); patch AREA is highly variable (famous lineage-village groves exceed 20 ha, e.g. Lingtou, 800 years old), but a TYPICAL village grove is a small forest patch, **~1-2 ha for the back grove** (modest villages <1 ha, big clan villages much larger) and **~0.1-0.5 ha for the water-mouth cluster**. So a ~1-2 ha back belt is *thousands* of woody stems in total, of which roughly **100-300 are mature canopy trees** over a dense bamboo/shrub understory; the water-mouth is **a few dozen big old trees**. Per "relative sizes roughly honest": the back belt reads as a real small FOREST (clearly the largest vegetation feature, a wall of dozens-to-hundreds of crowns - `village_grove` fills its polygon with overlapping dense clumps so a big belt does not read as a handful of lone trees), the water-mouth as a distinct smaller cluster, plus the bamboo/fruit scatter through the village. Hoshigaoka draws a ~1-2 ha embracing windward belt + a ~0.3 ha water-mouth + the leafy scatter.

- *Why the sizing is honest at this scale.* At 1 px = 2 ft a ~1-2 ha grove is ~27,000-54,000 px² - genuinely large relative to the ~11 ha built cluster (~10-18%), so the belt reads as the dominant feature without being cartoonishly oversized. Sources: Fengshui woodland (Wikipedia); Chen & Coggins et al., "Fengshui forests and village landscapes in China" (57-village survey); Hu et al., "Values of village fengshui forest patches" (Pearl River Delta, 32 patches, the density/basal-area figures); "Village Fengshui Forests as Cultural and Ecological Heritage" (Forests 2020).

## Forest density and crown size

**Grounds:** `settlement._tree_stand`, `structures_clear_of_trees`

**Evidence:** reconstruction

**Sources:** not recorded - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- *Density and crown size - the numbers and the why.* A closed premodern hill wood (the mixed broadleaf/conifer cover of a settled valley's back slope, cut over for fuel and timber on a rotation) carries roughly **500-800 canopy stems per hectare**. 1 ha = 107,639 sq ft, so ~600 stems/ha is one canopy tree per ~180 sq ft: a mean spacing near **13 ft** (`CANOPY_SPACING_FT`). Canopy crowns in such a stand run **~5-8 m across** (16-26 ft) with occasional wider emergents, so `CANOPY_R_FT = 8.5` is the mean radius, jittered 0.75-1.4x. Crowns of ~17 ft mean diameter on 13 ft centers OVERLAP, and that is the point - **closure is what makes a wood a wood**, so the packed look is honest rather than decorative. Same finding as the mulberry rows (`_mulberry_rows`): at a to-scale grain, drawing real planted density honestly IS a dense mass of crowns, not sparse symbols spaced for the eye. Nothing is inflated for legibility - at 1 ft/px a crown is r ~6-12 px and it shrinks with the map at coarser grains, exactly like the buildings.


## The crop margin - scrub stands 6 ft off every field edge

**Evidence:** reconstruction (web research 2026-08-15; searched paddy-levee structure/width and traditional field-margin management)

**Sources:** not recorded per-claim - the finding is in the prose below; add a key to `SOURCES.md` when it is re-consulted

- *What was found.* A paddy levee (*keihan*/*aze*; Chinese *tian'geng*) is a narrow earthen ridge - roughly 1-2 ft wide and under a foot tall, up to ~3 ft where it doubles as a footpath (*azemichi*). Levee structure studies (e.g. the Lake Biwa paddy-levee flora work) describe a flat trodden part plus a grassed face, and the levee grass was CUT several times a season - fodder, thatch, green manure - as was the strip immediately beside any crop. Constant cutting is why woody scrub could not establish within about a scythe's swath (~1-2 m) of a field edge; the same ~1 m clean strip separating crop from boundary vegetation shows up as standing practice in traditional field-margin management. The 6 m+ "conservation headlands" of modern European agri-environment schemes are a MODERN wildlife intervention, not the historical norm, and East Asian land hunger kept margins at the narrow end of the range.
- *The decision it drove.* `settlement/homestead_parts.py` `_CROP_MARGIN_FT = 6.0` - bund plus one cut swath (~1.8 m total). The `commons` scatter (all roles) skips every paddy and dry plot padded by this margin, converted at the map's `ftpx`; tall glyphs (scraggly pines ~14*bs px tip reach, woodland crowns ~11.5*bs px radius) additionally stand their own drawn reach back so no ink leans over a crop.
- *Disclosed departures.* (1) Grass-tuft blade TIPS may lean up to a few real feet past the margin line at coarse tiers (blades are 2.4-4.2*bs px and get no lean pad) - accepted deliberately: grass overhanging a bund is real, and the overhang is sub-pixel-to-invisible at render (settlement-review, 2026-08-16). (2) The reed `marsh` gets NO margin at all - wet ground genuinely starts at the polder dike, so reeds abutting a field's low bund is honest.

## Scrub stays off open water - including the comb laterals' drawn width

**Grounds:** `settlement._watercourse_segs`, `test_commons_keeps_scrub_off_drawn_channels`

**Evidence:** defect fix (GM 2026-08-16, Inashiro), not new research

- The scatter's water skip ("vegetation never draws OVER open water") read `M['streams']` + `M['channels']` only - and on a comb-built map `M['channels']` holds the hairline TOPOLOGY connectors (w 2.5) while the drawn supply laterals live in `M['drawn_channels']`, up to ~14 ft wide on their own filleted post-clip polylines. Result: 27 grass tufts standing on Inashiro's head-race, plus tufts crowding its banks inside the drawn stroke. `_watercourse_segs` now feeds the skip every drawn course at its drawn (piece-tapered) width; base points keep the same 2 px pad as before, and the scatters query it through a pre-boxed grid (the grid prunes, it never decides).
- *Deliberately NOT decided here* (as of this fix): a maintained-bank margin - tufts standing right up to the water's edge remained legal. DECIDED the same day, when the GM saw them: see "The cut bank" below. *(Worked example for the open-decision-sketch convention, diagram CLAUDE.md: this entry should also have carried the three lines the deciding session had to re-derive - land it at the commons scatter's `wat_b` grid in `settlement/land.py`; hold it by extending the drawn-channels margin test in `tests/settlement/test_homestead_parts.py`; exclude streams + marsh, whose natural banks keep vegetation to the water's edge.)*

## The cut bank - scrub stands 6 ft off every irrigation channel's drawn edge

**Grounds:** `settlement/homestead_parts.py` `_BANK_MARGIN_FT`, `test_commons_keeps_scrub_a_cut_bank_off_the_channels_but_not_the_streams`

**Evidence:** GM decision (2026-08-16, Inashiro second pass), extending the crop-margin reconstruction above; no new sources consulted

- *What prompted it.* After the drawn-width fix (previous section), tufts still seeded the 10-16 ft berm strips between the supply channels and the dry hem plots: the drawn-width skip (2 px pad) and the 6 ft crop margin each guarded their own edge and left a legal sliver mid-strip. The GM read the strips as scrub crowding the channels and resolved the open decision: the bank takes a margin too.
- *The decision.* The `commons` scatter (all roles) stands its base points `_BANK_MARGIN_FT = 6.0` real feet off the drawn water edge of every IRRIGATION course - `M['channels']` and `M['drawn_channels']` at their drawn (piece-tapered) widths, converted at the map's `ftpx`. The reasoning is the crop margin's, applied to the bank: a supply channel's bank is maintained ground - walked for sluice operation and bund upkeep, its grass scythed for fodder on the same rotation as the field margins - so woody scrub never establishes within a swath of the water. 6 ft = one scythe swath, the same figure as `_CROP_MARGIN_FT`. Between them the crop margin and the bank margin close any berm strip up to ~12 ft of bare ground, which covers every hem berm the comb builds (Inashiro's run 3-9 ft).
- *Deliberate exclusions.* (1) STREAMS take no margin - a natural brook bank is vegetated to the water's edge, and the 2026-08-16 settlement-review pass explicitly praised the ABSENCE of a sterile halo on the banks; only the engineered courses are maintained ground. (2) The reed `marsh` keeps its no-margin rule from the crop-margin entry - reeds ARE the water fringe. (3) Grass-tuft blade TIPS keep their few-feet lean allowance, exactly as at crop edges.
