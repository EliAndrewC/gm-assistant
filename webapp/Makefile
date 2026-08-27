.PHONY: lint format types test cov done clean serve prepare-deploy deploy \
        screenshots dom-audit ui-verify guard hooks-test

# The Principle X "done" checklist. A change is not done until `make done` passes.
#
# Runs EVERY phase and reports all failures together (GM 2026-07-25). It used to be
# `done: lint format-check types test cov`, which make stops at the first failure - so a lint slip
# hid a type error hid a coverage hole, and each hidden failure cost another full round trip to
# discover. Phases stay in cheap-to-expensive order so the fast ones report first, but none of them
# short-circuits the rest. Exit is non-zero if any phase failed: exactly as strict as before.
done:
	@fail=""; \
	for phase in lint format-check types hooks-test test cov; do \
	  printf '\n\033[1m== %s ==\033[0m\n' "$$phase"; \
	  $(MAKE) --no-print-directory $$phase || fail="$$fail $$phase"; \
	done; \
	if [ -n "$$fail" ]; then printf '\n\033[1mGATE FAILED:%s\033[0m (every phase ran - fix them together, then re-run once)\n' "$$fail"; exit 1; fi; \
	root=$$(git rev-parse --show-toplevel 2>/dev/null) && [ -n "$$root" ] && python3 "$$root/scripts/gate-stamp.py" --write webapp || true; \
	printf '\n\033[1mgate green\033[0m\n'

# Refuse to run from the MAIN /gm-assistant tree (CLAUDE.md "Session clones": main is the
# integration point, never a workspace - work runs in .clones/<session-name>). Every target
# except `serve` depends on this (the GM legitimately serves the toolkit from main to browse
# it). GM override for a deliberate main-tree run: GM_ASSISTANT_ALLOW_MAIN=1.
# MAIN IS THE TREE THAT CONTAINS `.clones/` (feature 131, 2026-08-25): a clone or a detached
# worktree has none of its own (gitignored), so no path is hardcoded - the same rule as the diagram
# Makefile's guard and webapp/mainguard.py.
guard:
	@top=$$(git rev-parse --show-toplevel 2>/dev/null); \
	case "$(CURDIR)" in */.clones/*) exit 0 ;; esac; \
	if [ -n "$$top" ] && [ -d "$$top/.clones" ] && [ "$$GM_ASSISTANT_ALLOW_MAIN" != 1 ]; then \
	    echo "ERROR: this ran from the MAIN tree ($$top). Main is the integration point, never a workspace."; \
	    echo "Check CLAUDE.md, section 'Session clones' (reload CLAUDE.md if it has fallen out of your context"; \
	    echo "window): create or reuse .clones/<kebab-cased-session-name>, sync it in with 'git pull origin main',"; \
	    echo "and run this same command from inside that clone. (GM override: GM_ASSISTANT_ALLOW_MAIN=1)"; \
	    exit 1; \
	fi

# EVERY GUARD'S TEST COMPANION ACTUALLY RUNS HERE TOO (constitution XVIII; feature 131, 2026-08-25).
# Until the split this target existed only in the diagram skill's Makefile, so gm-assistant's own
# hooks were exercised by nothing once the diagram left. Same loop, same companion rule.
hooks-test:
	@root=$$(git rev-parse --show-toplevel); fail=""; n=0; \
	for h in $$root/scripts/*-hooks.sh $$root/scripts/review-gate.sh; do \
	  [ -f "$$h" ] || continue; \
	  b=$$(basename $$h); case $$b in test-*) continue ;; esac; \
	  if [ ! -f "$$root/scripts/test-$$b" ]; then \
	    printf '\n\033[1mGUARD WITHOUT A TEST: %s has no scripts/test-%s\033[0m\n' "$$b" "$$b"; fail="$$fail $$b"; continue; \
	  fi; \
	  n=$$((n+1)); \
	  "$$root/scripts/test-$$b" >/tmp/ht.$$$$ 2>&1 || { printf '\n\033[1mHOOK TESTS FAILED: %s\033[0m\n' "$$b"; sed 's/^/  /' /tmp/ht.$$$$; fail="$$fail $$b"; }; \
	  rm -f /tmp/ht.$$$$; \
	done; \
	if [ -n "$$fail" ]; then printf '\n\033[1mhooks-test FAILED:%s\033[0m\n\n' "$$fail"; exit 1; fi; \
	printf 'hooks-test: %s guard suites green\n' "$$n"

lint format format-check types test cov clean screenshots dom-audit ui-verify prepare-deploy deploy: | guard

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

types:
	mypy .

test:
	@pytest; ec=$$?; \
	if [ $$ec -eq 5 ]; then \
		echo "[done] No tests collected - OK for now"; exit 0; \
	else exit $$ec; fi

cov:
	@if [ -d l7r ]; then \
		pytest --cov=l7r --cov=chargen.brief --cov=chargen.opcache --cov=chargen.opsynth --cov=chargen.similarity --cov=chargen.namepool --cov=chargen.sheetroster --cov=chargen.placeuse --cov-report=term-missing --cov-fail-under=100; ec=$$?; \
		if [ $$ec -ne 0 ]; then python3 ../scripts/uncovered-in-diff.py || true; fi; exit $$ec; \
	else \
		echo "[done] No l7r/ package yet - coverage check skipped"; \
	fi

serve:
	cherryd --import l7r.app

# Capture multi-scroll contact sheets at all four standard viewports. Output
# in /tmp/l7r-shots/sheet-<page>-<viewport>.png. Assumes a server is running
# at L7R_BASE_URL (default http://127.0.0.1:8080).
screenshots:
	python3 tests/screenshot.py

# DOM audit: clipping + layout balance (Constitution Principle I, v1.3.0).
dom-audit:
	python3 tests/dom_audit.py

# Full Principle I verification: contact sheets + DOM audit. Assumes a server.
# After this passes, the persona-driven review pass + frontend-review subagent
# (if author == reviewer) is the remaining step before declaring a UI change done.
ui-verify: screenshots dom-audit
	@echo "[ui-verify] contact sheets in /tmp/l7r-shots/sheet-*.png - review at GM-200 with Eli's task in mind."

# Sync pool data from ../.claude/skills into the Docker build context.
# `skills/` is gitignored - it's a build artifact, not source code.
prepare-deploy:
	@echo "[deploy] syncing pool data into webapp/skills/"
	@rm -rf skills
	@mkdir -p skills/relic skills/name skills/place-names skills/dream
	@cp -r ../.claude/skills/relic/pool skills/relic/pool
	@cp ../.claude/skills/name/pool-male.jsonl ../.claude/skills/name/pool-female.jsonl skills/name/
	@# GUARD_EDIT_OK: adding a new file to the deploy bundle. used-names-extra.txt lists names in
	@# use that OP cannot report (a PC with no record); the deployed engine must exclude them too.
	@cp ../.claude/skills/name/used-names-extra.txt skills/name/
	@# GUARD_EDIT_OK: bundling the verified Wikipedia links the /names page renders on bearers' names.
	@cp ../.claude/skills/name/wiki-links.json skills/name/
	@cp ../.claude/skills/place-names/pool.jsonl skills/place-names/pool.jsonl
	@# Dream scenes: copy the PUBLIC pool ONLY. pool-local/ is gitignored spoiler
	@# content and must never enter the image (feature 011, FR-007).
	@cp -r ../.claude/skills/dream/pool skills/dream/pool
	@echo "[deploy] context ready: $$(find skills -type f | wc -l) files"
	@echo "[deploy] snapshotting setting corpus into webapp/setting/"
	@rm -rf setting
	@mkdir -p setting
	@cp "$${L7R_SETTING_DIR:-/host-l7r-repo/setting}/l7r.md" setting/l7r.md
	@cp "$${L7R_SETTING_DIR:-/host-l7r-repo/setting}/budgets.md" setting/budgets.md
	@echo "[deploy] corpus ready: $$(find setting -type f | wc -l) files"
	@echo "[deploy] refreshing campaign-character cache into webapp/opcache/"
	@python3 -c "import l7r.app; from chargen import opcache; opcache.refresh_cache_file()"
	@echo "[deploy] opcache ready: $$(find opcache -type f | wc -l) files"

# Deploy to Fly.io. Reads FLY_API_TOKEN from .env (handled by grep, not `source`,
# because Fly tokens contain a literal space which trips shell sourcing).
# Adds the standard flyctl install location to PATH so non-interactive shells
# (like make) find it without the user re-sourcing their shell profile.
deploy: done prepare-deploy
	@FLY_API_TOKEN="$$(grep '^FLY_API_TOKEN=' .env | sed 's/^FLY_API_TOKEN=//')"; \
	export FLY_API_TOKEN; \
	PATH="$$HOME/.fly/bin:$$PATH" flyctl deploy --remote-only

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__ \
	       .coverage htmlcov skills
	find . -type d -name __pycache__ -exec rm -rf {} +
