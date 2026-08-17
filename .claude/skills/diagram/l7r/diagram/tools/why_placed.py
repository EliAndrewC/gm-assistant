#!/usr/bin/env python3
"""Ask a settlement gen WHY something is where it is - who placed it, or what refused to place there.

WHY THIS EXISTS (GM 2026-08-08). "Which call put this building here?" is not answerable from the
manifest: a record carries its geometry and nothing about its provenance, and the engine has ~200
methods that can append one. A profiled session spent roughly ten sequential greps through
the `settlement/` package and the gen chasing a single servant house - reading `top_up`, then `servant_ranges`,
then the apron block polys, then `_fits` - and none of them answered it. What DID answer it, first
try and in one run, was eight lines of throwaway monkeypatch that wrapped `M["buildings"]` and
printed a stack trace on append. This is that, made permanent and given the second half of the
question too.

Two modes, and they are the two halves of every placement puzzle:

    # WHO put a feature here? (and what else is recorded at that spot)
    python3 -m l7r.diagram.tools.why_placed pool/provincial-cities/nagahara.gen.py --at 1102.6,1429.5

    # WHY did nothing land here? (which observed test refused the candidates)
    python3 -m l7r.diagram.tools.why_placed pool/provincial-cities/nagahara.gen.py --refused 1102.6,1429.5

`--at` reports every manifest record appended within the radius, with the gen line and the
`settlement/` call chain that produced it. `--refused` reports the `_fits` calls made near the
point, how many were refused, and WHICH SUB-TEST said no - observed by watching the real predicates
return, never by restating their logic here. That distinction is the same one `site_justice.py`'s
docstring draws and it matters for the same reason: a tool that re-implements a rule drifts from it,
and then confidently tells you the wrong thing.

Both modes run the gen once with rendering skipped (~1-15s depending on the map).
"""

from __future__ import annotations

import argparse
import contextlib
import math
import os
import runpy
import sys
import traceback
from collections.abc import Iterator, Sequence
from typing import Any

from l7r.diagram import settlement

# Frames from these files are plumbing, not an answer - the tracer's own, and the stdlib's runner.
_NOISE = ("why_placed.py", "runpy.py", "<frozen runpy>", "traceback.py")


class Hit:
    """One recorded placement near the target: the manifest key, the record, and the call chain."""

    def __init__(self, key: str, rec: dict[str, Any], frames: Sequence[tuple[str, int, str]]) -> None:
        self.key = key
        self.rec = rec
        self.frames = list(frames)


def near(rec: dict[str, Any], x: float, y: float, radius: float) -> bool:
    """Whether a manifest record sits within `radius` of (x, y).

    Prefers the record's own centre; falls back to the vertices of a `poly`/`outline` ring so
    ring-shaped features (fields, flower beds, groves recorded as outlines) are findable too. A
    record with no position at all can never match."""
    if "x" in rec and "y" in rec:
        return math.hypot(float(rec["x"]) - x, float(rec["y"]) - y) <= radius
    ring = rec.get("poly") or rec.get("outline")
    if isinstance(ring, list) and ring and isinstance(ring[0], (list, tuple)) and len(ring[0]) >= 2:
        return any(math.hypot(float(p[0]) - x, float(p[1]) - y) <= radius for p in ring)
    return False


def useful_frames(stack: Sequence[Any], limit: int = 6) -> list[tuple[str, int, str]]:
    """The call chain worth printing: drop this file and the stdlib runner, keep the rest INNERMOST
    LAST, capped. The gen line tells you which call site to go and look at; the settlement/ engine frames
    under it tell you which engine method chose the spot."""
    out: list[tuple[str, int, str]] = []
    for fr in stack:
        path = str(getattr(fr, "filename", ""))
        if any(n in path for n in _NOISE):
            continue
        out.append((os.path.basename(path), int(getattr(fr, "lineno", 0) or 0), str(getattr(fr, "name", "?"))))
    return out[-limit:]


class _Sink:
    def __init__(self, x: float, y: float, radius: float, keys: tuple[str, ...] | None) -> None:
        self.x, self.y, self.radius, self.keys = x, y, radius, keys
        self.hits: list[Hit] = []

    def consider(self, key: str, rec: dict[str, Any]) -> None:
        if self.keys and key not in self.keys:
            return
        if near(rec, self.x, self.y, self.radius):
            self.hits.append(Hit(key, dict(rec), useful_frames(traceback.extract_stack())))


class _WatchList(list):  # type: ignore[type-arg]
    """A manifest list that reports dict appends near the target."""

    def __init__(self, key: str, seq: Sequence[Any], sink: _Sink) -> None:
        super().__init__(seq)
        self._key = key
        self._sink = sink

    def append(self, rec: Any) -> None:
        if isinstance(rec, dict):
            self._sink.consider(self._key, rec)
        super().append(rec)


class _WatchDict(dict):  # type: ignore[type-arg]
    """`s.M`, wrapping every list it ever holds - including ones created later by `setdefault`,
    which is how `farm_sheds` and several other keys come into being."""

    def __init__(self, base: dict[str, Any], sink: _Sink) -> None:
        super().__init__()
        self._sink = sink
        for k, v in base.items():
            dict.__setitem__(self, k, _WatchList(k, v, sink) if isinstance(v, list) else v)

    def __setitem__(self, k: str, v: Any) -> None:
        dict.__setitem__(self, k, _WatchList(k, v, self._sink) if isinstance(v, list) and not isinstance(v, _WatchList) else v)

    def setdefault(self, k: str, default: Any = None) -> Any:
        if k not in self:
            self[k] = default
        return self[k]


@contextlib.contextmanager
def watching(x: float, y: float, radius: float = 8.0, keys: tuple[str, ...] | None = None) -> Iterator[list[Hit]]:
    """Patch `Settlement` so every manifest record appended within `radius` of (x, y) is captured
    with its call chain. Restores the class on exit."""
    sink = _Sink(x, y, radius, keys)
    orig = settlement.Settlement.__init__

    def patched(self: Any, *a: Any, **kw: Any) -> None:
        orig(self, *a, **kw)
        self.M = _WatchDict(self.M, sink)

    settlement.Settlement.__init__ = patched  # type: ignore[method-assign]
    try:
        yield sink.hits
    finally:
        settlement.Settlement.__init__ = orig  # type: ignore[method-assign]


class Refusal:
    """One `_fits` call near the target, and the sub-test observed refusing it."""

    def __init__(self, w: float, h: float, verdict: bool, cause: str, frames: Sequence[tuple[str, int, str]]) -> None:
        self.w, self.h, self.verdict, self.cause = w, h, verdict, cause
        self.frames = list(frames)


@contextlib.contextmanager
def watching_fits(x: float, y: float, radius: float = 8.0) -> Iterator[list[Refusal]]:
    """Capture every `_fits` candidate within `radius` of (x, y), with the OBSERVED reason.

    The cause is read off the real sub-predicates as they run - `_in_blocked`, `_near_corridor`,
    `_hard_clear` - not re-derived here. When `_fits` refuses and none of those did, the refusal
    came from a clause with no separate predicate (the canvas edge, the bound ring, or a standing
    footprint's collision circle), and it is reported as exactly that much. Naming it more precisely
    would mean restating `_fits` in this file, which is how a diagnostic starts lying."""
    out: list[Refusal] = []
    S = settlement.Settlement
    o_fits, o_blocked, o_corr, o_hard = S._fits, S._in_blocked, S._near_corridor, S._hard_clear
    seen: dict[str, bool] = {}

    def blocked(self: Any, px: float, py: float) -> bool:
        r = o_blocked(self, px, py)
        seen["_in_blocked"] = r
        return r

    def corr(self: Any, px: float, py: float, skip: Any = None) -> bool:
        r = o_corr(self, px, py, skip)
        seen["_near_corridor"] = r
        return r

    def hard(self: Any, px: float, py: float, w: float, h: float) -> bool:
        r = o_hard(self, px, py, w, h)
        seen["_hard_clear"] = r
        return r

    # *a/**kw passthrough, NOT a restated signature (2026-08-11): this wrapper pinned _fits's
    # parameter list, so the day _fits gained a keyword the diagnostic died with a TypeError -
    # in the middle of the gen it was supposed to be observing. A tool that OBSERVES must not
    # re-declare the thing it observes; same rule as asking the gate instead of re-deriving it.
    def fits(self: Any, px: float, py: float, w: float, h: float, *a: Any, **kw: Any) -> bool:
        watched = math.hypot(px - x, py - y) <= radius
        if watched:
            seen.clear()
        verdict = o_fits(self, px, py, w, h, *a, **kw)
        if watched:
            if verdict:
                cause = "-"
            elif seen.get("_in_blocked"):
                cause = "_in_blocked (a block_poly keep-out - CENTRE-tested)"
            elif seen.get("_near_corridor"):
                cause = "_near_corridor (a way's cleared band)"
            elif seen.get("_hard_clear") is False:
                cause = "_hard_clear (crop/pond/bog/ditch - FOOTPRINT-tested)"
            else:
                cause = "the canvas edge, the bound ring, or a standing footprint's collision circle"
            out.append(Refusal(w, h, verdict, cause, useful_frames(traceback.extract_stack())))
        return verdict

    S._fits, S._in_blocked, S._near_corridor, S._hard_clear = fits, blocked, corr, hard  # type: ignore[method-assign,assignment]
    try:
        yield out
    finally:
        S._fits, S._in_blocked, S._near_corridor, S._hard_clear = o_fits, o_blocked, o_corr, o_hard  # type: ignore[method-assign]


def run_gen(path: str) -> None:
    """Execute a gen the way the gate does, with the renderer skipped (the PNG is not the question).

    The gen's own stdout is silenced: it prints shortfall and census lines that would bury the
    report. Its directory goes on `sys.path` so `import settlement` resolves the module we patched,
    never a second copy."""
    d = os.path.dirname(os.path.abspath(path))
    if d not in sys.path:
        sys.path.insert(0, d)
    os.environ["DIAGRAM_SKIP_RENDER"] = "1"
    try:
        with open(os.devnull, "w") as devnull, contextlib.redirect_stdout(devnull):
            runpy.run_path(path, run_name="__main__")
    finally:
        os.environ.pop("DIAGRAM_SKIP_RENDER", None)


def report_hits(hits: Sequence[Hit], x: float, y: float, radius: float) -> str:
    if not hits:
        return f"nothing recorded within {radius:g} px of ({x:g}, {y:g}).\nTry a bigger --radius, or --refused to ask what stopped anything landing there."
    lines = [f"{len(hits)} record(s) placed within {radius:g} px of ({x:g}, {y:g}):"]
    for h in hits:
        rec = h.rec
        what = rec.get("kind") or rec.get("name") or rec.get("label") or rec.get("role") or ""
        pos = f"({rec['x']:g}, {rec['y']:g})" if "x" in rec and "y" in rec else "(ring)"
        size = f" {rec['w']:g}x{rec['h']:g}" if "w" in rec and "h" in rec else ""
        rot = f" rot={rec['rot']:g}" if rec.get("rot") else ""
        lines.append(f"\n  {h.key}: {what} {pos}{size}{rot}")
        for name, lineno, fn in h.frames:
            lines.append(f"      {name}:{lineno}  {fn}()")
    return "\n".join(lines)


def report_refusals(refs: Sequence[Refusal], x: float, y: float, radius: float) -> str:
    if not refs:
        return f"no candidate was ever tested within {radius:g} px of ({x:g}, {y:g}) - nothing tried to build there.\nThe ground is not refused, it is UNVISITED: look at the region the placer was given, not at the keep-outs."
    bad = [r for r in refs if not r.verdict]
    lines = [f"{len(refs)} candidate(s) tested within {radius:g} px of ({x:g}, {y:g}); {len(bad)} refused, {len(refs) - len(bad)} accepted."]
    causes: dict[str, int] = {}
    for r in bad:
        causes[r.cause] = causes.get(r.cause, 0) + 1
    for cause, n in sorted(causes.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {n:5d}  {cause}")
    if bad:
        lines.append("\ndeepest caller of the last refusal:")
        for name, lineno, fn in bad[-1].frames:
            lines.append(f"      {name}:{lineno}  {fn}()")
        lines.append(f"      (candidate footprint {bad[-1].w:g}x{bad[-1].h:g})")
    return "\n".join(lines)


def parse_point(s: str) -> tuple[float, float]:
    try:
        a, b = s.split(",")
        return float(a), float(b)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"want x,y - got {s!r}") from e


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ask a settlement gen why something is (or is not) at a point.")
    ap.add_argument("gen", help="path to a *.gen.py")
    ap.add_argument("--at", type=parse_point, help="x,y - report who placed the records here")
    ap.add_argument("--refused", type=parse_point, help="x,y - report what refused candidates here")
    ap.add_argument("--radius", type=float, default=8.0, help="match radius in px (default 8)")
    ap.add_argument("--key", action="append", help="restrict --at to this manifest key (repeatable)")
    a = ap.parse_args(argv)
    if not a.at and not a.refused:
        ap.error("one of --at or --refused is required")
    if a.at:
        with watching(a.at[0], a.at[1], a.radius, tuple(a.key) if a.key else None) as hits:
            run_gen(a.gen)
        print(report_hits(hits, a.at[0], a.at[1], a.radius))
    else:
        with watching_fits(a.refused[0], a.refused[1], a.radius) as refs:
            run_gen(a.gen)
        print(report_refusals(refs, a.refused[0], a.refused[1], a.radius))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
