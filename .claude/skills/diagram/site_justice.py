#!/usr/bin/env python3
"""Propose legal seats for the justice works (feature 015) on an existing Mode B manifest.

    python3 site_justice.py pool/provincial-cities/nagahara.json execution_ground
    python3 site_justice.py pool/towns/hirameki.json boundary_marker --ground 1620,1900

WHY THIS EXISTS. Siting an execution ground by hand costs a regenerate-and-check cycle per guess,
and the constraints interact: outside the wall, on the way out, past the boundary stone, clear of
the community's dead, off the farmland, on the outcast side, clear of every structure, and inside
the map's existing view (a seat beyond it drags the crop out and detaches the road from the edge it
must run off). The first two pool maps cost several cycles each before this existed.

THE ORACLE IS THE REAL GATE, NOT A RESTATEMENT OF IT. The predecessor of this tool was a scratchpad
script that re-implemented each rule as its own predicate, and it drifted within a single session:
a relaxation made for one map silently persisted and put Nagahara's boundary stone in an open field
off the highway, which the gate accepted because the rule it broke was not yet checked. So this
tool never restates a rule. It builds a TRIAL manifest with the feature placed at a candidate spot,
runs `check_village.gate()` on it, and reports the checks that fail there but not on the same map
with that feature absent. New rules are therefore picked up for free, and a rule this tool "knows"
cannot disagree with the rule the gate enforces - the recurring engine trap recorded in the
dev-loop doc ("placement and its check must read the SAME manifest source"), applied to tooling.

The cheap geometric pass below is a RANKING and a coarse sieve, never an authority: it exists only
to keep the number of gate runs small, and it is deliberately permissive, because a candidate it
wrongly admits merely costs a gate run while one it wrongly rejects would hide a legal seat.

KNOWN LIMIT: label collisions cannot be judged from a manifest, because a label box is produced by
the generator at draw time, not recorded for a hypothetical placement. `labels_clear_of_other_
buildings` and `no_label_overlaps` are therefore still found by regenerating. Both `punishment_spot`
and `execution_ground` take `label_above` / `label_xy` for exactly that reason.
"""

import copy
import json
import math
import sys
from typing import Any

import check_village
from settlement import BOUNDARY_MARKER_FT, BOUNDARY_MARKER_MIN_PX, PUNISHMENT_SPOT_FT, crop_boxes, execution_ground_ft

Manifest = dict[str, Any]
Pt = tuple[float, float]

REGISTRY = {"execution_ground": "execution_grounds", "punishment_spot": "punishment_spots", "boundary_marker": "boundary_markers"}


def footprint_px(M: Manifest, kind: str) -> tuple[float, float]:
    """The feature's drawn extent in px on this map - from settlement.py's own figures, so a trial
    placement is exactly the size the engine would draw."""
    ftpx = float(M["meta"].get("ftpx") or 1)
    if kind == "execution_ground":
        w, h = execution_ground_ft("city" if M["meta"].get("scale") == "city" else "town")
        return w / ftpx, h / ftpx
    if kind == "punishment_spot":
        return PUNISHMENT_SPOT_FT[0] / ftpx, PUNISHMENT_SPOT_FT[1] / ftpx
    v = max(BOUNDARY_MARKER_FT / ftpx, BOUNDARY_MARKER_MIN_PX)  # a location marker: the DRAWN box is what collides
    return v, v


def record(M: Manifest, kind: str, x: float, y: float, rot: float = 0.0) -> dict[str, Any]:
    """The manifest record the engine would write for this feature at (x, y)."""
    w, h = footprint_px(M, kind)
    rec: dict[str, Any] = {"x": float(x), "y": float(y), "w": w, "h": h, "rot": rot, "label": kind.replace("_", " ")}
    if kind == "execution_ground":
        rec["screened"] = M["meta"].get("scale") == "city"
    if kind == "boundary_marker":
        rec["vw"], rec["vh"] = w, h
        ftpx = float(M["meta"].get("ftpx") or 1)
        rec["w"] = rec["h"] = BOUNDARY_MARKER_FT / ftpx  # TRUE footprint; vw/vh is what the checks clear
    return rec


def _with(M: Manifest, kind: str, recs: list[dict[str, Any]]) -> Manifest:
    trial = copy.copy(M)  # shallow: only the one registry is replaced, so the rest is shared and cheap
    trial[REGISTRY[kind]] = recs
    return trial


def failures(M: Manifest) -> set[str]:
    return set(check_village.gate(M, verbose=False))


def new_failures(M: Manifest, kind: str, x: float, y: float, base: set[str], rot: float = 0.0) -> set[str]:
    """Checks that fail with the feature seated at (x, y) but do NOT fail with it absent.

    This is the whole adjudication: every rule the gate enforces applies, including ones added long
    after this file was written, and nothing here has to know what any of them are."""
    return failures(_with(M, kind, [record(M, kind, x, y, rot)])) - base


def view_box(M: Manifest) -> tuple[float, float, float, float]:
    """The map's current frame (x0, y0, x1, y1). A seat outside it drags the crop out."""
    v = M["meta"].get("view")
    if v:
        return float(v[0]), float(v[1]), float(v[0] + v[2]), float(v[1] + v[3])
    return 0.0, 0.0, float(M["meta"]["W"]), float(M["meta"]["H"])


def content_box(M: Manifest, kind: str) -> tuple[float, float, float, float]:
    """The frame the REST of the map needs, with this feature absent. Computed once per run, from
    crop_boxes() - the same contributor list the crop itself reads, so it cannot drift from the
    real frame."""
    boxes = crop_boxes(_with(M, kind, []), M["meta"].get("scale") == "city", M["meta"].get("ftpx", 1), M["meta"]["W"], M["meta"]["H"])
    if not boxes:  # pragma: no cover - a manifest with no frame-setting content at all
        return view_box(M)
    return min(b[0] for b in boxes), min(b[2] for b in boxes), max(b[1] for b in boxes), max(b[3] for b in boxes)


def frame_cost(M: Manifest, kind: str, x: float, y: float, box: tuple[float, float, float, float] | None = None) -> float:
    """How far, in px, this seat would push the frame past what the rest of the map already needs.
    Zero means the seat is free: the crop is unchanged by it."""
    w, h = footprint_px(M, kind)
    x0, y0, x1, y1 = box if box is not None else content_box(M, kind)
    return max(0.0, x0 - (x - w / 2), (x + w / 2) - x1, y0 - (y - h / 2), (y + h / 2) - y1)


def routes(M: Manifest) -> list[list[Any]]:
    out = [M["road"]] if M.get("road") else []
    out += [st["pts"] for st in M.get("town_streets", [])]
    out += [ln["pts"] for ln in M.get("lanes", [])]
    return out


def way_out_distance(M: Manifest, x: float, y: float) -> float:
    """Distance to the nearest road or gate. RANKING ONLY - the gate decides legality."""
    ds = [check_village.seg_dist(x, y, r[k], r[k + 1]) for r in routes(M) for k in range(len(r) - 1)]
    ds += [math.hypot(x - g[0], y - g[1]) for g in (M.get("gates") or [])]
    if M.get("gate"):
        ds.append(math.hypot(x - M["gate"][0], y - M["gate"][1]))
    return min(ds) if ds else float("inf")


def outside_the_wall(M: Manifest, x: float, y: float) -> bool:
    wall = M.get("wall") or []
    return len(wall) < 3 or not check_village.point_in_poly(x, y, wall)


def rank_key(M: Manifest, kind: str, p: Pt, box: tuple[float, float, float, float]) -> tuple[float, ...]:
    """Order candidates so legal ones surface early, keeping the number of gate runs small.

    This is a HEURISTIC and may freely resemble the rules - it only orders, it never rejects, so it
    cannot hide a legal seat the way the old scratchpad script's predicates could. Getting it wrong
    costs gate runs, not correctness. The execution ground and its stone belong outside the wall and
    on the way out; the punishment ground belongs inside, on the traffic. Frame cost breaks ties,
    because a seat that leaves the crop alone is strictly better than one that does not."""
    out = outside_the_wall(M, *p)
    wants_out = kind != "punishment_spot"
    w, h = footprint_px(M, kind)
    beside = max(w, h) / 2 + 20.0  # BESIDE the way out, not ON it - minimizing the distance just
    #                                ranks candidates sitting in the carriageway first, which was
    #                                the first thing this ranking got wrong
    return (0.0 if out == wants_out else 1.0, frame_cost(M, kind, *p, box=box), abs(way_out_distance(M, *p) - beside))


def candidates(M: Manifest, kind: str, step: float) -> list[Pt]:
    """A coarse grid over the map's current view. Deliberately permissive - it prunes for SPEED, and
    every survivor is still adjudicated by the gate."""
    x0, y0, x1, y1 = view_box(M)
    w, h = footprint_px(M, kind)
    out: list[Pt] = []
    gy = y0 + h
    while gy <= y1 - h:
        gx = x0 + w
        while gx <= x1 - w:
            out.append((gx, gy))
            gx += step
        gy += step
    return out


def propose(M: Manifest, kind: str, limit: int = 25, step: float = 0.0, rot: float = 0.0) -> list[dict[str, Any]]:
    """Legal seats for `kind`, cheapest-on-the-frame first.

    Ranks candidates by (frame cost, distance to the way out) and adjudicates the best `limit` of
    them against the real gate, returning those that add no new failure."""
    step = step or max(24.0, 40.0 / float(M["meta"].get("ftpx") or 1))
    base = failures(_with(M, kind, []))
    box = content_box(M, kind)
    ranked = sorted(candidates(M, kind, step), key=lambda p: rank_key(M, kind, p, box))
    ok: list[dict[str, Any]] = []
    for x, y in ranked[:limit]:
        if not new_failures(M, kind, x, y, base, rot):
            ok.append({"x": round(x), "y": round(y), "frame_cost": round(frame_cost(M, kind, x, y, box=box)), "way_out": round(way_out_distance(M, x, y))})
    return ok


def report(M: Manifest, kind: str, limit: int, ground: Pt | None, step: float = 0.0) -> str:
    if ground is not None:  # judge a chosen ground first, so a stone is proposed against THAT ground
        M = _with(M, "execution_ground", [record(M, "execution_ground", *ground)])
    lines = [f"{kind}: adjudicating the {limit} best-ranked seats against check_village.gate()"]
    seats = propose(M, kind, limit, step)
    if not seats:
        lines.append("  no legal seat among them - raise --limit, widen --step, or move what is blocking")
    for s in seats:
        lines.append(f"  ({s['x']}, {s['y']})  frame_cost={s['frame_cost']}px  way_out={s['way_out']}px")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        return 2
    opts = {a.split("=", 1)[0]: a.split("=", 1)[1] for a in argv if a.startswith("--") and "=" in a}
    with open(args[0]) as fh:
        M = json.load(fh)
    kind = args[1]
    if kind not in REGISTRY:
        print(f"unknown kind {kind!r} - one of {sorted(REGISTRY)}")
        return 2
    g = opts.get("--ground")
    ground = (float(g.split(",")[0]), float(g.split(",")[1])) if g else None
    print(report(M, kind, int(opts.get("--limit", 25)), ground, float(opts.get("--step", 0))))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main(sys.argv[1:]))
