# Quickstart: verifying feature 127 by hand

Every check below is also an automated test. This is the by-hand version for a reader who wants to
see the guards work, and the acceptance walk-through for the feature.

## 1. The guards FIRE (FR-015)

```
python3 -m l7r.diagram.tools.cohort_audit --count 48   # expect: refused, names `make maps`
python3 -m pytest                                      # expect: refused, names `make test`
make -f /tmp/anything.mk somegoal                       # expect: refused before running
python3 -c "from l7r.diagram.hamletgen import generate; generate(...)"   # expect: refused
```

Each refusal must name the make target that does the same job (FR-006). If a refusal does not tell
you what to run instead, that is a bug: the whole point is that the correct route is one line away.

## 2. The cheap path is unobstructed (FR-016, SC-002)

```
make reference        # expect: CLEAN, ~60 s, NO prompt, NO override
make why-placed ...   # a read-only diagnostic: runs immediately, no prompt
```

If either prompts, the feature has failed in the direction that matters most - a prompt on correct
work is what teaches a session that the override is routine.

## 3. The prompt defaults to CANCEL (FR-010, FR-011)

```
make done FULL=1              # expect: explanation, then a prompt; pressing Enter CANCELS
echo | make done FULL=1       # expect: cancelled, nothing expensive ran
make done FULL=1 REF_WHY=x    # non-interactive: expect REFUSED, not silently accepted
```

## 4. The audit log records all three outcomes (FR-012)

```
tail -3 .claude/skills/diagram/dev/bypass-log.jsonl
```

Expect `permitted`, `cancelled` and `refused` to be distinguishable. A log with only `permitted`
entries cannot answer how often the expensive path was reached for.

## 5. The guard files are protected (FR-013)

Attempt an edit to `Makefile`, to any `scripts/*-hooks.sh`, and to `.claude/settings.json`; each is
intercepted and asks for a reason. Attempt an edit to `.claude/agents/frontend-review.md`; it is NOT
intercepted, deliberately - that path is how review subagents get improved.

## 6. Removing a guard turns the gate red (SC-003)

In a scratch copy, delete each guard in turn and run the tests. Each removal must produce at least one
failure naming that guard. **A guard whose test still passes when the guard is gone is not
implemented** - it is decoration, and this is the check that says so.

## 7. The stop-work ritual still works (SC-004)

```
scripts/sync-with-main.sh done
```

Expect render-sync to complete, invoking its make target rather than a bare interpreter call, with no
refusal and no prompt.
