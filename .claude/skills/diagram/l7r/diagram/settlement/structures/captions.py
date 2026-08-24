"""The primitives a siter uses to ask whether a caption fits, and whether a footprint would land under one.

Split from settlement/structures.py by feature 114 - see settlement/structures/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING

from .._geom import (
    Pt,
    label_aabb,
    seg_dist,
)

if TYPE_CHECKING:
    from ..core import Settlement


class CaptionProbesMixin:
    def label_blockers(self: Settlement, skip_key: str | None = None) -> list[tuple[float, float, float, float]]:  # type: ignore[misc]
        """Every axis-aligned box a caption must miss: any manifest list of dicts carrying w/h, plus
        every caption already placed.

        DERIVED, never hand-listed. This was a list of nine keys and it fell behind exactly the way
        the CAPTION and KEEP-CLEAR registries did before they became registries (CLAUDE.md, "the
        KEEP-CLEAR CONTRACT"): `dye_yards` was never in it, so when a reflow put Minami\'s punishment
        ground beside the dye works the probe reported a clear box and the gate reported a caption on
        a dye works (2026-07-27). A probe that cannot see a feature looks exactly like a probe that
        passes. Nothing here needs to know WHICH lists exist, so a new feature is covered the day it
        is drawn; `skip_key` drops the captioned feature\'s own glyph.

        ROTATION-AWARE, because `labels_clear_of_other_buildings` tests each building\'s AABB and a
        rotated shopfront\'s AABB is much larger than its w/h - probing the unrotated rect passes here
        and still fails the gate."""
        boxes: list[tuple[float, float, float, float]] = []
        for key, recs in self.M.items():
            if key == skip_key or not isinstance(recs, list):
                continue
            for o in recs:
                if not (isinstance(o, dict) and all(isinstance(o.get(f), (int, float)) for f in ("x", "y", "w", "h"))):
                    continue
                a = math.radians(o.get("rot", 0) or 0)
                ca, sa = math.cos(a), math.sin(a)
                hw2, hh2 = o["w"] / 2, o["h"] / 2
                cs = ((-hw2, -hh2), (hw2, -hh2), (hw2, hh2), (-hw2, hh2))
                xs = [o["x"] + dx * ca - dy * sa for dx, dy in cs]
                ys = [o["y"] + dx * sa + dy * ca for dx, dy in cs]
                boxes.append((min(xs), min(ys), max(xs), max(ys)))
        boxes += [label_aabb(lb) for lb in self.M["labels"] if len(lb) > 3]  # AABB: a tilted caption blocks the ground its rotated run can reach
        return boxes

    def label_caption_hw(self: Settlement, label: str, size: float) -> float:  # type: ignore[misc]
        """A caption\'s half-width AS RECORDED. `_record_label` writes len(text) * size * 0.55, and
        that is what `labels_clear_of_other_buildings` tests - so probing the PIL-measured glyph box
        (~2px narrower per side at caption size) is the same class of bug as a hand-written victim
        list: the probe reports clear and the gate reports a collision on the 2px it could not see
        (Minami, 2026-07-27). Placement and its check read the SAME geometry."""
        return len(label) * size * 0.55 / 2

    def label_seat_clear(self: Settlement, lx: float, ly: float, tw: float, size: float = 9.0, boxes: list[tuple[float, float, float, float]] | None = None, tilt: float = 0.0) -> bool:  # type: ignore[misc]
        """Is a caption box centered at (lx, ly) clear of every blocker? `boxes` lets a caller that
        probes many seats build the blocker list once. A TILTED caption probes its rotated AABB -
        conservative against these axis-aligned blockers, so the probe stays at least as strict as
        the quad the gate tests."""
        bx = self.label_blockers() if boxes is None else boxes
        b: tuple[float, float, float, float] = (lx - tw, ly - size * 0.8, lx + tw, ly + size * 0.25)
        if tilt:
            b = label_aabb([*b, 0, "", None, tilt])
        if any(b[0] < x1 and x0 < b[2] and b[1] < y1 and y0 < b[3] for x0, y0, x1, y1 in bx):
            return False
        # ...AND CLEAR OF THE WAYS, which `label_blockers` structurally cannot see.
        #
        # That helper walks the manifest for records carrying x/y/w/h, and a LANE is a polyline of
        # `pts` - so no caption has ever been tested against a lane tread by this probe, while
        # `captions_clear_the_ways_they_stand_on` measures exactly that. The seat probe and the check
        # were asking different questions, which is the defect this project keeps re-finding under
        # different names ("MEASURE WHAT THE RULE MEASURES", dev/gate.md).
        #
        # It went unnoticed because a caption landed on a tread only when the ways ran unusually
        # close to the busiest node; feature 126 derives the lanes from the houses, so they thread
        # the cluster more tightly and it started happening (cohort seeds 34 and 35, both clean at
        # HEAD). The check's own tolerance is the tread half-width plus its 3 px halo plus 2 ft.
        for _ln in self.M.get("lanes", []):
            _pts = _ln.get("pts") or []
            _half = float(_ln.get("w", 5)) / 2 + 3.0 + 2.0
            for _k in range(len(_pts) - 1):
                _a, _b2 = _pts[_k], _pts[_k + 1]
                _cx, _cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                if seg_dist(_cx, _cy, (float(_a[0]), float(_a[1])), (float(_b2[0]), float(_b2[1]))) < _half + max(b[2] - b[0], b[3] - b[1]) / 2:
                    return False
        return True

    def clear_label_seat(self: Settlement, x: float, y: float, w: float, h: float, label: str, size: float = 9.0, skip_key: str | None = None) -> Pt | None:  # type: ignore[misc]
        """A caption seat for a verge-hugging feature: below, above, then left and right, walking
        OUTWARD, first clear box wins; None when nothing is clear.

        A feature that hugs the frontage puts its default below-label ON that frontage - not bad luck
        but what "hugging the frontage" means, and it fired on all three maps that first used this
        probe. SIXTEEN rings, not nine: these features are sited at the BUSIEST node by definition, so
        the ground around them is the most crowded on the map, and nine ran out on Minami - at which
        point the caption fell back to its default seat, on top of three dwellings. A probe that gives
        up silently is worse than no probe, so callers must handle None rather than inherit a seat."""
        tw = self.label_caption_hw(label, size)
        boxes = self.label_blockers(skip_key)
        for ring in range(16):
            d = ring * 14
            for lx, ly in ((x, y + h / 2 + 11 + d), (x, y - h / 2 - 9 - d), (x - tw - w / 2 - 6 - d, y + 3), (x + tw + w / 2 + 6 + d, y + 3)):
                if self.label_seat_clear(lx, ly, tw, size, boxes):
                    return (lx, ly)
        return None

    def _under_a_caption(self: Settlement, x: float, y: float, w: float, h: float, rot: float = 0.0, pad: float = 2.0) -> bool:  # type: ignore[misc]
        """Whether a footprint at (x, y, w, h, rot) would land under a caption ALREADY on the map.

        A label may cover only the thing it labels (`labels_clear_of_other_buildings`), and a
        feature sited LATE can walk under a caption placed early: Minami's punishment ground
        auto-sited onto the burakumin quarter's caption when a reflow moved the busiest traffic
        node 24px north (2026-08-08). The existing probe cannot catch this - it seats the
        feature's OWN caption clear of the buildings, and this is the offense the other way
        round, the feature walking under someone else's caption. Reads `label_aabb`, the same
        geometry the check reads, per the same-source doctrine."""
        hw = (abs(w * math.cos(math.radians(rot))) + abs(h * math.sin(math.radians(rot)))) / 2 + pad
        hh = (abs(w * math.sin(math.radians(rot))) + abs(h * math.cos(math.radians(rot)))) / 2 + pad
        return any(x - hw < a1 and a0 < x + hw and y - hh < b1 and b0 < y + hh for a0, b0, a1, b1 in (label_aabb(L) for L in self.M.get("labels", [])))
