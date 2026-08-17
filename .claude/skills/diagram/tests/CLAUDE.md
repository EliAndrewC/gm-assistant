# `tests/` - the diagram skill's test bed

**The layout mirrors the source.** A test for `settlement/houses.py` is in
`tests/settlement/test_houses.py`; a test for `pipeline/gencache.py` is in
`tests/pipeline/test_gencache.py`. That is the whole navigation rule - if you know which module you
changed, you know which directory to open.

| directory | tests | its own index |
|---|---|---|
| `settlement/` | the Mode B drawing engine | [CLAUDE.md](settlement/CLAUDE.md) |
| `check_village/` | the gate (the ~1,371-segment check battery) | [CLAUDE.md](check_village/CLAUDE.md) |
| `hamletgen/` | the scripted hamlet generator | - |
| `waterfields/` | the water-first field engine | - |
| `pipeline/` | the cache, regen driver, render cache and pool index | - |
| `tools/` | the audits and diagnostics that are under the 100% rule | - |
| `fixtures/` | DATA, not tests: frozen red SVGs (Mode A negative fixtures), `gate_check_names.json`, `registry_legacy_rows.json` | - |

At the root of `tests/` sit the suites that are not about one module:

- **`test_villages.py`** - the pool sweep. Generates every LIVE map (via `gencache.gate_obtain`, so
  a verified hit skips generation but never checking) and runs the full check battery on each.
  Also enforces the per-gen CPU budgets in `GEN_TIME_BUDGETS`.
- **`test_regressions.py`** - replays the frozen negative-fixture corpus in `pool/regressions/`,
  demanding each manifest still fires the checks it was frozen to fire.
- **`test_compound.py` / `test_citybudget.py`** - the two engine modules that are still single
  top-level files.

## Running it

    python3 -m pytest -q -n auto                      # everything (from the skill root)
    python3 -m pytest tests/settlement/ -q -n auto    # one mirrored package, WHOLE
    make done                                          # the real gate: lint + format + mypy + tests + coverage

**Always `-n auto`.** Serial pytest is about 7x slower here; the 695-manifest regression replay is
~2 minutes under the gate and 13.4 minutes serial. And before the gate, run the WHOLE affected file
or directory, never a `-k` subset: a filter selects the tests you were thinking about, and a change
breaks the ones you were not. Both rules, with the round trips they each cost once, are in the
skill's [`../CLAUDE.md`](../CLAUDE.md).

`testpaths = ["tests"]` in `pyproject.toml` pins collection here. Without it pytest walks the whole
skill directory, and from the repo root it walks every `.clones/` checkout as well - pytest does
not read `.gitignore`.

## Conventions

- **`_builders.py`** in a mirrored package holds that package's shared manifest/settlement
  builders. Import it by package path: `from tests.check_village._builders import bldg, house`.
  These files do not start with `test_`, which is why the engine-tree walks prune `tests/` by name
  (below).
- **`test_surface.py`** in `check_village/`, `hamletgen/` and `waterfields/` is the package-surface
  guard: it censuses what the rest of the skill actually reaches through the package and proves the
  `__init__.py` re-export still resolves it. Feature 027 replaced hand-maintained rosters with star
  imports plus these guards, so the surface is derived and the guard is what makes that safe.
- **Every found defect becomes a check, and the check gets a negative fixture.** Mode B fixtures
  are frozen manifests in `pool/regressions/`; Mode A fixtures are frozen bad SVGs in
  `fixtures/`. Coverage alone does not prove a check has teeth - a red fixture does.

## `tests/` is invisible to the generation cache, on purpose

`gencache.engine_files()` and `render_cache.engine_fingerprint()` both prune this directory. Before
the 2026-08-16 reorganization every test was a root-level `test_*.py` and the name filter covered
them; under `tests/` the helpers match no name filter, and counting them as engine inputs would
invalidate every map in the pool on any edit to a test helper.

The consequence worth knowing: **a `.py` file placed under `tests/` can never affect a map's cache
key.** That is correct for tests and helpers. If you ever need a module here that a generator
imports, it does not belong here - put it in the engine, or in
[`../l7r/diagram/pipeline/`](../l7r/diagram/pipeline/CLAUDE.md).

**`tests/` did not move under `l7r/diagram/` and should not.** The skill directory stays the
`sys.path` root (feature 119), so `HERE`-style roots computed here are unchanged, while the engine's
own roots moved two levels deeper. Tests import the engine by its full name -
`from l7r.diagram.settlement import Settlement`, `from l7r.diagram import check_village`.
