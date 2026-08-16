# waterfields/ - the water-first field engine as a package

Split from the 2,737-line `waterfields.py` monolith by feature 110 (constitution Principle X
clause 13: files stay at human scale - the cost being managed is context-window tokens). **Load
only the file the task calls for**; this index is the map. `import waterfields` still exposes
the whole consumed surface via `__init__.py` (star-import re-exports per clause 14 / the 027
mechanism, plus an aliased block for the externally-consumed underscore names; guard:
`tests/waterfields/test_surface.py`) - never add logic to the `__init__`.

The engine's doctrine (THE INVERSION - fields grow around the water network; the warp-thread
march; slope as a knob) lives in the `__init__.py` docstring and `settlements.md`
'Water-first fields v2'. The split changed no behavior: every manifest was byte-identical
before and after (the feature's oracle).

## Look here when

| file | look here when |
|---|---|
| `__init__.py` | you need the engine doctrine docstring or the re-export mechanism; never logic |
| `frame.py` | the contour(u)/fall(f) frame (`_Frame`), warp-thread state (`_Thread`), the march constants (`DF`, `GAP`, `DRAIN_W_*`, `BANK_MARGIN`), the channel TAPER LAW (`taper_w` - width goes as sqrt(discharge), so w SQUARED interpolates; shared by every consumer of a local width, and the one place to change it), or pure geometry (`_at_f`, `_f_at_u`, `_seg_x`, `_seg_d`, `_pip`, `_poly_perim`, `_signed_area`, `_poly_area`, `_dug_polyline`, `_point_along`, `_drain_bank`, `_miter_normals`) |
| `palette.py` | colors (`_RICE_GREEN`, `RICE_GREENS`, `FLOODED`, `RIPE_GOLD`, `BUND`, `AZE`, `BEAN_GREEN`), the real-feet paddy-cell calibration (`PADDY_CELL_ACRES`, `paddy_grain`), `aze_w`, `organic_parcel`, `DRY_CROPS` |
| `banks.py` | how plots hem to canals and ditches: `polyline_cum`, `drain_bank_clearance`, `supply_bank_clearance`, `floor_overhang`, `hem_to_bank`, `hem_on_paddy`, `_TOE_MIN_THICKNESS`, `_TOE_MIN_APEX`, `pointed_ring`, `dedup_ring`, `round_channel_joints`. **The two ways a plot can fail to be a basin live here and are independent**: `_TOE_MIN_THICKNESS` (an inradius - too narrow anywhere) and `_TOE_MIN_APEX` (a taper - a LONG needle passes the thickness test, which is how the fan-toe sunburst survived; see `research/fields.md`, "A basin never tapers to a point") |
| `comb.py` | `build_comb` - the water-first comb builder (pond sluice, head-race, supply canals, thread march, offtakes) - and `_fill_wedges` |
| `carve.py` | `_carve` (cutting paddy plots between marched threads), `_dry_fields` (the dry-crop hem tiling), `_bund_beans` (azemame bead accents) |
| `seams.py` | `close_seams` - the last pass over a comb fan: it plants or absorbs every scrap of bare ground left inside the command area so that **two adjacent basins share ONE bund**. Read it before changing how the fan's leftovers are handled; it replaced `_fill_wedges` (feature 2026-08-17) and its docstring carries the research, the defect, and why it runs after the toe/hem pass. The only shapely consumer in the engine |
| `polder.py` | `build_polder` (dike-and-drain reclamation), `build_terraces` (contour terraces), `build_ribbon` (valley ribbon paddies) |

Import DAG (leaf-first: frame, palette, banks, carve, comb, polder; no cycles). The three
former mega-functions (`build_comb`, `build_polder`, `_carve`) are decomposed into named
sequential stage functions in their own files - each stage takes its state as parameters and
returns what the next stage needs, so the pipeline reads top-down in the builder body.
