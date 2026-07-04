# Contract: the `/synthesize` skill command

## Invocation

`/synthesize <character name>` - free-text name of an existing OP character
(partial/approximate allowed).

## Flow

1. **Resolve** the name against `op.existing_characters()` via
   `opsynth.match_character`. Unique -> proceed. Ambiguous -> present candidates
   and ask (AskUserQuestion or plain confirm). No match -> report nearest names,
   stop.
2. **Gather**: `op.get_character_body(id)` + `op.fetch_character_page(url)` ->
   `opsynth.parse_tagline`. Infer caste (`opsynth.infer_caste`), state it.
   Optionally compute related characters (P3) from the tagline cache.
3. **Synthesize**: `synthesis.synthesize(char, campaign_context=..., 
   character_type=caste, campaign_context_recent=...)` with
   `opcache.get_campaign_context(exclude_name=name)`. Write a JSON handoff
   (id, name, existing game_master_info, caste, backstory) to the scratchpad.
4. **Present** the backstory, then two listed options plus a free-text path:
   - **Upload as-is to Obsidian Portal**
   - **Generate another synthesis**
   - free-text ("Other") = **upload with changes**: the typed text IS the
     changes; apply them, then upload.
5. **On upload** (as-is or with typed changes): re-fetch `game_master_info`,
   merge via `opsynth.merge_backstory`,
   `op.update_character(id, game_master_info=merged)`, confirm exactly what was
   written and where. On "generate another": re-run step 3 and re-present.

## Guarantees (map to FRs / SCs)

- Never generates for the wrong character silently (FR-002, SC-006).
- Uses the same corpus/caste/campaign context as the webapp (FR-004, SC-005).
- Save preserves all existing notes; re-save yields one section (FR-010/011,
  SC-003/004).
- Fails safe: on OP/corpus failure, reports and writes nothing (FR-013).
