# Quickstart: Human-Scale Files (024)

All commands from `.claude/skills/diagram/` in the session clone unless noted.

```bash
# 0. Baseline (monolith untouched)
python3 ../../../specs/022-gate-check-registry/oracle_sweep.py capture \
        ../../../specs/024-human-scale-files/oracle_pre.json

# 1. Stage 1 - split the 9 oversized segments in place
python3 ../../../specs/024-human-scale-files/split_oversized.py        # writes check_village.py
python3 ../../../specs/022-gate-check-registry/oracle_sweep.py compare \
        ../../../specs/024-human-scale-files/oracle_pre.json           # must be zero diffs
python3 ../../../specs/022-gate-check-registry/oracle_sweep.py targeted
python3 make_regressions.py --pin-names   # regenerate test_fixtures/gate_check_names.json
                                          # (or the documented regeneration path for that fixture)

# 2. Stage 2 - monolith -> package
python3 ../../../specs/024-human-scale-files/split_package.py          # writes check_village/, deletes check_village.py
python3 ../../../specs/022-gate-check-registry/oracle_sweep.py compare \
        ../../../specs/024-human-scale-files/oracle_pre.json
python3 ../../../specs/022-gate-check-registry/oracle_sweep.py targeted

# 3. Cheap linters, then the full gate (background, never polled)
python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy
make done > /tmp/claude-1000/-gm-assistant/*/scratchpad/gate.log 2>&1   # background it

# 4. Docs sweep - no stale invocations anywhere
grep -rn "python3 check_village.py" ../.. --include="*.md"   # must be empty
```

Constitution amendment + template/CLAUDE.md mirrors are plain edits (see tasks) and docs-only -
they skip the gate.

**Verify after the feature** (GM test steps):
- `cd .claude/skills/diagram && python3 -m check_village pool/<any>.json` prints the familiar
  verdict stream.
- `python3 - <<< "import check_village; print(len(check_village.GATE_SEGMENTS))"` - row count
  ≥ 972 (splits add rows).
- `wc -l check_village/*.py` - only registry.py exceeds ~1,000 lines, and its header says why.
- `cat check_village/CLAUDE.md` - every file listed with a "look here when" line.
