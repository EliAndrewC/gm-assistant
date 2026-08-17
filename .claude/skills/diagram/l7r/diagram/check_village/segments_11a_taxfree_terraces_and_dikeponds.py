"""Gate segments (taxfree terraces and dikeponds; keys 0564-0580) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import seg_in_ellipse_core

from .common_01_geometry import point_in_poly, poly_area, poly_dist, pt_to_rect, seg_closest, seg_dist
from .common_02_overlap_policy import in_ellipse
from .common_03_capacity import _UNBOUND, _kept

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
