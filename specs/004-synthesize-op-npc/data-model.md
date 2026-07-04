# Data Model: /synthesize skill for existing Obsidian Portal NPCs

The feature holds no new persistent domain model of its own; it reads OP
character records and writes back one delimited notes section. The entities below
describe the shapes that flow through the skill.

## OP character (read)

Sourced from `op.get_character_body` (JSON API) plus the page fetch (tagline).

| Field | Source | Use |
| ----- | ------ | --- |
| `id` | API list/detail | PATCH target on save |
| `slug` / `character_url` | API list | build the page URL for the tagline fetch |
| `name` | API | display; excluded from its own campaign context |
| `tags` | API (list[str]) | caste inference; passed to synthesis |
| `description` | API (prose) | passed to synthesis as public info |
| `game_master_info` | API (prose) | passed as private info; merge target on save |
| `tagline` | **page HTML** | the one-line summary; synthesis `summary`; relationship source |
| `updated_at` | API | tagline-cache freshness key |

Validation / rules:
- A missing tagline is allowed (empty string); synthesis proceeds without it.
- `name` is matched case-insensitively and token-wise against the requested name
  (FR-002); ambiguity -> confirm, no match -> report nearest.

## Inferred caste

A derived value in {`Samurai`, `Monk`, `Peasant`}, computed from `tags` +
`game_master_info` by `opsynth.infer_caste` (see research D3). Selects the
per-caste supplement via `brief.build_caste_supplement`. Default `Samurai`.

## Synthesis input (assembled)

The character dict handed to `synthesis.synthesize`, matching the webapp shape:

```text
{ full_name, tags, summary (= tagline), public (= description),
  private (= game_master_info), name_meaning? }
```

plus `character_type` (= inferred caste) and the campaign-context blocks from
`opcache.get_campaign_context(exclude_name=full_name)`.

## Tagline cache (new, gitignored)

`webapp/opcache/taglines.json`: `{ character_id: { tagline, updated_at } }`.
Refreshed incrementally (fetch a page only for new/changed ids), mirroring
`opcache.characters.json`. Consumed only by the P3 related-character scan.

## Related characters (derived)

For a subject whose tagline names another cast member `X`: the list of other
characters whose tagline also mentions `X`, produced by
`opsynth.related_by_tagline(subject_tagline, cast_taglines, cast_names)`. Fed into
synthesis as extra steering context. Empty when the subject's tagline names no
cast member.

## Synthesized-backstory section (write)

The delimited block merged into `game_master_info`:

```text
--- Synthesized Backstory (auto) ---
<prose>
--- End Synthesized Backstory ---
```

State transitions on save (`opsynth.merge_backstory(existing, prose)`):
- **absent -> present**: append the block after existing notes (one blank-line gap).
- **present -> replaced**: replace text between the sentinels in place.
- Everything outside the sentinels is preserved byte-for-byte.
