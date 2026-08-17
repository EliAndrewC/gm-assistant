# Quickstart: the runbook for feature 120

Every command runs from `.claude/skills/diagram/` inside the session clone
(`/gm-assistant/.clones/diagram-architecture`) unless a step says otherwise.

    SCRATCH=/tmp/claude-1000/-gm-assistant/2f74207d-6962-4710-b92e-aa3596608fd6/scratchpad

## 0. Baseline, BEFORE any edit - and know which tree runs what

Two halves, and they run in DIFFERENT trees. Getting that wrong cost one cycle here (research.md
R8): a bare copy of `.claude/skills/diagram/` cannot run `make done`, because the Makefile's lint
phase shells out to `../../../scripts/check-duplicate-defs.py`, which only resolves when the skill
dir sits inside the repo. The first attempt duly reported `GATE FAILED: lint` with every other phase
green - a pure artifact of the copy.

**The gate baseline runs in the CLONE** (clean tree, before any edit):

    make done > $SCRATCH/120-baseline-gate.log 2>&1
    # measured 2026-08-17 at 56f6dfb: gate green, coverage TOTAL 95%

**The byte-identity baseline runs in a SCRATCH COPY**:

    rm -rf $SCRATCH/base && cp -a <clone>/.claude/skills/diagram $SCRATCH/base
    cd $SCRATCH/base && python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py \
        > $SCRATCH/120-baseline-sweep.log 2>&1
    cd $SCRATCH/base && find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) \
        | sort | xargs sha256sum | sed "s|  .*/base/|  |" > $SCRATCH/120-baseline.sha
    # measured: REGENERATED 28, CACHED 0, 893 artifacts hashed

`--frozen-ok` is REQUIRED. Without it the 19 frozen legacy maps print `FROZEN` and skip - and they
are exactly the maps that exercise `perimeter_dike`, `dike_top_houses` and `near_ring_paddy`, which
the scripted hamlet cohort barely touches. Skipping them would leave this feature's headline members
unverified.

**Re-take the baseline if main moves under you.** A baseline belongs to one commit. This feature's
first baseline was invalidated by a peer session's `waterfields/frame.py` push arriving on sync-in.

## 1. Transform

    python3 ../../../specs/120-land-package/split_land.py \
      && python3 -m ruff check --select F401 --fix settlement/land/ \
      && python3 -m ruff format settlement/land/ settlement/homestead_parts.py \
      && git rm -q settlement/land.py \
      && find settlement -name __pycache__ -prune -exec rm -rf {} +

The transformer REFUSES rather than guesses: a partition that does not exactly cover the class, a
member assigned twice, an unnamed class-body member, a module-level tail without
`surface_water_dist`, a `HomesteadPartsMixin` that does not run to EOF, or a REPOINT that did not
fire exactly once. A refusal is the design working - fix the partition table in the script, do not
work around it.

**Clear the bytecode** (the `find` above): a `land.cpython-*.pyc` left from the deleted module can
shadow the new package on some import paths, and the resulting failure looks nothing like its cause
(feature 118).

## 2. Cheap linters BEFORE the gate

    python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy

`make done` stops at the first failing phase, so a format or type slip discovered there costs a full
gate cycle to find and another to confirm. `mypy --strict` is doing real work here, not ceremony: it
is what catches a name used only in an ANNOTATION that no submodule imports, which deferred
annotations would otherwise hide until runtime (feature 117 R6). The live instance is
`_farmstead_nudges` returning `Iterator` as it crosses into `homestead_parts.py`; the transformer
adds that import itself.

Expected after the split: **118** source files for mypy, up from 114.

## 3. Comment conservation

    git show HEAD:.claude/skills/diagram/settlement/land.py | grep -c '^[[:space:]]*#'
    cat settlement/land/*.py | grep -c '^[[:space:]]*#'

Measured: **158 and 158**, with a delta of 0 in `homestead_parts.py`. Conserved exactly. A "pure
move" that drops a why-comment is not pure, and comments are the one thing no downstream test can
notice.

## 4. The surface guards, red first

Add C1-C4 from [contracts/surface.md](contracts/surface.md) to `tests/settlement/test_land.py`, then
prove each half bites before trusting it. Restore after each sabotage:

    rm -rf /tmp/land_backup && cp -a settlement/land /tmp/land_backup
    # A: delete "    NearRingMixin,\n" from land/__init__.py's bases   -> C1 fails
    # B: append a second `toe_band` to GroundCoverMixin in cover.py    -> C2 fails
    # C: append an `_attach_grove` stub to cover.py                    -> C3 fails
    # D: delete the surface_water_dist re-export from land/__init__.py -> C4 fails collection
    python3 -m pytest tests/settlement/test_land.py -q --no-cov -k "<the guard>"

All four observed failing on 2026-08-17, each naming the right thing. A guard that has never been
seen to fire is not a guard.

## 5. Whole affected test files, then the byte-identity oracle

    python3 -m pytest tests/settlement/ tests/hamletgen/ tests/check_village/ -q -n auto --no-cov
    # measured: 2070 passed in 64.62s

Run the WHOLE files, never a `-k` subset - and note that `scripts/gate-hooks.sh` enforces this and
CANNOT see a whole-file run buried later in the same `&&` chain as `make done`. Run them as their
own command.

    rm -rf $SCRATCH/work && cp -a <clone>/.claude/skills/diagram $SCRATCH/work
    cd $SCRATCH/work && python3 -m pipeline.regen --no-cache --frozen-ok pool/*/*.gen.py \
        > $SCRATCH/120-work-sweep.log 2>&1
    cd $SCRATCH/work && find pool -type f \( -name '*.json' -o -name '*.svg' -o -name '*.png' \) \
        | sort | xargs sha256sum | sed "s|  .*/work/|  |" > $SCRATCH/120-work.sha
    diff $SCRATCH/120-baseline.sha $SCRATCH/120-work.sha && echo BYTE-IDENTICAL

**Read the LOG, not only the diff.** This is the trap feature 116 recorded and it is worth repeating:
the sweep is only meaningful if it actually WROTE every artifact. `regen` fans out across processes,
and if it dies early - OOM is the realistic cause - the unwritten files in the scratch copy are still
the COPIED ones, which hash equal to a baseline that faithfully reproduced those same bytes. `diff`
prints nothing and the oracle reports success having tested nothing at all. Confirm a nonzero
regenerate count first. Measured: **REGENERATED 28, CACHED 0, 893 = 893, empty diff**.

## 6. The gate, backgrounded and NOT polled

    cd <clone>/.claude/skills/diagram && make done > $SCRATCH/120-gate.log 2>&1

Nothing after the redirect - a trailing `; echo EXIT=$?` makes a FAILED gate notify as exit 0. Act on
the completion notification; tail the log before believing green.

## 7. Confirm the cache actually SEES the new package

Cheap, and it converts an expectation into a check. The dependency walk in `pipeline/regen.py` must
reach `settlement/land/*.py` the way it reached `settlement/land.py`, or a future edit leaves every
map `CACHED` and a green sweep proves nothing.

    python3 -m pipeline.regen pool/hamlets/inashiro.gen.py        # settle to CACHED first
    # touch a numeric literal inside a land/ member that map executes, then:
    python3 -m pipeline.regen pool/hamlets/inashiro.gen.py        # must print REGENERATED
    # revert the literal

**Re-establish `CACHED` before each trial.** A miss REBUILDS the entry against whatever the sources
say at that moment, so reverting an edit legitimately produces the next miss - test the wrong way
round and you conclude the cache is broken when it is working perfectly.

## 8. Leave `pool/` clean

    git status --short pool

The frozen exhibits' renders are TRACKED. If a stray local run dirtied them, restore the bytes
(`git checkout -- pool`) rather than re-running a generator - the engine may have drifted since they
were committed.

## Traps from the lineage, collected

- **Do not run a pytest beside the running gate.** Both regenerate the same live maps in the same
  tree, and a test that reads a manifest another writer is mid-write fails a gate that is otherwise
  clean (feature 116, one gate cycle).
- **The gencache key moves for every map** the moment module-level source changes, so the first
  post-split sweep is a full cold regen. Expected, not a cache bug.
- **Take a baseline in a detached worktree or a scratch copy, never by stashing** - a stash mutates
  the working tree under any review agent currently reading a pool file.
