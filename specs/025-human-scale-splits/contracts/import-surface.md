# Contract: the `settlement` import surface (US3)

`import settlement` is consumed by ~45 modules: `check_village` segments and commons, `hamletgen`,
`site_justice`, `why_placed`, `test_*` modules, every pool `*.gen.py`, and `wip/*.gen.py`. The
package split MUST preserve this surface exactly.

## Contract

1. `import settlement` succeeds and exposes every name any current in-repo consumer references
   (public AND underscore-prefixed - tests reach internals today).
2. `settlement.Settlement` is one class; every current method resolves on it to a single
   definition (mixin MRO, no duplicates - `scripts/check-duplicate-defs.py` is the repo-wide
   backstop).
3. Class-level monkeypatching (`monkeypatch.setattr(settlement.Settlement, "m", ...)`) behaves as
   before. Module-level monkeypatch targets that move into submodules are re-pointed in the tests
   within US3, and the hazard is documented in `settlement/CLAUDE.md` (check_village precedent).
4. The CLI/script entry points that today execute `settlement.py` behavior (none directly -
   generation always goes through gens/hamletgen) are unaffected; `_assert_not_main_tree` keeps
   firing on package import.

## How the re-export list is derived and verified

- **Derived**: the mover script scans all consumers for `settlement.<name>` attribute references
  and `from settlement import ...` names, unions the two, intersects with the monolith's
  module namespace, and generates `settlement/__init__.py` with explicit imports (024 R6
  method). The generated list is committed with the split and recorded below at implement time.
- **Verified**: (a) full test suite + gate green; (b) generation-identity oracle covers the gens
  (the consumers a test run does not import); (c) a one-off import smoke over every consumer
  module (`python3 -c "import <mod>"` per consumer, or the oracle run itself for gens).

## Generated surface

(filled at implement time by the task that generates `settlement/__init__.py`)
