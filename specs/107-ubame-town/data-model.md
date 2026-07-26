# Phase 1 Data Model: Ubame County Town

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

The "data model" for a Mode B map is the **manifest contract**: what the generator records and what
the validator reads. Placement and its check must read the SAME manifest source, so every field
below is written by `settlement.py` and consumed by `check_village.py` - never re-derived from
engine internals.

## New manifest keys

### `M["charcoal_yards"]` - list

| field | type | meaning |
|---|---|---|
| `x`, `y` | float | center of the whole ground, map coords |
| `w`, `h` | float | TRUE footprint of the whole ground, in px (= feet at town scale) |
| `rot` | float | degrees; the yard's **road side is local -y**, matching the tanning yard's water-side convention |
| `label` | str | caption, default `"charcoal yard"` |
| `sheds` | int | number of roofed stacking sheds drawn (>= 1) |
| `apron` | `[x, y, w, h]` | the open cooling ground, recorded separately from the covered sheds |

Written by `s.charcoal_yard(...)` via the shared `_trade_record` tail (which also appends to
`placed` and reserves the caption band in `block_polys`), plus the `sheds` / `apron` extras.

### `M["refining_forges"]` - list

| field | type | meaning |
|---|---|---|
| `x`, `y` | float | center of the whole ground |
| `w`, `h` | float | TRUE footprint of the whole ground |
| `rot` | float | degrees; the forge's **open working front is local +y** |
| `label` | str | caption, default `"refining forge"` |
| `hearths` | int | hearths under the shed (2 - the two-stage refining) |

### `M["borders"]` - list

| field | type | meaning |
|---|---|---|
| `poly` | `[[x, y], ...]` | the jurisdictional line, authored north-to-south |
| `label` | str | e.g. `"Fox lands"` |

**No `w`/`h`.** A border is a line of law, not a footprint. It is classified in `_OVERLAP_EXEMPT`
and `_LABEL_EXEMPT` with that reason recorded, so nothing is required to stand clear of it - the
magistracy's east wall standing on it is the intended arrangement.

## New `meta()` knobs

| knob | default | effect |
|---|---|---|
| `charcoal_district=True` | absent (off) | requires a charcoal yard (`settlement_has_charcoal_yard`) |
| `iron_district=True` | absent (off) | requires a refining forge (`settlement_has_refining_forge`) |

Both are **opt-in**, following the `granary=True` precedent: an ordinary county seat declares
neither and is unaffected.

## Registry classification (the KEEP-CLEAR CONTRACT)

| key | `_OVERLAP_*` | `_LABEL_*` | note |
|---|---|---|---|
| `charcoal_yards` | `_OVERLAP_STRUCTS` | `_LABEL_GROUP: "charcoal yard"` | gated off all fifteen hazards by membership alone |
| `refining_forges` | `_OVERLAP_STRUCTS` | `_LABEL_GROUP: "refining forge"` | same |
| `borders` | `_OVERLAP_EXEMPT` + reason | `_LABEL_EXEMPT` + reason | a line of law is not a physical object |

`every_feature_classified_for_overlap` and `every_solid_feature_classified_for_labels` fail if any
of the three is left unclassified, so this cannot be forgotten.

## New check contracts

| check | scope | fires when |
|---|---|---|
| `settlement_has_charcoal_yard` | `meta.charcoal_district` | the knob is declared and no charcoal yard is drawn |
| `charcoal_yard_keeps_fire_gap` | any map with a charcoal yard | a yard's footprint comes within **30 real ft** of any other solid structure |
| `settlement_has_refining_forge` | `meta.iron_district` | the knob is declared and no forge is drawn |
| `refining_forge_stands_off_dwellings` | any map with a forge | a forge's footprint comes within **60 real ft** of any dwelling |
| `refining_forge_downwind` | any map with a forge **and** a `windward` declaration | the forge does not lie on the downwind side of the dwelling centroid |

**Deliberate asymmetry**: the two *presence* checks are declaration-gated (only a fuel or iron county
should own one), but the three *siting* checks key off the FEATURE's presence, not the knob. A yard
or forge drawn on any map, declared or not, is fully validated. This is the mitigation for the
"a check that never RUNS looks exactly like a check that passes" hazard, and the pool-wide
`grep -c` diagnostic is run as an explicit task to prove each one actually executes.

Thresholds are expressed in **real feet** and converted through `meta.ftpx`, so they mean the same
thing at every tier rather than being pixel constants that silently change size between scales.

## Ubame map declarations

```text
name        = "Ubame"          scale       = "town"        walled      = False
clan        = "Scorpion"       ftpx        = 1             toscale     = True
down_deg    = 135              water_flow  = 135           windward    = "NW"
nucleated   = True             charcoal_district = True    iron_district = True
```

`imperial_road` is **not declared** - the trunk road is a domain road, so it carries no label and the
town draws no farrier. `walled=False` means the wall, gate, gate-market, fire-tower and drum-tower
checks correctly do not run; that absence is deliberate and is confirmed by the pool-wide check-ran
diagnostic rather than assumed.

Monasteries come from `clan="Scorpion"` -> Benten and Jurojin (`CLAN_FORTUNES`).
