# Census: consumed check_village surface (T001, 2026-08-16, clone tip)

Modules in package (star-import candidates): common_01_geometry, common_02_overlap_policy, common_03_capacity, driver, registry, segments_01_city_frame_and_yards, segments_02_capital_and_walls, segments_03_structures_and_wards, segments_04_homesteads, segments_05_fields_and_funerary, segments_06_ways_and_bridges, segments_07_water, segments_08_town_and_fire, segments_09_justice_and_tanning, segments_10_city_battery_a, segments_10_city_battery_b, segments_10_city_battery_c, segments_11_polders_and_edges

| name | provider | via | consumers (sample) |
|---|---|---|---|
| `_LABEL_EXEMPT` | `.common_01_geometry` | EXPLICIT | .claude/skills/diagram/test_checks/test_driver_and_fixtures.py |
| `_LABEL_GROUP` | `.common_01_geometry` | EXPLICIT | .claude/skills/diagram/test_checks/test_driver_and_fixtures.py; .claude/skills/diagram/test_checks/test_segments_04_homesteads.py |
| `_MATRIX_OUTSTANDING` | `.common_01_geometry` | EXPLICIT | .claude/skills/diagram/test_checks/test_segments_01_city_frame_and_yards.py |
| `_OVERLAP_EXEMPT` | `.common_01_geometry` | EXPLICIT | .claude/skills/diagram/test_checks/test_driver_and_fixtures.py |
| `_OVERLAP_STRUCTS` | `.common_01_geometry` | EXPLICIT | .claude/skills/diagram/test_checks/test_driver_and_fixtures.py; .claude/skills/diagram/test_checks/test_segments_03_structures_and_wards.py; .claude/skills/diagram/test_settlement/test_homestead_parts.py |
| `_ward_interior` | `.common_02_overlap_policy` | EXPLICIT | .claude/skills/diagram/test_checks/test_segments_10_city_battery_b.py |
| `BUDGET_TOL_OVER` | `.common_03_capacity` | star | .claude/skills/diagram/test_checks/test_segments_02_capital_and_walls.py; .claude/skills/diagram/test_citybudget.py |
| `BUDGET_TOL_UNDER` | `.common_03_capacity` | star | .claude/skills/diagram/test_checks/test_segments_02_capital_and_walls.py |
| `GATE_SEGMENTS` | `.driver` | star | .claude/skills/diagram/test_checks/test_driver_and_fixtures.py |
| `HOUSEHOLD` | `.common_03_capacity` | star | .claude/skills/diagram/pool/provincial-cities/minami.gen.py |
| `META_CHECKS` | `.driver` | star | .claude/skills/diagram/test_checks/test_segments_11_polders_and_edges.py; .claude/skills/diagram/test_regressions.py |
| `OVERLAP_CLASS` | `.common_01_geometry` | star | .claude/skills/diagram/test_checks/test_segments_01_city_frame_and_yards.py |
| `QUARTER_DENSITY_CEIL` | `.common_03_capacity` | star | .claude/skills/diagram/check_village/__main__.py |
| `QUARTER_DENSITY_FLOOR` | `.common_03_capacity` | star | .claude/skills/diagram/check_village/__main__.py |
| `RESERVE_CAP_FRAC` | `.common_03_capacity` | star | .claude/skills/diagram/check_village/__main__.py; .claude/skills/diagram/test_checks/test_segments_01_city_frame_and_yards.py |
| `TWIN_AXES` | `.driver` | star | .claude/skills/diagram/test_checks/test_driver_and_fixtures.py |
| `city_capacity` | `.common_03_capacity` | star | .claude/skills/diagram/check_village/__main__.py; .claude/skills/diagram/test_checks/test_common_capacity.py; .claude/skills/diagram/test_checks/test_segments_01_city_frame_and_yards.py |
| `clip_poly_rect` | `.common_02_overlap_policy` | star | .claude/skills/diagram/test_checks/test_common_overlap_policy.py |
| `crop_relocatable_singletons` | `.common_03_capacity` | star | .claude/skills/diagram/test_checks/test_common_capacity.py |
| `edge_gap` | `.common_01_geometry` | star | .claude/skills/diagram/test_checks/test_common_geometry.py |
| `forest_reveal_x` | `.common_02_overlap_policy` | star | .claude/skills/diagram/settlement/_geom.py |
| `gate` | `.driver` | star | .claude/skills/diagram/cohort_audit.py; .claude/skills/diagram/hamletgen.py; .claude/skills/diagram/make_regressions.py |
| `kiln_quarters` | `.common_01_geometry` | star | .claude/skills/diagram/test_checks/test_common_geometry.py |
| `lane_near_misses` | `.common_03_capacity` | star | .claude/skills/diagram/test_checks/test_common_capacity.py |
| `lane_ward_shortfalls` | `.common_03_capacity` | star | .claude/skills/diagram/test_checks/test_common_capacity.py |
| `largest_empty_gap` | `.common_01_geometry` | star | .claude/skills/diagram/test_checks/test_common_geometry.py |
| `main` | `.driver` | star | .claude/skills/diagram/check_village/__main__.py; .claude/skills/diagram/test_gencache.py; .claude/skills/diagram/test_villages.py |
| `matrix_extents` | `.common_02_overlap_policy` | star | .claude/skills/diagram/test_checks/test_common_overlap_policy.py; .claude/skills/diagram/test_checks/test_segments_01_city_frame_and_yards.py |
| `matrix_policy` | `.common_01_geometry` | star | .claude/skills/diagram/test_checks/test_common_geometry.py |
| `matrix_violations` | `.common_02_overlap_policy` | star | .claude/skills/diagram/test_checks/test_common_overlap_policy.py; .claude/skills/diagram/test_checks/test_segments_01_city_frame_and_yards.py |
| `onmap_field_edge` | `.common_02_overlap_policy` | star | .claude/skills/diagram/test_checks/test_common_overlap_policy.py |
| `point_in_poly` | `.common_01_geometry` | star | .claude/skills/diagram/site_justice.py; .claude/skills/diagram/test_villages.py |
| `poly_area` | `.common_01_geometry` | star | .claude/skills/diagram/test_citybudget.py |
| `poly_dist` | `.common_01_geometry` | star | .claude/skills/diagram/test_settlement/test_land.py |
| `poly_gap` | `.common_02_overlap_policy` | star | .claude/skills/diagram/test_checks/test_common_overlap_policy.py |
| `rect_corners` | `.common_01_geometry` | star | .claude/skills/diagram/test_checks/test_common_geometry.py |
| `seg_dist` | `.common_01_geometry` | star | .claude/skills/diagram/site_justice.py |
| `seg_intersect` | `.common_01_geometry` | star | .claude/skills/diagram/test_checks/test_common_geometry.py |
| `seg_to_rect_dist` | `.common_01_geometry` | star | .claude/skills/diagram/test_checks/test_common_geometry.py |
| `sweep_hi` | `.common_01_geometry` | star | .claude/skills/diagram/test_checks/test_common_geometry.py |
| `twin_axes` | `.driver` | star | .claude/skills/diagram/test_checks/test_driver_and_fixtures.py |
| `twin_diff_count` | `.driver` | star | .claude/skills/diagram/test_checks/test_driver_and_fixtures.py |
| `twin_report` | `.driver` | star | .claude/skills/diagram/test_checks/test_driver_and_fixtures.py |
| `water_setback` | `.common_02_overlap_policy` | star | .claude/skills/diagram/test_checks/test_common_overlap_policy.py |

**Totals**: 44 consumed names (2 regex artifacts from specs/024's split_package.py f-strings excluded); 38 star-provided; 6 need the explicit aliased block:
- `_LABEL_EXEMPT` from `.common_01_geometry`
- `_LABEL_GROUP` from `.common_01_geometry`
- `_MATRIX_OUTSTANDING` from `.common_01_geometry`
- `_OVERLAP_EXEMPT` from `.common_01_geometry`
- `_OVERLAP_STRUCTS` from `.common_01_geometry`
- `_ward_interior` from `.common_02_overlap_policy`
- `{'` from `??? MISSING`
