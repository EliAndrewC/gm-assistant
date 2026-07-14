#!/usr/bin/env python3
"""Replay the captured regression corpus (pool/regressions/*.json).

The third leg of the Mode B testing discipline (see settlements.md "Three testing disciplines"):

  - test_villages.py  - the GOOD maps still PASS the whole gate (integration).
  - test_checks.py    - each check still FIRES on a minimal synthetic break (unit).
  - test_regressions.py (this) - the actual BAD manifests we hit while iterating a map stay
                        caught: every fixture lists the checks it MUST trip, and we assert they
                        still do. A permanent, growing guard - drop the manifest of any map that
                        slips past a check (or that a newly-tightened check should have caught)
                        into pool/regressions/ with a `_regression` block and it is pinned forever.

Each fixture is a normal manifest plus a top-level `_regression` block:
    "_regression": {"fires": ["check_name", ...], "source": "where it came from"}
We pop that block and assert gate(manifest) still includes every name in `fires`.

Regenerate the backfilled corpus from the in-test fixtures with `python3 make_regressions.py`;
hand-dropped real-map captures are replayed identically and survive regeneration if named
distinctly from the auto-captured ones.

    python3 -m pytest test_regressions.py -q
    python3 test_regressions.py
"""

import glob
import json
import os

import pytest

import check_village

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = sorted(glob.glob(os.path.join(HERE, "pool", "regressions", "*.json")))


def _load(path):
    with open(path) as fh:
        M = json.load(fh)
    fires = M.pop("_regression")["fires"]
    return M, fires


def test_corpus_is_not_empty():
    assert CORPUS, "no regression fixtures found in pool/regressions/"


@pytest.mark.parametrize("path", CORPUS, ids=[os.path.basename(p) for p in CORPUS])
def test_regression_fixture_still_fires(path):
    M, fires = _load(path)
    failed = set(check_village.gate(M, verbose=False))
    missing = [c for c in fires if c not in failed]
    assert not missing, f"{os.path.basename(path)} no longer trips: {missing}"


if __name__ == "__main__":
    rc = 0
    for p in CORPUS:
        M, fires = _load(p)
        failed = set(check_village.gate(M, verbose=False))
        missing = [c for c in fires if c not in failed]
        print(("PASS " if not missing else "FAIL ") + os.path.basename(p) + (f"  missing={missing}" if missing else ""))
        rc |= 0 if not missing else 1
    raise SystemExit(rc)
