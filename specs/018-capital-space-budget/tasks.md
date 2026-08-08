# Tasks: Domain-capital space budget and tier declaration

**Feature**: 018-capital-space-budget | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Working directory for every path below**: `.claude/skills/diagram/` (paths are given repo-relative).

**Red-green TDD is NON-NEGOTIABLE here** (Constitution Principle X.4). Every implementation task is preceded by the test task that must be **written and seen failing** first. Do not batch the tests to the end.

**Two files are EXTENDED, never recreated**: `test_citybudget.py` and `test_checks.py`.

**Do not touch `test_tango_program_back_predicts_the_shipped_wall`** or `test_shipped_city_programs_price_exactly_as_they_did_before_the_temple_knobs`. They are the byte-identity guards. If either goes red, the feature has broken the provincial path and the fix is to stop, not to update the expectation.

---

## Phase 1: Setup

- [x] T001 Confirm the working base: `git -C . log --oneline -1` shows the spec/plan commit, and `git status --porcelain` is clean, in the session clone `.clones/diagram-city`
- [x] T002 Re-read the two settled decision docs so no number is re-derived from memory: `.claude/skills/diagram/settlements/capitals.md` and `.claude/skills/diagram/research/cities/capitals.md`

---

## Phase 2: Foundational (BLOCKING - all user stories depend on this)

**Purpose**: the constants and the program dataclass every later phase constructs. Nothing here is user-visible on its own.

- [x] T003 Write failing tests for the two new ground-cost constants in `.claude/skills/diagram/test_citybudget.py`: assert `C_YASHIKI` and `C_TERRACE` exist, sit in the documented ranges, and stand in the expected order against the existing `C_PACKED` / `C_SPACED` (terrace > packed, yashiki > spaced)
- [x] T004 Add `C_YASHIKI` (~4,150) and `C_TERRACE` (~660) to `.claude/skills/diagram/citybudget.py`, each with its measured basis in a comment at the definition (Fukui Suginuma plan; Shibata ashigaru-nagaya floor + detached-house ceiling), and mark `C_TERRACE` in its comment as the softest number in the feature
- [x] T005 Write failing tests in `.claude/skills/diagram/test_citybudget.py` for `CAPITAL_FAMILIES`, `CAPITAL_RANK_BANDS` and `CAPITAL_SAMURAI_INWALL_FRAC`: the caste table matches budgets.md exactly (480/960/600/120/240 +72 +12, zero farmers), the rank bands sum to the 800-working column and yield 20/50/30, and the in-wall fraction is the capital's ~0.85 rather than the provincial 2/3
- [x] T006 Add `CAPITAL_FAMILIES`, `CAPITAL_RANK_BANDS` (stored as the raw rank-table counts, with shares DERIVED from them so the split stays traceable) and `CAPITAL_SAMURAI_INWALL_FRAC` to `.claude/skills/diagram/citybudget.py`, each carrying its budgets.md provenance in a comment
- [x] T007 Write failing tests in `.claude/skills/diagram/test_citybudget.py` for the `CapitalProgram` dataclass shape: it is frozen, carries the fields in data-model.md with their defaults, and rejects a population outside the capital band with both the figure and the band in the message
- [x] T008 Add the frozen `CapitalProgram` dataclass and `CAPITAL_POP_MIN`/`CAPITAL_POP_MAX` to `.claude/skills/diagram/citybudget.py` with population-band validation in `__post_init__`

**Checkpoint**: constants and program exist; nothing plans a budget yet.

---

## Phase 3: User Story 1 - A capital's wall is DERIVED, never guessed (Priority: P1) 🎯 MVP

**Goal**: declare a capital program, receive an itemized budget and the wall that program requires.

**Independent test**: construct a `CapitalProgram` and call `plan_capital`; read back a wall, with no map drawn and nothing else in the tier implemented.

- [x] T009 Write failing tests in `.claude/skills/diagram/test_citybudget.py` for the capital civic program table: it exists, every row is `(label, count | None, row_total_px2)`, and the six domain ministries row is a ROW TOTAL rather than a per-unit cost
- [x] T010 Add `CAPITAL_CIVIC_PROGRAM` to `.claude/skills/diagram/citybudget.py` with the rows from data-model.md (domain ministries + government ward, House Chancellery, Imperial Magistrate's compound, Emperor's granaries, domain school, domain granary + brokers' row, martial hall + rolled dojos, aqueduct in-wall works, minor civic, shops/inns/stables, bell-and-drum tower, breweries, trade works), each row carrying its derivation in a comment, and a comment stating the row-total convention explicitly
- [x] T011 Write a failing PINNED test in `.claude/skills/diagram/test_citybudget.py` that fixes the shipped capital civic program - every row's label, count and total - so the row-total-vs-per-unit trap that nearly doubled every city's temple ground in feature 016 cannot recur silently on this table
- [x] T012 Write failing tests in `.claude/skills/diagram/test_citybudget.py` for `plan_capital`'s inventory: the samurai cohort is split in-wall by `CAPITAL_SAMURAI_INWALL_FRAC` and then by rank band into three housing lines (yashiki / detached / terrace), and the packed castes are priced at `C_PACKED`
- [x] T013 Implement `plan_capital` in `.claude/skills/diagram/citybudget.py` - inventory, the three samurai housing lines, the castle line, the civic program, the sovereign temples, the adept-monk line, the water line, extras, and the solved circulation fraction - returning the existing `CityBudget`
- [x] T014 Widen `CityBudget.program` to `CityProgram | CapitalProgram` in `.claude/skills/diagram/citybudget.py` and confirm `budget_to_manifest` / `format_budget` need NO tier branch (this is what `CapitalProgram.agricultural_district` exists for)
- [x] T015 Write failing tests in `.claude/skills/diagram/test_citybudget.py` that the capital's lines sum exactly to `required_interior_px2`, that circulation is the declared fraction OF THE INTERIOR (not of the fixed subtotal), and that every capital line carries a non-empty label and basis
- [x] T016 Write a failing test in `.claude/skills/diagram/test_citybudget.py` that the canonical capital program derives a wall of ~rx 1,029 / ry 957 and that it FITS the standard 3,200 x 2,700 canvas including `WALL_MARGIN_PX` (SC-002)
- [x] T017 Write a failing test in `.claude/skills/diagram/test_citybudget.py` that a derived capital wall too large for a declared canvas raises with the numbers stated rather than clamping (FR-013)
- [x] T018 Write a failing PINNED test in `.claude/skills/diagram/test_citybudget.py` fixing the capital's budget LINE ORDER, so the capital sequence cannot churn silently the way the provincial temple line once threatened to
- [x] T019 [P] Write failing tests in `.claude/skills/diagram/test_checks.py` for `capital_wall_matches_budget`: a capital manifest enclosing more than +8% over its declared required interior FAILS, one under -5% FAILS, one inside the band PASSES, and a non-capital manifest never runs the check
- [x] T020 [P] Implement `capital_wall_matches_budget` in `.claude/skills/diagram/check_village.py`, scoped to `meta.scale == "capital"`, reusing the provincial tolerances with a comment saying they are inherited deliberately (pinned by the shipped-Tango / rejected-Nagahara pair) rather than re-derived
- [x] T021 [P] Write a failing test in `.claude/skills/diagram/test_checks.py` for `capital_declares_a_budget`: a capital manifest with NO `meta.budget` FAILS rather than silently skipping the conformance check (FR-015, SC-007)
- [x] T022 [P] Implement `capital_declares_a_budget` in `.claude/skills/diagram/check_village.py`, modeled on `settlement_declares_a_land_fall`, with a message that says a capital declaring no budget skips its conformance check while still showing green

**Checkpoint**: a capital budget can be planned and a capital manifest is held to it. This is the MVP.

---

## Phase 4: User Story 2 - The GM can audit the budget line by line (Priority: P2)

**Goal**: read where a capital's ground goes before anything is drawn.

**Independent test**: run the report for a capital and read the itemized lines; no map need exist.

- [x] T023 Write a failing test in `.claude/skills/diagram/test_citybudget.py` that `format_budget` on a capital prints every line with its label, count, px^2, acres and basis, and that the castle appears as its OWN line and the samurai cohort as THREE separate housing lines rather than one total (SC-004, US2 AS-2)
- [x] T024 Extend `format_budget` in `.claude/skills/diagram/citybudget.py` as needed so a capital budget renders correctly, without changing the provincial output by a single character
- [x] T025 Write failing tests in `.claude/skills/diagram/test_citybudget.py` for the CLI: `--tier capital` prints the capital report, `--tier` DEFAULTS to provincial so every existing invocation is unchanged, and `--agri` with `--tier capital` is REJECTED rather than silently ignored
- [x] T026 Add `--tier` to the CLI in `.claude/skills/diagram/citybudget.py`, defaulting to `provincial`, routing to `plan_capital` for `capital`, and refusing `--agri` at capital tier with a message saying a capital walls its farms out

**Checkpoint**: the budget is auditable from the command line at both tiers.

---

## Phase 5: User Story 3 - A capital's variant knobs are validated when declared (Priority: P3)

**Goal**: an impossible declaration is refused at construction, not discovered on a rendered map.

**Independent test**: construct each knob value and each invalid combination and observe acceptance or a stated refusal.

- [x] T027 Write failing parametrized tests in `.claude/skills/diagram/test_citybudget.py` covering the knob matrix: `castle_seat="edge"` without `river` raises; `castle_seat="edge"` with `river` is accepted; `castle_seat="ring"` is accepted either way; an unrecognized `castle_seat` raises listing the legal set; an unrecognized `imperial_granary_seat` raises listing the legal set; `castle_px2` outside the 50-230 ha band raises; `agricultural_district=True` raises
- [x] T028 Add `CASTLE_SEATS` and `IMPERIAL_GRANARY_SEATS` constants and the matching validation to `CapitalProgram.__post_init__` in `.claude/skills/diagram/citybudget.py`, each raise naming the offending value AND the legal alternatives (SC-005), with the castle-seat/water coupling carrying its reason in the message
- [x] T029 Add the castle-band and always-False-agricultural-district validation to `CapitalProgram.__post_init__` in `.claude/skills/diagram/citybudget.py`, each with its reason in a comment (a castle outside 50-230 ha is a program error the GM should see; a capital walls its farms out)

**Checkpoint**: every invalid declaration in the spec's Edge Cases produces a named refusal.

---

## Phase 6: Polish, docs and verification

- [x] T030 [P] Update `.claude/skills/diagram/settlements/capitals.md`: drop the blanket "NOT YET IMPLEMENTED" for the parts this feature ships, point the budget, knobs and ground-cost sections at the shipped surface, and keep the banner ONLY for the still-undrawn glyph work
- [x] T031 [P] Update `.claude/skills/diagram/research/cities/capitals.md`: mark `C_YASHIKI` / `C_TERRACE` / the castle line as shipped, and keep the note that both constants are provisional pending re-derivation against the first drawn capital
- [x] T032 [P] Add the capital tier to the load table in `.claude/skills/diagram/settlements.md` if its description still implies the tier is undesigned
- [x] T033 Run the cheap linters from `.claude/skills/diagram/`: `python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy` - all clean before any gate run
- [x] T034 Run the WHOLE affected test files from `.claude/skills/diagram/`: `python3 -m pytest test_citybudget.py test_checks.py -q -n auto --no-cov`. NEVER a `-k` subset - a hook enforces this, and the one time it was skipped a same-file test the filter missed cost a full gate cycle
- [x] T035 Confirm `test_tango_program_back_predicts_the_shipped_wall` and `test_shipped_city_programs_price_exactly_as_they_did_before_the_temple_knobs` pass UNMODIFIED - if either is red, stop and fix the code, never the expectation
- [x] T036 Run `make done` ONCE from `.claude/skills/diagram/`, backgrounded, as `cd <dir> && make done > /tmp/gate.log 2>&1` and nothing more - do not append `; echo EXIT=$?`, which makes a failed gate report exit 0. Act on the completion notification; never poll
- [x] T037 Verify the feature's CENTRAL CLAIM rather than asserting it: `git status --porcelain -- .claude/skills/diagram/pool/` MUST be EMPTY. Any dirty tracked manifest means a shipped map moved and the byte-identity claim is false
- [x] T038 Commit in the session clone and run the stop-work ritual: `scripts/sync-with-main.sh done` from the clone root

---

## Dependencies

```
Phase 1 (Setup)
    └─> Phase 2 (Foundational: constants + CapitalProgram)   [BLOCKS everything]
            ├─> Phase 3 (US1: plan_capital + wall + validator)  [MVP]
            │       ├─> Phase 4 (US2: report + CLI)   - needs a budget to print
            │       └─> Phase 5 (US3: knob validation) - needs the dataclass only,
            │                                            so it may run beside Phase 4
            └─────> Phase 6 (Polish + verification)   [needs all of the above]
```

- **US1 depends on** Phase 2 only. It is the MVP and is independently shippable.
- **US2 depends on** US1 (there must be a budget to format).
- **US3 depends on** Phase 2 only, so it can proceed in parallel with US2.
- **Phase 6** depends on everything.

## Parallel opportunities

- **T019-T022** (`check_village.py` + `test_checks.py`) touch different files from T009-T018 (`citybudget.py` + `test_citybudget.py`) and can run alongside them.
- **T030-T032** are three different documentation files.
- **US2 (Phase 4) and US3 (Phase 5)** can run concurrently once Phase 3 lands.
- Everything else is sequential: the TDD pairs are strictly ordered (test, then implementation), and most tasks in a phase share one file.

## Implementation strategy

**MVP is Phase 1 + 2 + 3.** That delivers the feature's whole reason to exist - a capital's wall derived from its declared program, and a capital manifest held to it. The report, the CLI and the knob validation are real requirements but they are additive polish on a working model.

**Ship increments in phase order.** Each checkpoint above is a coherent stopping point, and the byte-identity claim (T037) holds at every one of them, because nothing in this feature is on the provincial code path.

**One thing NOT in this feature, by design**: Principle XII's closing gate. It examines a rendered artifact and this feature renders nothing, so the obligation transfers to feature 019 against the first Shiro Daika PNG. See [plan.md](plan.md) Complexity Tracking and [quickstart.md](quickstart.md).
