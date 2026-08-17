"""The types and unit conversions every tier generator measures with.

Moved verbatim out of `hamletgen/consts.py` by feature 119. They were never about hamlets - a
village, a town and a city all describe a point as a pair of floats and all convert square pixels
to acres the same way - so they are the natural floor of the shared library.

`hamletgen/consts.py` re-exports these three names, so `from .consts import Poly, Pt` keeps working
inside that package and `hamletgen`'s public surface is unchanged.
"""

from __future__ import annotations

Pt = tuple[float, float]
Poly = list[Pt]

SQ_FT_PER_ACRE = 43560.0
