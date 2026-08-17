"""Ground given over to punishment, and to the boundaries punishment is measured against.

Split from settlement/civic_grounds.py by feature 115 - see settlement/civic_grounds/CLAUDE.md for the index.
"""

from typing import TYPE_CHECKING

from .._geom import (
    Pt,
    label_tilt,
    tilt_caption_seat,
)
from .._knobs import BOUNDARY_MARKER_FT, BOUNDARY_MARKER_MIN_PX, CITY_TIER_SCALES, PUNISHMENT_SPOT_FT, execution_ground_ft

if TYPE_CHECKING:
    from ..core import Settlement


class JusticeGroundsMixin:
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
