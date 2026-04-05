---
name: name
description: Generate Rokugani personal names with meanings and explanations in varied formats
argument-hint: [male|female] [x<N>]
allowed-tools: Bash Read
---

# Rokugani Name Generator

Generate personal names (given names only, not family/house names) for characters in the L5R setting. Each name comes with an explanation of its meaning, using one of 20 different explanation formats to keep things varied and interesting.

Names are pre-generated into a pool and selected via script to ensure they don't collide with existing campaign NPCs.

## How to Parse Arguments

Arguments can appear in any order and are optional:
- `male` or `female` - specifies gender. If omitted, randomly choose 50/50.
- `x<N>` (e.g. `x3`, `x5`) - generate N names. If omitted, generate 1.

Examples: `/name`, `/name male`, `/name x5`, `/name female x3`, `/name x3 male`

## How to Serve a Name Request

1. **Parse arguments** to determine gender (or null for random) and count (default 1).

2. **Run the picker script**:
   ```
   cd ${CLAUDE_SKILL_DIR} && python3 pick_name.py [male|female] <count>
   ```
   Omit the gender argument if unspecified (the script randomizes). The script outputs one JSON object per line with `name`, `gender`, `format`, and `explanation` fields.

3. **Display the results** to the user in a clean format — just the name and explanation, not the JSON.

4. **If the script reports a warning** about low pool size, inform the user: "The name pool is running low. Say 'refill names' to generate more."

5. **If the pool is empty**, fall back to generating a name directly (see "How to Generate Directly" below) and warn the user to refill.

## How to Refill the Name Pool

When the user says "refill names" or the pool is empty:

1. Generate 50 male and 50 female names using the direct generation method below.
2. For each name, produce a JSON object: `{"name": "...", "gender": "male|female", "format": N, "explanation": "..."}`
3. Append to `${CLAUDE_SKILL_DIR}/pool-male.jsonl` and `${CLAUDE_SKILL_DIR}/pool-female.jsonl` respectively.
4. Before adding, check each name against `${CLAUDE_SKILL_DIR}/campaign-names.txt` using the similarity rules to avoid adding names that would be filtered out anyway.

## How to Update the Campaign Name Cache

When the user says "update name cache":

Run: `python3 ${CLAUDE_SKILL_DIR}/fetch_campaign_names.py`

This scrapes the current NPC list from Obsidian Portal and saves it. The session cookie may expire periodically — if the script fails, ask the user for updated cookies.

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

- Names should feel like they belong in Rokugan — draw on the setting's culture, values, history, and cosmology
- Male names typically end in consonants or -o, -u, -i (e.g. Takeshi, Haruto, Kenshin)
- Female names often end in -ko, -mi, -e, -ka, -na, -yo (e.g. Yoshiko, Kazumi, Hanae)
- Explanations should reference Rokugani concepts (bushido virtues, the Fortunes, clan culture, the Tao, etc.) when natural to do so, but not forced into every single name
- When a format references a historical figure, event, or place, it MUST be consistent with the GM's setting notes — consult `/campaigns/` and `/setting/` files if needed
- Keep explanations concise — one to three sentences matching the format template

## Similarity Rules

Names are rejected if they are too similar to existing campaign NPC names. "Too similar" means:
- Edit distance of 1 (differ by a single letter change, addition, or removal)
- One name is a longer version of another (e.g. Chiyo/Chiyoko)

The similarity logic is in `${CLAUDE_SKILL_DIR}/similarity.py`.

## Source Material — Name Formats

<!-- SOURCE: GM NOTES — DO NOT MODIFY -->
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
- See `/setting/clans-and-imperials.md` for clan/family names (these are NOT generated by this skill — only personal names)
- See `/.claude/skills/calendar/SKILL.md` for calendar events (relevant to Format #20)
- See `/cosmology/fortunes.md` for Fortune references
- See `/campaigns/` for historical figures and events (relevant to Formats #7, #11, #13, #18, #19)
