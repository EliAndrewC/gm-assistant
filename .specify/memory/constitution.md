<!--
SYNC IMPACT REPORT
==================
Version change: 1.17.0 -> 1.18.0

Version 1.18.0 (amended 2026-08-25, GM-directed): all map-making material removed. The GM: "there's
no longer any reason to include map making information in the Speckit constitution." Every
principle keeps its rule; the diagram-era motivating cases, measurements and mechanisms that
illustrated them are gone from this copy, and each lesson is restated in this repository's own
terms. The narrative amendment history that used to sit in this header (1.0.0 through 1.17.0) was
itself mostly diagram incidents and is reduced to the version table below; the full text is in git
history and in the diagram repository's copy of this constitution
(https://github.com/EliAndrewC/diagram). Amendment: MINOR - sections materially rewritten, no
principle removed or redefined.

Version table (what each version added; details in git history):
  1.0.0  2026-05-27  Principles I-IX, Technical Standards, Development Workflow, Governance
  1.1.0  2026-05-27  X  Python Discipline
  1.2.0  2026-05-27  XI Japanese Authenticity
  1.3.0  2026-07     I expanded: layout balance + multi-scroll contact sheets
  1.4.0  2026-07     XII Historical Grounding Bookends
  1.4.1  2026-07-19  XII calibrated-liberty clause
  1.4.2  2026-07-20  Python 3.13 -> 3.14
  1.5.0  2026-08-15  X clause 12 (functions at human scale)
  1.6.0  2026-08-15  X clause 13 (files at human scale); 1.6.1 tests included
  1.7.0  2026-08-16  X clause 14 (rosters are derived, not maintained)
  1.8.0  2026-08-17  XIII No Known Regressions
  1.9.0  2026-08-18  XII research precedes a ruling; two answers become a knob
  1.10.0 2026-08-17  XIV Fix Defects Where You Find Them
  1.11.0 2026-08-23  XV Keep Going; XIII's exits are not a menu
  1.12.x 2026-08-23  VI reference-first rule (mechanism since moved to the diagram repository)
  1.13.0 2026-08-24  XVI Build What Was Asked; 1.13.1 XIII worktree-baseline clause
  1.14.0 2026-08-24  XVII A README Is Written By A Human
  1.15.0 2026-08-24  XVIII A Guard Ships With Its Test
  1.17.0 2026-08-25  diagram mechanisms generalized after feature 131 (superseded by 1.18.0)
-->

# L7R Toolkit Constitution

This constitution governs the L7R toolkit project - a working setup of Claude
Code skills, generated content pools, and the L7R Toolkit webapp for a custom
Legend of the Five Rings tabletop RPG setting. It is the highest-level guide
for how Claude Code agents and human contributors collaborate on this
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

- **Generators: ONE ARTIFACT UNTIL IT WORKS, then the sweep** (GM 2026-08-23).
  A change to a generator - a pool skill, a toolkit section, anything that
  produces many artifacts from shared code - is proven on a SINGLE named
  artifact first: one pool entry, one page, one test file. The full sweep (the
  whole pool, the whole suite) runs once, AFTER that artifact is fully working -
  never as the loop you iterate inside. A slow loop is what tempts a session
  into guessing another fix instead of measuring again.
  - **EVERY STEP OF A FEATURE IS TWO STEPS** (GM 2026-08-23): get it working on
    the reference artifact, THEN get it working everywhere. A plan or task list
    that says only "make X work" is incomplete - it must say "make X work on the
    reference artifact" and, separately, "make X work across the pool". The
    second half is a distinct task with its own verification, not a footnote to
    the first. The plan and tasks templates carry this shape.
  - **`make done` IS THE BACKSTOP, and it is why narrow defaults are safe.** The
    gate re-checks everything, so a session that forgets the sweep entirely still
    cannot ship what it broke. Cheap defaults trade no correctness - only the
    moment you find out.
  - The final sweep stays MANDATORY whenever shared code changed - this clause
    changes WHEN it runs, never WHETHER.
  - A feature that adds a KNOB owes one artifact per knob VALUE, not one per
    artifact in the pool.

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

12. **Functions stay at human scale** (added v1.5.0, GM-directed
    2026-08-15): a function that has grown past a few hundred logical
    statements is suspect and rarely the right shape in Python; past
    roughly 1,000 it is a defect unless an inline annotation at the
    definition explains why it must remain one body. Size is measured
    in LOGIC UNITS (statements/expressions), never raw lines: a call
    or string literal wrapped across lines counts once, so formatting
    never forces a split. The 10-line-function dogma is explicitly
    REJECTED - over-fragmentation damages design more than length
    does, and a deep-but-cohesive engine function is legitimate at a
    scale a utility function never is. The failure mode is GROWTH: no
    single edit crosses the line, so the line must be checked rather
    than felt. Deferred future work, recorded here so it is not lost:
    an automated gate check counting expressions per function, failing
    past the threshold unless the justification annotation is present.
    The cost of ignoring this surfaces as an architecture problem -
    nothing inside the function can be invoked separately - long before
    anyone would have chosen that shape.

13. **Files stay at human scale** (added v1.6.0, GM-directed 2026-08-15):
    a source file that has grown past roughly 1,000 lines prompts a
    question that MUST actually be asked: should this become a package
    of subfiles? The unit here is RAW LINES - deliberately unlike
    clause 12's logic units - because the motivating cost is token
    economy: a session that needs one function from a file pays
    context-window tokens for the whole file, and that cost scales with
    text, not logic. Unit TEST files are covered exactly as source files
    (clarified v1.6.1, GM-directed 2026-08-16): a test file is loaded
    under the same conditions as source - you load test_names.py to
    modify one test the same way you load names.py to use one
    function - so nothing about being a test changes the economics, and
    tests get no exemption. The target shape is a directory-module whose
    CLAUDE.md indexes the subfiles with a "look here when" line each,
    per the project's slim-index / load-on-demand doc pattern, so a
    future session loads only the part it needs. Like clause 12 this is
    an ask-the-question line, not a mandate: over-fragmentation damages
    design more than length does, and a file that is one cohesive
    ordered dataset (a registry whose row order IS the execution
    contract) may stay large - with an inline justification at the top
    saying why. The failure mode is the same GROWTH pattern as clause
    12: no single edit crosses the line, so the line must be checked
    rather than felt. A file that has grown to tens of thousands of
    lines one addition at a time costs a full context window to
    consult; the package-of-subfiles split is the fix.

14. **Rosters that restate code are derived, not maintained** (added
    v1.7.0, GM-directed 2026-08-16): when a file's bulk is a
    hand-maintained roster whose rows restate what the code already
    declares elsewhere - a package `__init__` explicitly importing
    thousands of names its submodules define, an `__all__` list
    duplicating the import block above it, registry rows a machine
    could regenerate by introspecting the functions they point at -
    splitting it per clause 13 is the WRONG fix: duplicated
    information does not shrink by being divided. The right fix
    DERIVES the surface from the single source of truth (star imports
    for a re-export surface; introspection or generation for
    derivable rows) and moves any safety property the explicit roster
    was providing into a test that fails loudly (e.g. a guard against
    silent star-import shadowing), proven to fire on a synthetic case
    before it is trusted. Method, in order: CENSUS the consumed
    surface first - grep who actually reads each name, because most
    of a grown roster has zero consumers and simply drops; write the
    guard/surface test against the CURRENT file so the rewrite must
    preserve what is actually used; then derive; then run the full
    gate. The line against clause 13's ordered-data carve-out is
    INFORMATION: a roster stating real decisions (execution order,
    curation, hand-written per-row metadata that exists nowhere else)
    is data and may stay; rows reproducible from the code they
    reference are duplication and must go - and when one file mixes
    both, derive the derivable facts and keep the decided ones. The
    question is per-fact, not per-file. The typical case is a package
    `__init__` of several thousand import lines plus a duplicate
    `__all__` restating what its submodules already declare, which
    derives down to a few dozen lines with zero consumer changes.

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

Any feature that changes what a **generator asserts about the world** - a
temple's daily life, a calendar's agricultural events, a legal case's
procedure, a place's layout; any generator that draws or states how a place
was farmed, built, governed, or lived in - MUST be bookended by
historical-grounding work: an analysis BEFORE it is built, and a verification
of the ARTIFACT after.

**Opening gate (Phase 0, before any design).** For every element the feature
adds or changes, the plan MUST state, in `research.md`:

1. **What the historical reality was** (China-first for geography, farming
   and transport - Song/Ming - with Japan as the tiebreaker and the cultural
   surface staying Japanese; the GM's standing doctrine), in enough detail to
   be checkable - not "the temple had a festival" but what determined its date,
   its scale, and who attended.
2. **Whether the proposed design matches it**, explicitly. A design that does
   not match MUST be changed or dropped at this point, not implemented and
   revisited.
3. **What determines the element in reality** - topography, season, tenure,
   economy. This matters because a generator usually gets the *existence* of
   a thing right and its *governing variable* wrong.

**Closing gate (final phase, before "done").** The feature MUST re-examine
the **rendered artifact** - the page, the pool entry as a reader sees it; not
the code and not the intent - and confirm each element still matches the
Phase 0 findings. This is a separate step from the automated gate: an
automated check proves internal consistency, never historical truth. An
artifact can pass every check and still depict something that never existed.

**Why the artifact and not the code.** The failure this guards against is a
generator that gets the *existence* of a thing right and its *governing
variable* wrong - two events that really happened, drawn as if they happened
at once; a feature scattered at random when the record says what actually
placed it. Nothing in the code reveals that; a test that encodes the same
misunderstanding passes. Only looking at the artifact and asking "could this
have existed?" catches it. And a confident, plausible, source-citing sentence
already written into a governing document can be wrong too: grounding claims
recorded here are inputs to research, never substitutes for it.

**Calibrated liberty where the record is genuinely unclear (GM, 2026-07-19).**
The bookends demand honesty about the evidence, NOT paralysis when the
evidence is thin. Where all three of the following hold:

1. the research shows the thing is **plausibly true**,
2. the **degree** to which it was true is genuinely unclear or
   region-dependent, and
3. a particular reading within that plausible range **serves the project's
   goals** (legibility, variety, playability),

then the favorable reading MAY be chosen deliberately. The conditions are
conjunctive and the obligation is disclosure: the choice, its plausible range,
and the fact that we picked from within it for a stated non-historical reason
MUST be written into `research.md` and alongside the rule in the code. What
this clause does NOT license is inventing a range that the research does not
support, or using "the record is unclear" to dodge a finding that is actually
clear - a decisive finding is not a matter of degree, and no amount of project
convenience overrides it.

**RESEARCH PRECEDES A RULING - the GM is the last resort, not the first
(GM, 2026-08-18).** A question about how a place was actually built, farmed or
lived in is a RESEARCH question, and it is answered by a research pass before
it is ever put to the GM. *"This is a category of question which should ALWAYS
be based on historical research when possible, so I should only be asked for a
ruling on this kind of question when a research pass has already been done and
has turned out to be inconclusive."*

This binds the review loop in particular, because that is where such questions
surface: a reviewer writing "this wants a one-line ruling" is describing a
QUESTION, not delegating it. Run the search first. Only if the record is
genuinely silent or contradictory does the question reach the GM - and when it
does, the ask MUST state what was searched, what was found, and why the finding
does not settle it. An unresearched question presented as a ruling spends the
GM's attention on work the project could have done, and it launders "I did not
look" into "the evidence is unclear".

**TWO SUPPORTABLE ANSWERS BECOME A KNOB, NOT A CHOICE (GM, 2026-08-18).** This
AMENDS the calibrated-liberty clause above, and takes precedence over it where
the two differ. When research shows a thing was genuinely done more than one
way, the project does NOT pick the reading it likes and write the other off.
It makes the variation a **tunable knob with per-artifact variance**, so an
artifact can be rolled either way and two artifacts can honestly differ.

The reason is a project goal, not a historical one: generated content exists
for players who must tell one temple, one festival, one relic from another at
a glance. The GM's goal is content that is within historical norms while being
as different from one instance to the next as the historical research
justifies. Every place where the record permits two forms is therefore a place
the generator can differ WITHOUT leaving those norms - which is exactly the
variation worth having, and picking one form throws it away permanently.

So the ladder for any such question is:

1. **Research it.** If the record is decisive, implement what it says - there
   is no knob and no ruling.
2. **If the record supports two or more forms, add the knob**, rolled per
   artifact from the artifact's own seed so a value depends only on (seed,
   knob name). Record the range and its evidence where the knob lives.
3. **Only if the record is silent or self-contradictory** does the GM rule -
   and the ask carries the research that failed to settle it.

Calibrated liberty survives for the case a knob cannot express: a single
element whose DEGREE is uncertain along a continuum (how large, how dense, how
often) where the project needs one figure to draw. Where the uncertainty is
between DISTINCT FORMS, it is a knob.

**Enforcement.** `/speckit-plan` MUST record both gates in its Constitution
Check. A feature that cannot state its grounding is not ready to build. The
findings MUST be written where the rule lives (per the "record the why" rule
in CLAUDE.md) - including grounding that led to *rejecting* a design, so a
future pass does not reinvent it.

This principle is NON-NEGOTIABLE because the failure it guards against is
SILENT: historically impossible output looks perfectly fine, passes the gate,
and is only caught if a human happens to ask about it.

### XIII. No Known Regressions (NON-NEGOTIABLE)

GM, 2026-08-17: *"never count our work as being done when there are known
regressions. Nothing should EVER be merged back into main if even one single
new regression was added."*

**The rule, in two halves.** Work is NOT done while a known regression exists,
and **nothing merges into main carrying even one new regression.** Both halves
bind independently: a change may be finished in the sense that its feature
works and still be un-mergeable, and that is the normal case this principle
exists to make visible.

**What counts as a regression.** Anything that worked before the change and
does not work after it - a test or check that passed and now fails, a pool
artifact that was green and now is not, a seeded case that passed and now
fails, a measured rate that went down. It is defined against a **measured**
baseline, never a remembered one: take the baseline on unmodified code (a
detached worktree, not a stash) before judging your own numbers.

**A WORKTREE BASELINE IS A STARTING POINT, NOT A VERDICT** (added 2026-08-24).
A detached worktree is still the right way to take a baseline - a stash mutates
the tree under any review agent reading it - but a fresh worktree does NOT carry
gitignored artifacts (the `/dream` skill's `pool-local/`, the webapp's `opcache/`
and `setting/` snapshots), so a test that reads one fails there for reasons that
have nothing to do with the code. **Every failure a worktree baseline reports is
checked against the clone before it is called pre-existing.**

This cuts both ways and the quiet direction is the dangerous one. A spurious baseline
failure is loud and gets investigated. But the same gap can make a test pass ONLY in
the worktree, and then a real regression is invisible from the moment the baseline is
taken. Neither reading is available without the second check, and neither error
announces itself.

**Pre-existing failures are NOT regressions** and do not block your merge.
The distinction is exactly "did this pass before my change", which is why the
baseline is mandatory rather than advisory. **But "not a regression" is not
"not your problem":** this clause governs the MERGE BAR only, and
**Principle XIV** governs what you do about a defect you actually found -
fix it in the work at hand, ledger it only when its fix would be an
architectural overhaul. Read the two together; taken alone, this paragraph
has been misread as a licence to ledger anything that predates the diff.

**What does NOT excuse a regression:**

- It is small, or it is one seed out of many.
- It is on a seeded case, a fixture, or a pool entry nobody ships. Every one
  of those is a test bed precisely because it stands in for the content that
  is not written yet.
- It is *documented*. Writing a regression down is how it gets tracked; it
  is not how it gets permitted. A ledger entry is not a waiver.
- The change fixes more than it breaks. Net-positive is an argument for
  doing the work, never for merging it broken.
- **The residue "rotated".** In a seeded generator a change that alters draw
  counts re-rolls every case, so failures move rather than persist in place.
  That is a real effect and it is NOT a defense: where seed-level comparison
  survives, any check that passed on a seed and now fails is a regression;
  where the re-roll makes per-seed comparison meaningless, the pass RATE must
  not drop AND every newly-failing check must be individually diagnosed.

**FIXING IT IS THE EXIT** (GM 2026-08-23). There are three in principle -
FIX it, REVERT the change, or obtain an explicit GM waiver - but they are
not peers, and treating them as a menu is itself the error:

- **FIX is the default and the expected outcome.** A session that has found
  a path forward TAKES it. "I could fix this, but here are three options,
  which do you prefer?" is not a report, it is a stall.
- **REVERT requires a demonstrated impossibility**, not a preference and not
  fatigue. The bar is an investigation written down: what was measured, what
  was tried, why each attempt failed, and why the remaining approaches are
  exhausted or unreasonable. Reverting because a fix looks like work is not
  an exit, it is an abandonment.
- **WAIVER is the GM's to grant, never the session's to assume.** Asking for
  one is only honest after the fix has been genuinely attempted.

A session that truly cannot fix a regression stops and says so - and "stops
and says so" means the work stays in the clone, unpushed, with the
impossibility investigation attached. But see Principle XV: stopping is
expensive, and the bar for it is high.

**Enforcement.** `/speckit-plan` records this in its Constitution Check. The
stop-work procedure does not run to completion on a red or regressed state: a
session may commit inside its own clone (mid-task work is sacred) but MUST
NOT push to main. Where a domain has a sweep, its measured before/after
numbers are the evidence, and they belong in the commit message or the
feature's notes.

This principle is NON-NEGOTIABLE because main is the shared integration
point: a regression merged there is silently inherited by every other
session and by every artifact generated afterwards, and the person who pays
for it is never the person who introduced it. The trade "I gained a feature
and lost a check" is legible for about a day and invisible forever after.

### XIV. Fix Defects Where You Find Them (NON-NEGOTIABLE)

GM, 2026-08-17 (said of one skill, applied to all of them): *"anytime ... you
in the course of implementing a feature come across some new defect - even if
it is a defect that did not have anything to do with what you were working on -
I would like you to fix it as part of that work ... in general, we should fix
bugs before writing new code."*

**The rule.** A defect discovered in the course of a piece of work is FIXED in
that piece of work, whether or not it has anything to do with the feature. Not
filed, not deferred to "its own pass", not handed to a future session - fixed,
in the same change, with the same verification every other fix gets.

**The one exception** is a defect whose fix would be a complete overhaul or a
giant architectural change: a stage reordering, a new subsystem, a rewrite of a
generator's core. Those are deferred - and deferring one is a real deliverable,
not a shrug: it carries the MEASUREMENT that establishes the defect, the
mechanism, and the implementation sketch, so the next session starts from
evidence rather than from a complaint. "This would take a while" is not the
exception; "this cannot be done without changing the architecture" is.

**Why this outranks the convenience of a tidy diff.** The reason is the GM's,
and it is about compounding: the value of this project's generators comes from
being able to expand them - new skills, new toolkit sections, new pools - on
top of a foundation whose behavior is known-good. Every defect left in place is a
defect the next tier inherits and builds over, and by then it is entangled with
work that assumed it. Fixing on contact keeps the floor level as the building
gets taller. It also removes the incentive that makes ledgers rot: a session
that may fix what it finds writes down only what it genuinely cannot, so the
ledger stays short and every entry in it is real.

**Interaction with Principle XIII.** XIII says a pre-existing failure is not a
regression and does not block your merge; that remains true and is about the
MERGE BAR. XIV is about your OBLIGATION once you have seen the defect. Together:
a pre-existing failure you never touched does not stop you shipping, and one you
found gets fixed rather than ledgered. Where they appear to conflict, XIV
decides what you do and XIII decides what blocks the push.

**Where the defects actually come from, and so where this bites.** Mostly from
the review subagents (`backstory-review`, `frontend-review`, `spec-fidelity`),
which are pointed at a DELTA and reliably find things
outside it - that is a feature of an independent reviewer, not scope creep by
it. A finding outside the delta is still yours. The same applies to a defect a
diagnostic surfaces, a number that looks wrong while measuring something else,
and a comment that turns out to describe code that no longer exists.

This principle is NON-NEGOTIABLE because the alternative is invisible: a
skipped fix costs nothing today, shows up as "the generator has always been a
bit off here" in a month, and is unattributable by the time it blocks the next
feature.

### XV. Keep Going (NON-NEGOTIABLE)

**The GM starts work and leaves.** That is how this project is actually used:
a request is kicked off and the computer is unattended for hours. A session
that stops to ask "which of these should I do?" does not cost a few seconds
of the GM's attention - it costs the entire span until they return, and they
come back to find the work exactly where they left it. GM, 2026-08-23:
*"it is bad for me to come back and find that you could have kept going but
decided to just stop and ask what to do next. And if one of the options is
actually, yes, go ahead and fix it and make it work, then that is always the
option that I want."*

**So: when a path forward exists, take it.** Finish the feature. If one
avenue is blocked, work the parts that are not blocked. The standing answer
to "should I keep going?" is yes.

**The ONLY reason to stop and ask** is a genuine belief that the thing
cannot be done - that there is a high probability no approach accomplishes
it. Not that it is hard, not that it is taking longer than expected, not
that there are several ways to proceed and one of them is nicer. If the
options list contains "fix it and make it work", that is the answer and it
does not need confirming.

**Two things this does NOT license:**

- **It is not "any means".** The bounds of ordinary, authorized, ethical work
  are unchanged - this principle is about persistence, never about reaching
  for access, systems or actions that were not granted.
- **It is not thrashing.** Persistence means continuing to make PROGRESS, not
  continuing to make CHANGES. When stuck, the next step is a MEASUREMENT, not
  another speculative edit. A session that changes code on four successive
  hypotheses without measuring between them is not keeping going, it is
  churning - and it will burn the unattended hours producing nothing, which
  is the same failure as stopping. (The recorded case of both halves, on
  2026-08-23: four wrong diagnoses in a row, and then a stop to ask which of
  three options to take when one of them was "fix it".)

**Interaction with the stop-and-ask calculus.** The older rule - interrupt
only when a wrong guess is expensive to unwind - still holds for AMBIGUITY
about what is wanted. This principle governs DIFFICULTY in delivering what is
already known to be wanted, and there the answer is to keep working.

**Interaction with XIII.** A regression that cannot be pushed does not end
the session's work; it redirects it. Keep fixing, or keep building the parts
that are not blocked, until the regression is fixed or the impossibility is
demonstrated in writing.

**Enforcement.** A standing goal (the `/goal` mechanism) means exactly this:
continue until the objective is met or shown impossible. Reporting progress
is welcome at any point; reporting progress is not the same as stopping.

### XVI. Build What Was Asked; Fidelity Is Not Self-Adjudicated (NON-NEGOTIABLE)

**The default is the literal thing.** When the GM asks for X, build X - not "X
except where Y". Being able to construct a persuasive argument for an exception is
not evidence that the exception is wanted; it is the ordinary result of having
thought about the problem, and such an argument will be available every time.

**An exception is never approved by the session that wants it.** If you believe one
is genuinely necessary, it goes to an independent subagent (Opus 5), whose question
is exactly: *is this a real exception, or is this a session carving out a case
contrary to what it was told?* Hand it the GM's request VERBATIM. If it agrees the
exception is valid, proceed - and raise it with the GM AFTER the implementation
works, not before, because the GM's preferred mode is to start long work and return
to something finished. If it disagrees, build the literal thing.

**Every spec-kit specification is reviewed against the GM's own words before
implementation begins.** The reviewer is an independent subagent and its input is
the GM's REQUEST AS WRITTEN - not the plan, not a paraphrase. A spec checked against
its own plan is being tested for self-consistency, which a wrong spec passes
comfortably. The question is: does this specification implement what was actually
asked, and does it add anything that was not?

**AT MOST three rounds, and stop at the first clean verdict.** A `FAITHFUL` verdict
on round one ends the review - there is no quota to fill and re-reviewing a spec the
reviewer has already passed buys nothing. A `CHANGES REQUIRED` verdict means: revise,
re-review. If the THIRD review still returns changes, STOP and put it to the GM.
Three failures to express a request as a specification is a persistent
misunderstanding, and a fourth attempt by the same session will not locate it.

**A scope-expansion finding is an ordinary finding.** "This spec does more than was
asked" goes through the same revise-and-re-review loop as anything else; it is not a
special case and it does not short-circuit the rounds. It becomes a stop only the way
every other finding does - by surviving three of them (GM 2026-08-24, declining the
tighter rule the implementing session proposed).

**Why this exists** (GM 2026-08-24). A feature was asked for as "do A before B".
The specification that came out of it said A before B EXCEPT in two cases - a
carve-out the GM never asked for, written by the implementing session on an
argument it found persuasive, and placed in a mid-list requirement where only a
full reading would find it. The implementation then followed its spec
faithfully, the two excepted cases went on constraining precisely what the
feature existed to free, and the feature under-delivered while no instruction
was ever disobeyed. The persuasive argument turned out to be only half-sound,
and nothing in the process was positioned to notice.

**This is the QA separation every engineering organization runs on**, and this
constitution already believes it. Principle I holds that the author of a design is
not a reliable reviewer of it, which is why `frontend-review` and `backstory-review`
exist. Every one of those guards an OUTPUT. This extends the same rule one step earlier, to the specification - the one
artifact still being written and graded by the same session.

**Interaction with XV (Keep Going).** This is not licence to stop. The reviews run
inside the work, the session keeps building while it acts on them, and escalation
happens only after the third round. Asking the GM to choose among options remains
the thing XV forbids.

**Interaction with the stop-and-ask calculus.** An exception is not ambiguity. Where
a request is genuinely unclear, the older calculus applies. Where a request is clear
and you want to depart from it, this principle applies, and the answer is to build
what was asked.

### XVIII. A Guard Ships With Its Test, And That Test Runs (NON-NEGOTIABLE)

**Every guard - a hook, a gate check, a refusal of any kind - ships in the same change as a test
companion, and that companion runs in the gate.** GM 2026-08-24.

**Both halves, because each has failed on its own.**

*A guard without a test is not implemented.* This project already knows that from the other
direction: `T034`'s rule is that a guard whose test does not fail when the guard is DELETED is
decoration. A guard with no test at all cannot be checked either way.

*A test nothing runs cannot fail.* The 2026-08-24 enforcement audit found **eight hook scripts, eight
test companions, and nothing that executed any of them.** The convention of writing them was healthy;
the convention of running them did not exist. They had been passing, or not, unobserved. (In this
repository that stayed true until 2026-08-25, because the target that ran them lived in a Makefile
that has since moved out; `webapp/Makefile` carries it now.)

**What the test must cover - two directions, always:**

- It **FIRES** on the case the guard exists to catch.
- It **STAYS QUIET** on correct work, and this half is the one that protects the project. A guard
  that fires on legitimate work teaches a session that the escape hatch is part of the routine, which
  is precisely the habit these guards exist to break. The first guards of this kind did this **seven
  times** in one feature - on a grep, a commit message, a docstring, a fixture argument, a redirect, a
  test harness, and once on a hook that could not edit its own repair. Every one of those is now a
  regression case in `scripts/test_hooks_cases.py`.

**The recurring failure has a name: a MENTION IS NOT AN INVOCATION.** Matching a name anywhere in a
command, a path, or a body will eventually match prose that talks ABOUT the thing. Anchor to a real
command position, require the operator adjacent to its target, walk an AST for calls rather than
grepping source - and put the case that fooled you into the table.

**And the escape is checked FIRST.** A guard whose escape is evaluated after its tests cannot be
repaired through the channel it guards: every command carrying the fix contains the offending text.
That happened, and it cost a session three blocked attempts at its own bugfix.

**Enforcement**: `make hooks-test` runs every `scripts/test-*-hooks.sh` and fails if any guard has no
companion. It is a phase of `make done`, so a guard added without a test turns the gate red.

### XVII. A README Is Written By A Human, For A Human (NON-NEGOTIABLE)

**Never create or edit a README.** GM 2026-08-24: *"you personally should literally never touch a
readme file because a readme file is something that should be written by a human for a human."*

**The mechanical reason, which is the important one.** A README is NOT loaded into a session's
context. A directory `CLAUDE.md` is, automatically, whenever work happens in that directory. So
anything a session must KNOW in order to act correctly is invisible in a README - it will be found
only by a session that happens to look, which is to say by luck.

That is not theoretical. A README once carried the rule that an append-only shared log must be a
DIRECTORY, because concurrent clones conflict on every push. A session read that file during an
unrelated audit, quoted from it, and hours later created a single-file log - breaking a rule it had
read the same day. Had the file been a `CLAUDE.md`, it would have been in context at the moment
the decision was made.

**Where knowledge goes instead:**

- **`CLAUDE.md` in the directory it governs** - auto-loaded exactly when relevant, which is the
  whole reason this project splits documentation by directory rather than piling it into one file.
- **A topic doc referenced from a CLAUDE.md**, when it is long enough that loading it always would
  be waste. That is the established `docs/` pattern (each file opens with a "load this when" line).

**What a README is still for**: a human arriving at the repository, or at a published subproject,
who wants an orientation. The GM writes those. If a README is factually wrong, say so and offer the
correction rather than making it.

**Enforcement**: `scripts/readme-hooks.sh` intercepts a Write or Edit to any `README*`, and any
shell command that writes one. It carries no silent escape - a genuine exception is the GM's to make.

## Technical Standards

**Languages and runtimes**
- Python 3.14 (system Python on the dev sandbox and the Fly prod image;
  bumped from 3.13 when the standard dev container moved to 3.14,
  GM-directed 2026-07-20).
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
- The L7R Toolkit (CherryPy + Jinja2) lives under `/gm-assistant/webapp/`;
  new code under `webapp/l7r/`, the legacy chargen app mounted beneath it.
  (The static `webapp-prototype/` tree that preceded it is gone.)
- Pool data reaches the toolkit by reading the skills' pool files directly in
  development and via `make prepare-deploy` snapshots in the Fly image.

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
before any UI change is reported as done. The canonical implementation is
`webapp/tests/screenshot.py` + `webapp/tests/dom_audit.py` (`make ui-verify`
from `webapp/`, against a running server):

1. For each of GM-100 (1850×1050), GM-200 (925×525), tablet (800×1100),
   and mobile (390×844, dsf=2): capture a multi-scroll contact sheet
   (0/33/66/100% scroll positions stitched side by side for any page
   taller than 1.3x the viewport) to `/tmp/l7r-shots/sheet-<page>-<viewport>.png`.
2. Run the DOM audit over every page x viewport: clipping (overflow,
   ellipsis, line-clamp) AND layout balance (sibling-height ratio inside
   flex/grid containers). It MUST report zero issues.
3. Do the persona-driven review pass at GM-200, and route the sheet to the
   `frontend-review` subagent when the author is also the reviewer.

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

**Version**: 1.18.0 | **Ratified**: 2026-05-27 | **Last Amended**: 2026-08-25
