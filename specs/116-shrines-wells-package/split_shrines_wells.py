#!/usr/bin/env python3
"""Feature 116's one-shot transformer: settlement/shrines_wells.py -> settlement/shrines_wells/.

Adapted from feature 114's split_structures.py, which came from 113's split_city.py, 112's
split_fields.py and 025's split_settlement.py. The lineage matters because the slicing rule is the
part worth preserving, and it is the part a fresh implementation gets wrong.

Run once from .claude/skills/diagram/:

    python3 ../../../specs/116-shrines-wells-package/split_shrines_wells.py

then prune the copied import headers with ruff (see PRUNE below) and delete the old file.

WHY the blocks are sliced as (previous node's end + 1 .. this node's end) rather than by the node's
own lineno: that span carries the DECORATOR lines (ast reports FunctionDef.lineno at the `def`, not
at the decorator above it), the blank lines, and any comment block written above the member. Slicing
by node.lineno silently drops all three.

BOTH of those hazards are live in THIS file, which is what makes the rule concrete rather than
inherited folklore:

  - `frozen_terrain` carries @contextlib.contextmanager - the first decorated member in the lineage.
    Lose it and the name still exists, the package still imports, mypy --strict still passes, and
    every `with self.frozen_terrain():` call site fails with AttributeError: __enter__.
  - The class is unusually comment-heavy, and in this project a comment above a method is usually
    researched grounding (the 45-minute-grind post-mortem above _well_ground_clear, the canopy
    density study, the 30 px-vs-ftpx reservation table). A "pure move" that drops a why-comment is
    not pure, which is why quickstart step 6b counts comment lines rather than trusting this.
"""

import ast
import pathlib
import sys

SRC = pathlib.Path("settlement/shrines_wells.py")
PKG = pathlib.Path("settlement/shrines_wells")

# The partition, per specs/116-shrines-wells-package/data-model.md. Keys are class-body member names
# in SOURCE order within each module. Unlike 112/114 this class carries NO class-level constants -
# every member is a FunctionDef - so the Assign branch in member_name() never fires here. It is kept
# because the next split will probably need it.
MODULES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "shrines": (
        "ShrineHallsMixin",
        "The religious hall and shrine GLYPHS, the hill one may stand on, and the hall's caption.",
        # _hall_caption_y reads torii geometry but its single consumer is shrine_hall and its subject
        # is where the HALL's caption goes - placement follows the caller (research R1d).
        ("hill", "shrine", "small_shrine", "_hall_caption_y", "shrine_hall"),
    ),
    "torii": (
        "ToriiAvenueMixin",
        "The torii arch and the whole approach engine: the gen authors the LINE, the engine owns the count, the stride, the threshold and the wall clearance.",
        (
            "_assert_walls_clear_of_torii",
            "_avenue_pitch",
            "_avenue_at_threshold",
            "_avenue_short_of_walls",
            "_torii",
            "torii_path",
            "torii_even",
        ),
    ),
    "wellground": (
        "WellGroundMixin",
        "One question - is this ground fit to sink a wellhead in? - and everything that makes asking it cheap.",
        # The package's hub: wells.py and seats.py call in, and this module calls out to neither
        # (research R10). frozen_terrain is the decorated member - see the module docstring above.
        (
            "_build_well_index",
            "_terrain_fingerprint",
            "frozen_terrain",
            "_well_index",
            "_wet_toe_keepout",
            "_well_ground_clear",
            "_in_scrub_cover",
        ),
    ),
    "wells": (
        "WellsMixin",
        "The wellhead glyph, and the four passes that put wells on a map.",
        # shrine_well is a WELL placed for a shrine - it delegates to well_at and records an
        # M['wells'] entry - so it is filed by its code rather than by its name (research R1c).
        ("_well_vr", "well", "farm_wells", "_farm_wells", "well_at", "place_wells", "_place_wells", "shrine_well"),
    ),
    "seats": (
        "OpenSeatMixin",
        "The general 'where can a w x h feature stand?' API, asked of the real _fits at the moment of placement.",
        # Does not belong to this subsystem at all: its home is houses.py, beside the _fits it
        # delegates to. Isolated so that move is a one-file change - feature 113's city/civic.py and
        # 114's structures/ground.py precedent. Full reasoning: research R1a.
        ("_footprint_clear", "open_seat"),
    ),
    "byres": (
        "DraftByresMixin",
        "The draft-animal byre (ox / water-buffalo shed) standing among the homesteads.",
        # Also misfiled at the parent level: a byre is a homestead appurtenance and belongs with
        # homestead_parts.py. Isolated for the same reason as seats.py - research R1b.
        ("_draw_byre", "draft_byres"),
    ),
    "woods": (
        "TreeStandsMixin",
        "Woods drawn as STANDS of individual trees - the floor early, the canopy deferred to crop time.",
        ("_tree_stand", "flush_tree_stands", "_draw_stand", "_stand_fringe", "_crowns", "_fringe_blocked", "forest"),
    ),
}

# Section-divider comments that describe the OLD file's layout and would be actively misleading once
# the sections live in different files. This file HAS two, unlike its predecessor: `# ---- hill +
# shrine + torii` sits above `hill` (and the torii half of what it names lands in another module),
# and `# ---- landscape / estate features` sits above _tree_stand. Both describe a position in a
# file that will no longer exist; each module's own docstring replaces them.
DROP_BANNERS: tuple[str, ...] = (
    "# ---- hill + shrine + torii",
    "# ---- landscape / estate features",
)


def member_name(node: ast.stmt) -> str | None:
    """The class-body member's name, for a def or a simple class-level assignment."""
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        return node.name
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def main() -> int:
    src = SRC.read_text()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ShrinesWellsMixin")

    # The parent header: everything above `class ShrinesWellsMixin:`. Copied wholesale into each
    # module and pruned by ruff afterwards (PRUNE below) - which reaches the same end state as
    # computing each module's used names by hand, without this script having to model name
    # resolution.
    header = "".join(lines[: cls.lineno - 1])
    header = header.replace("from ._geom import", "from .._geom import")
    header = header.replace("from ._knobs import", "from .._knobs import")
    header = header.replace("from .core import Settlement", "from ..core import Settlement")
    header = header.replace('"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""\n', "")

    # Slice every class-body member into a block that carries its decorators, its blank lines and any
    # comment written above it.
    blocks: dict[str, str] = {}
    cursor = cls.lineno  # 1-based line of `class ShrinesWellsMixin:`; body text starts on the next line
    for node in cls.body:
        name = member_name(node)
        text = "".join(lines[cursor : node.end_lineno])
        # The same one-dot -> two-dot rewrite the header gets, applied to the BODY as well. 113 found
        # a LAZY in-body `from .core import Settlement` which, left alone, silently resolves to a
        # module that does not exist. This file has no in-body import today; the rewrite is free.
        text = text.replace("from .core import", "from ..core import")
        text = text.replace("from ._geom import", "from .._geom import")
        text = text.replace("from ._knobs import", "from .._knobs import")
        if name is None:
            print(f"REFUSING: unnamed class-body member at line {node.lineno} ({type(node).__name__})", file=sys.stderr)
            return 1
        blocks[name] = text
        cursor = node.end_lineno

    assigned = [n for _, _, names in MODULES.values() for n in names]
    if len(assigned) != len(set(assigned)):
        dupes = sorted({n for n in assigned if assigned.count(n) > 1})
        print(f"REFUSING: a member is assigned to more than one module: {dupes}", file=sys.stderr)
        return 1
    if sorted(assigned) != sorted(blocks):
        missing = sorted(set(blocks) - set(assigned))
        extra = sorted(set(assigned) - set(blocks))
        print(f"REFUSING: partition does not cover the class. missing={missing} extra={extra}", file=sys.stderr)
        return 1

    PKG.mkdir(exist_ok=True)
    for mod, (mixin, doc, names) in MODULES.items():
        body = []
        for n in names:
            text = blocks[n]
            for banner in DROP_BANNERS:
                text = "".join(ln for ln in text.splitlines(keepends=True) if ln.strip() != banner)
            body.append(text)
        out = f'"""{doc}\n\nSplit from settlement/shrines_wells.py by feature 116 - see settlement/shrines_wells/CLAUDE.md for the index.\n"""\n\n{header}\nclass {mixin}:\n{"".join(body)}'
        (PKG / f"{mod}.py").write_text(out)
        print(f"wrote {PKG / mod}.py  ({len(out.splitlines())} lines, {len(names)} members)")

    init = '''"""The shrines/wells subsystem of the Mode B settlement engine.

Split from the 1,179-line settlement/shrines_wells.py by feature 116 (constitution Principle X
clause 13). See CLAUDE.md in this directory for which submodule holds what.

This package was never ONE subsystem, and its NAME concedes it - the only module in the engine joined
by an `and`. Feature 025 sliced the 16,016-line original by position, so six unrelated subsystems
ended up sharing a file: religious halls, torii avenues, the well subsystem, a general seat-finding
API, draft byres, and woodland stands. The seven submodules are therefore grouped by what a session
comes here to CHANGE, and they are deliberately uneven in size - a partition tuned for equal files
would have to cut a cluster that no task cuts.

`ShrinesWellsMixin` exists ONLY to preserve settlement/core.py's single import and its position in
the `class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call needs
no import and the partition can be re-cut later without touching core.py. wellground.py is the hub:
wells.py and seats.py call into it and it calls out to neither.

The base order below is source order and is behaviorally irrelevant - no name is defined twice, which
is what the composed-surface guard's second assertion exists to keep true.
"""

from .byres import DraftByresMixin
from .seats import OpenSeatMixin
from .shrines import ShrineHallsMixin
from .torii import ToriiAvenueMixin
from .wellground import WellGroundMixin
from .wells import WellsMixin
from .woods import TreeStandsMixin


class ShrinesWellsMixin(
    ShrineHallsMixin,
    ToriiAvenueMixin,
    WellGroundMixin,
    WellsMixin,
    OpenSeatMixin,
    DraftByresMixin,
    TreeStandsMixin,
):
    """The composed shrines/wells surface. No members of its own by design - see the module docstring."""
'''
    (PKG / "__init__.py").write_text(init)
    print(f"wrote {PKG / '__init__.py'}")
    print("\nPRUNE the copied headers next:")
    print("  python3 -m ruff check --select F401 --fix settlement/shrines_wells/")
    print("  python3 -m ruff format settlement/shrines_wells/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
