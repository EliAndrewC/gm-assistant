#!/usr/bin/env python3
"""Feature 115's one-shot transformer: settlement/civic_grounds.py -> settlement/civic_grounds/ package.

Adapted from feature 114's split_structures.py, which came from 113's split_city.py, from 112's
split_fields.py, from feature 025's split_settlement.py. The lineage matters because the slicing rule
is the part worth preserving, and it is the part a fresh implementation gets wrong.

Run once from .claude/skills/diagram/:

    python3 ../../../specs/115-civic-grounds-package/split_civic_grounds.py

then prune the copied import headers with ruff (see PRUNE below) and delete the old file.

WHY the blocks are sliced as (previous node's end + 1 .. this node's end) rather than by the node's
own lineno: that span carries the decorator lines, the blank lines, and any comment block written
above the member. Slicing by node.lineno silently drops all three - and in this project the third is
the real loss, because a comment above a method is usually researched grounding. A "pure move" that
drops a why-comment is not pure.

This file is the biggest concentration of that grounding in the engine (the Qingming Shanghe Tu gate
convention, the ox-consumption arithmetic behind the trough count, the two-round dung-heap clearance
history), so quickstart step 6 CHECKS the result rather than trusting this docstring.

NOTE what this script does NOT do: it does not decompose _stable_yard. That is stage 2, done by hand
against a tree already proven byte-identical, so that a hash mismatch has exactly one possible cause
(plan.md, "Three stages, not two").
"""

import ast
import pathlib
import sys

SRC = pathlib.Path("settlement/civic_grounds.py")
PKG = pathlib.Path("settlement/civic_grounds")

# The partition, per specs/115-civic-grounds-package/data-model.md. Keys are class-body member names
# in SOURCE order. Unlike 114's StructuresMixin, this class carries NO class-level constants - all 22
# members are functions - so the Assign branch in member_name() never fires here. It is kept because
# the next split probably has some.
MODULES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "funerary": (
        "FuneraryGroundsMixin",
        "Ground given over to the dead: where a settlement buries, entombs, burns and stores its bones.",
        # _ward_fence_cap is mausoleum's own ward-fence predicate. It also has an external consumer
        # (structures/compounds.py), which reaches it through the composed Settlement either way, so
        # placement follows the caller WITHIN the package being cut - 113's _ring_upslope rule.
        # Research R1a; its eventual home is beside the ward fences in water_ways.py.
        ("cemetery", "_ward_fence_cap", "mausoleum", "cremation_ground", "ossuary"),
    ),
    "justice": (
        "JusticeGroundsMixin",
        "Ground given over to punishment, and to the boundaries punishment is measured against.",
        ("punishment_spot", "execution_ground", "boundary_marker"),
    ),
    "civic": (
        "CivicWorksMixin",
        "Institutional and commercial works: what a domain builds because it administers and trades,\nas opposed to what its inhabitants build in order to live.",
        # precinct_interior draws a temple precinct's interior program and calls self.cemetery, which
        # lands in funerary.py - a cross-module self. call, which is normal here. Its natural eventual
        # home is beside the shrines in shrines_wells.py, a PARENT-level move deliberately not folded
        # into this feature. Research R1b.
        ("precinct_interior", "district", "terrace", "granary", "merchant_storehouses", "merchant_residences"),
    ),
    "lodging": (
        "LodgingMixin",
        "Where travelers and their animals stop: the beds, the stalls, and the deferred draw that puts\nthe yards on the map last.",
        # _way_seat_near is LIVE - _way_bearing_near calls it, one line, inside the old file. A
        # cross-file census that excludes the defining file reports it as dead; the pre-spec census
        # did exactly that and proposed deleting it. Research R6.
        ("_way_bearing_near", "_way_seat_near", "flophouse", "inn", "stables", "animal_ground", "flush_stable_yards"),
    ),
    "stable_yard": (
        "StableYardMixin",
        "The working yard around a gate stables: beaten earth, hitching rails, troughs and muck heaps.",
        # One private method gets a module because at 335 lines it is larger than three of the other
        # four modules; folding it into lodging.py would make a ~575-line module, which would move the
        # grab-bag problem rather than solve it. Research R1c.
        ("_stable_yard",),
    ),
}

# Section-divider comments that describe the OLD file's layout and would be actively misleading once
# the sections live in different files. civic_grounds.py has none today (checked): every class-body
# comment above a member describes that member. The hook is kept because predecessors needed it.
DROP_BANNERS: tuple[str, ...] = ()


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
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CivicGroundsMixin")

    # The parent header: everything above `class CivicGroundsMixin:`. Copied wholesale into each
    # module and pruned by ruff afterwards (PRUNE below) - which reaches the same end state as
    # computing each module's used names by hand, without this script having to model name resolution.
    header = "".join(lines[: cls.lineno - 1])
    header = header.replace("from ._geom import", "from .._geom import")
    header = header.replace("from ._knobs import", "from .._knobs import")
    header = header.replace("from .core import Settlement", "from ..core import Settlement")
    header = header.replace(
        '"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""\n',
        "",
    )

    # Slice every class-body member into a block that carries its decorators, its blank lines and any
    # comment written above it.
    blocks: dict[str, str] = {}
    cursor = cls.lineno  # 1-based line of `class CivicGroundsMixin:`; body text starts on the next line
    for node in cls.body:
        name = member_name(node)
        text = "".join(lines[cursor : node.end_lineno])
        # The same one-dot -> two-dot rewrite the header gets, applied to the BODY as well. 113 found
        # a LAZY in-body `from .core import Settlement` which, left alone, silently resolves to a
        # module that does not exist. civic_grounds.py has no in-body import today, but the rewrite
        # costs nothing and the next split inherits it.
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
        out = f'"""{doc}\n\nSplit from settlement/civic_grounds.py by feature 115 - see settlement/civic_grounds/CLAUDE.md for the index.\n"""\n\n{header}\nclass {mixin}:\n{"".join(body)}'
        (PKG / f"{mod}.py").write_text(out)
        print(f"wrote {PKG / mod}.py  ({len(out.splitlines())} lines, {len(names)} members)")

    init = '''"""The civic-grounds subsystem of the Mode B settlement engine.

Split from the 1,162-line settlement/civic_grounds.py by feature 115 (constitution Principle X
clause 13). See CLAUDE.md in this directory for which submodule holds what.

Like settlement/structures/ and unlike settlement/fields/ or settlement/city/, this package was never
ONE subsystem: civic_grounds.py held four unrelated ones - funerary ground, judicial ground, civic
and commercial works, and lodging with its livestock yards. So the submodules are grouped by what a
session comes here to CHANGE, and they are deliberately uneven in size.

`CivicGroundsMixin` exists ONLY to preserve settlement/core.py's single import and its position in
the `class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call needs
no import and the partition can be re-cut later without touching core.py. Two such calls exist by
design: civic.precinct_interior -> funerary.cemetery, and lodging.flush_stable_yards ->
stable_yard._stable_yard.

The base order below is source order and is behaviorally irrelevant - no name is defined twice, which
is what the composed-surface guard's second assertion exists to keep true.
"""

from .civic import CivicWorksMixin
from .funerary import FuneraryGroundsMixin
from .justice import JusticeGroundsMixin
from .lodging import LodgingMixin
from .stable_yard import StableYardMixin


class CivicGroundsMixin(
    FuneraryGroundsMixin,
    JusticeGroundsMixin,
    CivicWorksMixin,
    LodgingMixin,
    StableYardMixin,
):
    """The composed surface. Holds no members of its own - see the module docstring."""
'''
    (PKG / "__init__.py").write_text(init)
    print(f"wrote {PKG / '__init__.py'}  ({len(init.splitlines())} lines)")

    print()
    print("PRUNE: the header was copied wholesale into every module, so most modules now import")
    print("names they do not use. Fix with:")
    print("    python3 -m ruff check --select F401 --fix settlement/civic_grounds/")
    print("    python3 -m ruff format settlement/civic_grounds/")
    print("then `git rm settlement/civic_grounds.py` and run quickstart steps 4-6.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
