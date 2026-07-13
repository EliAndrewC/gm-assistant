---
name: synthesize
description: Write a backstory for an existing Obsidian Portal NPC, Claude-native - reads the OP record + tagline and the campaign-context cast, researches the setting files directly, writes the prose IN-SESSION (no external LLM), optionally steered by GM notes after a ` - ` separator, presents a review (upload as-is, regenerate, or upload with typed changes), and merges the result into GM-only notes.
argument-hint: <character name> [ - steering notes]
allowed-tools: Bash Read Grep AskUserQuestion
---

# Synthesize a backstory for an existing OP character (Claude-native)

Turn an NPC that already exists on the campaign wiki into a grounded backstory.
**You write the prose yourself, in this session** - this skill does NOT call an
external LLM (GM decision 2026-07; the webapp's Synthesize Backstory button
still uses the Gemini engine in `chargen/synthesis.py`, but the chat path is
Claude-native). The `chargen` package still does the plumbing: `op` fetches the
record, `opsynth` parses/merges, `opcache` supplies the campaign cast.

Where the Gemini path ships a ~100k-token corpus per call, you instead READ
TARGETED setting material on demand (you already carry the project context) -
the only bulk input you ingest wholesale is the campaign-context cast block
(~18k tokens).

**All Python runs from `/gm-assistant/webapp`** (imports `l7r` first to dodge
the chargen circular-import, exactly like the webapp). Substitute the bracketed
placeholders. `$SCRATCH` is this session's scratchpad directory.

## Step 0 - Split the argument into name and steering notes

The argument is the character name, optionally followed by ` - ` (space-hyphen-
space) and free-text **steering notes** - a description, event, characterization,
or relationship the GM wants incorporated. Split on the FIRST ` - `: everything
before is `[NAME]`, everything after is `[STEERING]` (high-priority GM guidance,
followed closely but never contradicting the setting or the character's stated
facts). No ` - ` means the whole argument is `[NAME]` and `[STEERING]` is empty.

## Step 1 - Resolve the name

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

- **unique** -> proceed to Step 2.
- **ambiguous** -> show the candidates and ask the GM (AskUserQuestion). Never guess.
- **none** -> report it, offer the nearest names, stop.

If `existing_characters()` returns nothing (OP unreachable), report that and
stop - do not fabricate a character.

## Step 2 - Gather the inputs

```bash
cd /gm-assistant/webapp && python3 - <<'PY'
import l7r, json
from chargen import op, opsynth, opcache, synthesis
ID, NAME, URL = "[ID]", "[NAME]", "[URL]"
STEERING = """[STEERING]"""
body = op.get_character_body(ID) or {}
html = op.fetch_character_page(URL) if URL else None
tagline = opsynth.parse_tagline(html) if html else ""
# Infer caste from the hand-written notes only (text before the first "--- "
# section): synthesized/added sections may mention monks, peasants, etc. and
# would poison the inference (caught live on a magistrate whose salt-ward note
# mentioned a shrine monk, 2026-07).
caste = opsynth.infer_caste(body.get("tags") or [], (body.get("game_master_info") or "").split("--- ")[0])
char = opsynth.build_synthesis_character(body, tagline)
snapshot, recent, n = opcache.get_campaign_context(exclude_name=body.get("name") or NAME)
json.dump(
    {"id": ID, "name": body.get("name") or NAME,
     "gm_info": body.get("game_master_info") or "", "caste": caste,
     "tagline": tagline, "steering": STEERING},
    open("[SCRATCH]/synthesize-handoff.json", "w"),
)
open("[SCRATCH]/synthesize-character.txt", "w").write(synthesis.format_character(char))
open("[SCRATCH]/synthesize-campaign-context.txt", "w").write((snapshot + "\n\n" + recent).strip())
open("[SCRATCH]/synthesize-tagline.txt", "w").write(tagline or "")  # existing OP tagline, for the review's tagline check
# Authoritative name->slug map of every existing OP character, for wrapping cast
# references in the backstory as OP links (Step 2c) and for the review agent.
try:
    cast_links = {c["name"]: c["slug"] for c in op.existing_characters() if c.get("slug")}
except Exception:
    cast_links = {}
json.dump(cast_links, open("[SCRATCH]/synthesize-cast-links.json", "w"), indent=0)
print("CASTE:", caste, "| TAGLINE:", tagline or "(none)", "| STEERING:", STEERING or "(none)",
      "| CONTEXT:", n, "characters,", len(snapshot) + len(recent), "chars,",
      len(cast_links), "cast-links")
PY
```

Then **Read** `$SCRATCH/synthesize-character.txt` (the subject's formatted
record) and `$SCRATCH/synthesize-campaign-context.txt` (the campaign cast -
read it in full; consistency with these characters is a hard requirement).

## Step 2b - Targeted setting research

Instead of a shipped corpus, research what THIS character needs. Typical
lookups (grep, then read the hits):

- The character's **posting and its economics**: `/host-l7r-repo/setting/budgets.md`
  (worked examples: county magistrate, governor, daimyo, ministers), plus
  `/gm-assistant/setting/government.md`, `demographics.md`, `median-domain.md`.
- **Clan / family / lineage** background: `/host-l7r-repo/setting/l7r.md`
  (grep the family and place names), `/gm-assistant/setting/lineages.md`,
  `clans-and-imperials.md`.
- **Caste-specific life**: for a Monk, `/gm-assistant/cosmology/` and the
  temple skill's reference material - including its **Monk Titles and Ceremonial
  Offices** section, so a monk with a specific duty (Steward, Senior Monk,
  appraiser) gets their correct ceremonial title (remember the Fortune-swap rule);
  for a Peasant, `/gm-assistant/setting/castes.md`,
  `professions.md`, `village-headsmen.md`, `economics.md`.
- Anything the tags or tagline name (an institution, a place, another NPC).

Read selectively - a few focused sections, not whole files. You already know
the house conventions from CLAUDE.md.

## Step 2c - Write the backstory yourself

Write 1 to 3 short paragraphs of prose. Content rules (these mirror the
engine's tested instructions - keep honoring them):

- Treat the traits as facets of ONE coherent person - weave, never list.
- Actively reconcile tensions between traits (a humble samurai with low honor,
  a devout one who is religiously unorthodox): decide what specific story makes
  both true at once, and commit.
- Commit to concrete, plausible specifics - a belief, habit, grudge, fear,
  relationship, or episode - never hedge or stay abstract.
- Prefer setting-grounded times (a named festival, month, or season) over "a
  few years ago" where it fits naturally.
- Grounded and mundane by default: the supernatural is real but rare and
  ambiguous; no magic, curses, or literal supernatural events unless the
  character's own details clearly point that way - and keep it uncertain even then.
- The character's stated facts are authoritative (summary, tags, posting, clan,
  family, school, age, rank, recognition). Keep the timeline consistent with
  the stated age. RANK is peerage, not office - never promote an unposted
  character into the office their rank would typically imply.
- Stay consistent with the campaign-context characters; when steering names one
  of them, ground the relationship in that character's stated backstory.
- Low honor means "as good as their incentives", not cartoon villainy (the GM's
  honor-as-conviction framework).
- Register: laconic, matter-of-fact, concrete. No purple prose. "domain" not
  "demesne"; "humans"/"inhabitants"/"population" for generic demographics
  ("people" means samurai). Hyphens only - never em- or en-dashes. Prose
  paragraphs only, no headings or bullets.
- **Link every reference to another OP character** (GM preference). When the prose
  names another character who has an Obsidian Portal record, wrap the first mention
  as an OP internal link `[[:slug|Display]]` - leading colon, the slug from
  `$SCRATCH/synthesize-cast-links.json` (the authoritative name->slug map), and the
  display text is the character's FULL name, e.g.
  `[[:hida-no-reiji-natsuo|Hida no Reiji Natsuo]]` (not the short "Natsuo"); the
  linked first mention reads as the full name, later bare mentions may use the
  short form. Link only characters that HAVE a record; leave a not-yet-created
  character bare UNLESS the cast already links it anticipatorily in GM-only notes
  (then match that). Not places/families/temples.

## Step 2c-review - Run the `backstory-review` subagent before the GM sees it

The author is not a reliable reviewer of their own prose (Principle I). Before
presenting, write the drafted prose to `$SCRATCH/synthesize-backstory.txt` and run
the `backstory-review` subagent on it - it sweeps the GM's growing catalog of
previously-caught mistakes plus the baseline canon/style rules, so recurring
errors get fixed in-session instead of reaching the GM again. Launch it (Agent
tool, `subagent_type: backstory-review`) and pass the paths to
`$SCRATCH/synthesize-backstory.txt`, `$SCRATCH/synthesize-character.txt`,
`$SCRATCH/synthesize-campaign-context.txt`, `$SCRATCH/synthesize-cast-links.json`,
and `$SCRATCH/synthesize-tagline.txt` (plus any steering). Apply backstory FLAGs
by rewriting `synthesize-backstory.txt`. The tagline here is the character's
EXISTING OP one, which this skill does not normally author - so if the agent
flags it (leaks non-public info, or color commentary), do NOT silently rewrite it;
surface it to the GM in your presentation and offer to trim it (a terse
`<Office/Title> of/for <Place>`), applying `op.update_character(id, tagline=...)`
only if they say yes. Apply every FLAG it returns (rewrite `synthesize-backstory.txt`),
re-running if a fix is substantial, until no unaddressed flags remain. **Same-
session gotcha**: if `.claude/agents/backstory-review.md` was created or edited
THIS session, launching by `subagent_type` gets the stale snapshot - instead
launch a `general-purpose` agent told to Read that definition and adopt it
verbatim, then review (see the harness-behavior note in the project CLAUDE.md).

Then present to the GM: the inferred **caste**, the **tagline**, the
**steering** applied, how many campaign characters you read - and **reproduce
the FULL backstory verbatim in your reply message** (never leave it only in a
tool result).

## Step 3 - Review menu (two options plus free-text changes)

Use AskUserQuestion with exactly these TWO options:

1. **Upload as-is to Obsidian Portal** -> Step 4 unchanged.
2. **Generate another synthesis** -> rewrite it yourself from the same inputs
   (take a genuinely different angle, don't lightly rephrase), re-present.

Free-text ("Other") answers are "upload with these changes": apply the
described edits yourself, then Step 4 with the edited text.

## Step 4 - Upload (idempotent, notes-preserving)

Upload the reviewed prose. It already lives in
`$SCRATCH/synthesize-backstory.txt` from Step 2c-review; if the GM chose "upload
with these changes" (Step 3 free-text), apply those edits to that same file
first, then:

```bash
cd /gm-assistant/webapp && python3 - <<'PY'
import l7r, json
from chargen import op, opsynth
h = json.load(open("[SCRATCH]/synthesize-handoff.json"))
prose = open("[SCRATCH]/synthesize-backstory.txt").read()
body = op.get_character_body(h["id"]) or {}          # re-fetch to avoid staleness
merged = opsynth.merge_backstory(body.get("game_master_info") or "", prose)
op.update_character(h["id"], game_master_info=merged)
print("Uploaded to", h["name"], "- backstory merged into GM-only notes.")
PY
```

`merge_backstory` preserves every existing note and replaces only its own
`--- Synthesized Backstory (auto) ---` block, so re-running never duplicates or
clobbers. Report exactly what was written and where. If `update_character`
raises, tell the GM the save did not complete and their existing notes are
unchanged.
