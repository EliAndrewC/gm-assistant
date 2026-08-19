"""The settlement's public street furniture and civic fixtures, and the two auto-siters that place them on the traffic.

Split from settlement/structures.py by feature 114 - see settlement/structures/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any

from .._geom import (
    Pt,
    label_tilt,
    linear_tilt,
    point_in_poly,
    seg_dist,
    street_runs,
    tilt_caption_seat,
    way_beds,
)
from .._knobs import KOSATSUBA_MARKER_MIN_PX, PUNISHMENT_SPOT_FT

if TYPE_CHECKING:
    from ..core import Settlement


class PublicFixturesMixin:
    def theater_stage(self: Settlement, cx: float, cy: float, w: Any = None, h: Any = None, rot: float = 0, label: Any = None, kind: str = "monzen") -> None:  # type: ignore[misc]
        """A public THEATER STAGE: a roofed raised stage facing an open viewing ground - the troupe-and-
        festival venue of a Rokugani town/city (the East Asian analog of a Greco-Roman amphitheater: a
        temple OPERA STAGE / shrine NOH-kagura stage). It belongs to a temple/monastery precinct, the
        audience gathering in the open ground between the stage and the hall. (cx,cy) is the center of the
        w x h viewing ground; the roofed stage sits at the -y (north) end facing +y into it; `rot` turns the
        whole feature (point it so the ground opens toward the temple). Records M['theater_stage'] - a LIST
        since 2026-08-10: the singleton dict write meant a second stage clobbered the first, so Shiro
        Daika's labeled entertainment-quarter theater existed as ink only, invisible to the overlap
        matrix in both directions (settlement-review). `kind` says which siting doctrine the stage owes:
        "monzen" (default) is a temple/shrine performance stage and must sit at its hall;
        "machi" is a commercial quarter theater and sits in the fabric. Reserves its footprint so
        packing avoids it."""
        if w is None:
            w, h = self.px(150), self.px(105)  # stage + viewing ground ~150x105 ft (town-calibrated)
        hw, hh = w / 2, h / 2
        sw, sh = w * 0.5, h * 0.26  # the roofed stage at the north end
        sy = -hh - sh * 0.5  # straddling the ground's north edge
        g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hw:.0f}" y="{-hh:.0f}" width="{w:.0f}" height="{h:.0f}" rx="4" fill="#E4D6B0" stroke="#A98E54" stroke-width="1.5"/>')  # the swept earthen viewing ground
        g.append(f'<rect x="{-hw + 5:.0f}" y="{-hh + 5:.0f}" width="{w - 10:.0f}" height="{h - 10:.0f}" rx="3" fill="none" stroke="#C9B484" stroke-width="0.7" opacity="0.6"/>')
        for i in range(3):  # a few faint rows of standing crowd in the ground
            ry = -hh + h * (0.40 + 0.17 * i)
            for k in range(7):
                px = -hw + 14 + (w - 28) * (k + 0.5) / 7
                g.append(f'<circle cx="{px:.0f}" cy="{ry:.0f}" r="1.7" fill="#8A7A56" opacity="0.5"/>')
        g.append(f'<rect x="{-sw / 2:.0f}" y="{sy:.0f}" width="{sw:.0f}" height="{sh:.0f}" rx="2" fill="#C9A57A" stroke="#5A3F1E" stroke-width="1.8"/>')  # stage platform
        g.append(f'<rect x="{-sw / 2:.0f}" y="{sy:.0f}" width="{sw:.0f}" height="{sh * 0.36:.0f}" fill="#7A5A30"/>')  # its roof
        # NO painted-pine roundel. The kagami-ita's pine is painted on the VERTICAL back board, so a
        # plan view cannot see it at all - and drawn as a green disc it used the sheet's own
        # vegetation idiom and read as a bush growing on the stage (settlement-review, Ubame).
        g.append(f'<rect x="{-sw / 2:.0f}" y="{sy + sh - 2.5:.0f}" width="{sw:.0f}" height="2.5" fill="#5A3F1E" opacity="0.6"/>')  # stage-front lip onto the ground
        g.append('</g>')
        self.add(''.join(g))
        self.M.setdefault("theater_stage", []).append({"x": cx, "y": cy, "w": w, "h": h, "rot": rot, "kind": kind})
        R = math.hypot(hw, hh) + sh * 0.5  # rotation-safe covering radius (stage + ground)
        self.ellipses.append((cx, cy, R, R))
        if label:
            # Offset from the ROTATED extent, not the raw half-height. At rot=90 the ground's reach
            # along +y is hw, not hh, so the caption landed INSIDE the ground it names, with the
            # outline stroke running through the text (settlement-review, Ubame, 2026-07-26).
            # Identical to the old expression at rot=0, so unrotated stages are untouched.
            # Seat by the STANDOFF LADDER against the stage's ROTATED extent, hinted at the historical
            # spot. Two bugs, one fix: the old `cy + hh + 16` used the unrotated half-height, so a
            # rot=90 stage captioned INSIDE its own ground (Ubame); and a hand seat has no idea what
            # else is there, so simply correcting the reach dropped Tango's caption onto a monk house.
            # The hint keeps every UNROTATED stage exactly where it was whenever that seat is clear.
            _a = math.radians(rot)
            _rx = abs(hw * math.cos(_a)) + abs(hh * math.sin(_a))
            _ry = abs(hw * math.sin(_a)) + abs(hh * math.cos(_a))
            self.place_caption(label, (cx - _rx, cy - _ry, cx + _rx, cy + _ry), 11, italic=True, hint=(cx, cy + _ry + 16), rot=rot)

    def fire_tower(self: Settlement, x: float, y: float, tw: float | None = None, rot: float = 0.0, label: str = "fire tower") -> int:  # type: ignore[misc]
        """A HINOMI-YAGURA (fire-watch tower): a tall, slender braced-timber tower with a lookout
        platform and an alarm bell (hansho), standing in the dense COMMONER quarter of a walled
        town or city where packed wooden rooftops make fire catastrophic. It is a CIVILIAN interior
        structure - the magistrate's fire-watch - distinct from a wall guard tower (military, on the
        rampart): drawn as an OPEN braced frame (not the guard tower's solid block) with a red bell.
        The watchman strikes the bell in a cadence that tells the town how near the fire is. Records
        M['fire_towers'] (an overlap-checked struct: it must stand clear of the wall, roads, and
        buildings) and reserves a small no-build block (it needs clear sightlines). Place it among the
        laborer/merchant blocks. See the settlements.md 'Fire towers' historical grounding."""
        if tw is None:
            tw = self.px(26)  # a real hinomi-yagura frame is ~26 ft square (town-calibrated glyph)
        h = tw / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-h - 2:.0f}" y="{-h - 5:.0f}" width="{tw + 4}" height="5" rx="1" fill="#7A5A30"/>')  # the little roof cap over the lookout platform
        g.append(f'<rect x="{-h:.0f}" y="{-h:.0f}" width="{tw}" height="{tw}" fill="#EFE6CC" fill-opacity="0.45" stroke="#7A5A30" stroke-width="2"/>')  # the open braced-timber frame
        g.append(f'<line x1="{-h:.0f}" y1="{-h:.0f}" x2="{h:.0f}" y2="{h:.0f}" stroke="#7A5A30" stroke-width="1.1"/>')  # cross-braces (an X)
        g.append(f'<line x1="{h:.0f}" y1="{-h:.0f}" x2="{-h:.0f}" y2="{h:.0f}" stroke="#7A5A30" stroke-width="1.1"/>')
        g.append(f'<circle cx="0" cy="0" r="{tw * 0.2:.1f}" fill="#B0462F" stroke="#5A3F1E" stroke-width="0.8"/>')  # the alarm bell (hansho)
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M["fire_towers"].append({"x": round(x, 1), "y": round(y, 1), "w": tw, "h": tw, "rot": round(rot, 1), "z": z, "label": label})
        self.placed.append((x, y, tw, tw))
        bm = 16
        self.block_polys.append([(x - h - bm, y - h - bm), (x + h + bm, y - h - bm), (x + h + bm, y + h + bm), (x - h - bm, y + h + bm)])
        if label:
            _t = label_tilt(rot)
            _lx, _ly = tilt_caption_seat(x, y, rot, _t, h, h, 14) if _t else (x, y + h + 14)
            self.label(_lx, _ly, label, 9, italic=True, color="#7A5A30", rot=_t)
        return z

    def kosatsuba(self: Settlement, x: float, y: float, rot: float = 0.0, label: str = "notice board", label_above: bool = False, label_xy: Pt | None = None) -> int:  # type: ignore[misc]
        """The KOSATSUBA - the settlement's official notice board: a small roofed frame posting
        the state's STANDING LAW (edicts, porter/packhorse rate tables, ban lists). Sited at the
        most TRAFFICKED public point - the highway frontage, the main street by the gate, a
        bridgehead or market corner - because it is the state talking at everyone who passes
        (Edo's principal board stood at Nihonbashi, the bridgehead). NEVER defaulted to the
        magistrate's manor gate: the manor's own board (Mode A program, buildings.md) posts the
        bench's OUTPUT (verdicts, bounties) for people who come to court, and the manor sits at
        the settlement edge where feet do not pass. True size ~12x5 ft (a 7x3 ft board under a
        small roof); the label carries the read.

        `rot` IS THE ROAD'S BEARING, not a free choice. The glyph's long axis is the board's
        FACE, so a board must stand square to the way it fronts - broadside to the traffic that
        reads it. Turned perpendicular, the face goes edge-on to everyone approaching and the
        institution fails while the siting checks stay green (that is exactly how Nagahara's
        third board shipped, GM 2026-07-27). Hand placements must pass the fronted route's
        bearing; `place_kosatsuba` derives it. Held by `kosatsuba_faces_the_road`. Records M['kosatsuba'] (an overlap-checked
        struct). WHY: settlements.md 'Notice board (kosatsuba)'. Place LAST, on a clear verge
        beside the road, like the fire tower.

        The DRAWN glyph is a LOCATION MARKER at the coarse tiers (GM call 2026-07-24, taking the
        escape settlements.md documented): the true 12x5 ft frame draws 6x2.5 px at village grain
        and 4x1.7 px at city grain - at city scale, rotated upright, that is a 1.7 px sliver that
        reads as gate hardware, not a feature (Nagahara: two of its three boards were invisible
        until the GM went looking, and the one that read did so only by its label). So the glyph
        is floored at KOSATSUBA_MARKER_MIN_PX on its long axis with the 12:5 aspect preserved -
        the wells' doctrine exactly (SKILL.md 'to scale'): the marker denotes the board's
        TO-SCALE LOCATION with legible pixels that are not themselves claimed to be to scale. The
        floor NEVER shrinks a board, so hamlets and towns (1 ft/px) still draw the true 12x5 px;
        only village and city grain lift. The manifest keeps the TRUE w/h (so a size audit reads
        real feet) and records the drawn box as vw/vh, which is what the overlap checks and the
        placement reservation use - the pixels that can actually collide."""
        w, h = self.px(12), self.px(5)
        k = max(1.0, KOSATSUBA_MARKER_MIN_PX / w)  # marker floor, aspect preserved
        vw, vh = w * k, h * k
        hw, hh = vw / 2, vh / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{vw:.1f}" height="{vh:.1f}" rx="1" fill="#7A5A30" stroke="#5A3F1E" stroke-width="0.8"/>')  # the little tiled roof, seen from above
        g.append(f'<line x1="{-hw:.1f}" y1="0" x2="{hw:.1f}" y2="0" stroke="#EFE6CC" stroke-width="0.9"/>')  # the ridge
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M["kosatsuba"].append({"x": round(x, 1), "y": round(y, 1), "w": w, "h": h, "vw": round(vw, 1), "vh": round(vh, 1), "rot": round(rot, 1), "z": z, "label": label})
        self.placed.append((x, y, vw, vh))
        bm = 6
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])
        if label:
            # label_above: for a board standing just inside a gate, the default below-label
            # would hang over the gate structure (labels_clear_of_other_buildings).
            # label_xy: a HAND seat for the caption when BOTH bands are taken - the forcing
            # case was Nagahara's principal board at the market-bend junction, where the
            # below band holds the drum tower, the above band abuts the samurai ward gate's
            # glyph and its caption (settlement-review 2026-08-02: the two stacked captions
            # read as one label on the gate), and the clear ground is diagonal, east along
            # the road edge. Same escape the punishment ground and execution ground carry
            # (label_xy there) and for the same reason: a deferred/derived seat cannot be
            # probed from a gen, so the last resort is an explicit one. Direct-labeled, so
            # label_hugs_its_referent does not govern it - keep a hand seat close enough to
            # read as the board's own. A hand seat keeps its SPOT but the text still tilts
            # with a diagonal board (angled captions, GM 2026-08-02) - same merge as
            # punishment_spot's label_xy.
            # A BOARD IS A LINE SUBJECT, NOT A BUILDING (settlement-review on Kashikawa,
            # 2026-08-17). This used `label_tilt`, which FOLDS mod 90 because a building has two
            # real edge families - and a kosatsuba has ONE meaningful axis, its FACE, the other
            # being its 5 ft depth. The fold is invisible while a board stands nearly square to the
            # page and catastrophic when it does not: a re-pack moved this board onto a lane
            # crossing the old one, its rot went 139.3 -> 49.3, and `label_tilt` returned -40.7 both
            # times - so the caption ran at right angles to the board's face and PARALLEL TO THE
            # OTHER LANE, reading as though it named that way instead. `linear_tilt` clamps rather
            # than folds and goes level past 45 degrees, which is the rule this file's own labels.md
            # docstring states for a line subject ("swapping them" is named there as the trap).
            _t = linear_tilt(rot)
            _chw = max(10.0, len(label) * 8 * 0.28)
            # FOUR DIRECTIONS, WALKED OUTWARD - and the outward part is what these boards need. Note
            # which boards arrive here: `linear_tilt` CLAMPS past 45 degrees, so a board at rot 51.6
            # returns tilt 0.0 and takes THIS branch, not the tilted one. All five seeds that gate
            # 0617 catches are in that group, which is why work on the tilted ladder never touched
            # them (I recorded them as "tilted" from their rot and had to correct it - rot is not
            # tilt past the clamp).
            #
            # Four seats at one fixed distance cannot clear a board standing in a lane crotch, and
            # measured on those seeds the BEST achievable clearance over a wide search is 36-51 ft:
            # good ground exists, the search simply was not reaching it. Six distances out to 60 px,
            # the way `clear_label_seat` rings outward for verge-hugging features - and for the same
            # stated reason, that such a feature sits at the busiest node so its surroundings are the
            # most crowded on the map. The default seat is first, so an unblocked board does not move.
            _cands = [(x, y + hh + 11 + _d) for _d in (0, 12, 24, 36, 48, 60)]
            _cands += [(x, y - hh - 11 - _d) for _d in (0, 12, 24, 36, 48, 60)]
            _cands += [(x + hw + _chw + 8 + _d, y) for _d in (0, 12, 24, 36, 48, 60)]
            _cands += [(x - hw - _chw - 8 - _d, y) for _d in (0, 12, 24, 36, 48, 60)]

            def _box_clearance(_q: Pt, _chw: float = _chw) -> float:
                """Least distance from the caption's BOX to any drawn way's edge (negative = on it)."""
                # READS THE LANE'S EDGE, THE SAME QUANTITY `captions_clear_the_ways_they_stand_on`
                # READS - and it did not, for four attempts. `street_runs` returns polylines with no
                # widths, so this scored distance to the CENTERLINE while the gate scores to the
                # tread EDGE: optimistic by half a lane width, ~2.5-3 px. Every seat the search called
                # best was chosen against a measure the rule does not use, which is why extending the
                # ladder, sliding laterally, walking outward and going 2D all changed nothing on the
                # five failing seeds. The placer and its check must read one source; that is the
                # oldest rule in this engine's CLAUDE.md and I broke it in code written to enforce it.
                _best = 1e9
                for _lane in self.M.get("lanes") or []:
                    _pts = _lane.get("pts") or []
                    _lhalf = float(_lane.get("w") or 3) / 2.0
                    for _i in range(len(_pts) - 1):
                        for _cx, _cy in ((_q[0] - _chw, _q[1] - 5), (_q[0] + _chw, _q[1] - 5), (_q[0] - _chw, _q[1] + 5), (_q[0] + _chw, _q[1] + 5), _q):
                            _best = min(_best, seg_dist(_cx, _cy, _pts[_i], _pts[_i + 1]) - _lhalf)
                return _best

            if label_xy:
                _lx, _ly = label_xy
            elif _t:
                # A TILTED BOARD PUSHES ITS CAPTION FURTHER OFF, because that is the ONE axis that can
                # move it (2026-08-19, third attempt and the first that works). Two levers were tried
                # and measured as EXACT no-ops first, and the reason is worth keeping:
                #
                #   - flipping `above` moves the caption by the board's own 5 ft depth. Not enough.
                #   - sliding LATERALLY along the baseline cannot help AT ALL: `kosatsuba_faces_the_road`
                #     requires the board to FACE its road, so its baseline is PARALLEL to the lane by
                #     rule, and sliding along a parallel line holds the perpendicular distance exactly
                #     constant. Geometrically incapable, not merely mistuned.
                #
                # `gap` is perpendicular to that baseline, so it is the axis that points AWAY from the
                # lane. The ladder stops well inside `LABEL_AIR_CAP` (3 x font size = 24 px at 8 pt),
                # which is what `label_hugs_its_referent` allows before it calls a caption adrift - so a
                # board can buy clearance without losing its subject.
                # THE LADDER MUST REACH PAST THE DIP. Clearance is NOT monotonic in `gap`, because a
                # board sited at the traffic optimum has ways on more than one side - moving away from
                # one lane walks toward another. Enumerated on Kashikawa (12 lanes, board in the lane
                # crotch): 2.0, -1.0, 1.0, -0.3, 7.7 ft at gaps 11/16/21/28/36. A ladder that stopped at
                # 21 took the first rung and left the caption on the tread; the good pocket is at 36.
                # Hug there is 38.5 px, which the pool already carries (inashiro and mizuguchi sit at
                # 41.0 and pass `label_hugs_its_referent`).
                _tilted = [
                    tilt_caption_seat(x, y, rot, _t, hw, hh, _g, above=_ab, lateral=_lat) for _ab in (False, True) for _g in (11, 16, 21, 28, 36) for _lat in (0.0, _chw + hw + 6, -(_chw + hw + 6))
                ]
                _lx, _ly = _tilted[15] if label_above else max(_tilted, key=_box_clearance)
            else:
                # THE HALO MUST NOT NOTCH THE WAY THE BOARD STANDS ON (settlement-review on Inashiro,
                # 2026-08-19). The caption is drawn with a 3 px background halo
                # (`paint-order="stroke"`), and a kosatsuba is sited ON a verge by construction - so
                # the below-seat lands on the lane about as often as not. Measured: the board at
                # (1224,1009) with `lanes[1]` passing x~1235 at w=5, and the halo knocked a visible
                # notch out of the map's busiest internal lane, between the words "notice" and
                # "board". That is the founding-run "caption pierced by its own feature" defect
                # inverted - here the caption does the piercing.
                #
                # So the side is CHOSEN rather than fixed: whichever of the two bands sits further
                # from any drawn way. `label_above=True` stays an unconditional override, because its
                # callers set it for a reason the geometry cannot see (a board just inside a gate,
                # whose below-label would hang over the gate structure).
                # CANDIDATE SEATS, SCORED ON THE CAPTION'S OWN BOX. Choosing between above and below
                # was the first cut and it is not enough: it cannot help where BOTH bands sit on a way,
                # which is Mizuguchi (caption box overlapping the tread by 1.9 ft even after picking the
                # better side). So the lateral seats are candidates too, and the score is the clearance
                # of the whole TEXT BOX rather than of its anchor point - the halo is what notches the
                # lane, and the halo follows the box.
                #
                # Half-width is estimated from the string rather than measured, because the seat has to
                # be chosen BEFORE `self.label` lays the text out. 8 pt italic runs ~0.28 em per
                # character: "notice board" estimates 26.9 px against a measured 26.4 on the shipped
                # sheet, which is close enough to rank seats by.
                # ONE SEARCH, BOTH CONSTRAINTS. A caption must clear STRUCTURES and WAYS, and honoring
                # them in separate places is what left two cohort seeds notched. `label_above` is a
                # two-seat STRUCTURE verdict from the caller (`label_seat_clear` on below, then above);
                # it knows nothing about lanes. Taking a fixed seat on it skipped the lane search
                # entirely - instrumented on seed 14, three of the twenty-four candidates clear the
                # structures and the best of those has 7.8 ft of lane clearance, while the seat the
                # flag forced had -1.2 ft. The good seat was found and then discarded.
                #
                # So every candidate is filtered by the engine's own structure probe and scored on lane
                # clearance. That subsumes the flag - the structural question is asked directly of every
                # seat instead of being inherited as a verdict about two of them - and the flag is kept
                # only for the case where nothing clears the structures at all, where its answer is the
                # best information available.
                _boxes = self.label_blockers("kosatsuba")
                _tw_lab = self.label_caption_hw(label, 8.0)
                _ok = [_q for _q in _cands if self.label_seat_clear(_q[0], _q[1], _tw_lab, 8.0, _boxes)]
                if _ok:
                    _lx, _ly = max(_ok, key=_box_clearance)
                else:
                    _lx, _ly = (x, y - hh - 11) if label_above else (x, y + hh + 11)
            # OUTSIDE the branch chain - all three seats (hand, tilted, chosen) draw their caption here.
            # It sat one level deeper for one revision and a TILTED board silently lost its label
            # entirely: Kashikawa's rot=145.7 takes the `elif _t` branch, never reached the call, and
            # shipped a 12 x 5 ft glyph that nothing on the sheet identifies. Caught only because the
            # clearance probe returned its "no caption found" sentinel instead of a distance - a
            # measurement that could not tell "infinitely clear" from "not there".
            self.label(_lx, _ly, label, 8, italic=True, color="#7A5A30", rot=_t)
        return z

    def fixture_clear_of_water(self: Settlement, x: float, y: float, half: float) -> bool:  # type: ignore[misc]
        """Does a point fixture of half-diagonal `half` stand clear of every watercourse?

        THE VERGE PROBES BYPASS THE WATER CLEARANCE, and this buys it back explicitly. A verge-hugging
        fixture must probe with `_fits(..., corridors=False)` - the corridor test is a HOUSE setback
        from the tread, and applying it would refuse every verge there is - but `corridors=False` also
        switches off the watercourse clearance bundled into the same test, so the probe will happily
        seat a board in a stream. Cohort seed 13 did exactly that (`features_do_not_overlap` on
        ('kosatsuba', 'streams') plus `no_structure_on_stream`) once a homestead re-pack changed which
        verges were free: the board sat at (715, 517) on a 7 px stream, INSIDE the house cloud, so the
        hamlet tier's outside-the-cloud re-seat never even looked at it.

        ONE predicate, two callers - `place_kosatsuba` here and `hamletgen.stage_notice`'s re-seat,
        which faces the identical problem for the identical reason. Fixing only the caller that
        happened to fail would have left the other seating boards in water on the next re-roll.

        Reads the DRAWN courses (`drawn_channels`) as well as the recorded ones, because the filleted
        stroke is what a reader sees and what the overlap matrix measures."""
        for key, default in (("streams", 9.0), ("channels", 2.5), ("field_ditches", 4.2), ("drawn_channels", 2.5)):
            for rec in self.M.get(key) or []:
                pts = rec.get("poly") or rec.get("pts") or []
                need = float(rec.get("w") or default) / 2 + half
                for i in range(len(pts) - 1):
                    if seg_dist(x, y, (pts[i][0], pts[i][1]), (pts[i + 1][0], pts[i + 1][1])) < need:
                        return False
        return True

    def place_kosatsuba(self: Settlement, label: str = "notice board") -> Pt | None:  # type: ignore[misc]
        """AUTO-SITE the settlement kosatsuba on a lane/road verge at the busiest clear node -
        the village/hamlet tiers' procedural sibling of the town/city hand placement (GM
        2026-07-24: EVERY settlement tier carries the board; the ofuregaki circulars reached
        the peasantry through it via the settlement's one required-literate reader - the
        headman, or a hamlet's senior farmer answering to the village headman - and officials
        also read notices aloud, so even a 50-inhabitant hamlet's board works). Deterministic:
        draws NO RNG, so calling it inside `roll_village` cannot perturb a rolled map's seed
        stream. Reads the SAME manifest route fields the validator's siting checks read (the
        dev-loop same-source doctrine): MAIN ways only (`roads`/`M['road']` + `main: True`
        town streets - kosatsuba_on_a_main_way, GM 2026-08-02) when the map declares any,
        else the whole network (`M['lane']` + `M['lanes']` + `town_streets`), and probes
        candidate verge spots with `_fits`, scoring for the most dwellings within ~260 px
        (siting is a TRAFFIC decision - the state talks at everyone who passes) while
        hugging the verge. Call AFTER the lanes, homesteads, and wells and BEFORE the crop, so
        the frame contains the board. No-op under meta(kosatsuba=False); returns the spot, or
        None when no verge inside the validator's ~60-real-ft siting band fits (the
        settlement-tier check would then fire - place by hand or widen the lane network)."""
        if not self.M["meta"].get("kosatsuba", True):
            return None
        ftpx = float(self.M["meta"].get("ftpx") or 1)
        lim = 60.0 / ftpx  # kosatsuba_by_the_road: ~60 REAL feet from a route, in px
        # probe with the DRAWN marker box, not the true footprint (village grain floors the glyph
        # to ~11x4.6 px - see kosatsuba): the spot has to hold the pixels that get drawn there
        w = max(self.px(12), KOSATSUBA_MARKER_MIN_PX)
        h = w * 5 / 12
        # (pts, tread width) per route; road/lane manifest fields carry no width, so assume
        # a generous tread for the bed-avoidance test below.
        # MAIN WAYS ONLY, where the map declares any (GM 2026-08-02, from Ubame: the siter put
        # the board a legal 49 ft off a side lane while the high street ran 200 ft away - "it
        # should be along the main road, in order to be more noticed"). The candidate tiers
        # mirror kosatsuba_on_a_main_way exactly (the same-source doctrine): every road and
        # every main: True town street is a MAIN way, and when the map has at least one, ONLY
        # main-way verges are sampled - a side lane's busiest node is still a side lane, so
        # scoring must never see it. A map with no declared hierarchy (village/hamlet lane
        # webs, towns whose streets are all unflagged) falls back to the whole network, where
        # the busiest-node scoring below stands in for "main". The fallback still needs TOWN
        # STREETS TOO: this probe was written for the lane/lanes tiers, and the omission was
        # invisible until Hirameki - no road, no lanes, all town_streets - gave it not one
        # candidate seat and it returned None (GM 2026-07-27).
        routes: list[tuple[list[Pt], float]] = []
        if self.M.get("road"):
            routes.append(([(p[0], p[1]) for p in self.M["road"]], 18.0))
        routes.extend(([(p[0], p[1]) for p in r["pts"]], 18.0) for r in (self.M.get("roads") or [])[1:])
        routes.extend(([(p[0], p[1]) for p in st["pts"]], float(st.get("w", 18))) for st in self.M.get("town_streets") or [] if st.get("main"))
        if not routes:
            for _st in street_runs(self.M):  # every lane; `M["lane"]` is only the last one drawn
                routes.append((_st, 8.0))
            # A SERVICE LANE IS NOT A PLACE TO POST THE STATE'S NOTICE. The fallback takes the whole
            # network when no way declares itself main, which a hamlet never does - so when the lane
            # web arrived it put ~1,000 ft of 3 ft footpaths into the candidate list on equal footing
            # with the 5 ft spine, and the board re-seated onto one: a settlement-review measured it
            # 34.9 ft off the spine where it had been 9.0, now facing a way the engine itself calls
            # SERVICE. This function's own docstring already states the rule it was breaking - "a
            # side lane's busiest node is still a side lane, so scoring must never see it" - and
            # `web` is exactly the hierarchy flag the hamlet tier lacked. Web lanes are used only if
            # there is nothing else to stand beside.
            _ways = self.M.get("lanes") or []
            _main = [ln for ln in _ways if not ln.get("web")] or _ways
            routes.extend(([(p[0], p[1]) for p in ln["pts"]], float(ln.get("w", 8))) for ln in _main)
            routes.extend(([(p[0], p[1]) for p in st["pts"]], float(st.get("w", 18))) for st in self.M.get("town_streets") or [])
        spots = [(b["x"], b["y"]) for b in self.M["houses"]] + [(b["x"], b["y"]) for b in self.M["buildings"]]

        beds = way_beds(self.M)  # EVERY way bed, not just the routes candidates were sampled from

        def off_every_bed(x: float, y: float) -> bool:
            # the board hugs the verge, so the lane corridor's no-build clearance (a HOUSE
            # setback: homesteads must not crowd the tread) is deliberately bypassed
            # (_fits corridors=False) - but the board must still stand off the TREAD of
            # every route, including ones it was not sampled from (a junction spot offset
            # from lane A can land on lane B, or on a town street or alley this tier's
            # candidate list does not carry at all - see way_beds)
            return all(seg_dist(x, y, bp[k], bp[k + 1]) >= bhw + h / 2 + 3 for bp, bhw in beds for k in range(len(bp) - 1))

        tw_lab = self.label_caption_hw(label, 8.0) if label else 0.0  # the caption half-width the seat must also hold, as RECORDED
        kb_boxes = self.label_blockers("kosatsuba")  # built once: the probe tests many seats against the same map
        cands: list[tuple[int, float, float, float, float, int | None]] = []  # (busy, score, x, y, rot, label_above|None)
        for pts, _rw in routes:
            for i in range(len(pts) - 1):
                (ax, ay), (bx, by) = pts[i], pts[i + 1]
                seg = math.hypot(bx - ax, by - ay)
                if not seg:
                    continue
                ux, uy = -(by - ay) / seg, (bx - ax) / seg  # verge normal
                # long axis ALONG the route: the board's face is broadside to the traffic that
                # reads it, never edge-on (kosatsuba_faces_the_road; see kosatsuba's docstring)
                rot = math.degrees(math.atan2(by - ay, bx - ax))
                for t in range(int(seg // 12) + 1):
                    f = t * 12 / seg
                    mx, my = ax + (bx - ax) * f, ay + (by - ay) * f
                    for side in (1.0, -1.0):
                        off = _rw / 2 + h / 2 + 4
                        while off <= lim:
                            x, y = mx + ux * off * side, my + uy * off * side
                            if off_every_bed(x, y) and self.fixture_clear_of_water(x, y, math.hypot(w, h) / 2) and self._fits(x, y, w, h, corridors=False):
                                busy = sum(1 for sx, sy in spots if math.hypot(x - sx, y - sy) < 260)
                                # THE CAPTION IS PART OF THE SEAT (GM 2026-07-27). The glyph is 11 px
                                # and fits almost anywhere; its caption does not, and the busiest
                                # frontage is exactly where there is least room for one - so a siter
                                # that hunts for ground big enough to hold BOTH walks away from the
                                # traffic and out to the quiet end of the road, which is how Ubame's
                                # board came to stand across the bridge from its own town.
                                lab = 0 if self.label_seat_clear(x, y + h / 2 + 11, tw_lab, 8.0, kb_boxes) else (1 if self.label_seat_clear(x, y - h / 2 - 11, tw_lab, 8.0, kb_boxes) else None)
                                cands.append((busy, busy * 10 - off / 3, x, y, rot, lab))
                            off += 5.0
        if not cands:
            return None
        # ON THE TRAFFIC IS THE RULE; A FITTING CAPTION IS ONLY THE PREFERENCE WITHIN IT. Scoring the
        # caption as a flat bonus large enough to outrank traffic was tried first and re-committed the
        # original sin at one remove: where no seat on a tight village frontage has a clear caption,
        # EVERY caption-clear seat is out in the fields, so all three village boards walked off the
        # frontage and their captions ran off the cropped frame. Open ground for a caption is abundant
        # exactly where nobody is - the same trap as open verge for the board. So the busiest node
        # sets a floor (60% of the best count available), and the caption chooses only among the seats
        # that already stand on the traffic. A board with nowhere to put its caption is still placed,
        # so labels_clear_of_other_buildings reports it rather than the siter hiding it.
        floor = 0.6 * max(c[0] for c in cands)
        _b, _s, x, y, rot, lab = max((c for c in cands if c[0] >= floor), key=lambda c: (c[5] is not None, c[1]))
        self.kosatsuba(x, y, rot, label=label, label_above=bool(lab))
        return (x, y)

    def place_punishment_spot(self: Settlement, label: str | None = "punishment ground", label_xy: Pt | None = None) -> Pt | None:  # type: ignore[misc]
        """AUTO-SITE the punishment ground on a street verge at the busiest clear node - the notice
        board's sibling, and for the same reason: both institutions are sited by FOOT TRAFFIC, so
        both want the same probe rather than a hand-picked rect. (Hand rects were tried first on
        three maps and all three failed `punishment_spot_by_the_traffic` the same way: `open_seat`
        ties toward the rect's CENTER, which is the open ground behind the frontage, precisely where
        this feature must not be.) Deterministic - draws no RNG.

        Reads the SAME manifest route fields the validator reads (the dev-loop same-source doctrine),
        including `town_streets`, which the board's village-tier probe does not need. Keeps the spot
        inside the rampart where there is one - the display faces the town, not the road out; that is
        the execution ground's job. No-op under meta(punishment_spot=False). Returns the spot, or
        None when no verge fits (the presence check then fires - place by hand)."""
        if not self.M["meta"].get("punishment_spot", True):
            return None
        ftpx = float(self.M["meta"].get("ftpx") or 1)
        lim = 60.0 / ftpx  # punishment_spot_by_the_traffic: ~60 REAL feet from a street
        w, h = self.px(PUNISHMENT_SPOT_FT[0]), self.px(PUNISHMENT_SPOT_FT[1])
        routes: list[tuple[list[Pt], float]] = []
        if self.M.get("road"):
            routes.append(([(p[0], p[1]) for p in self.M["road"]], float(self.M.get("road_width") or 18)))
        routes.extend(([(p[0], p[1]) for p in st["pts"]], float(st.get("w", 18))) for st in self.M.get("town_streets") or [])
        routes.extend(([(p[0], p[1]) for p in ln["pts"]], float(ln.get("w", 8))) for ln in self.M.get("lanes") or [])
        if not routes:
            return None
        wall = self.M.get("wall")
        spots = [(b["x"], b["y"]) for b in self.M["houses"]] + [(b["x"], b["y"]) for b in self.M["buildings"]]
        beds = way_beds(self.M)  # see way_beds: EVERY bed, including the alleys and the ring road
        # this list does not sample candidates from - a display bypasses the lane CORRIDOR
        # deliberately (it is a house setback), never the roadbed itself

        def off_every_bed(x: float, y: float) -> bool:
            return all(seg_dist(x, y, bp[k], bp[k + 1]) >= bhw + h / 2 + 3 for bp, bhw in beds for k in range(len(bp) - 1))

        best: tuple[float, float, float, float] | None = None  # (score, x, y, rot)
        # ...and the best seat that is ALSO out from under the captions already on the map. A
        # PREFERENCE, not a filter (2026-08-08): landing under someone else's caption is a real
        # defect - Minami's ground auto-sited onto the burakumin quarter's label when a reflow moved
        # the busiest node 24px north - but it is the caption's problem to solve, and refusing the
        # seat outright would let a densely-captioned quarter drive the whole probe to None, i.e.
        # turn "the label wants moving" into "the city has no punishment ground at all". So: take a
        # clear seat when one exists at any score, and fall back to the busiest seat when none does.
        best_clear: tuple[float, float, float, float] | None = None
        for pts, _rw in routes:
            for i in range(len(pts) - 1):
                (ax, ay), (bx, by) = pts[i], pts[i + 1]
                seg = math.hypot(bx - ax, by - ay)
                if not seg:
                    continue
                ux, uy = -(by - ay) / seg, (bx - ax) / seg
                rot = math.degrees(math.atan2(by - ay, bx - ax))
                for t in range(int(seg // 12) + 1):
                    f = t * 12 / seg
                    mx, my = ax + (bx - ax) * f, ay + (by - ay) * f
                    for side in (1.0, -1.0):
                        off = _rw / 2 + h / 2 + 4
                        while off <= lim:
                            x, y = mx + ux * off * side, my + uy * off * side
                            if (not wall or len(wall) < 3 or point_in_poly(x, y, wall)) and off_every_bed(x, y) and self._fits(x, y, w, h, corridors=False):
                                busy = sum(1 for sx, sy in spots if math.hypot(x - sx, y - sy) < 260)
                                score = busy * 10 - off / 3
                                if best is None or score > best[0]:
                                    best = (score, x, y, rot)
                                if not self._under_a_caption(x, y, w, h, rot) and (best_clear is None or score > best_clear[0]):
                                    best_clear = (score, x, y, rot)
                            off += 5.0
        best = best_clear or best
        if best is None:
            return None
        _, x, y, rot = best
        if label and label_xy is None:
            # A verge-hugging feature's DEFAULT below-label lands on the frontage it hugs - that is
            # not bad luck, it is what "hugging the frontage" means, and it fired on all three maps.
            # So probe the label too: below, above, then left/right, first clear box wins.
            label_xy = self.clear_label_seat(x, y, w, h, label, skip_key="punishment_spots")
        self.punishment_spot(x, y, rot, label=label, label_xy=label_xy)
        return (x, y)

    def drum_tower(self: Settlement, x: float, y: float, tw: float | None = None, label: str = "drum tower") -> int:  # type: ignore[misc]
        """A combined BELL-AND-DRUM TOWER (zhonggulou) - the timekeeping/curfew institution of a
        WALLED seat (GM 2026-07-24). Morning bell, evening drum: dawn gate-opening, the dusk
        gate-closing that starts the street curfew, the five night watches, alarm and ceremony.
        Part of the standard county-seat kit (yamen, temples, drum tower); a county seat had ONE
        combined tower - the paired gulou/zhonglou on an axis is capital grammar (Pingyao, a
        wealthy county seat, has exactly one Market Tower, ~60 ft). Distinct from the fire towers:
        fire watch was a SEPARATE institution in both reference cultures (Song Kaifeng ran
        dedicated fire-lookout towers; Edo split the licensed toki-no-kane time bell from the
        hinomi-yagura). Drawn as a heavy masonry platform (county tier ~60-80 ft square) carrying
        a timber pavilion with the drum and the bell - visibly heavier-built than the skeletal
        braced-frame fire towers. Stands at the main street crossing, near (not inside) the yamen.
        Records M['drum_towers'] (an overlap-checked struct) and reserves a no-build block."""
        if tw is None:
            tw = self.px(
                36
            )  # county-tier footprint RE-VERIFIED (GM eye + research 2026-07-24): Pingyao's Market Tower - the wealthy-county showpiece - is ATTESTED at 133.4 m^2 plan (~38 ft square); these towers dominate by HEIGHT (50-60 ft), not plan, so ~36 ft = one rowhouse width reads correctly. The first-draft 70 ft was contaminated by garrison street-arch platforms (Dingbian 52 ft, Xingcheng 66 ft) - that variant is prefecture/garrison tier, never a 3,000-person seat
        h = tw / 2
        hi = tw * 0.31  # the pavilion atop the platform
        g = [f'<g transform="translate({x:.0f},{y:.0f})">']
        g.append(f'<rect x="{-h:.1f}" y="{-h:.1f}" width="{tw:.1f}" height="{tw:.1f}" rx="1.5" fill="#E3D7B8" stroke="#4A3318" stroke-width="2.4"/>')  # the masonry platform
        g.append(f'<rect x="{-hi:.1f}" y="{-hi:.1f}" width="{hi * 2:.1f}" height="{hi * 2:.1f}" rx="1" fill="#C9A57A" stroke="#4A3318" stroke-width="1.5"/>')  # the timber pavilion
        g.append(f'<line x1="{-hi:.1f}" y1="0" x2="{hi:.1f}" y2="0" stroke="#4A3318" stroke-width="0.9" opacity="0.7"/>')  # the pavilion roof ridge
        g.append(
            f'<circle cx="{-tw * 0.155:.1f}" cy="0" r="{max(tw * 0.105, 1.2):.1f}" fill="#8A4A2A" stroke="#4A3318" stroke-width="0.8"/>'
        )  # the great drum (radius floored - legible at the corrected 12px platform)
        g.append(f'<circle cx="{tw * 0.155:.1f}" cy="0" r="{max(tw * 0.08, 0.9):.1f}" fill="#6B5A3A" stroke="#4A3318" stroke-width="0.8"/>')  # the bell
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("drum_towers", []).append({"x": round(x, 1), "y": round(y, 1), "w": tw, "h": tw, "rot": 0.0, "z": z, "label": label})
        self.placed.append((x, y, tw, tw))
        bm = 12
        # the block reserves the caption band below too, AT THE CAPTION'S WIDTH - the corrected
        # 36 ft platform is narrower than the "drum tower" text, so a footprint-width band let
        # rowpack houses slide under the caption's ends (GM tower-resize ripple, 2026-07-24)
        self.block_polys.append([(x - h - bm, y - h - bm), (x + h + bm, y - h - bm), (x + h + bm, y + h + bm), (x - h - bm, y + h + bm)])
        cb_ = max(h + bm, 2.9 * len(label) + 10)
        self.block_polys.append([(x - cb_, y + h), (x + cb_, y + h), (x + cb_, y + h + 40), (x - cb_, y + h + 40)])
        # the caption is TWO LINES, "drum/bell" over "tower" (GM 2026-07-24): the county tower is
        # genuinely the combined zhonggulou - both instruments in one building, and both are drawn
        self.label(x, y + h + 12, "drum/bell", 9, italic=True, color="#4A3318")
        self.label(x, y + h + 24, "tower", 9, italic=True, color="#4A3318")
        return z
