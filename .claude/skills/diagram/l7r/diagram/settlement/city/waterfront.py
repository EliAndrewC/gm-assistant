"""Where the city meets navigable water: quay, aqueduct, docks, jetties, the log boom.

Split from settlement/city.py by feature 113 - see settlement/city/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any

from .._geom import (
    Pt,
)

if TYPE_CHECKING:
    from ..core import Settlement


class WaterfrontMixin:
    def quay(self: Settlement, pts: Any, steps: int = 3, width: float | None = None) -> None:  # type: ignore[misc]
        """A REVETTED QUAY FACE - the bank cut back, faced with stone or timber cribbing, with
        STEPPED LANDINGS notched into it at intervals, and mooring posts along the top.

        WHY THIS AND NOT MORE PIERS (GM 2026-08-11, asking whether three piers was the right
        number for six granaries: "is there some sort of dock that is not a boardwalk... I don't
        know how this would have worked"). Research is in research/cities/river-cities.md, and it
        inverts what a modern marina suggests. **A river's level moves by many feet across the
        year**, so a fixed-height deck is at the right height for a few weeks and wrong the rest -
        unreachable in the dry season, awash in the wet. A flight of steps down a faced bank is
        correct at EVERY level, because the barge simply lies against a different tread. That is
        why the stepped quay is the norm on a river and the projecting pier the exception: the
        Chinese matou is characteristically a stone-stepped landing in a faced bank, and the
        Japanese kashi district uses the same arrangement with the steps called gangi. The pier
        exists for REACH, where the bank shelves too gently for a loaded hull to come alongside.

        So the working face is the BANK, continuous along the frontage, and its capacity is
        measured in feet of mooring rather than in piers - which is why three piers serve six
        granaries perfectly well while a wharf drawn WITHOUT its quay face reads as three fingers
        poking into an otherwise natural riverbank.

        `pts` is the bank line, `steps` how many landings are notched into it. Records M['quays']
        and reserves a shallow corridor so nothing packs onto the working face."""
        if width is None:
            width = max(self.px(10), 2.6)
        dd = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        # the faced edge: a stone band, drawn heavier than a path and with a coursing tick every
        # few feet so it reads as revetment rather than as another way
        self.add(f'<path d="{dd}" fill="none" stroke="#8C8377" stroke-width="{width:.1f}" stroke-linejoin="round" stroke-linecap="butt"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#6E6558" stroke-width="{max(0.8, width * 0.18):.1f}" stroke-linejoin="round" stroke-linecap="butt" opacity="0.8"/>')
        segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
        total = sum(lens) or 1.0

        def at(d: float) -> tuple[float, float, float, float]:
            acc = 0.0
            for (a, b), sl in zip(segs, lens, strict=True):
                if sl and acc + sl >= d:
                    f = (d - acc) / sl
                    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (b[0] - a[0]) / sl, (b[1] - a[1]) / sl)
                acc += sl
            a, b = segs[-1]  # pragma: no cover - defensive: every caller below asks for a
            sl = lens[-1] or 1.0  # pragma: no cover   fraction strictly inside the run, so the
            return (b[0], b[1], (b[0] - a[0]) / sl, (b[1] - a[1]) / sl)  # pragma: no cover  loop always matches

        landings = []
        posts = []
        for k in range(max(0, steps)):
            d = total * (k + 0.5) / max(1, steps)
            x, y, tx, ty = at(d)
            nx, ny = -ty, tx  # toward the water; the caller draws the bank with water on this side
            tread = self.px(20)  # a landing wide enough for two porters to pass
            run = self.px(22)
            g = []
            for t in range(4):  # four treads stepping down into the water
                off = width / 2 + run * t / 4.0
                x0, y0 = x + nx * off - tx * tread / 2, y + ny * off - ty * tread / 2
                x1, y1 = x + nx * off + tx * tread / 2, y + ny * off + ty * tread / 2
                g.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="#665D50" stroke-width="{max(1.1, self.px(3)):.1f}" stroke-linecap="butt"/>')
            self.add("".join(g))
            landings.append([round(x, 1), round(y, 1)])
        for k in range(max(2, steps + 2)):  # mooring posts along the top of the face
            x, y, tx, ty = at(total * (k + 0.5) / max(2, steps + 2))
            nx, ny = ty, -tx  # landward side
            px_, py_ = x + nx * (width / 2 + self.px(3)), y + ny * (width / 2 + self.px(3))
            self.add(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="{max(0.9, self.px(2)):.1f}" fill="#5A5044"/>')
            posts.append([round(px_, 1), round(py_, 1)])
        self.M.setdefault("quays", []).append({"pts": [[round(x, 1), round(y, 1)] for x, y in pts], "w": round(width, 2), "landings": landings, "posts": posts})
        self.corridors.append(([(x, y) for x, y in pts], width / 2 + 6))

    def aqueduct(self: Settlement, pts: Any, width: float | None = None) -> None:  # type: ignore[misc]
        """The capital's water-supply channel: intake works on the river, an OPEN cut at grade
        outside the wall, terminating at a city gate - and buried beyond it.

        THE FORM IS SETTLED AND THE NEGATIVE IS EXPLICIT (GM 2026-08-08; research/cities/
        capitals.md, "The aqueduct is open outside the wall and buried inside it"). The East
        Asian vocabulary is Edo's Kanda and Tamagawa josui and Odawara's sosui: a gravity canal
        in a plain earth cut (the Kanda ran 43 km at grade), a buried pipe inside the town, and -
        only where water must CROSS water - a kakehi flume carried over on a bridge (Edo's
        Suidobashi, "aqueduct bridge", is named for one; none is needed where the route crosses
        nothing). NO ARCADED AQUEDUCT EXISTS in either anchor tradition: arches are the one form
        the possibility space excludes, so this glyph draws straight cuts only and takes no
        arcade parameter. Past the gate nothing is drawn - the in-wall conduit is honestly
        buried, and what a resident sees of it is its draw-basins (feature 021's, with the
        wells).

        `pts[0]` is the INTAKE on the river, drawn with the sluice vocabulary (paired head-posts
        and a lifted board) so it reads as engineered water rather than a stray stream. Records
        M['aqueducts'] (a list, with intake and terminus); the shared crossing source
        (bridge_crossed_waters) reads it, so any way crossing the cut demands a deck like any
        other watercourse."""
        if width is None:
            width = max(self.px(10), 3.0)  # a ~10 ft supply cut - far below the 36 ft cargo canal
        dd = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        # the bank lines first, then the water on top: a narrow cut reads from its earthwork
        # edges. GLYPH CONVENTION, not scale (GM 2026-08-09): the true berms of a 10 ft cut
        # would draw ~1 px of pale tan and vanish, so the banks render DARKER and WIDER than
        # life - masonry brown, ~2 px of reveal per side - exactly as a wellhead draws at `vr`
        # over its true `r`. The to-scale rule governs the WATER (the feature); the banks are
        # the glyph's legibility furniture.
        self.add(f'<path d="{dd}" fill="none" stroke="#7A6A48" stroke-width="{width + 4.4:.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="{width:.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
        ia = math.degrees(math.atan2(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0]))
        hp = max(self.px(3), 2.0)  # head-post ~3 ft square
        span = width / 2 + hp + 1
        g = [f'<g transform="translate({pts[0][0]:.1f},{pts[0][1]:.1f}) rotate({ia:.1f})">']
        for sy in (-span, span - hp):
            g.append(f'<rect x="{-hp / 2:.1f}" y="{sy:.1f}" width="{hp:.1f}" height="{hp:.1f}" fill="#6B5A3C"/>')
        g.append(f'<line x1="0" y1="{-span:.1f}" x2="0" y2="{span:.1f}" stroke="#6B5A3C" stroke-width="1.6"/>')
        g.append("</g>")
        self.add("".join(g))
        # the TERMINAL BASIN at the gate end: the settling tank where the open cut ends and the
        # buried in-wall pipe begins (Edo's josui ended in exactly such head-tanks). Without it
        # the cut just stops - or worse, reads as a brook spilling into the moat (GM 2026-08-09).
        tb = max(self.px(16), 5.0)
        ta = math.degrees(math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0]))
        self.add(
            f'<g transform="translate({pts[-1][0]:.1f},{pts[-1][1]:.1f}) rotate({ta:.1f})">'
            f'<rect x="{-tb / 4:.1f}" y="{-tb / 2:.1f}" width="{tb:.1f}" height="{tb:.1f}" rx="1" fill="#9CB4C8" stroke="#6B5A3C" stroke-width="1.4"/>'
            f"</g>"
        )
        self.M.setdefault("aqueducts", []).append(
            {
                "poly": [[round(px_, 1), round(py_, 1)] for px_, py_ in pts],
                "w": round(width, 2),
                "intake": [round(pts[0][0], 1), round(pts[0][1], 1)],
                "to": [round(pts[-1][0], 1), round(pts[-1][1], 1)],
            }
        )
        self.corridors.append(([(px_, py_) for px_, py_ in pts], width / 2 + 10))

    def dock(self: Settlement, cx: float, cy: float, w: float, h: float) -> Pt:  # type: ignore[misc]
        """An in-city DOCK BASIN at the head of the cargo canal - a rectangular cut of open water
        with a stone quay lip, where the barges tie up (the Jiangnan water-city pattern). Records
        M['docks']; blocks placement so the merchant rows leave the quay clear."""
        self._water(
            f'<rect x="{cx - w / 2:.0f}" y="{cy - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="#9CB4C8"/>',
            {},
            sheen=f'<rect x="{cx - w / 2 + 4:.0f}" y="{cy - h / 2 + 4:.0f}" width="{w - 8}" height="{h - 8}" rx="2" fill="#B6CAD8" opacity="0.5"/>',
        )
        self.add(f'<rect x="{cx - w / 2:.0f}" y="{cy - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="none" stroke="#7A6A48" stroke-width="2.2"/>')
        self.M.setdefault("docks", []).append({"x": cx, "y": cy, "w": w, "h": h, "rot": 0})
        self.placed.append((cx, cy, w + 14, h + 14))
        return (cx, cy)

    def jetty(self: Settlement, x: float, y: float, rot: float = 0.0, length: float | None = None) -> int:  # type: ignore[misc]
        """A timber JETTY - a planked finger running out from the riverbank into the water, where
        the river craft moor (the wharf suburb outside a river city's water-side gate). Drawn in
        the TOP layer over the water; records M['jetties']."""
        if length is None:
            length = self.px(60)
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="0" y="-3.2" width="{length:.0f}" height="6.4" fill="#B0905E" stroke="#59431F" stroke-width="1.1"/>')
        for px_ in range(6, int(length), 9):
            g.append(f'<line x1="{px_}" y1="-3" x2="{px_}" y2="3" stroke="#59431F" stroke-width="0.7" opacity="0.6"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("jetties", []).append({"x": round(x, 1), "y": round(y, 1), "rot": round(rot, 1), "len": round(length, 1), "z": z})
        return z

    def log_boom(self: Settlement, x: float, y: float, rot: float = 0.0, length: float | None = None, width: float | None = None, label: str | None = "log boom", label_xy: Pt | None = None) -> int:  # type: ignore[misc]
        """A LOG BOOM - a shore-fast holding pen for rafted timber at a river port whose main trade
        is TIMBER: a cabled chain of floating logs anchored to the bank at both ends, enclosing a
        strip of water packed with raft-mats between the chain and the shore.

        WHY THIS EXISTS (GM 2026-07-26). A timber city drawn with only a lumber yard and jetties gets
        the same river vocabulary as any other river town: the yard says "someone sells wood", not
        "this is a timber river". Logs came DOWN the water loose or rafted and had to be held at the
        mill or yard until they were pulled out, and the holding pen is the boom - the one piece of
        river furniture that is specific to the trade. Minami is where it matters: l7r.md has Fox
        charcoal burners outnumbering farmers and "significantly more" timber going downriver than
        the ~10,000 koku/yr moved by cart, so the boom is not decoration but the largest working
        thing on the city's water.

        WHY IT IS A PEN AGAINST THE BANK, NOT A LINE IN THE STREAM (GM 2026-08-02, "it just looks
        like a bunch of logs in the middle of the river"; the research is in
        research/urban-features.md, "The log boom"). A boom is a floating FENCE - anchored to
        nothing it holds nothing. Attested booms anchor to fixed ground (bank abutments, stone-
        filled cribs, driven piles) and run ALONG a navigated river, the pen between chain and
        shore, with the fairway kept clear by law; only a loose-log CATCH boom on an unnavigated
        reach ever spans the water (the Kiso tsunaba at the gorge mouth), and that is upstream
        lore, not port furniture. And the held stock is MASS - attested pens are measured in
        thousands of logs packed edge to edge - so the pen draws as a near-solid mat of raft
        strips, never scattered sticks.

        Local frame: `length` runs along the bank (local x), the pen is `width` across (local y,
        default ~40 real ft - about a third of a 120 ft channel), and THE BANK LIES ON THE LOCAL
        +y SIDE - orient `rot` so +y faces the shore. The chain draws on the -y (offshore) edge,
        short end-booms close the pen, mooring posts sit at the bank corners and pile clusters at
        the chain. The checks (log_boom_moored_to_the_bank / log_boom_leaves_the_fairway /
        log_boom_serves_the_lumber_yard) derive the pen quad from the recorded x/y/rot/len/pen_w
        under this same convention. Drawn in the TOP layer OVER the water, like a jetty deck - it
        floats, so overlapping the river is the whole point (OVERLAP_CLASS FIXTURE,
        _OVERLAP_EXEMPT). Records M['log_booms']."""
        if length is None:
            length = self.px(330)
        if width is None:
            width = self.px(40)
        hl, hp = length / 2, width / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        # the held stock first, so the chain reads as holding it in: raft-mats packed nearly solid
        # between chain and shore (sparse sticks read as debris - the attested pens hold thousands)
        # each strip is drawn as an OUTLINED log - a dark underlay a hair wider than the lighter
        # log tone over it - so the dark rims and butt gaps resolve into individual timbers to the
        # eye (GM 2026-08-03: the first solid mat read as one brown mass, "hard to pick out
        # individual logs"); runs kept short (~18-36 real ft) for the same reason
        n_rows = max(4, round((width - 3.2) / 2.05) + 1)
        for r in range(n_rows):
            ry = -hp + 1.6 + r * (width - 3.2) / max(1, n_rows - 1)
            pos = -hl + 2.6 + 1.7 * ((r * 7) % 3)
            while pos < hl - 3.6:
                run = 9.0 + 3.0 * math.sin(r * 3.1 + pos * 0.13)
                end = min(pos + run, hl - 2.6)
                tone = "#7A5B33" if (r + int(pos)) % 2 else "#85643B"
                g.append(f'<line x1="{pos:.1f}" y1="{ry:.1f}" x2="{end:.1f}" y2="{ry:.1f}" stroke="#4A3A22" stroke-width="2.0" stroke-linecap="round" opacity="0.9"/>')
                g.append(f'<line x1="{pos + 0.4:.1f}" y1="{ry:.1f}" x2="{end - 0.4:.1f}" y2="{ry:.1f}" stroke="{tone}" stroke-width="1.2" stroke-linecap="round" opacity="0.95"/>')
                pos = end + 1.5

        # the pen fence: logs cabled end to end (stubby round-ended timbers over a cable line),
        # along the offshore edge and closing both short ends back to the bank
        def chain(x0: float, y0: float, x1: float, y1: float) -> None:
            n_seg = max(2, int(math.hypot(x1 - x0, y1 - y0) / 9.0))
            g.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="#4A3A22" stroke-width="0.8" opacity="0.8"/>')
            for i in range(n_seg):
                t0, t1 = (i + 0.06) / n_seg, (i + 0.88) / n_seg
                g.append(
                    f'<line x1="{x0 + (x1 - x0) * t0:.1f}" y1="{y0 + (y1 - y0) * t0:.1f}" x2="{x0 + (x1 - x0) * t1:.1f}" y2="{y0 + (y1 - y0) * t1:.1f}" stroke="#8A6B42" stroke-width="4.2" stroke-linecap="round"/>'
                )
                g.append(
                    f'<line x1="{x0 + (x1 - x0) * t0:.1f}" y1="{y0 + (y1 - y0) * t0:.1f}" x2="{x0 + (x1 - x0) * t1:.1f}" y2="{y0 + (y1 - y0) * t1:.1f}" stroke="#59431F" stroke-width="0.7" opacity="0.55"/>'
                )

        chain(-hl, -hp, hl, -hp)
        chain(-hl, hp, -hl, -hp)
        chain(hl, hp, hl, -hp)
        # anchorage - a floating fence is only as strong as its fixed ground: mooring posts at the
        # bank corners, pile clusters at the chain's corners and mid-run
        for cx_, cy_ in ((-hl, hp), (hl, hp)):
            g.append(f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="1.8" fill="#4A3A22"/>')
        for cx_ in (-hl, 0.0, hl):
            for dx_, dy_ in ((-1.6, 0.0), (1.4, -1.0), (0.6, 1.4)):
                g.append(f'<circle cx="{cx_ + dx_:.1f}" cy="{-hp + dy_:.1f}" r="1.1" fill="#59431F"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        # record TRUE unrotated dims (w = along-bank length, h = pen width) with rot, exactly as a
        # building does - the matrix extractor rotates x/w/h records by `rot` itself, so recording a
        # rotation-FOLDED bounding box here double-rotates into a phantom footprint (that phantom
        # put the pen "on" Minami's lumber yard 42px away, 2026-08-02)
        self.M.setdefault("log_booms", []).append(
            {"x": round(x, 1), "y": round(y, 1), "rot": round(rot, 1), "len": round(length, 1), "pen_w": round(width, 1), "w": round(length, 1), "h": round(width, 1), "z": z}
        )
        if label:
            th = math.radians(rot)
            aabb_h = abs(math.sin(th)) * length + abs(math.cos(th)) * width
            lx, ly = label_xy if label_xy else (x, y + aabb_h / 2 + 12)
            self.label(lx, ly, label, 9, italic=True, color="#5A4326")
        return z
