"""The `rolls_map` marker must not rot (feature 127).

WHY THIS GUARD EXISTS. `make quick` used to deselect two FILES and announce, in its own output, that
"the map-rolling tests are NOT included". That was false: the three polder tests in
`hamletgen/test_water.py` each roll a hamlet and cost 110 s, 86 s and 63 s, and they ran on every
invocation. `quick` measured 254 SECONDS while every blocked command was being funnelled toward it
as the cheap option - a guard pointing at a fast path that was not fast.

A file list cannot track which tests roll a map: a new one lands in an unlisted file and the target
silently gets slower. A marker travels with the test, and this is what makes the marker true.

IT MATCHES CALLS, NOT TEXT, and that lesson was learned three times in one day. The first version
regex'd the source, so a test whose DOCSTRING mentioned "cohort()'s pool children" was reported as
unmarked. The same defect made the command hook block a grep, a commit message and its own test
harness. Walking the AST for real call nodes cannot make that mistake, because prose is not a call.
"""

from __future__ import annotations

import ast
import pathlib

# THE RECEIVER IS PART OF THE SIGNAL, and leaving it out was the fourth instance of this feature's
# recurring mistake. `build` and `generate` are ordinary words: `tests/check_village/` passes a
# callable named `build` as a PARAMETRIZED FIXTURE ARGUMENT, so matching the bare name reported two
# gate tests as un-marked map-rollers. They roll nothing.
#
# So a dotted call must come off the generator module, and only the distinctive bare names count.
ROLLING_ATTRS = frozenset({"build", "generate", "main", "roll_village", "cohort", "gate_obtain"})
ROLLING_RECEIVERS = frozenset({"hg", "hamletgen", "driver"})
ROLLING_BARE = frozenset({"roll_village", "cohort", "gate_obtain"})

# ADDED AFTER PROFILING RATHER THAN BY GUESSING, and the two additions were the two most expensive
# tests in the suite: `hg.main([...])` runs the generator through its CLI (24.8 s) and
# `gencache.run_and_record` regenerates a real scripted hamlet (58.5 s). Neither matched the first
# list, so both kept running inside `make quick` while the marker guard reported everything clean.
#
# `run_and_record` and `gencache` were tried here and REMOVED. They caught 20 cache tests that use
# tiny synthetic gens and finish in milliseconds - marking those would have cost `make quick` real
# coverage to save nothing. Only ONE cache test rolls a real map, and it is marked by hand.
#
# THE LESSON, which is why this comment exists: a list of "calls that roll a map" is a GUESS unless
# it is checked against a MEASUREMENT, and the guess errs in both directions. `make durations` is the
# check - and `make quick` now enforces its own time budget, so a slow unmarked test makes the target
# fail rather than quietly making it slower.
TESTS = pathlib.Path(__file__).resolve().parent


def _rolls_a_map(node: ast.AST) -> bool:
    """Does this test actually CALL something that generates a settlement?"""
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        fn = sub.func
        if isinstance(fn, ast.Attribute) and fn.attr in ROLLING_ATTRS:
            if isinstance(fn.value, ast.Name) and fn.value.id in ROLLING_RECEIVERS:
                return True
        elif isinstance(fn, ast.Name) and fn.id in ROLLING_BARE:
            return True
    return False


def test_every_map_rolling_test_carries_the_rolls_map_marker() -> None:
    missing: list[str] = []
    for p in sorted(TESTS.rglob("test_*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            if not _rolls_a_map(node):
                continue
            decorated = {d.attr for dec in node.decorator_list for d in ast.walk(dec) if isinstance(d, ast.Attribute)}
            if "rolls_map" not in decorated:
                missing.append(f"{p.relative_to(TESTS)}::{node.name}")
    assert not missing, "these tests generate a settlement but carry no @pytest.mark.rolls_map, so `make quick` would run them and get slower without saying so:\n  " + "\n  ".join(missing)
