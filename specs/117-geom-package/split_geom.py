#!/usr/bin/env python3
"""Feature 117's one-shot transformer: settlement/_geom.py -> settlement/_geom/.

Adapted from feature 116's split_shrines_wells.py, which came from 114's split_structures.py, 113's
split_city.py, 112's split_fields.py and 025's split_settlement.py. The lineage matters because the
slicing rule is the part worth preserving, and it is the part a fresh implementation gets wrong.

Run once from .claude/skills/diagram/:

    python3 ../../../specs/117-geom-package/split_geom.py

then prune the copied import headers with ruff (see PRUNE below) and delete the old file.

WHY the blocks are sliced as (previous node's end + 1 .. this node's end) rather than by the node's
own lineno: that span carries the decorator lines, the blank lines, and any comment block written
above the member. Slicing by node.lineno silently drops all three.

TWO THINGS ARE NEW HERE, because this is the first split in the lineage of a MODULE rather than a
class body, and the first whose surface is re-exported by star imports rather than by composing a
mixin:

  - **An unnamed top-level statement exists**: `_assert_not_main_tree()` on line 35, the import-time
    main-tree guard. A class body of nothing but `def`s has no such thing, so 112-116 could refuse on
    any unnamed member. Here an unnamed statement is folded into the PRECEDING named member's block,
    which puts the call in base.py with its own definition. Dropping it would disarm the guard while
    every test still passed, since every test already runs inside a clone.
  - **One comment bank must MOVE between modules.** The 16-line "A TORII STANDS CLEAR OF EVERY WALL"
    doctrine physically precedes `_rect_ring` (a pure corner-ring helper bound for overlap.py) but
    documents `torii_seat_on_wall` / `torii_wall_conflicts` (bound for walls.py). The slicing rule
    alone would file a torii ruling in the collision-predicates module, away from both functions it
    explains. BANK_MOVES lifts it; REPOINT then fixes the four sentences whose "above"/"below" would
    become false across a module boundary. Every REPOINT is asserted to fire exactly once - a
    silently-missed rewrite is the failure mode, since nothing downstream reads a comment.
"""

import ast
import pathlib
import sys

SRC = pathlib.Path("settlement/_geom.py")
PKG = pathlib.Path("settlement/_geom")

# The partition, per specs/117-geom-package/data-model.md: module -> (docstring, supplemental
# imports, member names). Members are written in SOURCE order regardless of the order listed here.
#
# The supplemental imports are hand-specified rather than inferred, and they respect the layering
# rule base <- primitives <- overlap <- everything else, so the package is acyclic by construction
# instead of by whatever survives ruff's pruning.
MODULES: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "base": (
        "What every other submodule of _geom needs first: the coordinate type aliases, the\nimport-time main-tree guard, and the land/crop palette.\n\nThe last two are not geometry, and are here rather than anywhere better because feature 025's\npositional cut put them in _geom.py. They sit at the bottom of the layering rule (base <-\nprimitives <- overlap <- everything else), which is the one placement that costs nothing: the\nguard must run on ANY import of the package, and it does, because every submodule's star import\nin __init__.py reaches this one.",
        (),
        ("Pt", "Poly", "Manifest", "_assert_not_main_tree", "LAND", "PADDY_SHADES", "FLOODED_SHADES", "RIPE_SHADES", "RICE_GREENS"),
    ),
    "primitives": (
        "Coordinate math on points, segments and rings - no map vocabulary in here at all.\n\nEverything above this layer is built from these: a distance, a containment, a crossing, an\nintersection. Nothing here reads a manifest or knows what a paddy is.",
        ("from .base import Poly, Pt",),
        ("_signed_area", "point_in_poly", "seg_closest", "seg_dist", "seg_in_ellipse_core", "ring_touches", "segments_cross", "seg_intersect", "edge_dist"),
    ),
    "overlap": (
        "A footprint's corner ring, and whether two regions meet or how far apart they are.\n\nThe distinction this module exists to keep straight is the one the skill's CLAUDE.md calls\n'CENTER vs FOOTPRINT': a gap VERDICT reads real rotated corners (sat_overlap, poly_gap,\nedge-to-edge), a PREFILTER may read a circumscribed extent, and the two must never be swapped.",
        ("from .base import Poly, Pt", "from .primitives import point_in_poly, seg_dist, segments_cross"),
        ("stroke_quads", "box_gap", "_rect_ring", "sat_overlap", "_union_area", "region_blocked", "quad_hits_poly", "point_quad_dist", "quad_hits_seg", "rot_rect", "poly_gap", "_aabb_gap", "rects_overlap"),
    ),
    "indexes": (
        "Prefilters and spatial indexes: how a per-candidate scan of static geometry stops being the\nwhole runtime of a gen.\n\nPREFILTER FAMILY, all of it - the box or the grid PRUNES, the caller's exact test still DECIDES,\nso a verdict is identical to a linear scan's and the pool regenerates byte-identical when a\ncaller switches over. That property is what separates indexing from coarsening, which this engine\ndoes not do (skill CLAUDE.md, 'When a check is slow, INDEX it - do not coarsen it').",
        ("from .base import Poly, Pt", "from .primitives import edge_dist, point_in_poly, seg_dist"),
        ("boxed_polys", "boxed_hit", "boxed_segs", "boxed_seg_hit", "Indexed", "indexed_grid", "boxed_grid", "PointGrid"),
    ),
    "seatmemo": (
        "SeatMemo - the lattice positions a dwelling top-up has already REFUSED, so a later pass over\nthe same ground does not pay for the same refusal twice.\n\nIts own module because it is its own subject: not an index (it remembers answers, not geometry),\nand carrying a long measured rationale that a reader of the indexes never needs.",
        (),
        ("SeatMemo",),
    ),
    "labels": (
        "Caption typography: how far a label stands off its subject, how big it is set, and which way it\ntilts.\n\nThe two tilt rules are the trap here and the docstrings say so at length: label_tilt FOLDS (a\nbuilding has two edge families) where linear_tilt CLAMPS (a line has one axis), and swapping them\ntilts a caption to match nothing on the map.",
        ("from .base import Poly, Pt",),
        ("LABEL_MIN_AIR", "LABEL_AIR_STEP", "LABEL_AIR_RINGS", "LABEL_AIR_CAP", "HALL_CAPTION_FS", "GOVERNOR_CAPTION_FS", "label_tilt", "linear_tilt_full", "linear_tilt", "label_quad", "label_aabb", "tilt_caption_seat"),
    ),
    "ways": (
        "The travelled ways as they are recorded on a manifest, the gate that bars one, and the\nconstants a crossing is built to.\n\n'What could someone walk or cart along here' - deliberately not walls, fences or watercourses.\nThe placer and the check both read these, which is the whole reason they are shared functions\nrather than two hand-rolled lists.",
        ("from .base import Manifest, Poly", "from .primitives import seg_dist"),
        ("PLANK_ABUTMENT", "PLANK_BANK_REACH", "LANDING_FT", "PLANK_VILLAGE_REACH", "LANE_THROUGH_TOL", "LANE_CROSSES_MIN_DEG", "lane_runs", "way_beds", "lane_through_gate", "kido_bar_deg", "CARRIED_LANDING_FLOOR_FT"),
    ),
    "walls": (
        "Every wall on a settlement map, what closes a ward against one, and the arches that must stand\nclear of one.\n\nThe torii members are here rather than with settlement/shrines_wells/torii.py deliberately: at\nTHIS level an arch has exactly one geometric rule - it may not stand in a wall - and both\npredicates are computed from wall_runs(). The arch glyph, the avenue count, the stride and the\nthreshold all live in shrines_wells/torii.py and are untouched by this module.",
        ("from .base import Manifest, Poly, Pt", "from .overlap import _rect_ring", "from .primitives import seg_dist, segments_cross"),
        ("TORII_PITCH_FT", "TORII_PITCH_MAX_SPANS", "torii_halfbox", "WARD_BARRED_KINDS", "ward_interior", "wall_runs", "_box_hits_run", "torii_seat_on_wall", "torii_wall_conflicts"),
    ),
    "extents": (
        "A recorded feature's DRAWN extent, read back off the manifest.\n\nOne subject, and it is a doctrine rather than a shape: each of these is the SINGLE definition of\nwhere some ink actually is, so that the placer and the check that grades it cannot disagree\n(skill CLAUDE.md, 'Placement and its check must read the SAME manifest source').",
        ("from .base import Manifest, Poly",),
        ("forest_reveal_x", "forest_frame_span", "paddy_wet_rings", "YARD_GLYPH_SLACK", "wellhead_quad", "trough_quad", "tower_quad", "rail_quad"),
    ),
    "curves": (
        "Making a drawn line or ring look hand-made rather than drafted: fillets, Catmull-Rom smoothing,\norganic jitter, a gently winding path.\n\nEvery one of these is a research-backed shape rather than a drawing quirk - a dug earth ditch\nbends on a swept curve because a sharp corner scours outside and silts inside until the water has\nrounded it itself.",
        ("from .base import Poly, Pt",),
        ("fillet_polyline", "smooth_closed", "smooth_points", "organic_bbox", "organic_poly", "winding"),
    ),
    "village": (
        "The village population distribution and the homestead-bundle pitch.\n\nNOT geometry, and not really _geom's business: a population roll belongs with rolling.py, which is\nits only consumer. They are here because feature 025's positional cut put them here, and they are\nisolated in a module of their own so that the eventual move is a one-file change - feature 116's\nseats.py/byres.py precedent.",
        (),
        ("_VILLAGE_POP_DIST", "BUNDLE_PITCH_FT", "village_population"),
    ),
}

# A comment bank that must land in a DIFFERENT module from the member it physically precedes.
# (donor member, recipient member, a line fragment identifying the bank). The bank is the contiguous
# run of `#` lines around that fragment.
BANK_MOVES: tuple[tuple[str, str, str], ...] = (("_rect_ring", "torii_seat_on_wall", "A TORII STANDS CLEAR OF EVERY WALL"),)

# Sentences whose "above"/"below" stops being true once the referent lives in another module. Each
# MUST fire exactly once, package-wide - a missed rewrite leaves a comment pointing at nothing, and
# no test reads a comment. (Every other positional word in the file refers within its own module or
# to geometry rather than position; the full grep is in research.md R5.)
REPOINT: tuple[tuple[str, str], ...] = (
    ("the same discipline as `paddy_wet_rings` below", "the same discipline as `paddy_wet_rings` in extents.py"),
    ("the same discipline as torii_wall_conflicts above", "the same discipline as torii_wall_conflicts in walls.py"),
    ("behind the label standoff ladder below AND behind the gate's", "behind the label standoff ladder in labels.py AND behind the gate's"),
    ("and all three read the SAME wall_runs() / torii_wall_conflicts() below.", "and all three read the SAME wall_runs() / torii_wall_conflicts() in this module."),
)


def member_name(node: ast.stmt) -> str | None:
    """The module-level member's name, for a def, a class, or a simple assignment."""
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return node.name
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def lift_bank(block: str, fragment: str) -> tuple[str, str]:
    """Split a member's block into (the comment bank around `fragment`, the rest). The bank is the
    contiguous run of comment lines containing the fragment, plus the blank line under it."""
    lines = block.splitlines(keepends=True)
    hit = next(i for i, ln in enumerate(lines) if fragment in ln)
    start, end = hit, hit
    while start > 0 and lines[start - 1].lstrip().startswith("#"):
        start -= 1
    while end + 1 < len(lines) and lines[end + 1].lstrip().startswith("#"):
        end += 1
    return "".join(lines[start : end + 1]), "".join(lines[:start] + lines[end + 1 :])


def main() -> int:
    src = SRC.read_text()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)

    first = next(n for n in tree.body if member_name(n) is not None)
    # The header: everything above the first member - the module docstring (dropped; each submodule
    # writes its own) and the imports. Copied wholesale into every module and pruned by ruff
    # afterwards, which reaches the same end state as modelling name resolution here.
    header = "".join(lines[: first.lineno - 1])
    header = header.replace('"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""\n', "")

    blocks: dict[str, str] = {}
    order: dict[str, int] = {}
    cursor = first.lineno - 1  # 0-based index of the first member's first line
    last: str | None = None
    for node in tree.body:
        if node.end_lineno is None or node.end_lineno <= cursor:
            continue  # part of the header
        name = member_name(node)
        text = "".join(lines[cursor : node.end_lineno])
        if name is None:
            # An unnamed top-level statement - the import-time guard CALL. It has no name to key a
            # partition on, so it travels with the member above it (research R4).
            if last is None:
                print(f"REFUSING: unnamed top-level statement at line {node.lineno} with no preceding member", file=sys.stderr)
                return 1
            print(f"  folding unnamed {type(node).__name__} at line {node.lineno} into `{last}`")
            blocks[last] += text
        else:
            blocks[name] = text
            order[name] = node.lineno
            last = name
        cursor = node.end_lineno

    assigned = [n for _, _, names in MODULES.values() for n in names]
    if len(assigned) != len(set(assigned)):
        dupes = sorted({n for n in assigned if assigned.count(n) > 1})
        print(f"REFUSING: a member is assigned to more than one module: {dupes}", file=sys.stderr)
        return 1
    if sorted(assigned) != sorted(blocks):
        missing = sorted(set(blocks) - set(assigned))
        extra = sorted(set(assigned) - set(blocks))
        print(f"REFUSING: partition does not cover the module. missing={missing} extra={extra}", file=sys.stderr)
        return 1

    banks: dict[str, str] = {}
    for donor, recipient, fragment in BANK_MOVES:
        bank, rest = lift_bank(blocks[donor], fragment)
        blocks[donor] = rest
        banks[recipient] = bank
        print(f"  moved a {len(bank.splitlines())}-line comment bank from `{donor}` to `{recipient}`")

    # Re-point AFTER the bank move, and over BOTH dicts: one of the four sentences lives inside the
    # bank that just moved, so a pass over `blocks` alone silently misses it - which is exactly what
    # the fired-exactly-once assertion is for, and it caught this on the first run.
    fired = dict.fromkeys(REPOINT, 0)
    for store in (blocks, banks):
        for name, text in store.items():
            for pair in REPOINT:
                old, new = pair
                if old in text:
                    fired[pair] += text.count(old)
                    store[name] = store[name].replace(old, new)
    for pair, n in fired.items():
        if n != 1:
            print(f"REFUSING: re-point fired {n} times (expected exactly 1): {pair[0]!r}", file=sys.stderr)
            return 1

    PKG.mkdir(exist_ok=True)
    for mod, (doc, imports, names) in MODULES.items():
        body = "".join(banks.get(n, "") + blocks[n] for n in sorted(names, key=lambda n: order[n]))
        extra = ("\n" + "\n".join(imports) + "\n") if imports else ""
        out = f'"""{doc}\n\nSplit from settlement/_geom.py by feature 117 - see settlement/_geom/CLAUDE.md for the index.\n"""\n\n{header}{extra}{body}'
        (PKG / f"{mod}.py").write_text(out)
        print(f"wrote {PKG / mod}.py  ({len(out.splitlines())} lines, {len(names)} members)")

    # The surface. Star imports because a hand-written 89-name roster restates what the submodules
    # already declare (Principle X clause 14, feature 027's idiom); the aliased block because
    # `import *` does not carry underscore names, and six of them are consumed by name.
    # Interleaved per module in sorted order, matching check_village/__init__.py - which is also
    # what ruff's isort rule (I) wants, so the surface stays lint-clean without a manual pass.
    # ALL SEVEN underscore members, not just the four with external consumers. The surface census
    # in tests/settlement/test_geom.py caught the difference the first time it ran: `import *` drops
    # every one of them, so a partial block leaves `settlement._geom._VILLAGE_POP_DIST` - a name
    # that resolved before the split - silently gone. Re-exporting all seven makes the census a
    # single list rather than a list with a footnote nobody maintains.
    ALIASES = [
        ("base", "_assert_not_main_tree"),
        ("overlap", "_aabb_gap"),
        ("overlap", "_rect_ring"),
        ("overlap", "_union_area"),
        ("primitives", "_signed_area"),
        ("village", "_VILLAGE_POP_DIST"),
        ("walls", "_box_hits_run"),
    ]
    surface = "\n".join(f"from .{mod} import *" + "".join(f"\nfrom .{m} import {name} as {name}" for m, name in sorted(ALIASES) if m == mod) for mod in sorted(MODULES))
    init = f'''"""The pure geometry / spatial helpers of the Mode B settlement engine.

Split from the 1,303-line settlement/_geom.py by feature 117 (constitution Principle X clause 13).
See CLAUDE.md in this directory for which submodule holds what.

The file was the most widely imported module in the engine - 41 of the 47 files under settlement/,
plus check_village, hamletgen and two tools/ scripts - and its `no self, just geometry` calling
convention hid the fact that it held eight unrelated populations: coordinate math, collision
predicates, spatial indexes, a placement memo, caption typography, manifest readers, curve
generation, and three things that are not geometry at all. Every one of those readers paid for all
eight. The submodules are grouped by what a session comes here to CHANGE, and are deliberately
uneven in size.

THE SURFACE IS DERIVED, NOT MAINTAINED (Principle X clause 14, feature 027's idiom): the star
imports below re-export every submodule's public names - mypy treats star-imported public names as
explicitly exported even under strict's no_implicit_reexport, so no __all__ is needed. `import *`
does NOT carry underscore names, so the six with consumers by name are re-exported by the aliased
block. tests/settlement/test_geom.py guards the two properties this design rests on: the whole
pre-split surface still resolves, and no public name is bound in two submodules (a star-import
collision is silent - no MRO to catch it, and neither ruff nor mypy reports one).

Layering, so the package stays acyclic: base <- primitives <- overlap <- everything else; seatmemo
and village import nothing from the package. Respect it when adding a member.
"""

{surface}
'''
    (PKG / "__init__.py").write_text(init)
    print(f"wrote {PKG / '__init__.py'}")
    print("\nPRUNE the copied headers next:")
    print("  python3 -m ruff check --select F401 --fix settlement/_geom/")
    print("  python3 -m ruff format settlement/_geom/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
