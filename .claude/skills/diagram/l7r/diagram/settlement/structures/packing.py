"""The two multi-building placement engines and the shortfall bookkeeping they share.

Split from settlement/structures.py by feature 114 - see settlement/structures/CLAUDE.md for the index.
"""

import math
import random
from collections import Counter
from typing import TYPE_CHECKING, Any

from .._geom import (
    point_in_poly,
)

if TYPE_CHECKING:
    from ..core import Settlement


class PackingMixin:
    def rowpack(self: Settlement, bbox: Any, items: Any, court_every: int = 2, court_ft: float = 21, eave_ft: float = 4, seam: float = 0.4, fill: bool = False) -> int:  # type: ignore[misc]
        """CITY row housing - the machiya/nagaya fabric (GM row-packing doctrine, 2026-07):
        urban commoners did not build detached-with-yard; street frontage was taxed and precious,
        back-lot nagaya were literally one roof over a row of family units, and Chinese county-seat
        housing shared party walls in continuous street walls. So dwellings go down as CONTIGUOUS
        TERRACES, not a scatter:
          - rows run E-W; houses TOUCH within a row (a hairline `seam` of 0.4px keeps the SAT
            overlap gate honest - independent structures grown together, outlines merging into
            a terrace strip);
          - rows come in BACK-TO-BACK PAIRS with both doors facing OUTWARD (GM doctrine
            2026-07-18): the first row of a pair faces UP (rot 180), the second DOWN (rot 0),
            their backs sharing the ~3-6 ft eave/drainage gap (`eave_ft` - rain drip, gutter,
            night-soil access - NOT an entrance). A city house has no farmhouse-style
            south-facing sun constraint; what it must have is an unblocked entrance;
          - after every pair a WALKABLE gap opens - a roji lane (~12 ft) by default, widening
            to a COURT (`court_ft`, ~15-25 ft, the idobata courtyard) every ~`court_every`
            rows - so rows never stack more than TWO deep and no household is trapped behind
            another (the city_house_doors_unblocked / city_rows_max_two_deep gates);
          - rows front the caller's roji/alleys TIGHTLY (a real roji had walls you could touch
            from its centerline) but stand a frontage-band back from real streets and the road,
            where the shop rows live. Draw the zone's alleys BEFORE calling this.
        Streets/roads/prior placements break a row naturally (the odd firebreak gap is
        historically honest). Dwelling sizes come from URBAN kinds via bscale, with mild
        per-house jitter so the terrace reads grown-up-over-time, not stamped.
        Returns the number placed."""
        # SCOPED (2026-08-08) - see pack(): same stream jitter, same cascade, same bbox key.
        with self.rng_scope("rowpack", *bbox):
            x0, y0, x1, y1 = bbox
            items = list(items)
            n0 = len(self.placed)  # obstacle snapshot: everything placed BEFORE this call
            court_px, eave_px = self.px(court_ft), max(self.px(eave_ft), 1.2)
            roji_px = max(self.px(12), 4.5)  # the walkable between-pairs lane: >= ~12 real ft, floored for legibility (vs the ~7 ft door-clear line the checks enforce)
            # linework the rows must respect: tight against alleys (roji), a frontage band off
            # streets/roads (the shop rows own that ground)
            lines = [(al["pts"], al.get("w", 10) / 2 + max(self.px(3), 2.5)) for al in self.M.get("alleys", [])]  # 2.5 >= the overlap gate's +2 margin
            lines += [(st["pts"], st.get("w", 18) / 2 + self.px(28)) for st in self.M.get("town_streets", [])]
            if self.M.get("road"):
                lines.append((self.M["road"], self.M.get("road_width", 26) / 2 + self.px(28)))
            if self.M.get("ring_road"):
                lines.append((self.M["ring_road"], self.M.get("ring_road_width", 7) / 2 + max(self.px(3), 2.5)))

            def seg_hits_rect(a: Any, b: Any, rx0: float, ry0: float, rx1: float, ry1: float) -> bool:
                # slab-clip the segment against the rect (exact for axis-aligned rects)
                (ax, ay), (bx, by) = a, b
                dx, dy = bx - ax, by - ay
                t0, t1 = 0.0, 1.0
                for p, q in ((-dx, ax - rx0), (dx, rx1 - ax), (-dy, ay - ry0), (dy, ry1 - ay)):
                    if p == 0:
                        if q < 0:
                            return False
                    else:
                        t = q / p
                        if p < 0:
                            if t > t1:
                                return False
                            t0 = max(t0, t)
                        else:
                            if t < t0:
                                return False
                            t1 = min(t1, t)
                return True

            def rect_ok(cx: float, cy: float, w: float, h: float) -> bool:
                corners = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
                for px_, py_ in corners + [(cx, cy)]:
                    if px_ < 55 or px_ > self.W - 55 or py_ < 88 or py_ > self.H - 26:
                        return False
                    if self.bound and not point_in_poly(px_, py_, self.bound):
                        return False
                    if self._in_blocked(px_, py_):
                        return False
                for pts, half in lines:  # exact rect-vs-polyline clearance (a corner
                    ex0, ey0 = cx - w / 2 - half, cy - h / 2 - half  # sample would miss a lane crossing
                    ex1, ey1 = cx + w / 2 + half, cy + h / 2 + half  # between two corners)
                    for k in range(len(pts) - 1):
                        if seg_hits_rect(pts[k], pts[k + 1], ex0, ey0, ex1, ey1):
                            return False
                r = math.hypot(w, h) / 2
                return all(math.hypot(cx - ox, cy - oy) >= r + math.hypot(ow, oh) / 2 + 1 for ox, oy, ow, oh, *_ in self.placed[:n0])

            n, idx, row = 0, 0, 0
            ytop = y0
            while items and idx < len(items):
                rowmax = 0.0
                x = x0 + self._hjit(x0, ytop, 0.7) * 4  # ragged row starts (not a stamped grid)
                while x < x1 and idx < len(items):
                    kind = items[idx]
                    bw, bh = self._dims(kind)
                    bw *= 0.94 + self._hjit(x, ytop, 1.3) * 0.24  # grown-over-time variation, still touching
                    bh *= 0.95 + self._hjit(x, ytop, 2.1) * 0.15
                    if x + bw > x1:
                        break
                    cx, cy = x + bw / 2, ytop + bh / 2
                    # pair-facing doctrine: first row of each pair faces UP (door at its top
                    # edge, onto the walkable gap above), second faces DOWN - backs meet
                    # across the eave gap, every door opens outward onto roji/court ground.
                    # building() may REFUSE the seat (a commoner unit inside a samurai ward) -
                    # the terrace then breaks there and the scan steps past, same as an obstacle.
                    if rect_ok(cx, cy, bw, bh) and self.building(cx, cy, bw, bh, kind, 180 if row % 2 == 0 else 0):
                        n += 1
                        idx += 1
                        rowmax = max(rowmax, bh)
                        x += bw + seam  # party wall: the next unit starts AT this one's gable
                    else:
                        x += 5  # an obstacle breaks the terrace; scan past it
                if rowmax == 0.0:
                    rowmax = self._dims("laborer")[1]  # an entirely-blocked row still advances
                row += 1
                if row % 2 == 1:
                    gap = eave_px  # inside a pair: the back-to-back eave/drainage gap
                elif (row // 2) % max(1, round(court_every / 2)) == 0:
                    gap = court_px  # a full idobata court every ~court_every rows
                else:
                    gap = roji_px  # between pairs: a walkable roji so both pair-fronts have entrance ground
                ytop += rowmax + gap
                if ytop + self._dims("laborer")[1] > y1:
                    break
            # RECORD THE SHORTFALL, like pack and frontage (settlement-review, 2026-08-11):
            # rowpack was the ONE placer that dropped what did not fit in silence, so
            # placement_runs_meet_their_ask - the check written to make exactly this visible - was
            # blind to it on the very map it was written for. Two monzen flanks drew 1 and 0 of 40
            # and another row 4 of 24, all behind a green gate.
            if not fill:  # fill=True declares the ask a capacity BUDGET ("row this ground out"), as in pack/frontage
                # items[idx:], NOT items: rowpack walks an INDEX where pack and frontage POP, so
                # handing the whole list over reported every run as asking exactly double what it
                # was given - and a run that seated half its ask looked like one that seated a
                # quarter, forever, because trimming to the reported figure just halved it again.
                self._shortfall("rowpack", bbox, n, list(items[idx:]))
            return n

    def pack(self: Settlement, bbox: Any, items: Any, rot: float = 0, step: float = 46, face_streets: Any = False, fill: bool = False, footpaths: int = 0) -> int:  # type: ignore[misc]
        """Densely fill a district bbox with a list of building kinds (one building
        each), grid-scan + jitter, skipping the road, blocked regions, and occupied
        spots. With face_streets, each building rotates to face its nearest street.
        Returns the number placed. Leftovers WARN via _shortfall unless fill=True
        declares the request a capacity BUDGET ("place up to N") rather than an exact
        count - the city gens' 600-samurai district fills are the idiom.

        `footpaths=N` lays a worn TRODDEN PATH across the district every N*step of its
        depth - before the scan, so `_fits` refuses any spot on the tread - and the quarter
        then reads as BLOCKS rather than a scatter of boxes.
        WHY (GM 2026-07-27, after settlement-review found the warrens had no circulation
        at all): a dense commoner quarter is served by narrow TRODDEN FOOTPATHS between
        the house rows - not paved streets, which were far beyond a quarter's means. The
        cities already carry `alleys` + `town_streets`; it was the UNWALLED TOWNS whose
        warrens hung straight off the trunk road with nothing between them (Hoshizora and
        Ubame both recorded zero lanes, zero alleys and zero streets).

        The path is laid FIRST rather than threaded between placed buildings, which is the
        whole point: clearance is then true by construction, instead of a path dodging
        jittered footprints and clipping one every few maps. It costs a little capacity
        (a ~30px no-build band), so a district that was exactly full may need a slightly
        bigger bbox. Default 0 keeps every existing map bit-identical - no corridor, and
        no RNG draw that could shift a single downstream spot."""
        # SCOPED (2026-08-08). The per-seat jitter below is a stream draw, so any upstream change
        # that consumed a different number of random numbers moved every building this pack seats -
        # and one moved building cascades into the gardens, groves, wells and crowns around it. This
        # was the first divergence left in a town once the pasture outline was scoped. Keyed on the
        # BBOX with rng_scope's per-key counter, so a quarter re-rolls when you move THAT quarter,
        # a second pack over the same ground still draws its own numbers, and adding a pack in one
        # quarter cannot renumber another.
        with self.rng_scope("pack", *bbox):
            x0, y0, x1, y1 = bbox
            items = list(items)
            n = 0
            gy = y0 + step / 2
            if footpaths:
                # Lay the paths BEFORE the scan, so `_fits` refuses any spot on the tread and the
                # clearance is true by construction. The first design reserved every Nth GRID ROW
                # instead, which was depth-dependent and therefore useless here: under the exact-
                # population rule these quarters are only two or three rows deep, so the reserved row
                # was never reached and the pack drew no path at all. Spacing off the bbox rather than
                # off the row counter makes the paths independent of how many houses are requested.
                _spacing = footpaths * step
                _py = y0 + _spacing
                while _py < y1 - step * 0.5:
                    # TRIM THE PATH TO GROUND THAT IS ACTUALLY FREE. A corridor only refuses spots taken
                    # AFTER it exists, so anything already standing - a district bbox routinely overlaps
                    # the road frontage placed earlier in the gen - is immune to it and the tread would be
                    # drawn straight through a shopfront. So walk the span, keep the longest clear run,
                    # and emit only if enough of it survives to read as a path rather than a stub.
                    # Clearance is scaled to the STEP because `_near_corridor` tests a building's CENTER:
                    # at a flat 15 a house sat 15px off the tread and put its footprint through it (the
                    # center-vs-footprint family again - see the skill CLAUDE.md).
                    _clr = max(20.0, step * 0.62)
                    _run: list[float] = []
                    _best: list[float] = []
                    _px = x0 + 4
                    while _px <= x1 - 4:
                        if self._fits(_px, _py, step * 0.5, step * 0.5, corridors=False):
                            _run.append(_px)
                        else:
                            if len(_run) > len(_best):
                                _best = _run
                            _run = []
                        _px += 10
                    if len(_run) > len(_best):
                        _best = _run
                    if _best and (_best[-1] - _best[0]) >= 0.4 * (x1 - x0):
                        self.lane([(_best[0], _py), (_best[-1], _py)], width=5, clearance=_clr, worn=True)
                    _py += _spacing
            while gy < y1 and items:
                gx = x0 + step / 2
                while gx < x1 and items:
                    jx, jy = random.uniform(-step * 0.28, step * 0.28), random.uniform(-step * 0.28, step * 0.28)
                    if face_streets:
                        fr, fd = self._face_street_rot(gx + jx, gy + jy)
                        if face_streets == "core":
                            if fr is not None and fd <= 76:
                                gx += step  # leave the street-facing band for shop frontage; dwellings pack the INTERIOR
                                continue
                            r = rot + random.uniform(-6, 6)  # ONLY the deep block core, set back behind the frontage line
                        elif fr is not None and fd <= 92:
                            r = fr + random.uniform(-4, 4)  # near a street: face it
                        elif face_streets == "fill":
                            r = rot + random.uniform(-6, 6)  # deep block core (e.g. tenement housing)
                        else:
                            gx += step  # businesses only line the frontage
                            continue
                    else:
                        r = rot + random.uniform(-6, 6)
                    # a scattered (non-street-facing) house still needs an UNBLOCKED door: keep the
                    # street-facing rotation when one was chosen, else pick the cardinal whose door
                    # side opens onto clear ground (doctrine 2026-07-18; skip a spot walled on all 4).
                    # RNG-NEUTRAL by construction: the prefer order starts at the pack's own base
                    # rotation and the already-drawn jitter is REUSED (no extra random draws), so a
                    # map whose scatter never actually blocks a door regenerates bit-identically to
                    # the pre-doctrine engine - the doctrine only perturbs the spots it must.
                    if not (face_streets and fr is not None and fd <= 92):
                        w_, h_ = self._dims(items[0])
                        base = (round(rot / 90) * 90) % 360
                        orot = self.open_face_rot(gx + jx, gy + jy, w_, h_, prefer=(base, (base + 180) % 360, (base + 270) % 360, (base + 90) % 360))
                        if orot is None:
                            gx += step
                            continue
                        r = orot + (r - rot)
                    if self.try_building(gx + jx, gy + jy, items[0], r):
                        items.pop(0)
                        n += 1
                    gx += step
                gy += step
            if not fill:
                self._shortfall("pack", bbox, n, items)
            return n

    def _shortfall(self: Settlement, fn: str, where: Any, placed: int, left: list[Any]) -> None:  # type: ignore[misc]
        """A placement helper SILENTLY dropping what does not fit is how authored-vs-landed
        drift happens (the 2026-07-24 town audit: Hirameki's gate market authored 12
        businesses, landed 4, and nothing said so - the "no silent caps" principle applied
        to pack/frontage). Loudly report any shortfall; the gen author decides whether to
        make room, trim the request to the ground truth, or mark the call fill=True when
        the request is deliberately a capacity budget. An unmarked warning is a standing
        TODO to make that call."""
        if left:
            want = placed + len(left)
            kinds = ", ".join(f"{k} x{c}" for k, c in Counter(left).items())
            print(f"{fn.upper()} SHORTFALL at {where}: placed {placed}/{want} (dropped {kinds})")
            # ...and RECORD it (GM 2026-08-05: "we definitely want that to be visible"). Printing
            # alone sends the one number that measures authored-vs-landed drift to a terminal
            # nobody keeps: a map shipping 88 of its 118 merchant households read exactly like one
            # that met its budget, and the only reason it was ever noticed was a perf investigation.
            # Recorded, it is reviewable after the fact and gateable in future. Deliberately NO
            # geometry key names (x/pts/poly/outline/boundary) - this is a diagnostic, not a drawn
            # feature, and every_feature_classified_for_overlap keys off exactly those names.
            self.M.setdefault("shortfalls", []).append(
                {
                    "by": fn,
                    "at": [round(float(v), 1) for v in (where if not isinstance(where[0], (list, tuple)) else [c for p in where for c in p])],
                    "placed": placed,
                    "wanted": want,
                    "dropped": kinds,
                }
            )
