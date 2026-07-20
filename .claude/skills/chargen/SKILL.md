---
name: chargen
description: Generate a brand-new Rokugani NPC end-to-end and upload it to Obsidian Portal - roll a skeleton character with the chargen engine, write a Claude-native backstory (the /synthesize method, NOT Gemini), generate and attach an AI portrait, and create the OP record. Public by default; GM-only if the GM asks for private/hidden.
argument-hint: <free-text character concept> [ ... private/gm-only if it should be hidden]
allowed-tools: Bash Read Grep AskUserQuestion
---

# Make an NPC from scratch and upload it (Claude-native)

Roll a random character with the chargen engine, flesh it out with a backstory
**you write in this session** (the same method as the `/synthesize` skill - no
external LLM), generate an AI portrait, and create the character on Obsidian
Portal in one shot. The GM describes a concept; you fill the gaps, roll the
sheet, and do the rest.

This is the chat-driven twin of the chargen webapp's Generate -> Synthesize ->
Generate Art -> Upload flow, reusing the exact same plumbing (`chargen.character`,
`chargen.art`, `chargen.op`, `chargen.opsynth`). The one difference from the
webapp is the backstory: the webapp button uses Gemini; here **you write it**,
per the `/synthesize` skill (GM decision 2026-07).

**All Python runs from `/gm-assistant/webapp`** (import `l7r` first to dodge the
chargen circular-import, exactly like the webapp and the `/synthesize` skill).
Substitute the bracketed placeholders. `$SCRATCH` is this session's scratchpad
directory.

## Step 0 - Parse the invocation

The argument is a free-text **character concept**. Extract:

1. **Privacy.** Default is **public**. Treat the character as **GM-only
   (hidden)** if the concept contains `private`, `gm-only`, `gm only`, `hidden`,
   or `secret`. This maps to the `gm_only` flag on `op.create_character` (a
   GM-only character is hidden from players from the moment it is created).
2. **Type** (one of `Samurai` / `Monk` / `Peasant`). Infer from the concept:
   - **Samurai**: bushi, courtier, magistrate, yoriki, clerk, governor,
     minister, duelist, shugenja, any Clan/Family name, any government post.
   - **Monk**: monk, abbot, shrine keeper, ascetic, Brotherhood, an Order of a
     Fortune. (Shrines, not temples, are for villages - a monastic NPC is a Monk.)
   - **Peasant**: farmer, merchant, artisan, fisherman, innkeeper, servant,
     ashigaru, bandit, any heimin/hinin trade.
   If the concept genuinely doesn't imply a type, ask in Step 1.
3. **Location / posting place.** Where this NPC lives or serves - a province, a
   castle-town (`Shiro Reiji`), a county, a village, a domain. Almost every
   character belongs somewhere and should carry the matching geographic tag(s)
   (see "Location tags" below). Take it from the concept, or infer it from the
   campaign context (e.g. a temple named in another character's record fixes the
   town), or ask in Step 1.
4. **Pinnable params** the GM named (everything else is left to roll randomly -
   that is the point). See the concept -> params table below. Only pin what the
   GM actually said; do not invent constraints.

### Concept -> generation params

Constructor kwargs accepted (unnamed ones roll randomly):

- **base_rank** (Samurai/Monk): the rank *number*. Map role words to it:
  - Samurai: `3-4` street Magistrate, `5` County Magistrate, `6` Deputy
    Provincial Minister, `7` Provincial Minister, `8` Governor, `9` Deputy
    Minister, `10` Minister, `11` Chancellor. "Young/junior/green" leans low
    (2-4); "senior/veteran" leans high.
  - Monk: `1` Grand Abbot, `2` Abbot, `3` Steward, `4` Senior Monk/Preceptor,
    `5` Adept/Country Monk, `6` Junior Monk, `7` Acolyte, `8` Novice, `9` Initiate.
  - Peasant has no rank table; omit base_rank (defaults to 0).
- **clan** (Samurai): `lion crab crane unicorn scorpion dragon phoenix imperial
  fox wasp sparrow mantis dragonfly hare`.
- **family**, **house**, **lineage**, **school** (Samurai): pin only if named.
- **post** (Samurai): `magistrate`, `yoriki`, `clerk`, or `unposted`. Overrides
  the rank designator (a Rank 8 samurai who is a clerk, not a Governor).
- **ministry** (Samurai, with yoriki/clerk): one of `Ministry of Rites /
  Retainers / Revenue / War / Works / Justice`.
- **location** (Samurai): an explicit place tag (else auto-derived). See
  "Location tags" - for a Samurai you MAY instead pass the single place via this
  kwarg, but the uniform `LOCATION_TAGS` append in Step 2 covers all types.
- **order**, **seat** (Monk): the Fortune's Order and, for ranks 4-5, which of
  the paired roles.
- **gender** is NOT a constructor arg. If the GM pins a gender, generate in a
  re-roll loop until it matches (Step 2 handles this) - this keeps the name and
  gendered traits coherent.

If unspecified, base_rank is picked randomly from the type's rank table (Peasant
-> 0), mirroring the webapp's Generate button.

### Location tags (REQUIRED - add them explicitly)

The chargen engine only auto-tags a **Samurai**'s location (derived from house/
lineage/rank, and only sometimes). **Monk and Peasant sheets carry NO location
tag at all** - `Monk.gen_tags` emits just the order and rank designator,
`Peasant.gen_tags` just `peasant`. So a monk or peasant will upload with no sense
of *where* they are unless you add it. Always tag the NPC's place, via the
`LOCATION_TAGS` list in Step 2.

**Tag at the scale of the posting**, mirroring how the existing cast is tagged
(the campaign conventions, confirmed against real records):

- Province -> `<Name> province` (lowercase noun): `Nagahara province`, `Minami province`.
- Castle-town / domain seat -> the town name: `Shiro Reiji`, `Shiro Daika`.
- County -> `<Name> county`: `Hayakawa county`.
- Village -> `<Name> village`: `Hoshigaoka village`.
- Domain -> `<Name> domain`: `Reiji domain`.

Match the character's reach: a **domain-capital abbot** gets the town
(`Shiro Reiji`); a **provincial abbot** gets the province
(`['Order of Bishamon', 'Abbot', 'Nagahara province']`); a **village monk or
peasant** gets the fine-grained stack the cast uses for locals
(`['Order of Bishamon', 'Country Monk', 'Nagahara province', 'Hoshigaoka village',
'Reiji domain', 'Hayakawa county']`). When unsure of the exact scale, prefer the
one the surrounding cast uses for comparable NPCs, or ask in Step 1.

## Step 1 - Ask only about genuinely-missing essentials

The only truly required field is **type**. If you could not infer it, ask with
AskUserQuestion (Samurai / Monk / Peasant). Otherwise, do NOT interrogate the GM
about clan/rank/gender/etc. - unspecified attributes are *supposed* to roll
randomly. Ask a follow-up ONLY if the concept implies the GM cares about a
detail but left it ambiguous (e.g. "a magistrate" without saying which clan, and
they seem to want a specific one). When in doubt, roll it and let the GM re-roll
in Step 2. Keep questions to at most one round.

**Location is the one detail worth chasing** (Step 0, item 3): the NPC should
carry a place tag, and monk/peasant sheets supply none on their own. If the
concept or the campaign context makes the location clear, use it silently; if the
NPC is plainly being placed in the campaign but no location is given or
inferable, fold a "where are they posted?" into this same one round of questions.

## Step 2 - Roll the skeleton and let the GM re-roll

```bash
cd /gm-assistant/webapp && python3 - <<'PY'
import l7r, json
from random import choice
from chargen import config, synthesis, opcache, op
from chargen.character import Character
TYPE = "[TYPE]"                 # 'Samurai' | 'Monk' | 'Peasant'
PARAMS = [PARAMS_DICT]          # e.g. {"base_rank": 5, "clan": "crab", "post": "magistrate"}
GENDER = "[GENDER]"             # '' | 'male' | 'female'
LOCATION_TAGS = [LOCATION_TAGS] # place tags at the posting's scale, e.g.
                                # ["Shiro Reiji"] or ["Nagahara province"] or
                                # ["Hoshigaoka village", "Hayakawa county", ...]
if "base_rank" not in PARAMS:
    ranks = config.get("ranks", {}).get(TYPE, {})
    if ranks:
        PARAMS["base_rank"] = int(choice(list(ranks)))
for _ in range(500):            # re-roll only to satisfy a pinned gender
    char = Character.types()[TYPE](**PARAMS)
    if not GENDER or char.gender == GENDER:
        break
d = char.to_dict()
# The engine tags a Samurai's location (sometimes); Monk/Peasant get none. Append
# the posting's place tags uniformly, de-duped and order-preserving, so every NPC
# lands with a location (see "Location tags"). Do NOT leave this empty for a
# monk/peasant who has a known posting.
for t in LOCATION_TAGS:
    if t and t not in d["tags"]:
        d["tags"].append(t)
json.dump(d, open("[SCRATCH]/chargen-character.json", "w"), default=str)
open("[SCRATCH]/chargen-formatted.txt", "w").write(synthesis.format_character(d))
snapshot, recent, n = opcache.get_campaign_context(exclude_name=d.get("full_name"))
open("[SCRATCH]/chargen-campaign-context.txt", "w").write((snapshot + "\n\n" + recent).strip())
# Authoritative name->slug map of every existing OP character, for wrapping cast
# references in the backstory as OP links (see 3b) and for the review agent.
try:
    cast_links = {c["name"]: c["slug"] for c in op.existing_characters() if c.get("slug")}
except Exception:
    cast_links = {}
json.dump(cast_links, open("[SCRATCH]/chargen-cast-links.json", "w"), indent=0)
print("NAME:", d["full_name"], "| GENDER:", d["gender"], "| CLAN:", d.get("clan"),
      "| RANK:", d["rank"], "| AGE:", d["age"], "| TAGS:", d["tags"],
      "| CONTEXT:", n, "characters | CAST-LINKS:", len(cast_links))
print("---")
print(synthesis.format_character(d))
PY
```

**Read** `$SCRATCH/chargen-formatted.txt` and show the GM the rolled sheet
(name, clan/family, rank, age, honor, traits, and the tags - including the
location tag(s) you added). Then ask with AskUserQuestion:

1. **Use this character** -> Step 3.
2. **Re-roll** -> rerun Step 2 unchanged, present the new roll.

A free-text ("Other") answer is a re-roll *with new constraints* (e.g. "re-roll
but make them Crane", "older", "make them a woman"): fold it into `PARAMS` /
`GENDER` and rerun. Do this cheap re-roll loop BEFORE spending on a portrait or a
backstory.

## Step 3 - Tagline, backstory, and portrait

Once the sheet is locked:

**3a. Write the tagline.** OP's one-line summary on the Characters list (the field
`/synthesize` later reads back). It is PLAYER-FACING, so keep it **terse and
player-safe**: state only who the character publicly is - their office/title and
where they serve, in the shape `<Office/Title> of/for <Place>` (e.g. "Guardian of
the Temple Treasury for the Sovereign Temple of Bishamon in Shiro Reiji"). Use the
character's formal office title where the setting gives one. Do NOT include
anything the PCs might not know (birth clan/family or origin, secrets, hidden
loyalties - nothing that lives only in the GM-only backstory), and do NOT add
color commentary or evaluative flourish ("the capable hand that...", "ambitious",
"in the shadow of..."). Write it to `$SCRATCH/chargen-tagline.txt`; you will show
it in the review for the GM to accept or edit.

**3b. Targeted setting research + write the backstory yourself.** Follow the
`/synthesize` skill's **Step 2b (targeted research)** and **Step 2c (write it
yourself)** exactly - that skill is the single source of truth for the prose
rules; read `.claude/skills/synthesize/SKILL.md` if you need to refresh them.
In brief: read a few focused setting sections for this character's clan/posting/
caste (caste is known from TYPE: Samurai->samurai, Monk->monk, Peasant->peasant -
no inference needed), read `$SCRATCH/chargen-campaign-context.txt` in full
(consistency with the existing cast is a hard requirement), then write 1-3 short
paragraphs treating the rolled traits as facets of ONE coherent person. Honor
every content rule there: reconcile trait tensions, commit to concrete
specifics, grounded-and-mundane by default, keep the timeline consistent with
the rolled age, RANK is peerage not office, low honor = "as good as their
incentives" not villainy, house style (hyphens only, "domain" not "demesne",
"humans/inhabitants" for generic demographics, no headings/bullets).

**Link every reference to another OP character** (GM preference). When the prose
names another character who has an Obsidian Portal record, wrap the first mention
as an OP internal link `[[:slug|Display]]` - leading colon, the slug from
`$SCRATCH/chargen-cast-links.json` (the authoritative name->slug map), and the
display text is the character's FULL name, e.g.
`[[:hida-no-reiji-natsuo|Hida no Reiji Natsuo]]` (not the short "Natsuo"); the
linked first mention reads as the full name, later bare mentions may use the short
form. Link only characters that HAVE a record (in the map); leave a not-yet-created
character bare UNLESS the cast already links it anticipatorily in GM-only notes
(then match that, e.g. `[[:soun|Soun]]`). Do not link places, families, clans, or
temples - only character records.

Write the final prose to `$SCRATCH/chargen-backstory.txt`.

**3b-review. Run the `backstory-review` subagent before the GM sees the prose.**
The author is not a reliable reviewer of their own prose (Principle I). This agent
runs the GM's growing catalog of previously-caught mistakes plus the baseline
canon/style rules as an enumerated sweep, so recurring errors are fixed in-session
instead of landing on the GM again. Launch it (Agent tool, `subagent_type:
backstory-review`) and pass the paths to `$SCRATCH/chargen-backstory.txt`,
`$SCRATCH/chargen-formatted.txt`, `$SCRATCH/chargen-character.json`,
`$SCRATCH/chargen-campaign-context.txt`, `$SCRATCH/chargen-cast-links.json`, and
`$SCRATCH/chargen-tagline.txt`. Apply every FLAG it returns (rewrite the prose in
`chargen-backstory.txt`, or the tagline in `chargen-tagline.txt`), re-running the
agent if a fix is substantial, until it comes back `clean` / `tweak-before-GM`
with no unaddressed flags. Only then present to the GM. **Same-session gotcha**: if `.claude/agents/backstory-review.md`
was created or edited THIS session, launching by `subagent_type` gets the stale
snapshot - instead launch a `general-purpose` agent told to Read that definition
file and adopt it verbatim, then do the review (see the harness-behavior note in
the project CLAUDE.md).

**3c. Generate the portrait** (this is the ~$0.07 image call - do it once here,
regenerate only on request).

**`art.generate_prompt` is caste-aware** (since 2026-07-20; it used to dress
every subject as a samurai - a Grand Abbot came out as a two-sword bushi,
2026-07-13). It classifies the subject via `art.infer_character_type` (explicit
`character_type` wins, else the dict shape: `order`/`seat` keys mean Monk, a
`peasant` tag means Peasant, default Samurai) and dresses accordingly: samurai
keep the school-based kimono/robes wardrobe, monks get a monastic look (worn
robes with kesa, prayer beads, no swords/armor, and a 50/50 roll between a
shaved head and hair grown out from the tonsure - never a topknot), peasants
get roughspun work clothes with no swords and no topknot. The full
`chargen-character.json` dict carries those signals, so calling it as-is is
correct **for every caste**. Optionally append one prompt line for monk
seniority (finer robes for a senior abbot, humbler for a country monk) or a
peasant's trade (a farmer's sun-weathered look, a fisherman's gear).

```bash
cd /gm-assistant/webapp && python3 - <<'PY'
import l7r, json, re, base64
from chargen import art
d = json.load(open("[SCRATCH]/chargen-character.json"))
name = d["full_name"]
prompt = art.generate_prompt(d)  # caste-aware; append seniority/trade nuance if wanted
img = base64.b64decode(art.generate_image_base64(prompt))
safe = re.sub(r"[^a-zA-Z0-9]", "", name.replace(" ", ""))
fname = f"{safe}.png"
open(f"[SCRATCH]/{fname}", "wb").write(img)
open("[SCRATCH]/chargen-art-prompt.txt", "w").write(prompt)  # record what was used
print("PORTRAIT:", f"[SCRATCH]/{fname}", "| bytes:", len(img))
PY
```

**Read** the saved PNG yourself to confirm it is a real portrait AND caste-correct
(a monk must not come back as a sword-bearing samurai); if it is wrong or a refusal
/ text-only image, fix the prompt and regenerate before proceeding. Tell the GM the
portrait's scratch path so they can open it if they want.

Present to the GM: the **tagline**, the **portrait path**, and the **FULL
backstory reproduced verbatim in your reply** (never leave it only in a file),
plus which caste and how many campaign characters you used.

## Step 4 - Review menu

Use AskUserQuestion. State the destination explicitly, including **public vs
GM-only** (from Step 0), so the GM confirms privacy here:

1. **Upload to Obsidian Portal** (`public` or `GM-only` as parsed) -> Step 5.
2. **Regenerate the backstory** -> rewrite it yourself from the same inputs (a
   genuinely different angle), re-present. Portrait unchanged.
3. **Regenerate the portrait** -> rerun 3c only. Backstory unchanged.

A free-text ("Other") answer is "upload with these changes": apply the described
edits (to backstory, tagline, or the public/GM-only choice), then Step 5. If the
GM asks to re-roll the whole character, go back to Step 2.

## Step 5 - Upload (create the OP record with everything attached)

```bash
cd /gm-assistant/webapp && python3 - <<'PY'
import l7r, json, re
from chargen import config, art, op, opsynth
d = json.load(open("[SCRATCH]/chargen-character.json"))
backstory = open("[SCRATCH]/chargen-backstory.txt").read().strip()
summary = """[TAGLINE]"""
gm_only = [GM_ONLY]                      # True or False (Python literal)
name = d["full_name"]
tags_list = d.get("tags") or []
public = d["public"]
private = d["private"]
gm_info = opsynth.merge_backstory(private, backstory)   # bare prose appended, /synthesize-compatible

# Re-load and re-crop the portrait saved in Step 3c, upload avatar + bio image.
safe = re.sub(r"[^a-zA-Z0-9]", "", name.replace(" ", ""))
fname = f"{safe}.png"
img = open(f"[SCRATCH]/{fname}", "rb").read()
x, y, w, h = art.get_headshot_crop(img)
head = art.crop_headshot(img, x, y, w, h)
avatar_id = str(op.upload_avatar(head, fname).get("id", ""))
fid = op.upload_image(img, fname).get("id")
embed = f"[[File:{fid} | class=media-item-align-none | {fname}]]" if fid else ""

op.create_character(
    name, summary=summary, tags=tags_list, description=public,
    bio=embed, gm_info=gm_info, avatar_upload_id=avatar_id, gm_only=gm_only,
)
slug = name.lower().replace(" ", "-")
base = config["campaign_url"]
print("CREATED:", name, "| gm_only:", gm_only)
print("VIEW:", base + "/characters/" + slug)
print("EDIT:", base + "/characters/" + slug + "/edit")
PY
```

`merge_backstory` appends the prose to GM-only notes as bare, unmarked prose
(no header/footer - GM decision 2026-07-20). A later `/synthesize` run on this
same character cannot recognize its earlier prose and would append a second
backstory, so warn the GM before re-synthesizing a character that already has
one. The public description, tags, avatar, and embedded portrait all come from
the rolled sheet.

Report exactly what was created: the name, **public vs GM-only**, the tagline,
that the backstory went into GM-only notes, that the portrait was attached, and
the View/Edit URLs. If `create_character` raises a 422/403, the OP session or
authenticity token has expired - tell the GM to refresh it in
`development-secrets.ini` (see `probe_op_oauth.py`); nothing was created.
