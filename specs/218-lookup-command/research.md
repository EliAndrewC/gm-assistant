# Research 218

## Gemini tiers (probed 2026-10-17 with a one-word prompt over REST)

| model | works | lowest thinking setting accepted | notes |
|---|---|---|---|
| `gemini-2.5-flash-lite` | **no** | - | 404: "no longer available to new users". Dropped from the tiers. |
| `gemini-3.1-flash-lite` | yes | none sent (no thinking by default), or `thinkingLevel: minimal` | `low` spent 111 thought tokens on a one-word reply |
| `gemini-3.5-flash-lite` | yes | `thinkingLevel: minimal` (also no thinking by default) | `thinkingBudget: 0` is a 400 |
| `gemini-3.8-flash` | yes | `thinkingBudget: 0` or `thinkingLevel: low` | thinks by default (67 thought tokens); `minimal` is a 400 |
| `gemini-3.1-pro-preview` | yes | `thinkingLevel: low` | "only works in thinking mode"; `minimal` and budget 0 are 400s |

So the thinking setting is per model and lives in configuration (`[lookup_models]`), not in code.

## Prices (per million tokens, USD; checked 2026-10-17)

| model | input | cached input | output (thinking included) |
|---|---|---|---|
| `gemini-3.1-flash-lite` | 0.25 | 0.025 | 1.50 |
| `gemini-3.5-flash-lite` | 0.30 | 0.03 | 2.50 |
| `gemini-3.8-flash` | 0.75 (introductory through 2026-12-31; 1.50 after) | 0.075 | 3.75 (7.50 after) |
| `gemini-3.1-pro-preview` | 2.00 (prompts up to 200k) | 0.20 | 12.00 |

Sources: Google's pricing page (<https://ai.google.dev/pricing>) for 3.1 Flash-Lite; aggregators
(<https://www.morphllm.com/gemini-api-pricing>, <https://benchlm.ai/google/api-pricing>,
<https://mem0.ai/library/llms-and-models/gemini-api-pricing>) for the rest. Prices change, which is
why they are configuration (`[lookup_prices]`) rather than constants.

## Facts the GM's five examples depend on (all verified in the sources)

- Marshals = haribugyo, "magistrates of the sting"; Inspectors = metsuke, "one who directs their
  eye"; Escorts = gosonin, "transport guard" (`l7r.md`, The Wasp hierarchy).
- The PCs report to Tsuruchi Kyoma (`l7r.md`, The Wasp Bounty Hunters Campaign and The Wasp
  hierarchy); his OP record `tsuruchi-kyoma` is public.
- Crab patron Fortunes: Bishamon and Ebisu (`l7r.md`, Temple Organization, the patron table).
- Public wiki pages `imperial-bounties` and `wasp-hierarchy` exist.
- Tsuruchi Hideki, the GM's motivating case, has a public OP record (`tsuruchi-hideki`).

## Discord

- The L7R GM Assistant application (`1509288141985415300`) has no interactions endpoint URL, so
  `INTERACTION_CREATE` arrives over the gateway.
- The character-sheet API (`/api/characters`, bearer token) carries `owner_discord_id`,
  `is_npc` and `gaming_group_name`. School, Dan and lineage are only on the public sheet page.
  Both gaming groups (Monday, Tuesday) are Wasp tables; most of their PCs are Tsuruchi, and the
  two that are not (Asako Tadashi, Kitsune Moriko) are in the same groups.

## Secrets reading

The secrets file writes `[gemini] api_key` in quotes. ConfigObj strips them (which is how `chargen`
and the deploy script read it), while `configparser` keeps them, which produced an
`API_KEY_INVALID` during probing. `l7r.lookup` reads with ConfigObj.
