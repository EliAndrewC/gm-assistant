# The diagram-skill quality gate (Constitution Principle X). Run `make done` before declaring
# any Python change complete. Runs, in order: lint, format-check, type-check, tests+100% coverage.
#
# mypy uses a per-module ratchet (see pyproject.toml): the legacy engine modules are relaxed until
# each is migrated to --strict in its own pass; new modules are strict immediately.

.PHONY: done lint format typecheck test guard perf perf-report

# Runs EVERY phase and reports all failures together (GM 2026-07-25). It used to be
# `done: lint format typecheck test`, which make stops at the first failure - so a lint slip hid a
# type error hid a coverage hole, and each hidden failure cost another full round trip to discover.
# Phases stay in cheap-to-expensive order so the fast ones report first, but none of them short-
# circuits the rest. Exit is non-zero if any phase failed, so this is exactly as strict as before.
done:
	@fail=""; \
	for phase in lint format typecheck test; do \
	  printf '\n\033[1m== %s ==\033[0m\n' "$$phase"; \
	  $(MAKE) --no-print-directory $$phase || fail="$$fail $$phase"; \
	done; \
	if [ -n "$$fail" ]; then printf '\n\033[1mGATE FAILED:%s\033[0m (every phase ran - fix them together, then re-run once)\n' "$$fail"; exit 1; fi; \
	root=$$(git rev-parse --show-toplevel 2>/dev/null) && [ -n "$$root" ] && python3 "$$root/scripts/gate-stamp.py" --write diagram || true; \
	printf '\n\033[1mgate green\033[0m\n'

# THE REFERENCE-HAMLET PERFORMANCE BOOKENDS (constitution VI, GM 2026-08-23).
#
# Deliberately NOT part of `done`. A hamlet takes 30-160s and the reference set is four seeds, so
# folding this into the gate would roughly double a cycle that already runs ~5 minutes - and this
# project's own measurements say iteration latency is the dominant cost of a feature. So the sweep
# is explicit and the CONSTITUTION carries the obligation to run it, at the start of a diagram
# feature and again before it ships.
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
test:
	@if python3 -c "import xdist" >/dev/null 2>&1; then python3 -m pytest -n auto; else python3 -m pytest; fi; ec=$$?; \
	if [ $$ec -ne 0 ]; then python3 ../../../scripts/uncovered-in-diff.py || true; exit $$ec; fi; \
	python3 -m coverage combine --append >/dev/null 2>&1 || true; \
	python3 -m coverage report -m --omit='*/settlement/*' --fail-under=100 || { echo "COVERAGE: a module other than settlement.py is under 100% - the table above names it and its missing lines"; exit 1; }; \
	python3 -m coverage report --include='*/settlement/*' --fail-under=$(SETTLEMENT_COV_FLOOR) || { echo "COVERAGE: settlement/ (package combined) fell below its $(SETTLEMENT_COV_FLOOR)% ratchet floor (see the comment above SETTLEMENT_COV_FLOOR in this Makefile; 'python3 -m coverage report -m --include=*/settlement/*' shows the missing lines)"; exit 1; }
