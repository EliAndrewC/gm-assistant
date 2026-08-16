"""gate() - the registry driver - plus the twin-detector helpers and the CLI main() (feature 024 package split; bodies verbatim)."""

import math
from collections.abc import Sequence
from typing import Any

from .common_01_geometry import Manifest, load
from .common_03_capacity import DEFAULT_MANIFEST, WAIVER_META_CHECKS
from .registry import _SEG_DEPS, GATE_SEGMENTS, META_CHECKS


def gate(M: Manifest, verbose: bool = True, only: set[str] | None = None) -> list[str]:
    """Run every check over a manifest dict M and return the list of FAILED check names.
    verbose prints the PASS/FAIL lines. Pass a synthetic M to unit-test a single check.
    A check named in meta(waivers=...) prints WAIVE and does not enter the failure list; see
    WAIVER_MIN_REASON above for the rules that keep that hatch from rotting."""
    # tolerate sparse synthetic manifests (unit tests build only the keys a check needs)
    M = {**DEFAULT_MANIFEST, **M}
    # pre-2026-08-10 manifests stored ONE stage as a bare dict (and the second stage of a
    # two-stage map clobbered the first - the Shiro Daika review catch); DEFAULT_MANIFEST's
    # placeholder is None. Normalized here so every check and the overlap registry read one shape.
    _ts_norm = M.get("theater_stage")
    M["theater_stage"] = [_ts_norm] if isinstance(_ts_norm, dict) else (_ts_norm or [])
    meta = M.get("meta", {})
    scale = meta.get("scale", "village")
    houses, fields = M["houses"], M["fields"]
    # A CAPITAL IS A CITY PLUS A CASTLE (GM 2026-08-10). Every urban rule used to test
    # `scale == "city"` exactly, so the capital tier - added later - silently skipped 74 of
    # them, the funerary program among them (no cremation ground, no ossuary, no mausoleum on
    # a city of 12,400). URBAN is the "walled town of any size" predicate; the handful of rules
    # that are genuinely about a PROVINCIAL city (its wall budget, its governor's mansion - a
    # capital has a castle and its own budget check) keep testing `scale == "city"`.
    URBAN = scale in ("city", "capital")
    field_by = {f["name"]: f for f in fields}
    Wd, Hd = meta.get("W", 1820), meta.get("H", 1180)
    # the "map edge" is the rendered window: the cropped view if one is set (city maps crop tight
    # to the walls and let the countryside run off), else the full canvas.
    _vw = meta.get("view")
    EX0, EY0, EX1, EY1 = (_vw[0], _vw[1], _vw[0] + _vw[2], _vw[1] + _vw[3]) if _vw else (0, 0, Wd, Hd)
    fails: list[str] = []
    # see WAIVER_MIN_REASON above. _waived records what was actually excused (so a waiver that
    # never fired can be reported as stale); _ran records every check name the gate reached, so a
    # waiver naming a check this map's scale never runs is caught as stale too, not silently kept.
    _waivers: dict[str, Any] = dict(meta.get("waivers") or {})
    _waived: dict[str, Any] = {}
    _ran: set[str] = set()

    def check(name: str, ok: Any, detail: str = "") -> None:
        _ran.add(name)
        if not ok and name in _waivers and name not in WAIVER_META_CHECKS:
            _waived[name] = _waivers[name]
            if verbose:
                print(f"WAIVE {name}  -> waived: {_waivers[name]}")
            return
        if verbose:
            print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))
        if not ok:
            fails.append(name)

    ns: dict[str, Any] = {k: v for k, v in locals().items()}
    if only is None:
        for _seg in GATE_SEGMENTS:
            ns.update(_seg.fn(**{n: ns[n] for n in _seg.free if n in ns}))
        return fails
    bases = set(only)
    known = set().union(*(s.checks for s in GATE_SEGMENTS)) if GATE_SEGMENTS else set()
    unknown = bases - known
    if unknown:
        raise ValueError(f"unknown check name(s): {sorted(unknown)}")
    requested_meta = bases & META_CHECKS
    if requested_meta:
        raise ValueError(f"meta-check(s) cannot run targeted (use a full gate run): {sorted(requested_meta)}")
    wanted = {i for i, s in enumerate(GATE_SEGMENTS) if (bases & set(s.checks)) or s.always}
    frontier = set(wanted)
    while frontier:
        deps = set().union(*(_SEG_DEPS[i] for i in frontier)) - wanted
        wanted |= deps
        frontier = deps
    for i in sorted(wanted):
        _seg = GATE_SEGMENTS[i]
        ns.update(_seg.fn(**{n: ns[n] for n in _seg.free if n in ns}))
    return fails


# ---- Pool-level twin-detector (feature 005) -----------------------------------------------------
# The per-map gate() validates ONE manifest; this is a CROSS-map tool. Two villages that share a water
# direction (down_deg) should still read as different PLACES - the GM's complaint was that Kikuta was a
# near-copy of Hoshigaoka down to the headman's house position. So for every same-down_deg pair we count
# how many of the structural axes a viewer actually reads (SC-001) fall in DIFFERENT coarse buckets, and
# flag the pair when too few differ. Two design choices, both from research.md D6:
#   - Same-down_deg SCOPING: villages that already differ by water direction are trivially distinguishable
#     and are not compared (comparing them would dilute the signal).
#   - COARSE buckets (which side / which type / which octant), never pixel positions, so genuine near-
#     variants are not falsely flagged as twins - the axes answer "different KIND of place?", not "moved a
#     few px?". The 4-of-7 threshold is the tuning target; recorded with its reasoning in settlements.md.
TWIN_AXES = ("cluster_region", "cluster_shape", "headman_side", "lane_skeleton", "water_source", "focal_set", "grain_orient", "settlement_form", "pond_layout")
TWIN_MIN_DIFF = 4  # a same-down_deg pair must differ on >= this many of the 8 axes to read as distinct


def _dir8(dx: float, dy: float, dead: float = 1e-9) -> str | None:
    """Bucket a vector into one of 8 compass labels (N/NE/E/SE/S/SW/W/NW), y DOWN = south. Returns None
    for a ~zero vector (no meaningful direction). Coarse on purpose: a village on the W margin reads the
    same whether it is a few px higher or lower."""
    if dx * dx + dy * dy < dead:
        return None
    ang = math.degrees(math.atan2(dy, dx)) % 360  # 0=E, 90=S (y down), 180=W, 270=N
    return ("E", "SE", "S", "SW", "W", "NW", "N", "NE")[int((ang + 22.5) % 360 // 45)]


def _cluster_centroid(M: Manifest) -> tuple[float, float] | None:
    hs = M.get("houses", [])
    if not hs:
        return None
    return (sum(h["x"] for h in hs) / len(hs), sum(h["y"] for h in hs) / len(hs))


def twin_axes(M: Manifest) -> dict[str, Any]:
    """Extract the coarse structural axes a viewer reads a village by, for twin comparison. Each axis is
    a small hashable label (or None when the map lacks the data); two maps 'differ' on an axis only when
    both are present and their labels are unequal (a missing datum never manufactures a difference)."""
    meta = M.get("meta", {})
    hs = M.get("houses", [])
    cen = _cluster_centroid(M)
    fields = M.get("fields", [])
    fb = fields[0]["bbox"] if fields else None
    fc = ((fb[0] + fb[2]) / 2, (fb[1] + fb[3]) / 2) if fb else None
    ax: dict[str, Any] = {}

    # 1. cluster_region: which side of the field the village sits on (the 背山面水 "background" octant)
    ax["cluster_region"] = _dir8(cen[0] - fc[0], cen[1] - fc[1]) if (cen and fc) else None

    # 2. cluster_shape: the declared knob if present, else the cluster-bbox aspect (round vs elongated + axis)
    if meta.get("cluster_shape"):
        ax["cluster_shape"] = meta["cluster_shape"]
    elif hs:
        xs = [h["x"] for h in hs]
        ys = [h["y"] for h in hs]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        r = w / h if h else 1.0
        ax["cluster_shape"] = "round" if 0.7 <= r <= 1.4 else ("wide" if r > 1.4 else "tall")
    else:
        ax["cluster_shape"] = None

    # 3. headman_side: where the headman compound sits WITHIN the cluster (octant off the centroid, or
    #    'center' when near the middle) - the GM's specific twinning symptom
    headman = next((h for h in hs if h.get("role") == "headman"), None)
    if headman and cen:
        span = 0.0
        if hs:
            span = max(max(h["x"] for h in hs) - min(h["x"] for h in hs), max(h["y"] for h in hs) - min(h["y"] for h in hs))
        d = math.hypot(headman["x"] - cen[0], headman["y"] - cen[1])
        ax["headman_side"] = "center" if d < 0.15 * span else _dir8(headman["x"] - cen[0], headman["y"] - cen[1])
    else:
        ax["headman_side"] = None

    # 4. lane_skeleton: the declared knob (spine / T / Y / cross / waterside); no reliable geometric fallback
    ax["lane_skeleton"] = meta.get("lane_skeleton")

    # 5. water_source: pond octant off the field center (which corner), else the stream entry edge, else None
    pond = M.get("pond")
    if meta.get("water_source_position"):
        ax["water_source"] = meta["water_source_position"]
    elif pond and fc:
        ax["water_source"] = _dir8(pond[0] - fc[0], pond[1] - fc[1])
    else:
        ax["water_source"] = None

    # 6. focal_set: the set of OPTIONAL focal features present (a frozenset so order does not matter)
    ax["focal_set"] = frozenset(meta.get("focal_features", []))

    # 7. grain_orient: median paddy/dry-plot grain angle, bucketed to 15-degree bands (mod 180, a bund has
    #    no head/tail) - the "uniform 45deg" residual becomes a real differentiator once it drifts per map
    thetas = [d["theta"] for d in M.get("dry_plots", []) if "theta" in d]
    if thetas:
        med = sorted(thetas)[len(thetas) // 2]
        ax["grain_orient"] = round((math.degrees(med) % 180) / 15)
    else:
        ax["grain_orient"] = None

    # 8. settlement_form: nucleated blob vs linear ribbon vs dispersed vs water-town - the biggest structural
    #    read of all. Defaults to 'nucleated' (the base form) when a map does not declare it.
    ax["settlement_form"] = meta.get("settlement_form", "nucleated")
    # 9. pond_layout: a POLDER's parcel geometry - the surveyed rectilinear 'grid' (圩田 lower-Yangtze) vs the
    #    accreted, creek-fitted 'mosaic' (桑基魚塘 Pearl-delta dike-pond); `build_polder`'s `mosaic` knob. So two
    #    same-water polders read as different KINDS of place. Defaults to 'grid' (the base surveyed form).
    ax["pond_layout"] = meta.get("pond_layout", "grid")
    return ax


def twin_diff_count(a: dict[str, Any], b: dict[str, Any]) -> int:
    """How many axes two extracted axis-dicts differ on (both present and unequal). A None on either side
    is 'no evidence', not a difference, so a data gap never inflates distinctiveness."""
    n = 0
    for k in TWIN_AXES:
        av, bv = a.get(k), b.get(k)
        if av is None or bv is None:
            continue
        if av != bv:
            n += 1
    return n


def twin_report(manifests: Sequence[Manifest]) -> list[dict[str, Any]]:
    """For every pair of villages that SHARE a water direction, report how many structural axes differ and
    whether the pair reads as distinct. Verdict 'TWINNED' (too similar) when fewer than TWIN_MIN_DIFF axes
    differ, else 'PASS'. Non-village manifests (no down_deg) are skipped. This is a pool-level tool run
    alongside - not inside - the per-map gate()."""
    named = [(str(M.get("meta", {}).get("name", i)), M) for i, M in enumerate(manifests)]
    axes = {name: twin_axes(M) for name, M in named}
    out: list[dict[str, Any]] = []
    for i in range(len(named)):
        for j in range(i + 1, len(named)):
            na, Ma = named[i]
            nb, Mb = named[j]
            da, db = Ma.get("meta", {}).get("down_deg"), Mb.get("meta", {}).get("down_deg")
            if da is None or db is None or da != db:
                continue  # only same-water-direction pairs are compared
            diff = twin_diff_count(axes[na], axes[nb])
            out.append({"pair": (na, nb), "down_deg": da, "diffs": diff, "verdict": "PASS" if diff >= TWIN_MIN_DIFF else "TWINNED"})
    return out


def main(path: str) -> int:
    return 1 if gate(load(path)) else 0
