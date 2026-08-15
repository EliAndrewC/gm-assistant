# Quickstart: Gate Check Registry (022)

All commands from `.claude/skills/diagram/` inside the session clone.

## Capture the baseline oracle (BEFORE touching check_village.py)

    python3 ../../../specs/022-gate-check-registry/oracle_sweep.py capture baseline.json

Records `(sorted verdicts, stdout sha256)` for all 791 regression fixtures + 28 pool manifests.

## Regenerate + verify after the transform

    python3 ../../../specs/022-gate-check-registry/oracle_sweep.py compare baseline.json
    # expected output: IDENTICAL on all manifests, zero diffs

## Targeted-vs-full equivalence over the whole corpus

    python3 ../../../specs/022-gate-check-registry/oracle_sweep.py targeted
    # every fixture: verdicts for its fires' base names equal under only= and full runs

## The usual gates

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy
    python3 -m pytest test_regressions.py test_checks.py -q -n auto --no-cov
    make done          # once, backgrounded

## Measure and record

    python3 timings.py --note "regression replay switched to targeted check execution"
