# Feature 218: `/look-up`, a private Discord lookup for the Wasp campaign

**Request**: [gm-request.md](gm-request.md) (2026-10-17, three messages). **Status**: approved for
implementation.

**Fidelity review** (constitution XVI, `spec-fidelity` subagent, Mode 2): round 1 CHANGES (SC-003
working target, no per-person rate limit, full-name instruction); round 2 CHANGES (GM-only roster
exclusion justified by the dead link only; FR-005 aligned); round 3 **FAITHFUL** (2026-10-17).

## Why

Players forget the campaign's vocabulary. The motivating case: a player talking about Hideki could
remember neither "gosonin" nor "escort". A glossary search does not help, because a player who has
forgotten the term cannot type it. What they can type is a vague, sometimes inaccurate question
("what are our minions called?"), and turning that into the answer they meant is a job for an
LLM.

The GM's earlier blind trial showed that backstory synthesis needs an expensive model and all the
setting notes, at about 40 cents per call. A lookup is a different task: it finds a fact and
repeats it. The bet is that a cheap Gemini model, handed a compact glossary instead of the notes,
answers lookups well for a small fraction of that cost. The bet gets measured, not assumed.

## User Scenarios & Testing

### Story 1 - a vague question gets the answer the player meant, privately (P1)

In a Wasp campaign channel, a player types `/look-up what are our minions called?`. Only that
player sees the reply, which appears within seconds and reads something like:

    The PCs are Marshals (haribugyo, literally "magistrates of the sting").
    Under you are Inspectors (metsuke, literally "one who directs their eye").
    Their staff are Escorts (gosonin, literally "transport guard").

**Acceptance**:
1. The reply is visible only to the person who asked. Nothing is posted that other channel
   members can see.
2. The reply is brief: at most about five short lines, never a multi-paragraph write-up.
3. The reply answers the question the player meant (here, the terms for the ranks) even though the
   player did not use any of those terms.
4. Asking a question in a channel the bot can read but outside the Wasp campaign still answers,
   with the Wasp campaign as context. (The GM: "we are in the Wasp Clan campaign specifically.")

### Story 2 - the answer knows the campaign and who is asking (P1)

`/look-up who is our boss?` from any Wasp PC's player answers **Tsuruchi Kyoma**, because "our"
means the Wasp marshals. The model is told which character the asker plays: name, school, Dan,
lineage, gaming group, and **clan of origin inferred from the school** (a Lion school means they
came from the Lion before joining the Wasp; a Mantis school, the Mantis; and so on). So
`/look-up what clan was I from?` or `/look-up who are the fortunes my old clan worships?` can be
answered.

**Acceptance**:
1. The asker is matched to their character by their Discord account, using the character-sheet
   app's ownership record.
2. Only PCs in the Wasp campaign's gaming groups count; NPCs and characters outside those groups
   are ignored.
3. If a player owns more than one Wasp PC, the model is told about each of them rather than
   guessing one.
4. If the asker owns no Wasp PC (for example, the GM), the question is still answered, without
   a character profile.
5. Clan of origin is derived from the school's clan, not typed by hand per character.

### Story 3 - people mentioned are linked, mechanically (P1)

Every person named in a reply who has a character record on the campaign's Obsidian Portal (or a
character sheet, for PCs without one) becomes a clickable link to that record. This happens in a
post-processing step over the model's text, not by asking the model to produce links, as the GM
proposed.

**Acceptance**:
1. A reply naming Tsuruchi Kyoma links his name to his Obsidian Portal character page.
2. Every name in the roster is linked wherever the reply mentions it, by full name, and by given
   name alone when that given name belongs to only one person in the roster (Story 2 makes "Kyoma"
   alone a likely way to answer).
3. Link previews (embeds) are suppressed so the reply stays short.
4. The model is instructed to name each person by their full name at least once, so the
   mechanical linker can match them.
5. A person with no record anywhere stays plain text. There is nothing to link to, so this is not
   an exception to the rule.
6. Records marked GM-only on Obsidian Portal are not in the roster: a player cannot open them, so
   a link would lead nowhere. (What the model may SAY is governed by the glossary's sources,
   Story 6.3, not by the roster.)

### Story 4 - topic questions link to the right wiki page (P1)

`/look-up what are the imperial bounties?` gives a one- or two-line answer and links the Imperial
Bounties wiki page, without listing every bounty. `/look-up what is the wasp org chart?` links the
Wasp Hierarchy page. The question's wording is too varied for a mechanical match, so the **model**
chooses these links from the glossary, as the GM said.

**Acceptance**:
1. Each glossary entry that has a matching public wiki page carries that page's address.
2. The model is instructed to include a page's link when the question is about that topic, and
   never to invent an address. Any link in the reply that is not an address taken from the glossary
   or the roster is removed before posting.

### Story 5 - "do what I mean" on mis-worded questions (P1)

`/look-up who are the fortunes that the crab worship?` answers with the Crab Clan's **two patron
Fortunes**, not "all of them", because that is what the question means in context. The GM's
framing: "a do what I mean and tell me what I'm looking for even if I have not properly expressed
it kind of deal."

**Acceptance**: the question set (Story 7) includes mis-worded and imprecise questions like this
one, each graded against what the asker meant.

### Story 6 - the glossary: world facts in, numbers and procedures out (P1)

Claude builds the glossary in a Claude Code session, not with an expensive Gemini call (the GM:
"I should just have you build the glossary. And then Gemini is handed the glossary."). Sources:
all of `l7r.md`, the rules in the `l7r` repository, and the public parts of the campaign's
Obsidian Portal wiki pages and character records.

**In**: everything a player might need to name or recognize. That covers institutions (the
Ministry of Retainers), offices and ranks (county magistrate, metsuke, gosonin, haribugyo), clans,
families and their patron Fortunes, named NPCs and places, setting vocabulary, festivals, and rule
terms (feint, TN, kept dice).

**Out**: hyper-specific numbers and procedures, even when the term they belong to is in. For
example, a county magistrate's budget is out although "county magistrate" is in.

**Acceptance**:
1. Each entry gives the term, its reading and literal meaning where it has one, a plain-English
   description of what it is, related terms, and a link when a public page covers it.
2. Each entry is tagged with its scope (the world in general, the Wasp campaign, or another named
   campaign), so material from the other campaigns in `l7r.md` is available but never mistaken
   for Wasp-campaign fact.
3. Obsidian Portal's GM-only fields (`game_master_info`) and GM-only pages and character records
   are never a source.
4. The glossary records which version of each source section it was built from, and a command
   reports the sections that have changed since, so a refresh rereads only those.
5. The glossary is checked into the repository as data; the deployed bot needs no access to the
   `l7r` repository or Obsidian Portal at question time.

### Story 7 - the efficacy experiment (P1)

A fixed question set measures any configuration, so model choices are made on numbers.

**Acceptance**:
1. At least 60 questions, including the GM's five verbatim examples, covering:
   - terminology asked from the English side
   - people, places, ranks and institutions
   - questions that depend on the asker's character
   - mis-worded or imprecise questions
   - rule terms
   - questions the glossary cannot answer
2. Each question carries the facts a correct answer must contain, the links it must carry (if
   any), and, for unanswerable ones, the expectation that the reply says it does not know rather
   than inventing an answer.
3. One command runs the set against a named Gemini model and reports, per question and overall:
   - correctness (required facts present)
   - required links present
   - invention on the unanswerable questions
   - brevity
   - cost per question, from the API's reported token counts
   - latency
4. The set is run against at least three Gemini model tiers, the cheapest included and a
   Pro-tier model as the quality ceiling. The results are recorded in this feature's directory.
5. The bot's default model is the cheapest tier whose correctness is within 5 points of the best
   tier measured, with no invented answers on the unanswerable questions beyond what the best tier
   produces. The choice and its numbers are recorded.
6. The run is repeatable, so it serves as a regression test whenever the glossary or the model
   changes.

### Story 8 - it stays cheap and well-behaved (P2)

**Acceptance**:
1. Each question is logged locally (asker, question, reply, model, tokens, cost), so the GM can see
   what players struggle with and the log can feed new questions into the set. The log is
   gitignored. *(A safeguard the session added; raised with the GM.)*
2. A daily spending ceiling (configurable) protects the GM's Gemini bill. Hitting it gets a polite
   private reply, not silence. *(A safeguard the session added; raised with the GM.)* There is
   deliberately no per-person rate limit: with a ceiling in place it adds no cost protection, and
   refusing a player works against the point that nobody should feel they are bothering anyone.
3. If Gemini fails or times out, the asker gets a short private apology instead of a hanging
   "thinking..." message.

## Edge cases

- **Empty or one-word question**: answered as a lookup of that word.
- **A question about secrets the notes do not record** ("what is Hideki hiding?"): the reply says
  the notes do not cover it; it never guesses.
- **A name shared by two people**: the full-name instruction (Story 3.4) normally avoids the
  problem. What is left over, a bare given name that two people in the roster share, stays
  unlinked rather than linking the wrong person.
- **Text that looks like a link but is not from the glossary or roster**: removed.
- **The character-sheet app is unreachable**: answer without a profile, from the last cached
  roster if one exists.
- **Discord's 3-second acknowledgement limit**: the bot acknowledges immediately with a private
  "thinking..." and replaces it with the answer.
- **The reply would exceed Discord's message limit**: trimmed at a line boundary (it should never
  get close given the brevity rule).

## Requirements

- **FR-001** A `/look-up` slash command, taking one free-text question, available in the GM's
  Discord server.
- **FR-002** Replies are visible only to the asker (Discord's "only you can see this").
- **FR-003** Answers come from a cheap Gemini model given the glossary, the Wasp campaign context,
  and the asker's character profile. The model is configurable without a code change.
- **FR-004** The asker's profile is derived from the character-sheet app by Discord account,
  limited to non-NPC characters in the Wasp campaign's gaming groups, with clan of origin
  derived from the school's clan.
- **FR-005** Every person named in a reply who has a player-visible Obsidian Portal record (not
  marked GM-only) or a character sheet is linked, by a mechanical post-processing step. *(GM-only
  records excluded because players cannot open them; raised with the GM.)*
- **FR-006** The model links the relevant public wiki page for topic questions, choosing only from
  addresses in the glossary; any other address is stripped.
- **FR-007** Replies are brief (about five short lines at most) and say so plainly when the
  glossary does not cover the question.
- **FR-008** The glossary is built by Claude from `l7r.md`, the rules, and public Obsidian Portal
  content, follows Story 6's in/out rule, tags each entry's scope, and records its source
  versions; a staleness report lists changed sections.
- **FR-009** An evaluation question set and runner (Story 7), with results across at least three
  Gemini tiers recorded in this feature's directory and the default model chosen by the rule in
  Story 7, acceptance item 5.
- **FR-010** Local query log, a configurable daily spending ceiling, and graceful failure replies
  (Story 8).
- **FR-011** The command runs in the existing always-on bot process, alongside the mention
  responder, rather than in a new service.

## Success criteria

- **SC-001** All five of the GM's example questions get a correct answer from the chosen default
  model: the rank terms, Tsuruchi Kyoma, the Crab Clan's two patron Fortunes, a link to the
  Imperial Bounties page, and a link to the Wasp Hierarchy page.
- **SC-002** Across the full question set, the default model's correctness is within 5 points of
  the Pro-tier ceiling.
- **SC-003** Cost per question is measured for every tier tested and recorded in the feature
  directory. The GM's bar is "a fraction of" the 40-cent backstory call; the session's working
  target is a median of 2 cents. If the default chosen under Story 7's rule costs more than 2
  cents, the numbers go to the GM. That does not count as the feature failing, and it does not
  justify swapping in a weaker model to hit the target.
- **SC-004** A player gets the reply within 10 seconds for at least 95% of questions.
- **SC-005** No reply is ever visible to anyone but the asker.

## Key entities

- **Glossary entry**: term, aliases, reading and literal meaning, kind (office, institution,
  person, place, clan, family, Fortune, vocabulary, rule term, ...), scope, description, related
  terms, link, source section and its version.
- **Player profile**: Discord account, character name(s), school, Dan, lineage, clan of origin,
  gaming group, sheet address, Obsidian Portal address.
- **Roster**: every linkable person, with full name and address.
- **Evaluation question**: question text, asker profile (or none), required facts, required links,
  answerable or not.
- **Evaluation run**: model, per-question results, totals, cost, latency, date.

## Assumptions

- Both of the character-sheet app's gaming groups (Monday and Tuesday) are playing the Wasp
  campaign; the list of campaign groups is configuration, not code.
- The command lives under the existing "L7R GM Assistant" Discord application. Its interactions
  arrive over the gateway connection the mention responder already holds, because the application
  has no interactions URL configured (checked 2026-10-17).
- The GM's existing Gemini API key pays for the questions.
- Discord markdown links work in private replies.
