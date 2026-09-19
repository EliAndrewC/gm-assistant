# Feature Specification: How the NPC APPEARED after an intimidation roll

**Feature Directory**: `specs/209-intimidation-appearance`

**Created**: 2026-09-19

**Status**: Implemented 2026-09-19.

**Input**: GM request 2026-09-19, verbatim in [gm-request.md](gm-request.md). Builds on feature 202
(annotation) and 207 (what `annotate()` asks depends on the skill).

## Why

An intimidation roll has a result the players see at the table - the NPC looks stoic, unsettled,
rattled or shaken - and today the record keeps only the number and what the roll was for. The
thresholds are hidden by rule, and an NPC can put on a face, so the record must say how the NPC
APPEARED and never claim how they felt.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Annotating an intimidation roll records how the NPC appeared (Priority: P1)

The GM annotates an intimidation roll. After saying what the roll was for, they pick one of four
options - stoic, unsettled, rattled, shaken - and the written line ends with
`<NPC name> appeared <state>`.

```
30 intimidation: Jimen - threatening to have him arrested: Fumitake appeared unsettled
```

**Independent Test**: Annotate an intimidation roll with a note and the choice "unsettled"; the
written line is the one above.

**Acceptance Scenarios**:

1. **Given** a captured intimidation roll, **When** annotated, **Then** after the note the GM is
   offered exactly the four states and must pick one; an unrecognized or blank answer asks again.
2. **Given** the choice "rattled", **Then** the line ends `: Fumitake appeared rattled` - the word
   "appeared", with the NPC's personal name, never "was" or "felt".
3. **Given** the rare CONTESTED intimidation roll (or one with a bonus), **Then** the same question
   is asked and the same clause ends its line.
4. **Given** a roll the GM discards, **Then** the question is not asked.
5. **Given** Ctrl-C at the question, **Then** everything staged in that `annotate()` run is
   abandoned, as at every other prompt in the menu.
6. **Given** a roll of any other skill, **Then** nothing about its annotation changes.
7. **Given** an intimidation roll saved bare by the interpreter-exit path, **Then** it is written
   with no appearance clause, since none was chosen.

## Requirements *(mandatory)*

- **FR-001**: Annotating an intimidation roll MUST ask, after what the roll was for, how the NPC
  appeared, offering exactly: stoic, unsettled, rattled, shaken.
- **FR-002**: A choice MUST be made; there is no default. (The thresholds are hidden and the GM
  decides them per scene, so the tool cannot infer the state from the number.)
- **FR-003**: The written line MUST end `: <NPC personal name> appeared <state>`, and MUST NOT
  assert the NPC's actual state in any wording.
- **FR-004**: The question MUST be asked for every way an intimidation roll can be recorded
  (open, open with bonus, contested) and MUST NOT be asked for a discarded roll.
- **FR-005**: No other skill's annotation or written line changes.

## Decisions the request left open

1. **Where the clause sits**: at the end of the line after a colon, the shape interrogation and
   acting already use for "what the players got" (`- <note>: <outcome>`).
2. **How an option is picked**: by number 1-4 or by typing the word or an unambiguous start of it
   (`u`, `r`, `st`, `sh`; a bare `s` is ambiguous and asks again).
3. **Feature 208's Decision 9 is closed**: the GM ruled that canceling a line of questioning is not
   wanted. Recorded there.

## Review history

Independent `spec-fidelity` review (constitution XVI), against gm-request.md as written.

- **Round 1 - FAITHFUL** (2026-09-19). No changes. The required choice (FR-002) was checked
  hardest and held: the four states are exhaustive, and the menu already has a required prompt
  that re-asks on blank (the note). Two asides: the review ran alongside the implementation rather
  than before it; and the spec assumes the roller is a PC, as the request does.

## Ruled after delivery

- **An NPC's own intimidation roll needs nothing here** (GM 2026-09-19, asked because the prompt
  always names the NPC as the one who appeared): *"we don't need to worry about NPCs rolling
  intimidation. The only time that they would do that is if it is a contested intimidation roll
  against a PC. So most PC intimidation rolls are open but all NPC rolls of intimidation are
  contested."* An NPC's roll is therefore only ever the OPPOSING side of a PC's contested roll,
  which `annotate()` already pairs, and the captured roll being annotated is always the PC's.
  Do not add a "who appeared?" question.

## Success Criteria *(mandatory)*

- **SC-001**: Every annotated intimidation roll in a bio says how the NPC appeared.
- **SC-002**: No written line claims what an NPC felt.
