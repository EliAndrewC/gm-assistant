"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import math
import random
from typing import TYPE_CHECKING, Any

from ._geom import (
    HALL_CAPTION_FS,
    YARD_GLYPH_SLACK,
    Poly,
    Pt,
    label_tilt,
    point_in_poly,
    rail_quad,
    rects_overlap,
    rot_rect,
    sat_overlap,
    seg_closest,
    seg_dist,
    segments_cross,
    smooth_closed,
    tilt_caption_seat,
    trough_quad,
    wellhead_quad,
)
from ._knobs import BOUNDARY_MARKER_FT, BOUNDARY_MARKER_MIN_PX, CITY_TIER_SCALES, PUNISHMENT_SPOT_FT, execution_ground_ft

if TYPE_CHECKING:
    from .core import Settlement


class CivicGroundsMixin:
    def precinct_interior(self: Settlement, x: float, y: float, w: float = 130.0, h: float = 100.0, rear: str = "north", graveyard: bool = True) -> None:  # type: ignore[misc]
        """A SOVEREIGN TEMPLE PRECINCT's interior (feature 021, research item 7): the head-house
        program - abbot's residence, order administration, library/sutra hall, two monk
        dormitories, kitchen/refectory - drawn INSIDE the ground the 020 reservation held,
        densest toward the hall axis with the dormitories rearward (the shared Zen/Chinese
        seven-halls plan; the 390x300 ft reservation was sized for exactly this). `rear` names
        the side AWAY from the sando (the torii face), where the service program gathers; the
        front third stays open for the approach. Also claims the reservation itself: records
        M['precincts'] and holds both placement registries, replacing the hand-rolled 020
        reserve, and (graveyard=True) draws the parish burial plot that closes the temple's
        020 `graveyard` claim. Map-scale glyphs are footprint boxes in the religious palette,
        labeled never - the hall's own caption names the complex (caption-loudness)."""
        self.M.setdefault("precincts", []).append({"x": round(x, 1), "y": round(y, 1), "w": w, "h": h, "rear": rear, "graveyard": graveyard})
        self.block_polys.append([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)])
        self.placed.append((x, y, w, h))
        sgn = -1.0 if rear == "north" else 1.0  # rear-edge offsets flip with the sando side
        ye = y + sgn * h / 2
        # (dx, dy-from-rear-edge, w-ft, h-ft, kind) - hand-set so nothing clips the 150x100 ft hall
        prog = [
            (-44, 12, 48, 30, "residence"),
            (-45, 30, 36, 24, "kitchen"),
            (-8, 10, 57, 21, "dormitory"),
            (14, 22, 57, 21, "dormitory"),
            (52, None, 33, 24, "library"),
            (-54, None, 42, 27, "administration"),
        ]
        g = []
        for dx, dy, wf, hf, kind in prog:
            bw, bh = wf / self.ftpx, hf / self.ftpx
            bx = x + dx
            by = (y + sgn * 2) if dy is None else (ye - sgn * dy)
            g.append(f'<rect x="{bx - bw / 2:.1f}" y="{by - bh / 2:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="1.2" fill="#E6DCC4" stroke="#6E5B3A" stroke-width="1.1"/>')
            self.M.setdefault("precinct_halls", []).append({"x": round(bx, 1), "y": round(by, 1), "w": round(bw, 1), "h": round(bh, 1), "kind": kind, "precinct": [round(x, 1), round(y, 1)]})
        self.add_top("".join(g))
        if graveyard:
            self.cemetery(x + 44, ye - sgn * 14, 24, 16, parish=True)

    def cemetery(  # type: ignore[misc]
        self: Settlement,
        cx: float,
        cy: float,
        w: float,
        h: float,
        rot: float = 0,
        label: Any = None,
        label_above: bool = False,
        parish: bool = True,
        organic: bool | None = None,
        label_xy: Pt | None = None,
    ) -> None:
        """A BURIAL GROUND - rows of grave markers (sotoba / stone stelae) with a couple of taller
        memorial stupas. Every settlement above a hamlet buries its dead: a Buddhist danka PARISH
        ground sits in a TEMPLE / MONASTERY precinct (death is the Buddhist clergy's business), while
        a Shinto SHRINE keeps death-pollution (kegare) at arm's length - so a graveyard sits well
        clear of any shrine. parish=False marks a NON-parish burial ground (a village-style plot not
        attached to a temple, e.g. one serving an in-wall farm quarter) - exempt from the temple-precinct
        rule. organic=True draws an IRREGULAR earthen plot; organic=None (the default) DERIVES it from
        parish: every non-parish COMMON ground is organic, parish precinct plots stay ruled rectangles.
        Historical grounding (researched 2026-07-23, written up in settlements.md 'shape of the common
        ground'): Japan's commoner burial grounds - Kyoto's burial fields, village sanmai, Edo's packed
        temple yards - were unplotted and terrain-following, never surveyed; Song China's state pauper
        cemeteries (louzeyuan, 1104 on) WERE surveyed walled compounds with numbered rowed plots, so a
        specific ordered city may pass organic=False to draw that Chinese form deliberately. Rokugan
        defaults to the Japanese mode (GM decision). The recorded bbox + the no-build block stay the
        w x h rectangle either way, so the placement/clearance checks are unaffected - only the DRAWN
        ground and the markers within it follow the blob. Records M['cemeteries'] and blocks placement.
        label_above puts the label over the plot (for a cramped intramural ground whose label would otherwise spill onto its temple)."""
        if organic is None:
            organic = not parish
        st = random.getstate()
        random.seed(int(abs(cx) + abs(cy) * 3 + w))
        g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({rot:.1f})">']
        if organic:  # a jittered blob INSCRIBED in the w x h footprint - star-shaped from the center
            blob = [(math.cos(a) * (w / 2) * jr, math.sin(a) * (h / 2) * jr) for a, jr in ((2 * math.pi * i / 14, random.uniform(0.74, 1.0)) for i in range(14))]
            g.append(f'<path d="{smooth_closed(blob)}" fill="#CFC6B4" stroke="#8C8470" stroke-width="1.3" opacity="0.75"/>')
        else:
            blob = None
            g.append(f'<rect x="{-w / 2:.1f}" y="{-h / 2:.1f}" width="{w:.0f}" height="{h:.0f}" rx="3" fill="#CFC6B4" stroke="#8C8470" stroke-width="1.3" opacity="0.75"/>')
        yy = -h / 2 + 9
        while yy < h / 2 - 5:  # rows of small upright grave markers (kept inside the blob)
            xx = -w / 2 + 8
            while xx < w / 2 - 5:
                if blob is None or point_in_poly(xx, yy, blob):
                    mh = random.choice([6, 7, 8])
                    g.append(f'<rect x="{xx - 1.4:.1f}" y="{yy - mh:.1f}" width="2.8" height="{mh}" rx="1" fill="#9AA1A4" stroke="#5A584F" stroke-width="0.5"/>')
                xx += 9
            yy += 9
        stupas = (
            [(-w * 0.24, -h * 0.22), (w * 0.24, -h * 0.22)]
            if organic  # interior anchors (always inside the blob)
            else [(-w / 2 + 13, -h / 2 + 1), (w / 2 - 13, -h / 2 + 1)]
        )  # a couple of taller memorial stupas
        for sxp, syp in stupas:
            g.append(f'<rect x="{sxp - 2.2:.1f}" y="{syp:.1f}" width="4.4" height="13" rx="1.5" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.7"/>')
            g.append(f'<circle cx="{sxp:.1f}" cy="{syp:.1f}" r="2.4" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.7"/>')
        random.setstate(st)
        g.append('</g>')
        self.add(''.join(g))
        self.M.setdefault("cemeteries", []).append({"x": round(cx, 1), "y": round(cy, 1), "w": w, "h": h, "rot": round(rot, 1), "parish": parish})
        self.placed.append((cx, cy, w, h))
        bm = 8
        self.block_polys.append([(cx - w / 2 - bm, cy - h / 2 - bm), (cx + w / 2 + bm, cy - h / 2 - bm), (cx + w / 2 + bm, cy + h / 2 + bm), (cx - w / 2 - bm, cy + h / 2 + bm)])
        self._clear_ground(cx, cy, w, h, 30)  # the tended grave collar - scrub trimmed back off the markers (the waste around it stays scrubby)
        if label:
            ly = cy - h / 2 - 8 if label_above else cy + h / 2 + 14
            # label_xy slides the caption ALONG the plot it names (it must still hug it) - a parish
            # graveyard often sits shoulder to shoulder with its temple, and the two captions can meet
            _lx, _ly = label_xy if label_xy else (cx, ly)
            self.label(_lx, _ly, label, 11, italic=True, color="#6B5A3C")

    def _ward_fence_cap(self: Settlement, a: Any, b: Any, tol: float = 16) -> int | None:  # type: ignore[misc]
        """If the axis-aligned wall segment a-b runs ALONG a neighborhood (ward) fence, re-stamp the
        fence stroke over it so the FENCE renders ON TOP - the compound's own wall runs underneath, and
        the fence IS that side of the compound (no doubled, clashing parallel walls). Mirrors how a
        ward's own ends run under the city rampart. Returns the cap's z if it stamped one, else None."""
        ax, ay = a
        bx, by = b
        horiz = abs(ax - bx) >= abs(ay - by)
        for w in self.M.get("wards", []):
            bnd = w["boundary"]
            for i in range(len(bnd) - 1):
                px, py = bnd[i]
                qx, qy = bnd[i + 1]
                if (abs(px - qx) >= abs(py - qy)) != horiz:  # fence segment must run the same way
                    continue
                if horiz:
                    if abs(py - ay) > tol:
                        continue
                    lo, hi = max(min(ax, bx), min(px, qx)), min(max(ax, bx), max(px, qx))
                    if hi - lo < 10:
                        continue
                    dd = f'M{lo:.0f},{ay:.0f} L{hi:.0f},{ay:.0f}'
                else:
                    if abs(px - ax) > tol:
                        continue
                    lo, hi = max(min(ay, by), min(py, qy)), min(max(ay, by), max(py, qy))
                    if hi - lo < 10:
                        continue
                    dd = f'M{ax:.0f},{lo:.0f} L{ax:.0f},{hi:.0f}'
                self.add(f'<path d="{dd}" fill="none" stroke="#9C8A5E" stroke-width="5" opacity="0.9" stroke-linecap="round"/>')
                z = self.add(f'<path d="{dd}" fill="none" stroke="#4A3A22" stroke-width="1.3" stroke-dasharray="2,7" opacity="0.85"/>')  # palisade dash
                return z
        return None

    def mausoleum(self: Settlement, cx: float, cy: float, w: float, h: float, label: str = "Ancestral Mausoleum", gate_dir: str = "south", label_below: bool = False) -> None:  # type: ignore[misc]
        """A walled CRYPT PRECINCT - the ruling clan's ancestral mausoleum, where important samurai are
        interred in crypts and stone monuments after cremation. A prestige ground sited by the SAMURAI /
        government quarter (ancestor veneration is central to samurai identity), religiously staffed but a
        martial-clan monument distinct from the commoner temple graveyards. A walled court (like a manor)
        holding a stone crypt hall and a few tall memorial stupas. Records M['mausoleums']; blocks placement."""
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" fill="#E7DDC4"/>')  # the swept precinct court
        wall = '#3A352C'
        sides = {"north": ((x0, y0), (x1, y0), cx, y0), "south": ((x0, y1), (x1, y1), cx, y1), "west": ((x0, y0), (x0, y1), x0, cy), "east": ((x1, y0), (x1, y1), x1, cy)}
        mgg = max(self.px(12) / 2, 2.0)  # ceremonial gate: ~12 real ft opening (half-gap), floored
        mww = max(self.px(2), 2.0)  # precinct wall ~2 ft, 2px cartographic floor (GM 2026-07-19 to-scale rule)
        for name, (a, b, gx, gy) in sides.items():
            if name != gate_dir:
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="{mww:.1f}"/>')
            elif name in ("west", "east"):  # vertical wall - gap in y
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{a[0]:.0f}" y2="{gy - mgg:.1f}" stroke="{wall}" stroke-width="{mww:.1f}"/>')
                self.add(f'<line x1="{b[0]:.0f}" y1="{gy + mgg:.1f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="{mww:.1f}"/>')
            else:  # horizontal wall - gap in x
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{gx - mgg:.1f}" y2="{a[1]:.0f}" stroke="{wall}" stroke-width="{mww:.1f}"/>')
                self.add(f'<line x1="{gx + mgg:.1f}" y1="{b[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="{mww:.1f}"/>')
        # a wall that ABUTS a neighborhood (ward) fence yields to it: the fence is re-stamped over our
        # own wall there, so it renders ON TOP and IS that side of the precinct (recorded for the gate)
        ward_walls = [name for name, (a, b, gx, gy) in sides.items() if name != gate_dir and self._ward_fence_cap(a, b) is not None]
        hw, hh = min(w * 0.42, 86), min(h * 0.34, 52)  # the stone crypt hall, centered
        self.add(f'<rect x="{cx - hw / 2:.0f}" y="{cy - hh / 2:.0f}" width="{hw:.0f}" height="{hh:.0f}" rx="2" fill="#C9C0AE" stroke="#5A584F" stroke-width="2"/>')
        self.add(f'<rect x="{cx - hw / 2:.0f}" y="{cy - hh / 2:.0f}" width="{hw:.0f}" height="8" fill="#7A5A30"/>')  # the hall's roof band
        for sx in (x0 + 16, x1 - 16):  # tall memorial stupas flanking the hall
            self.add(f'<rect x="{sx - 3:.0f}" y="{cy - 9:.0f}" width="6" height="18" rx="2" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.8"/>')
            self.add(f'<circle cx="{sx:.0f}" cy="{cy - 9:.0f}" r="3.4" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.8"/>')
        self.M["mausoleums"].append({"x": cx, "y": cy, "w": w, "h": h, "rot": 0, "label": label, "gate_dir": gate_dir, "ward_walls": ward_walls, "gate_w": round(2 * mgg, 2), "wall_w": round(mww, 2)})
        self._assert_walls_clear_of_torii("the mausoleum wall")
        self.placed.append((cx, cy, w, h))
        m = 30 * self.bscale  # a building-half margin at the map's grain
        self.block_polys.append([(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)])
        if label:
            ly = y1 + 14 if label_below else y0 - 12
            # HALL_CAPTION_FS, not a rank size: a clan crypt's glyph is a hall-class walled compound
            # (Minami's is 132x96 real ft against a temple hall's 130x84), so it takes the hall's
            # caption. At its old 12pt it came out the LOUDEST body text on a city sheet once the
            # temple halls dropped to 9 - above the governor's yamen at 11, whose compound is 525x300
            # ft - which is the size-by-rank ladder the whole change exists to remove.
            self.label(cx, ly, label, HALL_CAPTION_FS, weight="bold", italic=True, color="#3A352C")

    def cremation_ground(self: Settlement, cx: float, cy: float, label: str = "cremation ground", label_above: bool = False) -> None:  # type: ignore[misc]
        """The CREMATORY (kasoba) - where the dead are burned before their bones are interred. Smoke, fire
        risk, and death-pollution put it OUTSIDE the walls; monks officiate with burakumin assistants (a
        religious order stands outside the caste system, so handling the dead does not pollute its caste).
        A cleared, scorched ground with a raised stone pyre platform, a wisp of smoke, and a small roofed
        shelter for the rite. Records M['cremation_grounds']; blocks placement."""
        # TO SCALE (GM 2026-07-19; anchors in settlements.md): a sanmai's cleared working core is
        # 30-80 real ft for a village/town, ~80-160 ft for a provincial city (even metropolitan
        # Edo's Yoyogi crematory was only ~180 ft square); the pyre platform ~15x10 ft. The old
        # glyph was FIXED-PIXEL (116x80px) and silently tripled at city scale.
        across = 130.0 if self.M["meta"].get("scale") in CITY_TIER_SCALES else 75.0
        crx, cry = max(self.px(across) / 2, 14.0), max(self.px(across * 0.7) / 2, 10.0)
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{crx:.1f}" ry="{cry:.1f}" fill="#C9BCA0" stroke="#8C7A56" stroke-width="1.5" opacity="0.85"/>')  # cleared scorched ground
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{crx * 0.58:.1f}" ry="{cry * 0.55:.1f}" fill="#9A8A6A" opacity="0.5"/>')  # the burned center
        ppw, pph = max(self.px(15), 7.0), max(self.px(10), 5.0)
        self.add(
            f'<rect x="{cx - ppw / 2:.1f}" y="{cy - pph / 2:.1f}" width="{ppw:.1f}" height="{pph:.1f}" rx="1.5" fill="#8C8470" stroke="#4A463C" stroke-width="1.2"/>'
        )  # stone pyre platform (~15x10 ft)
        abw, abh = max(self.px(12), 5.0), max(self.px(8), 3.6)  # the ash bed ON the platform (~12x8 ft burn area)
        self.add(f'<rect x="{cx - abw / 2:.1f}" y="{cy - abh / 2:.1f}" width="{abw:.1f}" height="{abh:.1f}" fill="#5A463A"/>')  # the ash bed
        shw, shh = max(self.px(14), 7.0), max(self.px(10), 5.0)  # the officiants' shelter (~14x10 ft hut)
        shx = cx + crx * 0.52
        self.add(f'<rect x="{shx:.1f}" y="{cy - shh / 2:.1f}" width="{shw:.1f}" height="{shh:.1f}" rx="1.5" fill="#CDB890" stroke="#5A4326" stroke-width="1.2"/>')
        self.add(f'<rect x="{shx:.1f}" y="{cy - shh / 2:.1f}" width="{shw:.1f}" height="{shh * 0.32:.1f}" fill="#5A4326"/>')
        self.M["cremation_grounds"].append({"x": round(cx, 1), "y": round(cy, 1), "w": round(2 * crx, 1), "h": round(2 * cry, 1), "rot": 0})
        self.placed.append((cx, cy, 2 * crx, 2 * cry))
        m = 8
        self.block_polys.append([(cx - crx - m, cy - cry - m), (cx + crx + m, cy - cry - m), (cx + crx + m, cy + cry + m), (cx - crx - m, cy + cry + m)])
        if label:
            self.label(cx, cy - cry - 8 if label_above else cy + cry + 14, label, 11, italic=True, color="#6B5A3C")

    def ossuary(self: Settlement, cx: float, cy: float, label: str = "pauper ossuary mound") -> None:  # type: ignore[misc]
        """A PAUPER OSSUARY MOUND - a communal earthen mound where the bones of the poor and the
        'unconnected dead' (muenbotoke - those with no family or temple to inter them) are gathered, by
        the cremation ground outside the walls. A low rounded mound with a single weathered marker stupa.
        Records M['ossuaries']; blocks placement."""
        # TO SCALE (GM 2026-07-19, tightened 2026-07-21): a muenzuka is a 10-30 real-ft mound
        # (cremated, consolidated bone takes almost no volume; Kyoto's monumental Mimizuka, a state
        # monument, is ~50 ft at the base). Drawn at ~22 ft, mid-band. History of this constant: the
        # original glyph was FIXED-PIXEL (92x60px = a 276 ft kofun at city scale); the first fix drew
        # ~40 ft with a 9px floor, which STILL rendered 54 real ft at city scale - the floor, not the
        # size, controlled. The floor is now 4.5px (27 ft at city, inside the band) - a stroke-
        # convention minimum for visibility, never a size license.
        orx = max(self.px(22) / 2, 4.5)
        ory = orx * 0.62
        self.add(f'<ellipse cx="{cx}" cy="{cy + ory * 0.2:.1f}" rx="{orx:.1f}" ry="{ory:.1f}" fill="#BCA878" stroke="#8C7A52" stroke-width="1.5"/>')  # the earthen mound
        self.add(f'<ellipse cx="{cx}" cy="{cy - ory * 0.1:.1f}" rx="{orx * 0.64:.1f}" ry="{ory * 0.55:.1f}" fill="#C8B584" opacity="0.7"/>')  # the crown (shading)
        self.add(f'<rect x="{cx - 2:.0f}" y="{cy - ory - 8:.1f}" width="4" height="9" rx="1.5" fill="#A8A294" stroke="#5A584F" stroke-width="0.8"/>')  # a weathered marker stupa
        self.add(f'<circle cx="{cx:.0f}" cy="{cy - ory - 8:.1f}" r="2.6" fill="#A8A294" stroke="#5A584F" stroke-width="0.8"/>')
        self.M["ossuaries"].append({"x": round(cx, 1), "y": round(cy, 1), "w": round(2 * orx, 1), "h": round(2 * ory, 1), "rot": 0})
        self.placed.append((cx, cy, 2 * orx, 2 * ory))
        m = 8
        self.block_polys.append([(cx - orx - m, cy - ory - m), (cx + orx + m, cy - ory - m), (cx + orx + m, cy + ory + m), (cx - orx - m, cy + ory + m)])
        if label:
            self.label(cx, cy + ory + 12, label, 11, italic=True, color="#6B5A3C")

    def punishment_spot(self: Settlement, x: float, y: float, rot: float = 0.0, label: str | None = "punishment ground", label_above: bool = False, label_xy: Pt | None = None) -> None:  # type: ignore[misc]
        """The PUNISHMENT GROUND - the everyday face of the magistrate's authority, in the middle of
        town: a cangue frame, a flogging post, and a kneeling stone on a patch of tamped earth at the
        market or the magistracy frontage. ~30x12 ft, true size at every tier.

        Historical grounding (the "why" - see settlements.md "Punishment spot"):
          - This is a DISPLAY installation, not a place of execution and not a courtroom. The Chinese
            evidence splits the two cleanly: the bamboo beating (chi / zhang) was a COURT act
            administered inside the yamen courtyard in front of the magistrate's bench - which in our
            maps is the Mode A magistracy, already drawn - while the 枷 jia, the cangue, was public.
            An offender wore it for one to six months with THEIR NAME, THE CRIME, AND THE SENTENCE
            inscribed on the boards in large characters, displayed at a marketplace, a crossroads, or
            an official gate. Japan corroborates from the other side: sarashi (exposure) and the
            public flogging post sat at the bottom of the Edo punishment ladder.
          - GOVERNING VARIABLE: foot traffic. Both traditions site the display where the most people
            pass, not where it is administratively convenient - the same criterion the notice board
            already answers to (kosatsuba_by_the_road).
          - It draws NO notice board. The crime text rides on the cangue itself, exactly as the
            historical inscription did, and the settlement already has a kosatsuba (a separate
            institution posting the state's standing law) plus the magistrate's own gate board in the
            Mode A program. A third board here would be a modeling error dressed up as detail.

        Records M['punishment_spots']; reserves ground. Call BEFORE the urban packs - it sits where
        packing pressure is highest, and reserving after the pack means fighting for a seat that no
        longer exists (see the DRAW ORDER map in this skill's CLAUDE.md)."""
        w, h = self.px(PUNISHMENT_SPOT_FT[0]), self.px(PUNISHMENT_SPOT_FT[1])
        hw, hh = w / 2, h / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{h:.1f}" rx="1" fill="#C6B79A" fill-opacity="0.9" stroke="#8A7550" stroke-width="1.0"/>')  # tamped, foot-polished earth
        cw = self.px(5)  # the CANGUE frame - the heavy board collar, seen from above as a slotted square
        g.append(f'<rect x="{-hw + self.px(2):.1f}" y="{-cw / 2:.1f}" width="{cw:.1f}" height="{cw:.1f}" rx="0.6" fill="#B49A6E" stroke="#5A4526" stroke-width="1.0"/>')
        g.append(f'<circle cx="{-hw + self.px(2) + cw / 2:.1f}" cy="0" r="{max(cw * 0.22, 0.9):.1f}" fill="#4A3D28"/>')  # the neck hole
        g.append(f'<ellipse cx="0" cy="0" rx="{max(self.px(1.6), 1.0):.1f}" ry="{max(self.px(1.1), 0.8):.1f}" fill="#A8A294" stroke="#5A584F" stroke-width="0.7"/>')  # the kneeling stone
        pr = max(self.px(0.9), 0.9)  # the FLOGGING POST
        g.append(f'<circle cx="{hw - self.px(3):.1f}" cy="0" r="{pr:.1f}" fill="#7A5A30" stroke="#4A3418" stroke-width="0.8"/>')
        g.append("</g>")
        self.add_top("".join(g))
        self.M["punishment_spots"].append({"x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1), "rot": round(rot, 1), "label": label})
        self.placed.append((x, y, w, h))
        bm = 6
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])
        if label:
            # The ground belongs at the magistracy frontage, which is the most label-congested ground
            # on a town map - so it needs both escapes. `label_above` flips the side; `label_xy` places
            # the label outright (the paddy_field convention), for the case Hoshizora hit, where the
            # only clear VERGE for the ground sits directly under the manor's own label box and the
            # only clear TEXT band is a little further down, between that label and the manor itself.
            _t = label_tilt(rot)
            if label_xy:
                lx, ly = label_xy
            elif _t:
                lx, ly = tilt_caption_seat(x, y, rot, _t, hw, hh, 9 if label_above else 11, above=label_above)
            else:
                lx, ly = (x, y - hh - 9) if label_above else (x, y + hh + 11)
            self.label(lx, ly, label, 9, italic=True, color="#6B5A3C", rot=_t)

    def execution_ground(self: Settlement, cx: float, cy: float, rot: float = 0.0, screened: bool | None = None, label: str | None = "execution ground", label_above: bool = False) -> None:  # type: ignore[misc]
        """The EXECUTION GROUND (keijou) - bare waste ground on the road past the settlement's
        boundary stone, where the Empire carries out the death sentences its magistrates confirm.
        `rot` lays the ground's ROAD SIDE (local -y, where the head-display stand faces) toward the
        road, the same convention the tanning yard uses for its water side.

        Historical grounding (the "why" - see settlements.md "Execution ground"):
          - WHY A COUNTY SEAT HAS ONE AT ALL. China and Japan disagree here and the reconciliation is
            load-bearing. Japan monopolized executions at castle towns and pushed them outside the
            settlement for kegare (death pollution); village authority topped out at banishment. But
            under the Chinese system a county magistrate could not CONFIRM a death sentence - capital
            cases climbed to the Board of Punishments and the emperor's autumn check-marking - and
            the confirmed sentence came back DOWN to be carried out at the county seat where the
            crime happened, because local deterrence was the entire point. So: China supplies the
            jurisdiction (the seat executes), Japan supplies the siting (outside the built edge).
            This is also why the canon county budget funds a jail with no execution line while
            "ceremonial executions" appear only at domain and Imperial level - the county jail is a
            HOLDING PEN for the condemned while the warrant travels, not a punishment in itself.
          - GOVERNING VARIABLE: the road and the direction of pollution - NOT population, and not the
            settlement's geometric edge. The ground exists to be seen by travelers arriving, so it
            sits on the busiest road; kegare puts it downwind, downstream, and on the outcast side,
            beyond the burakumin quarter.
          - SIZE. Suzugamori, which served Edo (a city of one million) for 220 years, measured
            74 x 16.2 m - about 243 x 53 ft, a third of an acre. Execution grounds are SMALL; the
            deterrent is the sight of the posts from the highway, not acreage. Our tiers scale down
            from that anchor by execution volume.
          - VOLUME, which is what sets the county tier's CHARACTER. At ~1-3 executions per 100,000
            per year, a county of ~7,000-8,000 inhabitants reaches the formal channel about once
            every 5-10 years (bandit sweeps add batches). So a county ground is a weedy, half-
            forgotten patch with socket stones and no standing posts - it must read DISUSED. Only at
            city scale and above does it earn screening and permanent furniture. Drawing a county
            ground as a busy scaffold would assert something false about how often Rokugan kills.

        Records M['execution_grounds']; reserves ground. Call beside the funerary cluster (phase 4),
        before the hinterland scrub and village_grove, so no crown is drawn onto it."""
        city = self.M["meta"].get("scale") in CITY_TIER_SCALES
        _gwft, _ghft = execution_ground_ft("city" if city else "town")
        gw, gh = self.px(_gwft), self.px(_ghft)
        if screened is None:
            screened = city  # a county ground is open to the road on every side; a city ground is hoarded on three
        hw, hh = gw / 2, gh / 2
        g = [f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot:.1f})">']
        # the bare ground itself: pale, dry, unbunded - deliberately unlike both the field greens and
        # the built tans, because "this is not farmland and not a yard" is the whole read. The dashed
        # edge says the ground has no boundary anyone maintains.
        g.append(f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{gw:.1f}" height="{gh:.1f}" rx="2" fill="#CFC6B4" stroke="#8F8566" stroke-width="1.2" stroke-dasharray="4,3"/>')
        if screened:  # the hoarding - three sides, the ROAD side (local -y) left open, because being seen is the point
            sx, sy = hw + self.px(1), hh + self.px(1)
            g.append(f'<path d="M {-sx:.1f} {-sy:.1f} L {-sx:.1f} {sy:.1f} L {sx:.1f} {sy:.1f} L {sx:.1f} {-sy:.1f}" fill="none" stroke="#6B5A3C" stroke-width="1.6"/>')
        # the CRUCIFIXION SOCKETS - stone bases with a square mortise. The permanent thing at a county
        # ground is the SOCKET, not a standing post: posts were raised for a sentence and taken down.
        for i in (-1, 1):
            sxp, syp = i * gw * 0.22, -gh * 0.16
            ss = max(self.px(3), 2.0)
            g.append(f'<rect x="{sxp - ss / 2:.1f}" y="{syp - ss / 2:.1f}" width="{ss:.1f}" height="{ss:.1f}" rx="0.5" fill="#A8A294" stroke="#4A463C" stroke-width="0.8"/>')
            g.append(f'<rect x="{sxp - ss / 6:.1f}" y="{syp - ss / 6:.1f}" width="{ss / 3:.1f}" height="{ss / 3:.1f}" fill="#3A352C"/>')  # the mortise, standing empty
        stk = max(self.px(1.2), 1.0)  # the IRON STAKE for burning - Edo burned arsonists, and a Rokugani town fears fire above all
        g.append(f'<circle cx="0" cy="{gh * 0.30:.1f}" r="{stk:.1f}" fill="#4A463C" stroke="#2E2A22" stroke-width="0.7"/>')
        bw, bh = max(self.px(10), 4.0), max(self.px(6), 3.0)  # the SAND BED with its head-hole
        g.append(f'<rect x="{-bw / 2:.1f}" y="{-gh * 0.34 - bh / 2:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="1" fill="#DED3B4" stroke="#9A8A63" stroke-width="0.8"/>')
        g.append(f'<circle cx="0" cy="{-gh * 0.34:.1f}" r="{max(bh * 0.2, 0.8):.1f}" fill="#5A463A"/>')
        dw = max(self.px(8), 4.0)  # the HEAD-DISPLAY STAND with its crime board, on the ROAD side, facing out
        g.append(f'<rect x="{-dw / 2:.1f}" y="{-hh + self.px(2):.1f}" width="{dw:.1f}" height="{max(self.px(2.5), 1.4):.1f}" rx="0.5" fill="#8A7550" stroke="#4A3418" stroke-width="0.8"/>')
        g.append(f'<line x1="{dw * 0.75:.1f}" y1="{-hh + self.px(1):.1f}" x2="{dw * 0.75:.1f}" y2="{-hh + self.px(6):.1f}" stroke="#5A4326" stroke-width="1.1"/>')  # the crime board's post
        wr = max(
            self.px(2.0), 1.6
        )  # the WELL - for washing the blade and sluicing the ground (Suzugamori kept one). Drawn, NOT recorded in M['wells']: it serves no household and must not enter the well-density accounting.
        g.append(f'<circle cx="{-gw * 0.34:.1f}" cy="{gh * 0.30:.1f}" r="{wr:.1f}" fill="#B9C7C4" stroke="#4A5A58" stroke-width="0.9"/>')
        pw_, ph_ = max(self.px(12), 5.0), max(self.px(8), 3.5)  # the DISPOSAL PIT, at the back - the executed are not carried to the community's ground
        g.append(f'<ellipse cx="{gw * 0.30:.1f}" cy="{gh * 0.30:.1f}" rx="{pw_ / 2:.1f}" ry="{ph_ / 2:.1f}" fill="#8C7A56" stroke="#5A4A30" stroke-width="0.9"/>')
        if not screened:  # WEEDS: the county ground is used about once a decade, so it must read DISUSED
            for wx, wy in ((-0.30, -0.36), (0.34, -0.30), (-0.16, 0.10), (0.20, 0.06), (-0.36, 0.14)):
                g.append(f'<path d="M {wx * gw:.1f} {wy * gh:.1f} l -1.4 -3.0 M {wx * gw:.1f} {wy * gh:.1f} l 1.4 -3.2" fill="none" stroke="#8A9464" stroke-width="0.8"/>')
        g.append("</g>")
        self.add("".join(g))
        self.M["execution_grounds"].append({"x": round(cx, 1), "y": round(cy, 1), "w": round(gw, 1), "h": round(gh, 1), "rot": round(rot, 1), "screened": bool(screened), "label": label})
        self.placed.append((cx, cy, gw, gh))
        bm = 8
        self.block_polys.append([(cx - hw - bm, cy - hh - bm), (cx + hw + bm, cy - hh - bm), (cx + hw + bm, cy + hh + bm), (cx - hw - bm, cy + hh + bm)])
        if label:
            # label_above: the ground shares the settlement's outskirts with the polluting trades
            # (kiln, tanning yard), whose small glyphs the default below-label can land on
            _t = label_tilt(rot)
            _lx, _ly = tilt_caption_seat(cx, cy, rot, _t, hw, hh, 8 if label_above else 13, above=label_above) if _t else ((cx, cy - hh - 8) if label_above else (cx, cy + hh + 13))
            self.label(_lx, _ly, label, 11, italic=True, color="#6B5A3C", rot=_t)

    def boundary_marker(self: Settlement, x: float, y: float, rot: float = 0.0, label: str | None = "boundary stone", label_xy: Pt | None = None) -> None:  # type: ignore[misc]
        """A DOSOJIN (sae no kami) stone at the settlement's ritual boundary - where the road leaves
        clean ground. Usually a paired male-female figure carved on one stone.

        Historical grounding (the "why" - see settlements.md "Boundary marker"): dosojin stand at
        village boundaries, mountain passes, and crossroads, and the etymology is the point - `sae`
        means "to block", and the deity's job is to stop evil, pestilence, and POLLUTION from
        entering the settlement. That is what makes it structural rather than decorative here: it
        turns "outside the settlement" from a vague spatial claim into a stated ritual boundary, and
        gives the execution ground its reason for being where it is. The ground is not merely far
        from the houses; it is on the far side of the stone that keeps pollution out.

        A LOCATION MARKER: a real stone is ~3 ft, sub-glyph at every tier, so the true footprint is
        recorded in w/h and the drawn box in vw/vh - the wells' and kosatsuba's doctrine exactly
        (SKILL.md "to scale"). Records M['boundary_markers']."""
        w = h = self.px(BOUNDARY_MARKER_FT)
        k = max(1.0, BOUNDARY_MARKER_MIN_PX / w)  # marker floor, aspect preserved
        vw, vh = w * k, h * k
        hw, hh = vw / 2, vh / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{vw:.1f}" height="{vh:.1f}" rx="{hw * 0.6:.1f}" fill="#A8A294" stroke="#4A463C" stroke-width="0.9"/>')  # the weathered stone
        g.append(f'<line x1="0" y1="{-hh * 0.5:.1f}" x2="0" y2="{hh * 0.5:.1f}" stroke="#4A463C" stroke-width="0.7"/>')  # the seam between the paired figures
        g.append("</g>")
        self.add_top("".join(g))
        self.M["boundary_markers"].append({"x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1), "vw": round(vw, 1), "vh": round(vh, 1), "rot": round(rot, 1), "label": label})
        self.placed.append((x, y, vw, vh))
        if label:
            # the default below-seat lands on the road the stone stands beside, which at a city gate
            # is the gate throat itself - label_xy hands it to open ground (Nagahara's east gate)
            _t = label_tilt(rot)
            _lx, _ly = label_xy if label_xy else (tilt_caption_seat(x, y, rot, _t, hw, hh, 10) if _t else (x, y + hh + 10))
            self.label(_lx, _ly, label, 8, italic=True, color="#6B5A3C", rot=_t)

    def district(self: Settlement, name: str, kind: str, poly: Any, rank_band: str | None = None) -> None:  # type: ignore[misc]
        """A declared fabric DISTRICT (feature 021): a named placement region for the housing
        packs and the ground truth for capital_rank_gradient. A declarative overlay like
        quarter() - draws nothing and reserves nothing; the packs it names do the drawing.
        Records M['districts'] {name, kind, poly, rank_band?}; kinds: yashiki, detached,
        terrace, machi, monzen, entertainment."""
        rec: dict[str, Any] = {"name": name, "kind": kind, "poly": [list(p) for p in poly]}
        if rank_band is not None:
            rec["rank_band"] = rank_band
        self.M.setdefault("districts", []).append(rec)

    def terrace(self: Settlement, x: float, y: float, units: int = 6, rot: float = 0.0, frontage_ft: float = 18.0, depth_ft: float = 21.0) -> int:  # type: ignore[misc]
        """A RETAINER TERRACE range (feature 021): ONE roof over `units` single-file household
        cells divided by party walls - the kumi-yashiki/nagaya form. Research (021 item 2):
        cells of 4.5-8 tatami behind an earth-floored entry, ~18 ft frontage each, ~21 ft
        deep (Shibata's 8-cell 143 x 21 ft range is the anchor); detached cottages were the
        Kanazawa EXCEPTION, so the glyph is a continuous roof with drawn seams, not houses at
        row pitch. In Rokugan these house junior SAMURAI (Ranks 1-4) - ashigaru are peasants
        and have no capital quarter (GM 2026-08-08). Records M['terraces']
        {x, y, w, h, rot, units, z}; classified SOLID in the keep-clear contract."""
        w, h = units * frontage_ft / self.ftpx, depth_ft / self.ftpx
        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-w / 2:.1f}" y="{-h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="1.5" fill="#C9B892" stroke="#6E5B3A" stroke-width="1.4"/>')
        step = w / units
        for i in range(1, units):
            sx = -w / 2 + i * step
            g.append(f'<line x1="{sx:.1f}" y1="{-h / 2:.1f}" x2="{sx:.1f}" y2="{h / 2:.1f}" stroke="#6E5B3A" stroke-width="0.9" opacity="0.8"/>')
        g.append("</g>")
        z = self.add_top("".join(g))
        self.M.setdefault("terraces", []).append({"x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1), "rot": round(rot, 1), "units": units, "z": z})
        # reserve the AXIS-ALIGNED BBOX of the rotated range, not the unrotated w x h: a rot=90
        # file reserves a wide/short phantom otherwise, and place_wells seated a wellhead ON the
        # Shiro Daika gate terraces through exactly that gap (found 2026-08-10, feature 021)
        ta = math.radians(rot)
        self.placed.append((x, y, abs(w * math.cos(ta)) + abs(h * math.sin(ta)), abs(w * math.sin(ta)) + abs(h * math.cos(ta))))
        return z

    def granary(self: Settlement, x: float, y: float, n: int = 3, w: float = 58, h: float = 34, gap: float = 14, label: str = "granary", append: bool = False, rot: float = 0.0) -> list[Any]:  # type: ignore[misc]
        """A short row of fireproof storehouses (kura) - the tax-rice granary of a rice-TRANSIT
        town, where grain from many counties is gathered and forwarded up the kick-up chain.
        White-walled with a dark hip roof. Opt-in (meta(granary=True)): a standard county seat
        keeps its grain inside the magistrate's yamen, so it is NOT drawn separately. Records to
        M['granary'] (gated by town_has_granary) and blocks houses, like the manor.
        append=True records each store into the M['granaries'] LIST instead and leaves the legacy
        dict untouched: a capital holds its grain in TWO places for two reasons (the domain's
        working stipend rice at the wharf, the Emperor's stores beside it - and the siege stock
        inside the castle, never drawn), and a second call on the dict would silently clobber the
        first. Per-store records, so the overlap matrix can see each one (feature 019's lesson).
        `rot` turns the whole row (degrees) so a riverside complex can stand parallel to its bank
        (GM 2026-08-09: the wharf granaries belong ON the wharf, aligned with the water they
        serve); the rot=0 path is byte-identical to the old drawing for every existing map."""
        stores: list[Any] = []
        ga = math.radians(rot)
        gca, gsa = math.cos(ga), math.sin(ga)
        x0 = x - (n * w + (n - 1) * gap) / 2
        for i in range(n):
            cx = x0 + i * (w + gap) + w / 2
            if rot:
                rcx, rcy = x + (cx - x) * gca, y + (cx - x) * gsa  # the store's seat along the turned row axis
                gg_ = [f'<g transform="translate({rcx:.1f},{rcy:.1f}) rotate({rot:.1f})">']
                gg_.append(f'<rect x="{-w / 2:.0f}" y="{-h / 2:.0f}" width="{w}" height="{h}" rx="2" fill="#E8E0CE" stroke="#6B5A3C" stroke-width="2"/>')
                gg_.append(f'<rect x="{-w / 2:.0f}" y="{-h / 2:.0f}" width="{w}" height="9" fill="#5A4A30"/>')
                gg_.append(f'<line x1="0" y1="{-h / 2 + 9:.0f}" x2="0" y2="{h / 2:.0f}" stroke="#6B5A3C" stroke-width="0.7"/>')
                gg_.append("</g>")
                self.add("".join(gg_))
                stores.append({"x": round(rcx, 1), "y": round(rcy, 1), "w": w, "h": h, "rot": rot})
                self.block_polys.append([(round(qx, 1), round(qy, 1)) for qx, qy in rot_rect(rcx, rcy, w + 60, h + 60, rot)])
                continue
            self.add(f'<rect x="{cx - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="{h}" rx="2" fill="#E8E0CE" stroke="#6B5A3C" stroke-width="2"/>')
            self.add(f'<rect x="{cx - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="9" fill="#5A4A30"/>')  # dark fireproof hip roof
            self.add(f'<line x1="{cx:.0f}" y1="{y - h / 2 + 9:.0f}" x2="{cx:.0f}" y2="{y + h / 2:.0f}" stroke="#6B5A3C" stroke-width="0.7"/>')
            stores.append({"x": cx, "y": y, "w": w, "h": h, "rot": 0})
            bm = 30  # block a RECT + a building-half margin so dwellings keep clear, like the manor
            self.block_polys.append([(cx - w / 2 - bm, y - h / 2 - bm), (cx + w / 2 + bm, y - h / 2 - bm), (cx + w / 2 + bm, y + h / 2 + bm), (cx - w / 2 - bm, y + h / 2 + bm)])
        if append:
            self.M.setdefault("granaries", []).extend({**st, "label": label} for st in stores)
        else:
            self.M["granary"] = {"x": x, "y": y, "n": n, "stores": stores, "label": label}
        if label:
            if rot:
                loff = h / 2 + 12  # seat the caption off the row's upslope flank, clear of the turned roofs
                # the caption lies ALONG the row at its full tilt (GM 2026-08-09: linear
                # subjects may carry the whole angle - linear_tilt_full - where the old clamp
                # would have gone level past 45 deg, and label_tilt's building fold would have
                # laid perpendicular text ACROSS the kura)
                self.label(x + gsa * loff, y - gca * loff, label, 11, italic=True, color="#6B5A3C", rot=rot, linear=True, full_tilt=True)
            else:
                self.label(x, y - h / 2 - 10, label, 11, italic=True, color="#6B5A3C")
        return stores

    def merchant_storehouses(self: Settlement, count: int = 6, kw: Any = None, kh: Any = None) -> int:  # type: ignore[misc]
        """Attach a small fireproof storehouse (kura) to the BACK of several merchant houses.
        Because most Rokugani farmers are TENANTS, the rent-rice and bulk goods of their (often
        absentee) landlords are kept in town - over and above the ordinary inventory storeroom a
        shop already has - so a noticeable MINORITY of businesses run a deep lot with a kura
        behind the shopfront (the classic narrow-front / deep-lot merchant compound). The kura
        is drawn as an annex behind the building (opposite its street-facing awning), like the
        farmhouse shed: part of the premises, not a separately-sited structure, so it needs no
        open ground in the packed quarter. Records to M['storehouses']; call AFTER the
        businesses are placed. Returns the number attached."""
        if kw is None:
            kw, kh = 20 * self.bscale, 14 * self.bscale  # a ~20x14 ft kura, scaled with the building grain
        biz = [b for b in self.M["buildings"] if b["kind"] in ("merchant", "shop")]
        st = random.getstate()  # spread the picks across the quarter without perturbing
        random.seed(7)  # the main placement RNG (saved/restored, like forest())
        random.shuffle(biz)
        random.setstate(st)
        placed = 0
        for b in biz:
            if placed >= count:
                break
            th = math.radians(b["rot"])
            bx, by = math.sin(th), -math.cos(th)  # the building's BACK direction (awning faces -back)
            off = b["h"] / 2 + kh / 2 - 2  # tuck the kura just behind the shopfront
            ox, oy = b["x"] + bx * off, b["y"] + by * off
            # never let a kura sit ON a street/alley bed (the broad corridor test would veto
            # every candidate at city scale, where the shop rows legitimately sit inside the
            # corridor clearance of the street they front)
            beds = [(st["pts"], st.get("w", 18) / 2) for st in self.M.get("town_streets", [])]
            beds += [(al["pts"], al.get("w", 10) / 2) for al in self.M.get("alleys", [])]
            if self.M.get("road"):
                beds.append((self.M["road"], self.M.get("road_width", 26) / 2))
            if any(seg_dist(ox, oy, pts[k], pts[k + 1]) < half + max(kw, kh) / 2 + 3 for pts, half in beds for k in range(len(pts) - 1)):
                continue
            # ...and never ACROSS A NEIGHBOR. The kura is an annex of its OWN shop - that is what
            # makes its overlap legitimate - so a kura tucked behind a narrow shopfront that happens
            # to back onto the next lot's larger house is a defect, not an annex. The overlap matrix
            # (feature 017) found exactly that twice, because the old blanket storehouse exemption
            # could only say "a kura may overlap a building", never "its own".
            kq = rot_rect(ox, oy, kw, kh, b["rot"])
            if any(other is not b and rects_overlap(kq, rot_rect(other["x"], other["y"], other["w"], other["h"], other.get("rot", 0))) for other in self.M["buildings"]):
                continue
            self.add(
                f'<g transform="translate({ox:.0f},{oy:.0f}) rotate({b["rot"]:.0f})">'
                f'<rect x="{-kw / 2:.0f}" y="{-kh / 2:.0f}" width="{kw}" height="{kh}" rx="1.5" fill="#E8E0CE" stroke="#6B5A3C" stroke-width="1.4"/>'
                f'<rect x="{-kw / 2:.0f}" y="{-kh / 2:.0f}" width="{kw}" height="4.5" fill="#5A4A30"/></g>'
            )  # dark fireproof roof
            # RECORD THE ROTATION. The kura is DRAWN at its shopfront's angle and was recorded without
            # one, so every manifest reader rebuilt it as an axis-aligned box a couple of px wider than
            # the thing on the page - placement cleared a merchant_large by 0.37px and the overlap
            # matrix, reading the un-rotated record, reported a 0.6px collision (Tango, 2026-07-27).
            # Placement and its check must read the same geometry; here they could not, because the
            # manifest did not carry it.
            self.M["storehouses"].append({"x": ox, "y": oy, "w": kw, "h": kh, "rot": b["rot"], "of": [b["x"], b["y"]]})
            self.placed.append((ox, oy, kw, kh))  # later packs (the city terraces) must flow around the annex
            placed += 1
        return placed

    def merchant_residences(self: Settlement, count: int = 4, depth_margin: float = 14, spread: float = 120) -> int:  # type: ignore[misc]
        """Place a few RICH merchant RESIDENCES (kind 'merchant_large') directly BEHIND the shopfront band,
        each ALIGNED to (same rotation as) the storefront it sits behind - the merchant family lives over/
        behind its own shop. Derived from the ACTUAL placed shops (not fixed coords), so it stays correct
        under any seed: each home is set one step DEEPER than the deepest shop (clearing the storefront band),
        parallel to it. Call AFTER the frontage but BEFORE the laborer packs (which then set back further,
        leaving the merchant-band -> gap -> warren order). Uses a true RECTANGULAR overlap test (the circle
        _fits is far too conservative for a large home in a tight band). Returns count placed."""
        rd = self.M.get("road")
        biz = [b for b in self.M["buildings"] if b["kind"] in ("merchant", "shop")]
        if not (rd and biz):
            return 0

        def droad(x: float, y: float) -> float:
            return min(seg_dist(x, y, rd[k], rd[k + 1]) for k in range(len(rd) - 1))

        def corners(cx: float, cy: float, rw: float, rh: float, rot: float = 0.0) -> list[Pt]:
            th = math.radians(rot)
            c, sn = math.cos(th), math.sin(th)
            return [(cx + dx * c - dy * sn, cy + dx * sn + dy * c) for dx, dy in ((-rw / 2, -rh / 2), (rw / 2, -rh / 2), (rw / 2, rh / 2), (-rw / 2, rh / 2))]

        def overlap(ca: Any, cb: Any) -> bool:
            return (
                any(point_in_poly(px, py, cb) for px, py in ca)
                or any(point_in_poly(px, py, ca) for px, py in cb)
                or any(segments_cross(ca[i], ca[(i + 1) % 4], cb[j], cb[(j + 1) % 4]) for i in range(4) for j in range(4))
            )

        bandmax = max(droad(b["x"], b["y"]) for b in biz)  # depth of the deepest storefront
        w, h = self._dims("merchant_large")
        st = random.getstate()  # spread the picks without perturbing the main placement RNG
        random.seed(11)
        random.shuffle(biz)
        random.setstate(st)
        placed = 0
        used: list[Pt] = []
        for b in biz:
            if placed >= count:
                break
            th = math.radians(b["rot"])
            backx, backy = math.sin(th), -math.cos(th)  # the shop's BACK (inland, away from the road)
            step = bandmax - droad(b["x"], b["y"]) + h / 2 + depth_margin  # land just behind the WHOLE band
            ox, oy = b["x"] + backx * step, b["y"] + backy * step
            if ox < 55 or ox > self.W - 55 or oy < 88 or oy > self.H - 26:
                continue
            if self.bound and not point_in_poly(ox, oy, self.bound):
                continue
            if self._in_blocked(ox, oy) or self._near_corridor(ox, oy):
                continue
            mc = corners(ox, oy, w, h, b["rot"])  # (_in_blocked above already keeps it off the paddies)
            if any(overlap(mc, corners(px, py, pw, ph)) for (px, py, pw, ph) in self.placed if abs(px - ox) + abs(py - oy) <= 150):  # rectangular, not circular: clears the tight band
                continue
            if any(math.hypot(ox - ux, oy - uy) < spread for ux, uy in used):
                continue  # keep the rich homes spread along the band
            self.building(ox, oy, w, h, "merchant_large", rot=b["rot"])
            used.append((ox, oy))
            placed += 1
        return placed

    def _way_bearing_near(self: Settlement, x: float, y: float) -> tuple[float, float]:  # type: ignore[misc]
        """(distance, bearing-in-degrees) of the nearest WAY to (x, y) - road, street, lane or
        alley, including the primary road under its own manifest key. A roadside work is defined by
        the way it stands on, so its angle is DERIVED from that way at draw time rather than pinned:
        re-route the road and the flophouse turns with it (GM 2026-08-11, after every flophouse on
        every map came out level while the roads ran at 138-167 degrees)."""
        return self._way_seat_near(x, y)[2:]

    def _way_seat_near(self: Settlement, x: float, y: float) -> tuple[float, float, float, float]:  # type: ignore[misc]
        """(seat_x, seat_y, distance, bearing) of the nearest point on the nearest WAY. The seat is
        what lets a roadside work SNAP: a gen names roughly where the doss-house belongs and the
        engine puts it on the road, which is the only way the two stay together when the road moves."""
        best = (float("inf"), 0.0)
        seat = (x, y)
        lists: list[Any] = [self.M.get(k) or [] for k in ("roads", "streets", "town_streets", "lanes", "alleys")]
        polys = [r["pts"] for lst in lists for r in lst if isinstance(r, dict) and r.get("pts")]
        if self.M.get("road"):
            polys.append(self.M["road"])
        for pts in polys:
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                d = seg_dist(x, y, a, b)
                if d < best[0]:
                    best = (d, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
                    _dx, _dy = b[0] - a[0], b[1] - a[1]
                    _t = 0.0 if _dx == _dy == 0 else max(0.0, min(1.0, ((x - a[0]) * _dx + (y - a[1]) * _dy) / (_dx * _dx + _dy * _dy)))
                    seat = (a[0] + _t * _dx, a[1] + _t * _dy)
        return (seat[0], seat[1], best[0], best[1])

    def flophouse(self: Settlement, x: float, y: float, w: Any = None, h: Any = None, label: str = "flophouse", label_below: bool = False, rot: Any = None) -> None:  # type: ignore[misc]
        """Real size ~104x46 ft (town-calibrated), converted at the map's ftpx.
        A large, plain communal lodging - a kichin-yado / market flophouse - where peasants
        who travel a long way to market day sleep on straw under a roof for a sen a night. It is
        BIGGER and PLAINER than a shophouse (no awning, a long dormitory of plain doorways), set
        where travelers arrive: the gate market of a walled town, the road of an unwalled one.
        Default-on for a town (town_has_flophouse); meta(flophouses=N) requires more. Records to
        M['flophouses'] and blocks houses - place it BEFORE any nearby pack/ring."""
        if w is None:
            w, h = self.px(104), self.px(46)
        if rot is None:
            # a doss-house FRONTS the road travelers arrive on - it exists to catch them - so it
            # lies along that road, and it SNAPS to it when the gen's hint lands adrift (GM
            # 2026-08-11: "the flophouse near the southwest gate is absurdly far from the road...
            # about three hundred feet, which seems absurd"). The gen says roughly where; the way
            # says exactly where, and the two cannot drift apart when the road is re-routed.
            # ROTATION ONLY - no snapping. Moving the seat here was tried and reverted: this method
            # runs before any collision test and has none of its own, so a pulled seat walked
            # doss-houses into streets, into standing terraces, and one into a quarter its own
            # siting rule forbids. The gen chooses the SPOT (with open_seat, which asks the
            # placer); the way chooses the ANGLE, which cannot collide with anything. A work with
            # no way within ~500 ft is not a roadside work and keeps its square default.
            _fd, _fb = self._way_bearing_near(x, y)
            rot = _fb if _fd < self.px(500) else 0.0
        rot = float(rot)
        if rot:
            self.add(f'<g transform="rotate({rot:.1f} {x:.1f} {y:.1f})">')
        x0, y0 = x - w / 2, y - h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" rx="2" fill="#CDBE96" stroke="#5A4A30" stroke-width="2"/>')
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="10" fill="#7A6038"/>')  # long roof ridge
        self.add(f'<line x1="{x0:.0f}" y1="{y:.0f}" x2="{x0 + w:.0f}" y2="{y:.0f}" stroke="#5A4A30" stroke-width="0.7"/>')
        for dx in range(int(x0) + 14, int(x0 + w) - 10, 26):  # a row of plain doorways (a long dormitory)
            self.add(f'<rect x="{dx}" y="{y + h / 2 - 7:.0f}" width="9" height="7" fill="#5A4A30" opacity="0.8"/>')
        if rot:
            self.add("</g>")
        self.M["flophouses"].append({"x": x, "y": y, "w": w, "h": h, "rot": rot, "label": label})
        self.placed.append((x, y, w, h))
        bm = 30  # block a RECT + a building-half margin so dwellings keep clear, like the manor
        self.block_polys.append([(x0 - bm, y0 - bm), (x0 + w + bm, y0 - bm), (x0 + w + bm, y0 + h + bm), (x0 - bm, y0 + h + bm)])
        if label:
            self.label(x, y0 + h + 19 if label_below else y0 - 10, label, 11, italic=True, color="#5A4A30")

    def inn(self: Settlement, x: float, y: float, w: Any = None, h: Any = None, rot: float = 0) -> None:  # type: ignore[misc]
        """A prominent caravan INN - larger and grander than a flophouse, lodging the merchants, drivers
        and guards of the wagon-trains. Recorded in M['buildings'] (kind 'inn', non-residential). It
        FRONTS the road, so `rot` tilts it to lie PARALLEL to a diagonal road with its noren entrance
        (the +y front) FACING the roadbed. Blocks placement - place BEFORE any nearby pack.
        Real size ~66x48 ft (a large 2-story post-road inn), converted at the map's ftpx - as a
        fixed-px glyph it read 2.5x too big on a city map."""
        if w is None:
            w, h = self.px(66), self.px(48)
        hw, hh = w / 2, h / 2
        sf = h / 48  # glyph detail scales with the footprint
        g = [
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" fill="#D9B98C" stroke="#5A3F1E" stroke-width="{max(2.2 * sf, 1.0):.1f}"/>',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{11 * sf:.1f}" fill="#7A5A30"/>',  # roof ridge
            f'<rect x="{-hw:.1f}" y="{hh - 4 * sf:.1f}" width="{w:.1f}" height="{4 * sf:.1f}" fill="#7A5A30" opacity="0.55"/>',
        ]  # lower eave (2-story)
        for i in range(3):  # upper-story lattice windows
            wx = -hw + w * (0.2 + 0.3 * i)
            g.append(f'<rect x="{wx:.1f}" y="{-hh + 14 * sf:.1f}" width="{10 * sf:.1f}" height="{7 * sf:.1f}" fill="#9A7E4E" stroke="#5A3F1E" stroke-width="0.6"/>')
            g.append(f'<line x1="{wx + 5 * sf:.1f}" y1="{-hh + 14 * sf:.1f}" x2="{wx + 5 * sf:.1f}" y2="{-hh + 21 * sf:.1f}" stroke="#D6C49A" stroke-width="0.6"/>')
        nx, nw = -w * 0.19, w * 0.38  # NOREN entrance curtain on the +y front
        g.append(f'<rect x="{nx:.1f}" y="{hh:.1f}" width="{nw:.1f}" height="{9 * sf:.1f}" rx="1" fill="#2E4A6B" stroke="#1E3450" stroke-width="0.6"/>')
        for k in (1, 2):
            g.append(f'<line x1="{nx + nw * k / 3:.1f}" y1="{hh:.1f}" x2="{nx + nw * k / 3:.1f}" y2="{hh + 9 * sf:.1f}" stroke="#C9D4E0" stroke-width="0.7"/>')
        g.append('</g>')
        self.add(''.join(g))
        self.M["buildings"].append({"x": x, "y": y, "w": w, "h": h, "kind": "inn", "rot": rot})
        self.placed.append((x, y, w, h))
        bm = 24
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])

    def stables(self: Settlement, x: float, y: float, w: Any = None, h: Any = None, rot: float = 0, yard: bool = True) -> None:  # type: ignore[misc]
        """A large STABLES - long rows of stalls for a wagon-train's many draft animals (oxen, horses).
        Recorded in M['buildings'] (kind 'stables', non-residential). Wants OPEN GROUND around it. `rot`
        tilts it to sit parallel to its inn / the road. Place BEFORE any nearby pack, but AFTER its
        cluster's inn + flophouse (so the yard, `yard=True`, skips them). Real size ~92x44 ft (stall rows
        for a full wagon-train), converted at the map's ftpx."""
        if w is None:
            w, h = self.px(92), self.px(44)
        hw, hh = w / 2, h / 2
        sf = h / 44  # glyph detail scales with the footprint
        g = [
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" fill="#B79A6E" stroke="#5A4326" stroke-width="{max(2 * sf, 1.0):.1f}"/>',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{9 * sf:.1f}" fill="#6B4F2A"/>',
        ]  # roof ridge
        sx, step = -hw + 12 * sf, max(16 * sf, 6)  # stall divisions
        while sx < hw - 8 * sf:
            g.append(f'<line x1="{sx:.1f}" y1="{-hh + 9 * sf:.1f}" x2="{sx:.1f}" y2="{hh:.1f}" stroke="#6B4F2A" stroke-width="1.4" opacity="0.7"/>')
            sx += step
        g.append('</g>')
        self.add(''.join(g))
        self.M["buildings"].append({"x": x, "y": y, "w": w, "h": h, "kind": "stables", "rot": rot})
        self.placed.append((x, y, w, h))
        bm = 24
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])
        # the working YARD is CITY-scope for now (its disk radius + furniture are calibrated for city
        # ftpx=3): a town's single caravan stables keeps its plain open ground until the yard is made
        # scale-aware. `yard=False` also suppresses it.
        if yard and self.M.get("meta", {}).get("scale") in CITY_TIER_SCALES:
            # QUEUED, not drawn (GM 2026-07-24): the yard scatter keeps its furniture off every
            # way and footprint it can SEE, but a stables placed early could not see the streets
            # drawn after it - so a heap landed on a later street (Nagahara wharf yard). Yards now
            # draw at crop time (flush_stable_yards, auto-run by crop_city), when the map is
            # complete - the same-data-as-the-checks doctrine (settlements.md, PLANK BRIDGES).
            self._pending_yards.append((x, y, w, h, 72.0, None))

    def _stable_yard(self: Settlement, sx: float, sy: float, sw: float, sh: float, r: float = 72.0) -> None:  # type: ignore[misc]
        """Draw the working YARD around a gate stables (GM 2026-07-22): the open ground where wagon-trains
        park, oxen are unyoked and tethered, teamsters wait between stages. Research (settlements.md 'Stable
        yard'): a beaten-earth forecourt - NO grass (trampled hard, animals hay-fed not grazed) - and NOT a
        fenced paddock (the least authentic option); its edges are the wall + flanking buildings, its "in
        active use" signal is carts, animals tethered at a hitching rail, and littered ground (the Qingming
        Shanghe Tu gate convention). Drawn as a feathered SCATTER (no solid fill, house style - a filled
        polygon reads as a crisp rhombus) that AUTO-AVOIDS every feature: the stables/inn/flophouse footprints,
        the road + streets, fields, and water - so it fills only the genuinely open pocket. It does NOT avoid
        block_polys (those RESERVED the pocket for exactly this) - only real drawn features. Glyph sizes are
        legibility-tuned for city scale (the wellhead-marker doctrine: a location read, not strict to-scale),
        so they stay legible where a true ~10 ft cart would be ~3 px. Records M['stable_yards'] linked to the
        stables so `stables_have_yards` can gate that no gate stables reverts to blank parchment."""
        st = random.getstate()
        random.seed(int(abs(sx) * 11 + abs(sy) * 7 + round(r)))
        corridors = self._corridor_buffers(2.0)  # keep every glyph off the road/street tread
        # a TIGHT footprint keep-out (real drawn buildings only, ~3px margin so the beaten earth meets the
        # walls) - NOT the wide urban halo (which would leave a bare ring) and NOT block_polys (the reserved
        # pocket IS the yard). A rotated building is covered by its half-diagonal square.
        keep: list[tuple[float, float, float, float]] = []
        # "farriers" belongs here because the shoeing forge stands ON this yard by design (GM
        # 2026-07-25) - it is the one trade work sited INSIDE a stable yard, so without it the
        # scatter would speckle straw litter across the forge's apron and roof
        for k in (
            "buildings",
            "flophouses",
            "storehouses",
            "merchant_estates",
            "ministries",
            "religious",
            "manors",
            "cemeteries",
            "mausoleums",
            "cremation_grounds",
            "ossuaries",
            "houses",
            "farriers",
        ):
            for o in self.M.get(k, []) or []:
                ohw, ohh = o["w"] / 2, o["h"] / 2
                if o.get("rot"):
                    ohw = ohh = math.hypot(ohw, ohh)
                m = 3.0
                if o["x"] + ohw + m < sx - r - 50 or o["x"] - ohw - m > sx + r + 50 or o["y"] + ohh + m < sy - r - 50 or o["y"] - ohh - m > sy + r + 50:
                    continue  # +50 past the disc: the watering point may sit at a well just OUTSIDE the yard rim
                keep.append((o["x"] - ohw - m, o["y"] - ohh - m, o["x"] + ohw + m, o["y"] + ohh + m))

        wallp = self.M.get("wall")  # a yard near the rampart (a gate-side animal ground) must not speckle the wall or spill outside it

        def clear(px: float, py: float, pad: float = 0.0, rim: bool = True) -> bool:
            if rim and (px - sx) ** 2 + (py - sy) ** 2 > (r - pad) ** 2:
                return False  # rim=False for the well-side watering point, which may sit at/just past the disc edge
            if wallp and (not point_in_poly(px, py, wallp) or any(seg_dist(px, py, wallp[i], wallp[i + 1]) < 9 for i in range(len(wallp) - 1))):
                return False
            if any(x0 <= px <= x1 and y0 <= py <= y1 for x0, y0, x1, y1 in keep):
                return False
            if any(any(seg_dist(px, py, pl[i], pl[i + 1]) < hwid for i in range(len(pl) - 1)) for pl, hwid in corridors):
                return False
            if any(point_in_poly(px, py, ff) for ff in self.field_polys):
                return False
            return not self._on_watercourse(px, py)

        # 1. BEATEN-EARTH scuff + STRAW litter: a feathered scatter so the ground reads TRODDEN, not blank
        g: list[str] = []
        feather = 22.0
        n = int(math.pi * r * r / 46.0)
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi)
            rr = r * math.sqrt(random.random())
            px, py = sx + rr * math.cos(a), sy + rr * math.sin(a)
            if not clear(px, py):
                continue
            ed = r - rr  # feather to nothing at the disk rim (no hard edge)
            if ed < feather and random.random() > ed / feather:
                continue
            t = random.random()
            if t < 0.6:  # a scuff speck of beaten earth
                g.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{random.uniform(0.7, 1.3):.1f}" fill="#A98C60" fill-opacity="0.7"/>')
            elif t < 0.82:  # a short hoof/cart-rut scuff
                aa, ln = random.uniform(0, math.pi), random.uniform(3, 6)
                g.append(
                    f'<line x1="{px - math.cos(aa) * ln / 2:.1f}" y1="{py - math.sin(aa) * ln / 2:.1f}" x2="{px + math.cos(aa) * ln / 2:.1f}" y2="{py + math.sin(aa) * ln / 2:.1f}" stroke="#9C7E52" stroke-width="0.9" opacity="0.5"/>'
                )
            else:  # spilled straw / fodder litter
                aa, ln = random.uniform(0, math.pi), random.uniform(2.5, 4.5)
                g.append(
                    f'<line x1="{px - math.cos(aa) * ln / 2:.1f}" y1="{py - math.sin(aa) * ln / 2:.1f}" x2="{px + math.cos(aa) * ln / 2:.1f}" y2="{py + math.sin(aa) * ln / 2:.1f}" stroke="#D8C176" stroke-width="0.9" opacity="0.8"/>'
                )
        self.add("".join(g))

        # 2. FURNITURE: greedily seated at clear spots on rings around the stables (deterministic order)
        cand: list[Pt] = []
        for rad in (32.0, 44.0, 56.0, 68.0):
            for i in range(12):
                aa = 2 * math.pi * i / 12 + rad  # per-ring phase offset so rings do not align
                cand.append((sx + rad * math.cos(aa), sy + rad * math.sin(aa)))
        random.shuffle(cand)
        used: list[Pt] = []

        def take(pad: float, minsep: float, probes: tuple[Pt, ...] = ((0.0, 0.0),)) -> Pt | None:
            # `probes` are offsets from the candidate that must ALL be clear - a rail or heap is
            # not a point, so its tips/edges are tested too (GM 2026-07-24: furniture off the
            # roads and the wall; a center-only test let an 18px rail lay its tip on the tread)
            for px, py in cand:
                if any((px - ux) ** 2 + (py - uy) ** 2 < minsep * minsep for ux, uy in used) or not all(clear(px + ox, py + oy, pad) for ox, oy in probes):
                    continue
                used.append((px, py))
                return (px, py)
            return None

        # HITCHING RAILS - the yard's active "edge" (rails + picket lines, NOT a paddock fence;
        # GM 2026-07-22). A wagon-train ties up MANY animals, so the yard shows two or three
        # rails: first a ROAD-PARALLEL rail set back from the nearest road/street (the yard's
        # road-side barrier so nothing strays onto the through-road), then one or two more at
        # clear interior spots. Rails draw as BARE posts - NO animal glyphs (GM 2026-07-25,
        # ending the "dung heaps at the hitching posts" saga: the drawn oxen kept reading as
        # muck piles no matter how the glyph was styled, and the standing doctrine is that
        # these maps render no humans, so they render no animals either; the rail itself plus
        # the beaten-earth litter carry the "in active use" signal).
        rails: list[dict[str, float]] = []
        heaps: list[dict[str, float]] = []

        def rail_rec(cx: float, cy: float, tx: float, ty: float) -> dict[str, float]:
            """The record a rail at this seat WOULD get - built before the rail is committed so a
            candidate can be tested at its true drawn extent (rail_quad) like everything else."""
            return {"x": round(cx, 1), "y": round(cy, 1), "tx": round(tx, 3), "ty": round(ty, 3), "len": 18.0, "reach": 2.4}

        def draw_hitch(cx: float, cy: float, tx: float, ty: float, nx: float, ny: float) -> None:
            length = 18.0
            rails.append(rail_rec(cx, cy, tx, ty))
            ex0, ey0 = cx - tx * length / 2, cy - ty * length / 2
            fg = [f'<line x1="{ex0:.1f}" y1="{ey0:.1f}" x2="{cx + tx * length / 2:.1f}" y2="{cy + ty * length / 2:.1f}" stroke="#6B4F2A" stroke-width="1.5"/>']
            for i in range(4):  # posts across the rail
                pxp, pyp = ex0 + tx * length * i / 3, ey0 + ty * length * i / 3
                fg.append(f'<line x1="{pxp - nx * 2.4:.1f}" y1="{pyp - ny * 2.4:.1f}" x2="{pxp + nx * 2.4:.1f}" y2="{pyp + ny * 2.4:.1f}" stroke="#5A4326" stroke-width="1.2"/>')
            self.add("".join(fg))

        # rails also seat SYMMETRICALLY clear of any EARLIER yard's dung heaps (GM 2026-07-25
        # round 2): the heap-vs-rail clearance below is map-wide, so a later yard must not lay
        # a rail into a neighboring yard's muck pile either - same 25px hold on the
        # heap-center-to-rail-line distance, measured against this candidate's drawn segment
        prior_heaps = [(h_["x"], h_["y"]) for yd_ in self.M.get("stable_yards", []) or [] for h_ in yd_.get("dung_heaps", []) or []]

        def _rail_clear_of_heaps(cx: float, cy: float, tx_: float, ty_: float) -> bool:
            return all(seg_dist(hx_, hy_, (cx - tx_ * 9.0, cy - ty_ * 9.0), (cx + tx_ * 9.0, cy + ty_ * 9.0)) >= 25.0 for hx_, hy_ in prior_heaps)

        # WELLS, TROUGHS, AND HITCHING POSTS NEVER OVERLAP ONE ANOTHER (GM 2026-07-25; the full
        # reasoning sits with the quad builders at the top of this module and in settlements.md
        # 'Stable yard'). Each of the three is placed at a different moment, so every stage tests
        # the DRAWN extents of whatever already exists: a rail avoids every wellhead on the map,
        # the trough cluster avoids the rails, and the dug-your-own wellhead avoids both. Prior
        # yards count too - two yards can sit close enough to collide across the gap between them,
        # which is the same cross-yard lesson the dung-heap rule had to learn twice.
        prior_boxes = [yd_["troughs_box"] for yd_ in self.M.get("stable_yards", []) or [] if yd_.get("troughs_box")]
        prior_rails = [r_ for yd_ in self.M.get("stable_yards", []) or [] for r_ in yd_.get("rails", []) or []]

        def _glyph_free(q: Poly, hug: Any = None) -> bool:
            """True when the drawn extent `q` overlaps no OTHER yard glyph (wellhead, trough
            cluster, hitching rail). Everything `q` is measured against is inflated by
            YARD_GLYPH_SLACK - except `hug`, the one wellhead a trough cluster deliberately stands
            beside, which is tested at TRUE extent: that bucket-pour gap is a deliberate ~1.5px and
            inflating it would shove the troughs away from the well they exist to be poured from."""
            if any(sat_overlap(q, wellhead_quad(w_, 0.0 if w_ is hug else YARD_GLYPH_SLACK)) for w_ in self.M.get("wells", []) or []):
                return False
            if any(sat_overlap(q, trough_quad(b_, YARD_GLYPH_SLACK)) for b_ in prior_boxes):
                return False
            return not any(sat_overlap(q, rail_quad(r_, YARD_GLYPH_SLACK)) for r_ in (*rails, *prior_rails))

        # (1) the ROAD-PARALLEL edge rail: nearest road/street segment, rail set back into the yard
        best_seg: Any = None
        for pl, hwid in corridors:
            for i in range(len(pl) - 1):
                cp = seg_closest(sx, sy, pl[i], pl[i + 1])
                sd = math.hypot(cp[0] - sx, cp[1] - sy)
                if best_seg is None or sd < best_seg[0]:
                    best_seg = (sd, cp, pl[i], pl[i + 1], hwid)
        if best_seg is not None and best_seg[0] < r:
            _d, (cpx, cpy), pa, pb, hwid = best_seg
            seglen = math.hypot(pb[0] - pa[0], pb[1] - pa[1]) or 1.0
            tx, ty = (pb[0] - pa[0]) / seglen, (pb[1] - pa[1]) / seglen  # rail runs ALONG the road
            ndist = math.hypot(sx - cpx, sy - cpy) or 1.0
            nx, ny = (sx - cpx) / ndist, (sy - cpy) / ndist  # from road toward the stables (yard side)
            rcx, rcy = cpx + nx * (hwid + 11.0), cpy + ny * (hwid + 11.0)  # set back off the roadbed into the yard
            # probe the rail's FULL extent (tips + post reach = len/2 + 2.4), not just its center -
            # a tip on the roadbed or against the rampart is exactly what the rail exists to prevent
            # (GM 2026-07-24; stable_yard_furniture_clear_of_roads_walls)
            if all(clear(rcx + tx * e, rcy + ty * e, 8.0) for e in (-11.4, 0.0, 11.4)) and _rail_clear_of_heaps(rcx, rcy, tx, ty) and _glyph_free(rail_quad(rail_rec(rcx, rcy, tx, ty))):
                draw_hitch(rcx, rcy, tx, ty, nx, ny)
                used.append((rcx, rcy))
        # (2) one or two more rails at clear interior spots (a busy train needs the tie-up room);
        # tips probed like the road rail
        # bounded RETRIES, not two attempts: a candidate refused by the heap/glyph rules must not
        # COST the yard a rail - a wagon-train's tie-up room is the whole "in active use" signal, so
        # keep walking the candidate rings until two rails are seated or the ground is genuinely full
        seated = 0
        for _ in range(8):
            if seated >= 2:
                break
            spot = take(10.0, 24.0, probes=((-11.4, 0.0), (0.0, 0.0), (11.4, 0.0)))
            if not spot:
                break
            if not _rail_clear_of_heaps(spot[0], spot[1], 1.0, 0.0) or not _glyph_free(rail_quad(rail_rec(spot[0], spot[1], 1.0, 0.0))):
                continue
            draw_hitch(spot[0], spot[1], 1.0, 0.0, 0.0, 1.0)
            seated += 1

        # the WATERING POINT (GM 2026-07-23, researched - settlements.md 'Stable yard' watering
        # paragraph): a working ox drinks ~10 gal/day, a buffalo more, so a wagon-train needs
        # 300-600 gal in one or two big sessions - one small trough is functionally undersized.
        # The historical form is 2-3 long troughs (~8-15 ft, ~2 ft of edge per drinking head)
        # CLUSTERED AT A WELL (animals are led to water in relays, not watered at the rail; the
        # bucket is poured straight from the wellhead, so the troughs sit BESIDE the well - GM
        # 2026-07-23: "otherwise you'd have to carry the water a long way"): the cluster hugs the
        # nearest recorded well within r + 40 - offset from the wellhead by just its visual radius
        # + a trough's half-length (~bucket-pour distance), on the yard side, even when that well
        # stands at or just past the disc rim. A
        # caravan-scale ground (r >= 76) gets 3 troughs, a plain stables yard 2. Drawn ~4.6x2 px
        # each (a ~14 ft trough at city scale, width floored at the 2px cartographic minimum so
        # the water reads). A yard with NO reachable well (or every wellhead flank blocked) digs
        # its OWN courtyard well instead of dropping the cluster at a random spot (GM 2026-07-23,
        # the Nagahara defect - both its yards fell back to 100/241 ft bucket-carries): the
        # caravanserai and the yizhan post-yard watered whole trains from their own courtyard
        # well, so "no well nearby" is a reason to sink one, never to carry water. Gated by
        # stable_troughs_beside_well.
        n_troughs = 3 if r >= 76 else 2
        t_h, t_gap, t_len = 2.0, 1.6, 4.6
        t_total = n_troughs * t_h + (n_troughs - 1) * t_gap  # the stacked cluster's full height

        def beside(wl: dict[str, Any]) -> Pt | None:
            # a clear cluster spot hugging THIS wellhead, preferring the yard side, then walking
            # around. The offset is DIRECTION-AWARE: the minimal center distance at which the
            # cluster BOX (t_len x t_total) clears the well-house roof square along this ray, + a
            # 1.5 step (~bucket-pour). A fixed `vr + t_len/2` only guarantees HORIZONTAL
            # clearance - the stack is taller than it is wide, so a near-vertical ray clipped the
            # roof corner (GM 2026-07-23, Tango's caravan ground). The box is then CORNER-checked
            # against everything clear() knows (buildings, roads, fields, water, the wall) - a
            # center-only point test let the rects themselves land on footprints - and passed
            # through _glyph_free, which keeps it off every OTHER wellhead roof, off every
            # hitching rail, and off any neighboring yard's cluster. Gated by
            # stable_troughs_clear_of_buildings + wells_troughs_rails_clear_of_each_other.
            vr = wl.get("vr", 4.0)
            w_ang0 = math.atan2(sy - wl["y"], sx - wl["x"])
            for w_da in (0.0, 0.7, -0.7, 1.4, -1.4, 2.1, -2.1, math.pi):
                ux, uy = math.cos(w_ang0 + w_da), math.sin(w_ang0 + w_da)
                w_off = 1.5 + min(
                    (vr + t_len / 2) / abs(ux) if abs(ux) > 1e-9 else math.inf,
                    (vr + t_total / 2) / abs(uy) if abs(uy) > 1e-9 else math.inf,
                )
                wcand = (wl["x"] + ux * w_off, wl["y"] + uy * w_off)
                bx0, by0, bx1, by1 = wcand[0] - t_len / 2, wcand[1] - t_total / 2, wcand[0] + t_len / 2, wcand[1] + t_total / 2
                if not all(clear(qx, qy, 2.0, rim=False) for qx, qy in ((wcand[0], wcand[1]), (bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1))):
                    continue
                if not _glyph_free(trough_quad([bx0, by0, bx1, by1]), hug=wl):
                    continue
                return wcand
            return None

        wp: Pt | None = None
        for wl in sorted(self.M.get("wells", []) or [], key=lambda o: math.hypot(o["x"] - sx, o["y"] - sy)):
            if not 1 <= math.hypot(wl["x"] - sx, wl["y"] - sy) <= r + 40:
                continue
            wp = beside(wl)
            if wp:
                used.append(wp)
                break
        if wp is None:  # dig the yard's own well at a clear spot, cluster the troughs beside it
            # the dug well is a PUBLIC wellhead (visual r 8), so probe its head's reach - the well
            # checks test way-distance at half-width + 8, tighter than clear()'s corridor buffer
            spot = take(12.0, 24.0, probes=((0.0, 0.0), (8.0, 0.0), (-8.0, 0.0), (0.0, 8.0), (0.0, -8.0), (5.7, 5.7), (-5.7, 5.7), (5.7, -5.7), (-5.7, -5.7)))
            # the dug head is a GLYPH like any other: predict its roof square (_well_vr) and refuse
            # a seat that would put it on a rail, on another wellhead, or on a neighbor's troughs
            if spot and self._well_ground_clear(spot[0], spot[1]) and _glyph_free(wellhead_quad({"x": spot[0], "y": spot[1], "vr": self._well_vr()})):
                self.well(spot[0], spot[1])
                wp = beside(self.M["wells"][-1])
                if wp:
                    used.append(wp)
        if wp:
            wpx, wpy = wp
            for t_i in range(n_troughs):
                t_y = wpy - t_total / 2 + t_i * (t_h + t_gap)
                self.add(f'<rect x="{wpx - t_len / 2:.1f}" y="{t_y:.1f}" width="{t_len:.1f}" height="{t_h:.1f}" rx="0.9" fill="#8FA6B0" stroke="#5A6B72" stroke-width="0.7"/>')

        # 1-2 DUNG HEAPS - the little "someone works here" tell; the ellipse's EDGE points are
        # probed too (GM 2026-07-24: a heap must not foul the road tread or the rampart clearance),
        # and a heap keeps WELL clear of every RAIL LINE ON THE MAP (GM 2026-07-25, two rounds:
        # round 1 held 15px, which parks the heap's edge ~8 ft behind the tethered-animal row -
        # the GM still read that as "directly next to the hitching posts", blocking the tie-up
        # flank - and it tested only THIS yard's rails, so a heap could sit 22px from a
        # NEIGHBORING yard's rail with nothing measuring the pair, Nagahara's SE yards being the
        # live case. Round 2: check floor 24px / 72 ft from every rail on the map, placement
        # holds 25 for slack - the heap's edge ends ~38 ft past the animals' rumps, unambiguously
        # out of the working row while still close enough to read as the yard's muck pile)
        all_rails = rails + [r_ for yd_ in self.M.get("stable_yards", []) or [] for r_ in yd_.get("rails", []) or []]

        def _clear_of_rails(hpx: float, hpy: float) -> bool:
            for rl_ in all_rails:
                rh_ = rl_["len"] / 2
                if seg_dist(hpx, hpy, (rl_["x"] - rl_["tx"] * rh_, rl_["y"] - rl_["ty"] * rh_), (rl_["x"] + rl_["tx"] * rh_, rl_["y"] + rl_["ty"] * rh_)) < 25.0:
                    return False
            return True

        for _ in range(2):
            d = None
            for hcx, hcy in cand:
                if any((hcx - ux) ** 2 + (hcy - uy) ** 2 < 16 * 16 for ux, uy in used) or not _clear_of_rails(hcx, hcy):
                    continue
                if all(clear(hcx + ox_, hcy + oy_, 6.0) for ox_, oy_ in ((0.0, 0.0), (-2.5, 0.0), (2.5, 0.0), (0.0, -1.8), (0.0, 1.8))):
                    d = (hcx, hcy)
                    used.append(d)
                    break
            if not d:
                break
            dx, dy = d
            heaps.append({"x": round(dx, 1), "y": round(dy, 1), "rx": 2.5, "ry": 1.8})
            self.add(f'<ellipse cx="{dx:.1f}" cy="{dy:.1f}" rx="2.5" ry="1.8" fill="#6E5A3A" stroke="#4A3A22" stroke-width="0.5" opacity="0.9"/>')

        yard_rec: dict[str, Any] = {
            "x": round(sx, 1),
            "y": round(sy, 1),
            "r": round(r, 1),
            "of": [round(sx, 1), round(sy, 1)],
            "troughs": n_troughs if wp else 0,
            "rails": rails,  # recorded so stable_yard_furniture_clear_of_roads_walls can test the drawn extents
            "dung_heaps": heaps,
        }
        if wp:
            yard_rec["troughs_at"] = [round(wp[0], 1), round(wp[1], 1)]  # cluster center - stable_troughs_beside_well anchors on it
            yard_rec["troughs_box"] = [
                round(wp[0] - t_len / 2, 1),
                round(wp[1] - t_total / 2, 1),
                round(wp[0] + t_len / 2, 1),
                round(wp[1] + t_total / 2, 1),
            ]  # drawn extent - stable_troughs_clear_of_buildings tests it
        self.M.setdefault("stable_yards", []).append(yard_rec)
        random.setstate(st)

    def animal_ground(self: Settlement, cx: float, cy: float, r: float = 68.0, label: Any = None) -> None:  # type: ignore[misc]
        """EXTRA interior ANIMAL / CARAVAN GROUND - a standalone stable-yard scatter (beaten earth,
        hitching rails, a trough, dung heaps) that CLAIMS an open pocket as
        deliberate working ground. This is the standing EASY REMEDY when city_no_large_empty_space
        flags unclaimed ground (GM 2026-07-23): where the bare pocket sits near a gate or the
        stables, more tie-up room for wagon-trains is the natural use - first applied to Tango's
        north gate, whose Phoenix-border traffic wants marshalling space for caravans coming down
        from (or departing toward) Phoenix lands. Draws the s._stable_yard scatter at (cx, cy) - it
        auto-avoids roads, streets, fields, water, the rampart, and every drawn footprint, so it
        fills only the genuinely open ground - and records M['stable_yards'], which the empty-space
        detector counts as claimed. The label (e.g. "caravan ground") is optional; the rails
        usually read on their own."""
        self._pending_yards.append((cx, cy, 0.0, 0.0, r, label))  # queued like the stables yards - drawn at crop time when every way exists (GM 2026-07-24)

    def flush_stable_yards(self: Settlement) -> None:  # type: ignore[misc]
        """Draw every queued stable-yard scatter (stables() gate yards + animal_ground() pockets).
        Runs at CROP time - crop_city calls it first - so the yard sees the COMPLETE map: every
        street/alley/ring road and every footprint, not just what happened to be drawn before the
        stables call (GM 2026-07-24: a wharf-yard dung heap landed on a street drawn later). The
        scatter's own seeded RNG makes the deferral ripple-free for every other feature; a late
        flush also means the watering point sees every real well, so the dig-your-own fallback
        fires only when the neighborhood genuinely has none in reach. Idempotent (drains the queue);
        unit tests call it directly after stables()/animal_ground()."""
        pending = self._pending_yards
        self._pending_yards: list[tuple[float, float, float, float, float, Any]] = []
        for sx, sy, sw, sh, r, label in pending:
            self._stable_yard(sx, sy, sw, sh, r=r)
            if label:
                self.label(sx, sy, label, 11, italic=True, color="#6B5A3C")
