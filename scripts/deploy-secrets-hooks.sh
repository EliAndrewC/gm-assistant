#!/usr/bin/env bash
# Deploy guard: a session clone deploys MAIN's gitignored secrets, never a stale copy of its own.
# Run by `make prepare-deploy` as: scripts/deploy-secrets-hooks.sh check <webapp dir>
#
# WHY (2026-10-18): the Dockerfile bakes webapp/development-secrets.ini into the image, and a clone's
# copy is copied from main once, when the clone is made (memory: "clone needs secrets"). Main's copy
# had since gained the /look-up key ([lookup] gemini_api_key); the shrines clone's had not, and its
# `make deploy` would have shipped production without it - a silent regression. Caught only because
# a cmp happened to run first. .env (FLY_API_TOKEN) is checked for the same reason.
#
# Main is the clone's origin (`git clone /gm-assistant .clones/<name>`); outside a clone this passes.
set -uo pipefail

[ "${1:-}" = check ] || { echo "usage: $0 check <webapp dir>" >&2; exit 2; }
dir="$(cd "${2:-.}" && pwd)"
root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" || exit 0
case "$root" in */.clones/*) ;; *) exit 0 ;; esac
main="$(git -C "$root" config --get remote.origin.url)"
[ -d "$main" ] || exit 0
rel="${dir#"$root"/}"

bad=0
for f in development-secrets.ini .env; do
  theirs="$main/$rel/$f"
  [ -f "$theirs" ] || continue
  if ! cmp -s "$theirs" "$dir/$f"; then
    echo "BLOCKED (deploy-secrets): $dir/$f is missing or differs from main's copy." >&2
    echo "  The image bakes it in, so deploying it would ship stale secrets. Fix:" >&2
    echo "    cp '$theirs' '$dir/$f'" >&2
    bad=1
  fi
done
exit "$bad"
