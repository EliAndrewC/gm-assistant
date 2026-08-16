# Implementation Plan: Cache-Backed Gate

**Branch**: `026-cache-backed-gate` (no branch; `SPECIFY_FEATURE=026-cache-backed-gate`) | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/026-cache-backed-gate/spec.md`

## Summary

Reverse the 2026-08-08 "gate never reads the cache" rule (GM decision 2026-08-16): `make done`'s
live-map sweep consults the gen cache and, on a verified hit, loads the cached manifest and runs
the full current check battery against it - skipping only generation. Before flipping the default,
the key's one known blind spot closes: installed-distribution versions + renderer font bytes join
the key, so pip-level changes invalidate automatically. Coverage floors stay meaningful via per-map
coverage data stored in each entry (recorded by a `coverage run --parallel-mode` generation
subprocess on miss, replayed into the run's combine on hit). `GATE_NO_CACHE=1` bypasses;
`cache_audit.py` remains the standing empirical auditor and runs as part of this feature's own
verification. Full design rationale in [research.md](research.md); interface in
[contracts/gate-cache.md](contracts/gate-cache.md).

## Technical Context

**Language/Version**: Python 3.14 (container pin)

**Primary Dependencies**: pytest + pytest-cov + pytest-xdist (`-n auto`), coverage.py
(parallel-mode data files), `importlib.metadata` (stdlib), resvg (version already keyed), PIL
(consumer of the newly-keyed font files)

**Storage**: the per-clone `.gencache/` entry store (atomic temp-then-replace publish, meta.json
last) - extended per [data-model.md](data-model.md)

**Testing**: the skill's own `make done` (ruff, format, mypy per-module ratchet, pytest -n auto,
100% per-module coverage + settlement/ ratchet floor 94); new pinning tests per the contract;
`cache_audit.py` for the byte-identity property; `timings.py` for SC-001

**Target Platform**: the dev container (22 cpus measured context; per-clone caches)

**Project Type**: existing single-directory skill package (`.claude/skills/diagram/`)

**Performance Goals**: warm gate >= 5% faster than cold gate wall clock (SC-001), measured and
ledgered; iteration path (`regen.py`) pays ZERO new overhead

**Constraints**: failure direction always "regenerate unnecessarily, never serve staleness";
checking never cached; atomic entry publish preserved; immunity test and regression replay
untouched; no map output changes (byte-identity oracle)

**Scale/Scope**: 4 live scripted hamlets today; every future tier conversion multiplies the payoff
(city-class gens measured ~155 s under-gate CPU pre-freeze)

## Constitution Check

- **I. Accessibility-First Viewports**: N/A - no UI introduced or modified.
- **II. Bold, Intentional Design**: N/A - no new UI surfaces.
- **III. Pool Data Conventions**: N/A - no generated pool content added or changed (pool
  artifacts are byte-identical by construction).
- **IV. One Canonical Home for GM Source**: N/A - no SOURCE blocks added or moved.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: PASS - no task touches SOURCE-marked
  content.
- **VI. Verify Before Reporting Done**: PASS - verification is itself most of the feature:
  `make done` cold AND warm with identical verdicts, all six pinning tests with demonstrated
  teeth, `cache_audit.py` green, `timings.py` ledger block for SC-001. Each task in tasks.md
  names its check.
- **VII. De-Localized Generation by Default**: N/A - no pool content generated.
- **VIII. Direct Voice Over Framing Distance**: N/A - no in-world prose.
- **IX. Setting Integration**: N/A - no setting content; no new named figures.
- **X. Python Discipline (NON-NEGOTIABLE)**: PASS - ruff + format + mypy (per-module ratchet
  respected; new code written to strict), red-green TDD for the new gate behavior (pinning tests
  written to fail against the old behavior first where the harness allows, teeth demonstrated by
  reversion otherwise), 100% per-module coverage held (the feature's whole point is keeping that
  gate honest), no swallowed exceptions (conservative degradation is explicit, not `except:
  pass` - every fallback returns a "regenerate" verdict), behavior-named tests. File scale: all
  touched files stay well under ~1,000 raw lines (gencache.py ~450 today; growth ~150 lines).
- **XI. Japanese Authenticity**: N/A - no kanji surfaces.
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: N/A - the feature changes nothing any
  generator asserts about the world; it is output-preserving by construction and `cache_audit.py`
  is the empirical enforcement (research.md R8). No rendered artifact changes to re-examine.

**Post-design re-check (after Phase 1)**: unchanged - the design introduced no UI, no content, no
generator-behavior change. Gate statuses stand.

## Project Structure

### Documentation (this feature)

```text
specs/026-cache-backed-gate/
├── plan.md              # this file
├── spec.md
├── research.md          # Phase 0 - decisions R1-R8
├── data-model.md        # Phase 1 - cache entry extensions + state transitions
├── quickstart.md        # Phase 1 - operator view of the new contract
├── contracts/
│   └── gate-cache.md    # Phase 1 - gate_obtain contract, env vars, pinning-test table
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks - not created by /speckit-plan)
```

### Source Code (repository root)

```text
.claude/skills/diagram/
├── gencache.py          # + dependency-state key input; + gate_obtain(); entry extensions
├── regen.py             # docstring only (iteration path unchanged)
├── test_villages.py     # _regen_and_gate -> gate_obtain; budget assert on child-reported CPU
├── test_gencache.py     # retire old pinning test; add the six contract tests + spike test
├── Makefile             # one `coverage combine --append` line before the report calls
├── timings.py           # + warm_gate benchmark; fix bench_hamlet (-m check_village);
│                        #   retarget bench_cache minami -> sawada
├── timings.md           # ledger blocks appended by measurement runs
├── CLAUDE.md            # cache/sweep doctrine rewrite + dependency-change procedure
└── cache_audit.py       # unchanged code; run as verification
docs/iteration-loop.md   # + GM 2026-08-16 >=5% whole-process threshold rule
```

**Structure Decision**: everything lands in the existing skill directory - this is a change to the
skill's own gate/cache machinery, no new packages. The only file outside it is the
`docs/iteration-loop.md` doctrine addition.

**Agent context note**: root CLAUDE.md carries no SPECKIT plan-pointer markers - deliberate
project convention ("no single active plan tracked here"); the highest-numbered specs/ dir is the
pointer. No agent-context update to perform.

## Complexity Tracking

No constitution gate is DEFERRED and no violation needs justification.
