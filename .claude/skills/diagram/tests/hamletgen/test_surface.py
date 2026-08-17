"""Feature 111: guard + surface-pin tests for the hamletgen package namespace.

The package __init__ re-exports its submodules' public names via star imports
(specs/111-hamletgen-package/, following features 027 and 110). Three properties
keep that safe, and this file holds all three lines:

1. No two submodules may bind the same public name to different objects -
   star-import shadowing is silent (last import wins), so a clash would swallow
   a stage or helper without any error. test_no_public_name_clashes holds the
   line; test_guard_fires_on_synthetic_clash proves the guard has teeth
   (check-before-fix: a checker never seen failing is not a check).
2. The consumed surface - every name reached through hamletgen anywhere in the
   skill tree at feature time (specs/111-hamletgen-package/contracts/package-surface.md)
   - must keep resolving, including the four underscore names the aliased
   explicit block carries.
3. The surface may not silently WIDEN either: test_census_matches_pin re-greps
   the tree and fails if a consumer reaches a name this file does not pin, so a
   new consumer forces a contract update rather than riding on the star imports.

This file is written to be green BOTH before and after the split: the
submodule-identity assertions activate only once `hamletgen` has a `__path__`,
so it could be committed against the monolith and stay meaningful afterwards.
"""

import importlib
import pkgutil
import re
import types
from pathlib import Path

import pytest

import hamletgen
import settlement

HERE = Path(__file__).resolve().parents[2]  # the skill root; this test lives in tests/hamletgen/


def _is_package() -> bool:
    return hasattr(hamletgen, "__path__")


def _submodules() -> list[types.ModuleType]:
    if not _is_package():
        return []
    return [importlib.import_module(f"hamletgen.{info.name}") for info in pkgutil.iter_modules(hamletgen.__path__) if info.name != "__main__"]


def _public_clashes(modules: list[types.ModuleType]) -> list[tuple[str, str, str]]:
    """Every (name, first_module, offending_module) where a public name is bound to two different objects."""
    seen: dict[str, tuple[str, object]] = {}
    clashes: list[tuple[str, str, str]] = []
    for mod in modules:
        for name, obj in vars(mod).items():
            if name.startswith("_"):
                continue
            if name in seen:
                if seen[name][1] is not obj:
                    clashes.append((name, seen[name][0], mod.__name__))
            else:
                seen[name] = (mod.__name__, obj)
    return clashes


# The 43 public names consumed as hamletgen.<name> / hg.<name>, plus the two imported
# directly by the pool gens (HamletSpec, generate). Census 2026-08-16, contracts/package-surface.md.
CONSUMED_PUBLIC = [
    "FIELD_ARCHETYPES",
    "GROSS_ACRES_PER_HOUSEHOLD",
    "HamletSpec",
    "OFFTAKE_LADDER",
    "ROLLED_ARCHETYPES",
    "Report",
    "SQ_FT_PER_ACRE",
    "SitePlan",
    "WIND_VECTORS",
    "back_fouled",
    "baseline_verdict",
    "below_drain",
    "belt_polygon",
    "build",
    "canvas_for",
    "centroid",
    "clip_to_clear",
    "cohort",
    "connector_track",
    "crosses_disc",
    "crosses_poly",
    "crossing_lands_on_crop",
    "default_jobs",
    "edge_run",
    "generate",
    "head_sluice",
    "main",
    "net_acres",
    "net_bends_acutely",
    "offtakes_for",
    "path_violations",
    "place_wells",
    "plan_site",
    "point_in_poly",
    "poly_area",
    "pond_clear_of_crop",
    "pond_setback",
    "pull_clear",
    "push_out_of",
    "route_around",
    "seat_cluster",
    "shallow_crossing",
    "stage_notice",
    "stage_water_frame",
    "unit",
    "well_target",
    "windward_for",
]

# The four underscore names with external consumers (test_hamletgen), and the submodule
# that owns each. A bare star import DROPS these - they need the aliased explicit block.
ALIASED_UNDERSCORE = {
    "_arm_crossing_accidental": "hamletgen.cluster",
    "_clear_gap": "hamletgen.hinterland",
    "_fork_spur": "hamletgen.cluster",
    "_near_line": "hamletgen.hinterland",
}


def test_no_public_name_clashes() -> None:
    clashes = _public_clashes(_submodules())
    assert not clashes, f"star-import shadowing - same public name, different objects: {clashes}"


def test_guard_fires_on_synthetic_clash() -> None:
    first = types.ModuleType("hamletgen.fake_first")
    second = types.ModuleType("hamletgen.fake_second")
    first.same_name = object()  # type: ignore[attr-defined]
    second.same_name = object()  # type: ignore[attr-defined]
    assert _public_clashes([first, second]) == [("same_name", "hamletgen.fake_first", "hamletgen.fake_second")]


@pytest.mark.parametrize("name", CONSUMED_PUBLIC)
def test_consumed_surface_resolves(name: str) -> None:
    getattr(hamletgen, name)


@pytest.mark.parametrize("name", sorted(ALIASED_UNDERSCORE))
def test_consumed_underscore_surface_resolves(name: str) -> None:
    getattr(hamletgen, name)


@pytest.mark.parametrize(("name", "owner"), sorted(ALIASED_UNDERSCORE.items()))
def test_aliased_underscore_reexport_is_identical(name: str, owner: str) -> None:
    if not _is_package():
        pytest.skip("hamletgen is still a module - submodule identity applies after the 111 split")
    assert getattr(hamletgen, name) is getattr(importlib.import_module(owner), name)


def test_pass_through_name_is_the_settlement_object() -> None:
    """`point_in_poly` is defined in settlement, not here; consumers reach it THROUGH hamletgen.

    It is the one contract name with no definition inside the package, so it is the one most
    likely to be dropped by a partition that forgets which submodule imported it.
    """
    assert hamletgen.point_in_poly is settlement.point_in_poly


def _submodule_names() -> set[str]:
    """`hg.driver`, `hg.sink` and their siblings are SUBMODULE handles, not re-exported names.

    contracts/package-surface.md puts them outside the contract in as many words ("Submodule
    paths... submodule layout is free to change in a later feature"), but the census regex cannot
    tell `hg.driver` from `hg.plan_site` - both are `hg.<word>`. So the submodules are subtracted
    here rather than pinned, which keeps the pin list a list of API names and leaves the layout
    free to change exactly as the contract promises.
    """
    return {m.__name__.rpartition(".")[2] for m in _submodules()}


def _censused_names() -> set[str]:
    """Re-grep the skill tree for every name any consumer reaches through hamletgen.

    This used to skip any path with `.clones` among its parts. That reads like "do not walk other
    sessions' clones", but it tests the ABSOLUTE path, and every session works inside
    `/gm-assistant/.clones/<name>/` - so the condition was true for EVERY file, the census returned
    the empty set, and `test_census_matches_pin` passed vacuously in the only place it is ever run.
    It was hiding two real unpinned consumers that the 111 split introduced. Found 2026-08-16 by
    running the gate from a clone OUTSIDE `.clones/`; the guard was never needed in the first place,
    because `HERE` is the skill directory and no `.clones` tree lives underneath it.
    """
    found: set[str] = set()
    for path in sorted(HERE.rglob("*.py")):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text()
        if "hamletgen" not in text:
            continue
        found.update(re.findall(r"\bhg\.([A-Za-z_][A-Za-z0-9_]*)", text))
        for group in re.findall(r"^from hamletgen import (.+)$", text, re.M):
            found.update(n.strip() for n in group.split("#")[0].split(","))
    return {n for n in found if n}


def test_census_matches_pin() -> None:
    """A consumer that reaches a name this file does not pin must fail HERE, not in production.

    The star-import surface would happily serve a brand-new name, so nothing else in the suite
    would notice the contract widening. This is the line that makes the pin a contract rather
    than a snapshot.
    """
    pinned = set(CONSUMED_PUBLIC) | set(ALIASED_UNDERSCORE) | _submodule_names()
    unpinned = _censused_names() - pinned
    assert not unpinned, f"consumers reach hamletgen names that are not pinned in this file (update contracts/package-surface.md too): {sorted(unpinned)}"
