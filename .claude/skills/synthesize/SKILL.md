---
name: synthesize
description: Generate a Gemini backstory for an existing Obsidian Portal NPC (the chat twin of the webapp Synthesize Backstory button) - reads the OP tagline, reuses the webapp's per-caste corpus + campaign context, optionally steered by GM notes after a ` - ` separator, presents a review (upload as-is, regenerate, or upload with typed changes), and merges the result into GM-only notes.
argument-hint: <character name> [ - steering notes]
allowed-tools: Bash Read AskUserQuestion
---

# Synthesize a backstory for an existing OP character

Turn an NPC that already exists on the campaign wiki into a grounded Gemini
backstory, without opening the web generator. The heavy lifting is done by the
`chargen` package (`opsynth` pure logic, `op` network boundary, `synthesis` +
`brief` + `opcache` reused verbatim from the webapp). This file is orchestration.

**All Python runs from `/gm-assistant/webapp`** (imports `l7r` first to dodge the
chargen circular-import, exactly like the webapp). Substitute the bracketed
placeholders. Write the handoff JSON to this session's scratchpad directory (call
it `$SCRATCH`).

## Step 0 - Split the argument into name and steering notes

The argument is the character name, optionally followed by ` - ` (space-hyphen-
space) and free-text **steering notes** - a description, event, characterization,
or relationship the GM wants incorporated (e.g. `/synthesize Jitsuyo - was
manipulated by the PCs at a drinking house over Fox/Crane folktales`). Split on
the FIRST ` - `: everything before is `[NAME]` (used for resolution only),
everything after is `[STEERING]` (carried verbatim into synthesis as high-
priority GM guidance). No ` - ` means the whole argument is `[NAME]` and
`[STEERING]` is empty. Do not fold steering text into the name match.

## Step 1 - Resolve the name

Run, with `[NAME]` = the name part from Step 0 (NOT the steering text):

```bash
cd /gm-assistant/webapp && python3 - <<'PY'
import l7r, json
from chargen import op, opsynth
NAME = "[NAME]"
chars = op.existing_characters()
r = opsynth.match_character(NAME, chars)
print("KIND:", r.kind)
if r.kind == "unique":
    c = r.character
    print(json.dumps({"id": c["id"], "name": c["name"], "url": c.get("character_url", "")}))
elif r.kind == "ambiguous":
    for c in r.matches:
        print(json.dumps({"id": c["id"], "name": c["name"], "url": c.get("character_url", "")}))
else:
    print("NEAREST:", ", ".join(r.nearest))
PY
```

- **unique** -> proceed to Step 2 with that `id`, `name`, `url`.
- **ambiguous** -> show the candidates and ask the GM which one (AskUserQuestion),
  then proceed. Never guess.
- **none** -> tell the GM there is no match and offer the nearest names. Stop.

If `existing_characters()` returns nothing (OP unreachable), report that and stop -
do not fabricate a character.

## Step 2 - Gather context and synthesize

Run, with `[ID]`, `[NAME]`, `[URL]` from Step 1 and `[SCRATCH]` = the session
scratchpad path:

```bash
cd /gm-assistant/webapp && python3 - <<'PY'
import l7r, json
from chargen import op, opsynth, opcache, synthesis
ID, NAME, URL = "[ID]", "[NAME]", "[URL]"
STEERING = """[STEERING]"""   # from Step 0; empty string if the GM gave none
body = op.get_character_body(ID) or {}
html = op.fetch_character_page(URL) if URL else None
tagline = opsynth.parse_tagline(html) if html else ""
caste = opsynth.infer_caste(body.get("tags") or [], body.get("game_master_info") or "")
char = opsynth.build_synthesis_character(body, tagline)
snapshot, recent, n = opcache.get_campaign_context(exclude_name=body.get("name") or NAME)
backstory = synthesis.synthesize(
    char, extra_notes=STEERING, campaign_context=snapshot,
    character_type=caste, campaign_context_recent=recent,
)
json.dump(
    {"id": ID, "name": body.get("name") or NAME,
     "gm_info": body.get("game_master_info") or "", "caste": caste,
     "tagline": tagline, "steering": STEERING, "backstory": backstory},
    open("[SCRATCH]/synthesize-handoff.json", "w"),
)
print("CASTE:", caste, "| TAGLINE:", tagline or "(none)", "| STEERING:", STEERING or "(none)", "| CONTEXT:", n)
print("----")
print(backstory)
PY
```

`STEERING` is passed as `extra_notes`, which the engine turns into a high-priority
GM STEERING NOTES block: it is followed closely (overriding the defaults) but
never contradicts the setting brief or the character's own OP details. So
`- this Steward has the respect of the entire temple, even more than the Grand
Abbot, and is functionally untouchable` shapes the whole backstory around that.

Then present to the GM:
- State the inferred **caste** and the **tagline** you read (so they can catch a
  mis-inference), the **steering** you applied (if any), and how many campaign
  characters were in context.
- **Reproduce the FULL backstory prose verbatim in your own reply message** (all
  paragraphs). Do NOT leave it only in the script's stdout: the terminal
  collapses long tool output and the GM would have to hit Ctrl+O to read it,
  whereas your reply text is always shown in full. Paste the whole thing.

If the corpus is missing the synthesis will fail loud - relay the error, do not
retry with a thinner prompt.

### Step 2b (optional, P3) - related cast members

If the tagline names another campaign NPC and the GM wants the extra grounding,
build/refresh the tagline cache and compute related characters, then re-run
Step 2 with those names woven into `extra_notes=`. This fetches OP pages for the
cast (incremental after the first run) - skip it for speed if not wanted:

```bash
cd /gm-assistant/webapp && python3 - <<'PY'
import l7r, json, os
from chargen import op, opsynth
CACHE = "opcache/taglines.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
chars = op.existing_characters()
fetch = lambda ch: (opsynth.parse_tagline(op.fetch_character_page(ch.get("character_url", "")) or "") or "")
cache, stats = opsynth.refresh_taglines(cache, chars, fetch)
json.dump(cache, open(CACHE, "w"))
names = {str(c["id"]): c["name"] for c in chars}
SUBJECT, TAGLINE = "[NAME]", "[TAGLINE]"
cast_taglines = {names[cid]: v["tagline"] for cid, v in cache.items()
                 if v.get("tagline") and names.get(cid) and names[cid] != SUBJECT}
print("RELATED:", ", ".join(opsynth.related_by_tagline(TAGLINE, cast_taglines, list(cast_taglines))) or "(none)")
PY
```

## Step 3 - Review menu (two options plus free-text changes)

Use AskUserQuestion with exactly these TWO explicit options:

1. **Upload as-is to Obsidian Portal** -> Step 4 with the backstory unchanged.
2. **Generate another synthesis** -> re-run Step 2 (fresh call, SAME `[STEERING]`)
   and re-present this menu. (If the caste looked wrong, this is where a corrected
   run happens.)

The "upload with changes" path is the free-text ("Other") box, not a listed
option: whatever the GM types there IS the set of changes to make. When the GM
answers with free text, treat it as "upload with these changes" - apply the
described edits to the backstory yourself, then go to Step 4 with the edited
text. (The GM describes the change in one step instead of picking a "with
changes" option and then being asked what.)

## Step 4 - Upload (idempotent, notes-preserving)

Run, with `[SCRATCH]` and `[BACKSTORY_FILE]` = a scratchpad file holding the final
(possibly edited) backstory text:

```bash
cd /gm-assistant/webapp && python3 - <<'PY'
import l7r, json
from chargen import op, opsynth
h = json.load(open("[SCRATCH]/synthesize-handoff.json"))
prose = open("[BACKSTORY_FILE]").read()
body = op.get_character_body(h["id"]) or {}          # re-fetch to avoid staleness
merged = opsynth.merge_backstory(body.get("game_master_info") or "", prose)
op.update_character(h["id"], game_master_info=merged)
print("Uploaded to", h["name"], "- backstory merged into GM-only notes.")
PY
```

`merge_backstory` preserves every existing note and replaces only its own
`--- Synthesized Backstory (auto) ---` block, so re-running the skill later never
duplicates or clobbers. Report exactly what was written and where (the character's
GM-only notes). If `update_character` raises, tell the GM the save did not
complete and that their existing notes are unchanged.
