---
name: name
description: Generate Rokugani personal names with meanings and explanations in varied formats
argument-hint: [male|female] [x<N>]
allowed-tools: Bash Read
---

# Rokugani Name Generator

Generate personal names (given names only, not family/house names) for characters in the L5R setting. Each name comes with an explanation of its meaning, using one of 20 different explanation formats to keep things varied and interesting.

Names are pre-generated into a pool and selected via script to ensure they don't collide with existing campaign NPCs.

## First Invocation in a Session

When this skill is first invoked in a session, do TWO things:

1. **Ensure dependencies are installed**: Run `${CLAUDE_SKILL_DIR}/setup.sh` to install pip and Python packages if needed.
2. **Start the background cache updater**: Use `/loop 1h update name cache` to periodically refresh the campaign name cache from Obsidian Portal. This keeps the similarity filter up to date if the GM adds new NPCs during the session.

Then proceed to serve the name request as described below.

On subsequent invocations in the same session, skip both steps and go straight to serving the request.

## How to Serve a Name Request

1. **Pass the user's arguments directly to the picker script** — do not parse them yourself. The script handles all argument parsing including shorthand:
   ```
   cd ${CLAUDE_SKILL_DIR} && python3 pick_name.py <user args>
   ```
   The script accepts: `male`/`female`/`m`/`f` for gender, `peasant`/`p` for caste, numbers or `x<N>` for count, and concatenated shorthand like `pf3`, `m2`, `3mp`. Order doesn't matter. The script outputs one JSON object per line with `name`, `gender`, `format`, `explanation`, and `notes` fields.

3. **Display the results** to the user in a clean format (not raw JSON). Show the name and explanation first, then a separate *Notes:* line with the real-world analysis from the `notes` field. Example:

   **Wakizaka** — The name Wakizaka is associated with the famous Battle of White Shore, in which...

   *Notes: Wakizaka is a real Japanese surname (most notably Wakizaka Yasuharu, a daimyo at Sekigahara) but uncommon as a given name. The explanation is fictional Rokugani history.*

4. **If the script reports a warning** about low pool size, inform the user: "The name pool is running low. Say 'refill names' to generate more."

5. **If the pool is empty**, fall back to generating a name directly (see "How to Generate Directly" below) and warn the user to refill.

## How to Refill the Name Pool

When the user says "refill names" or the pool is empty:

1. First run `${CLAUDE_SKILL_DIR}/setup.sh` to ensure dependencies are present.
2. Load ALL existing names from both `pool-male.jsonl` and `pool-female.jsonl`, plus all names from `campaign-names.txt`. These are the "excluded names" -- every new name must pass the similarity check against ALL of them.
3. Generate names one at a time using the direct generation method below. For each name:
   a. Check it against the full excluded list using `similarity.is_too_similar()`.
   b. If it passes, add it to the appropriate pool file AND add it to the excluded list before generating the next name.
   c. If it fails, discard it and generate a replacement.
4. Each name is a JSON object: `{"name": "...", "gender": "male|female", "format": N, "explanation": "..."}`
5. Continue until each pool has at least 50 names.
6. After generation, run `cd ${CLAUDE_SKILL_DIR} && python3 validate_pool.py` to confirm zero conflicts.
7. If validation fails, run `cd ${CLAUDE_SKILL_DIR} && python3 fix_pool.py` and then re-validate.

## How to Update the Campaign Name Cache

When the user says "update name cache" (or when triggered by /loop):

1. Run: `cd ${CLAUDE_SKILL_DIR} && python3 fetch_campaign_names.py`
2. This scrapes the current NPC list from Obsidian Portal and saves it to `campaign-names.txt`.
3. The session cookie may expire periodically -- if the script fails with an authentication error, ask the user for updated cookies from Chrome DevTools.

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

## Similarity Rules

Names are rejected if they are too similar to existing campaign NPC names. "Too similar" means:
- Edit distance of 1 (differ by a single letter change, addition, or removal)
- One name is a longer version of another (e.g. Chiyo/Chiyoko)

The similarity logic is in `${CLAUDE_SKILL_DIR}/similarity.py`.

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
