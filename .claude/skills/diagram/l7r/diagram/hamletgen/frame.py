"""STAGE 8: the crossings, the notice board, and the map frame.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import math

from l7r.diagram.settlement import Settlement

from .hinterland import CROP_MARGIN
from .plan import SitePlan

_BOARD_W, _BOARD_H = 14.0, 8.0  # the kosatsuba plank's footprint, as the re-seat probe measures it

# ---- STAGE 8: crossings, the board, and the frame ------------------------------------------------


def stage_crossings(s: Settlement, plan: SitePlan) -> None:
    """Bridges where a way crosses water, and plank footbridges over the long irrigation ditches.

    After every way and every watercourse, because a crossing added later leaves an unbridged one -
    the engine's own `bridges()` docstring says so and the `roads_bridge_water` check enforces it."""
    s.bridges()
    if s.M.get("field_ditches"):
        s.channel_footbridges(spacing=300)


def stage_notice(s: Settlement, plan: SitePlan) -> None:
    """The official notice board, on a lane verge at the busiest node.

    EVERY settlement tier posts the state's standing law, hamlets included - the ofuregaki circulars
    reached the peasantry through this board, read out by the one required-literate person (a
    hamlet's senior farmer, answering to the village headman). `place_kosatsuba` sites it itself,
    deterministically, from the same route records the validator reads.

    It runs BEFORE the ground cover and the woods, not with the framing, because it needs a clear
    verge and it competes for the same ground the scrub scatter and the grove clumps take. Sited
    after them it silently found nowhere to go on one cohort map in six and the gate reported a
    hamlet with no notice board - a failure of ORDER, not of siting."""
    spot = s.place_kosatsuba()
    # ...AND IT MUST STAND WHERE THE FRAME WILL KEEP IT. `place_kosatsuba` maximises passing traffic
    # (dwellings within ~260 px) along the whole way network, and a lane ARM that runs past the
    # cluster still sees the whole cluster from its far end - so on a held-out cohort hamlet the
    # board landed 87 px north of the northernmost farmhouse, on a stretch of lane serving nobody.
    # `crop_to_content` frames the HARD features and deliberately ignores linear runners like lanes,
    # so the board and its caption fell outside the sheet (`labels_within_image`). Adding the board
    # to the crop's hard set was tried and is worse: it then holds the frame open by itself, which is
    # what `crop_not_held_open_by_one_feature` exists to stop. The board belongs among the houses it
    # is read by, so if the engine's traffic score sends it outside them, re-seat it on the nearest
    # verge that is inside the cloud.
    hs = s.M.get("houses", [])
    if spot is not None and hs:
        hx0, hx1 = min(h["x"] for h in hs), max(h["x"] for h in hs)
        hy0, hy1 = min(h["y"] for h in hs), max(h["y"] for h in hs)
        if not (hx0 - 30 <= spot[0] <= hx1 + 30 and hy0 - 30 <= spot[1] <= hy1 + 30):
            board = s.M["kosatsuba"].pop()
            # ...and its CAPTION with it. `kosatsuba` records the board and calls `self.label`, so
            # popping only the board leaves an orphan "notice board" caption sitting where the board
            # used to be - which is the very label the frame could not hold, still failing
            # `labels_within_image` after the board itself had moved.
            for _li in range(len(s.M.get("labels", [])) - 1, -1, -1):
                if len(s.M["labels"][_li]) > 5 and s.M["labels"][_li][5] == "notice board":
                    s.M["labels"].pop(_li)
                    break
            best: tuple[float, float, float, float] | None = None
            for lane in s.M.get("lanes", []):
                if lane.get("connector"):
                    continue
                pts = lane["pts"]
                for i in range(len(pts) - 1):
                    (ax, ay), (bx, by) = pts[i], pts[i + 1]
                    seg = math.hypot(bx - ax, by - ay) or 1.0
                    ux, uy = -(by - ay) / seg, (bx - ax) / seg
                    rot = math.degrees(math.atan2(by - ay, bx - ax))
                    for t in range(int(seg // 12) + 1):
                        mx, my = ax + (bx - ax) * (t * 12 / seg), ay + (by - ay) * (t * 12 / seg)
                        for side in (1.0, -1.0):
                            cx2, cy2 = mx + ux * 16.0 * side, my + uy * 16.0 * side
                            if not (hx0 <= cx2 <= hx1 and hy0 <= cy2 <= hy1):
                                continue
                            if not s._fits(cx2, cy2, _BOARD_W, _BOARD_H, corridors=False):
                                continue
                            # ...AND NOT IN THE WATER. `_fits(corridors=False)` is required here - the
                            # corridor test is a HOUSE setback from the tread and would refuse every
                            # verge - but it also switches off the watercourse clearance bundled into
                            # the same call, so this probe would seat a plank board in a stream.
                            # ONE predicate, shared with `place_kosatsuba`, which had the identical
                            # hole and shipped it on cohort seed 13.
                            if not s.fixture_clear_of_water(cx2, cy2, math.hypot(_BOARD_W, _BOARD_H) / 2):
                                continue
                            busy = sum(1 for h in hs if math.hypot(cx2 - h["x"], cy2 - h["y"]) < 260)
                            if best is None or -busy < best[0]:
                                best = (-busy, cx2, cy2, rot)
            if best is not None:
                s.kosatsuba(best[1], best[2], rot=best[3])
            else:  # pragma: no cover - no verge inside the cloud takes a board; keep the engine's seat rather than none
                s.M["kosatsuba"].append(board)


def stage_frame(s: Settlement, plan: SitePlan) -> None:
    """The crop, then the title.

    In that order: the title searches the FRAMED window for blank space to sit in, so the frame has
    to exist first."""
    # The margin leaves the TITLE somewhere to stand: `title()` scans the framed window for a box
    # that clears every feature and falls back to a corner overlap when the map is too full, which
    # `title_clear_of_features` then fails. But it is bounded above as well as below - `crop_hugs_
    # content` allows at most 56 px of view past the frame-setting content, because a band whose
    # only extra is open ground is wasted image. 64 was tried and fails all twelve. 48 is the most
    # air the frame will give the title.
    s.crop_to_content(margin=CROP_MARGIN)
    s.title(plan.spec.name)
