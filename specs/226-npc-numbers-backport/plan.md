# Implementation Plan: NPC numbers backport

**Spec**: [spec.md](spec.md) | **Date**: 2026-10-25

## Summary

A new toolkit route, `POST /api/npc-numbers`, on the same token-gated `/api` controller as `/api/names` (feature 213).
The character-sheet app posts an NPC's name and built stats; the toolkit resolves the name to one Obsidian Portal
character, merges the stats into the "NPC numbers:" block of its GM-only notes (sheet wins on every stat it sends,
lines it does not send are kept), writes only when something changed, and answers with what it did. The REPL's
conversation writer is changed to merge the fresh block instead of overwriting it. The sheet-side caller goes to the
character-sheet session by GitHub issue.

## Technical context

- Python 3.14, CherryPy (`webapp/l7r/app.py`), the existing OP client `chargen/op.py` (`existing_characters`,
  `get_character_body`, `update_character`), `chargen/opsynth.match_character`, and the block's own pure module
  `l7r/repl/rolls/npcnumbers.py` (`parse`, `render`).
- Tests: pytest beside the code's suites in `webapp/tests/`, 100% coverage of the new pure logic; the OP boundary is
  injected (callables), as `honor.discern_honor` does, so no transport mocks.

## Design

### `l7r/npcbackport.py` (new, PURE apart from its injected callables)

- `normalize(stats) -> tuple[dict[str, int], list[str]]` - lowercases, turns `_` into a space (sheet ids such as
  `double_attack`), and keeps a stat only when its name is letters and spaces (the block's line format,
  `npcnumbers._ENTRY`) and its value an integer 0-6. Everything else comes back by name in the refused list.
- `merge(existing, sent) -> Merge` - `numbers` (existing keys in their order with sent values over them, then new keys
  in sent order), and the `added`, `changed` (`name: (old, new)`), `unchanged` lists. Existing keys the sheet did not
  send are carried over untouched (FR-004).
- `backport(name, stats, *, characters, get_body, update) -> dict` - resolve (FR-006), fresh read (FR-009), merge,
  `render`, write only when the notes text changed (FR-005), and the answer (FR-007): `status`, `record`
  (`name`, `url`), `added`, `changed`, `unchanged`, `refused`, `nearest` / `candidates`, `message` (one line the sheet
  can show the GM as is). An OP failure is `status: failed` with the error text, never an exception out of the route.

### `npcnumbers.render` keeps unparsed block lines

`render` replaces the whole block, so a hand-edited line inside it that `parse` skips (`- tact 2 (drunk)`) is deleted
by any write - the REPL's today, and the backport's. FR-004 needs it kept, and the REPL's loss is the same defect
(Principle XIV), so `render` keeps every block line it could not parse, after the parsed ones, in their order.

### The route

`NamesApi.npc_numbers` (CherryPy's default dispatcher maps `npc-numbers` to `npc_numbers`), same gate as `names`:
503 when `names_token` is unset, 401 on a wrong bearer, both before the body is read or OP is touched. POST only (405
otherwise). The body is JSON `{"name": str, "stats": {str: int}, "sheet_id": int?}`; anything else is a 400 with the
reason. The class keeps its name (the `/api` controller for the sheet app) and its docstring says it now carries both
routes.

### The REPL merge (FR-010)

`conversation._write_notes` renders `{**npcnumbers.parse(fresh notes), **conv.numbers}` instead of `conv.numbers`, so a
stat written into the block since the conversation opened survives, while every number the conversation learned
still wins.

## Decisions

- **Same token as `/api/names`** - in the spec's Assumptions, with the declined alternative.
- **One OP list call per backport** (`existing_characters`, live, not the cache): a backport happens a few times a
  fight at most, and a cached roster could miss a character created minutes ago.
- **No lock across processes.** The deployed toolkit and the GM's REPL are separate processes; `NOTES_LOCK` is
  in-process. The fresh read before each write (both sides) narrows the race to the seconds between a read and its
  write; accepted, because the two writers touching the same NPC in the same seconds needs the GM generating that NPC
  for a fight while talking to it in the REPL.

## Constitution check

Principle XIII baseline: the gate in a detached worktree of main before the change. XIV: the `render` fix above. XVI:
spec-fidelity rounds in the spec's Review history. No UI change, so no screenshots or frontend-review.

## Verification

- `( cd webapp && pytest -n auto tests/test_npcbackport.py tests/test_rolls_npcnumbers.py tests/test_sheetnames.py )`,
  then `make done`.
- After deploy: `curl -s -X POST -H "Authorization: Bearer $TOKEN" -d '{"name":"Nobody Atall","stats":{"Air":3}}'
  https://<toolkit>/api/npc-numbers` answers `no_record` without writing.
