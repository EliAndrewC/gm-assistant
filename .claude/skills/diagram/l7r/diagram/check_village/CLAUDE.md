# check_village/ - the Mode B gate as a package

Split from the 37k-line `check_village.py` monolith by feature 024, and cut again to 38 segment files by feature 122 (constitution Principle X
clause 13: files stay at human scale - the cost being managed is context-window tokens). **Load
only the file the task calls for**; this index is the map. `import check_village` still exposes
the consumed legacy surface via `__init__.py` (star-import re-exports since feature 027), and the CLI is now `python3 -m l7r.diagram.check_village
<manifest.json> [--capacity [--capacity-map]]`.

Two invariants the split does NOT touch:

- **Registry order IS execution order** (feature 022) - and since feature 109 the registry is
  DERIVED, not maintained (constitution clause 14). `registry.py` still exports the one ordered
  `GATE_SEGMENTS` tuple, but every row is computed from the `segments_*` files at import: `free`
  from the keyword-only signature, `writes` from the literal `_kept` return tuple, the rest by
  AST analysis (`registry_analysis.py`), and order from the numeric key in each segment's name
  plus the small `_PLACEMENTS` decision table. The pre-collapse rows are frozen in
  `tests/fixtures/registry_legacy_rows.json` and `tests/check_village/test_registry_derive.py` holds the guards.
- **Run one check by itself** with `gate(M, only={"check_name"})` (driver.py); don't go hunting
  for the segment function by hand.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the package docstring or the re-export mechanism - star imports carry every submodule's public names, an aliased block carries the six consumed underscore names (feature 027; guard: `tests/check_village/test_surface.py`); never add logic here |
| `__main__.py` | the CLI behavior (`python3 -m l7r.diagram.check_village`, `--capacity`) needs changing |
| `common_01_geometry.py` | core types (`Manifest`, `Pt`, `Poly`, `Check`), `load`, `rect_corners`, hulls/gaps, the overlap + label TAXONOMY tables (`_OVERLAP_*`, `_LABEL_*`, `OVERLAP_CLASS`, `_MATRIX_*` policy), size constants (`GATE_FT_*`, `WALL_FT_*`, ...) |
| `common_02_overlap_policy.py` | the overlap-matrix ENGINE (`matrix_violations`, `matrix_extents`), `GridIndex` (the spatial index), ring-road/theater/fire-feature helpers, torii/footbridge/dojo constants |
| `common_03_capacity.py` | street/lane/ward helpers (`empty_street_runs`, `lane_near_misses`), crop-frame helpers, `DEFAULT_MANIFEST`, dwelling/business kind tables, `city_capacity` (the walled-city capacity model), waiver constants, and the gate-scope plumbing (`_UnboundType`, `_UNBOUND`, `_kept`) |
| `segments_01a_city_ring_and_frame.py` | segs 0000-0037: the city ring and farmland frame, the crop frame, captions that hold it open, hard features within the frame |
| `segments_01b_quarters_and_civic_reserve.py` | segs 0038-0051: quarters and interior cells, open-civic ground, the city reserve cap |
| `segments_01c_work_yards_and_matrix.py` | segs 0052-0096: the overlap-matrix classification contract, farrier/stable/charcoal work yards, kilns, dung heaps vs hitching rails |
| `segments_02a_capital_budget_and_ministries.py` | segs 0097-0106_026: capital battery - budget, six ministries, domain school, the avenue, lineages |
| `segments_02b_capital_ways_and_burial.py` | segs 0106_027-0123: capital labels and gates, door clearances, cremation and burial-ground sizing, dry plots to scale |
| `segments_02c_walls_gates_and_housing.py` | segs 0124-0133_030: wall and gate sizing, poor-housing interiors, gate spurs |
| `segments_03a_overlaps_and_ward_fences.py` | segs 0133_031-0196: alleys, the overlap classification contract, torii, road layering, ward fences joining the wall |
| `segments_03b_structures_vs_water_and_streets.py` | segs 0197-0231: structures vs stream/canal/moat/street, businesses fronting streets |
| `segments_03c_clusters_and_labels.py` | segs 0232-0267: cluster edges, canopies, labels, subtitles and titles |
| `segments_04a_margins_lanes_and_wells.py` | segs 0268-0285_005: field margins as a continuous ring, label clearances, lanes, wells vs shrine/torii |
| `segments_04b_yards_gardens_and_sheds.py` | segs 0285_006-0285_065: wells, harvest yards, farm sheds, dooryard gardens, grove areas |
| `segments_04c_groves_and_shading.py` | segs 0285_066-0598: groves and shading (yards, gardens, village groves), windbreaks, commons; hand-added 0598 (cluster-seeding trace) |
| `segments_05a_field_cover_and_cremation.py` | segs 0285_092-0286_024: barren and woodland cover, farmhouse size variation, ossuaries, bogs, external cremation grounds |
| `segments_05b_graveyards_and_channel_sources.py` | segs 0286_025-0305: cemeteries in precincts, town graveyards and cremation, label rendering, ponds, channel-source anchoring |
| `segments_05c_streams_and_field_ditches.py` | segs 0306-0324: streams and their sources, acute turns, dry-plot furrows, funerary clearances, field-ditch termination |
| `segments_05d_supply_roadways_and_commons.py` | segs 0324_500-0602: comb supply flanks, roadways, fields clear of the road, woodland commons; hand-added 0597 (woodland commons within the frame) |
| `segments_06a_bridges_and_gate_roads.py` | segs 0334-0359: bridges and crossings, wall gaps, the capital rank gradient, precinct reservations, gate roads |
| `segments_06b_bridge_labels_and_reach.py` | segs 0360-0386: bridge scale and labels, captions clear of the defenses, funerary reach, roads joining the network |
| `segments_06c_decks_yards_and_moat_clearances.py` | segs 0387-0409: decked crossings, animal yards, well clustering, castle-moat clearances |
| `segments_07a_channels_and_bridge_spans.py` | segs 0410-0438_010: watercourses, bridge spans, dry mouths and drains, scrub clear of the urban fabric |
| `segments_07b_ponds_hems_and_land_fall.py` | segs 0438_011-0464: lanes and ponds, hems, canopies, fields clear of the wall, the declared land fall |
| `segments_07c_moats_drains_and_edges.py` | segs 0465-0512: moat junctions, in-wall drains, map-edge rules, halls on lanes, pond feeds |
| `segments_08a_ponds_marshes_and_drainage.py` | segs 0513-0523_018: ponds connected to their field, defense marshes, drainage discharge, bunds |
| `segments_08b_flow_bands_and_the_burakumin_seam.py` | segs 0523_019-0543_010: flow direction and bands, abandoned ground, banks, the burakumin seam |
| `segments_08c_town_trades_and_theater.py` | segs 0543_011-0543_057: town battery - farmers plurality, storefronts, inns, caravans, theater, monasteries |
| `segments_08d_kosatsuba_and_paddy_basins.py` | segs 0544-0607: manor gates, kosatsuba, punishment spots, paddy plot seams and basins; hand-added 0595 (supply-bank bunds), 0600 (comb floor ends at the collector), 0607 (basins worth their bund - the paddy size floor; 0606 went to a peer's `farmhouses_shed_separately` the same day, so this one moved up) |
| `segments_09a_justice_grounds_and_land_fall.py` | segs 0555_000-0561: punishment spots, execution grounds (road/boundary/outcast-side rules), the land-fall and water-flow declarations |
| `segments_09b_tanning_yards.py` | segs 0562_000-0562_042: tanning yards - water discharge, intakes, the outcast side, squareness to the water |
| `segments_10a_city_castes_and_dojos.py` | segs 0563_000-0563_044: city caste counts and shifts, samurai housing, dojos, outside farmland |
| `segments_10b_city_civic_and_commerce.py` | segs 0563_045-0563_077: merchant storehouses, theater, civic labels, government-office standoffs, lanes |
| `segments_10c_city_gates_and_wall_towers.py` | segs 0563_078-0563_125: shortfalls, gates, inspection stations, wall towers |
| `segments_10d_city_temples_and_estates.py` | segs 0563_126-0563_194: city temples and their dedications, estates and their gates |
| `segments_10e_city_governor_and_quarters.py` | segs 0563_195-0563_251: the governor's mansion, gated samurai quarters, loose servants, streets, ponds vs the wall |
| `segments_10f_city_labels_and_works.py` | segs 0563_252-0563_308: labels placed with their subject, moat irrigation, the oil press, flophouses |
| `segments_10g_city_streets_and_docks.py` | segs 0563_309-0563_333: estates shown, empty streets, in-wall farms, moat feeders, docks, jetties, log booms |
| `segments_10h_city_torii_and_estate_grounds.py` | segs 0563_334-0563_376: torii over streets, estate grounds and cells, no large empty space |
| `segments_11a_taxfree_terraces_and_dikeponds.py` | segs 0564-0580: tax-free plots, common-field orientation, hill shrines, paddy archetypes, contour terraces, dike-ponds |
| `segments_11b_polder_dikes_and_waivers.py` | segs 0581-0594: polder dikes and parcels, ribbon fields, the waiver meta-checks |
| `registry.py` | the derived-registry surface (feature 109): the `_PLACEMENTS` execution-position decisions, the `_NEEDS_OVERRIDES` exceptions, the source-hash row cache, and the assembly that binds derived rows to segment functions |
| `registry_analysis.py` | the AST analysis that derives `checks`/`needs`/`meta`/`always` from segment bodies (typed port of feature 022's transform; the helper-mutation fixpoint and upward-exposed-reads model live here) |
| `driver.py` | `gate()` itself (verbose output, `only=` closure semantics), the twin-detector (`twin_axes`, `twin_report`), `main()` |

## Adding a check (unchanged mechanics, new geography)

Write the `_seg_<key>__<name>`-style function in whichever `segments_*` file covers its theme
(body reads inputs as keyword params defaulting to `_UNBOUND`, returns `_kept(locals(), <literal
tuple of the names it binds>)` - the literal is REQUIRED, derivation fails loudly on a computed
tuple), extend `tests/fixtures/gate_check_names.json`, and import nothing by hand - each segment
file already imports the shared helpers it uses. There is NO registry row to write (feature
109): the row derives from the function itself, and its EXECUTION POSITION comes from the
numeric key in the name - `_seg_0533_500__x` runs between 0533 and 0534. Two caveats: the
sub-number places you after the plain-numbered segment only if that segment sorts in the base
key order - to run beside a PLACED segment (one with a `_PLACEMENTS` entry, e.g. 0595-0600),
add your own `_PLACEMENTS` entry anchored on it rather than sub-numbering its label; and a
hand-decided `needs` tighter than the derived one goes in `_NEEDS_OVERRIDES` with its why.
Full doctrine: `.claude/skills/diagram/dev/gate.md` "The gate is a REGISTRY".

## Monkeypatching a policy table

Each submodule binds shared names at import, so `monkeypatch.setattr(check_village, "_OVERLAP_STRUCTS", ...)`
no longer reaches the code that reads them. Patch every holder instead:

    for m in [m for m in sys.modules.values() if getattr(m, "__name__", "").startswith("check_village") and hasattr(m, "_OVERLAP_STRUCTS")]:
        monkeypatch.setattr(m, "_OVERLAP_STRUCTS", new_value)

(`test_every_solid_feature_classified_for_labels_fires_on_an_unclassified_key` (in `tests/check_village/`) is the exemplar.)

## Why the segment files are numbered ranges, and what the LETTER means

The split preserved definition order file-by-file (concatenating the files in name order
reproduces the old monolith's order), so each file is a CONTIGUOUS registry range - that is what
makes the move provably behavior-identical (feature 024's oracle sweeps). Theme names describe
the dominant content of each range; a few neighbors ride along with any theme.

Feature 122 cut those 13 files again, to 38, because every one of them was 1,406-2,661 lines
against a ~1,000-line bar while the MEDIAN segment is 5 lines - so reading one check cost about
2,200 lines of context. The `<number><letter>` names keep sorted-glob order equal to key order,
so the directory listing still reads in execution order. **The three `segments_10_city_battery_a/
b/c` files became one lettered run `10a..10h`**: they were always one contiguous range
(0563_000-0563_376) that feature 023 cut into three for size alone, and the letters now say so.

Nothing about the file a segment lives in is load-bearing, and has not been since feature 109:
`registry.py` finds segments by GLOBBING `segments_*.py` and orders them by the numeric key in the
FUNCTION NAME plus `_PLACEMENTS`. That is why 122 could move 24,354 lines across 13 files in one
pass and prove it: `GATE_SEGMENTS` serialized before and after is identical on all 1,377 rows.
**So a further split needs no registry work at all** - move whole functions, keep their order, add
the star-import line in `__init__.py`, and add the row here.
