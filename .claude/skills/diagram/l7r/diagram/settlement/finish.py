"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import json
import math
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from ._geom import LAND, Pt, label_quad, label_tilt, linear_tilt, linear_tilt_full, point_in_poly, seg_closest, seg_dist, segments_cross

if TYPE_CHECKING:
    from .core import Settlement


class FinishMixin:
    # ---- annotation

    def _record_label(self: Settlement, x: float, y: float, text: str, size: float, anchor: str, z: int, ref: Sequence[float] | None = None, rot: float = 0.0) -> None:  # type: ignore[misc]
        w = len(text) * size * 0.55  # rough serif advance; slightly generous so near-misses flag
        x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        # record the TEXT (element [5]) too, so the gate can verify a zone/neighborhood label actually
        # sits with the cluster it names (same side of the wall, among its buildings)
        rec: list[Any] = [round(x0, 1), round(y - size * 0.8, 1), round(x0 + w, 1), round(y + size * 0.25, 1), z, text]
        if ref is not None or rot:
            # element [6]: the box of the ONE feature this caption names, recorded only by the
            # standoff-ladder path (`place_caption` / the road label). A district caption names an
            # AREA, not a thing, so it carries no referent and `label_hugs_its_referent` skips it.
            # (Recorded as null when only a tilt follows - the elements are positional.)
            rec.append([round(float(v), 1) for v in ref] if ref is not None else None)
        if rot:
            # element [7]: the caption's TILT in degrees (see label_tilt) - present ONLY when
            # nonzero, so every level caption's record stays byte-identical to the pre-tilt
            # format (the 695-manifest regression corpus reads unchanged). Elements [0..3] stay
            # the UNROTATED box; label_quad / label_aabb derive the drawn geometry from it.
            rec.append(rot)
        self.M["labels"].append(rec)

    def label(  # type: ignore[misc]
        self: Settlement,
        x: float,
        y: float,
        text: str,
        size: float = 12,
        anchor: str = "middle",
        italic: bool = False,
        weight: str = "normal",
        color: str = "#2D2A24",
        ref: Sequence[float] | None = None,
        rot: float = 0.0,
        linear: bool = False,
        full_tilt: bool = False,
    ) -> None:
        esc = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        st = ' font-style="italic"' if italic else ''
        # `rot` is the SUBJECT's rotation; the fold turns it into the caption's tilt (0 for any
        # square rotation, so nothing changes for level callers). A tilted caption rotates about
        # its recorded box's CENTER, so label_quad reads the drawn glyph run straight off the
        # record (GM 2026-08-02, angled-building labels).
        #
        # `linear=True` says the subject is a LINE, not a box - a road, a street, a frontage row
        # laid along one - and takes `linear_tilt`'s CLAMP instead of `label_tilt`'s FOLD (GM
        # 2026-08-08). The two are not interchangeable: the fold would send a 72-degree road's
        # caption to -18 degrees, an angle nothing on the map is drawn at.
        # `full_tilt=True` (linear subjects only) takes linear_tilt_full's unclamped angle - the
        # GM's 2026-08-09 extension for along-row captions like the wharf granary rows
        tilt = (linear_tilt_full(rot) if full_tilt else linear_tilt(rot)) if linear else label_tilt(rot)
        if tilt:
            w_ = len(text) * size * 0.55
            x0_ = x - w_ / 2 if anchor == "middle" else (x - w_ if anchor == "end" else x)
            tr = f' transform="rotate({tilt:.1f} {x0_ + w_ / 2:.1f} {y - size * 0.275:.1f})"'
        else:
            tr = ''
        # labels live in the topmost LABEL layer so nothing - not a road, not a wall, not a kido or torii
        # - ever paints over the text (a label must always be fully readable)
        z = self.add_label(
            f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}"{st}{tr} fill="{color}" paint-order="stroke" stroke="{LAND}" stroke-width="3">{esc}</text>'
        )
        self._record_label(x, y, text, size, anchor, z, ref, tilt)

    def _text_width(self: Settlement, s: str, fs: float) -> float:  # type: ignore[misc]
        """Measured pixel width of bold `s` at font-size `fs` in the RENDER font (DejaVu Serif Bold -
        what resvg substitutes for 'serif'), via PIL; falls back to a calibrated estimate when PIL or
        the font is absent. WHY (GM 2026-07-21): the em/char estimates under-measured wide lowercase
        names - 'Akagahara' measured 180px against a 167px estimate, and the missing 14px ran the
        name off its placard's right edge. Measuring the actual glyphs makes the padding true.

        The layout engine is PINNED to BASIC, and that pin is load-bearing (2026-07-25). PIL picks its
        engine at runtime - RAQM when libraqm happens to be installed, BASIC when it is not - and the
        two disagree: BASIC sums integer-rounded glyph advances, RAQM sums true subpixel ones, so the
        same name measures 110.00 vs 110.59 ('Honda') or 103.95 vs 101.70 ('Tango'). That fraction of
        a pixel sizes the title placard, which is recorded in the manifest, so a container that merely
        HAS libraqm regenerates every titled map to different bytes: a laptop crash and a container
        rebuild dirtied all 16 tracked pool manifests at once, with no code change behind it. Which
        engine is not the point (both are within a pixel of what resvg draws, under 12px of padding) -
        being a pure function of the font FILE is, so the pool stays byte-reproducible on any
        container. `test_text_width_is_pinned_to_the_basic_layout_engine` holds the pin."""
        try:
            from PIL import ImageFont

            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", int(round(fs)), layout_engine=ImageFont.Layout.BASIC)
            return float(f.getlength(s))
        except Exception:  # PIL / font absent: the engine stays standalone on a generous estimate
            return len(s) * fs * 0.62

    def title(self: Settlement, name: str, fs: float = 30) -> None:  # type: ignore[misc]
        """Place the map title (the bold place name plus a scale bar under it) over BLANK space: scan the
        rendered window for a spot where the box clears every feature (buildings, fields, water, groves,
        the pond), scanning top-first so the title lands high when it can. Records the placed box in M['title']
        so `title_clear_of_features` can verify it. Call AFTER crop_to_content, so the search runs over the
        framed window. Falls back to the top-left of the view (or the canvas center) only if the map is too full
        to find any gap.

        SCALE BAR (GM 2026-07-20: every settlement map shows its scale, matching the Mode A compound
        sheets): the bar spans 100 map-px, which is a round real distance at every rung of the GM's
        scale ladder - 100 ft at hamlet/town (1 ft/px), 200 ft at village (2 ft/px), 300 ft at
        provincial city (3 ft/px) - drawn in the Mode A furniture style (end ticks + mid tick, the
        distance under the bar, a fine-print '(1 px = N ft)' line). The searched AND recorded box
        covers the title + bar together, so `title_clear_of_features` gates the bar's placement too.

        PLACARD (GM 2026-07-21): the title + scale bar sit on a stylized parchment CARD - a cream
        cartouche (lighter than the #EFE3C2 ground, double-line brown border) drawn under the text -
        so the block stays legible no matter what ground cover it lands over (the satoyama ring put
        scrub speckle nearly everywhere a title can sit, and ink-on-scrub was hard to read). The
        searched and recorded box is the PLACARD's extent, so the clearance check gates the whole
        card; `title_has_placard` gates its presence (a manifest without one predates the card)."""
        tw, th = self._text_width(name, fs) + 4, fs * 1.2  # MEASURED text box (+4 breathing room) - see _text_width; symmetric placard padding follows for free
        bar_px, bar_ft = 100.0, round(100 * self.ftpx)
        PAD = 12  # placard padding around the text block
        bw, bh = max(tw, bar_px) + 2 * PAD, th + 46 + 2 * PAD  # the searched box: the whole placard
        vx0, vy0, vw, vh = self.view if self.view else (0, 0, self.W, self.H)
        spot = self._blank_label_spot(vx0, vy0, vw, vh, bw, bh)
        if spot:
            px0, py0 = spot
        elif self.view:  # map too full - fall back to the top-left corner
            px0, py0 = vx0 + 30, vy0 + 16
        else:
            px0, py0 = self.W / 2 - bw / 2, 22
        y = py0 + PAD  # the text block's top, inside the card
        pcx = px0 + bw / 2  # the placard's axis: the name AND the scale bar center on it (GM 2026-07-21)
        self.M["title"] = {
            "name": name,
            "bbox": [round(px0, 1), round(py0, 1), round(px0 + bw, 1), round(py0 + bh, 1)],
            "placard": [round(px0, 1), round(py0, 1), round(px0 + bw, 1), round(py0 + bh, 1)],
        }
        self.add_label(  # the card FIRST, so every text draws over it (add_label draws in call order)
            f'<g><rect x="{px0:.0f}" y="{py0:.0f}" width="{bw:.0f}" height="{bh:.0f}" rx="7" fill="#F7F0DC" fill-opacity="0.94" stroke="#8C7A55" stroke-width="1.6"/>'
            f'<rect x="{px0 + 3.5:.0f}" y="{py0 + 3.5:.0f}" width="{bw - 7:.0f}" height="{bh - 7:.0f}" rx="5" fill="none" stroke="#BCAA7E" stroke-width="0.8"/></g>'
        )
        self.add_label(f'<text x="{pcx:.0f}" y="{y + fs:.0f}" text-anchor="middle" font-size="{fs}" font-weight="bold" fill="#2D2A24">{name}</text>')
        bx0, bx1, by = pcx - bar_px / 2, pcx + bar_px / 2, y + th + 12  # bar CENTERED under the name, on the placard's axis
        self.M["scalebar"] = {"ft": bar_ft, "ftpx": self.ftpx, "bbox": [round(bx0, 1), round(by - 5, 1), round(bx1, 1), round(y + bh, 1)]}
        self.add_label(
            f'<g stroke="#3A2E1C" stroke-width="2">'
            f'<line x1="{bx0:.0f}" y1="{by:.0f}" x2="{bx1:.0f}" y2="{by:.0f}"/>'
            f'<line x1="{bx0:.0f}" y1="{by - 5:.0f}" x2="{bx0:.0f}" y2="{by + 5:.0f}"/>'
            f'<line x1="{bx1:.0f}" y1="{by - 5:.0f}" x2="{bx1:.0f}" y2="{by + 5:.0f}"/>'
            f'<line x1="{(bx0 + bx1) / 2:.0f}" y1="{by - 3:.0f}" x2="{(bx0 + bx1) / 2:.0f}" y2="{by + 3:.0f}" stroke-width="1"/>'
            f'</g>'
        )
        self.add_label(f'<text x="{(bx0 + bx1) / 2:.0f}" y="{by + 17:.0f}" text-anchor="middle" font-size="12" fill="#3A2E1C">{bar_ft} ft</text>')
        self.add_label(f'<text x="{(bx0 + bx1) / 2:.0f}" y="{by + 31:.0f}" text-anchor="middle" font-size="10" font-style="italic" fill="#5C4830">(1 px = {self.ftpx:g} ft)</text>')

    def _title_obstacles(self: Settlement) -> tuple[list[Any], list[Any], list[Any]]:  # type: ignore[misc]
        """Feature footprints a title must clear, as (rects, polys, lines). Solid buildings/plots -> rects;
        the fields, groves, and commons -> polygons (so the title can sit in the empty corners around a diagonal
        field); the pond -> a rect; water lines + lanes -> polylines (a title must not cross a road or stream)."""
        rects: list[Any] = []
        polys: list[Any] = []
        lines: list[Any] = []
        for k in (
            "houses",
            "gardens",
            "threshing_yards",
            "groves",
            "dry_plots",
            "buildings",
            "manors",
            "religious",
            "shrines",
            "flophouses",
            "storehouses",
            "merchant_estates",
            "cemeteries",
            "mausoleums",
            "cremation_grounds",
            "ossuaries",
            "ministries",
        ):
            for o in self.M.get(k, []):
                if o.get("poly"):
                    xs = [p[0] for p in o["poly"]]
                    ys = [p[1] for p in o["poly"]]
                    rects.append((min(xs), min(ys), max(xs), max(ys)))
                elif "w" in o and "h" in o:
                    rects.append((o["x"] - o["w"] / 2, o["y"] - o["h"] / 2, o["x"] + o["w"] / 2, o["y"] + o["h"] / 2))
        for lb in self.M.get("labels", []):  # placed LABEL boxes: a title must never cover a label
            rects.append((lb[0], lb[1], lb[2], lb[3]))  # (caught 2026-07-23: the Tango content crop landed the
            #                                             placard on the 'pauper ossuary mound' label)
        # NOT the scrub commons: it is sparse GROUND COVER (a feathered scatter of grass tufts on open ground),
        # not a feature with a footprint, and a bold place name reads perfectly well over it. Treating it as an
        # obstacle only worked while some ground was left bare - once the commons properly clothes the field's
        # voids too, scrub covers nearly the whole map and a title could find nowhere at all to sit. The grove
        # (dense closed canopy) and the marsh (a distinct wetland) stay obstacles.
        # ...and a WOODLAND commons is dense canopy too, so it is an obstacle by the same test the
        # paragraph above applies (2026-08-17). The exclusion above is for the SCRUB commons - a
        # feathered scatter of grass tufts that a bold place name reads perfectly well over - and a
        # `role="woodland"` parcel is not that: it is a stand of tree crowns, the same closed canopy
        # as a grove. Left out, the placard printed over 64-68% of one of Sawada's two woodland
        # parcels, with a dozen crown circles ghosting up through the title card: one of the map's
        # two woods two-thirds invisible, and the title reading as smudged. The grazing parcels stay
        # excluded, which is what keeps a title from having nowhere to sit.
        _woodland = [c for c in self.M.get("commons", []) if c.get("role") == "woodland" and c.get("poly")]
        for o in self.M.get("village_groves", []) + self.M.get("marshes", []) + _woodland:
            polys.append([tuple(p) for p in o["poly"]])
        for fd in self.M.get("fields", []):
            polys.append([tuple(p) for p in fd["outline"]])
        if self.M.get("pond"):
            cx, cy, rx, ry = self.M["pond"]
            rects.append((cx - rx, cy - ry, cx + rx, cy + ry))
        for o in self.M.get("streams", []) + self.M.get("channels", []):
            lines.append([tuple(p) for p in o["poly"]])
        for ln in self.M.get("lanes", []):
            lines.append([tuple(p) for p in ln["pts"]])
        # CITY barriers + arteries (caught 2026-07-23, the aggressive Tango content crop): with no blank
        # corner left, the placard landed straddling the rampart/moat band - the wall, moat, ring road,
        # and the through-road are obstacles too (crossing the centerline is what the box test catches;
        # the placard is taller than the wall-moat gap, so it cannot hide between them).
        for key in ("wall", "moat", "ring_road", "road"):
            pl = self.M.get(key)
            if pl and len(pl) >= 2:
                lines.append([tuple(p) for p in pl])
        return rects, polys, lines

    def _box_clear(self: Settlement, bx0: float, by0: float, bx1: float, by1: float, obs: Any) -> bool:  # type: ignore[misc]
        """Whether the axis-aligned box clears every obstacle in (rects, polys, lines)."""
        rects, polys, lines = obs
        for ox0, oy0, ox1, oy1 in rects:
            if not (bx1 < ox0 or bx0 > ox1 or by1 < oy0 or by0 > oy1):
                return False
        corners = [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]
        for poly in polys:
            n = len(poly)
            if (
                any(point_in_poly(cx, cy, poly) for cx, cy in corners)
                or any(bx0 <= vx <= bx1 and by0 <= vy <= by1 for vx, vy in poly)
                or any(segments_cross(corners[e], corners[(e + 1) % 4], poly[k], poly[(k + 1) % n]) for e in range(4) for k in range(n))
            ):
                return False
        for poly in lines:
            if any(bx0 <= vx <= bx1 and by0 <= vy <= by1 for vx, vy in poly) or any(
                segments_cross(corners[e], corners[(e + 1) % 4], poly[k], poly[k + 1]) for e in range(4) for k in range(len(poly) - 1)
            ):
                return False
        return True

    def _blank_label_spot(self: Settlement, vx0: float, vy0: float, vw: float, vh: float, tw: float, th: float, margin: float = 22, step: float = 24) -> Pt | None:  # type: ignore[misc]
        """Scan the window (top-to-bottom, left-to-right) for the first box of size (tw, th) that clears every
        feature; returns its (x, y) top-left, or None if the map is too full."""
        obs = self._title_obstacles()
        y = vy0 + margin
        while y + th <= vy0 + vh - margin:
            x = vx0 + margin
            while x + tw <= vx0 + vw - margin:
                if self._box_clear(x, y, x + tw, y + th, obs):
                    return (x, y)
                x += step
            y += step
        return None

    def finish(self: Settlement, basepath: str, render: bool = True, png_width: int = 2600) -> int:  # type: ignore[misc]
        # BACKSTOP for the deferred canopy: crop_to_content / crop_city normally flush it, but a map
        # that frames to the bare canvas never calls either (Hoshizora), and a queued stand that is
        # never flushed is a wood with no trees. Idempotent, so the usual crop-time flush still wins.
        self.flush_tree_stands()
        # Deferred place_caption() seats, in call order, against the FINISHED map - and BEFORE the
        # road caption, which goes last because it has by far the most room to move: its subject is
        # a whole road segment with a wide slide set, where a market row's caption has one short
        # stretch of frontage to sit against. Most-constrained-first; the road yields.
        for _tx, _bx, _sz, _it, _wt, _co, _hi, _sl, _ro in self._captions:
            _lx, _ly = self._best_label_spot(_bx, _tx, _sz, hint=_hi, slides=_sl, tilt=_ro)
            self.label(_lx, _ly, _tx, _sz, italic=_it, weight=_wt, color=_co, ref=_bx, rot=_ro)
        self._captions: list[tuple[Any, ...]] = []
        if getattr(self, "_road_label", None):
            text, lx, ly = self._road_label
            rd = self.M.get("road") or []
            # The caption names the ROAD, so its subject is the nearest STRETCH of roadway: box
            # that segment out to the corridor half-width and run the standard standoff ladder
            # against it. The authored label_xy stays a HINT - which flank, and where along the
            # road - and no longer sets the distance. That was the defect the GM caught on Tango
            # (2026-07-26): the old candidates were generated at the anchor's own perpendicular
            # offset, mirrored across the roadline and slid along it, so a hand anchor 102px out
            # produced a label 55px clear of the roadway with nothing but bare ground between.
            half = float(self.M.get("road_width") or 26) / 2
            i_ = min(range(len(rd) - 1), key=lambda i: seg_dist(lx, ly, rd[i], rd[i + 1]))
            (ax_, ay_), (bx_, by_) = (rd[i_][0], rd[i_][1]), (rd[i_ + 1][0], rd[i_ + 1][1])
            # The subject is the roadway's CROSS-SECTION at the point the anchor pointed at, plus
            # the tangent there - NOT the segment's bounding box, which for a diagonal road is a
            # huge square whose edges are hundreds of px from the roadway (Hoshizora: a 486x256 box
            # for a road running through it at 27 degrees). Cross-section + axis is right at any angle.
            px_, py_ = seg_closest(lx, ly, (ax_, ay_), (bx_, by_))
            seg_ = math.hypot(bx_ - ax_, by_ - ay_) or 1.0
            axis_ = ((bx_ - ax_) / seg_, (by_ - ay_) / seg_)
            # ...and the caption RUNS ALONG that tangent (GM 2026-08-08): "Imperial Road" set level
            # beside Hoshizora's -27deg roadbed named the road the way a caption beside a diagonal
            # building named the building - which is the defect the 2026-08-02 tilt fixed for
            # glyphs and stopped short of fixing for the linear features. A road is a LINE, so this
            # takes linear_tilt's clamp, NOT label_tilt's fold: past 45deg the caption goes level
            # (the GM's own north-south convention), where the fold would tilt it to the road's
            # cross direction, which is an axis of nothing. Tango (due N-S) and Nagahara (72deg)
            # therefore stay exactly as they were; only genuinely diagonal roads move.
            tilt_ = linear_tilt(math.degrees(math.atan2(axis_[1], axis_[0])))
            box = (px_ - half, py_ - half, px_ + half, py_ + half)
            lx, ly = self._best_label_spot(box, text, 12, hint=(lx, ly), slides=(-45.0, 45.0, 90.0, -90.0), axis=axis_, tilt=tilt_)
            # RE-SEAT the recorded subject on the roadway beside where the caption actually landed.
            # `label_hugs_its_referent` measures an axis-aligned gap between two recorded boxes, so a
            # cross-section pinned at the ANCHOR reads the along-road distance as drift once the
            # ladder slides the caption - Tango measured 45px for a caption sitting 29px off the
            # roadway. Boxing the roadway nearest the caption's own box makes the recorded gap the
            # clearance a reader sees, at any road angle.
            # A TILTED caption re-seats on the quad it actually DRAWS, not its pre-tilt box - the
            # recorded gap has to be the clearance a reader sees. At tilt 0 label_quad returns that
            # box corner-for-corner in the same order, so every level road's referent is unchanged.
            lb_ = self._label_box(lx, ly, text, 12)
            qs_ = label_quad([*lb_, 0, text, None, tilt_])
            cq_ = ((qs_[0][0] + qs_[2][0]) / 2, (qs_[0][1] + qs_[2][1]) / 2)
            px_, py_ = min(
                (seg_closest(qx, qy, (ax_, ay_), (bx_, by_)) for qx, qy in (*qs_, cq_)),
                key=lambda c: min(math.hypot(c[0] - qx, c[1] - qy) for qx, qy in qs_),
            )
            box = (px_ - half, py_ - half, px_ + half, py_ + half)
            self.label(lx, ly, text, 12, italic=True, weight="bold", color="#5A4326", ref=box, rot=tilt_, linear=True)
            self.M["road_label"] = [lx, ly]
            self._road_label = None
        splices: list[Any] = []  # (placeholder_idx, block) - spliced high-index-first below
        if self._ground_idx is not None:  # the ordered linear-ground block (alley<street<road)
            feats = sorted(self.ground, key=lambda g: (g["zpri"], g["seq"]))
            block: list[Any] = []
            edge_zs: list[Any] = []
            bed_zs: list[Any] = []
            for g in feats:  # EDGES first (the dark borders), bottom of the block
                if g["edge"] is not None:
                    edge_zs.append(self._ground_idx + len(block))
                    block.append(g["edge"])
            for g in feats:  # then BEDS (paved surfaces) - they merge at crossings
                if g["bed"] is not None:
                    g["rec"][g["zkey"]] = self._ground_idx + len(block)  # recorded z = the bed's draw position
                    bed_zs.append(self._ground_idx + len(block))
                    block.append(g["bed"])
            for g in feats:  # then TOP marks (center dashes / gravel speckle)
                if g["top"] is not None:
                    block.append(g["top"])
            if edge_zs:  # every edge sits below every bed -> clean crossroads
                self.M["ground_edge_zmax"] = max(edge_zs)
            if bed_zs:
                self.M["ground_bed_zmin"] = min(bed_zs)
            splices.append((self._ground_idx, block))
        # Does a LATE-block channel JOIN the pond? Then the pond's FILL + SHEEN must RELOCATE into
        # the late block (GM 2026-07-23, Tango's in-wall tank): the late block draws after the whole
        # shared block, so an early fill can never cover a late mouth's inside-the-rim overshoot -
        # the channel's round end-cap rode ON TOP of the open water and read as intersecting the
        # pond. The rim EDGE stays early (below every bed, so the mouth still covers it); only the
        # fill and sheen move, re-emitted LAST among the late beds - restoring exactly the covering
        # order the shared block gives an early feeder. Gated by pond_fill_covers_channel_mouths.
        _pond_late = False
        if self.M.get("pond") and self._pond_entry is not None and self._late_water_idx is not None:
            _pex, _pey, _perx, _pery = self.M["pond"]
            _pond_late = any(ch["late"] and ((q[0] - _pex) / _perx) ** 2 + ((q[1] - _pey) / _pery) ** 2 <= 1.12 for ch in self.M.get("drawn_channels", []) for q in (ch["pts"][0], ch["pts"][-1]))
        if self._water_idx is not None:  # the watercourse block: all EDGES (pond rims), then all
            wblock: list[Any] = []  # BEDS (one opacity group), then all SHEENS - crossings MERGE
            bedzs: list[Any] = []
            sheenzs: list[Any] = []
            for w in self.water:  # rims below every bed -> a feeder's bed covers the rim at its mouth
                if w.get("edge") is not None:
                    wblock.append(w["edge"])
            for w in self.water:  # a pond-anchored feeder is snapped to the rim now that the
                w["_bed"], w["_sheen"] = w["bed"], w["sheen"]  # pond is known (deferred - it may predate the pond)
                if w["clip"] is not None and self.M.get("pond"):
                    cp = self._clip_to_pond(w["clip"]["pts"])
                    dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in cp)
                    w["_bed"] = w["clip"]["bed_t"].format(dd=dd)
                    if w["clip"]["sheen_t"] is not None:
                        w["_sheen"] = w["clip"]["sheen_t"].format(dd=dd)
            wblock.append('<g opacity="0.85">')
            for w in sorted(self.water, key=lambda w: w["pond_fill"]):  # pond FILL drawn LAST (stable sort) so it
                if _pond_late and w is self._pond_entry:
                    continue  # fill relocates to the late block (see above) - the rim edge already emitted
                w["rec"]["bedz"] = self._water_idx + len(wblock)  # covers any feeder's inside-the-rim overshoot
                bedzs.append(self._water_idx + len(wblock))
                wblock.append(w["_bed"])
            wblock.append('</g>')
            wblock.append('<g opacity="0.55">')
            for w in self.water:
                if w["_sheen"] is not None:
                    if _pond_late and w is self._pond_entry:
                        continue  # the pond sheen moves with its fill
                    w["rec"]["sheenz"] = self._water_idx + len(wblock)
                    sheenzs.append(self._water_idx + len(wblock))
                    wblock.append(w["_sheen"])
            wblock.append('</g>')
            if bedzs:  # every bed sits below every sheen -> clean confluence
                self.M["water_bed_zmax"] = max(bedzs)
            if sheenzs:
                self.M["water_sheen_zmin"] = min(sheenzs)
            splices.append((self._water_idx, wblock))
        if self._late_water_idx is not None:  # the LATE block (comb-field channels; see __init__): same
            lblock: list[Any] = ['<g opacity="0.85">']  # shared-opacity compositing, spliced at ITS OWN
            for w in self.late_water:  # first-call position so the ditch net draws OVER the field's plots
                w["rec"]["bedz"] = self._late_water_idx + len(lblock)
                lblock.append(w["bed"])
            if _pond_late:  # the relocated pond FILL: topmost late bed, covering every joining mouth's overshoot
                pe = self._pond_entry
                assert pe is not None
                pe["rec"]["late"] = True  # the fill now lives in the late block (z pairs: see pond())
                pe["rec"]["bedz"] = self._late_water_idx + len(lblock)
                lblock.append(pe["_bed"])
            lblock.append('</g>')
            lblock.append('<g opacity="0.55">')
            for w in self.late_water:
                if w["sheen"] is not None:
                    w["rec"]["sheenz"] = self._late_water_idx + len(lblock)
                    lblock.append(w["sheen"])
            if _pond_late and self._pond_entry is not None and self._pond_entry["_sheen"] is not None:  # the pond sheen rides above the late beds too
                self._pond_entry["rec"]["sheenz"] = self._late_water_idx + len(lblock)
                lblock.append(self._pond_entry["_sheen"])
            lblock.append('</g>')
            splices.append((self._late_water_idx, lblock))
        for idx, block in sorted(splices, key=lambda s: -s[0]):  # high index first so the lower stays valid
            self.out[idx : idx + 1] = block
        if self.view:  # crop the viewBox to the requested window
            ox, oy, vw, vh = self.view
            self.out[0] = self.out[0].replace(f'viewBox="0 0 {self.W} {self.H}"', f'viewBox="{ox} {oy} {vw} {vh}"')
        body = self.out + self.walls + self.top + self.toplabels + ['</svg>']  # WALLS over lanes; TOP furniture; LABEL text topmost
        with open(basepath + '.svg', 'w') as f:
            f.write('\n'.join(body))
        with open(basepath + '.json', 'w') as f:
            json.dump(self.M, f)
        # Two env knobs make iteration cheap without changing committed output (see SKILL.md
        # 'Render pipeline'; since the resvg switch the raster is ~0.6s even for the biggest map,
        # so these mostly save the render when nothing will look at the PNG):
        #   DIAGRAM_SKIP_RENDER  - skip the raster entirely; the gate reads the JSON, so tests set this and
        #                          never pay to render a PNG no test looks at.
        #   DIAGRAM_PNG_WIDTH=N  - render at N px instead of 2600; unset for the full-res committed PNG.
        if render and not os.environ.get("DIAGRAM_SKIP_RENDER"):
            env_w = os.environ.get("DIAGRAM_PNG_WIDTH")
            self.render_png(basepath, int(env_w) if env_w else png_width)  # keep the .png paired with the .svg
        return len(self.placed)

    def render_png(self: Settlement, basepath: str, width: int = 2600) -> None:  # type: ignore[misc]
        """Rasterize basepath.svg -> basepath.png via resvg.

        Called from finish() so the PNG can never drift from the SVG: there is no way to
        regenerate a map's SVG (by hand or via the test harness, which re-runs every gen)
        without also refreshing its PNG. Settlement maps need ~2600px for the small labels.

        resvg, not rsvg-convert (and deliberately NO fallback - resvg is required, see the
        SKILL.md skill-load install check): profiling Tango (2026-07) showed rsvg-convert
        spent ~16s at 2600px, ~2/3 of it on foliage circles lying entirely outside the
        cropped city viewBox; resvg culls off-view geometry properly and rasterizes the
        same SVG in ~0.6s with visually identical output. Two font requirements for that
        "identical": resvg's generic-family defaults name MS fonts, so 'serif' must be
        mapped to DejaVu Serif explicitly (--serif-family), and resvg does not synthesize
        oblique, so the real italic faces (fonts-dejavu-extra) must be installed or every
        italic label silently renders upright.
        A no-op (with a warning) when resvg is absent - the skill cannot render at all
        without it, so that is a host-setup problem, not a generation bug."""
        exe = shutil.which('resvg')
        if not exe:  # pragma: no cover - depends on the host toolchain, not on any code path
            sys.stderr.write(f'warning: resvg not found (sudo apt-get install -y resvg fonts-dejavu-extra); {basepath}.png not refreshed\n')
            return
        subprocess.run([exe, '--width', str(width), '--serif-family', 'DejaVu Serif', basepath + '.svg', basepath + '.png'], check=True)
