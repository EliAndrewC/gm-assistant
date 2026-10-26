# Feature 229: Retire project memories

**Feature Branch**: none (main, in a session clone)

**Created**: 2026-10-26

**Status**: Draft

**Input**: `request.md` (the GM's two messages, verbatim, and the audit they approved).

## Why

This is a one-person project. Claude Code's per-project memory is invisible to the repository, unreviewed, and loaded
whether or not it is still true, so it is the worst place for a rule: a rule belongs in a checklist or a doc where
the next session will read it, and a mistake that keeps recurring belongs in a hook or a test that makes it
impossible. The GM approved an audit of all 29 memories; this feature carries it out and then switches memory off.

## User Scenarios & Testing

### User Story 1 - Nothing a memory knew is lost (Priority: P1)

Every fact in the 29 memories that is still true and still needed ends up in the repository (or the GM's `l7r.md`),
at the place a session doing that work already reads.

**Acceptance**:
1. For each memory, the table below names its destination, and the destination contains the rule (with its "why"
   where the memory had one), or the memory is listed as already covered with the place that covers it.
2. Setting content does not narrate how it was decided (house style, `docs/l7r-style.md`); dev-history detail that
   the memory carried (dates of renames, logs of what was swept) is dropped unless a doc needs it.

### User Story 2 - Recurring mistakes become impossible, not remembered (Priority: P1)

The seven memories that worked around a process gap become tooling, each with a test that fails when the tooling is
removed (constitution XVIII: every guard has a test companion run by the gate).

**Acceptance**:
1. A fresh session clone can talk to Obsidian Portal and deploy without hand-copying secrets: clone setup copies
   `webapp/development-secrets.ini` and `webapp/.env` from main when they are missing; `flyctl` is installed by the
   container setup script. A missing-credentials OP read reports an error instead of answering "no characters".
2. `art.generate_prompt` carries the portrait steering lines (healed scars, daisho on the left hip for bushi, full
   figure with white space at head and feet, tabi and zori, "unmistakably a woman" for women), and the headshot crop
   pads the trimmed image with white so the crown is not clipped.
3. A session cannot end its turn while a `make done` it started in its clone is still running, or while its clone
   has commits that main lacks; the block message says exactly what to do. It never blocks twice in a row (no
   loop) and never blocks a session with no clone.
4. A session that works in a clone another LIVE session has claimed is told so, whether or not the tree is dirty:
   the 2026-07-26 incident was a "crashed" session still editing an uncommitted file, and the existing claim backstop
   runs only at a clean boundary, after the dirty-tree exit. It is a WARNING (never a block, so mid-task work is not
   stranded), given once per session per other claimant, naming the other session and saying to ask the GM before
   taking over.
5. Writing a local container path (`/host-l7r-repo/`, `/gm-assistant/`, `/workspace/`) into setting content is
   blocked, with the public GitHub URL forms in the message (l7r's branch is `master`). Setting content is this
   repository's `setting/`, `campaigns/`, `cosmology/`, `hooks/` and `notes/`, and EVERY file under the l7r repo
   (`setting/*.md` including `l7r.md` and `budgets.md`, `current/*.md` handouts). The rule checks text the session
   is writing, so it does not inherit the house-style hook's exemption for the GM's own files; only SOURCE blocks
   are skipped. Operational docs (CLAUDE.md files, `docs/`, scripts, specs, skills, code) keep their real paths.
6. The `frontend-review` agent flags hardcoded catalog counts in card blurbs and section copy.
7. A test prices Shizu's Shoda memorial design and fails when the price moves from the figure the player handout
   states, telling the session to re-price the handout (`current/shoda-shrine.md` in the l7r repo) and redeploy.

### User Story 3 - Memory is off and empty (Priority: P1)

**Acceptance**:
1. `.claude/settings.json` sets `autoMemoryEnabled: false`, so no session of this project loads or writes memory.
2. The project memory directory (`~/.claude/projects/-gm-assistant/memory/`) holds no memory files and no index.

### User Story 4 - The Fox secret libraries are canon (Priority: P2)

The GM vetted the Obsidian Portal page "Secret Libraries of the Fox"; its public body and its GM-only truth are in
`l7r.md` under The Fox Clan, converted from Textile to the file's Markdown. (Done before this spec was written.)

### Edge Cases

- A Stop event fired while the hook's own block is being answered (`stop_hook_active`) is allowed through.
- A clone with uncommitted edits but no unpushed commits: the turn-end hook does not block on that (out of the
  approved scope; the clone-sync hook already treats a dirty tree as mid-task work).
- The path rule skips a SOURCE block inside the written text (the GM's words), and never applies to operational
  files, which include every file that has to quote the forbidden form to state the rule.
- The Shoda handout lives in the GM's repo and may be absent (another machine): the test still pins the recorded
  figure and skips only the handout cross-check.

## Requirements

### Functional Requirements - the 29 memories

Delete outright (already covered, or finished history):

- **FR-001** speckit-answer-own-questions: covered by `docs/dev-workflow.md` ("Run the chain end-to-end, unattended").
- **FR-002** procedure-not-ritual: done; `scripts/sync-with-main.sh` header records the rename and why.
- **FR-003** two-empire-multipliers: covered by `budgets.md` "The two Empire-wide multipliers".
- **FR-004** synthesize-skill: covered by `webapp/CLAUDE.md` (tagline not in the API) and the code.
- **FR-005** money-section: covered by `webapp/l7r/money/CLAUDE.md`; the rest is feature history in `specs/222-224`.
- **FR-006** lookup-command: covered by `webapp/l7r/lookup/CLAUDE.md`; add one line there that 3.5 Flash-Lite scored
  97% on 149 entries but 87% on the full glossary, so do not switch without rerunning the eval.
- **FR-007** image-gen-fix-at-prompt: covered by `docs/generation-rules.md` (portrait bullet) and `art.py`.
- **FR-008** Kazuma/Harima rename: history; its rule moves with FR-013.

Into documentation:

- **FR-009** China-first geography, with "GM canon overrides it" and the Lion-only transport canals -> `docs/generation-rules.md`.
- **FR-010** foreign-term italics (usage rule, never inside code blocks) -> `docs/l7r-style.md`.
- **FR-011** "tax farming" not "corruption" -> `docs/l7r-style.md`.
- **FR-012** village shrines not temples (silently correct the GM's slip) -> `docs/generation-rules.md`.
- **FR-013** L5R compatibility stance (minimal term fixes; eta -> burakumin), no threshold without a basis, and check
  new example names for collisions against `l7r.md` and `budgets.md` -> `docs/generation-rules.md`.
- **FR-014** OP -> Toolkit cross-links (Textile, once per field, verify 200, never invent a mention) -> the OP part of
  `docs/l7r-style.md`, pointed at from `docs/note-intake.md`.
- **FR-015** bulk generation belongs in chat, not a toolkit screen -> `webapp/CLAUDE.md`.
- **FR-016** check before fix (a defect the GM names gets a red check first, diagnosis in the failure message) ->
  `docs/dev-workflow.md`.
- **FR-017** temple density canon (two major complexes per city, monk/initiate numbers, lay temple neighborhood, the
  temple sells its own sacred goods) -> `.claude/skills/temple/SKILL.md`.
- **FR-018** Discord repo split (gm-assistant writes OP; character-sheet owns rolls and slash commands; l7r holds the
  rules as text) -> `docs/key-paths.md`.
- **FR-019** Discord server layout (private game channels need a per-bot allow-view; the portal install link adds
  commands only; bot calls need a `DiscordBot` User-Agent) -> `webapp/l7r/mention/CLAUDE.md`.
- **FR-020** PC character-sheet ids (Shizu #10, Tadashi #14, others) -> `campaigns/wasp-bounty-hunters.md`.

Into tooling (User Story 2):

- **FR-021** clone secrets + loud OP credentials failure + flyctl in container setup.
- **FR-022** portrait steering lines + headshot padding in `art.py`.
- **FR-023** turn-end (Stop) hook: running gate or unpushed clone commits.
- **FR-024** another live session in the clone: a warning that also fires on a dirty tree.
- **FR-025** local container paths in setting content: house-style hook.
- **FR-026** no hardcoded counts in blurbs: `frontend-review` rule.
- **FR-027** Shoda design price pinned to the handout.

Then:

- **FR-028** Fox secret libraries into `l7r.md` (done).
- **FR-029** delete every memory file and `MEMORY.md`; set `autoMemoryEnabled: false` in `.claude/settings.json`;
  CLAUDE.md says in one line that this project keeps no memory and where things go instead.
- **FR-030** every new guard is added to the table in `docs/guards.md`, and the count in CLAUDE.md's Guards line is
  updated.

## Success Criteria

- **SC-001**: 29 of 29 memories accounted for (deleted as covered, moved, or tooled), and the memory directory is empty.
- **SC-002**: each of the tooling items has a test that fails with the tooling removed, run by `make done`.
- **SC-003**: `make done` is green.

## Resolved Decisions

- **Turn-end hook scope**: the approved two conditions only (running gate, unpushed commits). Dirty trees are not
  blocked, because a session that stops to ask the GM a question mid-task legitimately has uncommitted work.
- **Shoda test reads the handout when present**, pins the recorded total always.

## Assumptions

- `autoMemoryEnabled` is a Claude Code settings key (present in the installed 2.1.310 binary); a project-level
  `false` turns auto memory off for that project.
- The diagram repository keeps its own copies of China-first and temple density; this feature does not edit it.

## Review history

- **Round 1 (spec-fidelity, 2026-10-26): CHANGES REQUIRED.** (1) FR-024 claimed the claim backstop already covers a
  live session in the clone; it does not, because the hook exits on a dirty tree before reaching it, and the incident
  was a dirty tree. Now a warning that fires dirty or clean. (2) FR-025 would have inherited the house-style hook's
  `/host-l7r-repo` / `l7r.md` exemption and so never fired on `budgets.md`, the file where the GM first saw the
  problem. Now applies to every l7r-repo file. Turn-end scope and the Shoda handout skip ruled legitimate.
- **Round 2 (spec-fidelity, 2026-10-26): FAITHFUL (PASS).** Aside on the plan: a PreToolUse hook's stdout at exit 0
  is not shown to the model, so the FR-024 warning must travel by a channel the model sees (the hook's JSON
  `additionalContext`), and its test asserts that channel.
