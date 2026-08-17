#!/usr/bin/env python3
"""Replay the captured regression corpus (pool/regressions/*.json).

The third leg of the Mode B testing discipline (see settlements.md "Three testing disciplines"):

  - tests/test_villages.py    - the GOOD maps still PASS the whole gate (integration).
  - tests/check_village/      - each check still FIRES on a minimal synthetic break (unit).
  - tests/test_regressions.py (this) - the actual BAD manifests we hit while iterating a map stay
                        caught: every fixture lists the checks it MUST trip, and we assert they
                        still do. A permanent, growing guard - drop the manifest of any map that
                        slips past a check (or that a newly-tightened check should have caught)
                        into pool/regressions/ with a `_regression` block and it is pinned forever.

Each fixture is a normal manifest plus a top-level `_regression` block:
    "_regression": {"fires": ["check_name", ...], "source": "where it came from"}
We pop that block and assert the gate still trips every name in `fires`.

TARGETED since feature 022 (specs/022-gate-check-registry/): the replay runs
`gate(M, only=<fires' base names>)`, which executes just those checks plus the shared derivations
they depend on - a 210-strong cohort of frozen whole-city fixtures used to pay a full 189-check
gate apiece (~61% of suite CPU) to verify one check each. Verdict identity between targeted and
full runs is held by the 022 oracle sweeps and by
`test_feature_022_targeted_verdict_matches_the_full_gate` (in tests/check_village/); a fixture naming a
META check (whole-run state, e.g. waivers_are_live) falls back to the full gate.

Regenerate the backfilled corpus from the in-test fixtures with `python3 -m l7r.diagram.tools.make_regressions`;
hand-dropped real-map captures are replayed identically and survive regeneration if named
distinctly from the auto-captured ones.

    python3 -m pytest test_regressions.py -q
    python3 test_regressions.py
"""

import glob
import json
import os

import pytest

from l7r.diagram import check_village

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # the skill root; the tests live one level down in tests/
CORPUS = sorted(glob.glob(os.path.join(HERE, "pool", "regressions", "*.json")))


def _load(path):
    with open(path) as fh:
        M = json.load(fh)
    fires = M.pop("_regression")["fires"]
    return M, fires


def _replay(M, fires):
    """The fixture's verdicts, via the targeted gate (full-gate fallback for meta-checks)."""
    bases = {f.split("[")[0] for f in fires}
    if bases & check_village.META_CHECKS:
        return set(check_village.gate(M, verbose=False))
    return set(check_village.gate(M, verbose=False, only=bases))


def test_corpus_is_not_empty():
    assert CORPUS, "no regression fixtures found in pool/regressions/"


@pytest.mark.parametrize("path", CORPUS, ids=[os.path.basename(p) for p in CORPUS])
def test_regression_fixture_still_fires(path):
    M, fires = _load(path)
    failed = _replay(M, fires)
    missing = [c for c in fires if c not in failed]
    assert not missing, f"{os.path.basename(path)} no longer trips: {missing}"


if __name__ == "__main__":
    rc = 0
    for p in CORPUS:
        M, fires = _load(p)
        failed = _replay(M, fires)
        missing = [c for c in fires if c not in failed]
        print(("PASS " if not missing else "FAIL ") + os.path.basename(p) + (f"  missing={missing}" if missing else ""))
        rc |= 0 if not missing else 1
    raise SystemExit(rc)


# Feature 022: the targeted replay no longer runs every check against every fixture, which
# uncovered 33 statements that only ever executed during fixtures' full-gate replays - deep
# branches needing frozen bad geometry (a capital deferral pass, a samurai-estate label pile-up,
# village fallow/shrine/pond forks). These four fixtures were selected EMPIRICALLY (greedy
# line-coverage search, specs/022-gate-check-registry/) to cover them; they also keep full-mode
# gate() integration-tested inside the suite. If coverage drops here again, re-run the greedy
# search rather than guessing fixtures.
_FULL_GATE_SENTINELS = [
    "stable_troughs_clip_the_well_house_roof_tango.json",
    "capital_fullness_deferral_fires_on_the_first_pass_shiro_daika.json",
    "city_samurai_estates_fire_on_a_tight_wall_cluster.json",
    "settlement_wells_fire_on_a_village_with_no_wells.json",
]


@pytest.mark.parametrize("name", _FULL_GATE_SENTINELS)
def test_full_gate_coverage_sentinel(name):
    path = os.path.join(HERE, "pool", "regressions", name)
    M, fires = _load(path)
    failed = set(check_village.gate(M, verbose=False))
    missing = [c for c in fires if c not in failed]
    assert not missing, f"{name} no longer trips under the FULL gate: {missing}"


# The 2026-08-16 legacy freeze (migration-plan.md "The accepted trade") removed the hand-authored
# maps from the test_villages sweep, which uncovered the handful of check_village branches only
# those maps' full-gate runs reached (a town's fire/justice variants, minami's no-Imperial-road
# walled-city branch, the odd water fork). These FROZEN pool manifests - committed, permanent,
# never regenerated - are replayed through the FULL gate purely as coverage carriers, selected by
# the same greedy line-coverage search as the sentinels above (if coverage drops here again,
# re-run the search rather than guessing). NOTHING is asserted about their verdicts: a frozen map
# is allowed to fail rules added after the freeze, so the only claim held is that the gate still
# RUNS on old manifests - the claim the whole corpus already makes.
_FROZEN_POOL_COVERAGE_CARRIERS = [
    "towns/hirameki.json",
    "towns/hoshizora.json",
    "provincial-cities/minami.json",
    "hamlets/akagahara.json",
    "hamlets/enokida.json",
]


@pytest.mark.parametrize("rel", _FROZEN_POOL_COVERAGE_CARRIERS)
def test_frozen_pool_full_gate_coverage_carrier(rel):
    with open(os.path.join(HERE, "pool", rel)) as fh:
        M = json.load(fh)
    failed = check_village.gate(M, verbose=False)
    assert failed is not None  # verdicts deliberately unchecked - see the carrier comment above
