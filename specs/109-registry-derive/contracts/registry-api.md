# Contract: check_village.registry (feature 109)

The module keeps its name and its complete import surface. This contract is what `driver.py`,
`__init__.py`'s star re-export, and the four test call sites (see research.md R1) rely on.

## Exports (unchanged names, unchanged types, values equal to the pre-collapse file)

| Symbol | Type | Contract |
|---|---|---|
| `GATE_SEGMENTS` | `tuple[_GateSeg, ...]` | 1,367 rows at introduction; row-for-row equal to the frozen fixture (by name, all six fields, order) |
| `META_CHECKS` | `frozenset[str]` | equal to the fixture's value (`{'waivers_are_live'}` at introduction) |
| `_SEG_DEPS` | `list[set[int]]` | computed from rows exactly as the pre-collapse file computed it |
| `_GateSeg` | `NamedTuple` class | same seven fields, same order, same field types |

## Behavioral contract

- `import check_village` (which pulls the registry) succeeds with no filesystem writes required
  (cache write is attempted but failure-soft) and adds < ~1 s warm / < ~3 s cold to import.
- `gate(M)` and `gate(M, only=...)` produce identical results to the pre-collapse package for
  every manifest, including targeted-run dependency closure (equal `_SEG_DEPS`).
- Star import surface: `from .registry import *` yields exactly the non-underscore names it
  yields today (`GATE_SEGMENTS`, `META_CHECKS`).

## New internal (non-contract) surface

`PLACEMENTS`, `NEEDS_OVERRIDES`, and the derivation/cache helpers are implementation detail:
underscore-prefixed or clearly documented as internal, NOT part of the package star surface, and
free to change shape in future features.
