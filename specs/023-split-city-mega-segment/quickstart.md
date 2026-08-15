# Quickstart: Split the City Mega-Segment (023)

All commands from `.claude/skills/diagram/` unless noted. The transformer is one-shot: after the
feature lands, `check_village.py` is the hand-maintained truth and `split_megaseg.py` is retired
(never imported, never under coverage), exactly like 022's `transform_gate.py`.

```sh
# 0. Baseline (BEFORE any transform) - fresh capture at the current tip, plus timings
python3 ../../../specs/022-gate-check-registry/oracle_sweep.py capture /tmp/claude-1000/-gm-assistant/*/scratchpad/oracle-baseline-023.json
time python3 -c "import check_village"                       # import-time baseline
time python3 -m pytest test_regressions.py -n auto -q        # replay baseline

# 1. Census (analyze only - prints stats, hard-fails on any model violation)
python3 ../../../specs/023-split-city-mega-segment/split_megaseg.py census

# 2. Transform (rewrites check_village.py in place; idempotent from the pre-split file only)
python3 ../../../specs/023-split-city-mega-segment/split_megaseg.py generate

# 3. Oracle battery (all must be green / zero-diff)
python3 ../../../specs/022-gate-check-registry/oracle_sweep.py compare /tmp/.../oracle-baseline-023.json
python3 ../../../specs/022-gate-check-registry/oracle_sweep.py targeted

# 4. Teeth check: invert one outer-guard check + one walled-guard check, expect their fixtures
#    red in targeted mode, revert (git checkout -- check_village.py is NOT usable here - the
#    transform is already applied; invert/revert by editing the two lines).

# 5. Size verification (FR-002 / SC-001)
python3 - <<'EOF'
import ast
tree = ast.parse(open('check_village.py').read())
worst = max(((sum(1 for x in ast.walk(n) if isinstance(x, ast.stmt)), n.name)
             for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)))
print("largest function:", worst)   # must be well under 1000; new _seg_0563_* under 400
EOF

# 6. Whole affected test files, then the gate (backgrounded; act on the notification)
python3 -m pytest test_checks.py test_regressions.py -n auto -q
make done > /tmp/.../make-done.log 2>&1     # nothing appended after - exit code must be honest
```
