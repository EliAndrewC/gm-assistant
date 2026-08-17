"""Gate segments (ponds hems and land fall; keys 0438_011-0464) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from .common_01_geometry import Poly, point_in_poly, poly_dist, seg_dist, segments_cross, unit_dir
from .common_02_overlap_policy import in_ellipse
from .common_03_capacity import _UNBOUND, _kept


def _seg_0438_011__nr_lines_1(*, nr_lines: Any = _UNBOUND, road: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.011 (nr_lines) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and road:
        nr_lines.append((road, 60.0))
    return _kept(locals(), ('nr_lines',))


def _seg_0438_012__nr_lines_2(*, M: Any = _UNBOUND, nr_lines: Any = _UNBOUND, scale: Any = _UNBOUND, st_: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.012 (nr_lines, st_) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_lines += [(st_["pts"], st_["w"] / 2 + 40) for st_ in M.get("town_streets", [])]
    return _kept(locals(), ('nr_lines', 'st_'))


def _seg_0438_013__ln_(*, M: Any = _UNBOUND, ln_: Any = _UNBOUND, nr_lines: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.013 (ln_, nr_lines) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_lines += [(ln_["pts"], 30.0) for ln_ in M.get("lanes", [])]
    return _kept(locals(), ('ln_', 'nr_lines'))


def _seg_0438_014__c2_(*, M: Any = _UNBOUND, c2_: Any = _UNBOUND, d_: Any = _UNBOUND, nr_lines: Any = _UNBOUND, s_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.014 (c2_, d_, nr_lines, s_) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_lines += [(s_["poly"], 30.0) for s_ in M.get("streams", [])] + [(c2_["poly"], 24.0) for c2_ in M.get("channels", [])] + [(d_["poly"], 20.0) for d_ in M.get("field_ditches", [])]
    return _kept(locals(), ('c2_', 'd_', 'nr_lines', 's_'))


def _seg_0438_015__nr_moat(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.015 (nr_moat) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_moat = M.get("moat")
    return _kept(locals(), ('nr_moat',))


def _seg_0438_016__nr_lines_3(*, M: Any = _UNBOUND, nr_lines: Any = _UNBOUND, nr_moat: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.016 (nr_lines) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and nr_moat:
        nr_lines.append((nr_moat, M.get("moat_width", 22) / 2 + 8))
    return _kept(locals(), ('nr_lines',))


def _seg_0438_017__nr_wall(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.017 (nr_wall) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_wall = M.get("wall")
    return _kept(locals(), ('nr_wall',))


def _seg_0438_018__nr_hill(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.018 (nr_hill) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_hill = M.get("hill")
    return _kept(locals(), ('nr_hill',))


def _seg_0438_019__nr_pond(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.019 (nr_pond) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_pond = M.get("pond")
    return _kept(locals(), ('nr_pond',))


# NEAR-RING BAND CAP (2026-07-23): on a WALLED CITY the near ring is the ground within ~800 real ft
# of the rampart (a few minutes' walk out the gates - wide enough to take in the moat-fed fans' plot mass, since the first ~500 ft is structurally moat + farmstead rings + gate suburbs) - NOT
# everything the frame happens to show. The thresholds were calibrated on a tight crop whose visible
# extramural WAS that band ("the countryside proper runs off-frame" above); when the frame widened to
# show the comb deltas as countryside (GM 2026-07-23, Tango), an uncapped sampler silently redefined
# "near ring" as "all visible countryside" and diluted the fraction with ground the check was never
# meant to judge. Capping by real distance keeps the check meaning the same at ANY frame size.
# Towns (no wall) keep their tight frames; unchanged there.


def _seg_0438_020__nr_band(*, URBAN: Any = _UNBOUND, meta: Any = _UNBOUND, nr_wall: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.020 (nr_band) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_band = (800.0 / (meta.get("ftpx") or 1)) if (URBAN and nr_wall is not None and len(nr_wall) >= 3) else None
    return _kept(locals(), ('nr_band',))


# SAMPLING WINDOW: for a walled city the band is sampled in CANVAS space (the wall bbox expanded
# by the band), NOT the view - the manifest records full-canvas geometry, so the near ring exists
# whether or not the crop shows it, and the metric must not shift when the frame is tightened
# (caught 2026-07-23: the aggressive Nagahara crop clipped band cells and dropped the fraction
# below the floor with not one field changed). Towns keep the view window (no wall, no band).


def _seg_0438_021__SX0(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    Hd: Any = _UNBOUND,
    Wd: Any = _UNBOUND,
    _wxs: Any = _UNBOUND,
    _wys: Any = _UNBOUND,
    nr_band: Any = _UNBOUND,
    nr_wall: Any = _UNBOUND,
    p_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0438.021 (SX0, SX1, SY0, SY1) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        if nr_band is not None and nr_wall is not None:
            _wxs = [p_[0] for p_ in nr_wall]
            _wys = [p_[1] for p_ in nr_wall]
            SX0, SY0 = max(0.0, min(_wxs) - nr_band - 25), max(0.0, min(_wys) - nr_band - 25)
            SX1, SY1 = min(float(Wd), max(_wxs) + nr_band + 25), min(float(Hd), max(_wys) + nr_band + 25)
        else:
            SX0, SY0, SX1, SY1 = EX0, EY0, EX1, EY1
    return _kept(locals(), ('SX0', 'SX1', 'SY0', 'SY1', '_wxs', '_wys', 'p_'))


def _seg_0438_022__nr_cultc(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.022 (nr_cultc, nr_elig) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_elig = nr_cultc = 0
    return _kept(locals(), ('nr_cultc', 'nr_elig'))


def _seg_0438_023__gy(*, SY0: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.023 (gy) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        gy = SY0 + 12.5
    return _kept(locals(), ('gy',))


def _seg_0438_024__bx0(
    *,
    SX0: Any = _UNBOUND,
    SX1: Any = _UNBOUND,
    SY1: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    committed: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    hw_: Any = _UNBOUND,
    i_: Any = _UNBOUND,
    nr_band: Any = _UNBOUND,
    nr_boxes: Any = _UNBOUND,
    nr_cult: Any = _UNBOUND,
    nr_cultc: Any = _UNBOUND,
    nr_elig: Any = _UNBOUND,
    nr_hill: Any = _UNBOUND,
    nr_lines: Any = _UNBOUND,
    nr_pond: Any = _UNBOUND,
    nr_skip: Any = _UNBOUND,
    nr_wall: Any = _UNBOUND,
    p_: Any = _UNBOUND,
    pl_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0438.024 (bx0, bx1, by0, by1) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        while gy < SY1:
            gx = SX0 + 12.5
            while gx < SX1:
                # a cell inside the rampart of a walled town/city is URBAN FLOOR, not near-ring farmland
                # (same reading as town_margins_clothed's inside-the-rampart exemption) - the near ring is
                # the EXTRAMURAL flat ground; the intramural chrysanthemum field / open squares are the town
                committed = (
                    (nr_wall is not None and len(nr_wall) >= 3 and point_in_poly(gx, gy, nr_wall))
                    or (nr_band is not None and nr_wall is not None and poly_dist(gx, gy, nr_wall) > nr_band)  # beyond the near ring: countryside, not judged here
                    or (nr_hill is not None and in_ellipse(gx, gy, nr_hill, 1.45))
                    or (nr_pond is not None and in_ellipse(gx, gy, [nr_pond[0], nr_pond[1], nr_pond[2] + 20, nr_pond[3] + 20]))
                    or any(bx0 <= gx <= bx1 and by0 <= gy <= by1 for bx0, by0, bx1, by1 in nr_boxes)
                    or any(any(seg_dist(gx, gy, pl_[i_], pl_[i_ + 1]) < hw_ for i_ in range(len(pl_) - 1)) for pl_, hw_ in nr_lines)
                    or any(point_in_poly(gx, gy, p_) for p_ in nr_skip)
                )
                if committed:
                    gx += 25
                    continue
                nr_elig += 1
                if any(point_in_poly(gx, gy, p_) for p_ in nr_cult):
                    nr_cultc += 1
                gx += 25
            gy += 25
    return _kept(locals(), ('bx0', 'bx1', 'by0', 'by1', 'committed', 'gx', 'gy', 'hw_', 'i_', 'nr_cultc', 'nr_elig', 'p_', 'pl_'))


def _seg_0438_025__nr_frac(*, nr_cultc: Any = _UNBOUND, nr_elig: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.025 (nr_frac) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nr_frac = nr_cultc / nr_elig if nr_elig else 1.0
    return _kept(locals(), ('nr_frac',))


def _seg_0438_026__near_ring_cultivated_fraction(*, check: Any = _UNBOUND, nr_frac: Any = _UNBOUND, nr_thr: Any = _UNBOUND, nrd_tier: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.026 (near_ring_cultivated_fraction) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        check(
            "near_ring_cultivated_fraction",
            nr_frac >= nr_thr,
            f"only {nr_frac:.0%} of the flat near-ring ground is cultivated (below the {nr_thr:.0%} floor for near_ring_density='{nrd_tier}') - "
            "a well-sited town/city sits in packed farmland: fill the flat clear ground with s.near_ring_cropland(...) "
            "(dry/garden cropland needs no water source) and keep scrub commons to the frame margins; or, for a genuinely "
            "dry/marginal locale, declare meta(near_ring_density='medium'|'thin')",
        )
    return _kept(locals(), ())


# NEAR-RING PADDY DOMINANCE (feature 014). Feature 013 packed the near ring but filled it with
# DRY grain (dry cropland needs no plumbed water, the cheap fill) - historically backwards: a town
# sits in the fertile basin BECAUSE of the wet rice, so its flat waterable near ring is PADDY-
# dominant. Dry grain is the SECONDARY use on the drier/higher margins; vegetable/market gardens
# (crop=="garden") hug the town. This reuses the exact 25px near-ring band + `committed` mask above
# and tallies PADDY-covered cells vs DRY-GRAIN-covered cells (dry_plots whose crop != garden;
# gardens are the legitimate near-town dry use, not the thing demoted), requiring paddy to DOMINATE
# - scaled by tier so a dialed-down map is paddy-LED but sparser, never dry-dominant. REJECTED (per
# Constitution XII, recorded so it is never reinvented): the dry-grain-dominant near ring 013 shipped;
# the flat waterable valley floor of a wet-rice county seat is paddy, not dryland grain. Grounded in
# settlements.md "Near-ring farmland density" + budgets.md (the ~1/3-paddy figure is a DOMAIN-wide
# average over hills+margins - the near ring is the most waterable flat ground, so paddy-heavy).
# WHY the ratios: a dense well-sited basin reads clearly paddy-led (paddy >= 1.2x dry-grain); a thin
# grazing/relay locale need only keep paddy at least TYING dry-grain (paddy >= dry-grain), so the
# honest lower-tier answer (a thinner ring where little water reaches) is not forced to dense.
# NOTE: what counts as dry-grain EXCLUDES a paddy comb's own dry hem (below), so a moated city whose
# extramural is an open GLACIS - moat-fed paddy + a thin garden fringe, the rest kept clear for defense
# (Tango) - passes as long as its paddy out-covers the FREE-STANDING dry grain (of which a glacis has
# little). That is the honest read: the immediate glacis is not packed dry farmland.


def _seg_0438_027__NRPD_RATIO(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.027 (NRPD_RATIO) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        NRPD_RATIO = {"dense": 1.2, "medium": 1.1, "thin": 1.0}
    return _kept(locals(), ('NRPD_RATIO',))


def _seg_0438_028__nrpd_ratio(*, NRPD_RATIO: Any = _UNBOUND, nrd_tier: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.028 (nrpd_ratio) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrpd_ratio = NRPD_RATIO.get(nrd_tier, NRPD_RATIO["dense"])
    return _kept(locals(), ('nrpd_ratio',))


def _seg_0438_029__f__1(*, M: Any = _UNBOUND, f_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.029 (f_, nrp_paddy) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrp_paddy = [f_["outline"] for f_ in M.get("fields", []) if f_.get("kind") == "paddy"]
    return _kept(locals(), ('f_', 'nrp_paddy'))


# a paddy comb's own DRY HEM (the barley/soy upslope margin of the flooded field) is part of the
# paddy system, not a competing dry-grain crop - exclude any dry plot sitting within OR HUGGING a
# paddy field's envelope, so only FREE-STANDING dryland grain (the 013 blanket) counts against
# paddy dominance. The hem quilt RINGS the envelope - at the head/flanks it sits OUTSIDE the
# recorded bbox by up to the dry_band (~88px city / ~132px village), so the test expands the bbox
# by that band; a bare in-bbox test miscounted every comb's head hem as free-standing grain
# (caught 2026-07-23 when the near ring became combs-only and the "dry grain" was all hems).


def _seg_0438_030___HEM(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.030 (_HEM) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        _HEM = 135.0
    return _kept(locals(), ('_HEM',))


def _seg_0438_031__f__2(*, M: Any = _UNBOUND, f_: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.031 (f_, nrp_pbbox) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrp_pbbox = [f_["bbox"] for f_ in M.get("fields", []) if f_.get("kind") == "paddy" and f_.get("bbox")]
    return _kept(locals(), ('f_', 'nrp_pbbox'))


def _seg_0438_032__nrp_drygrain(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.032 (nrp_drygrain) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrp_drygrain = []  # type: ignore[var-annotated]
    return _kept(locals(), ('nrp_drygrain',))


def _seg_0438_033__bx0_(
    *,
    M: Any = _UNBOUND,
    _HEM: Any = _UNBOUND,
    bx0_: Any = _UNBOUND,
    bx1_: Any = _UNBOUND,
    by0_: Any = _UNBOUND,
    by1_: Any = _UNBOUND,
    dcx_: Any = _UNBOUND,
    dcy_: Any = _UNBOUND,
    nrp_drygrain: Any = _UNBOUND,
    nrp_pbbox: Any = _UNBOUND,
    o_: Any = _UNBOUND,
    p_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    v_: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0438.033 (bx0_, bx1_, by0_, by1_) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        for o_ in M.get("dry_plots", []) or []:
            p_ = o_.get("poly") if isinstance(o_, dict) else o_
            if p_ is not None and len(p_) >= 3 and (not isinstance(o_, dict) or o_.get("crop") != "garden"):
                dcx_ = sum(v_[0] for v_ in p_) / len(p_)
                dcy_ = sum(v_[1] for v_ in p_) / len(p_)
                if not any(bx0_ - _HEM <= dcx_ <= bx1_ + _HEM and by0_ - _HEM <= dcy_ <= by1_ + _HEM for bx0_, by0_, bx1_, by1_ in nrp_pbbox):
                    nrp_drygrain.append(p_)
    return _kept(locals(), ('bx0_', 'bx1_', 'by0_', 'by1_', 'dcx_', 'dcy_', 'nrp_drygrain', 'o_', 'p_', 'v_'))


def _seg_0438_034__nrp_dc(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.034 (nrp_dc, nrp_pc) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        nrp_pc = nrp_dc = 0
    return _kept(locals(), ('nrp_dc', 'nrp_pc'))


def _seg_0438_035__gy_1(*, SY0: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0438.035 (gy) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        gy = SY0 + 12.5  # the same canvas-space band window as the fraction sampler above
    return _kept(locals(), ('gy',))


def _seg_0438_036__bx0_1(
    *,
    SX0: Any = _UNBOUND,
    SX1: Any = _UNBOUND,
    SY1: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    committed: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    hw_: Any = _UNBOUND,
    i_: Any = _UNBOUND,
    nr_band: Any = _UNBOUND,
    nr_boxes: Any = _UNBOUND,
    nr_hill: Any = _UNBOUND,
    nr_lines: Any = _UNBOUND,
    nr_pond: Any = _UNBOUND,
    nr_skip: Any = _UNBOUND,
    nr_wall: Any = _UNBOUND,
    nrp_dc: Any = _UNBOUND,
    nrp_drygrain: Any = _UNBOUND,
    nrp_paddy: Any = _UNBOUND,
    nrp_pc: Any = _UNBOUND,
    p_: Any = _UNBOUND,
    pl_: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0438.036 (bx0, bx1, by0, by1) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        while gy < SY1:
            gx = SX0 + 12.5
            while gx < SX1:
                committed = (
                    (nr_wall is not None and len(nr_wall) >= 3 and point_in_poly(gx, gy, nr_wall))
                    or (nr_band is not None and nr_wall is not None and poly_dist(gx, gy, nr_wall) > nr_band)  # beyond the near ring: countryside (same cap as the fraction sampler above)
                    or (nr_hill is not None and in_ellipse(gx, gy, nr_hill, 1.45))
                    or (nr_pond is not None and in_ellipse(gx, gy, [nr_pond[0], nr_pond[1], nr_pond[2] + 20, nr_pond[3] + 20]))
                    or any(bx0 <= gx <= bx1 and by0 <= gy <= by1 for bx0, by0, bx1, by1 in nr_boxes)
                    or any(any(seg_dist(gx, gy, pl_[i_], pl_[i_ + 1]) < hw_ for i_ in range(len(pl_) - 1)) for pl_, hw_ in nr_lines)
                    or any(point_in_poly(gx, gy, p_) for p_ in nr_skip)
                )
                if not committed and any(point_in_poly(gx, gy, p_) for p_ in nrp_paddy):
                    nrp_pc += 1
                elif any(point_in_poly(gx, gy, p_) for p_ in nrp_drygrain):
                    nrp_dc += 1
                gx += 25
            gy += 25
    return _kept(locals(), ('bx0', 'bx1', 'by0', 'by1', 'committed', 'gx', 'gy', 'hw_', 'i_', 'nrp_dc', 'nrp_pc', 'p_', 'pl_'))


def _seg_0438_037__near_ring_paddy_dominant(
    *, check: Any = _UNBOUND, nrd_tier: Any = _UNBOUND, nrp_dc: Any = _UNBOUND, nrp_pc: Any = _UNBOUND, nrpd_ratio: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0438.037 (near_ring_paddy_dominant) - body verbatim from _seg_0438__near_ring_cultivated_fraction (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        check(
            "near_ring_paddy_dominant",
            nrp_pc >= nrpd_ratio * nrp_dc,
            f"near-ring paddy does not dominate: {nrp_pc} paddy cells vs {nrp_dc} dry-grain cells "
            f"(need paddy >= {nrpd_ratio:g}x dry-grain for near_ring_density='{nrd_tier}') - a wet-rice county seat's "
            "flat near ring is PADDY, not dryland grain: add near-ring paddy where water reaches (s.near_ring_paddy(...), "
            "or enlarge the combs), demote the dry grain to the drier/higher margins + a garden band by the town, or - "
            "where the near ring genuinely lacks water - draw it at a lower near_ring_density tier",
        )
    return _kept(locals(), ())


# NO CANOPY STANDS OVER OPEN WATER (GM audit 2026-07): a village-grove clump drawn across a
# stream / channel / moat reads as trees growing in the current. The fengshui-pond rule
# (trees_clear_of_fengshui_ponds) covered only ponds; this closes the running-water half.
# village_grove now skips watercourse corridors at draw time; this is the ratchet.


def _seg_0439__wet_canopy() -> dict[str, Any]:
    """Gate segment 439 (wet_canopy) - body verbatim from the legacy gate() (feature 022)."""
    wet_canopy = []  # type: ignore[var-annotated]
    return _kept(locals(), ('wet_canopy',))


def _seg_0440__canopy_lines(*, M: Any = _UNBOUND, st_c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 440 (canopy_lines, st_c) - body verbatim from the legacy gate() (feature 022)."""
    canopy_lines = [(st_c["poly"], st_c.get("w", 9) / 2) for st_c in M.get("streams", [])]
    return _kept(locals(), ('canopy_lines', 'st_c'))


def _seg_0441__canopy_lines_1(*, M: Any = _UNBOUND, canopy_lines: Any = _UNBOUND, cc_c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 441 (canopy_lines, cc_c) - body verbatim from the legacy gate() (feature 022)."""
    canopy_lines += [(cc_c["poly"], cc_c.get("w", 2.5) / 2) for cc_c in M.get("channels", [])]
    return _kept(locals(), ('canopy_lines', 'cc_c'))


def _seg_0442__canopy_lines_2(*, M: Any = _UNBOUND, canopy_lines: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 442 (canopy_lines) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("moat"):
        canopy_lines.append((M["moat"], M.get("moat_width", 22) / 2))
    return _kept(locals(), ('canopy_lines',))


def _seg_0443__cl_c(
    *, M: Any = _UNBOUND, canopy_lines: Any = _UNBOUND, cl_c: Any = _UNBOUND, k: Any = _UNBOUND, vg_c: Any = _UNBOUND, wet_canopy: Any = _UNBOUND, whw: Any = _UNBOUND, wl: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 443 (cl_c, k, vg_c, wet_canopy) - body verbatim from the legacy gate() (feature 022)."""
    for vg_c in M.get("village_groves", []):
        for cl_c in vg_c.get("clumps", []):
            if any(min(seg_dist(cl_c[0], cl_c[1], wl[k], wl[k + 1]) for k in range(len(wl) - 1)) < whw + 6 for wl, whw in canopy_lines):
                wet_canopy.append((round(cl_c[0]), round(cl_c[1])))
    return _kept(locals(), ('cl_c', 'k', 'vg_c', 'wet_canopy', 'whw', 'wl'))


def _seg_0444__canopy_clear_of_watercourses(*, check: Any = _UNBOUND, wet_canopy: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 444 (canopy_clear_of_watercourses) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "canopy_clear_of_watercourses",
        not wet_canopy,
        f"grove canopy clump(s) stand over open water at {sorted(set(wet_canopy))[:4]} - trees do not grow in a stream, channel, or moat; keep the belt polys (and the clump filter) clear of every watercourse",
    )
    return _kept(locals(), ())


def _seg_0445__watercourse_ends_reach_water(*, check: Any = _UNBOUND, dry_drains: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 445 (watercourse_ends_reach_water) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "watercourse_ends_reach_water",
        not dry_drains,
        f"canal/collector end(s) dangle in bare ground at {sorted(set(dry_drains))[:4]} - an on-map main or drain end outside the crop must JOIN a watercourse (a culvert, the stream, another ditch, the moat) or run off the frame; water never just stops",
    )
    return _kept(locals(), ())


def _seg_0446__channels_join_streams_at_confluence(*, check: Any = _UNBOUND, dry_mouths: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 446 (channels_join_streams_at_confluence) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "channels_join_streams_at_confluence",
        not dry_mouths,
        f"channel mouth(s) declared frm/to={{stream}} stop short of the bed at {sorted(set(dry_mouths))[:4]} - "
        f"an intake or drain culvert joins its stream at a CONFLUENCE (the mouth reaches into the water, like a "
        f"road junction), never dying in the grass beside the bank; snap the recorded polyline to the stream centerline",
    )
    return _kept(locals(), ())


# no field overlaps the town wall: a field may ABUT the wall but must stay on one
# side of it (the chrysanthemum field inside the walls touches but never crosses)


def _seg_0447__wall_1(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 447 (wall) - body verbatim from the legacy gate() (feature 022)."""
    wall = M.get("wall")
    return _kept(locals(), ('wall',))


def _seg_0448__fields_clear_of_wall(
    *,
    M: Any = _UNBOUND,
    bad_fw: Any = _UNBOUND,
    check: Any = _UNBOUND,
    e: Any = _UNBOUND,
    f: Any = _UNBOUND,
    ff: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    i: Any = _UNBOUND,
    k: Any = _UNBOUND,
    n: Any = _UNBOUND,
    nm: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    wall: Any = _UNBOUND,
    walled_fields: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 448 (fields_clear_of_wall) - body verbatim from the legacy gate() (feature 022)."""
    if wall:
        walled_fields = [(f["name"], f["outline"]) for f in fields] + [(f"flower[{i}]", ff["outline"]) for i, ff in enumerate(M.get("flower_fields", []))]
        bad_fw = []
        for nm, ol in walled_fields:
            n = len(ol)
            if any(segments_cross(wall[k], wall[k + 1], ol[e], ol[(e + 1) % n]) for k in range(len(wall) - 1) for e in range(n)) or any(point_in_poly(wx, wy, ol) for wx, wy in wall):
                bad_fw.append(nm)
        check("fields_clear_of_wall", not bad_fw, f"field(s) overlap the wall: {sorted(set(bad_fw))}")
    return _kept(locals(), ('bad_fw', 'e', 'f', 'ff', 'i', 'k', 'n', 'nm', 'ol', 'walled_fields', 'wx', 'wy'))


# EVERY fully-on-map paddy field must SHOW a source of water: a channel feeding it, or
# the field directly abutting a stream or pond (its bank at the water). A field merely
# NEAR water without a visible connection does not count. Fields that run off the map
# edge are exempt (their water source may be off-map too).


def _seg_0449__channels(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 449 (channels) - body verbatim from the legacy gate() (feature 022)."""
    channels = M.get("channels", [])
    return _kept(locals(), ('channels',))


def _seg_0450__streams_m(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 450 (streams_m) - body verbatim from the legacy gate() (feature 022)."""
    streams_m = M.get("streams", [])
    return _kept(locals(), ('streams_m',))


def _seg_0451__watered(
    *,
    c: Any = _UNBOUND,
    channels: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    sp: Any = _UNBOUND,
    st: Any = _UNBOUND,
    streams_m: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 451 (watered) - body verbatim from the legacy gate() (feature 022)."""

    def watered(ol: Poly) -> bool:
        if any(point_in_poly(c["poly"][-1][0], c["poly"][-1][1], ol) for c in channels):
            return True  # a channel ends inside it
        if any(
            seg_dist(px, py, sp[k], sp[k + 1]) < 18  # the field bank abuts a stream
            for st in streams_m
            for sp in [st["poly"]]
            for px, py in ol
            for k in range(len(sp) - 1)
        ):
            return True
        return bool(pond and any(in_ellipse(px, py, pond, 1.10) for px, py in ol))  # ...or the pond

    return _kept(locals(), ('watered',))


def _seg_0452__dry(*, f: Any = _UNBOUND, fields: Any = _UNBOUND, runs_off_edge: Any = _UNBOUND, watered: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 452 (dry, f) - body verbatim from the legacy gate() (feature 022)."""
    dry = [f["name"] for f in fields if f["kind"] == "paddy" and not runs_off_edge(f["outline"]) and not watered(f["outline"])]
    return _kept(locals(), ('dry', 'f'))


def _seg_0453__fields_show_water_source(*, check: Any = _UNBOUND, dry: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 453 (fields_show_water_source) - body verbatim from the legacy gate() (feature 022)."""
    check("fields_show_water_source", not dry, f"on-map field(s) with no visible water source (channel or abutting stream/pond): {sorted(set(dry))}")
    return _kept(locals(), ())


# water flows DOWNHILL. If the map declares its slope (meta(downhill=<dir>)), every
# channel must run with it: the source (tap on the stream/pond, poly[0]) sits uphill of
# where it feeds the field (poly[-1]). A channel angled the other way would carry the
# stream's water away from the field, not into it. <dir> is a cardinal name or [dx,dy]
# vector in map coords (+y = south). Maps without the tag are exempt (slope unknown).
# ONE DIRECTION MODEL, NOT THREE (GM 2026-07-25). These two were gated on the LEGACY
# meta(downhill) - a cardinal name or vector - which only 2 of 17 maps ever declared, so 15 maps
# (both provincial cities among them) skipped them entirely behind a green gate: the same
# silent-skip that hid the drainage-slope rules. The fall now comes from `downhill` where a map
# declares it, else meta(down_deg), and per-channel from the TARGET FIELD's own fall when it has
# one - a settlement ringed by farmland drains several ways at once, so the field a channel feeds
# is the right authority for whether that channel runs downhill into it.


def _seg_0454__downhill(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 454 (downhill) - body verbatim from the legacy gate() (feature 022)."""
    downhill = meta.get("downhill")
    return _kept(locals(), ('downhill',))


def _seg_0455___dh_dd(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 455 (_dh_dd) - body verbatim from the legacy gate() (feature 022)."""
    _dh_dd = meta.get("down_deg")
    return _kept(locals(), ('_dh_dd',))


def _seg_0456___dh_fields(*, M: Any = _UNBOUND, f: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 456 (_dh_fields, f) - body verbatim from the legacy gate() (feature 022)."""
    _dh_fields = {f.get("name"): f["down_deg"] for f in M.get("fields", []) if f.get("down_deg") is not None}
    return _kept(locals(), ('_dh_fields', 'f'))


def _seg_0457___dh_vec() -> dict[str, Any]:
    """Gate segment 457 (_dh_vec) - body verbatim from the legacy gate() (feature 022)."""

    def _dh_vec(deg: float) -> tuple[float, float]:
        return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))

    return _kept(locals(), ('_dh_vec',))


def _seg_0458___dh_map(*, _dh_dd: Any = _UNBOUND, _dh_vec: Any = _UNBOUND, downhill: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 458 (_dh_map) - body verbatim from the legacy gate() (feature 022)."""
    _dh_map = unit_dir(downhill) if downhill else (_dh_vec(_dh_dd) if _dh_dd is not None else None)
    return _kept(locals(), ('_dh_map',))


def _seg_0459__downhill_direction_valid(*, check: Any = _UNBOUND, downhill: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 459 (downhill_direction_valid) - body verbatim from the legacy gate() (feature 022)."""
    if downhill:
        check("downhill_direction_valid", bool(unit_dir(downhill)), f"meta(downhill={downhill!r}) is not a cardinal name or [dx,dy] vector")
    return _kept(locals(), ())


def _seg_0460__channels_flow_downhill(
    *,
    L: Any = _UNBOUND,
    _cdd: Any = _UNBOUND,
    _cto: Any = _UNBOUND,
    _dh_fields: Any = _UNBOUND,
    _dh_map: Any = _UNBOUND,
    _dh_vec: Any = _UNBOUND,
    c: Any = _UNBOUND,
    channels: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dvec: Any = _UNBOUND,
    ex: Any = _UNBOUND,
    ey: Any = _UNBOUND,
    sx: Any = _UNBOUND,
    sy: Any = _UNBOUND,
    uphill: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 460 (channels_flow_downhill) - body verbatim from the legacy gate() (feature 022)."""
    if (_dh_map or _dh_fields) and channels:
        uphill = []
        for c in channels:
            _cto = (c.get("to") or {}).get("name")
            _cdd = _dh_fields.get(_cto) if _cto else None
            dvec = _dh_vec(_cdd) if _cdd is not None else _dh_map
            if dvec is None:
                continue  # neither this channel's field nor the map declares a fall - nothing to judge it by
            (sx, sy), (ex, ey) = c["poly"][0], c["poly"][-1]
            vx, vy = ex - sx, ey - sy
            L = math.hypot(vx, vy)
            if L > 0 and (vx * dvec[0] + vy * dvec[1]) < 0.2 * L:  # not clearly running downhill
                uphill.append(c["to"].get("name", "?"))
        check("channels_flow_downhill", not uphill, f"channel(s) not running downhill (source must be uphill of the field it feeds): {sorted(set(uphill))}")
    return _kept(locals(), ('L', '_cdd', '_cto', 'c', 'dvec', 'ex', 'ey', 'sx', 'sy', 'uphill', 'vx', 'vy'))


# the same flow logic applies to a city MOAT: the moat is fed by a stream entering from one
# side (the source), so the moat water heads that-source-to-the-far-side direction (Tango's
# feeder enters from the north, so the moat water heads SOUTH). A moat-fed irrigation channel
# must run WITH that current - its field-end downstream of its moat-tap. A channel whose field
# is UPSTREAM of the tap reads as water flowing from the field INTO the moat (backwards).


def _seg_0461__moat_ring(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 461 (moat_ring) - body verbatim from the legacy gate() (feature 022)."""
    moat_ring: Any = M.get("moat")
    return _kept(locals(), ('moat_ring',))


def _seg_0462__c_5(*, c: Any = _UNBOUND, channels: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 462 (c, mfed) - body verbatim from the legacy gate() (feature 022)."""
    mfed = [c for c in channels if (c.get("frm") or {}).get("kind") == "moat"]
    return _kept(locals(), ('c', 'mfed'))


def _seg_0463__moat_channels_flow_with_current(
    *,
    M: Any = _UNBOUND,
    _mdx: Any = _UNBOUND,
    _mdy: Any = _UNBOUND,
    _mfl: Any = _UNBOUND,
    _mi: Any = _UNBOUND,
    _mo: Any = _UNBOUND,
    against: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dx: Any = _UNBOUND,
    dy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    ends: Any = _UNBOUND,
    ends_on_moat: Any = _UNBOUND,
    entry: Any = _UNBOUND,
    ex: Any = _UNBOUND,
    ey: Any = _UNBOUND,
    feeder: Any = _UNBOUND,
    flow: Any = _UNBOUND,
    mfed: Any = _UNBOUND,
    moat_ring: Any = _UNBOUND,
    origin: Any = _UNBOUND,
    st: Any = _UNBOUND,
    streams_m: Any = _UNBOUND,
    sx: Any = _UNBOUND,
    sy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 463 (moat_channels_flow_with_current) - body verbatim from the legacy gate() (feature 022)."""
    if moat_ring and len(moat_ring) >= 3 and mfed:
        # READ THE RECORDED CIRCULATION (GM 2026-07-25). This used to re-derive the moat's current by
        # taking the FIRST stream whose end touches the ring and snapping its entry heading to a
        # cardinal - fragile twice over: on a river-cut city BOTH the feeder and the outfall touch the
        # ring, so the answer depended on which the gen happened to draw first, and the cardinal snap
        # threw away up to 45 degrees. s.moat_flow / s.moat now record the inlet and outlet outright,
        # so the current is simply inlet -> outlet. Falls back to the old derivation for a moat with
        # no recorded circulation (moat_declares_circulation is what stops that being silent).
        # THE CURRENT COMES FROM THE RECORDED CIRCULATION (GM 2026-07-25), snapped to a cardinal as
        # this check has always done. Two fragilities in the old derivation are gone: it took the
        # FIRST stream whose end touched the ring, so on a river-cut city the answer depended on
        # draw order; and it required a stream END within 35px of the ring, which Nagahara's river
        # (ends off-map, the MOAT's ends meeting IT) never satisfies - so the check silently never
        # ran there at all. inlet -> outlet is the moat's net travel and needs no guessing.
        # The cardinal snap is deliberate and load-bearing: an irrigation offtake leaves the ring
        # roughly PERPENDICULAR, so its component along a precisely-measured tangent is near
        # arbitrary. The coarse hemisphere is what makes the test mean "the field is not back
        # upstream", rather than a coin flip on the along-ring component.
        flow = None
        _mfl = M.get("moat_flow") or {}
        if _mfl.get("inlet") and _mfl.get("outlet"):
            _mi, _mo = _mfl["inlet"], _mfl["outlet"]
            _mdx, _mdy = _mo[0] - _mi[0], _mo[1] - _mi[1]
            flow = (0, 1 if _mdy > 0 else -1) if abs(_mdy) >= abs(_mdx) else (1 if _mdx > 0 else -1, 0)
        feeder = None
        for st in streams_m:
            ends = (st["poly"][0], st["poly"][-1])
            ends_on_moat = [e for e in ends if poly_dist(e[0], e[1], moat_ring) <= 35]
            if ends_on_moat:
                entry = ends_on_moat[0]
                feeder = (entry, ends[1] if ends[0] == entry else ends[0])
                break
        if flow is None and feeder:
            entry, origin = feeder
            dx, dy = entry[0] - origin[0], entry[1] - origin[1]  # the heading the feeder water enters on
            flow = (0, 1 if dy > 0 else -1) if abs(dy) >= abs(dx) else (1 if dx > 0 else -1, 0)  # snapped to a cardinal
        if flow is not None:
            against = []
            for c in mfed:
                (sx, sy), (ex, ey) = c["poly"][0], c["poly"][-1]  # frm=moat, so poly[0] is the moat tap
                if (ex - sx) * flow[0] + (ey - sy) * flow[1] < -8:  # field clearly upstream of the tap
                    against.append(c["to"].get("name", "?"))
            check(
                "moat_channels_flow_with_current",
                not against,
                f"moat-fed channel(s) running against the moat current (field is upstream of the tap; the feeder makes the moat flow {flow}): {sorted(set(against))}",
            )
    return _kept(locals(), ('_mdx', '_mdy', '_mfl', '_mi', '_mo', 'against', 'c', 'dx', 'dy', 'e', 'ends', 'ends_on_moat', 'entry', 'ex', 'ey', 'feeder', 'flow', 'origin', 'st', 'sx', 'sy'))


# A MOAT JUNCTION IS SWEPT WITH THE CURRENT (GM 2026-07-25). Where a channel meets the moat, its
# LOCAL heading at the junction must carry a downstream component - a tributary joins a trunk
# pointing downstream, and an irrigation offtake takes off downstream so the water turns in
# smoothly instead of doubling back on itself. The engine already holds moat<->RIVER junctions to
# exactly this (city_moat_junction_angles: inlet near-square, outlet swept downstream); this
# extends it to moat<->CHANNEL junctions, which nothing checked.
#
# NOTE the quantity: the LOCAL segment at the junction, NOT the channel's net vector to its field.
# The net vector is near-arbitrary for an offtake that leaves the ring roughly perpendicular (that
# is why moat_channels_flow_with_current above keeps a coarse cardinal test and is NOT this check).
# The current is the ring TANGENT at the tap, in the direction of travel along that tap's own arc -
# a ring has no single downstream side, since water entering the inlet runs BOTH ways round to the
# outlet. WHAT IT CAUGHT (GM's eye, then this check): every offtake on BOTH cities stepped upstream,
# because the offtake tee was drawn as mirrored geometry whose along-rim step was never oriented to
# the local flow; plus Tango's fn2 drain culvert doubling back to enter at 138 deg and Nagahara's
# fnn1 at 115 deg. Fixtures: the pre-fix Tango and Nagahara manifests in pool/regressions/.


def _seg_0464___mjr(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 464 (_mjr) - body verbatim from the legacy gate() (feature 022)."""
    _mjr: Any = M.get("moat")
    return _kept(locals(), ('_mjr',))
