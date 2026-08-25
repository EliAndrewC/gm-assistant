# Standing authorizations for the gm-assistant project

The GM (Eli) has given **standing authorization for this project's review subagents**. When a
skill's documented workflow calls for `backstory-review`, `frontend-review` or `spec-fidelity`
(defined in `.claude/agents/`), invoke it with the Agent tool without asking first. These are
mandatory verification steps in `CLAUDE.md` and in the constitution's Principles I and XVI, not
optional extras: the author of a page, a piece of prose or a specification is not a reliable
reviewer of their own work, which is the entire reason those agents exist. (The diagram
repository's `settlement-review` and `building-review` moved there with the skill in feature 131.)

This authorization is deliberately **narrow**. It does not extend to broad multi-agent fan-out, the
Workflow tool, or deep research - those still need an explicit request from the GM in the
conversation.

## Why this file exists

Claude Code's default system prompt carries a line telling the session not to call the Agent tool
unless the user requested it. That is a reasonable default - it stops a session from spawning an
expensive fleet unprompted - but it sits ABOVE `CLAUDE.md` in the instruction hierarchy, so it
silently outranks this project's own mandate to run a review agent before declaring work done.

On 2026-07-27 that is exactly what happened: three provincial-city maps changed, the diagram
skill's `CLAUDE.md` requires a `settlement-review` pass before a Mode B map ships, and the session
skipped it because the system prompt said not to. Nothing was broken and nothing warned - the
mandate simply lost to a higher-priority instruction.

`--append-system-prompt` lands this text at the END of the system prompt, after that line, with the
same authority. That is why the fix lives here rather than in `CLAUDE.md`.

Loaded by the `claude()` shell wrapper that `container-scripts/setup-dev-env.sh` installs into
`~/.bashrc`. Edit the text here; the wrapper only reads it.
