"""The nagaya pass that attaches a servant range to each ward samurai household, and the four probes that exist to serve it.

Split from settlement/structures.py by feature 114 - see settlement/structures/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any

from .._geom import (
    Poly,
    _aabb_gap,
    point_in_poly,
    poly_gap,
    rects_overlap,
    rot_rect,
    seg_dist,
)

if TYPE_CHECKING:
    from ..core import Settlement


class ServantRangesMixin:
    SERVANT_RANGE_DEPTH_FT = 15.0  # the measured nagayamon depth (Omura Yahei 2.5 ken; the Tokyo ICP gate 4.7 m)
    _OFFICE_STANDOFF = 15.0  # city_government_offices_dont_abut wants 14px of daylight; a px of margin over it

    def _solid_records(self: Settlement) -> list[dict[str, Any]]:  # type: ignore[misc]
        """Every drawn record on the map carrying a footprint, swept from the manifest rather than
        named in a list - so a feature added later is visible to placement without being remembered
        into it (the lesson `place_punishment_spot`'s caption probe paid for: skill CLAUDE.md,
        'the same disease turns up in PLACEMENT PROBES')."""
        out: list[dict[str, Any]] = []
        for key, recs in self.M.items():
            if key in ("labels", "title", "scalebar"):
                continue
            if isinstance(recs, dict) and "x" in recs and "w" in recs:
                out.append(recs)  # the singletons (governor_mansion, theater_stage)
            elif isinstance(recs, list):
                out += [r for r in recs if isinstance(r, dict) and "x" in r and "w" in r]
        return out

    def _blocks_any_door(self: Settlement, quad: Poly) -> bool:  # type: ignore[misc]
        """Would a footprint at `quad` stand in some building's DOORWAY?

        Mirrors `city_house_doors_unblocked`'s own geometry sample for sample - the door face
        centre, three lateral offsets, three depths - because placement and its check must read the
        same geometry, not merely the same data (skill CLAUDE.md). A rear service range is the seat
        that needs this: the ground behind a house is often the roji the row BEHIND it faces."""
        dc = 7.0 / self.ftpx  # DOOR_CLEAR_FT, the check's own constant
        qx = sum(p[0] for p in quad) / 4.0
        qy = sum(p[1] for p in quad) / 4.0
        qr = max(math.hypot(p[0] - qx, p[1] - qy) for p in quad)
        for o in self.M["buildings"]:
            if "w" not in o or math.hypot(o["x"] - qx, o["y"] - qy) > qr + math.hypot(o["w"], o["h"]) / 2 + dc + 2:
                continue
            th = math.radians(o.get("rot", 0.0))
            ux, uy = -math.sin(th), math.cos(th)  # the door face's outward normal
            vx, vy = -uy, ux
            fx, fy = o["x"] + ux * o["h"] / 2, o["y"] + uy * o["h"] / 2
            for d in (0.8, dc * 0.55, dc):
                for t in (-0.3 * o["w"], 0.0, 0.3 * o["w"]):
                    if point_in_poly(fx + ux * d + vx * t, fy + uy * d + vy * t, quad):
                        return True
        return False

    def _door_is_clear(self: Settlement, cx: float, cy: float, w: float, h: float, rot: float, skip: Any = None) -> bool:  # type: ignore[misc]
        """Does a footprint placed here have an unobstructed DOORWAY of its own?

        The mirror of `_blocks_any_door`, and sampled at exactly the same points the check uses -
        an earlier version approximated the door band with a small rect and let a blocker sitting
        between 2.0 and 2.33 px of the face slip through, which the gate then reported."""
        dc = 7.0 / self.ftpx
        th = math.radians(rot)
        ux, uy = -math.sin(th), math.cos(th)
        vx, vy = -uy, ux
        fx, fy = cx + ux * h / 2, cy + uy * h / 2
        near = [o for o in self._solid_records() if o is not skip and math.hypot(o["x"] - cx, o["y"] - cy) < math.hypot(w, h) / 2 + dc + math.hypot(o["w"], o.get("h", o["w"])) / 2 + 2]
        corners = [rot_rect(o["x"], o["y"], o["w"], o.get("h", o["w"]), o.get("rot", 0)) for o in near]
        for d in (0.8, dc * 0.55, dc):
            for t in (-0.3 * w, 0.0, 0.3 * w):
                px_, py_ = fx + ux * d + vx * t, fy + uy * d + vy * t
                if any(point_in_poly(px_, py_, c) for c in corners):
                    return False
        return True

    def _office_records(self: Settlement) -> list[dict[str, Any]]:  # type: ignore[misc]
        """The government offices, which keep a standoff rather than merely not overlapping."""
        offices = list(self.M.get("ministries", []))
        gov = self.M.get("governor_mansion")
        return offices + ([gov] if gov else [])

    def servant_ranges(self: Settlement, hosts: Any = None) -> int:  # type: ignore[misc]
        """Attach each ward samurai household's SERVANT RANGE - the *nagaya* - to its own house.

        A samurai household's domestics lived inside the master's plot: in the perimeter nagaya
        that forms the street boundary itself, in the nagayamon gate rooms, or in nando off the
        kitchen. They never held a freestanding house in the buke-chi, and a Chinese elite compound
        says the same thing from the other side (servants in the daozuofang, the south row whose
        blank back IS the street wall). Ranks of small uniform dwellings are a real castle-town
        texture, but they are ashigaru kumi-yashiki on the town FRINGE - never inside the fence.
        Full findings + measured examples: research/cities/government.md.

        So the range is drawn as a LONG THIN building (15 real ft deep, running the length of its
        master's frontage) laid against the house's side and flush with its front plane - reading
        as that household's street range rather than as a cottage. It is recorded as an ordinary
        `servant` dwelling carrying `of`, so the population and caste arithmetic are untouched: a
        servant family is a property-holding, taxed household in budgets.md (a provincial city's
        120 servant families include 72 attached to its 60 samurai households - about one per
        junior house, two per senior), and this changes where they are DRAWN, never how many exist.

        LATERAL, not in front, because our in-city samurai houses are unwalled: history put the
        range on the plot boundary with the house set back behind it, but with no wall to hide
        behind, a range across the frontage would stand in its own master's doorway
        (`city_house_doors_unblocked`). Beside-and-flush keeps both doors on the open side.

        ORDERING: call AFTER every samurai house in the ward is placed (the census fills seat some)
        and AFTER s.ward, which is what defines the interior; but BEFORE the exact-population fill,
        so it can top the servant count up elsewhere. Returns the number attached."""
        if not self._samurai_ward_interiors:
            return 0
        depth = self.px(self.SERVANT_RANGE_DEPTH_FT)
        beds = [(st["pts"], st.get("w", 18) / 2) for st in self.M.get("town_streets", [])]
        beds += [(al["pts"], al.get("w", 10) / 2) for al in self.M.get("alleys", [])]
        if self.M.get("road"):
            beds.append((self.M["road"], self.M.get("road_width", 26) / 2))
        if self.M.get("ring_road"):
            beds.append((self.M["ring_road"], self.M.get("ring_road_width", 15) / 2))
        in_ward = [b for b in self.M["buildings"] if any(point_in_poly(b["x"], b["y"], rg) for rg in self._samurai_ward_interiors)]
        if hosts is None:
            hosts = [b for b in in_ward if b["kind"] in ("samurai", "samurai_large")]
        # IDEMPOTENT: count what each household already has, so the pass can be run again after a
        # late household top-up without giving anyone a second (or third) range over its quota.
        had: dict[tuple[float, float], int] = {}
        for r in self.M["buildings"]:
            if r["kind"] == "servant" and "of" in r:
                k = (round(r["of"][0], 1), round(r["of"][1], 1))
                had[k] = had.get(k, 0) + 1
        placed = 0
        for b in hosts:
            want = (2 if b["kind"] == "samurai_large" else 1) - had.get((round(b["x"], 1), round(b["y"], 1)), 0)  # budgets.md: 2 servant families to a senior house, 1 to a junior
            th = math.radians(b.get("rot", 0.0))
            ux, uy = math.cos(th), math.sin(th)  # the house's LOCAL +x (along its frontage)
            fx, fy = -math.sin(th), math.cos(th)  # its LOCAL +y - the door/front side
            # SEATS, in the order the sources put them. The nagaya on a FLANK, flush with the
            # frontage, is the first choice - that is the range that forms the plot's street
            # boundary. Where a terraced neighbor leaves no flank, the REAR service row is the
            # attested fallback (China's houzhaofang; Japan's service wing behind the house), and a
            # SHORTER range is tried before giving up, since a nagayamon need not span the whole
            # frontage. A household with no seat at all simply has no separate servant dwelling -
            # which is itself attested: below ~100-300 koku the domestics slept in nando off the
            # master's kitchen, with no building of their own.
            _lens = (b["w"], b["w"] * 0.78)  # a nagayamon need not span the whole frontage; shorten before giving up
            # SEAT ORDER, and it is a LEGIBILITY rule as much as a historical one
            # (settlement-review 2026-08-03). A single appendage stuck to one corner of a ROTATED
            # box stops reading as a plot and starts reading as an implement - the reviewer read
            # four of these as a paintbrush and a meat cleaver before reading them as households.
            # So: take both flanks at full length first (a house with ranges to either side reads
            # as a frontage, not a handle), and for the two-range senior house prefer the SAME
            # side, giving a doubled range rather than one flank plus one rear stub.
            seats = [(sd, ln, False) for ln in _lens for sd in (1, -1)]
            seats += [(sd, ln, True) for ln in _lens for sd in (1, -1)]
            for side, length, rear in seats:
                if want <= 0:
                    break
                if length < 3.0 * depth:
                    continue  # below ~3x depth it stops reading as a range and starts reading as a blob (settlement-review
                    # 2026-08-03 found the 2.3x floor's 35x15 ft seats doing exactly that). A household with no seat this
                    # long simply goes without, which the docstring already justifies.
                rrot = (b.get("rot", 0.0) + 180.0) if rear else b.get("rot", 0.0)  # a rear range turns its door away from the house
                if rear:
                    off = b["h"] / 2 + depth / 2 + 0.6  # tucked behind the back wall, like the merchant kura
                    ox, oy = b["x"] - fx * off, b["y"] - fy * off
                else:
                    off = b["w"] / 2 + length / 2 + 0.6  # a hair of daylight: sat_overlap ignores touching, but never risk it
                    fo = (b["h"] - depth) / 2  # flush with the house's front plane
                    ox, oy = b["x"] + ux * off * side + fx * fo, b["y"] + uy * off * side + fy * fo
                quad = rot_rect(ox, oy, length, depth, rrot)
                if not all(any(point_in_poly(qx, qy, rg) for rg in self._samurai_ward_interiors) for qx, qy in quad):
                    continue  # the whole range stays inside the fence
                # ...and CLEAR of the fence's own ink. "Inside the interior polygon" is the fence
                # LINE, and the palisade is stroked 5px wide, so a range flush to the boundary is
                # geometrically inside it and still drawn through it (city_ward_fence_clear_of_structures).
                if any(seg_dist(ox, oy, wb[i], wb[i + 1]) < max(length, depth) / 2 + self._WARD_STROKE for wd in self.M.get("wards", []) for wb in [wd["boundary"]] for i in range(len(wb) - 1)):
                    continue
                if self.bound and not all(point_in_poly(qx, qy, self.bound) for qx, qy in quad):
                    continue
                if any(seg_dist(ox, oy, pts[k], pts[k + 1]) < half + max(length, depth) / 2 + 2 for pts, half in beds for k in range(len(pts) - 1)):
                    continue  # a range is a building on the verge, not an obstruction in the roadbed
                # CLEAR OF EVERY SOLID THING, found by SWEEPING the manifest rather than by a hand
                # list of keys. The first cut here tested only `buildings` and `houses`, and the
                # ranges promptly landed on the martial hall, a dojo and four ministry aprons - the
                # same defect the punishment-ground caption probe had (skill CLAUDE.md: a probe must
                # iterate any manifest list of dicts carrying w/h, or the next feature is invisible
                # to it). Offices additionally keep their 14px standoff
                # (`city_government_offices_dont_abut`), so they are tested against an inflated range.
                if any(rects_overlap(quad, rot_rect(o["x"], o["y"], o["w"], o.get("h", o["w"]), o.get("rot", 0))) for o in self._solid_records() if o is not b):
                    continue
                # THE OFFICE STANDOFF, MEASURED THE WAY THE CHECK MEASURES IT - AABB to AABB.
                # `city_government_offices_dont_abut` compares axis-aligned BOUNDS, while this
                # probe used to inflate the range's ROTATED rect and test that: for a range drawn
                # at its host's frontage angle the two disagree by up to the difference between its
                # half-depth and its half-diagonal, so Nagahara seated a -109 deg servant range
                # 13.96px off the Ministry of Works - clear on the probe's measure, abutting on the
                # gate's (2026-08-08). Same rule as the punishment-ground caption probe: a probe
                # must measure the box the CHECK will measure (skill CLAUDE.md).
                if any(_aabb_gap(quad, rot_rect(o["x"], o["y"], o["w"], o["h"], o.get("rot", 0))) < self._OFFICE_STANDOFF for o in self._office_records()):
                    continue
                _hostgap = min(poly_gap(quad, rot_rect(b["x"], b["y"], b["w"], b["h"], b.get("rot", 0))), 1e9)
                if any(poly_gap(quad, rot_rect(o["x"], o["y"], o["w"], o.get("h", o["w"]), o.get("rot", 0))) < _hostgap for o in self.M["buildings"] if o is not b):
                    continue  # it must read as ITS OWN household's range: nothing may touch it more closely than its host
                if self._blocks_any_door(quad):
                    continue  # a range is service accommodation on the household's own ground, never a wall across a neighbor's entrance
                if not self._door_is_clear(ox, oy, length, depth, rrot, skip=b):
                    continue  # ...and its OWN door has to open onto open ground
                if self.building(ox, oy, length, depth, "servant", rrot, of=b):
                    placed += 1
                    want -= 1
        return placed
