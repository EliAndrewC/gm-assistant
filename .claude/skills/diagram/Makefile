# The diagram-skill quality gate (Constitution Principle X). Run `make done` before declaring
# any Python change complete. Runs, in order: lint, format-check, type-check, tests+100% coverage.
#
# mypy uses a per-module ratchet (see pyproject.toml): the legacy engine modules are relaxed until
# each is migrated to --strict in its own pass; new modules are strict immediately.

.PHONY: done lint format typecheck test test-full guard perf perf-report maps reference bypass-audit quick durations test-file audit perf-gate hooks-test explain \
	 map cohort tripwire hamlet cache-audit regressions placement-stages pool-index compound render-sync \
	 gate-manifest why-placed site-justice crop jogs pack-audit scatter-audit timings citybudget help

# Runs EVERY phase and reports all failures together (GM 2026-07-25). It used to be
# `done: lint format typecheck test`, which make stops at the first failure - so a lint slip hid a
# type error hid a coverage hole, and each hidden failure cost another full round trip to discover.
# Phases stay in cheap-to-expensive order so the fast ones report first, but none of them short-
# circuits the rest. Exit is non-zero if any phase failed, so this is exactly as strict as before.
# ---- ONE COMMAND, AND IT IS THE CHEAP ONE BY DEFAULT (GM 2026-08-24) -------------------------
#
# `make done` runs the REFERENCE settlement and everything that does not roll another map. That is
# the gate for the normal case, and it is what a reference-only push is verified with.
#
# `make done FULL=1` additionally rolls every live pool map, re-gates each, and runs the seeds 41-44
# ratchet - and it will not do so silently: it PROMPTS for a written justification and appends it to
# dev/bypass-log.jsonl with the date, target and commit. There is no second command to reach for.
#
# WHY THERE IS ONLY ONE (GM 2026-08-24): *"I don't know if I like the idea of there being both a
# make done and a make done reference because that just gives you a way to run the wrong version."*
# That is not hypothetical - during feature 126 three separate guards were added and each was walked
# around by using a command the guard did not cover: `cohort_audit` while `make maps` was gated, then
# `make done` and `make test` while both of those were. A choice between a fast path and a slow path
# is a choice that gets made wrong under pressure, so the choice is gone.
#
# The constitution requires every diagram feature to AUDIT dev/bypass-log.jsonl as a closing step -
# read the entries added during the feature and say, in writing, whether each was justified.
done:
	@$(if $(FULL),$(MAKE) --no-print-directory bypass-audit REF_WHY="$(REF_WHY)",$(MAKE) --no-print-directory reference)
	@T0=$$(date +%s); fail=""; \
	for phase in lint format typecheck hooks-test $(if $(FULL),test-full perf-gate,test); do \
	  printf '\n\033[1m== %s ==\033[0m\n' "$$phase"; \
	  $(MAKE) --no-print-directory $$phase || fail="$$fail $$phase"; \
	done; \
	if [ -n "$$fail" ]; then $(LOGRUN) done "$(if $(FULL),full,reference)" "$$(( $$(date +%s) - $$T0 ))" "failed:$$fail"; printf '\n\033[1mGATE FAILED:%s\033[0m (every phase ran - fix them together, then re-run once)\n' "$$fail"; exit 1; fi; \
	root=$$(git rev-parse --show-toplevel 2>/dev/null) && [ -n "$$root" ] && python3 "$$root/scripts/gate-stamp.py" --write diagram || true; \
	$(LOGRUN) done "$(if $(FULL),full,reference)" "$$(( $$(date +%s) - $$T0 ))" green; \
	$(if $(FULL),printf '\n\033[1mgate green (FULL - every pool map re-gated, seeds 41-44 rolled)\033[0m\n',printf '\n\033[1mgate green\033[0m (reference settlement + non-map tests; `make done FULL=1` also rolls the other pool maps)\n')

# THE REFERENCE-HAMLET PERFORMANCE BOOKENDS (constitution VI, GM 2026-08-23).
#
# Deliberately NOT part of `done`. A hamlet takes 30-160s and the reference set is four seeds, so
# folding this into the gate would roughly double a cycle that already runs ~5 minutes - and this
# project's own measurements say iteration latency is the dominant cost of a feature. So the sweep
# is explicit and the CONSTITUTION carries the obligation to run it, at the start of a diagram
# feature and again before it ships.
# ---- ONE COMMAND, WHICH PICKS ITS OWN SCOPE (constitution VI) --------------------------------
#
# `make maps` reads how the LAST run went and decides:
#
#     last run PASSED -> the whole tier, reporting every failure together
#     last run FAILED -> the REFERENCE map alone, stopping at the first problem;
#                        only if it passes does it go on to the rest
#     no last run     -> treated as FAILED
#
# There is deliberately no second command. The rule this replaces ("prove it on the reference
# settlement first, then sweep") was correct, was written into the constitution, and was violated by
# its own author six hours later - five 10-12 minute four-map cycles chasing a defect the reference
# hamlet answered in 67 seconds. A choice is a thing that gets chosen wrong under pressure.
#
# `SCOPE=reference` / `SCOPE=all` says what you mean when you know better.
# ---- THE REFERENCE SETTLEMENT GATES EVERYTHING EXPENSIVE (constitution VI) -------------------
#
# `make reference` rolls ONE seed of ONE map - Inashiro - and nothing else. It is the cheapest
# question in the project (~60 s) and every expensive target now asks it FIRST:
#
#     make test   -> reference, then the suite
#     make done   -> reference, then lint/format/typecheck/test/coverage
#     make maps   -> reference, then (only if clean) the rest of the tier
#
# If the reference settlement is red, those targets STOP THERE. Not a warning, not a slow path -
# they refuse to run the expensive work at all.
#
# WHY (GM 2026-08-24): "our goal here is to start small, get something working, and then expand on
# it ... the very fact that you are capable of running more than that means that our tooling is
# supporting more expensive testing than what I have explicitly said should be permitted."
#
# The measured cost of not having this, in ONE feature: six 20-25 minute cohorts, most launched over
# a tree already known to be broken, plus repeated four-map ratchet runs to diagnose a single failing
# seed. The rule existed in the constitution the whole time and was violated by its own author within
# hours, twice. A guard that lives only in documentation is not a guard, and a guard on one command
# out of four is not a guard either.
#
# ESCAPE HATCH: REF_OK=1 on the command line, for the case where the reference map is legitimately
# expected to fail (you are mid-surgery on it, or bisecting). Deliberately awkward, and it says so.
# ---- BYPASSING THE REFERENCE GATE COSTS A WRITTEN JUSTIFICATION ------------------------------
#
# REF_OK=1 does not simply let the expensive targets run. It demands WHY, in prose, and appends it
# to dev/bypass-log.jsonl with the date, the target and the git HEAD - so a later reader can ask
# whether the reason was any good. That log is the point: a flag you can type is a speed bump, a
# reason someone will READ is a decision you have to defend.
#
# WHY THIS EXISTS (GM 2026-08-24): *"how often I keep saying over and over again to just run the
# quick tests, and then you keep finding ways to run the long tests ... we need to make it either
# literally impossible or so obvious that you should not be doing it that you simply won't."*
# Measured, in one feature: six 20-25 minute cohorts, most over a tree already known to be broken,
# plus repeated four-map ratchet runs to diagnose one seed. Three separate guards were added during
# that feature and each was walked around by using a command the guard did not cover.
#
# LEGITIMATE reasons look like: the reference map is the thing under surgery and is expected to
# fail; you are bisecting and need the suite's verdict on a knowingly-red tree; a check that only
# fires on a non-reference map is the subject. "I want to see everything" is not one.
#
# REF_WHY="..." supplies the reason without the prompt - but ONLY with a terminal attached. A
# non-interactive FULL run with REF_WHY set is REFUSED outright (see bypass-audit), because that
# combination is precisely how feature 126 ran the full gate three times against a standing
# instruction to run only the reference settlement: the prompt defaults to NO, and a backgrounded
# run cannot be asked to reconsider. Every one of those bypasses was logged, and none was stopped -
# which is the whole lesson. An audit trail records a decision; it does not make one.
# ---- THE MIDDLE TIER, AND THE ONE THAT STOPS AT THE FIRST FAILURE ---------------------------
#
# MEASURED 2026-08-24: `quick` is ~4 MINUTES, not "seconds" as this comment and the hook's
# refusal text both claimed. The label was written from intent rather than a stopwatch. It is
# still the right target for an iteration loop - it stops at the first failure - but it is not
# cheap, and a tip that misstates a cost teaches a session to distrust the tips.
#
# `make quick` is what an iteration loop uses once the reference map is clean: lint, types, and
# every test that does NOT roll a map, with pytest's `-x` so it STOPS at the first failure. Seconds,
# not minutes, and it answers "is what I just wrote coherent" rather than "is this safe to ship".
#
# The full suite rolls a dozen-plus maps (test_village_passes_gate regenerates and re-gates every
# live pool map; the ratchet rolls seeds 41-44), which is right for a pre-push gate and wrong for a
# loop. Measured on feature 126: `make done` is ~5 minutes and I ran it repeatedly over a tree I
# already knew was broken.
# QUICK ROLLS NO MAPS AT ALL, and that is the whole contract. It used to run `make reference` first
# (~26 s of map generation) which contradicted its own promise and, with the marker fix below, was
# most of what remained of its cost. FR-014's reference-first ordering binds EXPENSIVE targets - the
# ones that would waste minutes on a tree the 60-second check would have condemned. `quick` rolls
# nothing, so there is nothing for a broken reference map to waste; run `make reference` when you
# want the map checked, which is a separate question from "did I break the code".
#
# MEASURED 2026-08-24: 254 s -> 94 s (marker deselect) -> this. The 254 s version was being pointed
# at by every guard in this feature as the cheap option.
# QUICK ENFORCES ITS OWN BUDGET, because the whole point of this feature is that the target the
# guards point at is actually fast. It was 254 s while every blocked command was being sent to it as
# the cheap option, and nothing said so - a target gets slower one unmarked test at a time and no
# check exists for "this is still quick" unless you write one.
#
# TIMED WITH `date +%s`, NOT `$$SECONDS`: make's default shell is sh, where SECONDS is unset, so the
# first version computed an empty elapsed time and never fired - it passed a 1-second budget on a
# 31-second run. Caught by testing the guard rather than trusting it, which is the same check that
# T034 applies to every other guard in this feature.
#
# 60 s against a measured ~33 s leaves room for a slower machine and for the suite to grow, and still
# fires long before anyone would call it slow. RAISE IT ONLY WITH A MEASUREMENT, and prefer marking
# the slow test instead: the budget is the alarm, not the fix.
# ============================================================================================
# OPERATIONS - every runnable unit of this project's work has a target (FR-001)
#
# "We want make commands for everything" (GM 2026-08-24). Not decoration: `scripts/make-only-hooks.sh`
# refuses a bare interpreter and NAMES the target instead, so an operation without one is an operation
# a session cannot legitimately run. That gap was real - gating bare pytest left "why is this slow"
# with no route but the override, which is precisely how an override becomes routine.
#
# EXPENSIVE targets check the reference settlement FIRST and stop if it fails (FR-014): spending
# minutes on a tree the 26-second check would have condemned is the waste this whole feature is about.
# CHEAP ones (read a recorded artifact rather than produce one) run immediately - prompting there
# would push a session toward regenerating a map, which is the opposite of the point.
#
# REF_OK=1 skips the reference check, and demands a logged reason like every other bypass here.
# ============================================================================================

REF_FIRST = @$(if $(REF_OK),$(MAKE) --no-print-directory bypass-audit REF_WHY="$(REF_WHY)",$(MAKE) --no-print-directory reference)
RUN = @python3 -m l7r.diagram

# --- expensive: they generate ---------------------------------------------------------------
map:            ## regenerate ONE gen and gate it            GEN=pool/hamlets/inashiro.gen.py
	$(REF_FIRST)
	$(RUN).pipeline.regen $(or $(GEN),pool/hamlets/inashiro.gen.py)

cohort:         ## roll N seeds and report every failure      N=48
	$(REF_FIRST)
	$(RUN).tools.cohort_audit --count $(or $(N),48)

tripwire:       ## the middle tier: reference map, then the tripwire seeds
	$(RUN).tools.mapcheck $(if $(SCOPE),--scope $(SCOPE),)

hamlet:         ## generate one hamlet from the CLI           ARGS="--name X --seed 4 ..."
	$(REF_FIRST)
	$(RUN).hamletgen $(ARGS)

cache-audit:    ## does using the generation cache change any map?
	$(REF_FIRST)
	$(RUN).tools.cache_audit $(ARGS)

regressions:    ## rebuild the frozen negative-fixture corpus
	$(REF_FIRST)
	$(RUN).tools.make_regressions $(ARGS)

placement-stages: ## re-plate the stage-by-stage walk-through page
	$(REF_FIRST)
	$(RUN).tools.placement_stages $(ARGS)

pool-index:     ## rebuild the pool index
	$(RUN).pipeline.pool_index $(ARGS)

compound:       ## draw a Mode A compound plan                ARGS=<out.svg>
	$(RUN).compound $(ARGS)

# RENDER-SYNC IS REFUSAL-ONLY AND NOT SUBJECT TO REFERENCE-FIRST (FR-009a, adjudicated at spec round
# 3). It runs in MAIN's tree during the stop-work ritual, and CLAUDE.md is explicit that render-sync
# is the ONLY thing a session runs there - "no generators, no tests". A reference check ahead of it
# would be a second generator run in main, which that rule forbids. It also re-renders from main's
# committed tip, which is already gate-verified, so the check would re-prove what the clone proved.
render-sync:    ## regenerate MAIN's renders (called by sync-with-main.sh; not for hand use)
	$(RUN).pipeline.render_cache $(ARGS)

# --- cheap: they READ a recorded artifact ----------------------------------------------------
gate-manifest:  ## run the check battery on an existing manifest   M=pool/hamlets/inashiro.json
	$(RUN).check_village $(or $(M),pool/hamlets/inashiro.json) $(ARGS)

why-placed:     ## who placed this, and what refused to        GEN=... AT=x,y | REFUSED=x,y
	$(RUN).tools.why_placed $(GEN) $(if $(AT),--at $(AT),)$(if $(REFUSED),--refused $(REFUSED),)

site-justice:   ## where can this feature legally go?
	$(RUN).tools.site_justice $(ARGS)

crop:           ## crop a rendered map in manifest coordinates
	$(RUN).tools.crop_map $(ARGS)

jogs:           ## find bunds that step sideways
	$(RUN).tools.jogs $(ARGS)

pack-audit:     ## empty space and geometry in a Mode A compound SVG
	$(RUN).tools.pack_audit $(ARGS)

scatter-audit:  ## is drawn ground cover standing where keep-outs should have stopped it?
	$(RUN).tools.scatter_audit $(ARGS)

timings:        ## where the generation loop's time goes
	$(RUN).tools.timings $(ARGS)

citybudget:     ## the city/capital space-budget planner
	$(RUN).citybudget $(ARGS)

# BOTH BOOKENDS ARE ENFORCED HERE, not requested (constitution VI, GM 2026-08-24: "are we now
# actually requiring at the tool level that -start was run at the beginning of a session and -end was
# run before shipping?"). Until today the answer was no, and the cost is on the record: feature 126
# took a `-start`, never took a `-end`, and shipped a +51% generation slowdown that nobody saw for a
# day. `perf-report` even printed "diagnose before shipping" - and exited 0.
#
# So this refuses to let a feature ship without its opening bookend, and takes the closing one
# itself. You cannot forget the second, and you cannot skip the first without the gate saying so.
#
# THE `-start` MAY BE TAKEN RETROACTIVELY, in a detached worktree at the pre-feature commit - that
# is the same tree the Principle XIII regression baseline uses, and it is measuring the same thing.
# What is NOT allowed is shipping with no baseline at all, because then "did this get slower" has no
# answer and the next session inherits the question.
# EVERY GUARD'S TEST COMPANION ACTUALLY RUNS (standing rule, GM 2026-08-24).
#
# The 2026-08-24 enforcement audit found EIGHT hook scripts, EIGHT test companions, and nothing that
# executed any of them. They were decoration by this project's own definition - the one T034 uses:
# a guard whose test does not fail when the guard is removed is not implemented, and a test nothing
# runs cannot fail at all.
#
# Cheap enough to sit in every `make done`: the whole set is seconds, because a hook test feeds JSON
# to a script and reads an exit code. Nothing here rolls a map.
hooks-test:     ## run every scripts/test-*-hooks.sh, and prove each guard still has a companion
	@root=$$(git rev-parse --show-toplevel); fail=""; n=0; \
	for h in $$root/scripts/*-hooks.sh $$root/scripts/review-gate.sh; do \
	  b=$$(basename $$h); case $$b in test-*) continue ;; esac; \
	  if [ ! -f "$$root/scripts/test-$$b" ]; then \
	    printf '\n\033[1mGUARD WITHOUT A TEST: %s has no scripts/test-%s\033[0m\n' "$$b" "$$b"; \
	    printf 'A guard ships with its companion. Without one, nothing can tell whether it still\n'; \
	    printf 'fires - or whether it fires on correct work, which is the more expensive failure.\n\n'; \
	    fail="$$fail $$b"; continue; \
	  fi; \
	  n=$$((n+1)); \
	  "$$root/scripts/test-$$b" >/tmp/ht.$$$$ 2>&1 || { printf '\n\033[1mHOOK TESTS FAILED: %s\033[0m\n' "$$b"; sed 's/^/  /' /tmp/ht.$$$$; fail="$$fail $$b"; }; \
	  rm -f /tmp/ht.$$$$; \
	done; \
	if [ -n "$$fail" ]; then printf '\n\033[1mhooks-test FAILED:%s\033[0m\n\n' "$$fail"; exit 1; fi; \
	printf 'hooks-test: %s guard suites green\n' "$$n"

perf-gate:      ## require the feature's -start bookend, take -end, and FAIL on a regression
	@f="$(or $(FEATURE),$(SPECIFY_FEATURE))"; \
	if [ -z "$$f" ] && [ -f ../../../.specify/feature.json ]; then \
	  f=$$(python3 -c "import json;print(json.load(open('../../../.specify/feature.json'))['feature_directory'].split('/')[-1])" 2>/dev/null); \
	fi; \
	n=$$(printf '%s' "$$f" | grep -oE '^[0-9]+' || true); \
	if [ -z "$$n" ]; then \
	  printf '\n\033[1mPERF GATE: cannot tell which feature this is.\033[0m\n'; \
	  printf 'Set SPECIFY_FEATURE=NNN-slug (spec-kit work) or FEATURE=NNN, so the bookends can be paired.\n\n'; \
	  exit 1; \
	fi; \
	if ! ls dev/perf-log/*"$$n"-start*.json >/dev/null 2>&1; then \
	  printf '\n\033[1mPERF GATE: no %s-start bookend exists, so a regression cannot be measured.\033[0m\n\n' "$$n"; \
	  printf 'Constitution VI wants it taken on UNMODIFIED code, before the first edit. Retroactively is\n'; \
	  printf 'fine and is what the regression baseline already does - take it in a detached worktree at\n'; \
	  printf 'the pre-feature commit:\n\n'; \
	  printf '  git worktree add --detach /tmp/base%s <pre-feature-commit>\n' "$$n"; \
	  printf '  ( cd /tmp/base%s/.claude/skills/diagram && make perf LABEL=%s-start )\n' "$$n" "$$n"; \
	  printf '  cp /tmp/base%s/.claude/skills/diagram/dev/perf-log/*%s-start*.json dev/perf-log/\n\n' "$$n" "$$n"; \
	  printf 'What is NOT allowed is shipping with no baseline: "did this get slower" then has no answer,\n'; \
	  printf 'and feature 126 shipped a +51%% slowdown exactly that way.\n\n'; \
	  exit 1; \
	fi; \
	$(MAKE) --no-print-directory perf LABEL="$$n-end" >/dev/null; \
	$(MAKE) --no-print-directory perf-report AGAINST="$$n-start"

audit:          ## how the gate has actually been used - every run, and every bypass
	@python3 -c "import json,glob,collections,os; \
rows=sorted((json.load(open(f)) for f in glob.glob('dev/run-log/*.json')),key=lambda r:r.get('utc','')); \
print(chr(10)+'\033[1mGate runs\033[0m (dev/run-log/)'); \
[print(f\"  {r['utc']}  {r['scope']:<9} {r['seconds']:>4}s  {r['result']:<22} {r['commit']}\") for r in rows[-25:]] or print('  (none yet)'); \
c=collections.Counter(r['scope'] for r in rows); \
print(f\"  {len(rows)} runs: \"+', '.join(f'{k}={v}' for k,v in sorted(c.items()))) if rows else None; \
b=sorted((json.load(open(f)) for f in glob.glob('dev/bypass-log/*.json')),key=lambda r:r.get('utc','')); \
print(chr(10)+'\033[1mBypasses\033[0m (dev/bypass-log/) - a FULL run is only justified at the END of a feature'); \
[print(f\"  {r['utc']}  {r.get('outcome','?'):<10} {r['why'][:76]}\") for r in b[-15:]] or print('  (none yet)'); \
print()"
	@printf '\033[1mFiles past the ~1,000-line bar\033[0m (constitution X clause 13 - a QUESTION, not a limit)\n'
	@find l7r tests -name '*.py' -exec wc -l {} + 2>/dev/null | awk '$$1>1000 && $$2!="total"{printf "  %5d  %s\n",$$1,$$2}' | sort -rn | head -12
	@printf '  Each asks: should this become a package of subfiles with its own CLAUDE.md index? An\n'
	@printf '  ordered-data REGISTRY may stay large with an inline justification - the only carve-out,\n'
	@printf '  and it protects rows stating real DECISIONS, never a roster derived from code elsewhere.\n'
	@printf '  Reported rather than gated on purpose: five files already exceed it and the rule prompts\n'
	@printf '  a question rather than forbidding a size.\n\n'

help:           ## list every target with its one-line purpose
	@printf '\n\033[1mOperations\033[0m - everything runs through one of these.\n\n'
	@grep -hE '^[a-z][a-z0-9-]*:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | sort | awk -F'\t' '{printf "  \033[1m%-18s\033[0m %s\n", $$1, $$2}'
	@printf '\nTimes: quick ~33s | reference ~26s | done ~5.5min (NOT the quick one) | done FULL=1 ~6min\n\n'


# THE LOG RECORDS WHAT HAPPENED, NOT ONLY WHAT WAS ALLOWED (FR-012). Without `outcome`, a session
# that read the warning and backed out is indistinguishable from one that never tried - so the log
# cannot answer the question it exists for. The GM's own use for it: a rising count of `cancelled`
# is the early signal that the cheap path has stopped being sufficient, at which point the answer is
# to make the fast path better rather than to keep refusing.
#
# The 2026-08-24 audit of the pre-guard entries found 3 of 5 unjustified, and the log had recorded
# all five and stopped none - an audit trail records a decision, it does not make one.
# NO LEADING `@`: that is a make RECIPE PREFIX, meaningful only at the start of a line. Expanded
# mid-recipe it is a literal character and the shell tries to run `@python3`, so the first version
# logged nothing at all while every other part of the prompt behaved correctly - a silent failure in
# the one component whose entire job is to leave a record.
# EVERY GATE RUN IS LOGGED, not only the bypassed ones (GM 2026-08-24): *"if there exists a make done
# that can be run in order to run the full tests, do we still have the ability to audit that it is
# only being run when we have fully completed a feature? ... not just confirming that in the moment,
# but also being able to audit after the fact."*
#
# The honest answer was no. `dev/bypass-log.jsonl` recorded FULL=1 attempts and nothing else, so
# there was no way to ask afterwards how often the 5-minute gate ran or whether each run was near a
# push. That matters here more than most places: the measured cost of getting this wrong, over three
# days, is hours - and the pattern that cost them was a session running the long gate repeatedly
# while believing each run was justified.
#
# `make audit` reads it back. Elapsed time is recorded too, so a target that has quietly got slower
# shows up in the history rather than in someone's memory.
LOGRUN = python3 -c "import json,os,subprocess,sys,time; \
  h=subprocess.run(['git','rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip(); \
  ts=time.strftime('%Y%m%dT%H%M%S',time.gmtime())+'%06d'%(time.time_ns()//1000%1000000); \
  os.makedirs('dev/run-log',exist_ok=True); \
  open(f'dev/run-log/{ts}-{os.getpid()}.json','w').write(json.dumps({'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'target':sys.argv[1],'scope':sys.argv[2],'seconds':int(sys.argv[3]),'result':sys.argv[4],'commit':h},indent=2)+chr(10))"

LOGBYPASS = python3 -c "import json,os,subprocess,sys,time; \
  h=subprocess.run(['git','rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip(); \
  ts=time.strftime('%Y%m%dT%H%M%S',time.gmtime())+'%06d'%(time.time_ns()//1000%1000000); \
  os.makedirs('dev/bypass-log',exist_ok=True); \
  open(f'dev/bypass-log/{ts}-{os.getpid()}.json','w').write(json.dumps({'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'target':'$(MAKECMDGOALS)','commit':h,'outcome':sys.argv[1],'why':sys.argv[2]},indent=2)+chr(10))"

QUICK_BUDGET = 60

# WHERE THE SUITE'S TIME GOES. Exists because the question could not be asked any other way once
# bare pytest was gated: a session needing to know why a target is slow had no route to the answer
# except the override, which is precisely the shape that trains a session to reach for overrides.
# A gate that blocks a legitimate question without providing the route is a gate that gets bypassed.
#
# N=<count> for a longer list; MARK=rolls_map to profile the map-rolling tests instead.
# ONE TEST FILE, WHOLE. Deliberately takes a FILE and not a `-k` expression: the project's own rule
# is to run the whole affected file, because a filter selects the tests you were thinking about and a
# change breaks the ones you were not (scripts/gate-hooks.sh enforces the same thing against the
# gate). Exists because gating bare pytest left "re-run the file I just changed" with no route, and a
# guard that blocks a legitimate action without offering the alternative is one that gets worked
# around - the same gap `make durations` filled for "why is this slow".
test-file:      ## run ONE test file, whole              FILE=tests/pipeline/test_gencache.py
	@python3 -m pytest -n auto -q --no-cov $(FILE)

# WHY EVERY CHECK FAILED ON THE REFERENCE MAP, in detail rather than by name.
#
# `make reference` prints the failing check NAMES, which is the right amount when you want a verdict.
# It is not enough when the reference map is the thing you are operating on - and at that moment
# every other target refuses to run, because they all check the reference map first and it is red.
# The REF_OK escape exists for exactly that case and is itself refused by the command-shape hook, so
# a session mid-surgery had NO route to the detail at all.
#
# Third time in one feature that a guard blocked a legitimate question without providing an
# alternative (after `make durations` and `make test-file`), and the answer is the same each time:
# supply the route. A gate that blocks a question you are entitled to ask is a gate that gets
# bypassed.
#
# Deliberately NOT reference-first: it IS the reference map, and gating it behind itself is the
# circularity this target exists to break.
explain:        ## why the reference map is failing - every check, with its message
	@python3 .explain.py

durations:
	@python3 -m pytest -n auto -q --no-cov $(if $(MARK),-m "$(MARK)",-m "not rolls_map" --deselect tests/test_villages.py) --durations=$(or $(N),12) 2>&1 | grep -E "^[0-9.]+s (call|setup)|passed|failed" | head -$$(( $(or $(N),12) + 2 ))

quick:
	@python3 -m ruff check l7r/ tests/ && python3 -m ruff format --check l7r/ tests/ && python3 -m mypy
	@start=$$(date +%s); python3 -m pytest -n auto -q --no-cov -x -m "not rolls_map" --deselect tests/test_villages.py; ec=$$?; \
	  el=$$(( $$(date +%s) - start )); \
	  if [ $$ec -ne 0 ]; then exit $$ec; fi; \
	  if [ $$el -gt $(QUICK_BUDGET) ]; then \
	    printf '\n\033[1mquick took %ss, over its %ss budget.\033[0m\n' "$$el" "$(QUICK_BUDGET)"; \
	    printf 'Something slow is running that should not be. Find it:  \033[1mmake durations\033[0m\n'; \
	    printf 'A test near the top of that list without @pytest.mark.rolls_map is the cause.\n\n'; \
	    exit 1; \
	  fi
	@printf '\n\033[1mquick: clean\033[0m - the %s map-rolling tests were NOT run; `make done` before pushing.\n' "$$(python3 -m pytest -q --no-cov --collect-only -m rolls_map 2>/dev/null | tail -1 | grep -oE '^[0-9]+' || echo 'slow')" 

bypass-audit:
	@why="$(REF_WHY)"; \
	if [ -n "$$why" ] && [ ! -t 0 ]; then \
	  printf "\n\033[1mREFUSED: a FULL run with REF_WHY set, with nothing attached to answer for it.\033[0m\n\n"; \
	  printf "The prompt below exists because its default answer is NO. Passing REF_WHY on the\n"; \
	  printf "command line skips it, and a backgrounded run cannot be asked to reconsider - which is\n"; \
	  printf "exactly how feature 126 ran the full gate THREE times against a standing instruction to\n"; \
	  printf "run only the reference settlement. Every bypass was logged and none was stopped.\n\n"; \
	  printf "  \033[1mmake reference\033[0m   Inashiro seed 4 alone, ~60 s - almost always what you want\n"; \
	  printf "  \033[1mmake done\033[0m        reference + lint/types + 3,420 tests, ~5.5 min (NOT the quick one)\n\n"; \
	  printf "If you truly need the FULL set, run it in the FOREGROUND and answer the prompt.\n\n"; \
	  $(LOGBYPASS) refused "$$why"; \
	  exit 1; \
	fi; \
	if [ -z "$$why" ]; then \
	  printf '\n\033[1mAbout to run the FULL test set.\033[0m\n\n'; \
	  printf 'The reference settlement rebuilds in ~60 s. The full set additionally rolls every\n'; \
	  printf 'live pool map, re-gates each, and rolls seeds 41-44 - minutes, not seconds.\n\n'; \
	  printf '\033[1mMost of the time the right answer here is to back out.\033[0m Press Enter to CANCEL\n'; \
	  printf 'and run the reference-scope gate instead - that is the default and it is usually right.\n\n'; \
	  printf 'Legitimate reasons to continue: the reference map is itself under surgery and expected\n'; \
	  printf 'to fail; you are bisecting a knowingly-red tree; the subject is a check that only fires\n'; \
	  printf 'on a non-reference map; you are about to push and need the full pre-push verdict.\n'; \
	  printf 'Not legitimate: wanting to see everything, impatience, or "while I am here".\n\n'; \
	  printf 'Reason to continue (Enter cancels): '; \
	  read why || true; \
	fi; \
	if [ -z "$$why" ]; then \
	  $(LOGBYPASS) cancelled "(no reason given - backed out at the prompt)"; \
	  printf '\n\033[1mCancelled - good call.\033[0m Nothing expensive ran.\n'; \
	  printf 'Run `make done` on its own for the reference-scope gate.\n\n'; \
	  exit 1; \
	fi; \
	mkdir -p dev; \
	$(LOGBYPASS) permitted "$$why"; \
	printf '\nlogged to dev/bypass-log.jsonl - proceeding\n\n'

reference:
	@python3 -c "import sys; sys.path.insert(0, '.'); 	from l7r.diagram import hamletgen as hg; 	r = hg.generate(hg.HamletSpec(name='Inashiro', seed=4, households=15, down_deg=90, water_sink='pond'), out_base=None, render=False); 	print('\033[1mreference settlement (Inashiro, seed 4): ' + ('CLEAN\033[0m' if r.ok else 'FAILING\033[0m -> ' + ', '.join(r.failures))); 	sys.exit(0 if r.ok else 1)" || { 	  printf '\n\033[1mSTOPPING HERE.\033[0m The reference settlement is red, so nothing more expensive runs.\n'; 	  printf 'Fix Inashiro first - it rebuilds in about a minute. Everything else is 4x to 25x that,\n'; 	  printf 'and none of it can tell you anything useful while the one map you iterate on is broken.\n'; 	  printf '(REF_OK=1 overrides, when the reference map is expected to fail.)\n\n'; exit 1; }

maps:
	@python3 -m l7r.diagram.tools.mapcheck

perf:
	@python3 -m l7r.diagram.tools.perf_snapshot --record --label "$(or $(LABEL),adhoc)"

perf-report:
	@python3 -m l7r.diagram.tools.perf_snapshot --report $(if $(AGAINST),--against $(AGAINST),)

# Refuse to run from the MAIN /gm-assistant tree (CLAUDE.md "Session clones": main is the
# integration point, never a workspace - work runs in .clones/<session-name>). Every target
# depends on this. GM override for a deliberate main-tree run: GM_ASSISTANT_ALLOW_MAIN=1.
guard:
	@case "$(CURDIR)" in \
	  /gm-assistant/.clones/*) ;; \
	  /gm-assistant|/gm-assistant/*) [ "$$GM_ASSISTANT_ALLOW_MAIN" = 1 ] || { \
	    echo "ERROR: this ran from the MAIN /gm-assistant tree. Main is the integration point, never a workspace."; \
	    echo "Check CLAUDE.md, section 'Session clones' (reload CLAUDE.md if it has fallen out of your context"; \
	    echo "window): create or reuse .clones/<kebab-cased-session-name>, sync it in with 'git pull origin main',"; \
	    echo "and run this same command from inside that clone. (GM override: GM_ASSISTANT_ALLOW_MAIN=1)"; \
	    exit 1; };; \
	esac

lint format typecheck test: | guard

lint:
	python3 -m ruff check .
	python3 ../../../scripts/check-duplicate-defs.py --selftest
	python3 ../../../scripts/check-duplicate-defs.py ../../..

format:
	python3 -m ruff format --check .

typecheck:
	python3 -m mypy

# parallel across cores when pytest-xdist is installed (~1 min vs ~5 min serial, measured
# 2026-07-20 on 22 cores), plain serial pytest otherwise - xdist is a speedup, not a requirement.
# The coverage gate combines worker data, so the coverage requirement holds either way.
#
# COVERAGE IS ENFORCED PER-MODULE since the 2026-08-16 legacy freeze (migration-plan.md "The
# accepted trade"): the hand-authored pool maps are frozen and their gens never run, so the
# above-hamlet wings of settlement.py (towns, cities, the capital) are exercised by nothing until
# those tiers convert to scripted generation. Every other measured module holds 100%; settlement.py
# holds a RATCHET floor - the same discipline as the retired mypy per-module ratchet. RAISE the
# floor as each tier converts (village -> town -> city re-cover their wings); NEVER lower it.
# 94 = measured 94.4% (447 of 8043 statements unreached) on 2026-08-16, the day of the freeze:
# the scripted hamlets + unit tests already reach everything but the town/city/capital wings.
SETTLEMENT_COV_FLOOR = 94

# The `coverage combine --append` below sweeps in the gate-cache parallel data files (hit replays
# and miss-subprocess recordings, feature 026) that pytest-cov's own end-of-session combine may or
# may not have consumed already - the explicit combine is deterministic either way, and a no-op
# when there is nothing left to merge.
# The tests that roll a map other than the reference one. `test` deselects them; `test-full` does not.
DESELECT = --deselect tests/test_villages.py --deselect tests/hamletgen/test_driver.py

test-full: DESELECT =
test-full: COV_FLOORS = 1
test-full: test

# A DESELECTED TEST TAKES ITS COVERAGE WITH IT, so the reference scope CANNOT hold the 100% floor
# (measured 2026-08-24, the first green-path run of this restructure). Deselecting
# tests/test_villages.py and tests/hamletgen/test_driver.py drops `hamletgen/driver.py` to 52% and
# the whole tree to 99% - on code nothing changed. Enforcing a global floor against a deliberately
# partial suite reports a hole that is not there, and it does it on EVERY run, which is the fastest
# way to teach a session to read a red gate as normal.
#
# So the floors belong to the scope that can actually meet them, and the two scopes verify different
# things ON PURPOSE:
#
#   make done          - did *I* break anything? Every test that does not roll another map, plus
#                        `uncovered-in-diff.py`, which names any line in the working diff that no
#                        test reaches. That is the question a working session keeps asking.
#   make done FULL=1   - is the TREE whole? Adds the pool maps and the seeds 41-44 ratchet, and
#                        enforces both coverage floors. This is the pre-push sweep, and the
#                        constitution's mandatory once-at-the-end full run (Principle VI).
#
# WHAT THIS COSTS, said plainly: a coverage hole in code the reference scope does not execute
# survives until the FULL run. It is not silent - the diff check still catches uncovered lines you
# wrote, which is where holes actually come from - but the global invariant is a FULL-run guarantee
# now, not a per-run one. That is the price of having a cheap gate at all, and it was paid
# deliberately rather than by leaving a floor in place that could never be met.
COV_FLOORS =

test:
	@if python3 -c "import xdist" >/dev/null 2>&1; then python3 -m pytest -n auto $(DESELECT); else python3 -m pytest $(DESELECT); fi; ec=$$?; \
	if [ $$ec -ne 0 ]; then python3 ../../../scripts/uncovered-in-diff.py || true; exit $$ec; fi; \
	python3 -m coverage combine --append >/dev/null 2>&1 || true; \
	if [ -z "$(COV_FLOORS)" ]; then \
	  printf '\033[1mcoverage floors: deferred to `make done FULL=1`\033[0m (a deselected test takes its coverage with it - see the Makefile comment)\n'; \
	  python3 ../../../scripts/uncovered-in-diff.py || true; \
	  exit 0; \
	fi; \
	python3 -m coverage report -m --omit='*/settlement/*' --fail-under=100 || { echo "COVERAGE: a module other than settlement.py is under 100% - the table above names it and its missing lines"; exit 1; }; \
	python3 -m coverage report --include='*/settlement/*' --fail-under=$(SETTLEMENT_COV_FLOOR) || { echo "COVERAGE: settlement/ (package combined) fell below its $(SETTLEMENT_COV_FLOOR)% ratchet floor (see the comment above SETTLEMENT_COV_FLOOR in this Makefile; 'python3 -m coverage report -m --include=*/settlement/*' shows the missing lines)"; exit 1; }
