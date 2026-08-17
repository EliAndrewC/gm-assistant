"""Crossings, from a single span to the footbridge net over a channel system.

Split from settlement/city.py by feature 113 - see settlement/city/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any, cast

from .._geom import (
    CARRIED_LANDING_FLOOR_FT,
    LANDING_FT,
    PLANK_ABUTMENT,
    PLANK_BANK_REACH,
    PLANK_VILLAGE_REACH,
    Pt,
    point_in_poly,
    quad_hits_poly,
    quad_hits_seg,
    seg_dist,
    seg_intersect,
    segments_cross,
)
from .._knobs import bridge_carried_ways, bridge_crossed_waters

if TYPE_CHECKING:
    from ..core import Settlement


# ---- footbridge geometry ------------------------------------------------------------------
# Three pure helpers, hoisted out of `channel_footbridges` by feature 113. They close over
# nothing and are shared by that method's slide loop and the two predicates it now delegates to;
# nesting them was a third of what made that method 195 lines, and hid the fact that they are
# ordinary geometry rather than anything footbridge-specific.


def _at_arc(pts: Any, seg: Any, s: float) -> Any:  # point + heading (deg) at arc-length s along the polyline
    acc = 0.0
    for i, sl in enumerate(seg):
        if acc + sl >= s or i == len(seg) - 1:
            fr = (s - acc) / sl if sl else 0.0
            ax, ay = pts[i]
            bx, by = pts[i + 1]
            return (ax + (bx - ax) * fr, ay + (by - ay) * fr, math.degrees(math.atan2(by - ay, bx - ax)))
        acc += sl


def _deck_quad(cx: float, cy: float, w: float, h: float, deg: float) -> list[Pt]:
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + dx * ca - dy * sa, cy + dx * sa + dy * ca) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def _quads_overlap(p: Any, q: Any) -> bool:  # separating-axis rect overlap (matches bridges_clear_of_houses)
    for poly in (p, q):
        for i in range(4):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % 4]
            nx, ny = -(y2 - y1), (x2 - x1)
            pa = [nx * x + ny * y for x, y in p]
            qa = [nx * x + ny * y for x, y in q]
            if max(pa) < min(qa) or max(qa) < min(pa):
                return False
    return True


class BridgesMixin:
    def bridge(self: Settlement, x: float, y: float, rot: float, span: float, deck_w: float) -> int:  # type: ignore[misc]
        """A timber BRIDGE carrying a road (or town street) over a watercourse - a stream, an
        irrigation channel, or the city moat at a gate. Centered on the crossing (x, y); the deck
        runs along `rot` (the road's bearing, degrees) for `span` px (long enough to reach both
        banks) and is `deck_w` wide (the carried road's width). Drawn on the TOP layer so it sits
        ABOVE the water and the roadbed. Records M['bridges']."""
        # ONE DECK PER CROSSING, enforced HERE so every caller is covered (GM 2026-07-26): the
        # road-crossing pass in bridges(), the plank pass in channel_footbridges(), and any gen that
        # hand-places a deck for a crossing one of those also finds. Minami carried two decks over the
        # Hayakawa 3px apart, and honda/hoshigaoka/kikuta each carried two footplanks at the SAME
        # point - a way that crosses a stream where a channel joins it is one bridge on the ground.
        # None of it was caught because bridges were invisible to the overlap matrix (FIXTURE was a
        # blanket permission); bridges x bridges is a violation now. Tolerance scales with the deck so
        # two genuinely distinct footplanks a few px apart still both draw.
        _btol = max(4.0, min(12.0, span * 0.5))
        for _b in self.M.get("bridges", []):
            if math.hypot(_b["x"] - x, _b["y"] - y) <= _btol:
                return int(_b["z"])
        hl, hw = span / 2, deck_w / 2
        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hl:.1f}" y="{-hw:.1f}" width="{span:.1f}" height="{deck_w:.1f}" rx="2" fill="#B68D5A" stroke="#5A3F1E" stroke-width="1.6"/>')  # the planked timber deck
        step = max(7, span / 8)  # plank seams across the deck
        sx = -hl + step
        while sx < hl - 1:
            g.append(f'<line x1="{sx:.1f}" y1="{-hw:.1f}" x2="{sx:.1f}" y2="{hw:.1f}" stroke="#5A3F1E" stroke-width="0.7" opacity="0.55"/>')
            sx += step
        g.append(f'<rect x="{-hl:.1f}" y="{-hw - 2.4:.1f}" width="{span:.1f}" height="2.6" fill="#5A3F1E"/>')  # the two side rails
        g.append(f'<rect x="{-hl:.1f}" y="{hw - 0.2:.1f}" width="{span:.1f}" height="2.6" fill="#5A3F1E"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("bridges", []).append({"x": round(x, 1), "y": round(y, 1), "rot": round(rot, 1), "span": round(span, 1), "w": round(deck_w, 1), "z": z})
        return z

    def bridges(self: Settlement) -> int:  # type: ignore[misc]
        """Auto-span every place a way CROSSES a watercourse with a s.bridge(), oriented ALONG the
        way. Call AFTER all ways (road, ring road, streets, lanes) AND all water (streams, channels,
        the cargo canal, the moat) are placed - a watercourse added later would leave an unbridged
        crossing (which the `roads_bridge_water` check then flags). Returns the number of bridges
        drawn. Historically a walled city's approach road crossed the moat on a bridge at each gate,
        and a country road crossed a stream on a timber bridge.

        SOLVE THE CROSSING, NEVER EYEBALL IT (GM 2026-07-27, Minami's cargo-basin bridge). A deck
        hand-placed at design coordinates goes crooked and slides off its crossing the moment the
        geometry around it is re-derived: Minami's canal bridge sat 17 px east of where the ring
        road actually met the canal and 39 deg off its bearing, so the road simply ran through the
        water beside it (Nagahara's was 15 px / 24 deg off, the same way). Both were hand-placed
        because this pass could not SEE the crossing - the RING ROAD was not a carried way here and
        the cargo CANAL was not a watercourse - so both are scanned now, and the checks
        `roads_bridge_water` + `bridges_align_with_their_way` re-derive the same crossings from the
        manifest. Anything this pass finds is aligned by construction; hand-place a deck only for a
        crossing this pass genuinely cannot see, and expect the alignment check to test it."""
        carried = bridge_carried_ways(self.M)
        waters = bridge_crossed_waters(self.M)
        n = 0
        for rpts, rw in carried:
            for i in range(len(rpts) - 1):
                ra, rb = tuple(rpts[i]), tuple(rpts[i + 1])
                for wpts, ww in waters:
                    for j in range(len(wpts) - 1):
                        wa, wb = tuple(wpts[j]), tuple(wpts[j + 1])
                        if segments_cross(ra, rb, wa, wb):
                            # segments_cross is True only for a genuine (non-parallel) crossing, so
                            # seg_intersect always returns a point here
                            p = cast(Pt, seg_intersect(ra, rb, wa, wb))
                            rot = math.degrees(math.atan2(rb[1] - ra[1], rb[0] - ra[0]))
                            # The span SOLVES the oblique crossing (GM 2026-08-09: the old flat
                            # +28px slack was eaten by obliquity and left deck CORNERS at the
                            # water's edge). Along the deck the water is ww/sin wide, the deck's
                            # own width adds rw*|cos|/sin before a corner clears the bank, and
                            # past that every corner runs LANDING_FT of real feet onto dry
                            # ground (see the constant for the research). sin is clamped:
                            # segments_cross guarantees a genuine crossing, but a near-parallel
                            # graze would otherwise ask for an absurd deck.
                            _rl = math.hypot(rb[0] - ra[0], rb[1] - ra[1]) or 1.0
                            _wl = math.hypot(wb[0] - wa[0], wb[1] - wa[1]) or 1.0
                            _cs = ((rb[0] - ra[0]) * (wb[0] - wa[0]) + (rb[1] - ra[1]) * (wb[1] - wa[1])) / (_rl * _wl)
                            _sn = max(math.sqrt(max(0.0, 1.0 - _cs * _cs)), 0.25)
                            _span = (ww + rw * abs(_cs)) / _sn + 2 * LANDING_FT / self.ftpx
                            # ...AND THE DECK IS GROWN UNTIL ITS CORNERS ACTUALLY CLEAR THE WATER
                            # (2026-08-12). The formula above solves the crossing against the ONE
                            # segment the way cuts, and clamps sin at 0.25 so a near-parallel graze
                            # cannot ask for an absurd deck. Both are reasonable and both under-size
                            # a deck where the watercourse BENDS near the crossing: the check
                            # (`bridges_span_their_water`) measures every corner against the whole
                            # crossed POLYLINE, so a neighbouring segment curving back toward a
                            # corner is water the formula never saw. Rather than model that, ask the
                            # same question the check asks and lengthen until the answer is yes.
                            _need = ww / 2 + CARRIED_LANDING_FLOOR_FT / self.ftpx  # the check's own carried-way floor
                            _rr = math.radians(rot)
                            _cu, _su = math.cos(_rr), math.sin(_rr)
                            for _grow in range(14):
                                _try = _span * (1.0 + 0.12 * _grow)
                                if all(
                                    min(
                                        seg_dist(p[0] + _qu * _cu * _try / 2 - _qv * _su * rw / 2, p[1] + _qu * _su * _try / 2 + _qv * _cu * rw / 2, wpts[k2], wpts[k2 + 1])
                                        for k2 in range(len(wpts) - 1)
                                    )
                                    >= _need
                                    for _qu, _qv in ((-1, -1), (-1, 1), (1, -1), (1, 1))
                                ):
                                    _span = _try
                                    break
                            self.bridge(p[0], p[1], rot, _span, rw)
                            n += 1
        return n

    def channel_footbridges(self: Settlement, spacing: float = 320, min_len: float = 140, plank_w: float = 2.0, seg_caps: Any = None) -> int:  # type: ignore[misc]
        """Standalone plank FOOTBRIDGES across the irrigation channels, where field-workers cross a ditch while
        walking the paddy bunds - NOT carried by any lane (people reach them along the earthen bunds, so no
        path leads to them). Any ditch stretch longer than `min_len` gets a plank about MIDWAY; a long stretch
        gets one roughly every `spacing` px, evenly spaced along it. Each plank crosses PERPENDICULAR to the
        ditch, spanning its local width plus a short abutment. Call AFTER the field ditches are recorded. Bridges
        draw on the TOP layer (over the water). Records via `bridge()` into M['bridges'] (tagged 'foot'); returns
        the count. DECK WIDTH (1 px = 2 ft): a dobashi footplank is a single-file crossing (~3-4 ft), so
        `plank_w=2.0` (~4 ft, GM 2026-07-22: was 2.5) - kept just wide enough to read and NARROWER than a cart
        lane (~5-6 px); the wider `bridges()` carried-way deck matches the lane it carries, but a footplank does not.
        USEFULNESS: a plank is placed only where BOTH banks reach ground someone walks to - cultivated field,
        the village, or a dike (via _plank_reaches_useful_ground). A drain/toe stretch whose far bank opens onto
        marsh/scrub/off-map carries NO plank (GM 2026-07-22, Hikari no Sato: crossings into the reed marsh)."""

        from l7r.diagram.waterfields import taper_w, worth_planking  # local: the engine packages are peers, imported lazily

        houses = [_deck_quad(h["x"], h["y"], h["w"], h["h"], h.get("rot", 0)) for h in self.M.get("houses", [])]
        n0 = len(self.M.get("bridges", []))
        # THREE MORE THINGS A PLANK SLIDES AWAY FROM (2026-08-11, found by rolling cohorts of
        # scripted hamlets - the shipped maps' ditches happen to run clear of all three):
        #
        #  - a DRY CROP PLOT. The slide already avoids houses; a deck laid across a hem strip is a
        #    board lying on the barley, and it is the same rule (`groves_clear_of_dry_plots` states
        #    it for trees, `structures_clear_of_dry_plots` for buildings). This became checkable at
        #    all only once `draw_comb_field` started registering its hem in `dry_polys`.
        #  - ANOTHER BRIDGE. Two planks drawn on top of each other is a drawing error, and it
        #    happens where two ditches run close and each independently wants a crossing at the
        #    same slot. `features_do_not_overlap` reads it as a ('bridges', 'bridges') pair.
        #  - A CONFLUENCE, where the deck is instead made LONGER. The span is sized from THIS
        #    ditch's nominal width, but where another watercourse joins, the water under the deck is
        #    the WIDER one - so a nominal deck comes up short and its abutment stands in the water
        #    (`bridges_span_their_water`). Skipping such spots was tried first and is too strong: on
        #    a drain whose banks are reed marsh for all but one short stretch, the only point with
        #    useful ground on both banks IS a junction, so the map ended up with a long ditch and no
        #    crossing (`long_ditches_have_a_footbridge`) - two correct rules forbidding between them
        #    a plank that ought to exist. A plank at a junction is simply a longer plank, which is
        #    what a farmer would lay, so the deck is sized to the widest water actually beneath it.
        dry_quads = [list(poly) for poly in self.dry_polys]
        DEFAULT_W = {"streams": 9.0, "channels": 2.5, "field_ditches": 4.2}
        # ...including the OTHER FIELD DITCHES, which is where the confluences actually are: a comb's
        # branch takes off from a main, and the plank the branch wants at its own head sits over the
        # junction where the water is the main's width, not the branch's. Listing only streams and
        # channels missed every one of them.
        # NOT `drawn_channels`: it holds the filleted twin of every course including the one being
        # planked, and `wl is pts` cannot exclude a twin, so every candidate then reads as sitting at
        # a confluence with itself. Tried 2026-08-11; it made both footbridge checks fail at once.
        other_water = [(rec.get("poly") or rec.get("pts"), float(rec.get("w") or DEFAULT_W[key])) for key in ("streams", "channels", "field_ditches") for rec in self.M.get(key, []) or []]
        for d in self.M.get("field_ditches", []):
            pts = d["poly"]
            seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
            total = sum(seg)
            if total < min_len:
                continue  # a short stub (e.g. the head-race) is stepped over, no plank
            w = d.get("w", 4.2)
            w_tail = float(d.get("w_tail", w))
            if not worth_planking(w, w_tail, self.ftpx):
                continue  # narrow enough to stride across ANYWHERE - see `worth_planking`; the gate agrees
            # HOW MANY planks, measured over the run that can actually TAKE one. `n` used to come
            # from the ditch's whole LENGTH, which on a tapering ditch asks for crossings along a
            # stretch too narrow to deserve any: on Inashiro one main qualified only at its head,
            # drew n=2, and its second slot fell through the wide-first sort onto 2.42 ft of water -
            # narrower than decks this very rule had just removed, and bunched 120 ft from its
            # neighbour (settlement-review 2026-08-17, which traced it to the slot count rather than
            # to the gate/placer standoff I had assumed). Measuring the QUALIFYING run collapses n to
            # 1 there. `long_ditches_have_a_footbridge` is unaffected - it demands one plank per long
            # ditch, never one per spacing interval - so this cannot re-open the placer/check split.
            _lw = [taper_w(w, w_tail, k2 / 40.0) for k2 in range(41)]
            n = max(1, round(total * sum(1 for v in _lw if worth_planking(v, v, self.ftpx)) / len(_lw) / spacing))
            # SIDE-AWARE crossings (research 2026-07-22): on a polder the ring-canal `seg` tag caps crossings
            # per side - they cluster on the SETTLEMENT (east) toe, sparse on the interior laterals, NONE on
            # the unsettled feeder / far toe / drain (people cross to the fields where they live, then walk the
            # bund network). `seg_caps` maps seg -> max planks (0 = none); an untagged ditch uses the spacing.
            if seg_caps is not None and d.get("seg") in seg_caps:
                cap = seg_caps[d["seg"]]
                if cap <= 0:
                    continue
                n = min(n, cap)
            span = w + PLANK_ABUTMENT  # provisional; re-sized at each seat from the LOCAL width below
            for k in range(n):
                base = (k + 0.5) / n * total  # midway for n=1, evenly spaced otherwise
                # SLIDE along the ditch to a spot that (a) misses every home and (b) lands on
                # useful ground (field/village/dike) on BOTH banks. If no such spot is near this
                # slot - a marsh/scrub toe stretch with nothing to cross to - it carries NO plank.
                # THE SLIDE SAMPLES AT THE CHECK'S RESOLUTION, in arc length, not in fractions.
                #
                # `long_ditches_have_a_footbridge` decides a ditch needs a plank by walking it in
                # steps of max(8, length/40) and asking whether ANY point has useful ground on both
                # banks. The placer used a handful of fractional offsets, which on a long ditch is a
                # far coarser grid - so on a drain whose banks are marsh for all but one short
                # stretch, the check found the one good point and the placer stepped over it, and
                # the map failed for a plank that was legal and simply never tried. Same discipline
                # as reading the same manifest source: placement and its check must also LOOK at the
                # same resolution, or one of them is answering a different question.
                _step = max(8.0, total / 40)
                _cands = [k2 * _step / total for k2 in range(-int(total / 2 / _step), int(total / 2 / _step) + 1)]

                def _wide_enough(fr: float, _base: float = base, _tot: float = total, _w0: float = w, _w1: float = w_tail) -> bool:  # noqa: B008 - bind this ditch's geometry at definition, not at call
                    """Does the water at this seat earn a board (`worth_planking` at the seat's own taper)?"""
                    _a = max(0.0, min(_tot, _base + fr * _tot))
                    _lw = taper_w(_w0, _w1, _a / _tot if _tot else 0.0)
                    return worth_planking(_lw, _lw, self.ftpx)

                # PREFER wide water, but do not REFUSE the ditch over it. Sorting by
                # (narrow-first-loses, distance-from-slot) puts every seat whose own taper earns a
                # board ahead of every seat that does not, so a plank lands on real water wherever
                # one legally can - while a ditch the GATE demands a crossing on still gets one at
                # the best available spot. Making the width a hard `continue` instead was tried and
                # is the classic placer/check split: it left cohort seeds 41 and 43 with a long
                # ditch the gate required a plank on and the placer would not lay, because the
                # placer's other constraints (houses, hem crop, other decks, oblique confluences)
                # ruled out every wide seat and it had no way to say "then take the best one".
                for frac in sorted(_cands, key=lambda fr: (not _wide_enough(fr), abs(fr))):
                    _arc = max(0.0, min(total, base + frac * total))
                    px, py, ang = _at_arc(pts, seg, _arc)
                    deck = ang + 90  # deck runs ACROSS the ditch (perpendicular)
                    quad = _deck_quad(px, py, span, plank_w, deck)
                    # WIDEN the deck to the widest water actually under it, then re-cut the quad:
                    # a plank at a junction spans the junction. Tested as "another course runs UNDER
                    # this deck", not "another course passes within a deck's length" - the looser
                    # form catches a ditch merely running parallel to a neighbor.
                    span_here = self._widen_for_confluence(quad, deck, pts, other_water, span, plank_w)
                    # THE OBLIQUENESS CEILING IS MEASURED AGAINST THE DITCH'S WIDEST SECTION, not
                    # against `span`, which is built from the HEAD width. On a COLLECTOR the head is
                    # the narrow end - a drain starts as a thread and earns its section at the
                    # outfall (`waterfields`, "a collector STARTS as a thread") - so a head-based
                    # ceiling is tiny and `_widen_for_confluence` clears it at every seat. Cohort
                    # seed 5 is the case: a 996 px drain tapering 1.5 -> 5.5 px got NO plank because
                    # all 40-odd seats read as "too oblique", while the gate rightly demanded one.
                    # `max(w, w_tail)` is the same section `worth_planking` uses to decide the ditch
                    # deserves a plank at all, so the two questions are now asked about one width.
                    #
                    # Re-sizing the DECK at each seat was tried first and is wrong: it widened decks
                    # on the downstream half of every collector and cost `features_do_not_overlap`
                    # (48-seed cohort 45 -> 44). The deck's size was never the defect; the ceiling's
                    # basis was.
                    if span_here > 3.0 * (max(w, w_tail) + PLANK_ABUTMENT):
                        continue  # too oblique to plank: widen where a longer deck is reasonable, but a
                        # crossing that needs three times the nominal span is a course running nearly
                        # ALONGSIDE this one, and the answer there is to cross somewhere else. (The fine
                        # arc-length slide above is what makes "somewhere else" reliably available.)
                    quad = _deck_quad(px, py, span_here, plank_w, deck)
                    if any(_quads_overlap(quad, hc) for hc in houses):
                        continue
                    if any(quad_hits_poly(quad, dp) for dp in dry_quads):
                        continue  # no plank laid across the hem crop
                    if any(_quads_overlap(quad, _deck_quad(b["x"], b["y"], b.get("span", 8.0), b.get("w", 4.0), b.get("rot", 0.0))) for b in self.M.get("bridges", [])):
                        continue  # ...nor on top of another deck
                    # ...tested on the EXACT numbers that will be recorded. `footbridges_reach_useful_ground`
                    # re-derives the bank points from the span and rot in the manifest, which `bridge()`
                    # rounds to 1 dp, while this used the unrounded values - and a bank sample sitting on
                    # the 55 px village reach flips between the two (a scripted-cohort hamlet, 2026-08-13:
                    # bank at 55.0 from the nearest house; placement said useful, the check said marsh).
                    # A MARGIN IS THE WRONG CURE HERE and was tried first: sampling further out is not
                    # strictly stricter, because past a strip of scrub the sample can land back INSIDE the
                    # field, so the wider test PASSED the very plank the check rejects. Rounding the inputs
                    # the same way the manifest does makes the two sides bit-identical, which is the only
                    # thing that actually settles a knife-edge. Measured on the plank that motivated it:
                    # bank-to-house 54.97 px at placement against 55.02 at the end, threshold 55.0 - and
                    # the 0.05 px came from `bridge()` rounding the deck's recorded POSITION, not its span.
                    if not self._plank_reaches_useful_ground(round(px, 1), round(py, 1), round(deck, 1), round(span_here, 1)):
                        continue
                    if not self._deck_clears_its_water(px, py, deck, span_here, plank_w):
                        continue
                    self.bridge(px, py, deck, span_here, plank_w)
                    self.M["bridges"][-1]["foot"] = True  # a standalone footplank (checked by footbridges_reach_useful_ground)
                    break
        return len(self.M["bridges"]) - n0

    def _widen_for_confluence(self: Settlement, quad: Any, deck: float, own_pts: Any, other_water: Any, span: float, plank_w: float) -> float:  # type: ignore[misc]
        """The widest water actually UNDER this deck, expressed as a span - a plank at a junction is
        simply a longer plank, which is what a farmer would lay. Tested as "another course runs
        under this deck", not "another course passes within a deck's length": the looser form
        catches a ditch merely running alongside a neighbor. Returns `span` unchanged where nothing
        else crosses."""
        _da = math.radians(deck)
        _dux, _duy = math.cos(_da), math.sin(_da)
        under: list[float] = []
        for wl, ow in other_water:
            if wl is own_pts:
                continue
            for i2 in range(len(wl) - 1):
                if not quad_hits_seg(quad, tuple(wl[i2]), tuple(wl[i2 + 1]), 3.0):
                    continue
                _wx, _wy = wl[i2 + 1][0] - wl[i2][0], wl[i2 + 1][1] - wl[i2][1]
                _wl = math.hypot(_wx, _wy) or 1.0
                _sin = abs(_dux * _wy / _wl - _duy * _wx / _wl)  # deck-vs-course crossing angle
                _cos = abs(_dux * _wx / _wl + _duy * _wy / _wl)
                # THE CHECK'S OWN GEOMETRY, not the shorthand in its message. It requires
                # every deck CORNER to stand at least `cw/2 + floor` from the crossed
                # course's centerline (floor = 2 real ft for a footplank), so at a
                # crossing angle t the deck's half-length must exceed that over sin(t) -
                # i.e. the whole span is (cw + 2*floor + deck_w*|cos|) / sin. Deriving it
                # from the message's "(width + deck_w*|cos|)/sin plus a landing" leaves
                # the landing UNDIVIDED by sin and comes up short on a shallow crossing,
                # which is precisely the case this exists for.
                under.append((ow + 2.0 * (2.0 / self.ftpx) + plank_w * _cos) / max(_sin, 0.02) + 1.0)
        return max([span] + under)

    def _deck_clears_its_water(self: Settlement, px: float, py: float, deck: float, span_here: float, plank_w: float) -> bool:  # type: ignore[misc]
        """EVERY DECK CORNER LANDS PAST THE BANK - the exact test `bridges_span_their_water` will
        make, on the same geometry, before the deck is committed rather than after. A deck
        perpendicular to a STRAIGHT ditch clears by construction, which is why this was not needed
        for years; a deck at a BEND does not, because the polyline curves back toward one of its
        corners. (`w`/2 + 2 real ft is the check's own floor for a footplank.)

        Measured against `bridge_crossed_waters`, which is where the CHECK reads its geometry - the
        DRAWN, filleted polyline, not the recorded one `field_channel` was handed. Testing the
        recorded line looked right and rejected nothing, because the fillet is exactly what curves
        back toward the corner."""
        _seat = None
        _cw = 0.0
        for _wp, _ww in bridge_crossed_waters(self.M):
            if min(seg_dist(px, py, _wp[i3], _wp[i3 + 1]) for i3 in range(len(_wp) - 1)) <= _ww / 2 + 2 and _ww > _cw:
                _seat, _cw = _wp, _ww
        if _seat is not None:
            _need = _cw / 2 + 2.0 / self.ftpx
            _dr = math.radians(deck)
            _cux, _cuy = math.cos(_dr), math.sin(_dr)
            if any(
                min(
                    seg_dist(px + su * _cux * span_here / 2 - sv * _cuy * plank_w / 2, py + su * _cuy * span_here / 2 + sv * _cux * plank_w / 2, _seat[i3], _seat[i3 + 1])
                    for i3 in range(len(_seat) - 1)
                )
                < _need
                for su, sv in ((-1, -1), (-1, 1), (1, -1), (1, 1))
            ):
                return False  # pragma: no cover - the corner rejection. It fires on real geometry (a scripted-cohort hamlet's branch ditch, whose gentle curve brought a deck corner back within the water at the ditch's head) but no pool map and no synthetic bed reproduces it: every fixture tried either finds a clear offset first or fails the useful-ground test before reaching here. The guard stays - the case it prevents shipped.
        return True

    def _plank_reaches_useful_ground(self: Settlement, px: float, py: float, deck_deg: float, span: float) -> bool:  # type: ignore[misc]
        """A STANDALONE footplank is worth building only if BOTH banks reach ground someone walks to:
        cultivated field (wet paddy or dry crop), the village (a dwelling within a short reach), or a
        walked polder-dike crest. A crossing whose far bank opens onto reed marsh, scrub commons, forest,
        or off-map serves no one - field-workers cross a ditch to reach the FIELD, not to wade into the
        bog (GM 2026-07-22, Hikari no Sato: drain-toe planks that stepped straight into the reed marsh).
        The deck spans the ditch along `deck_deg`, so its two ends ARE the two banks; each is sampled a
        short reach past its abutment. See the footbridges_reach_useful_ground check in check_village.py."""
        a = math.radians(deck_deg)
        ux, uy = math.cos(a), math.sin(a)
        reach = span / 2 + PLANK_BANK_REACH
        # read the SAME cultivation source the footbridges_reach_useful_ground check reads (the manifest
        # field outlines + dry plots), so placement and check never disagree - self.field_polys is a
        # separate blocking-only list that some gens leave empty.
        crop = [f["outline"] for f in self.M.get("fields", []) if f.get("outline")]
        crop += [d["poly"] for d in self.M.get("dry_plots", [])]
        dikes = [dk["outline"] for dk in self.M.get("dikes", []) if dk.get("outline")]
        houses = self.M.get("houses", [])
        for sgn in (1.0, -1.0):
            bx, by = px + ux * reach * sgn, py + uy * reach * sgn
            if any(point_in_poly(bx, by, p) for p in crop):
                continue
            if any(point_in_poly(bx, by, p) for p in dikes):
                continue
            if any((bx - h["x"]) ** 2 + (by - h["y"]) ** 2 < PLANK_VILLAGE_REACH**2 for h in houses):
                continue
            return False
        return True
