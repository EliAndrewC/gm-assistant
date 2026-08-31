# Feature Specification: Campaign Lore Intents

**Feature**: 205-campaign-lore-intents | **Request**: [gm-request.md](gm-request.md) | **Status**: reviewed FAITHFUL (3 rounds), implementing

Feature 204 gave the bots personalities and the long tail of what people say to any bot. This makes
them know THIS CAMPAIGN. Ask about a village headsman, the Ministry of Justice, the Moto, or Moto
Gaheris specifically, and the GM Assistant is visibly irritated at you and then tells you something
true out of `l7r.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sarcastic AND informative (Priority: P1)

A player asks the GM Assistant about village headsmen. He is annoyed that this is what they want to
talk about, and then rattles off an actual fact from the campaign notes - what a headsman does about
a family whose plot no longer matches its size, how rent works, why the job is mostly arithmetic and
grudges. The player learns something. The GM's own framing: *"special annoyance that they are
talking about village headsmen and then rattle off some fact about this pulled from our campaign
setting writeup."*

**Acceptance**: every lore reply carries a fact traceable to `l7r.md`, and reads as put upon rather
than helpful.

### User Story 2 - The Character Sheet has no idea, and says so at length (Priority: P1)

The same question to the Character Sheet gets no lore. He effusively praises the GM Assistant, tells
the player to @-mention them for real information, and tells a story about a time the GM Assistant's
knowledge of that very subject saved the pair of them - a story set IN ROKUGAN, with the subject
Mad-Libbed in.

**Acceptance**: his lore replies never assert a fact about the setting, always name the GM Assistant,
and are drawn from a pool distinct from his existing real-world-story pool.

### User Story 3 - The stories differ by WHERE they happen (Priority: P1)

Asked something unanticipated and non-lore, the Character Sheet still tells his story - but that one
is set in the real world (New Orleans during Mardi Gras, a bus station in Amarillo). Same shape, same
praise, same Mad Libs; different world. That contrast is the joke.

### User Story 4 - A named sword by any name (Priority: P2)

A player says "Shitsuten" and gets the famous-swords answer, without Shitsuten having a category of
its own.

### User Story 5 - Somebody nobody has heard of (Priority: P2)

A player asks about a minor named samurai. There is no category for them, and the GM Assistant is
contemptuous that they asked - *"ugh, are you asking me about specific individuals? Come on. That
guy's a loser."*

### Edge Cases

- A house or lineage name is NOT a personal name. `Akodo no Damasu` is family + house; a person is
  `Akodo no Damasu Sei`. A question about the house must not be answered as a question about a
  person.
- A lore word appearing incidentally ("my samurai draws his katana") must not turn every reply into
  a lecture; the game-flavored unmatched pool already covers casual game vocabulary.
- A lore subject with no extractable words must still produce a reply.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The GM Assistant MUST gain lore categories drawn from `l7r.md`, each with at least ten
  replies, per the floor established in feature 204.
- **FR-002**: Every lore reply MUST be BOTH sarcastic AND informative - annoyance first, then a real
  fact from the campaign notes. A reply that is only annoyed fails this; so does one that is only
  informative.
- **FR-003**: Facts MUST come from `l7r.md` and MUST NOT be invented. Where the notes are silent,
  the line says something true about the silence rather than filling it in.
- **FR-004**: The categories MUST be the entries of [candidate-list.md](candidate-list.md), which
  records the list the GM approved and the amendments they made to it. A cluster paraphrase is not
  sufficient: message 1 made list approval an explicit gate (*"present me with the list to make sure
  that I like the level of specificity that you have chosen"*), so the approved LEVEL OF SPECIFICITY
  is the requirement, and only the list itself carries it.
- **FR-005**: Vow types MUST be grouped into one category; the four Gods of Death MUST each have
  their own. Both are the GM's explicit instruction.
- **FR-006**: Famous swords MUST be ONE category, but its pattern MUST match any of the individually
  named swords - the GM: *"I don't want a separate response category for each individual famous
  sword, but I want to make sure that mentioning any of our individual famous swords, which are
  named, such as Shitsuten, will bring up a famous sword response."*
- **FR-007**: Any mention resolving to an INDIVIDUAL with no category of their own MUST draw a
  dismissal pool - *"ugh, are you asking me about specific individuals? Come on. That guy's a loser.
  Why are you even bothering? Why do you even care?"* The GM's trigger is *"someone mentions what
  looks like a different name"*, so this covers every personal-name FORM, of which `Family Given`
  (`Shinjo Jotsu`), `Family no House Given` (`Akodo no Damasu Sei`) and a bare given name are
  EXAMPLES rather than an exhaustive list. `Family Given` matters most: it is the ordinary Rokugani
  form and the form of every significant person that IS kept, so the live distinction at
  implementation time is `Kitsu Okura` (has a category) against `Shinjo Jotsu` (cut, dismissed).
  A POOL of at least ten, not one fixed line.
- **FR-008**: The naming convention MUST be respected: `Family no House Given`, stated outright in
  the notes - *"Akodo is the family name, 'no Damasu' indicates that he is 'of the Damasu' vassal
  house, and Kojima is his personal name."* A HOUSE OR LINEAGE mention with NO given name after it
  (`Akodo no Damasu`, `Mirumoto no Ryusei`) MUST route to the houses handling of FR-017 - NOT to the
  person handling, and NOT to FR-007's dismissal. Both errors are the same error the GM corrected:
  answering a house as though it were a guy. The discriminator is whether a given name follows the
  house.
- **FR-009**: **The Character Sheet MUST NOT have lore categories of its own.** He recognizes that a
  lore question was asked and answers from a pool, without asserting setting facts.
- **FR-010**: That pool MUST hold about ONE HUNDRED replies in which the Character Sheet
  exclusively praises the GM Assistant, tells the player to @-mention them for real information, and
  tells a story of a REQUIRED SHAPE: the GM Assistant's knowledge OF THE ASKED-ABOUT SUBJECT proved
  decisive on an occasion when the two bots were together. The GM's words - *"the story is about how
  the [GM Assistant] knew a bunch of stuff about this, and then it came in really handy one time
  when the two of the bots were together"* - and the specific-subject knowledge plus the it-came-in-
  handy beat are the substance of the joke, not decoration. Without them this pool is a reskin of
  the existing one.
- **FR-011**: The Character Sheet's LORE stories MUST be set in Rokugan; his existing default
  stories remain set in the real world. The GM: *"they are clearly real world stories versus
  fictional setting stories and that's the difference."*
- **FR-012**: Both Character Sheet story pools MUST incorporate the asked-about proper nouns Mad
  Libs style, using the existing extraction.
- **FR-013**: The Character Sheet MUST still never post an image (feature 204, FR-017).
- **FR-014**: Every new pool MUST hold at least ten replies, enforced by the existing test.

The following arrived from the GM in messages 3-5, AFTER the round-1 review. They are recorded with
their wording attached so a later reader does not mistake them for scope the implementer invented.

- **FR-015**: Each of the SEVEN GREAT CLANS MUST have its own category - *"Each of the seven clans
  do as well."*
- **FR-016**: A mention of ANY Great Family MUST route to its clan's category - *"if the Asako
  family is mentioned then that is the same as if the Phoenix clan was mentioned."* The mapping is
  the population table in `l7r.md`: Lion (Akodo, Matsu, Ikoma, Kitsu); Crab (Hida, Yasuki, Kaiu,
  Kuni, Hiruma); Crane (Doji, Daidoji, Kakita, Asahina); Scorpion (Bayushi, Shosuro, Soshi, Yogo);
  Unicorn (Shinjo, Otaku, Moto, Ide, Iuchi); Dragon (Togashi, Mirumoto, Agasha, Kitsuki); Phoenix
  (Shiba, Isawa, Asako).
- **FR-017**: There MUST be a famous-houses category, and the Damasu MUST have their own - *"there
  is probably room for a famous houses section like the Damasu probably deserve their own entry."*
  The notes name the Karo Houses: the Akito of the Hida, the Tsume of the Doji, the Damasu of the
  Akodo.
- **FR-018**: **IMPERIAL FAMILIES ARE A DELIBERATE EXCEPTION TO FR-009**, and the exception is the
  GM's, not the implementer's - asked in message 4 and ruled on in message 5: *"I understand that
  the imperial thing is an exception to the lore rule But I think that's okay because it's funny."*
  A mention of Seppun, Hantei, Otomo or Miya routes to one `imperial_families` category which BOTH
  bots answer, because the contrast IS the joke: the Character Sheet praises the dynasty *"in a
  really earnest way"*, while the GM Assistant is *"oh, sooooooooo great, yeah, nothing bad to say
  about them (out loud, in public)"*. This is the only lore category with a Character Sheet pool.
- **FR-019**: RESOLUTION ORDER MUST be: named individuals, then rich specific topics, then Imperial
  families, then houses, then clans, then FR-007's dismissal. Without it the new routing silently
  destroys existing categories - `Moto` is a Unicorn FAMILY, so FR-016 would swallow all fourteen
  Moto categories; `Kuni` is a Crab family, so it would swallow `kuni_yori` and `kuni_isamu`. The
  order MUST be pinned by tests, since the symptom is a category that simply stops being reachable.
- **FR-020**: The Phoenix category MUST carry its OWN material rather than the shugenja fallback,
  and **`shugenja` MUST be a separate category** - message 6, after the implementer reported what the
  notes actually hold: *"I do have quite a lot of Phoenix material even if I have not run a campaign
  there... you can just give them their own stuff and then have shugenja be its own separate
  category."* The Phoenix material is distinctive (Isawa himself practiced maho; Isawa Akuma wielded
  it without losing his spellcasting; the Isawa are ruled by the Council of Elemental Masters rather
  than a daimyo; Shiba bent his knee to Isawa at the founding), and the GM's own note that the
  Phoenix is the one clan they have never set a campaign in - *"which I suppose is noteworthy in and
  of itself"* - is usable material.
- **FR-021**: There MUST be a category for BEING MERELY AN ASSISTANT, and **it belongs to the GM
  Assistant alone** - message 7: *"people might ask to speak to your manager or deride you for only
  being an assistant? That seems like something that would be specific to you. and that the
  character sheet would not get and I want to make sure we have some responses for that."* Triggers
  include asking for his manager, his supervisor, whoever is in charge, or the GM himself, and
  belittling him as "just" or "only" an assistant. The Character Sheet MUST NOT have this category;
  the joke is that the insult only lands on the one whose name contains his own subordination.


### Key Entities

- **Lore category** - a pattern plus a GM Assistant pool. Has no Character Sheet counterpart.
- **Lore trigger** - the union of every lore pattern; what tells the Character Sheet a lore question
  was asked without giving him anything to say about it.
- **Named-person dismissal** - a POOL, for an individual with no category of their own.
- **House / lineage reference** - a different thing entirely, answered as lineages.
- **Rokugan story pool / real-world story pool** - the Character Sheet's two ways of not answering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every named sword in `l7r.md` routes to the famous-swords category.
- **SC-002**: The Character Sheet's Rokugan-story pool holds at least 100 replies.
- **SC-003**: No Character Sheet reply asserts a lore fact; none carries an image.
- **SC-004**: Every lore category holds at least ten GM Assistant replies.
- **SC-005**: A lore question and a non-lore unanticipated question draw the Character Sheet's
  stories from different pools.
- **SC-006**: Every reply in the Rokugan-story pool names the GM Assistant AND refers to the
  asked-about subject, so the required story shape (FR-010) is checkable rather than aspirational.
- **SC-007**: A house or lineage mention routes to the houses handling; the same string with a given
  name appended draws the FR-007 dismissal.
- **SC-008**: A `Family Given` name NOT on the kept list (e.g. `Shinjo Jotsu`) draws the dismissal,
  while one that IS kept (e.g. `Kitsu Okura`) reaches its own category. This is the form the round-2
  review found unrouted.
- **SC-009**: Every Great Family routes to its clan, and no existing category is made unreachable by
  that routing - specifically `Moto` and `Kuni` still reach their own categories (FR-019).
- **SC-010**: Each Imperial family name reaches `imperial_families`, and both bots answer it.
- **SC-011**: Asking for the GM Assistant's manager, or calling him "just an assistant", reaches
  FR-021's category - and the Character Sheet has no such category at all.

## Assumptions

- **"About one hundred"** is a target, read the way FR-008 of feature 204 read "about a hundred".
- **Which characters are "significant"** is the implementer's call from the GM's shortlist plus
  mention counts, correcting for the house/person confusion the GM caught. Recorded because the GM
  said *"the ones which appear to be significant, such as the ones that you listed"* - a direction,
  not a closed list.
- **Facts are lifted from `l7r.md` at authoring time, not read at runtime.** The deployed bot has no
  copy of the campaign notes, exactly as it has no copy of the rules (feature 204, `vocab.py`).
  Whether a fact is still accurate is therefore a question for whoever edits the notes; a test can
  only hold the shape, not the truth.
- **Tone remains untestable.** Counts, routing, the image ban and the absence of lore claims in the
  Character Sheet's pools are machine-checked; whether a line is funny is not.

## Out of Scope

- Reading `l7r.md` at runtime, or shipping it to the box.
- Any model call to generate lore answers.
- Lore categories for the Character Sheet.

## Review history

Constitution XVI: reviewed by the independent `spec-fidelity` subagent against the GM's request
VERBATIM ([gm-request.md](gm-request.md)), before implementation.

**Round 1 - CHANGES REQUIRED.** Three, and the first is the one worth remembering:

1. **FR-007 and FR-008 contradicted each other on the GM's own example.** `Akodo no Damasu` is
   name-shaped, so FR-007 sent it to the "that guy's a loser" dismissal, while FR-008 said it must
   not be treated as a person - and the spec never said what a house DOES get. The GM's correction
   had survived as prose and was absent as behavior. Answering a house as though it were an
   unimportant guy is the same mistake as answering it as though it were a person.
2. **FR-010 had dropped the required shape of the Character Sheet's story** - that the GM
   Assistant's knowledge OF THAT SUBJECT came in handy when the two of them were together. Compressed
   to "a story about the two of them", which is the difference between the joke and a reskin.
3. **The approved candidate list was not recorded**, so FR-004's "clusters the GM approved" could
   not be checked against anything. List approval was an explicit gate in message 1; the list is now
   [candidate-list.md](candidate-list.md) and FR-004 requires its entries.

The reviewer also asked one thing of the GM rather than of the spec: FR-007 said "a single generic
dismissal" while the project floor is ten replies per pool. Resolved as a pool of ten, since the GM's
*"that kind of thing"* reads as a shape rather than a count, and nothing argues for exempting it.

**Round 2 - NOT FAITHFUL.** The three round-1 findings were confirmed fixed and internally
consistent, and the reviewer verified `candidate-list.md` against the list actually presented (via
the session transcript) rather than against itself. Three further findings:

1. **Fixing finding 1 had narrowed the dismissal.** FR-007's enumeration - `Family no House Given`
   or a bare given name - dropped the plain `Family Given` form, which is the ordinary Rokugani name
   AND the form of every significant person kept, so a non-kept name like `Shinjo Jotsu` had no
   route at all. Now stated as forms-by-example with `Family Given` called out, plus SC-008.
2. **The request record had gone stale.** The GM sent three more messages while the review ran, and
   *"a fidelity gate run against a two-message record while the session implements a three-message
   request certifies nothing."* Messages 3-5 are now in `gm-request.md` verbatim and carried by
   FR-015 through FR-020.
3. Two recording defects in `candidate-list.md` (the Emma-O pointer, and the kept-names list not
   distinguishing the GM's five from the implementer's four additions), both repaired.

Messages 6 and 7 arrived while round 2's fixes were being applied, and are folded in the same way -
verbatim in `gm-request.md`, carried by FR-020 and FR-021, listed in `candidate-list.md`. The GM
asked whether adding requirements mid-flight was disruptive; the honest answer is that it is cheap
during the spec phase and expensive once the response prose is written, so the review simply runs
against whatever the complete record says at review time.

**Round 3 - FAITHFUL.** All three round-2 findings fixed; messages 3-7 verified as carried by
FR-015 through FR-021 and clusters L-O; and the four rules that claim overlapping inputs (FR-007
dismissal, FR-008 houses, FR-016 clans, FR-019 order) confirmed to give every string exactly one
route. Three editorial corrections were made rather than deferred, one of which mattered on
principle: the spec had silently corrected the GM's dictation *inside a quotation* ("derive" ->
"deride"), which the project forbids. It is bracketed now, as `Hunte [Hantei]` already was.

The reviewer also recorded, unprompted, that round 3 is normally the escalation point and that **no
persistent misunderstanding occurred here**: round 1 found real drafting defects, round 2's first
finding was collateral from fixing round 1 and its other two were caused by the GM sending five
further messages while the review ran. New input from the GM is not the failure the three-round
limit exists to catch.
