"""The channel TAPER LAW - `waterfields.taper_w`.

A rule that lives only in a docstring has already been proven not to hold, so the square-root law
gets a ratchet. The load-bearing test here is not that the arithmetic is a square root - it is
`test_the_drawn_stroke_and_the_bank_clearance_use_the_SAME_law`: the bunds are laid against the bank
these helpers return and the gate re-measures them, so the day a call site re-derives its own
straight line, a bund gets drawn inside the water.
"""

import math

from waterfields import supply_bank_clearance, taper_pieces, taper_w
from waterfields.frame import CANAL_A_FT, DELIVERY_FT, DELIVERY_PARENT_FRAC, DRAIN_FT, MIN_CHANNEL_PX, _drain_bank, _Frame, chan_px


def _linear(w0: float, w1: float, t: float) -> float:
    """The law this replaced, kept here so the tests can assert the DIFFERENCE rather than a number."""
    return w0 + (w1 - w0) * t


def test_taper_pins_both_ends_exactly() -> None:
    """A taper is an interpolation, so it must hit its declared head and tail on the nose - the
    pieces of a multi-segment canal meet at those values and a gap would show as a visible step."""
    assert taper_w(8.0, 3.0, 0.0) == 8.0
    assert taper_w(8.0, 3.0, 1.0) == 3.0
    assert taper_w(3.0, 12.0, 0.0) == 3.0
    assert taper_w(3.0, 12.0, 1.0) == 12.0


def test_the_width_SQUARED_is_what_runs_linearly() -> None:
    """The law itself: width goes as sqrt(discharge) and discharge is linear along the run, so w^2
    interpolates linearly. Asserted on the square rather than on sampled widths so the test states
    the rule instead of restating the implementation."""
    w0, w1 = 8.0, 3.0
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        assert math.isclose(taper_w(w0, w1, t) ** 2, w0 * w0 + (w1 * w1 - w0 * w0) * t, rel_tol=1e-12)


def test_a_narrowing_ditch_holds_its_width_LONGER_than_a_straight_line() -> None:
    """The visible point of the change (GM 2026-08-17): a delivery ditch must keep most of its
    working width while it still has most of its water to deliver, then dwindle hard at the tail -
    not thin evenly along its whole length and stop dead at a substantial width."""
    w0, w1 = 8.0, 3.0
    for t in (0.25, 0.5, 0.75, 0.9):
        assert taper_w(w0, w1, t) > _linear(w0, w1, t)
    # ...and the narrowing is BACK-LOADED: more of the total drop happens in the last quarter than
    # the first, which is the reading a straight line cannot produce.
    first_quarter = w0 - taper_w(w0, w1, 0.25)
    last_quarter = taper_w(w0, w1, 0.75) - w1
    assert last_quarter > first_quarter


def test_a_gathering_collector_gains_body_EARLY_the_mirror_of_the_same_law() -> None:
    """A drain accumulates catchment rather than shedding it, so the same law runs in reverse: it
    picks up the largest share of its body in its first stretch and flattens toward the outfall."""
    w0, w1 = 3.0, 12.0
    for t in (0.25, 0.5, 0.75):
        assert taper_w(w0, w1, t) > _linear(w0, w1, t)
    assert taper_w(w0, w1, 0.25) - w0 > w1 - taper_w(w0, w1, 0.75)


def test_a_shallow_taper_is_barely_moved() -> None:
    """The law must only bite where a stroke really is shedding most of what it carries. A supply
    canal piece between two offtakes (12.4 -> 10.1 ft) sheds a little, so it should look almost
    exactly as it did - otherwise this change would have quietly rewritten the whole net."""
    for t in (0.25, 0.5, 0.75):
        assert abs(taper_w(12.4, 10.1, t) - _linear(12.4, 10.1, t)) < 0.1


def test_taper_is_monotone_between_its_ends() -> None:
    """No overshoot in either direction - a ditch that widened mid-run before narrowing again would
    read as a pond, and the bank clearances would follow it."""
    narrowing = [taper_w(8.0, 3.0, k / 20) for k in range(21)]
    widening = [taper_w(3.0, 12.0, k / 20) for k in range(21)]
    assert all(a >= b for a, b in zip(narrowing, narrowing[1:], strict=False))
    assert all(a <= b for a, b in zip(widening, widening[1:], strict=False))


def test_taper_never_returns_a_negative_root() -> None:
    """`t` is a clamped fraction everywhere it is called, but the burial filter and the seam buffer
    derive theirs from arc-length ratios on polylines the fillet has moved - so a hair past 1.0 is
    reachable, and `sqrt` of a negative is a crash rather than a wrong pixel."""
    assert taper_w(8.0, 3.0, 1.05) >= 0.0
    assert taper_w(8.0, 0.0, 1.0) == 0.0


def test_the_drawn_stroke_and_the_bank_clearance_use_the_SAME_law() -> None:
    """THE RATCHET. `supply_bank_clearance` reports the half-width a paddy bund must stand off, and
    the gate re-measures the bunds against it - so it has to agree with the stroke the renderer
    actually inks. Both now come from `taper_w`; revert either to a straight line and the two
    disagree by up to ~0.55 ft at mid-run, which is a bund drawn inside the water."""
    pts = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    cum = [0.0, 100.0, 200.0]
    w0, w1 = 8.0, 3.0
    for x in (50.0, 100.0, 150.0):
        _gap, halfw, _past, _foot, _nrm = supply_bank_clearance((x, 40.0), pts, w0, w1, cum)
        assert math.isclose(halfw, taper_w(w0, w1, x / 200.0) / 2, rel_tol=1e-9)
        assert halfw > _linear(w0, w1, x / 200.0) / 2  # and it is the NEW law, not the old one


def test_the_delivery_taper_holds_then_dwindles() -> None:
    """THE WORKED EXAMPLE for the taper law, kept HERE rather than in `taper_w`'s docstring.

    Twice the docstring carried measured magnitudes and twice they went false with nothing failing -
    once when the sampling was wrong, once when the true-size ladder changed every figure the same
    day. A number in prose is not falsifiable; this is. So it asserts the SHAPE the doctrine
    promises, in the units the engine actually ships, and stays true when the tiers move again:

      - wider than a straight line at every interior point (it HOLDS its working width),
      - more of the total narrowing in the back half than the front (it DWINDLES late),
      - and the tail value reached only at the tail, never as a flat run.
    """
    head, tail = DELIVERY_FT
    pts = [(float(x) * 30, 0.0) for x in range(18)]  # an evenly-sampled delivery ditch
    pieces = taper_pieces(pts, head, tail)
    widths = [w for _p, w in pieces]

    assert all(a >= b for a, b in zip(widths, widths[1:], strict=False)), "the taper must not widen mid-run"
    # HOLDS: every interior width beats the straight line between the same two ends
    for k, w in enumerate(widths):
        t = (k + 0.5) / len(widths)
        assert w > _linear(head, tail, t) - 1e-9, f"piece {k} is thinner than a straight line at t={t:.2f}"
    # DWINDLES LATE: the back half of the run sheds more width than the front half
    mid = taper_w(head, tail, 0.5)
    assert (mid - tail) > (head - mid), "the narrowing must be back-loaded, not spread evenly"
    # ...and the tail figure is not held as a FLAT run - only the last piece may sit at it
    assert sum(1 for w in widths if abs(w - tail) < 0.01) <= 1


def test_chan_px_converts_TRUE_FEET_to_pixels_at_the_map_scale() -> None:
    """The net is drawn at true size (GM 2026-08-17), so a width in feet must come out as that many
    feet of pixels. `grain` is defined as 2 / ftpx, so grain 2.0 is a 1 ft/px hamlet and grain 2/3 is
    a 3 ft/px provincial city - where the same channel is a third as many pixels wide."""
    assert chan_px(5.0, 2.0) == 5.0  # hamlet: 1 ft/px, so 5 ft is 5 px
    assert chan_px(6.0, 1.0) == 3.0  # village: 2 ft/px
    assert math.isclose(chan_px(12.0, 2.0 / 3.0), 4.0)  # city: 3 ft/px


def test_chan_px_floors_at_the_visibility_minimum_and_only_there() -> None:
    """The floor is the ONE place map scale enters the ladder: a true width below it would not be a
    line at all. It must never REDUCE a width that already clears it - that would be inflation's
    mirror, quietly flattening the hierarchy from the top."""
    assert chan_px(0.4, 2.0 / 3.0) == MIN_CHANNEL_PX  # city terminal tier: 0.13 px true -> floored
    assert chan_px(DELIVERY_FT[1], 2.0) == MIN_CHANNEL_PX  # a 1.2 ft tail at 1 ft/px floors too
    assert chan_px(5.0, 2.0) == 5.0  # well clear of the floor, returned untouched
    # and the floor is BELOW the finest true tier at hamlet scale, so a delivery still TAPERS there
    # rather than arriving pre-flattened - which is the whole reason it is 1.5 and not 2.0
    assert chan_px(DELIVERY_FT[0], 2.0) > MIN_CHANNEL_PX


def test_a_delivery_head_never_exceeds_its_parents_local_width() -> None:
    """The rank read must not invert (settlement-review 2026-08-17, twice). Whatever the canal has
    tapered to where a delivery taps it, the delivery leaves narrower - checked across every cut of a
    canal, including the last, where the parent is at its thinnest and the cap actually bites."""
    from waterfields.comb import _canal_ft

    n = 6
    for j in range(n):
        parent = _canal_ft(CANAL_A_FT, j + 1, n)
        head = min(DELIVERY_FT[0], parent * DELIVERY_PARENT_FRAC)
        assert head < parent, f"delivery at cut {j + 1} would be drawn wider than its parent"
    # the cap is SLACK high in the tree (the delivery keeps its own tier) and BINDS low in it
    assert min(DELIVERY_FT[0], _canal_ft(CANAL_A_FT, 1, n) * DELIVERY_PARENT_FRAC) == DELIVERY_FT[0]
    assert min(DELIVERY_FT[0], _canal_ft(CANAL_A_FT, n, n) * DELIVERY_PARENT_FRAC) < DELIVERY_FT[0]


def test_taper_pieces_parameterizes_by_ARC_not_by_vertex_index() -> None:
    """THE SECOND RATCHET (settlement-review 2026-08-17). The law was right and the SAMPLING was
    wrong: the stroke used to be cut into 7 equal slices of the INDEX range, which only lands the
    right width if the vertices are evenly spaced. Here they are not - eight points, seven segments,
    with the last segment carrying half the length - so an index split would put the mid-LENGTH
    piece at t = 0.5 while its true arc fraction is far earlier."""
    pts = [(0.0, 0.0), (10.0, 0.0), (20.0, 0.0), (30.0, 0.0), (40.0, 0.0), (50.0, 0.0), (60.0, 0.0), (160.0, 0.0)]
    pieces = taper_pieces(pts, 8.0, 3.0)
    assert len(pieces) == len(pts) - 1  # one piece per SEGMENT, none dropped
    # the long tail segment spans arc 0.375 -> 1.0, so its width is the law at its arc MIDPOINT...
    tail_poly, tail_w = pieces[-1]
    assert tail_poly == [(60.0, 0.0), (160.0, 0.0)]
    assert math.isclose(tail_w, taper_w(8.0, 3.0, (60.0 + 160.0) / 2 / 160.0), rel_tol=1e-9)
    # ...which is emphatically NOT what an index split would have drawn there (t = 6.5/7 = 0.929)
    assert abs(tail_w - taper_w(8.0, 3.0, 6.5 / 7)) > 1.0


def test_taper_pieces_draws_a_TWO_POINT_stub_at_its_middle_not_its_tail() -> None:
    """The extreme case the index split got worst: a 2-point stub had six EMPTY slices and was drawn
    end to end at the tail width - 3.6 px where its record declared a 7.2 px head, hanging off a
    parent drawn twice that. One segment must be drawn at the law's midpoint."""
    (poly, w), *rest = taper_pieces([(0.0, 0.0), (20.0, 0.0)], 7.2, 3.2)
    assert not rest
    assert poly == [(0.0, 0.0), (20.0, 0.0)]
    assert math.isclose(w, taper_w(7.2, 3.2, 0.5), rel_tol=1e-9)
    assert w > 3.2 + 1.0  # decisively not the tail width


def test_taper_pieces_is_monotone_and_spans_head_to_tail() -> None:
    """No piece may fall outside the declared ends, and the ladder must descend - a widening piece
    mid-run would read as a pond and would drag its keep-out corridor with it."""
    pts = [(float(x), 0.0) for x in (0, 7, 40, 55, 130, 200)]
    widths = [w for _p, w in taper_pieces(pts, 8.0, 3.0)]
    assert all(a >= b for a, b in zip(widths, widths[1:], strict=False))
    assert 3.0 < widths[-1] < widths[0] < 8.0  # strictly inside: these are arc MIDPOINTS


def test_taper_pieces_declines_a_degenerate_polyline() -> None:
    """A single point (or none) is not a stroke - callers must get an empty ladder, not a crash."""
    assert taper_pieces([], 8.0, 3.0) == []
    assert taper_pieces([(1.0, 1.0)], 8.0, 3.0) == []


def test_taper_pieces_survives_a_ZERO_LENGTH_polyline() -> None:
    """Repeated identical vertices make the total arc zero; the `or 1.0` guard must keep the divide
    alive rather than raising in the middle of a render."""
    assert [w for _p, w in taper_pieces([(5.0, 5.0), (5.0, 5.0)], 8.0, 3.0)] == [8.0]


def test_the_collector_bank_follows_the_same_law_as_its_stroke() -> None:
    """The drain half of the ratchet: `_drain_bank` decides where a paddy's low bund stops, and it
    has to taper with the ditch it abuts. A constant - or a straight line - is inside the stroke at
    one end and leaves a bare stripe at the other."""
    F = _Frame(90.0)
    dpts = [(0.0, 0.0), (100.0, 20.0), (200.0, 40.0)]
    g = 2.0
    bank = _drain_bank(F, dpts, g)
    us = sorted(F.to_uf(*p)[0] for p in dpts)
    lo, hi = us[0], us[-1]
    mid = bank((lo + hi) / 2)
    # the half-width at mid-run, before the margin and the slope correction, is the sqrt law's
    assert mid > (taper_w(chan_px(DRAIN_FT[0], g), chan_px(DRAIN_FT[1], g), 0.5) / 2)
    assert bank(lo) < mid < bank(hi)  # and it still grows monotonically toward the outfall
