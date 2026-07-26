# Phase 1 Data Model: The Overlap Matrix

**Feature**: [spec.md](./spec.md)

## 1. Overlap classes

Every geometric manifest key gets exactly one class. The class carries the *semantics* of the
ground the feature occupies - which is what makes a pairwise policy possible at all.

| class | means | keys |
|---|---|---|
| `SOLID` | an exclusive built footprint | `houses`, `buildings`, `flophouses`, `manors`, `religious`, `shrines`, `ministries`, `cemeteries`, `cremation_grounds`, `ossuaries`, `mausoleums`, `fire_towers`, `drum_towers`, `martial_halls`, `dojos`, `kosatsuba`, `punishment_spots`, `execution_grounds`, `boundary_markers`, `theater_stage`, `wells`, `merchant_estates`, and every trade work (`breweries`, `dye_yards`, `lumber_yards`, `oil_presses`, `pawnshops`, `bathhouses`, `kilns`, `farriers`, `tanning_yards`, `charcoal_yards`, `refining_forges`) |
| `GROUND` | cultivated / engineered ground worked as a surface | `fields`, `dry_plots`, `flower_fields`, `fallow_patches` |
| `WATER` | a watercourse or body | `streams`, `channels`, `field_ditches`, `canals`, `pond`, `moat` |
| `WAY` | a trafficked bed | `road`, `town_streets`, `alleys`, `lanes` |
| `COVER` | **permissive** ground cover - what the ground IS, not a thing occupying it | `commons`, `pastures`, `marsh` |
| `OVERLAY` | declarative zoning that CONTAINS features by definition | `quarters`, `wards` |
| `VEGETATION` | planted or standing timber | `village_groves`, `groves`, `forest`, `tree_stands` |
| `ANNEX` | belongs to a named parent and abuts it | `gardens`, `threshing_yards`, `farm_sheds`, `storehouses`, `byres` |

**Why `COVER` is permissive** (the GM's own example, and the design's load-bearing distinction): a
grazing common, a pasture or a scrub margin is a description of *what the ground is*, not an object
sitting on it. A well, a house or a field built on grazing land is the normal case - the grazing
simply stops there. Contrast `GROUND`, which is worked *as a surface*: a paddy basin or a hatake bed
is destroyed by anything standing in it. That is the whole difference between "overlap is fine" and
"overlap is a defect", and it is a fact about land use, not about drawing.

## 2. The policy matrix

**FORBIDDEN by default.** Every permission below carries its reason.

| pair | policy | reason |
|---|---|---|
| `COVER` x anything | ALLOW | permissive ground cover (above) |
| `OVERLAY` x anything | ALLOW | a zoning overlay contains features by definition |
| `WATER` x `WATER` | ALLOW | watercourses meet at confluences |
| `WAY` x `WAY` | ALLOW | ways meet at junctions |
| `WATER` x `WAY` | ALLOW **only where bridged** | a road crosses water at a bridge; unbridged crossings are already gated separately |
| `VEGETATION` x `VEGETATION` | ALLOW | adjacent groves abut; canopies merge |
| `VEGETATION` x `COVER`/`OVERLAY` | ALLOW | via the permissive rows |
| everything else | FORBIDDEN | including the motivating `GROUND` x `WATER` |

## 3. Parent-scoped exemption (replaces most per-pair rules)

Several records name their parent. Such a feature may overlap **its own parent and nothing else** -
which is strictly stronger than the blanket per-pair exemptions it replaces.

| key | parent field | meaning |
|---|---|---|
| `gardens`, `threshing_yards`, `farm_sheds`, `byres` | `of` | abuts its own farmhouse |
| `storehouses` | `of` | a kura behind its own shop |
| `field_ditches` | `field` | a field's own irrigation, drawn ON it by design |

An annex overlapping a *different* building stays a defect - which the old blanket
`_OVERLAP_EXEMPT` entries could not express.

## 4. Drawn extents, not envelopes (the central correctness rule)

Several records are an ENVELOPE around sparse drawn objects. Testing the envelope is what produced
~50 of the 101 false positives in the survey. The matrix reads the **drawn** geometry:

| key | recorded envelope | what is actually inked - test THIS |
|---|---|---|
| `fields` | `outline` (a smoothed curve bowing outside the crop) | `plots` |
| `village_groves` | `poly` (the belt outline) | `clumps` at radius `r` |
| `forest` / `tree_stands` | stand outline | `tree_crowns` |
| `commons` / `pastures` | `poly` | n/a - permissive, never tested |
| `wells` | - | the drawn marker radius `vr`, not `r` |
| markers (`kosatsuba`, `boundary_markers`) | true `w`/`h` | drawn `vw`/`vh` where present |

## 5. Tolerance

Linear features draw at a **stroke floor** (a 1 ft ditch inks at the 4 px minimum), so a drawn
watercourse is wider than its true width. The matrix tests at TRUE half-width plus a small slack,
never at ink width, so stroke-floor slop cannot manufacture a defect. Where a true width is unknown
the check abstains rather than guessing.

## 6. Checks

| check | fires when |
|---|---|
| `features_do_not_overlap` | any pair whose classes are FORBIDDEN overlaps in drawn extent, and no parent-scope or per-pair exception applies |
| `every_feature_classified_for_matrix` | a drawn geometric key has no class (the ratchet) |

Per-pair overlap checks the matrix subsumes are retired; any kept keeps a recorded reason.
