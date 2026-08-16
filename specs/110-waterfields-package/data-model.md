# Data Model: waterfields/ Package Split

**Feature**: 110-waterfields-package | **Date**: 2026-08-16

This feature moves code; it defines no new runtime data. The entities are the package layout
and the two records the verification rides on.

## Package layout (target state)

```text
.claude/skills/diagram/waterfields/
├── __init__.py     # derived surface: docstring + 6 star imports + aliased underscore block (~40 lines)
├── CLAUDE.md       # "look here when" index (check_village style)
├── frame.py        # Pt/Poly, DF, GAP, DRAIN_W_*, _Frame, _Thread, _at_f, _f_at_u, _seg_x,
│                   # _seg_d, _pip, _poly_perim, _signed_area, _poly_area, _dug_polyline,
│                   # _point_along, _drain_bank, _miter_normals
├── palette.py      # PADDY_CELL_ACRES, paddy_grain, _RICE_GREEN, RICE_GREENS, FLOODED,
│                   # RIPE_GOLD, BUND, AZE, AZE_FT, aze_w, BEAN_GREEN, organic_parcel, DRY_CROPS
├── banks.py        # BANK_MARGIN, polyline_cum, drain_bank_clearance, supply_bank_clearance,
│                   # hem_to_bank, hem_on_paddy, _TOE_MIN_THICKNESS, round_channel_joints
├── comb.py         # build_comb + its extracted stage functions + _fill_wedges
├── carve.py        # _carve + its extracted stage functions + _dry_fields + _bund_beans
└── polder.py       # build_polder + stages + build_terraces + build_ribbon
```

Import DAG (arrows point at the imported module; no cycles):

```text
comb ──> carve ──> banks ──> frame
comb ──> banks, frame, palette
polder ──> banks, frame, palette
carve ──> frame
banks ──> frame
```

## Entity: re-export surface (`__init__.py`)

- Six `from .<module> import *` lines (order: frame, palette, banks, carve, comb, polder -
  leaf-first, mirroring the DAG).
- Aliased explicit block for the consumed underscore names:
  `_RICE_GREEN`, `_Frame`, `_miter_normals` (re-censused at implement time).
- No `__all__`, no logic (clause 14: derived, not maintained).

## Entity: consumed-surface census (guard-test input)

The names any file outside the package imports from `waterfields`, pinned by
`test_waterfields_surface.py`:

| kind | names |
|---|---|
| builders | `build_comb`, `build_polder`, `build_terraces`, `build_ribbon` |
| palette | `AZE`, `BEAN_GREEN`, `PADDY_CELL_ACRES`, `aze_w`, `paddy_grain`, `_RICE_GREEN` |
| banks | `BANK_MARGIN`, `polyline_cum`, `drain_bank_clearance`, `supply_bank_clearance`, `hem_on_paddy` |
| frame (tests) | `_Frame`, `_miter_normals` |

## Entity: manifest baseline (verification oracle)

- Pre-split scratch run of every waterfields-consuming gen at HEAD: `{map}.json` (+ `.svg`)
  per map, stored under the session scratchpad.
- Post-move and post-each-decomposition runs diff against it byte-for-byte.
- The `net` dict the builders return (`channels`, `plots`, `stats` keys) and the manifest
  schema are UNCHANGED by this feature - byte-identity is the proof.
