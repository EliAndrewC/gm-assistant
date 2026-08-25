"""What every other submodule of _geom needs first: the coordinate type aliases, the
import-time main-tree guard, and the land/crop palette.

The last two are not geometry, and are here rather than anywhere better because feature 025's
positional cut put them in _geom.py. They sit at the bottom of the layering rule (base <-
primitives <- overlap <- everything else), which is the one placement that costs nothing: the
guard must run on ANY import of the package, and it does, because every submodule's star import
in __init__.py reaches this one.

Split from settlement/_geom.py by feature 117 - see settlement/_geom/CLAUDE.md for the index.
"""

import os
from typing import Any

Pt = tuple[float, float]  # an (x, y) point in map pixels
Poly = list[Pt]  # a polyline / polygon as a list of points
Manifest = dict[str, Any]  # the JSON settlement manifest the generator emits


def _is_main_tree(p: str) -> bool:
    """True when `p` (a real path) sits inside a checkout that holds `.clones/` and is not itself
    under one - i.e. the integration tree, whichever repository and mount this is."""
    if "/.clones/" in p:
        return False
    d = p if os.path.isdir(p) else os.path.dirname(p)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return os.path.isdir(os.path.join(d, ".clones"))
        parent = os.path.dirname(d)
        if parent == d:
            return False
        d = parent


def _assert_not_main_tree(path: str | None = None) -> None:
    """Refuse to run from the MAIN checkout (the tree that holds .clones/). Main is the integration point,
    never a workspace (CLAUDE.md "Session clones"): a generator/gate/test writing into main's
    tree races with another session's mid-ritual push-to-checkout (the 2026-07-20 double-push
    post-mortem). Import-time enforcement here covers every Mode B gen, check_village.py, and
    the pytest suites, since they all import this module. GM_ASSISTANT_ALLOW_MAIN=1 overrides
    the guard: the GM sets it for a deliberate main-tree run, and the stop-work ritual's
    render-sync sets it (scoped to its one locked regen-in-main); a session never sets it by
    hand for anything else."""
    # MAIN IS THE TREE THAT CONTAINS `.clones/` (feature 131, 2026-08-25). A session clone or a
    # detached worktree has no .clones/ of its own (it is gitignored), so no path is hardcoded and
    # the guard holds at /gm-assistant and at /diagram alike. Same rule as webapp/mainguard.py.
    p = os.path.realpath(path if path is not None else __file__)
    if _is_main_tree(p) and os.environ.get("GM_ASSISTANT_ALLOW_MAIN") != "1":
        raise SystemExit(
            "ERROR: this ran from the MAIN tree. Main is the integration point, never a workspace -\n"
            "every generator, gate, and test runs inside the session's own clone under <main>/.clones/.\n"
            "Check CLAUDE.md, section 'Session clones' (reload CLAUDE.md if it has fallen out of your context\n"
            "window) for the procedure: create or reuse .clones/<kebab-cased-session-name>, sync it in with\n"
            "'git pull origin main', and run this same command from inside that clone.\n"
            "(GM override for a deliberate main-tree run: GM_ASSISTANT_ALLOW_MAIN=1)"
        )


_assert_not_main_tree()

LAND = '#EFE3C2'
PADDY_SHADES = ['#A7C49C', '#9FBE93', '#AECBA1', '#9BBA8F', '#B4CCA6']  # rice mid-growth (green)
FLOODED_SHADES = ['#93B0A2', '#8AAB9A', '#9DBAAB', '#88A99A', '#9AB6A8']  # just-transplanted paddy (water+shoots, blue-green)
RIPE_SHADES = ['#CBBB74', '#C4B36A', '#D1C180']  # ripening rice (golden) - a few plots
# CROWN FILLS - every color the engine paints a RECORDED tree crown with. `tools/scatter_audit.py`
# imports this rather than carrying its own copy.
#
# THE LIST IS THE AUTHORITY AND IT IS CHECKED, because a hand-written "exhaustive" list is a claim
# and claims rot. It has now rotted TWICE in one day. First the audit hardcoded #6E8B4A / #7C9856 /
# #87A45C and parsed ZERO crowns on maps recording thousands. Then this constant replaced them with
# the four fills two of the three drawing sites use - and asserted in its own comment that the
# engine "has not painted [the old three] for some time", which was FALSE: `land/cover.py` paints
# every woodland-commons canopy with exactly those three, two lines above the `M["tree_crowns"] +=`
# that records them. The audit went from 0% to 63% coverage and still printed "crown checked".
# `test_crown_fills_covers_every_recorded_crown` regenerates a map and compares parsed against
# recorded, so the next drift fails instead of narrowing the count.
#
# The three sites, and why they differ: `shrines_wells/woods.py` (tree stands) and
# `homestead_parts.py` (homestead groves) each pick a conifer green and two broadleaf greens -
# #4A6733 vs #496733 is a small unintended drift between them, left alone because unifying it would
# change committed ink for no gain the eye can see. `land/cover.py` (woodland commons) kept an older
# triple. `homestead_parts.py` also caps bamboo with #BBD06A, recorded like any other crown.
CROWN_FILLS = (
    '#4A6733',  # woods.py conifer
    '#496733',  # homestead_parts.py conifer (the drift above)
    '#6E8B43',  # both, broadleaf
    '#7C9A4E',  # both, broadleaf
    '#6E8B4A',  # land/cover.py woodland commons
    '#7C9856',  # land/cover.py woodland commons
    '#87A45C',  # land/cover.py woodland commons
    '#BBD06A',  # homestead_parts.py bamboo top
)
RICE_GREENS = ['#A6C398', '#A2C094', '#A9C69C']  # rice at ONE stage - near-identical greens (reads uniform)
