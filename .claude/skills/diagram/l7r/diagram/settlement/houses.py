"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import math
import random
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, cast

from ._geom import PointGrid, Pt, boxed_polys, drawn_extent, edge_dist, indexed_grid, point_in_poly, quad_hits_poly, rot_rect, seg_dist
from ._knobs import skeleton_layout

if TYPE_CHECKING:
    from .core import Settlement


class HousesMixin:
    # ---- houses
    def house(self: Settlement, cx: float, cy: float, w: float, h: float, kind: str = "plain", rot: float = 0, shed: bool = False, shed_side: str = "W") -> None:  # type: ignore[misc]
        # POSITION-SEEDED (2026-08-08). A house's wall color is a property of the house, and this
        # was the single most-executed stream draw in the engine - one per house, on every map - so
        # it moved the whole sequence for everything drawn afterwards.
        _plain = ('#C6AC76', '#BEA26C', '#C2A672', '#B89A62')
        pal = {
            "plain": (_plain[int(self._hjit(cx, cy, 13.0) * len(_plain))], '#A98C58', '#5A4326'),
            "big": ('#CFAB64', '#B08C4C', '#4E3A1E'),
            "abandoned": ('#B4AC96', '#9A917A', '#7A7058'),
        }
        light, dark, edge = pal[kind]
        ridge = '#E2CB98' if kind != "abandoned" else '#C7C0AA'
        x0, y0 = -w / 2, -h / 2
        # kura footprint (ox, oy center; sw, sh) in the house's local frame, per side. WEST = a tall block on the
        # west wall (dispersed farms, where the west is free); NORTH = a wide block on the shaded back wall
        # (nucleated farms, where the garden takes the sunnier walls). Shared by the draw + the record below.
        _sox, _soy, _ssw, _ssh = (0.0, -0.60 * h, 0.46 * w, 0.30 * h) if shed_side == "N" else (-0.64 * w, 0.0, 0.32 * w, 0.56 * h)
        # EMIT WHAT WAS PLACED (feature 121, found by settlement-review on Sawada). This rounded the
        # center to whole pixels and the rake to whole DEGREES, while the placer clears and the gate
        # measure full floats - so after all of this feature's work the drawn quad was still not the
        # tested quad, by up to ~0.5 deg of rake plus ~0.7 px of center: about 0.95 ft at a long
        # minka's corner. Nothing was at risk on any current map (the tightest lane gap is 27 ft),
        # but LANE_CLEARANCE is now DERIVED to the foot, and handing an exact derivation to a
        # renderer that rounds is how the next tightening quietly stops being true. No check can see
        # this: every check reads the manifest, never the SVG.
        g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({rot:.2f})">']
        if shed and kind == "plain":
            g.append(f'<rect x="{_sox - _ssw / 2:.1f}" y="{_soy - _ssh / 2:.1f}" width="{_ssw:.1f}" height="{_ssh:.1f}" rx="2" fill="{dark}" stroke="{edge}" stroke-width="1.1"/>')
        g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h / 2:.1f}" fill="{dark}"/>')
        g.append(f'<rect x="{x0:.1f}" y="0" width="{w}" height="{h / 2:.1f}" fill="{light}"/>')
        dash = ' stroke-dasharray="5,3"' if kind == "abandoned" else ''
        g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h}" rx="3" fill="none" stroke="{edge}" stroke-width="1.5"{dash}/>')
        g.append(f'<line x1="{-w * 0.30:.1f}" y1="0" x2="{w * 0.30:.1f}" y2="0" stroke="{ridge}" stroke-width="2"/>')
        if kind == "big":
            g.append(f'<rect x="{x0 - 1:.1f}" y="{y0 - h * 0.42:.1f}" width="{w * 0.40:.1f}" height="{h * 0.5:.1f}" rx="3" fill="{light}" stroke="{edge}" stroke-width="1.3"/>')
        if kind == "abandoned":
            g.append(f'<polygon points="{-w * 0.16:.1f},{-h * 0.16:.1f} {w * 0.16:.1f},{-h * 0.04:.1f} {-w * 0.04:.1f},{h * 0.2:.1f}" fill="#6E6452" opacity="0.7"/>')
        else:
            g.append(f'<rect x="-3.5" y="{h / 2 - 2:.1f}" width="7" height="3.3" fill="{edge}" opacity="0.85"/>')
        g.append('</g>')
        self.add(''.join(g))
        if shed and kind == "plain":  # record the attached kura so it is first-class + checkable
            th = math.radians(rot)
            self.M.setdefault("farm_sheds", []).append(
                {
                    "x": round(cx + _sox * math.cos(th) - _soy * math.sin(th), 1),
                    "y": round(cy + _sox * math.sin(th) + _soy * math.cos(th), 1),
                    "w": round(_ssw, 1),
                    "h": round(_ssh, 1),
                    "rot": round(rot, 1),
                    "of": [round(cx, 1), round(cy, 1)],
                }
            )

    def _in_blocked(self: Settlement, x: float, y: float) -> bool:  # type: ignore[misc]
        # bbox pre-filter (cached, same idea as _rect_hits): a point outside a polygon's bbox - expanded by
        # the 14px field set-back - can neither be inside it nor within 14px of an edge, so skip the O(vertices)
        # point_in_poly / edge_dist. Matters for the one big field envelope and a city's many block polys.
        # INDEXED (2026-08-03), replacing a bbox prefilter that still VISITED every polygon: 419k
        # calls and 12.9s of self time on Minami, whose block_polys accretes one entry per placed
        # homestead. Each grid's boxes carry that registry's own pad, so a zero-pad query is exact
        # and the tests below are the same ones, in the same order.
        for poly, *_ in self._keepout_index(self.field_polys, "field_keepout", 14.0).near(x, y):
            if point_in_poly(x, y, poly) or edge_dist(x, y, poly) < 14:
                return True
        for poly, *_ in self._keepout_index(self.block_polys, "block_keepout", 0.0).near(x, y):
            if point_in_poly(x, y, poly):
                return True
        for poly, *_ in self._keepout_index(self.dry_polys, "dry_keepout", 12.0).near(x, y):
            if point_in_poly(x, y, poly) or edge_dist(x, y, poly) < 12:
                return True  # dry plots are cropland: a building's whole footprint stays off them
        return any(math.hypot((x - cx) / (rx + 12), (y - cy) / (ry + 12)) < 1.0 for cx, cy, rx, ry in self.ellipses)

    def _near_corridor(self: Settlement, x: float, y: float, skip: Any = None) -> bool:  # type: ignore[misc]
        # INDEXED (2026-08-03). This walked every segment of every corridor per candidate seat -
        # 230k calls and 22.6s of self time on Minami, the biggest single cost left in that gen
        # after the well grids. The per-segment bbox test below is unchanged; the grid only decides
        # which segments are worth testing, and each segment's box already carries its clearance,
        # so a zero-pad query is exact. `skip` still works: the index carries each segment's parent
        # polyline, so a frontage row can sit against the street it fronts.
        # `skip` matches GEOMETRICALLY, not by identity (GM 2026-08-11). Identity worked only when
        # a frontage was handed the very list object the corridor was registered with - and a
        # frontage on a SUB-STRETCH of a road or street is written as a fresh two-point list, so
        # the parent way's own cleared band then refused the shops meant to line it. That silently
        # cost the pool two thirds of its commercial frontage (90 of 274 requested seats on the
        # capital; 10 of 80 on Tango's main commercial street) with a green gate, because the
        # docstring's "pass skip=<registered poly>" is a footgun nobody could see they had trodden
        # on. A corridor segment is skipped when it lies ALONG the stretch being fronted: both of
        # its ends sit within a hair of the skip polyline, so the two describe the same ground.
        # `skip` is one polyline OR several (2026-08-11): a shop row lines a street AND may cross
        # a road, and it must be excused from both cleared bands or the crossing way refuses the
        # seats either side of the junction. Nesting is detected by shape - a polyline's first
        # element is a POINT (two numbers), a list-of-polylines' first element is a polyline.
        # LEGACY PATH, verbatim, for any caller that has not opted into a dense row: `skip` is one
        # object, matched by identity-or-along exactly as before. Normalizing it to a list changed
        # the answer for a caller that passes a list of STRETCHES (Tango's twin south streets),
        # which is a shipped map - so the new shape is reached only from a dense row.
        if not getattr(self, "_dense_row", False):
            # IDENTITY match, as it always was: a corridor is skipped only when the caller passed
            # the very polyline object it was registered with. That is the footgun the dense row
            # fixes, and it is left standing here on purpose - every shipped map's fabric was drawn
            # against it, and re-rolling those is a deliberate per-map job with its own review,
            # not a side effect of the capital's gate markets.
            return any(poly is not skip and seg_dist(x, y, a, b) < clearance for poly, a, b, clearance, *_ in self._corridor_index().near(x, y))
        skips = [] if skip is None else ([skip] if (len(skip) and isinstance(skip[0], (list, tuple)) and len(skip[0]) == 2 and all(isinstance(v, (int, float)) for v in skip[0])) else list(skip))
        skips = [q for q in skips if q is not None and len(q) >= 2]

        def _along(a: Pt, b: Pt) -> bool:
            # SYMMETRIC containment (2026-08-11). Testing only "the fronted stretch lies on this
            # segment" covers a short row on a long straight road and nothing else: a road that
            # BENDS inside the fronted stretch, or a stretch spanning two segments, matched no
            # single segment and so the way's own cleared band refused the shops meant to line
            # it - 325 refusals on the capital's Imperial road alone. A segment counts as running
            # ALONG the stretch if either contains the other: both stretch ends near the segment,
            # or the segment's own midpoint near the stretch AND the two pointing the same way
            # (a crossing street passes the midpoint test and must still refuse).
            for poly in skips:
                if all(seg_dist(q[0], q[1], a, b) <= 3.0 for q in poly):
                    return True
                mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
                if min(seg_dist(mx, my, poly[k], poly[k + 1]) for k in range(len(poly) - 1)) > 3.0:
                    continue
                sl = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
                ux, uy = (b[0] - a[0]) / sl, (b[1] - a[1]) / sl
                for k in range(len(poly) - 1):
                    px_, py_ = poly[k + 1][0] - poly[k][0], poly[k + 1][1] - poly[k][1]
                    pl = math.hypot(px_, py_) or 1.0
                    if abs(ux * px_ / pl + uy * py_ / pl) >= 0.990:  # within ~8 degrees, either sense
                        return True
            return False

        # no `if skips:` branch: a dense row always carries at least the street it fronts, and
        # _along answers False for an empty skip list anyway, so the guard was unreachable.
        return any(all(poly is not q for q in skips) and not _along(a, b) and seg_dist(x, y, a, b) < clearance for poly, a, b, clearance, *_ in self._corridor_index().near(x, y))

    def _corridor_index(self: Settlement) -> PointGrid:  # type: ignore[misc]
        def build(lst: Any) -> PointGrid:
            grid = PointGrid()
            grid.extend(
                (poly, poly[k], poly[k + 1], cl, min(poly[k][0], poly[k + 1][0]) - cl, min(poly[k][1], poly[k + 1][1]) - cl, max(poly[k][0], poly[k + 1][0]) + cl, max(poly[k][1], poly[k + 1][1]) + cl)
                for poly, cl in lst
                for k in range(len(poly) - 1)
            )
            return grid

        return indexed_grid(self.corridors, "corridor_segs", build)

    def _keepout_index(self: Settlement, polys: Any, key: str, pad: float) -> PointGrid:  # type: ignore[misc]
        """The no-build polygons of `polys` indexed by their bbox, expanded by `pad` so a zero-pad
        query is exact for a rule that also tests `edge_dist(...) < pad`."""

        def build(lst: Any) -> PointGrid:
            grid = PointGrid()
            grid.extend(boxed_polys(lst, pad))
            return grid

        return indexed_grid(polys, key, build)

    def _hard_ground(self: Settlement) -> list[Any]:  # type: ignore[misc]
        """Every HARD no-build polygon, read from the MANIFEST plus anything a gen registered by hand.

        Manifest-sourced on purpose. The first cut kept a `hard_polys` registry that `draw_comb_field`
        populated - and it was EMPTY on any map whose field is drawn by a different path (the polder
        and contour archetypes have their own), so the rule silently did nothing there. Reading the
        drawn record instead makes it order-independent and impossible for a gen to forget: the same
        placement-and-check-read-the-same-source doctrine the footbridges taught us. Cached on the
        record counts, since this is called once per placement candidate."""
        dp, fd = self.M.get("dry_plots", []) or [], self.M.get("field_ditches", []) or []
        key = (len(dp), len(fd), len(self.hard_polys))
        if self._hard_cache_key == key:
            return self._hard_cache
        out: list[Any] = [list(self.hard_polys)[i] for i in range(len(self.hard_polys))]
        out += [[(q[0], q[1]) for q in d["poly"]] for d in dp if d.get("poly") and len(d["poly"]) >= 3]
        for ch in fd:
            pts = ch.get("poly") or ch.get("pts")
            if not pts:
                continue  # pragma: no cover - defensive: every ditch carries a path
            hw = float(ch.get("w") or 1.5) / 2 + 2.0
            for k in range(len(pts) - 1):
                ax, ay = pts[k]
                bx, by = pts[k + 1]
                ln = math.hypot(bx - ax, by - ay) or 1.0
                nx, ny = -(by - ay) / ln * hw, (bx - ax) / ln * hw
                out.append([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
        self._hard_cache_key: tuple[int, int, int] | None = key
        self._hard_cache = out
        return out

    def _hard_clear(self: Settlement, x: float, y: float, w: float, h: float) -> bool:  # type: ignore[misc]
        """Is this footprint clear of HARD no-build ground (crop, pond, bog, a field's own ditches)?

        Factored out of `_fits` because placement is not the only moment that needs it:
        `_solve_homestead` NUDGES a farmstead after it has already passed `_fits`, to make room for
        its yard, garden and grove - and nothing re-tested the moved position, so a steading that
        genuinely cleared every keep-out where it was placed could be shifted onto a ditch or a hem
        plot afterwards. That was the last root cause behind the overlap matrix's residue."""
        hard = self._hard_ground()
        if not hard:
            return True
        # ROTATION ALLOWANCE. `_fits` is called before a farmhouse is given its small random tilt
        # (+/-5 deg), so the box tested here is axis-aligned while the box DRAWN and RECORDED is
        # rotated - and a rotated rect reaches further on both axes than its unrotated self. Testing
        # the swept extent closes that gap; without it a steading clears at placement and laps a hem
        # plot once tilted, which is exactly one of the defects the overlap matrix kept reporting.
        _th = math.radians(5.0)
        w = w * math.cos(_th) + h * math.sin(_th)
        h = w * math.sin(_th) + h * math.cos(_th)
        fp = [(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)]
        fx0, fy0, fx1, fy1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
        for hp, (hx0, hy0, hx1, hy1) in zip(hard, self._poly_bboxes(hard), strict=False):
            if fx1 < hx0 or fx0 > hx1 or fy1 < hy0 or fy0 > hy1:
                continue
            if quad_hits_poly(fp, hp):
                return False
        return True

    def _record_tread(self: Settlement, pts: Any, half: float) -> None:  # type: ignore[misc]
        """Register a way's DRAWN tread, so `_fits` can keep whole footprints off it (see `_on_a_tread`).

        ONLY `lane` calls this today, and the scope is a deliberate decision rather than an
        oversight. WATER (streams, channels, canals, the moat, the aqueduct) is out because its
        keep-out is `hard_polys`, which is already footprint-tested, and so are the BARRIERS (wall,
        city wall, ward fence), whose corridors are a standoff rather than a surface anything is
        drawn on. The other TRAFFICKED ways - street, alley, road, ring road, towpath - were tried
        (2026-08-12) and reverted the same day: each of them already inflates its corridor by a
        half-diagonal's worth of margin precisely to cover this gap by hand, so the tread test
        changes no verdict they were getting wrong, and the extra tightening cost Tango a public
        well, tipping `city_well_density_sufficient` into the documented well-versus-collision-
        circle squeeze (this skill's CLAUDE.md, "The collision circle is now blocking FEATURES").
        Extending the registry is one `_record_tread` call per way plus a pool re-roll with a
        `settlement-review` per map - a job, not a side effect. Do it when the collision circle is
        replaced by a real footprint test, which frees the ground those wells need."""
        self.treads.append(([(float(q[0]), float(q[1])) for q in pts], float(half), pts))

    def _on_a_tread(self: Settlement, x: float, y: float, w: float, h: float, skip: Any = None, rot: float = 0.0) -> bool:  # type: ignore[misc]
        """Would a building of this size, at this spot, have any CORNER on a way's drawn tread?

        THE DEBT THIS PAYS (this skill's CLAUDE.md, "placement tests a different footprint than the
        one drawn"): `_near_corridor` tests a candidate's CENTER against a way's soft clearance, so
        a building whose drawn footprint is wider than the placer assumed can stand a legal distance
        off by its center and still put a corner on the road. Measured: a well-off farmhouse (the
        minka's length varies to 1.35x) ended 2.4 px from a track's centreline with its center a
        legal 34 px away, which `houses_clear_of_lanes` reports as a house standing in the lane.

        The two tests are kept SEPARATE on purpose. Footprint-testing the whole clearance was tried
        once for `block_polys` and reverted, because a clearance is slack that a footprint routinely
        overhangs by a few px; the TREAD is not slack. So the clearance keeps its center test and
        the tread gets an exact one, with the same 2 px hair `houses_clear_of_lanes` allows.

        `rot` IS THE FOOTPRINT (feature 121). This used to pass 0.0 unconditionally, which made the
        "exact" test axis-aligned - so it measured a square-on rect while the map drew a raked one,
        the very substitution the paragraph above is about. It defaults to 0.0 because most callers
        seat something genuinely unrotated; a caller that knows its rake passes it, and the bundle
        placer gets it from `_house_rot`. GAP VERDICT family (this skill's dev/placement.md, "CENTER
        vs FOOTPRINT"): real rotated corners, never a center, never a circumscribed radius."""
        if not self.treads:
            return False
        quad = rot_rect(x, y, w, h, rot)
        corners = [*quad, (x, y)]
        return any(not self._tread_skipped(orig, skip) and any(seg_dist(qx, qy, tp[i], tp[i + 1]) < half + 2.0 for qx, qy in corners for i in range(len(tp) - 1)) for tp, half, orig in self.treads)

    def _tread_skipped(self: Settlement, poly: Any, skip: Any) -> bool:  # type: ignore[misc]
        """Is this tread the way the caller is FRONTING, and so exempt?

        `_near_corridor` has excused the fronted way since frontage rows existed, and its own notes
        record what happens when a skip is matched too narrowly: a frontage written as a fresh
        two-point list over a sub-stretch of a street stopped matching by identity and the street's
        own band refused the shops meant to line it - two thirds of the pool's commercial frontage,
        silently. So this matches the same way that one does: identity OR geometry, with either
        polyline allowed to contain the other, since a fronted stretch may be shorter than the way
        or span several of its segments."""
        if skip is None:
            return False
        nested = bool(len(skip)) and isinstance(skip[0], (list, tuple)) and len(skip[0]) == 2 and all(isinstance(v, (int, float)) for v in skip[0])
        for q in [skip] if nested else list(skip):
            if q is poly:
                return True
            if q is None or len(q) < 2 or len(poly) < 2:
                continue
            if all(min(seg_dist(pt[0], pt[1], q[k], q[k + 1]) for k in range(len(q) - 1)) <= 3.0 for pt in poly):
                return True
            if all(min(seg_dist(pt[0], pt[1], poly[k], poly[k + 1]) for k in range(len(poly) - 1)) <= 3.0 for pt in q):
                return True
        return False

    def _fits(  # type: ignore[misc]
        self: Settlement, x: float, y: float, w: float, h: float, skip: Any = None, corridors: bool = True, row_mates: Any = None, row_axis: Any = None, disc: bool = False, rot: float | None = None
    ) -> bool:
        if x < 55 or x > self.W - 55 or y < 88 or y > self.H - 26:  # keep clear of edges + title
            return False
        if self.bound and not point_in_poly(x, y, self.bound):  # stay inside a bounding ring (city wall)
            return False
        if self._in_blocked(x, y) or (corridors and self._near_corridor(x, y, skip)):
            return False
        if corridors and self._on_a_tread(x, y, w, h, skip):
            return False
        if not self._hard_clear(x, y, w, h):
            return False
        # INDEXED (2026-08-04), and the history is worth the paragraph. These two scans are
        # O(placed) per candidate seat - 58M hypot() calls on Minami - and indexing them was tried
        # on 2026-08-03 and REVERTED: an incremental index assumed `placed` was append-only, two
        # sites rebind it to a shorter filtered list (search for "lift own reservation" and "drop
        # the un-appurtenanced farmhouse"), and the stale index cost Minami and Nagahara every
        # garden and farm shed. What makes it safe now is `Indexed`, which was built for that
        # lesson: the registry versions ITSELF and carries its own index, so a rebind cannot be
        # missed - the filtered copies below are Indexed too, and each starts with an empty cache.
        # ROW MATES ARE MEASURED EDGE TO EDGE (GM 2026-08-11). The circumscribed circle is
        # rotation-safe and load-bearing everywhere else (this skill's CLAUDE.md, "CENTER vs
        # FOOTPRINT", item 2), but it forces a 48x32 shopfront 62px from its neighbor where the
        # true touching distance is 48 - so a frontage asking for a 22px pitch placed every third
        # seat and a market row drew at a third of its density. A shop row is the one case where
        # the exception is safe: the buildings are AXIS-ALIGNED to the way they front and sit in a
        # straight line, so an axis-aligned edge gap is exact, not an approximation. Only the
        # row's own previously-placed seats are measured this way; everything else keeps the circle.
        # A WELLHEAD IS A DISC, so its own reach is its RADIUS, not the half-diagonal of the
        # probe box around it (2026-08-11). The circumscribed circle is the documented
        # over-restriction in this skill's CLAUDE.md ("CENTER vs FOOTPRINT" item 2); for a round
        # feature it is not an approximation anyone has to live with - min(w, h) / 2 is EXACT, and
        # for a 16 px probe that is 8 px of reach instead of 11.3. This is the one case that can be
        # made exact without first solving the rotated-footprint problem, and it is the case that
        # was blocking the capital: open_seat refused a wellhead at 12, 10 and 8 px in two blocks
        # that the well-density rule says need one.
        r = (min(w, h) / 2) if disc else (math.hypot(w, h) / 2)
        # THE CANDIDATE'S OWN DRAWN EXTENT, when the caller knows its rake (feature 121). `None`
        # means UNKNOWN, not "zero": a caller that does not say keeps the circumscribed circle,
        # because assuming axis-aligned for a candidate the map draws raked would under-state it.
        _cw, _ch = drawn_extent(w, h, rot) if rot is not None and not disc else (None, None)
        _mates = {(round(m[0], 2), round(m[1], 2)) for m in (row_mates or ())}
        _ax = row_axis or (1.0, 0.0)
        # the angle that matters is the seat's rotation RELATIVE TO THE ROW's bearing, not its
        # absolute rot: a shop fronting a north-south sando is drawn at -90 deg, and measuring
        # its reach with the absolute angle returns its depth where the row needs its width
        _rel = math.radians(getattr(self, "_row_rot", 0.0)) - math.atan2(_ax[1], _ax[0])
        _along = abs(w * math.cos(_rel)) + abs(h * math.sin(_rel))  # the seat's reach ALONG the row
        for px, py, pw, ph, _pw_drawn, _ph_drawn, *_ in self._reach_index(self.placed, "placed_reach").near(x, y, r):
            if (round(px, 2), round(py, 2)) in _mates:
                # SAME FILE ONLY. A both=True row alternates sides of the street, so a seat's
                # immediate mate is often its twin ACROSS the way - zero distance along the row and
                # no business constraining it. Compare only mates on this side (the across-row
                # offset is within a footprint depth); anything further across is a different file.
                _d_along = abs((x - px) * _ax[0] + (y - py) * _ax[1])
                _d_across = abs((x - px) * -_ax[1] + (y - py) * _ax[0])
                _mate_along = abs(pw * math.cos(_rel)) + abs(ph * math.sin(_rel))
                if _d_across < (max(w, h) + max(pw, ph)) / 2 and _d_along < (_along + _mate_along) / 2 + 1.5:
                    return False
                continue
            # EXACT BOX when BOTH sides have declared what they draw; the circumscribed circle
            # otherwise. The circle refuses seats nothing occupies - measured on a provincial city,
            # 38.7% of all refusals - but it is rotation-invariant, and that invariance is what has
            # been covering for placement dimensions that ignore rake, so it may only be given up
            # where the real extent is known on both sides.
            if _cw is not None and _pw_drawn is not None:
                if abs(x - px) < (_cw + _pw_drawn) / 2 + 4 and abs(y - py) < (_ch + _ph_drawn) / 2 + 4:
                    return False
            elif math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 4:
                return False
        return all(math.hypot(x - gx, y - gy) >= r + math.hypot(gw, gh) / 2 + 4 for gx, gy, gw, gh, *_ in self._reach_index(self.grove_rects, "grove_reach").near(x, y, r))

    @staticmethod
    def _reach_boxed(entries: Any) -> Iterator[Any]:
        """(x, y, w, h) footprints boxed by their COLLISION REACH - the half-diagonal `_fits`
        measures against, plus its 4px. Boxing by reach means a query pads by the CANDIDATE's own
        radius alone: anything that could collide has the query point inside its reach box widened
        by r, so it shares a cell with the query span and is never pruned away.

        THE REACH BOX KEEPS THE HALF-DIAGONAL even though the verdict no longer does (feature 121).
        It is a PREFILTER: over-stating an extent can only admit a pair the exact test then rejects,
        while under-stating one starts rejecting before the exact test runs - the index would be
        deciding. Tightening this to match `drawn_extent` would look like a tidy-up and would be a
        bug. (specs/121-placer-drawn-footprint/contracts/placement.md, C1.)

        AN ENTRY MAY DECLARE ITS DRAWN EXTENT, as a trailing `(ew, eh)`. Declaring it opts that
        entry into the exact box verdict; a plain 4-tuple keeps the circle, unchanged. That is
        deliberate rather than a migration half-done: an entry whose stored `w`/`h` is the UNROTATED
        size of a feature the map draws raked would silently under-state itself under a box test,
        and a 90-degree building is the case where that is worst. Opt-in means a site nobody has
        checked cannot become an overlap - it just keeps today's conservative circle.
        `PointGrid` reads the box as the LAST FOUR fields, so the declaration rides in front of it."""
        for px, py, pw, ph, *decl in entries:
            rr = math.hypot(pw, ph) / 2 + 4
            ew, eh = (decl[0], decl[1]) if len(decl) >= 2 else (None, None)
            yield (px, py, pw, ph, ew, eh, px - rr, py - rr, px + rr, py + rr)

    def _reach_index(self: Settlement, registry: Any, key: str) -> PointGrid:  # type: ignore[misc]
        def build(lst: Any) -> PointGrid:
            grid = PointGrid()
            grid.extend(self._reach_boxed(lst))
            return grid

        def add(grid: PointGrid, tail: Any) -> None:
            grid.extend(self._reach_boxed(tail))

        return indexed_grid(registry, key, build, add)

    def frontage(  # type: ignore[misc]
        self: Settlement,
        street: Any,
        items: Any,
        width: float = 24,
        setback: float = 10,
        spacing: float = 58,
        both: bool = True,
        rows: int = 1,
        rowgap: float = 9,
        jitter: float = 4,
        skip: Any = None,
        fill: bool = False,
        dense: bool = False,
    ) -> int:
        """Place buildings in row(s) along a street, each rotated so its FRONTAGE faces the
        street (shophouses lining the road). rows=2 stacks a second row BACK-TO-BACK behind the
        front one, facing AWAY from the street (GM doctrine 2026-07-18: a door opens onto open
        ground, never into the back row ahead of it - the rear row fronts the back lane/block
        interior, the real ura-dana pattern). Sits against the fronted street (skips that
        street's own corridor - pass skip=<registered poly> when fronting a sub-stretch of a
        longer road) but respects walls, other streets, fields, and collisions."""
        # SCOPED (2026-08-08): the per-building rot jitter below was the LAST root cause of a town
        # re-rolling. Its seats were already stable once pack was scoped, but a different rake gives a
        # different footprint, which changes what fits beside it - and the cascade ran through every
        # house, well, garden and crown on the map. Keyed on the street run it fronts.
        with self.rng_scope("frontage", len(street), street[0][0], street[0][1], street[-1][0], street[-1][1]):
            # the fronted street is ALWAYS skipped, and a caller's skip is ADDED to it, never
            # substituted for it (2026-08-11): `skip=ROAD` used to REPLACE the street, so a row
            # lining a street that crosses the Imperial road was excused from the road's band and
            # then refused by the band of the very street it was fronting.
            # DENSE (2026-08-11, GM: "is that the correct amount of space between gate market
            # buildings?"): a machiya row is a CONTINUOUS street wall - shops share party walls and
            # the row reads as one frontage, not a dotted line of freestanding boxes. Three things
            # change together, and all three are opt-in because each one re-rolls any map that
            # takes it: row mates are measured edge-to-edge along the row's own axis instead of by
            # the rotation-invariant collision circle (which forces a 46x28 shop 57.8 px from its
            # neighbor where the true touching distance is 28); the fronted street is skipped
            # ALONGSIDE the caller's skip rather than replaced by it; and a corridor segment counts
            # as running along the stretch if EITHER contains the other, so a bending road no
            # longer refuses the shops meant to line it. Default off keeps every shipped map
            # byte-identical - the same bargain footpaths=0 struck.
            self._dense_row = dense
            skip = ([street] if skip is None else [street, skip]) if dense else (skip if skip is not None else street)
            items = list(items)
            seg = [math.hypot(street[i + 1][0] - street[i][0], street[i + 1][1] - street[i][1]) for i in range(len(street) - 1)]
            total = sum(seg)
            sh = width / 2
            if dense:
                # DERIVE the standoff from the way's OWN registered band, do not trust the caller's
                # `width` (GM 2026-08-11: "the gate market buildings are a surprising distance from
                # the road... they look to be dozens of feet back"). Every gen passed width=8 while
                # the ways it fronted were two and three times that, so `setback` had to absorb the
                # difference by eye - which is why the same setback number put one row on the verge
                # and another in the roadbed, and why the markets sat 45-63 ft back. Measured from
                # the band, a setback means what it says: the width of the verge.
                # the way's DRAWN width, not its cleared band: the band is a keep-out for everything
                # ELSE, and the row lining the way is precisely what it does not apply to (that is
                # what the skip is for). Measuring the verge from the band put the markets 60 ft
                # back - the same defect one step further out.
                # test EVERY vertex of the stretch, not its midpoint: a row lining a road that
                # bends is written as a chord, whose midpoint can sit 26 px off the roadway even
                # though both ends are on it - which is how the north gate market derived nothing.
                _probe = [(float(q[0]), float(q[1])) for q in street]
                _mid = _probe[len(_probe) // 2]
                # a ROAD carries a SHOULDER the street does not: a highway's verge is the drained
                # strip carts pull onto, and a shopfront built to the paved edge of one stands in
                # the traffic. So a row fronting a road stands off by half its width PLUS the
                # shoulder; a row fronting a street sits at the kerb, which is the machiya norm.
                # the PRIMARY road is recorded under its own key as a bare polyline, not in
                # M["roads"] - so a row fronting it derived nothing and sat in the roadbed (the
                # north gate market, 2026-08-11). Fold it in with its own width.
                _prim = self.M.get("road") or []
                if len(_prim) >= 2 and any(seg_dist(q[0], q[1], _prim[k], _prim[k + 1]) <= 8.0 for q in _probe for k in range(len(_prim) - 1)):
                    sh = max(sh, float(self.M.get("road_width", self.px(26))) / 2.0 + self.px(18))
                _wide = [
                    float(r.get("w") or r.get("width") or 0) + (self.px(18) if key == "roads" else 0.0)
                    for key in ("roads", "streets", "town_streets", "lanes", "alleys")
                    for r in (self.M.get(key) or [])
                    if isinstance(r, dict) and r.get("pts") and any(seg_dist(q[0], q[1], r["pts"][k], r["pts"][k + 1]) <= 8.0 for q in _probe for k in range(len(r["pts"]) - 1))
                ]
                if _wide:
                    sh = max(sh, max(_wide) / 2.0)

            def at(d: float) -> tuple[float, float, float, float]:
                acc: float = 0
                for i, sl in enumerate(seg):
                    if sl and acc + sl >= d:
                        f = (d - acc) / sl
                        return (
                            street[i][0] + (street[i + 1][0] - street[i][0]) * f,
                            street[i][1] + (street[i + 1][1] - street[i][1]) * f,
                            (street[i + 1][0] - street[i][0]) / sl,
                            (street[i + 1][1] - street[i][1]) / sl,
                        )
                    acc += sl
                i = len(seg) - 1  # pragma: no cover
                sl = seg[i] or 1  # pragma: no cover
                return (
                    street[-1][0],
                    street[-1][1],
                    (street[-1][0] - street[-2][0]) / sl,  # pragma: no cover
                    (street[-1][1] - street[-2][1]) / sl,
                )  # defensive: while-guard keeps d < total, so a segment always matches

            placed = 0
            row: list[tuple[float, float, float, float]] = []
            mates: list[tuple[float, float]] = []  # this row's own seats - measured edge to edge, not by circle
            d = spacing * 0.55
            sides = [1, -1] if both else [1]
            while d < total and items:
                x, y, tx, ty = at(d)
                for s in sides:
                    nx, ny = -ty * s, tx * s  # outward normal (street -> building)
                    base_rot = math.degrees(math.atan2(nx, -ny))  # frontage faces the street
                    depth = sh + setback
                    for ri in range(rows):
                        if not items:
                            break
                        kind = items[0]
                        w, h = self._dims(kind)
                        off = depth + h / 2
                        bx, by = x + nx * off, y + ny * off
                        # rear rows flip 180: back-to-back with the row ahead, door onto the
                        # back lane - never into the front row's rear wall. building() may REFUSE
                        # the seat (a commoner unit inside a samurai ward); the station then ends
                        # its rows there, exactly as an unfit seat does.
                        self._row_rot = base_rot
                        if self._fits(bx, by, w, h, skip=skip, row_mates=(mates if dense else None), row_axis=(tx, ty)) and self.building(
                            bx, by, w, h, kind, base_rot + (180 if ri % 2 else 0) + random.uniform(-jitter, jitter)
                        ):
                            row.append((bx - w / 2, by - h / 2, bx + w / 2, by + h / 2))
                            mates.append((bx, by))
                            items.pop(0)
                            placed += 1
                            depth = off + h / 2 + rowgap  # next row sits behind this one
                        else:
                            break
                d += spacing
            # the row's own extent, for `place_caption` - a market row is captioned as ONE feature, and
            # asking the gen script to hand-copy the bounding numbers is how a caption drifts off its
            # subject when the row is later re-laid (which is exactly what happened to Tango's two
            # "gate market" captions). Cleared when nothing was placed, so a stale box can never be read.
            self.frontage_box = (min(b[0] for b in row), min(b[1] for b in row), max(b[2] for b in row), max(b[3] for b in row)) if row else None
            # ...and the row's AXIS, for a caption that names the RUN rather than one shopfront
            # (`s.label(..., rot=s.frontage_rot, linear=True)`; GM 2026-08-08, "merchant houses &
            # shops" set level over storefronts that each tilt to a -27deg road). A frontage row has no
            # rotation of its own - it IS the street it fronts - so the axis is the street's tangent at
            # the run's arc-length midpoint, read from the street rather than hand-copied off it, which
            # is the same reason `frontage_box` exists. `linear`, because a row of shopfronts is a LINE.
            if row:
                tan_ = at(total / 2)
                self.frontage_rot = math.degrees(math.atan2(tan_[3], tan_[2]))
            else:
                self.frontage_rot = 0.0
            if not fill:
                self._shortfall("frontage", (street[0], street[-1]), placed, items)
            self._dense_row = False  # never let a later placer inherit this run's relaxation
            return placed

    @staticmethod
    def _hjit(x: float, y: float, salt: float) -> float:
        """Deterministic per-position pseudo-random in [0,1) from (x,y,salt) - jitters a homestead's parts
        (house aspect, garden/yard size + shape) WITHOUT a global RNG draw, so it never ripples other
        placement or household counts (position-seeded, exactly like the wealth tier). Real villages were
        never rows of copy-pasted identical farmsteads; this gives each one its own proportions."""
        v = math.sin(x * 12.9898 + y * 4.1414 + salt * 7.373) * 43758.5453
        return v - math.floor(v)

    def _house_rot(self: Settlement, cx: float, cy: float) -> float:  # type: ignore[misc]
        """The rake a farmhouse seated at (cx, cy) will be DRAWN at, in degrees.

        ONE DEFINITION, because the placer and the renderer must not each have their own (feature
        121). This expression used to be written out at both farmhouse record sites, and the bundle
        placer had no third copy at all - it cleared an AXIS-ALIGNED rect and the map then drew the
        house raked, which is the whole of the drawn-versus-placed divergence. Measured on
        pool/hamlets/inashiro.json: the bundle's position and size match the drawn record to four
        decimal places, and the rake alone pushes a corner up to 2.56 px outside the rect that was
        cleared - which is the 2.4 px `_on_a_tread`'s own docstring reports.

        POSITION-SEEDED, and that is what makes the fix possible: the rake is a pure function of the
        seat's coordinates (so it never ripples other placement - see `_hjit`), and therefore the
        placer can know the exact quad it is going to draw BEFORE it commits to the seat. Nothing
        about when rotation is decided had to change."""
        return self._hjit(cx, cy, 11.0) * 10.0 - 5.0

    def _quad(self: Settlement, cx: float, cy: float, w: float, h: float, jit: float, salt: float) -> list[Pt]:  # type: ignore[misc]
        """A slightly-IRREGULAR 4-sided polygon INSCRIBED in the (cx,cy,w,h) rect: each corner is pulled
        INWARD by a deterministic, position-seeded fraction (0..jit of the half-span), so the footprint loses
        its perfect 90-degree corners while staying ENTIRELY within its reserved rect - so it can never create
        a new overlap the rect-based placement/checks didn't already clear. Real dooryard plots were bounded by
        paths, walls, and awkward soil, not surveyed to a clean rectangle. `jit` sets how irregular: a garden
        gets more (a hand-worked bed), a threshing yard less (a swept work surface stays near-square). Returns
        the 4 corners [NW, NE, SE, SW] as (x, y) tuples."""
        hw, hh = w / 2.0, h / 2.0
        out: list[Pt] = []
        for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):  # NW, NE, SE, SW
            jx = self._hjit(cx, cy, salt + i * 0.19) * jit  # each corner its own inward pull
            jy = self._hjit(cx, cy, salt + i * 0.19 + 0.5) * jit
            out.append((cx + sx * hw * (1.0 - jx), cy + sy * hh * (1.0 - jy)))
        return out

    def _toscale(self: Settlement) -> bool:  # type: ignore[misc]
        """Whether this map uses the to-scale HOMESTEAD BUNDLE (house + grove + yard + garden as one packed
        unit, dimensions in FEET drawn at the map's `ftpx`) vs the legacy house-first path + urban glyphs.
        Every VILLAGE does; a HAMLET opts in with `meta(toscale=True)` (village 2 ft/px, hamlet 1). Every POOL
        map is now to-scale (Moritono was the last legacy hamlet, redone water-first); the legacy house-first
        path is kept as a fallback, covered by `test_legacy_dispersed_farmstead_path_still_covered`
        in `tests/settlement/`. Kept as one predicate so every to-scale gate stays in sync."""
        m = self.M["meta"]
        return cast(bool, m.get("toscale", m.get("scale") == "village"))

    def try_place(self: Settlement, x: float, y: float, kind: str, role: Any = None, size: Any = None) -> bool:  # type: ignore[misc]
        """Place one farmhouse. VILLAGES + HAMLETS + TOWNS use the to-scale HOMESTEAD BUNDLE (house + grove/
        garden + yard, reserved and packed as ONE unit; towns run the NUCLEATED form). CITIES keep the
        shipped house-first path until their own to-scale conversion. `size=(w,h)` overrides the kind's default footprint (base FEET) so
        farmhouses can be individually sized - e.g. a headman is just a LARGER plain farmhouse."""
        if self._toscale():
            return self._try_place_bundle(x, y, kind, role, size)
        return self._try_place_legacy(x, y, kind, role)

    def _try_place_bundle(self: Settlement, x: float, y: float, kind: str, role: Any = None, size: Any = None) -> bool:  # type: ignore[misc]
        # a farmhouse shares the MAP'S building grain (bscale): at village/hamlet scale bscale is
        # 1.0 (full size), but a town/city compresses its urban buildings, and a peasant farmhouse
        # must not render LARGER than the samurai and merchant houses inside the walls - so it
        # scales down by the same factor.
        if kind == "abandoned":  # a lone derelict ruin - no homestead bundle
            w, h = self.px(46), self.px(28)  # the 46x28 ft minka, at this map's ft/px
            if not self._fits(x, y, w, h):
                return False
            self.placed.append((x, y, w, h))
            # POSITION-SEEDED, not a stream draw (2026-08-08): a farmhouse's rake is a property of
            # the house, not of how many houses preceded it. See _hjit - "so it never ripples other
            # placement or household counts" - which is the convention this line was missing.
            rec = {"x": x, "y": y, "w": w, "h": h, "kind": kind, "rot": self._house_rot(x, y), "role": role, "shed": False, "wealth": 1.0}
            self.M["houses"].append(rec)
            self._pending_farmsteads.append(rec)
            return True
        # TO-SCALE HOMESTEAD BUNDLE: an occupied farmstead is placed as ONE unit - house + windward grove +
        # threshing yard + dooryard garden - reserved and overlap-checked together so the grove always keeps
        # its ~6:1 room (the fix for groves never reaching target under end-reconciliation). Dimensions are in
        # FEET, drawn at this map's ftpx (village 2 ft/px, hamlet 1): the plain house is the 46x28 ft 8:5 minka
        # (px(46) = 23px at 2 ft/px). A modest, position-seeded wealth tier scales the whole bundle. See
        # settlements.md 'To-scale villages'.
        if size is not None:  # explicit footprint in FEET (e.g. a larger headman)
            wf, hw, hh = 1.0, self.px(size[0]), self.px(size[1])
        elif getattr(self, "_nucleated", False):
            # a minka grew by adding BAYS (ken) along the ridge, so a bigger farmhouse is LONGER far more
            # than it is wider (the roof span caps the depth) - vary length a lot, depth only a little, so
            # houses are individually proportioned (some long, some near-square) but always within the
            # ~1.3-2.5:1 minka norm, never uniformly scaled copies. Position-seeded (no RNG ripple).
            wf = 1.0
            hw = self.px(46) * (0.85 + self._hjit(x, y, 1.0) * 0.5)  # length factor [0.85, 1.35]
            hh = self.px(28) * (0.90 + self._hjit(x, y, 2.0) * 0.2)  # depth factor  [0.90, 1.10]
        else:
            bw, bh = (64, 40) if kind == "big" else (46, 28)  # base minka in FEET
            t = int(abs(x) * 53 + abs(y) * 29) % 100
            wf = 1.0 if kind == "big" else (0.9 if t < 30 else (1.12 if t >= 80 else 1.0))
            hw, hh = self.px(bw) * wf, self.px(bh) * wf
        # a fireproof KURA storehouse is a WEALTH MARKER, not universal - it attaches to the house on ~30% of
        # plain farms (position-seeded off the SEED spot, no RNG ripple; a ruin has none). The HEADMAN always
        # has one (GM 2026-07-21): the shoya/nanushi is by definition among the village's most prosperous
        # farmers - historically the land-opening family - AND the office needs one functionally: the headman
        # kept the village's tax ledgers, land registers, and tax rice awaiting collection, exactly what
        # fireproof kura storage is for. Leaving him on the ~30% dice let all four pool headmen roll bare
        # (chance masquerading as doctrine); headman_has_kura gates it now. It goes on the
        # NORTH (back) wall of a nucleated house: the cluster hugs the field to the EAST so a house's garden takes
        # the west/sunny walls but never the shaded NORTH, so a north kura is clear of it - and its footprint is
        # RESERVED in the homestead bundle so a neighbor never lands on it. Drawn + recorded in farmsteads() so
        # it always moves WITH the house (farm_sheds_attached guards it).
        _shed = kind == "plain" and (role == "headman" or self._hjit(x, y, 3.0) < 0.30)
        spot = self._place_bundle(x, y, hw, hh, shed=_shed)  # pack the bundle (incl. the reserved kura) near (x,y)
        if spot is None:
            return False
        cx, cy, geom = spot
        self.placed.append(geom["bbox"])  # reserve the whole homestead footprint as one rect
        rec = {
            "x": cx,
            "y": cy,
            "w": hw,
            "h": hh,
            "kind": kind,
            "rot": self._house_rot(cx, cy),
            "role": role,
            "shed": _shed,
            "shed_side": "N",
            "wealth": wf,
            "geom": geom,
        }  # rot position-seeded, like _shed above
        self.M["houses"].append(rec)
        self._pending_farmsteads.append(rec)
        return True

    def _try_place_legacy(self: Settlement, x: float, y: float, kind: str, role: Any = None) -> bool:  # type: ignore[misc]
        # a farmhouse shares the MAP'S building grain (bscale): at hamlet scale bscale is 1.0 (full size), but
        # a town/city compresses its urban buildings, and a peasant farmhouse must not render LARGER than the
        # samurai and merchant houses inside the walls - so it scales down by the same factor.
        bw, bh = (60, 40) if kind == "big" else (44, 29)
        wf = 1.0
        if kind == "plain":
            t = int(abs(x) * 53 + abs(y) * 29) % 100
            wf = 0.9 if t < 30 else (1.12 if t >= 80 else 1.0)
        w, h = bw * self.bscale, bh * self.bscale
        if not self._fits(x, y, w, h):
            return False
        # BOTH position-seeded (2026-08-08). The bundle path already rolled its kura off _hjit at
        # the same 3.0 salt; this path drew from the stream, so an upstream change that consumed one
        # extra random number silently re-rolled every legacy farmhouse's rake AND which of them had
        # a storehouse - measured as the entire manifest drift of a hamlet (2 keys of 63).
        rot = self._hjit(x, y, 11.0) * 10.0 - 5.0
        shed = self._hjit(x, y, 3.0) < 0.3
        self.placed.append((x, y, w, h))
        rec = {"x": x, "y": y, "w": w, "h": h, "kind": kind, "rot": rot, "role": role, "shed": shed, "wealth": wf}
        self.M["houses"].append(rec)
        self._pending_farmsteads.append(rec)
        return True

    def lane_skeleton(self: Settlement, kind: str, cx: float, cy: float, ex: float, ey: float, width: float = 5, clearance: float = 18, worn: bool = True) -> dict[str, Any]:  # type: ignore[misc]
        """Lay a nucleated cluster's internal lanes for the given skeleton and record the skeleton kind on
        the manifest (meta.lane_skeleton, read by the twin-detector). Returns the DERIVED focal points -
        `headman` (place the headman house there) and `gateway` (the downslope exit; anchor the connector
        track and the tutelary shrine off it). The lanes lay their no-build corridors BEFORE the houses,
        so the homesteads front them (same as a hand-placed lane)."""
        layout = skeleton_layout(kind, cx, cy, ex, ey)
        for pts in layout["lanes"]:
            self.lane(pts, width=width, clearance=clearance, worn=worn)
        self.M["meta"]["lane_skeleton"] = kind
        return layout

    def cluster_seeds(self: Settlement, shape: str, cx: float, cy: float, ex: float, ey: float, n: int, rng: random.Random, record: bool = True) -> list[Pt]:  # type: ignore[misc]
        """Generate `n` house-seed positions for a nucleated cluster of the given SHAPE (feature 005
        `cluster_shape` knob), to feed to `try_place` (the bundle solver then hugs each homestead to the field
        edge). Records `meta.cluster_shape` when `record=True`. Shapes (grounding: research.md D2 - cluster
        shape followed the available dry ground):
          - `round`     - a filled ellipse (a knoll): the classic disk.
          - `elongated` - a long narrow ellipse (a levee / ridge string): stretched along the margin (the ey axis).
          - `crescent`  - positions hugging a shallow arc (a field-edge crescent), concave toward the field.
          - `split`     - two sub-hamlets on either flank (two dry patches flanking the arable).
        Off the flood toe / field-adjacency are enforced downstream by `try_place` (each candidate that is not
        field-adjacent or lands on a blocker is simply rejected), so this only has to SHAPE the seed cloud."""
        if shape not in ("round", "elongated", "crescent", "split"):
            raise ValueError(f"unknown cluster_shape {shape!r}; expected round / elongated / crescent / split")
        if record:
            self.M["meta"]["cluster_shape"] = shape
        out: list[Pt] = []
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.random() ** 0.5
            if shape == "round":
                out.append((cx + math.cos(a) * r * ex, cy + math.sin(a) * r * ey))
            elif shape == "elongated":  # narrow across the margin, long along it
                out.append((cx + math.cos(a) * r * ex * 0.55, cy + math.sin(a) * r * ey * 1.4))
            elif shape == "crescent":  # a curved band, concave toward the field, NARROW across the margin.
                # The old form spread wide (x1.15 lateral) with the horns curved hard back, so the placer -
                # which pulls every house to hug the paddy and packs ALONG it - strung them into a wide, hollow
                # arc that stranded the horns far from the crops (Kikuta: 55 houses over a hull filled ~20%, NE
                # horn ~400px from any field; see village_cluster_compact / settlements.md 'Cluster compactness').
                # WIDTH is what the placer amplifies, so keep the lateral reach narrow (a nucleated village is a
                # deep blob, not a wide ribbon) and let the depth carry the frontage, with a gentle concave bow.
                t = rng.uniform(-1.0, 1.0)
                depth = rng.random() ** 0.5
                bx = cx + t * ex * 0.5 + math.cos(a) * ex * 0.22 * depth
                by = cy + (t * t - 0.5) * ey * 0.5 + math.sin(a) * ey * 0.95 * depth
                out.append((bx, by))
            else:  # split: two sub-disks on the flanks
                side = -1.0 if rng.random() < 0.5 else 1.0
                out.append((cx + side * ex * 0.62 + math.cos(a) * r * ex * 0.42, cy + math.sin(a) * r * ey * 0.82))
        return out

    def cluster_anchor(  # type: ignore[misc]
        self: Settlement, position: str, field_bbox: tuple[float, float, float, float], down_deg: float, lateral_frac: float = 0.6, depth_frac: float = 0.34
    ) -> tuple[float, float, float, float]:
        """Resolve the `cluster_position` knob into a cluster ANCHOR `(cx, cy, ex, ey)` to feed `cluster_seeds`.
        The knob says WHERE on its field's dry margin a nucleated village sits; this reads that against the
        field's bbox and its `down_deg` fall line and returns a center just OFF the paddy plus screen-axis
        half-extents (`ex`, `ey`) oriented so the cluster runs ALONG that margin. (Field-adjacency + off-the-toe
        are still enforced downstream: `try_place` rejects any seeded house that is not field-adjacent or lands
        on the flood toe / a blocker, so this only has to aim the cloud at the right dry ground.)

        Grounding (research.md D2 - villages took the best DRY ground beside their paddy, 背山面水 'mountain
        behind, water in front'; which dry ground was available varied, and that variation is the knob):
          - `high_margin`  - the upslope (high) edge, centered: the classic back-to-the-hill seat. DEFAULT.
          - `valley_head`  - the high edge but tucked to one cross-slope corner (a head terrace by the intake).
          - `mid_margin`   - the high edge, offset the other way along the margin (partway along, not centered).
          - `flank`        - a cross-slope SIDE margin (a side levee / valley wall), off to one flank.
          - `valley_mouth` - down by the low end where the valley opens, but pulled to the dry lateral shoulder
                             (NEVER straight down into the wet central toe below the drain).
          - `on_rise`      - a dry knoll off a high corner (a rise standing a little out of the plain).
        """
        if position not in ("high_margin", "valley_head", "mid_margin", "flank", "valley_mouth", "on_rise"):
            raise ValueError(f"unknown cluster_position {position!r}")
        fx0, fy0, fx1, fy1 = field_bbox
        fcx, fcy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        hw, hh = (fx1 - fx0) / 2, (fy1 - fy0) / 2
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))  # downhill unit
        ux, uy = -dy, dx  # cross-slope (lateral / along-margin) unit
        ad = abs(dx) * hw + abs(dy) * hh  # field half-extent along the fall
        au = abs(ux) * hw + abs(uy) * hh  # field half-extent across the fall (the margin's run)
        lat = au * lateral_frac  # the cluster runs ALONG the margin (lateral)...
        dep = min(
            max(ad, au) * depth_frac, 118.0
        )  # ...but stays fairly shallow: the near rows ring the field (field_ringed), the back rows are a legit cluster-span back (cluster_abuts_fields allows it for a nucleated seat)
        clr = dep + 22.0  # the along-slope clearance: the cluster's near edge sits `pad`-ish off the paddy, whole cluster clear
        # (along-slope offset s: -ve = uphill of center; lateral offset t along +u)
        # high-margin lateral offsets stay MODEST (a fan field is narrow at its head, so the bbox overstates
        # how far a high-corner cluster can slide and still sit over the paddy) - the flank/mouth positions push
        # fully out to a cross-slope side where the field is at full width.
        if position == "high_margin":
            s, t = -(ad + clr), 0.0
        elif position == "valley_head":
            s, t = -(ad + clr), -au * 0.3
        elif position == "mid_margin":
            s, t = -(ad + clr), au * 0.3
        elif position == "flank":
            s, t = 0.0, au + clr
        elif position == "valley_mouth":
            s, t = ad * 0.45, au + clr  # low-ish AND pushed to the dry lateral shoulder, never the central toe
        else:  # on_rise: a dry knoll at a HIGH CORNER (up, and a little laterally) - still hugging the high margin
            s, t = -(ad + clr), au * 0.3
        cx = fcx + dx * s + ux * t
        cy = fcy + dy * s + uy * t
        ex = abs(ux) * lat + abs(dx) * dep  # project the lateral+depth extents back onto screen x / y
        ey = abs(uy) * lat + abs(dy) * dep
        return (cx, cy, ex, ey)

    def plot_texture(self: Settlement, plot_size: str = "medium", plot_regularity: str = "organic", record: bool = True) -> tuple[float, tuple[float, float]]:  # type: ignore[misc]
        """Resolve the `plot_size` + `plot_regularity` knobs into `build_comb`'s `(plot_across, row_step)` levers
        so they actually change the paddy grain. `plot_across` sets how many bunded plots tile across each canal
        reach (small = many small paddies, large_block = few big ones, strip = narrow but long); `row_step` is
        the along-canal row spacing, and its SPREAD is the regularity: a WIDE spread reads organic/old-grown, a
        TIGHT spread reads as a planned/surveyed grid. Records the two knobs on the manifest. Grounding: old
        wet-rice terraces grew as small irregular paddies fitted to the microtopography; large regular blocks or
        long strips signal a later planned reclamation/allotment (which is why `grid` is typing-gated to a
        planned field origin). Returns `(plot_across, row_step)` to pass straight into `build_comb`.

        SIZED IN REAL FEET at ftpx >= 2 (GM 2026-07-22): for a village or provincial city each `plot_size`
        picks a real-feet CELL-AREA target (acres) and an aspect, and `waterfields.paddy_grain` converts that to
        px at THIS map's `ftpx` - so the paddy grain is the same real size at every scale (see
        waterfields.PADDY_CELL_ACRES / settlements.md 'Paddy cell size'). The targets bracket the calibrated
        norm: `small_irregular` below it, `medium` at it, `large_block` above, `strip` at the norm's area but
        long-and-narrow (aspect > 1). The ft/px=1 HAMLETS (the only maps that reach this at that scale, via
        roll_village) stay on the LEGACY px grain: they already render in-band (~0.02-0.06 acre) and the GM
        asked to leave them untouched, so recalibrating them would only reshuffle vetted maps for no gain."""
        from l7r.diagram.waterfields import PADDY_CELL_ACRES, paddy_grain

        if plot_size not in ("small_irregular", "medium", "large_block", "strip"):
            raise ValueError(f"unknown plot_size {plot_size!r}")
        if plot_regularity not in ("organic", "grid"):
            raise ValueError(f"unknown plot_regularity {plot_regularity!r}")
        if self.ftpx >= 2:  # village / city: the real-feet calibration
            # (target_acres, aspect = along/across): small below the norm, large above, strip = norm area but elongated
            tgt_acres, aspect = {
                "small_irregular": (PADDY_CELL_ACRES * 0.72, 0.66),
                "medium": (PADDY_CELL_ACRES, 0.66),
                "large_block": (PADDY_CELL_ACRES * 1.35, 0.72),
                "strip": (PADDY_CELL_ACRES, 1.9),
            }[plot_size]
            across, step = paddy_grain(self.ftpx, target_acres=tgt_acres, aspect=aspect)
        else:  # ft/px=1 hamlet: the legacy px grain (already in-band; left untouched by GM request)
            across, step = {
                "small_irregular": (34.0, (20.0, 40.0)),
                "medium": (48.0, (26.0, 36.0)),
                "large_block": (70.0, (30.0, 44.0)),
                "strip": (32.0, (46.0, 66.0)),
            }[plot_size]
        if plot_regularity == "grid":  # collapse the row-step spread toward its mean -> even, surveyed rows
            mid = (step[0] + step[1]) / 2
            step = (mid - 3.0, mid + 3.0)
        if record:
            self.M["meta"]["plot_size"] = plot_size
            self.M["meta"]["plot_regularity"] = plot_regularity
        return across, step

    @staticmethod
    def water_sources_for(down_deg: float, water_kind: str) -> list[str]:
        """The `water_source_position` values that gravity-feed a field falling toward `down_deg` (the source
        must sit UPHILL of the field intake - water runs downhill through the comb). Pond kinds are the
        corner/mid/chain set; a stream enters from a canvas edge. A source on the downhill half is excluded
        (it could not feed the field), which is the gravity typing the knob's own `typing_rule` defers to
        placement. Used by the seed roll so an unpinned water source lands somewhere water can actually flow
        from."""
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        # each candidate's outward direction from field center; keep those on the UPHILL half (dot with
        # downhill <= a small tolerance, so a cross-slope side counts as feedable)
        dirs = {
            "corner_NW": (-1, -1),
            "corner_NE": (1, -1),
            "corner_SW": (-1, 1),
            "corner_SE": (1, 1),
            "edge_N": (0, -1),
            "edge_E": (1, 0),
            "edge_S": (0, 1),
            "edge_W": (-1, 0),
            "mid_margin": (-dx, -dy),
            "chain": (-dx, -dy),  # the uphill margin itself
        }
        pond = ["corner_NW", "corner_NE", "corner_SW", "corner_SE", "mid_margin", "chain"]
        edge = ["edge_N", "edge_E", "edge_S", "edge_W"]
        names = edge if water_kind == "stream" else pond
        out = []
        for nm in names:
            vx, vy = dirs[nm]
            n = math.hypot(vx, vy) or 1.0
            if (vx / n) * dx + (vy / n) * dy <= 0.35:  # not on the downhill half (tolerance admits cross sides)
                out.append(nm)
        return out

    def water_source_anchor(self: Settlement, position: str, field_bbox: tuple[float, float, float, float], down_deg: float, pad: float = 90.0) -> Pt:  # type: ignore[misc]
        """Resolve `water_source_position` into the SLUICE / stream-entry point (where water reaches the field
        head), just off the field on the named margin. Pond positions (`corner_*` / `mid_margin` / `chain`) put
        the feed on that corner or margin; stream `edge_*` positions put it at that canvas-edge margin. RAISES
        if the resolved point is on the DOWNHILL half of the field (gravity: a source below the field cannot
        feed it) - so a historically-impossible pin is rejected here, and `water_sources_for` lists the legal
        set for a roll. Grounding: Chinese canal doctrine feeds a comb from its high end; the varied high-side
        entry (a corner pond, a mid-margin tank, a stepped chain, a stream off one edge) is the knob."""
        if position not in ("corner_NW", "corner_NE", "corner_SW", "corner_SE", "mid_margin", "chain", "edge_N", "edge_E", "edge_S", "edge_W"):
            raise ValueError(f"unknown water_source_position {position!r}")
        fx0, fy0, fx1, fy1 = field_bbox
        fcx, fcy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        corners = {"corner_NW": (fx0 - pad, fy0 - pad), "corner_NE": (fx1 + pad, fy0 - pad), "corner_SW": (fx0 - pad, fy1 + pad), "corner_SE": (fx1 + pad, fy1 + pad)}
        edges = {"edge_N": (fcx, fy0 - pad), "edge_S": (fcx, fy1 + pad), "edge_E": (fx1 + pad, fcy), "edge_W": (fx0 - pad, fcy)}
        if position in corners:
            sx, sy = corners[position]
        elif position in edges:
            sx, sy = edges[position]
        else:  # mid_margin / chain: the middle of the UPHILL margin (opposite the fall)
            sx, sy = fcx - dx * ((fx1 - fx0) / 2 + pad), fcy - dy * ((fy1 - fy0) / 2 + pad)
        if (sx - fcx) * dx + (sy - fcy) * dy > 0.35 * math.hypot(sx - fcx, sy - fcy):
            raise ValueError(f"water_source_position {position!r} sits downhill of a field falling to {down_deg} deg - it cannot gravity-feed it")
        return (round(sx, 1), round(sy, 1))
