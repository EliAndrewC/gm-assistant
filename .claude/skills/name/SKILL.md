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
   - Fits the Rokugani setting: a PRE-MODERN name, never a modern Japanese one (see "Period Sensibility" below - this is a hard rule, not a flavor note)
   - Is a personal/given name, not a family name, a deity, an office, an object or a common noun

4. **Write the explanation** following the selected format template exactly.

## Period Sensibility (GM 2026-08-25)

Rokugan draws on pre-Meiji Japan (Heian through Edo), so every name in the pool must read as a name from THAT world. A name that only entered Japanese use in the 20th century (Naomi, Misaki, Haruto, Yuto, Akemi, Hiroki, Daiki) is as wrong here as a samurai wearing a wristwatch, even though it is built from perfectly Japanese syllables. Two kinds of name are welcome:

- **Attested names** - names that real pre-modern Japanese people carried, from the famous (Kiyomori, Masako, Tomoe, Nobunaga) down to the long tail of the uncommon-but-recognizable, the register of a name like "Eli": rare, but nobody doubts it is a name.
- **Constructed names in the historical idiom** - names no register records but that a reader of period history cannot tell from attested ones, the way "Katniss" reads as a plausible future descendant of contemporary names. These are the setting's Hunger Games license and they are welcome, PROVIDED the mixture stays credible: most of the pool should be attested or indistinguishable from attested, and no name should be built from a modern idiom.

**Why this matters for POOL SIZE** (research 2026-08-25, sources in `docs/name-stock-research.md`): the credible stock is very different for the two genders, and that decides how far each pool can grow.

- **Male: effectively unbounded.** The samurai formal name (nanori) is combinatorial - two elements from a vocabulary of ~30 core / ~60-80 recognizable "name characters" (masa, nobu, yoshi, tada, ie, yasu, yori, taka, kane, tomo, naga, katsu, toki, mitsu, hisa, hide, toshi, sada, kuni, aki, shige, nori, mune, uji, mori, tsugu, chika, haru, hiro, kiyo, kage, tsune, moto, yuki, michi, tane, suke, oki, fusa, ari, nari...), so ~3,500 combinations are plausible and 1,500-3,000 are attested, all of them instantly readable as "a samurai name". On top of that: common names (tsusho) from birth-order and office suffixes (Goro, Shinnosuke, Sukezaemon, Hanbei, Kichiemon, Zoroku), childhood names in -maru / -chiyo / -waka, and two-kanji on-reading Buddhist names (Rensho, Genshin, Eishun). Village registers show almost every man with a name unique in his village, built from that small parts kit. Order of magnitude of the recognizable male stock: **5,000-8,000**. A male pool of 300-500 does not dent it; the binding constraint is the project's own similarity rule.
- **Female: small and flat, roughly 300-500 in real circulation.** Pre-modern women outside the court had short kana names, overwhelmingly two morae (93% in one Edo register), from a stock of auspicious words - Kiku, Matsu, Sen, Kin, Hatsu, Kane, Yasu, Tome, Kiyo, Tora, Toyo, Shige, Chiyo, Tsune, Hana, Mitsu, Haru, Kuma, Natsu, Yoshi, Yuki, Katsu, Rin, Taki, Masa, Fumi, Ume, Take, Tsuru, Kame, Fuku, Ito, Sato, Nao, Sayo, Miyo, Tama, Man, Raku... The distribution is flat (the top name covers ~1.6% of women, the top 100 about 65%), so the long tail is real but short: the recognizable-to-a-reader subset is about **250-400**. There is no combinatorial system for women. The only honest levers are kanji spelling variants of the same short name, the suffix ladder (X / O-X / X-hime / X-ko / X-me / X-jo), and the Heian court pattern of one auspicious kanji + `-ko`. A female pool of 300 would reach the floor of the attested stock and 500 would be past it, so female growth is bounded by how many attested names the raw lists actually yield, not by ambition - the invented-name budget below is what keeps the constructed fraction from drifting toward the one-in-six credibility failure this rule guards against.

**Modern male styles to refuse** (Meiji or later, per the Meiji Yasuda name rankings and the 1872 abolition of the double tsusho/nanori name): single-kanji virtue names (Noboru, Isao, Tadashi, Osamu, Makoto, Hiroshi, Wataru, Chikara - Meiji onward); `-o` in 男/夫/雄 and numeral suffixes `-ichi` / `-ji` / `-zo` (Shunichi, Eiichi, Etsuji - Meiji-Taisho-Showa); `-hiko` (Heian-mythic, revived by Meiji nativists - use only for a deliberately archaic or priestly flavor); `-kazu` written 一 as a SECOND element (Meiji-leaning; Kazu- as a FIRST element is fine); `-ya` (也 only became a name kanji in 1951), `-ki` (Hiroki, Daiki, Naoki), Yuki, Takumi, Tatsuya, Daisuke, Kenta, Shota (Showa-Heisei); Haruto, Yuto, Sota, Kaito, Riku, Hinata, Ren, Aoi (2000s). Sounds modern but is attested and fine: Hayato (an office title), Ukyo/Sakon (court offices used as common names).

**Modern female styles to refuse:** the Meiji-Taisho three-mora forms in `-e` / `-yo` / `-mi` (Michie, Fumie, Hanae, Yoshie, Kazuyo, Michiyo, Tomoyo, Hidemi, Yukimi, Harumi); the postwar `-mi` wave (Akemi 1965, Natsumi, Mayumi, Naomi, Emi); Chihiro, Azumi, Asuka, Wakana, Shiori, Urara, Erina, Rikako (Showa-Heisei); Misaki, Sakura, Hina, Aoi, Yui, Mio, Yuina (1990s-2000s). Plant names beyond matsu / take / ume / kiku / fuji / hana are rare pre-modern, so Ayame, Tsubaki, Kaede, Suzume read as geisha or pen names, not birth names - allowed only with that framing in the explanation. Sounds modern but is attested and fine: Tomoe, Shizuka, Rin, Saki, Sayo, Chiyo, Hatsu, Natsu.

**The `-ko` question: source material wins (GM 2026-08-25).** Historically `-ko` was a Heian court usage (Teishi, Shoshi, Masako, Noriko, Sadako, Shigeko, Yasuko, Tokiko, Teruko, Fusako are all attested court names), absent among commoners and warriors' wives until 1872, and a 20th-century mass phenomenon after that (over 80% of girls in the 1930s). L5R canon nevertheless uses `-ko` freely for samurai women AND for peasants. Where real history and the game's source material conflict, the call is made case by case, and the GM's default is to stay true to the source material whenever it does not overly detract from verisimilitude - here it does not. **So `-ko` is acceptable for every caste, peasants included**; a session must NOT restrict it to samurai. What still holds is the period rule on the BASE: Masako, Noriko, Sadako, Shigeko, Takeko (Take), Umeko (Ume), Fujiko (Fuji), Kameko (Kame), Chiyoko (Chiyo) are fine; Sachiko, Reiko, Emiko, Yuriko, Rumiko, Kimiko, Chieko, Makiko, Nanako are 20th-century bases wearing a court suffix and are refused. The short kana names (Kiku, Matsu, Sen, O-Hatsu) remain the most historically typical peasant form and should stay well represented, but they are a flavor, not a caste rule.

**Caste and the `peasant` flag (GM 2026-08-26).** `peasant: true` on a pool entry means "suitable for a commoner" - the short kana register names (Kiku, Matsu, O-Sen) and the everyday `-emon` / `-bei` / `-suke` names. There is deliberately NO peasant-only flag: sumptuary law reserved surnames, dress and swords for the nobility, never given names, so Kiku can be a samurai's daughter. The asymmetry runs the other way - the two-kanji formal name (nanori) came with genpuku and a lord, so a farmer called Hidetsuna is wrong. The rule, in both the `/name p` filter and the chargen engine (`namepool.pick_name(peasant=...)`): **a peasant draws only from `peasant: true`; a samurai prefers the `peasant: false` names and falls back to the whole pool only when the set/roster rules exhaust them; no caste given = the whole pool.** The preference rather than an even draw matters because 81% of the female pool is peasant-flagged (2026-08-26: 151 of 186) - an even draw would name most samurai women after village registers, and would spend the scarce samurai-style female stock (35 names) on peasants. Monks draw from the whole pool.

**The invented-name budget (GM 2026-08-25).** The existing pool is not purged; the ratio is fixed by ADDING names under this rule:

- A **majority of each pool must be real traditional names** - attested in a historical source (the raw lists under `raw/`, `docs/name-stock-research.md`), or, for men, a nanori built from two attested elements, which a reader cannot distinguish from an attested one.
- **At most 20% of each pool may be invented** (constructed in the historical idiom but recorded nowhere). Track this: an invented entry carries `"invented": true` in its pool record so the ratio can be measured rather than guessed.
- **Spend the invented budget only on under-represented initials.** Sets of names generated together must differ in first letter (the similarity rule), which needs a flatter spread across the alphabet than any real language has: Japanese has few historical names in Y, Z, W, R, E and a glut in K, M, S, T, H. Invented names go to the thin letters; **never add an invented name to a letter already rife with attested ones**.

**Not names at all - refuse regardless of period:** deities (Raijin, Suijin, Ryujin, Bishamon), offices and ranks (Busho, Gunshi, Doshin), common nouns and objects (Chusei "loyalty", Isshun "instant", Eboshi "hat", Gusoku "armor", Enishi "bond"), surnames (Akimoto, Wakizaka, Watarai, Ogushi, Watase, Obana, Fukano), era and posthumous imperial names (Daigo, Jomei), go/art terms (Joseki). A monk's or retired man's assumed name (Bokuden, Jozan, Ugetsu) is fine ONLY when the explanation says that is what it is.

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
