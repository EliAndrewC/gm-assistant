# Feature 230: conversations with several NPCs

**Request**: [gm-request.md](gm-request.md) (2026-10-26, two messages). **Status**: specified.
**Cross-repository half**: <https://github.com/EliAndrewC/character-sheet/issues/6> (`/discern-honor`
across several NPCs; contract agreed there 2026-10-26).

## Why

`begin_conversation` takes one NPC. When the PCs talk to Hideki and Souma together, the GM can
record the scene against only one of them: Souma's rolls, numbers and Sincerity rolls land on
Hideki's record or nowhere. The code already expected this (`npcskills.py`: "a later feature will
track several, which is why a tag holds no NPC").

## Terms

- **Primary**: the first NPC named in `begin_conversation`. The conversation's public record (its
  heading and every player roll line) is written to the primary's bio, for the whole conversation,
  whoever joins or leaves.
- **Member**: any NPC in the conversation: the primary and every other NPC, present or departed.
- **Present**: a member who has not left (`remove_from_conversation`).
- **Handle**: the name a member gets at the prompt while the conversation is open (`hideki`,
  `souma`).

## User Scenarios & Testing

### Story 1 - opening a conversation with several NPCs (P1)

`begin_conversation('Hideki', 'Souma', 'stolen sheets')` opens one conversation. Hideki is primary
because he is named first; the title is the one argument that names no NPC, wherever it sits.

**Acceptance**
1. One argument: it is the NPC (today's behavior, no title).
2. Two or more: every argument is matched against the Obsidian Portal roster the way a single name
   is today (whole name tokens). Exactly one must match no record; it is the title. Zero
   non-matching arguments (with two or more given), or two or more, raise an error naming the
   arguments and saying which way it failed. An argument matching several records raises the
   candidates, as today. The same NPC named twice is an error.
3. `begin_conversation('Otsuki', 'confrontation on the Imperial road')` still opens a one-NPC
   conversation with a title, and a one-NPC conversation behaves exactly as it does today.
4. Each member gets a handle at the prompt (Story 3). The open message names the primary and the
   other members.
5. `channel=` and `new=` stay keyword-only and mean what they mean today.

### Story 2 - the records (P1)

The primary's bio gets the conversation's `h4.` heading and every player roll line, exactly as
today. **Every other member's bio** gets an entry under its portrait, at the same place a
conversation block goes:

    h4. Stolen sheets
    Rolls for this conversation are on [[:tsuruchi-hideki|Tsuruchi Hideki]]'s page.

It is written once, when the NPC becomes a member (at open, or at `add_to_conversation`), so it
exists even if no roll is ever made, and it is never rewritten. It is the only thing a
conversation writes to a non-primary member's bio.

**Each member's GM-only notes** carry that member's own NPC-specific records, each in the existing
block: `NPC numbers:` (rings and ranks read off that member's tagged rolls), `Hidden rolls:` (that
member's Sincerity rolls and the acting rolls they opposed), `Void points spent:` (that member's
void points), and `Discern Honor:` (records of PCs who used the knack on that member).

**Acceptance**: after a conversation with Hideki (primary) and Souma in which Souma rolled tact
and spent a void point, Souma's notes hold `tact` in `NPC numbers:` and a `Void points spent:`
line, Hideki's hold neither; the player roll lines are on Hideki's bio only; Souma's bio holds
only the link entry.

### Story 3 - saying whose roll it is (P1)

The GM's forms, with Hideki as primary:

| typed | the roll is |
|---|---|
| `tact()` | Hideki's tact, as today |
| `hideki.tact()` / `souma.tact()` | that member's tact; every called form works on a handle: `souma.tact(2)`, `souma.tact(5, 3)`, `souma.tact(vp)`, `souma.acting(2)` |
| `xky(5, 3) - tact` | Hideki's tact |
| `xky(5, 3) - souma.tact` | Souma's tact |
| `xky(5, 3) - tact - souma` | Souma's tact |
| `xky(5, 3) - souma - tact` | Souma's tact, identical in every effect to the line above |
| `xky(5, 3) - souma` | Souma's roll, untagged |

**Nothing NPC-specific happens to a tagged roll until its NPC is settled.** The things a tag does
today - read the ring and rank and record them, stop and ask when they disagree with the record,
apply an oppose penalty, note a Sincerity roll - all depend on WHICH NPC, so in a conversation that
has ever had more than one member, `- tact` with no NPC yet only marks the roll. The effects run:

- at the moment `- souma` (or `- hideki`) is applied, for that member; or
- at the END OF THE STATEMENT the GM typed, for the primary - before the statement's value is
  echoed, so the echoed total is the one with any oppose penalty taken off.

`xky(5, 3) - souma - tact` reaches the same state by the other road: `- souma` settles the NPC
first, so `- tact` runs its effects at once. Either order leaves the roll, the record, the prompts
asked and the echoed total identical; a test pins that equivalence.

A roll marked for one member cannot be marked for another (`xky(5, 3) - souma - hideki` is an
error, as tagging twice is today). A one-member conversation keeps today's immediate behavior.

**Handles.** A member's handle is their personal name in lower case (`Tsuruchi Souma` ->
`souma`). If that name is already taken at the prompt by anything that is not a handle of this
conversation, or two members share a personal name, those members' handles are their full names in
snake case (`tsuruchi_souma`) instead, and the open message says so. Handles are removed when the
conversation ends or is abandoned, and a member's handle stays usable after they leave (so the GM
can still mark an earlier roll as theirs or read it) - but rolling for a departed member raises.
`npc('Souma')` returns the same handle, for scripts and for the collision case.

### Story 4 - joining and leaving (P1)

`add_to_conversation('Kenji', 'Aiko')` adds any number of NPCs (each resolved like a name in
Story 1; an argument matching no record or several is an error, and nothing is added). Each new
member gets a handle, the Story 2 link entry, a Discern Honor plan (Story 6), and their numbers
read from their notes. Adding a departed member again makes them present again.

`remove_from_conversation('Souma')` (any number) marks members as departed. Their records stay;
their handle stays (Story 3) but rolling for them raises.

**Removing the primary does not make anyone else primary.** The heading and every player roll line
still go to the primary's bio. From then on `tact()`, `xky(5, 3) - tact` with no member named, and
every other default-to-primary form RAISE an error that names the present members and the handle
form to use (`souma.sincerity()`); nothing is dispatched to another member.

**The join or leave is marked in the primary's bio at the point it happened**: a line
`Souma joined the conversation` / `Hideki left the conversation` between the lines from rolls made
before it and the lines from rolls made after it. A grouped line (the Etiquette line that collects
every roller) is split at a membership change so each part sits on its own side of the marker; an
interrogation line of questioning stays one line, placed where its first roll was.

**Acceptance**: rolls A and B, then `add_to_conversation('Kenji')`, then roll C writes A, B, the
`Kenji joined` line, C, in that order. Removing and re-adding writes both markers.

### Story 5 - an oppose roll's target (P1)

A player's Oppose Social / Oppose Knowledge applies, by default, to the PRIMARY: its penalty comes
off the primary's later Air / Water rolls, exactly as today, and not off any other member's. The GM
moves it with `move_oppose(souma)`, `move_oppose(souma, 'Jimen')`, `move_oppose(souma, 'Jimen',
'social')` - the PC and the knack are needed only when more than one live oppose roll could be
meant, and it never guesses (the same rule `cancel_oppose` follows). Moving re-prices every
already-made roll of the old and the new target, as a late-seen oppose roll does today. If the
primary has left when an oppose roll is seen, it has no target until the GM moves it, and the
watcher says so.

### Story 6 - Discern Honor covers every member (P1)

When an NPC becomes a member, what each knack-holder PC would be told about THAT NPC is decided
then and sent to the character-sheet app, as feature 212 does for the one NPC today. The sheet's
`/discern-honor` (character-sheet#6) answers for one named NPC or for every present member; the
REPL records each ask on the asked-about member's own `Discern Honor:` block, once, on sight. A
member without an `Honor:` line is reported and skipped, as today. Removing a member tells the
sheet they left (they are no longer answered), but an ask made before they left is still recorded.
`discern_honor('Souma', Jimen)` inside the conversation returns Souma's planned value.
`abandon_conversation()` rolls every member's Discern Honor block back.

The REPL sends the new multi-NPC shape only once the sheet app says it is live; until then it
sends the one-NPC shape for the primary, which is what is deployed today.

### Story 7 - the annotate menu with several members (P2)

- A contested line names the member whose roll was paired: `Jimen vs Souma tact: ...`.
- A typed opposing total, and an intimidation roll's "How did X appear?", ask which member when
  more than one is present (a menu, the primary highlighted first if present); with one present
  member there is no question.
- A line of questioning's hidden entry goes to the notes of the member whose Sincerity roll opposes
  it.

### Edge cases

- A tag made with no conversation open only marks the roll (today's rule); no handle exists then.
- `- tact` left unsettled at statement end while the primary has left raises the primary-left error
  (Story 4); the roll stays tagged with no NPC, nothing is recorded, and `_ - souma` settles it.
- A statement assigned rather than echoed (`r = xky(5, 3) - tact`) settles at the end of that
  statement too, before the next prompt.
- `repl.py 'xky(5, 3) - tact'` (one-shot) settles the same way.
- The interpreter-exit path and `end_conversation()` settle anything still unsettled first.
- The watcher thread never settles anything: settling can ask the GM a question.
- `end_conversation()` / the exit path write every member's notes, not only the primary's.

## Requirements

- **FR-001** Argument classification exactly as Story 1.
- **FR-002** Public lines and the heading go only to the primary's bio, for the whole conversation.
- **FR-003** Each non-primary member's bio gets one link entry (Story 2), written when they join.
- **FR-004** NPC numbers, hidden rolls, void points and Discern Honor records are kept per member
  and written to that member's GM-only notes.
- **FR-005** Every form in Story 3's table; the NPC-specific effects of a tag run once, against the
  settled member, never provisionally against another; `- tact - souma` == `- souma - tact`.
- **FR-006** Handles as Story 3, never shadowing an existing prompt name; removed at close.
- **FR-007** `add_to_conversation(*names)` and `remove_from_conversation(*names)` as Story 4.
- **FR-008** After the primary leaves, every default-to-primary form raises; public lines still
  go to the primary's bio.
- **FR-009** Join and leave markers in the primary's bio at their point in the sequence.
- **FR-010** Oppose rolls target the primary by default; `move_oppose` moves one (Story 5).
- **FR-011** Discern Honor plans, serves and records per member (Story 6), against the
  character-sheet#6 contract, switched on only once that app says it is live.
- **FR-012** A one-member conversation is unchanged in every observable way; the existing rolls
  test suite passes unmodified except where a test asserts the one-NPC ceiling itself.
- **FR-013** `COMMANDS` / `help_l7r()` document the new functions and the handle forms.

## Out of scope

- Making a member other than the first the primary, or changing the primary mid-conversation (the
  GM ruled it out: the original primary stays where the record goes).
- Several conversations open at once.
