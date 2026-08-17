# Phase 1 Data Model: the geometry this feature reads and writes

No persisted schema changes. Every record below already exists; this feature changes **which of them the placer consults**, not what they contain. That is the whole point - the defect is that the placer reads a different record than the renderer.

## Records

### Bundle geometry (`_bundle_geom` -> `geom`)

The metric layout of one homestead around a seed point. In-memory only, but it is also stashed on each house record as `geom` (which is how the sun-corridor rule reads neighbors' yards during placement, before `farmsteads()` has flushed anything to the manifest).

| key | shape | notes |
|---|---|---|
| `house` | `(cx, cy, w, h)` | the seed rect. **Not necessarily what is drawn** - this is the defect |
| `yard` | `(cx, cy, w, h)` | threshing yard, south of the house; jitters DOWN from its base (a work apron sized to the harvest) |
| `garden`/`gardens` | rect / list of beds | dooryard garden, on an adaptive sunny side when nucleated; jitters UP from its base (a minimum plot to feed a household) |
| `shed` | `(cx, cy, w, h)` | optional *kura*, N or W side |
| `grove_n`, `grove_w` | `(cx, cy, w, h)` | the windward L-belt; **dispersed only** - a nucleated cluster shelters itself |
| `bbox` | `(cx, cy, W, H)` | the whole-bundle reservation, and the thing bundles are currently spaced by |

**The divergence this feature closes**: the drawn house comes from the house *record* (`rec["x"], rec["y"], rec["w"], rec["h"], rec["rot"]`) passed to `house()`, while the seat was cleared from `geom["house"]`. Offset, scale (wealth/length jitter) and rotation can all differ. The renderer and the placer must agree, and the renderer is the authority.

### Placed reservation (`self.placed`)

An `Indexed` registry of `(x, y, w, h)` tuples. Two sites rebind it to a shorter filtered list ("lift own reservation", "drop the un-appurtenanced farmhouse"), which is why it is `Indexed` and not a plain list - a rebind must not silently leave a stale spatial index behind. Any change here must preserve that property.

### Grove rects (`self.grove_rects`)

`(x, y, w, h)` per drawn grove arm. **Sanctioned abutment lives here**: adjacent groves may abut into one shared windbreak, and a grove may hug a paddy bund. The tightened verdict must keep both legal.

### Drawn surface / tread

A way's rendered width, registered beside its softer corridor (`_record_tread`). Currently consulted by `_fits` via `_on_a_tread(x, y, w, h)` and **not at all** by the bundle path. Lanes only, deliberately - the other ways already pad their corridors by hand, and tightening them cost a public well.

### Soft clearance (corridor)

A way's no-build band, plus caption bands, civic aprons and fence standoffs. Slack that a footprint routinely overhangs by a few px. Consulted by center (`_near_corridor(cx, cy)`) and **stays that way**; conflating it with a surface is a known, costed mistake.

## The one distinction that matters

| | measured against | test | why |
|---|---|---|---|
| **surface** (tread, another building) | the rotated corner quad the map draws | exact | you could pace the distance out between two walls; a wall on a road is wrong at any tolerance |
| **clearance** (corridor, apron, caption band) | the candidate's center | center, deliberately | it is slack, not a wall; footprint-testing it starts refusing seats that are fine, which has already cost a well and a punishment ground |

This table is the feature in one page. Everything else is plumbing.

## State transitions (placement order, which is load-bearing)

```
water + fields laid
   -> lanes laid          (a lane lays its corridor AND registers its tread; houses front it)
   -> bundles seated      (try_place / _place_bundle_nucleated -> _bundle_fits)   <-- item 3 acts here
   -> wells, byres        (open_seat, which is where the circle blocks features)  <-- item 2 acts here
   -> farmsteads() flush  (the DRAWN rects finally appear)
   -> groves drawn last   (so no tree is drawn over a building, by rule not z-order)
```

The reason item 3 is a placement-time fix and not a draw-time one: by the time `farmsteads()` runs, every seat is already committed. The placer has to know the drawn geometry *while it is choosing*, which is why the fix is to test the drawn rect at seat time rather than to reconcile afterward.
