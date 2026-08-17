"""SITEGEN - the generation machinery the settlement TIERS share.

WHY THIS PACKAGE EXISTS. `hamletgen/` is the first scripted tier generator; the village, town and
city tiers follow (`migration-plan.md` section 8). The GM's ruling on 2026-08-17 was that **tiers
share a library** rather than one tier's generator growing into the others. This package is that
library: the destination for anything a second tier turns out to need.

THREE RULES, and they are the whole contract:

1. **Membership.** A module belongs here only if its LOGIC is tier-independent - *parameterized by
   scale rather than assuming one*. A hard-coded household count, hamlet band, headman, ward or
   wall means it belongs to that tier's generator instead.

   "Does it say hamlet?" is a first filter, not the test. `net_acres` in `geom.py` mentions both a
   village grain and a hamlet grain and takes `ftpx` as a parameter so it is right at either - that
   mention is the RECORD of someone checking it against two tiers, and it is evidence for
   inclusion. Conversely `hamletgen/frame.py` says "hamlet" nowhere and stays out anyway, because
   all three of its members take a `SitePlan`.

2. **Direction, one-way.** `hamletgen` (and `villagegen`, `towngen` after it) import `sitegen`.
   `sitegen` NEVER imports a tier generator. `tests/sitegen/test_direction.py` asserts this rather
   than trusting the convention - a cycle here would make the shared library depend on the first
   tier that happened to be written, which is exactly the shape this package exists to avoid.

3. **Growth: MOVE, never copy.** When a later tier needs a stage that currently lives in
   `hamletgen`, move it here and have both tiers import it. Copying is how two tiers quietly drift
   apart, and the drift stays invisible until the maps disagree.

WHY IT STARTED SMALL. Feature 119 extracted ~110 lines, not the ~450 its own spec first estimated:
reading the dependency edges refuted an estimate that had been made from filenames. That is the
correct size for a FIRST extraction. The remaining candidates - `WIND_VECTORS`, `FALL_BEARINGS`,
`CARDINAL_BEARINGS`, `WIND_TURNS`, all genuinely terrain doctrine a village shares - move when the
village tier makes them a second real consumer, so the seam is OBSERVED rather than predicted.

The re-export mechanism below is the same star-import surface the sibling packages use (clause 14,
feature 027): `from l7r.diagram.sitegen import centroid` works, and so does reaching into the
submodule directly.
"""

from __future__ import annotations

from .geom import *  # noqa: F403 - the stars ARE the re-export mechanism (clause 14)
from .jobs import *  # noqa: F403
from .types import *  # noqa: F403
