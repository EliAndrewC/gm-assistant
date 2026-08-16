# Contract: the `waterfields` import surface

**Feature**: 110-waterfields-package

The package's one external interface is its import surface. The contract: every import form
below resolves after the split exactly as before it, with zero consumer-file changes.

## Import forms in the wild (census 2026-08-16, re-verify at implement time)

```python
# 1. Named imports - pool gens, hamletgen, settlement/, check_village/ segments, tests
from waterfields import AZE, BEAN_GREEN, aze_w, build_comb, paddy_grain
from waterfields import BANK_MARGIN, drain_bank_clearance, polyline_cum, supply_bank_clearance
from waterfields import build_polder, build_ribbon, build_terraces, hem_on_paddy, PADDY_CELL_ACRES
from waterfields import _RICE_GREEN            # settlement/fields.py:525

# 2. Module-alias attribute access - test_hamletgen.py
import waterfields as wf
wf.build_comb(...); wf._Frame(90.0); wf._miter_normals(pts, F)
```

## Guarantees

- Every censused name resolves from the package root and is the SAME object as the defining
  submodule's binding (identity, not a copy).
- `mypy --strict` accepts the named-import forms (star imports are explicit exports;
  underscore names use the `as`-aliased explicit idiom).
- No consumer is edited; `git diff` scope proves it (SC-002).

## Enforcement

`test_waterfields_surface.py`: pins the censused names, re-runs the census by grep, and
asserts object identity for the consumed constants. Proven to fire (guard-test TDD: break one
re-export, watch it fail, restore).
