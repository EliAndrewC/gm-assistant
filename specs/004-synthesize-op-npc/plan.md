# Implementation Plan: /synthesize skill for existing Obsidian Portal NPCs

**Branch**: `main` (feature branch `004-synthesize-op-npc` deferred to GM) | **Date**: 2026-07-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-synthesize-op-npc/spec.md`

## Summary

Add a Claude Code skill `/synthesize <character name>` that produces a Gemini
backstory for an NPC that already exists on the campaign wiki (Obsidian Portal) -
the chat-session twin of the webapp's "Synthesize Backstory" button. The skill
resolves an approximate name to an OP character, gathers the character's data
(including the OP **tagline** / one-line summary, which the OAuth JSON API does
not expose and which carries relationship cues like "drinking companion of
Kyoma"), runs the exact same per-caste corpus + campaign-context synthesis the
webapp uses, presents the result with a review (upload as-is, regenerate, or
upload with typed changes), and - on
approval - merges the backstory into the character's GM-only notes under a
delimited marker without disturbing existing notes.

The technical approach keeps all network I/O (OP page fetch, character PATCH) as
thin, fail-soft boundary functions in the grace-listed `chargen/op.py`, and puts
all decision logic (name matching, caste inference, tagline HTML parsing,
related-character extraction, and the marked-section merge) in one new pure-logic
module, `chargen/opsynth.py`, that is fully typed and 100%-covered. The skill
file itself (`.claude/skills/synthesize/SKILL.md`) is orchestration: it calls the
Python building blocks via short scripts and drives the review menu.

## Technical Context

**Language/Version**: Python 3.13 (matches the webapp; skill markdown is plain text)

**Primary Dependencies**: existing project modules only - `chargen/synthesis.py`,
`chargen/brief.py`, `chargen/opcache.py`, `chargen/op.py`; `google-genai` (already
used); `requests` (already used, for the OP browser session). No new third-party
dependency.

**Storage**: OP character records (remote, via existing API/session). A small
gitignored session-local tagline cache (`webapp/opcache/taglines.json`) mirroring
the existing opcache pattern, for the P3 related-character lookup. No new database.

**Testing**: pytest + pytest-cov. New pure logic (`opsynth.py`) at 100% line
coverage. New `op.py` boundary functions tested against saved fixtures - a real
OP character-page HTML snippet and a character JSON - not transport mocks.

**Target Platform**: the Claude Code dev container (the same environment that runs
the webapp and the note-intake workflow), with OP credentials and the Gemini key
configured in `development-secrets.ini`, and the setting corpus on the mount.

**Project Type**: Claude Code skill + supporting Python helper (CLI-style, invoked
from chat). No web UI.

**Performance Goals**: interactive - a single synthesis is one Gemini call
(seconds); the P3 related-character scan is bounded by the cast size (~81) and is
incremental/cached so it is paid once, not per run.

**Constraints**: must not clobber existing GM notes on save (idempotent
marked-section merge); must fail safe when OP or the corpus is unavailable; must
reuse the webapp's synthesis context verbatim so chat and web results are
equivalent.

**Scale/Scope**: one campaign, ~81 cast members; one new ~150-line pure module,
~2 new `op.py` boundary functions, one skill file, and their tests/fixtures.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design (below).*

- **I. Accessibility-First Viewports**: **N/A** - no UI. The feature is a chat
  skill; it renders no webapp page, HTML, or embedded preview.
- **II. Bold, Intentional Design**: **N/A** - no new UI surface or typography.
- **III. Pool Data Conventions**: **N/A** - the output is a per-character
  backstory written to one OP record, not recurring pool content; nothing is
  added under `/.claude/skills/<skill>/pool/`.
- **IV. One Canonical Home for GM Source**: **N/A** - adds/moves no
  `SOURCE`-marked blocks.
- **V. Protecting the GM's Writing (NON-NEGOTIABLE)**: **PASS** - the feature
  touches no `SOURCE`-marked content. Its OP write is guarded by a marked-section
  merge that preserves every pre-existing GM note verbatim and only ever
  replaces its own delimited block (FR-010, FR-011); a save failure leaves notes
  untouched (FR-013).
- **VI. Verify Before Reporting Done**: **PASS** - the plan commits to `pytest`
  + `--cov-fail-under=100` on `opsynth.py`, fixture-based tests for the `op.py`
  boundary additions, and a read-only end-to-end spot-check against a real OP
  character (resolve + tagline fetch + synthesis) plus one reversible round-trip
  save-and-verify before the skill is reported done.
- **VII. De-Localized Generation by Default**: **N/A** (explicit-scoping
  exception) - the GM names a specific existing campaign NPC; the backstory is
  session/campaign content by request and never enters a pool.
- **VIII. Direct Voice Over Framing Distance**: **N/A** - voice is governed by
  the existing synthesis instructions, which this feature reuses unchanged; it
  adds no new in-world institutional writing.
- **IX. Setting Integration**: **PASS** - reuses the exact corpus + per-caste
  supplement + campaign-cast context from `brief.py`/`opcache.py`; invents no
  setting facts beyond what synthesis already does, and keeps the new NPC
  consistent with the cast via the campaign-context block.
- **X. Python Discipline (NON-NEGOTIABLE)**: **PASS** - `opsynth.py` is new
  production code: fully typed, `ruff check` + `ruff format --check` +
  `mypy --strict` clean, red-green TDD, `pytest --cov-fail-under=100`. OP network
  calls are fail-soft boundary functions in `op.py` (grace-listed), tested via
  saved fixtures, not transport mocks. No new dependency (so no
  `requirements.in`/`.txt` change). No `print` (uses `logging`), no swallowed
  exceptions, behavior-named + parametrized tests, no hardcoded magic (marker
  strings and cache path are module constants).

No gate is DEFERRED and no gate fails; **Complexity Tracking is empty**.

## Project Structure

### Documentation (this feature)

```text
specs/004-synthesize-op-npc/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (function + skill-command contracts)
│   ├── opsynth.md
│   ├── op-boundary.md
│   └── skill-command.md
└── tasks.md             # Phase 2 output (/speckit-tasks - not created here)
```

### Source Code (repository root)

```text
gm-assistant/
├── .claude/skills/synthesize/
│   └── SKILL.md                     # NEW: the /synthesize skill (orchestration)
└── webapp/chargen/
    ├── opsynth.py                   # NEW: pure logic - match, caste, tagline
    │                                #      parse, related-cast, notes merge
    ├── test_opsynth.py              # NEW: 100%-covered unit tests
    ├── op.py                        # EDIT: + fetch_character_page (boundary),
    │                                #       + tagline cache refresh helper
    ├── test_op.py                   # EDIT/NEW: fixture-based boundary tests
    └── fixtures/
        ├── op_character_page.html   # NEW: saved real OP page (tagline present)
        └── op_character.json        # NEW: saved real character JSON
```

**Structure Decision**: Single existing project (the chargen webapp package holds
the reusable Python; the skill lives under `.claude/skills/` like every other
skill). All new decision logic is concentrated in one pure module so the
coverage gate is meaningful; the only new I/O is two thin `op.py` functions.

## Complexity Tracking

No constitutional violations; no entries.
