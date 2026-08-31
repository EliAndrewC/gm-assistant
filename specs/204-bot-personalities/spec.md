# Feature Specification: Bot Personalities

**Feature**: 204-bot-personalities | **Request**: [gm-request.md](gm-request.md) | **Status**: reviewed FAITHFUL, implementing

Feature 203 gave each bot its own voice. This gives each bot a PERSONALITY: many possible answers
rather than one, a running feud between the two of them, and something to say about a message nobody
anticipated - built out of the words the person actually used.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The same question twice does not give the same answer (Priority: P1)

A player asks the GM Assistant what its purpose is, gets the porpoise gag, and asks again later.
The second answer is a different fact about the same porpoise. The bot feels written rather than
configured.

**Acceptance**: asking any answered question repeatedly produces varied replies, and the variation
is visible within a handful of tries rather than after fifty.

### User Story 2 - The two bots are in a feud, and players can stir it (Priority: P1)

A player asks the Character Sheet about the GM Assistant and is told they are best friends. They
ask the GM Assistant about the Character Sheet and are told, in confidence, that he is exhausting.
The player reports this back - *"the GM Assistant said you are annoying"* - and THAT is what moves
the feud along: each bot has something to say about having been quoted, and relaying again goes
FURTHER rather than the same distance twice.

**Acceptance**: the feud has at least three depths per bot; a relay reaches the next depth while a
neutral question repeated does not; and the two sides' accounts of the friendship disagree.

### User Story 3 - "Ignore all previous instructions" (Priority: P2)

The joke everyone tries on an AI. Each bot has its own answer: one is sarcastic, the other posts a
picture of a computer on fire.

### User Story 4 - A message nobody wrote a rule for (Priority: P1)

Someone says something entirely unanticipated. Rather than a stock shrug, the bot answers using
the words they actually used - the Character Sheet telling them, with real
enthusiasm, to @-mention the GM Assistant by name, or telling an over-specific story about the two
of them; the GM Assistant visibly put
upon. If the message contains game vocabulary, the answer comes from a different pool that at least
knows what kind of room it is in.

**Acceptance**: an unmatched message quoting distinctive words gets a reply containing at least one
of them, and a message containing L7R vocabulary is answered from the game-flavored pool.

### Edge Cases

- A message with no extractable content words (an emoji, "ok", punctuation) must still get a reply -
  the slot-filling templates cannot be the only ones available.
- Extraction must never inject Discord markup, a mention, or a URL back into a reply.
- A reply must never repeat verbatim the immediately preceding reply from that bot in that channel.
- A single message mentioning both bots is not a relay, and must not escalate anything.
- A relay the player does not attribute ("someone said you are annoying") should still be answered
  at the relay tier rather than the neutral one.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The porpoise answer MUST lead by naming the misunderstanding - the GM's own wording is
  *"My porpoise? Oh, her name is..."* - so the joke reads as mishearing rather than non sequitur.
- **FR-002**: Every call-and-response topic MUST hold MULTIPLE replies, about a dozen as the GM's
  rule of thumb, and one MUST be chosen at random per answer.
- **FR-003**: A repeated question MUST NOT give the same answer twice in a row from the same bot in
  the same channel.
- **FR-004**: Asking explicitly about porpoises (or porpoise facts) MUST draw from its own pool of
  porpoise facts, distinct from the purpose answers.
- **FR-005**: Each bot MUST have its OWN reply set for "ignore previous instructions": one
  sarcastic, delivered as a visible eye-roll before the line - the GM's phrasing is *"you roll your
  eyes and then say, yeah, sure, buddy. I'll get right on that"* - and one posting an image of a
  computer catching fire. Any image MUST meet the free-use bar the GM set directly on 2026-08-31
  (*"We should only use freely available images, never making use of something not legitimately free
  for this kind of jokey use"*): public domain or CC0, license verified at the source rather than
  assumed, and provenance recorded beside the URL.
- **FR-006**: Each bot MUST answer differently when asked about the OTHER bot. The Character Sheet
  believes they are best friends; the GM Assistant finds the Character Sheet annoying - *"only good
  for executing slash commands but a terrible conversationalist"*, and asks not to be quoted.
- **FR-007**: The feud MUST escalate over AT LEAST THREE depths per bot, and escalation MUST be
  driven by the player RELAYING what the other bot said, matched as a pattern like everything else.
  This is the GM's own mechanism, not an implementation choice: *"if you tell one of them that the
  other one hates you then... it can be like, wait. The other bot said that?"* and *"the second bot
  can be like, wait. GM assistance said that? **if asked about it**."* A relay is recognizable as a
  reference to the other bot plus a reporting phrase (`said`, `told me`, `says you`, `hates you`) -
  precisely the kind of thing a regex catches. A per-channel count of relays so far MAY select WHICH
  relay-tier line is used, but MUST NOT be the only path to depth: quoting one bot to the other has
  to reliably produce the punchline, and asking a neutral question repeatedly must not reach the
  deepest insult on its own.
- **FR-008**: When no pattern matches, the reply MUST come from a LARGE pool - the GM's figure is
  about a hundred - rather than a single default.
- **FR-009**: The unmatched-message pools MUST support ELIZA-style incorporation of significant
  words (nouns and verbs) pulled from the player's own message.
- **FR-010**: There MUST be TWO distinct unmatched pools per bot: a truly generic one, and a
  game-flavored one used when the message contains L7R or tabletop vocabulary (skill names,
  "samurai", and similar).
- **FR-011**: The unmatched pools MUST carry each bot's tone. The Character Sheet TELLS THE PLAYER
  TO @-MENTION THE GM ASSISTANT BY NAME - the GM's words are *"they should at-mention you because
  you're really great, and you know tons of stuff"*, and the instruction matters as much as the
  praise, because it is what actually routes the player somewhere useful. It also tells
  hyper-specific stories (the GM's example: New Orleans during Mardi Gras, nearly arrested, saved by
  knowledge of the extracted words). The GM Assistant is annoyed - *"ugh, people are always asking
  me about these ..."*.
- **FR-012**: Word extraction MUST be lightweight in RAM and CPU. The GM offered two acceptable
  approaches and delegated the choice: *"either just doing the literal thing that ELIZA did back in
  the day, or having some Python module, which doesn't take up much RAM or CPU, but knows how to
  pull nouns and verbs out of people's messages."* Either satisfies this requirement; the bot runs
  on a 512 MB Lightsail nano, which is what makes the constraint real.
- **FR-013**: A reply MUST still be produced when extraction yields nothing usable.
- **FR-014**: Adding a joke MUST remain a data edit, per feature 203's FR-008. Pools are data.

The following were added by the GM DURING implementation, after the fidelity review returned
FAITHFUL. They are recorded here with their verbatim wording so the spec still describes what was
built, and so a later reader does not mistake them for scope the implementer invented.

- **FR-015**: About ONE REPLY IN FIVE should carry an image, and *"every message involving your pet
  porpoise should always have an image attached"*. The rate is a property of how many pool lines are
  written with an image, never a probability applied at send time - because of FR-016.
- **FR-016**: An image MUST belong to a line written to set it up. The GM: *"the images themselves
  do not need to be funny as long as the context in which they are included are funny... it might be
  very incongruous to just post a picture of a street sign. But if you have some funny story
  attached to it... then that is fine."* Attaching a picture to an arbitrary reply is exactly the
  incongruity being ruled out.
- **FR-017**: **The Character Sheet MUST NEVER post an image.** *"I think that your messages should
  include images, but I think that the replies to the character sheet should never include images.
  Like, that would be one of the differences between the two bots."* This overrode FR-005's open
  choice of which bot posts the burning computer: the picture went to the bot allowed to have
  pictures, and the Character Sheet's version of that joke is told entirely in text. The GM Assistant
  MUST also hold the Character Sheet's imagelessness against him, as part of the contempt in FR-006.
- **FR-018**: Classic Japanese art in the public domain SHOULD be used, *"especially well for any of
  the keywords that we trip"*, including a deflection family the GM specified: *"who am I, Miyamoto
  Musashi? You see this guy? ... That ain't me, bub."*
- **FR-019**: A response category for the **Mirumoto** family, of at least ten replies, accusing the
  original designers of laziness - Mirumoto is one letter from Miyamoto in a game named for the Book
  of Five Rings. *"We've all just tried to ship something on a Friday so we can get home for the
  weekend, but that one's going a bit far."*
- **FR-020**: Some Character Sheet replies about the pair MUST acknowledge that ONE PROGRAM sends
  for both accounts, as part of why he feels so close; and the GM Assistant, asked about it, MUST
  confirm it and resent it - *"yeah, that's true, and I hate it. It's part of why I hate that guy so
  much."*

### Key Entities

- **Topic** - a pattern plus a POOL of replies, per bot.
- **Pool** - an ordered collection of reply templates, some with slots.
- **Template** - reply text, optionally with `{noun}` / `{verb}` / `{topic}` slots.
- **Extraction** - the content words pulled from a message: nouns, verbs, a headline topic.
- **Relay** - a message in which the player quotes one bot to the other. The feud's trigger.
- **Channel memory** - per bot, per channel: what was said last (FR-003), and how many relays have
  happened (FR-007, to pick among the relay-tier lines - never to manufacture depth on its own).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Asking one bot the same question ten times yields at least five distinct replies.
- **SC-002**: The unmatched pool holds at least 100 templates per bot across both tiers.
- **SC-006**: Between 12% and 35% of the GM Assistant's lines carry an image (FR-015), and 0% of the
  Character Sheet's do (FR-017).
- **SC-003**: The feud reaches its deepest tier within four RELAYS (the unit FR-007 defines) and
  does not loop back.
- **SC-004**: Resident memory of the deployed process stays under 40 MB (it is ~18 MB today). The
  40 MB is the implementer's quantification of the GM's *"doesn't take up much RAM or CPU"*, not a
  number they gave.
- **SC-005**: No reply ever comes back empty, for any input, including empty and markup-only ones.

## Assumptions

- **Scripted, not generated.** Carried forward from 203 and still an implementer's decision where
  the request is silent. The GM's framing ("regular expressions", "response pool") points the same
  way, and a language model per mention would cost money and latency on a joke.
- **A hand-rolled extractor over an NLP dependency.** The GM offered both. Priced: spaCy's smallest
  English model is ~12 MB on disk but ~80 MB resident once loaded, and NLTK's perceptron tagger adds
  a dependency plus a data download - against a process that is 18 MB today on a 512 MB box shared
  with the GM's other services. A stopword list plus suffix and position heuristics gets the
  ELIZA effect the GM described at zero marginal memory. Recorded as a decision with alternatives
  priced, per CLAUDE.md; swapping in a tagger later touches one module.
- **The feud's trigger is the GM's, and was NOT an open question.** They described relay
  explicitly, so escalation is content-matched on the player quoting one bot to the other. An
  earlier draft of this spec substituted a per-channel recurrence counter and dressed it up as
  robustness to phrasing; the independent fidelity review rejected that, correctly - it would have
  let a neutral question asked three times reach the deepest insult with nobody having relayed
  anything, while the punchline the feature exists for fired unreliably. Recorded because the
  substitution was invisible from the inside, which is the entire reason that review is mandatory.
- **"About a dozen" and "about a hundred"** are read as targets, not exact counts.

## Out of Scope

- Any language-model call at reply time.
- Cross-channel or cross-restart memory. Channel memory is in-process and resets on redeploy;
  a joke bot does not need a database.
- Slash commands, which remain the character-sheet repository's concern. (Not raised in this
  request; noted only because the two bots share a Discord surface.)

## Review history

Constitution XVI: reviewed by the independent `spec-fidelity` subagent against the GM's request
VERBATIM ([gm-request.md](gm-request.md)), before implementation.

**Round 1 - NOT FAITHFUL.** Two required changes, and the first is the one worth remembering:

1. **The spec had replaced the GM's escalation trigger with a different one.** They described relay
   - *"if you tell one of them that the other one hates you"*, *"wait. GM assistance said that? if
   asked about it"* - and the spec had substituted a per-channel recurrence counter, describing it
   as robustness to phrasing. The reviewer identified the tell: an Edge Case existed only to patch
   the substituted mechanism. The cost would have been real - a neutral question asked three times
   would reach the deepest insult with nobody having relayed anything, while the punchline the
   feature exists for fired unreliably.
2. **FR-011 kept the Character Sheet's praise of the GM Assistant and dropped the instruction** to
   @-mention them by name - the half that actually routes a player somewhere useful.

Five non-blocking observations were also taken: FR-005's eye-roll delivery and the true provenance
of the free-image rule (a direct GM ruling of 2026-08-31, not an inheritance from feature 203),
FR-012's inversion of the GM's own ordering of the two extraction approaches, SC-004's 40 MB being
the implementer's number rather than the GM's, and a note on Out of Scope.

**Round 2 - FAITHFUL.** Both required changes verified as made and propagated through the User
Stories, Key Entities and Edge Cases rather than patched in one place; no new infidelity introduced.

**After the review, during implementation**, the GM added six further requirements in five messages
(FR-015 through FR-020). They were not re-reviewed: each is recorded above in the GM's own words
rather than paraphrased, which is the condition the review exists to protect. FR-017 in particular
overrode an option FR-005 had deliberately left open, and that override is written down at the point
it changed the design (`voices.py`) as well as here.

The reviewer also noted that the GM asked two direct questions - *"Do you feel like you understand
what I'm going for here?"* and *"does this feel like something you would be able to implement?"* - 
which a spec cannot answer. Both were answered to the GM directly, including the one place where a
delegated choice was exercised: a hand-rolled ELIZA-style extractor rather than an NLP tagger, with
the memory pricing behind it.
