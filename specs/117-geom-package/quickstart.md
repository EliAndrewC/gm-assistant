# Quickstart: running feature 117

Every command runs from `.claude/skills/diagram/` inside the session clone unless stated otherwise.
Steps 1 and 2 are already done and their results are recorded here.

## 1. Baseline (DONE - 2026-08-17, before any code was written)

Principle XIII requires a measured baseline taken on unmodified code in a **detached worktree**,
never a stash - a stash mutates the tree under any review agent reading it.

```bash
git worktree add --detach /tmp/base117 HEAD
cd /tmp/base117/.claude/skills/diagram
python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py > /tmp/117-baseline-sweep.log 2>&1
find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort \
  | xargs sha256sum > /tmp/117-baseline-hashes.txt
```

**Result**: exit 0, `REGENERATED 28`, `893` artifacts hashed. This is the oracle for step 6.

## 2. The cache-audit target measurement (DONE)

Coverage over `inashiro` + `sawada` mapped onto the planned modules, counting the literals
`tools/cache_audit.numeric_sites` would consider. Table and reasoning in `research.md` R7; the answer
is `curves.py` (35 candidates, 9 executed, all of them geometry-moving).

## 3. Run the transformer

```bash
python3 ../../../specs/117-geom-package/split_geom.py
python3 -m ruff check --select F401 --fix settlement/_geom/
python3 -m ruff format settlement/_geom/
git rm -q settlement/_geom.py        # FR-006: never leave a module beside a package of the same name
```

The transformer REFUSES (non-zero exit, naming names) if the partition does not exactly cover the
module, if a member is assigned twice, or if an unnamed statement has no preceding member. A refusal
is the design working - fix the partition table in the script, do not work around it.

## 4. Cheap linters BEFORE the gate

```bash
python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy
```

`mypy --strict` is doing real work here, not ceremony: it is what catches a name used in an
ANNOTATION that no submodule imports, which Python 3.14's deferred annotations would otherwise hide
until runtime (research R6).

## 5. The surface guard, red first

Add C1-C3 from `contracts/surface.md` to `tests/settlement/test_geom.py`, then prove each half bites
before trusting it:

```bash
# C1: delete a member from a submodule, expect the census to name it
python3 -m pytest tests/settlement/test_geom.py -q -k surface
# C2: bind `seg_dist` in a second submodule, expect the collision half to fire
python3 -m pytest tests/settlement/test_geom.py -q -k surface
```

Record the observed failure text in `tasks.md`. Restore the sabotage after each.

## 6. The byte-identity oracle

Run the post-split sweep in a SCRATCH COPY, never in the clone - the clone's committed `pool/`
artifacts must stay clean (the frozen renders are tracked in git).

```bash
rm -rf /tmp/post117 && cp -a /gm-assistant/.clones/diagram-tokens/.claude/skills/diagram /tmp/post117
cd /tmp/post117
python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py > /tmp/117-post-sweep.log 2>&1
find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) | sort \
  | xargs sha256sum > /tmp/117-post-hashes.txt
diff /tmp/117-baseline-hashes.txt /tmp/117-post-hashes.txt && echo "BYTE-IDENTICAL"
```

Anything but an empty diff is a refactor bug. Do NOT compare against the COMMITTED manifests instead:
the engine may have drifted since they were committed, so a mismatch there is indistinguishable from
a bug this feature introduced (feature 110 research R3).

## 7. The comment-line count

```bash
git show HEAD:.claude/skills/diagram/settlement/_geom.py | grep -c '^\s*#'
cat settlement/_geom/*.py | grep -c '^\s*#'
```

The second must be >= the first (each new module's own header adds a few). Zero lost is the bar;
the four re-pointed sentences in `research.md` R5 are edits, not losses, and the moved doctrine bank
is a move.

## 8. The gate, backgrounded and NOT polled

```bash
cd /gm-assistant/.clones/diagram-tokens/.claude/skills/diagram && make done > /tmp/117-gate.log 2>&1
```

Nothing after the redirect - a trailing `; echo EXIT=$?` makes a FAILED gate notify as exit 0. Act on
the completion notification; tail the log before believing green.

## 9. The cache audit

```bash
python3 -m tools.cache_audit --trials 3        # ~10 min; verifies the new TARGET has teeth
```

Read the per-trial `moved N artifacts` figure as well as the verdict: a trial that moved nothing
proved nothing about the cache, and a run where every trial moved nothing means the target is wrong.

## Traps, from the lineage

- **Do not run a pytest beside the running gate** - both regenerate the same live maps in the same
  tree, and a test that reads a manifest another writer is mid-write fails a gate that is otherwise
  clean (2026-08-16, feature 116, cost one gate cycle).
- **The gencache key moves for every map** the moment module-level source changes, so the first
  post-split sweep is a full cold regen. That is expected, not a cache bug.
- **A miss REBUILDS the entry against whatever the sources say at that moment**, so if you revert an
  edit and re-run, the next run is a legitimate miss. Re-establish `CACHED` before testing any cache
  question.
- **Leave `pool/` clean**: check `git status --short pool` before the stop-work ritual. If a stray
  local run dirtied it, restore the bytes (`git checkout -- pool`) rather than re-running a generator.
