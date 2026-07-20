# The diagram-skill quality gate (Constitution Principle X). Run `make done` before declaring
# any Python change complete. Runs, in order: lint, format-check, type-check, tests+100% coverage.
#
# mypy uses a per-module ratchet (see pyproject.toml): the legacy engine modules are relaxed until
# each is migrated to --strict in its own pass; new modules are strict immediately.

.PHONY: done lint format typecheck test guard

done: lint format typecheck test

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

format:
	python3 -m ruff format --check .

typecheck:
	python3 -m mypy

# parallel across cores when pytest-xdist is installed (~1 min vs ~5 min serial, measured
# 2026-07-20 on 22 cores), plain serial pytest otherwise - xdist is a speedup, not a requirement.
# The coverage gate combines worker data, so the 100% requirement holds either way.
test:
	@if python3 -c "import xdist" >/dev/null 2>&1; then python3 -m pytest -n auto; else python3 -m pytest; fi
