#!/usr/bin/env bash
# Tests for deploy-secrets-hooks.sh. Run: scripts/test-deploy-secrets-hooks.sh (exit 0 = all green)
# Both directions: it FIRES on a clone whose secrets differ from or lack main's, and it PASSES when
# they match and outside a clone (main itself deploys from its own copy).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/deploy-secrets-hooks.sh"
PASS=0; FAIL=0
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

git init -q "$tmp/main" && mkdir -p "$tmp/main/webapp" && touch "$tmp/main/webapp/keep"
git -C "$tmp/main" add -A && git -C "$tmp/main" -c user.name=t -c user.email=t@t commit -qm init
git clone -q "$tmp/main" "$tmp/main/.clones/x"
M="$tmp/main/webapp"; C="$tmp/main/.clones/x/webapp"

check() { # label expected dir
  local rc; "$HOOK" check "$3" >/dev/null 2>"$tmp/err"; rc=$?
  if { [ "$2" = ok ] && [ "$rc" -eq 0 ]; } || { [ "$2" = blocked ] && [ "$rc" -ne 0 ]; }; then
    echo "  ok      $1"; PASS=$((PASS+1))
  else echo "  FAIL    $1 (expected $2, rc=$rc)"; FAIL=$((FAIL+1)); fi
}

echo "1. IT FIRES on a clone with stale or missing secrets"
printf '[a]\nk = new\n' > "$M/development-secrets.ini"
check "clone lacks the file"            blocked "$C"
printf '[a]\nk = old\n' > "$C/development-secrets.ini"
check "clone's copy differs"            blocked "$C"
grep -q "cp '$M/development-secrets.ini' '$C/development-secrets.ini'" "$tmp/err" \
  && { echo "  ok      the error carries the cp fix"; PASS=$((PASS+1)); } \
  || { echo "  FAIL    the error carries the cp fix"; FAIL=$((FAIL+1)); }
cp "$M/development-secrets.ini" "$C/"
printf 'FLY_API_TOKEN=a\n' > "$M/.env"; printf 'FLY_API_TOKEN=b\n' > "$C/.env"
check ".env differs"                    blocked "$C"

echo "2. IT PASSES when nothing is stale"
cp "$M/.env" "$C/"
check "clone matches main"              ok "$C"
check "main itself"                     ok "$M"
rm "$M/.env"
check "main has no .env: nothing to compare" ok "$C"

echo; echo "deploy-secrets-hooks: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
