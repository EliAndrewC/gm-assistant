"""The traveled ways as they are recorded on a manifest, the gate that bars one, and the
constants a crossing is built to.

'What could someone walk or cart along here' - deliberately not walls, fences or watercourses.
The placer and the check both read these, which is the whole reason they are shared functions
rather than two hand-rolled lists.

Split from settlement/_geom.py by feature 117 - see settlement/_geom/CLAUDE.md for the index.
"""

import math
from typing import Any

from .base import Manifest, Poly
from .primitives import seg_dist

# STANDALONE plank-footbridge geometry, shared by channel_footbridges() (placement) and the
# footbridges_reach_useful_ground check in check_village.py (which duplicates these three values -
# keep them in sync). A dobashi footplank spans an ~8 ft ditch with a short landing each bank; it
# exists so field-workers can cross to the FIELD, so both banks must reach ground worth crossing to.
PLANK_ABUTMENT = 6.0  # deck = local ditch width + this SHORT abutment (GM 2026-07-22: was 15, far too long for a footplank)
PLANK_BANK_REACH = 11.0  # px past the abutment where a bank opens onto the terrain it lands on
LANDING_FT = 10.0  # a CARRIED deck runs this many REAL feet of deck onto dry ground past each
# bank (GM 2026-08-09). Researched: a bridge does not stop at the water's edge - the girder
# bears on an abutment sill set BACK from the channel edge, both because scour (the current
# undercutting the bank) must never reach the bearing and because the seat itself needs
# bearing length - so a modest timber bridge lands ~5-15 ft of deck past the water on each
# side; 10 ft is mid-band. REAL feet (convert by self.ftpx when drawing), unlike
# PLANK_ABUTMENT above, which is px and deliberately short: a dobashi footplank simply rests
# its ends on the bank (GM 2026-07-22), so footplanks do NOT take this landing.
PLANK_VILLAGE_REACH = 55.0  # a bank within this of a dwelling reaches the VILLAGE (a place worth crossing to)


# ---- the traveled ways, and the gate that bars one ------------------------------------------
# A kido is a gate ACROSS A WAY, so what it squares to is the way, not the fence it hangs in (GM
# 2026-07-26). These helpers are the single definition of "a road runs through here", shared by
# s.ward/s.kido (which place the gate) and check_village (which grades it), so placer and checker
# cannot drift - the same discipline as torii_wall_conflicts in walls.py.
LANE_THROUGH_TOL = 12.0  # a lane whose centerline passes within this of a gate seat runs THROUGH the gate (the kido's roofed bar is ~16px long, so a lane this near is one the bar spans)
LANE_CROSSES_MIN_DEG = (
    25.0  # ...and it must actually CROSS the fence rather than run ALONGSIDE it: a street laid parallel to the ward fence never passes through the gate, so it must not be what the gate squares to
)


def lane_runs(M: Manifest) -> list[tuple[Poly, float]]:
    """Every traveled way on the map as (polyline, bed half-width): the major/Imperial roads, the
    town streets, the gravel alleys, and the city ring road. Deliberately NOT walls, fences or
    watercourses - this answers "what could someone walk or cart along here"."""
    runs: list[tuple[Poly, float]] = []
    roads: Any = M.get("roads")
    if not roads and M.get("road"):
        roads = [{"pts": M["road"], "w": M.get("road_width", 26)}]
    for rd in roads or []:
        runs.append(([(float(p[0]), float(p[1])) for p in rd["pts"]], float(rd.get("w", 26)) / 2))
    for st in M.get("town_streets") or []:
        runs.append(([(float(p[0]), float(p[1])) for p in st["pts"]], float(st.get("w", 18)) / 2))
    for al in M.get("alleys") or []:
        runs.append(([(float(p[0]), float(p[1])) for p in al["pts"]], float(al.get("w", 6)) / 2))
    if M.get("ring_road"):
        runs.append(([(float(p[0]), float(p[1])) for p in M["ring_road"]], float(M.get("ring_road_width", 20)) / 2))
    return runs


def way_beds(M: Manifest) -> list[tuple[Poly, float]]:
    """Every DRAWN way BED as (polyline, half-width): `lane_runs` (roads, town streets, alleys, the
    ring road) PLUS the village/hamlet lane network (`lane`, `lanes`), which lane_runs does not carry.

    This is the AVOIDANCE list for a verge-hugging feature - the notice board and the punishment
    ground, which both site themselves on a frontage and both deliberately bypass the lane CORRIDOR
    (a house setback: homesteads must not crowd the tread, while a board that everyone passes is the
    whole institution). Bypassing the corridor must not mean standing in the roadbed, so each siter
    still tests every bed - and it must be EVERY bed, not merely the ones it sampled candidates
    from: a spot offset from street A can land on alley B, and each siter had built its own partial
    list (the board's omitted town_streets and alleys, the punishment ground's omitted alleys and
    the ring road), so a seat clipping an alley was proposed rather than refused and had to be
    hand-sited (Tango, reported by another session 2026-07-27). The gate caught it after the fact -
    the overlap matrix forbids SOLID x WAY - so this closes the PLACEMENT half of the same rule.
    """
    runs = lane_runs(M)
    if M.get("lane"):
        runs.append(([(float(p[0]), float(p[1])) for p in M["lane"]], 4.0))
    for ln in M.get("lanes") or []:
        runs.append(([(float(p[0]), float(p[1])) for p in ln["pts"]], float(ln.get("w", 8)) / 2))
    return runs


def lane_through_gate(M: Manifest, x: float, y: float, fence_deg: float) -> tuple[float, float] | None:
    """The traveled way a ward gate seated at (x, y) BARS, as (tangent degrees, bed half-width), or
    None if the gate stands in open fence with no lane through it. `fence_deg` is the local fence
    tangent, used only to reject a lane running ALONGSIDE the fence (which the gate does not bar).
    The nearest true crossing wins where several lanes are close."""
    best: tuple[float, float, float] | None = None
    for pts, half in lane_runs(M):
        for i in range(len(pts) - 1):
            d = seg_dist(x, y, pts[i], pts[i + 1])
            if d > LANE_THROUGH_TOL:
                continue
            a = math.degrees(math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0]))
            if abs(((a - fence_deg + 90.0) % 180.0) - 90.0) < LANE_CROSSES_MIN_DEG:
                continue  # runs alongside the fence, not through the gate
            if best is None or d < best[0]:
                best = (d, a, half)
    return None if best is None else (best[1], best[2])


def kido_bar_deg(lane_deg: float, fence_deg: float) -> float:
    """The angle a ward gate's roofed bar takes: SQUARE TO THE LANE it bars. Returned as the
    representative nearest the fence direction, so the guard box's ward-interior flank (which s.ward
    resolves against the bar's local +y) keeps the same sense whichever way the fence was drawn."""
    return fence_deg + (((lane_deg + 90.0) - fence_deg + 90.0) % 180.0 - 90.0)


# How far a CARRIED-WAY deck's corner must stand back from the water it spans, in real feet - the
# floor `bridges_span_their_water` applies to anything that is not a standalone footplank. A real
# abutment sill sits back from the channel edge so scour cannot undercut the bearing.
CARRIED_LANDING_FLOOR_FT = 6.0
