# Plan: feature 214 - the Isawa Ishi 3rd Dan boost

**THIS SESSION WRITES NO CODE IN THE CHARACTER-SHEET TREE.** Its one file there is the handoff
document `discord-design/ishi-boost-requirements.md`, left uncommitted for that repository's
session (the 211 / 212 pattern). gm-assistant's half is built against that document's contract and
verified live once the sheet app deploys it (tasks Phase 3).

## Constitution check

- **X (tests, 100% coverage)**: every new branch has a test; boundaries injected as elsewhere in
  `rolls/`. `conversation.py` is 866 lines, so the boost logic goes in a new module rather than
  pushing it past ~1,000.
- **XIII (no regressions)**: baseline `make done` taken on the unmodified clone before any edit.
- **XIV (fix what you find)**: the deferred-response defect (below) is fixed in this feature.
- **XVI (literal)**: spec reviewed; see its Review history.

## Where each piece lives

| piece | file |
|---|---|
| `Roll.boost` / `Roll.boosted_by` (the amount folded into `total`, and who), `Conversation.boosts` | `models.py` |
| `Boost` (booster, total, message, target message, applied roll index, reason held, discarded); recognizing a boost in a bot message, a typed message, a recorded row; the reply reference; resolving and applying a target; un-applying | `boost.py` (new, pure apart from `say`) |
| `RecordedRoll.roll_key` / `.target_message_id` from `/api/rolls` | `sheet.py` |
| collect: a boost message is routed to `boost.py` and contributes no roll; the LOADING fix | `conversation.py` |
| the close rule (FR-007), `cancel_boost()` (FR-008) | `conversation.py` |
| the menu (FR-006) | `annotate.py` |
| `cancel_boost` at the prompt | `rolls/__init__.py`, `repl/__init__.py` |

## Design notes

- **Folded into `total`** (spec Decision 2). Rounding, the cap, ceilings, contest margin and the
  exact interrogation total all read `total`, and are all applied at render time, so a boost that
  lands after a write re-renders correctly with no change to any renderer.
- **Target resolution is by MESSAGE id.** A collected roll already carries the id of the message it
  came from (`Roll.message_id`, the image's message for a joined dice card), and a reply / jump link
  names a message. Exactly one attributed, undiscarded roll with that id, by another character,
  unboosted -> applied. Otherwise held with the reason.
- **Order**: messages are processed oldest first and a reply always follows its target, so the
  target is collected before the boost, in the same poll or an earlier one.
- **After applying**: an oppose roll re-settles the GM's tagged rolls (`oppose.settle`), an
  interrogation roll on a line re-runs the private comparison - the same calls `collect` and
  `announce_oppose` already make.
- **The LOADING fix**: a deferred interaction response is an empty message with flag `1 << 7` until
  its edit lands. `collect` stops a channel's page at the first such message (the cursor stays
  before it, so the next poll re-reads it), unless it is older than the 15 minutes an interaction
  token lives - then the edit is never coming and it is passed over.
- **annotate()**: held boosts join the "Which roll?" list as their own rows. Choosing one opens the
  target picker (every attributed, undiscarded, unboosted roll, annotated or not, plus discard).
  Staged like everything else; Ctrl-C discards the lot; committed at finish.
