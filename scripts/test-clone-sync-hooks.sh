#!/usr/bin/env bash
# test-clone-sync-hooks.sh - exercise the pretool guards in clone-sync-hooks.sh and the
# gm-assistant refusal in sync-with-main.sh. These hooks govern EVERY session (all sessions run
# main's copy of clone-sync-hooks.sh via the absolute path in .claude/settings.json), so a bug
# here can block all editing - this suite is the regression guard. Run it from anywhere:
#   scripts/test-clone-sync-hooks.sh
# It builds throwaway git repos, fake session-json files, and real/killed processes for liveness,
# drives the hooks through the CLONE_MAIN / CLONE_SESSIONS_DIR test seams, and asserts exit codes.
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
HOOK=$HERE/clone-sync-hooks.sh
RITUAL=$HERE/sync-with-main.sh
TMP=$(mktemp -d)
# NB: cleanup is done EXPLICITLY at the end, NOT via a `trap ... EXIT` - an EXIT trap also fires in
# the forked subshells that `&` background jobs and pipelines create, which would rm the fixtures
# mid-run (it did: standalone passed, `... | tail` wiped $TMP). A leaked /tmp dir on early abort is
# harmless.

FAILED=0
check() { # check <label> <expected-rc> <actual-rc>
  if [ "$2" = "$3" ]; then
    printf 'ok    %s (rc=%s)\n' "$1" "$3"
  else
    printf 'FAIL  %s (expected rc=%s, got rc=%s)\n      out: %s\n' "$1" "$2" "$3" "$OUT"
    FAILED=1
  fi
}

# ---- fixtures ---------------------------------------------------------------------------------
FMAIN=$TMP/main
git init -q "$FMAIN"
git -C "$FMAIN" config user.email t@t; git -C "$FMAIN" config user.name t
echo m0 > "$FMAIN/f"; git -C "$FMAIN" add f; git -C "$FMAIN" commit -qm m0
mkdir -p "$FMAIN/.clones/.session-clones"
MAPDIR=$FMAIN/.clones/.session-clones
SESS=$TMP/sessions; mkdir -p "$SESS"

mkclone() { git clone -q "$FMAIN" "$FMAIN/.clones/$1"; }   # a clone at main's current tip
mkclone miscellaneous
mkclone diagram-town
mkclone gm-assistant

# session-json fixtures: <pid>.json carries {id, name, nameSource}
sess() { printf '{"id":"%s","name":"%s"%s}' "$2" "$3" "${4:+,\"nameSource\":\"$4\"}" > "$SESS/$1.json"; }
sess 1001 sid-me miscellaneous            # named "miscellaneous" -> canon .clones/miscellaneous
sess 1002 sid-town "Diagram (town)"       # named -> canon .clones/diagram-town
sess 1003 sid-unnamed "Auto Title" derived  # derived title -> unnamed -> canon .clones/gm-assistant

# a LIVE process whose /proc cmdline names claude (via exec -a), and a DEAD one
bash -c 'exec -a claude-fake-live sleep 300' & LIVE_PID=$!
sess "$LIVE_PID" sid-live-other "Diagram (city)"
bash -c 'exec -a claude-fake-dead sleep 300' & DEAD_PID=$!
sess "$DEAD_PID" sid-dead-other "Diagram (hamlet)"
kill "$DEAD_PID" 2>/dev/null; wait "$DEAD_PID" 2>/dev/null || true

run() { # run <mode> <sid> <clonename> <file-under-clone> ; sets OUT/RC
  local fp="$FMAIN/.clones/$3/$4"
  OUT=$(printf '{"session_id":"%s","tool_input":{"file_path":"%s"}}' "$2" "$fp" \
        | CLONE_MAIN="$FMAIN" CLONE_SESSIONS_DIR="$SESS" "$HOOK" "$1" 2>&1); RC=$?
}

# ---- pretool scenarios ------------------------------------------------------------------------
OUT=$(printf '{"session_id":"sid-me","tool_input":{"file_path":"%s/README.md"}}' "$FMAIN" \
      | CLONE_MAIN="$FMAIN" CLONE_SESSIONS_DIR="$SESS" "$HOOK" pretool 2>&1); check "non-clone path ignored" 0 $?

run pretool sid-me miscellaneous a.txt;        check "canonical clone, clean, at tip, unclaimed" 0 "$RC"

printf '%s' "$FMAIN/.clones/miscellaneous" > "$MAPDIR/sid-live-other"
run pretool sid-me miscellaneous a.txt;        check "canonical clone claimed by a LIVE other session -> blocked" 2 "$RC"
rm -f "$MAPDIR/sid-live-other"

printf '%s' "$FMAIN/.clones/miscellaneous" > "$MAPDIR/sid-dead-other"
run pretool sid-me miscellaneous a.txt;        check "canonical clone claimed by a DEAD other session -> allowed" 0 "$RC"
rm -f "$MAPDIR/sid-dead-other"

run pretool sid-me diagram-town a.txt;         check "wrong (but valid) clone, clean -> name-routing block" 2 "$RC"

echo dirt > "$FMAIN/.clones/diagram-town/dirt"
run pretool sid-me diagram-town a.txt;         check "wrong clone but DIRTY -> grandfathered" 0 "$RC"
rm -f "$FMAIN/.clones/diagram-town/dirt"

run pretool sid-me gm-assistant a.txt;         check "editing forbidden gm-assistant clone -> blocked" 2 "$RC"
run pretool sid-unnamed miscellaneous a.txt;   check "unnamed session (resolves to gm-assistant) -> blocked" 2 "$RC"
run pretool sid-ghost miscellaneous a.txt;     check "unresolvable sid, clean, at tip, unclaimed -> allowed (fall-through)" 0 "$RC"

echo dirt > "$FMAIN/.clones/miscellaneous/dirt"
run pretool sid-me miscellaneous a.txt;        check "dirty canonical clone -> sacred, allowed" 0 "$RC"
rm -f "$FMAIN/.clones/miscellaneous/dirt"

# stale-base: a dedicated main advanced one commit past its clone
FMAIN2=$TMP/main2; git init -q "$FMAIN2"; git -C "$FMAIN2" config user.email t@t; git -C "$FMAIN2" config user.name t
echo a > "$FMAIN2/f"; git -C "$FMAIN2" add f; git -C "$FMAIN2" commit -qm a
mkdir -p "$FMAIN2/.clones"; git clone -q "$FMAIN2" "$FMAIN2/.clones/miscellaneous"
echo b > "$FMAIN2/f"; git -C "$FMAIN2" commit -qam b   # advance main past the clone
OUT=$(printf '{"session_id":"sid-me","tool_input":{"file_path":"%s/.clones/miscellaneous/a.txt"}}' "$FMAIN2" \
      | CLONE_MAIN="$FMAIN2" CLONE_SESSIONS_DIR="$SESS" "$HOOK" pretool 2>&1); check "canonical clone behind main -> sync-in block" 2 $?

# ...but a clone that is merely AHEAD of main (the normal state right after committing your own
# work, before the push back) must keep working. The equality test this replaced blocked it, which
# deadlocked every multi-commit work unit - GM-reported 2026-07-25, spec-kit's per-step commits.
FMAIN3=$TMP/main3; git init -q "$FMAIN3"; git -C "$FMAIN3" config user.email t@t; git -C "$FMAIN3" config user.name t
echo a > "$FMAIN3/f"; git -C "$FMAIN3" add f; git -C "$FMAIN3" commit -qm a
mkdir -p "$FMAIN3/.clones"; git clone -q "$FMAIN3" "$FMAIN3/.clones/miscellaneous"
git -C "$FMAIN3/.clones/miscellaneous" config user.email t@t; git -C "$FMAIN3/.clones/miscellaneous" config user.name t
echo c > "$FMAIN3/.clones/miscellaneous/f"; git -C "$FMAIN3/.clones/miscellaneous" commit -qam c  # clone ahead, tree clean
OUT=$(printf '{"session_id":"sid-me","tool_input":{"file_path":"%s/.clones/miscellaneous/a.txt"}}' "$FMAIN3" \
      | CLONE_MAIN="$FMAIN3" CLONE_SESSIONS_DIR="$SESS" "$HOOK" pretool 2>&1); check "canonical clone AHEAD of main, clean -> allowed" 0 $?

# a DIVERGED clone (each side has a commit the other lacks) is still stale and must block
git -C "$FMAIN3" commit -q --allow-empty -m d   # main advances too, after the clone's own commit
OUT=$(printf '{"session_id":"sid-me","tool_input":{"file_path":"%s/.clones/miscellaneous/a.txt"}}' "$FMAIN3" \
      | CLONE_MAIN="$FMAIN3" CLONE_SESSIONS_DIR="$SESS" "$HOOK" pretool 2>&1); check "canonical clone diverged from main -> sync-in block" 2 $?

# ---- sync-with-main.sh gm-assistant refusal ---------------------------------------------------
OUT=$(cd "$FMAIN/.clones/gm-assistant" && CLONE_MAIN="$FMAIN" "$RITUAL" sync-in 2>&1); RC=$?
check "ritual refuses to run from .clones/gm-assistant" 1 "$RC"
case $OUT in *"FORBIDDEN"*) : ;; *) echo "FAIL  ritual refusal message missing 'FORBIDDEN': $OUT"; FAILED=1 ;; esac

[ -n "${LIVE_PID:-}" ] && kill "$LIVE_PID" 2>/dev/null; true
rm -rf "$TMP"
echo "-----"
[ "$FAILED" = 0 ] && echo "all clone-sync-hook tests passed" || { echo "SOME TESTS FAILED"; exit 1; }
