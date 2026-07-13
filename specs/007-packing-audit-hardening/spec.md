# Feature Specification: Packing-Audit Hardening + Ochiba SE Consolidation

**Feature branch:** `007-packing-audit-hardening`
**Status:** Draft (awaiting GM approval to plan/implement)
**Input:** GM caught a ~1,760 sq ft empty rectangle (73 x 24 ft) below Ochiba's
granary that the packing check + size-audit subagent had waved through as a
"granary cart apron." The check surfaced the gap but the metric landed on the
legitimate forecourt, the global coverage average hid the local hole, and the
subagent rationalized the void without quantifying it.

## User Scenarios & Testing *(mandatory)*

The "user" here is the GM reviewing a Mode A compound plan, and the size-audit
subagent that runs `pack_audit.py` on their behalf.

### User Story 1 - A big secondary empty region cannot hide behind the forecourt (Priority: P1)

When a compound has more than one large vacant region, the packing report must
surface all of them, not just the single largest. Today `pack_audit.py` reports
only the one biggest vacant rectangle; on Ochiba that was the legitimate entry
forecourt (115 x 26 ft), so the nearly-as-large SE void (73 x 24 ft) never
appeared as a headline and got no scrutiny.

**Acceptance:** running the hardened `pack_audit.py` on Ochiba (pre-fix) lists
BOTH the forecourt rectangle AND the SE-void rectangle among its top vacant
regions, each with its size, location, and orientation.

### User Story 2 - Local sparsity is visible even when global coverage is in-band (Priority: P1)

A compound can be ~37% built overall (in the historical jin'ya band) while one
quadrant is ~68% empty. The report must expose that local unevenness so a
locally-sparse region is not masked by a healthy global average.

**Acceptance:** the report includes a per-region (tiled) coverage breakdown;
Ochiba's SE region reads as markedly sparser than the compound average, and the
size-audit sweep is instructed to treat a large low-density region as a
consolidation candidate, not a pass.

### User Story 3 - "It's an apron / a forecourt" must be defended with a number (Priority: P2)

When the size-audit subagent clears a large empty region by naming its function
(cart apron, forecourt, oshirasu, court), it must state the historical size that
function warrants (a cart-and-oxen loading apron is ~15-20 ft deep; a forecourt
is sized for assembly) and confirm the drawn region is within it. An unquantified
function label may not clear an oversized void.

**Acceptance:** the size-audit PACKING sweep output requires, for every empty
region it declares a feature, a one-line "warrants ~N ft because <function>"
justification; a 24 ft-deep loading apron fails this and is flagged.

### User Story 4 - Ochiba's SE is consolidated; the check confirms it green (Priority: P1)

The cell and barracks (currently shoved against the south wall with a ~24 ft void
above them) are pulled up into a coherent SE range against the granary, leaving a
real ~15 ft loading apron, not a 73 x 24 ft void. The envelope and coverage are
unchanged (no wall moved).

**Acceptance:** after the fix, the hardened `pack_audit.py` shows no large
low-density SE region and no 20+ ft-deep empty rectangle that isn't a justified
forecourt; the size-audit subagent returns a clean PACKING sweep; the envelope
(267 x 200 ft) and ~37% coverage are unchanged.

### User Story 5 - pack_audit.py meets Python Discipline (Priority: P1)

`pack_audit.py` is production-quality tooling, so it must pass all five Principle
X gates: ruff check, ruff format --check, mypy --strict, pytest, and 100% line
coverage on its pure logic. Its geometry (coverage, maximal-rectangle, top-N
vacant regions, per-region density, aligned gaps) is pure logic and gets
unit tests written test-first.

**Acceptance:** `ruff check`, `ruff format --check`, `mypy --strict`, and
`pytest --cov-fail-under=100` all pass on `pack_audit.py` + `test_pack_audit.py`.

### Edge Cases

- A compound with a genuinely large legitimate forecourt (e.g., Ochiba's 115 x 26
  ft entry apron) must NOT be flagged after the fix - the check distinguishes a
  justified forecourt from undifferentiated slack (by size-vs-function, per US3).
- A compound with an annex (Hayakawa) - the interior mask must include the annex
  rect(s), and per-region tiling must handle a non-rectangular interior.
- Point glyphs (wells, fire-water tubs, latrines) count as occupied so they are
  not mistaken for empty ground, but do not count as "buildings" for coverage.
- A degenerate SVG (no interior rect) must fail loud, not silently mis-report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-1** `pack_audit.py` reports the **top-N (>=3) vacant rectangles**, each
  with area, width x height in ft, orientation, and location.
- **FR-2** `pack_audit.py` reports a **per-region coverage breakdown** (interior
  tiled into a small grid, e.g. 3x3 or quadrants), so a locally-sparse region is
  visible against the global average.
- **FR-3** The report keeps the existing headline coverage %, purposeful-open %,
  and aligned-gap list (behavior preserved).
- **FR-4** The size-audit PACKING / WHITESPACE sweep is updated so that (a) it
  reads the top-N vacant regions and the per-region density, and (b) any empty
  region cleared as a "feature" carries a quantified `warrants ~N ft because
  <function>` justification; an unquantified or over-size void is flagged.
- **FR-5** Ochiba's cell + barracks (and their attached fixtures) are repositioned
  into a coherent SE range with a ~15 ft granary apron; no compound wall moves;
  coverage stays ~37%.
- **FR-6** `pack_audit.py` is refactored so pure-logic geometry is importable and
  unit-testable, separate from file I/O and CLI printing.
- **FR-7** `pack_audit.py` carries full type annotations and passes `mypy --strict`.
- **FR-8** A `pyproject.toml` ruff config exists and `ruff check` + `ruff format
  --check` pass on `pack_audit.py`.
- **FR-9** `test_pack_audit.py` gives 100% line coverage of `pack_audit.py`'s pure
  logic, written test-first (red before green), with behavior-named parametrized
  tests and small synthetic fixtures (not the pool maps).
- **FR-10** The coverage source/config is extended so `pack_audit` is in the
  100%-coverage gate alongside `check_village`/`settlement`, without forcing an
  untimely full retrofit of the existing untyped Mode B modules (scope decision
  recorded in plan).
- **FR-11** Grounding/notes/memory updated per project policy (the "why" of the
  top-N + local-density rules; the Ochiba SE fix logged; the size-audit
  quantify-the-apron rule recorded as a validated example).

### Key Entities

- **Compound SVG** - hand-authored Mode A plan; parsed for the interior rect(s),
  building rects (by fill/pattern), open-feature rects (garden, oshirasu), and
  point glyphs.
- **Vacant rectangle** - a maximal all-empty axis-aligned rectangle in the
  interior; now a ranked list, each with area/dims/orientation/location.
- **Region density** - coverage % within each tile of a grid over the interior.
- **Aligned gap** - unchanged: two stacked buildings with empty between them.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-1** Running hardened `pack_audit.py` on the PRE-fix Ochiba surfaces the SE
  void (73 x 24 ft) in its top-N vacant list AND shows the SE region's local
  coverage far below the 37% average (red state reproduced).
- **SC-2** After the SE consolidation, no unjustified empty rectangle >~20 ft deep
  remains, and the SE region's local coverage rises into a plausible band; the
  size-audit PACKING sweep returns clean (green state).
- **SC-3** `ruff check`, `ruff format --check`, `mypy --strict`, `pytest`,
  `pytest --cov-fail-under=100` all pass on the pack_audit module + its tests.
- **SC-4** Ochiba's envelope (267 x 200 ft) and global coverage (~37%) are
  unchanged; Hayakawa re-checked and unaffected.
- **SC-5** The size-audit subagent, re-run on the fixed Ochiba, no longer clears a
  20+ ft loading apron and documents the quantified justification for any region
  it keeps.

## Assumptions

- The historical band already established stands (jin'ya coverage ~37-42%;
  forecourt/oshirasu ~12-18% of site; loading apron ~15-20 ft deep; kura
  fire-gap ~6-10 ft). No new historical research is required beyond confirming the
  loading-apron depth figure.
- The fix is repositioning existing buildings within the fixed envelope (no wall
  moves, no resize), so no coverage-band or envelope re-validation is needed.
- Retrofitting `check_village.py`/`settlement.py` to ruff+mypy is OUT of scope
  (they hold the Principle X grace period and already have tests+coverage); this
  feature brings only the new `pack_audit.py` to full compliance. (Confirm in plan.)
