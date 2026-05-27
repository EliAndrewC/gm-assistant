.PHONY: lint format types test cov done clean serve prepare-deploy deploy

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
		pytest --cov=l7r --cov-report=term-missing --cov-fail-under=100; \
	else \
		echo "[done] No l7r/ package yet — coverage check skipped"; \
	fi

serve:
	cherryd --import l7r

# Sync pool data from /workspace/.claude/skills into the Docker build context.
# `skills/` is gitignored — it's a build artifact, not source code.
prepare-deploy:
	@echo "[deploy] syncing pool data into webapp/skills/"
	@rm -rf skills
	@mkdir -p skills/relic skills/name
	@cp -r ../.claude/skills/relic/pool skills/relic/pool
	@cp ../.claude/skills/name/pool-male.jsonl ../.claude/skills/name/pool-female.jsonl skills/name/
	@echo "[deploy] context ready: $$(find skills -type f | wc -l) files"

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
