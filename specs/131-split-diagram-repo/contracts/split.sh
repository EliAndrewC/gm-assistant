#!/usr/bin/env bash
# split.sh - feature 131: extract the diagram skill into its own repository, or prepare
# gm-assistant's post-split tree. ONE procedure, run on a throwaway for the rehearsal and then for
# real; the path list below IS the result, so it lives here, in the feature, not in a session's head.
#
#   split.sh diagram <src-repo> <dest>   fresh clone of <src-repo> at <dest>, history filtered to the
#                                        MOVE + COPY-TO-BOTH set, then the diagram-side edits, committed
#   split.sh gm      <src-repo> <dest>   fresh clone at <dest>, the MOVE set removed, gm-assistant-side
#                                        edits, committed
#
# Dispositions per spec.md FR-001 (MOVE / COPY TO BOTH / STAY). Deliberately verbose.
set -euo pipefail
MODE=${1:?diagram|gm} SRC=${2:?source repo} DEST=${3:?destination dir}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)          # specs/131-.../contracts
[ -e "$DEST" ] && { echo "refusing: $DEST exists" >&2; exit 1; }

STAY_SPECS="001-toolkit-shell 002-synthesize-backstory 003-campaign-character-context 004-synthesize-op-npc 011-dreams-section"
MOVE_SCRIPTS="make-only-hooks.sh _hookmatch.py test-make-only-hooks.sh"
MOVE_AGENTS="building-review.md settlement-review.md size-audit.md"
COPY_AGENTS="spec-fidelity.md"

git clone --quiet --no-local "$SRC" "$DEST"   # --no-local: a hardlinked clone is not "fresh" to filter-repo
cd "$DEST"
git config user.name "$(git -C "$SRC" config user.name)"; git config user.email "$(git -C "$SRC" config user.email)"
MOVE_SPECS=$(cd specs && ls -d */ | tr -d / | grep -vxF -f <(printf '%s\n' $STAY_SPECS))

case $MODE in
diagram)
  args=(--path .claude/skills/diagram --path .claude/settings.json --path scripts --path .specify
        --path container-scripts --path docs --path ruff.toml --path CLAUDE.md --path .gitignore --path LICENSE)
  for a in $MOVE_AGENTS $COPY_AGENTS; do args+=(--path ".claude/agents/$a"); done
  for s in $MOVE_SPECS; do args+=(--path "specs/$s"); done
  for k in .claude/skills/speckit-*; do args+=(--path "$k"); done
  git filter-repo --quiet "${args[@]}"
  # --- diagram-side edits ---------------------------------------------------------------
  cp "$HERE/CLAUDE.diagram.md" CLAUDE.md
  sed -i 's|/gm-assistant/scripts/|/diagram/scripts/|g' .claude/settings.json
  python3 - <<'PY'
import re
p='scripts/gate-stamp.py'; t=open(p).read()
t=t.replace('AREAS = {"diagram": ".claude/skills/diagram", "webapp": "webapp"}', 'AREAS = {"diagram": ".claude/skills/diagram"}  # the webapp area lives in gm-assistant since feature 131')
open(p,'w').write(t)
for p in ['.claude/agents/settlement-review.md','.claude/agents/building-review.md','.claude/agents/size-audit.md','.claude/skills/diagram/dev/gate.md','.claude/skills/diagram/CLAUDE.md']:
    t=open(p).read(); t=t.replace('/gm-assistant/.claude/skills/diagram/','/diagram/.claude/skills/diagram/').replace('/gm-assistant/.clones/','/diagram/.clones/'); open(p,'w').write(t)
p='.claude/skills/diagram/SKILL.md'; t=open(p).read()
t=t.replace("- `/gm-assistant/setting/village-headsmen.md`", "(gm-assistant is mounted read-only at `/gm-assistant`; on GitHub: <https://github.com/EliAndrewC/gm-assistant/tree/main/setting>)\n- `/gm-assistant/setting/village-headsmen.md`",1)
open(p,'w').write(t)
PY
  git add -A
  git commit --quiet -m "feature 131: the diagram skill becomes its own repository

Extracted from EliAndrewC/gm-assistant with git filter-repo, history preserved for every path
that moved. The internal layout is unchanged (.claude/skills/diagram/ at the same depth) so the
engine, the pool generators and the feature-127 guards did not move. Repository-level machinery
the two projects both need was copied; only the diagram-scoped guards and review agents moved.
Roots are derived from git in the ritual, the hooks and the Makefile guards, so nothing here
hardcodes /diagram except .claude/settings.json's hook paths."
  ;;
gm)
  git rm -r --quiet .claude/skills/diagram
  for s in $MOVE_SPECS; do git rm -r --quiet "specs/$s"; done
  for f in $MOVE_SCRIPTS; do git rm --quiet "scripts/$f"; done
  for a in $MOVE_AGENTS; do git rm --quiet ".claude/agents/$a"; done
  cp "$HERE/CLAUDE.gm-assistant.md" CLAUDE.md
  python3 - <<'PY'
import json
p='.claude/settings.json'; d=json.load(open(p))
gone=('make-only-hooks.sh',)   # gate-hooks and guard-file-hooks are COPY TO BOTH (spec FR-001, round 2)
for ev,entries in list(d.get('hooks',{}).items()):
    keep=[]
    for e in entries:
        e['hooks']=[h for h in e.get('hooks',[]) if not any(g in h.get('command','') for g in gone)]
        if e['hooks']: keep.append(e)
    d['hooks'][ev]=keep
json.dump(d,open(p,'w'),indent=2); open(p,'a').write('\n')
p='scripts/gate-stamp.py'; t=open(p).read()
t=t.replace('AREAS = {"diagram": ".claude/skills/diagram", "webapp": "webapp"}', 'AREAS = {"webapp": "webapp"}  # the diagram area lives in its own repository since feature 131')
open(p,'w').write(t)
# guard-file-hooks.sh left as is: its diagram-Makefile pattern simply never matches here.
# .gitignore: the diagram pool lines are inert without the directory; left as history.
PY
  git add -A
  git commit --quiet -m "feature 131: the diagram skill moved to https://github.com/EliAndrewC/diagram

Removed: .claude/skills/diagram, its 47 spec-kit feature directories, the diagram-scoped guards
(make-only-hooks and its companion) and the three diagram review
agents. Kept: every hook and script the content skills and the webapp use, spec-kit, the
constitution, the docs, the container setup. The webapp Makefile now runs hooks-test so the
retained guards keep being exercised (constitution XVIII)."
  ;;
*) echo "mode must be diagram or gm" >&2; exit 2 ;;
esac
echo "split.sh $MODE: done -> $DEST ($(git rev-list --count HEAD) commits)"
