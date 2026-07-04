# Contract: `chargen/opsynth.py` (pure logic, 100% covered)

All functions are deterministic and side-effect-free. No network, no file I/O.

## `match_character(query, characters) -> MatchResult`

- `characters`: list of dicts each with at least `id`, `name`, `slug`.
- Returns one of: exact/unique match (the character dict), an ambiguous set
  (list of candidate dicts), or no-match (with the nearest names by token
  overlap / edit distance).
- Matching is case-insensitive and token-based so "Daidoji Jitsuyo" resolves
  "Daidoji no Etsuko Jitsuyo" (all query tokens present in the name).
- Ambiguous when >1 character contains all query tokens.

## `infer_caste(tags, gm_info) -> str`

- Returns `"Samurai" | "Monk" | "Peasant"`.
- Monk when a monastic marker appears (an "Order of ..." tag, or
  monk/temple/abbot/shugenja/priest in tags/notes); Peasant on explicit peasant
  markers (peasant/heimin/ashigaru/farmer/servant); else Samurai.
- Case-insensitive; deterministic precedence Monk > Peasant > Samurai.

## `parse_tagline(html) -> str`

- Extracts the text of `<div class='tagline'> ... <em>TEXT</em> ...`.
- Returns the inner text stripped of tags/whitespace, or `""` when absent or the
  tagline div is empty (both real cases: the page has an empty banner tagline and
  a populated body tagline; return the populated one).

## `related_by_tagline(subject_tagline, cast_taglines, cast_names) -> list[str]`

- `cast_taglines`: `{name: tagline}` for other cast members.
- Finds the cast name(s) referenced in `subject_tagline`, then returns other cast
  members whose tagline references the same name(s).
- Returns `[]` when the subject tagline names no cast member.

## `merge_backstory(existing_gm_info, prose) -> str`

- Inserts `prose` between the sentinels `--- Synthesized Backstory (auto) ---`
  and `--- End Synthesized Backstory ---`.
- If both sentinels already exist, replaces the text between them (inclusive);
  else appends the delimited block after `existing_gm_info` with one blank line.
- All text outside the sentinels is preserved unchanged. Idempotent: merging
  twice with the same prose yields the same string, and exactly one section.

## `build_synthesis_character(body, tagline) -> dict`

- Maps an OP `get_character_body` dict + tagline into the webapp-shaped character
  dict (`full_name`, `tags`, `summary`, `public`, `private`).
- Pure remap; no defaults invented beyond empty-string coalescing.
