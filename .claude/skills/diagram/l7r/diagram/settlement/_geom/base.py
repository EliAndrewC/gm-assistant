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


def _assert_not_main_tree(path: str | None = None) -> None:
    """Refuse to run from the MAIN /gm-assistant checkout. Main is the integration point,
    never a workspace (CLAUDE.md "Session clones"): a generator/gate/test writing into main's
    tree races with another session's mid-ritual push-to-checkout (the 2026-07-20 double-push
    post-mortem). Import-time enforcement here covers every Mode B gen, check_village.py, and
    the pytest suites, since they all import this module. GM_ASSISTANT_ALLOW_MAIN=1 overrides
    the guard: the GM sets it for a deliberate main-tree run, and the stop-work ritual's
    render-sync sets it (scoped to its one locked regen-in-main); a session never sets it by
    hand for anything else."""
    p = os.path.realpath(path if path is not None else __file__)
    if p.startswith("/gm-assistant/") and "/.clones/" not in p and os.environ.get("GM_ASSISTANT_ALLOW_MAIN") != "1":
        raise SystemExit(
            "ERROR: this ran from the MAIN /gm-assistant tree. Main is the integration point, never a workspace -\n"
            "every generator, gate, and test runs inside the session's own clone under /gm-assistant/.clones/.\n"
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
# CROWN FILLS - every colour the engine paints a tree CROWN with, in one place so a reader of the
# ink can find them all. `tools/scatter_audit.py` imports this rather than carrying its own copy:
# it used to hardcode #6E8B4A / #7C9856 / #87A45C, none of which the engine has drawn for some time,
# so the audit parsed ZERO crowns on maps recording thousands and still printed "crown checked".
# A palette copied into a reader is a copy that drifts, and this one drifted silently because
# nothing compared the two. (Two conifer greens are listed because the woodland stand and the
# homestead grove each picked their own - #4A6733 and #496733 - which is itself a small drift, left
# alone deliberately: unifying them would change committed ink for no gain the eye can see.)
CROWN_FILLS = ('#4A6733', '#496733', '#6E8B43', '#7C9A4E')
RICE_GREENS = ['#A6C398', '#A2C094', '#A9C69C']  # rice at ONE stage - near-identical greens (reads uniform)
