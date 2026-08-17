# Feature Specification: One `l7r` Namespace Across the Repo - `l7r.diagram`, and a Shared `sitegen` for the Tiers Above Hamlet

**Feature Branch**: none - this project stays on `main` (CLAUDE.md, GM 2026-07-27). Active feature
is declared with `export SPECIFY_FEATURE=119-l7r-diagram-namespace` and
`export SPECIFY_FEATURE_DIRECTORY=specs/119-l7r-diagram-namespace`.

**Created**: 2026-08-17

**Status**: Draft

**Input**: GM, 2026-08-17: *"I thought it was possible to have different submodules in different
directories/locations with the same parent module like l7r.xxx despite being in different places.
Is that not correct? I would prefer an l7r prefix if possible. Does that work?"* - following the
architectural question *"I expect tiers to share libraries, and that hamletgen/ will presumably
become a submodule of a top-level module... then everything is underneath that, and then
l7r.diagram.hamletgen is where hamletgen/ ends up, and things which hamletgen/ has which are more
broadly general move into a different submodule."*

## Why this feature exists

The village tier is the next big step in `migration-plan.md`, and its section 5 flags the open
architectural question by name: *"Expect this to surface the architectural question of whether
`hamletgen/` generalizes or whether tiers share a stage library."* The GM has answered it - **tiers
share libraries** - and asked for the shared root to carry an `l7r` prefix.

Three things have to be true before the village generator is written, and none of them is village
work:

1. **The `l7r` prefix has to be available.** It currently is not: `/gm-assistant/webapp/l7r/` is a
   *regular* package, and a regular package terminates the import search. A second `l7r` elsewhere
   on `sys.path` does not merge with it - it is shadowed by whichever root comes first.
2. **The diagram engine has to live under that prefix**, so that the day the L7R Toolkit webapp
   wants to render a settlement map, `import l7r.diagram...` simply works instead of requiring a
   `sys.path` stunt between two colliding top-level packages named `l7r`.
3. **The tier-agnostic parts of `hamletgen/` have to have somewhere to go.** Today there is no
   package that means "generation machinery that is not about hamlets", so the village generator's
   only options would be to import from `hamletgen` (wrong direction) or to copy (worse).

Doing this **before** the village tier rather than after is a cost argument, not an aesthetic one.
Every import line, doc command reference and gate-config path this feature repaths is a line the
village tier would otherwise add to the same sweep - and the village generator's own diff stays
readable instead of being tangled with a repo-wide rename.

## The mechanism, verified rather than assumed

The GM's intuition is correct and the mechanism is **PEP 420 implicit namespace packages**. Verified
empirically before this spec was written, not recalled:

```
$ python3 -c "...two roots, l7r/diagram/__init__.py in one..."
namespace __file__: None | path: ['/tmp/tmpung_fvac/l7r']
```

A directory named `l7r` with **no `__init__.py`** on each of two `sys.path` roots produces a single
`l7r` whose `__path__` spans both, so `l7r.app` (from `/gm-assistant/webapp`) and
`l7r.diagram.hamletgen` (from the diagram skill directory) coexist under one parent.

**The one blocker is that the webapp's `l7r/__init__.py` is load-bearing**, not incidental:

```python
"""L7R Toolkit package. Importing this package wires the CherryPy tree. Used by `cherryd --import l7r`."""
from l7r import app  # noqa: F401 - side effect: mounts CherryPy tree
```

`cherryd --import l7r` (Dockerfile CMD, `make serve`), `webapp/conftest.py:10` and five character
tests all rely on bare `import l7r` having that side effect. A namespace portion cannot have an
`__init__.py`, so the mount has to move to an explicitly named module before the prefix is
shareable.

**`l7r.__file__ is None` is the property that distinguishes the two states**, which is what makes
the regression guardable: the failure mode of someone later adding an innocuous `l7r/__init__.py`
is *silent*. The other portion does not error at definition time; it simply stops existing, and
surfaces as a `ModuleNotFoundError` somewhere unrelated.

## Scope, measured in the clone

| surface | count |
|---|---|
| absolute engine imports to repath (`from settlement …`, `import check_village`, …) | **245 lines across 124 files** |
| pool + wip generator scripts importing the engine | **26** (of 28 gens) |
| markdown command references (`python3 -m check_village`, `-m pipeline.regen`, `-m tools.why_placed`) | **97 lines across 44 files** |
| webapp files touched by the namespace conversion | **~10**, none of them logic |
| `hamletgen/` lines that are tier-agnostic today | **~110 of 3,275** (revised down from an initial ~450 estimate by Phase 0 research R7 - see below) |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The `l7r` prefix becomes shareable (Priority: P1)

A session (or a future webapp feature) can put a second `l7r.*` portion anywhere on `sys.path` and
have it merge with the toolkit's rather than shadow it. The webapp's `l7r` becomes a namespace
portion: `l7r/__init__.py` is deleted, the CherryPy mount is reached as `l7r.app`, and everything
that relied on the bare-import side effect names the module it actually wants.

**Why this priority**: it is the blocker. Nothing else in this feature is possible while a regular
`l7r` package owns the name. It is also the only landing that touches the *deployed* application, so
it ships alone, behind its own gate and its own smoke check, where a failure cannot be confused with
a diagram failure.

**Independent Test**: with landings 2 and 3 not yet started, `make done` in `webapp/` is green,
`cherryd --import l7r.app` serves the site, and a scratch `l7r/` portion on a second `sys.path` root
imports successfully alongside `l7r.app`. That is a complete, valuable change on its own - it is
what makes the prefix available to anything, not just to `/diagram`.

**Acceptance Scenarios**:

1. **Given** the converted webapp, **When** `import l7r` runs, **Then** `l7r.__file__` is `None`
   (it is a namespace portion) and no CherryPy tree has been mounted as a side effect.
2. **Given** the converted webapp, **When** the server is started the way the Dockerfile starts it,
   **Then** the site serves and the landing page and at least one sub-page render.
3. **Given** the converted webapp, **When** `make done` runs, **Then** it is green including the
   100% coverage gate, with zero new failures against a detached-worktree baseline.
4. **Given** a second directory tree containing `l7r/scratch_portion.py` and no `__init__.py`,
   **When** both roots are on `sys.path`, **Then** `import l7r.app` and `import l7r.scratch_portion`
   both succeed in the same interpreter.

---

### User Story 2 - The diagram engine moves under `l7r.diagram` (Priority: P1)

A session working on the engine imports `from l7r.diagram.settlement import Settlement` and runs
`python3 -m l7r.diagram.check_village`. The eight engine units - `settlement/`, `check_village/`,
`waterfields/`, `hamletgen/`, `pipeline/`, `tools/`, `compound.py`, `citybudget.py` - move into
`l7r/diagram/` inside the skill directory. `pool/`, `tests/`, the `Makefile` and `pyproject.toml`
stay where they are, so the skill directory remains the `sys.path` root and the gate stays the
diagram gate.

**Why this priority**: it is the landing the GM actually asked for, and it is what makes the engine
importable from the webapp. It is P1 alongside story 1 rather than behind it because the two
together are the deliverable; separately, story 1 is only an enabler.

**Independent Test**: regenerate every `pool/` artifact in a scratch copy and hash it against a
pre-move baseline. A pure repath cannot change a single byte of output, so byte-identity is a
mechanical oracle rather than a judgment call - and the gate proves the toolchain configuration
followed the code.

**Acceptance Scenarios**:

1. **Given** the moved engine, **When** every `pool/` generator is regenerated in a scratch copy
   (frozen legacy maps included), **Then** every produced artifact is byte-identical to a pre-move
   baseline.
2. **Given** the moved engine, **When** `make done` runs in the skill directory, **Then** it is
   green - `ruff`, `ruff format --check`, `mypy --strict` over the repathed module list, the full
   test suite, 100% coverage on every measured module, and the `settlement/` ratchet floor.
3. **Given** any pool generator, **When** its `sys.path` bootstrap block is diffed, **Then** it is
   byte-unchanged; only its single engine-import line differs.
4. **Given** the repo's markdown, **When** it is grepped for `python3 -m check_village`,
   `python3 -m pipeline.`, `python3 -m tools.` and `python3 -m hamletgen`, **Then** every remaining
   occurrence names a module path that resolves.
5. **Given** the skill directory, **When** `import l7r` runs from it, **Then** `l7r.__file__` is
   `None`.

---

### User Story 3 - `sitegen` exists, and the rule for growing it is written down (Priority: P2)

A future village generator has a package to build on. The tier-agnostic pieces move out of
`hamletgen/` into `l7r/diagram/sitegen/`: the geometry helper set, the `Pt`/`Poly`/`SQ_FT_PER_ACRE`
types and units, and `default_jobs`. `hamletgen` keeps every stage whose content is about hamlets,
and its public surface (`HamletSpec`, `generate`) does not move, so no pool generator changes.

**Revised by Phase 0 research (R7).** This story originally also claimed `frame.py` and the
driver's `Report`. Reading the dependency edges refuted that: `frame.py`'s three members are all
`stage_*(s, plan: SitePlan)` and it imports `CROP_MARGIN` from `hinterland`, and `Report` wraps
`SitePlan` to print a hamlet cohort row. Both stay. The extraction is ~110 lines, not ~450 - and
that is the correct size for a first extraction, because the remaining candidates move under the
MOVE-don't-copy rule when the village tier makes them their second real consumer, rather than being
predicted now.

**Why this priority**: it is the smallest landing and the one with the least mechanical certainty
about *where* the seam falls, so it ships last, after the two moves whose oracle is exact. It is
still in scope because without it the village tier has nowhere to import from.

**Independent Test**: with the move already landed, extract and re-run the same byte-identity oracle
plus the gate. Identical artifacts prove the extraction preserved behavior; the gate proves the
coverage and typing followed.

**Acceptance Scenarios**:

1. **Given** `sitegen`, **When** its modules are read, **Then** none of them mentions households,
   paddies, hamlet bands or any other tier-specific concept - a module that does belongs in
   `hamletgen`.
2. **Given** `sitegen`, **When** the pool byte-identity sweep runs, **Then** every artifact is
   byte-identical, the four scripted hamlets included.
3. **Given** `migration-plan.md` and `hamletgen/CLAUDE.md`, **When** a session reads them before
   writing the village generator, **Then** both state the standing rule: a hamlet stage that a later
   tier needs is **MOVED** into `sitegen`, never copied.
4. **Given** `migration-plan.md` section 5, **When** it is read, **Then** it records the
   architectural question as ANSWERED (tiers share a library) rather than as open.

---

### Edge Cases

- **A stray `__init__.py` re-added later.** The whole feature rests on two directories NOT having
  one, and adding one is a natural, innocent-looking act. Silent failure: the other portion stops
  existing with no error at the point of the mistake. Guarded by an assertion in each portion's
  test suite, and the assertion must be proven RED by actually creating the file.
- **`__pycache__` shadowing the old layout.** A stale `settlement/__pycache__` at the old path can
  keep an import resolving after the source has moved. The move must delete the old trees outright,
  and the byte-identity sweep must run in a scratch copy taken from the committed tree.
- **`mypy --strict` and namespace packages.** `[tool.mypy] files` currently names bare packages
  (`settlement`, `check_village`, …). Under a namespace root mypy may need explicit package bases to
  resolve `l7r.diagram.*` without inventing a second module identity for the same file - the classic
  symptom being a module reported twice under two names.
- **Coverage source names.** `[tool.coverage.run] source` names modules deliberately, one by one, so
  that a new tool does not silently inherit the 100% obligation. That property must survive the
  repath - the list becomes longer, not looser.
- **A pool generator's bootstrap depending on directory depth.** Each gen computes
  `SKILL = dirname(dirname(HERE))` from its own location. Because `pool/` does NOT move, that
  arithmetic stays correct; if `pool/` were moved under `l7r/`, every gen's bootstrap would silently
  point one level wrong.
- **The frozen legacy pool.** Frozen gens are never re-run, but their import lines still have to be
  repathed or they become permanently unrunnable. They are edited and included in the byte-identity
  sweep via the frozen-inclusive path, exactly as feature 118 did - a sweep that honored the freeze
  would exercise most of the pool not at all.
- **Two `l7r` portions with asymmetric depth.** The webapp's modules sit directly in the namespace
  (`l7r.app`) while the diagram's nest one level (`l7r.diagram.settlement`). This is legal and
  intended; tidying the webapp to `l7r.toolkit.*` is explicitly out of scope.
- **A concurrent session editing the engine.** Three other diagram sessions are live. This feature
  repaths every engine import in the repo, so it is a textual conflict magnet; it wants a short
  wall-clock and a prompt push rather than a long-running clone.

## Requirements *(mandatory)*

### Functional Requirements

**Landing 1 - webapp namespace conversion**

- **FR-001**: `webapp/l7r/__init__.py` MUST be deleted, making `webapp/l7r/` a PEP 420 namespace
  portion.
- **FR-002**: The CherryPy tree-mounting side effect MUST be reachable by importing a named module
  (`l7r.app`), and every caller that relied on bare `import l7r` MUST name that module instead -
  `conftest.py` and the five character tests included.
- **FR-003**: The Dockerfile CMD and the Makefile `serve` target MUST invoke `cherryd` with the
  module that mounts the tree.
- **FR-004**: `pytest --cov=l7r` MUST continue to measure the same modules at 100%.
- **FR-005**: No route, template, or behavior of the toolkit may change.

**Landing 2 - diagram engine under `l7r.diagram`**

- **FR-006**: `settlement/`, `check_village/`, `waterfields/`, `hamletgen/`, `pipeline/`, `tools/`,
  `compound.py` and `citybudget.py` MUST move to `l7r/diagram/` within the skill directory, with
  `l7r/` carrying no `__init__.py` and `l7r/diagram/` carrying one.
- **FR-007**: `pool/`, `tests/`, `Makefile` and `pyproject.toml` MUST stay at the skill root, and
  every pool generator's `sys.path` bootstrap block MUST be byte-unchanged.
- **FR-008**: All 245 absolute engine-import lines MUST be repathed, with no module importable
  under two names.
- **FR-009**: `pyproject.toml` MUST be repathed in all four places that name modules by path: the
  ruff per-file-ignores, the mypy `files` list, the coverage `source` list, and the coverage `omit`
  patterns. The Makefile's coverage include/omit globs MUST still select the intended trees.
- **FR-010**: All **live-doc** markdown command references (39 lines across 13 files) MUST be
  updated to module paths that resolve. No compatibility shim or alias module may be introduced to
  avoid this - a shim would leave two live names for one module, which is the specific thing the
  namespace exists to prevent. Historical `specs/NNN-*/` artifacts MUST NOT be rewritten: they are
  dated records of what was true when each feature shipped, not live mirrors (research R6).
- **FR-011**: Every directory-level `CLAUDE.md` index that states where engine code lives MUST be
  updated, the skill's own "Where things live" table included.

**Landing 3 - `sitegen`**

- **FR-012**: A `l7r/diagram/sitegen/` package MUST hold the tier-agnostic machinery extracted from
  `hamletgen/`: the geometry helper set (`geom.py`), the `Pt` / `Poly` / `SQ_FT_PER_ACRE` types and
  units, and `default_jobs`. Every member MUST move VERBATIM, comments included. A module that
  names any tier concept MUST NOT be in `sitegen`, and `sitegen` MUST NOT import `hamletgen` - the
  import direction is one-way and is asserted by a test.
- **FR-013**: `hamletgen`'s public surface (`HamletSpec`, `generate`, its `__main__` CLI) MUST NOT
  move, and no pool or wip generator may need changing for this landing.
- **FR-014**: The hamlet-specific stage modules (`water`, `sink`, `ways`, `cluster`, `homesteads`,
  `hinterland`) and the `STAGES` ordering MUST stay in `hamletgen` - the stage ORDER is the hamlet
  design, not shared machinery.
- **FR-015**: `migration-plan.md` (sections 5 and 8) and `hamletgen/CLAUDE.md` MUST record the
  answered architectural question and the MOVE-don't-copy rule, at the place a village-tier session
  will actually read them.

**Cross-cutting**

- **FR-016**: Each namespace portion MUST carry a test asserting its parent package is still a
  namespace, and each assertion MUST be proven RED against a real `__init__.py` before it is
  trusted.
- **FR-017**: Every `pool/` artifact MUST regenerate byte-identically against a baseline taken on
  unmodified code in a **detached worktree**, never by stashing.
- **FR-018**: Both gates - `webapp/make done` and the diagram `make done` - MUST be green with zero
  new failures against that baseline (constitution Principle XIII).

### Key Entities

- **Namespace portion**: a directory named `l7r` with no `__init__.py`, contributing its contents to
  the shared `l7r.__path__`. Identified by `l7r.__file__ is None`.
- **Regular package**: a directory with an `__init__.py`. `l7r/diagram/` is one; `l7r/` must not be.
- **Engine unit**: one of the eight top-level modules/packages that moves in landing 2.
- **Tier-agnostic module**: a module with no concept from any one settlement tier in it - the test
  for `sitegen` membership.
- **Byte-identity oracle**: the pool-wide regeneration-and-hash comparison that makes a pure
  repath's correctness mechanical rather than reviewed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `import l7r.app` and `import l7r.diagram.settlement` succeed in one interpreter with
  both roots on `sys.path` - the capability that does not exist today at all.
- **SC-002**: Every `pool/` artifact regenerated after each landing is byte-identical to the
  pre-feature baseline - 100%, live and frozen generators alike.
- **SC-003**: Both `make done` gates are green with zero new failures against the detached-worktree
  baseline.
- **SC-004**: Zero remaining references to the old module paths anywhere in the repo's Python or
  markdown - measured by grep, not by inspection.
- **SC-005**: Both namespace guard assertions have been observed to FAIL against a real
  `__init__.py` and to pass without one.
- **SC-006**: `hamletgen/` shrinks by the extracted machinery and every remaining module in it names
  a hamlet concept; `sitegen/` names none.
- **SC-007**: A session reading `migration-plan.md` before starting the village tier finds the
  architecture question answered and the MOVE-don't-copy rule stated, without needing this spec.

## Assumptions

- **The oracle is byte-identity, not judgment.** All three landings are behavior-preserving by
  construction, so artifact drift is a bug rather than a trade-off. As with feature 118, this is why
  no `settlement-review` pass is required: a change that cannot alter output has a mechanical
  oracle. If any map does drift, the feature stops and the drift is diagnosed - it is not reviewed
  and accepted.
- **The frozen legacy pool is included in the sweep.** Frozen gens are edited (import lines) and
  swept, following 118's precedent.
- **`webapp/l7r` stays flat.** Restructuring the toolkit to `l7r.toolkit.*` for symmetry with
  `l7r.diagram.*` is a real option and explicitly deferred; it buys tidiness, not capability.
- **The diagram gate stays separate from the webapp gate.** Two `pyproject.toml`s, two `make done`s,
  two coverage regimes. Sharing a namespace is not sharing a build.
- **No `pip install -e`.** The `sys.path`-root arrangement is retained; converting either tree to an
  installed distribution is out of scope and would change how every pool generator bootstraps.
- **The webapp does not gain a map-rendering feature here.** This feature makes that possible; it
  does not build it.
- **`sitegen`'s membership is decided conservatively.** Only modules with no tier concept move in
  landing 3. Anything arguable stays in `hamletgen` and moves later under the MOVE-don't-copy rule,
  when the village tier gives it a second real consumer - extraction on the second use, not the
  first, so the seam is observed rather than predicted.
- **Three sibling sessions are live** in other clones. This feature's diff is repo-wide and textual,
  so it is sequenced to land promptly rather than to sit.
