# Contract: check_village gate API (022)

## `gate(M, verbose=True, only=None) -> list[str]`

- `only=None` (default): FULL run. Byte-compatible with the legacy gate: same failure list, same
  order, same PASS/FAIL/WAIVE stdout, same waiver semantics. Every existing caller
  (`test_villages.py`, `test_checks.py`, `site_justice.py`, gens' self-gating, `main()`) is
  unaffected.
- `only={"name", ...}`: targeted run. Executes only the segments that can emit the requested BASE
  names plus their dependency closure, in original order. Returns the failure list restricted to
  what ran. For each requested name the verdict equals the full run's.
- Parametrized verdicts (`base[instance]`) are requested by base name and all instances are
  evaluated.
- Errors (both `ValueError`, message names the offender): unknown base name; meta-check requested.
- Purity: no cross-invocation state; safe under pytest-xdist.

## `META_CHECKS: frozenset[str]`

Module constant naming the whole-run meta-checks. The replay imports it; nothing else may
hand-list meta names.

## Registry introspection (internal, for tests/tools)

An importable ordered registry mapping segments -> (free, writes, base check names, meta flag).
Tests pin: the union of base names equals the legacy 549-name set; every name registered; order
stable.

## `test_regressions.py` behavior

Per fixture: `fires` intersect `META_CHECKS` -> full gate; else targeted on the base names of
`fires`. Assertion unchanged: every name in `fires` still in the failure set, else the fixture
"no longer trips".

## CLI

`python3 check_village.py <manifest.json>` unchanged (full run). No new CLI surface required by
this feature.
