# The diagram-skill quality gate (Constitution Principle X). Run `make done` before declaring
# any Python change complete. Runs, in order: lint, format-check, type-check, tests+100% coverage.
#
# mypy uses a per-module ratchet (see pyproject.toml): the legacy engine modules are relaxed until
# each is migrated to --strict in its own pass; new modules are strict immediately.

.PHONY: done lint format typecheck test test-full guard perf perf-report maps reference bypass-audit quick

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
	@fail=""; \
	for phase in lint format typecheck $(if $(FULL),test-full,test); do \
	  printf '\n\033[1m== %s ==\033[0m\n' "$$phase"; \
	  $(MAKE) --no-print-directory $$phase || fail="$$fail $$phase"; \
	done; \
	if [ -n "$$fail" ]; then printf '\n\033[1mGATE FAILED:%s\033[0m (every phase ran - fix them together, then re-run once)\n' "$$fail"; exit 1; fi; \
	root=$$(git rev-parse --show-toplevel 2>/dev/null) && [ -n "$$root" ] && python3 "$$root/scripts/gate-stamp.py" --write diagram || true; \
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
# `make quick` is what an iteration loop uses once the reference map is clean: lint, types, and
# every test that does NOT roll a map, with pytest's `-x` so it STOPS at the first failure. Seconds,
# not minutes, and it answers "is what I just wrote coherent" rather than "is this safe to ship".
#
# The full suite rolls a dozen-plus maps (test_village_passes_gate regenerates and re-gates every
# live pool map; the ratchet rolls seeds 41-44), which is right for a pre-push gate and wrong for a
# loop. Measured on feature 126: `make done` is ~5 minutes and I ran it repeatedly over a tree I
# already knew was broken.
quick:
	@$(MAKE) --no-print-directory reference
	@python3 -m ruff check l7r/ tests/ && python3 -m ruff format --check l7r/ tests/ && python3 -m mypy
	@python3 -m pytest -n auto -q --no-cov -x --deselect tests/test_villages.py --deselect tests/hamletgen/test_driver.py
	@printf '\n\033[1mquick: clean\033[0m - the map-rolling tests are NOT included; `make done` before pushing.\n'

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
	  printf '\n\033[1mCancelled - good call.\033[0m Nothing expensive ran.\n'; \
	  printf 'Run `make done` on its own for the reference-scope gate.\n\n'; \
	  exit 1; \
	fi; \
	mkdir -p dev; \
	python3 -c "import json,sys,time,subprocess; \
	h=subprocess.run(['git','rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip(); \
	open('dev/bypass-log.jsonl','a').write(json.dumps({'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'target':'$(MAKECMDGOALS)','commit':h,'why':sys.argv[1]})+chr(10))" "$$why"; \
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
