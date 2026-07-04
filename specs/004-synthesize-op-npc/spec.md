# Feature Specification: /synthesize skill for existing Obsidian Portal NPCs

**Feature Branch**: `004-synthesize-op-npc`

**Created**: 2026-07-04

**Status**: Draft

**Input**: User description: "A Claude Code skill `/synthesize <character name>` that generates a Gemini backstory for an existing Obsidian Portal character - the chat-session equivalent of the webapp's Synthesize Backstory button, for NPCs already uploaded to OP that the GM wants to flesh out later."

## User Scenarios & Testing *(mandatory)*

The single actor is the **GM** (game master), working inside a Claude Code chat
session. The campaign's cast already lives on the campaign wiki (Obsidian
Portal); the GM frequently uploads a bare character - name, portrait, a one-line
summary, some stats - intending to flesh out a backstory later. Today the only
way to synthesize a backstory is to open the web character generator and click a
button, which does not work for a character that already exists on the wiki. This
feature closes that gap: the GM names an existing wiki character in chat and gets
the same quality of synthesized backstory, grounded in the same setting corpus
and campaign cast, reviewed and saved back to the wiki without leaving the chat.

### User Story 1 - Synthesize a reviewable backstory for a named wiki character (Priority: P1)

The GM types `/synthesize <character name>` naming an NPC that already exists on
the campaign wiki. The system finds that character, gathers everything known
about them (including their one-line summary, which carries relationship cues
like "drinking companion of Kyoma"), generates a backstory grounded in the same
setting material and campaign cast the web generator uses, and presents it in the
chat for the GM to read.

**Why this priority**: This is the core value - turning an existing bare wiki
character into a grounded backstory from within a chat session. Even if the GM
had to save the result manually, this alone would be worth using.

**Independent Test**: Run `/synthesize` with the name of a real wiki NPC and
confirm a backstory appears in chat that is consistent with that character's
stated summary, clan, and traits, and does not contradict the campaign's other
characters.

**Acceptance Scenarios**:

1. **Given** a wiki character whose one-line summary reads "drinking companion of
   Kyoma", **When** the GM runs `/synthesize <that character>`, **Then** the
   presented backstory reflects that relationship rather than inventing an
   unrelated life.
2. **Given** a partial or approximate name (e.g. "Daidoji Jitsuyo" for a
   character stored as "Daidoji no Etsuko Jitsuyo"), **When** the GM runs the
   command, **Then** the system resolves it to the correct character.
3. **Given** a name that matches more than one character, **When** the GM runs
   the command, **Then** the system lists the candidates and asks which one
   before generating anything.
4. **Given** a name that matches no character, **When** the GM runs the command,
   **Then** the system says so and offers the closest names rather than
   fabricating a character.

### User Story 2 - Review and save with three dispositions (Priority: P2)

After the backstory is presented, the GM has three dispositions, offered as two
listed options plus a free-text box: (1) save it to the wiki as-is, (2) generate
a different backstory, or (3) save it with changes - the GM types the changes in
their own words into the free-text box, and that text is what gets applied.
Saving writes the backstory into the character's GM-only notes without disturbing
anything already there.

**Why this priority**: The disposition workflow is what makes the result
durable and safe to accept. It depends on P1 having produced a backstory.

**Independent Test**: With a presented backstory, exercise each disposition and
confirm: as-is saves the text unchanged; "generate another" produces a fresh
backstory and re-presents the options; typed changes are applied before saving.

**Acceptance Scenarios**:

1. **Given** a presented backstory and existing GM-only notes (stats, traits,
   prior remarks), **When** the GM chooses "save as-is", **Then** the backstory
   is added to the GM-only notes and every pre-existing note is preserved intact.
2. **Given** a presented backstory, **When** the GM chooses "generate another",
   **Then** a new backstory is produced from the same context and the GM is again
   offered the same options.
3. **Given** a presented backstory, **When** the GM chooses "save with changes"
   and describes the changes, **Then** the saved text reflects those changes.
4. **Given** a character that already has a previously-synthesized backstory saved,
   **When** the GM synthesizes and saves again, **Then** the new backstory
   replaces the previous synthesized one and no other notes are affected.

### User Story 3 - Surface related characters from the cast (Priority: P3)

When the character's summary names another campaign NPC, the system also notices
which other cast members are described in relation to that same NPC, and feeds
those connections in as additional grounding so the backstory sits correctly
within the web of established relationships.

**Why this priority**: This deepens fidelity - a "drinking companion of Kyoma"
backstory is richer when it is aware of Kyoma's other associates - but the
feature is valuable without it.

**Independent Test**: Synthesize a character whose summary names an NPC who is
also referenced by other characters' summaries, and confirm the related
characters are identified and reflected in the grounding.

**Acceptance Scenarios**:

1. **Given** a character summarized as "drinking companion of Kyoma" and other
   cast members also described in relation to Kyoma, **When** the GM synthesizes,
   **Then** those other characters are surfaced as related context.
2. **Given** a character whose summary names no other cast member, **When** the GM
   synthesizes, **Then** the feature proceeds normally with no related-character
   grounding and no error.

### Edge Cases

- **Missing one-line summary**: the character has no summary on the wiki - proceed
  using the rest of the character's information and note that no summary was found.
- **Wiki unreachable**: the campaign wiki cannot be reached to look up or read the
  character - report clearly and do not save anything; never fabricate the
  character's existing data.
- **Setting corpus unavailable**: the shared setting material that grounds every
  backstory is missing - fail loudly with a clear message rather than silently
  producing a thin, ungrounded backstory (matching the web generator's behavior).
- **Empty generation**: the model returns no usable text - report it and let the
  GM retry rather than saving an empty backstory.
- **Ambiguous caste**: the character's caste (which selects extra setting material)
  cannot be determined from their information - assume the most common case
  (samurai), state the assumption, and let the GM correct it by generating again.
- **Save interrupted or rejected**: if saving to the wiki fails, the GM's existing
  notes remain exactly as they were and the GM is told the save did not complete.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The GM MUST be able to trigger the feature in a chat session by
  naming an existing campaign-wiki character (`/synthesize <character name>`).
- **FR-002**: The system MUST resolve an approximate or partial name to the
  intended wiki character, MUST ask the GM to choose when a name is ambiguous, and
  MUST report a clear "no match" (with nearest names) when nothing matches.
- **FR-003**: The system MUST gather the character's known information from the
  wiki, including the one-line summary that carries relationship cues, even though
  that summary is not available through the wiki's data feed and must be read from
  the character's page.
- **FR-004**: The system MUST generate the backstory using the SAME setting
  grounding and campaign-cast context as the web character generator, including the
  caste-specific material, and MUST exclude the subject character from their own
  campaign-cast context.
- **FR-005**: The system MUST determine the character's caste from their
  information to select the correct setting material, defaulting to samurai and
  stating that assumption when it cannot be determined.
- **FR-006**: The system MUST present the generated backstory to the GM for review
  before anything is saved.
- **FR-007**: The system MUST offer three review dispositions - save as-is,
  generate another, and save with GM-described changes - presented as two listed
  options plus a free-text box whose typed content is taken as the changes.
- **FR-008**: On "generate another", the system MUST produce a fresh backstory
  from the same context and MUST re-present the same options.
- **FR-009**: On "save with changes", the system MUST apply the GM's described
  changes to the backstory before saving.
- **FR-010**: On any save, the system MUST write the backstory into the
  character's GM-only notes as a clearly-delimited section and MUST preserve all
  pre-existing notes unchanged.
- **FR-011**: When a character already has a previously-synthesized backstory, a
  new save MUST replace only that delimited section and leave all other notes
  untouched.
- **FR-012**: When the character's summary names another campaign NPC, the system
  SHOULD surface other cast members described in relation to that same NPC and feed
  those connections into the grounding.
- **FR-013**: The system MUST fail safely: if the wiki cannot be read or written,
  or the setting corpus is missing, it MUST report the problem and MUST NOT leave
  the character's existing notes in a partially-modified state.

### Key Entities *(include if feature involves data)*

- **Wiki character**: an NPC on the campaign wiki, with a name, tags, portrait, a
  public description, a one-line summary (relationship-bearing), and GM-only notes.
  The summary is reachable only from the character's page, not the data feed.
- **Synthesized backstory**: the generated prose, stored as a delimited section
  inside the character's GM-only notes so it can be recognized and replaced on a
  later run without touching other notes.
- **Campaign cast context**: the set of other campaign characters used to keep a
  new backstory consistent with the established cast (the same context the web
  generator uses).
- **Related characters**: cast members whose summaries reference the same NPC as
  the subject's summary, used as extra relationship grounding.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The GM can go from naming an existing wiki character to reading a
  grounded backstory for it without leaving the chat session and without opening
  the web generator.
- **SC-002**: For a character whose one-line summary states a relationship, the
  generated backstory reflects that relationship rather than contradicting or
  ignoring it, in every synthesis run.
- **SC-003**: Saving a backstory never destroys or alters pre-existing GM notes -
  measured as zero loss of prior notes across saves, including repeated saves.
- **SC-004**: Re-synthesizing and saving a character that already has a
  synthesized backstory results in exactly one synthesized-backstory section, not
  an accumulation.
- **SC-005**: The backstory quality matches the web generator's for an equivalent
  character, because the same setting grounding, caste material, and campaign-cast
  context are used.
- **SC-006**: When a name is ambiguous or unmatched, the GM is never silently
  given the wrong character; they are asked or told, before any generation.

## Assumptions

- The GM is authenticated to the campaign wiki in this environment (the session
  can both read character pages and save changes), as the existing note-intake and
  generator workflows already assume.
- The one-line summary a GM wants reflected lives in the character's summary field
  on the wiki (confirmed present for the motivating example), and is the intended
  source of relationship cues.
- Reusing the web generator's setting grounding and campaign-cast context is
  desired, so backstories from chat and from the web generator are equivalent.
- Caste is inferable from the character's tags/notes in the common case; samurai
  is the correct default for the campaign's overwhelmingly-samurai cast.
- Synthesized backstories belong in GM-only notes, not the public description, by
  default (the GM chose this); public placement is out of scope for this version.
- A backstory is regenerated fresh rather than incrementally edited by the model;
  "save with changes" applies the GM's described edits to the chosen text.
- Cost per synthesis is already understood and acceptable (see the synthesis cost
  reference); this feature adds no new model beyond the one already in use.
