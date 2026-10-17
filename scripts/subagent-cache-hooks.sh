#!/usr/bin/env bash
# subagent-cache-hooks.sh - a Claude Code PreToolUse hook on the Agent tool that BLOCKS (once per
# session) a general-purpose subagent launch whose prompt repeats a large block of text an earlier
# launch in the same session already sent.
#
# GUARD_EDIT_OK: new guard (feature: subagent prompt caching, GM 2026-10-17).
#
# WHY (GM 2026-10-17; measured the same day from this project's subagent transcripts, full numbers in
# docs/subagent-caching.md): text repeated across subagent prompts was never read back from the cache,
# whatever order it was in. Nine shrine-text-review launches put a 5.4k-character shared rubric FIRST
# and only the file name LAST - the textbook order - and every first request read exactly the 17,178
# tokens of tools + system prompt and wrote ~41.7k fresh. Typed review agents read a flat 2-4k across
# launches with different prompts. The only reuse past the system prompt was a launch whose prompt
# was byte-identical to an earlier one. What DOES carry across launches is the agent's system prompt -
# the body of .claude/agents/<name>.md.
#
# So repeated text across launches is the mechanical signature of the mistake, and this hook looks for
# it: paragraphs (blank-line separated) of >= 200 characters already sent by an earlier launch this
# session, totalling >= 2,000 characters (~500 tokens). Paragraph hashing rather than a common-prefix
# check, because the shape the GM described (a unique sentence first, the shared block after it)
# has no common prefix at all.
#
# SCOPE: only general-purpose (or untyped) launches. A typed launch already has its instructions in
# its definition, and what it repeats is per-task context (the GM's request on each spec-fidelity
# round), which no launch shape can cache - so blocking it would teach bypassing. `fork` launches
# inherit the parent context by design and are never checked.
#
# It blocks ONCE per session: the fix (a new agent definition) registers only in the NEXT session, so
# a second block in the same session could only teach bypassing.
#
# ESCAPE HATCH: CACHE_OK in the prompt, with a reason. Checked FIRST, so the hook can never block its
# own repair.
#
# State: one small JSON file per session under ${TMPDIR:-/tmp}/claude-subagent-cache/.
# Tested by test-subagent-cache-hooks.sh - keep it green.
set -euo pipefail

MODE=${1:-pretool}
INPUT=$(cat 2>/dev/null || true)
[ "$MODE" = "pretool" ] || exit 0

STATE_DIR=${SUBAGENT_CACHE_STATE_DIR:-${TMPDIR:-/tmp}/claude-subagent-cache}
export STATE_DIR

printf '%s' "$INPUT" | python3 -c '
import hashlib, json, os, re, sys

MIN_PARA = 200      # shorter is boilerplate ("Report under 300 words."), not shared context
MIN_SHARED = 2000   # ~500 tokens: below this the repeated write costs less than a blocked turn
GENERIC = ("", "general-purpose", "claude")

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if data.get("tool_name") not in ("Agent", "Task"):
    sys.exit(0)
ti = data.get("tool_input") or {}
prompt = ti.get("prompt") or ""
if "CACHE_OK" in prompt or (ti.get("subagent_type") or "") not in GENERIC:
    sys.exit(0)

session = re.sub(r"[^A-Za-z0-9_-]", "_", str(data.get("session_id") or "nosession"))
path = os.path.join(os.environ["STATE_DIR"], session + ".json")
try:
    state = json.load(open(path))
except Exception:
    state = {"seen": [], "warned": False}

paras = [p.strip() for p in re.split(r"\n\s*\n", prompt) if len(p.strip()) >= MIN_PARA]
digest = {hashlib.sha1(p.encode()).hexdigest()[:16]: p for p in paras}
seen = set(state["seen"])
repeated = [p for h, p in digest.items() if h in seen]
shared = sum(len(p) for p in repeated)

state["seen"] = sorted(seen | set(digest))
block = shared >= MIN_SHARED and not state["warned"]
if block:
    state["warned"] = True
os.makedirs(os.environ["STATE_DIR"], exist_ok=True)
with open(path, "w") as f:
    json.dump(state, f)
if not block:
    sys.exit(0)

first = repeated[0][:120].replace("\n", " ")
sys.stderr.write(f"""BLOCKED (subagent-cache): this prompt repeats {shared:,} characters ({len(repeated)} paragraph(s)) that an
earlier Agent launch in this session already sent, starting: "{first}..."

Text repeated across subagent prompts is written to the cache on every launch and never read back -
putting it FIRST does not help (measured 2026-10-17: nine shrine reviews with a shared 5.4k-character
rubric first each read only the 17,178-token tools+system prefix and wrote ~41.7k fresh).

Fix, in order of preference:
  1. Shared INSTRUCTIONS (a rubric, a review procedure, house rules): move them into
     .claude/agents/<name>.md (with omitClaudeMd: true) and launch by subagent_type. The definition
     body is the subagent system prompt, which IS reused across launches. Keep the launch prompt to
     the varying part only ("review <file>"). A new or edited definition registers next session; for
     the rest of THIS session, re-send this launch with CACHE_OK and a reason.
  2. Shared CONTEXT the parent already holds, for work that does not need an independent reviewer:
     subagent_type "fork" reuses the parent conversation cache.
  3. Neither fits: re-send with CACHE_OK and a reason.

This blocks once per session. Escape: CACHE_OK in the prompt, with a reason.
(scripts/subagent-cache-hooks.sh; rules and measurements in docs/subagent-caching.md)
""")
sys.exit(2)
'
