# Feature Specification: Campaign Character Context

**Feature Branch**: `003-campaign-character-context`

**Created**: 2026-07-02

**Status**: Draft

**Input**: User description: When synthesizing an NPC backstory, include the campaign's other characters (their backstories) so the new backstory does not contradict them and can reference them via steering notes. Characters live in Obsidian Portal; the app maintains a gitignored, id-keyed incremental cache (one list call + body fetches only for new/changed characters), bundled at deploy and refreshed in-memory at runtime. Missing/unreachable data degrades gracefully (synthesis still works). Include all campaign characters (minus the one being generated).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New backstory stays consistent with existing characters (Priority: P1)

The GM has already created several characters for a place (say, a temple: a Grand Abbot, some monks). When the GM generates and synthesizes a new character for that same campaign, the resulting backstory does not contradict the established facts of those existing characters (their roles, relationships, history), because the model is given the existing characters' backstories as context.

**Why this priority**: This is the core value - it makes a growing cast internally coherent instead of a set of independently-invented, mutually-contradictory people.

**Independent Test**: Ensure a couple of characters with distinctive, checkable facts exist in the campaign; synthesize a new related character; confirm the new backstory does not assert anything that conflicts with those established facts.

**Acceptance Scenarios**:

1. **Given** the campaign has existing characters with backstories, **When** the GM synthesizes a new character, **Then** the synthesis prompt includes those other characters' backstories and the result is consistent with them.
2. **Given** the character being generated shares a name with an existing campaign record, **When** the backstory is synthesized, **Then** that same character is not fed back in as its own "other character" context.

---

### User Story 2 - Steering notes can reference another character (Priority: P1)

The GM types a steering note that names another character - e.g. "butts heads with the Grand Abbot" - and the synthesized backstory reflects a relationship grounded in the Grand Abbot's actual established personality and history, not an invented stand-in.

**Why this priority**: This is the GM's concrete motivating example and the most valuable, most reliable use of the context (naming a character focuses the model far better than passive "don't contradict anyone").

**Independent Test**: With the Grand Abbot present in the campaign, synthesize a character with the steering note "butts heads with the Grand Abbot"; confirm the result references the Abbot in a way consistent with the Abbot's real backstory.

**Acceptance Scenarios**:

1. **Given** a named character exists in the campaign, **When** the GM references that character by name in steering notes, **Then** the backstory's treatment of that character is consistent with the referenced character's established backstory.

---

### User Story 3 - It never blocks or slows the GM to a halt (Priority: P1)

Bringing in campaign context must not make synthesis fragile or slow. If the character store is unreachable, or nothing is cached yet, synthesis still produces a backstory (just without the extra context). Repeated re-rolls do not repeatedly pay the full cost of gathering every character.

**Why this priority**: The existing one-click synthesis experience must be preserved. Context is an enhancement, not a dependency; regressing reliability or speed would be worse than not having the feature.

**Independent Test**: Simulate the character store being unreachable and confirm synthesis still returns a backstory with a clear "0 characters in context" signal; re-roll several times quickly and confirm the character context is not re-gathered from scratch each time.

**Acceptance Scenarios**:

1. **Given** the character store is unreachable, **When** the GM synthesizes, **Then** a backstory is still produced (without campaign context) and nothing errors out.
2. **Given** a backstory was just synthesized, **When** the GM re-rolls within a short window, **Then** the campaign context is reused rather than fully re-gathered.
3. **Given** the GM saved a new character a moment ago, **When** they next synthesize, **Then** that new character is available in the context (the store is the source of truth and newly-changed characters are picked up).

---

### User Story 4 - The GM can see what is in context (Priority: P2)

After synthesizing, the GM can see how many campaign characters were included as context, so they can trust the result and notice if it says 0 when they expected more.

**Why this priority**: Trust and debuggability. It's a small readout, not core behavior, hence P2.

**Independent Test**: Synthesize and confirm a visible count of campaign characters included appears near the result; confirm it reads 0 when the store is unreachable.

**Acceptance Scenarios**:

1. **Given** a synthesis completes, **When** the result is shown, **Then** the GM sees how many campaign characters were included in context.

### Edge Cases

- **Store unreachable / auth failure**: synthesis proceeds with whatever context is cached (possibly none); the readout reflects the reduced count; no error surfaced to block the GM.
- **First run with no cache** (e.g. fresh checkout): a one-time full gather of all character backstories; acceptable latency once, then incremental.
- **A character was edited in the store**: the next gather picks up the edit (per-character change detection), without re-gathering unchanged characters.
- **A character was deleted in the store**: it drops out of the context.
- **The character being generated already exists in the store** (regeneration): it is excluded from its own context.
- **Very large cast**: the context grows with the campaign; it must remain within the model's input limits and not degrade the core synthesis (all-characters scope is v1; narrowing scope is a future option).
- **Typographic dashes**: character bodies come from the GM's own writing and may contain any characters; they are runtime prompt content, not committed files, so the hyphens-only policy applies to committed project files, not to fetched character text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When synthesizing a backstory, the system MUST include the campaign's other characters' backstories (name, tags, public bio, and GM-only notes) as context in the prompt, in a clearly delimited section separate from the character being generated.
- **FR-002**: The system MUST instruct the model to keep the new character consistent with those other characters and to honor references the GM makes to them in steering notes.
- **FR-003**: The character being generated MUST be excluded from its own campaign context (matched by id when known, else by name).
- **FR-004**: The system MUST maintain an id-keyed cache of character backstories with a per-character change marker, refreshed incrementally: one listing of all characters, then fetching a full body only for characters that are new or changed since the cache was last updated, and removing characters no longer present.
- **FR-005**: The cache MUST persist as a gitignored local artifact (not committed to version control, not dependent on server-side persistent storage), refreshed and bundled into the deployment artifact at build time, and loaded as the starting point at runtime.
- **FR-006**: At runtime the cache MUST be refreshed against the store cheaply (a single listing plus only-changed body fetches) and reused for a short window so repeated re-rolls do not re-gather everything.
- **FR-007**: Gathering campaign context MUST be non-blocking and non-fatal: if the store is unreachable or returns errors, synthesis MUST still produce a backstory using whatever context is available (possibly none). Only a missing setting corpus fails loud; missing campaign context never does.
- **FR-008**: Newly saved or edited characters MUST become available to subsequent syntheses without a redeploy (the store is the source of truth; the incremental refresh picks up changes).
- **FR-009**: The synthesis result MUST report how many campaign characters were included as context, surfaced to the GM near the result.
- **FR-010**: All existing synthesis behavior MUST be preserved unchanged: the honor model, calendar date-anchoring, rank-is-not-an-office rule, and the summary/tags handling.
- **FR-011**: The character-store integration is an external boundary and MUST be tested against saved fixtures of real responses (not transport mocks); the cache's pure logic (change detection, body-fetch selection, context assembly, cache read/write) MUST have full automated test coverage.
- **FR-012**: The feature MUST NOT introduce typographic dashes into any committed project file.

### Key Entities *(include if feature involves data)*

- **Campaign character (cached)**: id, display name, tags, change marker (last-updated), public bio, GM-only notes. The unit of both the cache and the assembled context.
- **Character cache**: the id-keyed collection of the above, with enough per-entry information to refresh incrementally and to assemble the context block.
- **Campaign context block**: the assembled, prompt-ready text listing the other characters, injected into the synthesis prompt.
- **Character being generated**: the current NPC (already defined by the synthesis feature); the subject the context is gathered *for* and excluded *from*.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a campaign with existing characters, a synthesized backstory does not contradict the established facts of those characters, and when the GM names one in steering notes the result reflects that character's real backstory.
- **SC-002**: Synthesis still returns a backstory when the character store is unreachable, with a visible indication that 0 campaign characters were in context - no error, no blocked click.
- **SC-003**: A steady-state synthesis gathers context with a single listing plus body fetches only for characters changed since the last refresh (typically none during a session), so the added latency over the prior one-click flow is small and roughly constant regardless of total cast size.
- **SC-004**: A character saved moments earlier appears in the next synthesis's context without any redeploy.
- **SC-005**: The GM can see, after each synthesis, how many campaign characters were included.
- **SC-006**: The project quality gate passes (lint, format, types, tests, and full coverage on the new cache logic), the character-store boundary is covered via saved fixtures, and any UI change passes the standard viewport + DOM-audit verification.

## Assumptions

- The single GM is the only user; no multi-user or permissions concerns.
- Obsidian Portal is the character store and is already integrated and credentialed; its listing endpoint returns all characters (with a per-character change marker) in one call, and full bodies are fetched per character.
- All-campaign scope is the v1 behavior (the GM asked to "pull every backstory"); narrowing by place/tag is a possible later refinement and is out of scope here.
- The cache being a gitignored artifact is acceptable; a fresh checkout paying a one-time full gather is acceptable.
- Character bodies are the GM's own campaign content and are acceptable to send to the same text model that already receives the full canonical setting notes.
- The runtime environment is ephemeral (scales to zero, multiple instances, no guaranteed local persistence), so the cache cannot rely on server-side durable storage; each instance reconciles against the store independently.
