#!/usr/bin/env python3
"""Render a scripted hamlet ONE STAGE AT A TIME and write an HTML walk-through.

    python3 -m l7r.diagram.tools.placement_stages                 # Inashiro, into dev/placement-stages/
    python3 -m l7r.diagram.tools.placement_stages --width 1400    # bigger plates

WHY THIS EXISTS (GM, 2026-08-20): *"a lot of the bugs that we've been working through feel like they
might have to do with the placement order of things on the map ... I would actually be very curious
to see what the Inashiro map looks like when it is only the water, and then when we have added only
the rice paddy fields, and then at whatever later stage, we have added the houses."*

It is the COMPANION to `dev/placement.md`, not a duplicate of it, and the split is deliberate. That
document is the rulebook a session loads before changing where something is placed - the registries,
the CENTER-vs-FOOTPRINT trap, the reserve/fill rule. This is the picture: what the map actually looks
like after each stage, so the sequence can be SEEN rather than reconstructed from thirteen function
names. A reader who has looked at the plates knows immediately why the web cannot run before the
houses, because the plate before it is visibly empty of the things it has to thread between.

It is a by-hand tool (see `pyproject.toml`'s coverage `source` list, which names the measured tools
one by one on purpose), so it is not under the 100% rule. Re-run it whenever `STAGES` changes; the
page is generated, never hand-edited.
"""

from __future__ import annotations

import argparse
import copy
import io
import os
import sys
from contextlib import redirect_stdout
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if SKILL not in sys.path:
    sys.path.insert(0, SKILL)

from l7r.diagram.hamletgen import HamletSpec, plan_site  # noqa: E402
from l7r.diagram.hamletgen.driver import STAGES  # noqa: E402
from l7r.diagram.settlement import Settlement  # noqa: E402

# WHAT EACH STAGE IS FOR, AND WHY IT SITS WHERE IT SITS. Keyed by function name so a reordering of
# `STAGES` reorders the page automatically and a RENAMED or NEW stage shows up as missing prose
# rather than silently inheriting its neighbour's - which is the failure mode a hand-kept list has.
NOTES: dict[str, tuple[str, str]] = {
    "stage_water_frame": (
        "The water skeleton",
        "Everything downstream is derived from this, so it is first. The intake, the head race and the "
        "line the land falls along decide where the field can lie, which decides where the dry margin "
        "is, which is the only ground a settlement can stand on. Nothing here is placed against "
        "anything - there is nothing yet to avoid.",
    ),
    "stage_field": (
        "The paddy",
        "The field is SOLVED for a real acreage rather than drawn to a pixel size, and it is laid before "
        "any built thing exists. That is the ordering decision with the longest reach on the whole map: "
        "the settlement afterwards takes whatever margin the field leaves it. Where that margin curves, "
        "the cluster has to curve with it.",
    ),
    "stage_sink": (
        "Where the runoff goes",
        "The tail drain and its pond or off-map outfall. It runs with the water rather than with the "
        "ground cover because the pond is a HARD feature - houses, lanes and trees all have to avoid it, "
        "so it must exist before any of them are seated.",
    ),
    "stage_ways": (
        "The skeleton and the connector",
        "The ground-RESERVING half of the ways. These lanes are laid BEFORE the houses precisely so the "
        "homesteads front them: a lane is a no-build corridor the steadings line up along. This is the "
        "half of the road network that behaves like terrain.",
    ),
    "stage_homesteads": (
        "The farmhouses",
        "Each bundle is seated against the field edge and packed toward its neighbours. It runs after the skeleton (so houses front lanes) and before everything that fills leftover ground.",
    ),
    "stage_appurtenances": (
        "Yards, gardens, byres, wells, sheds",
        "The rest of each steading, plus the shared fixtures. Kept as its own stage after the houses "
        "because several of them are sited RELATIVE to a house that must already exist - a threshing "
        "yard south of its own farmhouse, a byre off the frontage, a well between steadings.",
    ),
    "stage_web": (
        "The lane web",
        "The ground-FILLING half of the ways, and the one stage that deliberately runs after the "
        "structures it serves. Laid first it competed for ground with the very houses it exists to "
        "reach: measured, the four pool clusters' long axes grew 15-97% and no check measures sprawl. "
        "Laid here it threads the room the cluster actually left. It also runs after the byres and "
        "wells, not merely after the houses - between the two, its corridor reserved courtyard ground "
        "and exiled fixtures up to 210 ft.",
    ),
    "stage_notice": (
        "The notice board",
        "The kosatsuba stands ON a way, so it cannot be placed until the ways are final - which is after "
        "the web, not with the other structures. This is the clearest case on the map of a feature whose "
        "position is defined by something drawn later than itself.",
    ),
    "stage_hinterland": (
        "Scrub and rough grazing",
        "Ground cover fills what is left, so it runs after everything it must avoid. It reads the drawn features as obstacles rather than reserving anything from them.",
    ),
    "stage_woodland": (
        "The woodland commons",
        "Managed coppice on ground nothing else wanted. After the hinterland so it sits in real open ground rather than in ground the scrub was about to take.",
    ),
    "stage_windbreak": (
        "The shelter belt",
        "Sited from the wind and the cluster it shelters, so it needs the cluster finished. Its canopy is "
        "deferred to the flush at the end - drawn here it would be painted over by nothing, but its "
        "crowns must be filtered against every structure, and not all of them exist yet.",
    ),
    "stage_crossings": (
        "Planks and decks",
        "Every way that crosses water gets its deck HERE, which is why the earlier way stages are free to cross a ditch: the crossing is legal because this stage will deck it.",
    ),
    "stage_frame": (
        "Crop, title, scalebar",
        "The canvas is deliberately generous and is cropped to content only now. Erring large is cheap - unused canvas is thrown away - while erring small silently mis-shapes the field.",
    ),
}


def _plate(snap: Settlement, out_dir: str, stem: str, width: int) -> tuple[str, int, int]:
    """Finish a COPY of the part-built settlement and scale its render down to a page plate."""
    from PIL import Image

    base = os.path.join(out_dir, stem)
    with redirect_stdout(io.StringIO()):
        snap.finish(base, render=True)
    png = base + ".png"
    with Image.open(png) as im:
        w, h = im.size
        if w > width:
            im = im.resize((width, max(1, round(h * width / w))), Image.LANCZOS)
        # PALETTISED, because these are flat-colour maps and this page is COMMITTED. At full render
        # size thirteen plates come to 96 MB, which is not a documentation asset, it is a liability -
        # and the whole point is that the page lives in the repo and is re-run when `STAGES` changes.
        # An adaptive 128-colour palette is visually indistinguishable on flat fills and hard strokes
        # while cutting each plate by roughly an order of magnitude.
        im = im.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        im.save(png, optimize=True)
        size = im.size
    # The SVG was only ever a means to the plate; keeping it doubles the directory for nothing.
    if os.path.isfile(base + ".svg"):
        os.remove(base + ".svg")
    if os.path.isfile(base + ".json"):
        os.remove(base + ".json")
    return os.path.basename(png), size[0], size[1]


def build_page(out_dir: str, width: int, spec: HamletSpec) -> str:
    """Roll `spec` one stage at a time, writing a plate per stage and an index page. Returns the path."""
    os.makedirs(out_dir, exist_ok=True)
    plan = plan_site(spec)
    s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
    rows = []
    for i, stage in enumerate(STAGES, 1):
        with redirect_stdout(io.StringIO()):
            stage(s, plan)
        title, why = NOTES.get(stage.__name__, ("(no note yet)", "This stage has no entry in `NOTES` - add one."))
        # A COPY IS FINISHED, NOT THE LIVE SETTLEMENT: `finish` flushes deferred canopies, seats
        # captions and crops, all of which mutate. Snapshotting the real one would change the map the
        # next stage sees, and the page would document a build nobody runs.
        img, iw, ih = _plate(copy.deepcopy(s), out_dir, f"{i:02d}-{stage.__name__}", width)
        rows.append((i, stage.__name__, title, why, img, iw, ih))
        print(f"  {i:>2}. {stage.__name__:<22} -> {img}")

    parts = [
        "<title>Hamlet placement order</title>",
        "<style>",
        ":root{--ink:#241c14;--dim:#6b5d4d;--rule:#d9cdbb;--bg:#fbf7f0;--card:#fff}",
        ':root:not([data-theme="light"]){}',
        "@media (prefers-color-scheme: dark){:root:not([data-theme=\"light\"]){--ink:#ece3d6;--dim:#a2957f;--rule:#3b332a;--bg:#171310;--card:#201a15}}",
        ':root[data-theme="dark"]{--ink:#ece3d6;--dim:#a2957f;--rule:#3b332a;--bg:#171310;--card:#201a15}',
        "body{margin:0;padding:2.5rem 1.25rem 4rem;background:var(--bg);color:var(--ink);",
        "font:16px/1.6 Georgia,'Times New Roman',serif}",
        ".wrap{max-width:1180px;margin:0 auto}",
        "h1{font-size:1.9rem;margin:0 0 .3rem}",
        ".lede{color:var(--dim);max-width:60ch;margin:0 0 2rem}",
        ".stage{background:var(--card);border:1px solid var(--rule);border-radius:6px;",
        "padding:1.1rem 1.25rem 1.4rem;margin:0 0 1.6rem}",
        ".hd{display:flex;gap:.7rem;align-items:baseline;flex-wrap:wrap;margin-bottom:.35rem}",
        ".n{font:700 .95rem/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--dim)}",
        ".t{font-size:1.15rem;font-weight:700}",
        ".fn{font:.85rem/1 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--dim)}",
        ".why{color:var(--ink);max-width:72ch;margin:.2rem 0 .9rem}",
        "img{display:block;width:100%;height:auto;border:1px solid var(--rule);border-radius:3px;background:#fff}",
        "</style>",
        '<div class="wrap">',
        "<h1>Hamlet placement order</h1>",
        f'<p class="lede">{escape(spec.name)}, rolled one stage at a time. Each plate is the map as it stands '
        "after that stage and nothing later - the same build, snapshotted thirteen times. Read "
        "<code>dev/placement.md</code> for the rules; this is what they look like. Generated by "
        "<code>python3 -m l7r.diagram.tools.placement_stages</code> - re-run it when <code>STAGES</code> changes.</p>",
    ]
    for i, fn, title, why, img, iw, ih in rows:
        parts += [
            '<section class="stage">',
            f'<div class="hd"><span class="n">{i:02d}</span><span class="t">{escape(title)}</span><span class="fn">{escape(fn)}</span></div>',
            f'<p class="why">{escape(why)}</p>',
            f'<img src="{escape(img)}" width="{iw}" height="{ih}" alt="{escape(title)}" loading="lazy">',
            "</section>",
        ]
    parts.append("</div>")
    page = os.path.join(out_dir, "hamlet-placement.html")
    with open(page, "w") as fh:
        fh.write("\n".join(parts) + "\n")
    return page


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(SKILL, "dev", "placement-stages"))
    ap.add_argument("--width", type=int, default=1100, help="plate width in px (default 1100)")
    a = ap.parse_args(argv)
    spec = HamletSpec(name="Inashiro", seed=4, households=15, down_deg=90, water_sink="pond")
    page = build_page(a.out, a.width, spec)
    print(f"\nwrote {page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
