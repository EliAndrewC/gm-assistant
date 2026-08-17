"""Site selection for `tools/cache_audit.py`.

`cache_audit` is a by-hand driver and deliberately outside the 100% rule (tools/CLAUDE.md - its
behavior is subprocess orchestration). Its SITE SELECTION is not: it is pure logic over an AST, and
getting it wrong is what made a 3-trial run take 19 attempts and eleven minutes while auditing the
cache exactly three times.

Both filters below exist because a mutation that changes no byte tests NOTHING about the cache, and
before 2026-08-17 such a trial printed the same `[OK ]` as a real one.
"""

import ast

from l7r.diagram.tools import cache_audit

# line 1: a default argument (15) - evaluated at DEFINITION time, so its line is always "executed"
# line 2: a body literal in a function the maps DO call
# line 5/6: a function the maps never call
SRC = "def used(a, b=15):\n    return a * 3\n\n\ndef never_called():\n    return 99 * 7\n"
EXECUTED = {1, 2, 5}  # both `def` lines run at import; only `used`'s body actually runs


def test_numeric_sites_skips_default_argument_literals():
    """A default's literal sits on the `def` line, which coverage always reports as executed even
    when nothing ever calls the function - so `covered` alone cannot see that it is inert. And when
    every caller passes the argument explicitly, perturbing it moves nothing at all. That pair is
    where most of the eleven minutes went."""
    values = [ast.literal_eval(s[3]) for s in cache_audit.numeric_sites(SRC, EXECUTED)]
    assert 15 not in values, "a default-argument literal was offered as a mutation site"


def test_numeric_sites_skips_a_line_the_maps_never_execute():
    """A literal in a function no audited map calls cannot change an artifact, so mutating it is a
    guaranteed-wasted sweep pair. It is also provably safe to exclude: with the artifacts identical,
    a cached sweep and a fresh sweep agree no matter what the key does."""
    sites = cache_audit.numeric_sites(SRC, EXECUTED)
    assert [s[0] for s in sites] == [2], f"expected only the executed body literal on line 2, got {sites}"


def test_numeric_sites_still_finds_the_literal_that_matters():
    """The filters must not be so eager that nothing survives - an empty candidate pool is the same
    silent no-op in the other direction."""
    sites = cache_audit.numeric_sites(SRC, EXECUTED)
    assert len(sites) == 1 and ast.literal_eval(sites[0][3]) == 3
    lineno, col, end_col, text = sites[0]
    assert SRC.splitlines()[lineno - 1][col:end_col] == text
