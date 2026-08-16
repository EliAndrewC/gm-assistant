# Contract: the `settlement` import surface (US3)

`import settlement` is consumed by ~45 modules: `check_village` segments and commons, `hamletgen`,
`site_justice`, `why_placed`, `test_*` modules, every pool `*.gen.py`, and `wip/*.gen.py`. The
package split MUST preserve this surface exactly.

## Contract

1. `import settlement` succeeds and exposes every name any current in-repo consumer references
   (public AND underscore-prefixed - tests reach internals today).
2. `settlement.Settlement` is one class; every current method resolves on it to a single
   definition (mixin MRO, no duplicates - `scripts/check-duplicate-defs.py` is the repo-wide
   backstop).
3. Class-level monkeypatching (`monkeypatch.setattr(settlement.Settlement, "m", ...)`) behaves as
   before. Module-level monkeypatch targets that move into submodules are re-pointed in the tests
   within US3, and the hazard is documented in `settlement/CLAUDE.md` (check_village precedent).
4. The CLI/script entry points that today execute `settlement.py` behavior (none directly -
   generation always goes through gens/hamletgen) are unaffected; `_assert_not_main_tree` keeps
   firing on package import.

## How the re-export list is derived and verified

- **Derived**: the mover script scans all consumers for `settlement.<name>` attribute references
  and `from settlement import ...` names, unions the two, intersects with the monolith's
  module namespace, and generates `settlement/__init__.py` with explicit imports (024 R6
  method). The generated list is committed with the split and recorded below at implement time.
- **Verified**: (a) full test suite + gate green; (b) generation-identity oracle covers the gens
  (the consumers a test run does not import); (c) a one-off import smoke over every consumer
  module (`python3 -c "import <mod>"` per consumer, or the oracle run itself for gens).

## Generated surface

87 names re-exported (explicit `X as X` form for mypy strict no_implicit_reexport), derived from the consumer census intersected with the monolith namespace:

- `._geom`: `BUNDLE_PITCH_FT`
- `._geom`: `GOVERNOR_CAPTION_FS`
- `._geom`: `HALL_CAPTION_FS`
- `._geom`: `LABEL_AIR_CAP`
- `._geom`: `LABEL_MIN_AIR`
- `._geom`: `LANDING_FT`
- `._geom`: `PLANK_ABUTMENT`
- `._geom`: `PLANK_BANK_REACH`
- `._geom`: `TORII_PITCH_FT`
- `._geom`: `Indexed`
- `._geom`: `PointGrid`
- `._geom`: `SeatMemo`
- `._geom`: `_assert_not_main_tree`
- `._geom`: `_union_area`
- `._geom`: `box_gap`
- `._geom`: `boxed_grid`
- `._geom`: `boxed_hit`
- `._geom`: `boxed_polys`
- `._geom`: `boxed_seg_hit`
- `._geom`: `boxed_segs`
- `._geom`: `edge_dist`
- `._geom`: `fillet_polyline`
- `._geom`: `forest_frame_span`
- `._geom`: `forest_reveal_x`
- `._geom`: `kido_bar_deg`
- `._geom`: `label_aabb`
- `._geom`: `label_quad`
- `._geom`: `label_tilt`
- `._geom`: `lane_runs`
- `._geom`: `lane_through_gate`
- `._geom`: `linear_tilt`
- `._geom`: `linear_tilt_full`
- `._geom`: `paddy_wet_rings`
- `._geom`: `point_in_poly`
- `._geom`: `point_quad_dist`
- `._geom`: `poly_gap`
- `._geom`: `quad_hits_seg`
- `._geom`: `rail_quad`
- `._geom`: `rects_overlap`
- `._geom`: `region_blocked`
- `._geom`: `ring_touches`
- `._geom`: `rot_rect`
- `._geom`: `sat_overlap`
- `._geom`: `seg_closest`
- `._geom`: `seg_dist`
- `._geom`: `seg_intersect`
- `._geom`: `segments_cross`
- `._geom`: `stroke_quads`
- `._geom`: `tilt_caption_seat`
- `._geom`: `torii_halfbox`
- `._geom`: `torii_wall_conflicts`
- `._geom`: `tower_quad`
- `._geom`: `trough_quad`
- `._geom`: `village_population`
- `._geom`: `ward_interior`
- `._geom`: `way_beds`
- `._geom`: `wellhead_quad`
- `._knobs`: `BOUNDARY_MARKER_FT`
- `._knobs`: `BOUNDARY_MARKER_MIN_PX`
- `._knobs`: `BOUNDARY_STONE_CLEAR_FT`
- `._knobs`: `EXECUTION_GROUND_DEAD_CLEAR_FT`
- `._knobs`: `KIDO_TOWER_KEEPCLEAR`
- `._knobs`: `KNOBS`
- `._knobs`: `KOSATSUBA_MARKER_MIN_PX`
- `._knobs`: `LANE_SKELETONS`
- `._knobs`: `MERCHANT_ESTATE_WEIGHTS`
- `._knobs`: `PUNISHMENT_SPOT_FT`
- `._knobs`: `WALL_DEFENSE`
- `._knobs`: `Knob`
- `._knobs`: `_centroid`
- `._knobs`: `_sharp_corners`
- `._knobs`: `bridge_carried_ways`
- `._knobs`: `bridge_crossed_waters`
- `._knobs`: `crop_boxes`
- `._knobs`: `execution_ground_ft`
- `._knobs`: `knob_rng`
- `._knobs`: `machi_mouths`
- `._knobs`: `moat_current_at`
- `._knobs`: `moat_swept_tap`
- `._knobs`: `register_knob`
- `._knobs`: `resolve_knob`
- `._knobs`: `roll_merchant_estate_count`
- `._knobs`: `roll_torii_count`
- `._knobs`: `scope_seed`
- `._knobs`: `skeleton_layout`
- `._knobs`: `wall_tower_spacing_px`
- `.core`: `Settlement`
