---
name: dream
description: Generate Rokugani dream-omen scenes - randomized d10 dream tables for one or more PCs seeking the will of a fortune (or other spirit) in sleep, grounded in the six-doctrine theology of attunement. Strange, open fragments that describe the dream's events and never its meaning.
---

# Dreams

Generate dream-omen scenes for the table: the set of tables a GM rolls on when one or more PCs sleep seeking guidance, usually beseeching a single fortune (but other spirits can send dreams too - ancestors, nature kami, the restless dead, gaki, Shadowlands things). The output is not a story; it is a rolling apparatus plus a bank of fragments. The players roll, the GM reads a band and picks a fragment, and the group must then interpret an ambiguous aggregate to discern the god's will. They really can learn it - but imperfectly, through noise and guesswork, never as a clean answer.

This skill exists because a scene we ran (PCs sleeping in a Temple of Ebisu to divine the Fortune of honest work's will about sheltering a fugitive) worked well, and the shape of it generalizes. What follows is that shape, plus the hard-won craft rules for writing the fragments.

## Why dreams work this way: the six doctrines

Rokugan is not the real world. Here the gods really are reaching out through dreams, more or less constantly; the difficulty is never that heaven is silent, it is that a mortal is a crowded, noisy receiver and can rarely attune to any one voice well enough to hear it clearly. Noise and silence are not failures of the system - they are theologically required by it. This is the core of Kitsu Okura's treatise, and it is the ground the whole mechanic stands on. Read it before writing a scene; the doctrines are the design spec.

<!-- SOURCE: GM NOTES - DO NOT MODIFY -->
We seek to know the will of the fortunes, to follow their guidance, to gain their favor, and to teach our children to do the same.  Few accomplish any part of this undertaking, for the ways of the fortunes are inscrutable.  Even those lucky and unlucky few whom the fortunes contact directly seldom comprehend the messages they've received.

Why should this be?  Why do the fortunes not communicate their desires more clearly?  When their instructions are misunderstood, their wishes often go unfulfilled.

I have traveled the world, combed through every library of note, and interviewed every living authority with wisdom to offer, from Isawa no Naka Kuro to Togashi Hoshi to the Council of Elemental Masters to the Qabal of the Sahir.  All collected wisdom on this topic divides roughly into six major doctrines, which I shall articulate herein.  All of them are wrong, and I shall explain in this treatise the particular failures of each to explain the immense complexity of the ways of the fortunes.  Yet each doctrine contains a glimpse of the truth, so by comprehending each well enough to studiously reject it, we bring ourselves closer to true understanding.

What follows is a brief summary of the six doctrines, each corresponding to the lengthier section of my treatise in which I expound and catalog their merits and flaws.

1. Just as we cannot truly comprehend the will and nature of the fortunes, they struggle to understand our limited minds.  Being so vast in their existence, the fortunes speak to us as we might attempt to communicate with worms.  The more attention and effort is brought to bear, the more danger the worm may be crushed by the weight of the superior being.

2. The fortunes push against one another with their very existence.  Consider the forces which direct human behavior.  Fear, desire, regret.  Loyalty, compassion, courage.  Love, hate, joy.  When we break our normal routine to attempt some great endeavor, it means those forces within ourselves are out of proportion and an overflowing of some emotion spurs us to action.  So too with the fortunes, who collectively maintain the balance of the world itself.  When a fortune commands mortals to act, their instructions are muddied by the thousand other fortunes pulling in a thousand other directions.

3. Our struggle to better understand their instructions is what the fortunes truly desire.  When the teacher sends his pupil on a pilgrimage, it is often the journey and not the destination which matters.  Likewise, after completing some great enterprise on behalf of the fortunes, we must consider whether the task itself was their goal, or the result it produced within us as we struggled to obey them.

4. The fortunes desire only the greatest and most dedicated followers to be rewarded with their blessings.  Why should they squander power and effort on those who will fail to act without clear instructions?  By giving enigmatic directions, only their shrewdest and most resourceful disciples will succeed and prove worthy of being imbued with their power.

5. Communicating their will unambiguously carries a high price, which is rarely worth paying.  Lesser spirits are easily understood by humans, but the fortunes must reduce themselves to such an inferior existence for a time when they choose to communicate clearly.  Why should they bear that burden when their mortal servants are already given sufficient direction to discern their will?

6. The fortunes are vast in their existence, but humans are deep in our nature.  We are composed of many disparate parts, and a single fortune is the avatar of only a single piece of our composition.  While that existence has a weight far beyond mortal man, in a sense it is we who are the giants, for we are constructions of all the fortunes combined.  The fortunes are clear to any who listen, but we so rarely pay our attention to whatever small part of ourselves speaks their will that we wrongly call the fortunes unfathomable.
<!-- END SOURCE -->

What the doctrines drive in the mechanic:

- **Noise is mandatory (doctrines 1, 2, 5).** A thousand fortunes pull a thousand ways, the sought god muddies its own signal to avoid crushing the dreamer, and clear speech costs the god too much to spend freely. So a scene MUST carry a real chance of no dream and of a misleading or unrelated dream. A clean 100%-signal oracle would be heresy against this cosmology, not just bad play.
- **The receiver, not the sender, is the variable (doctrine 6).** You are not tuning heaven; heaven is always transmitting. You are tuning the one small part of yourself that speaks the god's will. That is why the circumstances of the *sleeper* - mindset, recent deeds, place, rites - set the odds, not the god's mood.
- **Aggregate signal is real (doctrines 3, 4).** The struggle to interpret is the point, and the god rewards the shrewd who can. Across 3-5 sleepers, a genuine message is present and recoverable by interpretation - but only by interpretation, never handed over.

Non-fortune senders (ancestors, kami, gaki, the dead, Shadowlands entities) use the same apparatus; the six doctrines are specifically about *fortunes*, but the noise-and-attunement model holds for any sender. When the sender is not a fortune, say so in the scene's GM notes and let the fragments carry that flavor (an ancestor is warmer and more personal than a fortune; a gaki lies).

## The mechanic

- **Roll:** each sleeping PC rolls **1k1 (a single d10)** and reports the number.
- **Bands:** every scene sorts the ten die faces into bands. The always-present bands are **no dream** (poorly remembered), **unrelated** (noise), and **meaningful**. A scene may add a **misleading** band (a dream that reads as a true sending but points wrong - another fortune's crosstalk per doctrine 2, or the dreamer's own psychology wearing a god's mask). **A 10 is always meaningful and opens a lucid dream** (see The 10, below).
- **The face-to-band map is randomized per scene** and never told to the players. Do NOT reuse "1-2 is no dream, 3-4 is noise" - that lets players metagame. Generate a fresh scatter each time with `randomize_bands.py`. The one thing players may know is that a 10 is significant; that is intended and good.
- **Within a band, do not map die faces to specific fragments.** The roll only decides the band. Then you pick (or blindly sub-roll) a fragment from that band's list, so two PCs on the same table who both land in "meaningful" still wake to different dreams. This applies to every band, including meaningful.
- Read results privately and narrate to each player; they should not see the tables or the map.

## Setting the probabilities (attunement rubric)

The odds are a function of how well the *sleeper* is attuned, per doctrine 6. Better circumstances mean fewer blanks and less noise; they never guarantee a clear dream, because the god's own reticence (doctrines 1, 5) sets a floor. Anchor: in the Ebisu scene the PCs handled holy relics, received guided prayer from qualified monks, slept in the god's own temple with open hearts - about as attuned as laypeople get - and there was still a **40% chance of no dream or an irrelevant one.** That 40% under near-ideal conditions is the calibration point; ordinary or poor conditions should be worse.

Factors that lower the no-dream and noise bands (raise signal):

- The right holy site for the god sought (a temple of that fortune, a relevant shrine, a place of the god's aspect).
- A qualified holy person guiding the prayer; relevant rites, relics, offerings, fasting, purification.
- A sincere, open-hearted, undivided sleeper who genuinely seeks the god's will (not one angling for permission).
- Physical rest and spiritual cleanliness.

Factors that raise no-dream / noise / misleading (lower signal):

- Sleeping rough, exhausted, drunk, or in the wrong place; no shrine or the wrong god's shrine.
- A guarded, divided, or self-justifying heart; seeking a rationalization rather than the truth.
- Spiritual taint, recent grave sin, proximity to the Shadowlands or to a competing power (raises the *misleading* band specifically - doctrine 2 crosstalk).

Suggested starting splits (GM overrides freely; a d10 makes tenths natural):

| Attunement | no dream | unrelated / misleading | meaningful (incl. the 10) |
|-----------|----------|------------------------|---------------------------|
| Near-ideal (Ebisu-like) | ~20% | ~20% | ~60% |
| Ordinary | ~30% | ~30% | ~40% |
| Poor / fraught | ~40% | ~30-40% | ~20-30% |

The 10 is always meaningful, so meaningful can never be below 10%. Decide the split, then run `randomize_bands.py` to place the faces.

## Table structure (default: four tables)

Beyond the two shared bands (below), the **meaningful** fragments live in per-cell tables chosen by what is true of each sleeper. The default is a 2x2:

1. **Coarse partition - which god or spirit is sought.** PCs beseeching different powers roll on entirely separate table-sets; a Bishamon-seeker and an Ebisu-seeker do not share a meaningful table. Build one 2x2 per god in play. (Often there is only one god and one partition.)
2. **Split 1 - the sleeper's mentality.** How the character is *leaning* on the question at hand, honestly reported by the player at the table. In the Ebisu scene this was Honest vs Sneaky. Ask the players to report their characters' mindsets truthfully; this narrows four tables to two.
3. **Split 2 - a scene-specific material/physical/spiritual factor.** This changes every time and **the GM specifies it before asking for tables**, because it is tied to the adventure. Examples: which relic they handled; sleeping indoors vs outdoors; whether they accepted or refused an enemy's hospitality before seeking the omen; whether they recently killed in a fight or stayed their hand; whether they lately dealt in judgment or in mercy; whether they came fasting or fed. This narrows two tables to one.

Two binary splits give four meaningful tables per god. Degenerate cases are fine: one split gives two tables; no meaningful split gives a single meaningful table; and a scene may run several gods' 2x2s in parallel.

**Which table a mismatch lands on is often the richest result.** A PC whose mentality or deed does not match what they were hoping for gets answered by the aspect they actually embodied, not the one they wanted. Design the four cells so the contrasts bite.

## The two shared bands (always present, choice-independent)

These do not vary by god, mentality, or factor - every sleeper draws from the same two lists. **Pick from the list, never die-map**, so identical rolls diverge. Keep a handful of options and re-skin a few to the actual place of sleeping.

### No dream (poorly remembered)

The craft goal is **ambiguity about whether anything happened at all**, plus a waking *feeling* conveyed obliquely - never named. Two flavors:

- **Half-waking the real room.** Deliberately blur "I was half awake sensing the actual place" against "the god sent me a dream *of* the place." The Ebisu example (re-skin the sensory details to wherever they slept): *"You dream only the temple itself: the boards, the lamp-oil smell, another sleeper breathing, so faithfully you are not sure you slept. Nothing comes. Your hands are empty and no line is snapped on any board."*
- **Nothing, but a feeling.** No dream, but wake carrying a sensation described through an *event*, not a gloss. Prefer the oblique form: *"You wake with the sense of having dropped a stone into a well and waited for the sound of it striking the bottom, and you waited long enough that it should have struck, and you never heard it land."* (Better than "you wake with hollowness" - that names the feeling; the well *shows* it.)

### Unrelated (noise)

The craft goal is a fragment that **feels meaningful - that is the trap - but bears on nothing.** Domestic, absurd, sensory, self-contained. Players who over-read these are meant to; part of the skill the god rewards is discarding them. Starter examples (write fresh ones per scene, but this is the register):

- *You eat cold rice from a lacquer box on a riverbank and keep finding small river-stones in it, and set each one on the lid in a row. There are eleven. A heron watches. You are not troubled. Then it is morning.*
- *You are counting something - fish, coins, days, you lose track - and every time you reach nine you must start again, not from error but because nine is simply where the count folds back.*

If the scene uses a **misleading** band, that is a THIRD list and a different craft goal: it must read like a genuine sending and point the wrong way (toward another fortune's concern, or the dreamer's own fear or wish). Write it with the same conviction as a meaningful fragment; its wrongness should only be discoverable by interpreting it against the aggregate.

## The 10: lucid dreaming and the point pool

A 10 is the always-significant capstone, and it is fine (good, even) that players know a 10 matters. A 10 does two things: it grants a **meaningful dream** (pick a fragment from the roller's table, as any meaningful result would), and it drops the dreamer into a **lucid dream** with a pool of points to spend on *choices*.

The load-bearing sensibility of the whole skill lives here: **a choice is more interesting than a result.** A 10 never simply hands over information; it hands the dreamer decisions, and the higher they roll, the more decisions they make. The old fixed "Coda of Understanding" - a canned paragraph telling the dreamer the sending was uneven - is now just *one thing a dreamer can choose to spend points learning* (the default flavor wrapper for the group-shape purchases below), not the automatic payout.

**Sizing the pool.** On a 10, reroll the die (1k1). The result is the dreamer's **lucid points** - this reroll only sizes the pool; do not re-consult the band map with it.

- Reroll 1-9: that many lucid points.
- Reroll 10: 10s explode, as everywhere in roll-and-keep. Start at 10 points, reroll again and add, and keep going on further 10s. A dreamer who chains 10s is diving unusually deep; at that tier stop metering and improvise - a lucid dream-quest, a rare near-clear word, a vision of something no table held. Bounded only by taste.

**Spending.** Points buy options from the scene's menu, in two families: **understand the others' dreams** (the shape of what the group received - the old Coda's job) and **delve deeper into your own dream** (more of what heaven sent *you*). Costs vary; vague or group-level facts are cheap, precise or powerful ones dear - build the menu per scene. As long as the dreamer has **at least 1 point**, they may buy one more option even if it costs more than remains; dipping to zero or below is allowed. Going negative normally costs nothing, but a **dream quest** may set a penalty for ending negative (a nightmare backlash, waking unrested, a lingering ill omen), declared for that scene.

**Void points.** While lucid (i.e. having rolled a 10) a dreamer may spend a void point to enlarge the pool (suggest +3 per void point; tune to taste). A Player Character Point can regain a spent void point per the standard rules.

A default menu to adapt (option - cost):

*Understand the others' dreams*

- How many distinct categories the group's dreams fell into - 2
- How many sleepers fell into a category you name (no dream, noise, your own table, or a specific table) - 2
- Which named sleepers were in a category you name - 1, **unlocked** only once the category counts are known (bought outright, or the last one deduced by elimination); naming every live category but one reveals the rest for free

*Delve deeper into your own dream*

- See another significant dream you might have gotten (a second fragment from your table) - 3
- See a significant dream from a different table - the road not taken - 4

Two properties worth keeping when you build a menu. First, aim for a **1/2/3/4 cost ladder** so a small pool still buys something and a large one buys real depth. Second, options can be **unlocked** by earlier purchases: the cheap 1-point "which sleepers were in a category you name" only opens once the counts are known, and since naming all-but-one live category reveals the rest by elimination, cheap options compound into full knowledge. Tiered menus like this reward planning the spend, which is the point - and the order matters, so a dreamer may take one 1-point reveal and bank the rest.

Whatever is purchased, deliver it **inside the lucid-dream fiction**, never as a stat readout: the dreamer *sees* the other sleepers as lamps lit or dark, *counts* the true dreams as marks struck on a board. The event-not-meaning rule holds even here. The generalized Coda paragraph is the model feeling to wrap the group-shape purchases in (swap the place slot):

> And this you carry up out of the dream like a stone closed in your fist: that of everyone who lay down [where you slept] tonight, the powers sent true dreams to some, sent noise to some, and sent nothing at all to others - the sending is not evenly given - and that yours was true, and meant, and meant for you. You do not know the reckoning behind it. You will look at the others' faces in the morning and not be able to tell which of them dreamed truly, which dreamed only nonsense, and which did not dream. You know only that you did.

**Extra dreams and 10-hunting (rerolls).** A dream die may be rerolled, and a reroll **replaces** the dream - you dream again and keep the new dream. This is how a determined dreamer fishes for a 10. Per the core rules **no single roll may be rerolled more than once, even across different abilities**, so one reroll per dream roll; more whole dreams come from more sleeping opportunities (or a menu option, where offered), each a fresh roll rerollable once in turn. Reroll sources that apply to dream rolls:

- A **Player Character Point** - reroll any roll ([PC Points rules](https://github.com/EliAndrewC/l7r/blob/master/rules/10-player_character_points.md)).
- **Lucky** - re-roll any roll once per adventure.
- **Togashi Ise Zumi, 4th Dan** - dream rolls count as **contested** for this ability, so the Ise Zumi may reroll a dream roll once after seeing it, **but must keep the new roll even if it is worse**. With rerolls to spare, an Ise Zumi can go 10-hunting, at the risk of dreaming down.
- The **Merchant 5th Dan does NOT apply** to dream rolls - that ability cannot reroll dice on all types of rolls.

Because a warning or damning fragment can land on a 10 and the dreamer then spends points to confirm the group's shape, a 10 makes hard truths certain and hands the dreamer the leverage of knowing what others cannot vouch for. That is intended.

## Writing the meaningful fragments (the core craft)

This is the part that matters most and the part that is easy to get wrong.

- **Strange fragments, meaningful yet open. Not dream-quests.** No narrative arc, no puzzle to solve, no guided vision. A single loaded image or a short sequence of them.
- **Describe the events and sensations of the dream. NEVER narrate what it means.** This is the load-bearing rule. Stay inside what happened and what was felt; do not tell the dreamer (or the reader) the theme. Contrast, from an actual revision pass:
  - BAD (narrates the meaning): *"You wake with the sense that you have been shown both the price of the honest road and its dignity, and that they are the same thing."*
  - GOOD (stays in the events): *"You wake not knowing whether that reach was far enough."*
  - Kill every tail of the form "you wake understanding that this means X," "you are being shown Y," "which is a different and better thing," or any narrator theology asserting what the god promises or blesses. A felt *uncertainty about an event* ("you wake still seeing the room") is in-bounds; a stated *theme* is not.
- **Ground each fragment in the specific god's domain and iconography**, and in the scene's factor when it is an object or deed (the relic handled, the blade, the measure, the road, the blood on the hands). Ebisu's fragments lived in carpenters' ink-lines, notched billhooks, honest measures; Bishamon's would live in weapons, walls, the weight of armor, the held line. Do the homework on the god before writing.
- **Valence tracks the split, but the virtuous cell is not automatically reassuring.** A fortune blesses the *straightness* of a choice, not its outcome; the honest path may cost the character everything (see doctrine 3, and the Tasuke precedent in Ebisu's billhook). Do not write the "good" table as a pat on the head.
- **House style:** hyphens only, no em- or en-dashes; two spaces after periods if the destination uses them (l7r.md and OP do); real kanji pass the kanji-romaji-meaning triangle if any surfaces.
- **Keep the meaning in GM-facing notes, never in the fragment.** Each scene's write-up has a "Design notes" / "what each cell is doing" section for the GM. That is where you say what a fragment is for. The fragment itself only ever shows the dream.

## Building a scene, step by step

A scene page opens with two framing sections, in this order: **the question the PCs are contemplating** (the concrete choices in front of them) and **the divine direction** (what the sender actually cares about, is neutral about, and turns cold on). Write the divine direction *before* the tables - it is the spec every fragment must satisfy, not a summary written afterward. Then the scene's own content: what each PC declares (the splits), the shared bands, the meaningful tables, the 10's menu, and the GM-facing design notes.

**A scene page carries only scene-specific content.** The general roll-and-band procedure - roll 1k1, read the band off the scatter, pick or blindly sub-roll a fragment from the band's list, players never see the map or tables, regenerate the scatter each night and never reuse it - is identical for every scene and lives here in the SKILL. Do NOT restate it on each page, and do NOT paste an illustrative band map into a page (the scatter is a per-night runtime artifact, not scene data). A scene's own tuning - its attunement level and band counts (`--none N --unrelated N`), the roll type - belongs in the page frontmatter, not in prose. If a page needs to point at the procedure, one line referencing `SKILL.md` is enough.

**Precision about whose stance, on what (a standing rule).** State the divine direction strictly as *this god's* stance on *this matter* - never a universal claim. The same god may care about entirely different things in a different situation, and a *different* god beseeched over the *same* situation may care about the opposite thing (e.g. Ebisu weighs the *how* of the Shoda matter, while a Fortune of justice or vengeance sought over the same case might weigh the *what* - whether Shoda is punished - and shrug at the how). So write "Ebisu, in this matter, cares about X," not "the god cares about X"; scope every "what this power wants" claim to the specific sender and the specific question, and where it clarifies, note explicitly how another god, or the same god elsewhere, might differ. This applies to the design notes and any prose that characterizes a sender, not just the divine-direction section.

1. Write **the question the PCs are contemplating** - the actual options on the table, grouped **twofold** to match the mentality split (split 1): the two groups are the two poles of that split (e.g. straightforwardness vs deception), with any finer choices listed as sub-bullets under them. Never present a flat list of three-plus co-equal options - the binary is the point, and it is the same binary the meaningful tables run on.
2. Write **the divine direction** - what the sender is nudging toward, neutral about, and against, stated explicitly and **scoped to this god on this matter** (never a universal law; see the precision rule above). Pin this first; it is the design spec.
3. Confirm the **sender(s)** (which fortune or spirit) and thus the coarse partition(s).
4. Get the **scene-specific factor** (split 2) from the GM - it is adventure-tied and only the GM has it.
5. Confirm **split 1** (the mentality axis) for the question at hand.
6. Set the **attunement** and thus the band probabilities (rubric above); decide whether a **misleading** band is in play.
7. Write the **two shared lists** (re-skin the no-dream half-waking option to the real place) and, if used, the misleading list.
8. Write the **four meaningful tables** (one per cell), several fragments each, following the craft rules. Make the cells contrast.
9. Write the **10's lucid-dream menu** for this scene (the two families of options with point costs) and re-skin the Coda flavor wrapper.
10. **Audit every fragment against the divine direction.** Re-read each dream and cut or fix any that guides toward an outcome the sender is neutral on, that fails to carry the stance, or that rewards what the sender discourages. This step is not optional - it is easy to write an evocative fragment that quietly argues for the wrong thing. (For Ebisu: honesty encouraged in both directions, no dream advocates turning Shoda in, freedom shown but shelter never commanded.)
11. Run `randomize_bands.py` with the chosen splits to produce the face-to-band map for THIS scene. Regenerate per fresh scene or per night.
12. Write the **GM-facing design notes** (what each cell does, mismatch outcomes, the theology in play).
13. Save to the correct **pool tier** (below), and publish to Obsidian Portal only if the GM asks.

## The randomizer

`randomize_bands.py` scatters the ten die faces into the scene's bands, pinning the 10 to meaningful, so the face-to-band map is fresh and unguessable each time.

```
python3 .claude/skills/dream/randomize_bands.py --none 2 --unrelated 2      # near-ideal: 6 meaningful (incl. 10)
python3 .claude/skills/dream/randomize_bands.py --none 3 --unrelated 2 --misleading 1
```

It prints a face-to-band table for the GM's eyes only. Never print the map to the players. Pure logic lives in `assign_bands`; run `pytest .claude/skills/dream` for the tests.

When a scene page reproduces an illustrative map, render it as a **two-column table (`face | band`), one row per die face** (1 through 10), matching the script's own output. Do not use a four-column `face | band | face | band` layout - it reads as confusing.

## Pool tiers and saving (spoiler safety)

Dream scenes are **spoilers**. Confirming to players that their reading of a god's will was correct wrecks the interpretation game. So there are two pools, and **you always confirm which tier a scene goes to before saving**:

- **`pool-local/` - GITIGNORED, local only.** Campaign-active or spoiler-sensitive scenes (anything tied to a live plot, an NPC's fate, a god's actual verdict the players are still trying to read). Persisted to the GM's local disk, never committed, safe for the assistant to read for continuity. When in doubt, this tier.
- **`pool/` - git-tracked, PUBLIC.** Theoretical or campaign-agnostic exemplars where spoilers are irrelevant or long dead - reference scenes written to demonstrate the form, and the seed corpus for the future **Dreams section of the l7r-gm-assistant webapp** (alongside relics, names, places).

Rules:

- **Never auto-promote local to public.** Promotion is an explicit GM decision, made after the plot has resolved or with a scene deliberately built to be spoiler-free. Silent promotion would expose players.
- **Obsidian Portal on request only.** OP is player-visible; publish a dream page (public body plus GM-only tables, as with the "Ebisu dreams" page) only when the GM asks, and keep the tables in the GM-only section.
- The live **Ebisu dreams** scene is a spoiler for an ongoing case; it stays out of `pool/` and belongs in `pool-local/` after a conforming pass (its OP page keeps the original fixed 1-2 / 3-4 bands for historical reference; a `pool-local/` copy should be re-cut to the randomized-band standard here).

## Historical grounding and design rationale (why these rules)

Recorded per the project's mandate to capture the reasoning behind a rule, not just the rule:

- **Why noise and silence are built in, not a bug:** Kitsu Okura's six doctrines make heaven a constant transmitter and the mortal a poor receiver. A dream oracle that always returns a clean signal contradicts doctrines 1, 5 (the god will not cheapen itself to speak plainly) and 2 (a thousand fortunes cross-talk). The ~40% no-signal floor even under near-ideal attunement (the Ebisu scene) encodes this. Removing it would be a theology error, not merely an ease-of-play choice.
- **Why the sleeper's circumstances set the odds:** doctrine 6 locates the variable in the receiver ("we so rarely pay our attention to whatever small part of ourselves speaks their will"). Attunement, not divine mood, is the dial - hence the rubric keys off place, rites, mindset, and recent deeds.
- **Why bands are randomized across the faces each scene:** fixed bands ("1-2 is always no dream") let players compute their result the instant they roll, collapsing the interpretation game. Randomizing keeps the reading in the fiction. The 10 is the deliberate exception - a known anchor of certainty is good for the meta-layer the Coda delivers.
- **Why fragments describe events and never meaning:** the whole point is that the group must interpret. A fragment that states its own theme does the players' work for them and destroys the doctrine-3 "struggle to understand" that the gods actually want. This rule was learned by getting it wrong first: an early fragment that ended "you have been shown both the price of the honest road and its dignity, and that they are the same thing" was rejected precisely because it narrated the meaning.
- **Why the two-tier pool:** a saved dream scene is a spoiler for the god's real verdict. Git-tracking or OP-publishing a live scene risks a player reading the answer key. The gitignored tier keeps continuity available to the GM (and the assistant) without exposure; the public tier is only for scenes where spoilers are moot.
