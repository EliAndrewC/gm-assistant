# Research: feature 131 - the split

Everything below was checked in the clone on 2026-08-24; commands are quoted so they can be re-run.

## R1 - What moves, by census

| set | how found | count |
|---|---|---|
| the skill | `.claude/skills/diagram/` | 1 directory, ~1,100 commits touch it (`git rev-list --count HEAD -- .claude/skills/diagram`) |
| diagram spec-kit features | every `specs/*/spec.md` matching `diagram|hamlet|village|settlement|provincial|pool/(hamlets|...)|check_village|magistracy|compound` | **46 of 51**; the 5 that stay: `001-toolkit-shell`, `002-synthesize-backstory`, `003-campaign-character-context`, `004-synthesize-op-npc`, `011-dreams-section`. A by-hand pass over the 46 is a task (the keyword net could catch a webapp feature that mentions a map) |
| repo-level scripts that are DIAGRAM-ONLY (they MOVE) | `grep -l diagram scripts/*`, minus the ones the content skills also use | 6 files + companions: `guard-file-hooks.sh`, `gate-hooks.sh`, `make-only-hooks.sh`, `_hookmatch.py`, `review-gate.sh`, `gate-stamp.py` |
| scripts the content skills still need (COPY TO BOTH) | the rest of `scripts/`, plus `sync-with-main.sh` and `check-duplicate-defs.py` which both sides use | `clone-sync-hooks.sh`, `house-style-hooks.sh`, `source-block-hooks.sh`, `readme-hooks.sh`, `repo-safety-hooks.sh`, `no-branch-hooks.sh`, `no-poll-hooks.sh`, `batching-hooks.sh`, `sync-with-main.sh` (its render-sync half becomes a no-op in gm-assistant), `launch-container.sh`, `check-duplicate-defs.py`, plus companions |
| hook wiring | `.claude/settings.json` | 13 hook entries, all `/gm-assistant/scripts/...` absolute paths - **the path prefix is what breaks first in a new repo** (R4) |
| container | `container-scripts/setup-dev-env.sh`, `append-system-prompt.md` | resvg / DejaVu / Playwright are diagram needs; the webapp needs Playwright too |
| docs | `docs/` | `iteration-loop.md`, `session-clones.md`, `container.md`, `spec-kit-and-reviews.md` are diagram-centric; `l7r-style.md` is content |
| memory | `grep -l diagram ~/.claude/projects/-gm-assistant/memory/*.md` | 32 of the notes; 16 index lines |

## R2 - History extraction: `git filter-repo`, on a fresh clone, by path list

**Verified**: `git-filter-repo` installs (`pip install git-filter-repo`, done in this session) and
is the tool git's own documentation recommends over `filter-branch`. It rewrites a FRESH clone in
place (it refuses to run on a repository with a remote, which is a safety feature - clone, filter,
then add the new remote). Invocation shape:

```
git clone /gm-assistant /tmp/split && cd /tmp/split
git filter-repo --path .claude/skills/diagram --path scripts --path .specify \
                --path container-scripts --path docs --path ruff.toml --path CLAUDE.md \
                --path specs/0NN-... (x46)
```

Commits that touched none of those paths vanish; commits that touched some keep only those
changes. `git log --follow` on any kept file shows its full history. **Rehearsal is mandatory
(FR-011)** because the path list is the whole result: a path missed is a file with no history, and
the moment other sessions clone the new repository the extraction is effectively frozen.

## R3 - The identical layout is what makes the engine indifferent to the move

**Verified**: every pool generator bootstraps with `SKILL = dirname(dirname(HERE))`; `_invocation.py`
resolves the repository root from its own file; `make-only-hooks.sh` and `guard-file-hooks.sh`
match `*/.claude/skills/diagram/...` suffixes, not absolute prefixes; the Makefile references
`../../../scripts/...` relatively. Keeping `.claude/skills/diagram/` at the same depth means all of
that keeps working with zero edits. Promoting to the root would touch every one.

## R4 - What DOES break on a new path, and it is short

`grep -rn '/gm-assistant' .claude/settings.json scripts/ container-scripts/ docs/ CLAUDE.md
.claude/skills/diagram/Makefile` - the absolute-prefix references:

- `.claude/settings.json`: 13 hook commands `/gm-assistant/scripts/...`
- `scripts/sync-with-main.sh`: `MAIN=${CLONE_MAIN:-/gm-assistant}`
- `scripts/clone-sync-hooks.sh`: the same root and the `.clones/` convention
- the diagram `Makefile` `guard` target: `case "$(CURDIR)" in /gm-assistant/.clones/*)`
- `docs/container.md`, `scripts/launch-container.sh`: the mount
- `container-scripts/append-system-prompt.md`: prose

**Decision**: the new repository mounts at `/l7r-diagram` (matching the name assumption) and each
of the above gets the new root. Better still where it is cheap: derive the root from
`git rev-parse --show-toplevel` so the next move is free - a task, applied where the script does
not already do it.

## R5 - The `l7r` namespace after the split

**Verified**: `webapp/l7r/app.py` and both `test_namespace_portion.py` files describe the shared
portion; `grep -rn 'l7r.diagram' webapp --include=*.py` finds only those comments and tests - no
runtime import. After the split, `webapp/l7r/` and `.claude/skills/diagram/l7r/` are never on one
`sys.path`, so each repository's guard test (no `__init__.py`) stays true and useful. Nothing to
build; one comment to update in each.

## R6 - Memory is keyed by project path

`/home/agent/.claude/projects/-gm-assistant/memory/` is derived from the working directory. A
session opened in `/l7r-diagram` gets `/home/agent/.claude/projects/-l7r-diagram/memory/`, empty.
The 32 diagram notes and their index lines are COPIED there (the split note and the clone-workflow
note are needed in both). Verified by inspecting the directory naming convention in this session's
own scratchpad path.

## R7 - CodeBuild repoints with the session's own key

**Verified**: `gm-assistant-ci` has `codebuild:UpdateProject` on both projects (granted in this
session's bootstrap), so `GITHUB_REPO` and the buildspec source change without the admin key. The
fine-grained PAT is repository-scoped and cannot be widened - the GM generates a new one for the
new repository and pastes it into the existing secret; the `main` ruleset is per repository and
the GM creates it (two clicks, documented in feature 130's earlier conversation).

## R8 - Spec-kit has no dependency mechanism

**Verified**: `.specify/scripts/bash/check-prerequisites.sh` checks only the current feature's own
artifacts; `common.sh` resolves one active feature; nothing reads another feature's state. The
convention adopted: a `**Blocked by**: NNN-slug` line in the dependent spec's header, and a `T000`
task in its `tasks.md` that verifies the blocker's completion marker. Cheap to enforce later with a
`review-gate`-style grep, if wanted.
