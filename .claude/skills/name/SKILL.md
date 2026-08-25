---
name: name
description: Generate Rokugani personal names with meanings and explanations in varied formats
argument-hint: [--refresh] [--avoid A,B] [--bank N] [m|f] [p] [N]
allowed-tools: Bash Read
---

# Rokugani Name Generator

Generate personal names (given names only, not family/house names) for characters in the L5R setting. Each name comes with an explanation of its meaning, using one of 20 different explanation formats to keep things varied and interesting.

Names are pre-generated into a pool and selected via script to ensure they don't collide with existing campaign NPCs.

The pool is the SINGLE source of given names in this project (feature 200, 2026-08-25): the `/names` web page and the chargen engine (`webapp/chargen/namepool.py`, used by `/chargen` and the webapp's Generate button) read the same two files. The used-name exclusion list is derived from the campaign-character cache (`webapp/opcache/characters.json` - the same cache the `/synthesize` prompt reads), which is reconciled after every character creation and, by `pick_name.py`, whenever it is more than an hour old. No cookie, no `.env`, no setup step, no background loop: the script does it.

## How to Serve a Name Request

1. **Pass the user's arguments directly to the picker script** - do not parse them yourself. The script handles all argument parsing including shorthand:
   ```
   cd ${CLAUDE_SKILL_DIR} && python3 pick_name.py <user args>
   ```
   The script accepts: `male`/`female`/`m`/`f` for gender, `peasant`/`p` for caste, numbers or `x<N>` for count, and concatenated shorthand like `pf3`, `m2`, `3mp`. Order doesn't matter. The script outputs pre-formatted markdown ready to display.

2. **Display the script's output directly** - no parsing or reformatting needed.

3. **Flags** (before or among the shorthand): `--refresh` forces a campaign-cache refresh from Obsidian Portal first (use when the GM says they just added someone on the website); `--avoid A,B` makes every pick set-distinct from those names (a `/synthesize` subject, names already chosen); `--bank N` returns N male + N female names as ONE mutually distinct set, gender-labeled - the name bank a backstory's invented supporting cast is drawn from.

4. **If the script prints a WARNING on stderr** (no campaign cache, an empty roster, or a stale cache it could not refresh), pass it on to the GM verbatim: the names were picked against an incomplete roster.

5. **If the pool is empty**, fall back to generating a name directly (see "How to Generate Directly" below) and warn the user to refill.

## How to Refill the Name Pool

When the user says "refill names" or the pool is empty:

1. Refresh the roster: `cd ${CLAUDE_SKILL_DIR} && python3 pick_name.py --refresh 1` (the pick itself is disposable; the refresh is the point).
2. Load ALL existing names from both `pool-male.jsonl` and `pool-female.jsonl`, plus the roster's given names (`python3 -c "import campaign; print(campaign.used_names(refresh=False))"` from the skill dir). These are the "excluded names" -- every new name must pass the similarity check against ALL of them.
3. Generate names one at a time using the direct generation method below. For each name:
   a. Check it against the full excluded list using `similarity.is_too_similar()`.
   b. If it passes, add it to the appropriate pool file AND add it to the excluded list before generating the next name.
   c. If it fails, discard it and generate a replacement.
4. Each name is a JSON object: `{"name": "...", "gender": "male|female", "format": N, "explanation": "..."}`
5. Continue until each pool has at least 50 names.
6. After generation, run `cd ${CLAUDE_SKILL_DIR} && python3 validate_pool.py` to confirm zero conflicts.
7. If validation fails, run `cd ${CLAUDE_SKILL_DIR} && python3 fix_pool.py` and then re-validate.

## How to Update the Campaign Name Cache

You normally never do: `pick_name.py` refreshes the cache via the OAuth API when it is more than an hour old, and every character creation from this project reconciles it immediately. If the GM says "update name cache", run `cd ${CLAUDE_SKILL_DIR} && python3 pick_name.py --refresh 1`. If that prints an OAuth-credentials error, the fix is `webapp/probe_op_oauth.py --full` (see `webapp/development-secrets.ini`), not a browser cookie.

## How to Generate Directly (Fallback / Pool Refill)

For EACH name to generate:

1. **Determine gender** (if not specified): Run `shuf -i 0-1 -n 1` via Bash. 0 = male, 1 = female.

2. **Select a format**: Run `shuf -i 1-20 -n 1` via Bash to pick a random format number. When generating multiple names, pick a different format for each.

3. **Generate the name**: Create a name appropriate to the gender that:
   - Sounds authentically Japanese
   - Has a real or plausible kanji-based meaning
   - Fits the Rokugani setting (not modern Japanese names)
   - Is a personal/given name, not a family name

4. **Write the explanation** following the selected format template exactly.

## Important Guidelines

- Names should feel like they belong in Rokugan -- draw on the setting's culture, values, history, and cosmology
- Male names typically end in consonants or -o, -u, -i (e.g. Takeshi, Haruto, Kenshin)
- Female names often end in -ko, -mi, -e, -ka, -na, -yo (e.g. Yoshiko, Kazumi, Hanae)
- Explanations should reference Rokugani concepts (bushido virtues, the Fortunes, clan culture, the Tao, etc.) when natural to do so, but not forced into every single name
- When a format references a historical figure, event, or place, it MUST be consistent with the GM's setting notes -- consult `/campaigns/` and `/setting/` files if needed
- Keep explanations concise -- one to three sentences matching the format template
- **Constitution Principle XI** (Japanese Authenticity): when the explanation cites kanji or kanji-derived meaning, the kanji MUST be real Japanese characters, the meaning MUST match how a Japanese speaker would parse them, and the romanization of the name MUST be a plausible reading. The `notes` field in pool entries is the place to flag any non-obvious or stylized reading.

## Similarity Rules

Names are rejected if they are too similar to existing campaign NPC names. "Too similar" means:
- Edit distance of 1 (differ by a single letter change, addition, or removal)
- One name is a longer version of another (e.g. Chiyo/Chiyoko)

The similarity logic lives in `webapp/chargen/similarity.py` (the one implementation, shared with the chargen engine); `${CLAUDE_SKILL_DIR}/similarity.py` re-exports it.

### Set Distinctness (GM rule, 2026-07-20)

When a SET of names is generated together (a multi-name request, a team of
NPCs, siblings, any group introduced at the same time), a stricter rule applies
*within the set*, on top of the campaign-wide check above. Similar names are
confusing for players - Tolkien was a great author, but "Sauron" and "Saruman"
are famously confusingly similar. Within one set:

- No two names may start with the same letter.
- No two names may rhyme (heuristic: a shared trailing run of 3+ letters).
  - **Exception for "-ko" names**: when both names end in `-ko`, the threshold
    is 4 letters, not 3. The shared tail must reach past the vowel to the
    consonant opening the penultimate syllable - that is, the last *two*
    syllables must match rather than just the `ko`. Yuriko/Mariko and
    Michiko/Sachiko still rhyme; Yuriko/Reiko and Haruko/Yasuko do not.
- No two names may be only 1 letter different from each other.

**Why "-ko" is special** (GM rule, 2026-07-25): `-ko` is by far the most common
ending for female given names, so at a flat 3-letter threshold every `-ko` name
collides with every other one sharing its preceding vowel. The whole `-ko` space
collapses into five rhyme classes (`-ako`, `-eko`, `-iko`, `-oko`, `-uko`),
which rejects roughly a fifth of the female pool per name already chosen. In
practice this made mixed-gender sets impossible past four or five women: a
Reiji-domain roster with Yuriko, Masako, and Okayo already in it left **zero**
valid female candidates in the 100-name pool. The 4-letter threshold restores
useful headroom while still catching the genuinely confusable pairs. The change
is purely a relaxation - it can only turn a conflict into a non-conflict, so
name sets generated before it remain valid and were deliberately left alone.

`pick_name.py` enforces this automatically for batch picks (and against
`--avoid` names) via `similarity.set_conflict()`, and the chargen engine
enforces it through its `avoid=` constructor argument - so `/chargen` and the
webapp never need a hand re-roll. Only when generating names directly (the
fallback path) do you apply the rule by hand: if a rolled name conflicts with
another member of the set, re-roll it.

This rule is deliberately set-scoped, not campaign-wide - applied against the
whole cast, the first-letter constraint would exhaust the alphabet in two
dozen NPCs.

## Source Material -- Name Formats

<!-- SOURCE: GM NOTES - DO NOT MODIFY -->
FORMAT #1:
{NAME} - This name represents {DEFINITION} and is often chosen by those who are {EXAMPLE} or who are expected to {OTHER EXAMPLE}.

FORMAT #2:
{NAME} - This name means "{DEFINITION}". It represents {EXPLANATION}.

FORMAT #3:
{NAME} means "{DEFINITION}" or "{ALTERNATE DEFINITION}", which can suggest {EXPLANATION} or {ALTERNATE EXPLANATION}. People with this name may be {SUGGESTION}.

FORMAT #4:
{NAME} can be written with two different kanji. One means "{FIRST EXAMPLE}", and the other means "{SECOND EXAMPLE}". The choice of kanji could reflect {SUGGESTION}, such as {ONE POSSIBILITY} or {ANOTHER POSSIBILITY}.

FORMAT #5:
{NAME} - This name signifies {EXPLANATION}, and may suggest that the one who chooses it values {SUGGESTION}.

FORMAT #6:
{NAME} - A name that means "{DEFINITION}", evoking {EXPLANATION}.

FORMAT #7:
{NAME} chose their name in honor of the famous {FAMILY} {NAME}, who {DESCRIPTION_OF_GREAT_DEED}.

FORMAT #8:
{NAME} was a deity that was said to have {THING_DONE} after {OTHER_THING}.

FORMAT #9:
{NAME} - Derived from the phrase "{PHRASE}", this name embodies the idea of {IDEA}. It is often associated with those who {ASSOCIATION}.

FORMAT #10:
{NAME} - Composed of the elements "{ELEMENT_1}" and "{ELEMENT_2}", this name symbolizes {SYMBOLISM}. It is commonly chosen for its connotations of {CONNOTATIONS}.

FORMAT #11:
{NAME} - This name is inspired by the ancient tale of {TALE}, in which {SUMMARY_OF_TALE}. It reflects qualities such as {QUALITIES}.

FORMAT #12:
{NAME} - Rooted in the ancient proverb "{PROVERB}", this name serves as a reminder of the wisdom it contains. It is often chosen by those who value {VALUES}.

FORMAT #13:
{NAME} - With origins in the legend of {LEGENDARY_FIGURE}, who {ACHIEVEMENT_OR_ACTION}, this name evokes a sense of {EMOTIONS_OR_QUALITIES}. It appeals to those who admire {ASPECTS_OF_LEGEND}.

FORMAT #14:
{NAME} - Stemming from the word "{WORD}", which denotes {WORD_MEANING}, this name embodies the spirit of {SPIRIT_OR_THEME}. It resonates with those who are {PERSONALITY_TRAITS}.

FORMAT #15:
{NAME} - This name is inspired by the natural element of {NATURAL_ELEMENT}, symbolizing {SYMBOLISM_OF_ELEMENT}. It is often chosen for its connection to {CONNECTION_TO_NATURE} and its representation of {REPRESENTED_QUALITIES}.

FORMAT #16:
{NAME} - A name derived from the fusion of "{FIRST_MEANING}" and "{SECOND_MEANING}", reflecting a balance between {BALANCING_CONCEPTS}. It is often embraced by those who strive for {STRIVE_FOR_QUALITIES}.

FORMAT #17:
{NAME} - Drawing inspiration from the traditional art form of {ART_FORM}, this name represents {SOMETHING RELATED TO THE ART FORM}. It is often chosen by those who appreciate {SOME QUALITY OF THE ART FORM} and have a deep respect for {SOMETHING RELATED TO ARTISTS OF THIS FORM}.

FORMAT #18:
The name {NAME} is associated with the famous {EVENT FROM THE HISTORY OF ROKUGAN}, in which {SUMMARY_OF_EVENT}. Those who choose this name try to embody values of {VALUES_OR_LESSONS}.

FORMAT #19:
The name {NAME} is inspired by the {PLACE IN ROKUGAN}, known for its {QUALITIES OF PLACE}. The name reflects the {TRAIT} of the place and is often chosen by those who value {PERSONALITY TRAITS}.

FORMAT #20:
{NAME} - This name pays tribute to the {LOCAL OR EMPIRE-WIDE CALENDAR EVENT}, an event that emphasizes {QUALITIES OF THE EVENT}. People choose this name to reflect their values for {EXPLANATION OF VALUES}.
<!-- END SOURCE -->

## Generation Preferences

(To be developed through iteration with the GM. This section will capture what the GM likes and dislikes about generated names, and why.)

## References

- See `/setting/castes.md` for social context that affects naming
- See `/setting/clans-and-imperials.md` for clan/family names (these are NOT generated by this skill -- only personal names)
- See `/.claude/skills/calendar/SKILL.md` for calendar events (relevant to Format #20)
- See `/cosmology/fortunes.md` for Fortune references
- See `/campaigns/` for historical figures and events (relevant to Formats #7, #11, #13, #18, #19)
