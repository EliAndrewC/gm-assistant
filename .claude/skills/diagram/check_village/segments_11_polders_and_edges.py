"""Gate segments (polders and edges) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from typing import Any

from settlement import seg_in_ellipse_core

from .common_01_geometry import point_in_poly, poly_area, poly_dist, pt_to_rect, seg_closest, seg_dist
from .common_02_overlap_policy import in_ellipse
from .common_03_capacity import _UNBOUND, WAIVER_META_CHECKS, WAIVER_MIN_REASON, _kept, crop_relocatable_singletons

# Tax-free (temple/monk glebe) plots are OPTIONAL - marking them on the map is a choice, not a
# requirement. The check only validates the COUNT when a map opts in (it drew some, or meta asks for
# them); a village that does not denote them at all is fine.


def _seg_0564__taxfree_plots_in_range(*, M: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND, tf: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 564 (taxfree_plots_in_range) - body verbatim from the legacy gate() (feature 022)."""
    if scale == "village" and (M.get("taxfree") or meta.get("taxfree_expected")):
        tf = M.get("taxfree", [])
        check("taxfree_plots_in_range", 2 <= len(tf) <= 3, f"{len(tf)} tax-free plots (law: ~2 households)")
    return _kept(locals(), ('tf',))


def _seg_0565__big_paddies(*, f: Any = _UNBOUND, fields: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 565 (big_paddies, f) - body verbatim from the legacy gate() (feature 022)."""
    big_paddies = sorted(
        [f for f in fields if f["kind"] == "paddy" and (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]) > 80000],
        key=lambda f: -(f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]),
    )
    return _kept(locals(), ('big_paddies', 'f'))


def _seg_0566__common_fields_vary_orientation(*, big_paddies: Any = _UNBOUND, check: Any = _UNBOUND, f: Any = _UNBOUND, scale: Any = _UNBOUND, wide: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 566 (common_fields_vary_orientation) - body verbatim from the legacy gate() (feature 022)."""
    if scale != "city" and len(big_paddies) >= 2:  # a city's in-wall plots / off-edge fields are not staggered common fields

        def wide(f: dict[str, Any]) -> bool:
            return bool((f["bbox"][2] - f["bbox"][0]) >= (f["bbox"][3] - f["bbox"][1]))

        check("common_fields_vary_orientation", wide(big_paddies[0]) != wide(big_paddies[1]), "the two large common fields share an orientation")
    return _kept(locals(), ('wide',))


def _seg_0567__fallow_has_abandoned(
    *, ADJ: Any = _UNBOUND, ab: Any = _UNBOUND, check: Any = _UNBOUND, f: Any = _UNBOUND, fields: Any = _UNBOUND, h: Any = _UNBOUND, houses: Any = _UNBOUND, meta: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 567 (fallow_has_abandoned) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("fallow_implies_abandoned"):
        for f in fields:
            if f["kind"] == "fallow":
                ab = sum(1 for h in houses if h["kind"] == "abandoned" and poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
                check(f"fallow_has_abandoned[{f['name']}]", ab >= 2, f"{ab} abandoned near {f['name']}, need 2")
    return _kept(locals(), ('ab', 'f', 'h'))


def _seg_0568__shrine_on_hill_summit(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    hill: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    offhill: Any = _UNBOUND,
    on_hill: Any = _UNBOUND,
    on_summit: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    sc: Any = _UNBOUND,
    sh: Any = _UNBOUND,
    sw: Any = _UNBOUND,
    sx: Any = _UNBOUND,
    sy: Any = _UNBOUND,
    t: Any = _UNBOUND,
    torii: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 568 (shrine_on_hill_summit, torii_on_hill) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("shrine_on_hill") and M.get("shrine") and M.get("summit") and hill:
        sx, sy, sw, sh = M["shrine"]
        sc = [(sx, sy), (sx + sw, sy), (sx + sw, sy + sh), (sx, sy + sh)]
        on_hill = all(in_ellipse(px, py, hill) for px, py in sc)
        on_summit = in_ellipse(sx + sw / 2, sy + sh / 2, M["summit"])
        check("shrine_on_hill_summit", on_hill and on_summit, "shrine overhangs the hill or is off the summit")
        offhill = [t for t in torii if not in_ellipse(t[0], t[1], hill)]
        check("torii_on_hill", not offhill, f"{len(offhill)} torii off the hill")
    return _kept(locals(), ('offhill', 'on_hill', 'on_summit', 'px', 'py', 'sc', 'sh', 'sw', 'sx', 'sy', 't'))


def _seg_0569__torii_count(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, torii: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 569 (torii_count) - body verbatim from the legacy gate() (feature 022)."""
    if "torii_expected" in meta:
        check("torii_count", len(torii) == meta["torii_expected"], f"{len(torii)} torii, expected {meta['torii_expected']}")
    return _kept(locals(), ())


# TORII COUNTS ARE NUMEROLOGICAL (GM 2026-07-21): in Rokugan the number 7 is even more significant
# than in the real world, so every PROPER religious site - shrine, monastery, temple - carries exactly
# 1, 3, or 7 torii, never another number, unless the hall is specifically marked an outlier
# (shrine_hall(torii_outlier=True), recorded on the religious rec). The rolled distribution per tier
# lives in settlement.roll_torii_count and settlements.md 'Torii'. The floor is 1: a proper hall with
# NO torii reads as the abandoned/anomalous case (historically rare enough that each had a story).
# kind='small_shrine' is EXEMPT - the hokora/wayside tier draws its own miniature token torii as part
# of the glyph and historically mostly had none; it is also excluded from ATTRIBUTION, so a wayside
# shed near a temple's sando cannot steal the temple's gates (that misattribution hid Tango's Daikoku
# pair during the first survey). Each recorded torii is attributed to the NEAREST proper hall.


def _seg_0570___proper(*, M: Any = _UNBOUND, r: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 570 (_proper, r) - body verbatim from the legacy gate() (feature 022)."""
    _proper = [r for r in M.get("religious", []) if r.get("kind") != "small_shrine"]
    return _kept(locals(), ('_proper', 'r'))


def _seg_0571__torii_count_canonical(
    *,
    M: Any = _UNBOUND,
    _THRESH_SLACK_FT: Any = _UNBOUND,
    _bad_torii: Any = _UNBOUND,
    _ft: Any = _UNBOUND,
    _gap: Any = _UNBOUND,
    _marooned: Any = _UNBOUND,
    _mismatch: Any = _UNBOUND,
    _near: Any = _UNBOUND,
    _nr: Any = _UNBOUND,
    _pcap: Any = _UNBOUND,
    _pitch: Any = _UNBOUND,
    _proper: Any = _UNBOUND,
    _t: Any = _UNBOUND,
    _tarch: Any = _UNBOUND,
    _tcount: Any = _UNBOUND,
    _tf_all: Any = _UNBOUND,
    _tf_bad: Any = _UNBOUND,
    _tf_major: Any = _UNBOUND,
    _tf_reach: Any = _UNBOUND,
    _tf_served: Any = _UNBOUND,
    _tfa: Any = _UNBOUND,
    _tfax: Any = _UNBOUND,
    _tfay: Any = _UNBOUND,
    _tfc: Any = _UNBOUND,
    _tfh: Any = _UNBOUND,
    _tfi: Any = _UNBOUND,
    _tfl: Any = _UNBOUND,
    _tfna: Any = _UNBOUND,
    _tfnb: Any = _UNBOUND,
    _tfr: Any = _UNBOUND,
    _tfs: Any = _UNBOUND,
    _tfw: Any = _UNBOUND,
    _tfwx: Any = _UNBOUND,
    _tfwy: Any = _UNBOUND,
    _ts: Any = _UNBOUND,
    _wide: Any = _UNBOUND,
    _worst: Any = _UNBOUND,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    r: Any = _UNBOUND,
    t: Any = _UNBOUND,
    torii: Any = _UNBOUND,
    v: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 571 (temple_torii_face_the_street, torii_avenue_meets_the_hall, torii_avenue_pitch_capped, torii_count_canonical, torii_match_roll) - body verbatim from the legacy gate() (feature 022)."""
    if _proper:
        _tarch: dict[int, list[Any]] = {id(r): [] for r in _proper}  # type: ignore[no-redef]
        for _t in torii:
            _nr = min(_proper, key=lambda r: math.hypot(r["x"] - _t[0], r["y"] - _t[1]))
            _tarch[id(_nr)].append(_t)
        _tcount = {k: len(v) for k, v in _tarch.items()}
        _bad_torii = [(round(r["x"]), round(r["y"]), _tcount[id(r)]) for r in _proper if _tcount[id(r)] not in (1, 3, 7) and not r.get("torii_outlier")]
        check(
            "torii_count_canonical",
            not _bad_torii,
            f"hall(s) with a non-numerological torii count (x, y, n): {_bad_torii[:4]} - every shrine/monastery/temple carries exactly 1, 3, or 7 torii (7 is numerologically potent in Rokugan; see settlements.md 'Torii'), or is explicitly marked shrine_hall(torii_outlier=True)",
        )
        # A HALL BY A MAJOR WAY FACES ITS TORII TOWARD *A* WAY (GM 2026-08-09): the sando exists
        # so an approacher passes beneath the arches on the way IN - that is what a monzen
        # ("before the gate") district is before. When a shrine/monastery/temple stands within
        # reach of a road or city street, its avenue must face SOME way it can serve - the major
        # way itself, or the hall's own approach lane (a temple legitimately fronts its monzen
        # lane while a bigger street passes behind: Minami's eight trade-sited precincts and
        # Nagahara's temple lane are exactly that, which is why the first cut of this rule -
        # "face the NEAREST major way" - fired on four correct Minami halls). Arches facing no
        # way at all put the gateway behind the temple, which is the defect that named the rule
        # (the capital's Jurojin marched its avenue away from the kagi-no-te road into empty
        # ground). ASSOCIATION/bearing family: hall-center to arch-centroid vs hall-center to
        # each way's closest point, 60 deg tolerance, ~180px reach; no major way in reach ->
        # skip, a hall in open fabric faces where it will.
        _tf_major: list[Any] = ([M["road"]] if M.get("road") else []) + [_tfr["pts"] for _tfr in M.get("roads", [])] + [_tfs["pts"] for _tfs in M.get("town_streets", [])]  # type: ignore[no-redef]
        _tf_all: list[Any] = _tf_major + [_tfl["pts"] for _tfl in M.get("lanes", [])]  # type: ignore[no-redef]
        _tf_bad = []
        for _tfh in _proper:
            _tfa = _tarch[id(_tfh)]
            if not _tfa:
                continue
            # a DOORSTEP arch is not an avenue: a hall's 1-2 modest-entrance arches stand at its
            # own threshold and face the way the HALL faces (south, by building convention) -
            # only a sando that actually marches somewhere has a direction worth policing
            # (Minami's Benten and Daikoku each keep one arch 18px off the south face; firing
            # on those was the rule mistaking a door for a road)
            if max(math.hypot(t[0] - _tfh["x"], t[1] - _tfh["y"]) for t in _tfa) < 45:
                continue
            _tf_reach = min((seg_dist(_tfh["x"], _tfh["y"], _tfw[_tfi], _tfw[_tfi + 1]) for _tfw in _tf_major for _tfi in range(len(_tfw) - 1)), default=1e9)
            if _tf_reach > 180:
                continue
            _tfax = sum(t[0] for t in _tfa) / len(_tfa) - _tfh["x"]
            _tfay = sum(t[1] for t in _tfa) / len(_tfa) - _tfh["y"]
            _tfna = math.hypot(_tfax, _tfay) or 1.0
            _tf_served = False
            for _tfw in _tf_all:
                for _tfi in range(len(_tfw) - 1):
                    _tfc = seg_closest(_tfh["x"], _tfh["y"], _tfw[_tfi], _tfw[_tfi + 1])
                    _tfwx, _tfwy = _tfc[0] - _tfh["x"], _tfc[1] - _tfh["y"]
                    _tfnb = math.hypot(_tfwx, _tfwy)
                    if _tfnb > 180 or _tfnb < 1e-6:
                        continue
                    if (_tfax * _tfwx + _tfay * _tfwy) / (_tfna * _tfnb) >= 0.5:
                        _tf_served = True
                        break
                if _tf_served:
                    break
            if not _tf_served:
                _tf_bad.append((round(_tfh["x"]), round(_tfh["y"])))
        check(
            "temple_torii_face_the_street",
            not _tf_bad,
            f"hall(s) whose torii avenue faces no way it could serve (x, y): {_tf_bad[:4]} - an approacher passes beneath the arches on the way in, so the sando stands between the hall and a street or its own approach lane",
        )
        # DRAWN COUNT MATCHES THE ROLL (GM 2026-07-23, the full re-roll): shrine_hall rolls each
        # hall's count on the tier's TORII_WEIGHTS column (or takes the torii_count= pin) and records
        # the target on the religious rec - this gates that the drawn, ATTRIBUTED avenue equals it,
        # so a stale hand-placed count (the pre-table Tango/Nagahara state) or a misattributed arch
        # (an extended avenue drifting nearer a NEIGHBOR hall) can never ship silently. Halls
        # without a recorded target (the village auto-shrine path records meta.torii_count instead)
        # are skipped.
        _mismatch = [(round(r["x"]), round(r["y"]), _tcount[id(r)], r["torii_count"]) for r in _proper if "torii_count" in r and _tcount[id(r)] != r["torii_count"]]
        check(
            "torii_match_roll",
            not _mismatch,
            f"hall(s) whose drawn torii count differs from their rolled/pinned target (x, y, drawn, target): {_mismatch[:4]} - the avenue must carry exactly the rolled/pinned count (shrine_hall torii_count=), and every arch must sit nearest ITS OWN hall (attribution is by nearest proper hall)",
        )

        # AN AVENUE'S ARCHES STAND CLOSE TOGETHER (GM 2026-07-25, after the spacing research pass -
        # settlements.md 'Torii'). WHY: Rokugan's sando is the 1/3/7 SET of formal gateways, not a
        # Fushimi-style donation row (donation rows are a designated-site special case here: Shinden
        # Togashi, the Temple of Amaterasu, the Ki Rin Shrine and their like), so neither real-world
        # spacing regime is the model - a donation row nearly touches (~0.5-1 m), ranked ichi/ni/san
        # gates stand 200 m - 1.3 km apart, and there is nothing in between to copy. The house rule:
        # ~20 ft center-to-center, never more than TWO rail-spans (32 ft), past which the arches read
        # as isolated gates strung across the map rather than one approach. This is the CEILING to
        # torii_spread_out's one-span floor. The village avenues (~30 ft) sit at the top of the band
        # by GM preference, hence the half-foot of rounding slack; the town/city avenues that motivated
        # it ran 45-114 ft. settlement._avenue_pitch re-lays anything over the cap at the ~20 ft
        # standard, so the gen authors the avenue's LINE and the engine owns its stride.
        # Measured per hall over its ATTRIBUTED arches (a single-arch hall has no pitch); an explicit
        # torii_outlier hall - the designated donation-row site - is exempt, as it is from the count rule.
        _pcap = 16.0 * 2.0 + 0.5
        _ft = float(meta.get("ftpx", 1) or 1)
        _wide = []
        for r in _proper:
            _ts = _tarch[id(r)]
            if r.get("torii_outlier") or len(_ts) < 2:
                continue
            _worst = max(min(math.hypot(a[0] - b[0], a[1] - b[1]) for b in _ts if b is not a) for a in _ts) * _ft
            if _worst > _pcap:
                _wide.append((round(r["x"]), round(r["y"]), round(_worst)))
        check(
            "torii_avenue_pitch_capped",
            not _wide,
            f"hall(s) whose avenue strings its arches too far apart (x, y, worst gap ft): {_wide[:4]} - an avenue's arches "
            f"stand ~20 ft apart and never more than two rail-spans (32 ft); further apart they read as isolated gates, "
            f"not one approach (settlements.md 'Torii'). Author the avenue's LINE and let shrine_hall set the pitch.",
        )

        # ...AND THE AVENUE STARTS AT ITS HALL (GM 2026-07-27): "the distance from the front of the
        # temple should be the same as the distance between each torii arch". WHY: fixing the STRIDE
        # (above) left the other half of the same defect standing. An avenue could be perfectly spaced
        # at 20 ft and still be authored yards from the temple it serves - Tango's Bishamon sando stood
        # 139 ft off, three arches up a street on the far side of a flophouse, and Nagahara's Ebisu
        # avenue began 120 ft south of its hall with the caption and two rows of houses in between.
        # Neither read as that temple's approach; they read as red marks near some other building. So
        # the gap from the hall's FOOTPRINT to the nearest arch is measured against the avenue's OWN
        # pitch, and settlement._avenue_at_threshold seats it there exactly - the gen authors the
        # LINE, the engine owns the count, the stride AND the threshold.
        #
        # An UPPER bound, not an equality, and the asymmetry is deliberate. The village path (the
        # civic-shrine roll and the gens' own s.shrine + _torii runs) seats its arches at 0.6-0.9 of
        # its 30 ft stride, which the GM approved as canon on 2026-07-22 - and that day's rule,
        # shrine_avenue_fronts_the_hall, already owns the LOWER bound ("the innermost arch sits at the
        # hall's threshold, not set out with a gap"). This one owns the upper, so the two meet without
        # either forcing cosmetic churn on maps the GM has already signed off.
        #
        # A single arch has no pitch of its own, so it is measured against the engine's standard stride
        # (TORII_PITCH_FT, 20 ft) - the same number _avenue_at_threshold seats it at. torii_outlier
        # halls are exempt here as they are from the count and pitch rules: a designated donation-row
        # site is not a 1/3/7 sando and is not measured like one.
        _THRESH_SLACK_FT = 4.0  # rounding + the sub-foot drift a shortened run leaves behind
        _marooned = []
        for r in _proper:
            _ts = _tarch[id(r)]
            if r.get("torii_outlier") or not _ts:
                continue
            _near = min(_ts, key=lambda t: pt_to_rect(t[0], t[1], r))
            _gap = pt_to_rect(_near[0], _near[1], r) * _ft
            _pitch = min(math.hypot(a[0] - _near[0], a[1] - _near[1]) for a in _ts if a is not _near) * _ft if len(_ts) > 1 else 20.0
            if _gap > _pitch + _THRESH_SLACK_FT:
                _marooned.append((round(r["x"]), round(r["y"]), round(_gap), round(_pitch)))
        check(
            "torii_avenue_meets_the_hall",
            not _marooned,
            f"hall(s) whose sando starts too far out (x, y, gap to the hall ft, pitch ft): {_marooned[:4]} - the "
            f"innermost arch stands one PITCH off the hall's front, so the gap to the temple matches the gap between "
            f"arches; further out the avenue reads as gates belonging to nothing. Author the avenue's LINE and let "
            f"shrine_hall seat the threshold (settlement._avenue_at_threshold).",
        )
    return _kept(
        locals(),
        (
            '_THRESH_SLACK_FT',
            '_bad_torii',
            '_ft',
            '_gap',
            '_marooned',
            '_mismatch',
            '_near',
            '_nr',
            '_pcap',
            '_pitch',
            '_t',
            '_tarch',
            '_tcount',
            '_tf_all',
            '_tf_bad',
            '_tf_major',
            '_tf_reach',
            '_tf_served',
            '_tfa',
            '_tfax',
            '_tfay',
            '_tfc',
            '_tfh',
            '_tfi',
            '_tfl',
            '_tfna',
            '_tfnb',
            '_tfr',
            '_tfs',
            '_tfw',
            '_tfwx',
            '_tfwy',
            '_ts',
            '_wide',
            '_worst',
            'a',
            'b',
            'k',
            'r',
            't',
            'v',
        ),
    )


def _seg_0572__pond_bigger_than_headman(
    *, M: Any = _UNBOUND, check: Any = _UNBOUND, headman: Any = _UNBOUND, hill: Any = _UNBOUND, pcx: Any = _UNBOUND, pcy: Any = _UNBOUND, prx: Any = _UNBOUND, pry: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 572 (pond_bigger_than_headman, pond_clear_of_hill) - body verbatim from the legacy gate() (feature 022)."""
    if M.get("pond"):
        pcx, pcy, prx, pry = M["pond"]
        if headman is not None:
            check("pond_bigger_than_headman", math.pi * prx * pry > headman["w"] * headman["h"], "pond not larger than headman house")
        if hill:
            check("pond_clear_of_hill", not in_ellipse(pcx, pcy, hill, 1.4), "pond too close to the hill (erosion)")
    return _kept(locals(), ('pcx', 'pcy', 'prx', 'pry'))


# A declared LAND-USE overlay must actually be DRAWN (feature 005 US4): a village that says it grows
# mulberry-fishpond / rape / lotus / hill-tea must show plots (or a tea fringe) of it, not just a label.


def _seg_0573__lu(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 573 (lu) - body verbatim from the legacy gate() (feature 022)."""
    lu = meta.get("land_use_overlay")
    return _kept(locals(), ('lu',))


def _seg_0574__land_use_overlay_drawn(
    *, M: Any = _UNBOUND, check: Any = _UNBOUND, had_ground: Any = _UNBOUND, lu: Any = _UNBOUND, off: Any = _UNBOUND, p: Any = _UNBOUND, r: Any = _UNBOUND, recs: Any = _UNBOUND, wet: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 574 (land_use_overlay_drawn, overlays_on_wet_ground_only) - body verbatim from the legacy gate() (feature 022)."""
    if lu and lu != "none":
        recs = [r for r in M.get("land_use", []) if r.get("overlay") == lu]
        wet = {tuple(p) for p in M.get("wet_plots", [])}
        # An overlay with NO eligible ground legitimately draws nothing (feature 010) - so the "was it
        # drawn" test is: the record must EXIST (proving apply_land_use ran), and must have a non-zero
        # count unless there was no eligible ground for it to sit on.
        had_ground = bool(wet) or lu == "tea_fringe" or (recs and recs[0].get("eligible") == "all")
        check(
            "land_use_overlay_drawn",
            bool(recs) and (recs[0].get("count", 0) > 0 or not had_ground),
            f"meta declares land_use_overlay={lu!r} but no plots/rows were drawn with it - call s.apply_land_use()",
        )

        # TOPOGRAPHIC GROUNDING (feature 010). A plot-based overlay may only sit on the LOW/WET ground.
        # Topography sets which plots are ELIGIBLE; economy decides how many convert. Deep-water lotus
        # (30-50cm, vs paddy rice's 5-9cm) physically cannot sit on high ground, and the dike-pond system
        # was dug out of 低洼易有洪患之处 - the low flood-prone hollows. See research.md D1/D2.
        # `eligible == "all"` is the named wholesale-conversion opt-out used by the dike-pond ARCHETYPE.
        # Teeth: `wet_plots` is written by the FIELD pass and `plots` by the OVERLAY pass, so this
        # compares two independently-produced records rather than reading back a self-report.
        for r in recs:
            if r.get("eligible") == "all" or not r.get("plots"):
                continue
            off = [p for p in r["plots"] if tuple(p) not in wet]
            check("overlays_on_wet_ground_only", not off, f"{len(off)} {lu} plot(s) sit on ordinary rice ground, not the low/wet ground that determines them (e.g. {off[:2]})")
    return _kept(locals(), ('had_ground', 'off', 'p', 'r', 'recs', 'wet'))

    # NO `dikeponds_are_clustered` CHECK - deliberately, and this is worth recording so nobody "adds
    # the missing check" later. The dike-pond conversion really did spread plot-by-plot in patches
    # (挖塘培基, a one-plot job in one dry season), and `_pick_overlay_plots` models that. But it is
    # NOT INDEPENDENTLY OBSERVABLE here: the eligible set is always a thin contiguous strip of low
    # ground (comb = plots abutting the drain, polder = the lowest rows, terraces/ribbon = the lowest
    # bands), and every subset of a strip is "clustered" by any nearest-neighbor-vs-span metric. A
    # version of this check was written, and an EVEN random scatter of the same count passed it - so
    # it would have been a check that cannot fail, which is worse than no check. If a future field
    # archetype ever yields a genuinely 2-D eligible region, this becomes testable and worth adding.


# IN-FIELD PADDY FEATURES (feature 012) must honor the per-archetype ELIGIBILITY MATRIX
# (specs/012-.../research.md): a low-pocket pond, a bedrock rock outcrop, or a rare grave island appear
# only where their archetype allows, and NEVER on mulberry_dike_fishpond (open water is its fabric).
# Ponds must additionally sit on LOW/WET ground (the pocket that determines them) - teeth from `wet_plots`
# (written by the field pass) vs the pond record (written by the feature pass), two independent sources.


def _seg_0575__arch(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 575 (arch) - body verbatim from the legacy gate() (feature 022)."""
    arch = meta.get("field_archetype")
    return _kept(locals(), ('arch',))


def _seg_0576___ELIG() -> dict[str, Any]:
    """Gate segment 576 (_ELIG) - body verbatim from the legacy gate() (feature 022)."""
    _ELIG = {
        "field_ponds": ("valley_paddy", "contour_terraces", "polder_grid", "ribbon_valley"),
        "field_rocks": ("contour_terraces", "ribbon_valley"),
        "field_graves": ("valley_paddy", "contour_terraces", "ribbon_valley"),
    }
    return _kept(locals(), ('_ELIG',))


def _seg_0577__paddy_features_match_archetype(
    *,
    M: Any = _UNBOUND,
    _ELIG: Any = _UNBOUND,
    arch: Any = _UNBOUND,
    check: Any = _UNBOUND,
    k: Any = _UNBOUND,
    mis: Any = _UNBOUND,
    off: Any = _UNBOUND,
    ok: Any = _UNBOUND,
    p: Any = _UNBOUND,
    wet: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 577 (field_ponds_on_low_ground, paddy_features_match_archetype) - body verbatim from the legacy gate() (feature 022)."""
    if arch:
        mis = [(k, len(M.get(k, []))) for k, ok in _ELIG.items() if M.get(k) and arch not in ok]
        check("paddy_features_match_archetype", not mis, f"in-field feature(s) on the wrong paddy type ({arch}): {mis} - see the archetype matrix in specs/012-in-field-paddy-features/research.md")
        if M.get("field_ponds"):
            wet = {tuple(p) for p in M.get("wet_plots", [])}
            off = [[p["x"], p["y"]] for p in M["field_ponds"] if (p["x"], p["y"]) not in wet]
            check("field_ponds_on_low_ground", not off, f"{len(off)} field pond(s) not on the low/wet ground that determines them (e.g. {off[:2]}) - a pond is a LOW pocket, not a mid-field puddle")
    return _kept(locals(), ('k', 'mis', 'off', 'ok', 'p', 'wet'))


# A feature-012 pond is sunk INTO one paddy plot - the field tiles AROUND it (the overlap
# registry's own words). Low/wet eligibility (`field_ponds_on_low_ground`, above) cannot hold that:
# it reads the host plot's flag, not the ellipse's extent, so Inashiro (2026-08-16) shipped green
# with a bbox-sized pond in a fan-toe WEDGE - the ellipse spilled over three neighboring wedge
# plots and two drain-hem plots, spoke bunds drawn straight through open water. The bund geometry
# here (`plot_rings` + `drain_hem`) is the FIELD pass's record and the pond is the FEATURE pass's,
# two independent sources; the core inset (4 px, in `seg_in_ellipse_core`) is the rim allowance -
# a bund may TOUCH the shore (the host plot's own ring does), it may not run through the water.


def _seg_0577_500__field_ponds_sunk_into_one_plot(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    fld: Any = _UNBOUND,
    fp: Any = _UNBOUND,
    spilled: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 577.5 (field_ponds_sunk_into_one_plot) - no bund/hem line through a field pond's water."""
    if M.get("field_ponds"):
        spilled = []
        for fp in M["field_ponds"]:
            for fld in M.get("fields") or []:
                if any(
                    seg_in_ellipse_core(ring[i], ring[(i + 1) % len(ring)], fp["x"], fp["y"], fp["rx"], fp["ry"])
                    for ring in (fld.get("plot_rings") or []) + (fld.get("drain_hem") or [])
                    for i in range(len(ring))
                ):
                    spilled.append([fp["x"], fp["y"]])
                    break
        check(
            "field_ponds_sunk_into_one_plot",
            not spilled,
            f"{len(spilled)} field pond(s) crossed by bund/hem lines (e.g. {spilled[:2]}) - a feature-012 pond is sunk INTO one plot and the field tiles AROUND it; an ellipse spanning plots reads as a flood, not a low pocket",
        )
    return _kept(locals(), ('fld', 'fp', 'spilled'))


# A contour-TERRACES field (feature 005 US4) must actually read as STEPPED CROSS-SLOPE BANDS: enough terrace
# retaining bunds, each running roughly PERPENDICULAR to the fall (a terrace lip follows the contour, across
# the slope - a bund that ran downhill would be a channel, not a terrace step). This is the archetype's teeth.


def _seg_0578__contour_terraces_are_stepped_bands(
    *,
    M: Any = _UNBOUND,
    acrs: Any = _UNBOUND,
    along: Any = _UNBOUND,
    bl: Any = _UNBOUND,
    bunds: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dd: Any = _UNBOUND,
    ddx: Any = _UNBOUND,
    ddy: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    n_cross: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 578 (contour_terraces_are_stepped_bands) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("field_archetype") == "contour_terraces":
        bunds = M.get("terrace_bunds", [])
        dd = meta.get("down_deg", 90)
        ddx, ddy = math.cos(math.radians(dd)), math.sin(math.radians(dd))
        n_cross = 0
        for bl in bunds:
            if len(bl) < 2:
                continue
            along = abs((bl[-1][0] - bl[0][0]) * ddx + (bl[-1][1] - bl[0][1]) * ddy)  # span along the fall
            acrs = abs((bl[-1][0] - bl[0][0]) * -ddy + (bl[-1][1] - bl[0][1]) * ddx)  # span across the fall
            if acrs > 2.0 * along:  # a genuine n_cross-slope contour bund
                n_cross += 1
        check(
            "contour_terraces_are_stepped_bands",
            len(bunds) >= 8 and n_cross >= 8,
            f"a contour_terraces field needs >=8 cross-slope terrace bunds (found {len(bunds)} bunds, {n_cross} cross-slope) - the defining stepped-band look",
        )
    return _kept(locals(), ('acrs', 'along', 'bl', 'bunds', 'dd', 'ddx', 'ddy', 'n_cross'))


# A POLDER-grid field (feature 005 US4) is a solid rectilinear BLOCK - it FILLS its bounding box (unlike the
# comb fan or the contour terraces, whose outline covers a small fraction of its bbox). That fill ratio is
# the archetype's teeth: a polder reads as a surveyed rectangle, not an organic field.


def _seg_0579__polder_fills_its_bbox(
    *, b: Any = _UNBOUND, bbox_area: Any = _UNBOUND, check: Any = _UNBOUND, fields: Any = _UNBOUND, fill_ratio: Any = _UNBOUND, meta: Any = _UNBOUND, pf: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 579 (polder_fills_its_bbox) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("field_archetype") == "polder_grid" and fields:
        pf = fields[0]
        b = pf.get("bbox") or [0, 0, 1, 1]
        bbox_area = max(1.0, (b[2] - b[0]) * (b[3] - b[1]))
        fill_ratio = poly_area(pf["outline"]) / bbox_area
        check(
            "polder_fills_its_bbox",
            fill_ratio >= 0.82,
            f"a polder_grid field must FILL its bounding box (a surveyed rectangular block), but its outline covers only {fill_ratio:.0%} of its bbox - that reads as a fan/terraced field, not a polder",
        )
    return _kept(locals(), ('b', 'bbox_area', 'fill_ratio', 'pf'))


# A MULBERRY-DIKE FISH-POND field (feature 005 US4, 桑基魚塘) is a filled block whose cells are FISH PONDS
# rimmed by mulberry dikes - so it must both fill its bbox (a reclaimed block) AND carry a mulberry_fishpond
# land-use over most of it. China-first: the Pearl-delta closed sericulture-aquaculture system.


def _seg_0580__dikepond_is_ponds_in_a_block(
    *,
    M: Any = _UNBOUND,
    _chs: Any = _UNBOUND,
    _cross: Any = _UNBOUND,
    _dp: Any = _UNBOUND,
    _dponds: Any = _UNBOUND,
    _dpw: Any = _UNBOUND,
    _drains: Any = _UNBOUND,
    _fd_bad: Any = _UNBOUND,
    _fdd: Any = _UNBOUND,
    _fdfall: Any = _UNBOUND,
    _fdx: Any = _UNBOUND,
    _fdy: Any = _UNBOUND,
    _feeds: Any = _UNBOUND,
    _mb_a: Any = _UNBOUND,
    _mb_b: Any = _UNBOUND,
    _mb_bad: Any = _UNBOUND,
    _mb_banks: Any = _UNBOUND,
    _mb_box: Any = _UNBOUND,
    _mb_boxes: Any = _UNBOUND,
    _mb_cp: Any = _UNBOUND,
    _mb_j: Any = _UNBOUND,
    _mb_k: Any = _UNBOUND,
    _mb_missing: Any = _UNBOUND,
    _mb_poly: Any = _UNBOUND,
    _mb_steps: Any = _UNBOUND,
    _mb_t: Any = _UNBOUND,
    _mb_x: Any = _UNBOUND,
    _mb_y: Any = _UNBOUND,
    _min_wv: Any = _UNBOUND,
    _mine: Any = _UNBOUND,
    _n_dp: Any = _UNBOUND,
    _o: Any = _UNBOUND,
    _reaches: Any = _UNBOUND,
    _sl: Any = _UNBOUND,
    _spill: Any = _UNBOUND,
    _w: Any = _UNBOUND,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cp: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dp_fill: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pf: Any = _UNBOUND,
    pond_rec: Any = _UNBOUND,
    pt: Any = _UNBOUND,
    q: Any = _UNBOUND,
    r: Any = _UNBOUND,
    s: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 580 (dikepond_corners_rounded, dikepond_is_ponds_in_a_block, dikepond_water_within_banks, dikeponds_fed_and_drained, mulberry_banks_clear_of_channels) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("field_archetype") == "mulberry_dike_fishpond" and fields:
        pf = fields[0]
        b = pf.get("bbox") or [0, 0, 1, 1]
        dp_fill = poly_area(pf["outline"]) / max(1.0, (b[2] - b[0]) * (b[3] - b[1]))
        pond_rec = [r for r in M.get("land_use", []) if r.get("overlay") == "mulberry_fishpond" and r.get("count", 0) >= 20]
        check(
            "dikepond_is_ponds_in_a_block",
            dp_fill >= 0.82 and bool(pond_rec),
            f"a mulberry_dike_fishpond field must be a filled block ({dp_fill:.0%} of bbox) of many mulberry-rimmed fish ponds (enough pond cells: {bool(pond_rec)}) - the 桑基魚塘 system",
        )

        # THE POND WATER IS INSET WITHIN ITS MULBERRY BANKS, WITH ROUNDED CORNERS (GM 2026-07-22, issues 3 + 5):
        # each 桑基魚塘 pond is a dug water body set INSIDE its parcel's green mulberry dike (基) - the water does
        # NOT fill the parcel to its edge, and its dug corners erode ROUND (a premodern earthen pond has no
        # poured-concrete right angles). Teeth read the recorded `dikeponds`: every pond's water polygon must lie
        # inside its parcel (issue 3), and carry the corner rounding as many sampled vertices (issue 5). The
        # pre-fix full-parcel teal fill recorded no `dikeponds` at all and fires both. Grounding:
        # apply_land_use / Settlement._rounded_pond + settlements.md 'Dike-pond water'.
        _dponds = M.get("dikeponds")
        _n_dp = len(_dponds) if _dponds else 0
        _spill = sum(1 for d in (_dponds or []) if any(not point_in_poly(wx, wy, d["parcel"]) for wx, wy in d["water"]))
        check(
            "dikepond_water_within_banks",
            _n_dp >= 12 and _spill == 0,
            f"a mulberry-dike fish pond's water must sit INSIDE its green mulberry banks, not fill the parcel to its edge (recorded ponds {_n_dp}, want >=12; ponds whose water spills past the parcel {_spill}, want 0) - the water 'running off the green interior' is the pre-fix full-parcel fill",
        )
        _min_wv = min((len(d["water"]) for d in (_dponds or [])), default=0)
        check(
            "dikepond_corners_rounded",
            _n_dp >= 12 and _min_wv >= 10,
            f"a dug fish pond erodes to ROUNDED corners, not sharp right angles - the recorded pond water polygons must carry the rounding (min sampled vertices {_min_wv}, want >=10 across {_n_dp} ponds); a 4-vertex quad is the pre-fix sharp-cornered parcel",
        )

        # EVERY DIKE-POND IS FED AND DRAINED (GM 2026-07-23): a pond on a slope is plumbed inlet-HIGH,
        # outlet-LOW so water flows DOWNHILL through it - so each pond carries TWO sluices: a FEEDER from an
        # uphill point on the creek network (water runs down INTO the pond) and a separate DRAIN to a downhill
        # point (water runs down OUT of it), and the two must not overlap. Teeth (in the down-slope frame):
        # every pond must have a feed AND a drain sluice on its water; a feed's network-end must sit UPHILL of
        # its pond-end and a drain's DOWNHILL; every sluice's far end must reach a channel or another pond (a
        # real connection); and a pond's feed + drain segments must not cross. Sealed / one-way / uphill-
        # draining / crossing ponds all fire. Grounding: apply_land_use + settlements.md 'Dike-pond sluices'.
        _sl = M.get("dikepond_sluices", [])
        _dpw = [d["water"] for d in (_dponds or [])]
        _chs = [c["poly"] for c in M.get("field_ditches", [])]
        _fdd = math.radians(float(meta.get("down_deg", 90)))
        _fdx, _fdy = math.cos(_fdd), math.sin(_fdd)

        def _fdfall(q: Any) -> float:
            return float(q[0] * _fdx + q[1] * _fdy)

        def _reaches(pt: Any) -> bool:
            on_ch = any(seg_dist(pt[0], pt[1], cp[k], cp[k + 1]) < 6 for cp in _chs for k in range(len(cp) - 1))
            in_pd = any(point_in_poly(pt[0], pt[1], w) or min(seg_dist(pt[0], pt[1], w[k], w[(k + 1) % len(w)]) for k in range(len(w))) < 6 for w in _dpw)
            return on_ch or in_pd

        def _cross(a: Any, b: Any, c: Any, d: Any) -> bool:
            def _o(p: Any, q: Any, r: Any) -> float:
                return float((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))

            return (_o(a, b, c) > 0) != (_o(a, b, d) > 0) and (_o(c, d, a) > 0) != (_o(c, d, b) > 0)

        _fd_bad = 0
        for _dp in _dponds or []:
            _w = _dp["water"]
            _mine = [s for s in _sl if isinstance(s, dict) and min(seg_dist(s["a"][0], s["a"][1], _w[k], _w[(k + 1) % len(_w)]) for k in range(len(_w))) < 3.0]
            _feeds = [s for s in _mine if s.get("kind") == "feed"]
            _drains = [s for s in _mine if s.get("kind") == "drain"]
            if (
                not _feeds  # sealed / one-way: no feeder ...
                or not _drains  # ... or no drain
                or any(_fdfall(s["b"]) >= _fdfall(s["a"]) for s in _feeds)  # a feed's network-end must be UPHILL
                or any(_fdfall(s["b"]) <= _fdfall(s["a"]) for s in _drains)  # a drain's network-end must be DOWNHILL
                or any(not _reaches(s["b"]) for s in _mine)  # every sluice's far end reaches the network
                or any(_cross(f["a"], f["b"], d["a"], d["b"]) for f in _feeds for d in _drains)  # feed + drain must not overlap
            ):
                _fd_bad += 1
        check(
            "dikeponds_fed_and_drained",
            _n_dp >= 12 and len(_sl) >= 1.5 * _n_dp and _fd_bad == 0,
            f"a mulberry-dike fish pond must be FED from an uphill sluice AND DRAINED by a downhill one (not overlapping), so water flows downhill through it - {_fd_bad} pond(s) are sealed, one-way, wrongly-angled or have crossing connectors (recorded sluices {len(_sl)} for {_n_dp} ponds)",
        )

        # MULBERRY BUSHES KEEP CLEAR OF THE CANALS (GM 2026-07-23): the bank planting is coppiced BUSHES
        # standing ON the dike - not canopy trees that could arch over water - and the ring canal + laterals
        # are open dug water at the dike toe. A channel centerline running INSIDE a pond's planted bank means
        # bushes drawn in the canal, a physical impossibility. Teeth: every pond records its `bank` outline
        # (the planted band's outer edge, which the crown dots fill - so "no canal inside a bank" bounds the
        # bushes without recording thousands of decorative dots); densified field-ditch centerlines must not
        # penetrate more than 2 px into any bank (edge-GRAZING is FINE - the canal genuinely runs along the
        # dike toe, earth meets water there, and the mosaic-bent laterals graze parcel edges by up to
        # ~1.5 px, which is the toe line clipping the bank rim, not a canal through the dike; the pre-fix
        # +5 px bank expansion scored penetrations to 6.5 px and fired). A pond missing its `bank` record fires too, so silently
        # dropping the record cannot disable the check. Placement side: _mulberry_rows filters crown dots
        # against channel segments at r + 3 px clearance. Grounding: settlements.md 'Polder fourth pass'.
        _mb_missing = sum(1 for d in (_dponds or []) if "bank" not in d)
        _mb_banks = [d["bank"] for d in (_dponds or []) if "bank" in d]
        _mb_boxes = [(min(q[0] for q in b), min(q[1] for q in b), max(q[0] for q in b), max(q[1] for q in b)) for b in _mb_banks]
        _mb_bad = 0
        for _mb_cp in _chs:
            for _mb_k in range(len(_mb_cp) - 1):
                _mb_a, _mb_b = _mb_cp[_mb_k], _mb_cp[_mb_k + 1]
                _mb_steps = max(1, int(math.hypot(_mb_b[0] - _mb_a[0], _mb_b[1] - _mb_a[1]) / 6))
                for _mb_t in range(_mb_steps + 1):
                    _mb_x = _mb_a[0] + (_mb_b[0] - _mb_a[0]) * _mb_t / _mb_steps
                    _mb_y = _mb_a[1] + (_mb_b[1] - _mb_a[1]) * _mb_t / _mb_steps
                    for _mb_poly, _mb_box in zip(_mb_banks, _mb_boxes, strict=True):
                        if not (_mb_box[0] - 2 <= _mb_x <= _mb_box[2] + 2 and _mb_box[1] - 2 <= _mb_y <= _mb_box[3] + 2):
                            continue
                        if point_in_poly(_mb_x, _mb_y, _mb_poly) and min(seg_dist(_mb_x, _mb_y, _mb_poly[_mb_j], _mb_poly[(_mb_j + 1) % len(_mb_poly)]) for _mb_j in range(len(_mb_poly))) > 2.0:
                            _mb_bad += 1
        check(
            "mulberry_banks_clear_of_channels",
            _n_dp >= 12 and _mb_missing == 0 and _mb_bad == 0,
            f"mulberry bushes are coppiced shrubs ON the dike and cannot stand in the canal at its toe - no channel centerline may run inside a pond's planted bank ({_mb_bad} channel point(s) penetrate a bank; {_mb_missing} pond(s) missing the `bank` record that gives this check teeth, of {_n_dp} recorded ponds)",
        )
    return _kept(
        locals(),
        (
            '_chs',
            '_cross',
            '_dp',
            '_dponds',
            '_dpw',
            '_drains',
            '_fd_bad',
            '_fdd',
            '_fdfall',
            '_fdx',
            '_fdy',
            '_feeds',
            '_mb_a',
            '_mb_b',
            '_mb_bad',
            '_mb_banks',
            '_mb_box',
            '_mb_boxes',
            '_mb_cp',
            '_mb_j',
            '_mb_k',
            '_mb_missing',
            '_mb_poly',
            '_mb_steps',
            '_mb_t',
            '_mb_x',
            '_mb_y',
            '_min_wv',
            '_mine',
            '_n_dp',
            '_reaches',
            '_sl',
            '_spill',
            '_w',
            'b',
            'c',
            'd',
            'dp_fill',
            'f',
            'k',
            'pf',
            'pond_rec',
            'q',
            'r',
            's',
            'wx',
            'wy',
        ),
    )


# A polder's PERIMETER DIKE is an irregular hand-piled EARTHWORK, not a ruled line (GM 2026-07-22,
# researched: the wei-tian / dike-pond dike was dredged pond-mud heaped and packed, planted and
# breach-repaired, and the OUTER dike followed the natural water edge - the 'fish-scale polder' 鱼鳞圩
# form; the dead-straight uniform-width rectangle is a post-1949 industrial shape). So a polder /
# dike-pond map must record an `s.perimeter_dike` band (M['dikes']) whose width VARIES along its length
# (w_max >= ~1.4x w_min) - a reverted uniform-width stroke, or no dike at all, fires. Grounding:
# settlements.md 'Perimeter dike'.


def _seg_0581__polder_dike_is_earthwork(
    *,
    M: Any = _UNBOUND,
    _a: Any = _UNBOUND,
    _b: Any = _UNBOUND,
    _dgaps: Any = _UNBOUND,
    _dike_densify: Any = _UNBOUND,
    _dol: Any = _UNBOUND,
    _fl: Any = _UNBOUND,
    _flvals: Any = _UNBOUND,
    _i: Any = _UNBOUND,
    _inband: Any = _UNBOUND,
    _k: Any = _UNBOUND,
    _leaves: Any = _UNBOUND,
    _ln: Any = _UNBOUND,
    _ring: Any = _UNBOUND,
    _stray: Any = _UNBOUND,
    _ungapped: Any = _UNBOUND,
    _waters: Any = _UNBOUND,
    _wax: Any = _UNBOUND,
    _way: Any = _UNBOUND,
    _wdd: Any = _UNBOUND,
    _wdev: Any = _UNBOUND,
    _wfrac: Any = _UNBOUND,
    _wi: Any = _UNBOUND,
    _wl: Any = _UNBOUND,
    _woff: Any = _UNBOUND,
    _wol: Any = _UNBOUND,
    _wox: Any = _UNBOUND,
    _woy: Any = _UNBOUND,
    _wpoly: Any = _UNBOUND,
    _wtot: Any = _UNBOUND,
    band: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    c: Any = _UNBOUND,
    ch: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dk: Any = _UNBOUND,
    dks: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    fx: Any = _UNBOUND,
    fy: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    h: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    i: Any = _UNBOUND,
    in_dike: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    on_dike: Any = _UNBOUND,
    out: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    rp: Any = _UNBOUND,
    s: Any = _UNBOUND,
    step: Any = _UNBOUND,
    sx: Any = _UNBOUND,
    sy: Any = _UNBOUND,
    wmn: Any = _UNBOUND,
    wmx: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 581 (polder_channels_clear_of_dike, polder_dike_gapped_at_sluices, polder_dike_is_earthwork, polder_edges_wander, polder_floor_is_ring_interior, structures_clear_of_dike) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("field_archetype") in ("polder_grid", "mulberry_dike_fishpond"):
        dks = M.get("dikes") or []
        dk = dks[0] if dks else None
        wmn, wmx = (dk.get("w_min", 0.0), dk.get("w_max", 0.0)) if dk else (0.0, 0.0)
        check(
            "polder_dike_is_earthwork",
            bool(dk) and wmx >= 1.4 * max(1.0, wmn),
            f"a polder's perimeter dike must be an irregular earthwork band of VARYING width (drawn present: {bool(dk)}; width {wmn:.0f}-{wmx:.0f} px, want max >= 1.4x min) - a uniform-width or missing dike reads as a post-1949 ruled rectangle, not a hand-piled fish-scale polder",
        )

        # THE DIKES WANDER - NOT A MACHINE-PERFECT RECTANGLE (GM 2026-07-22, issue 4): a hand-dug wei-tian dike
        # followed the old water edge, so it runs at a slight ANGLE and gently CHANGES direction with the ground
        # (the 'fish-scale polder' 鱼鳞圩 read); a dead-straight axis-aligned block is the post-1949 land-
        # consolidation shape. Teeth: in the down-slope frame, most of the field OUTLINE must run OFF both axes -
        # a pure rectangle scores 0 (every edge axis-aligned) and fires, while the edge-wander block clears the
        # floor comfortably. Grounding: build_polder 'EDGE WANDER' + settlements.md 'Polder edge wander'.
        _wdd = math.radians(meta.get("down_deg", 90))
        _wox, _woy = math.cos(_wdd), math.sin(_wdd)
        _wol = fields[0]["outline"] if fields else []
        _wtot = _woff = 0.0
        for _wi in range(len(_wol) - 1):
            _wax, _way = _wol[_wi + 1][0] - _wol[_wi][0], _wol[_wi + 1][1] - _wol[_wi][1]
            _wl = math.hypot(_wax, _way)
            if _wl < 1:
                continue
            _wdev = min(abs(_wax * _wox + _way * _woy), abs(_wax * _woy - _way * _wox)) / _wl  # 0 = on an axis
            _wtot += _wl
            if _wdev > 0.05:  # > ~3 deg off the nearer axis
                _woff += _wl
        _wfrac = _woff / _wtot if _wtot else 0.0
        check(
            "polder_edges_wander",
            bool(fields) and _wfrac >= 0.30,
            f"a polder's dikes must WANDER, not run axis-perfect - only {_wfrac:.0%} of the field outline runs off-axis (want >=30%); a dead-straight rectangle is the post-1949 consolidation shape, not a hand-dug fish-scale polder",
        )

        # THE GREEN FLOOR IS THE RING-CANAL INTERIOR, not the dike-boundary envelope (GM 2026-07-22): the
        # greenery must be bounded by the OUTERMOST irrigated channels (the feeder/drain/toe ring), so it
        # follows the wavering ring instead of a separate envelope rectangle that drifts in and out of it.
        # Teeth: every recorded field-floor vertex must lie within ~8 px of a ring channel centerline; the
        # pre-fix envelope floor sat ~9-22 px out at the dike boundary and fires. Grounding: build_polder's
        # `floor` (the concatenated ring sides) + comb_base_fill + settlements.md 'Polder edge wander'.
        _ring = [d["poly"] for d in M.get("field_ditches", []) if d.get("seg") in ("feeder", "drain", "e_toe", "w_toe")]
        _flvals = list(M.get("comb_floors", {}).values())
        if _ring and _flvals:
            _fl = _flvals[0]
            _stray = [(round(fx), round(fy)) for fx, fy in _fl if min(seg_dist(fx, fy, rp[i], rp[i + 1]) for rp in _ring for i in range(len(rp) - 1)) > 8]
            check(
                "polder_floor_is_ring_interior",
                not _stray,
                f"the polder's green field floor must be the INTERIOR of the ring canal (bounded by the outermost channels), but {len(_stray)} floor vertex/vertices sit >8 px off the ring at {_stray[:3]} - a floor drawn to the dike-boundary envelope drifts in and out of the wavering ring",
            )

        # THE RING CANAL RUNS ON THE INNER TOE, CLEAR OF THE DIKE (GM 2026-07-22, researched: the trunk
        # irrigation/drainage canal rings the block on the INSIDE toe of the perimeter dike, on the field
        # side - "一河围田 / one river surrounds the field"; outside the dike is the wild water it holds back,
        # so no channel runs out there, and water crosses the dike ONLY at gated sluices at the inlet +
        # outfall). So an irrigation channel buried in the dike earthwork is wrong. Teeth: count field-ditch
        # vertices falling inside the recorded dike band; a couple (the inlet/outfall sluice crossings) are
        # fine, but a trunk running along inside the dike (the old s=+-12 feeder, ~36 pts in the band) fires.
        if dk:
            band = dk["outline"]
            in_dike = sum(1 for ch in M.get("field_ditches", []) for x, y in ch["poly"] if point_in_poly(x, y, band))
            check(
                "polder_channels_clear_of_dike",
                in_dike <= 4,
                f"{in_dike} irrigation-channel point(s) run through the dike earthwork (want <= 4, the inlet/outfall sluice crossings) - the polder RING CANAL runs on the INNER TOE of the dike (field side), not buried in the dike body; water crosses the dike only at the sluices",
            )

            # WATER CROSSES THE DIKE ONLY THROUGH A DUG GAP (GM 2026-07-22, issue 1): the inlet + outfall sluices
            # pass THROUGH a notch cut in the earthwork, not OVER the top of the unbroken bank (which read as the
            # water running uphill onto the dike and back down). Teeth: a THROUGH-CROSSER - a water line with a
            # densified point inside the dike band AND a vertex outside the field outline (so it genuinely runs
            # from the field, through the dike, to the far / off-map side) - must have a recorded gap within
            # ~26 px of where it enters the band. The pre-fix dike recorded NO gaps, so every crosser fires. The
            # incidental ring-canal clipping the inner toe at a concave bend is NOT a crosser (it never leaves the
            # field), so it is not required to have a gap. Grounding: perimeter_dike gaps + settlements.md.
            _dgaps = dk.get("gaps", [])
            _dol = fields[0]["outline"] if fields else []

            def _dike_densify(poly: Any, step: float = 4.0) -> list[tuple[float, float]]:
                out: list[tuple[float, float]] = []
                for _i in range(len(poly) - 1):
                    _a, _b = poly[_i], poly[_i + 1]
                    _ln = math.hypot(_b[0] - _a[0], _b[1] - _a[1])
                    _steps = max(1, int(_ln / step))
                    for _k in range(_steps):
                        out.append((_a[0] + (_b[0] - _a[0]) * _k / _steps, _a[1] + (_b[1] - _a[1]) * _k / _steps))
                if poly:
                    out.append((poly[-1][0], poly[-1][1]))
                return out

            _waters = [c["poly"] for c in M.get("field_ditches", [])] + [s["poly"] for s in M.get("streams", [])] + [c["poly"] for c in M.get("channels", [])]
            _ungapped: list[tuple[int, int]] = []  # type: ignore[no-redef]
            for _wpoly in _waters:
                _inband = [(x, y) for x, y in _dike_densify(_wpoly) if point_in_poly(x, y, band)]
                _leaves = bool(_dol) and any(not point_in_poly(px, py, _dol) for px, py in _wpoly)
                if _inband and _leaves and not any(math.hypot(bx - gx, by - gy) <= 26 for bx, by in _inband for gx, gy in _dgaps):
                    _ungapped.append((round(_inband[0][0]), round(_inband[0][1])))
            check(
                "polder_dike_gapped_at_sluices",
                not _ungapped,
                f"{len(_ungapped)} channel(s) cross the dike with no dug gap at {_ungapped[:4]} - a polder's inlet/outfall sluice passes THROUGH a notch cut in the earthwork bank, not over the top of it; every through-crossing needs a recorded dike gap",
            )

            # STRUCTURES + WINDBREAK KEEP OFF THE DIKE (GM 2026-07-22): the dike is a raised earthwork bank,
            # not building ground, so no farmhouse footprint and no windbreak grove clump may sit ON it (the
            # bank carries only its own soil-binding trees). perimeter_dike registers the band as a placement
            # keep-out; this verifies it. A house corner or a grove clump center inside the dike band fires.
            on_dike = []
            for h in M.get("houses", []):
                if h.get("on_dike"):
                    continue  # a dike_top_houses house LIVES on the bank (settlement_form 'dike_top') - dike_top_houses_on_the_dike verifies it instead
                hw, hh = h.get("w", 40) / 2, h.get("h", 26) / 2
                if any(point_in_poly(h["x"] + sx * hw, h["y"] + sy * hh, band) for sx in (-1, 1) for sy in (-1, 1)):
                    on_dike.append(("house", round(h["x"]), round(h["y"])))
            for g in M.get("village_groves", []):
                on_dike += [("grove", round(cx), round(cy)) for cx, cy in g.get("clumps", []) if point_in_poly(cx, cy, band)]
            check(
                "structures_clear_of_dike",
                not on_dike,
                f"structure(s)/windbreak clump(s) sitting ON the perimeter dike earthwork: {on_dike[:4]} - the dike is a raised bank, not building ground; houses and the windbreak keep off it",
            )
    return _kept(
        locals(),
        (
            '_dgaps',
            '_dike_densify',
            '_dol',
            '_fl',
            '_flvals',
            '_inband',
            '_leaves',
            '_ring',
            '_stray',
            '_ungapped',
            '_waters',
            '_wax',
            '_way',
            '_wdd',
            '_wdev',
            '_wfrac',
            '_wi',
            '_wl',
            '_woff',
            '_wol',
            '_wox',
            '_woy',
            '_wpoly',
            '_wtot',
            'band',
            'bx',
            'by',
            'c',
            'ch',
            'cx',
            'cy',
            'd',
            'dk',
            'dks',
            'fx',
            'fy',
            'g',
            'gx',
            'gy',
            'h',
            'hh',
            'hw',
            'i',
            'in_dike',
            'on_dike',
            'out',
            'px',
            'py',
            'rp',
            's',
            'sx',
            'sy',
            'wmn',
            'wmx',
            'x',
            'y',
        ),
    )


# DIKE-TOP HOUSES REALLY SIT ON THE DIKE (GM 2026-07-24, settlements.md 'Polder siting Q&A'): a house
# tagged `on_dike` (placed by dike_top_houses, settlement_form 'dike_top') is exempt from
# structures_clear_of_dike - so the tag must not be a free pass. Every tagged house's center must lie
# ON the recorded dike band (or within the small platform slack - the widened-crest house pad bulges
# the band a touch). A tagged house floating off the bank, or tagged houses on a map with no dike at
# all, fires.


def _seg_0582___dtag(*, M: Any = _UNBOUND, h: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 582 (_dtag, h) - body verbatim from the legacy gate() (feature 022)."""
    _dtag = [h for h in M.get("houses", []) if h.get("on_dike")]
    return _kept(locals(), ('_dtag', 'h'))


def _seg_0583__dike_top_houses_on_the_dike(
    *, M: Any = _UNBOUND, _dbands: Any = _UNBOUND, _doff: Any = _UNBOUND, _dtag: Any = _UNBOUND, b: Any = _UNBOUND, check: Any = _UNBOUND, dk: Any = _UNBOUND, h: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 583 (dike_top_houses_on_the_dike) - body verbatim from the legacy gate() (feature 022)."""
    if _dtag:
        _dbands = [dk["outline"] for dk in M.get("dikes", []) if dk.get("outline")]
        _doff = [(round(h["x"]), round(h["y"])) for h in _dtag if not any(poly_dist(h["x"], h["y"], b) <= 14 for b in _dbands)]
        check(
            "dike_top_houses_on_the_dike",
            not _doff,
            f"house(s) tagged on_dike but not ON the dike band: {_doff[:4]} - the on_dike tag exempts a house from structures_clear_of_dike, so it is only honest for a house actually seated on the crest (dike_top_houses)",
        )
    return _kept(locals(), ('_dbands', '_doff', 'b', 'dk', 'h'))


# THE WATERWARD FLANKS ARE WET (GM 2026-07-24, settlements.md 'Polder siting Q&A'): outside a polder's
# dike is the FLUCTUATING WATER it was reclaimed from - lake, creek, reed marsh, mudflat - except on a
# landward flank where the polder abuts the natural shore (the margin-polder case; reclamation advanced
# FROM the shore). A map declares its water-facing flanks in meta.waterward (compass letters, frame
# axes); each declared flank must then actually READ wet - sampled just outside the dike band's extreme
# on that side, most points must land in recorded wet cover (a waterside/toe marsh poly or the header
# pond). Undeclared maps skip (a non-polder map has no dike to face water).


def _seg_0584___ww(*, c: Any = _UNBOUND, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 584 (_ww, c) - body verbatim from the legacy gate() (feature 022)."""
    _ww = [str(c) for c in (meta.get("waterward") or [])]
    return _kept(locals(), ('_ww', 'c'))


def _seg_0585___dks_all(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 585 (_dks_all) - body verbatim from the legacy gate() (feature 022)."""
    _dks_all = M.get("dikes") or []
    return _kept(locals(), ('_dks_all',))


def _seg_0586__polder_waterward_flanks_wet(
    *,
    M: Any = _UNBOUND,
    _K: Any = _UNBOUND,
    _bpts: Any = _UNBOUND,
    _bx0: Any = _UNBOUND,
    _bx1: Any = _UNBOUND,
    _by0: Any = _UNBOUND,
    _by1: Any = _UNBOUND,
    _dks_all: Any = _UNBOUND,
    _dryf: Any = _UNBOUND,
    _fl: Any = _UNBOUND,
    _fx: Any = _UNBOUND,
    _fy: Any = _UNBOUND,
    _hi: Any = _UNBOUND,
    _is_wet: Any = _UNBOUND,
    _lo: Any = _UNBOUND,
    _pnd: Any = _UNBOUND,
    _samples: Any = _UNBOUND,
    _wetc: Any = _UNBOUND,
    _wetp: Any = _UNBOUND,
    _ww: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dk: Any = _UNBOUND,
    k: Any = _UNBOUND,
    m: Any = _UNBOUND,
    p: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    wp: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 586 (polder_waterward_flanks_wet) - body verbatim from the legacy gate() (feature 022)."""
    if _ww and _dks_all:
        _bpts = [p for dk in _dks_all for p in dk.get("outline", [])]
        _bx0, _bx1 = min(p[0] for p in _bpts), max(p[0] for p in _bpts)
        _by0, _by1 = min(p[1] for p in _bpts), max(p[1] for p in _bpts)
        _wetp = [m["poly"] for m in M.get("marshes", []) if m.get("role") in ("waterside", "toe") and m.get("poly")]
        _pnd = M.get("pond")

        def _is_wet(px: float, py: float) -> bool:
            if any(point_in_poly(px, py, wp) for wp in _wetp):
                return True
            if not _pnd:
                return False
            return bool(((px - _pnd[0]) / max(1e-9, _pnd[2])) ** 2 + ((py - _pnd[1]) / max(1e-9, _pnd[3])) ** 2 <= 1.0)

        _dryf = []
        for _fl in _ww:
            _K = 20
            if _fl in ("W", "E"):
                _fx = (_bx0 - 28) if _fl == "W" else (_bx1 + 28)
                _lo, _hi = _by0 + 0.15 * (_by1 - _by0), _by1 - 0.15 * (_by1 - _by0)
                _samples = [(_fx, _lo + (_hi - _lo) * k / (_K - 1)) for k in range(_K)]
            else:
                _fy = (_by0 - 28) if _fl == "N" else (_by1 + 28)
                _lo, _hi = _bx0 + 0.15 * (_bx1 - _bx0), _bx1 - 0.15 * (_bx1 - _bx0)
                _samples = [(_lo + (_hi - _lo) * k / (_K - 1), _fy) for k in range(_K)]
            _wetc = sum(1 for px, py in _samples if _is_wet(px, py))
            if _wetc < 0.7 * _K:
                _dryf.append((_fl, _wetc))
        check(
            "polder_waterward_flanks_wet",
            not _dryf,
            f"declared waterward flank(s) read DRY outside the dike: {_dryf} (flank, wet samples of 20; want >=14) - outside a polder dike on a water-facing flank is the fluctuating wet wild it holds back (waterside marsh / open water), not the same dry scrub as the landward shore",
        )
    return _kept(
        locals(), ('_K', '_bpts', '_bx0', '_bx1', '_by0', '_by1', '_dryf', '_fl', '_fx', '_fy', '_hi', '_is_wet', '_lo', '_pnd', '_samples', '_wetc', '_wetp', 'dk', 'k', 'm', 'p', 'px', 'py')
    )


# A polder's PARCEL fabric must VARY (researched 2026-07-21; grounding in build_polder's docstring).
# The surveyed chessboard was the CANAL grid; the parcels inside were a private-tenure patchwork
# (Buck 1929-33: mean parcel ~1 mu, several scattered per farm; dike-ponds accreted 挖塘培基,
# household by household). Identical uniform cells are the 20th-century consolidation look (hojo
# seibi 30x100m), so a block of them - the original Kuwabata/Enokida render - must fire. Applies to
# both polder-geometry archetypes; measured from the manifest's per-plot [along, cross] spans, and a
# polder manifest that records NO parcel geometry fails rather than passes by omission.


def _seg_0587__polder_parcels_vary(
    *,
    M: Any = _UNBOUND,
    areas: Any = _UNBOUND,
    asps: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dp: Any = _UNBOUND,
    fdits: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    i: Any = _UNBOUND,
    mean_a: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pl: Any = _UNBOUND,
    pv_cv: Any = _UNBOUND,
    pv_ob: Any = _UNBOUND,
    pv_ok: Any = _UNBOUND,
    reach: Any = _UNBOUND,
    ruled: Any = _UNBOUND,
    shaped: Any = _UNBOUND,
    sq_mean: Any = _UNBOUND,
    unfronted: Any = _UNBOUND,
    x: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 587 (polder_parcels_are_organic, polder_parcels_front_water, polder_parcels_vary) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("field_archetype") in ("polder_grid", "mulberry_dike_fishpond") and fields:
        pl = fields[0].get("plots") or []
        pv_cv = pv_ob = 0.0
        pv_ok = len(pl) >= 12
        if pv_ok:
            areas = [p[0] * p[1] for p in pl]
            mean_a = sum(areas) / len(areas)
            pv_cv = (sum((x - mean_a) ** 2 for x in areas) / len(areas)) ** 0.5 / max(1e-9, mean_a)
            asps = [max(p[0], p[1]) / max(1.0, min(p[0], p[1])) for p in pl]
            pv_ob = sum(1 for x in asps if x >= 1.45) / len(asps)
            pv_ok = pv_cv >= 0.18 and pv_ob >= 0.35
        check(
            "polder_parcels_vary",
            pv_ok,
            f"a polder's parcel fabric must be a patchwork, not identical cells - the survey grid was the CANALS, the parcels were private-tenure oblongs of varied size (area cv {pv_cv:.2f}, want >=0.18; oblong share {pv_ob:.0%}, want >=35%; n={len(pl)}, want >=12) - uniform squares read as 20th-century land consolidation",
        )

        # EVERY POLDER PARCEL FRONTS A DITCH (GM-flagged 2026-07-21: the original Kuwabata's ponds floated
        # with no water connection at all). The jingbang 泾浜 polder interior was a creek-and-ditch net in
        # which every basin fronted water (qualitatively well-attested; the exact spacing is a reasoned
        # reconstruction - see build_polder's docstring). Teeth: each parcel's centroid must sit within
        # ~0.62x its own longer span (+16 px corridor slack) of a recorded supply/drain ditch polyline.
        # Parcels recorded without centroids (the pre-fix format) count as NOT fronting - no passing by
        # omission.
        fdits = [d["poly"] for d in M.get("field_ditches", []) if d.get("role") in ("main", "lateral", "branch", "feed", "drain")]
        unfronted = 0
        for p in pl:
            if len(p) < 4:
                unfronted += 1
                continue
            reach = 0.62 * max(p[0], p[1]) + 16
            if not any(seg_dist(p[2], p[3], dp[i], dp[i + 1]) < reach for dp in fdits for i in range(len(dp) - 1)):
                unfronted += 1
        check(
            "polder_parcels_front_water",
            not pl or unfronted == 0,
            f"{unfronted}/{len(pl)} polder parcel(s) have no ditch frontage - a polder interior is a jingbang creek-and-ditch net where EVERY basin fronts a supply/drain ditch; a parcel out of reach of any ditch (or recorded without a centroid) has no water",
        )

        # HAND-PILED EARTHWORK IS NEVER RULED (GM 2026-07-24, looking at Enokida: "the lines themselves
        # appear perfectly straight and have sharp angles rather than looking like the kind of organically
        # grown shapes that you get when humans create such bunds by hand"). A farmer piling a rectangular
        # basin out of puddled mud INTENDS four straight sides and a right angle at each corner and gets
        # neither: a right angle in soft earth is the thinnest, least-supported point of the ridge, so it
        # slumps under its own weight and under every rain, and it is the one spot everyone cuts across
        # rather than walking to the point - the corner converges on a walked-and-slumped curve. The runs
        # between corners are paced and eyeballed, re-cut a little differently each time a holding is
        # split or re-plastered, so they wander by a foot or two over a hundred. The ruled, sharp-cornered
        # cell is the machine signature of 20th-century consolidation - the same anachronism
        # polder_parcels_vary guards at the fabric scale and polder_edges_wander at the block scale; this
        # is that rule at the scale of one parcel outline. Grounding: waterfields.organic_parcel.
        # TEETH: the recorded per-parcel [.., vertex count, count of still-square corners], measured on
        # two levels because the rule works on two levels. PER PARCEL, >=12 vertices: a ruled quad has
        # 4, and no amount of easing gets a genuinely hand-drawn outline down near that. ACROSS THE
        # FABRIC, a mean of <=2.5 square corners per parcel: corner reach is drawn from a wide spread
        # precisely so that SOME corners stay square (the one behind a neighbor's bund never gets
        # walked), so no per-parcel corner rule can be right - but a field where nothing has eased
        # scores the full 4.0, and both pool polders sit at ~1.4, so the threshold is clear of both.
        # A polder recording the pre-fix 4-element parcel format fails rather than passing by omission.
        shaped = [p for p in pl if len(p) >= 6]
        ruled = [p for p in shaped if p[4] < 12]
        sq_mean = sum(p[5] for p in shaped) / len(shaped) if shaped else 4.0
        check(
            "polder_parcels_are_organic",
            bool(pl) and len(shaped) == len(pl) and not ruled and sq_mean <= 2.5,
            f"{len(pl) - len(shaped)} parcel(s) record no outline shape, {len(ruled)} are drawn as ruled few-vertex quads (want >=12 vertices each), and corners ease on too few of them (mean {sq_mean:.2f} still-square corners per parcel, want <=2.5 of 4; n={len(pl)}) - a bund is hand-piled mud whose corners slump and get walked round and whose runs are paced by eye, so a fabric of dead-straight sides meeting at sharp angles reads as machine-cut land consolidation, not as earth",
        )
    return _kept(locals(), ('areas', 'asps', 'd', 'dp', 'fdits', 'i', 'mean_a', 'p', 'pl', 'pv_cv', 'pv_ob', 'pv_ok', 'reach', 'ruled', 'shaped', 'sq_mean', 'unfronted', 'x'))


# A RIBBON-VALLEY field (feature 005 US4) is LONG and NARROW - a thin strip strung down a confined valley -
# so its extent ALONG the fall is much greater than its extent ACROSS it. That aspect is the archetype's
# teeth: a ribbon reads as a winding valley strip, not a broad fan/block.


def _seg_0588__ribbon_is_long_and_narrow(
    *,
    along_span: Any = _UNBOUND,
    along_vals: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cross_span: Any = _UNBOUND,
    cross_vals: Any = _UNBOUND,
    dd: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    rdx: Any = _UNBOUND,
    rdy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 588 (ribbon_is_long_and_narrow) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("field_archetype") == "ribbon_valley" and fields:
        dd = meta.get("down_deg", 90)
        rdx, rdy = math.cos(math.radians(dd)), math.sin(math.radians(dd))
        ol = fields[0]["outline"]
        along_vals = [px * rdx + py * rdy for px, py in ol]
        cross_vals = [px * -rdy + py * rdx for px, py in ol]
        along_span = max(along_vals) - min(along_vals)
        cross_span = max(1.0, max(cross_vals) - min(cross_vals))
        check(
            "ribbon_is_long_and_narrow",
            along_span >= 2.0 * cross_span,
            f"a ribbon_valley field must run far along the fall relative to its width (along {along_span:.0f} vs across {cross_span:.0f}, want >=2x) - the defining narrow-valley strip",
        )
    return _kept(locals(), ('along_span', 'along_vals', 'cross_span', 'cross_vals', 'dd', 'ol', 'px', 'py', 'rdx', 'rdy'))


# SOFT ADVISORY (default-on; a map opts out with meta(crop_advisory=False)): a single feature that could
# be moved to free a significantly tighter crop. NOT a failure - it never enters `fails` or gates the map;
# it just prints a hint. (Unlike a hard invariant, e.g. houses-clear-of-moats, this is a default we accept.)


def _seg_0589__adv(*, M: Any = _UNBOUND, adv: Any = _UNBOUND, meta: Any = _UNBOUND, verbose: Any = _UNBOUND, who: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 589 (adv, who) - body verbatim from the legacy gate() (feature 022)."""
    if meta.get("crop_advisory", True):
        for adv in crop_relocatable_singletons(M):
            if verbose:
                who = f"the {adv['kind']} at {adv['at']} (a {adv['members']}-feature group, moved as one unit)" if adv.get("members", 1) > 1 else f"the {adv['kind']} at {adv['at']} alone"
                print(
                    f"ADVISORY crop_could_tighten  -> {who} holds the "
                    f"{adv['edge']} crop edge out by ~{adv['shrink']}px; empty space near {adv['landing']} "
                    f"could take it, cropping the image significantly smaller (soft hint - move it + re-crop, "
                    f"or set meta(crop_advisory=False) to silence)"
                )
    return _kept(locals(), ('adv', 'who'))


# ---- the waiver hatch audits itself (GM 2026-07-27; the "why" is at WAIVER_MIN_REASON) ------
# Runs LAST, because it can only judge the waivers once every check has had its chance to fire.


def _seg_0590___wv_thin(*, _waivers: Any = _UNBOUND, k: Any = _UNBOUND, v: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 590 (_wv_thin, k, v) - body verbatim from the legacy gate() (feature 022)."""
    _wv_thin = sorted(k for k, v in _waivers.items() if not isinstance(v, str) or len(v.strip()) < WAIVER_MIN_REASON)
    return _kept(locals(), ('_wv_thin', 'k', 'v'))


def _seg_0591__waivers_are_documented(*, _wv_thin: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 591 (waivers_are_documented) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "waivers_are_documented",
        not _wv_thin,
        f"waiver(s) with no real explanation: {_wv_thin} - a waiver's value is the REASON this particular place "
        f"overrides the rule ({WAIVER_MIN_REASON}+ chars of it), and it is the only record that the map broke the "
        f"rule on purpose. Write the history ('the Emperor lies southeast, so the samurai quarter...'), not 'by design'",
    )
    return _kept(locals(), ())


def _seg_0592___wv_stale(*, _waived: Any = _UNBOUND, _waivers: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 592 (_wv_stale) - body verbatim from the legacy gate() (feature 022)."""
    _wv_stale = sorted(set(_waivers) - set(_waived) - WAIVER_META_CHECKS)
    return _kept(locals(), ('_wv_stale',))


def _seg_0593__waivers_are_live(*, _ran: Any = _UNBOUND, _wv_stale: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 593 (waivers_are_live) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "waivers_are_live",
        not _wv_stale,
        f"stale waiver(s): {_wv_stale} - each names a check that did NOT fail on this map (it now passes, this "
        f"scale never runs it, or the name is a typo/renamed). Delete it: a waiver kept past the defect it "
        f"excused is how a map ends up exempt from rules nobody remembers it was breaking. "
        f"Checks that ran: {len(_ran)}",
    )
    return _kept(locals(), ())


def _seg_0594__k_3(*, _waived: Any = _UNBOUND, fails: Any = _UNBOUND, k: Any = _UNBOUND, v: Any = _UNBOUND, verbose: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 594 (k, v) - body verbatim from the legacy gate() (feature 022)."""
    if verbose:
        if _waived:
            print("\n" + "\n".join(f"WAIVED {k}: {v}" for k, v in sorted(_waived.items())))
        print(f"\n{len(fails)} failing check(s): {fails}" if fails else "\nALL CHECKS PASSED")
    return _kept(locals(), ('k', 'v'))
