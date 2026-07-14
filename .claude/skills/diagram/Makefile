# The diagram-skill quality gate (Constitution Principle X). Run `make done` before declaring
# any Python change complete. Runs, in order: lint, format-check, type-check, tests+100% coverage.
#
# mypy uses a per-module ratchet (see pyproject.toml): the legacy engine modules are relaxed until
# each is migrated to --strict in its own pass; new modules are strict immediately.

.PHONY: done lint format typecheck test

done: lint format typecheck test

lint:
	python3 -m ruff check .

format:
	python3 -m ruff format --check .

typecheck:
	python3 -m mypy

test:
	python3 -m pytest
