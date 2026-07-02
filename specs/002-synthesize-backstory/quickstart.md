# Quickstart: Synthesize Backstory

How to build, verify, and smoke the feature. All commands from `webapp/`.

## Prerequisites

- Dev container with the GM notes mounted at `/host-l7r-repo/setting/` (l7r.md + budgets.md).
- `[gemini] api_key` set in `development-secrets.ini`; `[gemini] text_model` defaults to `gemini-3.1-pro-preview`.
- `pip install --break-system-packages -r requirements.txt -r requirements-dev.txt` (no new deps; google-genai already pinned).

## Part A - productionize the brief (do first)

1. Move `bakeoff/flavor_clans.md` -> `chargen/flavor_clans.md`.
2. Implement `chargen/brief.py` (corpus resolution + full-brief assembly) test-first; wire `synthesis.load_brief`/`build_prompt` to it.
3. Extend `make prepare-deploy` to snapshot `l7r.md` + `budgets.md` into `webapp/setting/` (gitignored).
4. **Equivalence check** (while bakeoff still exists):
   ```
   python3 -c "import l7r; from chargen import brief; from bakeoff import briefs; \
     assert brief.build_full_brief() == briefs.build_tier('full'); print('full assembly matches')"
   ```
   (Codified as a test too.)

## Part B - wire the button

5. Add the `@ajax synthesize` route in `chargen/website.py` (mirror `generate_art`).
6. Add the button + in-progress state + result panel + steering-notes textarea to `chargen/templates/index.html` (mirror the portrait control); disable the button while a request is in flight.

## Verification (before declaring done)

Python (Principle X, on the new modules):
```
make lint && make format-check && make types && make test && make cov
```
(`cov` runs `--cov=l7r --cov-fail-under=100`; `chargen/brief.py` is added to the coverage source so it is gated too.)

UI (Principle I + VI):
```
make serve            # in one shell (cherryd), then in another:
make ui-verify        # screenshots (4 viewports, multi-scroll) + DOM audit -> zero issues
```
Then an independent `frontend-review` subagent pass on the chargen character page contact sheet at GM-200.

Live smoke:
- Open the chargen page, generate a character, click **Synthesize Backstory**, confirm a 1-3 paragraph grounded result; add a steering note and re-roll; confirm it reflects the steer.
- Verify a clear error (not a thin-prompt fallback) when the corpus path is unavailable.

## Cleanup (last)

7. Delete `webapp/bakeoff/` entirely and remove its `pyproject.toml` grace-list / coverage-omit / mypy-override entries; confirm `make done` stays green and no references to `bakeoff` remain (`grep -rn bakeoff webapp` is clean except history).

## Deploy note

`make prepare-deploy` must run where the GM notes are available (the dev container), since it snapshots them into the artifact. The shipped prompt is that snapshot - re-deploy after editing notes to refresh it.
