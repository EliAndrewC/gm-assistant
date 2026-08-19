#!/usr/bin/env python3
"""Find every place a paddy bund steps sideways and carries on parallel to itself.

WHY THIS EXISTS (GM 2026-08-18, reading Inashiro). "The earthen wall is kind of going in a southward
direction, and then instead of just continuing on and meeting at the four way intersection ... it
just goes sharply to the left before going down, thus making these extremely irregular shapes. This
really, really looks like a rendering error." It is one: `close_seams` makes it, the carve does not
(snapshotting the pass's input and output gives 0 steps on Inashiro's 543 carved rings and 28 on the
634 it hands back), and `research/fields.md` "A bund runs on, or it turns for a reason" carries the
research and the mechanism.

WHY A TOOL AS WELL AS A GATE CHECK. `paddy_bunds_do_not_stagger` holds the shape the GM actually
reported - a wall that steps, steps again and steps again - and it is at zero on all four scripted
hamlets, against 6/9/4/7 basins carrying a flight of them before the fix. What it deliberately does
not fail is a SINGLE step: seven of those survive across the four maps, each one an awkward corner
where a scrap of ground had exactly one home and the repair pass could not move the wall without
breaking another rule. This tool holds that stricter, absolute rule, so the residue stays visible
and measured rather than forgotten - `future-work.md` "paddy bunds that step sideways" lists what
refuses each and what it would take to reach zero.

    python3 -m l7r.diagram.tools.jogs pool/hamlets/inashiro.json
    python3 -m l7r.diagram.tools.jogs pool/hamlets/*.json --top 20

Reads the recorded manifest - it does not run the gen - so it costs milliseconds and answers about
exactly the geometry that shipped.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from l7r.diagram.waterfields import jog_vertices  # noqa: E402


def jogs(manifest: dict[str, Any]) -> list[tuple[float, float, float, str]]:
    """Every step in every paddy plot ring, as (x, y, step in real feet, field name), worst first.

    `jog_vertices` works in PIXELS and takes the engine's grain, so the map's `ftpx` is converted the
    way the engine does it (`grain = 2 / ftpx`) rather than by a second, drifting rule of thumb.
    """
    ftpx = float((manifest.get("meta") or {}).get("ftpx") or 1.0)
    grain = 2.0 / ftpx
    out: list[tuple[float, float, float, str]] = []
    for field in manifest.get("fields") or []:
        for ring in field.get("plot_rings") or []:
            pts = [(float(q[0]), float(q[1])) for q in ring]
            for b, c in jog_vertices(pts, grain):
                step = ((c[0] - b[0]) ** 2 + (c[1] - b[1]) ** 2) ** 0.5 * ftpx
                out.append(((b[0] + c[0]) / 2, (b[1] + c[1]) / 2, step, str(field.get("name") or "?")))
    return sorted(out, key=lambda t: -t[2])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="report paddy bunds that step sideways and carry on")
    ap.add_argument("manifests", nargs="+", help="pool manifest .json files")
    ap.add_argument("--top", type=int, default=8, help="how many of the worst steps to list per map")
    args = ap.parse_args(argv)
    worst = 0
    for path in args.manifests:
        with open(path) as fh:
            M = json.load(fh)
        found = jogs(M)
        rings = sum(len(f.get("plot_rings") or []) for f in M.get("fields") or [])
        worst = max(worst, len(found))
        print(f"{os.path.basename(path):24s} {len(found):4d} step(s) in {rings} plot ring(s)")
        for x, y, step, name in found[: args.top]:
            print(f"    ({x:8.1f}, {y:8.1f})  {step:5.1f} ft   {name}")
    return 1 if worst else 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
