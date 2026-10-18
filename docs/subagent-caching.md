# Subagent prompt caching

*Project reference, split out of [`../CLAUDE.md`](../CLAUDE.md) so it is loaded on demand.*

**Load this file when:** writing or editing a `.claude/agents/*.md` definition, launching more than
one subagent with shared instructions or context, writing a `Workflow` script, hitting a
`subagent-cache` hook block, or writing code that sends a large prompt to any LLM API.

---

## The rule, short

1. **Shared instructions go in an agent definition, never in the launch prompt.** The definition
   body is the subagent's system prompt, and that is the only part of a subagent's context reused
   across launches. The launch prompt carries only what varies ("review /tmp/x.txt").
2. **Every definition sets `omitClaudeMd: true`** and restates, in its own body, any project rule it
   enforces. Asserted by `webapp/tests/test_agent_definitions.py`.
3. **Prefer a typed agent to `general-purpose` for anything launched repeatedly.** A general-purpose
   launch writes ~41-69k tokens to the cache before it does any work (all its tools, every
   CLAUDE.md, a ~24KB environment block); a typed agent with `omitClaudeMd` writes ~2.6k on a
   repeat launch. Trimming CLAUDE.md and excluding clone copies (below) shrinks the general-purpose
   figure but does not close that gap.
4. **Putting shared text FIRST in a launch prompt does not make it cache.** It is the right shape for
   a raw API call with your own breakpoint, and it does nothing here. Enforced for general-purpose
   launches by [`scripts/subagent-cache-hooks.sh`](../scripts/subagent-cache-hooks.sh).
5. **Context the parent already holds, for work that needs no independent reviewer: `fork`.** A fork
   reuses the parent's cached conversation. Review agents must NOT be forks (Principle I: the author
   is not a reliable reviewer, and a fork is the author).

## What was measured (2026-10-17)

From the `usage` blocks of every subagent transcript under `~/.claude/projects/-gm-assistant*`
(script: read the first assistant record's `cache_read_input_tokens` /
`cache_creation_input_tokens`).

**Before:**

| launch | first request reads | first request writes |
|---|---|---|
| spec-fidelity, 35 launches | avg 1.8k | avg 34.3k |
| frontend-review, 7 | avg 1.2k | avg 34.5k |
| backstory-review, 6 | avg 3.4k | avg 38.4k |
| shrine-text-review via general-purpose, 9 launches, shared 5.4k-char rubric FIRST | 17,178 every time | ~41.7k every time |

Typed review prompts were 660-1,337 characters, so almost all of the ~34k was not the prompt. It was
the CLAUDE.md files that non-fork subagents load by default (project 64.7KB + user 8.5KB, ~18k
tokens) plus the rest of the injected context. Reads stayed flat at the tools + system prompt size
whatever the prompts said. The one exception: a launch whose prompt was byte-identical to an earlier
one read everything (58,924 read, 0 written).

**After `omitClaudeMd: true`**, measured in a fresh `claude -p` session (definitions register at
session start, so a mid-session edit cannot be measured in the session that made it):

| launch | reads | writes |
|---|---|---|
| frontend-review, first launch | 0 | 6.9k (the whole context) |
| frontend-review, repeat launch | 4.3k | 2.6k |
| general-purpose (still loads CLAUDE.md and every tool) | 0 | 69.1k |

So a typed launch went from ~34k written to ~2.6k, about 13x less.

## Why: the request a subagent actually sends (measured 2026-10-17, Claude Code 2.1.302)

Captured with a logging reverse proxy on `ANTHROPIC_BASE_URL` (a small Python `ThreadingHTTPServer`
that saves each `/v1/messages` body and streams the response through). A subagent's first request is:

| position | content | cache breakpoint |
|---|---|---|
| tools | the agent's tool list (31 tools for general-purpose, 3 for a typed reviewer) | - |
| `system` | billing header, SDK line, then the agent's own prompt (the definition body; ~2.7k chars for general-purpose) | yes, 5-minute TTL |
| first user message | [CLAUDE.md block] [user context] [attribution] [the launch prompt] | **none** |
| a system-role message | the Environment block (cwd, skills list, agents list: ~24KB general-purpose, ~3KB typed) | yes, at its end |

So there is no breakpoint between the CLAUDE.md block and the launch prompt, and none before the
launch prompt at all. The second launch's request can reuse only what an earlier request wrote at
a breakpoint, which is the end of `system` (and the end of an entire identical first message). That
is the whole mechanism behind every number above: the measured reads are exactly tools + system.

**What the CLAUDE.md block held in a clone: both copies.** A session whose cwd is a clone loads
`/gm-assistant/CLAUDE.md` as an ancestor AND the clone's own `CLAUDE.md`: 142KB of near-duplicate
text in every general-purpose subagent and every clone session. A main-cwd session (the usual shape)
picks up the clone copy as a nested file the first time it touches the clone. Fixed by
`"claudeMdExcludes": ["**/.clones/*/CLAUDE.md"]` in `.claude/settings.json`: measured through the
proxy, the block dropped to 75KB (user + main CLAUDE.md only) in both the session and its
general-purpose subagent. The cost: a session reads MAIN's CLAUDE.md, so an edit to it in a clone
reaches sessions only after it is pushed.

**After the trim and the exclude** (same proxy, a session started in `/gm-assistant` like the GM's
usual sessions, 2026-10-17): the CLAUDE.md block is 31KB (user CLAUDE.md + the trimmed project
CLAUDE.md + MEMORY.md); the session's first request is 54k tokens in all, and a general-purpose
subagent's first request writes 46.6k (was ~58.9k from main, ~86.9k from a clone).

**Not reproduced:** two earlier general-purpose launches with different prompts both read exactly
48,505 and wrote 10,413. The structure above does not explain an intermediate match; the probe runs
did not show one again.

## Settings priced and declined

- **1-hour subagent cache TTL** (`experimental.cacheTtl: 1h` in a definition, or
  `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL`). Subagents default to 5 minutes. Same-type launches here
  come either in clusters 1-3 minutes apart, which the 5-minute TTL already covers, or 19-48 minutes
  apart between features. The 1-hour TTL makes EVERY write the subagent makes during its run cost
  2x instead of 1.25x (a review run writes ~160k tokens over its turns), in exchange for keeping a
  ~4k-token prefix warm. That is a loss. Declined 2026-10-17; asserted by
  `test_no_agent_sets_a_one_hour_cache`.
- **A hook on typed launches.** A typed launch repeats per-task context (the GM's request on each
  spec-fidelity round). No launch shape can cache that, so a block there would only teach bypassing.
  The hook checks general-purpose launches only.

## Parallel launches

A cache entry is readable only once the request that writes it has started streaming, so agents
launched in one message all write the shared prefix. **Do not hand-stagger** (one now, the rest next
turn): another session measured it as a loss, and the numbers agree. The extra main-session turn
re-reads the whole session context, median 253k tokens here (last 30 sessions, 2026-10-17), about 25k
token equivalents at the cache-read price; the prefix it saves is about 4k per extra typed agent.

`Workflow` staggers by itself with no extra turn. Measured in julie-medical's one run (2026-10-11):
the first agent wrote 35.5k, and the four started 0.6-1.5 s later each read 18.9k and wrote about
16.6k. It pays for waves of 4 or more agents, launched with `agentType` set (the default workflow
subagent loads CLAUDE.md and every tool). This repository rarely fans out (review rounds are
sequential, `mention-context-review` must run one category at a time, and the largest batch so far
was nine `shrine-text-review` sections), so the default here is plain Agent calls in one message.
If a recurring job ever needs a workflow, one line in CLAUDE.md or in its skill saying so is enough:
the harness does not need a per-session request (tested and confirmed 2026-10-17). Ask the GM
before adding such a line, since this repository keeps broad fan-out to his request.

## The same-session fallback

A definition created or edited this session is not registered until the next one (gotcha in
[`spec-kit-and-reviews.md`](spec-kit-and-reviews.md)). The fallback is a `general-purpose` agent told
to adopt the definition. It is correct, and it costs ~41-69k tokens per launch, which no prompt
shape avoids. Use it only for that session, with `CACHE_OK` in the prompt, and switch back to the
typed launch in the next session.

## Non-Claude-Code LLM calls

When you control the request (the Gemini calls in `chargen/brief.py` / `chargen/synthesis.py` and
`l7r/lookup/gemini.py`), the textbook rule applies, and this project already follows it: stable
content first, variable content last, no timestamps or reordering in the stable part. The layer
order in `synthesis.build_prompt` is a documented caching contract (`webapp/CLAUDE.md`), and
`lookup` splits `system` (stable) from `prompt` (the question) and reports `cachedContentTokenCount`.
