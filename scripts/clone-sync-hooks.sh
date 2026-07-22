#!/usr/bin/env bash
# clone-sync-hooks.sh - Claude Code harness hooks enforcing the session-clone discipline.
#
# WHY (GM 2026-07-21): sync-in at the start of each work unit "has been getting skipped a lot and
# I'm not sure how to enforce it" - memory-dependent steps do get skipped, so the harness enforces
# them instead. Wired from .claude/settings.json (project settings, committed):
#
#   UserPromptSubmit -> `prompt` mode: every time the GM sends a message, this session's known
#     clone is auto-synced with main (git pull via sync-with-main.sh sync-in) - but ONLY when its
#     tree is clean; a dirty tree means mid-task, and yanking main's tip into half-done work would
#     be sabotage. Stdout is injected into the model's context, so the model also SEES the sync
#     happen (or why it was skipped).
#
#   PreToolUse (Edit|Write|NotebookEdit) -> `pretool` mode: at a CLEAN work-unit boundary it
#     enforces, in order: (0) FORBIDDEN NAME - '.clones/gm-assistant' is banned (it is the repo,
#     not a session), so a session that resolves or routes to it is stopped and the GM is asked to
#     name it; (1) NAME-ROUTING - a session may only edit in .clones/<its-own-name>, resolved from
#     its session_id via ~/.claude/sessions/*.json; (2) CLAIM BACKSTOP - that clone must not be one
#     another LIVE session already occupies; (3) STALE-BASE - the clone's HEAD must equal main's. A
#     DIRTY tree is mid-task work and is sacred: never blocked (would strand in-flight work), only
#     its clone->session claim is recorded so the prompt hook can find it.
#
# WHY name-routing (GM 2026-07-22): the 2026-07-22 incident - TWO named sessions ("miscellaneous"
# and "Diagram (town)") both ignored their own names and defaulted to .clones/gm-assistant, sharing
# one working tree, which interleaved their uncommitted work and contaminated a gate. The fix is to
# ROUTE each session to .clones/<its-own-name> (deterministic from session_id -> sessions json ->
# name) and block edits anywhere else. The GM keeps unique session names, so the claim backstop is
# only a safety net for an accidental concurrent duplicate name; it uses DETERMINISTIC liveness
# (session_id -> PID = the sessions-json filename -> /proc) so a PREVIOUS same-named session's stale
# claim (e.g. the GM reuses "miscellaneous" across sessions) never blocks a legitimate new one - only
# a genuinely LIVE concurrent claimant does. HEAD equality, not timestamps, is the freshness test:
# needs no clock and cannot rot. Renders are no longer synced into the clone at all - render-sync
# REGENERATES main's renders in place from main's tip, so nothing flows clone -> main.
set -euo pipefail

MAIN=${CLONE_MAIN:-/gm-assistant}                                    # CLONE_MAIN: test seam only
MAPDIR=$MAIN/.clones/.session-clones
SESSIONS_DIR=${CLONE_SESSIONS_DIR:-${HOME:-/home/agent}/.claude/sessions}  # CLONE_SESSIONS_DIR: test seam only
MODE=${1:-}
INPUT=$(cat 2>/dev/null || true)

field() { # field <dotted.path> - pull a string field out of the hook's stdin JSON
  printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for k in '$1'.split('.'):
        d = d.get(k, {}) if isinstance(d, dict) else {}
    print(d if isinstance(d, str) else '')
except Exception:
    print('')"
}

canonical_clone() { # canonical_clone <sid> - print .clones/<kebab-name> for a session, or "" if
  # the session_id resolves to no sessions-json entry (unresolvable -> caller falls through). An
  # entry with a derived/auto title or blank name is treated as UNNAMED -> the shared default,
  # matching CLAUDE.md's naming rule.
  SID="$1" MAIN="$MAIN" SDIR="$SESSIONS_DIR" python3 -c "
import glob, json, os, re, sys
sid, main, sdir = os.environ['SID'], os.environ['MAIN'], os.environ['SDIR']
if not sid:
    sys.exit(0)
name = source = None; found = False
for f in glob.glob(os.path.join(sdir, '*.json')):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    if sid in (d.get('id'), d.get('sessionId'), d.get('session_id')):
        found, name, source = True, d.get('name'), d.get('nameSource'); break
if not found:
    sys.exit(0)                       # unresolvable -> print nothing -> caller falls through
if source == 'derived' or not str(name or '').strip():
    name = 'gm assistant'             # unnamed / auto-derived -> shared default
kebab = re.sub(r'\s+', '-', re.sub(r'[^a-z0-9\s-]', '', str(name).lower()).strip())
if kebab:
    print(os.path.join(main, '.clones', kebab))"
}

sid_is_live() { # exit 0 iff a live process backs this session_id. The sessions-json FILENAME is the
  # session's PID; /proc/<pid> existing (cmdline naming claude, to survive PID reuse) means live.
  local sid="$1" pid
  pid=$(SID="$sid" SDIR="$SESSIONS_DIR" python3 -c "
import glob, json, os
sid, sdir = os.environ['SID'], os.environ['SDIR']
for f in glob.glob(os.path.join(sdir, '*.json')):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    if sid in (d.get('id'), d.get('sessionId'), d.get('session_id')):
        print(os.path.splitext(os.path.basename(f))[0]); break")
  case $pid in ''|*[!0-9]*) return 1 ;; esac              # no numeric pid -> treat as not live
  [ -r "/proc/$pid/cmdline" ] || return 1
  tr '\0' ' ' < "/proc/$pid/cmdline" | grep -q claude
}

claim() { # record clone<-session_id so the prompt hook can find this session's clone
  [ -n "$sid" ] || return 0
  mkdir -p "$MAPDIR"
  printf '%s' "$clone" > "$MAPDIR/$sid"
}

case $MODE in
  pretool)
    fp=$(field tool_input.file_path)
    case $fp in
      "$MAIN"/.clones/*/*) ;;
      *) exit 0 ;;  # not a clone file - this hook has no opinion
    esac
    rest=${fp#"$MAIN"/.clones/}
    clone=$MAIN/.clones/${rest%%/*}
    [ -d "$clone/.git" ] || exit 0
    sid=$(field session_id)
    dirty=$([ -n "$(git -C "$clone" status --porcelain 2>/dev/null)" ] && echo 1 || true)
    canon=$(canonical_clone "$sid")

    # DIRTY = mid-task work, sacred: allow (record the claim), never strand in-flight work on a
    # moving main. EVERY guard below is a clean-work-unit-boundary check only.
    if [ -n "$dirty" ]; then claim; exit 0; fi

    # --- clean work-unit boundary: enforce isolation before recording any claim ---

    # (0) 'gm-assistant' is a FORBIDDEN clone name (GM 2026-07-22): it is the repository, not a
    #     session, and being the old unnamed-default is exactly what made two sessions collide in
    #     it. A session that resolves to it has no distinct name; a session editing in it wandered
    #     into the forbidden workspace. Either way, stop and make the GM name the session.
    if [ -n "$canon" ] && [ "$(basename "$canon")" = "gm-assistant" ]; then
      echo "BLOCKED: this session has no distinct name - it resolves to the FORBIDDEN '.clones/gm-assistant' ('gm-assistant' is the repository, not a session workspace). Ask the GM to /rename this session to something distinct, then work in .clones/<that-name>.   (CLAUDE.md 'Session clones' - 'gm-assistant' is a forbidden clone name)" >&2
      exit 2
    fi
    if [ "$(basename "$clone")" = "gm-assistant" ]; then
      echo "BLOCKED: '.clones/gm-assistant' is a FORBIDDEN clone name ('gm-assistant' is the repository, not a session). Work in .clones/<your-session-name>${canon:+ (this session resolves to $canon)}.   (CLAUDE.md 'Session clones' - 'gm-assistant' is a forbidden clone name)" >&2
      exit 2
    fi

    # (1) NAME-ROUTING: a session may only edit in .clones/<its-own-name>. Unresolvable -> skip.
    if [ -n "$canon" ] && [ "$clone" != "$canon" ]; then
      echo "BLOCKED: this session's clone is $canon (resolved from its session name); the edit targets $clone. Two sessions must never share a working tree (the 2026-07-22 collision). Work in $canon - if it does not exist: git clone /gm-assistant $canon && cd $canon && git config user.name \"\$(git -C /gm-assistant config user.name)\" && git config user.email \"\$(git -C /gm-assistant config user.email)\" && scripts/sync-with-main.sh sync-in   (CLAUDE.md 'Session clones' - name-routing guard)" >&2
      exit 2
    fi

    # (2) CLAIM BACKSTOP: another LIVE session already occupying this clone (only possible via a
    #     concurrent duplicate session name). A dead/previous claimant is ignored, so sequential
    #     reuse of a generic name like "miscellaneous" is fine.
    if [ -n "$sid" ] && [ -d "$MAPDIR" ]; then
      for m in "$MAPDIR"/*; do
        [ -f "$m" ] || continue
        other=$(basename "$m")
        [ "$other" = "$sid" ] && continue
        [ "$(cat "$m" 2>/dev/null)" = "$clone" ] || continue
        if sid_is_live "$other"; then
          echo "BLOCKED: $clone is already occupied by another live session ($other) - two sessions must not share a working tree. Ask the GM to /rename one session distinctly and use its own clone.   (CLAUDE.md 'Session clones' - claim backstop)" >&2
          exit 2
        fi
      done
    fi

    # (3) claim, then the stale-base check.
    claim
    if [ "$(git -C "$clone" rev-parse HEAD 2>/dev/null)" != "$(git -C "$MAIN" rev-parse HEAD 2>/dev/null)" ]; then
      echo "BLOCKED: $clone has a clean tree (a new work unit) but its HEAD is behind main - new work must not build on a stale base. Run: cd $clone && scripts/sync-with-main.sh sync-in   (CLAUDE.md 'Session clones' / sync-in rule)" >&2
      exit 2
    fi
    exit 0
    ;;
  prompt)
    sid=$(field session_id)
    [ -n "$sid" ] && [ -f "$MAPDIR/$sid" ] || exit 0  # no known clone yet - silent (the pretool backstop covers the first edit)
    clone=$(cat "$MAPDIR/$sid")
    [ -d "$clone/.git" ] || exit 0
    if [ -n "$(git -C "$clone" status --porcelain 2>/dev/null)" ]; then
      echo "clone-sync: $clone has uncommitted work (mid-task) - auto sync-in skipped; finish and run sync-with-main.sh done"
      exit 0
    fi
    if out=$(cd "$clone" && scripts/sync-with-main.sh sync-in 2>&1); then
      echo "clone-sync: auto-synced $clone with main (git)"
    else
      echo "clone-sync: auto sync-in FAILED in $clone - resolve before modifying the repo: $(printf '%s' "$out" | tail -2)"
    fi
    exit 0
    ;;
  *)
    echo "clone-sync-hooks: unknown mode '$MODE' (want: prompt | pretool)" >&2
    exit 1
    ;;
esac
