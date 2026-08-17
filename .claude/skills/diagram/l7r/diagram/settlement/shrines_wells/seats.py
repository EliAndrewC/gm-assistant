"""The general 'where can a w x h feature stand?' API, asked of the real _fits at the moment of placement.

Split from settlement/shrines_wells.py by feature 116 - see settlement/shrines_wells/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any

from .._geom import (
    Pt,
    point_in_poly,
)

if TYPE_CHECKING:
    from ..core import Settlement


class OpenSeatMixin:
    def _footprint_clear(self: Settlement, x: float, y: float, w: float, h: float) -> bool:  # type: ignore[misc]
        """Is the WHOLE `w` x `h` footprint at (x, y) inside the bound and off every block/corridor?

        `_fits` deliberately tests only a candidate's CENTER against `self.bound`, `block_polys` and
        the corridors (it is footprint-aware only for `placed` / `grove_rects`). That asymmetry is
        what lets a dense urban pack put a house's eaves over the edge of a block poly, and changing
        it wholesale would reflow every packed quarter in the pool - so this tightens exactly one
        thing: **the bound**.

        The distinction is soft reservation vs hard boundary. `block_polys` and corridors are
        RESERVATIONS - a label band, a civic apron, a fence standoff - and a footprint overhanging
        one by a few px is routine and invisible; demanding the whole footprint clear them cost
        Nagahara a well and pushed Hoshizora's punishment ground off its street when it was tried.
        `self.bound` is a HARD EDGE: the ring-road loop a city packs inside, or the wall. A footprint
        that crosses it is drawn on the patrol road, which is a defect at any overhang - and it is
        exactly how the martial hall got a seat whose SE corner crossed Tango's ring bed while its
        center sat comfortably inside the bound (GM 2026-07-25).

        Nine samples (four corners, four edge midpoints, the center) - enough for any bound bigger
        than a quarter of the footprint, and free at the scale open_seat is called at. Corridors and block
        polys stay center-tested here, deliberately - see above."""
        hw, hh = w / 2, h / 2
        pts = [(x + dx, y + dy) for dx in (-hw, 0.0, hw) for dy in (-hh, 0.0, hh)]
        return not self.bound or all(point_in_poly(px, py, self.bound) for px, py in pts)

    def open_seat(self: Settlement, rect: Any, w: float, h: float, step: float = 4.0, clear_of: Any = (), well: bool = False, footprint: bool = True, disc: bool = False) -> Pt | None:  # type: ignore[misc]
        """WHERE can a `w` x `h` feature actually stand inside `rect` (x0, y0, x1, y1)? Scans the
        rect and returns the best clear seat, or None if the ground is genuinely full.

        WHY THIS EXISTS (GM 2026-07-25, from a transcript profile): fitting one extra well into a
        packed quarter took THREE regenerate-and-check cycles - two batches of hand-picked
        coordinates, every one of them rejected - because the engine knows where a feature can go
        and nothing outside it could ask. Guessing from a manifest is worse than useless: a scan
        that sees only building rects recommends seats that `_fits` then refuses for reasons that
        never appear in the manifest at all (a ward fence's no-build corridor, a block poly, the
        bound ring). So this asks the SAME `_fits` the real placement path asks, at the same moment
        in the gen, and the answer is therefore the truth rather than a guess.

        `clear_of` is a list of (x, y) to stand away FROM - pass the existing wells/features of the
        same kind and the seat returned is the one that splits the catchment best (maximum distance
        to the nearest of them, ties broken toward the rect's center). `well=True` also applies the
        wellhead-specific refusal (`_in_scrub_cover`), so the seat it returns is one `well_at` will
        actually take. Call it right where the feature would be placed - what fits depends entirely
        on what has been drawn so far (see CLAUDE.md "DRAW ORDER").

        The seat returned is clear along its WHOLE FOOTPRINT, not merely at its center - see
        `_footprint_clear` for why that differs from `_fits` and why only this API tightens it.
        `footprint=False` falls back to the bare center test, i.e. exactly what a pack would take."""
        x0, y0, x1, y1 = (float(v) for v in rect)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        pts = [(float(px), float(py)) for px, py in clear_of]
        best: tuple[float, float, Pt] | None = None
        gy = y0
        while gy <= y1:
            gx = x0
            while gx <= x1:
                # `disc=True` says the CANDIDATE is round, so min(w,h)/2 is its exact reach rather
                # than the probe box's half-diagonal. Opt-in, not implied by well=True: the derived
                # well GRID relies on the conservative radius as its padding, and making it exact
                # there put a wellhead on a building.
                if (not well or not self._in_scrub_cover(gx, gy)) and self._fits(gx, gy, w, h, disc=disc) and (not footprint or self._footprint_clear(gx, gy, w, h)):
                    apart = min((math.hypot(gx - px, gy - py) for px, py in pts), default=0.0)
                    central = -math.hypot(gx - cx, gy - cy)  # tie-break toward the middle of the rect
                    if best is None or (apart, central) > (best[0], best[1]):
                        best = (apart, central, (gx, gy))
                gx += step
            gy += step
        return best[2] if best else None
