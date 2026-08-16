"""Woods drawn as STANDS of individual trees - the floor early, the canopy deferred to crop time.

Split from settlement/shrines_wells.py by feature 116 - see settlement/shrines_wells/CLAUDE.md for the index.
"""

import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from .._geom import (
    Poly,
    edge_dist,
    point_in_poly,
    seg_dist,
)

if TYPE_CHECKING:
    from ..core import Settlement


class TreeStandsMixin:
    def _tree_stand(self: Settlement, poly: Poly, seed: int, floor: Poly | None = None, outliers: bool = True) -> None:  # type: ignore[misc]
        """Fill `poly` with INDIVIDUAL TREES - the ONE way this engine draws a wood (GM 2026-07-25).

        A forest is NOT a terrain type here. It used to be drawn as a flat pale wash under a widely-
        spaced grid of identical dots, which read as patterned ground rather than as trees, and did
        not match how every other piece of vegetation on these maps is already drawn (the
        yashikirin, the fengshui belt, the dooryard copse - all real crowns, via _draw_grove). So a
        wood is now a STAND: every canopy tree is one drawn crown at true size and true spacing, and
        the polygon survives only as DATA (what it blocks, what it frames, where the brook comes
        from) - never as a shape you can see the outline of.

        DENSITY / SIZE - the why (research 2026-07-25; China-first per the setting's geography note,
        cross-checked against Japanese satoyama hill wood):
          - A closed premodern hill wood - the mixed broadleaf/conifer cover of a settled valley's
            back slope, cut over for fuel and timber on a rotation - carries roughly 500-800 CANOPY
            stems per hectare. 1 ha = 107,639 sq ft, so ~600 stems/ha is one canopy tree per ~180
            sq ft: a mean spacing near 13 ft. That is CANOPY_SPACING_FT.
          - Canopy crowns in such a stand run ~5-8 m across (16-26 ft), with occasional emergents
            wider. CANOPY_R_FT = 8.5 is the mean radius; each crown is jittered 0.75-1.4x, so drawn
            diameters land inside the real band, a few emergents over many smaller crowns.
          - Crowns of ~17 ft mean diameter on 13 ft centers OVERLAP, and that is the point: closure
            is what makes a wood a wood. Same finding as the mulberry rows (see _mulberry_rows) -
            at a to-scale grain the honest drawing of real planted density IS a packed mass of
            crowns, not sparse symbols spaced for the eye.
          - NOTHING is inflated for legibility. At 1 ft/px a crown is r ~6-12 px; at a coarser grain
            it shrinks with the map, exactly like the buildings do.
        The stand's EDGE is made by the trees themselves - there is no boundary stroke and the
        crowns are NOT clipped, so they break the outline the way a real wood does (a clipped stand
        reads as a ruled terrain boundary, which is the exact defect this replaced). `floor` is
        therefore drawn INSET from `poly` - its hard edge has to sit under the canopy - and
        `outliers` scatters a thinning fringe of advance growth on the cut-over margin outside.

        The FLOOR is drawn here; the CROWNS are QUEUED and drawn at crop time (flush_tree_stands),
        the same deferral the stable yards use. A wood is usually drawn EARLY - it is terrain, and
        the settlement is sited against it - but "no crown on a roof" can only be honored against
        buildings that already exist, and half the map is placed after the wood. Deferring the
        canopy alone (the litter floor stays down where it belongs, under everything) lets the
        filter see the COMPLETE map. Labels are unaffected: they live in the topmost layer."""
        # the FLOOR: shaded leaf litter and understory glimpsed between the crowns. Not a terrain
        # wash - under a closed canopy hardly any of it shows, and its outline is buried under the
        # trees whose centers stand inside it.
        d = 'M' + ' L'.join(f'{x:.0f},{y:.0f}' for x, y in (floor or poly)) + ' Z'
        self.add(f'<path d="{d}" fill="{self.FOREST_FLOOR}"/>')
        self._pending_stands.append((list(poly), seed, outliers))

    def flush_tree_stands(self: Settlement) -> None:  # type: ignore[misc]
        """Draw the canopy of every queued tree stand (see _tree_stand). Runs at CROP time, so each
        crown is tested against the COMPLETE map - every building and wellhead, not just the ones
        that happened to precede the wood - and a crown that would cover one is simply not drawn:
        the stand THINS around the structure instead of retreating from it. Deterministic (each
        stand re-seeds its own RNG, state saved/restored), so deferring ripples nothing. Idempotent;
        unit tests call it directly after forest()/forest_patch()."""
        pending = self._pending_stands
        self._pending_stands: list[tuple[Poly, int, bool]] = []
        for poly, seed, outliers in pending:
            self._draw_stand(poly, seed, outliers)

    def _draw_stand(self: Settlement, poly: Poly, seed: int, outliers: bool) -> None:  # type: ignore[misc]
        """One queued stand's canopy: the crowns inside `poly` plus (optionally) its fringe outside,
        each filtered so no tree is drawn on a roof or a wellhead."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        step = self.px(self.CANOPY_SPACING_FT)
        rad = self.px(self.CANOPY_R_FT)
        st = random.getstate()
        random.seed(seed)
        trees: list[tuple[float, float, float, str]] = []
        yy = min(ys)
        while yy <= max(ys) + step:
            xx = min(xs)
            while xx <= max(xs) + step:
                tx = xx + random.uniform(-step * 0.42, step * 0.42)
                ty = yy + random.uniform(-step * 0.42, step * 0.42)
                big = random.random() < 0.18
                kind = "conifer" if random.random() < 0.34 else "broadleaf"
                if point_in_poly(tx, ty, poly):
                    trees.append((tx, ty, rad * (random.uniform(1.05, 1.4) if big else random.uniform(0.75, 1.05)), kind))
                xx += step
            yy += step
        # no crown is drawn on a roof or a wellhead - and by flush time that means EVERY one of them
        reach = rad * 1.4
        krect, kcirc = self._canopy_keepouts((min(xs) - reach, min(ys) - reach, max(xs) + reach, max(ys) + reach))
        self.add(''.join(self._crowns([t for t in trees if not self._crown_covers(t[0], t[1], t[2], krect, kcirc, self.CANOPY_PAD)])))
        if outliers:
            self.add(''.join(self._crowns(self._stand_fringe(poly, step, rad, krect, kcirc))))
        random.setstate(st)

    def _stand_fringe(self: Settlement, poly: Poly, step: float, rad: float, krect: Any, kcirc: Any) -> list[tuple[float, float, float, str]]:  # type: ignore[misc]
        """The cut-over FRINGE of a wood: scattered advance growth thinning out past the tree line,
        kept off every bit of ground already spoken for. Advance growth comes in THICKETS, not as an
        even sprinkle, so a coarse position-seeded mask (~5 crowns across) decides which stretches of
        the margin have seeded at all and which have been kept clear by grazing and fuel-cutting.
        Each fringe tree becomes a block poly, so a later farmstead cannot land on it."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        band = step * 2.6
        out: list[tuple[float, float, float, str]] = []
        yy = min(ys) - band
        while yy <= max(ys) + band:
            xx = min(xs) - band
            while xx <= max(xs) + band:
                tx = xx + random.uniform(-step * 0.55, step * 0.55)
                ty = yy + random.uniform(-step * 0.55, step * 0.55)
                keep = random.random()
                kind = "conifer" if random.random() < 0.3 else "broadleaf"
                r = rad * random.uniform(0.55, 0.95)
                xx += step * 1.15
                if point_in_poly(tx, ty, poly):
                    continue
                gap = edge_dist(tx, ty, poly)
                thicket = 1.0 if self._hjit(round(tx / (step * 5)), round(ty / (step * 5)), 31.0) > 0.42 else 0.12
                if gap > band or keep > thicket * (1 - gap / band) ** 1.4:  # thins out with distance from the wood
                    continue
                if self._fringe_blocked(tx, ty, r) or self._crown_covers(tx, ty, r, krect, kcirc, self.CANOPY_PAD):
                    continue
                out.append((tx, ty, r, kind))
            yy += step * 1.7
        return out

    def _crowns(self: Settlement, trees: Sequence[tuple[float, float, float, str]]) -> list[str]:  # type: ignore[misc]
        """SVG for a set of (x, y, r, kind) canopy crowns, drawn back-to-front so the stand layers
        with depth. One circle per tree (plus a dark apex for a conifer) - the same two-tone crown
        the grove clumps use, so a wood and a windbreak read as the same kind of thing. Records every
        crown it emits (M['tree_crowns'])."""
        out: list[str] = []
        self._record_crowns([(t[0], t[1], t[2]) for t in trees])
        for tx, ty, r, kind in sorted(trees, key=lambda t: t[1]):
            col = "#4A6733" if kind == "conifer" else ("#6E8B43" if (int(tx) + int(ty)) % 2 else "#7C9A4E")
            out.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="{r:.1f}" fill="{col}" stroke="#3C5526" stroke-width="0.7"/>')
            if kind == "conifer":
                out.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="{r * 0.4:.1f}" fill="#364D22" opacity="0.55"/>')
        return out

    def _fringe_blocked(self: Settlement, tx: float, ty: float, r: float) -> bool:  # type: ignore[misc]
        """Whether a fringe tree at (tx, ty) would land on ground already spoken for - anything
        blocking, a field or dry plot, open water, or a way. The wood's margin grows on waste
        ground, never in the crop or on the road."""
        if any(point_in_poly(tx, ty, b) for b in self.block_polys):
            return True
        if any(point_in_poly(tx, ty, f) or edge_dist(tx, ty, f) < r for f in self.field_polys + self.dry_polys):
            return True
        if self._on_watercourse(tx, ty, pad=r):
            return True
        return any(seg_dist(tx, ty, lp[k], lp[k + 1]) < buf + r for lp, buf in self._corridor_buffers() for k in range(len(lp) - 1))

    def forest(self: Settlement, west_edge: Any, label: str = "", label_xy: Any = None) -> None:  # type: ignore[misc]
        """A woodland filling east of an irregular tree-line to the canvas edge, drawn as a stand of
        INDIVIDUAL TREES (see _tree_stand for the density research). Blocks houses. Deterministic
        (RNG saved/restored) so it never perturbs house placement. The TREE LINE is recorded
        separately from the filled polygon because the frame reveals only a shallow band of wood
        past it (crop_to_content) - deeper in it is undifferentiated canopy, i.e. wasted image."""
        pts = list(west_edge) + [(self.W + 12, west_edge[-1][1]), (self.W + 12, west_edge[0][1])]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        # the litter floor is pushed a crown's width BACK from the tree line (the canvas side stays
        # put) so its straight edge lies under the canopy and the trees alone make the wood's edge
        inset = self.px(self.CANOPY_R_FT)
        self._tree_stand(pts, seed=9, floor=[(x + inset, y) for x, y in west_edge] + pts[len(west_edge) :])
        self.block_polys.append(pts)
        self.M["forest"] = [[round(x, 1), round(y, 1)] for x, y in pts]
        self.M["forest_edge"] = [[round(x, 1), round(y, 1)] for x, y in west_edge]
        if label:
            lx, ly = label_xy if label_xy else (min(xs) + (self.W - min(xs)) / 2, (min(ys) + max(ys)) / 2)
            self.label(lx, ly, label, 14, italic=True, weight="bold", color="#22301A")
