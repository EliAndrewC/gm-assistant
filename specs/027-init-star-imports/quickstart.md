# Quickstart: verifying and living with the star-import __init__ (feature 027)

## Verify the refactor

```bash
cd .claude/skills/diagram
wc -l check_village/__init__.py        # <= 150
pytest test_check_village_surface.py -n auto -v   # guard + surface pin (file name per tasks.md)
make done                               # full gate: ruff + format + mypy + pytest + coverage
```

## After the refactor: how the package surface works

- `check_village.<public name>` works for every public name of every submodule - star imports carry them, and mypy treats star-imported public names as explicitly exported (no `__all__` needed; probe-verified against mypy 2.3.0, research.md R1).
- Underscore names are **package-private by default**. The few with external consumers are re-exported in `__init__.py`'s aliased block (`from .x import _name as _name`). If you need another underscore name outside the package, add it there - or better, question whether the consumer should import from the submodule directly.
- Adding a new submodule: add its `from .new_module import *` line in dependency order (segments first, `registry`/`driver` last). The clash guard test will fail loudly if the new module's public names collide with an existing module's.
- Do NOT reintroduce `__all__` or explicit public rosters - the entire point of 027 is that those rosters cost ~3,000 lines to state what the star imports already say.
