# check_village/ - the Mode B gate as a package

Split from the 37k-line `check_village.py` monolith by feature 024 (constitution Principle X
clause 13: files stay at human scale - the cost being managed is context-window tokens). **Load
only the file the task calls for**; this index is the map. `import check_village` still exposes
the full legacy surface via `__init__.py`, and the CLI is now `python3 -m check_village
<manifest.json> [--capacity [--capacity-map]]`.

Two invariants the split does NOT touch:

- **Registry order IS execution order** (feature 022). `registry.py` holds the one ordered
  `GATE_SEGMENTS` tuple; segment functions live in the `segments_*` files but their ROWS - and
  therefore their execution - are ordered by the registry alone.
- **Run one check by itself** with `gate(M, only={"check_name"})` (driver.py); don't go hunting
  for the segment function by hand.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the re-export list or the package docstring; never add logic here |
| `__main__.py` | the CLI behavior (`python3 -m check_village`, `--capacity`) needs changing |
| `common_01_geometry.py` | core types (`Manifest`, `Pt`, `Poly`, `Check`), `load`, `rect_corners`, hulls/gaps, the overlap + label TAXONOMY tables (`_OVERLAP_*`, `_LABEL_*`, `OVERLAP_CLASS`, `_MATRIX_*` policy), size constants (`GATE_FT_*`, `WALL_FT_*`, ...) |
| `common_02_overlap_policy.py` | the overlap-matrix ENGINE (`matrix_violations`, `matrix_extents`), `GridIndex` (the spatial index), ring-road/theater/fire-feature helpers, torii/footbridge/dojo constants |
| `common_03_capacity.py` | street/lane/ward helpers (`empty_street_runs`, `lane_near_misses`), crop-frame helpers, `DEFAULT_MANIFEST`, dwelling/business kind tables, `city_capacity` (the walled-city capacity model), waiver constants, and the gate-scope plumbing (`_UnboundType`, `_UNBOUND`, `_kept`) |
| `segments_01_city_frame_and_yards.py` | segs 0000-0096: city ring/farmland frame, quarters, commoner dwellings, farrier/stable/charcoal work yards |
| `segments_02_capital_and_walls.py` | segs 0097-0133_030: capital battery (budget, ministries, aqueduct, lineages, avenue), wall/gate/burial sizing |
| `segments_03_structures_and_wards.py` | segs 0133_031-0267: structure overlaps, buildings-face-street, alleys, headman rules, ward interiors, labels/titles |
| `segments_04_homesteads.py` | segs 0268-0285_091: wells vs shrine/torii, gardens (area/quads/sun/clearances), groves, farm sheds, farmhouse variation, commons |
| `segments_05_fields_and_funerary.py` | segs 0285_092-0333: field margins/ditches, channels (anchoring, winding), cemetery/cremation/mausoleum/ossuary placement |
| `segments_06_ways_and_bridges.py` | segs 0334-0409: bridges vs ways/water, roads, capital districts/housing bands, castle moat clearances |
| `segments_07_water.py` | segs 0410-0512: watercourses, channel gates, aqueduct taps, ponds, bank/edge rules, lane runs vs water |
| `segments_08_town_and_fire.py` | segs 0513-0554: town battery (farmers plurality, storefronts, inns, theater), kosatsuba, fire towers, burakumin seam, defense marsh |
| `segments_09_justice_and_tanning.py` | segs 0555_000-0562_042: punishment spots, execution grounds (road/boundary/outcast-side rules), tanning yards (water discharge, outcast side) |
| `segments_10_city_battery_a.py` | segs 0563_000-0563_125: city caste counts/shifts, dojos, wells per neighborhood, civic labels (feature 023's per-statement city battery, first third) |
| `segments_10_city_battery_b.py` | segs 0563_126-0563_251: city estates (gates, roads, moat clearances), clan/capital-direction meta, lanes |
| `segments_10_city_battery_c.py` | segs 0563_252-0563_376: city canal/dock, civic vs streets, flophouses, fields near city, moat feeders |
| `segments_11_polders_and_edges.py` | segs 0564-0594: polder dikes, dike-pond blocks, contour terraces, torii counts, common-field orientation, map-edge rules |
| `registry.py` | a row's `free`/`writes`/`checks`/`needs` needs editing, or a new row needs splicing at its execution position. EXCEEDS the clause-13 file threshold deliberately: ordered DATA whose row order is the execution contract (justification header in the file) |
| `driver.py` | `gate()` itself (verbose output, `only=` closure semantics), the twin-detector (`twin_axes`, `twin_report`), `main()` |

## Adding a check (unchanged mechanics, new geography)

Write the `_seg_NNNN__<name>`-style function in whichever `segments_*` file covers its theme
(body reads inputs as keyword params defaulting to `_UNBOUND`, returns `_kept(locals(), <names it
binds>)`), add its `_GateSeg` row at the right position in `registry.py`, extend
`test_fixtures/gate_check_names.json`, and import nothing by hand - each segment file already
imports the shared helpers it uses; add an import only if your new body introduces a new helper
dependency. Full doctrine: `.claude/skills/diagram/CLAUDE.md` "The gate is a REGISTRY".

## Why the segment files are numbered ranges

The split preserved definition order file-by-file (concatenating the files in name order
reproduces the old monolith's order), so each file is a CONTIGUOUS registry range - that is what
makes the move provably behavior-identical (feature 024's oracle sweeps). Theme names describe
the dominant content of each range; a few neighbors ride along with any theme.
