# Dream scene pool (public tier)

This directory holds **git-tracked, campaign-agnostic** dream-omen scenes: theoretical
or spoiler-dead exemplars written to demonstrate the form, and the seed corpus for the
future Dreams section of the l7r-gm-assistant webapp (alongside relics, names, places).

**Spoiler rule:** a saved dream scene reveals a god's actual verdict, so anything tied to a
live plot must NOT go here. Campaign-active and spoiler-sensitive scenes live in the sibling
`pool-local/` directory, which is `.gitignore`'d (local disk only, never committed).

- `pool/` (here) - public, safe to commit, spoilers moot or dead.
- `pool-local/` - private, gitignored, campaign-active scenes and the assistant's continuity reference.

**Never auto-promote** a scene from `pool-local/` to here. Promotion is an explicit GM
decision, made only after a plot resolves or for a scene deliberately built spoiler-free.

See `../SKILL.md` for how scenes are built and the theology behind the mechanic.
