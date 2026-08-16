# Quickstart: verifying 109-registry-derive

All commands from `.claude/skills/diagram/` inside the working clone.

```bash
# 1. Derived rows == frozen legacy fixture (the transition oracle)
pytest test_check_village_surface.py test_registry_derive.py -n auto -q

# 2. Full behavioral proof: whole diagram test bed, regression corpus included
pytest . -n auto -q

# 3. Lint / format / types on the touched package
ruff check check_village && ruff format --check check_village
mypy --strict check_village

# 4. Import-time budget (FR-009): warm-cache import cost
python3 - <<'EOF'
import time
t0 = time.perf_counter(); import check_village  # noqa: F401
print(f"import: {time.perf_counter() - t0:.3f}s")
EOF

# 5. Reproduce the research numbers (optional)
python3 ../../../specs/109-registry-derive/probe2_refined.py
```

Guard-fires evidence (FR-004 / SC-003) is recorded in tasks.md against the task that ran each
perturbation red-then-green.
