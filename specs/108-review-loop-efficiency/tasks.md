# Tasks: Review-Loop Efficiency (scatter audit + three process rules)

**Input**: Design documents from `/specs/108-review-loop-efficiency/` (plan.md, research.md, data-model.md, contracts/scatter-audit-cli.md, quickstart.md)

**Tests**: INCLUDED - Constitution Principle X mandates red-green TDD for new non-trivial behavior.

**Organization**: By user story from spec.md. All paths are relative to the repo root of the session clone.

## Phase 1: Setup

- [X] T001 Wire the new module into the quality gates: add `scatter_audit` to `[tool.coverage.run] source` and to the mypy `files` list in `.claude/skills/diagram/pyproject.toml` (follow the `site_justice` rows; research.md R5)

## Phase 2: Foundational

*(No shared blocking work beyond T001 - the four stories are independent.)*

## Phase 3: User Story 1 - Scatter audit as a script (P1) - MVP

**Goal**: One script parses every scatter base from a pool SVG and adjudicates against the engine's own keep-outs, in seconds.

**Independent test**: `python3 scatter_audit.py pool/hamlets/inashiro` exits 0 with zero violations; a seeded-violation fixture exits 1 naming each violation; a doctored no-scatter SVG exits 2 loudly.

- [X] T002 [US1] RED: write `.claude/skills/diagram/test_scatter_audit.py` first - behavior-named tests against `scatter_audit` covering: base parsing per family from a real tiny-canvas engine render (blade/dot/pine/crown/reed counts per research.md R2, including the three-blades-one-tuft counting); adjudication flags a base seeded inside the cut-bank margin and inside a crop margin (build the fixture by rendering a miniature Settlement with a channel + commons whose scatter is then doctored, or by planting synthetic bases); reed family counted but never adjudicated; zero-bases SVG exits 2; missing artifact exits 2; missing `meta.ftpx` exits 2; `--json` emits the Report keys from data-model.md; exit 0 on clean. Run it - every test must FAIL (module absent) before T003 lands.
- [X] T003 [US1] GREEN: implement `.claude/skills/diagram/scatter_audit.py` per contracts/scatter-audit-cli.md and data-model.md - single-pass anchored-regex SVG parse (R2 styling anchors, bases only); keep-outs via shim + unbound `Settlement._watercourse_segs(shim, channel_margin=shim.px(Settlement._BANK_MARGIN_FT))` and manifest `fields[].poly`+`dry_plots[].poly` padded `_CROP_MARGIN_FT` through `boxed_polys`/`boxed_grid` (R3 - observe-don't-restate, no rule re-implementation); density bands 0-15/15-30/30-45 px beyond the water keep-out; human + `--json` reports; exit codes 0/1/2; `main(argv) -> int` with `# pragma: no cover - CLI entry` guard only. Verify: T002 suite green, 100% coverage on the module, ruff + mypy --strict clean.
- [X] T004 [US1] Ground-truth + performance check (SC-001, SC-003): run `python3 scatter_audit.py pool/hamlets/inashiro` - expect exit 0, zero violations, parse totals reconciling with the 2026-08-16 review's counts (~231k bases), wall time well under 30s (record the measured time in this task's checkbox note); then confirm the committed Inashiro artifacts are byte-untouched (`git status` clean for `pool/`). DONE: 3.0s wall, exit 0, totals reconcile (231,392 adjudicated bases); the first (pre-merge) run caught 3 REAL crop-margin tufts in hem-seam wedges, independently fixed by a57b191 - see research.md R8
- [X] T005 [US1] Update `.claude/agents/settlement-review.md`: DELTA reviews touching scatter/ground-cover run `scatter_audit.py` THEMSELVES (author runs are claims to re-verify, not evidence) and interpret its output; state what the script does NOT cover (halos, corridors, form/legibility - its `checked:` line is authoritative); add the catch-rate requirement - every review pass's notes-entry line records what the pass caught, including "nothing", so the keep/drop question stays answerable (research.md R6 evidence cited). This adds a TOOL, not a detection rule - the Subagent-check TDD procedure does not apply (research.md R7); say so in the commit message.

**Checkpoint**: US1 alone is the MVP - the review-agent bottleneck is converted.

## Phase 4: User Story 2 - Review launches before the author's own pass (P2)

**Goal**: Doctrine orders the review launch ahead of the session's own verification.

**Independent test**: The diagram dev-loop doc's review section states the sharpened rule with the 2026-08-16 measurement.

- [X] T006 [P] [US2] Edit `.claude/skills/diagram/CLAUDE.md` "Invoking a review agent" section: sharpen "launch it EARLY" to "launch the moment the motivating map's regen + gate is green, BEFORE your own visual pass" with the measured why (2026-08-16: review launched after a 52s reasoning turn + own crop reads; review is the critical-path tail, 84s ran past the already-green gate; every second earlier is a second off the task)

## Phase 5: User Story 3 - Open decisions carry an implementation sketch (P3)

**Goal**: Open-decision entries record how the follow-up would land, not just that it is open.

**Independent test**: The convention is in the diagram dev-loop doc; the cut-bank entry is retro-fitted as the worked example.

- [X] T007 [P] [US3] Add the convention to `.claude/skills/diagram/CLAUDE.md` (beside the record-the-why/"A side effect is not a rule" material): an entry recording a deliberately-open rule ALSO records a 2-3 line implementation sketch - landing site, holding test, deliberate exclusions - with the measured why (2026-08-16: the cut-bank follow-up spent its largest LLM turn re-deriving what the open-decision author already knew; ~60-120s per follow-up)
- [X] T008 [P] [US3] Retro-fit the worked example in `.claude/skills/diagram/research/vegetation.md`: annotate the "Scrub stays off open water" entry's superseded open-decision bullet with the sketch it SHOULD have carried (commons `wat_b` call site, the drawn-channels test to extend, streams/marsh exclusions), explicitly labeled as the convention's worked example pointing at "The cut bank" resolution

## Phase 6: User Story 4 - Pre-gate rule + profile recorded (P4)

**Goal**: The redundant foreground pool sweep is ruled out with verified wording; the 2026-08-16 profile is durably recorded.

**Independent test**: docs/iteration-loop.md carries the dated profile block and the rule; the rule's render claim matches research.md R1.

- [X] T009 [P] [US4] Add to `docs/iteration-loop.md` a dated 2026-08-16 block: the cut-bank fix profile (14m33s; LLM 60% / background-wait 28% / tools 12%; top-7 thinking turns 273s; gate 177s NEVER on the critical path - the review agent was; projected floor ~12min for tasks of this shape) and the pre-gate rule: regenerate only the MOTIVATING map in the foreground; run the whole affected test file; do NOT run a foreground pool-regen sweep - the gate verifies the pool (DIAGRAM_SKIP_RENDER + cache) and render-sync regenerates main's renders from main's own tip, so clone-side pool renders feed nothing (verified wording per research.md R1, citing scripts/sync-with-main.sh RENDER MODEL)
- [X] T010 [P] [US4] Add the short always-on form of the pre-gate rule to the root `CLAUDE.md` "Iteration-loop efficiency" bullet list (one line, pointing at docs/iteration-loop.md for the evidence), and mirror a one-line pointer in `.claude/skills/diagram/CLAUDE.md`'s gate-timings section if a natural anchor exists

## Phase 7: Polish & Cross-Cutting

- [X] T011 Full gate: `cd .claude/skills/diagram && make done` backgrounded (Python changed: scatter_audit.py + test + pyproject) - green log tail is the proof; docs-only edits add no gate work. DONE: gate green (log tail verified)
- [X] T012 Spot-check the delegated-nothing rule and finish: re-read every edited doc section as rendered (constitution VI), update `.claude/skills/diagram/CLAUDE.md`/docs for the new diagnostic (add scatter_audit.py beside crop_map.py/why_placed.py in the "Batch the rendered-map inspection"-adjacent tooling mentions if a natural list exists), verify no em-dashes/British spellings in new text, then commit and run `scripts/sync-with-main.sh done`. DONE: doc sections re-read, dash/spelling scans clean; the "natural tooling list" mention landed as the agent-doc Tooling section + quickstart + the gate-timings pointer (no additional list existed to extend)

## Dependencies

- T001 before T003 (gate wiring must exist for coverage to bind) - T002 may run in parallel with T001
- T002 strictly before T003 (red before green, Principle X)
- T003 before T004, T005 (script must exist and be proven before the agent doc points at it)
- US2 (T006), US3 (T007, T008), US4 (T009, T010) are mutually independent and independent of US1 - all [P] after Phase 1
- T011 after all Python tasks (T001-T004); T012 last

## Parallel example

After T001+T002+T003: run T004 while editing T005-T010 (docs, all different files, all [P]); then T011 backgrounded; T012 on its notification.

## Implementation strategy

MVP = Phase 3 (US1). Docs stories are near-free and ride the same session. Single session, single commit-and-sync at the end (plus the gate). Estimated: script+tests dominate; docs are minutes.
