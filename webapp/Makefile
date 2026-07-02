.PHONY: lint format types test cov done clean serve prepare-deploy deploy \
        screenshots dom-audit ui-verify

# The Principle X "done" checklist. A change is not done until `make done` passes.
done: lint format-check types test cov

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
		echo "[done] No tests collected — OK for now"; exit 0; \
	else exit $$ec; fi

cov:
	@if [ -d l7r ]; then \
		pytest --cov=l7r --cov=chargen.brief --cov-report=term-missing --cov-fail-under=100; \
	else \
		echo "[done] No l7r/ package yet — coverage check skipped"; \
	fi

serve:
	cherryd --import l7r

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
	@echo "[ui-verify] contact sheets in /tmp/l7r-shots/sheet-*.png — review at GM-200 with Eli's task in mind."

# Sync pool data from /gm-assistant/.claude/skills into the Docker build context.
# `skills/` is gitignored — it's a build artifact, not source code.
prepare-deploy:
	@echo "[deploy] syncing pool data into webapp/skills/"
	@rm -rf skills
	@mkdir -p skills/relic skills/name skills/place-names
	@cp -r ../.claude/skills/relic/pool skills/relic/pool
	@cp ../.claude/skills/name/pool-male.jsonl ../.claude/skills/name/pool-female.jsonl skills/name/
	@cp ../.claude/skills/place-names/pool.jsonl skills/place-names/pool.jsonl
	@echo "[deploy] context ready: $$(find skills -type f | wc -l) files"
	@echo "[deploy] snapshotting setting corpus into webapp/setting/"
	@rm -rf setting
	@mkdir -p setting
	@cp "$${L7R_SETTING_DIR:-/host-l7r-repo/setting}/l7r.md" setting/l7r.md
	@cp "$${L7R_SETTING_DIR:-/host-l7r-repo/setting}/budgets.md" setting/budgets.md
	@echo "[deploy] corpus ready: $$(find setting -type f | wc -l) files"

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
