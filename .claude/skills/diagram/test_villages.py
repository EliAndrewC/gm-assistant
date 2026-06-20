#!/usr/bin/env python3
"""Automated tests for Mode B settlement maps (diagram skill).

Regenerates every village in pool/ from its generator and runs the full
check_village gate over the resulting manifest. This pins the whole Mode B
process: any change to settlement.py or a village spec that breaks an invariant
(no overlaps, every field ringed, households-consistent house counts, channels
anchored, no label overlaps, ...) fails here.

Works under pytest OR standalone:
    python3 -m pytest test_villages.py -q     # from the diagram skill directory
    python3 test_villages.py                  # no pytest required
"""
import glob
import os
import runpy
import sys

import check_village

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, "pool")
GENERATORS = sorted(glob.glob(os.path.join(POOL, "*.gen.py")))


def _regen_and_gate(gen):
    """Run a village generator, then its gate; return True if every check passes.
    Runs the generator IN-PROCESS (not as a subprocess) so coverage measures settlement.py."""
    runpy.run_path(gen, run_name="__main__")
    manifest = gen[: -len(".gen.py")] + ".json"
    assert os.path.exists(manifest), f"{os.path.basename(gen)} produced no manifest"
    return check_village.main(manifest) == 0


def test_at_least_one_village_exists():
    assert GENERATORS, "no *.gen.py village generators found in pool/"


def test_villages_pass_gate():
    failures = [os.path.basename(g) for g in GENERATORS if not _regen_and_gate(g)]
    assert not failures, f"villages failed the gate: {failures}"


if __name__ == "__main__":
    rc = 0
    for g in GENERATORS:
        ok = _regen_and_gate(g)
        print(("PASS " if ok else "FAIL ") + os.path.basename(g))
        rc |= 0 if ok else 1
    sys.exit(rc)
