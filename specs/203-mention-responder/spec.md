# Feature Specification: Answering when a bot is mentioned

**Feature Directory**: `specs/203-mention-responder`

**Created**: 2026-08-29

**Status**: Draft

**Input**: GM request, reproduced verbatim in [gm-request.md](gm-request.md).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A player mentions a bot and it answers (Priority: P1)

A player writes `@L7R GM Assistant What is your purpose?` in a channel. The bot replies, in that
channel, in seconds.

**Why this priority**: It is the whole feature. The players asked for it directly.

**Independent Test**: With the responder running against the test server, a mention produces a reply.

**Acceptance Scenarios**:

1. **Given** the responder is running, **When** a human mentions a bot it watches, **Then** that bot
   replies in the same channel.
2. **Given** a message that mentions nobody, **When** it arrives, **Then** nothing is sent.
3. **Given** a message mentioning a bot the responder does not hold a token for, **When** it
   arrives, **Then** nothing is sent.
4. **Given** a mention matching no response rule, **When** it arrives, **Then** the default reply is
   sent - a page is never met with silence.

---

### User Story 2 - The bot that was addressed is the bot that answers (Priority: P1)

Mentioning the Character Sheet bot gets a reply from the Character Sheet bot, not from whichever bot
happens to be listening.

**Why this priority**: The GM's stated reason for the feature's shape - *"it is a feature of good
user interface design that a computer program works the way that its users will intuitively expect
it to work."* Answering under the wrong name breaks exactly that.

**Independent Test**: Mention each bot in turn; each reply's author is the bot addressed.

**Acceptance Scenarios**:

1. **Given** a mention of bot A, **When** it replies, **Then** the reply's author is A.
2. **Given** a mention of bot B, **When** it replies, **Then** the reply's author is B - even though
   A holds the gateway connection.
3. **Given** a message mentioning BOTH bots, **When** it is answered, **Then** each replies once,
   and neither reply triggers the other.

---

### User Story 3 - It cannot melt the server (Priority: P1)

The responder never replies to a bot, including itself, and cannot enter a reply loop.

**Why this priority**: The GM has watched this exact failure take down a server: *"the bot was
carelessly programmed, so it just kept responding to itself in an infinite loop that was really bad
for the server and made it unusable."* A loop here is not a bug, it is an outage.

**Independent Test**: Feed it a message whose author is a bot, including a reply it just sent.

**Acceptance Scenarios**:

1. **Given** a message whose author is a bot, **When** it arrives, **Then** nothing is sent, whatever
   it says.
2. **Given** the responder's own reply mentions a bot, **When** that reply arrives back over the
   gateway, **Then** nothing is sent.
3. **Given** a human mentions a bot many times in quick succession, **When** they are handled,
   **Then** replies are rate-limited per channel rather than sent one per message.

---

### User Story 4 - It survives a night alone (Priority: P2)

The connection drops - Discord restarts a gateway, the network blips - and the responder reconnects
without help.

**Why this priority**: It runs unattended on a server the GM is not watching. A responder that dies
silently at 2am is worse than none, because everyone assumes it works.

**Acceptance Scenarios**:

1. **Given** the socket closes, **When** it does, **Then** the responder reconnects and resumes.
2. **Given** Discord asks it to reconnect, **When** it does, **Then** no message is answered twice.
3. **Given** it cannot connect at all, **When** it retries, **Then** it backs off rather than
   hammering Discord.

---

### Edge Cases

- A mention inside a code block or a quote of someone else's message: still a mention as far as
  Discord is concerned, and answered. Not worth distinguishing.
- A mention in a channel the listening bot cannot see: never heard, so never answered. The listener
  must therefore be the bot with the widest view.
- A mention of a bot that is in the guild but lacks Send Messages: the reply fails; it is logged and
  not retried forever.
- An `@everyone` or a role mention that happens to include a bot: NOT treated as addressing it.
- A message with no text after the mention: still answered.
- A DM to the bot: out of scope for this feature; ignored.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The responder MUST hold a gateway connection and observe messages in every channel the
  listening bot can see.
- **FR-002**: It MUST reply when a message directly mentions a bot it holds a token for. When no
  response rule matches, it MUST still reply, using a DEFAULT reply - a page always gets an answer.
  Subject only to FR-005's per-channel limit. (Without this, the GM's own example question would be
  met with silence, since a rule table only answers what someone anticipated - see Assumptions.)
- **FR-003**: The reply MUST be sent AS the bot that was mentioned, using that bot's own token.
- **FR-004**: It MUST NEVER reply to a message whose author is a bot, including its own replies.
- **FR-005**: It MUST rate-limit replies per channel, so a burst of mentions cannot produce a burst
  of messages.
- **FR-006**: A role mention or `@everyone` that includes a bot MUST NOT count as addressing it.
- **FR-007**: It MUST reconnect and resume when the connection drops, with backoff, and MUST NOT
  answer the same message twice across a reconnect.
- **FR-008**: What it says MUST be configured as data - patterns and replies, plus the default of
  FR-002 - so adding a joke is not a code change. The rule-table shape follows from a recorded
  implementer's decision (see Assumptions), not from the request, which is silent on how replies are
  produced.
- **FR-009**: It MUST run as a standalone process with no dependency on the fly.io apps, so it costs
  nothing beyond the always-on server the GM already pays for.
- **FR-010**: It MUST be runnable against the test server alone, so the GM can exercise it before
  the Character Sheet bot joins the live server.
- **FR-011**: The feature MUST state what the GM has to change to exercise it in Robot Role Call
  before the Character Sheet bot joins the live server - which application needs which permission and
  which intent, and how the responder is pointed at the test server alone. The GM asked this
  directly: *"What needs to change for me to test all of this out in robot role call prior to adding
  L7R Character Sheet to the real server."*

### Key Entities

- **Watched bot**: an application id, a token to speak with, and whether it is the listener.
- **Response rule**: a pattern to match against the message text and what to say. Data, not code.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A mention is answered within a few seconds, without the GM running anything by hand.
- **SC-002**: Each bot answers under its own name, so a player cannot tell the replies come from one
  process.
- **SC-003**: No reply loop is possible: a message authored by any bot produces nothing.
- **SC-004**: The responder survives a dropped connection unattended.
- **SC-005**: Adding a new joke is a data change. (Consequence of the scripted-reply decision in
  Assumptions, which the GM can overrule.)
- **SC-006**: It costs nothing beyond the server the GM already runs.

## Assumptions

- **Replies are SCRIPTED, not generated - an implementer's decision taken where the request is
  SILENT, not the GM's instruction.** The request does not say how reply text is produced. This spec
  chooses a fixed rule table: a generated reply carries a per-call cost against something the GM
  called *"basically a joke"*, and would put unreviewed text under the GM's bots' names in their
  players' channel. What the choice costs, stated plainly: a mention nobody anticipated - INCLUDING
  the GM's own example, `@L7R GM Assistant What is your purpose?` - gets the default reply rather
  than an answer to the question. The GM can overrule this without disturbing any other requirement.

  The cake-is-a-lie exchange of 2026-08-28 is **NOT** the model for this feature. An earlier draft of
  this spec cited it as though it were, which was the author completing the GM's thought: the GM said
  they *"would think about implementing that kind of feature in the future"* and *"couldn't make any
  promises"*, so keyword auto-response is out of scope here and is not evidence for anything.
- **One gateway connection, two tokens.** Posting a message is a REST call authorized by a bot
  token and needs no gateway of its own, so the listener hears everything and either bot can speak.
  A second connection would buy nothing unless a channel existed that only the other bot could see.
- The listening bot is the one with the widest channel access - today the GM Assistant, which is in
  both servers where the Character Sheet bot is in one.
- The process runs on the GM's Lightsail box. Nothing in the design depends on that; it needs only
  somewhere always-on with outbound network.
- **What the GM must change, per FR-011** (verified against Discord 2026-08-29): the listening
  application needs the **Message Content intent**, already enabled; the speaking bot needs **Send
  Messages** in that guild. In Robot Role Call the Character Sheet bot already has it (`52224`) and
  the GM Assistant does not (`66560`) - one toggle on its role, editable in place, no kick and no
  re-invite, recorded in the server Audit Log rather than announced in a channel.
- A bot's permissions can be widened after it has joined; the GM asked whether it had to be removed
  and re-added, and it does not.

## Review history

**Round 1** (2026-08-29, `spec-fidelity` Mode 2, independent of the author): **CHANGES REQUIRED**,
four findings, all applied. Question 1 passed on every clause of the request. Question 2 found:

1. **The scripted-reply Assumption attributed the author's decision to the GM.** It read *"The GM
   asked for 'the jokes' and described a canned cake-is-a-lie response as the model"* - and the GM
   did neither. "Jokes" says nothing about how reply text is produced, and the cake exchange is from
   a different conversation about a feature the GM explicitly declined to promise (*"couldn't make
   any promises"*). Using a not-promised idea as the model for this one was the author completing
   the GM's thought. The decision stands and is defensible; the false provenance is gone, and the
   cost is now stated in the open - a mention nobody anticipated, INCLUDING the GM's own example
   question, gets the default reply rather than an answer.
2. **FR-002 promised a reply FR-008 could not always deliver**, and the gap landed exactly on the
   GM's example: `What is your purpose?` is answered only if someone wrote that joke in advance.
   FR-002 now requires a default reply, pinned by a new acceptance scenario.
3. **FR-011 (log every reply) was unrequested** - ordinary hygiene wearing a MUST. Replaced with the
   requirement that actually answers the GM's direct question.

And one finding against question 1 rather than question 2:

4. **The GM asked "what needs to change for me to test" and no requirement carried it.** A request
   clause with no deliverable behind it - it sat in Assumptions, and one line there assumed the work
   was already done.

The reviewer explicitly CLEARED three additions a later reviewer should not reopen: FR-005 (per
channel rate limiting - carried by the GM's own loop-outage history AND their ToS-conformance
statement, since honoring rate limits is Discord's documented expectation); FR-006 (a role mention
or `@everyone` does not address a bot - Discord's payload distinguishes `mentions` from
`mention_roles`/`mention_everyone`, so the distinction is native rather than invented, and nobody is
addressing the bot when they ping the room); and FR-007 (reconnect with backoff - the minimum viable
behavior for an unattended process, and again inside ToS conformance).

It also confirmed the single-gateway answer is faithful and honestly recorded rather than buried:
the GM's question was scoped to *"these particular Discord channels"*, and the limitation appears in
both Edge Cases and Assumptions with its consequence stated.

One item referred to the GM: if the Character Sheet bot is later added to a channel the GM Assistant
cannot see, a player mentioning it there gets silence - the one place the "works the way users
intuitively expect" rationale could break. That is a permissions question at invite time, not a code
question.

**Round 2** (2026-08-29, re-read from disk rather than trusting the described diff): **FAITHFUL.**
All four resolved. Of finding 1 the reviewer wrote: *"The decision that remains is the author's, is
labeled as the author's, and is priced."*

Two record-keeping notes it raised, both fixed rather than waved off:

- The Assumptions bullet said *"the GM asked whether it had to be removed and re-added"* while
  `gm-request.md` contained no such question. The GM DID ask it - the words were in the conversation
  and never made it into the verbatim record, which is the same class of error as finding 1 one step
  removed. Their actual words are now in `gm-request.md` under "On the permission change", so the
  claim can be checked against the primary record.
- This history filed finding 4 under question 2 when it was a question 1 gap. Corrected above.

The reviewer also asked that the server name be confirmed rather than taken from dictation. Verified
against Discord: guild `1543009570157236274` is named **Robot Role Call**, matching the spec.
