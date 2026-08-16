# check_village/ - the Mode B gate as a package

Split from the 37k-line `check_village.py` monolith by feature 024 (constitution Principle X
clause 13: files stay at human scale - the cost being managed is context-window tokens). **Load
only the file the task calls for**; this index is the map. `import check_village` still exposes
the consumed legacy surface via `__init__.py` (star-import re-exports since feature 027), and the CLI is now `python3 -m check_village
<manifest.json> [--capacity [--capacity-map]]`.

Two invariants the split does NOT touch:

- **Registry order IS execution order** (feature 022) - and since feature 109 the registry is
  DERIVED, not maintained (constitution clause 14). `registry.py` still exports the one ordered
  `GATE_SEGMENTS` tuple, but every row is computed from the `segments_*` files at import: `free`
  from the keyword-only signature, `writes` from the literal `_kept` return tuple, the rest by
  AST analysis (`registry_analysis.py`), and order from the numeric key in each segment's name
  plus the small `_PLACEMENTS` decision table. The pre-collapse rows are frozen in
  `test_fixtures/registry_legacy_rows.json` and `test_registry_derive.py` holds the guards.
- **Run one check by itself** with `gate(M, only={"check_name"})` (driver.py); don't go hunting
  for the segment function by hand.

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the package docstring or the re-export mechanism - star imports carry every submodule's public names, an aliased block carries the six consumed underscore names (feature 027; guard: `test_check_village_surface.py`); never add logic here |
| `__main__.py` | the CLI behavior (`python3 -m check_village`, `--capacity`) needs changing |
| `common_01_geometry.py` | core types (`Manifest`, `Pt`, `Poly`, `Check`), `load`, `rect_corners`, hulls/gaps, the overlap + label TAXONOMY tables (`_OVERLAP_*`, `_LABEL_*`, `OVERLAP_CLASS`, `_MATRIX_*` policy), size constants (`GATE_FT_*`, `WALL_FT_*`, ...) |
| `common_02_overlap_policy.py` | the overlap-matrix ENGINE (`matrix_violations`, `matrix_extents`), `GridIndex` (the spatial index), ring-road/theater/fire-feature helpers, torii/footbridge/dojo constants |
| `common_03_capacity.py` | street/lane/ward helpers (`empty_street_runs`, `lane_near_misses`), crop-frame helpers, `DEFAULT_MANIFEST`, dwelling/business kind tables, `city_capacity` (the walled-city capacity model), waiver constants, and the gate-scope plumbing (`_UnboundType`, `_UNBOUND`, `_kept`) |
| `segments_01_city_frame_and_yards.py` | segs 0000-0096: city ring/farmland frame, quarters, commoner dwellings, farrier/stable/charcoal work yards |
| `segments_02_capital_and_walls.py` | segs 0097-0133_030: capital battery (budget, ministries, aqueduct, lineages, avenue), wall/gate/burial sizing |
| `segments_03_structures_and_wards.py` | segs 0133_031-0267: structure overlaps, buildings-face-street, alleys, headman rules, ward interiors, labels/titles |
| `segments_04_homesteads.py` | segs 0268-0285_091: wells vs shrine/torii, gardens (area/quads/sun/clearances), groves, farm sheds, farmhouse variation, commons; hand-added 0598 (cluster-seeding trace) |
| `segments_05_fields_and_funerary.py` | segs 0285_092-0333: field margins/ditches, channels (anchoring, winding), cemetery/cremation/mausoleum/ossuary placement; hand-added 0597 (woodland commons within the frame) |
| `segments_06_ways_and_bridges.py` | segs 0334-0409: bridges vs ways/water, roads, capital districts/housing bands, castle moat clearances |
| `segments_07_water.py` | segs 0410-0512: watercourses, channel gates, aqueduct taps, ponds, bank/edge rules, lane runs vs water |
| `segments_08_town_and_fire.py` | segs 0513-0554: town battery (farmers plurality, storefronts, inns, theater), kosatsuba, fire towers, burakumin seam, defense marsh; hand-added 0595 (supply-bank bunds), 0600 (comb floor ends at the collector) |
| `segments_09_justice_and_tanning.py` | segs 0555_000-0562_042: punishment spots, execution grounds (road/boundary/outcast-side rules), tanning yards (water discharge, outcast side) |
| `segments_10_city_battery_a.py` | segs 0563_000-0563_125: city caste counts/shifts, dojos, wells per neighborhood, civic labels (feature 023's per-statement city battery, first third) |
| `segments_10_city_battery_b.py` | segs 0563_126-0563_251: city estates (gates, roads, moat clearances), clan/capital-direction meta, lanes |
| `segments_10_city_battery_c.py` | segs 0563_252-0563_376: city canal/dock, civic vs streets, flophouses, fields near city, moat feeders |
| `segments_11_polders_and_edges.py` | segs 0564-0594: polder dikes, dike-pond blocks, contour terraces, torii counts, common-field orientation, map-edge rules |
| `registry.py` | the derived-registry surface (feature 109): the `_PLACEMENTS` execution-position decisions, the `_NEEDS_OVERRIDES` exceptions, the source-hash row cache, and the assembly that binds derived rows to segment functions |
| `registry_analysis.py` | the AST analysis that derives `checks`/`needs`/`meta`/`always` from segment bodies (typed port of feature 022's transform; the helper-mutation fixpoint and upward-exposed-reads model live here) |
| `driver.py` | `gate()` itself (verbose output, `only=` closure semantics), the twin-detector (`twin_axes`, `twin_report`), `main()` |

## Adding a check (unchanged mechanics, new geography)

Write the `_seg_<key>__<name>`-style function in whichever `segments_*` file covers its theme
(body reads inputs as keyword params defaulting to `_UNBOUND`, returns `_kept(locals(), <literal
tuple of the names it binds>)` - the literal is REQUIRED, derivation fails loudly on a computed
tuple), extend `test_fixtures/gate_check_names.json`, and import nothing by hand - each segment
file already imports the shared helpers it uses. There is NO registry row to write (feature
109): the row derives from the function itself, and its EXECUTION POSITION comes from the
numeric key in the name - `_seg_0533_500__x` runs between 0533 and 0534. Two caveats: the
sub-number places you after the plain-numbered segment only if that segment sorts in the base
key order - to run beside a PLACED segment (one with a `_PLACEMENTS` entry, e.g. 0595-0600),
add your own `_PLACEMENTS` entry anchored on it rather than sub-numbering its label; and a
hand-decided `needs` tighter than the derived one goes in `_NEEDS_OVERRIDES` with its why.
Full doctrine: `.claude/skills/diagram/CLAUDE.md` "The gate is a REGISTRY".

## Monkeypatching a policy table

Each submodule binds shared names at import, so `monkeypatch.setattr(check_village, "_OVERLAP_STRUCTS", ...)`
no longer reaches the code that reads them. Patch every holder instead:

    for m in [m for m in sys.modules.values() if getattr(m, "__name__", "").startswith("check_village") and hasattr(m, "_OVERLAP_STRUCTS")]:
        monkeypatch.setattr(m, "_OVERLAP_STRUCTS", new_value)

(`test_checks.py::test_every_solid_feature_classified_for_labels_fires_on_an_unclassified_key` is the exemplar.)

## Why the segment files are numbered ranges

The split preserved definition order file-by-file (concatenating the files in name order
reproduces the old monolith's order), so each file is a CONTIGUOUS registry range - that is what
makes the move provably behavior-identical (feature 024's oracle sweeps). Theme names describe
the dominant content of each range; a few neighbors ride along with any theme.
