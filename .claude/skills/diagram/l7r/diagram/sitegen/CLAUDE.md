# `sitegen/` - the machinery the settlement TIERS share

**The three rules first, because they are what this package is for.** The full reasoning is in
`__init__.py`'s docstring; this is the operational form.

1. **Membership** - a module belongs here only if its LOGIC is tier-independent, *parameterized by
   scale rather than assuming one*. A hard-coded household count, hamlet band, headman, ward or
   wall means it belongs to that tier's generator instead. "Does it say hamlet?" is a first filter,
   not the test: `net_acres` mentions a village grain AND a hamlet grain and takes `ftpx` as a
   parameter so it is right at either - that mention is the record of someone checking it against
   two tiers. `hamletgen/frame.py` says "hamlet" nowhere and stays out, because all three of its
   members take a `SitePlan`.
2. **Direction, one-way** - `hamletgen` (and `villagegen`, `towngen` after it) import `sitegen`.
   `sitegen` NEVER imports a tier generator. `tests/sitegen/test_direction.py` asserts it.
3. **Growth: MOVE, never copy** - a hamlet stage a later tier needs gets moved down here and
   imported by both. Copying is how two tiers quietly drift apart, invisibly, until the maps
   disagree.

## Look here when

| file | look here when |
|---|---|
| `geom.py` | you need a geometry predicate or measure - `poly_area`, `net_acres`, `centroid`, `unit`, `crop_polys`, `pull_clear`, `crosses_disc`, `crosses_poly` - or one of them is giving a wrong answer |
| `types.py` | you need `Pt`, `Poly`, or the `SQ_FT_PER_ACRE` conversion |
| `jobs.py` | you are fanning a cohort roll out across cpus and need the courtesy rule |
| `__init__.py` | you are deciding whether something belongs in this package at all |

`from l7r.diagram.sitegen import centroid` works (star-import re-exports, clause 14), and so does
reaching into a submodule directly.

## Why it is small, and why that is correct

Feature 119 extracted ~110 lines. Its own spec had estimated ~450 from filenames; reading the
dependency edges refuted that (`frame.py` is three `stage_*(s, plan: SitePlan)` functions, `Report`
prints a hamlet cohort row - both stay in `hamletgen`).

A first extraction should be small. The remaining candidates - `WIND_VECTORS`, `FALL_BEARINGS`,
`CARDINAL_BEARINGS`, `WIND_TURNS`, all genuinely terrain doctrine a village shares - move when the
village tier makes them a **second real consumer**. Extracting on the second use means the seam is
observed; extracting on the first means it is predicted, and a predicted seam has to be re-cut.

## Tests

`tests/sitegen/` mirrors this directory and is deliberately self-contained - it must not import
from `tests/hamletgen/`, for the same reason the source must not. `SQUARE` is duplicated in
`tests/sitegen/_builders.py` rather than shared: four numbers against a dependency that would
undo the point of the package.
