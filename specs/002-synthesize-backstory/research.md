# Phase 0 Research: Synthesize Backstory

Decisions that resolve the open questions before design. No `NEEDS CLARIFICATION` remained in the spec; these settle implementation approach.

## D1. Where the new pure logic lives (Principle X coverage home)

**Decision**: Put corpus loading + full-brief assembly in a new module `chargen/brief.py`, added to the coverage source and to `mypy --strict`. Keep the Gemini call in the grace-listed `synthesis.py` as the fixture-tested boundary.

**Rationale**: The coverage gate runs `--cov=l7r` and omits all chargen modules, so logic placed in the legacy chargen files is invisible to the 100% gate (FR-011 would be unmeetable there). The project direction is "new code is compliant; legacy chargen has a grace period." A dedicated new module is the smallest change that brings the new logic under ruff + mypy --strict + 100% coverage without forcing a full migration of `synthesis.py`/`website.py`. `pyproject.toml` adds `chargen/brief.py` to `[tool.coverage.run] source` and removes it from any omit; it is NOT added to the chargen grace lists.

**Alternatives rejected**: (a) Put logic in `synthesis.py` and un-grace the whole module - larger blast radius, drags the Gemini-call code into strict typing churn now. (b) Put it in the `l7r/` package - awkward, the logic is chargen-coupled (reads chargen brief/flavor files) and would invert the dependency.

## D2. How the corpus reaches production (no bind-mount on Fly)

**Decision**: Extend `make prepare-deploy` to snapshot `l7r.md` + `budgets.md` from the dev mount into `webapp/setting/` (gitignored, like `webapp/skills/`), and ensure the Dockerfile build context includes it. `chargen/brief.py` resolves the corpus from a configured path with a clear resolution order: an explicit config/env path, else the bundled `webapp/setting/`, else the dev mount `/host-l7r-repo/setting/`. If none is found, raise a clear error (FR-010) - never silently degrade.

**Rationale**: Mirrors the established pool-data bundling (`prepare-deploy` already syncs `skills/`). Keeping the snapshot gitignored avoids committing a duplicate of the GM's notes into this repo (and avoids SOURCE-block duplication concerns - Principle IV). The snapshot is a per-deploy point-in-time copy (FR-007, accepted in Assumptions).

**Alternatives rejected**: committing l7r.md into the repo (duplicates GM source, Principle IV friction); fetching from GitHub at runtime (network dependency + auth in the request path).

## D3. New home for flavor_clans.md

**Decision**: Move `webapp/bakeoff/flavor_clans.md` to `webapp/chargen/flavor_clans.md`. `brief.py` reads it from the chargen package dir.

**Rationale**: `bakeoff/` is deleted at the end; the flavor summary is production prompt content and must survive. It is AI-generated (no SOURCE markers), so relocation is unrestricted.

## D4. "The Great Clans" blurb in production

**Decision**: `brief.py` extracts the "The Great Clans" section from the bundled/mounted `l7r.md` by heading (the same `extract_section` logic the bakeoff used), so it stays single-sourced and cannot drift. Since `full` already includes the entire l7r.md, the blurb is technically a duplicated slice; keep it for parity with the validated `full` assembly (D6) and because it front-loads the framing.

**Rationale**: No retyping, no drift; matches the assembly the bakeoff validated.

## D5. Testing the Gemini boundary via fixtures

**Decision**: Record one real `gemini-3.1-pro-preview` response (a `generate_content` result) and save it under `chargen/fixtures/`. `test_synthesis.py` patches only the client's `generate_content` to return the saved fixture object, asserting that `synthesize()` assembles the prompt correctly and returns the stripped text. `build_prompt`/`brief.py` are tested directly with no network at all.

**Rationale**: Principle X.5 - external boundaries test against saved fixtures, not transport-layer mocks. The fixture is the real response shape; we do not mock `requests`/HTTP.

## D6. Equivalence verification before deleting bakeoff

**Decision**: Before removing `bakeoff/`, add a one-shot check (a test, marked so it can run while bakeoff still exists) asserting `chargen.brief.build_full_brief(...) == bakeoff.briefs.build_tier('full')` for the same corpus inputs. Only after it passes (FR-009) do we delete `bakeoff/` and its pyproject entries.

**Rationale**: Proves the productionized assembly reproduces the validated winner before the reference implementation is destroyed. The check is deleted along with `bakeoff/`.

## D7. UI verification for the chargen page

**Decision**: Reuse the Playwright screenshot + DOM-audit workflow at the four standard viewports, pointed at the chargen character page (the page hosting the new button). Run the `frontend-review` subagent for the independent pass since the implementing agent is also reviewing. If the existing tooling only targets l7r pages, add a chargen target URL as part of the UI task.

**Rationale**: Principle I + VI are non-negotiable for UI changes; the control is small but still UI.

## D8. Re-roll and steering wiring

**Decision**: Re-roll is a re-invocation of the same `@ajax synthesize` route (no extra state; each call is fresh). Steering notes are a form field passed straight to `synthesis.synthesize(extra_notes=...)`, which already supports them and gives them high priority in `build_prompt`. Concurrency: disable the button while a request is in flight (mirrors `generate_art`).

**Rationale**: Minimal surface; the backend already supports `extra_notes`; matches the portrait pattern.
