# Plan 217: void points spent, in the GM-only notes

## Shape

- `rolls/voidspent.py` (new, PURE): `note(conv, entry, count)` records a spend on the
  `Conversation` (`count < 0` is the "previous roll" answer); `entries(conv)` renders the
  `Void points spent:` lines, filtering rolls marked a mistake at render time.
- `models.py`: `VoidSpend(entry, count, earlier)`; `Conversation.void_spends` and
  `void_written` (what was last persisted, as `hidden_written` is for the hidden block).
- `npcskills.py`: `voidspent.note` at the three spend points - `_roll` (the called `vp`) and
  both `[v]` branches of `resolve`.
- `conversation.py`: `_tick` weighs `voidspent.entries` beside the numbers and hidden rolls;
  `_write_notes` rewrites the block in the same single `game_master_info` update, under
  `honor.NOTES_LOCK`, and records `void_written` only on success.
- `hidden.rewrite` gains a `heading` parameter so both GM-only logs share one swap routine.

## Decisions

- **One routine for both logs.** A second copy of `_split`/`rewrite` would drift.
- **Rewrite removes this conversation's earlier lines as a MULTISET from the block's tail**
  (a defect found here, Principle XIV). The old `set` removal deleted EVERY copy of a line, so a
  same-day untitled spend in a second conversation, reading identically to the first's, would
  have erased the first's line. The same latent bug applied to `Hidden rolls:`; fixed for both.
- **A second answer on the same roll updates its count** rather than adding a spend
  (`tact(5, 3, vp)` notes the spend, and the check can still ask).
- **No new module import cycle:** `voidspent` imports only `gmrolls` and `models`; the shared
  rewrite is called from `conversation.py`, not from `voidspent` (which `npcskills` imports, and
  `hidden` imports `npcskills`).

## Constitution check

X (gate, 100% coverage): new module fully covered by `tests/test_rolls_voidspent.py`.
XIII: baseline taken in a detached worktree - 2114 passed. XVI: spec reviewed in three rounds.
No UI change (I does not apply).
