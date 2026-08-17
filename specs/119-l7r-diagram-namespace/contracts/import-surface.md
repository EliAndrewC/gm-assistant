# Contract: the import surface, before and after

The only interface this feature changes is how code and documentation NAME the modules. This file is
the authoritative mapping; `tasks.md` executes it and the gate proves it.

## Python imports

| before | after |
|---|---|
| `from settlement import Settlement` | `from l7r.diagram.settlement import Settlement` |
| `import check_village` | `import l7r.diagram.check_village` |
| `from waterfields import …` | `from l7r.diagram.waterfields import …` |
| `from hamletgen import HamletSpec, generate` | `from l7r.diagram.hamletgen import HamletSpec, generate` |
| `from pipeline import …` / `import pipeline.regen` | `from l7r.diagram.pipeline import …` |
| `import tools.why_placed` | `import l7r.diagram.tools.why_placed` |
| `import compound` | `import l7r.diagram.compound` |
| `import citybudget` | `import l7r.diagram.citybudget` |
| `from .geom import centroid` (intra-package) | **unchanged** |

**Unchanged by construction**: every relative import inside a moved package, and every generator's
`sys.path` bootstrap block (`HERE` / `SKILL = dirname(dirname(HERE))` / `sys.path.insert`), because
`pool/` does not move.

## Command lines

| before | after |
|---|---|
| `python3 -m check_village pool/<type>/<map>.json` | `python3 -m l7r.diagram.check_village pool/<type>/<map>.json` |
| `python3 -m pipeline.regen pool/*/*.gen.py` | `python3 -m l7r.diagram.pipeline.regen pool/*/*.gen.py` |
| `python3 -m tools.why_placed …` | `python3 -m l7r.diagram.tools.why_placed …` |
| `python3 -m hamletgen --batch 24` | `python3 -m l7r.diagram.hamletgen --batch 24` |

All are still run **from the skill directory**, which remains the `sys.path` root. The rule that a
packaged module is run as a module (`-m`), never as a loose script path, is unchanged and now
matters slightly more: running a file by path would put `l7r/diagram/` on `sys.path` and give one
file two identities.

## Webapp

| before | after |
|---|---|
| `import l7r` (for the CherryPy mount side effect) | `import l7r.app` |
| `cherryd --import l7r` | `cherryd --import l7r.app` |
| `from l7r import app as app_module` | **unchanged** |
| `from l7r.names import …` and every other `l7r.<mod>` import | **unchanged** |
| `pytest --cov=l7r` | **unchanged** |

## Gate configuration

| file | key | change |
|---|---|---|
| `diagram/pyproject.toml` | `[tool.ruff.lint.per-file-ignores]` | 5 keys re-prefixed with `l7r/diagram/` |
| | `[tool.mypy] files` | every entry re-prefixed |
| | `[tool.coverage.run] source` | every dotted name re-prefixed; the one-by-one listing style is preserved, not loosened |
| | `[tool.coverage.run] omit` | `pool/*/*.gen.py` unchanged (pool does not move) |
| `diagram/Makefile` | coverage `--include` / `--omit` globs | must still select the `settlement/` tree at its new path |

## What is deliberately NOT provided

- **No compatibility shim** at any old path. Two live names for one module is the ambiguity the
  namespace exists to remove.
- **No console scripts / entry points.** Neither tree is an installed distribution and this feature
  does not make one.
- **No `l7r/__init__.py`**, ever, in either portion. This is the contract the guard tests enforce.
