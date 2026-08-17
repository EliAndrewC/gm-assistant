"""Prefilters and spatial indexes: how a per-candidate scan of static geometry stops being the
whole runtime of a gen.

PREFILTER FAMILY, all of it - the box or the grid PRUNES, the caller's exact test still DECIDES,
so a verdict is identical to a linear scan's and the pool regenerates byte-identical when a
caller switches over. That property is what separates indexing from coarsening, which this engine
does not do (skill CLAUDE.md, 'When a check is slow, INDEX it - do not coarsen it').

Split from settlement/_geom.py by feature 117 - see settlement/_geom/CLAUDE.md for the index.
"""

from collections.abc import Callable
from typing import Any, SupportsIndex, cast

from .base import Poly, Pt
from .primitives import edge_dist, point_in_poly, seg_dist


def boxed_polys(polys: Any, pad: float = 0.0) -> list[tuple[Poly, float, float, float, float]]:
    """Each polygon paired with its bounding box, expanded by `pad`, computed ONCE. Feed the result
    to `boxed_hit` - which is where the why is written down."""
    out: list[tuple[Poly, float, float, float, float]] = []
    for poly in polys:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        out.append((poly, min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad))
    return out


def boxed_hit(px: float, py: float, boxed: Any, edge_pad: float = 0.0) -> bool:
    """Is (px, py) inside any pre-boxed polygon - or within `edge_pad` of one's edge?

    PREFILTER family (this skill's CLAUDE.md, "Centers, footprints, and aggregates"): the bbox
    PRUNES, the exact `point_in_poly` / `edge_dist` still DECIDES. The verdict is therefore
    identical to a bare scan, which is what lets the whole pool regenerate byte-identical when a
    caller switches over - and is why this is a prefilter rather than the forbidden "coarsen it"
    (CLAUDE.md, "When a check is slow, INDEX it - do not coarsen it").

    WHY IT EXISTS: the ground-cover scatters test every field poly, block poly and clearing PER
    SCATTER POINT, and a marshy village pushes hundreds of thousands of points through them -
    Kikuta burned 24.6M `point_in_poly` calls, 93% of its whole gen (profiled 2026-08-03). The
    PLACEMENT path had had this treatment for months (`_in_blocked`, via `_poly_bboxes`); the
    scatter path never got it. Build the boxes with the SAME pad you pass as `edge_pad`, or the
    prefilter can reject a point the edge test would have wanted."""
    return any(bx0 <= px <= bx1 and by0 <= py <= by1 and (point_in_poly(px, py, poly) or (edge_pad > 0 and edge_dist(px, py, poly) < edge_pad)) for poly, bx0, by0, bx1, by1 in boxed)


def boxed_segs(corridors: Any) -> list[tuple[Pt, Pt, float, float, float, float, float]]:
    """Every corridor segment with its clearance-expanded bbox, flattened and computed ONCE - the
    polyline companion of `boxed_polys`. Feed to `boxed_seg_hit`."""
    out: list[tuple[Pt, Pt, float, float, float, float, float]] = []
    for pl, hw in corridors:
        for i in range(len(pl) - 1):
            a, b = pl[i], pl[i + 1]
            out.append((a, b, hw, min(a[0], b[0]) - hw, min(a[1], b[1]) - hw, max(a[0], b[0]) + hw, max(a[1], b[1]) + hw))
    return out


def boxed_seg_hit(px: float, py: float, segs: Any) -> bool:
    """Is (px, py) within its clearance of any pre-boxed corridor segment? Prefilter family exactly
    as `boxed_hit` - and the same shape `_near_corridor` already uses on the placement side."""
    return any(bx0 <= px <= bx1 and by0 <= py <= by1 and seg_dist(px, py, a, b) < hw for a, b, hw, bx0, by0, bx1, by1 in segs)


class Indexed(list):  # type: ignore[type-arg]
    """A no-build registry that carries a VERSION, so an index built from it can be invalidated by
    the data itself rather than by a guess about the data.

    WHY NOT A CACHE KEY. Two attempts in this engine at "is my cached index still valid?" failed,
    both SILENTLY, both on 2026-08-03: an incremental index over `placed` missed the two sites that
    REBIND it to a filtered copy (Minami and Nagahara lost every garden), and a record-count
    fingerprint for the well grids missed an in-place replacement of a same-LENGTH ring (a wellhead
    cleared to stand in a paddy). Length, object identity and record counts are all guesses about
    CONTENT. A version the list bumps itself is not a guess - mutating is the only way content
    changes, and every mutator bumps.

    The cache lives on the list too (`cache`), keyed by consumer, so an index physically cannot be
    read against a different list than it was built from. That covers the one non-append pattern in
    the engine: `farm_wells` swaps `field_polys` for an empty list and swaps the ORIGINAL OBJECT
    back, which an identity- or length-keyed cache gets wrong and this cannot.

    `test_indexed_overrides_every_mutating_list_method` is the ratchet: it enumerates `list`'s
    mutators by introspection and fails if one is not overridden here, so a Python version adding a
    mutating method cannot open a silent staleness hole."""

    __slots__ = ("appends", "cache", "version")

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.version = 0
        self.appends = 0  # bumped ONLY by append/extend - see indexed_grid for why that distinction pays
        self.cache: dict[str, tuple[int, int, int, Any]] = {}

    def _bump(self) -> None:
        self.version += 1

    def append(self, item: Any) -> None:
        self.appends += 1
        self._bump()
        super().append(item)

    def extend(self, items: Any) -> None:
        self.appends += 1
        self._bump()
        super().extend(items)

    def insert(self, i: SupportsIndex, item: Any) -> None:
        self._bump()
        super().insert(i, item)

    def remove(self, item: Any) -> None:
        self._bump()
        super().remove(item)

    def pop(self, i: SupportsIndex = -1) -> Any:
        self._bump()
        return super().pop(i)

    def clear(self) -> None:
        self._bump()
        super().clear()

    def sort(self, **kw: Any) -> None:
        self._bump()
        super().sort(**kw)

    def reverse(self) -> None:
        self._bump()
        super().reverse()

    def __setitem__(self, i: Any, v: Any) -> None:
        self._bump()
        super().__setitem__(i, v)

    def __delitem__(self, i: Any) -> None:
        self._bump()
        super().__delitem__(i)

    def __iadd__(self, other: Any) -> Any:  # type: ignore[misc]  # same as __imul__ below: mypy checks this against list.__add__, which an in-place op on a subclass cannot satisfy; the override exists so `reg += xs` bumps the version
        self._bump()
        return super().__iadd__(other)

    def __imul__(self, n: Any) -> Any:  # type: ignore[misc]  # mypy compares __imul__ against list.__mul__, which cannot hold for an in-place op on a subclass; the override exists so `reg *= n` still bumps the version rather than silently invalidating an index
        self._bump()
        return super().__imul__(n)


def indexed_grid(lst: Any, key: str, build: Callable[[Any], PointGrid], add: Callable[[PointGrid, Any], None] | None = None) -> PointGrid:
    """The PointGrid `build` makes from `lst`, cached ON `lst` under `key` until `lst` mutates.

    A plain list (one a caller rebound out from under us) is handled by simply building fresh every
    time: slower, never wrong. That fallback is the whole reason this is safe to use on registries
    whose mutation pattern might change later."""
    if not isinstance(lst, Indexed):
        return build(lst)
    hit = lst.cache.get(key)
    if hit is not None:
        version, appends, count, grid = hit
        if version == lst.version:
            return cast(PointGrid, grid)
        # EVERY change since was an append (the version moved exactly as far as the append counter),
        # so the index is not stale - it is merely SHORT, and appending to a grid is exact. This is
        # what keeps an accreting registry cheap: `placed` grows ~1,000 times per city map with
        # queries interleaved, and rebuilding all of it per append would cost more than the scan
        # being replaced.
        if add is not None and lst.version - version == lst.appends - appends:
            add(cast(PointGrid, grid), lst[count:])
            lst.cache[key] = (lst.version, lst.appends, len(lst), grid)
            return cast(PointGrid, grid)
    fresh = build(lst)
    lst.cache[key] = (lst.version, lst.appends, len(lst), fresh)
    return fresh


def boxed_grid(boxed: Any) -> PointGrid:
    """A PointGrid over already-boxed items, for a caller that builds its keep-outs ONCE per region
    and then queries them per scatter point. `boxed_hit`/`boxed_seg_hit` accept the narrowed list
    `near` returns, so switching a linear prefilter to an index is a two-line change at the call
    site and the exact tests underneath are untouched."""
    grid = PointGrid()
    grid.extend(boxed)
    return grid


class PointGrid:
    """A uniform-grid spatial index for POINT queries against many static extents.

    PREFILTER family, like `boxed_hit` one level up: the grid narrows the CANDIDATE LIST, the
    caller's exact test still DECIDES, so verdicts match a linear scan exactly - which is what lets
    the pool regenerate byte-identical when a caller switches over.

    WHY IT EXISTS. A bbox prefilter drops the cost per item but still visits EVERY item, and some
    of this engine's per-candidate scans are long: Minami's well siting probes ~133k seats against
    ~580 watercourse segments plus 927 paddy rings (~123M box comparisons, 74% of that gen), and
    `_fits` measures every candidate against every building already standing. `check_village.py`
    solved exactly this on the CHECKING side with `GridIndex` (whole-pool gate 34.1s -> 11.8s); the
    GENERATOR side had no equivalent until 2026-08-03.

    Items are `(payload..., x0, y0, x1, y1)` - the box is the LAST FOUR fields, the shape
    `boxed_polys` and `boxed_segs` already produce. Filing is INCREMENTAL (`extend` appends), which
    is exact for an append-only registry like `Settlement.placed`, so a growing list is indexed as
    it grows instead of rebuilt.

    A GRID BOX IS A COST, SO IT IS CLAMPED - the lesson recorded in this skill's CLAUDE.md, learned
    when a negative fixture's 9,000,000px vertex asked the checker's index for ~5.6 billion cells
    and the gate ate gigabytes. An item spanning more than `_MAX_SPAN` cells on either axis is
    filed as OVERSIZED and returned by every query. That makes a wild coordinate cheap rather than
    unbounded, and it cannot change a verdict: an oversized item is simply never pruned."""

    __slots__ = ("buckets", "cell", "n", "oversized")
    _MAX_SPAN = 64  # cells per axis before an item is oversized (64 * 128px = 8,192px - wider than any canvas we draw)

    def __init__(self, cell: float = 128.0) -> None:
        self.cell = cell
        self.buckets: dict[tuple[int, int], list[Any]] = {}
        self.oversized: list[Any] = []
        self.n = 0  # items filed so far - an append-only source hands in only the tail

    def extend(self, items: Any) -> None:
        c = self.cell
        for item in items:
            self.n += 1
            i0, j0 = int(item[-4] // c), int(item[-3] // c)
            i1, j1 = int(item[-2] // c), int(item[-1] // c)
            if i1 - i0 > self._MAX_SPAN or j1 - j0 > self._MAX_SPAN:
                self.oversized.append(item)
                continue
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    self.buckets.setdefault((i, j), []).append(item)

    def near(self, px: float, py: float, pad: float = 0.0) -> Any:
        """Every filed item whose box comes within `pad` of (px, py) - plus, harmlessly, some that
        do not, and possibly the same item twice (an item spanning several queried cells). It never
        OMITS one that does, which is the only property the callers' exactness rests on."""
        c = self.cell
        i0, j0 = int((px - pad) // c), int((py - pad) // c)
        i1, j1 = int((px + pad) // c), int((py + pad) // c)
        if i0 == i1 and j0 == j1 and not self.oversized:  # the common case - one cell, no copy
            return self.buckets.get((i0, j0)) or ()
        out: list[Any] = list(self.oversized)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                bucket = self.buckets.get((i, j))
                if bucket:
                    out.extend(bucket)
        return out
