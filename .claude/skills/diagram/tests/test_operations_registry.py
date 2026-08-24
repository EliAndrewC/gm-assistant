"""Every entry point has a registry row, and every row a make target that exists (feature 127).

WHY ALL THREE DIRECTIONS. A refusal that cannot name the right command is only half a guard: the
whole design rests on the correct route being one line away, because a guard that blocks a legitimate
action without offering the alternative is one that gets worked around. That is not hypothetical -
while this feature was being built, `pytest` was gated before `make durations` existed, so "why is
this slow" had no answer except the override.

And an entry point added later WITHOUT a row would ship ungated, because the failure mode is silence:
nothing crashes, nothing warns, the command simply runs.

The registry is enumerated by hand on purpose (see its comment in `_invocation.py`), so these tests
are what keep a hand-made list honest against the tree.
"""

from __future__ import annotations

import pathlib
import re

from l7r.diagram._invocation import OPERATIONS, target_for

SKILL = pathlib.Path(__file__).resolve().parents[1]


def _entry_points() -> set[str]:
    """Every module runnable as `python3 -m ...`: a package `__main__.py`, or a `__main__` guard.

    Both forms, because the first census of this tree looked only for `__main__.py` and reported 18
    entry points. Walking for the guard as well found 20 - `compound` and `citybudget` had neither a
    package CLI nor an obvious name, and `compound` DRAWS a Mode A plan."""
    found: set[str] = set()
    for p in (SKILL / "l7r").rglob("*.py"):
        mod = ".".join(p.relative_to(SKILL).with_suffix("").parts)
        if p.name == "__main__.py":
            found.add(mod.rsplit(".__main__", 1)[0])
        elif re.search(r'^if __name__ == ["\']__main__["\']:', p.read_text(encoding="utf-8"), re.M):
            found.add(mod)
    return found


def test_every_entry_point_has_a_registry_row() -> None:
    missing = sorted(_entry_points() - set(OPERATIONS))
    assert not missing, "these are runnable as `python3 -m ...` but carry no row in _invocation.OPERATIONS, so a refusal could not name their make target:\n  " + "\n  ".join(missing)


def test_no_registry_row_names_a_module_that_is_gone() -> None:
    """The other direction: a row for a deleted module sends a session to a command for something
    that no longer exists, which reads as a broken guard rather than a stale list."""
    stale = sorted(set(OPERATIONS) - _entry_points())
    assert not stale, "registry rows for modules that no longer exist:\n  " + "\n  ".join(stale)


def test_every_registry_target_exists() -> None:
    makefile = (SKILL / "Makefile").read_text(encoding="utf-8")
    targets = set(re.findall(r"^([a-z][a-z0-9-]*):", makefile, re.M))
    missing = sorted({t for t, _cost in OPERATIONS.values()} - targets)
    assert not missing, "the registry names make targets that do not exist, so a refusal would send a session to a command that fails:\n  " + "\n  ".join(missing)


def test_every_row_declares_a_known_cost() -> None:
    """`cost` decides whether the target PROMPTS. A typo here would silently move an operation
    between the two behaviors, which is exactly the class of drift this feature exists to stop."""
    bad = sorted(f"{m}={c}" for m, (_t, c) in OPERATIONS.items() if c not in {"cheap", "expensive"})
    assert not bad, "rows with an unrecognized cost:\n  " + "\n  ".join(bad)


def test_an_unknown_module_still_gets_a_usable_target() -> None:
    """A guard that crashes is worse than one that points somewhere slightly wrong."""
    assert target_for("l7r.diagram.not.a.real.module") == "help"
