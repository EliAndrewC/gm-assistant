#!/usr/bin/env python3
"""Feature 120's one-shot transformer: settlement/land.py -> settlement/land/.

Adapted from feature 118's split_rolling.py, which came from 117's split_geom.py, 116's
split_shrines_wells.py, 114's split_structures.py, 113's split_city.py, 112's split_fields.py and
025's split_settlement.py. The lineage matters because the SLICING RULE is the part worth
preserving, and it is the part a fresh implementation gets wrong.

Run once from .claude/skills/diagram/:

    python3 ../../../specs/120-land-package/split_land.py

then prune the copied import headers with ruff (see PRUNE below) and delete the old file.

WHY the blocks are sliced as (previous node's end + 1 .. this node's end) rather than by the node's
own lineno: that span carries the DECORATOR lines (ast reports FunctionDef.lineno at the `def`, not
at the decorator above it), the blank lines, and any comment block written above the member.
Slicing by node.lineno silently drops all three. land.py has no decorators, but it is dense with
comment banks that ARE researched grounding - the perimeter dike's wei-tian sourcing, the sluice-gap
ruling, the toe band's alluvial-fan correction, the swept verge's inward-only-bay argument - and a
"pure move" that drops a why-comment is not pure. The quickstart counts comment lines rather than
trusting this docstring.

THREE THINGS ARE NEW HERE, and each is a place a fresh implementation would lose something:

  - **The source has a MODULE-LEVEL TAIL.** `surface_water_dist` is defined AFTER `class LandMixin`
    ends, so a transformer that slices only the class body would drop it silently and every consumer
    of `settlement.surface_water_dist` would break at import. 112-118 all split files that ended
    with their class. The tail is captured explicitly and appended to TAIL_MODULE.

  - **Three members RELOCATE OUT of the package**, into settlement/homestead_parts.py. They are
    `_attach_grove`, `_find_appurtenances` and `_farmstead_nudges`, and every function they call
    (`_draw_grove`, `_find_yard_spot`, `_farm_shed_rect`, `_find_garden_spot`) is already defined
    there. Packaging them as a 27-line submodule would enshrine feature 025's positional accident;
    moving them removes it. They are appended to HomesteadPartsMixin, whose body runs to EOF, and
    they keep their ONE-dot imports because they stay at the same package depth - which is why the
    relative-import rewrite below is applied to the land/ blocks ONLY.

  - **One cross-module comment reference is REPOINTED.** `marsh`'s bucketed-blades note says "see
    the note in `commons`", and the two land in different modules now. REPOINT rewrites it and
    ASSERTS it fired exactly once - a silently-missed rewrite is the failure mode, since nothing
    downstream reads a comment. (The other candidate, hinterland's "see the comment at the marsh
    block", needs no rewrite: that comment is inside hinterland's own `if marsh:` block and travels
    with it.)

RETIRED, and the paths below are the ones it RAN against (2026-08-17, at commit 56f6dfb). Feature
119's relocation landed while this feature was in flight and moved the whole engine to
`l7r/diagram/`, so a re-run today would need `SRC`/`PKG`/`RELOC_FILE` re-rooted there and the
in-body `from waterfields import ...` rewrite that the relocation applied. The paths are left as
they were rather than "fixed", because this file's value is the record of what was actually
executed - see research.md R9 for the merge and how it was resolved.
"""

import ast
import pathlib
import sys

SRC = pathlib.Path("settlement/land.py")
PKG = pathlib.Path("settlement/land")
RELOC_FILE = pathlib.Path("settlement/homestead_parts.py")
RELOC_CLASS = "HomesteadPartsMixin"

# The partition, per specs/120-land-package/data-model.md: module -> (mixin name, docstring, member
# names). Members are written in SOURCE order regardless of the order listed here.
#
# The axis is SUBJECT, not stage. Unlike rolling.py (a chain: roll -> seed -> shape -> test -> place
# -> draw), land.py is a RESIDUE BUCKET left by feature 025's positional cut - four unrelated land
# subsystems that happened to sit next to each other in the 16,016-line original. So the test of the
# partition is that a real task stays inside one module, not that the modules form a sequence.
MODULES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "dikes": (
        "DikeMixin",
        "The polder PERIMETER DIKE, and the village that stands on its crest.\n\nOne subject in two halves. `perimeter_dike` draws the earthwork itself - an irregular hand-piled\nband whose OUTER face follows the natural water edge in gentle curves (the fish-scale polder form;\nthe dead-straight right-angled rectangle is a post-1949 industrial shape), planted with a willow row\non the water face and a mulberry row on the inner one, and NOTCHED where a channel crosses it.\n`dike_top_houses` puts a single file of farmhouses ON the crest, each on its own widened platform -\nthe settlement form for an islet polder where the dike's raised earth is the only dry ground there\nis.\n\nThey are one module because the second reads the `crest` centerline the first records. Change the\ndike's geometry and the village on it moves; that coupling is the reason to keep them together and\nthe reason a session loading one wants the other in front of it.",
        ("perimeter_dike", "dike_top_houses"),
    ),
    "wet": (
        "WetGroundMixin",
        "WET GROUND: the reed marsh, the contour band that decides where it lies, the trim that keeps a\nway out of it, and the package's one surface-water distance predicate.\n\nThe BAND is the load-bearing idea. Wet ground is defined by HEIGHT, so `toe_band` returns a CONTOUR\nband perpendicular to the fall rather than an axis-aligned box - a rectangle is only an honest\ncontour at a 0/90/180/270 fall, and at a diagonal it slices across the slope. Its WIDTH comes from\nthe ground the fan waters, never from the canvas: an alluvial fan's spring line follows the FAN's\ntoe, and a floodplain's backswamp is bounded by its natural levees, so wet ground is FEATURE-bounded\nin both landforms (research/water.md, 'The wet toe is as wide as the FAN'). Both corrections are\nargued at length in the members themselves; read them before changing either.\n\n`surface_water_dist` is module-level rather than a mixin method: it takes a MANIFEST, not a\nSettlement, and it is the ONE predicate shared by the gate's `settlement_dwellings_watered` and by\n`hamletgen.place_wells` - written that way because the two had drifted into separate definitions of\n\"needs a well\". It lives in this module because it is this package's water-distance question.\n`settlement/__init__.py` re-exports it, so consumers import it from `settlement` and never from\nhere.",
        ("marsh", "trim_off_marsh", "toe_band"),
    ),
    "cover": (
        "GroundCoverMixin",
        "The DRY ground cover, the layout that lays it, and the swept verge it must skip.\n\n`commons` is the feathered scatter - coarse grass and brush with a few scraggly pines, open grazing\ngrass, or a spaced coppice canopy, by `role`. `hinterland` is the COMPOSER: it decides which frame\nsides carry scrub, which side is the downhill toe, and fills the interior voids an irregular field\nleaves inside its own bbox; it asks wet.py for the toe band and hands it to `commons` as a keep-out\nso the two never overlap. `_clear_ground` / `reserve_clearing` reserve the swept ground around a\nsacred or funerary feature.\n\nThe verge belongs in THIS module rather than with the features it protects, because the scatters are\nwhat must skip it: `clearings` is a keep-out registry this module both writes and reads, and a\nclearing registered after its scatter has run does nothing at all (`scatter_respects_swept_\nclearings` checks exactly that ordering).\n\nNO SOLID FILL is the rule the scatters are built on. A filled polygon always has a crisp geometric\nEDGE, so each land type is defined PURELY by cover that thins to nothing at its margin - the ground\nhas no boundary, just its cover petering out.",
        ("commons", "hinterland", "_clear_ground", "reserve_clearing"),
    ),
    "nearring": (
        "NearRingMixin",
        "NEAR-RING FARMLAND: the packed working ground immediately outside a town or a city.\n\nTwo tilers over one set of keep-outs, and the ORDER between them is part of the design - paddy runs\nfirst and grain fills only what paddy did not. A market town sits in the middle of its best land and\nthe near ring is the part worked hardest (the von Thuenen intensity gradient), so the flat near ring\nis cropland and the labor-limited fallow retreats to the far margins.\n\nThe rule both are built on: a basin is placed ONLY where it can be LEGITIMATELY WATERED. Ground with\nno reachable water is SKIPPED rather than given conjured hydrology - where the near ring genuinely\nlacks water, draw fewer basins, do not fake it.\n\nRead `near_ring_cropland`'s `_blocked` / `_blocked_region` pair before changing either. The cheap\npoint test is a PREFILTER and the region test is what DECIDES: center-plus-corners sampling leaks,\nbecause a small keep-out sitting against the middle of a cell EDGE touches neither the center nor\nany corner, which is how a wellhead once ended up 1 px inside a hatake plot.",
        ("near_ring_cropland", "near_ring_paddy"),
    ),
}

# The module-level statements AFTER `class LandMixin` ends - here, `surface_water_dist`. See the
# docstring: this is the first file in the lineage with a tail, and dropping it would break every
# consumer of `settlement.surface_water_dist` at import time.
TAIL_MODULE = "wet"

# Members that leave the package entirely, appended to RELOC_CLASS in RELOC_FILE. See the docstring.
RELOCATE: tuple[str, ...] = ("_attach_grove", "_find_appurtenances", "_farmstead_nudges")

# `_farmstead_nudges` is annotated `-> Iterator[...]`, and homestead_parts.py imports only Sequence
# from collections.abc. mypy --strict is what would catch this; fixing it here keeps the transform
# a single step.
RELOC_IMPORT_FIX = ("from collections.abc import Sequence", "from collections.abc import Iterator, Sequence")

# Section-divider comments describing the OLD file's layout, which would be actively misleading once
# the sections live in different files. land.py has NONE - it was cut positionally out of
# settlement.py and never grew banners. The hook is kept because every predecessor needed it.
DROP_BANNERS: tuple[str, ...] = ()

# Comment sentences whose target crosses a module boundary. Each is asserted to fire EXACTLY once.
REPOINT: tuple[tuple[str, str], ...] = (("see the note in `commons`", "see the note in cover.py's `commons`"),)


def member_name(node: ast.stmt) -> str | None:
    """The class-body member's name, for a def or a simple class-level assignment."""
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        return node.name
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def deepen(text: str) -> str:
    """Rewrite one-dot relative imports to two-dot, for a block moving one level down into land/.

    Applied to the land/ blocks ONLY. The relocated members stay at settlement/ depth, so applying
    it to them would point them at a package that does not exist. Feature 113 found a LAZY in-body
    `from .core import Settlement` doing exactly that; land.py's in-body imports are
    `from waterfields import ...`, which is absolute and unaffected, so this is free insurance.
    """
    for old, new in (("from ._geom import", "from .._geom import"), ("from ._knobs import", "from .._knobs import"), ("from .core import", "from ..core import")):
        text = text.replace(old, new)
    return text


def main() -> int:
    src = SRC.read_text()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LandMixin")

    # The parent header: everything above `class LandMixin:`. Copied wholesale into each module and
    # pruned by ruff afterwards (PRUNE below) - which reaches the same end state as computing each
    # module's used names by hand, without this script having to model name resolution.
    header = deepen("".join(lines[: cls.lineno - 1]))
    header = header.replace('"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""\n', "")

    # Slice every class-body member into a block carrying its decorators, blanks and comment bank.
    blocks: dict[str, str] = {}
    cursor = cls.lineno  # 1-based line of `class LandMixin:`; body text starts on the next line
    for node in cls.body:
        name = member_name(node)
        if name is None:
            print(f"REFUSING: unnamed class-body member at line {node.lineno} ({type(node).__name__})", file=sys.stderr)
            return 1
        blocks[name] = "".join(lines[cursor : node.end_lineno])
        cursor = node.end_lineno

    # THE TAIL: everything after the class body ends. New in this feature - see the docstring.
    tail = "".join(lines[cls.end_lineno :])
    if "def surface_water_dist" not in tail:
        print(f"REFUSING: the module-level tail does not contain surface_water_dist (got {len(tail)} chars)", file=sys.stderr)
        return 1

    assigned = [n for _, _, names in MODULES.values() for n in names] + list(RELOCATE)
    if len(assigned) != len(set(assigned)):
        dupes = sorted({n for n in assigned if assigned.count(n) > 1})
        print(f"REFUSING: a member is assigned to more than one destination: {dupes}", file=sys.stderr)
        return 1
    if sorted(assigned) != sorted(blocks):
        missing = sorted(set(blocks) - set(assigned))
        extra = sorted(set(assigned) - set(blocks))
        print(f"REFUSING: partition does not cover the class. missing={missing} extra={extra}", file=sys.stderr)
        return 1

    def repoint(text: str, counts: dict[str, int]) -> str:
        for old, new in REPOINT:
            counts[old] = counts.get(old, 0) + text.count(old)
            text = text.replace(old, new)
        return text

    seen: dict[str, int] = {}
    PKG.mkdir(exist_ok=True)
    for mod, (mixin, doc, names) in MODULES.items():
        body = []
        for n in names:
            text = deepen(blocks[n])
            for banner in DROP_BANNERS:
                text = "".join(ln for ln in text.splitlines(keepends=True) if ln.strip() != banner)
            body.append(repoint(text, seen))
        out = f'"""{doc}\n\nSplit from settlement/land.py by feature 120 - see settlement/land/CLAUDE.md for the index.\n"""\n\n{header}\nclass {mixin}:\n{"".join(body)}'
        if mod == TAIL_MODULE:
            out += "\n" + deepen(tail).lstrip("\n")
        (PKG / f"{mod}.py").write_text(out)
        print(f"wrote {PKG / mod}.py  ({len(out.splitlines())} lines, {len(names)} members{', + the module-level tail' if mod == TAIL_MODULE else ''})")

    for old, _new in REPOINT:
        if seen.get(old, 0) != 1:
            print(f"REFUSING: REPOINT {old!r} fired {seen.get(old, 0)} times, expected exactly 1", file=sys.stderr)
            return 1

    # RELOCATION: append the three farmstead helpers to HomesteadPartsMixin, whose body runs to EOF.
    reloc_src = RELOC_FILE.read_text()
    reloc_tree = ast.parse(reloc_src)
    reloc_cls = next(n for n in reloc_tree.body if isinstance(n, ast.ClassDef) and n.name == RELOC_CLASS)
    if reloc_cls.end_lineno != len(reloc_src.splitlines()):
        print(f"REFUSING: {RELOC_CLASS} does not run to EOF (ends {reloc_cls.end_lineno}, file has {len(reloc_src.splitlines())})", file=sys.stderr)
        return 1
    if RELOC_IMPORT_FIX[0] not in reloc_src:
        print(f"REFUSING: cannot apply the import fix - {RELOC_IMPORT_FIX[0]!r} not found in {RELOC_FILE}", file=sys.stderr)
        return 1
    reloc_src = reloc_src.replace(*RELOC_IMPORT_FIX, 1)
    reloc_src = reloc_src.rstrip("\n") + "\n" + "".join(blocks[n] for n in RELOCATE)
    RELOC_FILE.write_text(reloc_src)
    print(f"appended {len(RELOCATE)} relocated members to {RELOC_FILE} ({len(reloc_src.splitlines())} lines)")

    init = '''"""The land-surface subsystem of the Mode B settlement engine.

Split from the 1,187-line settlement/land.py by feature 120 (constitution Principle X clause 13),
the LAST un-split file in this package. See CLAUDE.md in this directory for which submodule holds
what.

This package was a RESIDUE BUCKET, not a chain. `land.py` was cut positionally out of the
16,016-line settlement.py by feature 025, so what it held was four unrelated land subsystems that
happened to be adjacent - a polder dike, wet ground, dry ground cover, and near-ring farmland - plus
three farmstead helpers that belonged in homestead_parts.py all along and moved there with this
split. The partition is therefore by SUBJECT, and the test of it is that a real task stays inside one
module: re-siting the wet toe is wet.py alone, changing what scrub looks like is cover.py alone,
re-shaping the dike is dikes.py alone.

`LandMixin` exists ONLY to preserve settlement/core.py's single import and its position in the
`class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call needs
no import and the partition can be re-cut later without touching core.py. cover.py is the one real
caller: `hinterland` composes `commons` (its own) with `toe_band` and `marsh` (wet.py).

The base order below is source order and is behaviorally irrelevant - no name is defined twice,
which is what the composed-surface guard's second assertion exists to keep true.
"""

from .cover import GroundCoverMixin
from .dikes import DikeMixin
from .nearring import NearRingMixin
from .wet import WetGroundMixin, surface_water_dist as surface_water_dist


class LandMixin(
    DikeMixin,
    WetGroundMixin,
    GroundCoverMixin,
    NearRingMixin,
):
    """The composed land surface. No members of its own by design - see the module docstring."""
'''
    (PKG / "__init__.py").write_text(init)
    print(f"wrote {PKG / '__init__.py'}")
    print("\nPRUNE the copied headers next:")
    print("  python3 -m ruff check --select F401 --fix settlement/land/")
    print("  python3 -m ruff format settlement/land/ settlement/homestead_parts.py")
    print("  git rm settlement/land.py")
    print("  find settlement -name __pycache__ -prune -exec rm -rf {} +")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
