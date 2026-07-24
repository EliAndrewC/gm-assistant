#!/usr/bin/env python3
"""hayakawa-magistracy.gen.py - rasterize the hand-authored manor plan.

Mode A magistracy plans are hand-authored svg SOURCE (tracked in git); only the png is
derived. This gen is the pool wiring that keeps the gitignored png fresh in main:
render-sync regenerates every `pool/*/*.gen.py` from its own directory, and a render
with no gen wrapper is a one-off hand render that silently goes stale (the
county-magistracy-example png did exactly that; caught 2026-07-24). This gen writes
nothing but the png - the tracked svg is never touched.

Run:  python3 pool/magistracies/hayakawa-magistracy.gen.py   (from anywhere)
"""

from __future__ import annotations

import os
import subprocess

SVG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hayakawa-magistracy.svg")


def main() -> int:
    if os.environ.get("DIAGRAM_SKIP_RENDER") != "1":
        subprocess.run(
            ["resvg", "--width", "2400", "--serif-family", "DejaVu Serif", SVG, SVG[:-4] + ".png"],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
