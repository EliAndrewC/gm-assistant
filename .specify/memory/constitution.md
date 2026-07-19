<!--
SYNC IMPACT REPORT
==================
Version change: 1.4.0 → 1.4.1
PATCH: Principle XII gains a "calibrated liberty" clause (GM, 2026-07-19) -
where research shows a thing is plausible but the DEGREE is genuinely unclear,
a favorable reading within the plausible range may be chosen deliberately, on
condition that the choice and its range are disclosed in research.md and beside
the rule in code. Conjunctive conditions; does not license inventing a range or
overriding a finding that is actually clear. Also CORRECTS a factual claim in
XII's own motivating example: the 桑基魚塘 dike-pond system did NOT replace
rice across whole districts as the norm - the mixed scatter was normal, and the
principle's opening gate caught the error on its first outing (feature 010).

PRIOR (1.3.0 → 1.4.0):
MINOR: Principle XII (Historical Grounding Bookends) ADDED - any feature that
changes what a generator asserts about the world must open with a historical-
grounding analysis and close with a verification of the RENDERED ARTIFACT.
Motivated by the /diagram `rape` land-use overlay, which passed every
automated check and its tests while depicting two seasons of one crop
rotation standing simultaneously; only looking at the picture caught it.

PRIOR (1.2.0 → 1.3.0):
Principle I (Accessibility-First Viewports) materially expanded
to require scroll-through verification and to forbid column-height
asymmetry past 2.5× ratio. The added requirements were already implicit
in the principle's intent but had been missed in practice because no
artifact captured them - the new dom_audit layout-balance rule + the
multi-scroll contact sheets in screenshot.py now enforce them.

Principles (12) - Principle XII added; Principle I previously expanded:
  I.   Accessibility-First Viewports (NON-NEGOTIABLE)        [EXPANDED]
  II.  Bold, Intentional Design                              [unchanged]
  III. Pool Data Conventions                                 [unchanged]
  IV.  One Canonical Home for GM Source                      [unchanged]
  V.   Protecting the GM's Writing (NON-NEGOTIABLE)          [unchanged]
  VI.  Verify Before Reporting Done                          [unchanged]
  VII. De-Localized Generation by Default                    [unchanged]
  VIII.Direct Voice Over Framing Distance                    [unchanged]
  IX.  Setting Integration                                   [unchanged]
  X.   Python Discipline (NON-NEGOTIABLE)                    [unchanged]
  XI.  Japanese Authenticity (NON-NEGOTIABLE)                [unchanged]
  XII. Historical Grounding Bookends (NON-NEGOTIABLE)        [ADDED]

Sections updated:
  - Core Principles: Principle I expanded with layout-balance + scroll-
    through-review rules.
  - Development Workflow (operational mirror in CLAUDE.md): contact-sheet
    artifact + persona-based review now required for UI changes.

Templates requiring review/update:
  ✅ webapp/tests/screenshot.py - produces multi-scroll contact sheets.
  ✅ webapp/tests/dom_audit.py - adds layout-balance rule (sibling-height
                              ratio cap inside flex/grid containers).
  ✅ /gm-assistant/.claude/agents/frontend-review.md - new independent
                              reviewer agent (Constitution mirror).
  ⚠  .specify/templates/plan-template.md - Constitution Check entry
                              for Principle I should now mention "no
                              dead-space; contact sheet attached".
                              Deferred until next /speckit-specify run.

Deferred TODOs: none.

------------------------------------------------------------
Version 1.2.0 history (amended 2026-05-27):
  Principle XI (Japanese Authenticity) added covering kanji ↔ romaji ↔
  meaning alignment.

Version 1.1.0 history (amended 2026-05-27):
  Principle X (Python Discipline) added; Technical Standards / Workflow
  expanded with concrete tooling (ruff, mypy, pytest-cov, uv pip compile,
  configobj, pydantic-settings).

Version 1.0.0 history (initial ratification on 2026-05-27):
  Introduced Principles I-IX, the Technical Standards / Development
  Workflow / Governance sections, and the Constitution Check gate in the
  plan template.
-->

# L7R Toolkit Constitution

This constitution governs the L7R toolkit project - a working setup of Claude
Code skills, generated content pools, and a forthcoming webapp frontend for a
custom Legend of the Five Rings tabletop RPG setting. It is the highest-level
guide for how Claude Code agents and human contributors collaborate on this
codebase. All specifications, plans, implementations, and reviews MUST comply
with the principles below.

## Core Principles

### I. Accessibility-First Viewports (NON-NEGOTIABLE)

The GM uses Chrome at 200% browser zoom on a 1850×1173 outer window
(effective CSS viewport ≈ 925×525). All UI work - webapp pages, generated
HTML, embedded previews - MUST be verified at the GM's actual viewport at
**both 100% and 200% zoom** before being declared done.

The following are **clipping** violations:
- Text truncated by `text-overflow: ellipsis` where the truncated portion
  carries information (clan names, named entities, type descriptors, etc.).
- Text or visuals clipped by `overflow: hidden` because a child exceeded
  its container's width or height.
- Elements whose `scrollWidth` or `scrollHeight` exceeds their corresponding
  `offsetWidth` or `offsetHeight` (excluding intentional internally-scrollable
  regions).
- Sticky / fixed elements that occupy more than ~25% of the 200%-zoom viewport
  height without strong justification.
- Tap/click targets smaller than 32×32 CSS pixels.
- Body / paragraph text smaller than 1rem; small-caps labels smaller than
  0.7rem.

The following are **balance** violations (added in v1.3.0):
- Inside a horizontal flex or grid container ≥600px wide with two or more
  visible children, sibling-element heights MUST NOT differ by more than
  **2.5×** when the taller sibling exceeds 200px. (The original failure
  mode: a short hero column beside a tall card stack produces a column of
  dead space below the hero when the user scrolls. Either bring the
  short column up in height or stack the layout vertically.)
- A vertical region larger than **30% of the viewport height** that is
  empty of content, decoration, or intentional negative space (no
  watermark, no rule, no whitespace clearly serving the composition) is
  itself a violation. Empty space is allowed only as a designed element.

A UI change is not complete until the verification workflow has produced:
  (a) **screenshots at the four standard viewports** (GM-100 1850×1050,
      GM-200 925×525, tablet 800×1100, mobile 390×844), captured as
      **multi-scroll contact sheets** for any page taller than 1.3× the
      viewport so mid-scroll layout is visible;
  (b) a **zero-issue DOM-audit report** covering both clipping and
      layout-balance rules above;
  (c) a **persona-driven review pass**: the reviewer (whether the same
      agent, the GM, or the frontend-review subagent at
      `.claude/agents/frontend-review.md`) MUST consider the page from
      the user's perspective ("Eli is opening this page; what is he
      trying to do here?") rather than as a static visual artifact.

The author of a UI change SHOULD NOT also be the sole reviewer. Where
practical, route the contact sheet to the frontend-review subagent for an
independent pass. The author rationalizes choices the reviewer would not.

### II. Bold, Intentional Design

Frontend work uses the official `frontend-design` Claude Code plugin and
follows its discipline: commit to a clear aesthetic direction per page,
avoid timid neutrals and generic AI aesthetics, and reject default typefaces
that no longer carry character (Inter, Roboto, Arial, system sans). Where the
content is Japanese-themed, the typographic system MUST pair a distinctive
display serif with a refined body serif and a Japanese mincho face; the
current canonical pairing is **Fraunces + EB Garamond + Shippori Mincho**.

A coherent palette is preferred to a balanced one: dominant tone, sharp
accent, intentional negative space. The current canonical palette is warm
washi paper, sumi ink, and vermillion accent (`#F4E8CC` / `#14110E` /
`#B8332A`). Deviations are permitted but MUST be deliberate, not accidental.

### III. Pool Data Conventions

Generated content of a kind that recurs (relics, names, vows, swords, etc.)
lives as individual markdown files with YAML frontmatter, organized into
per-category directories under `/.claude/skills/<skill>/pool/<category>/`.
Each entry's frontmatter MUST carry the fields needed for scriptable
filtering - at minimum a category slug (e.g. `fortune`) and a clan
designator (`clan: any | crab | crane | ...`).

Pool entries MUST be reusable across campaigns. They MUST NOT bake in
specific cities (`Kyuden X`, `Shiro X`, `Shinden X`) either in frontmatter
or prose. Where a clan-level designation is appropriate, use that (e.g.
"a temple of Ebisu in Crab lands"); where no clan is implied by the named
entity, use `clan: any`.

### IV. One Canonical Home for GM Source

Each piece of GM source content - text inside `<!-- SOURCE: GM NOTES - DO
NOT MODIFY -->` markers - has exactly **one** canonical home file. Other
files that need that content reference it by path and section rather than
duplicating the SOURCE block. This keeps canonical-source syncs surgical:
when the GM updates their notes, only one downstream file must change per
concept, and drift between duplicate copies is impossible.

When deciding where a source block belongs:
- Generation guidance (how to write a kind of thing, with worked examples)
  belongs in the relevant skill's `SKILL.md`.
- Setting reference (demographics, geography, hierarchies, fixed facts)
  belongs in a file under the relevant reference directory.
- If both, place it where the content leans heavier and have the other
  side reference.

**Exception:** `/notes/canonical-source.txt` is a sync diff baseline; it
intentionally mirrors the GitHub canonical source and is the one duplicate
the system requires.

### V. Protecting the GM's Writing (NON-NEGOTIABLE)

Content between `<!-- SOURCE: GM NOTES - DO NOT MODIFY -->` and
`<!-- END SOURCE -->` markers is the GM's original writing. It MUST NEVER
be modified, rephrased, summarized, reworded, or "improved" by any agent.
Only the GM may edit those sections, and only when they explicitly
instruct an agent to do so.

The sole automated exception is the canonical-source sync workflow
documented in `/gm-assistant/CLAUDE.md`: when the GM has updated their
GitHub notes, downstream SOURCE blocks MUST be updated to match exactly.

AI-generated content (preferences, generation instructions, examples of
liked/disliked output, scaffolding, layout text) lives outside SOURCE
markers and MAY be updated freely.

### VI. Verify Before Reporting Done

No agent or skill may report a task complete without verifying the actual
artifacts. Specifically:

- **Python skills**: Run `pytest` for the relevant skill directory. Target
  100% line coverage on pure logic. External boundaries (HTTP, browser
  sessions, third-party APIs) are tested via saved fixtures, not via
  transport-layer mocks.
- **UI changes**: Run the Playwright screenshot suite at the four standard
  viewports (GM-100, GM-200, tablet, mobile) AND a DOM-overflow audit
  (`scrollWidth/scrollHeight > offsetWidth/offsetHeight`, computed
  `text-overflow: ellipsis` truncation, `-webkit-line-clamp` clipping).
  Both MUST be clean before the change is reported as done.
- **Delegated work**: When a subagent or skill reports completion, the
  caller MUST spot-check the artifacts (read a sample of changed files,
  run a verification query) before relaying the result to the user.
  "The agent said it was done" is not sufficient.

Trust-but-verify is the working mode. Reporting a thing as done without
verification is a constitutional violation, not just a quality issue.

### VII. De-Localized Generation by Default

When generating an instance of a kind that the pool already organizes
(relics, names, temples, vows, etc.), the default framing is generic and
reusable: no specific city, no campaign-tied named samurai, no fixed
geographic coordinates. Use clan-level designators in temple / location
fields; let named entities sit at the family or peasant level rather than
the household level when no specific household is requested.

Specific scoping (Kyuden X, the Reiji domain, named PCs/NPCs, specific
campaign hooks) is permitted only when the user explicitly requests it.
When the user gives a specific scoping for in-session use, the resulting
content is for that session - it does not enter the pool until it has
been de-localized.

### VIII. Direct Voice Over Framing Distance

When writing in-world content - especially relic descriptions, vows, temple
material, and other quasi-religious or institutional writing - the
institution's own voice is used as direct statement of fact. Avoid
meta-narrational framings that hold the supernatural at distance:

- ❌ "The temple holds that the staff glows when Bishamon's favor is upon
  the inquirer."
- ✓ "The staff glows when Bishamon's favor is upon the inquirer."

- ❌ "Tradition says that a bandit who waylays a traveler within sight of
  the cord is tagged."
- ✓ "A bandit who waylays a traveler within sight of the cord is tagged."

Phrases to avoid: *"the temple holds that…," "tradition says that…,"
"the monks understand that…," "skeptics report no effect," "the temple
acknowledges privately that…"*

The supernatural ambiguity that the GM's setting cultivates lives in the
**layered evidence** (each piece of "proof" individually thin) and the
**unfalsifiability of soft claims** ("may," "are graced with," "some
pilgrims find"), NOT in distancing language about belief vs. skepticism.
Failure modes range from comfortable to harmful proof; the institution's
voice asserts what its own theology says, not what it "thinks."

### IX. Setting Integration

When generating content, draw on the GM's source notes under `/setting/`,
`/cosmology/`, `/campaigns/`, etc. for tone, style, and setting details.
Setting facts that are established in those notes MUST NOT be contradicted.

Skills SHOULD cross-reference reference directories rather than duplicate
their content. The CLAUDE.md files inside reference directories serve as
indexes - consult them before writing new content of an indexed kind, and
update them when adding new files.

When a relic, vow, or temple references a Fortune, clan family, lineage,
or setting figure, the reference MUST match the canonical setting as
established in `/cosmology/`, `/setting/`, and `/campaigns/`. New named
figures invented during generation MUST NOT collide with names already
in the campaign-names cache (see `/.claude/skills/name/campaign-names.txt`)
or with established figures in the GM's notes.

### X. Python Discipline (NON-NEGOTIABLE)

Python code in this project - the chargen webapp, the skill helpers, the
forthcoming backend service - MUST meet the following standards. Failing
any single rule is reason enough to refuse "done" status.

1. **Lint passes**: `ruff check` MUST pass on all production paths. The
   ruff configuration lives in a versioned `pyproject.toml`. Ruff is the
   single canonical lint tool (replaces flake8 / isort / pyupgrade /
   pylint); do not run alternatives alongside it.

2. **Format is canonical**: `ruff format --check` MUST pass. Ruff format
   is the single formatter (replaces black / autopep8); do not run
   alternatives alongside it.

3. **Type checking is strict**: `mypy --strict` MUST pass on production
   modules. Public functions and methods carry full type annotations.
   Existing chargen code that predates this principle has a one-time
   grace period to migrate; new code does not.

4. **Red-green TDD**:
   - New non-trivial behavior is introduced **test-first**: the test
     exists and fails (red) before the implementation lands (green).
   - Bug fixes begin with a failing test that reproduces the bug.
   - Trivial code (one-line accessors, dataclass declarations, plain
     data transforms with no logic) is exempt.
   - In the commit history, where practical, a `test:` commit precedes
     or accompanies the `feat:` / `fix:` commit. Solo iteration may
     squash these; the principle is the order of work, not the shape of
     the history.

5. **100% line coverage on pure logic**: `pytest --cov-fail-under=100`
   is the enforcement gate for pure-logic packages. External-boundary
   modules (HTTP clients, browser sessions, Claude API calls, DB
   sessions, file I/O against external services) test against **saved
   fixtures** of real responses, not transport-layer mocks. Fixtures
   live in a `fixtures/` directory alongside the tests.

6. **Pinned dependencies**: `requirements.txt` is generated from
   `requirements.in` via `uv pip compile` (or `pip-compile`). Installing
   a package without updating the source-of-truth file is a violation.
   `development-secrets.ini` and similar secret-bearing files MUST stay
   gitignored.

7. **No swallowed exceptions in production code**: bare `except:` or
   `except Exception: pass` are forbidden. Always re-raise, log
   specifically, or handle a known exception type explicitly.

8. **No `print` in production code**: use `logging.getLogger(__name__)`.
   `print` is permitted in scripts and one-off dev tools; banned in
   library and service code that other modules import.

9. **Test names describe behavior, not implementation**: prefer
   `test_picks_random_name_when_no_filters_given` over
   `test_pick_name_1`. The intent of the test should read off the name.

10. **`pytest.parametrize` for variant inputs**: prefer a single
    parametrized test over a family of near-identical tests. The
    parameter list documents the variation surface explicitly.

11. **Configuration over hardcoding**: Runtime configuration uses
    ConfigObj INI files (validated by `configspec.ini`) for chargen and
    other legacy paths; pydantic-settings for env-var-driven new code.
    Magic strings and environment-dependent constants MUST NOT be
    hardcoded in production paths.

### XI. Japanese Authenticity (NON-NEGOTIABLE)

Any content this project generates or surfaces in Japanese script - relic
names, sword names, given names, place names, temple titles, vow refrains,
filter labels, decorative kanji - MUST satisfy a three-way alignment:

1. **The kanji are real Japanese characters.** Not Chinese-only characters
   absent from Japanese use, not invented glyphs, not mojibake. Each
   character must be one a Japanese reader could parse.

2. **The romaji is a plausible reading of the kanji.** A native speaker
   reading the kanji aloud could arrive at the romaji. On-yomi vs kun-yomi
   compounds are both acceptable; sokuon / rendaku contractions (e.g.,
   `鉄 + 旋 → tessen`) are acceptable; truly non-existent readings are not.
   The project's romaji convention strips long-vowel macrons (`ō` → `ou`,
   `ū` → `uu`); follow that style for consistency.

3. **The English name connects to the kanji's meaning.** Not necessarily a
   literal gloss - poetic translation is welcome - but a reader who knew
   what the kanji meant should be able to see the connection. "The Half-
   Mirror" rendered as `別れ鏡 / Wakare-Kagami` ("Parting Mirror") works:
   the English name takes the kanji's image and renders it idiomatically.
   `五代 / Goshu` would not work: the romaji simply does not match.

**Compound nouns** SHOULD be real Japanese words where possible. Constructed
compounds are permitted when the constituent characters carry meanings that
combine sensibly *and* the construction is explained in surrounding prose
(see `鉄旋 / Tessen` in `ebisu/sandals-of-the-walking-monk-tessen.md`, where
the prose names the character `旋 'circuit, turning'` as part of the monk's
identity). A constructed compound with no in-fiction explanation is a
violation.

**Stylized name readings** (a kun-yomi reading where Sino-Japanese would be
expected, an obscure kanji choice for a personal name) are permitted but
should be deliberate - preferably explained in prose if they would surprise
a reader. `業道 / Narimichi` is borderline-acceptable as a Buddhist-themed
monastic name; the same reading without monastic framing would not be.

**Hiragana-only words** (e.g., `お露 / Otsuyu` mixing honorific お with the
kanji 露) are acceptable when they reflect real Japanese naming or naming-
adjacent conventions. Avoid katakana except for explicitly foreign elements.

**Enforcement**: every kanji-bearing entry - every relic, every sword, every
generated name - MUST pass the kanji ↔ romaji ↔ meaning triangle. When
generating new content, the skill MUST verify each entry against the triangle
before adding it to a pool. When reviewing an existing pool (e.g., after
this constitution was amended), entries that fail are content bugs to be
fixed, not stylistic preferences to be argued.

This principle is NON-NEGOTIABLE because the project's stated aesthetic
(Principle II) is built on Japanese cultural authenticity; a relic catalog
that says one thing in kanji, another in romaji, and a third in English
undermines the whole reading experience for any player who knows Japanese.

### XII. Historical Grounding Bookends (NON-NEGOTIABLE)

Any feature that changes what a **generator asserts about the world** - the
`/diagram` settlement and compound engines above all, but equally any future
generator that draws or states how a place was farmed, built, or lived in -
MUST be bookended by historical-grounding work: an analysis BEFORE it is
built, and a verification of the ARTIFACT after.

**Opening gate (Phase 0, before any design).** For every element the feature
adds or changes, the plan MUST state, in `research.md`:

1. **What the historical reality was** (China-first, Japan corroborating, per
   the `/diagram` doctrine), in enough detail to be checkable - not "terraces
   existed" but what determined their placement, extent, and season.
2. **Whether the proposed design matches it**, explicitly. A design that does
   not match MUST be changed or dropped at this point, not implemented and
   revisited.
3. **What determines the element in reality** - topography, season, tenure,
   economy. This matters because a generator usually gets the *existence* of
   a thing right and its *governing variable* wrong.

**Closing gate (final phase, before "done").** The feature MUST re-examine
the **rendered artifact** - the PNG, not the code and not the intent - and
confirm each element still matches the Phase 0 findings. This is a separate
step from the automated gate: `check_village` proves internal consistency,
never historical truth. A map can pass every check and still depict something
that never existed.

**Why the artifact and not the code (the motivating failure).** The
`land_use_overlay` knob shipped a `rape` value that recolored a random ~32%
of paddy plots yellow. It passed every automated check, was covered by tests,
and carried a grounded-sounding docstring citing the real 油菜 winter
rotation. It was still wrong: rice and rape are the two halves of ONE
rotation in the SAME plot (rice May-Oct; rape sown into the drained stubble
Oct-Nov, flowering Mar-Apr), so they are never both standing - the map
depicted two seasons at once. Nothing in the code could reveal that; only
looking at the picture and asking "what season is this?" could. The same pass
also showed the second failure mode: the overlay scattered plots at random
when the real governing variable was topography - deep-water lotus goes on the
wettest ground, and the 桑基魚塘 dike-ponds were dug out of the low
flood-prone hollows.

**A correction this principle caught on its own first outing (feature 010),
worth keeping as a warning.** The original wording here claimed the dike-pond
system "replaced rice across whole districts rather than dotting among it,"
and a feature was specified to DELETE the overlay on that basis. Phase 0
research refuted it: a scatter of dike-ponds among rice was the system's
NORMAL state (Shunde county was ~4.6% dike-pond in 1581; at Lake Tai mulberry
sat on the *tang* banks with rice remaining the polder's main crop
permanently), and the wall-to-wall landscape is the rare end state. The lesson
is not merely that the claim was wrong - it is that a **confident, plausible,
kanji-citing sentence written into a governing document was wrong**, and only
the opening gate caught it. Grounding claims already recorded here are inputs
to research, never substitutes for it.

**Calibrated liberty where the record is genuinely unclear (GM, 2026-07-19).**
The bookends demand honesty about the evidence, NOT paralysis when the
evidence is thin. Where all three of the following hold:

1. the research shows the thing is **plausibly true**,
2. the **degree** to which it was true is genuinely unclear or
   region-dependent, and
3. a particular reading within that plausible range **serves the project's
   goals** (legibility, visual variation, playability),

then the favorable reading MAY be chosen deliberately. The conditions are
conjunctive and the obligation is disclosure: the choice, its plausible range,
and the fact that we picked from within it for a stated non-historical reason
MUST be written into `research.md` and alongside the rule in the code. What
this clause does NOT license is inventing a range that the research does not
support, or using "the record is unclear" to dodge a finding that is actually
clear - the `rape` rotation was not a matter of degree, and no amount of
project convenience makes rice and rape stand in the same field at once.

**Enforcement.** `/speckit-plan` MUST record both gates in its Constitution
Check. A feature that cannot state its grounding is not ready to build. The
findings MUST be written where the rule lives (per the "record the why" rule
in CLAUDE.md) - including grounding that led to *rejecting* a design, so a
future pass does not reinvent it.

This principle is NON-NEGOTIABLE because the failure it guards against is
SILENT: historically impossible output looks perfectly fine, passes the gate,
and is only caught if a human happens to ask about it.

## Technical Standards

**Languages and runtimes**
- Python 3.13 (system Python on the dev sandbox; the chargen webapp's
  CLAUDE.md still pins 3.10 - that is the chargen-specific constraint,
  not a project-wide one).
- Node.js for headless-browser tooling (Playwright bundles its own
  Chromium binary; do not assume a system Chrome).

**Python tooling (per Principle X)**
- **Lint + format**: `ruff` (lint + formatter, single tool). Config lives
  in `pyproject.toml`.
- **Type checking**: `mypy --strict` on production modules. The mypy
  config lives in `pyproject.toml` or `mypy.ini`.
- **Testing**: `pytest` + `pytest-cov`. Coverage enforced via
  `pytest --cov-fail-under=100` for pure-logic packages.
- **Dependency management**: source-of-truth in `requirements.in`,
  compiled to `requirements.txt` via `uv pip compile` (or `pip-compile`).
  `uv.lock` is acceptable for `uv`-native projects.
- **Config validation**: `configobj` with `configspec.ini` for the
  chargen pattern; `pydantic-settings` for env-var-driven new code.
- **Logging**: stdlib `logging` with `logging.getLogger(__name__)`.

**UI / browser tooling**
- `playwright` (Python async API) with bundled Chromium for screenshots
  and DOM-overflow audits.
- Standard viewport set: GM-100 (1850×1050), GM-200 (925×525), tablet
  (800×1100), mobile (390×844 with `device_scale_factor=2`).

**Test layout**
- Test files live alongside the code as `test_<module>.py`.
- Saved fixtures for external boundaries live in a `fixtures/`
  subdirectory next to the tests that consume them.
- Test names describe behavior (not implementation); parametrize
  variant inputs.

**Webapp conventions**
- Static prototypes live under `/gm-assistant/webapp-prototype/`.
- The chargen backend (CherryPy + Jinja2) lives under `/gm-assistant/webapp/`.
- A `relics.js` (or analogous) bundle inlines pool data as
  `window.<NAME>_BUNDLE` so prototypes work over `file://` without a
  server. A parallel `relics.json` artifact is produced for future API
  parity.

**Secrets**
- `development-secrets.ini` files MUST be gitignored. The corresponding
  `.example` template stays in the repo with empty values. No secret
  values may be committed.

## Development Workflow

**Specification → Plan → Tasks → Implement**
This project uses the spec-kit workflow. Significant features SHOULD start
with `/speckit-specify`, refine with `/speckit-clarify` if needed, plan
with `/speckit-plan`, decompose with `/speckit-tasks`, and execute with
`/speckit-implement`. Constitutional principles are enforced at the plan
gate via the *Constitution Check* section of `plan-template.md`.

**Screenshot-as-feedback workflow (mandatory for UI changes)**
The verification workflow described in Principle I and VI MUST be run
before any UI change is reported as done. The canonical implementation
lives at `/gm-assistant/webapp-prototype/relics/screenshot.py` and runs:

1. Boot the prototype via `python3 -m http.server` on port 8123.
2. For each of GM-100 (1850×1050), GM-200 (925×525), tablet (800×1100),
   and mobile (390×844, dsf=2): take a full-page screenshot and an
   above-the-fold screenshot.
3. Run a DOM-overflow audit using Playwright's `page.evaluate` over
   `.card`, `.card__top`, `.card__name`, `.card__entity`,
   `.card__type`, `.card__kanji`, and any other narrow-target selectors
   added by the change.
4. Report dimensions (page height, card height, hero/foot heights) and
   any overflow / truncation findings to the user.

**Python "done" checklist (mandatory per Principle X)**
A Python change is not complete until all of the following pass on the
modified package:

1. `ruff check`
2. `ruff format --check`
3. `mypy --strict` (on production modules)
4. `pytest`
5. `pytest --cov-fail-under=100` (on pure-logic packages)

Subagents and skills MUST run all five before reporting Python work
done. The TDD order - write failing test, watch it fail, implement,
watch it pass, refactor - is the working mode for new code.

**Delegation**
Subagents are used for parallel generation and large-context work.
Whenever a subagent is delegated a task whose output is shipped to the
user (file edits, generated content), the calling agent MUST verify the
delegated work before reporting success.

**Memory and persistent context**
The agent maintains persistent memory at
`/home/agent/.claude/projects/-gm-assistant/memory/`. Memory entries follow
the format and rules described in the harness system prompt; this
constitution does not duplicate them, but the agent's behavior MUST be
consistent with both the constitution and the memory rules.

## Governance

This constitution supersedes ad-hoc development practices for the L7R
toolkit project. Where this document conflicts with other guidance, this
document wins; where this document is silent, defer to the project's
`CLAUDE.md` and the conventions established there.

**Amendment procedure**
- The GM (project owner) approves all amendments.
- Amendments are made by editing `.specify/memory/constitution.md` and
  re-running `/speckit-constitution` with the change described in natural
  language. The skill produces a new Sync Impact Report and propagates
  changes to dependent templates.
- After amendment, dependent artifacts (plan template, spec template,
  tasks template, runtime guidance docs) MUST be reviewed for
  consistency and updated if needed.

**Versioning policy** (semver applied to governance)
- MAJOR: A principle is removed, redefined with materially incompatible
  meaning, or NON-NEGOTIABLE designation is lifted from a principle that
  had it.
- MINOR: A new principle or section is added, or an existing principle is
  materially expanded.
- PATCH: Clarification, wording, typo fixes, non-semantic refinements.

**Compliance**
- Every plan generated via `/speckit-plan` includes a Constitution Check
  gate that verifies the plan against each principle. Plans that fail
  the check MUST be revised before tasks are generated.
- UI changes verified by the screenshot/overflow workflow have an
  automatic compliance signal: zero overflows + clean screenshots = pass.
- Generated content (relics, names, etc.) is checked against the pool
  conventions (Principle III) and the de-localization rule (Principle VII)
  before being added to a pool.

**Runtime guidance**
`/gm-assistant/CLAUDE.md` and the per-directory CLAUDE.md files remain the
day-to-day runtime guidance. This constitution is the higher-level
authority; CLAUDE.md operationalizes it.

**Version**: 1.4.1 | **Ratified**: 2026-05-27 | **Last Amended**: 2026-07-19
