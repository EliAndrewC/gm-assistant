"""SeatMemo - the lattice positions a dwelling top-up has already REFUSED, so a later pass over
the same ground does not pay for the same refusal twice.

Its own module because it is its own subject: not an index (it remembers answers, not geometry),
and carrying a long measured rationale that a reader of the indexes never needs.

Split from settlement/_geom.py by feature 117 - see settlement/_geom/CLAUDE.md for the index.
"""

from typing import Any


class SeatMemo:
    """The lattice positions a generator's dwelling top-up has already REFUSED, so a later pass
    over the same ground does not pay for the same refusal a second time.

    WHY IT EXISTS (2026-08-08). Minami's top-up evaluated **511,519 candidate positions** at ~46us
    each - effectively the whole of that gen's 21s, and 2.2x its sibling cities - and **64.6% of
    those visits were RE-visits of a position an earlier pass had already refused at the same
    tightness**. The caller sweeps each caste's regions three times over and then again in
    `fill_exactly`, always on the same fixed 5x6 px lattice, so a target the ground cannot meet
    rescans the identical positions from scratch every time. Merchant houses alone: 295,400 visits,
    20 placements. The per-candidate work was already indexed to the floor by the 2026-08-03/04
    passes, so the only remaining lever was the candidate COUNT.

    IT IS A MINAMI TOOL, AND THAT IS MEASURED, NOT ASSUMED. The same memo was wired into Nagahara
    and Tango and both got SLOWER (9.56 -> 10.29s and 9.71 -> 10.19s): their re-visit share is
    **3.1% and 0.0%**, so every candidate paid the lookup and almost none of them saved a test.
    Minami is the outlier because the Fox eight-temple doctrine puts 8 precincts and 48 monk houses
    inside its walls, its residential packs seat nothing (`PACK SHORTFALL ... 0/300`), and its
    merchant target is unmeetable - which is what produces the repeated whole-region rescans. Do
    not wire this into a gen without measuring that gen's re-visit share first; below roughly a
    third it is a pessimization.

    THE INVARIANT IT RESTS ON. A refusal can only turn into a placement if some obstacle
    DISAPPEARS. Through a top-up phase every registry those tests read - `placed`, `block_polys`,
    `corridors`, `grove_rects`, `hard_polys`, and the manifest's buildings / houses / wells /
    labels - is only ever appended to, and `bound` only ever TIGHTENS (None -> the wall ring). So a
    refused position stays refused, skipping it changes nothing, and the maps regenerate
    byte-identical. That byte-identity is the real proof; everything below is what keeps it true.

    IT CHECKS THE INVARIANT RATHER THAN ASSUMING IT, because this engine has been burned twice by
    a memo that guessed (see `Indexed`: an incremental index over `placed` missed the two sites
    that REBIND it to a filtered copy, and Minami and Nagahara silently lost every garden).
    `sync()` compares a witness per registry and CLEARS everything unless it grew append-only:

    - an `Indexed` registry is exact - `version` moving exactly as far as `appends` means every
      change since was an append or extend, the same test `indexed_grid` uses to keep its grids;
    - a plain list is witnessed by identity + length, so a rebind or a truncation is caught (an
      in-place edit of an existing record is not, and nothing in a top-up phase does that);
    - `bound` may go from None to a ring - that only ADDS a constraint - but never the reverse.

    A violation costs the SPEEDUP, never the map: the memo forgets and the scan does the work
    again. That is the failure mode to preserve in anything built on this.

    THE LOOKUP HAS TO BE CHEAP, because it runs on every candidate including the ones it does NOT
    save - and the sibling cities above are what that costs when it is not worth paying. `level()`
    hands out the refusal set for one (seat, tightness) so the caller hoists that part of the key
    out of its two nested while loops and pays one small tuple and one set probe per candidate."""

    __slots__ = ("_levels", "_s", "_witness")

    def __init__(self, s: Any) -> None:
        self._s = s
        self._levels: dict[Any, set[Any]] = {}
        self._witness: dict[str, Any] = self._snapshot()

    def _snapshot(self) -> dict[str, Any]:
        """(identity, length, version, appends) per registry. version/appends are None for a plain
        list, where length is the only witness available. `bound` is None until a gen sets it."""
        s = self._s
        w: dict[str, Any] = {}
        for name, v in list(vars(s).items()):
            if isinstance(v, list):
                w["s." + name] = (id(v), len(v), getattr(v, "version", None), getattr(v, "appends", None))
        for key, v in s.M.items():
            if isinstance(v, list):
                w["M." + key] = (id(v), len(v), None, None)
        w["bound"] = None if s.bound is None else (id(s.bound), len(s.bound), None, None)
        return w

    @staticmethod
    def _grew(before: dict[str, Any], after: dict[str, Any]) -> bool:
        """Did every registry we had a witness for grow APPEND-ONLY? A registry that appeared since
        is new keep-out ground, which only ever refuses more, so it needs no witness of its own."""
        for name, was in before.items():
            if was is None:
                continue  # only `bound` is ever None, and unset -> set is a TIGHTENING
            now = after.get(name)
            if now is None or now[0] != was[0] or now[1] < was[1]:
                return False  # registry gone, rebound, or shorter: ground may have been freed
            if was[2] is not None and now[2] - was[2] != now[3] - was[3]:
                return False  # an Indexed registry changed by something that was not an append
        return True

    def sync(self) -> None:
        """Call once at the top of each top-up call - and ONLY there, never mid-scan, because a set
        `level()` already handed out goes on being written to. Re-takes the witness, and forgets
        every refusal if the map did anything but grow since the last one."""
        now = self._snapshot()
        if not self._grew(self._witness, now):
            self._levels.clear()
        self._witness = now

    def level(self, *key: Any) -> set[Any]:
        """The set of (x, y) already refused for one kind of seat at one tightness. `key` must name
        everything the verdict depends on beyond the position itself - the kind AND the footprint
        it was measured at, and the pass's padding - or one pass's refusals will silence another's.
        The caller tests and records positions in it directly; that is the whole hot path."""
        return self._levels.setdefault(key, set())
