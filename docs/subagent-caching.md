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
   launch writes ~41-69k tokens to the cache before it does any work; a typed agent with
   `omitClaudeMd` writes ~2.6k on a repeat launch.
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

**Open question, not needed for the rules:** two general-purpose launches with different prompts
both read exactly 48,505 and wrote 10,413. That is an intermediate match the "only the system prompt
carries over" picture does not explain. Claude Code's breakpoint placement for subagents is
undocumented. If it matters, log the raw request bodies through a proxy on `ANTHROPIC_BASE_URL` and
diff two launches.

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

A cache entry is readable only once the request that writes it has started streaming. N identical
launches sent at the same instant all write and none read. The `Workflow` runtime already holds
same-prefix agents for up to 5 seconds behind the first one. For hand-launched Agent calls, the
shared part is now only the ~4k system prompt, so staggering saves little. When launching 3 or more
of one type, launching one first and the rest in the next turn is still the cheaper shape.

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
