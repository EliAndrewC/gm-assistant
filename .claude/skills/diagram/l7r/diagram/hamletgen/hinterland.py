"""STAGE 7: the ground between everything - open-ground scan, woodland, windbreak.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

from l7r.diagram.settlement import Settlement, point_in_poly, seg_dist
from l7r.diagram.sitegen.geom import crop_polys

from .consts import Poly, Pt
from .plan import SitePlan

# ---- STAGE 7: the ground between everything ------------------------------------------------------


def stage_hinterland(s: Settlement, plan: SitePlan) -> None:
    """The non-arable ground: reed marsh at the wet toe, cut-over scrub everywhere else.

    One engine call, because the engine already knows the doctrine (China-first: the south-China rice
    hills were stripped for fuel and timber over centuries, so the DOMINANT cover past the fields is
    scrub, not forest). It runs after the structures so the scatter skips them, and before the woods
    so the woodland patches draw on top of the scrub they stand in."""
    s.hinterland()


CROP_MARGIN = 48.0  # the one crop margin, shared by stage_frame's crop_to_content call and the
# predicted-kept-window math in open_ground_patches - two hardcoded 48s would drift

_COMMONS_FLOOR_FT = 120.0
"""The smallest square a woodland COMMONS may be drawn as, in feet.

Not a historical minimum - `research/fields.md` is clear that coppice lots were "whatever odd corner
the village spared", and there is no attested floor. This is a LEGIBILITY floor, and it exists
because the size-variance machinery above can compound its way under one: a per-map ladder scale
times a per-parcel band multiplier took Kashikawa to 103 ft. The number is our own recorded
judgment - when the first (shrink-only) size roll produced a 116 ft parcel on Mizuguchi the reading
was "a copse, not a commons", which is what made the roll two-sided - so 120 ft is just above the
size we have already said does not read. A settlement whose ground genuinely cannot hold one draws
FEWER parcels rather than smaller ones."""


def open_ground_patches(s: Settlement, plan: SitePlan, count: int, size: float = 250.0) -> list[Poly]:
    """Find `count` patches of ground still open enough for a managed woodland - by SCANNING.

    Woodland (coppice, bamboo, tung-oil - the "economic forest") is a few discrete patches on the
    higher, farther ground, set back from the sun-needing crops by the scrub between. Ikegami places
    three by hand. The script cannot hand-place, so it scans a coarse lattice over the canvas and
    scores each candidate square on the two things that actually decide the answer:

      - it must be CLEAR of the crops by a real margin, and clear by MORE on the crop's sunny side,
        because a canopy south of a field shades it (this mirrors `woodland_clear_of_crops`, whose
        set-back is bigger to the south for exactly that reason);
      - it must be clear of the settlement, its lanes, its grove and its water.

    Among the candidates that qualify it prefers the ones furthest from the crop and highest up the
    slope, and it keeps them apart from each other so three patches read as three woods rather than
    one ragged mass. This is the stage that most obviously could not be done by pinning coordinates:
    "where is there still room" is a question about the map as it stands at that moment."""
    dx, dy = plan.fall
    keep: list[tuple[float, float, float]] = []  # (x, y, radius) of everything to stay clear of
    for h in s.M.get("houses", []):
        keep.append((h["x"], h["y"], 150.0))
    for wl in s.M.get("wells", []):
        keep.append((wl["x"], wl["y"], 90.0))
    pond = s.M.get("pond")
    if pond:
        keep.append((pond[0], pond[1], max(pond[2], pond[3]) + 120.0))
    lanes: list[tuple[Poly, float]] = [(ln["pts"], 70.0) for ln in s.M.get("lanes", [])]
    # THE COPPICE IS A DISTINCT WOOD from the fengshui grove, and must not merge into it
    # (`woodland_clear_of_grove`, which measures to each grove CLUMP, not to the belt outline - so a
    # patch merely touching the belt's edge already fails). Both groves count: the windbreak belt
    # behind the cluster, and the copse scattered through the gaps among the houses, whose footprint
    # is the house bbox. The margin is generous because a clump's drawn canopy overhangs its
    # recorded radius, and because two woods that nearly touch read as one ragged mass anyway.
    # Kept clear by RECTANGLE, not by a circle around the bounding box. A belt is a long thin band
    # and a cluster is usually longer than it is deep, so a circle sized to the LONG side leaves the
    # short side hugely over-reserved while a circle sized any tighter under-covers the ends - and
    # the ends are exactly where a patch slips in and merges with the grove.
    keep_rects: list[tuple[float, float, float, float]] = [title_pocket(s, plan)]
    if plan.belt:
        keep_rects.append((min(p[0] for p in plan.belt) - 110.0, min(p[1] for p in plan.belt) - 110.0, max(p[0] for p in plan.belt) + 110.0, max(p[1] for p in plan.belt) + 110.0))
    hxs = [h["x"] for h in s.M.get("houses", [])]
    hys = [h["y"] for h in s.M.get("houses", [])]
    if hxs:  # the copse's ground, which is the house cloud
        keep_rects.append((min(hxs) - 110.0, min(hys) - 110.0, max(hxs) + 110.0, max(hys) + 110.0))
    streams: list[tuple[Poly, float]] = [(st["poly"], 60.0) for st in s.M.get("streams", [])]
    # ...AND THE MARSH IS NOT OPEN GROUND (settlement-review x3, 2026-08-16: the kept-window
    # confinement pushed parcels onto the wet toe - Inashiro seated one 100% inside the marsh
    # with zero crowns, Sawada 97%, Mizuguchi ~60%; the crown filter refuses wet ground, so a
    # wet seat renders as a claimed woodland with almost no trees). "Still open" is not "dry":
    # a candidate square must keep every sample point out of every recorded marsh poly.
    # `woodland_commons_on_dry_ground` gates the result.
    marshes: list[Poly] = [[(float(v[0]), float(v[1])) for v in mp.get("poly") or []] for mp in s.M.get("marshes", [])]
    marshes = [mp for mp in marshes if len(mp) >= 3]

    def _wet(x: float, y: float, half_: float) -> bool:
        return any(point_in_poly(x + ddx * half_, y + ddy * half_, mp) for mp in marshes for ddx in (-1.0, 0.0, 1.0) for ddy in (-1.0, 0.0, 1.0))

    crops: list[Poly] = [list(plan.envelope)] + [[(float(v[0]), float(v[1])) for v in d["poly"]] for d in s.M.get("dry_plots", [])]
    _hx = [h["x"] for h in s.M.get("houses", [])] or [plan.W / 2]
    _hy = [h["y"] for h in s.M.get("houses", [])] or [plan.H / 2]
    ccx, ccy = sum(_hx) / len(_hx), sum(_hy) / len(_hy)

    # THE PATCHES MUST NOT STRETCH THE FRAME. `crop_to_content` frames the map to its HARD features,
    # and a woodland patch is one - so a patch parked in a far corner of the working canvas drags the
    # crop out with it, leaving a band of empty scrub on one side and (worse) putting the map edge
    # beyond the reach of the drain brook, which then no longer runs off the frame. That is three
    # gate failures from one badly-sited wood: `crop_not_held_open_by_one_feature`,
    # `stream_runs_off_edge` and `stream_end_anchored`. So the scan is confined to the ground the
    # map already occupies, expanded by a margin - a coppice stands on the settlement's own high
    # ground, not a quarter mile out in nowhere.
    cbx0, cby0, cbx1, cby1 = content_box(s, plan, pad=210.0)
    step = 90.0

    # ...AND CONFINED TO THE PREDICTED KEPT WINDOW (known-open ledger 2026-08-16, Sawada: two of
    # three parcels wholly above the frame, the third half-cropped under the title; Kashikawa and
    # Mizuguchi the same shape). The commons never set the frame (crop_to_content: woods bleed at
    # the edge), so a parcel the keep-outs push past the future crop simply vanishes from the
    # sheet. The decision, over "let the crop admit them": the frame stays tight to the working
    # settlement - the documented reason commons do not set the frame at all - and a coppice is
    # walked-to-daily ground that belongs ON the sheet, so it is the coppice that moves. The
    # window is computed from the SAME source the crop will read (`_crop_boxes` -> hull + the
    # shared CROP_MARGIN), and at this stage it is final except for features that only GROW it -
    # so a parcel held inside it now is inside the kept view later.
    # `woodland_commons_within_the_frame` gates the result.
    _cb = s._crop_boxes(city=False)
    _cx = [v for b in _cb for v in (b[0], b[1])] or [0.0, plan.W]
    _cy = [v for b in _cb for v in (b[2], b[3])] or [0.0, plan.H]
    _fx0, _fy0 = max(0.0, min(_cx) - CROP_MARGIN), max(0.0, min(_cy) - CROP_MARGIN)
    _fx1, _fy1 = min(plan.W, max(_cx) + CROP_MARGIN), min(plan.H, max(_cy) + CROP_MARGIN)

    chosen: list[Poly] = []
    centers: list[tuple[float, float, float]] = []  # (x, y, this parcel's OWN exclusion radius - see the stride roll)
    # THE LADDER ITSELF IS ROLLED PER MAP (settlement-review x2, 2026-08-18). The shrink ladder's
    # rungs were the same four numbers on every map, so every tight composition fell to the SAME
    # bottom rung and produced the same wood: Kashikawa shipped a 121.7 ft stand with 18 crowns and
    # Sawada a 127.2 ft stand with 19 - two different hamlets, effectively one wood, and the
    # per-parcel size roll could not separate them because it only spans +/-15% of a rung they
    # SHARED. Scaling the whole ladder by a per-map factor moves the rungs themselves apart, so two
    # tight maps land on different sizes before the per-parcel roll even runs.
    _ladder = 0.90 + 0.20 * s._hjit(plan.W, plan.H, 76.0)
    # ...AND THE PARCEL SIZES ARE STRATIFIED, one per band, rather than drawn independently. A
    # continuous roll clusters near its own middle, which is exactly the reading being fixed:
    # Mizuguchi's four came out 292 / 294 / 290 / 269 ft - three of them inside 1.4% of each other,
    # perceptually one wood drawn three times, from a roll that was already +/-18% wide. Independent
    # draws will keep doing that (with four samples a near-tie somewhere is the NORMAL outcome, not
    # bad luck), so each accepted parcel instead TAKES a band and removes it from the pool: with
    # four parcels the multipliers are 0.865 / 0.955 / 1.045 / 1.135 and no two woods can land
    # within 9% of each other. Which parcel gets which band is still rolled from its own position,
    # so the sizes are not ordered by seating order.
    _bands = list(range(max(2, count)))
    # SHRINK BEFORE GIVING UP (settlement-review round 2, 2026-08-16): with the kept window and
    # the marsh both closed to it, a tight composition can offer no full-size seat at all - the
    # first dry pass seated ZERO parcels on Kashikawa, the map NAMED for its oaks. A smaller
    # woodlot (200 ft, then 160 ft) is historically ordinary - coppice lots were whatever odd
    # corner the village spared - while an absent one on a name-story map is not. Unfilled slots
    # re-scan at the smaller sizes; a slot no size can seat is honestly dropped.
    # ...AND THE SET-BACK RELAXES BEFORE THE MAP GOES WOODLESS (Kashikawa round 3, 2026-08-16:
    # after the wells realigned, the generous 80/180 px crop set-backs plus the marsh closed the
    # whole kept window at every rung - zero parcels on the map NAMED for its oaks). The scan's
    # defaults are deliberately far above the gate's own floors (`woodland_clear_of_crops`:
    # CLEAR 14 px overhang, SHADE 69 px sunny-side at 1 ft/px), so a second pass at 40/100 px
    # still clears them - and the satoyama mosaic genuinely puts the woodlot on the margin
    # beside the field. ONE trap, found by the 48-seed sweep (Audit-24): `_clear_gap` measures
    # center-to-crop minus HALF, which overstates the true polygon gap by up to 0.414*half when
    # the crop lies diagonal to the square - the generous profile absorbed that slack, the
    # relaxed one shipped a parcel the check called shading. So the relaxed thresholds carry
    # the diagonal slack EXPLICITLY, per parcel size (the measured-gap floor then implies a
    # true-gap floor of 40/100, both above the check's 14/69). The generous profile always runs
    # first, so a roomy composition is byte-identical; only one that would otherwise draw NO
    # woodland tightens.
    for _sb_normal, _sb_sunny in ((80.0, 180.0), (40.0, 100.0)):
        if len(chosen) >= count:
            break
        for size_try in (size * _ladder, size * 0.8 * _ladder, size * 0.64 * _ladder, size * 0.5 * _ladder):
            if len(chosen) >= count:
                break
            # A RUNG UNDER THE LEGIBILITY FLOOR IS NOT OFFERED AT ALL. The first cut clamped each
            # candidate up to the floor and then dropped the parcel when the clamped size did not
            # fit, which needed a fall-through nobody could reach in a test; skipping the rung says
            # the same thing in one line and leaves `half_used = half` unconditionally safe, because
            # every rung that survives to the accept block is already above the floor. Either way a
            # settlement whose ground cannot hold a legible commons draws FEWER, never smaller.
            if size_try < _COMMONS_FLOOR_FT:
                continue
            half = size_try / 2.0
            _sb_pad = 0.415 * half if _sb_normal < 80.0 else 0.0  # the diagonal slack (see above); the generous profile keeps its historical thresholds exactly
            _sb_n, _sb_s = _sb_normal + _sb_pad, _sb_sunny + _sb_pad
            # MIRROR THE CHECK'S WINDOW, NOT JUST ITS FORMULA (2026-08-18). The kept-window
            # confinement above and `woodland_commons_within_the_frame` are meant to be the same
            # rule, and they were not: the check asks for **70% of the parcel's bbox** inside the
            # view and says in as many words that a parcel clipping at the edge "reads as 'more wood
            # that way' and is fine", while the scan demanded the whole square inside the window
            # plus a further 16 px. Being stricter than your own gate sounds safe and is not - it
            # cost two of the four hamlets their woodland outright. Measured before the fix: at
            # EVERY rung of the shrink ladder and BOTH set-back profiles, Kashikawa - the map named
            # 樫川, "oak river" - had ZERO qualifying seats out of a 231-286 point lattice and Sawada
            # exactly one, with the crop clause alone refusing 93-97% and the best achievable
            # clearance NEGATIVE (the square overlapped a paddy). Neither the shrink ladder nor the
            # set-back relaxation, both added FOR Kashikawa, could ever have worked: the binding
            # constraint was never the set-back, it was that a 20-household hamlet's field fills its
            # own frame and the scan would not let a wood touch the edge of it.
            #
            # So the seat is judged the way the check judges it, by AREA. The center may now sit up
            # to 0.6*half outside the kept window and the exact bbox-overlap fraction is tested in
            # `_ok` - which is what makes the both-axes corner case safe, where a per-axis box test
            # would pass two 0.4*half overhangs at 0.64 inside and ship a check failure. The floor
            # is 0.8 rather than the check's 0.7 because this window is a PREDICTION of the crop:
            # the margin absorbs the features that may still grow it.
            sx0, sy0 = max(cbx0 + 16.0, _fx0 - 0.6 * half), max(cby0 + 16.0, _fy0 - 0.6 * half)
            sx1, sy1 = min(cbx1 - 16.0, _fx1 + 0.6 * half), min(cby1 - 16.0, _fy1 + 0.6 * half)

            # THE QUALIFICATION IS ONE PREDICATE, so a seat can be re-asked after it is nudged. It
            # used to be an inline `if` that only the lattice scan could evaluate, which is why the
            # jitter below could not exist: there was no way to check that a moved seat was still
            # legal. Same shape as every other "placement and its check read one source" fix here.
            def _ok(
                x: float,
                y: float,
                half: float = half,
                n: float = _sb_n,
                sn: float = _sb_s,
                sx0: float = sx0,
                sy0: float = sy0,
                sx1: float = sx1,
                sy1: float = sy1,
            ) -> bool:
                # ONE guard clause, deliberately: the window bounds and the kept-window AREA are the
                # same question asked of a seat that may have been MOVED since the scan offered it
                # (the jitter and the size roll both re-ask). Split into two statements the bounds
                # half is unreachable in the corpus - no pool map or cohort seed happens to jitter a
                # seat past the edge - and an untested line in a predicate whose whole job is
                # re-asking is exactly what rots.
                if (
                    not (max(half + 40.0, sx0) <= x <= min(plan.W - half - 40.0, sx1) and max(half + 40.0, sy0) <= y <= min(plan.H - half - 40.0, sy1))
                    or (max(0.0, min(x + half, _fx1) - max(x - half, _fx0)) * max(0.0, min(y + half, _fy1) - max(y - half, _fy0))) < 0.8 * (2.0 * half) ** 2
                ):
                    return False  # off the window, or under the check's own 70%-of-bbox rule (0.8 here, for prediction slack)
                return (
                    _clear_gap((x, y), half, crops, dy, n, sn) is not None
                    and not any(math.hypot(x - kx, y - ky) < kr + half for kx, ky, kr in keep)
                    and not any(rx0 - half < x < rx1 + half and ry0 - half < y < ry1 + half for rx0, ry0, rx1, ry1 in keep_rects)
                    and not any(_near_line((x, y), half, pts, pad) for pts, pad in lanes + streams)
                    and not _wet(x, y, half)
                )

            scored: list[tuple[float, float, float]] = []
            y = max(half + 40.0, sy0)
            while y <= min(plan.H - half - 40.0, sy1):
                x = max(half + 40.0, sx0)
                while x <= min(plan.W - half - 40.0, sx1):
                    if _ok(x, y):
                        # PREFER THE NEAREST QUALIFYING GROUND, leaning upslope. The first version of this
                        # maximized distance from the crop instead, which sounds right and is wrong twice
                        # over: it drove every patch to the canvas's far upslope margin, where the dedupe
                        # radius strung them out along one line at identical height, and then the crop -
                        # which frames to the HARD features and lets commons bleed off-frame - cut three of
                        # the four off the sheet entirely. A settlement's coppice is walked to daily for
                        # fuel and fodder; it stands on the back slope behind the houses, as close as the
                        # crop set-back allows. The keep-outs above are what make it far ENOUGH.
                        upslope = -((x - ccx) * dx + (y - ccy) * dy)
                        scored.append((-math.hypot(x - ccx, y - ccy) + 0.35 * upslope, x, y))
                    x += step
                y += step
            # THE COPPICE IS A HILLSIDE WOOD, SO A DOWN-SLOPE-DOMINANT SEAT LOSES TO A CROSS-SLOPE ONE
            # (settlement-review, Kashikawa 2026-08-18 round 2, and its research pass settled the
            # ruling this ledger item was waiting for). Three project files say woodland goes on the
            # higher, farther ground - `settlements/vegetation.md`, `research/fields.md` and this
            # function's own scorer comment - and Kashikawa drew both its stands downslope, one of them
            # 886 ft down and 75 ft off the reed marsh: a coppice walking onto the wet toe of the fan.
            # The scorer's additive `+0.35 * upslope` never binds, because a 90 px step toward the
            # cluster outbids 257 px of height.
            #
            # THE RULING, and why it is neither of the two options I ledgered. Raising the weight until
            # it binds returns this map to ZERO parcels - the defect closed that morning - and a knob
            # was not available either: the reviewer's research pass found satoyama DEFINED as the
            # foothill border zone with its coppice on the hillsides, and the China-first analog (the
            # fengshui back-hill wood) upslope as well, so a downslope commons is not a co-equal
            # attested form and "correct the prose instead" would mean rewriting doctrine to match a
            # placement artifact. What the record does support is weaker than "uphill of the houses":
            # the wood is ON THE HILLSIDE, i.e. at or above the settlement's own contour. So the test
            # is the along/cross RATIO, not the height. Decomposed on Kashikawa, that refuses the
            # down-dominant parcel (886 ft down against 276 cross) and keeps the cross-dominant one
            # (505 down against 1562 cross, effectively a contour seat) - one parcel, not zero.
            #
            # A PREFERENCE, not a filter, per this scan's standing habit: if no cross-slope seat
            # qualifies at all, the down-slope ones are still offered rather than leaving a map
            # woodless. The GM can reverse this ruling; it is recorded in `future-work.md`.
            _cross_seats = [t for t in scored if abs((t[1] - ccx) * -dy + (t[2] - ccy) * dx) >= ((t[1] - ccx) * dx + (t[2] - ccy) * dy)]
            if _cross_seats:
                scored = _cross_seats
            for _, x, y in sorted(scored, reverse=True):
                if len(chosen) >= count:
                    break
                if any(math.hypot(x - cx0, y - cy0) < _ex0 for cx0, cy0, _ex0 in centers):
                    continue
                # OFF THE LATTICE, AND NOT ALL ONE SIZE (settlement-review, Mizuguchi 2026-08-18).
                # The scan samples a uniform 90 px lattice, scores every seat by one monotone
                # function (near the cluster, leaning upslope) and then takes the best remaining seat
                # outside a FIXED separation radius. Those three together do not merely tend to
                # produce an even chain - they produce one by construction, and Mizuguchi shipped the
                # proof: three identical 250 x 250 ft squares at (456,967), (726,697), (996,427),
                # offsets of exactly (+270,-270) and (+270,-270), reading as three stamps of one wood
                # marching up a ruled diagonal. The fourth parcel, seated off the ladder at a
                # different size, reads fine and is the control.
                #
                # So the LATTICE is a sampling artifact and must not survive into the output. The
                # accepted seat is nudged up to half a step off it and the parcel's size rolled down
                # by up to a fifth, both from `_hjit` - positional, so a map is unchanged by
                # regeneration and two maps differ from each other. Every nudge is re-asked through
                # `_ok`, and a nudge that would not qualify is simply not taken: this can only move a
                # legal seat to another legal seat, never widen what the scan admits.
                # VARY THE STRIDE, NOT JUST THE SEAT (settlement-review x2, 2026-08-18 - the FIRST
                # version of this fix did not work and this is why). Jittering the accepted seat off
                # the lattice killed the identical-STAMP reading, and left the CHAIN: Mizuguchi still
                # stepped 379.7 ft then 361.9 ft up one axis with the middle parcel 3.1% off the
                # straight line, and Inashiro independently stepped 366 / 371 / 392 ft. Measured, and
                # the cause is not the lattice at all - it is that a MONOTONE score plus a FIXED
                # `size * 1.5` exclusion radius means each parcel is by construction the nearest
                # qualifying seat just outside the last one's circle, so the stride is pinned at
                # ~375 ft however the seats are dithered. A +/-45 px jitter is +/-12% of that stride:
                # far too small to break a rhythm it does not touch. So each parcel now carries its
                # OWN exclusion radius, rolled 1.15x-2.50x its size from its own position, and the
                # spacing varies because the generative rule varies rather than because the output
                # is dithered.
                jx = x + (s._hjit(x, y, 71.0) - 0.5) * step
                jy = y + (s._hjit(x, y, 72.0) - 0.5) * step
                # ...and the size roll is wider than it was, for the reason recorded at `_ladder`:
                # +/-15% of a shared rung left two maps' stands 1.8% apart. This is a DEGREE on a
                # continuum (calibrated liberty), not a knob - `settlements/vegetation.md` already
                # says coppice lots were "whatever odd corner the village spared", so a narrow roll
                # was narrower than our own doctrine.
                # TRY THE MIRRORED SIZE BEFORE FALLING BACK TO THE RUNG. Widening the roll upward
                # made it WORSE at first, in a way only the artifact showed: a grown parcel often
                # fails `_ok` (it is asking for ground the rung already fitted snugly), the ladder
                # fell straight back to `half`, and Mizuguchi shipped three parcels at 292 / 294 /
                # 290 ft - the exact rung, three times, more identical than before the roll existed.
                # Reflecting the factor about 1.0 gives a distinctly SMALLER parcel to try before
                # surrendering to the rung, so a refused growth becomes variety instead of a twin.
                _bi = min(int(s._hjit(x, y, 73.0) * len(_bands)), len(_bands) - 1) if _bands else 0
                _f = 0.82 + 0.36 * (((_bands[_bi] if _bands else 0) + 0.5) / max(2, count))
                # The band first; then one distinctly SMALLER try, because a grown parcel is asking
                # for ground the rung only just fitted and the plain fallback to `half` is what
                # produced the near-identical trio above.
                # ...BUT NEVER BELOW A COMMONS' OWN FLOOR. The band multipliers compound with the
                # per-map ladder, and at the ladder's bottom rung that took Kashikawa's smaller
                # parcel to 103 ft - under the ~116 ft that THIS change already judged "a copse, not
                # a commons" when it made the size roll two-sided. A floor is the honest guard: a
                # parcel too small to read as a managed wood should not be drawn smaller to satisfy
                # a variance rule. If the floor does not fit, the rung fallback still applies, so
                # this can only ever make a parcel larger or leave it alone.
                half_used = half  # the rung, which the ladder above guarantees is at or over the floor
                for _cand in (max(half * _f, _COMMONS_FLOOR_FT / 2.0), max(half * 0.84, _COMMONS_FLOOR_FT / 2.0)):
                    if _ok(jx, jy, _cand):
                        x, y, half_used = jx, jy, _cand
                        break
                    if _ok(x, y, _cand):
                        half_used = _cand
                        break
                # THE FLOOR WAS NOT A FLOOR (settlement-review, Kashikawa 2026-08-18 round 2). Both
                # candidates are clamped to `_COMMONS_FLOOR_FT`, but when neither fitted, control fell
                # through to `half_used = half` - the UNCLAMPED rung - and Kashikawa shipped a 116.6 ft
                # parcel, under the floor, at the very size this file's own docstring calls "a copse,
                # not a commons". The comment above claimed the clamp "can only ever make a parcel
                # larger or leave it alone" and the fall-through did the one thing it forbade.
                #
                # The rung is now only taken if the rung itself clears the floor; otherwise the parcel
                # is DROPPED, which is what `_COMMONS_FLOOR_FT`'s docstring says should happen - "a
                # settlement whose ground genuinely cannot hold one draws FEWER parcels rather than
                # smaller ones". The band is returned to the pool by not popping it until acceptance,
                # so a dropped parcel does not silently consume a size band the next one could use.
                if _bands:
                    _bands.pop(_bi)
                chosen.append([(x - half_used, y - half_used), (x + half_used, y - half_used), (x + half_used, y + half_used), (x - half_used, y + half_used)])
                centers.append((x, y, size * (1.15 + 1.35 * s._hjit(x, y, 74.0))))
    return chosen


def content_box(s: Settlement, plan: SitePlan, pad: float = 0.0) -> tuple[float, float, float, float]:
    """The bounding box of everything the crop will frame to - the field, its hem, the homesteads and
    the pond - grown by `pad`. Read from the manifest, so it tracks whatever actually got drawn."""
    xs: list[float] = [p[0] for p in plan.envelope]
    ys: list[float] = [p[1] for p in plan.envelope]
    for d in s.M.get("dry_plots", []):
        xs += [float(v[0]) for v in d["poly"]]
        ys += [float(v[1]) for v in d["poly"]]
    for h in s.M.get("houses", []):
        xs.append(h["x"])
        ys.append(h["y"])
    pond = s.M.get("pond")
    if pond:
        xs += [pond[0] - pond[2], pond[0] + pond[2]]
        ys += [pond[1] - pond[3], pond[1] + pond[3]]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def title_pocket(s: Settlement, plan: SitePlan, w: float = 300.0, h: float = 190.0) -> tuple[float, float, float, float]:
    """Ground held back so the map has somewhere to put its NAME.

    `title()` scans the framed window for a box clearing every feature and falls back to a corner
    overlap when there is none - and on a hamlet the blank ground is a short list: the field takes
    the middle, the hem the high margin, the marsh the whole low toe, the cluster and its grove one
    flank. That leaves the lateral corners, which is exactly where the coppice scan wants to go
    (`open_ground_patches` prefers the nearest qualifying ground). Both cannot have them.

    So one corner of the map's content is reserved before the coppice is sited. The corner chosen is
    the one furthest from the field's middle AND from the houses - the emptiest quarter of the sheet,
    which is where a reader would expect the cartouche anyway. It is a reservation, not a placement:
    `title()` still does its own search and may well sit somewhere else."""
    x0, y0, x1, y1 = content_box(s, plan, pad=30.0)
    # ASK THE ENGINE WHICH GROUND IS ACTUALLY BLANK, rather than assuming a corner is.
    #
    # `_blank_label_spot` is the same scan `title()` will run, so this reserves ground the title can
    # really use. Picking "the corner furthest from the field and the houses" was tried first and is
    # not the same thing: on the reference map that corner already held the reed marsh - which IS a
    # title obstacle, being a distinct wet surface rather than sparse ground cover - so the pocket
    # was reserved over ground the title could never have taken, the coppice went somewhere else for
    # nothing, and the title still landed on the fallback corner. Reserving what is blank NOW works
    # because this runs after the water, the crops, the houses and the hinterland and before the
    # only two things left that could fill it (the coppice and the grove).
    spot = s._blank_label_spot(x0, y0, x1 - x0, y1 - y0, w, h)
    if spot is None:  # pragma: no cover - the map is already too full to title; nothing to reserve
        return (x0, y0, x0, y0)
    return (spot[0], spot[1], spot[0] + w, spot[1] + h)


def _clear_gap(center: Pt, half: float, crops: Sequence[Poly], fall_y: float, normal: float = 80.0, sunny: float = 180.0) -> float | None:
    """Distance from a candidate square to the nearest crop, or None if it is too close.

    The set-back is 80 px normally and 180 px when the square sits on the crop's SUNNY side (south,
    in screen terms) - the shading case. `woodland_clear_of_crops` uses 1 : 2.5-ish set-backs for the
    same reason; this is deliberately a little more generous than the check, so a patch that passes
    here passes there with room to spare rather than sitting on the line."""
    cx, cy = center
    best = 1e9
    for crop in crops:
        d = min(seg_dist(cx, cy, crop[i], crop[(i + 1) % len(crop)]) for i in range(len(crop))) - half
        if point_in_poly(cx, cy, list(crop)):
            return None
        south_of = cy - half > max(p[1] for p in crop) - 40 and min(p[0] for p in crop) - half < cx < max(p[0] for p in crop) + half
        if d < (sunny if south_of else normal):
            return None
        best = min(best, d)
    return None if best >= 1e9 else best


def _near_line(center: Pt, half: float, pts: Sequence[Pt], pad: float) -> bool:
    cx, cy = center
    return any(seg_dist(cx, cy, pts[i], pts[i + 1]) < half + pad for i in range(len(pts) - 1))


def stage_woodland(s: Settlement, plan: SitePlan) -> None:
    """A few managed-woodland patches on the high, far ground - the green EXCEPTION to the scrub.

    The windbreak belt is COMPUTED here, before the scan, and only DRAWN in the next stage. That
    split exists because the two woods must not merge: `woodland_clear_of_grove` requires a coppice
    patch to keep off every clump of the fengshui grove, or the two read as one indistinct green
    mass. The scan therefore has to know where the belt is going, but the belt has to be DRAWN late
    so its per-crown filter sees every structure already standing (the engine's DRAW ORDER rule).
    Computing early and drawing late satisfies both."""
    plan.belt = belt_polygon(s, plan)
    for patch in open_ground_patches(s, plan, plan.woodland_patches):
        s.commons(patch, role="woodland")


def stage_windbreak(s: Settlement, plan: SitePlan) -> None:
    """The communal fengshui belt behind the cluster, shaped to the houses that actually landed.

    A nucleated settlement shelters behind ONE grove rather than per-house belts, and the belt must
    do two things the gate measures: stand on the WINDWARD side of the house centroid, and EMBRACE
    the cluster (a substantial belt within 150 px of a farmhouse - "far corner masses alone are
    decoration"). Both fall out of deriving it from the houses: the belt is a band offset into the
    wind from the cluster's own centroid, spanning the cluster's width across the wind, ragged along
    its edges because a grove hugs the land and is not a ruled wall. A copse scatter then fills the
    leafy gaps among the homes.

    Drawn LATE, after the ground cover and the woods, so its per-crown filter sees every structure
    already standing and no tree is drawn on a roof."""
    if not plan.belt:  # pragma: no cover - stage_woodland always computes it first
        return
    # ...DENTED AROUND THE TITLE'S POCKET. `stage_woodland` reserves blank ground for the map's name
    # (`title_pocket`) and keeps the woods out of it, but the BELT is drawn later and honors
    # nothing - `village_grove` takes only a polygon, with no keep-out list - so on a tightly framed
    # map the belt simply covered the reservation and `title()` had nowhere clear to sit (seed 8's
    # polder, 3 of 4 falls). Pushing the belt's vertices out of that rectangle costs the band a
    # local dent where a hamlet's own name goes, which is cheaper than the alternative of moving a
    # windbreak that is correct on every other count.
    # ...AND CLAMPED TO THE FRAME THE CROP WILL SET (settlement-review, Mizuguchi 2026-08-17). Soft
    # cover clips at the map edge on purpose - the commons and the marsh trail off as "more wild
    # ground this way" - but a settlement's own PLANTED windbreak is not wild ground: it is a belt of
    # finite depth that the hamlet made, and a belt sliced by the page edge along its whole length
    # reads as woodland running off-map instead. On Mizuguchi the re-pack pulled the crop's bottom up
    # 37 px while the belt's canopy still reached 62 px below it, so 58 of 217 clumps touched the
    # edge and 23 were drawn WHOLLY outside the viewBox - ink emitted where nothing can ever see it,
    # which is a record-vs-drawing mismatch as much as a composition one.
    #
    # The clamp can be exact rather than a guess, because every HARD feature that sets the crop is
    # already placed by the time this stage runs: ask `_crop_boxes` - the very source
    # `crop_to_content` reads - and hold the belt inside that box. Same-source doctrine, and the same
    # move the title-pocket dent above already makes: push the vertices, keep the belt. (Only
    # `stage_crossings` follows, and a footbridge sits on water well inside the frame, so it cannot
    # pull the box back out from under this.)
    _boxes = s._crop_boxes(city=False)
    _fx0 = min((b[0] for b in _boxes), default=0.0) - CROP_MARGIN
    _fx1 = max((b[1] for b in _boxes), default=float(s.W)) + CROP_MARGIN
    _fy0 = min((b[2] for b in _boxes), default=0.0) - CROP_MARGIN
    _fy1 = max((b[3] for b in _boxes), default=float(s.H)) + CROP_MARGIN
    _tp = title_pocket(s, plan)
    _dented = []
    for _bx, _by in plan.belt:
        if _tp[0] <= _bx <= _tp[2] and _tp[1] <= _by <= _tp[3]:
            _cands = ((_tp[0] - 6.0, _by), (_tp[2] + 6.0, _by), (_bx, _tp[1] - 6.0), (_bx, _tp[3] + 6.0))
            _bx, _by = min(_cands, key=lambda q: (q[0] - _bx) ** 2 + (q[1] - _by) ** 2)
        _dented.append((_bx, _by))
    # THE BELT ITSELF IS NOT MOVED - the CLUMPS are held inside the frame instead, via
    # `village_grove(within=...)`. Clamping the polygon was tried first and is wrong, recorded so it
    # is not retried: the outline's bbox center is what `village_grove` records as the grove's `x`,`y`
    # and what `village_windbreak_on_windward_side` judges, so pulling vertices inward walks that
    # center toward the cluster - cohort seeds 19 and 28 crossed to the LEE side, and a guard on the
    # polygon's centroid did not catch it because the centroid is not the point the check reads. The
    # belt's position is its meaning; only its leaves needed containing.
    # The frame ITSELF, with no inset: `village_grove` skips only a clump lying WHOLLY outside it, so
    # the belt still clips at the page edge the way every other soft cover does (and the way
    # `settlements/presentation.md` requires) and only ink nobody can see is dropped. An inset was
    # tried first and cost Sawada 46% of its canopy - see the comment at the skip.
    s.village_grove(_dented, role="windbreak", within=(_fx0, _fy0, _fx1, _fy1))
    # The COPSE fills the leafy gaps AMONG the homes, over the house cloud. That is only reasonable
    # ground because `stage_homesteads` now bounds every seat to the cluster band: over a cloud with
    # a strewn farmstead in it, this became a scatter across 1,446 x 1,244 px - a wood over the whole
    # settlement rather than a copse among the houses, and every clump an obstacle the map's own
    # title could then find no room around (`title_clear_of_features`).
    houses = s.M.get("houses", [])
    xs = [h["x"] for h in houses]
    ys = [h["y"] for h in houses]
    pad = 16.0
    s.village_grove([(min(xs) - pad, min(ys) - pad), (max(xs) + pad, min(ys) - pad), (max(xs) + pad, max(ys) + pad), (min(xs) - pad, max(ys) + pad)], role="copse", dense=False)


def belt_polygon(s: Settlement, plan: SitePlan) -> Poly:
    """The windbreak belt's footprint - a band FOLLOWING the cluster's windward fringe.

    The belt used to be a straight band standing off the single windward-most house, its length set
    by the widest cross-wind pair. That is right for a round cluster and wrong for every other
    shape: on a tall narrow settlement under a diagonal wind it put the belt 350 px clear of the
    nearest farmhouse and nearly square, and `village_grove`'s own filters then threw most of its
    clumps away - nine survived. A belt that shelters nothing fails
    `village_windbreak_embraces_cluster` and `village_windbreak_scales_with_cluster` together, and
    both are right to fail it.

    So the near face is sampled ACROSS the wind and, in each column, sits just behind whichever
    house is furthest upwind THERE. The result hugs the settlement's windward profile whatever its
    shape - which is what a back-village grove does, being planted where the houses are - and stays
    a band of constant depth, so `village_grove` still fills it as a belt rather than a blob."""
    houses = s.M.get("houses", [])
    if len(houses) < 3:  # pragma: no cover - fewer houses than this fails the gate first
        return []
    wx, wy = plan.wind
    px, py = -wy, wx  # across the wind
    ccx, ccy = sum(h["x"] for h in houses) / len(houses), sum(h["y"] for h in houses) / len(houses)
    uv = [(((h["x"] - ccx) * wx + (h["y"] - ccy) * wy), ((h["x"] - ccx) * px + (h["y"] - ccy) * py)) for h in houses]
    v_lo, v_hi = min(v for _u, v in uv), max(v for _u, v in uv)
    COLS = 7
    half = (v_hi - v_lo) / 2 + 90.0  # a shoulder past the outermost house at each end
    v_mid = (v_lo + v_hi) / 2
    rng = random.Random((plan.spec.seed * 7919) & 0xFFFFFFFF)

    def rag(q: Pt, amp: float = 13.0) -> Pt:
        return (q[0] + rng.uniform(-amp, amp), q[1] + rng.uniform(-amp, amp))

    # NO COLUMN FALLS BEHIND THE MEDIAN HOUSE. Following the profile is right, but on a cluster
    # that is long ACROSS the wind the flank columns' own frontrunner sits well downwind of the
    # middle ones, so the band bows back around the settlement and its centroid can land level with
    # (or behind) the house cloud - which is exactly what `village_windbreak_on_windward_side`
    # measures, and it fired on two cohort maps with a belt that looked fine in every other check.
    # Flooring each column at the cluster's MEDIAN u keeps the belt following the fringe where the
    # fringe leads it, and keeps the whole band on the windward half where a back-village grove
    # belongs. The median, not the mean: one house pushed far upwind should not drag the wall out.
    u_sorted = sorted(u for u, _v in uv)
    u_floor = u_sorted[len(u_sorted) // 2]

    def profile(span_f: float) -> list[tuple[float, float]]:
        """(v, u) of the windward fringe, sampled in columns across the wind."""
        cols: list[tuple[float, float]] = []
        for k in range(COLS + 1):
            v = v_mid + half * span_f * (-1.0 + 2.0 * k / COLS)
            width = half * span_f / COLS + 40.0
            near = [u for u, vv in uv if abs(vv - v) <= width]
            if not near:  # a column with no house of its own leans on the whole cluster's fringe
                near = [max(u for u, _v in uv) - 40.0]
            cols.append((v, max(max(near), u_floor)))
        return cols

    # ~110 px deep - a real wind wall, not a hedge. The 24 px stand-off is set by
    # `village_windbreak_embraces_cluster`, which wants a clump within 150 px of a farmhouse: the
    # clump grid starts some way inside the polygon, so a 42 px face measured 160 px to the nearest
    # tree.
    crops: list[Poly] = [list(plan.envelope), *crop_polys(s)]

    def band(span_f: float, back: float) -> Poly:
        cols = profile(span_f)
        # 36 px, not 24. `village_grove` filters clumps against every structure and crop, and it
        # filters the near face hardest - so a belt whose POLYGON sits clearly windward can still
        # have its DRAWN clumps average back onto the cluster's own line, which is what
        # `village_windbreak_on_windward_side` measures (Kashikawa: polygon centroid +137, drawn
        # centroid -5). The extra 12 px comes out of the 150 px embrace budget and leaves plenty.
        near = [rag((ccx + wx * (u + 36.0 + back) + px * v, ccy + wy * (u + 36.0 + back) + py * v)) for v, u in cols]
        far = [rag((ccx + wx * (u + 146.0 + back) + px * v, ccy + wy * (u + 146.0 + back) + py * v)) for v, u in reversed(cols)]
        return near + far

    def fouled(poly: Poly) -> bool:
        return any(point_in_poly(q[0], q[1], list(c)) or min(seg_dist(q[0], q[1], c[i2], c[(i2 + 1) % len(c)]) for i2 in range(len(c))) < 20.0 for q in poly for c in crops)

    # THE LADDER STANDS BACK BEFORE IT SHRINKS. Both moves get the belt off the crop, but they cost
    # different things: standing back spends the embrace budget (a clump within 150 px of a
    # farmhouse, and the belt starts 24 px behind the fringe, so there is room), while shrinking
    # spends the SIZE budget (canopy worth 40% of the roof area it shelters, which a belt trimmed to
    # half its length cannot meet). Shrinking first cost both checks on two cohort maps.
    belt = band(1.0, 0.0)
    for span_f, back in ((1.0, 0.0), (1.0, 22.0), (1.0, 44.0), (0.88, 44.0), (0.74, 60.0), (0.6, 60.0)):
        belt = band(span_f, back)
        if not fouled(belt):
            break
    return [(max(6.0, min(plan.W - 6.0, bx)), max(6.0, min(plan.H - 6.0, by))) for bx, by in belt]
