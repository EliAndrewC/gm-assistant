<!--
SYNC IMPACT REPORT
==================
Version change: 1.12.0 → 1.12.1

Version 1.12.1 (amended 2026-08-23): replaces the two-command reference-first
workflow with ONE self-scoping command. `make maps` reads how the last run went -
passed means the whole tier with every failure reported, failed means the
reference map alone stopping at the first problem, and only widening once it is
clean. One piece of state drives both scope and verbosity. The two-command
version lasted about an hour before its own author reached for the expensive one
by habit, which is the argument: a choice is a thing that gets chosen wrong under
pressure. Applies to every settlement tier, not just hamlets. Amendment: PATCH -
it strengthens the enforcement of an existing principle without changing it.

Version 1.12.0 (amended 2026-08-23): makes the reference-settlement rule
STRUCTURAL rather than advisory. Every step of a generator feature is now two
steps - working on the reference settlement, then working across the pool - and
both are tasks with their own verification. The tooling defaults to the cheap
thing on purpose (SUPERSEDED BY 1.12.1 - that version's two commands, `make
map` and `make full-hamlet-sweep`, are gone; use `make maps`), because a wide
sweep that is cheap to invoke is what lets a session drift onto it unnoticed.
`make done` remains the backstop, which is what makes narrow defaults safe: the
gate re-checks the whole pool, so forgetting the sweep costs time, never
correctness. Amendment: MINOR. Motivating measurement: feature 126 spent five
10-12 minute four-map cycles chasing one connectivity defect that the reference
hamlet answered in 67 seconds - and the slow loop was itself the cause, because
waiting ten minutes for an answer is what tempts a session into guessing another
fix instead of measuring again.

Version 1.11.0 (amended 2026-08-23): adds Principle XV (Keep Going) and
rewrites Principle XIII's exits. The GM starts work and leaves the computer
for hours, so a session that stops to ask which option to take costs that
entire span, not a few seconds - and when one of the options is "fix it and
make it work", that is always the answer. XIII's three exits are no longer a
menu: FIX is the expected outcome, REVERT requires a written impossibility
investigation rather than a preference, and a WAIVER is the GM's to grant
after a fix has genuinely been attempted. Also adds the performance bookends
to Principle VI and the single-artifact rule for generators. New principle:
MINOR per the versioning policy. Motivating case: feature 126 (2026-08-23),
which produced four successive wrong diagnoses without measuring between
them and then stopped to ask the GM to choose among three options, one of
which was simply to fix the defect.
MINOR: Principle XIV (Fix Defects Where You Find Them) ADDED (GM-directed,
2026-08-17): "anytime we are working on the diagram skill and you in the
course of implementing a feature come across some new defect - even if it is
a defect that did not have anything to do with what you were working on - I
would like you to fix it as part of that work ... in general, we should fix
bugs before writing new code." A defect found during a piece of work is
fixed in that work; the ONLY exception is one whose fix would be a complete
overhaul or a giant architectural change, which is deferred with the
measurement and the sketch. This deliberately NARROWS Principle XIII's
"ledgered, not fixed under someone else's feature": that clause governs the
MERGE BAR (a pre-existing failure does not block your push) and no longer
licenses ledgering a defect you found and could have fixed. New principle:
MINOR per the versioning policy. Motivating case: the /diagram paddy
size-floor work (2026-08-17), where three `settlement-review` findings -
lane frontage regressed past the engine's own recorded 94 ft threshold, the
three shared byres collapsing onto three farmsteads, and a windbreak clipped
with 23 clumps drawn wholly off-canvas - had nothing to do with paddy basin
size, and the GM directed that all three be fixed before the feature landed
rather than ledgered. The rationale in his words: keep the foundation rock
solid, then hold that level of functionality as the skill expands into new
settlement types.

Sections updated:
  - Core Principles: Principle XIV added; Principle XIII's "ledgered, not
    fixed" sentence now cross-references XIV so the two do not read as
    contradicting each other.

Templates requiring review/update:
  ✅ .specify/templates/plan-template.md - Constitution Check gains a
                              Principle XIV entry.
  ✅ CLAUDE.md - "Verification before reporting done" gains the
                              fix-what-you-find rule.
  ✅ .claude/skills/diagram/CLAUDE.md - the always-on list gains it, since
                              /diagram is where it bites hardest.
  ✅ .claude/skills/diagram/dev/reviews.md - states that a review finding
                              outside the delta is still yours to fix.

PRIOR (1.7.0 → 1.8.0):

PRIOR (1.8.0 → 1.9.0):
MINOR: Principle XII (Historical Grounding Bookends) gains two GM-directed
rules, 2026-08-18. (a) RESEARCH PRECEDES A RULING: a question about how a
place was actually built, farmed or lived in is answered by a research pass
BEFORE it reaches the GM, and an ask that does reach them must state what was
searched and why the finding does not settle it. Binds the review loop above
all, since a reviewer's "wants a one-line ruling" describes a question, not a
delegation. (b) TWO SUPPORTABLE ANSWERS BECOME A KNOB, NOT A CHOICE: where
research shows a thing was genuinely done more than one way, the variation
becomes a tunable per-settlement knob rather than a pick, because a project
goal is settlements within historical norms that differ from one another as
far as the research justifies - players must tell two maps apart at a glance.
This AMENDS the existing calibrated-liberty clause and takes precedence where
they differ; liberty survives only for a DEGREE along a continuum, never for a
choice between distinct FORMS. Motivating cases: the byre-beside-a-well and
back-rank-access questions, both of which had been queued as GM rulings and
were answered by a single research pass.

PRIOR (1.7.0 → 1.8.0):
MINOR: Principle XIII (No Known Regressions) ADDED (GM-directed,
2026-08-17): "never count our work as being done when there are known
regressions. Nothing should EVER be merged back into main if even one
single new regression was added." Two independently-binding halves - work
is not done while a known regression exists, AND nothing merges to main
carrying one. A regression is defined against a MEASURED baseline (taken on
unmodified code, in a detached worktree, never a stash); pre-existing
failures are explicitly NOT regressions and stay ledgered. The principle
enumerates what does NOT excuse one - smallness, "it is only a cohort
seed", having documented it, being net-positive, and the residue having
"rotated" under a re-roll - and names the only three exits: fix, revert, or
an explicit GM waiver for that specific regression. New principle: MINOR
per the versioning policy. Motivating case: the /diagram fan-toe needle fix
(2026-08-17), which resolved the GM-ruled sunburst on all four shipped
hamlets and 22 of 24 cohort seeds while regressing seeds 9 and 11 on
paddy_plot_seams_shared - net-positive, fully diagnosed, ledgered with an
implementation sketch, and under this principle still NOT mergeable.

Sections updated:
  - Core Principles: Principle XIII added.
  - Governance/Compliance: the stop-work ritual may commit in-clone but
    MUST NOT push a regressed state.

Templates requiring review/update:
  ✅ .specify/templates/plan-template.md - Constitution Check gains a
                              Principle XIII entry (baseline measured,
                              zero new regressions at merge).
  ✅ CLAUDE.md - "Verification before reporting done" gains the
                              no-regressions merge gate; the session-clone
                              stop-work ritual now states the push bar.
  ✅ .claude/skills/diagram/CLAUDE.md - the cohort-baseline rule now says
                              a rotated residue is not a defense.

PRIOR (1.6.1 → 1.7.0):
MINOR: Principle X clause 14 (Rosters That Restate Code Are Derived, Not
Maintained) added (GM-directed, 2026-08-16). Clause 13 says a large file
prompts the split question; clause 14 says a roster-shaped file - one whose
bulk restates declarations the code already carries - takes a different
fix entirely: census the consumed surface, move the roster's safety
property into a guard test proven to fire, then DERIVE the surface (star
imports for re-export __init__s, introspection/generation for derivable
registry rows) instead of maintaining or splitting the roster. Drawn from
feature 027 (check_village/__init__.py, 3,148 -> 63 lines, zero consumer
changes), the named exemplar. New rule: MINOR per the versioning policy.

Sections updated:
  - Core Principles: Principle X clause 14 added.

Templates requiring review/update:
  ✅ .specify/templates/plan-template.md - Principle X gate entry extended
                              with the clause-14 derive-don't-maintain
                              commitment.
  ✅ CLAUDE.md - "Files stay at human scale" operational mirror extended
                              with the clause-14 short form + the 027
                              exemplar pointer.

Deferred TODOs:
  - (carried) automated file-length check; clause 12's deferred
    expression-counting gate check.

PRIOR (1.6.0 → 1.6.1):
PATCH: Principle X clause 13 (Files Stay at Human Scale) clarified
(GM-directed, 2026-08-16): unit TEST files are covered exactly as source
files. The managed cost is context-window tokens, and a test file is loaded
under the same conditions as source - a session loads test_settlement.py to
modify one test the same way it loads settlement.py to use one function - so
nothing about being a test changes the economics, and tests get no
exemption. The ordered-data justification (a registry whose row order is the
execution contract) remains the only carve-out. Clarification of existing
reach, no new rule: PATCH per the versioning policy. Motivating case:
test_checks.py (11,475 lines) and test_settlement.py (7,123 lines), split by
feature 025 alongside settlement.py itself.

Sections updated:
  - Core Principles: Principle X clause 13 wording extended (tests
    included).

Templates requiring review/update:
  ✅ .specify/templates/plan-template.md - Principle X gate entry says
                              "source or test file".
  ✅ CLAUDE.md - "Files stay at human scale" operational mirror says tests
                              are covered.

Deferred TODOs:
  - Automated file-length check (flags source files past the threshold
    lacking a justification header) - recorded alongside clause 12's
    deferred expression-counting gate check.

PRIOR (1.4.2 → 1.5.0):
MINOR: Principle X (Python Discipline) materially expanded - clause 12
(Functions Stay at Human Scale) added (GM-directed, 2026-08-15). A function
past a few hundred logical statements is suspect; past ~1,000 it is a defect
unless an inline annotation justifies why it must remain one body. Measured
in logic units (statements/expressions), never raw lines, so wrapped strings
and long call signatures never force a split. The 10-line-function dogma is
explicitly rejected. Motivating case: check_village.py's gate() reached
12,944 lines one check at a time, and the cost surfaced as an architecture
problem (nothing inside it could be invoked separately) before anyone chose
it.

Sections updated:
  - Core Principles: Principle X clause 12 added.

Templates requiring review/update:
  ✅ .specify/templates/plan-template.md - Principle X gate entry now names
                              the function-scale clause.
  ✅ CLAUDE.md - spec-kit working-style + single-constitution notes land in
                              Development Workflow the same day.

Deferred TODOs:
  - Automated expression-counting gate check (fails past threshold unless
    the function carries the justification annotation) - recorded in
    Principle X clause 12 as future work, deliberately not implemented as
    part of the 2026-08-15 gate-registry feature.

PRIOR (1.4.1 → 1.4.2):
PATCH: Technical Standards runtime bump - Python 3.13 -> 3.14 (GM, 2026-07-20),
matching the new standard dev container; the Fly prod image, both lockfiles,
both pyproject.toml pins (webapp + diagram skill), and CLAUDE.md move together.
Also drops the stale note that the chargen webapp pinned 3.10 (it no longer
does). No principle changes.

PRIOR (1.4.0 → 1.4.1):
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

- **Generators: ONE ARTIFACT UNTIL IT WORKS, then the sweep** (GM 2026-08-23).
  A change to a generator is proven on a SINGLE named artifact first. The full
  cohort / pool sweep runs once, AFTER that artifact is fully working - never as
  the loop you iterate inside. Feature 126 is the case that produced this clause:
  a 48-map cohort was launched while the approach was still being tried out, one
  seed near-hung, and thirty minutes bought no result at all. A single hamlet
  rebuilds in well under a minute, so the same thirty minutes is thirty
  experiments instead of nothing.
  - The canonical hamlet is **Inashiro**, unless the feature names a better one
    and says why.
  - **EVERY STEP OF A FEATURE IS TWO STEPS** (GM 2026-08-23): get it working on
    the reference settlement, THEN get it working everywhere. A plan or task list
    that says only "make X work" is incomplete - it must say "make X work on the
    reference settlement" and, separately, "make X work across the pool". The
    second half is a distinct task with its own verification, not a footnote to
    the first.
  - **THERE IS ONE COMMAND, AND IT PICKS ITS OWN SCOPE** (GM 2026-08-23).
    `make maps` reads how the LAST run went and decides:

        last run PASSED -> the whole tier, reporting EVERY failure together
        last run FAILED -> the REFERENCE map alone, stopping at the FIRST
                           problem; only if it passes does it go on to the rest
        no last run     -> treated as FAILED

    **One piece of state drives both the scope and the verbosity**, and for the
    same reason: a failed previous run means you are mid-fix and want the fastest
    signal, so the run is narrow and stops early; a passed previous run means you
    are verifying breadth, so it is wide and collects everything - which is what
    `make done` already does. `SCOPE=reference` / `SCOPE=all` says what you mean
    when you know better; an adaptive default is right, but a tool that cannot be
    told the truth gets worked around instead of used.

    **There is deliberately NO second command.** An earlier version of this rule
    offered `make map` and `make full-hamlet-sweep` and relied on the session
    choosing correctly. A choice is a thing that gets chosen wrong under
    pressure: the reference-first rule was written into this constitution and
    violated by its own author six hours later, at a cost of five 10-12 minute
    four-map cycles chasing a defect the reference hamlet answered in 67 seconds.
    *"Just remembering to do the right thing always is much worse than having
    good tooling."*

    **Sequential is cheaper than it looks.** A reference run that passes costs
    about a minute before the wide run starts; a reference run that FAILS saves
    the wide run entirely. The apparent loss of parallelism is bought back many
    times over across a feature.

    **This is the general pattern for every settlement tier**, not a hamlet
    special case - `mapcheck.py` is a tier table, and villages, towns and cities
    each get a row and a named reference map as they gain live scripted gens.
  - **`make done` IS THE BACKSTOP, and it is why narrow defaults are safe.** The
    gate re-checks the whole pool, so a session that forgets the sweep entirely
    still cannot ship a map it broke. Cheap defaults trade no correctness - only
    the moment you find out.
  - The final sweep stays MANDATORY whenever shared code changed - this clause
    changes WHEN it runs, never WHETHER.
  - A feature that adds a KNOB owes one artifact per knob VALUE, not one per
    artifact in the pool: three maps, not forty-eight.

- **Generators: PERFORMANCE IS BOOKENDED, not remembered** (GM 2026-08-23).
  A spec-kit feature that touches the diagram generators records a performance
  snapshot BEFORE it changes anything and again BEFORE it ships:

      make perf LABEL=<NNN>-start     # first thing, on unmodified code
      make perf LABEL=<NNN>-end       # last thing, before the push
      make perf-report AGAINST=<NNN>-start

  Any seed more than **5% slower** must be diagnosed before the feature ships -
  the same 5% the project already treats as a whole-process speedup worth having,
  applied in the other direction. Diagnosed means explained and either fixed or
  accepted in writing with the number; it does not mean noticed.

  - **Seeds, not one map.** The reference hamlet is rolled across a fixed seed
    set, because a single seed can be pathologically good as easily as bad.
  - **The start snapshot is also a health check.** Read the trend before
    beginning: if performance has drifted since the last feature, the first work
    is finding out why, not adding to it.
  - Snapshots live one-file-per-run in `.claude/skills/diagram/dev/perf-log/`, so
    concurrent clones never conflict. Never edit or delete one.
  - This does not replace `GEN_TIME_BUDGETS`, which is a per-gen ceiling. This is
    a trend, and it answers the other question: is it getting slower, and when.

  Feature 126 is why this exists: it moved a stage and took one seed from 65s to
  160s, and nothing noticed until a 48-map cohort stalled a 20-worker pool for
  thirty minutes and was killed twice with no result.

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
    Motivating case: `check_village.py`'s `gate()` reached 12,944
    lines one check at a time, and the cost surfaced as an
    architecture problem - nothing inside it could be invoked
    separately - long before anyone would have chosen that shape.

13. **Files stay at human scale** (added v1.6.0, GM-directed 2026-08-15):
    a source file that has grown past roughly 1,000 lines prompts a
    question that MUST actually be asked: should this become a package
    of subfiles? The unit here is RAW LINES - deliberately unlike
    clause 12's logic units - because the motivating cost is token
    economy: a session that needs one function from a file pays
    context-window tokens for the whole file, and that cost scales with
    text, not logic. Unit TEST files are covered exactly as source files
    (clarified v1.6.1, GM-directed 2026-08-16): a test file is loaded
    under the same conditions as source - you load test_settlement.py to
    modify one test the same way you load settlement.py to use one
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
    rather than felt. Motivating case: `check_village.py` reached
    35,603 lines one check at a time and cost a full context window to
    consult; feature 024 split it into the `check_village/` package,
    the exemplar of the practice.

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
    question is per-fact, not per-file. Motivating case:
    `check_village/__init__.py`, 3,148 lines of import rosters plus a
    duplicate `__all__` restating what 18 submodules already
    declared, reduced to 63 derived lines by feature 027 with zero
    consumer changes - the exemplar; full method in
    `specs/027-init-star-imports/`.

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
It makes the variation a **tunable knob with per-settlement variance**, so a
map can be rolled either way and two maps can honestly differ.

The reason is a project goal, not a historical one: these maps exist for
players who must tell one settlement from another at a glance. *"One of our
goals in this map generation project is to be able to produce settlements which
are within historical norms while being as different from one another as is
justifiable by our historical research."* Every place where the record permits
two forms is therefore a place the generator can differ WITHOUT leaving those
norms - which is exactly the variation worth having, and picking one form
throws it away permanently.

So the ladder for any such question is:

1. **Research it.** If the record is decisive, implement what it says - there
   is no knob and no ruling (the `rape` rotation was decisive; so was the
   threshing yard's sun).
2. **If the record supports two or more forms, add the knob**, rolled per
   settlement like every other knob (`_knobs.py`, seeded from the map's own
   seed so a value depends only on (seed, knob name)). Record the range and
   its evidence where the knob lives.
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
artifact that was green and now is not, a cohort seed that passed and now
fails, a measured rate that went down. It is defined against a **measured**
baseline, never a remembered one: take the baseline on unmodified code (a
detached worktree, not a stash) before judging your own numbers.

**Pre-existing failures are NOT regressions** and do not block your merge.
The distinction is exactly "did this pass before my change", which is why the
baseline is mandatory rather than advisory. **But "not a regression" is not
"not your problem":** this clause governs the MERGE BAR only, and
**Principle XIV** governs what you do about a defect you actually found -
fix it in the work at hand, ledger it only when its fix would be an
architectural overhaul. Read the two together; taken alone, this paragraph
has been misread as a licence to ledger anything that predates the diff.

**What does NOT excuse a regression:**

- It is small, or it is one seed out of twenty-four.
- It is on a cohort seed, a fixture, or a map nobody ships. Every one of
  those is a test bed precisely because it stands in for the maps that are
  not written yet.
- It is *documented*. Writing a regression down is how it gets tracked; it
  is not how it gets permitted. A ledger entry is not a waiver.
- The change fixes more than it breaks. Net-positive is an argument for
  doing the work, never for merging it broken.
- **The residue "rotated".** In a seeded cohort a change that alters draw
  counts re-rolls every map, so failures move rather than persist in place.
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
stop-work ritual does not run to completion on a red or regressed state: a
session may commit inside its own clone (mid-task work is sacred) but MUST
NOT push to main. Where a domain has a cohort or sweep, its measured
before/after numbers are the evidence, and they belong in the commit message
or the feature's notes.

This principle is NON-NEGOTIABLE because main is the shared integration
point: a regression merged there is silently inherited by every other
session and by every artifact generated afterwards, and the person who pays
for it is never the person who introduced it. The trade "I gained a feature
and lost a check" is legible for about a day and invisible forever after.

### XIV. Fix Defects Where You Find Them (NON-NEGOTIABLE)

GM, 2026-08-17: *"anytime we are working on the diagram skill and you in the
course of implementing a feature come across some new defect - even if it is a
defect that did not have anything to do with what you were working on - I would
like you to fix it as part of that work ... in general, we should fix bugs
before writing new code."*

**The rule.** A defect discovered in the course of a piece of work is FIXED in
that piece of work, whether or not it has anything to do with the feature. Not
filed, not deferred to "its own pass", not handed to a future session - fixed,
in the same change, with the same verification every other fix gets.

**The one exception** is a defect whose fix would be a complete overhaul or a
giant architectural change: a stage reordering, a new subsystem, a rewrite of a
placement engine. Those are deferred - and deferring one is a real deliverable,
not a shrug: it carries the MEASUREMENT that establishes the defect, the
mechanism, and the implementation sketch, so the next session starts from
evidence rather than from a complaint. "This would take a while" is not the
exception; "this cannot be done without changing the architecture" is.

**Why this outranks the convenience of a tidy diff.** The reason is the GM's,
and it is about compounding: the value of this project's generators comes from
being able to expand them - new settlement tiers, new archetypes - on top of a
foundation whose behavior is known-good. Every defect left in place is a
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
the review subagents (`settlement-review`, `building-review`, `backstory-review`,
`frontend-review`), which are pointed at a DELTA and reliably find things
outside it - that is a feature of an independent reviewer, not scope creep by
it. A finding outside the delta is still yours. The same applies to a defect a
diagnostic surfaces, a number that looks wrong while measuring something else,
and a comment that turns out to describe code that no longer exists.

This principle is NON-NEGOTIABLE because the alternative is invisible: a
skipped fix costs nothing today, shows up as "the generator has always been a
bit off here" in a month, and is unattributable by the time it blocks a tier.

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
  is the same failure as stopping. (Feature 126, 2026-08-23, is the recorded
  case of both halves: four wrong diagnoses in a row, and then a stop to ask
  which of three options to take when one of them was "fix it".)

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

**Version**: 1.12.1 | **Ratified**: 2026-05-27 | **Last Amended**: 2026-08-23
