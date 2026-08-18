"""The religious hall and shrine GLYPHS, the hill one may stand on, and the hall's caption.

Split from settlement/shrines_wells.py by feature 116 - see settlement/shrines_wells/CLAUDE.md for the index.
"""

import math
import random
from typing import TYPE_CHECKING, Any

from .._geom import (
    HALL_CAPTION_FS,
    TORII_PITCH_FT,
    Pt,
    torii_halfbox,
)
from .._knobs import roll_torii_count

if TYPE_CHECKING:
    from ..core import Settlement


class ShrineHallsMixin:
    def hill(self: Settlement, cx: float, cy: float, rx: float, ry: float, steep: bool = False) -> Pt:  # type: ignore[misc]
        rings = [(cx, cy + 28, rx, ry), (cx, cy, rx * 0.76, ry * 0.76), (cx, cy - 26, rx * 0.52, ry * 0.52), (cx, cy - 44, rx * 0.30, ry * 0.32)]
        self.M["hill"] = [rings[0][0], rings[0][1], rings[0][2], rings[0][3]]
        self.M["summit"] = [rings[3][0], rings[3][1], rings[3][2], rings[3][3]]
        self.ellipses.append((rings[0][0], rings[0][1], rings[0][2], rings[0][3]))
        for (ax, ay, arx, ary), shade in zip(rings, ['#DFD0A2', '#D8C795', '#D0BD87', '#C8B37B'], strict=False):
            self.add(f'<ellipse cx="{ax:.0f}" cy="{ay:.0f}" rx="{arx:.0f}" ry="{ary:.0f}" fill="{shade}" stroke="#A8995F" stroke-width="1"/>')
        ocx, ocy, orx, ory = rings[0]
        for k in range(30):
            a = 2 * math.pi * k / 30
            ex, ey = ocx + math.cos(a) * orx, ocy + math.sin(a) * ory
            self.add(f'<line x1="{ex:.0f}" y1="{ey:.0f}" x2="{ex + math.cos(a) * 9:.0f}" y2="{ey + math.sin(a) * 9:.0f}" stroke="#A8995F" stroke-width="0.9"/>')
        if steep:
            # emphasized downslope hachures over the steep north back and upper flanks:
            # closely-spaced, longer ticks read as a steep, undefendable-on-foot slope
            n = 52
            for k in range(n + 1):
                ang = math.radians(195 + (345 - 195) * k / n)
                ex, ey = ocx + math.cos(ang) * orx, ocy + math.sin(ang) * ory
                ln = 19 + 5 * math.sin(math.radians(195 + (345 - 195) * k / n) - math.pi / 2)
                self.add(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{ex + math.cos(ang) * ln:.1f}" y2="{ey + math.sin(ang) * ln:.1f}" stroke="#8F7E48" stroke-width="1.0"/>')
        st = random.getstate()
        random.seed(4)
        for _ in range(15):
            a = random.uniform(0, 2 * math.pi)
            rr = random.uniform(0.4, 0.9)
            tx = cx + math.cos(a) * rx * rr
            ty = (cy + 12) + math.sin(a) * ry * rr
            self.add(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{random.uniform(4, 6):.1f}" fill="#7E9B5C" stroke="#52663C" stroke-width="0.8"/>')
            self.add(f'<circle cx="{tx - 1:.0f}" cy="{ty - 1:.0f}" r="1.6" fill="#9DB87A"/>')
        random.setstate(st)
        return (cx, cy - 40)  # summit point for the shrine

    def shrine(self: Settlement, x: float, y: float, w_ft: float = 62, h_ft: float = 42, kind: str = "shrine") -> None:  # type: ignore[misc]
        """The legacy simple shrine glyph (the civic_shrine roll path + secondary_shrine). TRUE SCALE
        (GM 2026-07-21): dimensions are REAL FEET, converted through px() - an ordinary village
        tutelary hall ~62x42 ft (~240 m2, inside the 600 m2 village ceiling). The old signature took
        fixed PIXELS (104x68 default), a latent footgun that would have drawn a 208x136 ft
        monastery-sized hall on any village that used the default civic_shrine path."""
        w, h = self.px(w_ft), self.px(h_ft)
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="#C9876C" stroke="#6B2A18" stroke-width="2"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="8" fill="#A03020"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y + h / 2 - 8:.0f}" width="{w}" height="8" fill="#A03020"/>')
        self.add(f'<line x1="{x - w / 2:.0f}" y1="{y:.0f}" x2="{x + w / 2:.0f}" y2="{y:.0f}" stroke="#6B2A18" stroke-width="0.7"/>')
        self.M["shrine"] = [x - w / 2, y - h / 2, w, h]
        self.M["religious"].append({"kind": kind, "x": x, "y": y, "w": w, "h": h})

    def small_shrine(self: Settlement, x: float, y: float, w: Any = None, h: Any = None) -> None:  # type: ignore[misc]
        """A small wayside / neighborhood Shinto SHRINE - a vermilion-roofed shed with a little torii
        in front, the kind that dot a temple neighborhood. Non-residential: recorded in M['religious']
        as kind 'small_shrine' (so it is not housing and not a full temple - it needs no torii avenue
        and is not counted as a dwelling). Placed early so the dense packs flow around it."""
        if w is None:
            w, h = self.px(32), self.px(24)  # ~32x24 ft wayside shrine (town-calibrated glyph)
        x0, y0 = x - w / 2, y - h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" rx="2" fill="#C9876C" stroke="#6B2A18" stroke-width="1.4"/>')
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="5" fill="#A03020"/>')  # vermilion roof ridge
        ty = y + h / 2 + max(self.px(8), 3)  # a little torii just in front (south)
        m2 = self.px(9.0) / 2  # TRUE SCALE: a wayside-shrine torii spans ~9 ft (vs the shed's ~32 ft)
        self.add(
            f'<g transform="translate({x:.0f},{ty:.0f})"><line x1="{-m2 * 0.87:.1f}" y1="0" x2="{m2 * 0.87:.1f}" y2="0" stroke="#A03020" stroke-width="{max(self.px(1.2), 1.4):.2f}"/>'
            f'<line x1="{-m2:.1f}" y1="{-m2 * 0.5:.1f}" x2="{m2:.1f}" y2="{-m2 * 0.5:.1f}" stroke="#A03020" stroke-width="{max(self.px(1.0), 1.2):.2f}"/>'
            f'<line x1="{-m2 * 0.62:.1f}" y1="{-m2 * 0.5:.1f}" x2="{-m2 * 0.62:.1f}" y2="{m2 * 0.75:.1f}" stroke="#A03020" stroke-width="{max(self.px(1.0), 1.2):.2f}"/>'
            f'<line x1="{m2 * 0.62:.1f}" y1="{-m2 * 0.5:.1f}" x2="{m2 * 0.62:.1f}" y2="{m2 * 0.75:.1f}" stroke="#A03020" stroke-width="{max(self.px(1.0), 1.2):.2f}"/></g>'
        )
        self.M["religious"].append({"kind": "small_shrine", "x": x, "y": y, "w": w, "h": h, "rot": 0})
        self.placed.append((x, y, w, h))
        bm = 16
        self.block_polys.append([(x0 - bm, y0 - bm), (x + w / 2 + bm, y0 - bm), (x + w / 2 + bm, y + h / 2 + bm + 16), (x0 - bm, y + h / 2 + bm + 16)])

    def _hall_caption_y(self: Settlement, x: float, y: float, w: float, h: float, label: str, label_below: bool, seats: list[Pt]) -> float:  # type: ignore[misc]
        """The baseline y of a hall's caption, kept OUT OF ITS OWN SANDO (GM 2026-07-27: an arch must
        "never be covered by the 'temple of X' label"). A hall's caption and its approach both want the
        ground at the hall's face, so the two collided the moment `_avenue_at_threshold` brought the
        arches in - and they were already colliding before it, three times in the shipped pool (Minami's
        'Temple of Bishamon' and Hoshizora's 'Monastery of Bishamon' each sat on their own arch, Kikuta's
        'Shrine to Benten' on its sando). The caption goes to the hall's BACK when its avenue owns the
        front: the gen's `label_below` is honored unless the arches are there, in which case the caption
        takes the other side. If both sides are fouled the requested side stands and
        `labels_clear_of_other_buildings` reports it - the engine does not get to hide a map that has no
        room for both.

        THREE candidate baselines, tried in a STRICT ORDER: the side the gen asked for, then that same
        side pushed clear PAST the far end of the avenue, and only then the opposite side. Arches veto a
        candidate; the first survivor wins. If all three are fouled the requested side stands and
        `labels_clear_of_other_buildings` reports it - the engine does not get to hide a map that has no
        room for both.

        WHY AN ORDER RATHER THAN A SCORE. The first version scored the survivors with `_label_hits`, the
        way `ministry` picks its label side, and it was wrong here for a DRAW ORDER reason: a hall goes
        in early, so at this point `_label_hits` can see almost nothing - Nagahara's fire tower, the
        graveyard's neighbors and the monk houses are all drawn later - and a blind score flipped
        Bishamon's caption to the hall's north side, onto a fire tower that did not exist yet. The gen
        author DOES know what is on each side, which is what `label_below` says; so honor it, and when
        the sando takes that ground, step past the sando rather than around the hall. Hoshizora is why
        stepping past has to exist at all: its monastery's parish graveyard sits deliberately at the
        BACK of the hall, so flipping the caption off the sando would just bury it in the cemetery.

        The label box measured here is `_record_label`'s recorded box, deliberately: placement and check
        must read the SAME geometry (CLAUDE.md, "Placement and its check must read the SAME manifest
        source"), or the engine congratulates itself on a clearance the gate does not see."""
        below, above = y + h / 2 + 22, y - h / 2 - 10
        want, alt = (below, above) if label_below else (above, below)
        if not seats:
            return want
        lhw = len(label) * HALL_CAPTION_FS * 0.55 / 2  # _record_label's box for a hall caption, half-width
        txh, tyu, tyd = torii_halfbox(self.ftpx)
        # past the far end of the sando, on whichever side the avenue actually runs
        beyond = max(ty + tyd for _, ty in seats) + 22 if sum(ty for _, ty in seats) / len(seats) > y else min(ty - tyu for _, ty in seats) - 10

        def fouled(ly: float) -> bool:
            top, bot = ly - HALL_CAPTION_FS * 0.8, ly + HALL_CAPTION_FS * 0.25  # ...and its vertical extent
            return any(abs(tx - x) < lhw + txh and top < ty + tyd and ty - tyu < bot for tx, ty in seats)

        return next((ly for ly in (want, beyond, alt) if not fouled(ly)), want)

    def shrine_hall(  # type: ignore[misc]
        self: Settlement,
        x: float,
        y: float,
        label: Any,
        sublabel: str = "",
        w: float = 120,
        h: float = 82,
        torii: Any = None,
        primary: bool = False,
        edge: str = "#6B2A18",
        kind: str = "shrine",
        graveyard: bool = True,
        label_below: bool = False,
        torii_outlier: bool = False,
        torii_count: Any = None,
    ) -> None:
        """A standalone religious hall on flat ground. The kind follows settlement
        scale: villages have shrines, towns have monasteries, cities have temples
        (hamlets have none). primary=True marks the settlement's main one (M['shrine'],
        used by the torii checks). torii=[(x,y),...] defines the AVENUE LINE in front; the
        arch COUNT is rolled per temple on the tier's TORII_WEIGHTS column (seeded, so it is
        deterministic per map+hall), or pinned with torii_count=N - see the roll block below.
        graveyard=False marks a temple that hosts NO burial ground (a new or special-purpose
        hall, e.g. one founded in a former samurai estate) - city_temples_have_graveyards
        then exempts it; every other temple is expected to have a graveyard in its precinct.

        SCALE CONTRACT: `w`/`h` are DRAWN PIXELS, so at 1 ft/px (town) they equal real feet, but a
        coarser map MUST pass s.px(real_ft) - four city temples shipped as fixed 100x64 px = 300x192
        real ft before this was caught (audit 2026-07-21). The guard below refuses a hall whose
        implied real footprint exceeds any real main hall (the largest kondo runs ~150-190 ft;
        Tango's deliberate Daibutsuden-tier landmark is 200 ft) so unscaled px can't slip through."""
        if self.ftpx > 1 and max(w, h) * self.ftpx > 220:
            raise ValueError(f"shrine_hall {w}x{h}px at {self.ftpx} ft/px implies a {max(w, h) * self.ftpx:.0f} ft hall - pass s.px(real_ft), not raw pixels")
        n_t = 0
        seats_t: list[Pt] = []  # the DRAWN avenue - the caption below reads it to stay out of the sando
        if torii:
            # TORII COUNT IS ROLLED PER TEMPLE, the avenue list is GEOMETRY (GM 2026-07-23, the full
            # re-roll: the town/city gens hand-placed counts that predated the TORII_WEIGHTS table and
            # were never re-rolled - Tango/Nagahara sat at four 1s and a 3, a ~1%-likely draw under the
            # city column). `torii` now defines the avenue LINE (points marching AWAY from the hall);
            # the COUNT comes from a per-temple seeded roll on the tier table (deterministic in the map
            # seed + hall position), pinnable per temple via torii_count= (the per-hall analog of the
            # village 'torii_count' knob). Rolling more arches than points extends the avenue along its
            # own step (or away from the hall at a 44px stride for a single-point approach); rolling
            # fewer draws the first n. The resolved target is recorded on the religious rec as
            # 'torii_count' and gated by torii_match_roll, so a stale hand count can never ship again.
            n_t = (
                int(torii_count)
                if torii_count is not None
                else roll_torii_count(self.M.get("meta", {}).get("scale", "village"), random.Random(self.seed * 977 + int(round(x)) * 31 + int(round(y)) * 57))
            )
            pts_t = [(float(tpx), float(tpy)) for tpx, tpy in torii]
            if len(pts_t) < n_t:
                if len(pts_t) >= 2:
                    step_t = (pts_t[-1][0] - pts_t[-2][0], pts_t[-1][1] - pts_t[-2][1])
                else:
                    d_t = math.hypot(pts_t[0][0] - x, pts_t[0][1] - y) or 1.0
                    step_t = ((pts_t[0][0] - x) / d_t * self.px(TORII_PITCH_FT), (pts_t[0][1] - y) / d_t * self.px(TORII_PITCH_FT))
                while len(pts_t) < n_t:
                    pts_t.append((pts_t[-1][0] + step_t[0], pts_t[-1][1] + step_t[1]))
            # STRIDE, then THRESHOLD, then walls - and the threshold AGAIN. _avenue_short_of_walls
            # shortens a blocked run by scaling every seat's offset from the first arch, which pulls
            # the STRIDE in while leaving the threshold at the old, wider pitch; re-seating afterwards
            # is what keeps "the gap to the hall equals the gap between arches" true on a shortened
            # avenue too (Nagahara's Ebisu sando is the one that shortens). The second pass only ever
            # slides the run TOWARD the hall, over ground the first arch already stood clear of.
            seats_t = self._avenue_pitch(pts_t[:n_t])
            seats_t = self._avenue_short_of_walls(self._avenue_at_threshold(x, y, w, h, seats_t))
            seats_t = self._avenue_at_threshold(x, y, w, h, seats_t)
            for tx, ty in seats_t:
                s2 = self.px(16.0) / 2  # matches _torii's default true span
                # block the arch + a NEIGHBOR'S HALF-FOOTPRINT: packs test footprint centers, so the
                # margin must absorb half a house (~28 ft) + slack or a house's edge crosses the arch
                # (the old fixed 38px arch had this margin baked into its own oversize). Still kept
                # SMALLER than a street corridor so torii on a street don't shove the frontage houses.
                bm: float = self.px(28) + 4.0
                self.block_polys.append([(tx - s2 - bm, ty - s2 * 0.5 - bm), (tx + s2 + bm, ty - s2 * 0.5 - bm), (tx + s2 + bm, ty + s2 + bm), (tx - s2 - bm, ty + s2 + bm)])
                self._torii(tx, ty)
                self._clear_ground(tx, ty + 2, max(2 * s2 + 4, 10), max(s2 * 1.3, 8), 30)  # a swept collar under the arch + its sando approach
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="#C9876C" stroke="{edge}" stroke-width="2"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="9" fill="#A03020"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y + h / 2 - 9:.0f}" width="{w}" height="9" fill="#A03020"/>')
        self.add(f'<line x1="{x - w / 2:.0f}" y1="{y:.0f}" x2="{x + w / 2:.0f}" y2="{y:.0f}" stroke="{edge}" stroke-width="0.7"/>')
        self.M["shrines"].append({"x": x, "y": y, "w": w, "h": h, "label": label})
        rec = {"kind": kind, "x": x, "y": y, "w": w, "h": h, "label": label, "sublabel": sublabel, "graveyard": graveyard, "torii_outlier": torii_outlier}
        if torii:
            rec["torii_count"] = n_t  # the resolved roll/pin target - torii_match_roll gates drawn == target
        self.M["religious"].append(rec)  # torii_outlier=True exempts this hall from torii_count_canonical (a deliberately non-numerological gate count, always with a recorded story)
        if primary:
            self.M["shrine"] = [x - w / 2, y - h / 2, w, h]
        # block a RECT + a building-half margin, at the map's grain (an ellipse undershot the hall
        # corners). The 22px FLOOR (added with the true-size halls, 2026-07-21): packs test footprint
        # CENTERS, so the margin must absorb the check's +4px pad plus half the largest urban neighbor
        # (~29px merchant_large) at ANY scale - at city grain the raw 34*bscale is only ~11px and let a
        # merchant seat its edge into the hall's pad.
        bm = max(34 * self.bscale, 22.0)
        self.block_polys.append([(x - w / 2 - bm, y - h / 2 - bm), (x + w / 2 + bm, y - h / 2 - bm), (x + w / 2 + bm, y + h / 2 + bm), (x - w / 2 - bm, y + h / 2 + bm)])
        self._clear_ground(x, y, w, h, 58)  # the swept shrine precinct - scrub kept off the tended keidai (the grove, if any, is separate)
        if label:
            self.label(x, self._hall_caption_y(x, y, w, h, label, label_below, seats_t), label, HALL_CAPTION_FS, weight="bold", color=edge)
            # RESERVE the caption's own ground (GM 2026-07-27). Every gen that draws a hall had been
            # hand-writing a block_poly under its caption - Tango's Benten and Nagahara's Bishamon each
            # carry one, re-seated by hand every time the hall moved - and the moment _hall_caption_y
            # started choosing the side, those hand bands were reserving ground the caption had left.
            # A caption's band belongs to whoever knows where the caption went, which is here. The pad
            # absorbs half a dwelling, because block_polys is CENTER-tested (CLAUDE.md, "CENTER vs
            # FOOTPRINT"); the stale hand bands are now merely redundant, not wrong.
            _lb = self.M["labels"][-1]
            _lp = max(14 * self.bscale, 8.0)  # half a dwelling past the recorded box, which is already ~13% wider than the drawn glyphs
            self.block_polys.append([(_lb[0] - _lp, _lb[1] - _lp), (_lb[2] + _lp, _lb[1] - _lp), (_lb[2] + _lp, _lb[3] + _lp), (_lb[0] - _lp, _lb[3] + _lp)])
        if sublabel:
            self.label(x, y + h / 2 + 16, sublabel, 9, italic=True, color=edge)
