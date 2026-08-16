# Quickstart: Human-Scale Splits (025)

All commands run from the session clone's skill dir:
`/gm-assistant/.clones/diagram-architecture/.claude/skills/diagram` (the Makefile guard refuses
main's tree).

## The gate (after every story)

```sh
make done          # lint + format-check + mypy --strict + pytest + coverage (100% / settlement ratchet 94)
```

Docs-only US1 skips the gate (docs-only rule) - its verification is grepping the three amended
sites:

```sh
grep -n "test" ../../../.specify/memory/constitution.md | grep -i "clause 13\|human scale"   # amended clause
grep -n "tests included\|test files" ../../../CLAUDE.md ../../../.specify/templates/plan-template.md
```

## Identity proofs

Capture BEFORE the story's split lands, compare AFTER (tooling lives in
`specs/025-human-scale-splits/`, adapted from 022/024):

```sh
# US2 / US4 - collection identity
python3 -m pytest --collect-only -q | sort > /tmp/collect_pre.txt     # before
python3 -m pytest --collect-only -q | sort > /tmp/collect_post.txt    # after
# compare on the ::-suffix (file paths change by design, node names must not)

# US3 - generation identity (regen-runnable gens + fixed-seed hamletgen cohort)
python3 ../../..../specs/025-human-scale-splits/oracle_gen.py capture   # pre
python3 ..../oracle_gen.py compare                                       # post: byte-equal svg/json

# US3 - gate identity over all pool manifests + regression fixtures
python3 ..../oracle_gate.py capture && python3 ..../oracle_gate.py compare
```

(Exact script names/paths are settled by tasks.md; the `....` is the specs dir.)

## Where things land

- `settlement/` - the package (index: `settlement/CLAUDE.md`)
- `test_checks/`, `test_settlement/` - test packages (each with its own CLAUDE.md + `_builders.py`)
- Proof artifacts - `specs/025-human-scale-splits/oracle_*.json`, `collect_*.txt`
