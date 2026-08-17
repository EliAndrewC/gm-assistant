# Quickstart: the runbook for feature 118

Every command runs from `.claude/skills/diagram/` inside the session clone
(`/gm-assistant/.clones/diagram-architecture`), except where a step says otherwise.

    SCRATCH=/tmp/claude-1000/-gm-assistant/17b6cc0a-e82e-420c-b23a-d446bdfb4f3e/scratchpad

## 0. Confirm the oracle can actually SEE the new package (ONCE, before trusting any sweep)

`pipeline/regen.py`'s dependency walk must reach `settlement/rolling/*.py` the way it reached
`settlement/rolling.py`, or every key stays put, every map reports `CACHED`, and the sweep is green
having regenerated nothing. The walk has been depth-agnostic since feature 025 made `settlement/` a
package and has survived five splits since, so the expected answer is yes - but "expected" is what
this step exists to convert into "checked".

Cheapest proof: after the split, touch a numeric literal inside a member that a live map executes
(`_bundle_geom`'s `gap = self.px(3)` will do) and confirm the next `pipeline/regen.py` prints
`REGENERATED`, not `CACHED`. Then revert the literal.

## 1. Baseline - already taken, do not re-take without a detached worktree

    make done      # measured 2026-08-17 at 15fac91: exit 0, 3263 passed in 119.77s

If a re-baseline is ever needed mid-feature: `git worktree add --detach /tmp/base HEAD`. **Never a
stash** - a stash mutates the working tree under any review agent currently reading a pool file.

## 2. Capture the byte-identity baseline, in a SCRATCH COPY

The committed manifests are NOT a valid baseline: they were produced by whatever engine shipped
them, and the frozen ones deliberately predate rules the current engine has. Capture from a scratch
copy of the tree at the pre-change commit, so the baseline is what THIS code produces.

    rm -rf $SCRATCH/base && cp -a /gm-assistant/.clones/diagram-architecture/.claude/skills/diagram $SCRATCH/base
    cd $SCRATCH/base && python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py 2>&1 | tee $SCRATCH/118-baseline.log

`--frozen-ok` is REQUIRED. Without it the legacy maps print `FROZEN` and skip - and all three
`roll_village` callers (`honda`, `shimizu`, `kikuta`) are frozen, so the sweep would exercise this
feature's headline function not at all (research R5).

Record the hashes:

    cd $SCRATCH/base && find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) \
        | sort | xargs sha256sum > $SCRATCH/118-baseline.sha

## 3. Run the transformer, prune, delete the old file

    python3 ../../../specs/118-rolling-package/split_rolling.py
    python3 -m ruff check --select F401 --fix settlement/rolling/
    python3 -m ruff format settlement/rolling/
    git rm settlement/rolling.py

The transformer REFUSES rather than guesses: an unnamed class-body member, a member assigned to two
modules, or a partition that does not exactly cover the class each abort it with a message naming
the members involved.

**Then clear stale bytecode**: `find settlement -name __pycache__ -prune -exec rm -rf {} +`. A
`rolling.cpython-*.pyc` left from the deleted module can shadow the new package on some import
paths, and the resulting failure looks nothing like its cause.

## 4. Cheap linters BEFORE the gate

    python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy

`make done` stops at the first failing phase, so a format or type slip discovered there costs a full
gate cycle to find and another to confirm.

## 5. The byte-identity sweep

    rm -rf $SCRATCH/work && cp -a /gm-assistant/.clones/diagram-architecture/.claude/skills/diagram $SCRATCH/work
    cd $SCRATCH/work && python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py 2>&1 | tee $SCRATCH/118-work.log
    cd $SCRATCH/work && find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) \
        | sort | xargs sha256sum > $SCRATCH/118-work.sha
    diff <(sed "s|$SCRATCH/base|X|" $SCRATCH/118-baseline.sha) <(sed "s|$SCRATCH/work|X|" $SCRATCH/118-work.sha) && echo IDENTICAL

**Read the LOG, not only the diff.** This is the trap 116 recorded and it is worth repeating: the
sweep is only meaningful if it actually WROTE every artifact. `regen` fans out across processes, and
if it dies early - OOM is the realistic cause - the unwritten files in the scratch copy are still the
COPIED ones, which hash equal to a baseline that faithfully reproduced those same bytes. `diff`
prints nothing and the oracle reports success having tested nothing at all. So confirm the log shows
a line per generator and a nonzero regenerate count before believing `IDENTICAL`.

For the same reason: **do not run the sweep beside an `-n auto` pytest or a `make done`**, and sweep
in the SCRATCH copy, never in the clone - the frozen pool's committed bytes must be left exactly as
found.

## 6. Prove nothing was lost

**6a. The composed surface.** `pytest tests/settlement/test_rolling.py -q`. Then prove the guard
RED before trusting it, per contracts/mixin-surface.md: delete a member name from one module's
tuple in the transformer, re-run into a scratch tree, confirm the test names it; then restore.

**6b. Comment lines: zero lost.** A verbatim move that drops a researched why-comment is not
verbatim, and this file's comments carry the bundle-pitch post-mortem, the windbreak correction and
the threshing-yard sun research.

    git show HEAD:.claude/skills/diagram/settlement/rolling.py | grep -c '^\s*#'
    grep -ch '^\s*#' settlement/rolling/*.py | paste -sd+ | bc

The two numbers must be equal. (Docstrings are not counted by either side, so they are covered by
the byte-identity of the members themselves.)

**6c. Nothing outside the package changed.**

    git diff --stat HEAD

`settlement/core.py` must not appear. No pool generator, test, tool or check may appear.

## 7. The gate, backgrounded and NOT polled

    make done > $SCRATCH/118-gate.log 2>&1

Nothing appended to that command - a trailing `; echo EXIT=$?` makes a FAILED gate notify as exit 0.
Act on the completion notification; tail the log before believing green.

## 8. Then, and only then, the decomposition (second commit)

Repeat steps 4, 5, 6c and 7 for the `roll_village` stage split. Step 5 is the one that matters here:
it is the only thing standing between a plausible-looking stage boundary and a silently re-rolled
map. Step 6b applies again - `roll_village` is where the heaviest comment banks are.

Additionally, after the decomposition:

    python3 - <<'PY'
    import ast, pathlib
    for p in sorted(pathlib.Path("settlement/rolling").glob("*.py")):
        t = ast.parse(p.read_text())
        for c in t.body:
            for f in getattr(c, "body", []) if isinstance(c, ast.ClassDef) else []:
                if isinstance(f, ast.FunctionDef):
                    n = f.end_lineno - f.lineno + 1
                    if n > 150:
                        print(f"OVER BAR: {p.name}::{f.name} = {n} raw lines")
    print("checked")
    PY

Must print only `checked` (SC-002).

## 9. Stop-work ritual

Commit in the clone, then `scripts/sync-with-main.sh done` from inside it. **Not before** the gate
is green AND the sweep says IDENTICAL - a byte that moved is a regression under Principle XIII, and
its three exits are fix, revert, or an explicit GM waiver. There is no fourth.

## What this feature does NOT need

- **No `settlement-review` pass.** It renders no new map and changes no map's bytes; a judgment
  pass adds nothing to a byte comparison (research R5, same reasoning the `SeatMemo` change
  recorded).
- **No `tools.cache_audit` run.** That audit exists for changes to the cache or to how generation
  is DRIVEN. This changes neither - though step 0 is the piece of its reasoning that does apply.
- **No pool regeneration in the clone.** The sweep runs in scratch copies; render-sync regenerates
  main's renders from main's own tip.
